---
title: "Warehouse Connectivity — default monitoring, real alerts, on-demand check"
epic: "BH-1036"
author: "drchinca"
status: Partial
created: "2026-08-05"
generates: "tickets"
tags: [warehouse, health, monitoring, alerts, slack, notifications, scheduling]
related:
  features: []
  pocs: []
  specs: ["warehouse-health-snapshot.md", "sqlserver-health-watch.md", "hive-health-landing-indicator.md"]
roadmap: mixed — folded into THEME-warehouse-health-truth.md — useful alerts
---

# Warehouse Connectivity — default monitoring, real alerts, on-demand check

> Full contract: `~/.claude/rules/spec-driven.md`. Direct follow-on to BH-1363
> (`drchinca/BH-1363/watchdog-connection-failure-health-status`, unmerged) —
> that fix makes a hard connection failure correctly produce a "Down"
> workspace-health snapshot instead of a stale "Healthy" one, verified live
> against real staging Neo4j. This spec covers the three gaps found while
> auditing what surrounds that fix: the snapshot can flip to "Down" and still
> (a) nobody gets told anything useful, (b) nobody can check right now instead
> of waiting for the next scheduled tick, and (c) most warehouses have no
> scheduled tick to begin with.

## 1. Context

[`warehouse-health-snapshot.md`](./warehouse-health-snapshot.md) (BH-1255, shipped) built the mechanism that
turns a watchdog signal into a workspace-level `Down`/`Degraded`/`Healthy`
snapshot. BH-1363 (unmerged) is the first bug fix riding on top of it — it
makes a genuine network/firewall failure actually produce that signal instead
of silently producing nothing. Both are real and both were just verified.

But auditing the full path from "connection breaks" to "someone who can fix
it finds out, or checks it themselves" found three gaps neither of those specs
covers — confirmed by direct code read, not inferred:

