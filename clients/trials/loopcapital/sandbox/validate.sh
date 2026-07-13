#!/usr/bin/env bash
# Runs BH-1045's two CONFIRMED query texts (docs/specs/golden-cases-loopcapital.md
# GC-15 / proactive-pipeline-ingestion-monitoring.md) against this sandbox and
# asserts the ACTUAL content, not just non-empty output — the same "prove it"
# pattern as Longaeva's validate_poc.sh, adapted for SQL Server instead of
# Snowflake.
#
# Queries use -d (database flag) instead of a leading "USE ...;" batch —
# SynapseConnection.execute_query (brightbot/tools/warehouse_connections.py)
# strips one trailing ";" and rejects any semicolon remaining after that, so
# a "USE db; SELECT ..." two-statement batch is NOT the shape BH-1045's real
# watchdog can send. Validating against -d instead keeps this script honest
# about what the real connection path actually accepts.
set -euo pipefail

: "${MSSQL_SA_PASSWORD:?export MSSQL_SA_PASSWORD before running validate.sh}"
readonly TARGET_FREE_PCT_MAX="${LOOPCAPITAL_TARGET_FREE_PCT_MAX:-25}" # must be BELOW this to prove disk pressure is real

PASS=0
FAIL=0

sqlcmd_query() {
  local database="${1}" query="${2}"
  docker exec -i loopcapital-sql-sandbox /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C -d "${database}" -h -1 -Q "${query}"
}

fail() {
  echo "FAIL: ${1}"
  FAIL=$((FAIL + 1))
}

pass() {
  echo "PASS: ${1}"
  PASS=$((PASS + 1))
}

echo "GC-15 disk-check query (BH-1045, pass 38 — sys.dm_os_volume_stats):"
disk_exit=0
disk_output=$(sqlcmd_query "LoopCapitalAM" "
SELECT DB_NAME(vs.database_id) AS database_name, mf.name AS logical_file_name,
    vs.total_bytes, vs.available_bytes,
    CAST(vs.available_bytes * 100.0 / vs.total_bytes AS DECIMAL(5,2)) AS percent_free
FROM sys.master_files AS mf
CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs;
") || disk_exit=$?
echo "${disk_output}" | sed 's/^/  /'

if [[ "${disk_exit}" -ne 0 ]]; then
  fail "disk-space query — sqlcmd exited ${disk_exit} (see output above for the real error)"
else
  # Last column is percent_free — pull the first data row's value, not just "non-empty."
  percent_free=$(echo "${disk_output}" | awk '/LoopCapitalAM/ {print $NF; exit}')
  if [[ -z "${percent_free}" ]]; then
    fail "disk-space query — ran, but no percent_free value could be parsed from output"
  elif (( $(echo "${percent_free} < ${TARGET_FREE_PCT_MAX}" | bc -l 2>/dev/null || echo 0) )); then
    pass "disk-space query — real percent_free=${percent_free}% (< ${TARGET_FREE_PCT_MAX}%, disk pressure confirmed)"
  else
    fail "disk-space query ran, but percent_free=${percent_free}% is NOT below ${TARGET_FREE_PCT_MAX}% — fill_disk.sh likely wasn't run, or the volume reset"
  fi
fi

echo ""
echo "GC-15 job-status query (BH-1045, pass 39 — msdb.dbo.sysjobs/sysjobhistory):"
job_exit=0
job_output=$(sqlcmd_query "msdb" "
WITH LatestRun AS (
    SELECT j.job_id, j.name AS job_name, h.run_status, h.run_date, h.run_time,
        ROW_NUMBER() OVER (PARTITION BY j.job_id ORDER BY h.run_date DESC, h.run_time DESC) AS rn
    FROM msdb.dbo.sysjobs AS j JOIN msdb.dbo.sysjobhistory AS h ON h.job_id = j.job_id
    WHERE h.step_id = 0
)
SELECT job_name, CASE run_status WHEN 0 THEN 'Failed' WHEN 1 THEN 'Succeeded' WHEN 2 THEN 'Retry'
    WHEN 3 THEN 'Canceled' WHEN 4 THEN 'In Progress' ELSE 'Unknown' END AS run_status_text
FROM LatestRun WHERE rn = 1 ORDER BY job_name;
") || job_exit=$?
echo "${job_output}" | sed 's/^/  /'

if [[ "${job_exit}" -ne 0 ]]; then
  fail "job-status query — sqlcmd exited ${job_exit} (see output above for the real error)"
else
  has_succeeded=$(echo "${job_output}" | grep -c "Succeeded" || true)
  has_failed=$(echo "${job_output}" | grep -c "Failed" || true)
  if [[ "${has_succeeded}" -ge 1 ]] && [[ "${has_failed}" -ge 1 ]]; then
    pass "job-status query — real mix confirmed (${has_succeeded} Succeeded row(s), ${has_failed} Failed row(s))"
  else
    fail "job-status query ran, but did not return BOTH a Succeeded and a Failed row (succeeded=${has_succeeded}, failed=${has_failed}) — jobs may still be running; see setup.sh's wait-for-completion step"
  fi
fi

echo ""
echo "Results: ${PASS} passed, ${FAIL} failed"
[[ "${FAIL}" -eq 0 ]]
