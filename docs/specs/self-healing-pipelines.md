---
title: "Self-Healing Pipelines — detect → diagnose → surgical PR loop"
epic: "BH-526"
author: "drchinca"
status: "Draft"
created: "2026-06-15"
generates: "tickets"
tags: [self-healing, pipelines, dbt, observability, dagster, brightbot, snowflake, golden-cases]
related:
  features: []
  pocs: []
  specs: ["longitudinal-monitoring.md", "quality-rules-configurable.md", "dbt-react-migration.md", "byow-end-to-end-omd-native.md"]
---

# Self-Healing Pipelines (Golden Case 11 / GAP-7)

> The last Longaeva PoC gap without an approach spec. GC-11 is currently `skip` — *no code, no ticket*. This spec defines how the **proven sandbox** (`clients/trials/longaeva/sandbox/self_healing/failure_modes.py`, 4/4 detect→fix verified) becomes a product capability: an agent loop that detects a pipeline failure, diagnoses it in plain language, and opens a **surgical** PR (not a rewrite).

## Problem

BrightHive's observability agent **alerts** on pipeline failures today, but stops there — a human still has to diagnose the cause and write the fix. For the four failure modes Grant (Longaeva) named — schema drift, missing partition, broken stage, dbt contract violation — the *fix* is small and mechanical (an `ALTER TABLE ADD COLUMN`, a re-point, a contract patch), yet there is no loop that turns a detected failure into a scoped PR. GC-11's bar is **"4/4 failure modes → surgical PR."** Today: 0 — the detect→diagnose→PR loop is not wired, and schema-drift detection specifically has zero code refs.

## Use Case / Goal

A pipeline run fails (or a monitor flags an anomaly — see `longitudinal-monitoring.md`). The Engineering agent reads the run logs + asset lineage + schema, identifies which of the four failure modes it is, and opens a GitHub PR containing **only the surgical fix** plus a plain-language diagnosis. A reviewer approves; nothing is auto-merged. Success = GC-11 flips `skip → live`: for each of the 4 sandbox failure modes, the agent produces the same surgical fix the fixture encodes.

## Current Situation

### How it works today
- **Proven in the sandbox** (`clients/trials/longaeva/sandbox/self_healing/failure_modes.py`, 4/4 verified): each mode is a `FailureMode` with `inject()` (create the failure), `detect()` (the diagnostic query, returns True when present), `diagnosis` + `fix_summary` (plain-language root cause + the exact surgical fix in prose — *not* a rewrite), and `heal()` (apply the surgical DDL + confirm detection clears). The four:
  - `schema_drift` — vendor adds/renames a landing-table column → `ALTER TABLE ADD COLUMN`.
  - `missing_partition` — an expected partition/date slice is absent.
  - `broken_stage` — a Snowflake external stage / load path is mis-pointed.
  - `dbt_contract` — a dbt model contract (column/type) is violated.
- **In the product**: the observability agent alerts; the dbt agent can already generate scoped PRs (verified live e2e). But nothing chains *detected failure → diagnosis → surgical PR* automatically.

