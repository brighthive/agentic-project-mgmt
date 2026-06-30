---
title: BrightRoutines Intent Loop
epic: BH-876
tickets: [BH-882, BH-883, BH-884, BH-885, BH-886, BH-887, BH-888, BH-889]
author: codex
status: draft
created: 2026-06-30
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
2. At least 3 distinct users in 28 days, or one user at least 5 times across at
   least 3 weeks.
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

### Webapp

Extend `src/Schedules/SchedulesPage.tsx`:

- Add "Suggested Routines" above the schedules table.
- Use `useRoutineSuggestions`, modeled after `useSchedules`.
- Suggestion card shows title, aggregate evidence, inferred cadence, and
  actions: Schedule, Dismiss.
- Schedule opens `AddScheduleDialog` prefilled with cadence and workflow task
  details, then commits through the schedule route.
- Cards are single-column on 320px, chips wrap, and action buttons stack under
  480px.

Extend Notifications inbox:

- Platform Core `formatSignal` returns `display.type = "workflow_suggestion"`.
- Webapp registers `workflow_suggestion` card with Schedule/Dismiss actions.

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
   webapp cards, notifications, or logs.
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

- P2 -> P3: shadow precision >= 0.70 against human labels for two weeks.
- P3 -> P4: live schedule rate >= 25 percent and false-offer complaint rate <
  5 percent.
- Circuit breaker: if live precision falls below 0.60, stop surfacing offers and
  keep shadow detection only.

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
