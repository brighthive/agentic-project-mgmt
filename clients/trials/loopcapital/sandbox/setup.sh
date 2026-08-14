#!/usr/bin/env bash
# Loop Capital SQL Server sandbox — idempotent setup.
# Mirrors clients/trials/longaeva/sandbox/'s DX shape (README → setup → validate),
# swapping Snowflake for a real, local Dockerized SQL Server. This is a REAL
# backend, not a mock — satisfies test-behavior-real.md the same way Longaeva's
# live Snowflake sandbox does; GC-15 (docs/specs/golden-cases-loopcapital.md)
# must run against this, never a stub, per Frank's "this is not live" pushback.
#
# This script owns CONTAINER lifecycle only (start + healthcheck + Agent
# check). All data seeding is reset.py's job — one seeding mechanism, not
# two. To reseed data without restarting the container (e.g. switching
# scenarios mid-development), run reset.py directly; use THIS script only
# for a full cold start.
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

: "${MSSQL_SA_PASSWORD:?export MSSQL_SA_PASSWORD before running setup.sh}"
readonly HEALTHCHECK_TIMEOUT_S="${LOOPCAPITAL_HEALTHCHECK_TIMEOUT_S:-120}"
readonly SCENARIO="${LOOPCAPITAL_SCENARIO:-baseline}"

# -b: treat a Severity >= 11 error (RAISERROR 16, a batch failure) as a
# real non-zero exit — without it, sqlcmd under `set -e` silently returns
# 0 on SQL errors and setup continues past a broken step (caught in review).
readonly SQLCMD="docker exec -i loopcapital-sql-sandbox /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P ${MSSQL_SA_PASSWORD} -C -b"

echo "[1/6] Starting SQL Server (Docker) — SQL Server Agent enabled, fixed-size data volume..."
docker compose up -d
echo "      Waiting for healthcheck (timeout ${HEALTHCHECK_TIMEOUT_S}s)..."
elapsed=0
until [[ "$(docker inspect -f '{{.State.Health.Status}}' loopcapital-sql-sandbox 2>/dev/null)" == "healthy" ]]; do
  if [[ "${elapsed}" -ge "${HEALTHCHECK_TIMEOUT_S}" ]]; then
    echo "ERROR: container did not become healthy within ${HEALTHCHECK_TIMEOUT_S}s." >&2
    echo "Check: docker logs loopcapital-sql-sandbox (common causes: MSSQL_SA_PASSWORD" >&2
    echo "doesn't meet SQL Server's complexity rules, or port 1433 already in use)." >&2
    exit 1
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done
echo "      SQL Server is healthy."

echo "[2/6] Confirming SQL Server Agent is running (required for GC-15's job-status query)..."
# ISNULL guards against sys.dm_server_services returning zero rows on some
# Linux container builds — a bare "<> 4" comparison against a missing row
# evaluates to UNKNOWN and silently skips the RAISERROR, letting setup
# continue as if Agent were verified when it was never checked (caught in
# review). ISNULL(..., 0) forces a real 0 in that case, which fails loudly.
${SQLCMD} -Q "IF ISNULL((SELECT status FROM sys.dm_server_services WHERE servicename LIKE 'SQL Server Agent%'), 0) <> 4
  RAISERROR('SQL Server Agent is not running (or its status row is missing) — check MSSQL_AGENT_ENABLED', 16, 1);"

echo "[3/6] Seeding data — scenario '${SCENARIO}' (override with LOOPCAPITAL_SCENARIO=...)..."
python3 reset.py --scenario "${SCENARIO}"

# reset.py drops and recreates LoopCapitalAM, so everything below must run AFTER
# it — database users do not survive a DROP DATABASE (server logins do).
echo "[4/6] Applying the medallion bank schema (sql/03_bank_schema.sql)..."
# Until now nothing in the automated path applied this file: setup.sh called only
# reset.py, and reset.py applies 01 + 02. The medallion tables the README documents
# therefore never existed unless someone ran the file by hand. Wiring it in here
# closes that gap — and governed_write_check.py depends on these tables existing,
# because a permission check against a missing table passes for the wrong reason.
# Piped via stdin, not `-i`: SQLCMD runs INSIDE the container (docker exec), so a
# `-i sql/...` path would resolve against the container filesystem, where the repo
# is not mounted. Feeding the file on stdin keeps one sqlcmd session, so `GO`
# batching and `USE` context work exactly as written.
${SQLCMD} -d LoopCapitalAM < sql/03_bank_schema.sql

