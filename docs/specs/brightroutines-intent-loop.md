---
title: BrightRoutines Intent Loop
epic: BH-876
tickets: [BH-882, BH-883, BH-884, BH-885, BH-886, BH-887, BH-888, BH-889, BH-944, BH-945, BH-946, BH-948, BH-949, BH-950, BH-954, BH-955, BH-956, BH-957, BH-958, BH-959, BH-960, BH-961, BH-962, BH-963, BH-964, BH-965, BH-966, BH-967, BH-968, BH-969, BH-970, BH-1001, BH-1002, BH-1003, BH-1004]
author: codex
status: implemented-verified-staging
created: 2026-06-30
last-reviewed: 2026-07-13
generates: tickets
tags:
  - brightagent
  - routines
  - intent-detection
  - proactive-agents
related:
  features: []
  pocs: []
  bedrock: []
---

# SPEC: BrightRoutines Intent Loop

> Scope: P2-P4 for BrightRoutines. This spec adds cross-session,
> workspace-scoped learning that detects repeated schedulable intent and offers
> a Routine. The manual execution substrate is specified in
> `brightroutines-execute-workflow-schedule.md`.

## Jira Tickets

| Ticket | Repo | Refined Scope | Phase | Depends On |
|---|---|---|---:|---|
| [BH-876](https://brighthiveio.atlassian.net/browse/BH-876) | all | Epic: BrightRoutines | - | - |
| [BH-882](https://brighthiveio.atlassian.net/browse/BH-882) | `brighthive-platform-core` | Provision `brightroutines-{env}` single-table schema, GSIs, TTL, env vars, and IAM grants with capacity guardrails and an embedding sidecar/size policy. | P2 | BH-881 |
| [BH-883](https://brighthiveio.atlassian.net/browse/BH-883) | `brightbot` | Add Pydantic DTOs, repository Protocols, `ProactiveSignal` store, redaction, bounded after-agent capture queue, drop/rate metrics, and tests. | P2 | BH-882 |
| [BH-884](https://brighthiveio.atlassian.net/browse/BH-884) | `brightbot` | Build shadow detector with paginated reads, configurable thresholds, judge interface, idempotent `RecurringAutomationPattern`/`RoutineSuggestion` state transitions, suppression, metrics, and evals. | P2 | BH-883 |
| [BH-885](https://brighthiveio.atlassian.net/browse/BH-885) | `brightbot` | Add routine suggestion service/routes for list, schedule, dismiss with RBAC, conditional transitions, WorkflowSpec factory client, and P1 `ScheduleRoutineRequest` integration. | P3 | BH-884 |
| [BH-886](https://brighthiveio.atlassian.net/browse/BH-886) | `brighthive-webapp` | Add `useRoutineSuggestions`, Suggested Routines cards, schedule/dismiss actions, and `workflow_suggestion` inbox handling with responsive states. | P3 | BH-885 |
| [BH-887](https://brighthiveio.atlassian.net/browse/BH-887) | `brightbot-slack-server` | Add `workflow_suggestion` stage, formatter, Block Kit buttons, and real async schedule/dismiss handlers that ack within 3s and call BrightBot idempotently. | P3 | BH-885 |
| [BH-888](https://brighthiveio.atlassian.net/browse/BH-888) | `brightbot`, `platform-core` | Add feature flags, precision/schedule/dismiss metrics, threshold config, suppression operations, and circuit breaker for live proactive offers. | P4 | BH-885, BH-886, BH-887 |
| [BH-889](https://brighthiveio.atlassian.net/browse/BH-889) | `brightbot`, `brighthive-e2e` | Add labeled routine corpus, L1/L2 evaluator, e2e spec/tracker bindings, and tests for capture, detector, suggestion schedule/dismiss, and notification delivery. | P2-P4 | each phase |

**Execution order**: P1 foundation ([BH-877](https://brighthiveio.atlassian.net/browse/BH-877)-[BH-881](https://brighthiveio.atlassian.net/browse/BH-881)) -> BH-882 -> BH-883 -> BH-884 -> BH-885 -> (BH-886 + BH-887) -> BH-888; BH-889 gates each phase.

---

## 1. Context

### Problem

BrightAgent answers the current turn but does not compound repeated work across
users in a workspace. Mem0 and thread checkpoints preserve per-user/thread
context, but there is no structured, cross-user, workspace-owned signal that
learns "this task keeps happening" and offers to automate it.

### Goal

When repeated, successful, schedulable `AutomationIntent` appears across a
workspace, BrightAgent records `ProactiveSignal` events, detects a
`RecurringAutomationPattern`, creates a `RoutineSuggestion`, and lets an
Admin/Collaborator schedule it as a `RoutineSchedule`. Scheduling creates a
WorkflowSpec if needed, creates an `execute_workflow` schedule, and records
feedback for future threshold tuning.

### Example

Three analysts ask for weekly earnings reporting. BrightAgent extracts the same
`AutomationIntent` from those turns, groups them by `AutomationSignature`,
detects recurrence, offers "Schedule weekly earnings report?", and on approval
creates a `RoutineSchedule` that runs headlessly and delivers results.

---

## 2. Current Situation

> **BH-942 note (added 2026-07-03)**: `ProactiveSignal` (defined in this
> spec's §3) is the platform's first user-shaped per-turn record. A
> proposed foundational spec —
> [`user-activity-event-store.md`](./user-activity-event-store.md) —
> generalizes it into a canonical `UserActivityEvent` store consumed by
> BrightRoutines detector + scoring, plus future features (prompt
> catalog, cost attribution, HITL replay). Once approved, ProactiveSignal
> becomes a Pydantic view over `CHAT_TURN`-kind rows rather than a
> separately-persisted DTO. This spec's §4 storage keys survive the
> rename verbatim; only the table name and the addition of GSI6–GSI8
> change downstream.

### Existing Reuse

- `deep_agent` middleware has `before_agent` and `after_agent` hooks and
  already extracts `workspace_id`, `user_id`, `user_email`, `turn_id`, and the
  last human message.
- LangGraph thread metadata is already partitioned by `user_id` and
  `workspace_id`; checkpoints remain available as raw-text backfill.
- Scheduled agents CRUD and EventBridge scheduling already exist in BrightBot.
- WorkflowSpec AGENT execution already exists in Platform Core and BrightBot.
- Webapp Schedules and Notifications already exist.
- Slack BrightSignals already has Block Kit notification rendering, action-id
  routing, and SSE/webapp delivery.

### Gaps

- No structured per-turn `ProactiveSignal` capture.
- No workspace-level proactive signal table.
- No recurring automation pattern detection.
- No `RoutineSuggestion` ledger, cooldown, or suppression state.
- No offer surfaces in webapp or Slack.
- No `ScheduleRoutineRequest` path that creates WorkflowSpec plus schedule from
  a suggestion.
- No online precision/acceptance metrics for proactive offers.

---

## 3. Naming And DTO Contract

Lifecycle:

```text
ProactiveSignal -> AutomationIntent -> AutomationSignature -> RecurringAutomationPattern -> RoutineSuggestion -> ScheduleRoutineRequest -> RoutineSchedule
```

Naming rules:

- Do not use `canonical_*`, `candidate`, or `params` in new DTOs.
- Use `AutomationSignature.fingerprint` for the grouping key. It is internal
  and not product copy.
- Public APIs expose `RoutineSuggestion` and `RoutineSchedule`. Patterns are
  detector internals unless an admin/debug surface explicitly needs them.
- Python class names use PEP 8 PascalCase. DTO fields use snake_case.
- DTOs are Pydantic v2 boundary objects. They must not call repositories,
  model providers, DynamoDB, or GraphQL clients.
- Store, judge, workflow, and scheduler clients are injected behind Protocols
  so capture, detection, and API routes stay testable and extensible.

Required DTO shapes:

```python
class AutomationSignature(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, str_strip_whitespace=True, frozen=True)
    fingerprint: str = Field(..., description="Stable hash used to group similar automation intents.", examples=["sha256:v1:weekly-earnings-report"])
    normalized_action: str = Field(..., description="Normalized verb for the work request.", examples=["generate"])
    normalized_object: str = Field(..., description="Normalized object of the work request.", examples=["earnings report"])
    normalized_scope: str | None = Field(None, description="Normalized scope when the request implies one.", examples=["workspace"])
    parameter_keys: list[str] = Field(default_factory=list, description="Stable sorted input keys used by the task.", examples=[["metric", "scope"]])
```

```python
class AutomationIntent(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, str_strip_whitespace=True, frozen=True)
    title: str = Field(..., description="Short user-facing task title.", examples=["Weekly earnings report"])
    summary: str = Field(..., description="Redacted normalized task summary.", examples=["Generate a weekly earnings report for the workspace."])
    intent_kind: AutomationIntentKind = Field(..., description="Schedulability category.", examples=["REPORT"])
    schedulable: bool = Field(..., description="Whether the intent can become a routine.", examples=[True])
    cadence_hint: CadenceHint | None = Field(None, description="Inferred cadence.", examples=["WEEKLY"])
    delivery_hint: DeliveryHint | None = Field(None, description="Inferred delivery channel.", examples=["WEBAPP"])
    inputs: dict[str, str | int | float | bool | list[str]] = Field(default_factory=dict, description="Redacted structured inputs.", examples=[{"metric": "earnings"}])
    signature: AutomationSignature = Field(..., description="Comparable signature used by the detector.")
    confidence: float = Field(..., ge=0, le=1, description="Classifier confidence.", examples=[0.91])
```

```python
class ProactiveSignal(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, str_strip_whitespace=True, frozen=True)
    signal_id: str = Field(..., description="Unique proactive signal ID.", examples=["sig_01JZ..."])
    workspace_id: str = Field(..., description="Workspace that owns the signal.", examples=["workspace_123"])
    user_id: str = Field(..., description="User whose turn produced the signal.", examples=["user_123"])
    user_role: str | None = Field(None, description="Workspace role observed at capture time.", examples=["WORKSPACE_ADMIN"])
    thread_id: str | None = Field(None, description="LangGraph thread ID.", examples=["thread_123"])
    turn_id: str | None = Field(None, description="BrightBot turn ID.", examples=["turn_123"])
    observed_at: datetime = Field(..., description="When the signal was observed.")
    source: ProactiveSignalSource = Field(..., description="Surface that produced the signal.", examples=["brightbot_chat"])
    intent: AutomationIntent = Field(..., description="Normalized automation intent.")
    outcome_ok: bool | None = Field(None, description="Whether the agent turn appeared successful.", examples=[True])
```

```python
class RoutineSuggestion(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, str_strip_whitespace=True, frozen=True)
    routine_suggestion_id: str = Field(..., description="Unique suggestion ID.", examples=["rsug_01JZ..."])
    workspace_id: str = Field(..., description="Workspace that owns the suggestion.", examples=["workspace_123"])
    pattern_id: str = Field(..., description="RecurringAutomationPattern that produced the suggestion.", examples=["pat_01JZ..."])
    title: str = Field(..., description="User-facing routine title.", examples=["Weekly earnings report"])
    description: str = Field(..., description="Redacted routine description.", examples=["Generate and deliver the weekly earnings report."])
    proposed_cadence: Cadence = Field(..., description="Suggested schedule cadence.")
    proposed_delivery: DeliveryConfig = Field(..., description="Suggested delivery channels.")
    evidence_summary: RoutineEvidenceSummary = Field(..., description="Counts-only evidence shown to users.")
    status: RoutineSuggestionStatus = Field(..., description="Suggestion lifecycle status.", examples=["OFFERED"])
```

```python
class ScheduleRoutineRequest(BaseModel):
    model_config = ConfigDict(serialize_by_alias=True, str_strip_whitespace=True, frozen=True)
    routine_suggestion_id: str | None = Field(None, description="Suggestion being scheduled, if any.", examples=["rsug_01JZ..."])
    project_id: str | None = Field(None, description="Existing WorkflowSpec project ID, if already created.", examples=["project_123"])
    title: str | None = Field(None, description="Optional override for the routine title.", examples=["Weekly earnings report"])
    cadence: Cadence = Field(..., description="Requested schedule cadence.")
    delivery: DeliveryConfig = Field(..., description="Requested delivery channels.")
```

---

## 4. Data Model

Use one DynamoDB table owned by the feature, provisioned through Platform Core
CDK and granted to BrightBot:

`BRIGHTROUTINES_TABLE = brightroutines-{env}`

### 4.1 ProactiveSignal

```text
PK = WORKSPACE#<workspace_id>
SK = SIGNAL#<iso_timestamp>#<signal_id>
GSI1PK = SCHEDULABLE#<workspace_id>
GSI1SK = <iso_timestamp>#<intent.signature.fingerprint>
GSI2PK = USER#<workspace_id>#<user_id>
GSI2SK = <iso_timestamp>
ttl = now + 35 days
```

Attributes:

- `signal_id`
- `workspace_id`
- `turn_id`
- `thread_id`
- `user_id`
- `user_role`
- `observed_at`
- `source`
- `intent`: `AutomationIntent`
- `embedding`: vector for similarity checks, compressed/encoded or sidecar
  stored if item size requires it
- `outcome_ok`: boolean or null
- `raw_excerpt`: redacted, max 500 chars, TTL 35 days

### 4.2 RecurringAutomationPattern

```text
PK = WORKSPACE#<workspace_id>
SK = PATTERN#<pattern_id>
GSI3PK = PATTERN_STATUS#<workspace_id>#<status>
GSI3SK = <last_detected_at>
```

Attributes:

- `pattern_id`
- `workspace_id`
- `representative_intent`: `AutomationIntent`
- `fingerprint`: copied from `AutomationSignature.fingerprint`
- `status`: OBSERVING, READY_TO_SUGGEST, SUPPRESSED
- `recurrence_score`
- `confidence`
- `evidence_summary`: counts only, never raw cross-user text
- `signal_count`
- `distinct_user_count`
- `window_start`, `window_end`
- `last_suggestion_id`
- `cooldown_until`
- `created_at`, `updated_at`, `last_detected_at`

### 4.3 RoutineSuggestion

```text
PK = WORKSPACE#<workspace_id>
SK = SUGGESTION#<routine_suggestion_id>
GSI4PK = SUGGESTION_STATUS#<workspace_id>#<status>
GSI4SK = <offered_at>
```

Attributes:

- `routine_suggestion_id`
- `workspace_id`
- `pattern_id`
- `title`
- `description`
- `proposed_cadence`
- `proposed_delivery`
- `evidence_summary`: counts only, never raw cross-user text
- `status`: OFFERED, SCHEDULING, SCHEDULED, DISMISSED, EXPIRED, SUPPRESSED
- `offer_count`
- `dismiss_count`
- `scheduled_by_user_id`
- `owner_user_id`
- `linked_project_id`
- `linked_workflow_spec_id`
- `linked_schedule_id`
- `cooldown_until`
- `created_at`, `updated_at`, `offered_at`

`RoutineSchedule` rows live in the scheduled-agents table from
`brightroutines-execute-workflow-schedule.md`; this feature stores only the
links to those rows.

---

## 5. Capture Contract

Add `IntentCaptureMiddleware` to `deep_agent` after `EndProcessingMiddleware`
or inside the same `after_agent` phase with explicit ordering.

Rules:

- Capture is best effort and non-blocking; agent response latency must not wait
  on LLM calls or DynamoDB writes.
- The hook submits work to a bounded executor/queue and drops on overflow.
- The worker uses Haiku to extract an `AutomationIntent` from only the latest
  user turn plus local metadata. It must not send raw cross-user text to the
  classifier.
- The capture worker writes a `ProactiveSignal` row only when `workspace_id`,
  `user_id`, and human text are present.
- Capture failures log structured warnings but never fail the agent turn.

Classifier output:

```json
{
  "intent": {
    "title": "Weekly earnings report",
    "summary": "Generate a weekly earnings report for the workspace.",
    "intent_kind": "REPORT",
    "schedulable": true,
    "cadence_hint": "WEEKLY",
    "delivery_hint": "WEBAPP",
    "inputs": {
      "metric": "earnings",
      "scope": "workspace"
    },
    "signature": {
      "fingerprint": "sha256:v1:...",
      "normalized_action": "generate",
      "normalized_object": "earnings report",
      "normalized_scope": "workspace",
      "parameter_keys": ["metric", "scope"]
    },
    "confidence": 0.91
  },
  "raw_excerpt": "weekly earnings report"
}
```

---

## 6. Detection Contract

Run a nightly EventBridge job or LangGraph scheduled job in shadow mode first.

Pattern detection window:

- Read only signals with `intent.schedulable=true` from the last 28 days.
- Group by `intent.signature.fingerprint` and embedding cosine similarity >=
  0.86.
- Cadence is an intent hint, not part of the fingerprint.
- Create or refresh a `RecurringAutomationPattern` only when trust gates pass.
- Create a `RoutineSuggestion` only when the pattern is ready and not cooling
  down.

Trust gates:

1. `intent.intent_kind` is REPORT, EXTRACT, or MONITOR.
2. At least 3 distinct users in 28 days AND those users are not all members of
   a single manager→reports chain, or one user at least 5 times across at
   least 3 weeks. **No reporting-hierarchy data source exists yet (§17.4,
   BH-949) — until one is wired in, the manager-chain sub-clause fails
   closed: user-breadth alone cannot pass gate 2. Only the single-user
   5×/3wk cadence path is currently reliable.** Flagged as a P0 follow-up,
   not backlog — the live detector (BH-884) has no hierarchy check today.
3. `outcome_ok_rate >= 0.8` for rows with known outcome.
4. Pattern cohesion >= 0.86.
5. Cadence consistency >= 60 percent when cadence is inferred.
6. Sonnet schedulability judge confidence >= 0.85.
7. Workspace has no live `RoutineSuggestion` in the last 14 days for a
   different pattern.
8. Pattern and suggestion are not suppressed.

The judge receives `AutomationIntent` titles, summaries, redacted inputs,
aggregate counts, and cadence signals. It must never receive raw cross-user
user text.

---

## 7. Routine Suggestion API

Add BrightBot management routes under:

```text
GET  /manage/routine-suggestions
POST /manage/routine-suggestions/{routine_suggestion_id}/schedule
POST /manage/routine-suggestions/{routine_suggestion_id}/dismiss
```

Authentication uses existing Bearer token validation. Authorization:

- Viewer, Contributor, and Agent Guest may not list offered suggestions.
- Admin and Collaborator may list and schedule suggestions when they still have
  `dataAssetRead` and project/workflow permissions.
- Scheduling user becomes `owner_user_id`.

Schedule flow:

1. Re-read `RoutineSuggestion` and conditionally transition
   `OFFERED -> SCHEDULING`.
2. Ensure one Project/WorkflowSpec exists for the suggestion's
   `AutomationIntent`.
3. Ensure the WorkflowSpec has a single AGENT step with `summary-agent` or
   another approved read-only graph.
4. Build `ScheduleRoutineRequest` with `routine_suggestion_id`, cadence,
   delivery, and title.
5. Create an `execute_workflow` schedule through the P1 scheduled-agent path.
6. Store `linked_project_id`, `linked_workflow_spec_id`, and
   `linked_schedule_id`; then transition `SCHEDULING -> SCHEDULED`.
7. Return the `RoutineSchedule` row and deep links.

Dismiss flow:

- First dismiss: status `DISMISSED`, `cooldown_until = now + 90 days`.
- Second dismiss for same pattern/workspace: status `SUPPRESSED`.
- Dismiss is idempotent.

---

## 8. Offer Surfaces

### Webapp — home is `/context/workflows` (FormulasPage)

The intended UI home is `/workspace/:workspaceId/context/workflows`, rendered
by `src/Context/pages/FormulasPage.tsx`. That page is today an **inspirational
preview** — a static grid of Formula categories (Data Transformations,
Calculated Metrics, **Scheduled Actions**, Custom Prompts, Document Pipelines,
Report Templates), every one marked `status: "coming_soon"`. It sets the
product vocabulary for automations in BrightHive; BrightRoutines is the first
*real* implementation of the **Scheduled Actions** category shown there.

Delivery shape:

- Introduce a `SchedulesPage`-style companion or an in-place upgrade of the
  Scheduled Actions card on FormulasPage. Either way, when a workspace has
  active `RoutineSuggestion` rows (status = `OFFERED`) or accepted routines
  (any `ScheduleRoutineRequest` derived from a suggestion), the Scheduled
  Actions card must switch from `coming_soon` to `active` with a count.
- Click-through lands on a "Suggested Routines" list styled to match the
  FormulasPage aesthetic (rounded cards, category color `#F47721` per current
  mock). Each card shows the fields on `RoutineSuggestion`: title, aggregate
  evidence (`RoutineEvidenceSummary` — counts only, no raw text — §9
  invariant 3), inferred cadence, primary actions **Schedule** and **Dismiss**.
- Schedule opens the existing `AddScheduleDialog` prefilled with cadence and
  workflow task details, then commits through the schedule route. This reuses
  the shipped scheduling infrastructure (BH-877/BH-878 execute_workflow) and
  keeps the routine → schedule handoff a one-liner.
- Mobile: cards are single-column on 320px, chips wrap, action buttons stack
  under 480px, tap target ≥ 44px.

Cross-repo consequence: BH-948's `RoutineSuggestion` contract snapshot in
`brightbot/routines/contracts/routine_suggestion.json` is the wire shape the
webapp binds against. Any field rename on the DTO must not land without a
matching webapp update.

Extend Notifications inbox:

- Platform Core `formatSignal` returns `display.type = "workflow_suggestion"`.
- Webapp registers `workflow_suggestion` card with Schedule/Dismiss actions
  that deep-link into `/context/workflows` so the inbox click leaves the user
  on the canonical routines home.

### Slack

Extend BrightSignals:

- Add notification stage `workflow_suggestion`.
- Add Block Kit buttons:
  - `bh_notif_routine_schedule`
  - `bh_notif_routine_dismiss`
- Button value carries `routine_suggestion_id`, `workspace_id`, and `event_id`.
- Handler calls BrightBot schedule/dismiss in the background after `ack()`.
- Slack card never quotes raw user prompts.

---

## 9. Governance Invariants

1. Workspace partition is strict: all signal, pattern, and suggestion reads use
   `PK=WORKSPACE#<workspace_id>`.
2. Viewer queries may count toward recurrence, but Viewers can never see, own,
   schedule, or receive a Routine.
3. Raw cross-user text never appears in suggestion copy, judge prompts, Slack,
   webapp cards, notifications, or logs. **Exception (§17.1, BH-949)**: a
   suggestion card MAY show one truncated line (≤140 chars) of the *viewing
   user's own* most-recent matching message as an anchor quote — never
   another user's text, and never in Slack/notification copy (webapp card
   only).
4. Raw excerpts are redacted, capped, and TTL-deleted after 35 days.
5. A Routine executes under the scheduling owner's current permissions,
   rechecked on every run by the P1 schedule execution contract.
6. Default generated WorkflowSpec uses read-only agent tooling.
7. Write-capable agent graphs require WorkspaceAdmin owner and explicit confirm;
   they are out of scope for P2/P3.
8. Dismiss/suppression state always wins over detector output.
9. Suggestion scheduling is conditional and idempotent; two users cannot create
   two schedules for the same suggestion.

---

## 10. Acceptance Criteria

```gherkin
Feature: BrightRoutines Intent Loop

  Scenario: Capture stores schedulable automation intent
    Given a user asks BrightAgent for a weekly earnings report
    When the deep_agent turn completes
    Then IntentCaptureMiddleware queues the latest human turn
    And a ProactiveSignal row is written with intent.schedulable = true
    And no user token is written to the row

  Scenario: Capture failure does not affect chat
    Given DynamoDB is throttling proactive signal writes
    When a user completes a BrightAgent turn
    Then the user still receives the agent response
    And capture logs a warning with workspace_id and turn_id

  Scenario: Shadow detector creates a routine suggestion
    Given three distinct users ask for the same weekly report within 28 days
    And each signal has outcome_ok = true
    When the nightly detector runs in shadow mode
    Then a RecurringAutomationPattern is written with status = READY_TO_SUGGEST
    And a RoutineSuggestion is written with status = OFFERED
    And evidence contains counts only

  Scenario: Offer is gated to eligible users
    Given a RoutineSuggestion status is OFFERED
    When a Viewer opens Schedules
    Then the suggestion is not returned
    When a Collaborator opens Schedules
    Then the suggestion is returned without raw prompt text

  Scenario: Scheduling creates a RoutineSchedule
    Given a Collaborator schedules an offered RoutineSuggestion
    When the schedule route succeeds
    Then a WorkflowSpec with one AGENT step exists
    And an execute_workflow schedule exists
    And the suggestion status is SCHEDULED with linked schedule and spec ids

  Scenario: Dismiss suppresses noisy offers
    Given a RoutineSuggestion is offered
    When eligible users dismiss it twice
    Then the suggestion status is SUPPRESSED
    And the detector does not re-offer it

  Scenario: User adjusts an offered routine before scheduling (§17.3, BH-949)
    Given a RoutineSuggestion status is OFFERED
    When a Collaborator clicks "Adjust"
    Then AddScheduleDialog opens prefilled with the suggestion's inferred cadence and recipients
    And the user may change cadence, recipients, or delivery before submitting
    When the user submits
    Then the suggestion is scheduled with the user's chosen values, not the inferred ones
    And which fields differed from the inferred values is recorded as adjustment feedback
    And the suggestion status is SCHEDULED
```

---

## 11. Evals And Metrics

LLM-powered pieces: automation-intent extractor and schedulability judge.

| Layer | Checks | Mode |
|---|---|---|
| L1 | Pydantic output shape, redaction, deterministic grouping utilities | Gate every PR |
| L2 | Real-model extractor/judge against labeled routine corpus | Gate when `BH_RUN_LIVE_EVALS=1` |
| L3 | RoutineSuggestion scheduling creates WorkflowSpec plus RoutineSchedule | E2E gate |
| L4 | Schedule rate, dismiss rate, false-offer reports | Observe in P2/P3, gate in P4 |

Promotion gates:

- P2 -> P3: shadow **precision >= 0.70 AND recall >= 0.50** against human labels
  for two weeks, over >= 25 evaluated cases, measured at the detector's live
  operating point. ECE is **reported, not gated** (see the hardening note).
- P3 -> P4: live schedule rate >= 25 percent and false-offer complaint rate <
  5 percent.
- Circuit breaker: if live precision falls below 0.60, stop surfacing offers and
  keep shadow detection only.

> **BH-956 hardening.** The P2->P3 gate was originally precision-only. That was
> a blind spot: a conservative judge that offers almost nothing trivially maxes
> precision (everything it does offer is right), so precision alone cannot see
> under-offering. The live judge (pre-recalibration) offered ~1 in 5 valid
> routines while still "passing". The **recall floor** (>= 0.50) closes that.
>
> Two things were validated by running the REAL Bedrock judge over the 60-case
> corpus (not just unit fakes):
>
> 1. **The evaluator must measure at the detector's operating point.** The
>    recalibration moved the detector 0.85 -> 0.70 but the evaluator's
>    `DEFAULT_THRESHOLD` initially stayed 0.85, so the live eval read recall
>    0.138 (scoring 0.78-0.82 verdicts against a 0.85 bar) even though
>    production offers correctly at 0.70. `DEFAULT_THRESHOLD` is now bound to
>    `MIN_JUDGE_CONFIDENCE` so the two can never drift.
> 2. **ECE is reported, not gated.** The real judge measures ECE ~0.46 at the
>    0.70 operating point — an excellent *classifier* (precision 0.931 / recall
>    0.931 / accuracy 0.933 over 60 cases) whose raw self-reported confidences
>    are not calibrated probabilities (normal for an LLM without post-hoc
>    temperature/isotonic scaling). A hard ECE ceiling would permanently block a
>    judge that decides correctly, so ECE is surfaced on the report and worth an
>    alert if it drifts, but classification quality — not probability
>    calibration — is the promotion bar.
>
> Enforced in `JudgeCalibrationReport.passes_shadow_promotion_gate()`
> (`brightbot/evals/routines/judge_evaluator.py`), verified via the live eval in
> `tests/integration/routines/test_judge_calibration.py` (`BH_RUN_LIVE_EVALS=1`).

---

## 12. Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Signal capture/detector | `brightbot` | Middleware, worker, detector job, routes, evals |
| DynamoDB/IAM | `brighthive-platform-core` | Table, grants, env wiring |
| Schedules UI | `brighthive-webapp` | Suggested Routines cards and hook |
| Notifications | `brighthive-platform-core`, `brighthive-webapp` | `workflow_suggestion` display and inbox card |
| Slack | `brightbot-slack-server` | suggestion formatter and schedule/dismiss handlers |
| Validation | `brighthive-e2e` | agent/schedule/product contract tests |

---

## 13. PR Split

| PR | Repo | Scope | Ticket | Target Size |
|---|---|---|---:|---:|
| 1 | `brighthive-platform-core` | single-table schema, IAM, env, capacity guards | [BH-882](https://brighthiveio.atlassian.net/browse/BH-882) | <400 lines |
| 2 | `brightbot` | DTOs, store Protocols, capture middleware | [BH-883](https://brighthiveio.atlassian.net/browse/BH-883) | <500 lines |
| 3 | `brightbot` | detector, judge adapter, pattern/suggestion state machine | [BH-884](https://brighthiveio.atlassian.net/browse/BH-884), [BH-889](https://brighthiveio.atlassian.net/browse/BH-889) | <600 lines |
| 4 | `brightbot` | routine suggestion service/routes and scheduler client | [BH-885](https://brighthiveio.atlassian.net/browse/BH-885) | <500 lines |
| 5 | `brighthive-webapp` | Suggested Routines on Schedules | [BH-886](https://brighthiveio.atlassian.net/browse/BH-886) | <500 lines |
| 6 | `brighthive-webapp` | notification card for workflow suggestions | [BH-886](https://brighthiveio.atlassian.net/browse/BH-886) | <300 lines |
| 7 | `brightbot-slack-server` | Slack formatter/buttons/action handlers | [BH-887](https://brighthiveio.atlassian.net/browse/BH-887) | <500 lines |
| 8 | `brighthive-e2e` | P2/P3 spec coverage and tracker bindings | [BH-889](https://brighthiveio.atlassian.net/browse/BH-889) | <400 lines |

## 14. Implementation Status (2026-07-04)

Snapshot of what's built vs. designed. The sections above are the target
contract; this tracks reality against it.

### ✅ Verified live end-to-end on staging (2026-07-04)

The full loop is proven on `brightagent-staging` + `api.staging.brighthive.net`,
capture flag ON (`FEATURE_FLAG_BRIGHTROUTINES_CAPTURE=true`):
chat turn → capture (Bedrock classify → secret-scrub → fingerprint → embed →
`brightroutines-stg`) → detector (`detect_recurring_patterns`: GSI1 fetch →
cohesion → 8 gates → Bedrock judge quorum) → OFFERED `RoutineSuggestion` →
`routineSuggestionsForWorkspace` GraphQL returns it. Two deploy-only bugs were
found + fixed during this pass, neither catchable without driving the real
system: (a) `IntentCaptureMiddleware.after_agent` was async but the middleware
runner invokes it sync → `InvalidUpdateError` (brightbot #775/#776); (b) the
Apollo Lambda had `BRIGHTROUTINES_TABLE_NAME` unset → read query degraded to []
(platform-core #997/#998).

### 🔍 Post-merge adversarial audit + remediation (BH-973, 2026-07-04)

Three independent agents (Python correctness, TS/security, QA/coverage) were
tasked to *disprove* "complete". Cross-tenant gating (P0), counts-only evidence
(§9), and the sync-hook fix were CONFIRMED solid. Eight defects were found and
all fixed (each in a green PR; the one live-harm item merged + deployed):

- **`scrub_text` credential leak (HIGH)** — the capture scrubber caught only a
  few shapes; AWS/OpenAI-proj/Anthropic/Stripe/DB-URL/`password=` etc. leaked
  into DynamoDB + OpenAI embeddings, making the "secret-scrubbed" label false.
  Expanded patterns + scrub the signature fields. brightbot #777 → **deployed to
  staging #778** (serving revision verified to contain the fix).
- **schedule double-create** on retry-after-partial-success (no idempotency
  key) → `scheduleCreationPlan` reuses an existing schedule. platform-core #999.
- **stranded-SCHEDULING lock** (rollback-also-failed) → self-healing reclaim of
  a stale lock via `scheduling_started_at` + `SCHEDULING_LOCK_STALE_MS`. #999.
- **raw AWS error leak** on the schedule read path → sanitized. #999.
- **`detector_task.py` had zero tests** → LocalStack round-trip guarding the
  store-write ⇄ read-mapper contract. brightbot #779.
- **detector embedded sync on the event loop** → `asyncio.to_thread`. #780.
- **capture spawned unbounded threads**, no timeout, shared boto3 resource, and
  an inline Secrets-Manager fetch → bounded pool + deadline + per-worker store +
  off-loop flag check. brightbot #781.
- **e2e chain test "missing"** — it existed as a conflicting draft (BH-947);
  rescued/rebased → mergeable. brighthive-e2e #30.

### Merged to develop
- **Detector + judge** (BH-884): recurring-automation detector (embedding
  cohesion clustering @0.86) + `RoutineJudge` (Protocol + LLM adapter + fake,
  N=3 quorum, model-agnostic via `BRIGHTROUTINES_JUDGE_MODEL`).
- **DynamoDB single-table** (BH-882) + **GSI5 for scores** (BH-985); judge
  calibration corpus (BH-944), OTel spans (BH-945), capture-time embedding +
  min-token gate (BH-946), contract snapshot (BH-948), W/P/U scoring (BH-950).
- **`summary-agent` graph** (BH-955, brightbot #763): read-only graph the
  schedule flow targets — registered in `langgraph.json` as `summary_agent`.
- **Write path** (§7): `scheduleRoutineSuggestion` (platform-core #991) +
  `dismissRoutineSuggestion` (#988) mutations, and **ownership persistence** —
  Neo4j `OWNS`/`ACCEPTED`/`RECEIVES`/`DERIVED_FROM` edges + DynamoDB mirror
  (BH-968, #992). Schedule state machine OFFERED→SCHEDULING→SCHEDULED with
  rollback; conditional-write lock prevents double-schedule.
- **Read query** — `routineSuggestionsForWorkspace` (platform-core #986):
  paginated GSI4 read, **gated on workspace membership** via
  `@authenticated(workspaceIdLoc)`. Exposes proposed action/artifact + ownership.

### In review (open PRs)
- **Capture path** (BH-960): `IntentCaptureMiddleware` `after_agent` hook on
  `deep_agent` + `LLMIntentClassifier` write the `ProactiveSignal` the detector
  clusters. Default-off behind the `BRIGHTROUTINES_CAPTURE` flag; best-effort,
  off-loop, secret-scrubbed. brightbot #770 (core) + #771 (wiring). **This is
  the last new code before the loop closes end-to-end.**
- **Resolve action/artifact at schedule** (BH-969): platform-core #994 +
  webapp #1264. Maps the scheduled graph id → resolved `ActionKind`/`OutputArtifact`.
- **Editable recipient** (BH-970): platform-core #995 + webapp #1265. Recipients
  are **validated to be workspace members** before delivery (owner always
  included) — cross-tenant leak guard.
- **Suggested Routines UI** — `/context/workflows` FormulasPage (webapp #1262):
  Suggested + always-anchored "Your routines"; cadence rail, cadence/channel
  chips, outcome chip (amber when it changes data), ownership line.

### Design added this cycle (not in §1–§13 above)
- **§3 extension — action/artifact axes** (BH-963/964): `ActionKind` ×
  `OutputArtifact`, inferred at OFFER, resolved at SCHEDULE. The UI renders the
  *outcome*, never the pipeline noun.
- **§7/§9 extension — accountability model** (BH-963/965): owner / accepter /
  recipients / contributors; unowned routine forbidden; Neo4j edges as SSOT.

### Not yet built (next phase)
> These two items are tracked as separate follow-up tickets, not blockers on
> the epic's Done status — BH-876 itself shipped and is verified live on
> staging without them.
- **§11 online eval / circuit breaker** — designed, unbuilt (BH-956/957).
- **Capture OTel spans** (BH-972) — classify + write path spans (spec §9).

### §8 correction
§8 originally targeted `src/Schedules/SchedulesPage.tsx`; the shipped surface
is `src/Context/pages/FormulasPage.tsx` at `/context/workflows` — the first
real implementation of that page's "Scheduled Actions" category.

---

## 15. Post-audit Appendix (BH-884 implementation, 2026-07-03)

A four-lens architectural audit (solutions-architect / llm-systems-engineer /
qa / end-user-persona) ran against BH-884's implementation branch. Six
code-level P0 findings landed on PR #759; the remaining findings are open
for spec-level revisit before the webapp UI ticket (BH-885+) ships. Each
open item has a dedicated follow-up ticket rather than being decided in
this document — the spec sections it questions (§6, §9, §10) are unchanged
until those tickets land.

**Findings that landed in code (BH-884 PR #759):**

- Judge is model-agnostic (renamed `LLMSchedulabilityJudge`, tier is
  `BRIGHTROUTINES_JUDGE_MODEL` env var, sonnet/haiku registry) — was
  "Sonnet judge" prior. Spec §6 gate 6 wording ("Sonnet schedulability
  judge confidence >= 0.85") should be read as "LLM judge with configurable
  tier."
- N=3 sample quorum with median confidence for the judge — smooths
  near-threshold variance a single call at temp=0 still exhibits.
- Typed `JudgeUnavailableError` distinct from low-confidence — a judge
  outage is no longer indistinguishable from "gate 6 fail, confidence=0.0".
- Prompt-injection defense: user-derived fields wrapped in
  `<untrusted_input>` delimiters at prompt render time (spec §9 invariant 3
  is enforced by type; this is defense-in-depth against injected
  instructions inside the redacted summary field).
- Within-run embedding memoization — reduces N+1 OpenAI cost during a
  single detection run. Capture-time embedding (spec §4.1's reserved
  `embedding` field) is [BH-946](https://brighthiveio.atlassian.net/browse/BH-946).
- `run_detector` graph node is `async def` — mandatory under LangGraph
  Cloud's live event loop.

**Findings open for spec-level revisit** — do not act on these in code
until the linked ticket lands a decision:

| Finding (from audit) | Spec section touched | Ticket |
|---|---|---|
| Evidence panel: counts-only reads as surveillance; add one anchor quote | §9 inv. 3 (revised) + §17.1 | **Decided 2026-07-06 — [BH-949](https://brighthiveio.atlassian.net/browse/BH-949)**: add anchor quote |
| Suppress after 1 dismiss, not 2 | §6 gate 8 (reaffirmed) + §17.2 | **Decided 2026-07-06 — [BH-949](https://brighthiveio.atlassian.net/browse/BH-949)**: kept 2-dismiss |
| "Accept / Adjust / Not this one" 3-option card | §10 Gherkin (added) + §17.3 | **Decided 2026-07-06 — [BH-949](https://brighthiveio.atlassian.net/browse/BH-949)**: add Adjust |
| Manager→report line detection in gate 2 (user breadth) | §6 gate 2 (revised) + §17.4 | **Decided 2026-07-06 — [BH-949](https://brighthiveio.atlassian.net/browse/BH-949)**: block gate 2, P0 |
| Direction inversion (pinned-first, proactive-second) | §17.5 ADR | **Decided 2026-07-06 — [BH-949](https://brighthiveio.atlassian.net/browse/BH-949)**: rejected, stay proactive-first |
| No canonical UserActivityEvent store — ProactiveSignal is a silo | §4 data model | [BH-942](https://brighthiveio.atlassian.net/browse/BH-942) |
| Nightly per-workspace EventBridge doesn't scale — fan out over SQS | §6 detector job shape | [BH-943](https://brighthiveio.atlassian.net/browse/BH-943) |
| No labeled judge corpus → §11 promotion gate unenforceable | §11 evals | [BH-944](https://brighthiveio.atlassian.net/browse/BH-944) |
| OTel/LangSmith span shape for judge + detector | §5 capture / new observability §9? | [BH-945](https://brighthiveio.atlassian.net/browse/BH-945) |
| EventBridge→dispatcher→LangGraph e2e in brighthive-e2e | §12 areas involved | [BH-947](https://brighthiveio.atlassian.net/browse/BH-947) |
| RoutineSuggestion webapp contract snapshot | §2 interface contract | [BH-948](https://brighthiveio.atlassian.net/browse/BH-948) |

**Guiding principle for the spec revisit** (BH-949): the end-user audit
concluded 6/10 week-1 retention as currently specified. One anchor quote +
"Adjust" button gets it to 8/10 by the persona's estimate. Suppression
count and manager-graph awareness are the two other retention levers. All
three are spec-level, not implementation choices, and should land before
BH-885 (webapp UI) starts.

---

## 16. W/P/U Scoring Layer (BH-950, 2026-07-03)

Rollup layer on top of §6's per-pattern outputs. Answers *"which
workspace / project / user has the strongest routine adoption?"* without
scanning raw signals. Composite score in `[0, 1]` per scope, computed
nightly at the tail of the detector pass.

### 15.1 Score DTO shape (counts-only, §9 invariant 3 compliant)

`RoutineScore` (`brightbot/routines/scoring/dtos.py`) — frozen Pydantic
with no field capable of carrying raw text:

- `scope: ScoreScope` — `WORKSPACE` | `PROJECT` | `USER`
- `workspace_id`, `scope_id` — always workspace-scoped (cross-workspace comparability lives in BH-942)
- `window_start`, `window_end`, `computed_at`
- Raw counts: `signals_count`, `schedulable_signals_count`,
  `distinct_users_count`, `distinct_projects_count`,
  `patterns_ready_count`, `suggestions_offered_count`,
  `suggestions_scheduled_count`, `suggestions_dismissed_count`
- Averages: `avg_judge_confidence`, `avg_recurrence_score` (nullable)
- `composite_score: float ∈ [0, 1]`

### 15.2 Composite formula (module-level, single tuning surface)

```
composite = schedulable_rate  * 0.4
          + avg_confidence    * 0.3
          + avg_recurrence    * 0.2
          + activation_rate   * 0.1   # scheduled / offered
```

Weights sum to 1.0 (unit test enforces). None → 0 for the missing
channels; inputs clamped to `[0, 1]` so rounding cannot push composite
past 1.0. Same shape as `quality_utils.py`'s `overall_score` precedent.

### 15.3 Persistence (audit-approved, non-conflicting with §4.1/4.2/4.3)

Under existing `PK=WORKSPACE#<workspace_id>`:

- `SK = SCORE#<scope>#<scope_id>#<window_end_iso>` — append-only per
  window, so history / trend / EWMA is computable without re-scanning
  signals.
- `GSI5PK = SCORE_SCOPE#<scope>#<workspace_id>`
- `GSI5SK = <inverted_composite_5-digit>#<scope_id>` — lexicographic
  DESC by composite for leaderboard queries.

CDK: `BrightroutinesDataStack` provisions GSI5 alongside GSI1–4.

### 15.4 Aggregation + wiring

`compute_scores_for_workspace()` runs at the tail of `run_detection`
sharing the same 28-day window and the same OTel parent span. Emits a
`brightroutines.score.compute` child span with `workspace_id`,
`window_days`, `signals.total`, `signals.in_window`, `scores.written`,
`scores.projects`, `scores.users` attributes. Never emits raw
`intent.summary` on span attributes — the score row itself is
counts-only by construction.

Backward-compatible: `run_detection`'s new `score_store` parameter is
optional. Existing callers get exactly pre-BH-950 behaviour.

### 15.5 Read API

- MCP tool `get_routine_scores(scope="WORKSPACE" | "PROJECT" | "USER")`
  in `_CORE_TOOL_MODULES` (always-on), returns the top-N leaderboard.
- `RoutineScoreStore.history(scope, scope_id, since=)` for trend
  reads. No GraphQL resolver yet — that's BH-885's concern.

### 15.6 Follow-ups (not in BH-950, tracked separately)

- **Per-recipient suggestion status** → user-level offered/scheduled/dismissed counts (currently zero — BH-885 wires per-recipient).
- **Per-signal recurrence score** → `avg_recurrence_score` populated (currently None — depends on BH-946 capture-time embedding).
- **EWMA / trend view** over `history()` output — dashboard concern, not shipped in BH-950.
- **Manager→reports gate 9** in the detector (spec §6 gate 2 refinement per BH-949) will consume `user_score.composite_score` as input; DTO shape is already designed for that consumer.

### 15.7 Rationale for not fanning out on skill/agent surfaces

Same argument as §6's non-adoption of Nano's skill framework: scoring is
a headless nightly aggregation with a deterministic input contract, not
a chat-turn capability. Wrapping it in a skill (`brightbot/skills/`) or
subagent (`docs/CREATING_SUBAGENTS.md`) would add a conversational loop
with no user to converse with. Pure Python module + Protocol store +
MCP read-tool is the right encapsulation.

## 16. Action/Artifact Type + Accountability Model (BH-963, shipped 2026-07-04)

Kuri (2026-07-03): a routine card showed title + cadence but not WHAT the
routine is (SQL? dbt run? table refresh? PDF? execution?) or WHO owns,
accepts, and receives it. A 4-agent panel (solutions-architect,
brighthive-product-voice, ux-designer, brightagent-enduser) converged on
the design below. Implementation shipped ahead of this write-up landing
(BH-964/965/966/968/969/970, PR #765 and follow-ons) — this section is the
retroactive spec-first record, confirmed against the merged code.

### 16.1 "What is it" — two orthogonal axes, outcome-framed

```python
ActionKind     = SQL_QUERY | DBT_RUN | QUALITY_CHECK | AGENT_TASK | EXPORT
OutputArtifact = TABLE | VIEW | CSV | PDF | DASHBOARD | SLACK_MESSAGE | NOTIFICATION | CHAT_ANSWER
```

Two-phase provenance, both nullable on `RoutineSuggestion`:

- **Offer time**: `proposed_action_kind` / `proposed_output_artifact` — hints
  from the Haiku classifier (§5), low-confidence. Most resolve to
  `AGENT_TASK` + `CHAT_ANSWER` until more graphs than `summary-agent` exist
  (BH-955). Do not overclaim.
- **Schedule time**: `resolved_action_kind` / `resolved_output_artifact` —
  deterministic from the WorkflowSpec's AGENT step + tool allowlist
  (`dbt.*`→`DBT_RUN`, `warehouse.query`→`SQL_QUERY`, `quality.*`→
  `QUALITY_CHECK`, `export.*`→`EXPORT`). This is the UI source-of-truth once
  scheduled — `RoutineSuggestionCard.tsx` prefers `resolved_*` over
  `proposed_*` (`suggestion.resolved_action_kind ?? suggestion.proposed_action_kind`).

**UX rule**: the card shows the OUTCOME, never the pipeline noun — "Report in
Slack" / "Refreshes the customer_orders table", never "dbt run" /
"execute_workflow". `outcomeLabel()` (`webapp/src/Context/routines/format.ts`)
buckets into **delivers-to-you** (read, calm grey) vs **changes-your-data**
(write, amber caution tint).

### 16.2 The one trust primitive: read/write authority

The safe-vs-reckless axis is blast radius, surfaced as "Read-only · runs as
you". §9 invariant 5 (runs under owner perms, rechecked per run) and
invariant 6 (read-only default) already encoded this; `outcomeLabel()`'s
`changesData` flag is what makes it visible on the card.

### 16.3 Accountability — four roles

- **OWNER** (`owner_user_id`) — accountable, runs under their perms.
  **New §9 invariant 10: an unowned routine cannot run** — enforced in code
  by `persistRoutineOwnership` (`platform-core/src/graphql/service/neo4j/routine-ownership.ts`),
  which throws if `ownerUserId` is falsy rather than writing a partial edge.
- **ACCEPTER** (`accepted_by` + `accepted_at`) — who clicked Schedule; audit;
  defaults to owner. Currently always equals owner (no delegated-scheduling
  path exists yet — `accepterUserId: ownerUserId` in
  `scheduleRoutineSuggestion`).
- **RECIPIENTS** (`recipient_user_ids`) — who gets output; editable at
  schedule-time via the `recipientUserIds` GraphQL arg, defaults to
  `[owner]`. Requested recipients are filtered down to real workspace
  members by `filterRecipientsToWorkspaceMembers` (Cypher `IS_A`/`HAS_A`
  membership check) before being persisted — closes the cross-tenant leak
  where a caller could name a user from another workspace. **New §9
  invariant 11: Viewers can never be recipients** (membership filter matches
  on role edge presence, not role type, so this still needs an explicit role
  check — tracked as BH-984's unbounded-fanout hardening ticket, not yet a
  role-exclusion; recorded here as a known gap, not closed by this section).
- **CONTRIBUTORS** (on the pattern) — distinct users whose signals triggered
  it; not yet wired into recipient defaulting (would drive "suggest sending
  to the people who asked" — unshipped, no ticket filed yet).

Pre-accept (`OFFERED`) there is no owner — ownership is post-accept only,
matching the "Scheduling makes you the owner" framing.

### 16.4 Storage

Neo4j SSOT edges, `platform-core/src/graphql/service/neo4j/routine-ownership.ts`:

```text
(User)-[:OWNS]->(RoutineScheduleNode)
(User)-[:ACCEPTED {at}]->(RoutineScheduleNode)
(User)-[:RECEIVES]->(RoutineScheduleNode)
(RoutineScheduleNode)-[:DERIVED_FROM]->(RoutineSuggestionNode)
```

Written non-blocking at the tail of `scheduleRoutineSuggestion`'s commit —
a graph write failure logs loudly and does not fail the mutation, since the
DynamoDB row is already committed and linked; a reconcile pass repairs the
edges. DynamoDB keeps the fast-read mirror (`owner_user_id`,
`recipient_user_ids`) that the list/read surfaces actually query.

### 16.5 Spec deltas realized

- §3 DTOs: `RoutineSuggestion` GraphQL type gained `proposedActionKind`,
  `proposedOutputArtifact`, `resolvedActionKind`, `resolvedOutputArtifact`,
  `ownership: RoutineOwnership` (`ownerUserId`, `ownerName`,
  `recipientUserIds`).
- §4 storage: Neo4j ownership edges (§16.4) added alongside the existing
  DynamoDB attrs in §4.3; no new DynamoDB attrs beyond `owner_user_id`/
  `recipient_user_ids` (already listed in §4.3, now populated in production).
- §5 classifier: not yet emitting `action_kind`/`output_artifact` hints —
  `proposed_action_kind`/`proposed_output_artifact` are wired end-to-end
  but currently always null pending a classifier update. Tracked as an open
  gap, not closed by BH-963's shipped scope.
- §7 schedule flow: owner/accepter split and editable recipients (BH-970)
  both shipped; contributor-based recipient defaulting (§16.3) unshipped.
- §9 governance: invariants 10 (no unowned routine runs) and 11 (Viewers
  excluded from recipients — partially; see §16.3 gap note) added.

### 16.6 End-to-end verification (2026-07-06)

Full ownership lifecycle confirmed against real deployed staging as part of
the BH-982 fix verification: `scheduleRoutineSuggestion` set
`ownership.ownerUserId` to the caller's Cognito `sub`; `unscheduleRoutine`
cleared it back to `null`. Neo4j edge writes were not independently queried
in that pass (DynamoDB mirror + GraphQL response were the verification
surface) — a dedicated Neo4j-edge read-back test is the natural next
real-behavior check, not yet performed.

## 17. BH-949 Spec Revisit — Kuri's Decisions (2026-07-06)

The end-user audit (§15's table) flagged four product decisions that were
supposed to land before the webapp UI (BH-954) shipped. BH-954 shipped
first with the pre-revisit behavior (counts-only evidence, binary
Accept/Dismiss, 2-dismiss escalation) — this section is the retroactive
decision record plus the delta each decision opens against the shipped
code. Each decision below closes one BH-949 AC bullet.

### 17.1 Decision 1 — Evidence panel: add one anchor quote

**Decided: add one anchor quote.** The card gains one truncated line of the
**viewer's own** most-recent matching message, alongside the existing
counts — never another user's text, so the cross-user redaction guarantee
(§9 invariant 3) is unchanged. Hidden counts alone read as surveillance;
seeing your own words read back builds trust that the system understood
the actual request.

**§9 invariant 3 revised**:

> Raw cross-user text never appears in suggestion copy, judge prompts,
> Slack, webapp cards, notifications, or logs. **Exception**: a suggestion
> card MAY show one truncated line (≤140 chars) of the *viewing user's own*
> most-recent matching message as an anchor quote — never another user's
> text, and never in Slack/notification copy (webapp card only).

**Implementation delta** (not yet built — new ticket, not this session's
scope): `RoutineSuggestion` needs a per-viewer-resolved
`viewer_anchor_excerpt: str | None` field, populated by looking up the
requesting user's own `ProactiveSignal` row matching the pattern's
fingerprint at read time (never stored on the shared suggestion row itself,
to avoid leaking one user's excerpt to another reader of the same
suggestion).

### 17.2 Decision 2 — Suppression: keep 2-dismiss escalation

**Decided: keep the current 2-dismiss escalation** (first dismiss →
90-day cooldown, second dismiss for the same pattern → permanent
SUPPRESSED). Rejects the audit's 1-dismiss proposal — a single dismiss is
often just bad timing ("not right now, I'm mid-report"), and going straight
to permanent suppression on one click costs more true positives than it
saves in \"the product isn't listening\" sentiment. The existing behavior
already ships correctly (BH-967's `nextDismissStatus` — see §15's
implementation status) — no code change from this decision.

**§6 gate 8 reaffirmed as-is**, no revision. This decision overrides the
audit's specific ask; the counter-argument above is the record of why.

### 17.3 Decision 3 — Card actions: add "Adjust"

**Decided: add a third "Adjust" option.** Cards move from binary
Accept/Dismiss to **Accept / Adjust / Not this one**. "Not this one" is
Dismiss renamed for clarity (no behavior change — still feeds §6 gate 8).
"Adjust" opens the existing `AddScheduleDialog` (already shipped, verified
working end-to-end this session — BH-975/976/977/982) prefilled with the
suggestion's inferred cadence/recipients, and **captures which fields the
user actually changed** as structured feedback before committing the
schedule — not just a silent edit. This is the refinement from Kuri's
2026-07-06 note: the Adjust flow isn't only "edit and go," it's a signal
capture point — *what was off* (cadence, recipients, relevance) feeds back
into future suggestion tuning, distinct from a clean Accept.

**§10 Gherkin addition**:

```gherkin
  Scenario: User adjusts an offered routine before scheduling
    Given a RoutineSuggestion status is OFFERED
    When a Collaborator clicks "Adjust"
    Then AddScheduleDialog opens prefilled with the suggestion's inferred cadence and recipients
    And the user may change cadence, recipients, or delivery before submitting
    When the user submits
    Then the suggestion is scheduled with the user's chosen values, not the inferred ones
    And which fields differed from the inferred values is recorded as adjustment feedback
    And the suggestion status is SCHEDULED
```

**Implementation delta** (new ticket, not this session's scope): webapp
`RoutineSuggestionCard.tsx` gains the third button; `AddScheduleDialog`
needs a diff step comparing submitted values against the suggestion's
`proposed_cadence`/inferred recipients, and a new field on the schedule
mutation (or a side-channel event) to record which fields were adjusted.

### 17.4 Decision 4 — Manager→report gate: block gate 2 until hierarchy-aware

**Decided: block gate 2 until hierarchy-aware** — the stricter of the two
options. Gate 2 ("at least 3 distinct users in 28 days") must not fire on
user-breadth alone if those users are a manager + their direct reports,
since that's one person's reporting chain surfacing across threads, not
organic multi-user demand. Until a reporting-hierarchy signal exists (no
HRIS/org-chart data source is currently wired into BrightHive), gate 2
requires an explicit hierarchy check to pass, not just a raw distinct-user
count.

**§6 gate 2 revised**:

> 2. At least 3 distinct users in 28 days AND those users are not all
>    members of a single manager→reports chain (no hierarchy data source
>    yet → **this sub-clause fails closed: gate 2 cannot pass on
>    user-breadth alone until a reporting-hierarchy signal is available**),
>    OR one user at least 5 times across at least 3 weeks.

**Consequence**: until the hierarchy signal ships, gate 2's user-breadth
path is effectively gated off for any workspace where BrightHive cannot
prove the ≥3 users are independent. The single-user cadence path (5×/3wk)
remains fully available. This is a real, immediate behavior change from
what's shipped today — **flagging as a P0 follow-up ticket**, not
optional cleanup, since the currently-live detector (BH-884, verified this
session) has no hierarchy check and gate 2 can fire on a manager's own
repeated ask surfacing through report threads right now.

**Implementation delta** (new ticket, P0 not backlog): needs (a) a
hierarchy data source — even a coarse one, e.g. Neo4j `REPORTS_TO` edges
if that relationship exists anywhere in the platform today, or an explicit
non-goal if it doesn't — and (b) a detector-side check in gate 2 before
the next production run. Until this ticket lands, gate 2's user-breadth
path should be treated as a known false-positive source, not a solved gate.

### 17.5 ADR: proactive-first vs pinned-first (considered and rejected)

**Status: Rejected — staying proactive-first.**

**Considered**: invert the architecture so a user manually "pins" a chat
thread as a routine (no detector involved in that path), with proactive
detection layered on as a secondary/optional discovery mechanism. This
would remove the "surveillance" framing entirely — nothing is offered
that wasn't explicitly asked for.

**Why rejected**: the detector → judge → suggestion pipeline (BH-884 and
its dependents) is built, tested (60-case judge corpus, calibration eval,
real-behavior LocalStack + real-staging verification this session), and
deployed. A pinned-first inversion would not extend this pipeline — it
would replace its primary entry point, discarding verified production
code to chase a UX framing problem that decisions 17.1 (anchor quote) and
17.3 (Adjust option) already address most of: the surveillance smell came
from *opaque* proactive offers, not from proactivity itself. Anchor quotes
make the evidence legible; the Adjust option makes acceptance reversible
and reviewable. Both are cheaper than a rearchitecture and ship the same
trust improvement.

**Not closed forever**: if user research after 17.1/17.2/17.3/17.4 ship
still shows meaningful "why is this suggesting things to me" friction,
revisit pinned-first as an *additive* v2 entry point (both paths coexist)
rather than a replacement — the DTOs (`RoutineSuggestion`,
`RoutineSchedule`) don't structurally prevent a user-initiated creation
path being added later.

### 17.6 Summary of what's now open (new tickets, not filed by this spec edit)

| Decision | Spec delta | Code delta | Priority |
|---|---|---|---|
| 17.1 Anchor quote | §9 inv. 3 exception (this edit) | `viewer_anchor_excerpt` field + resolver + card render | Backlog |
| 17.2 Suppression | None — reaffirmed | None | N/A |
| 17.3 Adjust option | §10 Gherkin scenario (this edit) | 3rd card button + dialog diff step + feedback capture | Backlog |
| 17.4 Manager gate | §6 gate 2 (this edit) | Hierarchy data source + detector gate check | **P0** — live detector has no hierarchy check today |
| 17.5 ADR | This section | None (rejected) | N/A |
