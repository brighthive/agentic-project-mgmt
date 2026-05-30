#!/usr/bin/env bash
# End-to-end smoke test for the Longaeva POC sandbox.
#
# Asserts the full pipeline:
#   1. Snowflake connection + sandbox context defaults
#   2. All medallion / ref / share schemas + tables exist (12 + 2)
#   3. Stages exist in BRONZE
#   4. YAML -> strip -> DDL emit -> Snowflake CREATE SEMANTIC VIEW round-trips
#   5. Semantic view is queryable via SEMANTIC_VIEW(...)
#   6. RBAC enforces agent boundary (5 sub-tests)
#
# Run: ./test_pipeline.sh
# Requires: snow CLI, uv, connection `brighthive` configured.

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PASS=0
FAIL=0
RESULTS=()

assert() {
  # assert <name> <command> <expected-substring-in-output>
  local name="$1" cmd="$2" expect="$3"
  local out
  out=$(eval "$cmd" 2>&1)
  if echo "$out" | grep -qF "$expect"; then
    echo "  ✅ $name"
    PASS=$((PASS + 1))
    RESULTS+=("PASS  $name")
  else
    echo "  ❌ $name"
    echo "     expected substring: $expect"
    echo "     actual output (last 5 lines):"
    echo "$out" | tail -5 | sed 's/^/       /'
    FAIL=$((FAIL + 1))
    RESULTS+=("FAIL  $name")
  fi
}

echo "==> 1. Connection + context defaults"
assert "default role is LONGAEVA_POC_ROLE" \
  "snow sql -q 'SELECT CURRENT_ROLE();' -c brighthive" \
  "LONGAEVA_POC_ROLE"
assert "default warehouse is POC_WH" \
  "snow sql -q 'SELECT CURRENT_WAREHOUSE();' -c brighthive" \
  "POC_WH"
assert "default database is LONGAEVA_POC" \
  "snow sql -q 'SELECT CURRENT_DATABASE();' -c brighthive" \
  "LONGAEVA_POC"

echo
echo "==> 2. All schemas + tables exist"
EXPECTED_TABLES_POC=12
EXPECTED_TABLES_SHARE=2

POC_COUNT=$(snow sql --format JSON -q "SELECT COUNT(*) AS C FROM LONGAEVA_POC.information_schema.tables WHERE table_schema IN ('BRONZE','SILVER','GOLD','REF');" -c brighthive 2>/dev/null | grep -oE '"C":[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+' || echo 0)
SHARE_COUNT=$(snow sql --format JSON -q "SELECT COUNT(*) AS C FROM LONGAEVA_VENDOR_SHARE_SIM.information_schema.tables WHERE table_schema = 'SHARED';" -c brighthive 2>/dev/null | grep -oE '"C":[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+' || echo 0)

assert "LONGAEVA_POC has $EXPECTED_TABLES_POC tables across BRONZE/SILVER/GOLD/REF" \
  "echo $POC_COUNT" \
  "$EXPECTED_TABLES_POC"
assert "LONGAEVA_VENDOR_SHARE_SIM has $EXPECTED_TABLES_SHARE tables in SHARED" \
  "echo $SHARE_COUNT" \
  "$EXPECTED_TABLES_SHARE"

echo
echo "==> 3. BRONZE stages exist"
STAGE_COUNT=$(snow sql --format JSON -q "SELECT COUNT(*) AS C FROM LONGAEVA_POC.information_schema.stages WHERE stage_schema = 'BRONZE';" -c brighthive 2>/dev/null | grep -oE '"C":[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+' || echo 0)
assert "2 stages exist in BRONZE" \
  "echo $STAGE_COUNT" \
  "2"

echo
echo "==> 4. YAML -> strip -> DDL -> Snowflake (round-trip)"
EMITTED=$(mktemp -t sv_emitted.XXXXXX.sql)
uv run --quiet --with pyyaml python semantic/strip_and_emit.py \
  semantic/sv_daily_portfolio_exposure.yaml --emit-ddl \
  > "$EMITTED" 2>/dev/null
