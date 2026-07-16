---
title: "Notify me on this chat session — completion + interrupt alerts for BrightAgent threads"
epic: "BH-409"
author: "Marwan Samih"
status: "Approved"
created: "2026-07-14"
generates: "tickets"
tags: ["brightsignals", "brightagent", "notifications", "cross-repo"]
related:
  specs:
    - slack-routine-suggestion-scheduling.md
  features: []
  pocs: []
  bedrock: []
---

# Notify me on this chat session

> Not a new delivery channel — this spec adds a new *trigger* (a LangGraph chat thread reaching
> a terminal state or pausing on an interrupt) onto the existing, already-shipped delivery
> pipeline (`publishNotification` → Slack DM/channel + in-app inbox, per BH-1088). No new
> subscription scope, no new channel-adapter code.

## Contents

- [1. Context](#1-context)
- [2. Interface Contract (MDE)](#2-interface-contract-mde)
- [3. Invariants (DbC)](#3-invariants-dbc)
- [4. Acceptance Criteria (BDD — Gherkin)](#4-acceptance-criteria-bdd--gherkin)
- [5. Out of Scope](#5-out-of-scope)
- [6. Dependencies](#6-dependencies)
- [9. Observability Contract](#9-observability-contract)
- [10. Test Coverage Update](#10-test-coverage-update)
- [Areas Involved](#areas-involved)
- [Ticket Breakdown](#ticket-breakdown)
- [Related](#related)

## 1. Context

BrightAgent chat runs already execute independently of the browser tab — `useStreamReconnect.ts`
proves this: closing the tab does not kill the LangGraph run, and reopening the thread re-attaches
to a still-running stream via `GET /threads/{threadId}/runs?status=running`. The gap isn't "make
chat async" — it already is. The gap is that a user who starts a slow multi-minute agent turn (a
sub-agent delegation, a long tool chain, a HITL-gated flow) has no way to be told when it's safe to
come back; they either babysit the tab or periodically reload to check.

Today's closest precedent is `notifyScheduleOfRunCompletion()`
(`brighthive-platform-core/src/graphql/service/workflow/scheduler-bridge.ts:94`) — a specific
scheduled run reaching a terminal state, notifying only the schedule's owning user. This spec
copies that pattern's *shape* (idempotent claim → terminal-state detection → addressed
notification) for a fundamentally different trigger (an interactive chat run, not a cron-scheduled
one) — it does not call into or depend on the scheduler bridge at runtime; the only shared code is
the `publishNotification` mutation both callers invoke independently.

**Spike correction (BH-1100, resolved before this spec's other tickets started)**: the original
draft assumed brightbot would need either a LangGraph completion webhook of unknown existence, or
a poller. Direct inspection of the self-hosted `langgraph-api` package installed in brightbot's own
`.venv` (`langgraph_api==0.8.7`) confirms a **real per-run webhook already exists** in the platform
itself:
- `langgraph_api/webhook.py:call_webhook()` POSTs `{run, status, values, error, ...}` to a URL
  carried on the run.
- `langgraph_api/worker.py:73-78,138` — the webhook URL is `run["kwargs"]["webhook"]`, a **per-run
  field supplied at run-creation time** (same request as `assistant_id`/`input`), not a thread-level
  setting.
- `langgraph_api/worker.py:418` sets a distinct `status = "interrupted"` value (separate from
  `"success"`/`"error"`/`"timeout"`/`"rollback"`), and the `WorkerResult` (including `webhook`) is
  returned **unconditionally regardless of which status fired** (line 507-514) — one webhook
  mechanism covers both completion and interrupts, no separate plumbing needed for either.
- Confirmed the webapp's own run-creation call
  (`brighthive-webapp/src/BrightAgent/hooks/useAgentStream.ts:437`, `POST /threads/{id}/runs/stream`)
  goes **directly to LangGraph**, not through brightbot, and does not set `webhook` today — the
  field is unused and free to adopt.
- **Further simplification**: brightbot's own FastAPI app (`http/app.py`) is mounted *into the same
  deployed LangGraph Platform process* via `langgraph.json`'s `http.app` field — it is not a
  separate service. `webhook.py:202-204` (`if webhook.startswith("/"): ... get_loopback_client()`)
  confirms LangGraph explicitly supports a **relative-path webhook** for exactly this case. The
  webapp sets `webhook: "/manage/chat-sessions/webhook/run-complete"` (a relative path), not an
  absolute cross-service URL — no new domain allowlisting, no network reachability concern; only
  the shared-secret header (already implemented in BH-1101) guards the endpoint.

This **replaces** the original thread-metadata-flag design (§2.1/§2.2 below) with a simpler,
event-driven one: the webapp supplies `webhook` on the specific run being opted into, brightbot
runs a lightweight receiver endpoint, no polling, no thread-metadata read required for the trigger
itself. `notify_user_id` still rides on run metadata (see §2.2), reusing the same `user_id` field
already threaded by `useAgentStream.ts`.

```mermaid
sequenceDiagram
    participant User
    participant Webapp as brighthive-webapp
    participant LangGraph as LangGraph Platform (thread/run)
    participant Brightbot as brightbot (new webhook receiver)
    participant PlatformCore as brighthive-platform-core
    participant SlackServer as brightbot-slack-server

    User->>Webapp: Opts in ("Notify me") on a long-running turn
    Note over Webapp: Opt-in is per-run, not persisted to thread metadata (see §1 spike correction)
    Webapp->>LangGraph: POST /threads/{id}/runs/stream with webhook=<brightbot-url>, notify_user_id in run metadata
    Note over LangGraph: Run continues executing after tab closes (existing behavior)
    LangGraph->>Brightbot: POST webhook — fires on EVERY terminal run (confirmed: worker.py returns WorkerResult unconditionally for success/error/interrupted)
    Brightbot->>Brightbot: duration >= floor (skip for interrupts)? claim not already fired for run_id?
    Brightbot->>PlatformCore: publishNotification(stage: chat_run_complete | chat_run_interrupt, visibility: "user", audienceUserIds: [notify_user_id])
    PlatformCore->>SlackServer: (existing poller picks up the event — no new delivery code)
    SlackServer->>User: Slack DM: "Your BrightAgent session finished" + mute action
    PlatformCore->>User: In-app inbox card (existing Inbox fan-out)
```

### Use Case / Goal

A user kicks off a slow BrightAgent turn, opts in to "notify me," and closes the tab. When the run
finishes (or pauses waiting on their input via an interrupt), they get a Slack DM / inbox card —
*only if* they weren't already watching live, and only past a minimum duration floor, so the
feature never fires for the common case of a normal few-second chat turn.

### How It Works Today

- **Thread identity**: a LangGraph `thread_id` is the entire "session" concept. There is no
  `Conversation`/`Thread` row in platform-core's Neo4j graph — `brighthive-webapp`'s adapters
  (`src/BrightAgent/hooks/adapters/*.ts`) build thread metadata (`workspace_id`, `graph_id`,
  `Title`, `Author`) client-side and POST it straight to the LangGraph API; platform-core is never
  in the loop for thread creation.
- **`user_id` IS available on thread metadata**, just not from the adapter layer that builds
  initial metadata — it's threaded in separately by `useAgentStream.ts:560,566,580`
  (`metadata: { ...metadata, user_id: userId }`) and by both session-sidebar components
  (`FullPage/SessionSidebar/index.tsx:209,260`, `StudioPage/StudioSessionSidebar/index.tsx:240,305`).
  This is the field this spec's `notify_user_id` piggybacks on — no new identity plumbing needed.
- **Runs survive tab closure today.** `useStreamReconnect.ts:checkForRunningStream()` queries
  `GET /threads/{threadId}/runs?status=running`; `useAgentLifecycle.ts:246-251` calls this on
  thread load and rejoins the SSE stream via `stream.joinExistingStream(threadId, runId)` if a run
  is still executing server-side. This is the existing "user comes back later" precedent this spec
  extends with a push instead of a pull.
- **HITL interrupts already pause runs indefinitely.** `brightbot/brightbot/utils/interrupt_utils.py`'s
  `interruptible()` wraps LangGraph's `interrupt()`; the webapp's `get_state` response surfaces
  `interrupts: [...]`, rendered by `useAgentInterrupt.ts`. A paused run can sit for hours/days —
  the checkpoint is the persistence layer.
- **Notification delivery — mostly reusable, one real gap found post-launch (2026-07-16).**
  `writeNotificationSignal()` (`brighthive-platform-core/src/graphql/service/aws/
  notification-signal.ts:51`) accepts `visibility` (`"workspace"` default | `"user"`) and
  `audienceUserIds: string[]` (line 18, 38), and platform-core's Inbox fan-out
  (`notification-preference.ts`'s `signalPassesPreferenceFilter`) genuinely does honor both
  fields with zero new code — that half of "reusable as-is" was correct. **What was wrong**:
  `brightbot-slack-server`'s `SlackChannel.deliver()` (`src/notifications/channels/slack.ts`)
  never reads `visibility`/`audience_user_ids` at all — it matches events purely against
  pre-declared `Subscription` rows (`event_filter`/`asset_filter`/`severity_filter`), which
  nothing in this feature ever created. Every real chat-notify event published correctly but
  produced zero Slack messages, silently (`match_count: 0`, no error). Fixed by having
  brightbot's webhook receiver auto-provision a `PERSONAL`/`SLACK_DM` subscription for both
  stages on a user's first opt-in, via the same `createNotificationSubscription` mutation +
  `x-service-key`/`actingUserId` dual-auth path `scheduled_agents_routes.py`'s scheduler
  provisioning already uses (see §2.2). "Same mechanism BH-1088's personal-scope Slack DMs
  already use" was never actually true for a *new* stage with no subscription UI of its own —
  BH-1088's precedent (a scheduled run's owner) works because *something* creates that
  subscription; this spec never specified what would for chat sessions.

### Hard Limitations

- **No server-side "is the user watching" signal exists today.** The SSE stream between browser
  and the LangGraph API is not observable from brightbot or platform-core — there is no
  active-listener count, no heartbeat, nothing. This spec's presence-check gate (§3 Invariant 2)
  requires *new* plumbing (a lightweight heartbeat the webapp sends while the stream tab is open,
  or a `last_seen` timestamp on thread metadata updated client-side) — this is a genuine gap, not
  something being "reused." **Still open after BH-1100** — the webhook spike resolved *how
  brightbot learns a run is terminal*, not *whether the user is watching when it happens*. These
  are separate problems; only the first is solved.
- ~~No completion webhook exists on the LangGraph run lifecycle today~~ — **resolved by BH-1100**,
  see the spike correction in §1 above. LangGraph Platform's own per-run `webhook` field covers
  both completion and interrupts; no poller needed.

### Gaps

1. The webapp's `runs/stream` call never sets `webhook` — no run is opted in today.
2. No brightbot receiver endpoint exists for LangGraph's per-run webhook POST.
3. No `chat_run_complete` / `chat_run_interrupt` stage constant exists in
   `notification_constants.py` (brightbot) or the webapp's `BackendStage` union
   (`brighthive-webapp/src/Notifications/types.ts`).
4. No presence-check / "is this session actively being watched" signal exists anywhere — genuinely
   unresolved even after BH-1100 (see Hard Limitations).
5. No minimum-duration gate exists for this trigger (the webhook payload includes
   `run_started_at`/`run_ended_at` per `worker.py:507-514` — the floor can be computed directly
   from the webhook payload itself, no separate metadata read required).
6. No UI affordance exists to opt in ("Notify me" toggle/offer in the chat header) or to mute after
   the fact (one-click mute action embedded in the delivered notification).
7. No idempotent claim exists to guarantee "fire once per run" the way `scheduleNotifiedAt` does
   for scheduled runs (§3 Invariant 4).

## 2. Interface Contract (MDE)

### 2.1 Webapp run creation — opt-in via the run's own `webhook` + `metadata` fields

```
POST /threads/{threadId}/runs/stream   (existing LangGraph call, brighthive-webapp/src/BrightAgent/hooks/useAgentStream.ts:437)
  New fields, set ONLY when the user opts in for this run:
    webhook: "<BRIGHTBOT_BASE_URL>/manage/chat-sessions/webhook/run-complete"
    metadata.notify_user_id: string      # BrightHive user id — same value already
                                          # threaded as metadata.user_id elsewhere
```

No thread-level PATCH, no new persistence — the opt-in is a per-run parameter on the exact call
the webapp already makes to start a run. LangGraph carries `webhook` and `metadata` through to the
`WorkerResult` and includes them in the POST described in §2.2.

### 2.2 brightbot — new webhook receiver (confirmed mechanism, per BH-1100 spike)

```
POST /manage/chat-sessions/webhook/run-complete   (NEW)
  Called by LangGraph Platform's own langgraph_api/webhook.py:call_webhook() — brightbot does not
  poll or subscribe; LangGraph pushes this unconditionally once per run, for every terminal status
  (success | error | timeout | rollback) AND for interrupted (worker.py:418, returned in the same
  WorkerResult as any other status per worker.py:507-514).

  Request body — CORRECTED 2026-07-16 against a real captured payload (the original spec text
  here, and brightbot's original implementation, both wrongly assumed a nested "run" key —
  call_webhook() actually does `{**result["run"], "status": ..., ...}`, a SPREAD at the top
  level, per langgraph_api/webhook.py:180-192):
    { run_id, thread_id, assistant_id, metadata: { notify_user_id, workspace_id, Title?, ... },
      kwargs: { input, config, metadata: <LangGraph-internal config metadata, NOT the same dict —
      has no notify_user_id> }, status: "success"|"error"|"interrupted"|"timeout"|"rollback",
      run_started_at, run_ended_at, values: <checkpoint state>, error?: {...} }

Behavior:
  1. Skip if metadata.notify_user_id is absent (run was never opted in) — read metadata
     straight off the top level (payload["metadata"]), never payload["kwargs"]["metadata"].
  2. Skip if status != "interrupted" and (run_ended_at - run_started_at) < DURATION_FLOOR_SECONDS
     (default 20) — the floor does not apply to "interrupted".
  3. Skip if the thread is muted (§3 Invariant 5). (A presence/"actively watched" skip was built
     and shipped here, then removed 2026-07-15 — see Invariant 2's strikethrough note in §3.)
  4. Claim (see §3 Invariant 4) — skip if already claimed for this run_id.
  5. Ensure the user has a PERSONAL/SLACK_DM subscription for both chat_run_complete and
     chat_run_interrupt (added 2026-07-16 — see the Context note above and §6 Dependencies).
     First opt-in only, gated by a small idempotent DynamoDB row
     (BrightbotChatNotifySubscriptionsProvisioned); calls platform-core's
     createNotificationSubscription with the x-service-key + actingUserId dual-auth path
     (scheduled_agents_routes.py's scheduler provisioning uses the same mutation, but omits
     actingUserId and has therefore been silently failing on every call — do not copy that).
     Best-effort: a failure here (most commonly no linked Slack identity) never blocks the
     publish in step 6 — Inbox delivery is unaffected either way.
  6. Call platform-core's publishNotification:
       stage: "chat_run_interrupt" (status=="interrupted") | "chat_run_complete" (otherwise)
       status: "info" (interrupt) | "success"/"failed" (complete, mapped from LangGraph's status)
       visibility: "user"
       audienceUserIds: [notify_user_id]
       metadata: { thread_id, run_id, thread_title }
```

### 2.3 brighthive-platform-core — new stage constants only

```
No new mutation, no new resolver. Adds two stage string literals to the existing
PublishNotificationInput.stage free-text field (already untyped/string on the platform-core
side — brightbot's notification_constants.py and the webapp's BackendStage union are the only
places that need real enum-like additions):
  "chat_run_complete"
  "chat_run_interrupt"
```

### 2.4 brighthive-webapp — opt-in UI + mute action

```
Chat header (per open thread): toggle/offer "Notify me when this finishes"
  On:  the NEXT runs/stream call for this thread includes webhook + metadata.notify_user_id (§2.1)
  Off: the NEXT runs/stream call omits both — no request needed, opt-in is per-run, not persisted

Delivered notification (Slack block + inbox card): "Mute this session" action
  → Since there is no persisted per-thread opt-in flag to clear (§2.1's correction — the opt-in is
    per-run, not a thread-level setting), "mute" here means: brightbot records a per-thread
    suppression (a lightweight store, keyed by thread_id, TTL'd) that the webhook receiver (§2.2)
    checks before publishing — NOT a webapp-side metadata PATCH. This is the one place the spike
    correction adds new brightbot-side state (a mute list), rather than removing state as it did
    for the opt-in itself. Callable from the Slack action handler
    (mirrors BH-887's routine-suggestion action-button pattern, see slack-routine-suggestion-scheduling.md).
```

## 3. Invariants (DbC)

1. A notification for `chat_run_complete`/`chat_run_interrupt` is only ever addressed
   `visibility: "user"` with `audienceUserIds: [notify_user_id]` — never `"workspace"` broadcast.
   This is a personal action on a personal session; no other workspace member should see it.
2. ~~WHEN the thread's stream is confirmed actively connected at trigger time, THE System SHALL NOT
   publish the notification at all~~ — **removed post-launch (2026-07-15)**. A presence-heartbeat
   gate was built and shipped exactly as originally scoped (suppressing the whole publish, not
   just Slack, per the note struck through above), but real usage showed it actively worked
   against the point of opting in: a user who opts in, sends a message, and simply keeps the tab
   open (the common case) would never get notified even though they explicitly asked to be. The
   opt-in itself (an explicit per-message action) is a stronger signal of intent than tab-open
   state is a signal of attention — so notification now fires unconditionally once opted in,
   regardless of whether the thread is being watched. `useChatNotifyPresence.ts`, the
   `/heartbeat` endpoint, and `_is_thread_being_watched()` were removed from brightbot and the
   webapp; there is no replacement mechanism.
3. WHEN elapsed time since `notify_armed_at` is below `DURATION_FLOOR_SECONDS`, THE System SHALL
   NOT fire a completion notification — this floor does NOT apply to interrupts (an interrupt is
   always actionable immediately, per user decision in this session's design discussion).
4. Each `(thread_id, run_id)` pair fires at most once per trigger type (complete vs interrupt) —
   an idempotent claim (mirroring `scheduleNotifiedAt`'s conditional-write pattern in
   `scheduler-bridge.ts:136-139`) prevents a retry or a duplicate trigger path from double-sending.
5. Turning the opt-in off (mute) takes effect for any *subsequent* trigger check — an in-flight
   notification already queued for delivery is not required to be recalled (best-effort, matching
   this codebase's existing "notification delivery is best-effort, never blocking" convention,
   e.g. `publishWorkflowScheduleNotification`'s try/catch-and-log).
6. The completion/interrupt message copy MUST be visually and textually distinct (different verb,
   different icon) so a user cannot mistake "I'm blocked waiting on you" for "I'm done."

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Notify me on this chat session

  Scenario: User opts in, closes tab, run finishes past the duration floor
    Given a user opts in to "Notify me" on an open BrightAgent thread
    And the run has been executing for more than 20 seconds
    And the user's stream is not currently connected
    When the run reaches a terminal success state
    Then publishNotification is called with stage="chat_run_complete", visibility="user",
      audienceUserIds=[the opted-in user]
    And the user receives a Slack DM and an in-app inbox card

  Scenario: User is actively watching when the run finishes (removed 2026-07-15)
    # No longer suppressed — opting in now always notifies past the duration floor,
    # regardless of tab/stream state. Kept here as a record of the original design;
    # see Invariant 2's strikethrough note in §3 for why it was removed.

  Scenario: Run finishes too quickly to matter
    Given a user opts in to "Notify me"
    And the run completes 10 seconds after opt-in
    When the run reaches a terminal state
    Then no notification is sent (below DURATION_FLOOR_SECONDS)

  Scenario: Agent pauses on an interrupt
    Given a user opts in to "Notify me" on an open BrightAgent thread
    When the run raises an interrupt requiring the user's input
    Then a notification is sent immediately regardless of elapsed duration
    And the message copy says the session needs the user's input, not that it's "finished"

  Scenario: Duplicate trigger does not double-notify
    Given a chat_run_complete notification has already been claimed and sent for run R
    When the same terminal-state trigger fires again for run R (retry/reconnect)
    Then no second notification is sent

  Scenario: User mutes from the delivered Slack message
    Given a user received a chat_run_complete Slack DM with a "Mute this session" action
    When they click "Mute this session"
    Then the thread's notify_on_complete is set to false
    And no further notifications fire for that thread until re-opted-in
```

## 5. Out of Scope

- Any change to `scheduler-bridge.ts` or the scheduled-workflow notification path — this spec adds
  a sibling trigger calling the same downstream mutation, not a shared code path.
- A new subscription scope, channel type, or delivery adapter — Slack DM + in-app inbox via the
  existing `visibility: "user"` mechanism is sufficient; no Teams/email/webhook work here.
- A durable, cross-session notification *preference* (the webapp's Preferences tab is still
  PREVIEW/mock, per BH-1088's audit) — this is a per-thread, ephemeral opt-in, not a saved setting.
- Notifying on intermediate progress within a run (e.g. "25% done") — only true terminal states and
  interrupts.
- Multi-user threads / shared sessions — `notify_user_id` assumes one requesting user per thread,
  matching today's `Author`/`user_id` single-value metadata shape.

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| LangGraph Platform per-run webhook | Blocking | **Resolved (BH-1100)** — confirmed present in `langgraph_api==0.8.7` (brightbot's installed version); fires for every terminal status and for `"interrupted"`; no polling needed. ~~Note (2026-07-15): the deployed managed runtime silently never dispatches a relative/loopback webhook URL, confirmed via direct staging test.~~ **Retracted (2026-07-16)**: that "confirmation" was a false positive. The real cause of every failed test that day was §2.2's payload-shape bug below — `chat_notify_webhook()` read `payload.get("run")` (always `None`; the real payload spreads `run_id`/`thread_id`/`metadata` at the top level) and therefore treated every arriving webhook as `not_opted_in`, indistinguishable from "never arrived" from outside. Once that bug was fixed, a webhook pointed straight at brightbot's own URL delivered correctly — proven with two independent real chat runs. The webapp's absolute-URL change (still in place, harmless) was not the fix and was not reverted, since it works fine and touching it again is pure risk for no benefit. |
| Presence-check / active-stream signal | ~~Blocking~~ | **Built (BH-1102), then removed (2026-07-15)** — see Invariant 2's strikethrough note in §3. Not a dependency anymore; nothing replaces it. |
| Per-thread mute suppression store (brightbot) | Blocking (new, small scope) | **Resolved (BH-1101)** — a TTL'd DynamoDB key-value table, no new database |
| `writeNotificationSignal` / `publishNotification` (`visibility: "user"` path) | Non-blocking (reused) | Ready — proven by BH-1088 + `scheduler-bridge.ts` |
| Thread/run metadata `user_id` field | Non-blocking (reused) | Ready — already threaded by `useAgentStream.ts` |
| brightbot-slack-server delivery pipeline (poller, `SlackChannel.deliver()`) | Non-blocking, but genuinely new work | **Resolved (2026-07-16)** — `deliver()` matches Subscription rows, not `visibility`/`audienceUserIds`; nothing auto-created a row for the two new stages. Fixed by auto-provisioning one on first opt-in (§2.2 step 5), not by changing `deliver()` itself. |

## 9. Observability Contract

- **Log events** (brightbot, new hook): `chat_notify.armed`,
  `chat_notify.skipped_duration_floor`, `chat_notify.claimed`, `chat_notify.publish_success`,
  `chat_notify.publish_error` — bracketed-tag style matching `[SchedulerBridge]`'s existing
  convention in `scheduler-bridge.ts`. (`chat_notify.skipped_watching` existed briefly for the
  presence gate; removed with it on 2026-07-15.)
- **Span**: none new required — this is a lightweight webhook/poll handler, not an LLM/tool node.
- **Metrics**: a count of `chat_notify.skipped_duration_floor` vs `chat_notify.publish_success` is
  the single most useful signal for tuning the duration floor — worth a dashboard once live, not a
  blocking requirement for v1.

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brightbot` | `tests/unit/http_routes/test_chat_session_notify_routes.py` | One test per §4 scenario touching the hook: duration floor, mute skip, interrupt-always-fires, idempotent claim (Property-equivalent to `scheduleNotifiedAt`'s dedup test if one exists for it). Presence-check tests existed here through BH-1102, removed with the mechanism on 2026-07-15. |
| `brighthive-platform-core` | `tests/unit/` | Regression-only — confirm `publishNotification` accepts the two new stage strings with `visibility: "user"` (no resolver change expected, since `stage` is already a free-text field) |
| `brighthive-webapp` | `tests/e2e` (Playwright) | One spec: opt-in toggle sets thread metadata; mute action from a rendered inbox card clears it |
| `brighthive-e2e` | `e2e/e2e/` | One end-to-end: real chat thread, real opt-in, simulate/wait for a real terminal run past the duration floor, assert Slack DM + inbox delivery against staging (mirrors BH-1000's scheduled-workflow chain test) |

**Real-behavior requirement**: the `brighthive-e2e` row must hit real staging services (LangGraph
run, platform-core mutation, brightbot-slack-server poller) — a construct-only test asserting the
webhook payload shape does not satisfy this.

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| BrightBot | `brightbot` | New `/manage/chat-sessions/webhook/run-complete` receiver (confirmed mechanism, BH-1100); new mute-suppression store; new `chat_run_complete`/`chat_run_interrupt` stage constants |
| Platform Core | `brighthive-platform-core` | No resolver change — `publishNotification`'s `stage` field already accepts arbitrary strings |
| Web App | `brighthive-webapp` | New opt-in toggle/offer in chat header (sets `webhook`/`metadata.notify_user_id` on the next `runs/stream` call, §2.1, as an absolute URL — see §6); new `BackendStage` entries + `STAGE_LABELS`; presence heartbeat (built BH-1102, removed 2026-07-15 — see §3 Invariant 2) |
| Slack Server | `brightbot-slack-server` | No new delivery code — existing poller/`SlackChannel.deliver()` handles the new stage automatically once published; only a new Block Kit "Mute this session" action button (mirrors BH-887's action-button pattern) calling brightbot's mute store |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| BH-1100 | spike: determine LangGraph Platform's run-completion signal (webhook vs poll) — resolves §6 blocking dependency before the rest can be estimated | 2 | BH-409 |
| BH-1101 | brightbot: chat-session webhook receiver + idempotent claim + duration floor + mute store | 5 | BH-409 |
| BH-1102 | webapp: presence heartbeat + opt-in toggle/offer setting webhook/notify_user_id on run creation | 5 | BH-409 |
| BH-1103 | webapp: `chat_run_complete`/`chat_run_interrupt` stage labels, mapper entries, inbox rendering | 2 | BH-409 |
| BH-1104 | brightbot-slack-server: Block Kit "Mute this session" action for the two new stages | 2 | BH-409 |
| BH-1105 | brighthive-e2e: end-to-end chat-session-notify delivery chain test against staging | 3 | BH-409 |

## Related

- **Parent epic**: BH-409 (BrightSignals)
- **Precedent**: `notifyScheduleOfRunCompletion()` / `publishWorkflowScheduleNotification()`
  (`scheduler-bridge.ts`) — the reviewed, production pattern this spec's hook mirrors for a chat
  run instead of a scheduled workflow run. No runtime dependency between the two.
- **BH-1088**: the notification-subscription model this spec's delivery path relies on entirely
  unchanged — `visibility: "user"` + `audienceUserIds` + personal-scope Slack DM resolution.
- **slack-routine-suggestion-scheduling.md**: the action-button pattern this spec's "Mute this
  session" Slack action should mirror (`STAGE_ACTIONS`, Bolt `app.action(...)` handler).