1. **No real alert copy.** When `source_connection_unreachable` (or any of the
   BH-1110-era stages before it) publishes, it reaches Slack and the in-app
   inbox, but both fall through to a generic `:bell:` card — `source_
   connection_unreachable` is absent from `NotificationStage` (`brightbot-
   slack-server/src/notifications/types.ts:2-69`), `classify.ts`'s switch
   (`:157-190`, falls to `classifyGeneric`), `formatter.ts`'s detail-render
   switch (`:144-190`, falls to `default: return []`), `signal-catalog.json`,
   and the webapp inbox's `sources[]` registry (`brighthive-platform-core/
   src/graphql/models/notifications.ts:414-427`, falls to
   `formatGenericDisplay`). Exactly the BH-1110 gap pattern (SSIS/Snowflake/
   Databricks stages had the identical hole before that ticket closed it),
   now repeating for the new stage.
2. **No on-demand check.** `connection_health_tool.py`'s `warehouse_
   connection_health` MCP tool (BH-1341, already built, already working — the
   same tool this session used indirectly to verify BH-1363) has zero UI
   callers anywhere in `brighthive-webapp`. The one "Test Connection" button
   that exists, `AddTransformation.tsx:527-552`, is a literal placeholder —
   its `onClick` shows `toast.info("Test connection will be available after
   backend integration.")` (`:537`) and calls nothing. There is no way for a
   user to check right now; every health signal comes only from the scheduled
   watchdog tick.
3. **No default monitoring.** The `pipeline_watchdog_task` schedule is
   opt-in-only, created by a direct `POST /manage/scheduled-agents` call
   (`brightbot/routes/scheduled_action_catalog.py:26`). No code path anywhere
   — checked workspace-creation, warehouse-creation, and the scheduled-agents
   routes — auto-creates this schedule when a warehouse connection is first
   configured. Worse: `pipeline_watchdog_task` isn't even **selectable** in
   the webapp's own schedule UI — `AddScheduleDialog.tsx`'s `TASKS` array
   (`:56-80`) lists only `quality_check_task`, `profiler_task`,
   `execute_workflow`. This is almost certainly *why* Loop Capital's SQLTest
   connection had no watchdog catching its outage in the first place — the
   monitoring this whole chain depends on was never turned on for that
   workspace, because there was no way to turn it on from the product.

```mermaid
flowchart LR
  subgraph today["today — 3 gaps"]
    A["warehouse connection created"] -.->|"no auto-schedule"| B["pipeline_watchdog_task<br/>NEVER RUNS"]
    C["user suspects a problem"] -.->|"no button exists"| D["check_now<br/>IMPOSSIBLE"]
    E["signal DOES fire<br/>(BH-1363 fixed)"] --> F["publishNotification"] -.->|"no renderer"| G["generic :bell: card<br/>no useful copy"]
  end
  subgraph target["target"]
    A2["warehouse connection created"] --> B2["default pipeline_watchdog_task<br/>schedule auto-created"]
    C2["user suspects a problem"] --> D2["Check Connection Now button<br/>-> warehouse_connection_health"]
    E2["signal fires"] --> F2["publishNotification"] --> G2["real Slack + inbox card:<br/>'Loop Capital SQL Server unreachable —<br/>check firewall/IP allowlist'"]
  end
```

### Use Case / Goal

A workspace admin connects a warehouse and, without configuring anything
extra, that connection is being watched. If it goes down, they (and everyone
in the workspace) get a real, specific alert — not a generic bell — in both
Slack and the in-app inbox. If they suspect a problem right now, they click
one button and get an immediate answer instead of waiting for the next
scheduled tick.

### Hard Limitations

- The watchdog's per-workspace schedule granularity is per-workspace, not
  per-connection (confirmed: `POST /manage/scheduled-agents` payload only
  requires `workspace_id`, `scheduled_action_catalog.py:47-48`) — a workspace
  with 2 warehouses gets one schedule covering both via `_poll_all_adapters`'s
  loop over `PIPELINE_SOURCE_ADAPTERS`, not two independent schedules. This
  spec does not change that granularity.
- `connection_health_tool.py`'s probe is a single trivial `SELECT 1` — it
  proves reachability, not the richer disk/job signals the scheduled watchdog
  produces. The on-demand button in this spec surfaces reachability only; a
  "run the full watchdog poll now" capability is a different, larger tool and
  is out of scope.

### Gaps

- No `NotificationStage`/`classify.ts`/`formatter.ts`/`signal-catalog.json`
  entries in `brightbot-slack-server` for `source_connection_unreachable`.
- No `sources[]` entry in platform-core's `notifications.ts` for the same
  stage — inbox card is generic.
- No GraphQL mutation or webapp UI wired to `warehouse_connection_health`.
- No auto-schedule-creation on warehouse connection create.
- No `pipeline_watchdog_task` entry in `AddScheduleDialog.tsx`'s `TASKS`.

## 2. Interface Contract (MDE)

### 2a. Slack renderer — new stage, following the BH-1110 pattern exactly

```typescript
// brightbot-slack-server/src/notifications/types.ts — NotificationStage union + NOTIFICATION_STAGES array
| 'source_connection_unreachable'

// classify.ts — severity/tier/emoji/headline (mirrors ssis_package_unreachable's tier)
case "source_connection_unreachable":
  return { severity: "critical", tier: "critical", emoji: ":x:", headline: "Warehouse connection unreachable" };

// formatter.ts — detail render (mirrors renderSsisSharedShapeDetails' metadata-driven pattern)
case "source_connection_unreachable": return renderConnectionUnreachableDetails(event);

function renderConnectionUnreachableDetails(event: NotificationEvent): string[] {
  const meta = event.metadata;
  const connectionKey = metaStringEscaped(meta, "connection_key");
  return [
    connectionKey
      ? `*Connection:* \`${connectionKey}\` — could not connect. Check network reachability (firewall/IP allowlist), credentials, and that the server is running.`
      : "Could not connect to this warehouse. Check network reachability (firewall/IP allowlist), credentials, and that the server is running.",
  ];
}
```

```json
// signal-catalog.json — new entry
{
  "stage": "source_connection_unreachable",
  "label": "Warehouse connection unreachable",
  "category": "pipeline",
  "hasLiveProducer": true,
  "severityRule": { "kind": "static", "severity": "critical" }
}
```

### 2b. Webapp inbox renderer — new `sources[]` entry

```typescript
// brighthive-platform-core/src/graphql/models/notifications.ts — mirrors formatSourceDiskLowDisplay
function formatConnectionUnreachableDisplay(signal: RawSignal): NotificationDisplay {
  const m = signal.metadata ?? {};
  const connectionKey = (m.connection_key as string) ?? "warehouse connection";
  return {
    type: "source_connection_unreachable",
    title: `Warehouse connection unreachable — ${connectionKey}`,
    subtitle: "Check firewall/IP allowlist and credentials",
    url: null,
    assetName: connectionKey,
  };
}
// registered in sources[] alongside source_disk_low, etl_job_failure, etc.
```

### 2c. On-demand check — new mutation wrapping the existing MCP tool

```graphql
# brightbot MCP surface already has warehouse_connection_health (BH-1341).
# NEW: a thin GraphQL passthrough so webapp can call it without an MCP client,
# mirroring how other brightbot capabilities are exposed to webapp today.
mutation checkWarehouseConnectionNow(warehouseServiceId: ID!): WarehouseConnectionCheckResult!
  Response 200: { healthy: Boolean!, warehouseType: String, server: String, database: String, detail: String, checkedAt: String! }
  Response 4xx: { error: "warehouse_not_found" | "forbidden_not_workspace_member" }
