# Student Matter-Scores — one dataset, three transformation engines

A single, engine-neutral demo dataset — **national weekly and monthly
"matter-scores" for high schools, by state** — materialized by three different
transformation engines against three different warehouses, from the **same
source files and the same cases**. It's the concrete fixture behind the
engine-agnostic pipeline story: prove the *same* three tables land, identically
shaped, whether the pipeline is SSIS on SQL Server, dbt on Snowflake, or dbt on
Redshift.

> **Why this exists.** The `PipelineRunner` port (brightbot) is engine-agnostic
> by contract; this sandbox is the matching engine-agnostic *content*. Same
> sources, same three tables, same golden cases — only the engine and warehouse
> dialect change. It mirrors the DX shape of
> [`clients/trials/loopcapital/sandbox/`](../../../clients/trials/loopcapital/sandbox/)
> (README → sources → contracts → engine projects) but is client-neutral and
> lives with the synthetic-warehouse POC it belongs to.

## The three tables (canonical model — identical on every engine)

The data model is defined **once** in
[`MODEL.md`](./MODEL.md) and every engine materializes exactly it. Column names,
types, and nullability are the contract; only the SQL dialect that expresses
them differs per warehouse.

| Table | Grain | Holds |
|---|---|---|
| `schools` | one row per high school | school identity + `state` (the by-state key) |
| `weekly_matter_scores` | one row per school × ISO week | national weekly matter-score + national rank |
| `monthly_matter_scores` | one row per school × calendar month | national monthly matter-score + national rank |

*Matter-score* = a 0–100 engagement/standing index; the demo's headline metric.
"National … by state" = every score row carries `state` so a report can roll the
national figure up per state.

## Same sources, same cases

All three engine projects read the **same** source files in
[`sources/`](./sources/) — no per-engine data forks:

```
sources/
├── schools.csv                 ← 12 schools across 6 states
├── weekly_matter_scores.csv    ← 4 ISO weeks × 12 schools
└── monthly_matter_scores.csv   ← 3 months × 12 schools
```

One **deliberate gap** is baked into the weekly feed (a `matter_score` delivered
as free text where the table's contract is numeric) so a diagnostics / profiler
skill has a real drift to find — the same convention as loopcapital's
`Extract_Holdings_Nightly.dtsx`. See [`MODEL.md`](./MODEL.md) § "Planted defect".

## One dataset × three engines × three warehouses

Each engine project is laid out **as it would live in its own repo** —
self-contained, scoped to the repo it belongs to, with the correct
pipeline-format file extensions for that engine:

| Engine | Warehouse | Project | Pipeline artifacts |
|---|---|---|---|
| **SSIS** | SQL Server / Azure Synapse | [`engines/ssis-sqlserver/`](./engines/ssis-sqlserver/) | `.dtsx` packages · `.xsd` contracts · `.rdl` report |
| **dbt** | Snowflake | [`engines/dbt-snowflake/`](./engines/dbt-snowflake/) | `dbt_project.yml` · `sources.yml` · `.sql` models · `schema.yml` |
| **dbt** | Redshift | [`engines/dbt-redshift/`](./engines/dbt-redshift/) | same dbt models, Redshift-retargeted profile + dialect |

The `.xsd` table contracts in [`contracts/`](./contracts/) are engine-neutral —
they describe the three destination tables in SQL terms (`sqlType` / `nullable`
/ `primaryKey`) and are shared by the SSIS packages and referenced by the dbt
`schema.yml` tests.

## Status

✅ Complete — canonical model, shared source cases, engine-neutral `.xsd`
contracts, and all three engine projects (SSIS→SQL Server, dbt→Snowflake,
dbt→Redshift) are in place and validate (YAML parses, XSDs are valid W3C
schemas, all `.dtsx`/`.rdl` XML is well-formed). Tracked under BH-1320.