if [ -s "$EMITTED" ]; then
  echo "  ✅ strip-and-emit produces non-empty DDL ($(wc -c < "$EMITTED" | tr -d ' ') bytes)"
  PASS=$((PASS + 1)); RESULTS+=("PASS  strip-and-emit produces non-empty DDL")
else
  echo "  ❌ strip-and-emit produces non-empty DDL"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  strip-and-emit produces non-empty DDL")
fi
assert "emitted DDL contains CREATE SEMANTIC VIEW" \
  "cat '$EMITTED'" \
  "CREATE OR REPLACE SEMANTIC VIEW sv_daily_portfolio_exposure"
assert "emitted DDL strips sdk_extensions" \
  "! grep -i 'sdk_extensions\|baseline_expectations\|agent_instructions' '$EMITTED' && echo CLEAN" \
  "CLEAN"
assert "emitted DDL applies cleanly to Snowflake" \
  "snow sql -f '$EMITTED' -c brighthive" \
  "successfully created"
rm -f "$EMITTED"

echo
echo "==> 5. Semantic view is queryable"
# Empty result set returns "No data"; non-empty returns rows. Either is success;
# a syntax error would print "SQL compilation error".
SV_OUT=$(snow sql -q 'SELECT * FROM SEMANTIC_VIEW(LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure DIMENSIONS region METRICS total_exposure_usd) LIMIT 1;' -c brighthive 2>&1)
if echo "$SV_OUT" | grep -qE "compilation error|invalid identifier"; then
  echo "  ❌ SEMANTIC_VIEW query plan accepted"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  SEMANTIC_VIEW query plan accepted")
else
  echo "  ✅ SEMANTIC_VIEW query plan accepted (empty/non-empty both valid)"
  PASS=$((PASS + 1)); RESULTS+=("PASS  SEMANTIC_VIEW query plan accepted")
fi
assert "DESCRIBE SEMANTIC VIEW returns dimensions" \
  "snow sql -q 'DESCRIBE SEMANTIC VIEW LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure;' -c brighthive" \
  "DIMENSION"

echo
echo "==> 6. Seed data + baseline_expectations enforcement"

# Helper for COUNT-style asserts
count() { snow sql --format JSON -q "$1" -c brighthive 2>/dev/null | grep -oE '"C":[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+'; }

EXP_COUNT=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure;")
if [ "${EXP_COUNT:-0}" -gt 100000 ]; then
  echo "  ✅ exposure mart has $EXP_COUNT rows (>100k)"
  PASS=$((PASS + 1)); RESULTS+=("PASS  exposure mart populated")
else
  echo "  ❌ exposure mart only has ${EXP_COUNT:-0} rows"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  exposure mart populated")
fi

# Baseline expectation 1: as_of_date NOT NULL
NULL_DATES=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure WHERE as_of_date IS NULL;")
if [ "${NULL_DATES:-1}" -eq 0 ]; then
  echo "  ✅ baseline_expectation: as_of_date_not_null"
  PASS=$((PASS + 1)); RESULTS+=("PASS  baseline as_of_date_not_null")
else
  echo "  ❌ baseline_expectation as_of_date_not_null: $NULL_DATES nulls"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  baseline as_of_date_not_null")
fi

# Baseline expectation 2: portfolio_id NOT NULL
NULL_PIDS=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure WHERE portfolio_id IS NULL;")
if [ "${NULL_PIDS:-1}" -eq 0 ]; then
  echo "  ✅ baseline_expectation: portfolio_id_not_null"
  PASS=$((PASS + 1)); RESULTS+=("PASS  baseline portfolio_id_not_null")
else
  echo "  ❌ portfolio_id has ${NULL_PIDS} nulls"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  baseline portfolio_id_not_null")
fi

