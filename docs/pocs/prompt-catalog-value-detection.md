---
title: "Prompt Catalog + Value Detection — Longitudinal Prompt Store for BrightHive"
date: "2026-07-03"
duration: "1-day design POC (no code — comparative analysis)"
decision: "Deferred — recommend Approach C, gate on BH-942 shipping first"
status: "Complete"
methodologies_compared:
  - "A: BrightRoutines detector only (status quo)"
  - "B: UserActivityEvent store + signature dedup (BH-942)"
  - "C: UserActivityEvent + signature + LLM value-tagging (BH-942 + BH-XXX)"
epic: "BH-876"
tags: [prompt-catalog, longitudinal-memory, value-detection, brightroutines, spec-extension]
related:
  specs: [user-activity-event-store.md, brightroutines-intent-loop.md]
  bedrock: []
  features: []
---

# Prompt Catalog + Value Detection

## Question

**Kuri, 2026-07-03**: *"do we need a system that is tracking all prompts that ever are run, and~ tagged and catalog so we can infer the repetition of these? it may be that we even have 1-shot prompts that are so worth-it that chances of prioritizing to schedule are 95%>"*

Restated as a decision question: **should the platform maintain a canonical, longitudinal, cross-workspace store of every user prompt — with a signature for dedup, a value tag for prioritization, and a browsable surface — separate from `ProactiveSignal`?**

Two sub-questions this POC answers:

1. **Repetition detection**: `ProactiveSignal` today captures schedulable candidates that pass a routine-detector filter. That's a subset. A one-shot high-value prompt (e.g. a Board-report request that runs once but is worth 95% of the value the user extracts from the platform in a quarter) never becomes a `ProactiveSignal` and therefore doesn't influence any routine / suggestion / score. What data model catches those?
2. **Value inference**: Given every prompt, can we score its *value-if-recurred* (independent of whether it did recur) — so a one-shot 95%-value prompt gets surfaced without waiting for it to repeat three times?

## Methodologies

### Approach A: Status quo — BrightRoutines detector only

**What it captures**: `ProactiveSignal` rows written by capture middleware only when the chat turn resembles a schedulable action (title/summary/cadence-hint/delivery-hint match). Everything else is dropped on the floor. `RoutineJudge` scores confidence on a per-pattern basis (3+ signals with cohesion). One-shot prompts are invisible.

**Storage**: Existing `brightroutines-{env}` DynamoDB table. No cross-workspace read — every query is scoped to `WORKSPACE#<id>`.

**Retrieval**: `list_signals_by_workspace(...)` for the workspace's own signals. Nothing browsable at the org level.

**Cost**: Zero net-new — it's what's shipped.

### Approach B: Foundational — `UserActivityEvent` store per BH-942

**What it captures**: **Every** user-originated intent turn, regardless of whether it's schedulable. `UserActivityEvent` (per BH-942 §2.1) has fields `user_id`, `workspace_id`, `project_id`, `kind` (chat_turn, tool_invocation, dashboard_view, etc.), `signature` (fingerprint of the normalized ask), `summary` (counts-only redaction — no raw text on the wire), `observed_at`. `ProactiveSignal` becomes a *projection* of the subset where `kind == chat_turn` and `intent_kind` was inferred by the schedulability capture path.

**Storage**: DynamoDB single-table extension of `brightroutines-{env}` per BH-942 §4 — new `SK` prefix `EVENT#<observed_at>#<event_id>`, GSI `USER_ACTIVITY#<user_id>` for per-user history.

**Retrieval**:
- `list_events_by_user(user_id, since)` — the user's own history.
- `list_events_by_signature(workspace_id, signature, since)` — repetition detection across a workspace.
- `list_events_by_kind(workspace_id, kind, since)` — kind-level slicing.

**Value inference**: Repetition count per `signature` is queryable, so recurring high-frequency prompts are trivially rankable. **One-shot value is NOT scored** — a single event with `signature=X` has the same repetition rank as an unused signature.

**Cost**: On top of Approach A, ~10-30x write volume (every turn, not just schedulable ones). At Longaeva's current scale (~50 turns/user/week × 20 users × 4 workspaces = 4k events/week), the DynamoDB PAY_PER_REQUEST bill is under $5/month — cost is not the constraint.

### Approach C: Foundational + LLM value-tagging — `UserActivityEvent` + per-event `value_score`

**What it captures**: Same as Approach B, plus a `value_score: float ∈ [0, 1]` attribute on each event, produced by an LLM judge at capture time (or in a batched offline pass) that estimates *"if this ask were to recur on a routine cadence, how valuable would that be?"* — independent of whether it did recur. Prompt shape:

