---
title: BrightRoutines Execute Workflow Scheduling
epic: BH-876
tickets: [BH-877, BH-878, BH-879, BH-880, BH-881, BH-908, BH-909, BH-910, BH-911, BH-914, BH-915, BH-916]
author: codex
status: implemented-pending-staging-verification
created: 2026-06-30
last-reviewed: 2026-07-03
generates: tickets
tags:
  - brightagent
  - routines
  - scheduled-agents
  - workflow-spec
related:
  features: []
  pocs: []
  bedrock: []
---

# SPEC: BrightRoutines Execute Workflow Scheduling

> Scope: P1 foundation for BrightRoutines. This spec makes an existing
> WorkflowSpec executable on a schedule, with no ML/proactive detection. The
> proactive automation-intent learning loop is specified separately in
> `brightroutines-intent-loop.md`.

## Jira Tickets

| Ticket | Repo | Refined Scope | Phase | Depends On |
|---|---|---|---:|---|
| [BH-876](https://brighthiveio.atlassian.net/browse/BH-876) | all | Epic: BrightRoutines | - | - |
| [BH-877](https://brighthiveio.atlassian.net/browse/BH-877) | `brightbot` | Replace scheduler allowlist/required-input sets with action descriptors; add `execute_workflow`, `ScheduleRoutineRequest` validation, recursive secret rejection, auth-derived workspace/owner injection, and unit tests. | P1 | - |
| [BH-878](https://brighthiveio.atlassian.net/browse/BH-878) | `brighthive-platform-core` | Replace dispatcher `auth_token` payloads with a reusable scheduler execution context/service-auth path; revalidate owner membership, role, project ownership, and `executeWorkflow` permissions every run. | P1 | BH-877 |
| [BH-879](https://brighthiveio.atlassian.net/browse/BH-879) | `brighthive-platform-core` | Add idempotent workflow-run terminal bridge from callback/poller completion to scheduled-agent state and notification fanout; make the bridge reusable for future workflow-backed schedules. | P1 | BH-878 |
| [BH-880](https://brighthiveio.atlassian.net/browse/BH-880) | `brighthive-webapp` | Convert Schedules hard-coded task choices to action metadata; add workflow project picker/prefill/edit/run-now labels while preserving shared table/mobile behavior. | P1 | BH-877 |
| [BH-881](https://brighthiveio.atlassian.net/browse/BH-881) | `brighthive-e2e` | Extend scheduler specs/tests for `execute_workflow` create/read/run lifecycle, forbidden secrets, auth scoping, terminal state, and notification delivery using ground truth and cleanup. | P1 | BH-877, BH-878, BH-879, BH-880 |

**Execution order**: BH-877 -> BH-878 -> BH-879; BH-880 can start after BH-877; BH-881 is the final gate.

---

## 0. Shipped Status (2026-07-03)

All P1 tickets (BH-877/878/879/880/881) plus 4 follow-on tickets are merged
to `develop` (and `staging` branch) in all 5 repos. **Not yet confirmed live
on the deployed staging environment** — see Staging Deploy Gaps below.

### What actually shipped, beyond this spec's original scope

- **BH-908**: `deliver()` in `lambdas/notification_dispatcher/delivery.py`
  was refactored from a hardcoded if/elif channel-type chain into an
  injectable adapter registry (matching the pre-existing pattern in
  `brightbot-slack-server/src/notifications/channels.ts`), and a Teams
  delivery adapter (Adaptive Card) was added on the same seam. Channel
  subscription-creation UI is separate, pre-existing work (BH-415, epic
  BH-409) this rides on, not re-scoped here.
- **BH-910**: a throwaway demo script
  (`brightbot/scripts/demo_workflow_from_intent.py`) proving BH-897's future
  "AI-authored WorkflowSpec from a prompt" direction works against real
  local infra — explicitly NOT shippable BH-897 code, see
  `brightroutines-ai-authored-workflowspec.md`.
- **BH-911**: `checkPolicies()` in `compiler.ts` gained a deterministic
  BLOCKER for DBT/PYTHON/INGEST runtimes (their `checkStatus()` adapters
  never reach a terminal state — see Real Bugs Found below) and a WARNING
  for report-generating AGENT steps missing `store_artifact` output.

### Real bugs found and fixed during implementation (not in the original spec)

Verification against real local infra (Docker Neo4j/Redis/LocalStack, no
mocks) surfaced defects the original interface contract didn't anticipate.
Each was fixed and regression-tested before merge:

1. **Unauthenticated callback-forgery vulnerability** (security,
   `callback-handler.ts`) — `workflowStepCallbackHandler` skipped HMAC
   validation entirely whenever a step run had no `callbackSecret` (true
   for every EXTERNAL-runtime step). Anyone knowing a `stepRunId` UUID
   could forge that step's completion with zero auth. This code predates
   BH-876 (merged via #785) — the fix landed as part of BH-879 (#964), so
   promoting this epic to staging is also what fixes this pre-existing,
   already-deployed bug.
2. **Dead retry-sweep path** — the poller's "recently completed" query
   compared a Neo4j `DateTime` to a raw ISO string via `>=`, which
   evaluates to `NULL` in Cypher (not `true`/`false`). Invariant 7's entire
   recovery mechanism for a once-failed webhook delivery had never worked.
3. **Non-constant-time secret comparisons** (2 instances) — brightbot's
   webhook token check (`routes/scheduled_agents_routes.py`) and
   platform-core's `SCHEDULER_SERVICE_API_KEY` check both used plain
   `!=`/`!==` instead of `hmac.compare_digest`/`crypto.timingSafeEqual`,
   this codebase's own established pattern. Both fixed.
4. **Forbidden-field guard bypassed by camelCase** — `_find_forbidden_fields`
   lowercased raw keys only, so a client sending `authToken` (camelCase)
   never matched the snake_case `FORBIDDEN_PAYLOAD_FIELDS` set (`auth_token`).
5. **`executeWorkflowAsOwner` never initialized its REST data sources** —
   any DBT/Datapiary-backed scheduled step would throw on first HTTP call.
6. **Schema-generation gap** — `emit-schema-sdl.ts`/`codegen.yaml` only
   loaded the base `typedefs.ts`, silently omitting `executeWorkflowAsOwner`
   from the SDL brightbot's introspection-disabled consumers rely on.
7. **`WorkflowSpecStatus` enum missing `BLOCKED`** — `compiler.ts` writes
   this value on any BLOCKER-level compile issue; any workflow with so much
   as a missing SQL template 500'd on `compileWorkflow` instead of
   returning the issue list. Pre-existing, surfaced by this epic's testing.

Full detail and commit references: see PR #964's description on
`brighthive-platform-core` and PR #749 on `brightbot`.

### Staging Deploy Gaps (open, ticketed, blocking live verification)

- **BH-914** (High): platform-core's CDK deploy to staging fails —
  `SCHEDULER_SERVICE_API_KEY`/`SCHEDULER_WEBHOOK_SECRET` are read from the
  `staging/platform/platform-core` secret but were never added there. This
  was a self-documented known gap in PR #964's own commit message. Needs
  explicit secret-edit approval per this org's env-var rule before fixing.
- **BH-915** (Medium): cannot confirm brightbot's staging LangGraph
  deployment picked up the `develop`→`staging` merge — `/info`'s
  `revision_id` was unchanged 30+ minutes after merge. Needs LangSmith
  deployments API access to investigate further.
- **BH-916** (Low): no way to confirm brighthive-webapp's Amplify staging
  build succeeded, or even find the canonical staging URL, without AWS
  console access.

**Until BH-914/915/916 close, this epic is code-complete and exhaustively
verified locally (see §6 Test Plan and the UAT findings appendix below) but
not confirmed live on staging.**

---

## 1. Context

### Problem

BrightHive can run WorkflowSpec projects and can schedule quality/profiler
agent tasks, but users cannot safely schedule a stored WorkflowSpec. The
existing scheduler dispatcher already has an `execute_workflow` action handler,
but the BrightBot management API allowlist and webapp only expose
`quality_check_task` and `profiler_task`.

The current `execute_workflow` handler is also not production-safe as a user
feature because it expects an `auth_token` in the schedule row. Scheduled rows
live in DynamoDB and must not store user JWTs or long-lived bearer tokens.

### What Exists Today

- `brightbot/routes/scheduled_agents_routes.py` owns CRUD for
  `/manage/scheduled-agents`, EventBridge Scheduler upsert/delete, run-now, and
  a run-complete webhook.
- `SCHEDULABLE_ACTIONS` currently allows only `quality_check_task` and
  `profiler_task`.
- `brighthive-platform-core/lambdas/scheduled_agent_dispatcher/action_registry.py`
  already registers `execute_workflow`.
- `workflow_execution_action.py` calls Platform Core GraphQL
  `executeWorkflow(input: { workspaceId, projectId })`.
- Platform Core `WorkflowSpec` already supports `StepRuntime.AGENT`, and the
  `AgentAdapter` triggers BrightBot `POST /workflow/run`.
- `brighthive-webapp/src/Schedules` already has schedule list, create, edit,
  enable/disable, run-now, adaptive polling, and output display fields.

### Goal

An Admin or Collaborator can create a `RoutineSchedule` for an existing active
WorkflowSpec project. The schedule fires through EventBridge, starts
`executeWorkflow`, records final status back on the schedule row, publishes a
notification, and never stores a user token at rest.

### Non-Goals

- No `ProactiveSignal` capture.
- No `RoutineSuggestion` offers.
- No new workflow runtime.
- No cron/timezone fields on `WorkflowSpecNode`; schedules remain DynamoDB rows.
- No use of deprecated Datapiary/PYTHON workflow runtime for Routines.

---

## 2. Interface Contract

### 2.1 Schedule Row Shape

The API DTO names for this P1 substrate are:

- `ScheduleRoutineRequest`: request to schedule a WorkflowSpec-backed Routine.
- `RoutineSchedule`: response/projection of an `execute_workflow`
  scheduled-agent row.

`ScheduleRoutineRequest.source_routine_suggestion_id` is `null` for manual P1
creation and set by the P2/P3 intent loop when a `RoutineSuggestion` is
scheduled.

`action_type = "execute_workflow"` schedule rows use the existing scheduled
agents table:

```json
{
  "PK": "WORKSPACE#<workspace_id>",
  "SK": "SCHEDULE#<schedule_id>",
  "schedule_id": "<uuid>",
  "workspace_id": "<workspace_id>",
  "action_type": "execute_workflow",
  "cron_expression": "0 8 * * MON",
  "sink_type": "workflow_run_notification",
  "enabled": true,
  "created_by": "<owner_user_id>",
  "action_payload": {
    "workspace_id": "<workspace_id>",
    "project_id": "<project_id>",
    "owner_user_id": "<owner_user_id>",
    "routine_schedule_source": "manual",
    "source_routine_suggestion_id": null,
    "delivery": {
      "webapp": true,
      "slack": true
    },
    "_schedule_meta": {
      "timezone": "America/New_York",
      "type": "weeks",
      "display_name": "Weekly earnings report"
    }
  }
}
```

Forbidden fields in `action_payload`: `auth_token`, `access_token`,
`id_token`, `refresh_token`, `authorization`, `jwt`, `api_key`.

### 2.2 BrightBot Management API

Extend `routes/scheduled_agents_routes.py`:

- Add `execute_workflow` to `SCHEDULABLE_ACTIONS`.
- Add required inputs: `workspace_id`, `project_id`, `owner_user_id`.
- Reject any forbidden token/key fields recursively.
- Preserve existing CRUD, run-now, timezone, overlap-lock, and CORS behavior.
- Keep `workspace_id` derived from the authenticated request, not trusted from
  client input.

### 2.3 Service Authentication

The dispatcher must not read a user JWT from DynamoDB. It must authenticate to
Platform Core with a scheduler service identity that is resolved at execution
time from secrets/env and never persisted in the schedule row.

Platform Core must revalidate, for every run:

1. `owner_user_id` is still an active member of `workspace_id`.
2. Owner role is still Admin or Collaborator.
3. Owner has the permissions required by `executeWorkflow`.
4. `project_id` belongs to `workspace_id`.

Implementation options:

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Mint short-lived service JWT in dispatcher | Small change to current GraphQL path | Needs service user membership/claims | Acceptable |
| Add internal `executeWorkflowAsOwner` service mutation | Clean owner revalidation contract | More Platform Core schema/service work | Preferred if service JWT cannot model owner scope |
| Store creator JWT in DynamoDB | Fast | Token at rest, stale permission, high risk | Rejected |

### 2.4 Terminal Completion Bridge

Verified gap: `WorkflowExecutionActionHandler` returns the initial
`executeWorkflow` response. For AGENT steps, that response is normally
`RUNNING`, and the current `langgraph_webhook` sink records schedule status as
running. There is no current callback from Platform Core workflow completion
back to the scheduled-agent schedule row.

Add a terminal bridge before shipping P1:

- Store `schedule_id`, `workspace_id`, and `owner_user_id` on the WorkflowRun or
  as a run trigger context when `executeWorkflow` is started by the dispatcher.
- When the workflow run reaches `SUCCESS`, `FAILED`, or `CANCELLED`, update the
  scheduled-agents row with final `last_run_status`, `last_run_message`,
  `last_run_output_type`, `last_run_output`, and `running=false`.
- Publish a notification signal with stage:
  - `scheduled_workflow_success`
  - `scheduled_workflow_error`
- The bridge must be idempotent by `(schedule_id, workflow_run_id)`.

### 2.5 Webapp UX

Extend the existing Schedules page rather than creating a new area.

- Add an action label for `execute_workflow`: "Workflow".
- Add a schedule creation path for an existing WorkflowSpec project.
- If opened from a project workflow page, prefill `project_id` and workflow
  display name.
- Existing `SchedulesTable` controls apply: enable/disable, edit cadence,
  run-now, delete.
- Mobile: controls fit at 320px; actions stack below 480px.

### 2.6 Notifications

Platform Core notification display must include a workflow schedule formatter:

```ts
display.type = "workflow_run"
display.title = "Routine completed - <display_name>"
display.subtitle = "<success|failed> at <timestamp>"
display.url = "<webapp workflow run detail or schedules row URL>"
```

Webapp inbox registers a `workflow_run` card, or the generic card handles the
display fields with a tested deep link. Slack notification formatting adds the
new stages and routes buttons through the existing `bh_notif_*` handler pattern.

---

## 3. Invariants

1. No user JWT, refresh token, API key, PAT, or Authorization header is stored in
   any schedule row.
2. `workspace_id` on create/update comes from authenticated context and cannot
   be overridden by request body.
3. A disabled schedule cannot run from EventBridge, but run-now may execute
   after explicit user action.
4. Overlap lock prevents concurrent runs of the same schedule.
5. The owner is revalidated on every run; removed, Viewer, Contributor, and
   Agent Guest owners cannot execute scheduled workflows.
6. The Routine uses `StepRuntime.AGENT` for agent work; deprecated Datapiary
   runtime is not used.
7. Every scheduled workflow run reaches a terminal schedule state or records a
   terminal bridge error within the polling timeout. *(Implementation note:
   this invariant's entire recovery path — the poller's retry-sweep for a
   once-failed webhook delivery — was dead code until fixed during BH-879;
   see §0 Real Bugs Found #2. DBT/PYTHON/INGEST runtimes are excluded from
   scheduling entirely via a `checkPolicies()` BLOCKER, BH-911, because
   their adapters' `checkStatus()` never returns a terminal state — a
   WorkflowSpec using one of these would otherwise violate this invariant
   permanently, not just recoverably.)*
8. Notification and schedule-state writes are idempotent for a retried
   workflow completion.
9. **(Added post-implementation, BH-879)** Any callback claiming to complete
   a `WorkflowStepRunNode` must present a valid HMAC signature keyed to that
   step run's `callbackSecret`; a step run with no `callbackSecret` rejects
   all callbacks rather than skipping validation. See §0 Real Bugs Found #1.
10. **(Added post-implementation, BH-877/878)** All secret/token comparisons
    on this epic's auth paths (webhook token, scheduler service key) use
    constant-time comparison (`hmac.compare_digest`/`crypto.timingSafeEqual`),
    never `==`/`!=`. See §0 Real Bugs Found #3.

---

## 4. Acceptance Criteria

```gherkin
Feature: Execute Workflow Scheduling

  Scenario: User creates a workflow schedule
    Given an Admin or Collaborator has an ACTIVE WorkflowSpec project
    When they create an execute_workflow schedule for that project
    Then the schedule row contains workspace_id, project_id, owner_user_id, and cadence metadata
    And the row contains no token or secret fields
    And EventBridge Scheduler has an enabled schedule for the row

  Scenario: Scheduled run starts workflow execution
    Given an enabled execute_workflow schedule exists
    When EventBridge invokes the dispatcher
    Then the dispatcher revalidates the owner permission through Platform Core
    And Platform Core starts executeWorkflow for the schedule project
    And the schedule row shows last_run_status = "running"

  Scenario: Workflow completion updates schedule state
    Given a scheduled workflow run is running
    When the WorkflowRun reaches SUCCESS
    Then the matching schedule row is updated to last_run_status = "success"
    And running is false
    And last_run_id equals the WorkflowRun id
    And a scheduled_workflow_success notification is published once

  Scenario: Owner loses access before next run
    Given an execute_workflow schedule was created by a Collaborator
    And that user is removed or demoted to Viewer
    When the schedule fires
    Then no workflow step is started
    And the schedule row records last_run_status = "error"
    And the message says owner permission must be restored

  Scenario: Manual run uses the same path
    Given an execute_workflow schedule exists
    When the owner clicks Run now
    Then BrightBot invokes the dispatcher Lambda with trigger_source = "manual"
    And the same owner revalidation and completion bridge are used
```

---

## 5. Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Scheduled agent API | `brightbot` | Add action descriptors, payload validation, token-field rejection |
| Workflow runtime | `brighthive-platform-core` | Service-auth execution and terminal bridge |
| Dispatcher Lambda | `brighthive-platform-core` | Secure service auth and trigger context |
| Notifications | `brighthive-platform-core`, `brightbot-slack-server`, `brighthive-webapp` | New workflow stages/display/card |
| Schedules UI | `brighthive-webapp` | Workflow labels and project/workflow picker/prefill |
| E2E | `brighthive-e2e` | Contract test for schedule to workflow run to notification |

---

## 6. Test Plan

- BrightBot unit tests:
  - `execute_workflow` allowed.
  - required payload keys enforced.
  - forbidden token fields rejected recursively.
  - run-now rejects unsupported actions and preserves overlap behavior.
- Platform Core unit tests:
  - dispatcher service-auth path never reads `auth_token`.
  - owner role revalidation accepts Admin/Collaborator and rejects Viewer,
    Contributor, Agent Guest, and removed users.
  - terminal bridge idempotency.
- Webapp tests:
  - action label renders.
  - workflow schedule payload is built without asset fields or tokens.
  - controls fit at 320px.
- E2E:
  - Extend `brighthive-e2e/specs/scheduler/SPEC-E2E-SCHEDULER.md`.
  - AC maps to tests under `e2e/features/scheduler/`.
  - Staging/local override path: schedule -> run-now -> WorkflowRun -> schedule
    terminal status -> notification inbox.

---

## 7. Dependencies

| Dependency | Type | Status |
|---|---|---|
| Scheduled agent table and EventBridge Scheduler | Blocking | Exists |
| Dispatcher `execute_workflow` registry entry | Blocking | Exists |
| Platform Core `executeWorkflow` | Blocking | Exists |
| WorkflowSpec AGENT adapter | Blocking | Exists |
| Service-auth owner revalidation | Blocking | New |
| Terminal completion bridge | Blocking | New |
| Notification display/card for workflow stages | Blocking | New |

---

## 8. PR Split

Keep one PR per repo and under the BrightHive PR-size rules.

| PR | Repo | Scope | Ticket | Target Size |
|---|---|---|---:|---:|
| 1 | `brightbot` | action descriptors, schedule DTO validation, tests | [BH-877](https://brighthiveio.atlassian.net/browse/BH-877) | <300 lines |
| 2 | `brighthive-platform-core` | service-auth scheduler execution context | [BH-878](https://brighthiveio.atlassian.net/browse/BH-878) | <500 lines |
| 3 | `brighthive-platform-core` | terminal bridge and workflow notification signal | [BH-879](https://brighthiveio.atlassian.net/browse/BH-879) | <500 lines |
| 4 | `brighthive-webapp` | metadata-driven workflow schedule UI | [BH-880](https://brighthiveio.atlassian.net/browse/BH-880) | <500 lines |
| 5 | `brightbot-slack-server` | scheduled workflow notification formatting | [BH-879](https://brighthiveio.atlassian.net/browse/BH-879) | <300 lines |
| 6 | `brighthive-e2e` | P1 scheduler workflow contract | [BH-881](https://brighthiveio.atlassian.net/browse/BH-881) | <300 lines |

---

## 9. UAT Pre-Prod Findings (2026-07-03)

Extensive UAT-style pre-prod sweep run after all P1 tickets merged to `develop`
across all 5 repos, before staging verification (blocked, see §0). Combined a
3-agent parallel code review (platform-core, brightbot, webapp+slack-server+e2e)
with direct-code-read verification of every High-severity claim before
ticketing — nothing below is speculative.

| Ticket | Severity | Finding | Repo | Status |
|---|---|---|---|---|
| [BH-917](https://brighthiveio.atlassian.net/browse/BH-917) | High | Deleting a schedule mid-run resurrects a malformed row — no existence/running guard on the dispatcher's DynamoDB `update_item` calls | brightbot, platform-core | ✅ Fixed, merged to `develop` |
| [BH-918](https://brighthiveio.atlassian.net/browse/BH-918) | High | No timeout for an AGENT step whose runtime never calls back — can hang RUNNING forever, permanently disabling that schedule | platform-core | ✅ Fixed, merged to `develop` |
| [BH-919](https://brighthiveio.atlassian.net/browse/BH-919) | High | 4th instance of the non-constant-time secret-comparison bug class, in `notifications.ts` (pre-existing, not introduced by this epic, same `x-service-key` attack surface family) | platform-core | ✅ Fixed, merged to `develop` |
| [BH-920](https://brighthiveio.atlassian.net/browse/BH-920) | High | Webapp lets a user create an `execute_workflow` schedule against a project with no compiled WorkflowSpec — guaranteed-fail schedule, zero warning at creation time | webapp | ✅ Fixed — [PR #1254](https://github.com/brighthive/brighthive-webapp/pull/1254) (draft) |
| [BH-921](https://brighthiveio.atlassian.net/browse/BH-921) | Medium | `execute_workflow` has zero e2e coverage against a real deployed dev/staging environment — only the local-only lifecycle test exists | e2e | ✅ Fixed — [PR #27](https://github.com/brighthive/brighthive-e2e/pull/27) (draft) |
| [BH-922](https://brighthiveio.atlassian.net/browse/BH-922) | Medium | Unescaped user-controlled `display_name` (and other producer-supplied fields) in Slack mrkdwn — link/formatting injection risk | slack-server | ✅ Fixed — [PR #106](https://github.com/brighthive/brightbot-slack-server/pull/106) (draft) |
| [BH-923](https://brighthiveio.atlassian.net/browse/BH-923) | Medium | Rejected dbt trigger mishandled as RUNNING instead of failing immediately (Datapiary was already correct) | platform-core | ✅ Fixed — [PR #973](https://github.com/brighthive/brighthive-platform-core/pull/973) (draft) |
| [BH-924](https://brighthiveio.atlassian.net/browse/BH-924) | Medium | A transport-level (not GraphQL-rejection) call failure before a `WorkflowRun` exists is invisible to the poller/retry-sweep recovery path | platform-core | ✅ Fixed — [PR #974](https://github.com/brighthive/brighthive-platform-core/pull/974) (draft) |
| [BH-925](https://brighthiveio.atlassian.net/browse/BH-925) | Low | Batch: unescaped IDs, missing click-through links, route-visibility UX inconsistency, missing regression tests | webapp, slack-server | Open |

**None of these block the epic's own P1 acceptance criteria** (§4) — all 4
Gherkin scenarios there pass against real local infra (see §0). They are
real gaps found by testing *beyond* the original spec's explicit scope,
surfaced because this epic's own verification discipline (real local infra,
no mocks) is thorough enough to find them. All 4 High-severity items
(BH-917/918/919/920) and all 4 Mediums (BH-921, BH-922 security-relevant,
BH-923, BH-924) are now fixed or in draft PR awaiting review; only BH-925
(Low) remains open. Independent of these, the epic still needs the
staging-deploy blockers in §0 resolved before it's genuinely
production-ready.
