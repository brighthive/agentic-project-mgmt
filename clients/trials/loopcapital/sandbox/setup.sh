#!/usr/bin/env bash
# Loop Capital SQL Server sandbox — idempotent setup.
# Mirrors clients/trials/longaeva/sandbox/'s DX shape (README → setup → validate),
# swapping Snowflake for a real, local Dockerized SQL Server. This is a REAL
# backend, not a mock — satisfies test-behavior-real.md the same way Longaeva's
# live Snowflake sandbox does; GC-15 (docs/specs/golden-cases-loopcapital.md)
# must run against this, never a stub, per Frank's "this is not live" pushback.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

: "${MSSQL_SA_PASSWORD:?export MSSQL_SA_PASSWORD before running setup.sh}"

echo "[1/5] Starting SQL Server (Docker) — SQL Server Agent enabled, fixed-size data volume..."
docker compose up -d
echo "      Waiting for healthcheck..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' loopcapital-sql-sandbox 2>/dev/null)" = "healthy" ]; do
  sleep 2
done
echo "      SQL Server is healthy."

SQLCMD="docker exec -i loopcapital-sql-sandbox /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P ${MSSQL_SA_PASSWORD} -C"

echo "[2/5] Confirming SQL Server Agent is running (required for GC-15's job-status query)..."
$SQLCMD -Q "IF (SELECT status FROM sys.dm_server_services WHERE servicename LIKE 'SQL Server Agent%') <> 4
  RAISERROR('SQL Server Agent is not running — check MSSQL_AGENT_ENABLED', 16, 1);"

echo "[3/5] Creating the demo database + Asset Management staging tables..."
$SQLCMD < sql/01_create_database.sql

echo "[4/5] Creating SQL Server Agent jobs (mix of pass/fail, for GC-15's job-status query)..."
$SQLCMD < sql/02_create_agent_jobs.sql

echo "[5/5] Filling the fixed-size data volume toward the 20% free-space threshold..."
./fill_disk.sh

echo ""
echo "Setup complete."
echo "  ./validate.sh              — confirm both GC-15 queries return real data"
echo "  ./profile_warehouse.py     — run a real profiler pass against holdings_raw"
echo "  ssis/*.dtsx, ssrs/*.rdl    — real SSIS/SSRS artifacts for diagnostics skills"
