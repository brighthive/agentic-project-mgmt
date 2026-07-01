#!/usr/bin/env bash
# Apply the local dogfood warehouse schema + synthetic data in one shot (BH-764).
#
# Prereqs: brightbot docker postgres up (container brightbot-postgres on :5432).
# Idempotent: schema uses IF NOT EXISTS; seed TRUNCATEs before insert.
#
# Usage:
#   bash seed_all.sh                 # apply schema + seed
#   PG_CONTAINER=brightbot-postgres bash seed_all.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PG_CONTAINER="${PG_CONTAINER:-brightbot-postgres}"
PG_USER="${POSTGRES_USER:-bh}"
PG_DB="${POSTGRES_DATABASE:-bh_warehouse}"

info() { echo "[dogfood-seed] $*"; }

# 1. Schema (idempotent)
info "Applying schema to ${PG_CONTAINER}:${PG_DB} ..."
docker exec -i "${PG_CONTAINER}" psql -U "${PG_USER}" -d "${PG_DB}" < "${SCRIPT_DIR}/01_schema.sql" >/dev/null
info "Schema applied."

# 2. Synthetic data (deterministic). Runs on the host via uv so psycopg2 is available.
info "Seeding synthetic data ..."
cd "${SCRIPT_DIR}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}" \
POSTGRES_PORT="${POSTGRES_PORT:-5432}" \
POSTGRES_USER="${PG_USER}" \
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-bh_local_dev}" \
POSTGRES_DATABASE="${PG_DB}" \
  uv run --with psycopg2-binary python seed_local_warehouse.py --reset

info "Local dogfood warehouse ready. Point a workspace_secret_store secret of"
info "type=POSTGRES at host=localhost db=${PG_DB} and the agent can query gold.* / ref.*"
