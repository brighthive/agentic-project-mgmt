# Longaeva sandbox — dbt project

dbt project that produces intermediate SILVER joins and GOLD-layer **derived data products** downstream of the semantic-view contract defined in [`../semantic/sv_daily_portfolio_exposure.yaml`](../semantic/sv_daily_portfolio_exposure.yaml).

The semantic view itself reads from the seeded `LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure` (loaded by [`../seed/seed.py`](../seed/seed.py)). dbt builds *additional* data products on top — proving the path Grant described:

> "downstream compute engine that's able to work off these time series primitives to then create derivative time series products and statistics"

## Models

| Model | Schema | Materializes | Purpose |
|---|---|---|---|
| `int_enriched_holdings` | `SILVER` | table | Holdings joined to issuer + geo + fiscal_calendar; canonical join layer |
| `dp_regional_exposure_daily` | `GOLD` | table | Daily exposure rollup per region — time-series primitive |
| `dp_top_issuers_daily` | `GOLD` | table | Daily top-50 issuers (materialization of the YAML's `top_50_issuers` filter preset) |
| `dp_fiscal_quarter_exposure` | `GOLD` | table | Per-fiscal-quarter exposure trend respecting non-Jan-Dec cohorts |

## Tests

Schema tests (`not_null`, `unique`, `accepted_values`) plus three custom singular tests that mirror the YAML's `baseline_expectations`:

- `tests/exposure_non_negative.sql`        ↔ `baseline_expectations.universal.total_exposure_usd_non_negative`
- `tests/distinct_issuers_minimum_30.sql`  ↔ `baseline_expectations.author_supplied.distinct_issuers_minimum_30`
- `tests/exposure_present_every_business_day.sql` ↔ `baseline_expectations.author_supplied.exposure_present_every_business_day`

When the YAML's baseline_expectations evolve, regenerate the corresponding singular tests — the ratchet mechanism keeps dbt's contract aligned to the semantic-view spec.

## Run

```bash
cd dbt
source ./set_env.sh                 # exports SNOWFLAKE_* env from ~/.snowflake/config.toml
DBT_PROFILES_DIR=. uv run --with 'dbt-snowflake' dbt build
```

`dbt build` runs:
1. Source freshness (skipped — no freshness configured)
2. Models (4) — materialize as tables
3. Tests (31 schema + 3 singular = 34 total)

Expected: **34 passing, 1 warning** (the warning is `int_enriched_holdings.fiscal_period_id` having ~10k nulls; some seeded `as_of_date` values fall outside the 24-period seeded fiscal calendar — known gap, severity=warn).

## Schema-name override

Default dbt schema-prefixing concatenates the target's schema with the model's `+schema` config (so `target=SILVER + +schema=GOLD` becomes `SILVER_GOLD`). [`macros/generate_schema_name.sql`](macros/generate_schema_name.sql) overrides this to use the configured schema verbatim.
