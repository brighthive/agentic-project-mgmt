---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "trial"
title: "Snowflake Standards — Longaeva PoC + financial-services template"
audience: "BrightHive engineers, Longaeva data team, anyone provisioning a financial-services PoC"
purpose: "Opinionated, repeatable Snowflake setup. Codifies what we did right, fixes what's drifting, and levels up the data to look like a real bank/asset-manager workload."
last_reviewed: "2026-06-17"
account: "bfddsko-dua97555 (BOA26592)"
database: "LONGAEVA_POC"
status: "draft — open for review, then promoted to canonical for FS engagements"
---

# Snowflake Standards — Longaeva PoC + financial-services template

> Read this top-to-bottom before you create another schema, role, or table in any financial-services PoC. The current `LONGAEVA_POC` is the reference implementation. Where it drifts from the standard, this doc flags it explicitly and tracks the cleanup in §10.

## TL;DR

| | |
|---|---|
| **Account** | `bfddsko-dua97555` (alias `BOA26592`) |
| **Canonical database** | `LONGAEVA_POC` — 5 layers + monitoring |
| **Layers** | BRONZE · SILVER · GOLD · REF · SEMANTIC · MONITORING |
| **Roles** | `LONGAEVA_POC_ROLE` (data owner) · `LONGAEVA_AGENT_ROLE` (read-only agent surface) |
| **Warehouse** | `POC_WH` X-Small, auto-suspend 60s, query-acceleration on |
| **Connection** | `snow -c brighthive` (LONGAEVA_POC_ROLE) · `snow -c brighthive-admin` (ACCOUNTADMIN) |
| **Honest state** | Foundation correct; row counts toy-scale; monitoring tables empty; governance policies absent |

---

## 1. Database & schema layout (canonical)

```
LONGAEVA_POC
├── BRONZE/              raw vendor drops — stages + raw tables
├── SILVER/              staging models — canonical types, source-of-truth granular grain
├── GOLD/                business-ready marts — denormalized, query-shaped
├── REF/                 reference data — identifiers, calendars, classifications
├── SEMANTIC/            semantic views — Atlas-shaped YAML, downstream consumer interface
├── MONITORING/          metric_history + anomaly_events (BrightHive monitoring)
└── PUBLIC/              empty in standard — DROP any orphan tables here

LONGAEVA_VENDOR_SHARE_SIM  ← simulates an inbound Snowflake Data Share (stays separate)
```

### Naming rules (HARD)

| Object | Pattern | Example |
|---|---|---|
| Database | `<CLIENT>_<ENV>` | `LONGAEVA_POC`, `ACME_BANK_DEV` |
| Schema | `<LAYER>` (UPPERCASE, no prefix) | `BRONZE`, `SILVER`, `GOLD`, `REF`, `SEMANTIC` |
| BRONZE table | `RAW_<SOURCE>_<ENTITY>` | `RAW_BLOOMBERG_HOLDINGS`, `RAW_S3_MARKET_PRICES` |
| SILVER staging | `STG_<ENTITY>` | `STG_HOLDINGS_SNAPSHOT`, `STG_SECURITY_PRICES` |
| SILVER intermediate | `INT_<ENTITY>` | `INT_ENRICHED_HOLDINGS` |
| GOLD mart | `MART_<DOMAIN>` or `DP_<DOMAIN>` (data product) | `MART_DAILY_PORTFOLIO_EXPOSURE`, `DP_REGIONAL_EXPOSURE_DAILY` |
| REF table | `<ENTITY>` (no prefix) | `IDENTIFIER_MAP`, `FISCAL_CALENDAR` |
| Semantic view | `SV_<GRAIN>_<DOMAIN>` | `SV_DAILY_PORTFOLIO_EXPOSURE` |
| Stage | `<KIND>_<VENDOR>_<DOMAIN>` | `S3_VENDOR_MARKET_DATA`, `GCS_BLOOMBERG_PRICES` |
| File format | `FF_<TYPE>_<VENDOR>` | `FF_CSV_VENDOR`, `FF_PARQUET_BLOOMBERG` |

