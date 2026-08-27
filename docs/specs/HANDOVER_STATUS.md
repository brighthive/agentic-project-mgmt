# BH-1255 Spec Family — Handover Status

The Loop Capital trial success criteria, mapped to the specs that answer them. The seven core specs
plus two adjunct surfacing specs below are **spec-complete** (§1–§10 per `~/.claude/rules/spec-driven.md`),
grounded in real `file:line` references, and ready for an engineer to pick up. **No implementation has started**,
but every Ticket Breakdown is now backed by real Jira children under epic BH-1255: the run-lifecycle
foundation is **BH-1256→1264** and the remaining six specs are **BH-1274→1303** (31 tickets, keys filled
into each spec's Ticket Breakdown). Lineage engineering (name-free tier derivation, delete/merge integrity)
lives under its own epic **BH-1273**; BH-1265 there is a cross-referenced dependency of the tier-surfacing spec.

> **Core principle:** in-trial SSIS/SSRS work is **diagnose & operate, don't author** — read +
> flag, never regenerate. The one regeneration spec is explicitly out of trial scope (POC).

## The family

| Spec | Trial criterion | Nature | Lines | Ready |
|---|---|---|---|---|
| [`pipeline-run-lifecycle.md`](pipeline-run-lifecycle.md) | Lineage-scoped, re-runnable runs (foundation) | **Mixed** — platform-core ships (verify-only); brightbot/webapp/e2e build | 333 | ✅ |
| [`sqlserver-health-watch.md`](sqlserver-health-watch.md) | 4 — proactive SQL Server health (disk-low + failed Agent jobs) | **Verify-only** (capability ships) | 377 | ✅ |
| [`ssis-ssrs-proactive-pipeline-source.md`](ssis-ssrs-proactive-pipeline-source.md) | 5 & 6 — legacy SSIS/SSRS diagnostics (read + flag) | **Mostly verify** — SSIS ships (wire+verify); only SSRS is net-new | 240 | ✅ |
| [`pipeline-self-healing-fleet.md`](pipeline-self-healing-fleet.md) | 7 — self-healing fleet (engine/warehouse/tool agnostic) | Build | 560 | ✅ |
| [`data-quality-rules.md`](data-quality-rules.md) | 7 (axis 3) — quality rules on assets, by tag/group, on a routine | Build (mostly a bridge) | 269 | ✅ |
| [`brightroutine-approve-schedule.md`](brightroutine-approve-schedule.md) | 9 — human approves in Slack → scheduled routine (+ 8 audit) | Build (the one missing seam) | 406 | ✅ |
| [`ssis-ssrs-to-dbt-regeneration.md`](ssis-ssrs-to-dbt-regeneration.md) | none — **OUT OF TRIAL SCOPE** (modernize / POC) | Build (POC) | 643 | ✅ (deferred) |

## Adjunct specs (surfacing + file-format seam — added 2026-07-30)

Two capabilities the trial surfaces asked for that aren't a numbered criterion but make the
built work visible/usable. Both start **simple + incremental** and are grounded against real source.

| Spec | Ask | Nature | Ready |
|---|---|---|---|
| [`data-product-tier-surfacing.md`](data-product-tier-surfacing.md) | Show Gold/Platinum data products in-app (grid + sidebar) and in Slack | Build (pure read; W1 first — see note) | ✅ |
| [`pipeline-artifact-parser-registry.md`](pipeline-artifact-parser-registry.md) | "Files need to work for any type/format" — in-trial format-agnostic seam | Build (seam only; behaviour unchanged — see note) | ✅ |

- **Tier surfacing is read-only** — it never authors or edits a tier; `pipelineTier` is derived from
  lineage depth (`pipeline-lineage.ts:464-472`), never node names. W1 exploits that
  `getCreatedDataProducts` already returns the tier-bearing Neo4j node (`project.ts:131-150`) —
  the field just isn't selected yet. **No workspace-wide "products by tier" query exists**
  (`pipelineLineage(tier:)` needs a `nodeId`+`direction`), so W2's filter is client-side over W1's column.
- **Format seam wraps, doesn't rewrite** — the real parsers return `dict[str, Any]`
  (`parse_dtsx:130`, `parse_rdl:52`); adapters carry that dict through unchanged (INV-1). A new format
  is then an additive adapter + one registry line, never a call-site edit.

## Notes for the engineer picking this up

- **More ships than the specs first assumed — grounded 2026-07-29 against committed source.** A
  cross-repo pass (all repos on `develop`/`origin/staging`) found the family had drifted from an
  already-built reality:
  - [`sqlserver-health-watch`](./sqlserver-health-watch.md) + the SSIS diagnostics capability ship in `brightbot`
    (`SqlServerPipelineSource`, `SsisCatalogPipelineSource` at `ssis_pipeline_source.py:103`,
    `analyze_dtsx_package`/`analyze_rdl_report`). SSIS work is **wire + verify**, not authoring;
    only SSRS (`.rdl` proactive source) is net-new.
  - **[`pipeline-run-lifecycle`](./pipeline-run-lifecycle.md)'s entire platform-core side ships** on staging (commit `a4c00f80`):
    `runPipelineSegment`, `reRunFromNode`, `WorkflowRunNode.lineageNodesTouched`/`runScope`/`immutable`,
    and a real `DbtAdapter.checkStatus` dbt Cloud poll. BH-1258/1259/1260/1263 are **verify-only**;
    the net-new is brightbot (`path_between`, `schedule_pipeline_run`, runner port) + webapp + e2e.
  - [`data-quality-rules`](./data-quality-rules.md)' scope storage already exists (`ALL_ASSETS`/`SELECTED_ASSETS`
    `typedefs.ts:631-633`, `DataAsset.tags` `:565`, group NODES via INCLUDES edges) — the bridge
    is a thin public `rulesInScope(tag|groupId)` resolver, not new tag/group storage. There is **no**
    `DataAsset.group: String` scalar — target group nodes.
  - **Verify a claim in the layer that OWNS it.** GraphQL enums live in platform-core `typedefs.ts`,
    not brightbot's Python persistence dict — reading the wrong layer nearly flagged real capability
    as invented. See memory `bh1255-specs-vs-built-reality`.
