---
title: "resetWorkspaceResources — purge a workspace to zero-state, zero orphans, keep the workspace"
epic: "BH-1245"
author: "Kuri"
status: "Draft"
created: "2026-08-03"
generates: "tickets"
tags: [platform-core, admin, cascade-delete, loop-capital, orphan-safety]
related:
  features: []
  pocs: []
  bedrock: []
---

# resetWorkspaceResources — purge a workspace to zero-state, zero orphans, keep the workspace

> Full contract: `~/.claude/rules/spec-driven.md`. §8 (LLM eval) is omitted — this is a deterministic
> GraphQL mutation with no LLM behavior. §7 and §9 apply (safety boundary + production surface).

## 1. Context

We need to hand Loop Capital a **clean, plug-and-play workspace** so the full before/after demo
reproduces deterministically for Frank. The workspace shell, members, and secrets must survive
(so the champion re-attaches into the *same* workspace and its BYOW warehouse connection); only
its *resources* — the catalog and everything the catalog touches across every store — get purged.
Today platform-core has **no workspace-level reset**: `deleteProject`/`deleteDataAsset` do plain
Neo4j-OGM `.delete` calls that **orphan** their children (metric snapshots, anomaly events,
quality rules), and the per-user `NotificationInbox` DynamoDB rows keyed by `workspaceId` are
**never** cleaned on any node delete — the exact "signal fired but inert" orphan class. Emptying a
workspace by hand-firing individual deletes leaves orphans in Neo4j, Redis, and DynamoDB.

```mermaid
stateDiagram-v2
    [*] --> Populated: workspace has assets, projects, signals
    Populated --> Refused: confirm != true
    Refused --> Populated: (no change; report describes what would purge)
    Populated --> Purging: confirm == true (@superAdminOnly)
    Purging --> ZeroState: all resources + children + inbox rows gone
    ZeroState --> [*]: WorkspaceNode + members + secrets INTACT
```

### Use Case / Goal

Success = one `@superAdminOnly` mutation that takes a `workspaceId`, and leaves the workspace with
**zero data assets, zero projects, zero orphaned child nodes, zero notification-inbox rows, zero
orphan Redis embeddings, zero chat/agent sessions, and no stale S3/Glue/OpenMetadata artifacts** —
while the `WorkspaceNode`, its members, roles, and secret store are untouched. A `DeletionReport`
records the outcome per store so partial failures are visible and the op is retryable. Beneficiary:
whoever re-zeroes a pilot or demo workspace (Loop Capital first; reusable for every trial).

**Two modes, one code path.** The same mutation serves a **global admin nuke** (omit `resources` →
every class purged) and an **independent per-element refresh** (name a subset → purge just that
class — e.g. delete only the chat sessions, or only the notification inbox, leaving everything else
intact). Each class is one entry in an ordered registry; a subset run preserves the fixed
external-first / Neo4j-node-last order and reaches the *same* per-class purge the nuke uses (one
impl, N entry points).

### How It Works Today

`brighthive-platform-core` is a GraphQL API over a Neo4j OGM plus AWS stores (S3, DynamoDB, Glue,
OpenMetadata, Redis). The privileged teardown building blocks already exist in
`src/graphql/models/admin-resource-deletion.ts` (`@superAdminOnly`): `deleteDataAssetAsAdmin`
reverses **S3 + DynamoDB + Glue + group-disconnect + node-delete + Redis embedding purge** for one
asset (delegating to `DataAssetModel.deleteDataAsset`), and there are sibling `*AsAdmin` deletes for
warehouse/ingestion/transformation services. `src/graphql/models/admin-cleanup.ts` has
`purgeOrphanEmbeddingsAsAdmin` (orphan Redis sweep) and a read-only `reconcileWorkspaceAsAdmin`
cross-store diff. `NotificationInbox` (`src/graphql/service/aws/notification-inbox.ts`) is a
DynamoDB table keyed `PK=USER#<uid>`, `SK=WS#<wsid>#<eventId>`, with `remove(user, ws, event)` — but
**no delete-by-workspace**.

### Hard Limitations

- **No workspace-wide reset / bulk purge exists** (grep-confirmed: no `reset*workspace`,
  `purge*workspace`, `wipe`, `clearWorkspace`, `deleteWorkspace`).
