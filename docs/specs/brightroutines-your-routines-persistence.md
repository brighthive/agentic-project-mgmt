---
title: BrightRoutines — "Your routines" Persistence
epic: BH-876
tickets: [BH-885]
author: kuri
status: draft
created: 2026-07-04
generates: tickets
tags:
  - brightagent
  - routines
  - persistence
  - webapp
related:
  specs:
    - brightroutines-intent-loop.md
  features: []
  pocs: []
  bedrock: []
---

# SPEC: BrightRoutines — "Your routines" Persistence

> Scope: the read-back half of BH-885. The offer→schedule→dismiss **write**
> path already shipped and is live on staging (see parent spec
> `brightroutines-intent-loop.md` §7). This spec closes the one remaining gap
> that makes scheduled routines feel unreal: they vanish on reload.

## 1. Context

**Problem.** On the Workflows surface (`/context/workflows`), the "Your
routines" section — the routines a user has turned on — is held in React
`useState` in `SuggestedRoutinesSection.tsx`. Scheduling a suggestion moves it
into that local array; a page reload throws the array away. The backend row is
correctly transitioned to `SCHEDULED` (the `scheduleRoutineSuggestion` mutation
writes the `SUGGESTION_STATUS#{ws}#SCHEDULED` GSI4 partition), but the webapp
has no way to read it back, so "Your routines" renders empty after every
reload. There is also no way to turn a routine **off** — `handleUnschedule`
only mutates local state (`TODO(BH-885)` at `SuggestedRoutinesSection.tsx:166`).

**Who / why now.** The buyer persona (a data leader) turns on a routine, leaves
the page, comes back, and their routines are gone — the feature reads as broken
even though the backend is correct. This is the last blocker to "Your routines"
being a trustworthy, durable surface. The recurrence-detection loop (capture →
detect → offer) is verified live; this is purely the read-back + turn-off.

```mermaid
sequenceDiagram
    actor U as User
    participant W as Webapp (Workflows)
    participant PC as Platform Core (Apollo)
    participant DDB as brightroutines-{env} (GSI4)

    U->>W: Schedule a suggestion
    W->>PC: scheduleRoutineSuggestion(ws, id)
    PC->>DDB: OFFERED → SCHEDULED (writes SUGGESTION_STATUS#ws#SCHEDULED)
    Note over W: TODAY: also pushed to local useState — lost on reload
    U->>W: Reload page
    W->>PC: scheduledRoutinesForWorkspace(ws)  ← NEW
    PC->>DDB: Query GSI4 SUGGESTION_STATUS#ws#SCHEDULED
    DDB-->>W: durable SCHEDULED rows → "Your routines" survives reload
    U->>W: Turn one off
    W->>PC: unscheduleRoutine(ws, id)  ← NEW
    PC->>DDB: SCHEDULED → OFFERED (+ deletes execute_workflow schedule)
```

## 2. Interface Contract (MDE)

### 2.1 New query — read SCHEDULED routines

Mirrors the existing `routineSuggestionsForWorkspace` (which reads the OFFERED
partition) but targets the SCHEDULED partition. Same `RoutineSuggestion` type,
same membership gate.

```graphql
# schema/typedefs.ts — Query
scheduledRoutinesForWorkspace(workspaceId: ID!): [RoutineSuggestion!]!
  @authenticated(workspaceIdLoc: ["args", "workspaceId"])
```

- **Returns**: `RoutineSuggestion` rows with `status == "SCHEDULED"`, newest
  first, paginated over GSI4 with the same `MAX_PAGES` cap as the OFFERED read.
- **Auth**: `@authenticated(workspaceIdLoc:["args","workspaceId"])` — the same
  workspace-membership gate the OFFERED query uses (a bare `@authenticated`
  would be a cross-tenant read; see parent spec §9 and the BH-885 read-slice
  self-audit fix).

### 2.2 New mutation — turn a routine off

```graphql
# schema/typedefs.ts — Mutation
unscheduleRoutine(
  workspaceId: ID!
  routineSuggestionId: ID!
): RoutineSuggestion!
  @authenticated(workspaceIdLoc: ["args", "workspaceId"])
```

- **Effect**: `SCHEDULED → OFFERED`; deletes the backing `execute_workflow`
  schedule in brightbot; clears `linked_schedule_id` and ownership fields; moves
  the GSI4 partition `SUGGESTION_STATUS#{ws}#SCHEDULED → #OFFERED`.
- **Return**: the updated `RoutineSuggestion` (status now `OFFERED`), so the
  webapp can move it back into "Suggested" without a refetch.
- **Idempotent**: calling on a row already `OFFERED` (or absent) returns it
  unchanged / a typed not-found; never errors on a double-tap.

### 2.3 Webapp hook surface

`useRoutineSuggestions` gains a scheduled list and an unschedule action. The
call sites (`SuggestedRoutinesSection`) drop their local `scheduled` state.