```
System: You are a business-value judge for BrightHive activity events.
User: A workspace user asked their assistant to <normalized_ask>. On a scale
      of 0.0-1.0, if this exact ask were scheduled to auto-run and deliver a
      result to the user on a recurring cadence, how valuable would that
      likely be to a data-savvy business stakeholder?
      Consider: reporting cadence value, decision-support value, monitoring
      value. Do NOT reward "sounds impressive"; reward "would this show up on
      a Monday-morning dashboard".
      Return {value_score, rationale}.
```

**Storage**: Same as B, plus a GSI on `VALUE_SCORE#<workspace_id>` with `SK = <inverted_value_score>#<observed_at>` for leaderboard queries.

**Retrieval**:
- All of B, plus:
- `high_value_one_shots(workspace_id, since, min_value=0.75)` — the 95%+ single-occurrence prompts Kuri asked about.
- `browse_catalog(workspace_id, cursor, filters)` — the browsable surface (MCP tool + optional webapp UI).

**Value inference**: Directly scored. `value_score` + repetition count together drive proactive-routine suggestions AND one-shot escalations (BH-949's "should we offer a scheduled version of this after ONE observation" decision).

**Cost**: On top of B, one small-model LLM call per event. At 4k events/week × ~500 input + 100 output tokens × Haiku pricing ≈ **$2-5/week**, well inside budget. Latency is not user-facing — capture middleware fires the call async and writes back the score.

## Success Criteria

| Metric | Target | Why This Matters |
|--------|--------|-----------------|
| **Coverage**: fraction of user prompts represented in the catalog | ≥ 95% | Answers Kuri's foundational Q — no user ask is dropped on the floor |
| **Repetition dedup precision**: same intent recognized under paraphrase | ≥ 0.80 | If dedup misclassifies "generate the Board deck" as two distinct signatures, repetition scoring is noise |
| **One-shot value precision**: LLM value-score identifies human-labeled high-value prompts | ≥ 0.75 (top-decile) | The whole reason for value-tagging — must beat "wait for 3 repetitions" |
| **Browse-catalog latency (p95)**: MCP list query for one workspace | < 500ms | Interactive-feel, not batch |
| **Cost**: net-new monthly per workspace | < $50 | Order-of-magnitude cheaper than what a routine saves the user |
| **PII exposure**: raw prompt text on the wire | 0 | Non-negotiable per BH-942 §3 invariants + BH-876 §9 invariant 3 |

## Results — Qualifying Numbers

Design-POC only — no live measurements. Numbers below are estimates from adjacent shipped systems (BrightRoutines detector rollout on staging, judge calibration corpus, DynamoDB cost benchmarks from BH-882 CDK) and clearly labeled as such.

### Comparison Table

| Metric | A (status quo) | B (BH-942 store) | C (B + value-tag) | Winner |
|--------|----------------|------------------|-------------------|--------|
| Coverage (all prompts) | ~15% (schedulable-only) | ≥ 95% | ≥ 95% | **B / C tie** |
| Repetition dedup precision | 0.85 (on schedulable subset — measured BH-884) | 0.85 (same signature algo) | 0.85 | **tie** |
| One-shot value inference | **not supported** | **not supported** | ≈ 0.75-0.85 (est. — reuses BH-884 judge calibration corpus, adds value axis) | **C** |
| Browse-catalog latency p95 | n/a — no surface | ~200ms (GSI3 by user, existing infra) | ~200ms (same infra) | **B / C tie** |
| Net-new cost/workspace/month | $0 | ≤ $5 (DDB) | ≤ $15 (DDB + Haiku) | **A → C is 3× more but absolute cost is negligible** |
| PII exposure | 0 (counts-only already enforced) | 0 (BH-942 §3 invariant) | 0 (value judge sees normalized signature, NOT raw text) | **all pass** |
| Enables BH-949 "one-observation escalation" | ❌ | ⚠️ partial (repetition = 1 is invisible from value angle) | ✅ | **C** |
| Time-to-first-value for Longaeva UAT | shipped | ~2 weeks (BH-942 impl) | ~3 weeks (BH-942 + value axis) | **B slightly faster** |

### Detailed Results

#### Approach A
- **Blind spot**: 85% of turns invisible. If Longaeva's Board wants a monthly narrative, and the user asks for it once as a one-shot, we never see it and never suggest a routine. High-value low-frequency asks are exactly where the platform's differentiation is — losing them is a product-value loss, not just a completeness gap.
- **Repetition detection works fine on its subset** but is fundamentally scoped to schedulable-looking asks per capture middleware's classifier — a false-negative in the classifier is a permanent loss.

#### Approach B
- **Covers the foundational gap**. Every turn becomes visible. Repetition detection works across kinds (chat + tool + dashboard-view + report-view — a user staring at a dashboard 3x/week is a routine signal that Approach A never sees).
- **Still misses one-shot value**. A user asks for the Board deck once; it never recurs; without a value tag, it sits in the log unreadably alongside 4000 other events. Kuri's specific ask (*"1-shot prompts worth 95%"*) is NOT answered by B alone.
- **Migration risk**: `ProactiveSignal` becomes a projection. That's a substantial refactor. Manageable if BH-942 §11 ADR is followed strictly.

#### Approach C
- **Directly answers Kuri's question**. One-shot value inference is the whole reason C exists.
- **Dependency on LLM judge quality**. Same discipline BH-884 already established: real-behavior corpus, N=3 quorum, model-agnostic tier config, offline calibration before promotion. Precedent exists — this is not new infra to build, it's the schedulability judge repointed at "value-if-recurred".
- **Extra $10/workspace/month** vs B. Negligible next to routine value if even one recurring routine ships per workspace.
- **The extra complexity is real**: value_score is a decision-relevant number that will drive UI and pricing signal. It needs its own eval corpus and drift monitoring — treat as first-class per BH-884's judge calibration pattern, not as a metadata field.

## Decision

**Deferred — recommend Approach C, but gate on B shipping first.**

Rationale:

1. **B is a hard prerequisite for C**. Value-tagging without foundational coverage is a UI on top of nothing. Ship BH-942 first, prove `UserActivityEvent` works end-to-end, migrate `ProactiveSignal` to a projection (BH-942 §11 ADR), *then* layer the value axis.
2. **The value-tagging path has a de-risked precedent** (BH-884 judge) but needs its own eval corpus. That's a real 2-3 week effort — not vaporware, but not free either. It should get its own ticket.
3. **Skipping straight to C is tempting** and would answer Kuri's question immediately. It's rejected because a value-score without foundational storage lands as a bolt-on metadata field on `ProactiveSignal`, which entrenches the schedulable-only blind spot rather than fixing it.
4. **Approach A is a No-Go** as a permanent answer — it's the status quo, it's what surfaces the gap in the first place.

## Learnings

- **The routine detector was solving the wrong problem to answer Kuri's question**. It optimizes for "3+ observations with cohesion" — that's a recurring-pattern classifier, not a value classifier. Value can be present on turn 1.
- **Cost is not the constraint**. Even the most aggressive (C) is under $20/workspace/month. The constraint is *judge quality* — a bad value-score is worse than no value-score because it drives UI decisions that erode trust.
- **`ProactiveSignal` was a symptom of not-yet-having a canonical activity store**. Every downstream feature that could be built on `UserActivityEvent` was instead built on the narrower shape, forcing repeated back-fits. BH-942 unblocks a category of features, not just one.
- **The dedup signature algorithm is doing more work than credited**. It's the load-bearing part of both B and C. Any regression there (see BH-884's signature computation) breaks repetition detection across the whole product. Signature quality deserves its own eval corpus separate from the value judge.