**Disallowed**: `TEST_*`, `TMP_*`, `_BACKUP`, dated suffixes (`_20260615`), personal user prefixes (`KURI_*`).

### Required columns per layer

| Layer | Required columns on every fact-shaped table |
|---|---|
| BRONZE | `_INGESTED_AT TIMESTAMP_NTZ`, `_SOURCE_FILE TEXT`, `_SOURCE_ROW_NUM NUMBER`, `_BATCH_ID TEXT` |
| SILVER | `AS_OF_DATE DATE`, `AS_OF_TIME TIMESTAMP_NTZ`, `SOURCE_SYSTEM TEXT`, `QUALITY_FLAG TEXT` |
| GOLD | `AS_OF_DATE DATE`, `BUILD_RUN_ID TEXT`, `BUILD_TS TIMESTAMP_NTZ` |
| REF | `EFFECTIVE_FROM DATE`, `EFFECTIVE_TO DATE`, `IS_ACTIVE BOOLEAN` (SCD-2 by default) |

SILVER has these today on enriched_holdings + corporate_actions + prices. **Drift**: BRONZE tables don't carry `_INGESTED_AT` or `_BATCH_ID` consistently — fix in §10.

---

## 2. Roles & access (HARD principle: agent role ≠ data role)

```
ACCOUNTADMIN
   │
   ├── SYSADMIN
   │     └── LONGAEVA_POC_ROLE        ← data owner, full CRUD on LONGAEVA_POC
   │           └── LONGAEVA_AGENT_ROLE  ← read-only on GOLD + REF + SEMANTIC; NO BRONZE/SILVER
   │
   └── SECURITYADMIN
         └── USERADMIN
```

### Rules

1. **No human ever runs as `LONGAEVA_AGENT_ROLE`**. It exists for the MCP / BrightAgent service identity only. If you're typing SQL, use `LONGAEVA_POC_ROLE` or `ACCOUNTADMIN`.
2. **Agents are clamped via `USE SECONDARY ROLES NONE`** at every session start — without this, ACCOUNTADMIN leaks through inheritance and the boundary test is fake. The dbt agent's connection wrapper enforces this; verify with `snow sql -q "SHOW SECONDARY ROLES" -c brighthive`.
3. **No PAT, key, or password in this database**. Service credentials live in AWS Secrets Manager and are surfaced via Snowflake EXTERNAL ACCESS integrations only.
4. **One role per workload, never per person**. Adding a new engineer? They get `LONGAEVA_POC_ROLE` via group membership, not a personal role.
5. **GRANT-by-future, not by-table**. Use `GRANT SELECT ON FUTURE TABLES IN SCHEMA <S> TO ROLE <R>` so newly created tables inherit policy without manual re-grant.

### The agent's read-only surface (canonical)

```sql
-- Run as ACCOUNTADMIN, or as the schema owner.
GRANT USAGE ON DATABASE LONGAEVA_POC TO ROLE LONGAEVA_AGENT_ROLE;
GRANT USAGE ON SCHEMA LONGAEVA_POC.GOLD     TO ROLE LONGAEVA_AGENT_ROLE;
GRANT USAGE ON SCHEMA LONGAEVA_POC.REF      TO ROLE LONGAEVA_AGENT_ROLE;
GRANT USAGE ON SCHEMA LONGAEVA_POC.SEMANTIC TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA LONGAEVA_POC.GOLD     TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA LONGAEVA_POC.REF      TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA LONGAEVA_POC.SEMANTIC TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON ALL SEMANTIC VIEWS IN SCHEMA LONGAEVA_POC.SEMANTIC TO ROLE LONGAEVA_AGENT_ROLE;
-- Future grants:
GRANT SELECT ON FUTURE TABLES         IN SCHEMA LONGAEVA_POC.GOLD     TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON FUTURE TABLES         IN SCHEMA LONGAEVA_POC.REF      TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON FUTURE SEMANTIC VIEWS IN SCHEMA LONGAEVA_POC.SEMANTIC TO ROLE LONGAEVA_AGENT_ROLE;
-- Explicit denies (writes, raw layers):
-- Snowflake doesn't have DENY; the absence of GRANT is the deny. Verify via:
--   USE ROLE LONGAEVA_AGENT_ROLE; USE SECONDARY ROLES NONE;
--   SELECT * FROM BRONZE.RAW_REST_HOLDINGS LIMIT 1;  -- expect "does not exist or not authorized"
```

