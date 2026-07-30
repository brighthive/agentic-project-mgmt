# BH-1255 Spec Family — Handover Status

The Loop Capital trial success criteria, mapped to the specs that answer them. All six specs
below are **spec-complete** (§1–§10 per `~/.claude/rules/spec-driven.md`), grounded in real
`file:line` references, and ready for an engineer to pick up. **No implementation has started;
no child tickets exist yet** — the `BH-XXXX (to create)` placeholders in each Ticket Breakdown
stay placeholders until the family is approved and `/create-jira-ticket` runs under epic BH-1255.

> **Core principle:** in-trial SSIS/SSRS work is **diagnose & operate, don't author** — read +
> flag, never regenerate. The one regeneration spec is explicitly out of trial scope (POC).

## The family

| Spec | Trial criterion | Nature | Lines | Ready |
|---|---|---|---|---|
| [`pipeline-run-lifecycle.md`](pipeline-run-lifecycle.md) | Lineage-scoped, re-runnable runs (foundation) | Build | 333 | ✅ |
| [`sqlserver-health-watch.md`](sqlserver-health-watch.md) | 4 — proactive SQL Server health (disk-low + failed Agent jobs) | **Verify-only** (capability ships) | 377 | ✅ |
| [`ssis-ssrs-proactive-pipeline-source.md`](ssis-ssrs-proactive-pipeline-source.md) | 5 & 6 — legacy SSIS/SSRS diagnostics (read + flag) | Build (new caller) | 240 | ✅ |
| [`pipeline-self-healing-fleet.md`](pipeline-self-healing-fleet.md) | 7 — self-healing fleet (engine/warehouse/tool agnostic) | Build | 560 | ✅ |
| [`data-quality-rules.md`](data-quality-rules.md) | 7 (axis 3) — quality rules on assets, by tag/group, on a routine | Build (mostly a bridge) | 269 | ✅ |
| [`brightroutine-approve-schedule.md`](brightroutine-approve-schedule.md) | 9 — human approves in Slack → scheduled routine (+ 8 audit) | Build (the one missing seam) | 406 | ✅ |
| [`ssis-ssrs-to-dbt-regeneration.md`](ssis-ssrs-to-dbt-regeneration.md) | none — **OUT OF TRIAL SCOPE** (modernize / POC) | Build (POC) | 643 | ✅ (deferred) |

## Notes for the engineer picking this up

- **Two specs are verify-only, not greenfield.** `sqlserver-health-watch` and the SSIS/SSRS
  diagnostics capability already ship in `brightbot` (`SqlServerPipelineSource`,
  `analyze_dtsx_package`/`analyze_rdl_report`). Those specs pin the trial acceptance bar around
  existing code + wire the schedule/surfacing + name the real gaps — they are not build-from-zero.
- **Three axes, not one — read fleet §1 first.** The live `register_adapters()` dict collapses
  three orthogonal ideas: **(1) engine** the pipeline runs on (`dbt`/`ssis`/`snowflake`/…) →
  `MonitoredPipeline.source_type`; **(2) detector** watched across engines (`longitudinal_drift`)
  → attached via `watch_drift`, never a `source_type`; **(3) quality rule** on a data asset →
  the new `data-quality-rules.md` spec. All three feed one `PipelineHealthSignal → route → alert`
  backbone. Don't re-collapse them.
- **`source_type` is an open `str`, validated against the live registry — not a closed Literal.**
  The old `Literal["dbt","databricks","etl"]` was fixed during the agnosticism audit: a closed type
  made every new engine a code change, contradicting INV-16. On a **signal** `source_type` = the
  emitting adapter's key; on the **entity** it's the engine only. SQL Server AND SSIS both emit
  `"etl"` at the disk/job level; consumers distinguish via `failure_type`.
- **Engine/warehouse/tool agnosticism is INV-16** in the fleet spec: adding a stack is a
  `PIPELINE_SOURCE_ADAPTERS` + `PIPELINE_HEALERS` registration (config), never a code change to
  anything that polls, routes, heals, or alerts. Loop Capital's SQL Server + SSIS are the first
  two adapters, not the design.
- **GC-17 (no self-merge) holds unconditionally** across every healer — enforced at registration
  (`Gc17SafetyViolation`) and re-checked at dispatch.
- **Budget note:** the fleet spec runs 560 lines (over the 500 default) — a deliberate override:
  it unifies five architectural layers behind one GC-17/self-heal safety story that splitting
  would fragment. Every other spec is within budget.

## Build order (scored by trial value, not spec number)

Score each spec on **Trial Value** (answers "this is not live" / hits a numbered criterion),
**Speed** (inverse effort — a capability that already ships scores 5), and **Unblocks** (gates
other specs). `score = TrialValue×2 + Speed + Unblocks`. Build highest-score first.

| # | Spec | Crit | TV | Speed | Unblk | Score | Wave |
|---|---|---|:--:|:--:|:--:|:--:|:--:|
| 1 | `sqlserver-health-watch` | 4 | 5 | 5 | 2 | **17** | **W1 — live proof** |
| 2 | `ssis-ssrs-proactive-pipeline-source` | 5 & 6 | 5 | 3 | 2 | **15** | **W1 — live proof** |
| 3 | `pipeline-run-lifecycle` | foundation | 3 | 3 | 5 | **14** | **W2 — foundation** |
| 4 | `brightroutine-approve-schedule` | 9 (+8) | 4 | 3 | 3 | **14** | **W2 — foundation** |
| 5 | `pipeline-self-healing-fleet` | 7 | 4 | 2 | 3 | **13** | **W3 — depth** |
| 6 | `data-quality-rules` | 7 (axis 3) | 3 | 4 | 1 | **11** | **W3 — depth** |
| — | `ssis-ssrs-to-dbt-regeneration` | none | 1 | 1 | 0 | **3** | **defer (OOS)** |

- **W1 buys the fastest live proof.** Both are verify-only / new-caller over capabilities that
  already ship — the fastest rebuttal to Frank's "this is not live" (2026-07-09), because the
  underlying watch already runs; the work is pinning the acceptance bar + wiring the schedule/surfacing.
- **W2 is the foundation** the rest leans on — re-runnable runs and human-approved scheduling
  (`Unblocks` is why `pipeline-run-lifecycle` sequences here despite a lower trial value).
- **W3 is the heavier depth work** — the engine-agnostic self-healing fleet and the quality-rule bridge.
- **Regeneration stays deferred** — out of trial scope; a POC, not a trial deliverable.

## What happens next (spec-first gate)

1. Review the family (this PR).
2. On approval → create child tickets under **BH-1255** (board 152, every ticket `parentKey`
   the epic, `issueType: Task`) from each spec's Ticket Breakdown, **in build order above** (W1 first).
3. Implement wave-by-wave; §10 test coverage lands in the real suites before each PR opens.
