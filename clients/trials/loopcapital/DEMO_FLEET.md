# Demo fleet — several projects, each its own repo, each its own dbt jobs

> The Frank demo must show the sync + observability + proactivity story across a **fleet of
> distinct projects** — not one happy-path project. Each project below links to a **different
> git repo** and runs a **different set of dbt jobs / pipelines** against a **different
> warehouse**. This is what proves BH-1330 (project↔engine run sync) and the observability
> surface are engine- and project-agnostic by construction, not tuned to a single project.
>
> Every repo and every job named here is **real and already provisioned** — no invented
> fixtures. Where a warehouse target is not yet wired live, the row says so honestly (the
> honesty layer the runbook and `~/.claude/rules/pr-templates.md` mandate).

## Why a fleet, not one project

A single project that syncs cleanly proves the happy path once. The capability claim is
stronger and only defensible if it holds across **heterogeneous** projects: different repos
(different owners, different model trees), different job cadences, different engines, different
warehouse dialects. The BH-1330 receiver (`platform-core syncProjectRuns`) and the brightbot
`sync_project_runs` port composition never branch on any of these — so the demo must actually
exercise more than one to show that.

## One workspace, one warehouse — the fleet is per PROJECT

**Loop Capital has ONE workspace and ONE warehouse: Snowflake** (plus their *legacy SQL Server
source*, which is a data source, not a warehouse they run transformations on). The demo does NOT
pretend LC runs on Redshift or any second warehouse — they don't. The heterogeneity Frank sees
inside his workspace is **several projects, each linked to a different git repo, each running a
different set of dbt jobs** — all landing on the one Snowflake warehouse he actually has.

This still fully exercises BH-1330 sync + observability + the remediation-PR targeting: a
warehouse binds *per project* in the model (`Project.transformationServiceId` →
`transformationService` connection, `platform-core src/graphql/service/neo4j/project.ts:36,163`),
but repo and dbt-job set are what vary here — because that's what varies for real.

Legend: 🟢 live on staging · 🟡 fixture ready, staging-wiring pending · ⚪ planned

### Loop Capital's workspace — several projects, distinct repos + jobs, ONE Snowflake warehouse

| # | Project | Git repo (distinct) | dbt jobs / pipelines (distinct) | Warehouse | State |
|---|---|---|---|---|---|
| 1 | **Asset Management** | `brighthive-dbt/loopcapital-dbt-demo` | nightly `stg_holdings_nightly` build (dbt Cloud job) | Snowflake | 🟢 |
| 2 | **Market Data** | a second distinct dbt repo | its own model tree + its own dbt Cloud job | Snowflake | ⚪ |
| 3 | **Trade DW** | a third distinct dbt repo | its own model tree + its own dbt Cloud job | Snowflake | ⚪ |

The three source families already declared in the one demo repo —
`sources_loopcapital_dbo.yml`, `sources_market_data.yml`, `sources_trade_dw.yml`
(`brighthive-dbt/loopcapital-dbt-demo/models`) — are the natural seams for three distinct
projects, each promotable into its own repo with its own dbt Cloud job. Same warehouse, different
repo + jobs per project: exactly the fleet you asked for, honest to LC's real single-warehouse
estate.

### Cross-WAREHOUSE agnosticism — a SEPARATE, non-LC story

Proving the same sync path works on Snowflake *and* Redshift *and* SQL Server is a real capability
claim — but it is **not** Loop Capital's workspace, because those connections don't exist there.
It lives in the client-neutral **student-scores** fixture on a **throwaway/demo workspace**, never
presented as LC's:

| Project | Repo | Engine | Warehouse |
|---|---|---|---|
| Student Scores — Snowflake | `student-scores/engines/dbt-snowflake` | dbt | Snowflake |
| Student Scores — Redshift | `student-scores/engines/dbt-redshift` | dbt | Redshift |
| Student Scores — SSIS | `student-scores/engines/ssis-sqlserver` | SSIS | SQL Server |

## What the LC fleet proves in the demo

- **Distinct repos** → the project↔repo link (task #31, verified live #39) is per-project, and
  the agent knows *which* repo a given project's transformations live in when it proposes a
  remediation PR (BH-1329). Three projects → three repos → three PR targets, never cross-contaminated.
- **Distinct dbt jobs** → `syncProjectRuns` pulls each project's *own* run history. Asset
  Management's nightly-holdings runs never leak into Market Data's Observability tab (INV-3
  project isolation, shown across real projects — not just asserted in a unit test).
- **One warehouse, honestly** → all three land on LC's real Snowflake; no invented second
  warehouse on their workspace. Cross-warehouse agnosticism is demonstrated on the student-scores
  throwaway workspace, clearly labeled not-LC.
- **Fleet view** → the SystemAdmin fleet-health page (BH-1337, task #72) shows LC's projects side
  by side — the "one glance across the whole estate" surface Frank asked for.

## Live-wiring checklist (staging)

What must be true on staging for the fleet demo to run green. 🟢 = confirmed, ⚪ = to wire.
No destructive ops; each write confirmed by name before it runs.

- [x] 🟢 Project 1 linked to `loopcapital-dbt-demo` on the Loop Capital workspace (verified #39)
- [ ] ⚪ Project 2 created + linked to `student_scores_snowflake` repo on a **throwaway/demo**
  workspace (never Loop Capital's `e3fc0917-…`)
- [ ] ⚪ Project 3 created + linked to `student_scores_redshift` repo
- [ ] ⚪ Project 4 created + linked to the SSIS package set (SQL Server engine, `LIST_RUNS` absent)
- [ ] ⚪ `syncProjectRuns` run once per project → each Observability tab fills from its own engine
- [ ] ⚪ Fleet-health page shows all four with independent last-run / success-rate

## Guardrails

- The multi-project wiring targets a **throwaway/demo workspace**, never Loop Capital's
  `e3fc0917-03a6-4ac6-aad4-ac265329bfb9`. Loop Capital's own workspace stays the single-project
  Asset-Management story until the deliberate nuke → rebuild step in
  [`DEMO_RUNBOOK_BEFORE_AFTER.md`](./DEMO_RUNBOOK_BEFORE_AFTER.md).
- Creating a dbt Cloud job or linking a repo on staging is a live write — confirm each by name
  before running it (the standing secret/write guardrail in the workspace `CLAUDE.md`).

## Related

- [`demo.md`](./demo.md) — the GC-14→17 demo loop this fleet feeds.
- [`../../../docs/specs/project-engine-run-sync.md`](../../../docs/specs/project-engine-run-sync.md) — BH-1330 sync spec (the capability the fleet exercises).
- [`../../../docs/pocs/synth-warehouse/student-scores/README.md`](../../../docs/pocs/synth-warehouse/student-scores/README.md) — the one-dataset-three-engines fixture projects 2–4 draw from.
- [`../../../docs/specs/pipeline-self-healing-fleet.md`](../../../docs/specs/pipeline-self-healing-fleet.md) — the fleet monitoring architecture the observability surface projects onto.