- **Three axes, not one — read fleet §1 first.** The live `register_adapters()` dict collapses
  three orthogonal ideas: **(1) engine** the pipeline runs on (`dbt`/`ssis`/`snowflake`/…) →
  `MonitoredPipeline.source_type`; **(2) detector** watched across engines (`longitudinal_drift`)
  → attached via `watch_drift`, never a `source_type`; **(3) quality rule** on a data asset →
  the new [`data-quality-rules.md`](./data-quality-rules.md) spec. All three feed one `PipelineHealthSignal → route → alert`
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
| 1 | [`sqlserver-health-watch`](./sqlserver-health-watch.md) | 4 | 5 | 5 | 2 | **17** | **W1 — live proof** |
| 2 | [`ssis-ssrs-proactive-pipeline-source`](./ssis-ssrs-proactive-pipeline-source.md) | 5 & 6 | 5 | 3 | 2 | **15** | **W1 — live proof** |
| 3 | [`pipeline-run-lifecycle`](./pipeline-run-lifecycle.md) | foundation | 3 | 3 | 5 | **14** | **W2 — foundation** |
| 4 | [`brightroutine-approve-schedule`](./brightroutine-approve-schedule.md) | 9 (+8) | 4 | 3 | 3 | **14** | **W2 — foundation** |
| 5 | [`pipeline-self-healing-fleet`](./pipeline-self-healing-fleet.md) | 7 | 4 | 2 | 3 | **13** | **W3 — depth** |
| 6 | [`data-quality-rules`](./data-quality-rules.md) | 7 (axis 3) | 3 | 4 | 1 | **11** | **W3 — depth** |
| — | [`ssis-ssrs-to-dbt-regeneration`](./ssis-ssrs-to-dbt-regeneration.md) | none | 1 | 1 | 0 | **3** | **defer (OOS)** |

- **W1 buys the fastest live proof.** Both are verify-only / new-caller over capabilities that
  already ship — the fastest rebuttal to Frank's "this is not live" (2026-07-09), because the
  underlying watch already runs; the work is pinning the acceptance bar + wiring the schedule/surfacing.
- **W2 is the foundation** the rest leans on — re-runnable runs and human-approved scheduling
  (`Unblocks` is why [`pipeline-run-lifecycle`](./pipeline-run-lifecycle.md) sequences here despite a lower trial value).
- **W3 is the heavier depth work** — the engine-agnostic self-healing fleet and the quality-rule bridge.
- **Regeneration stays deferred** — out of trial scope; a POC, not a trial deliverable.

## What happens next (spec-first gate)

1. Review the family (this PR).
2. On approval → create child tickets under **BH-1255** (board 152, every ticket `parentKey`
   the epic, `issueType: Task`) from each spec's Ticket Breakdown, **in build order above** (W1 first).
3. Implement wave-by-wave; §10 test coverage lands in the real suites before each PR opens.
