#!/usr/bin/env bash
set -euo pipefail

# Description: Client-facing walkthrough proving BrightHive's cloud reads THIS local SQL Server.
# Usage: cloud_sees_local.sh [--staging] [--unplug]
#
# Act 1  the box      docker: the container, the image, the three databases on the instance
# Act 2  the data     SELECT *: real rows in all three databases, plus the source-vs-warehouse gap
# Act 3  the link     one query, two addresses (localhost and the public tunnel) -> same server
# Act 4  --staging    BrightHive staging resolves its own workspace secret and lands on this box
# Act 5  --unplug     stop the container: the cloud goes blind. start it: the cloud sees again.
#
# Acts 1-3 are read-only and safe to run in front of anyone. Act 4 reads (never writes) the
# staging workspace secret. Act 5 stops and restarts the container - data survives, but do not
# run it mid-conversation with a live client query in flight.

readonly SCRIPT_NAME="$(basename "$0")"
readonly CONTAINER="loopcapital-sql-sandbox"
readonly TUNNEL_HOST="${LOOPCAPITAL_TUNNEL_HOST:-bore.pub}"
readonly TUNNEL_PORT="${LOOPCAPITAL_TUNNEL_PORT:-59916}"
readonly STAGING_WORKSPACE="e3fc0917-03a6-4ac6-aad4-ac265329bfb9"
readonly BRIGHTBOT_DIR="${LOOPCAPITAL_BRIGHTBOT_DIR:-${HOME}/iccha/brighthive/brightbot}"
readonly DATABASES=(LoopCapitalAM OMS TradeDW)

info() { echo "[${SCRIPT_NAME}] INFO:  $*"; }
error() { echo "[${SCRIPT_NAME}] ERROR: $*" >&2; }
die() {
  error "$@"
  exit 1
}

act() {
  echo ""
  echo "════════════════════════════════════════════════════════════════════════"
  echo "  $*"
  echo "════════════════════════════════════════════════════════════════════════"
  echo ""
}

step() { echo "── $* ──"; }

require_commands() {
  local cmd
  for cmd in "$@"; do
    command -v "${cmd}" >/dev/null 2>&1 || die "Required command not found: ${cmd}"
  done
}

# The SA password is never committed. Recover it from the running container unless the operator
# already exported it. Printed nowhere, passed only into the container's own sqlcmd.
resolve_sa_password() {
  local recovered
  if [[ -n "${MSSQL_SA_PASSWORD:-}" ]]; then
    echo "${MSSQL_SA_PASSWORD}"
    return 0
  fi
  recovered="$(docker inspect "${CONTAINER}" \
    --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null |
    grep '^MSSQL_SA_PASSWORD=' | cut -d= -f2- || true)"
  [[ -n "${recovered}" ]] || die "Could not recover MSSQL_SA_PASSWORD - export it, or start the container"
  echo "${recovered}"
}

# Query through the container's own loopback - what we see standing at the machine.
ask_local() {
  local database="${1:?ask_local requires a database}"
  local query="${2:?ask_local requires a query}"
  docker exec -i "${CONTAINER}" /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P "${SA_PASSWORD}" -C -d "${database}" -W -s'|' -w 400 -Q "${query}"
}

# Query through the public tunnel address - the exact host:port BrightHive's cloud is registered
# against. Same engine, different door.
ask_through_tunnel() {
  local database="${1:?ask_through_tunnel requires a database}"
  local query="${2:?ask_through_tunnel requires a query}"
  docker exec -i "${CONTAINER}" /opt/mssql-tools18/bin/sqlcmd \
    -S "${TUNNEL_HOST},${TUNNEL_PORT}" -U sa -P "${SA_PASSWORD}" -C -d "${database}" \
    -W -s'|' -w 400 -l 20 -Q "${query}"
}

# Probe the tunnel from the HOST, not from inside the container. `docker exec` blocks against a
# paused container, so Act 5's "is it frozen?" check can never go through ask_through_tunnel.
# Short login timeout keeps the frozen case quick instead of hanging the demo.
ask_through_tunnel_briefly() {
  local database="${1:?ask_through_tunnel_briefly requires a database}"
  local query="${2:?ask_through_tunnel_briefly requires a query}"
  MSSQL_SA_PASSWORD="${SA_PASSWORD}" \
    LOOPCAPITAL_PROBE_HOST="${TUNNEL_HOST}" \
    LOOPCAPITAL_PROBE_PORT="${TUNNEL_PORT}" \
    LOOPCAPITAL_PROBE_DB="${database}" \
    LOOPCAPITAL_PROBE_QUERY="${query}" \
    uv run --with pymssql python -c '
import os, sys
import pymssql

try:
    connection = pymssql.connect(
        server=os.environ["LOOPCAPITAL_PROBE_HOST"],
        port=int(os.environ["LOOPCAPITAL_PROBE_PORT"]),
        user="sa",
        password=os.environ["MSSQL_SA_PASSWORD"],
        database=os.environ["LOOPCAPITAL_PROBE_DB"],
        login_timeout=8,
        timeout=8,
    )
    cursor = connection.cursor()
    cursor.execute(os.environ["LOOPCAPITAL_PROBE_QUERY"])
    print(cursor.fetchone())
    connection.close()
except Exception as exc:
    print(f"no answer: {type(exc).__name__}", file=sys.stderr)
    sys.exit(1)
'
}