# Baseline expectation 3: total_exposure_usd >= 0
NEG_EXP=$(count "SELECT COUNT(*) AS C FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure WHERE exposure_amount_usd < 0;")
if [ "${NEG_EXP:-1}" -eq 0 ]; then
  echo "  ✅ baseline_expectation: total_exposure_usd_non_negative"
  PASS=$((PASS + 1)); RESULTS+=("PASS  baseline non_negative_exposure")
else
  echo "  ❌ ${NEG_EXP} negative exposure rows"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  baseline non_negative_exposure")
fi

# Baseline expectation 4: distinct issuers per day >= 30
LOW_ISSUER_DAYS=$(count "SELECT COUNT(*) AS C FROM (SELECT as_of_date, COUNT(DISTINCT internal_issuer_id) AS n FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure GROUP BY as_of_date HAVING n < 30);")
if [ "${LOW_ISSUER_DAYS:-1}" -eq 0 ]; then
  echo "  ✅ baseline_expectation: distinct_issuers_minimum_30 (per day)"
  PASS=$((PASS + 1)); RESULTS+=("PASS  baseline distinct_issuers_minimum_30")
else
  echo "  ❌ ${LOW_ISSUER_DAYS} days with <30 distinct issuers"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  baseline distinct_issuers_minimum_30")
fi

# Semantic view returns real (non-empty) results post-seed
SV_REGIONS=$(snow sql --format JSON -q "SELECT COUNT(*) AS C FROM SEMANTIC_VIEW(LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure DIMENSIONS region METRICS total_exposure_usd);" -c brighthive 2>/dev/null | grep -oE '"C":[[:space:]]*[0-9]+' | head -1 | grep -oE '[0-9]+')
if [ "${SV_REGIONS:-0}" -ge 4 ]; then
  echo "  ✅ semantic view returns real data ($SV_REGIONS regions)"
  PASS=$((PASS + 1)); RESULTS+=("PASS  semantic view returns real data")
else
  echo "  ❌ semantic view returned only ${SV_REGIONS:-0} regions"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  semantic view returns real data")
fi

echo
echo "==> 7. RBAC: agent role boundary (strict mode, no secondary-role leak)"
STRICT="USE ROLE LONGAEVA_AGENT_ROLE; USE SECONDARY ROLES NONE;"

AGENT_OUT=$(snow sql -q "$STRICT SELECT * FROM SEMANTIC_VIEW(LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure DIMENSIONS region METRICS total_exposure_usd) LIMIT 1;" -c brighthive 2>&1)
if echo "$AGENT_OUT" | grep -qE "Insufficient privileges|not authorized|compilation error"; then
  echo "  ❌ agent CAN query semantic view"
  FAIL=$((FAIL + 1)); RESULTS+=("FAIL  agent CAN query semantic view")
else
  echo "  ✅ agent CAN query semantic view"
  PASS=$((PASS + 1)); RESULTS+=("PASS  agent CAN query semantic view")
fi
assert "agent BLOCKED on BRONZE" \
  "snow sql -q \"$STRICT SELECT COUNT(*) FROM LONGAEVA_POC.BRONZE.raw_market_prices;\" -c brighthive" \
  "does not exist or not authorized"
assert "agent BLOCKED on SILVER" \
  "snow sql -q \"$STRICT SELECT COUNT(*) FROM LONGAEVA_POC.SILVER.stg_security_prices;\" -c brighthive" \
  "does not exist or not authorized"
assert "agent BLOCKED on vendor share" \
  "snow sql -q \"$STRICT SELECT COUNT(*) FROM LONGAEVA_VENDOR_SHARE_SIM.SHARED.vendor_security_master;\" -c brighthive" \
  "does not exist or not authorized"
assert "agent BLOCKED on writes (INSERT into GOLD)" \
  "snow sql -q \"$STRICT INSERT INTO LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure(as_of_date, portfolio_id, internal_issuer_id, instrument_id) VALUES (CURRENT_DATE(), 'P-1', 'I-1', 'X-1');\" -c brighthive" \
  "Insufficient privileges"

echo
echo "============================================================"
echo "Results: $PASS passed, $FAIL failed"
echo "============================================================"
[ $FAIL -eq 0 ]
