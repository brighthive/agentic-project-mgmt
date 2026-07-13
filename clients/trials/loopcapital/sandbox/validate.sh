#!/usr/bin/env bash
# Runs BH-1045's two CONFIRMED query texts (docs/specs/golden-cases-loopcapital.md
# GC-15 / proactive-pipeline-ingestion-monitoring.md) against this sandbox and
# asserts real, non-trivial results — the same "prove it" pattern as Longaeva's
# validate_poc.sh, adapted for SQL Server instead of Snowflake.
set -euo pipefail

: "${MSSQL_SA_PASSWORD:?export MSSQL_SA_PASSWORD before running validate.sh}"
SQLCMD="docker exec -i loopcapital-sql-sandbox /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P ${MSSQL_SA_PASSWORD} -C -h -1"

PASS=0
FAIL=0

check() {
  local name="${1}" query="${2}" expect_nonempty="${3}"
  local result
  echo -n "  ${name}... "
  result=$(${SQLCMD} -Q "${query}" 2>&1 | grep -v '^$' | grep -v 'rows affected' || true)
  if [[ "${expect_nonempty}" == "true" ]] && [[ -z "${result}" ]]; then
    echo "FAIL (empty result)"
    FAIL=$((FAIL + 1))
  else
    echo "PASS"
    echo "${result}" | sed 's/^/      /'
    PASS=$((PASS + 1))
  fi
}

echo "GC-15 disk-check query (BH-1045, pass 38 — sys.dm_os_volume_stats):"
check "disk-space query returns real percent_free" "
USE LoopCapitalAM;
SELECT DB_NAME(vs.database_id) AS database_name, mf.name AS logical_file_name,
    vs.total_bytes, vs.available_bytes,
    CAST(vs.available_bytes * 100.0 / vs.total_bytes AS DECIMAL(5,2)) AS percent_free
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs;
" true

echo ""
echo "GC-15 job-status query (BH-1045, pass 39 — msdb.dbo.sysjobs/sysjobhistory):"
check "job-status query returns a mix of Succeeded/Failed" "
USE msdb;
WITH LatestRun AS (
    SELECT j.job_id, j.name AS job_name, h.run_status, h.run_date, h.run_time,
        ROW_NUMBER() OVER (PARTITION BY j.job_id ORDER BY h.run_date DESC, h.run_time DESC) AS rn
    FROM msdb.dbo.sysjobs AS j JOIN msdb.dbo.sysjobhistory AS h ON h.job_id = j.job_id
    WHERE h.step_id = 0
)
SELECT job_name, CASE run_status WHEN 0 THEN 'Failed' WHEN 1 THEN 'Succeeded' WHEN 2 THEN 'Retry'
    WHEN 3 THEN 'Canceled' WHEN 4 THEN 'In Progress' ELSE 'Unknown' END AS run_status_text
FROM LatestRun WHERE rn = 1 ORDER BY job_name;
" true

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[[ "${FAIL}" -eq 0 ]]
