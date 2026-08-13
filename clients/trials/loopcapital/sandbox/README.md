# Loop Capital SQL Server Sandbox

A real, local, Dockerized Microsoft SQL Server — standing in for Frank's legacy
SQL Server (per [`artifacts/poc-scope-from-client.md`](../artifacts/poc-scope-from-client.md))
so BrightHive's watchdog (GC-15, [`docs/specs/golden-cases-loopcapital.md`](../../../docs/specs/golden-cases-loopcapital.md))
can be built and validated against a real T-SQL backend — **replaces the original
BH-1057 plan of provisioning a real AWS RDS SQL Server instance**, per direction
to keep the demo fixture simple and local rather than a billable cloud resource.

> **This is still a real backend, not a mock.** `SynapseConnection`
> (`brightbot/tools/warehouse_connections.py:248-424`) is a plain pymssql/T-SQL
> client — it cannot tell the difference between this container and a real
> production SQL Server. Per `test-behavior-real.md`, GC-15 must run against
> this sandbox, never a stub — a mocked page is exactly what triggered Frank's
> "this is not live" reaction on 2026-07-09.

## Why this exists

Mirrors `clients/trials/longaeva/sandbox/`'s DX shape (README → setup → validate)
so the same "prove it against a real backend before building the agent" pattern
applies here — swapping Longaeva's live Snowflake account for a local Docker
container, since Loop Capital's demo fixture doesn't need (and per direction,
should not use) a provisioned cloud resource.

## What's inside

```
sandbox/
├── README.md              ← you are here
├── docker-compose.yml      ← SQL Server 2019 image, SQL Server Agent ON, fixed-size data volume
├── sql/
│   ├── 01_create_database.sql   ← LoopCapitalAM DB + holdings_raw (Asset Management shape)
│   ├── 02_create_agent_jobs.sql ← 2 SQL Server Agent jobs: one Succeeded, one Failed
│   ├── 03_bank_schema.sql       ← medallion model (raw_* → stg_* → mart_*)
│   └── 05_governed_principals.sql ← the two scoped logins the trial implies
├── governed_write_check.py ← proves the read/write boundary on a REAL server
├── ssis/
│   ├── Extract_Holdings_Nightly.dtsx     ← Loop-specific SSIS package feeding holdings_raw
│   └── Create_AssetManagement_MySQL.dtsx ← generic sample, MySQL-targeted, unrelated to GC-15
├── ssrs/
│   └── Holdings_Daily_Report.rdl     ← real SSRS report reading holdings_raw (first .rdl in this org)
├── setup.sh                ← idempotent: start container → Agent check → seed (via reset.py)
├── reset.py                ← tear down to ground zero + reseed against a named scenario
├── fill_disk.sh            ← pushes the fixed-size data volume toward ~18-20% free
├── profile_warehouse.py    ← real profiler run against holdings_raw (row/null/cardinality stats)
└── validate.sh             ← runs BH-1045's real query text, asserts actual content (not just non-empty)
```

## SSIS/SSRS artifacts

Loop's real legacy stack is SSIS-fed, SSRS-reported (per Track A —
[`../overview.md`](../overview.md)) — this sandbox now includes real,
well-formed artifacts of both, not just plain SQL Server jobs:

- **`ssis/Extract_Holdings_Nightly.dtsx`** — a real, Loop-Capital-SPECIFIC SSIS
  package (verified well-formed XML) that models the client's own
  custodian-feed → holdings extract, targeting THIS sandbox's `holdings_raw`
  table. Deliberately includes one intentional gap (no data-type validation
  on `quantity`) so a diagnostics skill has something real to find — the
  same class of drift GC-16's demo scenario references.
- **`ssis/Create_AssetManagement_MySQL.dtsx`** — a real but deliberately
  GENERIC SSIS package (same content as brightbot's existing
  `tests/fixtures/skills/create_assetmanagement_mysql.dtsx`, ~130 lines,
  one XML-escaping fix applied), added alongside the Loop-specific package
  above so this sandbox has both a generic and a domain-specific example.
  Targets MySQL via ODBC, not SQL Server — it does NOT participate in
  GC-15's disk/job-status queries, which are SQL-Server-specific.
