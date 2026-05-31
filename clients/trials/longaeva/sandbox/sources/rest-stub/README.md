# Source Type 2 — Paginated REST API

Stand-in for a vendor REST endpoint that delivers data partitioned by date, with batched ID lookups against Longaeva's instrument universe (20–30k IDs).

DDL phase: stub directory only. The FastAPI implementation lands in a follow-up — it doesn't gate the Snowflake DDL.

## Snowflake landing target

| Object | Where |
|---|---|
| Landing table | `LONGAEVA_POC.BRONZE.raw_rest_holdings` |
| ID universe (20–30k IDs) | `LONGAEVA_POC.REF.identifier_map` |

DDL: [`../../snowflake/10_bronze.sql`](../../snowflake/10_bronze.sql) and [`../../snowflake/40_ref.sql`](../../snowflake/40_ref.sql).

## Eventual stub shape

A FastAPI app exposing endpoints that mirror real vendor APIs:

```
GET /v1/holdings?as_of_date=YYYY-MM-DD&page=N&page_size=M&ids=ID1,ID2,...
GET /v1/instruments?cohort=...&page=N
```

- Date-partitioned: `as_of_date` is required.
- Paginated: returns `{ data: [...], page, total_pages, next_cursor }`.
- Batched IDs: `ids` query param accepts up to 500 IDs per call. Universe of 20–30k IDs is chunked client-side.

## Lifecycle the ingestion agent must scaffold

1. **ID universe load** — read `REF.identifier_map` to get the active instrument list.
2. **Chunking** — split the 20–30k IDs into 500-ID batches.
3. **Parallel download** — fan out across batches, with retry + exponential backoff on 5xx.
4. **Date partitioning** — write to `BRONZE.raw_rest_holdings` with `as_of_date` set per call.
5. **dbt source YAML** — `bronze.raw_rest_holdings` + downstream staging model into `SILVER.stg_holdings_snapshot`.

## Verification (once stub exists)

```bash
uv run uvicorn main:app --reload &
curl 'http://localhost:8000/v1/holdings?as_of_date=2026-05-28&page=1' | jq '.data | length'
```