## Next Steps

- **Immediate** (no ticket needed): update `docs/specs/brightroutines-intent-loop.md` §14 (non-goals) to remove the "prompt catalog UI/API deferred" line and link to this POC.
- **BH-942 (already open)**: proceed with the foundational spec + implementation. This POC does not change its scope; it clarifies why it's foundational.
- **New ticket (post-BH-942 merge)**: *"Value-score axis on `UserActivityEvent` — LLM judge for one-shot value inference"*. Scope:
  - Reuse BH-884 judge pattern (Protocol + Fake + real triad, model-agnostic tier via env var).
  - Ship offline eval corpus (target 100-200 hand-labeled events across `kind` mix, Longaeva as anchor).
  - Async capture-time value-tagging, write-back to event row.
  - GSI for `VALUE_SCORE#<workspace_id>` leaderboard.
  - MCP tool `get_high_value_activity` (list top-N by value_score for a workspace, filterable by `kind` and `since`).
  - Do NOT ship a webapp catalog UI in the same ticket — that's a separate BH-XXX-webapp scope.
- **BH-949 (blocked on product)**: the "one-observation escalation" decision Kuri owes an answer on is exactly what Approach C makes viable. Route the question back to product with this POC as context.

## Artifacts

- **Related specs**: `docs/specs/user-activity-event-store.md` (BH-942), `docs/specs/brightroutines-intent-loop.md` §14/§15
- **Reference implementation for value-judge shape**: `../brightbot/brightbot/routines/judge.py` (BH-884 — RoutineJudge Protocol + LLMRoutineJudge + FakeRoutineJudge)
- **Cost baseline**: `../brighthive-platform-core/brighthive_core/brightroutines_data_stack.py` (BH-882 — DDB PAY_PER_REQUEST)
- **Signature algorithm precedent**: `../brightbot/brightbot/routines/dtos.py::AutomationSignature`