- **`ssrs/Holdings_Daily_Report.rdl`** — a real SSRS report (verified
  well-formed XML) querying `holdings_raw`, standing in for the morning
  holdings report GC-14's Bar references. This is the **first `.rdl` fixture
  anywhere in this org** — a prior audit confirmed zero existed before this
  (`find . -iname "*.rdl"` returned nothing repo-wide).

### Standalone diagnostic artifacts (`TradeDW`/`OMS` model — NOT wired to this DB)

Three known-bad artifacts model a **second**, self-contained trading world
(`TradeDW` / `OMS` / FIX drop-copy) used purely as **byte-level inputs** to the
diagnostics readers (`parse_dtsx` / `parse_rdl` / XSD contract read). They are
deliberately NOT seeded into `LoopCapitalAM` — the tables they reference
(`dbo.Trades`, `dbo.FactTrade`, `dbo.ReconStaging`) do **not** exist in
`sql/03_bank_schema.sql`, and that's fine: these are diagnostic *samples*, not
DB fixtures. Do not run them against the container.

- **`ssis/02_LoadTradesFromOLTP.dtsx`** — SSIS package with baked-in flaws for
  criterion-5 diagnostics: no error handling, direct fast-load with no staging
  step, `SELECT *` source + full-cache lookup.
- **`ssrs/DailyTradeBlotter.rdl`** — SSRS report with `SELECT *`, report-side
  filter (no query pushdown), and report-side sort — criterion-6 diagnostics.
- **`contracts/TradeDW.ReconStaging.xsd`** — captured table contract for the
  FIX reconciliation landing table (no PK; `LastPx money` fed a `DT_STR`,
  TC-DTM-03), the schema-parity + PII-classification target.

## On-prem read/write — the governed boundary

Frank is off-cloud. The trial connects BrightAgent to **his own SQL Server 2019 box** with
"scoped read + optional governed-write (reviewable PRs only, nothing applied without
approval)". His DBAs will not hand over `sa`, and a demo that runs as `sa` proves nothing —
`sa` can do anything, so a write that succeeds says nothing about whether a boundary holds.

`sql/05_governed_principals.sql` creates the two principals the trial actually implies:

| Principal | Reads | Writes |
|---|---|---|
| `brightagent_reader` | all of `dbo`, disk stats, SQL Agent job history | **nothing, anywhere** |
| `brightagent_engineer` | all of `dbo` | **only** the `brightagent` schema it owns |

The boundary is enforced by SQL Server's permission engine — not by prompt wording, not by an
agent behaving well, and not by a tool-layer guard a future refactor could quietly drop. The
engineer's `DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::dbo` is the load-bearing line: it is
what makes "the agent cannot touch your data" a database fact rather than a claim in a deck.

```bash
export BRIGHTAGENT_READER_PASSWORD='...'    # printed by setup.sh
export BRIGHTAGENT_ENGINEER_PASSWORD='...'
uv run --with pymssql python governed_write_check.py
```

Every assertion runs against the real server over real TDS; a FAIL is a real privilege
escalation. Denials are matched on SQL Server's **error number** (229/230/262/300), not on the
mere fact that something raised — otherwise a missing table would report a triumphant PASS for
a boundary that was never tested.

### What actually writes: dbt Core, on his network

dbt **Cloud** cannot serve this trial at all, for two independent reasons:

1. **No SQL Server destination.** dbt Cloud hosts Snowflake, BigQuery, Databricks, Redshift,
   Postgres, Fabric and Synapse. Plain SQL Server is the *community* `dbt-sqlserver` adapter,
   which dbt Cloud does not run.
2. **It could not reach him anyway.** dbt Cloud is SaaS; Frank's box is on-prem behind his
   firewall. This is his own objection restated — *"if the SQL server does not have any MCP or
   any other service to actually connect."*

So **dbt Core runs on his network instead**. That is a deployment change, not an architecture
change: dbt is still the thing that writes to the warehouse. BrightAgent keeps its existing
role — author models, open governed PRs, orchestrate runs — and needs no raw write path of its
own, so brightbot's SELECT-only enforcement stays intact.

`dbt_governed/` is that path, proven end to end against this sandbox:

```bash
export BRIGHTAGENT_ENGINEER_PASSWORD='...'   # printed by setup.sh
cd dbt_governed
../disk_reclaim/.venv/bin/dbt run --profiles-dir . --project-dir .
```

