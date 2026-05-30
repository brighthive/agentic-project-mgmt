# Longaeva sandbox — Dagster orchestration

Dagster project that orchestrates the full ELT pipeline as an asset graph,
mirroring Grant's stack (Dagster + OpenLineage + dbt). The asset graph **is**
the lineage the self-healing and monitoring agents traverse.

## Asset graph

```
bronze_s3_market_prices ─┐
bronze_rest_holdings ────┤
vendor_share_seeded ─────┴─> dbt_build ─┬─> semantic_view_validated
                                        └─> anomaly_snapshot
```

| Asset | Group | What it runs |
|---|---|---|
| `bronze_s3_market_prices` | bronze | `sources/s3-vendor-market-data/ingest.py` (generate + COPY) |
| `bronze_rest_holdings` | bronze | `sources/rest-stub/ingest.py` (needs stub on :8000) |
| `vendor_share_seeded` | bronze | `sources/snowflake-data-share/seed_share.sql` |
| `dbt_build` | silver_gold | `dbt build` — int model + 3 data products + tests |
| `semantic_view_validated` | semantic | `semantic/validate.py` 3-layer harness (fails the run if invalid) |
| `anomaly_snapshot` | monitoring | `monitoring/monitor.py snapshot` |

## Run

Interactive (Dagster UI on :3000):

```bash
cd orchestration
# start the REST stub first (bronze_rest_holdings depends on it)
(cd ../sources/rest-stub && uv run --with fastapi --with uvicorn python -m uvicorn main:app --port 8000 &)

DAGSTER_HOME=$(mktemp -d) uv run --python 3.12 \
  --with 'dagster>=1.7,<1.9' --with dagster-webserver --with dbt-snowflake \
  --with snowflake-connector-python --with httpx --with pyyaml \
  dagster dev -m longaeva_dagster.definitions
```

Headless materialize (CI / smoke):

```bash
DAGSTER_HOME=$(mktemp -d) uv run --python 3.12 \
  --with 'dagster>=1.7,<1.9' --with dbt-snowflake \
  --with snowflake-connector-python --with httpx --with pyyaml \
  dagster asset materialize --select '*' -m longaeva_dagster.definitions
```

Verified end-to-end: all 7 assets materialize in dependency order, RUN_SUCCESS.

## OpenLineage

`definitions.py` wires OpenLineage export when `OPENLINEAGE_URL` is set (e.g. a
Marquez backend); absent, it no-ops so the project runs locally. The Dagster
asset graph is itself the lineage surface — the self-healing agent
(`../self_healing/failure_modes.py`) reads asset dependencies + run logs to
diagnose failures.

## Notes

- Pin **Python 3.12** + **Dagster 1.7–1.8**: Dagster's context type-hint
  validator rejects newer Python/Dagster combos with annotated `context` params.
  Assets here leave `context` unannotated to stay version-tolerant.
- A daily schedule (`daily_refresh`, 06:17 ET) mirrors a vendor daily cadence.