```

```tsx
// brighthive-webapp — new "Check Connection Now" button, one per warehouse row
// in Settings > Warehouses (mirrors MCPConnectivityCard.tsx's live-check pattern:
// loading spinner while in flight, CheckCircleOutlineIcon/ErrorOutlineIcon on result)
<CheckConnectionButton warehouseServiceId={wh.id} />
```

### 2d. Default scheduling — auto-create on warehouse connection creation

```typescript
// brighthive-platform-core — createWarehouseService / upsertWarehouseConfig
// resolver (src/graphql/models/warehouse-service.ts), on FIRST successful
// connection creation for a workspace: call brightbot's
// POST /manage/scheduled-agents with action_type="pipeline_watchdog_task"
// and a sensible default cadence (e.g. every 15 minutes), service-key authed,
// same pattern as other brightbot->platform-core / platform-core->brightbot
# machine calls in this codebase.
```

```tsx
// brighthive-webapp/src/Schedules/components/AddScheduleDialog.tsx — TASKS array
{
  value: "pipeline_watchdog_task",
  label: "Warehouse Connectivity Watchdog",
  requiresAssets: false,
  requiresProject: false,
}
```

## 3. Invariants (DbC)

1. WHEN a workspace's first warehouse connection is successfully created,
   THE System SHALL create a default `pipeline_watchdog_task` schedule for
   that workspace if one does not already exist — never duplicate an
   existing schedule.
2. THE System SHALL NOT auto-create a second `pipeline_watchdog_task`
   schedule for a workspace that already has one (idempotent on
   workspace_id, mirrors the existing per-workspace, not per-connection,
   granularity in §1 Hard Limitations).
3. WHEN `checkWarehouseConnectionNow` runs, THE System SHALL NOT block on or
   interfere with the scheduled watchdog's own poll cycle — the on-demand
   check and the scheduled poll are independent, concurrent-safe callers of
   the same underlying connection-open logic.
4. THE System SHALL require the caller to be an authenticated member of the
   warehouse's workspace for `checkWarehouseConnectionNow` — never a
   service-key-only call (this is a user-triggered action, unlike
   `recordWarehouseHealth`).
5. WHEN `source_connection_unreachable` (or any currently-generic-rendered
   stage) publishes, THE System SHALL render a stage-specific Slack card and
   a stage-specific inbox card — a generic `:bell:`/`formatGenericDisplay`
   render for an already-registered stage is a regression, not acceptable
   degraded behavior.
6. THE on-demand check SHALL NOT write to `WarehouseServiceNode.
   healthOperationalStatus` — it is a read-only, user-facing probe, distinct
   from the scheduled watchdog's workspace-level snapshot (Invariant 3
   applies: the two paths stay independent, so a user's manual check never
   masks or overwrites the workspace-level truth other teammates see).

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Default warehouse connectivity monitoring

  Scenario: First warehouse connection gets a default schedule
    Given a workspace with no warehouse connections and no watchdog schedule
    When the first warehouse connection is successfully created
    Then a pipeline_watchdog_task schedule exists for that workspace

  Scenario: Second warehouse connection does not duplicate the schedule
    Given a workspace with one warehouse connection and an existing watchdog schedule
    When a second warehouse connection is created
    Then exactly one pipeline_watchdog_task schedule still exists for that workspace

Feature: On-demand connection check

  Scenario: User checks a healthy connection right now
    Given a warehouse connection that is currently reachable
    When the user clicks "Check Connection Now"
    Then the button shows healthy=true within a few seconds
    And no workspace-level health snapshot is modified

  Scenario: User checks an unreachable connection right now
    Given a warehouse connection that is currently unreachable
    When the user clicks "Check Connection Now"
    Then the button shows healthy=false with a diagnosis
    And no workspace-level health snapshot is modified

Feature: Real alert copy for connection-unreachable

  Scenario: Slack card is stage-specific, not generic
    Given a source_connection_unreachable signal publishes
    When the Slack notification renders
    Then the card headline is "Warehouse connection unreachable"
    And the detail line names the connection, not a generic bell message

  Scenario: In-app inbox card is stage-specific, not generic
    Given a source_connection_unreachable signal publishes
    When the NotificationInbox resolves the signal
    Then the display title names the specific warehouse connection
    And the display does not fall through to formatGenericDisplay
```