### Hard limitations / gaps
- **No auto-trigger**: detection exists in pieces; the loop isn't wired to fire on failure.
- **No schema-drift detection in product**: zero code refs (the sandbox `detect()` is the reference).
- **Lineage surface**: the sandbox uses Dagster run-logs + asset-lineage (same shape as Longaeva's Dagster + OpenLineage stack) as the diagnosis input; the product agent needs an equivalent read path.
- **"Surgical, not rewrite"** is the hard product constraint — the `fix_summary` field (and the scoped DDL `heal()` applies) is the contract for scope.

## Proposals / Solutions

**Wire the loop on top of capabilities that already exist** — the dbt agent already opens scoped GitHub PRs (BH-526, verified live); add a detector layer + a diagnosis step that targets the 4 modes.

- **Detect**: port each sandbox `detect()` into the governance/observability agent, triggered on pipeline-failure event (or by the longitudinal monitor's anomaly, reusing that source).
- **Diagnose**: agent reads run logs + asset lineage + current schema; classifies into one of the 4 modes; produces a plain-language root-cause.
- **Surgical PR**: reuse the dbt agent's `commitSemanticViewToGitHub`-style scoped-PR path; the PR body carries the diagnosis; the diff is the surgical DDL only (the fix `heal()` encodes). **Never auto-merge** — human approval gate (matches the platform's HITL pattern for destructive ops).
- **Bound the blast radius**: the agent emits *only* the surgical fix the fixture encodes; a PR that touches more than the failure's scope fails the eval.

## Areas Involved

| Area | Repo | Role |
|---|---|---|
| Failure detectors (4 modes) | brightbot governance/observability agent | port sandbox `detect()` |
| Diagnosis | brightbot | read run logs + lineage + schema → classify + root-cause |
| Surgical PR | brightbot dbt agent (scoped-PR path) | open PR with surgical DDL + diagnosis, no auto-merge |
| Lineage/run-log read path | brightbot + platform-core | Dagster/OpenLineage equivalent surface |
| Trigger | longitudinal monitor (`longitudinal-monitoring.md`) or pipeline-failure event | fire the loop |
| Acceptance | brightbot `tests/integration/golden_cases/test_gc_11_self_healing.py` | flip skip → live |

## Acceptance Criteria

```gherkin
Feature: Self-healing pipelines (GC-11 / GAP-7)

  Scenario Outline: a failure mode yields exactly the surgical fix
    Given the <mode> failure is injected into LONGAEVA_POC (sandbox fixture)
    When the engineering agent runs detect -> diagnose -> propose
    Then it classifies the failure as <mode>
    And it opens a GitHub PR whose diff equals the fixture's surgical fix (heal DDL / fix_summary)
    And the PR body carries a plain-language diagnosis
    And the PR is NOT auto-merged (human approval gate)
    And applying the PR clears detection (heal confirms)

    Examples:
      | mode |
      | schema_drift |
      | missing_partition |
      | broken_stage |
      | dbt_contract |

  Scenario: surgical, not rewrite
    Given any of the 4 failure modes
    When the agent proposes a fix
    Then the diff is scoped to the failure (no unrelated files / full-model rewrite)

  Scenario: a merged fix that worked gets an honest confirmation, not silence
    Given a human merged a surgical PR for a detected failure
    When the watchdog's next poll (within the VERIFYING window, not the full cooldown) finds
      the same failure signature is GONE
    Then a success confirmation is posted on the SAME alert thread — not just an absence of
      a second alert, a positive "this is confirmed fixed" signal

  Scenario: a merged fix that did NOT work is never silently suppressed
    Given a human merged a surgical PR for a detected failure
    When the watchdog's next poll finds the SAME failure signature has recurred
    Then a NEW, higher-severity alert fires immediately — bypassing the normal cooldown —
      explicitly stating the prior merge did not resolve it
    And this is NOT an automatic new fix proposal — it goes through the same human-approval
      gate as the original, never an unattended retry loop
```

## Post-merge verification loop (added on review — real gap, not previously designed)

**The question that exposed this gap**: "once approved how does the PR build and self-correct
until success? imagine this is production and it fails a pipeline, we can't PR and hope for the
best — then it fails, then what?" Researched against real code before answering, not invented:

**What already exists, confirmed real**: `interruptible()`
(`brightbot/brightbot/utils/interrupt_utils.py:102-131`, a LangGraph `interrupt()` wrapper) is
the platform's real, shipped "agent proposes → pauses → human decides → resumes" pattern —
`agents/super_agent/nodes/agents/dbt.py:379-405` already uses it for exactly this shape
(propose a commit/PR, pause, wait for `approval_status`). This spec's "never auto-merge" gate
should be built ON this existing primitive, not a new one.

**What genuinely does NOT exist anywhere in brightbot, confirmed by direct search**: any
"propose → apply → re-run → verify → iterate if still broken" loop. Every existing fix-proposing
capability (dbt commits, quality expectation selection) is strictly one-shot — propose once,
human decides, done. `registration_tools.py:129-157` states this explicitly: once a PR merges,
the code assumes success and never re-checks. **This spec's own Acceptance Criteria (Scenario
"a failure mode yields exactly the surgical fix," line 75) only asserts the SANDBOX fixture's
guarantee ("applying the PR clears detection — `heal()` confirms") — that guarantee lives in
the sandbox's `failure_modes.py`, not in any real product loop.** Nothing wires "the human
merged it, now go check if it actually worked" into a real pipeline.

**Consequence, confirmed as a real risk, not hypothetical**: `proactive-pipeline-ingestion-
monitoring.md`'s Invariant 3 (cooldown key `(workspace_id, source_type, job_id, failure_type)`,
default 1hr window) keys on the FAILURE SIGNATURE, not "was the last alert resolved." A merged
fix that is WRONG — doesn't actually address the root cause — would leave the SAME
`failure_type` recurring on the SAME `job_id`. The watchdog has no "did the fix land" state,
only "have I alerted on this signature recently" — so a bad merge gets SILENTLY SUPPRESSED for
up to the cooldown window, the opposite of what Frank needs to trust this feature. This is a
real correctness gap this spec must close, not a nice-to-have.

