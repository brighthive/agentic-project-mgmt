# Demo swarm — one product, agents working across many data-engineering situations

> Frank is not being sold a grid of projects. He is being shown that **BrightAgent is a swarm of
> agents that monitor, fix, build, maintain, and support across many, many data-engineering
> situations** — different repos, different transformation engines, different warehouses, different
> failure modes — each agent doing real operational work: diagnose a broken run, open a remediation
> PR into the right repo, watch a disk fill, sync run history, guard a merge gate. The heterogeneity
> below (a distinct repo + distinct dbt jobs per situation) is **evidence of swarm breadth**, not the
> point itself. The point: one product's agents handle all of it, engine-agnostically.
>
> Every repo and every job named here is **real and already provisioned** — no invented fixtures.
> Where a target is not yet wired live, the row says so honestly (the honesty layer the runbook and
> `~/.claude/rules/pr-templates.md` mandate).

## Why breadth, not one situation

A single situation that syncs cleanly proves the happy path once. The capability claim is stronger
and only defensible if the same agents hold across **heterogeneous** situations: different repos
(different owners, different model trees), different job cadences, different engines. The BH-1330
receiver (`platform-core syncProjectRuns`) and the brightbot `sync_project_runs` port composition
never branch on any of these — so the demo must actually exercise more than one situation to show
the swarm is engine- and repo-agnostic by construction, not tuned to a single happy path.
(Cross-warehouse agnosticism is a related but separate claim, proven off a throwaway workspace — see
below.)

## Loop Capital is ONE workspace on ONE warehouse — breadth is per PROJECT

**Loop Capital has ONE workspace and ONE warehouse: Snowflake** (plus their *legacy SQL Server
source*, which is a data source, not a warehouse they run transformations on). The demo does NOT
pretend LC runs on Redshift or any second warehouse — they don't. The breadth Frank sees inside his
workspace is **several projects, each linked to a different git repo, each running a different set of
dbt jobs** — all landing on the one Snowflake warehouse he actually has. Each project is a distinct
*situation* a BrightAgent agent operates in.

This still fully exercises BH-1330 sync + observability + the remediation-PR targeting: a warehouse
binds *per project* in the model (`Project.transformationServiceId` → `transformationService`
connection, `platform-core src/graphql/service/neo4j/project.ts:36,163`), but repo and dbt-job set
are what vary here — because that's what varies for real.

Legend: 🟢 live on staging · 🟡 fixture ready, staging-wiring pending · ⚪ planned

### Loop Capital's workspace — several situations, distinct repos + jobs, ONE Snowflake warehouse

| # | Situation (project) | Git repo (distinct) | dbt jobs / pipelines (distinct) | Warehouse | State |
|---|---|---|---|---|---|
| 1 | **Asset Management** | `brighthive-dbt/loopcapital-dbt-demo` | nightly `stg_holdings_nightly` build (dbt Cloud job) | Snowflake | 🟢 |
| 2 | **Market Data** | a second distinct dbt repo | its own model tree + its own dbt Cloud job | Snowflake | ⚪ |
| 3 | **Trade DW** | a third distinct dbt repo | its own model tree + its own dbt Cloud job | Snowflake | ⚪ |

The three source families already declared in the one demo repo —
`sources_loopcapital_dbo.yml`, `sources_market_data.yml`, `sources_trade_dw.yml`
(`brighthive-dbt/loopcapital-dbt-demo/models`) — are the natural seams for three distinct projects,
each promotable into its own repo with its own dbt Cloud job. Same warehouse, different repo + jobs
per situation: exactly the breadth needed, honest to LC's real single-warehouse estate.

### Cross-WAREHOUSE agnosticism — a SEPARATE, non-LC story

Proving the same swarm works on Snowflake *and* Redshift *and* SQL Server is a real capability claim
— but it is **not** Loop Capital's workspace, because those connections don't exist there. It lives
in the client-neutral **student-scores** fixture on a **throwaway/demo workspace**, never presented
as LC's:

| Situation | Repo | Engine | Warehouse |
|---|---|---|---|
| Student Scores — Snowflake | `student-scores/engines/dbt-snowflake` | dbt | Snowflake |
| Student Scores — Redshift | `student-scores/engines/dbt-redshift` | dbt | Redshift |
| Student Scores — SSIS | `student-scores/engines/ssis-sqlserver` | SSIS | SQL Server |

## What the swarm proves in the demo

The same agents, doing real operational work across every situation above — this is the swarm, not a
dashboard:

- **monitor** — a watchdog agent fires on a filling disk / stalled run (GC-15 pattern), in each
  situation, engine-agnostic.
- **fix** — the agent opens an **engine-appropriate remediation PR into that situation's *own* repo**
  (BH-1329 before/after evidence). Three situations → three repos → three PR targets, never
  cross-contaminated. The agent knows *which* repo a given project's transformations live in (task
  #31, verified live #39).
- **build / maintain** — `syncProjectRuns` backfills each situation's *own* run history + data
  products. Asset Management's nightly-holdings runs never leak into Market Data's Observability tab
  (INV-3 project isolation, shown across real projects — not just asserted in a unit test).
- **support** — the same agent answers "why did this run fail?" in each situation, engine-agnostic
  (dbt Cloud, Snowflake-native, SSIS-degraded per INV-6).
- **one honest warehouse** — all LC situations land on LC's real Snowflake; no invented second
  warehouse on their workspace. Cross-warehouse agnosticism is demonstrated on the student-scores
  throwaway workspace, clearly labeled not-LC.

## Live-wiring checklist (staging)

What must be true on staging for the swarm demo to run green. 🟢 = confirmed, ⚪ = to wire.
No destructive ops; each write confirmed by name before it runs.

**LC workspace (`e3fc0917-…`), all on Snowflake:**
- [x] 🟢 Situation 1 (Asset Management) linked to `loopcapital-dbt-demo` (verified #39)
- [ ] ⚪ Situation 2 (Market Data) created + linked to its own repo + its own dbt Cloud job
- [ ] ⚪ Situation 3 (Trade DW) created + linked to its own repo + its own dbt Cloud job
- [ ] ⚪ `syncProjectRuns` run once per situation → each Observability tab fills from its own job
- [ ] ⚪ An agent shown doing monitor/fix/build/support work in each situation, isolated to its repo

**Throwaway/demo workspace (NOT LC) — cross-warehouse agnosticism:**
- [ ] ⚪ Student-scores Snowflake + Redshift + SSIS situations wired on a throwaway workspace
- [ ] ⚪ `syncProjectRuns` fills each identically → proof the path is warehouse-agnostic

## Guardrails

- The LC multi-situation wiring stays on Loop Capital's real Snowflake — no invented second warehouse
  on their workspace. Adding situations 2–3 does **not** nuke anything: their single Asset-Management
  story stays intact until the deliberate nuke → rebuild step in
  [`DEMO_RUNBOOK_BEFORE_AFTER.md`](./DEMO_RUNBOOK_BEFORE_AFTER.md).
- The cross-warehouse (Redshift/SQL Server) story targets a **throwaway/demo workspace**, never Loop
  Capital's `e3fc0917-03a6-4ac6-aad4-ac265329bfb9` — those connections don't exist on LC's workspace
  and must never be presented as if they do.
- Creating a dbt Cloud job or linking a repo on staging is a live write — confirm each by name before
  running it (the standing secret/write guardrail in the workspace `CLAUDE.md`).

## Related

- [`demo.md`](./demo.md) — the GC-14→17 demo loop this swarm feeds.
- [`../../../docs/specs/project-engine-run-sync.md`](../../../docs/specs/project-engine-run-sync.md) — BH-1330 sync spec (the capability the swarm exercises).
- [`../../../docs/pocs/synth-warehouse/student-scores/README.md`](../../../docs/pocs/synth-warehouse/student-scores/README.md) — the one-dataset-three-engines fixture situations 2–4 draw from.
- [`../../../docs/specs/pipeline-self-healing-fleet.md`](../../../docs/specs/pipeline-self-healing-fleet.md) — the proactive monitoring architecture the observability surface projects onto.