## 5. Out of Scope

- **dbt/Transformation health staleness** and the hardcoded-always-`Healthy`
  "Platform Core API" row (`analytics-resolver.ts:198-205`) — confirmed via
  direct audit to be a different, unaddressed mechanism entirely
  (`TransformationServiceNode.status` has no poll/snapshot path at all, unlike
  the warehouse fold this spec and BH-1363 build on). Tracked separately, not
  bundled here to keep this spec's blast radius to warehouse connectivity.
- **Per-connection schedule granularity** — the default schedule this spec
  creates is per-workspace, matching the watchdog's existing loop-over-every-
  adapter design (§1 Hard Limitations). Splitting to per-connection schedules
  is a separate, larger change.
- **Running the full disk/job watchdog poll on demand** — the on-demand
  button in §2c is a reachability probe only (`SELECT 1`), not a trigger for
  the richer scheduled poll.
- **Configurable default cadence per workspace** — the auto-created schedule
  uses one sensible default interval; a UI to tune that interval per
  workspace is a follow-on, not required for this spec's Gherkin scenarios.
- **Renderer coverage for other still-generic stages** beyond `source_
  connection_unreachable` — this spec closes the gap for the one stage BH-1363
  introduces; a full audit/fix of every other under-rendered stage is
  tracked as its own cleanup, not bundled here.

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| BH-1363 (watchdog connection-failure fix) | Blocking | Unmerged, verified locally — `source_connection_unreachable` must exist as a real signal before its renderer/schedule work makes sense |
| `warehouse-health-snapshot.md` mechanism (BH-1255) | Blocking | Shipped |
| `connection_health_tool.py` / `warehouse_connection_health` MCP tool (BH-1341) | Blocking | Shipped, already verified working — this spec only adds a GraphQL passthrough + UI, no new probe logic |
| `POST /manage/scheduled-agents` scheduling API | Blocking | Shipped — this spec adds an auto-caller, not new scheduling infra |
| BH-1110 Slack/inbox renderer pattern (precedent) | Non-blocking | Shipped — this spec's §2a/§2b are additive entries following that exact pattern |

## 7. Correctness Properties

### Property 1: Default schedule is idempotent per workspace

*For any* workspace, at most one `pipeline_watchdog_task` schedule exists
regardless of how many warehouse connections are created over time.

**Validates: §3 Invariants 1-2, §4 Scenarios "First warehouse connection gets a default schedule", "Second warehouse connection does not duplicate the schedule"**

### Property 2: On-demand check never mutates workspace-level truth

*For any* call to `checkWarehouseConnectionNow`, `WarehouseServiceNode.
healthOperationalStatus`/`healthPolledAt`/`healthDiskFreePct`/
`healthFailedJobCount` are unchanged before and after the call.

**Validates: §3 Invariants 3, 6, §4 Scenarios "User checks a healthy/unreachable connection right now"**

### Property 3: No registered stage renders generically

*For any* `NotificationEvent` whose `stage` has a `NOTIFICATION_STAGES` /
`sources[]` registration, the rendered card is never the generic fallback
(`classifyGeneric` / `formatGenericDisplay`).

**Validates: §3 Invariant 5, §4 Scenarios "Slack card is stage-specific, not generic", "In-app inbox card is stage-specific, not generic"**

## 8. Eval Criteria

N/A — no LLM in the schedule-creation, on-demand-check, or renderer path.
All three are deterministic: a create-if-absent schedule call, a pass-through
liveness probe, and a stage-keyed lookup into a static renderer registry.
§3 invariants + §4 scenarios fully cover correctness.

