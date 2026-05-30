# Longaeva POC — Snowflake sandbox

Pre-trial sandbox that mirrors the shape Longaeva will provision on Days 1–2 of the [POC](../overview.md). Lets Brighthive's `SnowflakeConnection` factory, schema introspection, semantic-view scaffolder, and dbt-source generator get exercised against real Snowflake objects **before** the trial starts.

DDL only — no seed data. Seeding waits for Longaeva's actual sample files during the trial.

Tracked under epic **BH-526** (pre-trial engineering gaps).

> **Fidelity tracker**: see [`FIDELITY.md`](FIDELITY.md) for what's high-fidelity vs. thin in this simulation, and the prioritized list of gaps we're closing next. Update it as work lands.

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
├── seed/
│   └── seed.py                            ← synthetic data loader (~450k rows)
├── sources/
│   ├── s3-vendor-market-data/             Source Type 1: ingest.py (PUT/COPY/flag)
│   ├── rest-stub/                         Source Type 2: main.py (FastAPI) + ingest.py
│   └── snowflake-data-share/              Source Type 3: seed_share.sql + dbt staging
├── orchestration/
│   └── longaeva_dagster/                  Dagster asset graph over the full ELT pipeline
├── self_healing/
│   └── failure_modes.py                   4 failure modes: detect→diagnose→surgical fix
├── monitoring/
│   ├── 00_monitoring_ddl.sql              metric_history + anomaly_events tables
│   └── monitor.py                         longitudinal anomaly detection (4 families)
├── test_pipeline.sh                       infra/DDL/dbt/RBAC smoke test (27/27)
└── validate_poc.sh                        every PoC use case mapped to scorecard (10/10)
```

The semantic/ dir also holds `strip_and_emit.py` (YAML→DDL), `validate.py`
(3-layer harness), and `mcp_check.py` (queryability + gap detection).

## Seeding

```bash
uv run --with 'snowflake-connector-python[pandas]' --with pandas --with numpy \
  python seed/seed.py --reset
# ~30s; deterministic (RNG_SEED=42)
# Generates: 25 countries, 14 classifications, 24 fiscal periods, 200 issuers,
#   50,400 prices, 174,384 holdings + exposures, 100 corp actions, 49,392 risk rows
# Total: ~450k rows
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

Run the end-to-end smoke test:

```bash
./test_pipeline.sh
# Expect: 17/17 passing
```

Covers: connection defaults, all 14 tables, stages, full strip-and-emit round-trip
(YAML → strip SDK fields → emit DDL → apply → compile success), semantic-view
queryability, and the RBAC agent-boundary matrix (5 sub-tests in strict mode).

Manual spot-checks:

```bash
snow sql -q "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();"
# Expect: LONGAEVA_POC_ROLE / POC_WH / LONGAEVA_POC

snow sql -q "DESCRIBE SEMANTIC VIEW LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure;"

# Re-emit + apply DDL from YAML (matches Longaeva's deploy pipeline exactly)
uv run --with pyyaml python semantic/strip_and_emit.py \
  semantic/sv_daily_portfolio_exposure.yaml --apply
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