```typescript
export interface UseRoutineSuggestionsResult {
  suggestions: RoutineSuggestion[];        // OFFERED (unchanged)
  scheduledRoutines: RoutineSuggestion[];  // NEW — SCHEDULED, server-fetched
  loading: boolean;
  error: Error | undefined;
  removeSuggestion: (id: string) => void;
  restoreSuggestion: (id: string) => void;
  scheduleSuggestion: (id: string, recipientUserIds?: string[]) => Promise<void>;
  dismissSuggestion: (id: string) => Promise<void>;
  unscheduleRoutine: (id: string) => Promise<void>;  // NEW
}
```

## 3. Invariants (DbC)

1. `scheduledRoutinesForWorkspace` returns ONLY rows whose `status == SCHEDULED`
   for the requested workspace. No OFFERED/DISMISSED/SUPPRESSED/EXPIRED leak in.
2. `WHERE the caller is not a member of workspaceId, THE System SHALL return a
   FORBIDDEN authorization error` (never rows from another tenant) — for both
   the new query and the new mutation.
3. `WHEN unscheduleRoutine succeeds, THE System SHALL delete the backing
   execute_workflow schedule` — a turned-off routine never fires again.
4. `unscheduleRoutine` is idempotent: applying it to a non-SCHEDULED row is a
   no-op that returns the current row, not an error.
5. After a successful schedule OR unschedule, a fresh page load reflects the new
   state with no client-held state — the server is the single source of truth
   for which routines are on.
6. The webapp holds NO scheduled-routine list in `useState`; "Your routines" is
   derived entirely from `scheduledRoutinesForWorkspace`. Optimistic UI is
   allowed (move-on-click) but every optimistic move is backed by a server
   mutation and reconciled on the next query result.
7. Counts-only evidence still holds (parent §9 invariant 3): the SCHEDULED read
   returns the same redacted `evidence_summary` shape as OFFERED — no raw text.

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: "Your routines" persists across reloads

  Scenario: Scheduled routine survives a reload
    Given a workspace with one OFFERED routine suggestion
    And I schedule it
    When I reload the Workflows page
    Then the routine appears under "Your routines"
    And it is no longer under "Suggested"

  Scenario: Reading scheduled routines is membership-gated
    Given a workspace I am NOT a member of
    When I query scheduledRoutinesForWorkspace for that workspace
    Then I receive a FORBIDDEN error
    And no routine rows are returned

  Scenario: Turning a routine off stops it and returns it to Suggested
    Given a SCHEDULED routine in my workspace
    When I turn it off
    Then its status becomes OFFERED
    And the backing execute_workflow schedule is deleted
    And on reload it appears under "Suggested", not "Your routines"

  Scenario: Turning off is idempotent
    Given a routine that is already OFFERED
    When unscheduleRoutine is called on it
    Then it returns the routine unchanged
    And no error is raised

  Scenario: Empty scheduled list renders the anchored empty state
    Given a workspace with no SCHEDULED routines
    When I load the Workflows page
    Then "Your routines" shows its "No routines running yet" empty state
    And the section is still anchored (not hidden)
```

## 5. Out of Scope

- Editing a scheduled routine's cadence/recipients in place (that is BH-970
  editable-recipient + a future edit-schedule mutation).
- Slack "Your routines" parity (BH-887 surface; this spec is webapp-only).
- Pausing (vs. turning off) a routine — no PAUSED state in this slice; off means
  `SCHEDULED → OFFERED`.
- Any change to the capture/detect/offer path — that loop is done and verified.
- A "run history" / last-run view for scheduled routines (net-new, not filed).

## 6. Dependencies

- **Shipped**: `scheduleRoutineSuggestion` / `dismissRoutineSuggestion`
  mutations + `routineSuggestionsForWorkspace` query (BH-885 write/read slices,
  live on staging). The `SUGGESTION_STATUS#{ws}#SCHEDULED` GSI4 partition
  already exists — the schedule mutation writes it.
- **Shipped**: `execute_workflow` schedule create/delete in brightbot (P1,
  BH-877/878) — `unscheduleRoutine` calls the existing delete path.
- **Reuse, do not duplicate**:
  - `RoutineSuggestionModel.listForWorkspace`-style GSI4 pagination
    (`routine-suggestion.ts` ~L220) — the new query is the same shape with a
    different status partition.
  - `filterRecipientsToWorkspaceMembers` / the `@authenticated` directive — the
    membership gate is identical to the OFFERED query.
  - The scheduling state machine + stale-lock reclaim in
    `routine-schedule-state.ts` — unschedule is the reverse transition; reuse
    the same conditional-write discipline.
  - `useRoutineSuggestions` mapper (`toRoutineSuggestion`) — the SCHEDULED read
    maps through the exact same camelCase→snake_case seam.

## 7. Correctness Properties

State machine + a cross-tenant boundary are both in play, so this section
applies (per spec-driven §7 required-when).

### Property 1: SCHEDULED read is status- and tenant-exact

*For any* workspace `w` and caller `c`, `scheduledRoutinesForWorkspace(w)`
returns exactly the rows with `status == SCHEDULED` and `workspace_id == w`,
and only if `c` is a member of `w`; otherwise FORBIDDEN with zero rows.

