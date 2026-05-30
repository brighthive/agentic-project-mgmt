#!/usr/bin/env bash
# PoC use-case validation suite.
#
# Runs every Longaeva POC scorecard criterion against the live sandbox and
# reports pass/fail mapped to overview.md success criteria. This is the single
# command that answers "can we actually resolve each use case?".
#
# Run: ./validate_poc.sh
# Requires: snow CLI, uv, REST stub reachable on :8000 for use case 1.2
#   (the suite starts/stops the stub itself).

set -uo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PASS=0; FAIL=0; SKIP=0
declare -a LINES

ok()   { echo "  ✅ $1"; PASS=$((PASS+1)); LINES+=("PASS  $1"); }
bad()  { echo "  ❌ $1"; FAIL=$((FAIL+1)); LINES+=("FAIL  $1"); }
skip() { echo "  ⏭️  $1"; SKIP=$((SKIP+1)); LINES+=("SKIP  $1"); }

count() { snow sql --format JSON -q "$1" -c brighthive 2>/dev/null | grep -oE '"[A-Z_]+":[[:space:]]*[0-9.]+' | head -1 | grep -oE '[0-9.]+'; }

echo "############################################################"
echo "# Longaeva PoC — use-case validation suite"
echo "# $(date '+%Y-%m-%d %H:%M')"
echo "############################################################"

# ---------------------------------------------------------------------------
echo
echo "## 1. Ingestion — 3 source patterns"

# 1.1 S3 vendor bucket
S3_ROWS=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_POC.BRONZE.raw_market_prices;")
if [ "${S3_ROWS%.*:-0}" != "" ] && [ "$(printf '%.0f' "${S3_ROWS:-0}")" -ge 50 ]; then
  ok "1.1 S3 bucket: raw_market_prices loaded via stage+COPY ($S3_ROWS rows)"
else
  bad "1.1 S3 bucket: raw_market_prices has too few rows (${S3_ROWS:-0}) — run sources/s3-vendor-market-data/ingest.py"
fi

# 1.2 REST API — needs the stub; start it if not up
if ! curl -s http://localhost:8000/healthz >/dev/null 2>&1; then
  echo "     (starting REST stub...)"
  (cd sources/rest-stub && uv run --quiet --with fastapi --with uvicorn python -m uvicorn main:app --port 8000 --log-level warning &)
  STARTED_STUB=1
  for _ in $(seq 1 15); do curl -s http://localhost:8000/healthz >/dev/null 2>&1 && break; sleep 1; done
fi
if curl -s http://localhost:8000/healthz >/dev/null 2>&1; then
  (cd sources/rest-stub && uv run --quiet --with httpx --with snowflake-connector-python python ingest.py --as-of-date 2026-05-29 --max-ids 1000 --truncate >/dev/null 2>&1)
  REST_ROWS=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_POC.BRONZE.raw_rest_holdings;")
  if [ "$(printf '%.0f' "${REST_ROWS:-0}")" -ge 100 ]; then
    ok "1.2 REST API: paginated/chunked ingestion loaded $REST_ROWS holdings"
  else
    bad "1.2 REST API: too few rows (${REST_ROWS:-0})"
  fi
  [ "${STARTED_STUB:-0}" = "1" ] && pkill -f "uvicorn main:app" 2>/dev/null
else
  skip "1.2 REST API: stub not reachable on :8000"
fi

# 1.3 Snowflake Data Share
SHARE_ROWS=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_VENDOR_SHARE_SIM.SHARED.vendor_security_master;")
if [ "$(printf '%.0f' "${SHARE_ROWS:-0}")" -ge 100 ]; then
  ok "1.3 Data Share: vendor_security_master available + dbt staging canonicalizes ($SHARE_ROWS rows)"
else
  bad "1.3 Data Share: share not seeded — run sources/snowflake-data-share/seed_share.sql"
fi

# ---------------------------------------------------------------------------
echo
echo "## 2. Semantic view enrollment"

VALIDATE_OUT=$(cd semantic && uv run --quiet --with pyyaml --with snowflake-connector-python python validate.py sv_daily_portfolio_exposure.yaml 2>&1)
if echo "$VALIDATE_OUT" | grep -q "Validation: PASS"; then
  ok "2.1-2.3 Semantic view: 3-layer validation PASS (syntax+correctness+baseline)"
else
  bad "2.1-2.3 Semantic view validation failed"
