# Source Type 1 — Vendor-managed S3 bucket

Stand-in for a real vendor S3 bucket. We use a Snowflake **internal stage** to test the same `COPY INTO` semantics without S3 credentials; swapping to a real S3 external stage later is a one-line DDL change.

## Snowflake objects

| Object | Where |
|---|---|
| Stage | `LONGAEVA_POC.BRONZE.@s3_vendor_market_data` |
| File format | `LONGAEVA_POC.BRONZE.ff_csv_vendor` |
| Landing table | `LONGAEVA_POC.BRONZE.raw_market_prices` |

DDL: [`../../snowflake/10_bronze.sql`](../../snowflake/10_bronze.sql).

## Expected file layout

```
@s3_vendor_market_data/
  yyyy=2026/mm=05/dd=28/
    market_prices_2026-05-28_001.csv
    market_prices_2026-05-28_002.csv
    completion.flag           ← presence signals batch ready
```

CSV header (matches `raw_market_prices`):

```
vendor_security_id,ticker,price_date,open_price,high_price,low_price,close_price,adj_close_price,volume,currency
```

## Lifecycle the ingestion agent must scaffold

1. **Stage upload** — `PUT file://<local>/*.csv @s3_vendor_market_data/yyyy=YYYY/mm=MM/dd=DD/`.
2. **Completion-file detection** — only `COPY INTO` after `completion.flag` lands. The agent should generate a Dagster sensor (or equivalent) that polls `LIST @s3_vendor_market_data/yyyy=.../mm=.../dd=...` for the flag.
3. **Lookback window** — re-process the last *N* days every run to capture late-arriving files. Default *N=7*.
4. **`COPY INTO`** — into `raw_market_prices`, with `source_file = METADATA$FILENAME` and `source_batch_id` derived from the partition path.
5. **dbt source YAML** — emit `sources.yml` for `bronze.raw_market_prices` and a downstream staging model that lifts vendor columns into the canonical `LONGAEVA_POC.SILVER.stg_security_prices` schema.

## Swap to real S3 later

Replace the stage definition in `10_bronze.sql`:

```sql
CREATE OR REPLACE STAGE s3_vendor_market_data
  URL = 's3://<vendor-bucket>/'
  STORAGE_INTEGRATION = <integration_name>
  FILE_FORMAT = ff_csv_vendor;
```

Everything downstream stays the same.