**Validates: §3 Invariant 1, §3 Invariant 2, §4 Scenario "membership-gated"**

### Property 2: Off means off

*For any* SCHEDULED routine `r`, a successful `unscheduleRoutine(r)` leaves no
live `execute_workflow` schedule that can fire `r`, and `r.status == OFFERED`.

**Validates: §3 Invariant 3, §4 Scenario "Turning a routine off…"**

### Property 3: Server is the source of truth for on/off

*For any* sequence of schedule/unschedule actions, a fresh page load with an
empty client cache renders "Your routines" identical to
`scheduledRoutinesForWorkspace`'s result.

**Validates: §3 Invariant 5, §3 Invariant 6, §4 Scenario "survives a reload"**

## 9. Observability Contract

This slice produces a production surface (two GraphQL operations), so:

- **Query `scheduledRoutinesForWorkspace`**: log events
  `routines.scheduled_read.started`, `routines.scheduled_read.success`
  (with `workspace.id`, `routines.scheduled_count`),
  `routines.scheduled_read.forbidden` (membership denial).
- **Mutation `unscheduleRoutine`**: log events `routines.unschedule.started`,
  `routines.unschedule.success` (with `workspace.id`, `routine.id`,
  `schedule.deleted=true`), `routines.unschedule.noop` (already OFFERED),
  `routines.unschedule.forbidden`.
- **Attributes**: never log raw routine title/summary — counts + ids only
  (parent §9 invariant 3).
- **Metrics**: none new; the P4 precision/acceptance metrics (BH-888) already
  cover schedule/dismiss rates. Turn-off rate is worth a counter later but is
  not gated here.

## 10. Test Coverage Update

### a. In-repo layered tests

**platform-core** (`src/graphql/models/__tests__/` + resolver tests):
- **L0** — `scheduledRoutinesForWorkspace` returns the `RoutineSuggestion` shape
  from §2.1; `unscheduleRoutine` returns the updated row shape from §2.2.
- **L1** — the query dispatches to the SCHEDULED GSI4 partition (not OFFERED);
  the mutation dispatches to the unschedule transition.
- **L2** — §3 invariants against a **real LocalStack DynamoDB** (mirror the
  BH-885 read-slice LocalStack tests): seed one SCHEDULED + one OFFERED row,
  assert the query returns only the SCHEDULED one; run `unscheduleRoutine` and
  assert the row flips to OFFERED, the GSI4 partition moves, and the schedule-
  delete client was invoked; assert idempotent no-op on an already-OFFERED row;
  assert a non-member caller gets FORBIDDEN (real `@authenticated` path).

**webapp** (`src/Context/routines/*.test.tsx`, jest — the repo uses jest, not
vitest):
- **L2** — `useRoutineSuggestions` exposes `scheduledRoutines` from a mocked
  `scheduledRoutinesForWorkspace` result; `unscheduleRoutine` calls the mutation
  and reconciles on refetch; `SuggestedRoutinesSection` renders scheduled rows
  from the hook (NOT `useState`) and shows the empty state when the list is
  empty. Extend the existing `SuggestedRoutinesSection.test.tsx` /
  `useRoutineSuggestions.test.tsx` — do not add sibling files.

### b. Cross-repo e2e (`brighthive-e2e`)

- **Feature test** — the §4 happy path end-to-end against staging: seed an
  OFFERED row, schedule via the real mutation, assert
  `scheduledRoutinesForWorkspace` returns it; unschedule, assert it flips back
  to OFFERED and the schedule is gone. Extend
  `e2e/surfaces/test_routines.py` (the file that already covers the read query
  + schedule/dismiss), not a new file.
- **Error path** — a non-member token calling `scheduledRoutinesForWorkspace`
  gets FORBIDDEN against the real backend.

### Self-verification (before the implementation PR)

Run platform-core jest + webapp jest + the brighthive-e2e routines surface
suite against staging; confirm each §2/§3/§4 entry has a corresponding new
case, and all green. A green run with no new SCHEDULED-read / unschedule cases
means the contract wasn't enforced.

## 11. PR Split

| PR | Repo | Scope | Est. lines |
|---|---|---|---:|
| 1 | `brighthive-platform-core` | `scheduledRoutinesForWorkspace` query + resolver + model read, LocalStack L2 | ~250 |
| 2 | `brighthive-platform-core` | `unscheduleRoutine` mutation + reverse transition + schedule-delete client + LocalStack L2 | ~300 |
| 3 | `brighthive-webapp` | hook `scheduledRoutines` + `unscheduleRoutine`; `SuggestedRoutinesSection` drops local state; jest L2 | ~250 |
| 4 | `brighthive-e2e` | surface + feature + FORBIDDEN cases against staging | ~150 |

Split so each PR stays well under the 900-line ceiling and the backend read
(PR 1) can land + deploy before the webapp (PR 3) depends on it. PR 2
(unschedule) is independent of PR 1 and can proceed in parallel.