The only lines that matter in `dbt_governed/profiles.yml` are `user: brightagent_engineer` and
`schema: brightagent`. dbt inherits the database-enforced boundary for free: it reads the
client's `dbo` tables as sources and materializes into the schema the engineer owns, and SQL
Server rejects any model that tries to write into `dbo`. No dbt-side guard, no allowlist.

> **dbt needs two metadata grants** beyond plain SELECT, both in
> `sql/05_governed_principals.sql`. Its table materialization reads
> `sys.sql_expression_dependencies`, which needs `VIEW DEFINITION` **and** an explicit
> `SELECT` — the latter is granted to `db_owner` by default, and these principals deliberately
> are not `db_owner`. Both are metadata-only; the boundary check still holds 13/13 after them.
> This was found by running the real adapter, not by reading docs.

> **`reset.py` drops the principals.** It drops and recreates `LoopCapitalAM`, and database
> users do not survive `DROP DATABASE` (server logins do). After any bare `reset.py` run the
> two users are gone and `governed_write_check.py` will fail to connect. Re-run `./setup.sh`
> instead — it is idempotent, and `LOOPCAPITAL_SCENARIO=disk-pressure ./setup.sh` reseeds a
> scenario *and* restores the principals in one pass.

Contract, invariants and correctness properties:
[`docs/specs/loopcapital-onprem-read-write-sandbox.md`](../../../../docs/specs/loopcapital-onprem-read-write-sandbox.md).

## Warehouse/DB profiler

**`profile_warehouse.py`** runs a REAL profiling pass against `holdings_raw`
using brightbot's actual `SynapseConnection` connectivity shape
(`brightbot/tools/warehouse_connections.py:248-424`) — the same class GC-15's
disk/job-status queries reuse. Surfaces row count, per-column null rate, and
cardinality — the "context added value info to the bank" framing: not a raw
JSON dump, but the numbers translated into what Frank's team would actually
check first (high null rates, unexpectedly low cardinality on an ID column).

```bash
export MSSQL_SA_PASSWORD='...'  # same value used by setup.sh
uv run --with pymssql python profile_warehouse.py
```

Verified end-to-end against a real running container (not claimed): profiled
2,000 real rows across 6 columns, correct null/cardinality math, real pymssql
connection over the same TDS protocol the actual demo will use.

## Quick start

Prereqs: Docker (Docker Desktop on Mac — no native Apple Silicon `mssql-server`
image, runs under emulation, works but slower to start), `bash`.

```bash
cd clients/trials/loopcapital/sandbox

export MSSQL_SA_PASSWORD='ChooseA-Strong1-Password!'  # SQL Server's own complexity rules apply

# 1. one-time setup — idempotent, safe to re-run
./setup.sh

# 2. prove it — both of GC-15's real queries return real data
./validate.sh
```

## Two real gaps Docker introduces (researched, not assumed — see also
## docs/specs/golden-cases-loopcapital.md's GC-15 section)

1. **SQL Server Agent is OFF by default** in the `mssql-server` image.
   `docker-compose.yml` sets `MSSQL_AGENT_ENABLED=true` — without it,
   `msdb.dbo.sysjobs`/`sysjobhistory` exist but stay empty, and BH-1045's
   job-status query would return nothing, even with jobs "created."
2. **`sys.dm_os_volume_stats` reports the REAL mounted volume's free space** —
   not a value we can fake. A default Docker volume has plenty of room and
   will never show "20% free" on its own. `docker-compose.yml` uses a
   fixed-size `tmpfs` mount for `/var/opt/mssql/data` (default 2GiB, override
   with `LOOPCAPITAL_DATA_VOLUME_BYTES`), and `fill_disk.sh` writes a filler
   file to deliberately push it toward the 18-20% free threshold Frank named.
   This is a genuine disk-pressure condition on a real volume, not a
   fabricated metric.

## Relationship to BH-1057 / BH-1045

- **BH-1057** (originally "provision a real AWS RDS SQL Server") is now
  "run this sandbox" — see the corrected ticket text for the updated scope.
- **BH-1045** (the disk/job-status query logic itself) is unaffected by this
  change — its two confirmed query texts are exactly what `validate.sh` runs;
  BH-1045's implementer should point `SynapseConnection` at
  `localhost:1433` / `LoopCapitalAM` when developing against this sandbox.

## Teardown

```bash
docker compose down -v   # -v also removes the tmpfs data volume + filler
```
