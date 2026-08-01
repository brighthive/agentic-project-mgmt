# Canonical data model — defined once, materialized by every engine

This is the contract. Every engine project (`engines/ssis-sqlserver/`,
`engines/dbt-snowflake/`, `engines/dbt-redshift/`) materializes **exactly** these
three tables with **exactly** these columns, types, and nullability. Only the
SQL *dialect* that expresses each type changes per warehouse — the shape does
not.

## Tables

### `schools` — one row per high school

| Column | Logical type | Null? | PK | Notes |
|---|---|---|---|---|
| `school_id` | int | NO | ✅ | surrogate key |
| `school_name` | string(120) | NO | | |
| `state` | string(2) | NO | | 2-letter US state code — the "by state" key |
| `city` | string(80) | YES | | |
| `enrollment` | int | YES | | headcount |

### `weekly_matter_scores` — one row per school × ISO week

| Column | Logical type | Null? | PK | Notes |
|---|---|---|---|---|
| `school_id` | int | NO | ✅ | → `schools.school_id` |
| `iso_year` | int | NO | ✅ | ISO-8601 year |
| `iso_week` | int | NO | ✅ | ISO-8601 week (1–53) |
| `matter_score` | decimal(5,2) | NO | | national weekly index, 0.00–100.00 |
| `national_rank` | int | YES | | 1 = highest that week |

### `monthly_matter_scores` — one row per school × calendar month

| Column | Logical type | Null? | PK | Notes |
|---|---|---|---|---|
| `school_id` | int | NO | ✅ | → `schools.school_id` |
| `year` | int | NO | ✅ | calendar year |
| `month` | int | NO | ✅ | 1–12 |
| `matter_score` | decimal(5,2) | NO | | national monthly index, 0.00–100.00 |
| `national_rank` | int | YES | | 1 = highest that month |

## Type mapping per warehouse

The **same logical type** renders in each dialect as:

| Logical type | SQL Server / Synapse (SSIS) | Snowflake (dbt) | Redshift (dbt) |
|---|---|---|---|
| int | `INT` | `NUMBER(38,0)` | `INTEGER` |
| string(N) | `NVARCHAR(N)` | `VARCHAR(N)` | `VARCHAR(N)` |
| decimal(5,2) | `DECIMAL(5,2)` | `NUMBER(5,2)` | `DECIMAL(5,2)` |

The `.xsd` contracts in `contracts/` express these in SQL-neutral terms
(`sqlType` / `nullable` / `primaryKey` appinfo, per the loopcapital convention)
so both the SSIS destination mappings and the dbt `schema.yml` tests validate
against one source of truth.

## Source → table flow (identical across engines)

```
sources/schools.csv                → schools
sources/weekly_matter_scores.csv   → weekly_matter_scores
sources/monthly_matter_scores.csv  → monthly_matter_scores
```

Each engine reads the **same** three CSVs. No per-engine data forks — that's the
whole point: same input, same output, different pipeline.

## Planted defect (for a diagnostics / profiler skill to find)

`sources/weekly_matter_scores.csv` contains **one** row where `matter_score` is
delivered as free text (`"n/a"`) instead of a number, and **one** row with a
`national_rank` left blank. The destination contract for `matter_score` is
`decimal(5,2) NOT NULL` — so a well-behaved pipeline either rejects that row or
surfaces a type-coercion failure, and a profiler run shows a non-numeric /
null-rank anomaly. This is the same class of intentional gap as loopcapital's
`Extract_Holdings_Nightly.dtsx` (no data-type validation on `quantity`): a real
drift, planted on purpose, so the diagnostics story has something true to catch.

Everything else in the source files is clean and internally consistent.
