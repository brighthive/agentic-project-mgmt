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

echo "[1/3] Starting SQL Server (Docker) — SQL Server Agent enabled, fixed-size data volume..."
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

echo "[2/3] Confirming SQL Server Agent is running (required for GC-15's job-status query)..."
# ISNULL guards against sys.dm_server_services returning zero rows on some
# Linux container builds — a bare "<> 4" comparison against a missing row
# evaluates to UNKNOWN and silently skips the RAISERROR, letting setup
# continue as if Agent were verified when it was never checked (caught in
# review). ISNULL(..., 0) forces a real 0 in that case, which fails loudly.
${SQLCMD} -Q "IF ISNULL((SELECT status FROM sys.dm_server_services WHERE servicename LIKE 'SQL Server Agent%'), 0) <> 4
  RAISERROR('SQL Server Agent is not running (or its status row is missing) — check MSSQL_AGENT_ENABLED', 16, 1);"

echo "[3/3] Seeding data — scenario '${SCENARIO}' (override with LOOPCAPITAL_SCENARIO=...)..."
python3 reset.py --scenario "${SCENARIO}"

echo ""
echo "Setup complete."
echo "  ./validate.sh              — confirm both GC-15 queries return real data"
echo "  ./profile_warehouse.py     — run a real profiler pass against holdings_raw"
echo "  ./reset.py --scenario X    — reset to ground zero + reseed against a named scenario"
echo "  ssis/*.dtsx, ssrs/*.rdl    — real SSIS/SSRS artifacts for diagnostics skills"