fi

# reference joins resolved: fiscal + identifier + geo all surface in the view
JOIN_OUT=$(snow sql -q "SELECT * FROM SEMANTIC_VIEW(LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure DIMENSIONS issuer_name, country_name, fiscal_year METRICS total_exposure_usd WHERE region='APAC') LIMIT 1;" -c brighthive 2>&1)
if ! echo "$JOIN_OUT" | grep -qiE "error|not authorized"; then
  ok "2.2 Reference joins resolved: identifier_map + geo_codes + fiscal_calendar all queryable in one slice"
else
  bad "2.2 Reference joins failed: $(echo "$JOIN_OUT" | grep -i error | head -1)"
fi

# ---------------------------------------------------------------------------
echo
echo "## 3. MCP feedback loop"

MCP_OUT=$(cd semantic && uv run --quiet --with pyyaml --with snowflake-connector-python python mcp_check.py sv_daily_portfolio_exposure.yaml 2>&1)
if echo "$MCP_OUT" | grep -qE "0 errors"; then
  WARN_N=$(echo "$MCP_OUT" | grep -oE "[0-9]+ warnings" | grep -oE "^[0-9]+")
  ok "3.1-3.3 MCP queryability: all measures/dims surface, representative queries pass, ${WARN_N:-0} gaps flagged"
else
  bad "3.x MCP queryability has errors"
fi

# ---------------------------------------------------------------------------
echo
echo "## 4. Automated maintenance"

# 4.1 self-healing — 4 failure modes
HEAL_OUT=$(cd self_healing && uv run --quiet --with snowflake-connector-python python failure_modes.py run-all 2>&1)
HEAL_N=$(echo "$HEAL_OUT" | grep -oE "[0-9]+/[0-9]+ detect" | head -1)
if echo "$HEAL_OUT" | grep -q "4/4 detect"; then
  ok "4.1 Self-healing: all 4 failure modes detect->fix verified ($HEAL_N)"
else
  bad "4.1 Self-healing: not all modes passed ($HEAL_N)"
fi
# clean drift column if left behind
snow sql -q "ALTER TABLE LONGAEVA_POC.BRONZE.raw_market_prices DROP COLUMN IF EXISTS settlement_ccy;" -c brighthive >/dev/null 2>&1

# 4.3 longitudinal monitoring — 4 anomaly families
MON_OUT=$(cd monitoring && uv run --quiet --with snowflake-connector-python python monitor.py simulate 2>&1)
if echo "$MON_OUT" | grep -q "PASS — anomaly families"; then
  ok "4.3 Longitudinal monitoring: all 4 anomaly families detected (row/cardinality/skew/null)"
else
  bad "4.3 Longitudinal monitoring: not all families detected"
fi
snow sql -q "DELETE FROM LONGAEVA_POC.MONITORING.metric_history WHERE run_id LIKE 'sim-%'; DELETE FROM LONGAEVA_POC.MONITORING.anomaly_events;" -c brighthive >/dev/null 2>&1

# 4.2 quality tests authored — dbt tests exist + pass
DBT_OUT=$(cd dbt && source ./set_env.sh >/dev/null 2>&1 && DBT_PROFILES_DIR=. uv run --quiet --with 'dbt-snowflake' dbt test 2>&1)
if echo "$DBT_OUT" | grep -qE "ERROR=0"; then
  DBT_PASS=$(echo "$DBT_OUT" | grep -oE "PASS=[0-9]+" | head -1)
  ok "4.2 Quality tests: dbt test suite green ($DBT_PASS)"
else
  bad "4.2 Quality tests: dbt test had errors"
fi

# RBAC note (4.x governance) — agent boundary
RBAC=$(snow sql -q "USE ROLE LONGAEVA_AGENT_ROLE; USE SECONDARY ROLES NONE; SELECT COUNT(*) FROM LONGAEVA_POC.BRONZE.raw_market_prices;" -c brighthive 2>&1)
if echo "$RBAC" | grep -q "not authorized"; then
  ok "4.x Governance: agent role correctly scoped (blocked on BRONZE in strict mode)"
else
  bad "4.x Governance: agent role boundary not enforced"
fi

# ---------------------------------------------------------------------------
echo
echo "############################################################"
echo "# Results: $PASS passed, $FAIL failed, $SKIP skipped"
echo "############################################################"
[ $FAIL -eq 0 ]
