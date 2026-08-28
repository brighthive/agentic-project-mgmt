---
title: "Access decisions v1 — one decision point + an editable permission matrix"
epic: "BH-1464"
author: "drchinca"
status: Partial
created: "2026-08-27"
last-reviewed: "2026-08-28"
roadmap: mixed — v1 in active implementation (BH-1465..1471); BH-1466 in code review (platform-core#1234/#1236), BH-1465 in progress
generates: "tickets"
tags: [authorization, rbac, security, tenant-isolation, permission-matrix, platform-core, webapp, brightbot, neo4j]
related:
  specs:
    - "THEME-governance-enforced.md"                     # BH-172 — the governance-gate convergence this v1 builds the foundation for (a LATER increment, §12)
    - "project-governance-observability-convergence.md"  # BH-1255 — GOVERNED_BY edge the governance increment will consume (§12)
  features: []
  pocs: []
---

# Access decisions v1 — one decision point + an editable permission matrix

> **This is the first shippable increment, not the whole program.** Epic BH-1464 is the program
> (configurable roles → per-resource grants → governance convergence). This spec is the
> **foundation** every later increment needs: one `authorize()` that unifies the two enforcement
> paths shipped today, backed by a **permission matrix you can edit at runtime**, rolled out behind
> shadow mode. Per-subject grants, custom-role authoring, governance-gate enforcement, and session
> sharing are **named follow-on increments (§12)** — deliberately out of v1.

## 1. Context

BrightHive ships a Neo4j-authoritative 3-tier model (`AUTH_TIERS_AND_RBAC.md`) that is coarse,
frozen, and split across two paths that never consult each other — so a workspace can't reconfigure
who-can-do-what without a deploy, and 49 mutations enforce nothing. v1 gives the platform a single
answer to *"can this subject do this verb on this resource?"* and makes that answer's inputs
editable at runtime, without changing any outcome until each verb is proven safe in shadow.

### Use Case / Goal

A workspace admin flips **"Viewers may READ data assets"** off in the UI and it takes effect on the
next request — **no deploy**. A pipeline `RUN` is allowed for Collaborators and blocked for
Viewers by the same matrix. Every gated GraphQL field and every mutating agent tool asks **one**
`authorize()`, which **fails closed**.

### How It Works Today (verified, real `file:line`)

- Two paths, never joined: `@authorized` checks role **rank** (`platform-core/src/graphql/directives/authorized.ts:212-331`);
  a manual path checks `WorkspacePolicyNode` **boolean flags** (`.../service/auth.ts:465-604`). The
  directive holds zero references to the flags.
- Roles + flags are **frozen**: flags are boolean literals written **once at workspace creation**
  (`.../service/workspace.ts:131-277`); no mutation edits them.
- **49 of 173 mutations** carry no directive (e.g. `syncDataAssets` — no directive at
  `src/graphql/schema/typedefs.ts:4878`); each leans on a hand check that can vanish.
- Agents are role-blind (`brightbot/mcp/permissions.py`), and the LangGraph run path trusts a
  client-supplied `session_info.workspace_id` (`super_agent/middleware/initialization_middleware.py:195`
  → cross-tenant warehouse read).

### The v1 decision order (BLOCK wins, fails closed)

```mermaid
flowchart TD
  IN["authorize(subject, verb, resource, ctx)"] --> T{subject.workspace ==<br/>resource.workspace?}
  T -- no --> B1["BLOCK · cross_tenant"]
  T -- yes --> A{SystemAdmin/SuperAdmin<br/>AND member of workspace?}
  A -- yes --> AL["ALLOW"]
  A -- no --> M{(verb, resourceKind) in<br/>subject-role's matrix cells?}
  M -- yes --> AL
  M -- no --> B2["BLOCK · not_permitted"]
  IN -. timeout / internal error .-> BE["BLOCK · fail_closed"]
```

No grant layer, no governance-gate layer in v1 — those are §12. v1 resolves a decision from
**tenant → admin tier → the matrix**, and nothing else.

### Hard Limitations & Gaps this v1 closes

Closes: the split (one path), the freeze (editable matrix), the ungated 49 (default-deny), and
role-blind agents + the run-path leak. Does **not** close (see §12): per-user/group sharing,
custom-role authoring, declared-governance enforcement, session sharing.

## 2. Interface Contract (MDE)

### 2.0 The decision function (platform-core, TypeScript) — one authority, no premature registry

```typescript
type Effect = "ALLOW" | "BLOCK";                                  // WARN arrives with governance gates (§12)
type DecidedBy = "tenant" | "admin_tier" | "matrix" | "fail_closed";
interface Decision { effect: Effect; reason: string; decidedBy: DecidedBy; }
interface Subject { userId: string; workspaceId: string; }         // token.sub → UserNode (Neo4j-authoritative, INV-4)
interface ResourceRef { kind: ResourceKind; id: string; workspaceId: string; }

// One typed, DI-injectable function — deps injected, not imported (testable without patch()).
// No adapter registry until a second engine (Cedar/OpenFGA) is an actual ticket — # TODO(port).
async function authorize(
  args: { subject: Subject; verb: Verb; resource: ResourceRef; ctx: RequestContext },
  deps: { roles: RoleReader; matrix: MatrixCache; clock: Clock },
): Promise<Decision>;
```

### 2.1 Closed vocabulary (v1 trim — engine-agnostic, no vendor string)

```graphql
enum Verb { READ  CREATE  UPDATE  DELETE  RUN }        # RUN = trigger a transformation/pipeline/workflow
                                                       # SHARE / MANAGE_* / INVOKE_AGENT arrive with their features (§12)
enum ResourceKind { WORKSPACE  PROJECT  DATA_ASSET  DATA_PRODUCT  TRANSFORMATION  PIPELINE  WORKFLOW  AGENT  WAREHOUSE }
enum WorkspaceRoleName { WORKSPACE_ADMIN  WORKSPACE_COLLABORATOR  WORKSPACE_CONTRIBUTOR  WORKSPACE_VIEWER  WORKSPACE_AGENT_GUEST }
```

**Implementation note (BH-1466):** platform-core already has this exact enum, values-for-values, as
`AuthWorkspaceRole` (`src/graphql/directives/authorized.ts:63-68`). v1 reuses it rather than
introducing a duplicate `WorkspaceRoleName` type — same shape, no vendor/type drift, one fewer
enum to keep in sync. This spec keeps the name `WorkspaceRoleName` for readability; treat it as an
alias for `AuthWorkspaceRole` in code.

### 2.2 The permission matrix — the thing `authorize()` reads (this is the core, requirement #1/#8)

A workspace's matrix is, per role, the set of `(verb, resourceKind)` cells that role may perform.
**The matrix is the sole runtime authority.** Role rank (`ADMIN>…>VIEWER`) is used only to *seed*
defaults and for the admin-tier short-circuit — never as a runtime comparison (INV-6). A cell is
either allowed or not; that dissolves "where does a custom role sit in the rank order" — it doesn't,
it's a cell-set.

```graphql
type PermissionCell { verb: Verb!  resourceKind: ResourceKind!  allowed: Boolean! }
type RolePermissions { role: WorkspaceRoleName!  cells: [PermissionCell!]! }
type PermissionMatrix { workspaceId: String!  roles: [RolePermissions!]! }
type ResolvedPermission { verb: Verb!  resourceKind: ResourceKind!  allowed: Boolean! }   # caller's own effective cells

# READ
permissionMatrix(workspaceId: String!): PermissionMatrix!             # @authorized(requires: WORKSPACE_VIEWER)
myPermissions(workspaceId: String!): [ResolvedPermission!]!           # @authenticated

# WRITE (runtime config — no deploy). One authority model: WORKSPACE_ADMIN. Audited (§9).
input SetRolePermissionInput { workspaceId: String!  role: WorkspaceRoleName!  verb: Verb!  resourceKind: ResourceKind!  allowed: Boolean! }
setRolePermission(input: SetRolePermissionInput!): PermissionMatrix!   # @authorized(requires: WORKSPACE_ADMIN)
```

**Storage:** extend the existing `WorkspacePolicyNode` (already per-role) from a fixed flag list to
a cell-set; today's booleans map 1:1 as seed values (below). No new store, no migration of identity.

**Seed defaults (maps today's flags → cells; new cells get a conservative default):**

| Cell (verb × kind) | ADMIN | COLLABORATOR | CONTRIBUTOR | VIEWER | AGENT_GUEST | Source |
|---|---|---|---|---|---|---|
| READ · DATA_ASSET | ✅ | ✅ | ✅ | ✅ | ❌ | `dataAssetRead` |
| CREATE · DATA_ASSET | ✅ | ✅ | ❌ | ❌ | ❌ | `dataAssetCreate` |
| READ/CREATE/UPDATE/DELETE · PROJECT | ✅ | C:✅ CRU / no D | R only | R only | ❌ | `project*` flags |
| READ · GOVERNANCE (→ v1: READ·WORKSPACE — `GOVERNANCE` is not a §2.1 `ResourceKind`; governance artifacts are workspace-scoped with no dedicated kind, same collapse as the `memberCreate` row below) | ✅ | ✅ | ✅ | ✅ | ❌ | `governanceRead` |
| MANAGE members (→ v1: CREATE·WORKSPACE-member) | ✅ | ❌ | ❌ | ❌ | ❌ | `memberCreate` |
| **RUN · TRANSFORMATION/PIPELINE/WORKFLOW** | ✅ | ✅ | ❌ | ❌ | ❌ | **new — conservative default** |
| **DELETE · DATA_ASSET** | ✅ | ❌ | ❌ | ❌ | ❌ | **new — admin-only default** |

Any cell absent from a role's set resolves to **not allowed** (default-deny, INV-2). Admins edit
any cell at runtime via `setRolePermission`.

### 2.3 Enforcement wiring + the `@public` escape

`@authorized` is refactored to **delegate to `authorize()`**; its `requires:` becomes the
`(verb, resourceKind)` the field maps to. A field with **no** directive fails schema-build — except
those tagged **`@public`** (login, register, health), an explicit, greppable allowlist (INV-2). No
field is silently open.

### 2.4 Operational contract (this is a hot path — treat it like one)

```typescript
// MatrixCache: read-through Redis cache of a workspace's matrix, keyed workspace_id.
//  - setRolePermission INVALIDATES the workspace key in the same transaction (INV-11) — no stale ALLOW.
//  - RoleReader lookups are DataLoader-batched so a list resolver returning N objects is 1 role read, not N.
// authorize() has its own configured budget (timeout_s, config — a duration) AND is bounded by
//  ctx.deadline (an absolute timestamp inherited from the caller, per pluggable-scalable.md PS-11:
//  "child deadline ≤ parent"). Effective cutoff = min(now + timeout_s, ctx.deadline) — whichever
//  comes first. On exceeding that cutoff, OR any internal error → BLOCK·fail_closed.
// Degraded mode is explicit and owned: authorize() unavailable ⇒ writes are DENIED (fail-closed), reads
//  fall back to the last cached matrix within TTL; a hard cache+graph outage denies writes, not silently allows.
//
// ctx (RequestContext, pluggable-scalable.md) — which fields v1 actually reads, and why the rest don't apply yet:
//  - ctx.deadline    — consulted (above). The only field that gates decision logic.
//  - ctx.correlation_id — stamped onto the authz.decision span and every authz.* log event (§9) so a
//    decision can be traced end-to-end; not consulted by the decision itself.
//  - ctx.budget_remaining, ctx.tenant_tier — NOT used. authorize() is a Neo4j/cache read, not a metered
//    external call (budget doesn't apply per pluggable-scalable.md PS-12), and per-tier matrix behavior
//    is out of scope until §12.2 (custom-role authoring). Carried on ctx for forward-compat only —
//    a later increment that needs them extends this contract explicitly, not by silent assumption.
```

### 2.5 brightbot — call the decider, re-bind the run path

The agent layer gains no second engine. It (a) resolves the caller's role into tool context so
tools are role-aware, (b) calls `authorize()` (GraphQL) before any **RUN** or write tool — bounded
to mutating tools, not every read (mirrors THEME "transform-run and query-execute only"), and
(c) **re-binds** `session_info.workspaceId` to the authenticated identity on the run path.

## 3. Invariants (DbC)

- **INV-1 One decision point.** No authorization outcome SHALL be produced outside `authorize()`;
  `@authorized` and every manual `AuthModel.check*` resolve through it.
- **INV-2 Default-deny + explicit public.** A `(verb, resource)` with no allowed cell SHALL return
  BLOCK. A gated field with no directive SHALL fail schema-build; only `@public` fields (login/
  register/health) are reachable unauthenticated, by an explicit allowlist.
- **INV-3 Fail-closed.** IF `authorize()` times out or errors, THEN THE System SHALL return BLOCK.
- **INV-4 Neo4j-authoritative.** THE decision SHALL derive from Neo4j role + matrix edges, never a
  JWT `custom:*` claim.
- **INV-5 Tenant isolation.** `subject.workspaceId` and `resource.workspaceId` SHALL match, else
  BLOCK · cross_tenant — independent of role or admin tier.
- **INV-6 Matrix is the authority.** THE runtime verdict SHALL be cell-membership in the subject
  role's matrix; role **rank** SHALL be used ONLY to seed defaults and for the admin-tier
  short-circuit, never as a runtime `rank ≥ required` comparison.
- **INV-7 Admin tier still needs membership.** A SystemAdmin/SuperAdmin SHALL pass only on
  workspaces they are a member of (platform role ≠ workspace membership).
- **INV-8 Config authority.** Editing the matrix SHALL require `WORKSPACE_ADMIN` and SHALL be
  recorded (§9). (Single authority model — no second verb.)
- **INV-9 Shadow safety.** WHILE a verb is in shadow mode (§11), `authorize()` SHALL compute + record
  the decision but SHALL NOT change the operation's outcome.
- **INV-10 Closed vocabulary, open config.** `Verb`/`ResourceKind`/`WorkspaceRoleName` SHALL be
  closed enums; which cells a role holds is open workspace config, never code.
- **INV-11 Cache coherence.** A `setRolePermission` write SHALL invalidate the workspace's cached
  matrix before the next decision reads it — no stale ALLOW SHALL survive an edit.
- **INV-12 Agents don't re-derive.** brightbot/webapp SHALL obtain decisions from `authorize()`,
  never compute a parallel verdict.

Budget: 12 invariants.

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: One decision point + an editable permission matrix (v1)

  Scenario: Edit a matrix cell at runtime
    Given a workspace where VIEWER has READ·DATA_ASSET allowed
    When an admin calls setRolePermission(role: VIEWER, verb: READ, kind: DATA_ASSET, allowed: false)
    Then a Viewer's next READ on a data asset returns BLOCK · not_permitted
    And no deploy occurred and the edit is recorded in the audit log

  Scenario: Role-based RUN gating
    Given RUN·PIPELINE is allowed for COLLABORATOR and not for VIEWER
    When a Viewer attempts to trigger a pipeline
    Then authorize returns BLOCK, and a Collaborator's RUN is ALLOWed

  Scenario: A previously ungated mutation is default-denied
    Given syncDataAssets, which carried no directive
    When an unauthorized caller invokes it
    Then it returns BLOCK (default-deny), not execution

  Scenario: Public fields stay reachable
    Given the login mutation tagged @public
    When an unauthenticated caller invokes it
    Then it is reachable and the schema builds; a non-@public undirected field fails schema-build

  Scenario: Cross-tenant is blocked regardless of role
    Given a valid token for workspace A (even a SystemAdmin of A)
    When the caller targets a resource in workspace B
    Then authorize returns BLOCK · cross_tenant

  Scenario: Fail closed on timeout
    Given authorize() exceeds its deadline reading the graph
    When any gated operation is attempted
    Then the operation is BLOCKed, not allowed

  Scenario: Shadow mode records but does not enforce
    Given verb RUN is in shadow mode
    When a decision would be BLOCK
    Then the operation proceeds and a shadow-divergence event is recorded

  Scenario: An edit is not defeated by cache
    Given a cached matrix where VIEWER may READ·DATA_ASSET
    When an admin revokes that cell
    Then the very next Viewer READ is BLOCKed (cache invalidated), not served from stale cache
```

Budget: 8 scenarios.

## 5. Out of Scope (v1) — see §12 for where each lands

- Per-subject / per-group **grants** and any **Share** UI (`GRANTED` edge) — §12.1.
- **Custom-role authoring** (create a brand-new role) — v1 edits the five existing roles' cells only — §12.2.
- **Declared-governance enforcement** (WARN, `GOVERNED_BY` gates, multi-gate combination, block-wins-across-gates) — §12.3.
- **Session sharing** and **project-content propagation** — §12.4/§12.5.
- **Adopting Cedar/OpenFGA** — a future adapter + its own ADR, never v1.
- **The Phase-0 security holes as line items** — split into their own fast-track spec (§11); default-deny + run-path re-bind close several structurally.

## 6. Dependencies

| Dependency | Source | Status | Blocking? |
|---|---|---|---|
| `WorkspacePolicyNode` / role nodes / `@authorized` directive | `platform-core/src/graphql/ogm/pipeline-typedefs.ts`, `directives/` | Exists | Extend / refactor target |
| Redis + GraphQL DataLoader | platform-core (per its CLAUDE.md) | Exists | Ready — §2.4 cache/batch |
| brightbot token-validated GraphQL client | `brightbot/utils/token_validator.py` | Exists | Ready — §2.5 |
| Neo4j OGM + raw-Cypher service | platform-core | Exists | Ready |

## 7. Correctness Properties

### Property 1: Default-deny completeness
*For any* `(subject, verb, resource)` with no allowed matrix cell and no admin-tier match, `authorize()` returns BLOCK.
**Validates: §3 INV-2, §4 "A previously ungated mutation is default-denied"**

### Property 2: Fail-closed
*For any* timeout or internal error in `authorize()`, the effect is BLOCK.
**Validates: §3 INV-3, §4 "Fail closed on timeout"**

### Property 3: Tenant isolation
*For any* decision where subject and resource workspaces differ, the effect is BLOCK · cross_tenant, independent of role/tier.
**Validates: §3 INV-5, INV-7, §4 "Cross-tenant is blocked regardless of role"**

### Property 4: Matrix authority (no rank at runtime)
*For any* runtime decision, the verdict depends only on cell-membership; no code path compares role rank to a required rank.
**Validates: §3 INV-6, §4 "Role-based RUN gating"**

### Property 5: Cache coherence
*For any* `setRolePermission` edit, no subsequent decision in that workspace reads a pre-edit cached cell.
**Validates: §3 INV-11, §4 "An edit is not defeated by cache"**

### Property 6: Shadow safety
*For any* verb in shadow mode, the operation's outcome equals authorization being absent, while divergence is recorded.
**Validates: §3 INV-9, §4 "Shadow mode records but does not enforce"**

Budget: 6 properties.

## 8. Eval Criteria

Not applicable — `authorize()` is a deterministic graph decision, pinned by §3/§7, not an LLM judge.
The LLM-shaped question ("does this operation violate a natural-language governance policy?") belongs
to the governance increment (§12.3 / `governance-policy-enforcement.md`), where its evaluator lives.

## 9. Observability Contract

- **Span**: `authz.decision` — attributes `workspace.id`, `authz.verb`, `authz.resource_kind`,
  `authz.effect`, `authz.decided_by`, `authz.shadow`, `correlation_id` (from `ctx.correlation_id`,
  §2.4 — the join key back to the request that triggered the decision). brightbot tool calls wrap
  it under `gen_ai.tool.execute`.
- **Log events**: `authz.allow`, `authz.block` (`reason`), `authz.shadow_divergence`, `authz.matrix_edited`
  (ids/counts only, never resource values) — each carries `correlation_id` too.
- **Metrics**: `authz_decisions_total{effect,verb,resource_kind,workspace_id}`;
  `authz_shadow_divergence_total{verb,workspace_id}` — the gauge that must reach ~0 before a verb
  leaves shadow (§11); `authz_decision_latency_ms` (guards the §2.4 hot-path budget).

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brighthive-platform-core` | `brighthive-platform-core/tests/` | One test per §2.2 contract entry; L2 per invariant against **real Neo4j** — default-deny on an undirected field, fail-closed on timeout, cross-tenant BLOCK, matrix-authority (edit a cell → verdict flips), cache invalidation (INV-11) |
| `brighthive-webapp` | `tests/e2e` (Playwright) + `cypress/` | L1: matrix editor writes `setRolePermission` and `permissionMatrix` reflects it; L2: a revoked cell blocks the role in-app |
| `brightbot` | `brightbot/tests/` + `brightbot/brightbot/evals/` | L2: a RUN tool is blocked for a role without the cell; run-path `session_info.workspaceId` re-bound to authenticated identity — real GraphQL, not a mock |
| `brighthive-e2e` | `e2e/` (cross-repo) | Feature: admin revokes VIEWER READ·DATA_ASSET → a Viewer is denied end-to-end against staging; error-path: a denied RUN returns BLOCK from the real API |

**Real-behavior requirement** (`~/.claude/rules/test-behavior-real.md`): the platform-core INV-4/INV-6
and cache cases and the e2e flow MUST hit real Neo4j / the real backend — resolver-shape assertions
don't satisfy these rows.

Before the implementation PR: run platform-core + webapp e2e + brightbot + `brighthive-e2e`; confirm
every §2/§3/§4 entry has a case; confirm the real-backend rows are green.

## Areas Involved

| Area | Repo | Impact (v1) |
|---|---|---|
| Platform Core | `brighthive-platform-core` | `authorize()` + matrix cache; `@authorized` delegates; `@public` allowlist; default-deny schema-build; `setRolePermission`/`permissionMatrix`/`myPermissions`; extend `WorkspacePolicyNode` to a cell-set |
| Web App | `brighthive-webapp` | Static matrix page → live editor bound to `setRolePermission`; fix the phantom `editor` role + local-dev gate bypass |
| BrightBot | `brightbot` | Role in tool context; call `authorize()` before RUN/write tools; re-bind run-path workspace |

## 11. Rollout (v1 stops at Phase 1b — never flip 49-ungated to fail-closed at once)

```
Phase 0   Fix-now security holes — OWN fast-track spec (gateway authorizer, upsertWarehouseConfig
          membership, /ogm claim-trust + missing return, run-path re-bind, thread-owner skip). Ships first.
Phase 1a  authorize() + matrix + cache behind SHADOW mode: computes + records, enforces nothing.
          Watch authz_shadow_divergence_total per verb.
Phase 1b  Flip @authorized to delegate verb-by-verb once that verb's divergence ≈ 0; default-deny
          becomes the schema-build rule (@public carve-out). Matrix editor + myPermissions ship. ← v1 DONE
```

INV-9 guarantees Phase 1a changes no outcome; the divergence metric is the go/no-go for each 1b flip.

## 12. Later increments (named — each its own spec/epic-child under BH-1464)

1. **Per-subject & group grants + Share UI** — a `GRANTED {verbs}` edge (revives cancelled BH-217);
   **group/tag-scoped** targets (borrow `RuleScope` node/tag/group from `data-quality-rules.md`) to
   answer *"a group of assets queryable by only X, Y, Z"*. Closes asks #3(per-user)/#4.
2. **Custom-role authoring** — create brand-new roles as cell-sets (v1 already made cells editable;
   this adds new named sets). Remainder of ask #1.
3. **Governance-gate convergence** — `authorize()` consumes `GOVERNED_BY` gates (BH-1255), adds WARN
   + multi-gate block-wins; the enforcement point `THEME-governance-enforced.md` (BH-172) needs. Ask #2 (full).
4. **Session sharing** — a real shared-session grant + join/read model (v1 only *closes* the
   thread-owner hole in Phase 0). Ask #7.
5. **Project-content propagation** — decide + document whether a PROJECT grant propagates to the
   project's assets/pipelines; **write the ADR-015 reconciliation** (project as relationship vs
   "not a permission axis") before building. Ask #3 (full).

## Ticket Breakdown (v1 only — children of BH-1464, `issueType=Task`)

| Ticket | Summary | Size | Phase |
|---|---|---|---|
| [BH-1465](https://brighthiveio.atlassian.net/browse/BH-1465) | `feat(platform-core): authorize() decision function (tenant→admin→matrix, fail-closed) + matrix cache/invalidation` | L | 1a |
| [BH-1466](https://brighthiveio.atlassian.net/browse/BH-1466) | `feat(platform-core): extend WorkspacePolicyNode to a cell-set + seed defaults + setRolePermission/permissionMatrix/myPermissions` | L | 1a |
| [BH-1467](https://brighthiveio.atlassian.net/browse/BH-1467) | `feat(platform-core): SHADOW mode + authz.decision telemetry + shadow_divergence & latency metrics` | M | 1a |
| [BH-1468](https://brighthiveio.atlassian.net/browse/BH-1468) | `refactor(platform-core): @authorized delegates to authorize(); @public allowlist; default-deny at schema-build (close 49 ungated)` | L | 1b |
| [BH-1469](https://brighthiveio.atlassian.net/browse/BH-1469) | `feat(webapp): permission-matrix live editor bound to setRolePermission; fix phantom role + local-dev bypass` | M | 1b |
| [BH-1470](https://brighthiveio.atlassian.net/browse/BH-1470) | `feat(brightbot): role-aware tool context + call authorize() before RUN/write tools` | M | 1b |
| [BH-1471](https://brighthiveio.atlassian.net/browse/BH-1471) | `test(e2e): matrix edit denies a role end-to-end + denied RUN returns BLOCK (real backend)` | S | 1b |

*(Phase 0 security tickets live in the separate fast-track security spec, not here.)*

## Related

- **Prior art**: `AUTH_TIERS_AND_RBAC.md` (shipped 3-tier model), `NEO4J_DATA_MODEL.md`.
- **Program epic**: BH-1464 (this is its v1; §12 are its later increments).
- **ADR-016**: "Extend Neo4j (matrix on the existing graph) over adopting Cedar/OpenFGA" —
  `platform-saas-ai-context/docs/decisions/decisions.md` (`platform-saas-ai-context#48`, draft).
  Originally miscited in this spec as "ADR-015" — that number is already claimed by an unrelated,
  still-open decision (`platform-saas-ai-context#46`, BrightAgent shared-core four-plane pattern,
  BH-1255). Recorded under the correct free number instead of colliding two decisions on one slot.
