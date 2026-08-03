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

## The fleet

Legend: 🟢 live on staging · 🟡 fixture ready, staging-wiring pending · ⚪ planned

| # | Project | Git repo (distinct) | dbt jobs / pipelines (distinct) | Engine | Warehouse | State |
|---|---|---|---|---|---|---|
| 1 | **Loop Capital — Asset Management** | `brighthive-dbt/loopcapital-dbt-demo` | nightly `stg_holdings_nightly` build (dbt Cloud job) | dbt Cloud | Snowflake | 🟢 |
| 2 | **Student Matter-Scores — Snowflake** | `student-scores/engines/dbt-snowflake` (`student_scores_snowflake`) | `staging` views + `marts` tables build | dbt | Snowflake | 🟡 |
| 3 | **Student Matter-Scores — Redshift** | `student-scores/engines/dbt-redshift` (`student_scores_redshift`) | same models, Redshift-retargeted profile | dbt | Redshift | 🟡 |
| 4 | **Loop Capital — Legacy SSIS** | `student-scores/engines/ssis-sqlserver` (`.dtsx` packages) | SQL Agent nightly extract + report | SSIS | SQL Server | 🟡 |

Projects 1–3 are all dbt but land on **two different warehouses through two different repos with
two different job sets** — the cleanest proof that sync is repo- and warehouse-agnostic. Project
4 is a non-dbt engine (SSIS) surfacing through the *same* `PipelineRunner` port with `LIST_RUNS`
degraded per INV-6 — the proof that "engine-agnostic" isn't just "any dbt".

## What each project proves in the demo

- **Distinct repos** → the project↔repo link (task #31, verified live #39) is per-project, and
  the agent is aware of *which* repo a given project's transformations live in when it proposes a
  remediation PR (BH-1329). Two projects → two repos → two PR targets, never cross-contaminated.
- **Distinct dbt jobs** → `syncProjectRuns` pulls each project's *own* run history. Project 1's
  nightly-holdings runs never leak into Project 2's Observability tab (INV-3 tenant/project
  isolation, shown across real projects, not asserted in a unit test alone).
- **Distinct warehouses** → the same sync path fills Observability for a Snowflake project and a
  Redshift project identically; the dialect only ever lives inside the adapter.
- **Fleet view** → the SystemAdmin fleet-health page (BH-1337, task #72) shows all four projects
  side by side — the "one glance across the whole estate" surface Frank asked for.

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