echo "[5/6] Creating the instance's other databases — OMS + TradeDW (sql/06_multi_database.sql)..."
# A SQL Server instance hosts many databases and Frank's box does too. These are
# the ones the sandbox's own SSIS/SSRS/XSD artifacts already reference, so
# creating them turns three orphaned diagnostic samples into live fixtures and
# gives cross-database (three-part name) targeting something real to run against.
# Anchor date is passed through so their seeded dates stay reproducible alongside
# reset.py's.
${SQLCMD} -v ANCHOR_DATE="${LOOPCAPITAL_ANCHOR_DATE:-$(date -u +%F)}" < sql/06_multi_database.sql

echo "[6/6] Creating governed connection principals (sql/05_governed_principals.sql)..."
# Passwords are generated per-run and exported for governed_write_check.py. These
# are throwaway local sandbox credentials — never a real Loop Capital secret, and
# this script still writes none of them to disk.
#
# But a recreate that regenerates them silently orphans anything already holding
# them — notably an installed engineering runner, whose env file then fails with a
# bare "Login failed for user 'brightagent_engineer'" that names no cause. So if
# that env file exists, it is the source of truth and we reuse what it holds.
# Explicit env vars still win over both, and a machine with no runner installed
# behaves exactly as before.
readonly RUNNER_ENV_FILE="${BRIGHTAGENT_ENV_FILE:-${HOME}/.brightagent/config/onprem.env}"

password_from_runner_env() {
  local key="${1:?password_from_runner_env requires a variable name}"
  [[ -r "${RUNNER_ENV_FILE}" ]] || return 0
  sed -n "s/^export ${key}=//p" "${RUNNER_ENV_FILE}" | tail -1 | tr -d "\"'"
}

if [[ -z "${BRIGHTAGENT_READER_PASSWORD:-}" || -z "${BRIGHTAGENT_ENGINEER_PASSWORD:-}" ]]; then
  if [[ -r "${RUNNER_ENV_FILE}" ]]; then
    echo "      reusing the logins an installed runner already holds (${RUNNER_ENV_FILE})"
  fi
  BRIGHTAGENT_READER_PASSWORD="${BRIGHTAGENT_READER_PASSWORD:-$(password_from_runner_env BRIGHTAGENT_ONPREM_SQL_READER_PASSWORD)}"
  BRIGHTAGENT_ENGINEER_PASSWORD="${BRIGHTAGENT_ENGINEER_PASSWORD:-$(password_from_runner_env BRIGHTAGENT_ENGINEER_PASSWORD)}"
fi

export BRIGHTAGENT_READER_PASSWORD="${BRIGHTAGENT_READER_PASSWORD:-Reader-$(openssl rand -hex 8)!aA1}"
export BRIGHTAGENT_ENGINEER_PASSWORD="${BRIGHTAGENT_ENGINEER_PASSWORD:-Engineer-$(openssl rand -hex 8)!aA1}"
${SQLCMD} -d LoopCapitalAM \
  -v BRIGHTAGENT_READER_PASSWORD="${BRIGHTAGENT_READER_PASSWORD}" \
  -v BRIGHTAGENT_ENGINEER_PASSWORD="${BRIGHTAGENT_ENGINEER_PASSWORD}" \
  < sql/05_governed_principals.sql

echo ""
echo "Setup complete."
echo "  ./validate.sh              — confirm both GC-15 queries return real data"
echo "  ./profile_warehouse.py     — run a real profiler pass against holdings_raw"
echo "  ./reset.py --scenario X    — reset to ground zero + reseed against a named scenario"
echo "  ssis/*.dtsx, ssrs/*.rdl    — real SSIS/SSRS artifacts for diagnostics skills"
echo ""
echo "Governed read/write boundary — export these, then prove it:"
echo "  export BRIGHTAGENT_READER_PASSWORD='${BRIGHTAGENT_READER_PASSWORD}'"
echo "  export BRIGHTAGENT_ENGINEER_PASSWORD='${BRIGHTAGENT_ENGINEER_PASSWORD}'"
echo "  uv run --with pymssql python governed_write_check.py"