- `deleteProject` (`service/project.ts:296`) and the node-delete inside `deleteDataAsset` are plain
  OGM `.delete` with no nested cascade → **child nodes are orphaned** (metric snapshots, anomaly
  events, quality rules, groups, workflow specs/runs).
- Signals/notifications live **outside Neo4j** (DynamoDB inbox rows) → never touched by any node
  delete. Deleting all assets still leaves every prior signal in every member's inbox.

### Gaps

1. No single call to empty a workspace's catalog.
2. No `NotificationInbox` delete-by-workspace (must enumerate members × their inbox partition).
3. No DETACH-DELETE cascade for the child node types the per-resource deletes orphan.
4. No orchestration that runs the external-first teardown across **all** of a workspace's resources
   and then sweeps orphan Redis embeddings, in one auditable report.

## 2. Interface Contract (MDE)

New `@superAdminOnly` GraphQL mutation. Reuses the existing `DeletionReport` shape from
SPEC-SUPERADMIN-RESOURCE-DELETION (extended with counts so a caller can assert zero-state).

```graphql
# One independently-runnable purge class. Same set on the wire, in the model
# (ResourceClass), and in the ordered registry — omit for the global nuke, or
# name a subset for a single-element refresh (delete just sessions, just the
# inbox, etc.). Order is fixed by the registry, NOT by the order named here.
enum WorkspaceResourceClass {
  DATA_ASSETS         # catalog assets + their S3/Dynamo/Glue/Redis/node teardown
  SOURCES             # ingestion + warehouse services (Airbyte ws / OMD + secrets)
  PROJECTS            # project nodes + owned subgraphs
  SCHEMAS             # standalone/target schema contracts (INCLUDES edge)
  GLOSSARY            # workspace-scoped glossary terms
  CUSTOM_AGENTS       # workspace custom-agent templates
  DOCUMENTS           # project files / uploaded documents (ResourceNodes)
  POLICIES            # custom/monitored/asset policies (keeps GovernanceNode)
  SETTINGS            # workspace-scoped RuntimeConfig (feature flags, never "*")
  CONTEXT_WORKSPACE   # the workspace context node + its content
  CHILD_NODES         # metric snapshots, anomaly events, quality rules + executions
  NOTIFICATIONS       # notification-inbox rows across members
  SESSIONS            # chat/agent threads (LangGraph Cloud — see §2.1)
  ORPHAN_EMBEDDINGS   # Redis embedding keys with no live owning node
}

input ResetWorkspaceResourcesInput {
  workspaceId: ID!
  confirm: Boolean!            # must be true to purge; false/absent → dry-run report
  resources: [WorkspaceResourceClass!]   # omit/empty → global nuke; else purge only these
}

type ResetDeletionStep {
  system: String!              # NEO4J | SECRETS_MANAGER | OPENMETADATA | AIRBYTE | DYNAMODB | REDIS | S3 | GLUE | SESSIONS
  status: String!              # OK | FAILED | SKIPPED
  detail: String               # never contains secret values (I-8)
  count: Int                   # resources affected by this step (0 for dry-run)
}

type ResetDeletionReport {
  success: Boolean!
  dryRun: Boolean!             # true when confirm != true
  workspaceId: ID!
  assetsPurged: Int!
  sourcesPurged: Int!          # ingestion + warehouse services torn down
  projectsPurged: Int!
  schemasPurged: Int!
  glossaryTermsPurged: Int!
  customAgentsPurged: Int!
  documentsPurged: Int!
  policiesPurged: Int!
  settingsPurged: Int!
  contextWorkspacePurged: Int! # 0 or 1 (the workspace context node)
  inboxRowsPurged: Int!
  orphanEmbeddingsPurged: Int!
  sessionsPurged: Int!         # chat/agent threads deleted (LangGraph Cloud)
  steps: [ResetDeletionStep!]!
}

extend type Mutation {
  resetWorkspaceResources(input: ResetWorkspaceResourcesInput!): ResetDeletionReport! @superAdminOnly
}
```

**Model signature (TypeScript):**

```typescript
AdminWorkspaceResetModel.resetWorkspaceResources(
  _parent: unknown,
  { input }: { input: { workspaceId: string; confirm: boolean; resources?: ResourceClass[] | null } },
  context: Context,
): Promise<ResetDeletionReport>
```

### 2.1 Chat/agent sessions live as LangGraph Cloud threads — scoped on two dimensions

