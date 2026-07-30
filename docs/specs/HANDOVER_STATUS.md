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
| [`pipeline-self-healing-fleet.md`](pipeline-self-healing-fleet.md) | 7 — self-healing fleet (engine/warehouse/tool agnostic) | Build | 538 | ✅ |
| [`brightroutine-approve-schedule.md`](brightroutine-approve-schedule.md) | 9 — human approves in Slack → scheduled routine (+ 8 audit) | Build (the one missing seam) | 406 | ✅ |
| [`ssis-ssrs-to-dbt-regeneration.md`](ssis-ssrs-to-dbt-regeneration.md) | none — **OUT OF TRIAL SCOPE** (modernize / POC) | Build (POC) | 643 | ✅ (deferred) |

## Notes for the engineer picking this up

- **Two specs are verify-only, not greenfield.** `sqlserver-health-watch` and the SSIS/SSRS
  diagnostics capability already ship in `brightbot` (`SqlServerPipelineSource`,
  `analyze_dtsx_package`/`analyze_rdl_report`). Those specs pin the trial acceptance bar around
  existing code + wire the schedule/surfacing + name the real gaps — they are not build-from-zero.
- **`source_type` is the closed `Literal["dbt","databricks","etl"]`.** SQL Server AND SSIS both
  emit `"etl"`, never `"sqlserver"`/`"ssis"`; consumers distinguish via `failure_type`. The fleet
  spec's §2 contract change widens this to the full `SourceType` set — that widening is the one
  DTO change the family introduces.
- **Engine/warehouse/tool agnosticism is INV-16** in the fleet spec: adding a stack is a
  `PIPELINE_SOURCE_ADAPTERS` + `PIPELINE_HEALERS` registration (config), never a code change to
  anything that polls, routes, heals, or alerts. Loop Capital's SQL Server + SSIS are the first
  two adapters, not the design.
- **GC-17 (no self-merge) holds unconditionally** across every healer — enforced at registration
  (`Gc17SafetyViolation`) and re-checked at dispatch.
- **Budget note:** the fleet spec runs 538 lines (over the 500 default) — a deliberate override:
  it unifies five architectural layers behind one GC-17/self-heal safety story that splitting
  would fragment. Every other spec is within budget.

## What happens next (spec-first gate)

1. Review the family (this PR).
2. On approval → create child tickets under **BH-1255** (board 152, every ticket `parentKey`
   the epic, `issueType: Task`) from each spec's Ticket Breakdown.
3. Implement spec-by-spec; §10 test coverage lands in the real suites before each PR opens.