**Proposed design** (new scope, not yet ticketed — flagging for a dedicated follow-up spec pass
before BH-1047 is built, since this changes BH-1047's contract):

1. **The cooldown key gets a third state, not just "cooling down" vs "cold."** When a PR
   resulting from this loop MERGES, the cooldown entry for that `(workspace_id, source_type,
   job_id, failure_type)` transitions to `VERIFYING` (not `SUPPRESSED`) — a state that shortens
   the next poll interval for THIS specific signature (e.g. poll within 15 min instead of
   waiting out the full cooldown) rather than lengthening it.
2. **On the next poll after `VERIFYING`, two outcomes, both real signals, neither silent**:
   - Failure signature is GONE (the job succeeded) → close the loop, notify success ("the fix
     you merged worked — here's the run that confirms it") on the SAME alert thread, giving
     Frank's team positive confirmation, not just an absence of a second alert.
   - Failure signature RECURS → this is NOT the same alert as before; it is a DISTINCT,
     higher-severity signal ("the fix merged on {date} did not resolve this — same failure
     recurred") that bypasses the normal cooldown entirely, since silence here is the exact
     trust failure this whole epic exists to prevent.
3. **This is NOT an automatic retry loop that keeps proposing new fixes unattended** — that
   would reintroduce the auto-merge risk GC-17 exists to close, just one layer removed (an
   agent that keeps proposing fix-after-fix without a human in the loop is barely different
   from one that merges its own fix). The loop's job is DETECTION + HONEST REPORTING of
   whether the human's merge worked — a new fix proposal after a failed one goes through the
   SAME human-approval gate as the first, not an autonomous retry.

**New ticket needed** (not filed yet — flagging here first since it changes an existing
ticket's contract): extend BH-1047's scope (or a dedicated follow-up) to add the `VERIFYING`
cooldown state + the two-outcome poll logic above. This is the single most important open
design gap in the whole Loop Capital chain as of this pass — everything else this session
fixed was tracking/traceability; this is a genuine missing product behavior.

## Dependencies

- **dbt agent scoped-PR path** — exists + verified live (BH-526). Reuse, don't rebuild.
- **GAP-2 schema introspection** — drift detection rides on schema-version comparison.
- **Longitudinal monitoring** (`longitudinal-monitoring.md`) — optional trigger source; the anomaly event can fire the loop.
- **Lineage/run-log surface** — Dagster/OpenLineage read path (Longaeva's stack); product equivalent needed.

## Ticket Breakdown

| Ticket | Repo | Gate |
|---|---|---|
| Port the 4 `detect()` functions into the agent | brightbot | unit (4 modes) + integ vs live LONGAEVA_POC fixtures |
| Diagnosis step (logs + lineage + schema → classify + root-cause) | brightbot | behavior |
| Surgical-PR emission (reuse dbt scoped-PR path; surgical DDL only; no auto-merge) | brightbot | behavior + write-safety review |
| Lineage/run-log read path | brightbot + platform-core | integ |
| Trigger wiring (pipeline-failure event / anomaly) | brightbot | integ |
| **Post-merge verification loop (`VERIFYING` cooldown state + two-outcome poll)** — new, not yet filed, see "Post-merge verification loop" above | brightbot | behavior + real-behavior (a merged fix's actual re-run result must be observed, not mocked) |
| Flip GC-11 skip → live (4/4 modes → surgical PR on staging) | brightbot | full Gherkin / UAT |

## Related

- `clients/trials/longaeva/BRIGHTHIVE_GAPS.md` §GAP-7 — gap inventory + effort/owner
- `clients/trials/longaeva/sandbox/self_healing/failure_modes.py` — proven reference (4 modes, detect/fix/heal)
- `longitudinal-monitoring.md` — sibling GAP-8 spec; shares the anomaly-trigger + agent pattern
- `brightbot/tests/integration/golden_cases/test_gc_11_self_healing.py` — acceptance bar ("4/4 → surgical PR")
- **Consumed by** (verified 2026-07-10, no taxonomy change needed): `proactive-pipeline-ingestion-monitoring.md` — routes job/run-STATUS watchdog signals whose root cause is DATA_SHAPE (schema drift/missing partition/broken stage/dbt contract) into this spec's EXISTING surgical-PR loop as an additional trigger source. Confirmed this spec's 4-mode `FailureMode` taxonomy does NOT extend to job-runtime failures (timeouts, cluster OOM) — those get retry/escalate/alert-only instead, never a fabricated mode here.
- **Gap noted 2026-07-10 (pass 32 of the consuming spec's verification loop)**: this spec has no §8 Eval Criteria section. Its Gherkin asserts diff-scoping in prose ("the diff is scoped to the failure") with no deterministic backing check. `proactive-pipeline-ingestion-monitoring.md`'s BH-1047 will build a `RemediationScopeEvaluator` (deterministic diff-analysis GATE) while wiring in its own trigger source — this spec should adopt that evaluator as its own §8 once built, rather than leaving the prose assertion unchecked.