BrightAgent chat/agent sessions are **not** DynamoDB rows on staging/prod (the
`brightagent-sessions-stg` / `brightbot-threads-stg` tables are empty) — they are **LangGraph
Cloud threads** in the deployment's managed store, reached over the deployment's HTTP API
(`POST /threads/search`, `DELETE /threads/{id}`) using `LANGGRAPH_BASE_URL` + `LANGGRAPH_API_KEY`
(read read-only from Secrets Manager, never logged — I-8). A workspace owns threads in **two
shapes**, and neither alone catches every thread:

1. **Interactive chats** (`deep_agent` global / project / custom-agent) carry the workspace in
   `metadata.workspace_id`, stamped on create by brightbot's `auth_handler`.
2. **Background-task graphs** (`profiler_task`, `quality_check_task`, `detect_recurring_patterns`,
   `pipeline_watchdog_task`, …) carry it in `values.workspace_id` (graph state), because the system
   invokes them without the interactive-chat metadata stamping.

`/threads/search` filters server-side on **metadata only**; `values` can't be filtered server-side.
So the SESSIONS purge **full-scans and matches a thread when EITHER `metadata.workspace_id` OR
`values.workspace_id` equals the target** — a metadata-only filter silently misses every task
thread (verified against Loop Capital staging: metadata-only found 0 threads, two-dimension found 4).
The reusable CLI mirror is `brightbot/scripts/purge_workspace_threads.py`; the resolver reaches the
same threads via `WorkspaceThreads` (`service/aws/workspace-threads.ts`). Where the deployment isn't
wired for an environment, the SESSIONS step is recorded **SKIPPED** (not FAILED).

## 3. Invariants (DbC)

- **I-1** `WHEN resetWorkspaceResources succeeds, THE System SHALL NOT delete, detach, or modify the
  WorkspaceNode, its member edges, its roles, or its secret store.**
- **I-2** `WHEN resetWorkspaceResources succeeds, THE System SHALL leave workspace.dataAssets length
  == 0 AND workspace projects == 0.**
- **I-3** `WHEN a data asset is purged, THE System SHALL also delete its child nodes (MetricSnapshot,
  AnomalyEvent, QualityRule, and any CHILD_OF DataAsset) — no orphaned child node survives.**
- **I-4** `WHEN resetWorkspaceResources succeeds, THE System SHALL leave zero NotificationInbox rows
  for that workspaceId across all members' partitions.**
- **I-5** `WHEN nodes are deleted, THE System SHALL sweep orphan Redis embedding keys for that
  workspace so no embedding key points at a deleted node.**
- **I-6** `IF confirm is not exactly true, THEN THE System SHALL make NO destructive change and
  return dryRun=true with the counts it WOULD purge.**
- **I-7** `WHERE any external teardown step (S3/Dynamo/Glue/OMD/Redis) throws for a resource, THE
  System SHALL record it FAILED in the report and SHALL NOT delete that resource's Neo4j node`
  (external-first ordering; the op stays retryable, per the existing `*AsAdmin` contract).
- **I-8** `THE System SHALL NOT place any secret value in a report `detail` field or audit log.`
- **I-9** `THE caller SHALL be a SUPERADMIN` (enforced by the `@superAdminOnly` directive; the
  resolver assumes an authorized caller).
- **I-10** `THE System SHALL emit one structured audit record naming the actor, workspaceId, per-store
  step outcomes, and success` (mirrors `admin-resource-deletion.ts` `auditLog`).
- **I-11** `THE reset SHALL be scoped to exactly one workspaceId; no resource outside that workspace
  is read or deleted` (cross-tenant guard, mirrors I-10 of the per-resource deletes).
- **I-12** `IF resources is omitted or empty, THEN THE System SHALL purge every class (global nuke);
  ELSE THE System SHALL purge ONLY the named classes and SHALL NOT touch any un-named class`
  (single-element refresh). Either way THE System SHALL run the selected classes in the fixed
  registry order (external-first, Neo4j-node-last), not the order named in `resources`.
- **I-13** `WHEN the SESSIONS class runs, THE System SHALL delete every LangGraph thread the
  workspace owns on EITHER metadata.workspace_id OR values.workspace_id, and SHALL record the step
  SKIPPED (not FAILED) where no LangGraph deployment is configured for the environment.`
- **I-14** `WHERE one selected class throws, THE System SHALL record it FAILED and SHALL still run
  the remaining selected classes` (a failed class never aborts the others; fail-isolation).
