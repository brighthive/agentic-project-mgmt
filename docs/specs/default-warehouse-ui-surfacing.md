---
title: Default warehouse — surface the isDefault badge + Set-as-default action in the webapp
epic: BH-172
ticket: BH-1362
status: Partial
last-reviewed: 2026-08-07
related:
  - warehouse-tables-mcp-surface.md
  - warehouse-agnostic-architecture.md
roadmap: mixed — folded into THEME-catalog-and-identity.md — default badge
---

# Spec: Default warehouse — surface it in the webapp

## 1. Context

A workspace can configure several warehouses, but there was never a *default* concept
anywhere the user could see or set. When code needed "the workspace's warehouse" with no
explicit pin, it picked one by a first-entry heuristic (`next(iter(warehouses.values()))`
in brightbot; `resolve_warehouse_id`'s first-configured fallback) — a coin-flip the user
never chose and cannot inspect.

The backend half of the fix is **already built and merge-pending** on platform-core branch
`drchinca/BH-1362/default-warehouse` (commit `567a729b`): `WarehouseServiceOutput.isDefault:
Boolean!` and the `setDefaultWarehouse(workspaceId, warehouseId)` mutation, with exactly-one-
default enforced atomically (INV-1 below), WorkspaceAdmin-gated, 181-line unit test green.

But the **webapp surfaces none of it**. Verified against `origin/develop` (2026-08-07): the
warehouse list (`Warehouse.tsx` → the shared `Service.tsx` AG-Grid) renders no "Default"
badge, the `getWarehouseServices` query never requests `isDefault`, and no "Set as default"
action or mutation exists in the frontend. The default is invisible and unsettable.

This spec covers the **webapp surfacing only** — make the default *visible* (a "Default" badge
on the warehouse row) and *settable* (a "Set as default" row action calling the existing
mutation). No new backend: it consumes the merge-pending BH-1362 surface as-is.

```mermaid
sequenceDiagram
  participant U as User (WorkspaceAdmin)
  participant G as Warehouse list (Service.tsx grid)
  participant C as platform-core (BH-1362, merged)
  U->>G: open Infra ▸ Warehouse
  G->>C: getWarehouseServices { … isDefault }
  C-->>G: [{id,name,provider,isDefault}, …]  (exactly one isDefault:true)
  G-->>U: rows render; the default row shows a "Default" badge
  U->>G: click "Set as default" on a non-default row
  G->>C: setDefaultWarehouse(workspaceId, warehouseId)
  C-->>G: WarehouseServiceOutput (the new default)
  G->>C: refetch getWarehouseServices
  C-->>G: badge moves to the chosen row (still exactly one)
```

**Non-admins** see the badge (read) but not the action (write) — the mutation is
WorkspaceAdmin-gated server-side; the UI hides the control for the same tier.

## 2. Interface Contract (MDE)

### 2a. GraphQL query delta (webapp — `getWarehouseServices.graphql`)

Add one field to the existing selection set. `isDefault` is non-null on the deployed schema
once BH-1362 is merged; requesting it before merge 400s the whole query (see §6 — this is a
hard ordering dependency, the same failure mode as the warehouse-catalog SELECT).

```graphql
query getWarehouseServices($input: WorkspaceInput!) {
  workspace(input: $input) {
    services {
      warehouseServices {
        id
        name
        provider
        status
        isDefault          # ← added (BH-1362)
        # …existing fields unchanged…
      }
    }
  }
}
```

### 2b. Mutation consumed (already exists server-side — new webapp query doc)

```graphql
mutation setDefaultWarehouse($workspaceId: ID!, $warehouseId: ID!) {
  setDefaultWarehouse(workspaceId: $workspaceId, warehouseId: $warehouseId) {
    id
    isDefault
  }
}
```

- **Response 200**: `WarehouseServiceOutput` — the warehouse now default (`isDefault: true`).
- **Response error** (surfaced as GraphQL `errors[]`): `warehouse_not_found` (no such
  warehouse in the workspace) · `workspace_mismatch` (warehouse belongs to another
  workspace) · authz denial for non-WorkspaceAdmin.

### 2c. Frontend rendering contract (`Service.tsx`)

- A **"Default" badge** renders inline in the Service Name cell for the row where
  `isDefault === true`. Warehouse rows only — the shared grid also serves
  Transformation/Ingestion services, whose rows carry no `isDefault` and MUST render no badge
  (guard on `__typename === "WarehouseServiceOutput"` and `isDefault === true`).
- A **"Set as default"** row action is present only on warehouse rows where
  `isDefault !== true`, and only for a WorkspaceAdmin principal. Clicking it fires the
  mutation with `{ workspaceId, warehouseId: row.id }`, then `refetchQueries:
  [GetWarehouseServicesDocument]`; a toast reports success/failure (the `ProjectTransformationCard`
  `useMutation` + `refetchQueries` + toast pattern).

## 3. Invariants (DbC)

- **INV-1 (server, already enforced by BH-1362, restated for the UI contract):** *For any*
  workspace with ≥1 configured warehouse, **exactly one** `warehouseService.isDefault` is
  `true`. The UI renders at most one badge and never zero when warehouses exist.
- **INV-2:** WHERE the row's `__typename` is not `WarehouseServiceOutput`, THE System SHALL
  render no "Default" badge and no "Set as default" action (the shared grid must not leak the
  default concept onto Transformation/Ingestion rows).
- **INV-3:** WHEN the principal is not a WorkspaceAdmin, THE System SHALL NOT render the "Set
  as default" action (read-only badge still shown). Server authz is the source of truth; the
  hidden control is defense-in-depth, not the enforcement.
- **INV-4:** WHEN `setDefaultWarehouse` succeeds, THE System SHALL refetch and move the badge
  to the chosen row within the same interaction — the list never shows two badges or a stale
  default.
- **INV-5:** The webapp SHALL depend only on the GraphQL contract (`isDefault`,
  `setDefaultWarehouse`), never on a vendor/provider identity — the badge is provider-agnostic
  (Snowflake, Redshift, Synapse rows all eligible).

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: Default warehouse visible and settable in the webapp

  Scenario: The default warehouse shows a badge
    Given a workspace with two configured warehouses, one isDefault:true
    When I open Infra ▸ Warehouse
    Then exactly one warehouse row shows a "Default" badge
    And it is the row whose isDefault is true

  Scenario: A WorkspaceAdmin sets a different default
    Given I am a WorkspaceAdmin viewing two warehouses
    And warehouse A is currently default
    When I click "Set as default" on warehouse B
    Then setDefaultWarehouse is called with warehouseId = B
    And after refetch the "Default" badge is on B and not on A

  Scenario: The badge concept does not leak to other service types
    Given I open Infra ▸ Transformation (the same shared grid)
    Then no row shows a "Default" badge
    And no row shows a "Set as default" action

  Scenario: A non-admin cannot set the default
    Given I am a workspace member without WorkspaceAdmin
    When I open Infra ▸ Warehouse
    Then I see the "Default" badge on the default row
    But no "Set as default" action is rendered on any row

  Scenario: Set-default failure is surfaced, not swallowed
    Given setDefaultWarehouse returns a warehouse_not_found error
    When I click "Set as default"
    Then an error toast is shown
    And the badge stays on the previously-default row
```

## 5. Out of Scope

- **The EXTEND/SCOPE context-mode toggle** (part of the old task #110 bundle). It depends on
  the chat-addressing UI, which is not built; specced separately when that lands. This spec is
  the default-*warehouse* surface only, not chat context mode.
- Any change to how the runtime *resolves* the default (brightbot `resolve_warehouse_id` /
  `next(iter(...))`). This spec makes the default visible/settable; wiring the resolver to
  read `isDefault` instead of first-entry is a follow-on (tracked, not here).
- The warehouse→database→table drill-down UI (Task #108/#109) — separate consumers of the
  same catalog layer.
- New backend: `isDefault` + `setDefaultWarehouse` already exist (BH-1362, merge-pending).

## 6. Dependencies

- **HARD, ordering:** platform-core BH-1362 (`567a729b`) merged to `develop` **and the schema
  regenerated into the webapp** (`src/generated.ts` must carry `isDefault` +
  `SetDefaultWarehouseDocument`) *before* the query delta ships. Requesting `isDefault` against
  a schema that lacks it fails the whole `getWarehouseServices` query (documented failure mode:
  memory `warehouse-catalog-query-deployed-fields`). Merge order: platform-core first → regen →
  webapp.
- Shared grid `src/common/Services/Service/Service.tsx` (badge + action land here, guarded).
- Warehouse query doc `src/graphql/queries/getWarehouseServices.graphql`.
- Mutation pattern reference `src/.../ProjectObservabilityPage/ProjectTransformationCard.tsx`
  (`useMutation` + `refetchQueries` + toast).

## 7. Correctness Properties

### Property 1: Exactly-one-default is preserved across a set

*For any* sequence of `setDefaultWarehouse` calls on a workspace, after each call the number
of `isDefault:true` warehouses is exactly one, and the UI reflects that within the same
interaction (refetch).

**Validates: §3 INV-1, INV-4, §4 Scenario "A WorkspaceAdmin sets a different default"**

### Property 2: The default concept is confined to warehouse rows

*For any* row in the shared Service grid, a "Default" badge or "Set as default" action is
rendered *only if* the row's `__typename` is `WarehouseServiceOutput`.

**Validates: §3 INV-2, §4 Scenario "The badge concept does not leak to other service types"**

## 9. Observability Contract

- **Log events (webapp analytics/console, existing toast path):**
  `warehouse.set_default.success`, `warehouse.set_default.error` (mirrors the delete-service
  toast telemetry already in `Service.tsx`).
- No new spans/metrics — this is a read + one gated mutation over existing GraphQL.

## 10. Test Coverage Update

### a. In-repo layered tests

- **L0 (webapp component, `Service.test.tsx` sibling via `MockedProvider`):**
  - one warehouse `isDefault:true` among two → exactly one "Default" badge on the correct row
    (§2c, INV-1).
  - a Transformation-service fixture → no badge, no action (INV-2, §4 leak scenario).
  - non-admin principal → badge shown, "Set as default" absent (INV-3).
- **L1 (interaction):** click "Set as default" on the non-default row → asserts
  `SetDefaultWarehouseDocument` fired with `{workspaceId, warehouseId: B}` and a refetch of
  `GetWarehouseServicesDocument` (§4 "sets a different default").
- **L2 (behavior):** mocked mutation returns `warehouse_not_found` → error toast, badge
  unchanged (§4 "failure is surfaced").

### b. platform-core (already covered)

`tests/unit/set-default-warehouse.test.ts` (181 lines, BH-1362) proves the mutation +
exactly-one-default invariant server-side. This spec adds no backend, so no new platform-core
case — but the webapp L0/L1 fixtures MUST mirror the real `WarehouseServiceOutput` shape
(`isDefault` non-null, `__typename` present), captured from the deployed schema, not invented.

### c. Cross-repo / e2e (brighthive-e2e)

One Playwright feature (post-deploy, `@writes` on a throwaway workspace): open Warehouse list,
assert one badge, click "Set as default" on the other warehouse, assert badge moves. Skipped
with a BLOCKER note until BH-1362 is deployed to staging (same gate as the query delta).

### Self-verification

Before opening the webapp implementation PR: confirm `src/generated.ts` carries `isDefault` +
`SetDefaultWarehouseDocument` (i.e. BH-1362 is merged + codegen re-run), the L0/L1/L2 cases
above exist and pass, and the query delta is not shipped against an unmerged schema.
