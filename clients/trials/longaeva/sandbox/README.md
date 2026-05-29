# Longaeva POC — Snowflake sandbox

Pre-trial sandbox that mirrors the shape Longaeva will provision on Days 1–2 of the [POC](../overview.md). Lets Brighthive's `SnowflakeConnection` factory, schema introspection, semantic-view scaffolder, and dbt-source generator get exercised against real Snowflake objects **before** the trial starts.

DDL only — no seed data. Seeding waits for Longaeva's actual sample files during the trial.

Tracked under epic **BH-526** (pre-trial engineering gaps).

## Topology

```
ACCOUNT bfddsko-dua97555
├── ROLE        LONGAEVA_POC_ROLE
├── WAREHOUSE   POC_WH (XSMALL, auto-suspend 60s)
│
├── DATABASE LONGAEVA_POC
│   ├── BRONZE   raw_market_prices, raw_rest_holdings, raw_corporate_actions
│   │            + @s3_vendor_market_data, @s3_vendor_corp_actions stages
│   ├── SILVER   stg_security_prices, stg_holdings_snapshot, stg_corporate_actions
│   ├── GOLD     mart_daily_portfolio_exposure, mart_issuer_risk_summary
│   ├── REF      fiscal_calendar, identifier_map, geo_codes, classification_codes
│   └── SEMANTIC sv_daily_portfolio_exposure
│
└── DATABASE LONGAEVA_VENDOR_SHARE_SIM
    └── SHARED   vendor_security_master, vendor_ratings
```

## Layout

```
sandbox/
├── README.md                              ← this file
├── snowflake/                             ← idempotent DDL (run in order)
│   ├── 00_account.sql                     ACCOUNTADMIN: warehouse + role + DBs
│   ├── 10_bronze.sql                      stages, file formats, raw landing
│   ├── 20_silver.sql                      canonical time-series tables
│   ├── 30_gold.sql                        marts (semantic-view foundation)
│   ├── 40_ref.sql                         security master + calendar + codes
│   ├── 50_share_sim.sql                   simulated inbound Data Share DB
│   └── 60_semantic.sql                    Snowflake Semantic View
├── semantic/
│   └── sv_daily_portfolio_exposure.yaml   Longaeva-extended YAML spec
└── sources/
    ├── s3-vendor-market-data/README.md    Source Type 1 (S3 stage stand-in)
    ├── rest-stub/README.md                Source Type 2 (paginated REST)
    └── snowflake-data-share/README.md     Source Type 3 (Data Share sim)
```

## Run order

```bash
# Account-level (one-time, ACCOUNTADMIN)
snow sql -f snowflake/00_account.sql -c brighthive

# Then update ~/.snowflake/config.toml [connections.brighthive] with:
#   role = "LONGAEVA_POC_ROLE"
#   warehouse = "POC_WH"
#   database = "LONGAEVA_POC"
#   schema = "SILVER"

# Layer DDL (run with the role-bound connection)
for f in snowflake/{10,20,30,40,50,60}_*.sql; do
  snow sql -f "$f" -c brighthive
done
```

Idempotent: every statement uses `CREATE ... IF NOT EXISTS` or `CREATE OR REPLACE`. Re-runs are safe.

## Verification

```bash
snow sql -q "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();"
# Expect: LONGAEVA_POC_ROLE / POC_WH / LONGAEVA_POC

snow sql -q "
  SELECT table_schema, table_name
  FROM LONGAEVA_POC.information_schema.tables
  WHERE table_schema IN ('BRONZE','SILVER','GOLD','REF')
  ORDER BY 1,2;
"
# Expect: 12 tables

snow sql -q "DESCRIBE SEMANTIC VIEW LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure;"
# Expect: dimensions, facts, metrics, relationships rendered
```

## Mapping to POC scorecard

| POC scope | Sandbox artifact |
|---|---|
| 1.1 Ingestion — S3 | `BRONZE.@s3_vendor_market_data` + `raw_market_prices` |
| 1.2 Ingestion — REST | `BRONZE.raw_rest_holdings` + `REF.identifier_map` (20–30k capacity) |
| 1.3 Ingestion — Data Share | `LONGAEVA_VENDOR_SHARE_SIM.SHARED.*` |
| 2.x Semantic view enrollment | `semantic/sv_daily_portfolio_exposure.yaml` + `snowflake/60_semantic.sql` (golden reference) |
| 3.x MCP feedback loop | Out of scope here — needs Longaeva's MCP. Compile success is the prerequisite. |
| 4.x Self-healing / monitoring | Out of scope here — runs in BrightAgent. Sandbox provides the substrate. |