- **I-15** `WHEN the SOURCES class runs, THE System SHALL tear down each ingestion service (Airbyte
  workspace cascade) and each warehouse service (OpenMetadata + secrets) external-first via the
  existing per-service `*AsAdmin` deletes, and a single service's failure SHALL be recorded FAILED
  without aborting the other services.`
- **I-16** `WHEN the POLICIES class runs, THE System SHALL delete only CustomPolicy / MonitoredPolicy
  / AssetPolicy nodes and SHALL NOT delete the GovernanceNode container` (the workspace keeps its
  governance anchor so it stays usable for handover; policy set returns to empty).
- **I-17** `WHEN the SETTINGS class runs, THE System SHALL delete only RuntimeConfig rows whose
  `scope` equals the workspaceId and SHALL NEVER touch the global `"*"` scope row` (cross-tenant /
  global-config guard).
- **I-18** `WHEN the CONTEXT_WORKSPACE class runs and the workspace has no context node, THE System
  SHALL record the step SKIPPED (count 0), not FAILED` (a missing context node is a no-op).

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: resetWorkspaceResources

  Scenario: Purge a populated workspace to zero-state
    Given a workspace with 11 data assets, 2 projects, quality rules, and notification-inbox rows
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true)
    Then workspace.dataAssets length is 0
    And the workspace has 0 projects
    And no MetricSnapshot/AnomalyEvent/QualityRule child nodes for those assets remain
    And 0 NotificationInbox rows exist for that workspaceId
    And 0 orphan Redis embedding keys remain for that workspace
    And the WorkspaceNode, its members, and its secret store still exist
    And the report success is true with assetsPurged=11 and projectsPurged=2

  Scenario: Dry-run when confirm is not true
    Given a workspace with resources
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: false)
    Then no resource is deleted
    And the report dryRun is true
    And the report reports the counts that WOULD be purged

  Scenario: Reject a non-superadmin caller
    Given an authenticated non-superadmin user
    When they call resetWorkspaceResources
    Then the call is rejected by the @superAdminOnly directive
    And no resource is deleted

  Scenario: External teardown failure leaves that node intact and retryable
    Given a workspace where one asset's S3 delete will throw
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true)
    Then that asset's step is recorded FAILED
    And that asset's Neo4j node is NOT deleted
    And the report success is false
    And re-running the mutation retries the failed resource

  Scenario: Cross-tenant isolation
    Given two workspaces A and B each with resources
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId: A, confirm: true)
    Then workspace B's resources, children, and inbox rows are unchanged

  Scenario: Single-element refresh — purge only chat/agent sessions
    Given a workspace with data assets, projects, inbox rows, and chat/agent threads
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true, resources: [SESSIONS])
    Then every LangGraph thread the workspace owns (interactive chats AND task graphs) is deleted
    And the report sessionsPurged equals the number of threads that existed
    And the data assets, projects, and inbox rows are all unchanged

  Scenario: Global nuke — omit resources
    Given a workspace with resources across every class
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true) with no resources
    Then every class is purged in the fixed registry order
    And the report success is true

  Scenario: Multi-class refresh — purge only glossary and documents
    Given a workspace with data assets, glossary terms, and uploaded documents
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true, resources: [GLOSSARY, DOCUMENTS])
    Then only the glossary terms and documents are deleted
    And the data assets, projects, and sources are unchanged
    And the report glossaryTermsPurged and documentsPurged reflect the counts deleted

  Scenario: Policies purge keeps the governance container
    Given a workspace with custom, monitored, and asset policies under its GovernanceNode
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true, resources: [POLICIES])
    Then every CustomPolicy/MonitoredPolicy/AssetPolicy node is deleted
    And the GovernanceNode container still exists
    And the report policiesPurged reflects the count deleted

  Scenario: Settings purge never touches the global config
    Given a workspace with a scoped RuntimeConfig row and a global "*" RuntimeConfig row
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true, resources: [SETTINGS])
    Then only the workspace-scoped RuntimeConfig row is deleted
    And the global "*" RuntimeConfig row is unchanged

  Scenario: One failing class does not abort the others
    Given a global reset where the NOTIFICATIONS step will throw
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true)
    Then the NOTIFICATIONS step is recorded FAILED
    And the SESSIONS and ORPHAN_EMBEDDINGS steps (later in the order) still run
    And the report success is false

  Scenario: Sessions skipped where LangGraph is not configured
    Given an environment with no LANGGRAPH_BASE_URL / LANGGRAPH_API_KEY
    When a SUPERADMIN calls resetWorkspaceResources(workspaceId, confirm: true, resources: [SESSIONS])
    Then the SESSIONS step is recorded SKIPPED, not FAILED
    And the report success is true
