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
├── docker-compose.yml      ← mssql-server image, SQL Server Agent ON, fixed-size data volume
├── sql/
│   ├── 01_create_database.sql   ← LoopCapitalAM DB + holdings_raw (Asset Management shape)
│   └── 02_create_agent_jobs.sql ← 2 SQL Server Agent jobs: one Succeeded, one Failed
├── ssis/
│   └── Extract_Holdings_Nightly.dtsx ← real SSIS package feeding holdings_raw (Track A's ask)
├── ssrs/
│   └── Holdings_Daily_Report.rdl     ← real SSRS report reading holdings_raw (first .rdl in this org)
├── setup.sh                ← idempotent: start container → seed → create jobs → fill disk
├── fill_disk.sh            ← pushes the fixed-size data volume toward ~18-20% free
├── profile_warehouse.py    ← real profiler run against holdings_raw (row/null/cardinality stats)
└── validate.sh             ← runs BH-1045's real query text, asserts non-empty results
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
