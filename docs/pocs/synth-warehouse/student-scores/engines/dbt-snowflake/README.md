# dbt → Snowflake

The dbt materialization of the canonical student matter-scores model
([`../../MODEL.md`](../../MODEL.md)) against Snowflake. Scoped as it would live
in its own analytics-engineering repo.

```
dbt-snowflake/
├── dbt_project.yml         ← project + seed config (reads ../../sources/*.csv)
├── profiles.yml            ← env-var-driven Snowflake connection (no secrets)
├── packages.yml            ← dbt_utils (composite-key uniqueness test)
└── models/
    ├── staging/
    │   ├── _sources.yml            ← declares the seeded raw feeds
    │   ├── stg_schools.sql
    │   ├── stg_weekly_matter_scores.sql   ← TRY_CAST surfaces the planted "n/a"
    │   └── stg_monthly_matter_scores.sql
    └── marts/
        ├── _schema.yml             ← PK unique/not_null tests = the XSD contract
        ├── schools.sql
        ├── weekly_matter_scores.sql
        └── monthly_matter_scores.sql
```

## Same sources, same model

The shared CSVs in [`../../sources/`](../../sources/) land as dbt seeds
(`seed-paths: ["../../sources"]`) — the identical inputs the SSIS and
dbt-redshift projects read. The three mart tables match
[`../../MODEL.md`](../../MODEL.md) exactly; only the Snowflake type rendering
(`NUMBER`/`VARCHAR`/`NUMBER(5,2)`) is dialect-specific.

## Run it

Point the connection at a Snowflake account via env vars — nothing is hardcoded:

```bash
export DBT_SNOWFLAKE_ACCOUNT=... DBT_SNOWFLAKE_USER=...
export DBT_SNOWFLAKE_DATABASE=STUDENT_SCORES
dbt deps          # install dbt_utils
dbt seed          # load the shared CSVs into raw
dbt run           # build staging views + mart tables
dbt test          # assert the XSD-contract keys
```

## Planted gap

`weekly_matter_scores.csv` carries one `"n/a"` `matter_score`. The seed leaves
that column un-typed and `stg_weekly_matter_scores` does `TRY_CAST(... as
number(5,2))`, so the bad value lands as `NULL` rather than failing the load.
The mart's `weekly_matter_scores` deliberately has **no** `not_null` test on
`matter_score` — the NULL flows through as drift for a data-quality skill to
surface (see [`../../MODEL.md`](../../MODEL.md) § "Planted defect").