```

## 5. Out of Scope

- Deleting the `WorkspaceNode`, its members, roles, or **any** secret (Cognito, Secrets Manager,
  BYOW warehouse credentials). The workspace shell and its BYOW connection survive.
- Any secret mutation of any kind (hard rule: no secret read-modify-write without named confirmation).
- Cross-workspace / bulk multi-workspace reset — exactly one `workspaceId` per call.
- A webapp UI for the reset (this is an admin/ops mutation; UI is a later ticket if wanted).
- Restoring/undo — this is a one-way purge; there is no snapshot-restore in this spec.

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `AdminResourceDeletionModel.deleteDataAssetAsAdmin` (S3+Dynamo+Glue+Redis+node per asset) | Non-blocking (reuse) | Ready |
| `admin-cleanup.ts` `purgeOrphanEmbeddingsAsAdmin` (orphan Redis sweep) | Non-blocking (reuse) | Ready |
| `NotificationInbox` service — needs new `deleteByWorkspace(workspaceId, memberUserIds)` | Blocking | Done |
| Workspace member-enumeration service method (users with inbox for the workspace) | Blocking | Done (`Workspace.findAllMembersByWorkspaceId`) |
| `@superAdminOnly` directive | Non-blocking (reuse) | Ready |
| Per-workspace "list all assets/projects/services" service methods | Blocking | Done (`DataAsset.find` + `ProjectModel.fetchProjects`) |
| `WorkspaceThreads` service — LangGraph two-dimension thread scan + delete-by-workspace | Blocking | Done (`service/aws/workspace-threads.ts`) |
| `LANGGRAPH_BASE_URL` + `LANGGRAPH_API_KEY` in `staging/prod platform-core` secret bundle | Non-blocking (read-only) | Ready |

## 7. Correctness Properties

### Property 1: Zero-orphan guarantee

*For any* workspace purged with `confirm: true` that reports `success: true`, there exists no Neo4j
child node (MetricSnapshot, AnomalyEvent, QualityRule, CHILD_OF asset), no NotificationInbox row, and
no Redis embedding key that references a deleted node of that workspace.

**Validates: §3 Invariants I-3, I-4, I-5; §4 Scenario "Purge a populated workspace to zero-state"**

### Property 2: Workspace-shell preservation

*For any* successful reset, the `WorkspaceNode`, its member edges, and its secret store are
bit-for-bit unchanged — a purge is never a workspace delete.

**Validates: §3 Invariant I-1; §4 Scenario "Purge a populated workspace to zero-state"**

### Property 3: No destructive change without confirm

*For any* call where `confirm != true`, the store state before and after is identical.

**Validates: §3 Invariant I-6; §4 Scenario "Dry-run when confirm is not true"**

### Property 4: Retryable, orphan-free on partial failure

*For any* reset where an external step throws for resource R, R's Neo4j node survives, R is reported
FAILED, and a re-run retries R — no half-deleted resource is left with its node gone but externals
intact (or vice-versa) beyond what the external-first ordering guarantees.

**Validates: §3 Invariant I-7; §4 Scenario "External teardown failure leaves that node intact and retryable"**

### Property 5: Selector purges exactly the named classes, in registry order

*For any* call naming a subset `resources`, exactly the named classes are purged and every un-named
class is untouched; the selected classes always run in the fixed registry order (external-first,
Neo4j-node-last), never the order named in `resources`. An omitted/empty `resources` purges all.

**Validates: §3 Invariant I-12; §4 Scenarios "Single-element refresh" and "Global nuke"**

### Property 6: One core purge per class, reached by every entry point

*For any* resource class, there is exactly one purge implementation (its `RESET_STEPS` entry); the
global nuke and every single-element refresh reach it through the same registry — no entry point
re-implements a class's teardown. The reusable CLI (`purge_workspace_threads.py`) and the resolver's
`WorkspaceThreads` service share the identical two-dimension thread-scoping rule.

**Validates: §3 Invariants I-12, I-13; ADR-015 shared-core one-impl pattern**

## 9. Observability Contract

- **Audit log**: one `[SUPERADMIN_AUDIT]` structured record per call — `{ mutation:
  "resetWorkspaceResources", actorUserId, workspaceId, resources, success, dryRun, assetsPurged,
  projectsPurged, inboxRowsPurged, orphanEmbeddingsPurged, sessionsPurged, steps }` (mirrors
  `admin-resource-deletion.ts`; `resources` records the selected classes so a single-element
  refresh is distinguishable from a global nuke).
- **No secret values** in any `detail` (I-8).
- **Log events**: `reset_workspace.started` (carries `resources`), `reset_workspace.asset_purged`,
  `reset_workspace.inbox_flushed`, `reset_workspace.completed`, `reset_workspace.step_failed`.
- **Metrics**: none.

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brighthive-platform-core` | `brighthive-platform-core/tests/unit/admin-workspace-reset.test.ts` | **L0/registry (delivered, 10 cases):** dry-run returns `dryRun:true` + counts and calls no destructive collaborator (I-6); global nuke (omit `resources`) runs every class in safe order and populates every class count — assets/sources/schemas/glossary/agents/documents/context (I-12); single-element refresh (`resources:[SCHEMAS]` / `[SOURCES]` / `[SESSIONS]` / `[NOTIFICATIONS]`) purges only the named class, with SOURCES tearing down ingestion-then-warehouse (I-12, I-15); multi-class subset (`resources:[GLOSSARY, DOCUMENTS]`) purges exactly those two, leaving assets/agents untouched (I-12); CONTEXT_WORKSPACE recorded SKIPPED (count 0) when the workspace has no context node (I-18); one failing class is recorded FAILED without aborting later classes (I-14); SESSIONS SKIPPED when LangGraph unconfigured (I-13). **L2 (behavior, real-backend):** against a real (or LocalStack) Neo4j + DynamoDB — seed a workspace with assets + child nodes + inbox rows, run reset, assert I-2/I-3/I-4/I-5 hold and I-1 (workspace + secrets survive). One test for I-7 (inject an S3 throw → node survives, report FAILED). One for I-11 (two workspaces → B untouched). One for `@superAdminOnly` rejection (I-9). **Sessions real-behavior:** the `brightbot/scripts/purge_workspace_threads.py` two-dimension scan is verified against Loop Capital staging (metadata-only 0 → two-dimension 4 → purged → re-verify 0). |
| `brighthive-e2e` | `brighthive-e2e/e2e/` | One feature test: populate the LC-shaped workspace, call `resetWorkspaceResources`, then assert via the real GraphQL API that `workspace.dataAssets == 0` AND the notification query returns 0 items — end-to-end across Neo4j + DynamoDB on staging. |

