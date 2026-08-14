#!/usr/bin/env bash
set -euo pipefail

# Description: Dump every database, every table, and sample rows from the local SQL Server sandbox.
# Usage: show_all_data.sh [row_limit]        (default 5 rows per table; use 0 for counts only)

readonly SCRIPT_NAME="$(basename "$0")"
readonly CONTAINER="loopcapital-sql-sandbox"
readonly ROW_LIMIT="${1:-5}"

info() { echo "[${SCRIPT_NAME}] INFO:  $*"; }
error() { echo "[${SCRIPT_NAME}] ERROR: $*" >&2; }
die() {
  error "$@"
  exit 1
}

command -v docker >/dev/null 2>&1 || die "docker not found"
docker ps --filter "name=${CONTAINER}" --format '{{.Names}}' | grep -q "${CONTAINER}" ||
  die "${CONTAINER} is not running - start it with ./setup.sh"

# The SA password is never committed. Recover it from the running container unless already exported.
if [[ -z "${MSSQL_SA_PASSWORD:-}" ]]; then
  MSSQL_SA_PASSWORD="$(docker inspect "${CONTAINER}" \
    --format '{{range .Config.Env}}{{println .}}{{end}}' |
    grep '^MSSQL_SA_PASSWORD=' | cut -d= -f2- || true)"
fi
[[ -n "${MSSQL_SA_PASSWORD}" ]] || die "Could not resolve MSSQL_SA_PASSWORD"
readonly MSSQL_SA_PASSWORD

# stdin is redirected from /dev/null: `docker exec -i` would otherwise swallow the caller's stdin
# and starve any loop reading a list of tables.
ask() {
  local database="${1:?ask requires a database}"
  local query="${2:?ask requires a query}"
  shift 2
  docker exec -i "${CONTAINER}" /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "${MSSQL_SA_PASSWORD}" -C -d "${database}" \
    -W -s'|' -w 400 "$@" -Q "${query}" </dev/null
}

main() {
  local databases=() tables=() database table

  info "Reading every user database on the instance ..."
  mapfile -t databases < <(
    ask master "SET NOCOUNT ON; SELECT name FROM sys.databases WHERE database_id > 4 ORDER BY name" -h -1 |
      tr -d '\r' | sed 's/[[:space:]]*$//' | grep -E '^[A-Za-z]'
  )
  [[ "${#databases[@]}" -gt 0 ]] || die "No user databases found"
  info "Found ${#databases[@]}: ${databases[*]}"

  for database in "${databases[@]}"; do
    echo ""
    echo "################################################################"
    echo "#  DATABASE: ${database}"
    echo "################################################################"

    echo ""
    echo "--- tables and row counts ---"
    ask "${database}" "SET NOCOUNT ON;
      SELECT s.name + '.' + t.name AS table_name, SUM(p.rows) AS row_count
      FROM sys.tables t
      JOIN sys.schemas s ON s.schema_id = t.schema_id
      JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
      GROUP BY s.name, t.name ORDER BY 1"

    [[ "${ROW_LIMIT}" == "0" ]] && continue

    mapfile -t tables < <(
      ask "${database}" "SET NOCOUNT ON;
        SELECT s.name + '.' + t.name
        FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
        ORDER BY 1" -h -1 | tr -d '\r' | sed 's/[[:space:]]*$//' | grep -E '^[A-Za-z]'
    )

    for table in "${tables[@]}"; do
      echo ""
      echo "--- SELECT TOP ${ROW_LIMIT} * FROM ${database}.${table} ---"
      ask "${database}" "SET NOCOUNT ON; SELECT TOP ${ROW_LIMIT} * FROM ${table}"
    done
  done

  echo ""
  info "Done - ${#databases[@]} databases dumped from ${CONTAINER}"
}

main "$@"
