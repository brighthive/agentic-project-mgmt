---
title: Routine permissions — one decision in platform-core
epic: BH-1464
tickets: [BH-1565]
author: kuri
status: Draft
created: 2026-10-05
last-reviewed: 2026-10-05
generates: tickets
tags:
  - authz
  - routines
  - scheduler
related:
  specs:
    - access-decision-and-governance-enforcement.md
    - brightroutines-your-routines-persistence.md
  features: []
  pocs: []
  bedrock: []
roadmap: next — follows BH-1564 (brightbot #1107, merged to develop)
---

# Routine permissions — one decision in platform-core

## 1. Context

Who may change a routine (a recurring job BrightAgent runs on a schedule) is decided in two places today, with two copies of the same rule: **the owner, or a workspace admin**.

- brightbot `routes/schedule_access.py` (BH-1564) guards edit, enable/disable, run-now and delete on `/manage/scheduled-agents/{id}`. It compares `workspaceRole == "ADMIN"` in Python.
- platform-core `unscheduleRoutine` (`models/routine-suggestion.ts`) checks `owner_user_id === token.sub`, else the admin group.

The access-decision spec forbids a second verdict in Python (INV-12), and a workspace admin can't change either copy from the permission-matrix editor. This spec moves the rule into platform-core's `authorize()` as a **ROUTINE** resource kind, so both callers ask one place.

Two facts shape the design:

1. `authorize()` can only check ownership through a Neo4j edge (`OWNER_OR_MANAGER` → `OWNS|MANAGES|CONTRIBUTES_TO`). Today only routines scheduled from a suggestion get a `RoutineScheduleNode` with an `OWNS` edge. Schedules created from the Schedules page, the agent tool or MCP have no node, so a check against them would refuse everyone.
2. `checkAccess` runs in shadow mode on dev and prod, where a refusal comes back as `ALLOW` with `decidedBy: "shadow"`. The guard it replaces is already enforced everywhere, so callers here treat a shadowed refusal as a refusal.

So the work ships in two phases:

```mermaid
flowchart LR
  subgraph P1[Phase 1 — platform-core]
    K[ROUTINE kind + binding] --> C[default cells + backfill]
    C --> U[unscheduleRoutine asks authorize()]
  end
  subgraph P2[Phase 2 — every schedule in the graph]
    R[brightbot records each schedule in platform-core] --> B[backfill existing schedules]
    B --> G[brightbot guard asks checkAccess]
  end
  P1 --> P2
```

## 2. Interface contract

### 2.1 Vocabulary (closed, INV-10)

```ts
// permission-matrix.ts, both SDLs, @authorized's AuthResourceKind, brightbot's ResourceKind mirror
type ResourceKind = ... | "ROUTINE";
```

`resource.id` for ROUTINE is the brightbot **schedule id** (the DynamoDB `schedule_id`, also `linked_schedule_id` on a routine suggestion).

### 2.2 Graph shape

```
(RoutineScheduleNode {id: scheduleId, workspaceId})-[:BELONGS_TO]->(WorkspaceNode)
(UserNode)-[:OWNS]->(RoutineScheduleNode)     // creator, and the run-as user for execute_workflow
```

`BINDING_CYPHER.ROUTINE` binds through `BELONGS_TO`, the same pattern as `AGENT`.

### 2.3 Default cells (`SEED_DEFAULTS`, plus backfill for existing workspaces)

| Role | UPDATE · ROUTINE | DELETE · ROUTINE | RUN · ROUTINE |
|---|---|---|---|
| WORKSPACE_ADMIN | ✅ | ✅ | ✅ |
| COLLABORATOR, CONTRIBUTOR, VIEWER, AGENT_GUEST | `OWNER_OR_MANAGER` | `OWNER_OR_MANAGER` | `OWNER_OR_MANAGER` |

This reproduces today's rule exactly: any member may change what they own, and admins may change anything. Reading and creating schedules aren't gated by this spec.

### 2.4 Phase 2 — recording schedules (platform-core, service-key only)

```graphql
recordRoutineSchedule(input: { workspaceId: ID!, scheduleId: ID!, ownerUserIds: [ID!]! }): Boolean!
forgetRoutineSchedule(input: { workspaceId: ID!, scheduleId: ID! }): Boolean!
```

- `record` MERGEs the node, `BELONGS_TO`, and one `OWNS` per owner id. It's idempotent.
- `forget` runs `DETACH DELETE`, and is a no-op if the node is already gone.

### 2.5 brightbot route → check

| Route | Verb |
|---|---|
| `PATCH /manage/scheduled-agents/{id}` (edit, enable/disable) | UPDATE |
| `DELETE /manage/scheduled-agents/{id}` | DELETE |
| `POST /manage/scheduled-agents/{id}/run` | RUN |

| Answer | brightbot response |
|---|---|
| ALLOW and `decidedBy != "shadow"` | continue |
| BLOCK, or ALLOW with `decidedBy == "shadow"` | 403, same detail as today |
| `checkAccess` unreachable / errors | 503, same detail as today |

Service-key callers (Slack) have no JWT, so `checkAccess` can't answer for them. They keep the owner-only check in brightbot.

## 3. Invariants

- **INV-1** WHEN brightbot or platform-core decides whether a user may change a routine, THE System SHALL ask `authorize()` (directly or via `checkAccess`) and SHALL NOT compare a role name in code.
- **INV-2** IF the decision is BLOCK, or ALLOW decided by shadow, THEN THE System SHALL refuse the change.
- **INV-3** IF the decision can't be obtained, THEN THE System SHALL refuse with a retryable 503 and SHALL NOT grant access.
- **INV-4** Ownership SHALL come from Neo4j `OWNS` edges, never from a caller-supplied id.
- **INV-5** Every live brightbot schedule SHALL have exactly one `RoutineScheduleNode` bound to its workspace (Phase 2 onward).
- **INV-6** A deleted or turned-off schedule SHALL leave no `RoutineScheduleNode` behind.
- **INV-7** Phase 2 SHALL NOT remove brightbot's local guard until INV-5 holds in that environment (backfill done and verified).

## 4. Acceptance criteria

```gherkin
Feature: One permission decision for routines

  Scenario: Owner changes their routine
    Given a routine owned by user A
    When A edits, disables, runs or deletes it
    Then authorize() returns ALLOW by condition and the change happens

  Scenario: Workspace admin changes another member's routine
    Given a routine owned by user A
    When admin B deletes it
    Then authorize() returns ALLOW by matrix

  Scenario: Collaborator is refused
    Given a routine owned by user A
    When collaborator C tries to edit it
    Then the response is 403 and nothing changes

  Scenario: Shadow mode does not open the door
    Given DELETE is shadowed in this environment
    When collaborator C deletes A's routine
    Then checkAccess returns ALLOW decided by "shadow"
    And brightbot still refuses with 403

  Scenario: Admin edits the matrix
    Given an admin grants UPDATE·ROUTINE unconditionally to COLLABORATOR
    When collaborator C edits A's routine
    Then the change is allowed

  Scenario: Permission service down
    Given checkAccess times out
    When admin B deletes A's routine
    Then the response is 503 and the routine still exists

  Scenario: Turning off cleans up
    Given a routine turned off through unscheduleRoutine
    Then its RoutineScheduleNode no longer exists

  Scenario: Every schedule is recorded (Phase 2)
    Given a schedule created from the Schedules page by user A
    Then a RoutineScheduleNode bound to the workspace exists with (A)-[:OWNS]->
```

## 5. Out of scope

- Gating read or create of schedules.
- Slack (service-key) admin override. That needs a service-key form of `checkAccess`.
- Showing owner names in the webapp (BH-1567 shows locked controls only).
- Flipping any verb from shadow to enforced. That stays with ADR-0003's ramp.

## 6. Dependencies

- BH-1564 (brightbot guard, merged), BH-1472 (`checkAccess`), BH-1476 (`OWNER_OR_MANAGER`), BH-1488 (resource binding).
- Phase 2 needs read access to each env's scheduled-agents DynamoDB table for the backfill.

## 7. Correctness properties

### Property 1: No role names in code
*For any* routine change, the allow/deny verdict comes from `authorize()`.
**Validates: §3 INV-1, §4 "Admin edits the matrix"**

### Property 2: Shadow never grants
*For any* environment's shadow configuration, a refused routine change stays refused.
**Validates: §3 INV-2, §4 "Shadow mode does not open the door"**

### Property 3: Outage never grants
*For any* failure to obtain a decision, the change is refused with 503.
**Validates: §3 INV-3, §4 "Permission service down"**

### Property 4: The graph matches the store
*For any* live schedule after Phase 2, exactly one bound node exists, and none exists after deletion.
**Validates: §3 INV-5, INV-6, §4 "Every schedule is recorded", "Turning off cleans up"**

## 9. Observability contract

- **Log events** (brightbot): `[SCHEDULER] Refused schedule change` with `schedule`, `caller`, `verb`, `reason`, `decidedBy`; `[SCHEDULER] Permission check unavailable`.
- **Log events** (platform-core): existing `authorize()` decision logging; `[routines] record/forget schedule failed` on Phase 2 mutations.
- **Metrics**: none new.

## 10. Test coverage

| Layer | Where | Cases |
|---|---|---|
| L0 surface | platform-core `tests/unit/permission-matrix.test.ts` | ROUTINE in every enum; kinds 9→10; seed cell counts updated; SDL regenerated (`check:core-api-schema`) |
| L1 routing | platform-core `tests/unit/authorize.test.ts`, `check-access.test.ts` | ROUTINE · {UPDATE, DELETE, RUN}: admin → matrix ALLOW; owner → condition ALLOW; non-owner → BLOCK; unbound id → `resource_scope` BLOCK |
| L2 behavior (real Neo4j) | platform-core `tests/integration/authorize.behavior.test.ts` | owner/admin/collaborator against real `OWNS` + `BELONGS_TO`; `forget` removes the node |
| L2 behavior (real DynamoDB, LocalStack) | `tests/unit/routine-unschedule-mutation.test.ts` | unscheduleRoutine refuses via `authorize()`; node removed on success |
| L2 behavior (moto) | brightbot `tests/integration/test_scheduled_agents_execute_workflow_dynamodb.py` | swap the role-lookup fake for a `checkAccess` fake: shadow ALLOW → 403, outage → 503, real ALLOW → passes |
| e2e | brighthive-e2e (BH-1569) | real staging ADMIN and COLLABORATOR against a recorded schedule |
