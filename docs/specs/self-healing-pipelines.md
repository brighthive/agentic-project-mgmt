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
```

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
| Flip GC-11 skip → live (4/4 modes → surgical PR on staging) | brightbot | full Gherkin / UAT |

## Related

- `clients/trials/longaeva/BRIGHTHIVE_GAPS.md` §GAP-7 — gap inventory + effort/owner
- `clients/trials/longaeva/sandbox/self_healing/failure_modes.py` — proven reference (4 modes, detect/fix/heal)
- `longitudinal-monitoring.md` — sibling GAP-8 spec; shares the anomaly-trigger + agent pattern
- `brightbot/tests/integration/golden_cases/test_gc_11_self_healing.py` — acceptance bar ("4/4 → surgical PR")
- **Consumed by** (verified 2026-07-10, no taxonomy change needed): `proactive-pipeline-ingestion-monitoring.md` — routes job/run-STATUS watchdog signals whose root cause is DATA_SHAPE (schema drift/missing partition/broken stage/dbt contract) into this spec's EXISTING surgical-PR loop as an additional trigger source. Confirmed this spec's 4-mode `FailureMode` taxonomy does NOT extend to job-runtime failures (timeouts, cluster OOM) — those get retry/escalate/alert-only instead, never a fabricated mode here.
- **Gap noted 2026-07-10 (pass 32 of the consuming spec's verification loop)**: this spec has no §8 Eval Criteria section. Its Gherkin asserts diff-scoping in prose ("the diff is scoped to the failure") with no deterministic backing check. `proactive-pipeline-ingestion-monitoring.md`'s BH-1047 will build a `RemediationScopeEvaluator` (deterministic diff-analysis GATE) while wiring in its own trigger source — this spec should adopt that evaluator as its own §8 once built, rather than leaving the prose assertion unchecked.