readonly FINGERPRINT_QUERY="SET NOCOUNT ON;
SELECT @@SERVERNAME AS server_name,
       SERVERPROPERTY('ProcessID') AS engine_pid,
       (SELECT COUNT(*) FROM OMS.dbo.Trades) AS oms_trades,
       (SELECT COUNT(*) FROM TradeDW.dbo.FactTrade) AS tradedw_facttrade,
       (SELECT COUNT(*) FROM LoopCapitalAM.dbo.holdings_raw) AS loopcapitalam_holdings,
       CONVERT(VARCHAR(23), GETDATE(), 121) AS answered_at"

show_the_box() {
  act "ACT 1 - The box: a real SQL Server, running here, right now"

  step "The container"
  docker ps --filter "name=${CONTAINER}" \
    --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

  echo ""
  step "Databases on the instance (a server hosts many databases - so does Frank's)"
  ask_local master "SET NOCOUNT ON;
    SELECT name AS database_name, state_desc AS state,
           CONVERT(VARCHAR(19), create_date, 120) AS created
    FROM sys.databases WHERE database_id > 4 ORDER BY name"
}

show_the_data() {
  act "ACT 2 - The data: real tables, real rows, in all three databases"

  local database
  for database in "${DATABASES[@]}"; do
    step "${database} - every table and its row count"
    ask_local "${database}" "SET NOCOUNT ON;
      SELECT s.name + '.' + t.name AS table_name, SUM(p.rows) AS row_count
      FROM sys.tables t
      JOIN sys.schemas s ON s.schema_id = t.schema_id
      JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
      GROUP BY s.name, t.name ORDER BY 1"
    echo ""
  done

  step "SELECT * - the operational trade book (OMS.dbo.Trades)"
  ask_local OMS "SET NOCOUNT ON; SELECT TOP 5 * FROM dbo.Trades ORDER BY trade_id"
  echo ""

  step "SELECT * - the warehouse fact table (TradeDW.dbo.FactTrade)"
  ask_local TradeDW "SET NOCOUNT ON; SELECT TOP 5 * FROM dbo.FactTrade ORDER BY fact_trade_id"
  echo ""

  step "SELECT * - the asset-management holdings feed (LoopCapitalAM.dbo.holdings_raw)"
  ask_local LoopCapitalAM "SET NOCOUNT ON; SELECT TOP 5 * FROM dbo.holdings_raw ORDER BY holding_id"
  echo ""

  step "One query, three-part names, across two databases - the source-vs-warehouse gap"
  ask_local master "SET NOCOUNT ON;
    SELECT 'OMS.dbo.Trades (source)' AS table_name, COUNT(*) AS row_count FROM OMS.dbo.Trades
    UNION ALL
    SELECT 'TradeDW.dbo.FactTrade (warehouse)', COUNT(*) FROM TradeDW.dbo.FactTrade
    UNION ALL
    SELECT 'unloaded trades', (SELECT COUNT(*) FROM OMS.dbo.Trades)
                              - (SELECT COUNT(*) FROM TradeDW.dbo.FactTrade)"
  echo ""
  info "That gap is deliberate: the nightly fact load lags the source. It is exactly the kind of"
  info "drift a monitoring agent is supposed to notice on its own."
}

show_the_link() {
  act "ACT 3 - The link: one question, two addresses, one server"

  info "Checking the public tunnel is up at ${TUNNEL_HOST}:${TUNNEL_PORT} ..."
  if ! nc -z -w 5 "${TUNNEL_HOST}" "${TUNNEL_PORT}" >/dev/null 2>&1; then
    error "${TUNNEL_HOST}:${TUNNEL_PORT} is not reachable."
    error "The tunnel port is assigned fresh on every restart. Check it is running:"
    error "    ps aux | grep '[b]ore local 1433'"
    error "Then re-run with the live port: LOOPCAPITAL_TUNNEL_PORT=<port> ${SCRIPT_NAME}"
    die "Cannot prove the link while the tunnel is down."
  fi
  info "Tunnel is up."
  echo ""

  step "Asked over localhost:1433 - standing at the machine"
  ask_local OMS "${FINGERPRINT_QUERY}"
  echo ""

  step "Asked over ${TUNNEL_HOST}:${TUNNEL_PORT} - the address BrightHive's cloud is registered against"
  ask_through_tunnel OMS "${FINGERPRINT_QUERY}"
  echo ""

  info "Same server_name, same engine_pid, same row counts. There is one database engine here,"
  info "and the public address reaches it. The clock in answered_at moves between the two runs,"
  info "so neither answer is a cached copy - both were computed just now, by this box."
}