## 9. Observability Contract

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=check_warehouse_connection_now` for the on-demand check (reuses `connection_health_tool.py`'s existing span shape).
- **Attributes**: `workspace.id`, `warehouse.id`, `check.healthy`, `check.triggered_by` (`"scheduled"` | `"on_demand"` — lets §7 Property 2's independence claim be verified from real trace data, not just code review).
- **Log events**: `warehouse_schedule.auto_created`, `warehouse_schedule.already_exists` (Invariant 1-2), `connection_check.on_demand_healthy`, `connection_check.on_demand_unhealthy`, `notification.stage_specific_rendered`, `notification.generic_fallback_used` (the last one is the regression detector for Invariant 5 — if this fires for `source_connection_unreachable` after this ships, the renderer wiring broke).
- **Metrics**: `notification_generic_fallback_total` (counter, tagged `stage`) — surfaces any stage that should have a real renderer but doesn't, catching future BH-1110-class gaps before they're discovered by an incident.

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brightbot-slack-server` | existing `classify`/`formatter` test files | One test per §2a entry: `classify("source_connection_unreachable")` returns the critical tier; `formatter` renders the connection-key detail line, never `default: return []` |
| `brighthive-platform-core` | `notifications.ts` test suite | One test: `resolveSignal` for `source_connection_unreachable` returns `formatConnectionUnreachableDisplay`'s output, never `formatGenericDisplay`. One test: warehouse-connection-creation resolver auto-creates exactly one schedule per workspace across 2 sequential connection creates (Property 1) |
| `brightbot` | `tests/unit/agents/governance_agent/` | Reuse/extend BH-1363's real-behavior harness pattern: `checkWarehouseConnectionNow`'s underlying probe against a real unreachable host returns `healthy=false` with a diagnosis, and does NOT call `recordWarehouseHealth` (Property 2) |
| `brighthive-webapp` | `Schedules`/`WorkspaceSettings` test files | `AddScheduleDialog` renders `pipeline_watchdog_task` as a selectable option. `CheckConnectionButton` shows the correct icon/state for healthy vs unhealthy results from a real captured `checkWarehouseConnectionNow` response shape |
| `brighthive-e2e` | `e2e/` | One feature test: create a warehouse connection end-to-end, confirm a watchdog schedule now exists via the scheduling API. One feature test: trigger `checkWarehouseConnectionNow` against a real unreachable sandbox host, confirm the UI shows unhealthy and no workspace snapshot changed |

**Real-behavior requirement**: the brightbot on-demand-check test MUST run
against a real unreachable host (per BH-1363's verified pattern — `192.0.2.1`,
RFC 5737 TEST-NET-1), not a mocked driver — a mock cannot prove the probe
correctly distinguishes "reachable" from "unreachable" the way this session's
own local verification did for the underlying watchdog fix.

Before opening the implementation PR: run every suite above, confirm each new
§2/§3/§4 entry has a corresponding new test case, and confirm all suites are
green.

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Slack Server | `brightbot-slack-server` | New `source_connection_unreachable` entries in `types.ts`/`classify.ts`/`formatter.ts`/`signal-catalog.json` |
| Platform Core | `brighthive-platform-core` | New `sources[]` renderer entry; new `checkWarehouseConnectionNow` mutation; auto-schedule-creation call on warehouse connection create |
| BrightBot | `brightbot` | Expose `warehouse_connection_health`'s probe to the new GraphQL passthrough (no change to the probe itself — BH-1341 already built it) |
| Web App | `brighthive-webapp` | New `pipeline_watchdog_task` entry in `AddScheduleDialog.tsx`; new "Check Connection Now" button in Settings > Warehouses |

## Ticket Breakdown

Generated via `/create-jira-ticket` from this spec. Every row is an
`issueType: "Task"` under the epic in frontmatter — never `"Story"`.

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | `brightbot-slack-server`: add `source_connection_unreachable` stage — types/classify/formatter/signal-catalog | 2 | BH-1036 |
| — | `platform-core`: add `sources[]` inbox renderer entry for `source_connection_unreachable` | 1 | BH-1036 |
| — | `platform-core`: `checkWarehouseConnectionNow` mutation (workspace-member-authed passthrough to BH-1341's probe) | 3 | BH-1036 |
| — | `platform-core`: auto-create default `pipeline_watchdog_task` schedule on first warehouse connection creation (idempotent) | 3 | BH-1036 |
| — | `webapp`: "Check Connection Now" button in Settings > Warehouses (mirrors `MCPConnectivityCard.tsx` pattern) | 3 | BH-1036 |
| — | `webapp`: add `pipeline_watchdog_task` to `AddScheduleDialog.tsx`'s `TASKS` | 1 | BH-1036 |
| — | `e2e`: warehouse-create auto-schedule + on-demand-check-against-real-unreachable-host feature tests | 2 | BH-1036 |

**Total: 15 points across 7 tickets**

## Related

- **Spec**: `warehouse-health-snapshot.md` (BH-1255) — the snapshot mechanism this spec's alerts/schedule surround
- **Spec**: `sqlserver-health-watch.md` (BH-1255) — the first signal producer
- **Fix (unmerged)**: BH-1363, `drchinca/BH-1363/watchdog-connection-failure-health-status` — the connection-failure signal this spec's renderer work is for
- **Precedent**: BH-1110 (SSIS/Snowflake/Databricks renderer gap closure) — the exact pattern §2a/§2b follow
- **Precedent**: `MCPConnectivityCard.tsx` — the live-check UI pattern §2c's button follows
- **Feature doc**: `docs/features/warehouse-connectivity-monitoring-alerts.md` (create after shipping)
