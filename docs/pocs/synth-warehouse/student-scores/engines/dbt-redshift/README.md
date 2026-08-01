# dbt → Redshift

The dbt materialization of the canonical student matter-scores model
([`../../MODEL.md`](../../MODEL.md)) against Amazon Redshift. Scoped as it would
live in its own analytics-engineering repo.

```
dbt-redshift/
├── dbt_project.yml         ← project + seed config (reads ../../sources/*.csv)
├── profiles.yml            ← env-var-driven Redshift connection (no secrets)
├── packages.yml            ← dbt_utils (composite-key uniqueness test)
└── models/
    ├── staging/
    │   ├── _sources.yml            ← declares the seeded raw feeds
    │   ├── stg_schools.sql
    │   ├── stg_weekly_matter_scores.sql   ← regex-guarded cast surfaces the "n/a"
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
dbt-snowflake projects read. The three mart tables match
[`../../MODEL.md`](../../MODEL.md) exactly; only the Redshift type rendering
(`INTEGER`/`VARCHAR`/`DECIMAL(5,2)`) is dialect-specific.

## One dialect divergence from Snowflake

Redshift has no `TRY_CAST`. `stg_weekly_matter_scores` instead regex-guards the
cast (`matter_score ~ '^[0-9]+(\.[0-9]+)?$'`) so the planted `"n/a"` lands as
`NULL` rather than erroring the view. Same effect, different dialect — this is
exactly the kind of engine-specific detail the multi-engine sandbox exists to
exercise.

## Run it

Point the connection at a Redshift cluster via env vars — nothing is hardcoded:

```bash
export DBT_REDSHIFT_HOST=... DBT_REDSHIFT_USER=... DBT_REDSHIFT_PASSWORD=...
export DBT_REDSHIFT_DATABASE=student_scores
dbt deps          # install dbt_utils
dbt seed          # load the shared CSVs into raw
dbt run           # build staging views + mart tables
dbt test          # assert the XSD-contract keys
```

## Planted gap

`weekly_matter_scores.csv` carries one `"n/a"` `matter_score`. The seed leaves
that column un-typed and the staging cast regex-guards it, so the bad value
lands as `NULL` rather than failing the load. The mart's `weekly_matter_scores`
deliberately has **no** `not_null` test on `matter_score` — the NULL flows
through as drift for a data-quality skill to surface (see
[`../../MODEL.md`](../../MODEL.md) § "Planted defect").