show_staging_resolves_it() {
  act "ACT 4 - BrightHive staging resolves its own workspace and lands on this box"

  [[ -d "${BRIGHTBOT_DIR}" ]] || die "brightbot not found at ${BRIGHTBOT_DIR} - set LOOPCAPITAL_BRIGHTBOT_DIR"

  info "Workspace ${STAGING_WORKSPACE} on staging holds several SQL-Server connections."
  info "This suite reads that workspace's stored connection details, opens a real connection for"
  info "each, and asks the server which login and database it actually landed in. Read-only."
  echo ""

  # AWS_ENDPOINT_URL must be unset: brightbot's committed .env points it at a localstack that is
  # not running, which silently hijacks every AWS call.
  (
    cd "${BRIGHTBOT_DIR}"
    env -u AWS_ENDPOINT_URL AWS_PROFILE=brighthive-staging \
      uv run pytest tests/integration/mcp/test_warehouse_selection_real.py -v --no-cov -p no:cacheprovider
  ) || die "Staging resolution suite failed - see output above."

  echo ""
  info "Green means staging's own stored configuration resolved to this container, over the"
  info "tunnel, with the scoped read-only login - not to a fixture and not to a copy."
}

show_the_unplug() {
  act "ACT 5 - Pull the plug: the cloud goes blind, then sees again"

  # We FREEZE the engine, we never stop the container. LoopCapitalAM's data files live on a
  # memory-backed mount (/var/opt/mssql/loopcapital_data, tmpfs) so that the disk-pressure
  # fixture can report real free space. Docker recreates that mount EMPTY on any container
  # restart, so `docker stop && docker start` would silently destroy LoopCapitalAM - minutes
  # before a client call. `docker pause` suspends the processes and leaves every mount intact.
  step "Freezing the database engine (mounts untouched - see note in this function)"
  docker pause "${CONTAINER}" >/dev/null
  info "Engine frozen."
  echo ""

  step "Asking again over ${TUNNEL_HOST}:${TUNNEL_PORT} - this SHOULD fail"
  local froze_out="frozen"
  if ask_through_tunnel_briefly OMS "SET NOCOUNT ON; SELECT 1" >/dev/null 2>&1; then
    froze_out="answered"
  fi

  if [[ "${froze_out}" == "answered" ]]; then
    docker unpause "${CONTAINER}" >/dev/null
    die "The address still answered while the engine was frozen - stop and investigate before demoing."
  fi
  info "No answer. The address is still there, but nothing behind it can reply."
  info "A cached copy or an exported extract would have answered anyway. This cannot -"
  info "because the only thing that ever answers is this machine."
  echo ""

  step "Unfreezing"
  docker unpause "${CONTAINER}" >/dev/null
  local attempt
  for attempt in $(seq 1 15); do
    if ask_local master "SET NOCOUNT ON; SELECT 1" >/dev/null 2>&1; then
      info "Answering again after ${attempt} attempt(s)."
      break
    fi
    sleep 2
  done
  echo ""

  step "Asking one more time - same server, same rows, nothing lost"
  ask_local OMS "${FINGERPRINT_QUERY}"
  echo ""
  info "Note: the tunnel port survives this, but NOT a restart of the tunnel process itself."
  info "If the tunnel restarts it is assigned a new port, and the address stored on the"
  info "BrightHive side has to be updated to match before anything can reach this box again."
}

main() {
  local run_staging="false"
  local run_unplug="false"
  local arg

  for arg in "$@"; do
    case "${arg}" in
    --staging) run_staging="true" ;;
    --unplug) run_unplug="true" ;;
    -h | --help)
      echo "Usage: ${SCRIPT_NAME} [--staging] [--unplug]"
      exit 0
      ;;
    *) die "Unknown option: ${arg} (see --help)" ;;
    esac
  done

  require_commands docker nc
  docker ps --filter "name=${CONTAINER}" --format '{{.Names}}' | grep -q "${CONTAINER}" ||
    die "${CONTAINER} is not running - start it with ./setup.sh"

  SA_PASSWORD="$(resolve_sa_password)"
  readonly SA_PASSWORD

  show_the_box
  show_the_data
  show_the_link
  [[ "${run_staging}" == "true" ]] && show_staging_resolves_it
  [[ "${run_unplug}" == "true" ]] && show_the_unplug

  act "Done"
  info "Local and cloud are the same server. Not a copy, not a sync, not a snapshot -"
  info "BrightHive reads this machine directly, and reads nothing it was not granted."
}

main "$@"