---

## 3. Warehouses & cost discipline

| Warehouse | Size | Auto-suspend | Auto-resume | Query accel | Purpose |
|---|---|---|---|---|---|
| `POC_WH` | X-Small | 60s | true | on (scale 2) | Demo + interactive analyst queries |
| `POC_LOAD_WH` *(MISSING — add)* | Small | 60s | true | off | Bulk loads, COPY INTO, MERGEs |
| `POC_DBT_WH` *(MISSING — add)* | X-Small | 120s | true | on (scale 2) | Scheduled dbt builds |
| `POC_AGENT_WH` *(MISSING — add)* | X-Small | 60s | true | on (scale 4) | BrightAgent / MCP queries — separate so spikes don't starve analysts |

**Rules**:
- One warehouse per workload class (load, transform, serve, agent). Never reuse the same WH for OLTP-shaped agent traffic + heavy backfill — the latency blowback will hide real issues.
- **`RESOURCE_MONITOR` mandatory on every warehouse**. Current state: POC_WH has `resource_monitor: null` — **gap**. Add one with monthly credit cap = expected + 50%.
- **Auto-suspend ≤ 120s**. Default Snowflake suggestion of 600s burns credits on idle.
- **No multi-cluster on PoC warehouses**. If you need MAX_CLUSTER_COUNT > 1, the PoC has graduated to production and that's a separate decision.

### Resource monitor template

```sql
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE RESOURCE MONITOR POC_RM
  WITH
    CREDIT_QUOTA = 200
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    NOTIFY_USERS = (KURICHINCA)
    TRIGGERS
      ON 75 PERCENT DO NOTIFY
      ON 90 PERCENT DO NOTIFY
      ON 100 PERCENT DO SUSPEND
      ON 110 PERCENT DO SUSPEND_IMMEDIATE;
ALTER WAREHOUSE POC_WH SET RESOURCE_MONITOR = POC_RM;
```

---

## 4. Reference data (REF) — the spine of bank-grade workloads

The REF schema is **load-bearing**. Without it the semantic layer can't ground identifiers, time periods, or classifications. Standard tables:

| Table | Required columns | Notes |
|---|---|---|
| `IDENTIFIER_MAP` | INTERNAL_ISSUER_ID, LEI, FIGI, CUSIP, ISIN, SEDOL, ISSUER_NAME, ISSUER_COHORT, PRIMARY_COUNTRY, PRIMARY_SECTOR, IS_ACTIVE, EFFECTIVE_FROM, EFFECTIVE_TO | SCD-2. **Add SEDOL** (currently missing). |
| `FISCAL_CALENDAR` | FISCAL_PERIOD_ID, ISSUER_COHORT, FISCAL_YEAR, FISCAL_QUARTER, PERIOD_START_DATE, PERIOD_END_DATE, IS_CURRENT | Currently 24 rows — **extend to 10 years × N cohorts** for bank-grade depth |
| `GEO_CODES` | COUNTRY_CODE, COUNTRY_NAME, REGION, SUB_REGION, ISO_NUMERIC_3, CUSTOM_GROUPING | Add ISO-3166-1 numeric; document `CUSTOM_GROUPING` semantics |
| `CLASSIFICATION_CODES` | CLASSIFICATION_ID, CLASSIFICATION_TYPE, CODE, LABEL, PARENT_ID, GRANULARITY_LEVEL | Currently 14 rows — for bank: full GICS (4 levels) + NAICS + SIC + LEI legal-form codes |
| `ASSET_CLASS_HIERARCHY` *(MISSING)* | ASSET_CLASS_CODE, ASSET_CLASS_NAME, PARENT_CODE, LEVEL, IS_DERIVATIVE | Equity / Fixed Income / FX / Commodity / Derivative branches |
| `COUNTERPARTY_MASTER` *(MISSING)* | COUNTERPARTY_ID, LEI, LEGAL_NAME, JURISDICTION, IS_REGULATED, PARENT_COUNTERPARTY_ID, CREDIT_RATING_LATEST | Required for any bank-grade lineage |
| `CURRENCY_RATES` *(MISSING)* | RATE_DATE, BASE_CCY, QUOTE_CCY, RATE_MID, RATE_BID, RATE_ASK, SOURCE | Daily, multi-source, with bid/ask spread |
| `INSTRUMENT_MASTER` *(MISSING)* | INSTRUMENT_ID, ISSUER_ID, ASSET_CLASS_CODE, INSTRUMENT_TYPE, ISSUE_DATE, MATURITY_DATE, COUPON_RATE, FACE_VALUE, CURRENCY, IS_CALLABLE, IS_PUTABLE | Bond / FI table — completely absent today |
| `BENCHMARK_INDICES` *(MISSING)* | INDEX_ID, INDEX_NAME, INDEX_PROVIDER, BASE_DATE, REBALANCE_FREQUENCY | For relative-value queries |
| `REGULATORY_CLASSIFICATIONS` *(MISSING)* | INTERNAL_ISSUER_ID, BASEL_RISK_WEIGHT, CRR_EXPOSURE_CLASS, IS_HQLA, IS_HVCRE, AS_OF_DATE | For RWA-shaped reporting |

---

## 5. Governance — masking, row-access, tags (currently absent)

Banks do not run without these. Current state: **none configured**. Standards:

### Tag taxonomy (mandatory)

```sql
USE ROLE ACCOUNTADMIN;
CREATE TAG IF NOT EXISTS LONGAEVA_POC.PUBLIC.CLASSIFICATION
  ALLOWED_VALUES 'PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED', 'PII', 'MNPI';
CREATE TAG IF NOT EXISTS LONGAEVA_POC.PUBLIC.OWNER
  ALLOWED_VALUES 'team:longaeva-data', 'team:longaeva-quant', 'team:longaeva-risk', 'team:brighthive-pipeline';
CREATE TAG IF NOT EXISTS LONGAEVA_POC.PUBLIC.RETENTION_DAYS;
CREATE TAG IF NOT EXISTS LONGAEVA_POC.PUBLIC.SOURCE_SYSTEM;
```

Every table created in BRONZE/SILVER/GOLD MUST be tagged with `CLASSIFICATION` + `OWNER` at create time.

### Masking policy (PII / identifier protection)

```sql
CREATE OR REPLACE MASKING POLICY LONGAEVA_POC.PUBLIC.MASK_PII_STRING AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN IS_ROLE_IN_SESSION('LONGAEVA_POC_ROLE') THEN val
    WHEN IS_ROLE_IN_SESSION('LONGAEVA_RISK_ROLE') THEN val
    ELSE '***REDACTED***'
  END;

-- Apply to any column that could carry PII
ALTER TABLE LONGAEVA_POC.REF.COUNTERPARTY_MASTER
  ALTER COLUMN LEGAL_NAME SET MASKING POLICY LONGAEVA_POC.PUBLIC.MASK_PII_STRING;
```

### Row-access policy (portfolio segregation)

