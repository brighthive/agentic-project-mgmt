# Longaeva PoC Sandbox

A complete, runnable recreation of Longaeva Partners' data stack — **Snowflake +
dbt + Dagster + a custom semantic-view/MCP layer** — built so BrightHive's agents
can be developed and validated against a known-good target **before** the 14-day
trial (epic [BH-526](https://brighthiveio.atlassian.net/browse/BH-526), starts
2026-06-15).

> **Status**: all 11 PoC use cases resolve against live Snowflake.
> `./validate_poc.sh` → **11/11**. `./test_pipeline.sh` → **27/27**.
> See [`ARCHITECTURE.md`](ARCHITECTURE.md) for diagrams, [`FIDELITY.md`](FIDELITY.md)
> for the build journal, [`../BRIGHTHIVE_GAPS.md`](../BRIGHTHIVE_GAPS.md) for the
> next-sprint plan.

## Why this exists

The sandbox is the **target**; BrightHive is the **agent that must hit it**. By
proving every PoC use case is resolvable here, the BrightHive product work
becomes "make the agent emit what the sandbox already validated" instead of
"figure out what correct looks like." That collapses trial risk.

## Quick start

Prereqs: `snow` CLI with a `brighthive` connection in `~/.snowflake/config.toml`
(account `bfddsko-dua97555`, role `LONGAEVA_POC_ROLE`, wh `POC_WH`, db
`LONGAEVA_POC`), `uv`, and network access to Snowflake.

```bash
cd clients/trials/longaeva/sandbox

# 1. (one-time) build the environment — idempotent
snow sql -f snowflake/00_account.sql -c brighthive          # ACCOUNTADMIN: wh + role + DBs
for f in snowflake/{10,20,30,40,50,60}_*.sql; do snow sql -f "$f" -c brighthive; done
snow sql -f snowflake/70_rbac.sql -c brighthive             # scoped agent role
snow sql -f monitoring/00_monitoring_ddl.sql -c brighthive  # monitoring tables

# 2. seed ~450k synthetic rows (deterministic, ~30s)
uv run --with 'snowflake-connector-python[pandas]' --with pandas --with numpy \
  python seed/seed.py --reset

# 3. prove it — every PoC use case
./validate_poc.sh        # 11/11

# 4. infra/contract smoke test
./test_pipeline.sh       # 27/27
```

## What's inside

```
sandbox/
├── README.md            ← you are here (DX entry point)
├── ARCHITECTURE.md      ← Mermaid diagrams: data flow, deploy, orchestration
├── FIDELITY.md          ← build journal + what's high-fidelity vs deferred
│
├── snowflake/           medallion DDL (00 account → 70 rbac)
├── seed/                synthetic data loader (~450k rows, RNG_SEED=42)
├── semantic/            extended YAML + strip_and_emit + validate (3-layer) + mcp_check
├── dbt/                 intermediate join + 3 GOLD data products + 41 tests
├── sources/             3 ingestion patterns: s3 / rest-stub / snowflake-data-share
├── orchestration/       Dagster asset graph over the full ELT pipeline
├── self_healing/        4 failure modes: detect → diagnose → surgical fix
├── monitoring/          longitudinal anomaly detection (4 families)
├── brighthive_adapter/  GAP-1 drop-in: BrightHive's WarehouseConnection ABC → live sandbox
│
├── validate_poc.sh      every PoC scorecard use case (11/11)
└── test_pipeline.sh     infra / DDL / strip-and-emit / dbt / RBAC (27/27)
```

## Topology

```
ACCOUNT bfddsko-dua97555
├── ROLE  LONGAEVA_POC_ROLE   ·   AGENT ROLE  LONGAEVA_AGENT_ROLE (scoped subset)
├── WAREHOUSE  POC_WH (XSMALL, auto-suspend 60s)
│
├── DATABASE LONGAEVA_POC
│   ├── BRONZE     raw_market_prices · raw_rest_holdings · raw_corporate_actions + @stages
│   ├── SILVER     stg_* (seeded) + int_enriched_holdings (dbt) + stg_vendor_* (dbt views)
│   ├── GOLD       mart_* (seeded) + dp_* data products (dbt)
│   ├── REF        fiscal_calendar · identifier_map · geo_codes · classification_codes
│   ├── SEMANTIC   sv_daily_portfolio_exposure
│   └── MONITORING metric_history · anomaly_events
│
└── DATABASE LONGAEVA_VENDOR_SHARE_SIM
    └── SHARED     vendor_security_master · vendor_ratings
```

## Run individual capabilities

```bash
# Semantic view: YAML → strip SDK → DDL → apply
uv run --with pyyaml python semantic/strip_and_emit.py \
  semantic/sv_daily_portfolio_exposure.yaml --apply

# 3-layer validation harness (syntax / correctness / baseline_expectations)
uv run --with pyyaml --with snowflake-connector-python \
  python semantic/validate.py semantic/sv_daily_portfolio_exposure.yaml

# MCP queryability + gap detection
uv run --with pyyaml --with snowflake-connector-python \
  python semantic/mcp_check.py semantic/sv_daily_portfolio_exposure.yaml

# Ingestion — S3 (generate drops + COPY)
(cd sources/s3-vendor-market-data && uv run --with snowflake-connector-python \
  python ingest.py --generate --days 3 && \
  uv run --with snowflake-connector-python python ingest.py --load --lookback 7)

# Ingestion — REST (start stub, then load)
(cd sources/rest-stub && uv run --with fastapi --with uvicorn \
  python -m uvicorn main:app --port 8000 &)
(cd sources/rest-stub && uv run --with httpx --with snowflake-connector-python \
  python ingest.py --as-of-date 2026-05-29 --max-ids 1000 --truncate)

# dbt — build data products + tests
(cd dbt && source ./set_env.sh && DBT_PROFILES_DIR=. \
  uv run --with dbt-snowflake dbt build)

# Self-healing — all 4 failure modes
(cd self_healing && uv run --with snowflake-connector-python \
  python failure_modes.py run-all)

# Monitoring — anomaly simulation (4 families)
(cd monitoring && uv run --with snowflake-connector-python \
  python monitor.py simulate)

# Dagster — full ELT asset graph (UI on :3000)
(cd orchestration && DAGSTER_HOME=$(mktemp -d) uv run --python 3.12 \
  --with 'dagster>=1.7,<1.9' --with dagster-webserver --with dbt-snowflake \
  --with snowflake-connector-python --with httpx --with pyyaml \
  dagster dev -m longaeva_dagster.definitions)

# BrightHive adapter — does our product plug in?
(cd brighthive_adapter && uv run --with snowflake-connector-python \
  python snowflake_connection.py)
```

## Mapping to the PoC scorecard

| PoC use case | Sandbox artifact | Validated |
|---|---|---|
| 1.1 S3 ingestion | `sources/s3-vendor-market-data/ingest.py` | ✅ |
| 1.2 REST ingestion | `sources/rest-stub/` | ✅ |
| 1.3 Snowflake Data Share | `sources/snowflake-data-share/` + `dbt/` staging | ✅ |
| 2.x Semantic view enrollment | `semantic/` (YAML + validate) | ✅ |
| 3.x MCP feedback loop | `semantic/mcp_check.py` (stand-in for theirs) | ✅ |
| 4.1 Self-healing | `self_healing/failure_modes.py` | ✅ |
| 4.2 Quality tests | `dbt/` test suite | ✅ |
| 4.3 Anomaly monitoring | `monitoring/monitor.py` | ✅ |
| 4.x Governance (RBAC) | `snowflake/70_rbac.sql` | ✅ |
| GAP-1 BrightHive integration | `brighthive_adapter/` | ✅ |

## Notes

- **Idempotent**: all DDL uses `CREATE ... IF NOT EXISTS` / `CREATE OR REPLACE`; seed uses `--reset`; ingestion COPY is load-metadata-aware.
- **Cost**: XSMALL warehouse, 60s auto-suspend. Seed + full validate is a few cents.
- **Deferred (not critical path)**: real S3 external stage and real Data Share are 1-line swaps from the internal-stage / second-DB stand-ins; Dagster is wired but OpenLineage export needs a backend URL. See [`FIDELITY.md`](FIDELITY.md).