**Real-behavior requirement** (`~/.claude/rules/test-behavior-real.md`): the L2 zero-state test MUST
hit a real Neo4j + DynamoDB (or LocalStack replay), not a mock — a mocked reset proves the wiring of
the test, not that orphans are actually gone. This is the exact bug class (orphaned inbox rows) the
spec exists to kill, so it must be verified against a real store.

Before opening the implementation PR: seed → reset → assert zero-state on a real backend, and run
the full platform-core suite green.

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Platform Core | `brighthive-platform-core` | New `@superAdminOnly resetWorkspaceResources` mutation: `WorkspaceResourceClass` enum + `resources` selector, typedef + resolver + `AdminWorkspaceResetModel` (ordered `RESET_STEPS` registry) + `NotificationInbox.deleteByWorkspace` + child-node DETACH DELETE cascade + orphan Redis sweep + `WorkspaceThreads` LangGraph two-dimension thread purge. |
| BrightBot | `brightbot` | Reusable CLI `scripts/purge_workspace_threads.py` (dry-run-first LangGraph thread purge; the sessions-class mirror). |
| Cross-repo e2e | `brighthive-e2e` | One feature test asserting zero-state across Neo4j + DynamoDB. |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| BH-1352 | resetWorkspaceResources mutation + `resources` selector (global nuke + per-element refresh) + model registry + inbox delete-by-workspace + child-node cascade + orphan Redis sweep + LangGraph session purge + tests | 5 | BH-1245 |

## Related

- **Recon**: platform-core cascade/delete/admin-auth ground truth (2026-08-03) — no existing
  workspace reset; per-resource deletes orphan children; inbox rows never cleaned on node delete.
- Reuses SPEC-SUPERADMIN-RESOURCE-DELETION building blocks (`admin-resource-deletion.ts`).