```sql
CREATE OR REPLACE ROW ACCESS POLICY LONGAEVA_POC.PUBLIC.RAP_PORTFOLIO_SCOPE AS (portfolio_id STRING)
RETURNS BOOLEAN ->
  EXISTS (
    SELECT 1 FROM LONGAEVA_POC.PUBLIC.PORTFOLIO_ACCESS_GRANTS gag
    WHERE gag.portfolio_id = portfolio_id
      AND gag.role_name = CURRENT_ROLE()
      AND CURRENT_DATE BETWEEN gag.effective_from AND COALESCE(gag.effective_to, '9999-12-31')
  );

ALTER TABLE LONGAEVA_POC.SILVER.STG_HOLDINGS_SNAPSHOT
  ADD ROW ACCESS POLICY LONGAEVA_POC.PUBLIC.RAP_PORTFOLIO_SCOPE ON (PORTFOLIO_ID);
```

This is what makes the RBAC scenario in `UAT_GUIDE.md` Scenario 12 actually mean something.

---

## 6. Data Quality Monitoring (DQM) — Snowflake-native, not yet used

Snowflake ships [Data Quality Monitoring functions](https://docs.snowflake.com/en/user-guide/data-quality-monitoring). Standard rules per layer:

| Layer | DMF | Threshold |
|---|---|---|
| BRONZE.RAW_* | `SNOWFLAKE.CORE.NULL_COUNT` on every NOT-NULL-intended col | alert if delta > 5% vs trailing 7d |
| SILVER.STG_* | `SNOWFLAKE.CORE.ROW_COUNT` daily | alert if delta > 20% vs trailing 7d |
| SILVER.STG_* | `SNOWFLAKE.CORE.UNIQUE_COUNT` on natural key | alert if duplicates > 0 |
| SILVER.STG_* | `SNOWFLAKE.CORE.FRESHNESS` on `AS_OF_TIME` | alert if > 25 hours stale |
| GOLD.MART_* | Custom DMF: row count == sum(SILVER source rows) ± 0% | hard fail |
| REF.* | `SNOWFLAKE.CORE.NULL_COUNT` = 0 on every column | hard fail |

Wire them via `ALTER TABLE ... SET DATA_METRIC_FUNCTION` — Snowflake runs them on schedule, BrightAgent reads results from `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS`. This is the **native** path; our `MONITORING.METRIC_HISTORY` table is the BrightHive overlay.

---

## 7. Retention, time-travel, change tracking

| Setting | Default in account | Standard for FS PoC | Rationale |
|---|---|---|---|
| `DATA_RETENTION_TIME_IN_DAYS` (table) | 1 | 7 (BRONZE/SILVER), 30 (GOLD/REF), 0 (MONITORING) | Banks audit data movement; 1 day is not enough |
| `MAX_DATA_EXTENSION_TIME_IN_DAYS` | 14 | 90 | Time-travel headroom |
| `CHANGE_TRACKING` | off | **on** for all SILVER + GOLD | Required for CDC streams; cheap |
| Fail-safe | 7 days (perma) | inherit | Snowflake-controlled, not a knob |

Apply via:
```sql
ALTER TABLE LONGAEVA_POC.SILVER.STG_HOLDINGS_SNAPSHOT
  SET DATA_RETENTION_TIME_IN_DAYS = 7, CHANGE_TRACKING = TRUE;
```

---

## 8. Stages, file formats, COPY discipline

Current state: `S3_VENDOR_CORP_ACTIONS`, `S3_VENDOR_MARKET_DATA` (both INTERNAL stages — fine for demo, swap to EXTERNAL with STORAGE INTEGRATION for prod). `FF_CSV_VENDOR` + `FF_PARQUET_VENDOR` defined.

Standards:

1. **One stage per vendor × source-type combination**. Never reuse `S3_VENDOR_*` across vendors.
2. **Always use STORAGE INTEGRATION**, never inline credentials. Required:
   ```sql
   CREATE STORAGE INTEGRATION S3_VENDOR_BLOOMBERG
     TYPE = EXTERNAL_STAGE STORAGE_PROVIDER = S3
     STORAGE_AWS_ROLE_ARN = '<role>' STORAGE_ALLOWED_LOCATIONS = ('s3://vendor-bloomberg/');
   ```
3. **COPY INTO MUST use named file format**, never inline. The format is the contract.
4. **COPY INTO MUST track lineage** via `METADATA$FILENAME`, `METADATA$FILE_ROW_NUMBER`:
   ```sql
   COPY INTO BRONZE.RAW_BLOOMBERG_HOLDINGS (PAYLOAD, _SOURCE_FILE, _SOURCE_ROW_NUM, _INGESTED_AT, _BATCH_ID)
   FROM (
     SELECT $1, METADATA$FILENAME, METADATA$FILE_ROW_NUMBER, CURRENT_TIMESTAMP, '<run_id>'
     FROM @BRONZE.S3_VENDOR_BLOOMBERG
   )
   FILE_FORMAT = (FORMAT_NAME = BRONZE.FF_PARQUET_BLOOMBERG)
   ON_ERROR = 'ABORT_STATEMENT';
   ```
5. **`ON_ERROR = 'ABORT_STATEMENT'` is the default**. Use `CONTINUE` only after explicit sign-off in the loader spec.

---

## 9. Enhancement plan — toward real bank/asset-manager workloads

The current PoC is **shape-correct but toy-scale**. To turn it into a defensible "this is what a real bank looks like" demo, the following gaps need closing. Ordered by leverage.

### 9.1 Volume & breadth

| Today | Bank-grade | Lift |
|---|---|---|
| 200 issuers | 30k–50k | Re-seed `IDENTIFIER_MAP` from a public LEI dump (GLEIF) + assign synthetic FIGI/CUSIP |
| 1 portfolio × 174k holdings rows | 50–500 portfolios × 5M+ rows | Generate by sampling holdings across issuer cohorts |
| Equity only | Equity + FI bonds + FX + derivatives | Add `INSTRUMENT_MASTER` w/ bond/option/swap instrument types |
| 24 fiscal calendar rows | 10 yr × 4 q × 5 cohorts = 200 | Generator script |
| No corporate actions data | 100k+ events across 5 yr | Synthetic dividend/split/spinoff series |

### 9.2 Domain depth (new tables)

These need to be added to `REF` + `SILVER` to make queries feel real:

| Table | Schema | Why it matters |
|---|---|---|
| `INSTRUMENT_MASTER` | REF | A bank doesn't have positions, it has instruments holding positions |
| `COUNTERPARTY_MASTER` | REF | Bilateral exposure, settlement risk, AML chain |
| `CURRENCY_RATES` | REF | Multi-currency P&L is the default, not an edge case |
| `BENCHMARK_INDICES` | REF | "Performance vs benchmark" is the most-asked question |
| `REGULATORY_CLASSIFICATIONS` | REF | Basel III risk weights, HQLA flags, CRR exposure classes |
| `STG_TRANSACTION_TAPE` | SILVER | Trades, not just positions — required for cash flow, turnover, slippage |
| `STG_DERIVATIVE_TERMS` | SILVER | Strike, expiry, underlying, multiplier, payoff |
| `STG_RISK_METRICS_DAILY` | SILVER | VaR, ES, duration, DV01, convexity, spread duration, delta, gamma, vega |
| `MART_LIMIT_USAGE` | GOLD | "Are we within concentration / exposure / counterparty / sector limits?" |
| `MART_STRESS_SCENARIOS` | GOLD | Parallel shift, twist, FX shock, equity drawdown scenarios |
| `MART_CASH_LADDER` | GOLD | Next-N-days settlement obligations |
| `MART_REGULATORY_REPORTING` | GOLD | RWA buckets, LCR/NSFR-shaped numerators/denominators |

### 9.3 New semantic views (Atlas-shaped)

| Semantic view | Grain | Primary metrics |
|---|---|---|
| `SV_DAILY_PORTFOLIO_EXPOSURE` ✅ exists | portfolio × asset_class × geo × sector × day | total_exposure_usd, weight |
| `SV_DAILY_RISK_METRICS` | portfolio × instrument × day | var_95_1d, es_95_1d, duration, dv01, delta |
| `SV_TRANSACTION_TAPE` | trade × day | notional_usd, slippage_bps, commission_bps |
| `SV_LIMIT_USAGE` | portfolio × limit_type × day | utilization_pct, headroom_usd, breach_count |
| `SV_COUNTERPARTY_EXPOSURE` | counterparty × portfolio × day | gross_exposure_usd, net_exposure_usd, settlement_pending |
| `SV_REGULATORY_REPORTING` | portfolio × reg_class × day | rwa_usd, hqla_eligible_usd, lcr_inflow_usd |
| `SV_BENCHMARK_RELATIVE` | portfolio × benchmark × day | active_weight, tracking_error_bps, information_ratio |

Each becomes a UAT scenario for Scenario 4 (QC), Scenario 5 (build), and Scenario 6 (monitor).

### 9.4 Operational depth

- **Streams + Tasks**: every BRONZE table gets a `STREAM`; every SILVER staging model is built by a `TASK` reading the stream. Today it's all SQL scripts.
- **Snowpark Python procedures** for the risk math: VaR, ES, duration. Today these are imported as columns; bank-grade demands recomputation in-warehouse.
- **External functions** for AWS Bedrock embedding calls — already exists in BrightAgent path, mirror the pattern for Snowflake-native enrichment.
- **Cortex Functions**: use `SNOWFLAKE.CORTEX.COMPLETE` for in-SQL LLM enrichment (e.g., classify a free-text trade note).
- **Notebooks**: spin up a Snowflake Notebook with `SV_DAILY_PORTFOLIO_EXPOSURE` queries pre-loaded so non-engineer analysts can prove the semantic view to themselves without writing SQL.

---

## 10. Drift from standard — what to fix in `LONGAEVA_POC` today

Snowflake audit (`snow -c brighthive`, 2026-06-17):

| Drift | Severity | Fix |
|---|---|---|
| `BRONZE.RAW_CORPORATE_ACTIONS` has 0 rows but is referenced by SILVER.STG_CORPORATE_ACTIONS (which has 100 rows) | P1 | Re-seed BRONZE from the seed script or remove the BRONZE table; pick one source of truth |
| `MONITORING.METRIC_HISTORY` + `ANOMALY_EVENTS` both 0 rows on this Snowflake while cycle-21 claims live monitoring | P0 | Confirm whether monitoring is staging-only or whether this Snowflake needs a backfill; reconcile scorecard if not |
| `STG_VENDOR_RATINGS` + `STG_VENDOR_SECURITY_MASTER` show NULL row count (external tables not populated) | P1 | Load from `LONGAEVA_VENDOR_SHARE_SIM` or drop |
| `TEST_SEMANTIC_VIEW` + `TEST_SEMANTIC_VIEW_SCRIPT` in SEMANTIC schema | P2 | Drop before customer-facing UAT |
| `PUBLIC.ORDERS` (1 row, 0 bytes) — orphan from prior tutorial | P2 | Drop |
| `POC_WH` has `resource_monitor: null` | P1 | Attach `POC_RM` per §3 template |
| No tags on any object | P1 | Apply `CLASSIFICATION` + `OWNER` tags per §5 to every BRONZE/SILVER/GOLD/REF table |
| No masking or row-access policies | P1 | Apply §5 templates to `COUNTERPARTY_MASTER` (when created) and `STG_HOLDINGS_SNAPSHOT` |
| `DATA_RETENTION_TIME_IN_DAYS = 1` on every table | P2 | Bump to 7/30 per §7 |
| `CHANGE_TRACKING` off on all SILVER tables | P2 | Turn on per §7 |
| No `POC_LOAD_WH` / `POC_DBT_WH` / `POC_AGENT_WH` — everything runs on POC_WH | P1 | Create the workload-class warehouses per §3 |
| BRONZE tables missing `_INGESTED_AT` / `_SOURCE_FILE` / `_BATCH_ID` | P1 | Add columns; backfill where possible |
| `IDENTIFIER_MAP.SEDOL` column missing | P2 | Add to SCD-2 table |
| No `INSTRUMENT_MASTER`, `COUNTERPARTY_MASTER`, `CURRENCY_RATES`, `BENCHMARK_INDICES`, `REGULATORY_CLASSIFICATIONS` | P1 | Per §4 + §9.2 — these are the enhancement plan |

---

## 11. How to apply this doc

1. **Read** §1–§8 once. These are non-negotiable hygiene.
2. **Pick one drift row from §10**, open a Jira ticket under BH-526, branch, write SQL under `clients/trials/longaeva/sandbox/snowflake/standards/<NNN>_<name>.sql`, PR.
3. **For §9 enhancement work**, write a spec first (`docs/specs/`), then ticket, then code. Don't seed bank-grade data without a spec — the seed shape *is* the contract.
4. **All SQL is idempotent**. `CREATE OR REPLACE`, `CREATE IF NOT EXISTS`, `MERGE INTO`. No imperative scripts.
5. **All standards changes get reflected in `LONGAEVA_VENDOR_SHARE_SIM`** if they affect external-share-shaped data.
6. **The Notion `5 · Tech Inputs` page is a quick reference**, not the contract. This doc is the contract; Notion mirrors a TL;DR.

---

## 12. Verification — run this after any standards-related change

```bash
# context check
snow sql -q "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();" -c brighthive

# layer inventory
snow sql -q "
SELECT table_schema, table_type, COUNT(*) AS n_tables
FROM LONGAEVA_POC.information_schema.tables
WHERE table_schema NOT IN ('INFORMATION_SCHEMA','GC_SANDBOX')
GROUP BY 1,2 ORDER BY 1,2;" -c brighthive

# row counts on load-bearing tables
snow sql -q "
SELECT table_schema, table_name, row_count, bytes
FROM LONGAEVA_POC.information_schema.tables
WHERE table_schema IN ('BRONZE','SILVER','GOLD','REF','MONITORING')
ORDER BY 1,2;" -c brighthive

# RBAC boundary test
snow sql -q "USE ROLE LONGAEVA_AGENT_ROLE; USE SECONDARY ROLES NONE; SELECT * FROM LONGAEVA_POC.BRONZE.RAW_REST_HOLDINGS LIMIT 1;" -c brighthive
# expect: SQL access control error (object does not exist or not authorized)

# semantic view inventory (should not contain TEST_*)
snow sql -q "SHOW SEMANTIC VIEWS IN DATABASE LONGAEVA_POC;" -c brighthive

# resource monitor coverage
snow sql -q "SHOW WAREHOUSES;" -c brighthive | grep -i resource_monitor
# expect: all PoC warehouses have a resource_monitor value, not null
```

---

## References

- Snowflake semantic-view YAML spec: https://docs.snowflake.com/en/user-guide/views-semantic/semantic-view-yaml-spec
- Snowflake DMF docs: https://docs.snowflake.com/en/user-guide/data-quality-monitoring
- Atlas YAML contract: `clients/trials/longaeva/artifacts/atlas-semantic-view-spec.md`
- Sandbox seeds: `clients/trials/longaeva/sandbox/seed/seed.py`
- UAT scenarios that depend on these standards: `clients/trials/longaeva/UAT_GUIDE.md` (Sc-4 QC, Sc-6 monitoring, Sc-12 RBAC, Sc-13 governance)
