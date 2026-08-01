# SSIS → SQL Server / Azure Synapse

The SSIS materialization of the canonical student matter-scores model
([`../../MODEL.md`](../../MODEL.md)) against a T-SQL backend (SQL Server, or
Azure Synapse dedicated SQL pool). Scoped as it would live in its own
integration-services repo.

```
ssis-sqlserver/
├── sql/
│   └── 01_create_tables.sql       ← T-SQL DDL for the 3 tables
├── ssis/
│   ├── Load_Schools.dtsx           ← schools.csv → dbo.schools
│   ├── Load_WeeklyMatterScores.dtsx  ← weekly feed (carries the planted gap)
│   └── Load_MonthlyMatterScores.dtsx ← monthly feed (clean)
└── ssrs/
    └── Weekly_MatterScores_ByState.rdl  ← national weekly score rolled up by state
```

## Pipeline formats

- **`.dtsx`** — SSIS packages (DTS XML, PackageFormatVersion 8). Flat-file
  source → OLE DB destination, one per table.
- **`.rdl`** — SSRS Report Definition Language, reads the materialized warehouse.
- **`.xsd`** — the destination table contracts live one level up in
  [`../../contracts/`](../../contracts/) (engine-neutral, shared with dbt).

## Same sources, same model

Every package reads the shared CSVs in [`../../sources/`](../../sources/) — the
identical inputs the dbt-snowflake and dbt-redshift projects read. The three
destination tables match [`../../MODEL.md`](../../MODEL.md) exactly; only the
T-SQL type rendering (`NVARCHAR`/`INT`/`DECIMAL(5,2)`) is dialect-specific.

## Planted gap

`Load_WeeklyMatterScores.dtsx` reads `matter_score` as a string with **no**
data-type validation or error-row redirect before the OLE DB destination. The
weekly source feed carries one `"n/a"` score and one blank `national_rank`, so
the bad score row fails at the `DECIMAL(5,2) NOT NULL` insert rather than being
caught upstream — a real drift for a diagnostics skill to surface (see
[`../../MODEL.md`](../../MODEL.md) § "Planted defect").
