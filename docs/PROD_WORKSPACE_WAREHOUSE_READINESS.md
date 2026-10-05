# Production workspace warehouse readiness

> Operational guide for **existing production workspaces**: what must be true for
> warehouse-backed features (pipelines, SQL workflow steps, agents, catalog routing)
> to work with **one or many** warehouses.
>
> Last validated: 2026-10-05 against **Staging Demo** (`1c7cb12e-…`) vs **Prod Test**
> (`1c814cd6-…`). Permanent architecture lives in
> `../platform-saas-ai-context`; implementation detail in
> `brighthive-platform-core` (warehouse reconcile, workflow SQL, OM sync).

---

## TL;DR

| Situation | Required admin work |
|-----------|---------------------|
| **Legacy prod workspace, one Redshift** | Connect credentials (if missing) → **`registerWarehouse`** → optional **`setDefaultWarehouse`**. You do **not** need to hand-stamp `warehouseServiceId` on every catalog asset. |
| **Workspace adds a 2nd warehouse (same or different provider)** | **Register each** warehouse → set **one default** for blind fallback → ensure **OM/catalog sync** (or targeted backfill) sets **`warehouseServiceId`** (or unambiguous `omServiceName`) on **warehouse tables**, especially when two warehouses share a provider (e.g. two Redshifts). |
| **Pipelines with SQL steps fail: “No warehouse could be resolved…”** | Almost always **missing Neo4j warehouse record** (`isRegisteredInBrighthive: false`) even when Infrastructure → Warehouse **shows** a connected warehouse. Fix: **register**, not re-edit pipeline steps. |

---

## Two stores — why Settings can look fine while pipelines fail

BrightHive tracks warehouses in **two places**:

1. **Workspace secret store** — `workspace_secret_store/{workspaceId}` in AWS Secrets Manager  
   Holds connection credentials keyed by **warehouse id** (often the workspace UUID for legacy Redshift).

2. **Neo4j warehouse registry** — `WarehouseServiceNode` linked to the workspace (`WorkspaceNode -[:USES]-> WarehouseServiceNode`)  
   Holds the **Brighthive record** used for defaults, deletion, OMD registration, and (today) **workflow SQL resolution**.

**BH-1372** reconciles both for **read surfaces** (Infrastructure → Warehouse, metrics, catalog warehouse context):

- Registered nodes appear first.
- Connections that exist **only** in the secret store appear as **synthesized** rows with `isRegisteredInBrighthive: false`.

**Workflow SQL execution** (`resolveWorkflowWarehouseContext` in platform-core) still resolves defaults via **Neo4j `WarehouseService.find`**, not the reconciled list. If the registry is empty, SQL steps fail with:

```text
No warehouse could be resolved for this step. Bind catalog assets with a
warehouseServiceId or configure a default warehouse for the workspace.
```

A **different** error means credentials, not registration:

```text
No warehouse credentials found for warehouse service {id} in workspace_secret_store/{workspaceId}.
```

---

## Reference workspaces (verified pattern)

| | Staging Demo `1c7cb12e-6d1a-4922-98a8-cff4de70f24d` | Prod Test `1c814cd6-c88f-40f6-8c1c-12b75a73758e` |
|---|------------------------------------------------------|--------------------------------------------------|
| Secret store | Present | Present |
| Warehouses in API list | 2 (Snowflake + Redshift) | 1 (Redshift) |
| `isRegisteredInBrighthive` | **true** (both) | **false** (Redshift row secret-only) |
| Default warehouse | Redshift `2edd100d-…` **`isDefault: true`** | **`isDefault: false`** |
| Sample catalog assets with `warehouseServiceId` | ~1/10 (most **null**) | 0/10 in sample (many **CSV** uploads) |
| Pipeline SQL smoke (RevOps prod project) | — | **FAIL** (warehouse resolution) until registry fixed |

**Takeaway:** Staging demo is healthy for pipelines **without** every asset having `warehouseServiceId`. Prod test needs **registration** (and ideally a default), not bulk manual catalog edits.

---

## Checklist — every existing prod workspace (single warehouse)

Do this once per workspace (workspace admin or platform ops with member JWT + `X-Workspace-Id`).

### 1. Confirm connection in Secrets Manager

- Secret exists: `workspace_secret_store/{workspaceId}` (platform account Secrets Manager).
- Under `warehouses.{warehouseId}` (or legacy key equal to workspace UUID): host, user, password, database, schema, type.

**UI:** Workspace → **Infrastructure / Services → Warehouse** — connection shows **active**.

### 2. Register the warehouse in Brighthive (required for pipelines)

**UI:** On the warehouse row, use **Register** (creates Neo4j record with the **same id** as the secret key — BH-1441).

**GraphQL:**

```graphql
mutation Register($workspaceId: ID!, $warehouseId: ID!) {
  registerWarehouse(workspaceId: $workspaceId, warehouseId: $warehouseId) {
    id
    isRegisteredInBrighthive
  }
}
```

**Verify:** `isRegisteredInBrighthive: true` on that warehouse in `workspace.services.warehouseServices`.

`setDefaultWarehouse` **before** registration returns `warehouse_not_found` for secret-only rows.

### 3. Set default warehouse (recommended)

Pick the warehouse SQL pipelines and agents should use when nothing else specifies one.

```graphql
mutation Default($workspaceId: ID!, $warehouseId: ID!) {
  setDefaultWarehouse(workspaceId: $workspaceId, warehouseId: $warehouseId) {
    id
    isDefault
  }
}
```

### 4. Smoke-test pipelines (optional but definitive)

As a workspace member:

```graphql
mutation Smoke($input: ValidatePipelineSmokeInput!) {
  validatePipelineSmoke(input: $input) {
    status
    failedStepName
    stepResults { stepName status errorMessage }
  }
}
```

Variables: `{ "input": { "workspaceId": "…", "projectId": "…" } }`.

Expect SQL load steps to get past warehouse resolution; failures after that are SQL/table/credential issues.

### 5. Transformation / dbt (project pipelines)

Separate from warehouses: each project using **DBT** steps needs `transformationServiceId`, valid dbt Cloud credentials in Secrets Manager (`dbt/cloud-api/{transformationServiceId}`), and `jobId` on steps (or project-level default job). See pipeline compile blockers in project specs / BrightAgent verifier output.

---

## Multi-warehouse workspaces

When a workspace has **more than one** connected warehouse (e.g. Staging Demo: Snowflake + Redshift), single-warehouse fallbacks are **not enough** for every feature.

### Per workspace

| Action | Why |
|--------|-----|
| **Register every** connected warehouse | Same Neo4j gap as above — each id in the secret store needs a registry node. |
| **Set one default** | Used when a step/asset does not specify a warehouse (single-warehouse SQL steps). |
| **Do not assume one default covers all providers** | Default is one warehouse id; Snowflake vs Redshift still need explicit routing on assets or bindings. |

### Per catalog asset (warehouse **tables**, not file uploads)

| Field | Purpose |
|-------|---------|
| **`warehouseServiceId`** | Canonical “this table lives on warehouse X.” |
| **`connectionType`** / **`tableFQN`** / **`catalogPath`** | Search, agents, preview, lineage. |
| **OpenMetadata sync** | Backfills `warehouseServiceId` from `omServiceName` when inference is **unique** (one warehouse of that provider). |

**Inference rule (catalog):** If two Redshifts (or two Snowflakes) exist, auto-stamping **cannot** pick reliably — assets need explicit `warehouseServiceId` or OM service names that map 1:1 to registered ids.

**You do not need** to copy **workspace id** onto every asset. Workspace membership is graph relationships (`DataAsset` ↔ `WorkspaceNode`), not a duplicate scalar.

**File / CSV catalog assets** often have **null** `warehouseServiceId` — expected; they are not warehouse tables.

### Pipelines

- Each **SQL step** must resolve to **exactly one** warehouse per run.
- Bindings pointing at assets with **conflicting** `warehouseServiceId` values → compile/runtime error (multi-warehouse step).
- With multiple warehouses and all-null assets, the **registered default** is used — fine only if all SQL in that step targets that warehouse.

### Agents / MCP / BrightBot

- Warehouse tools and routing enrichment prefer assets with `warehouseServiceId` + `connectionType`.
- Multi-warehouse workspaces: ensure OM ingest and catalog index jobs have run so search metadata includes `warehouse_id` where possible.

---

## Verification queries (prod API)

Use `https://api.app.brighthive.net/graphql`, member JWT, header `X-Workspace-Id: {workspaceId}`.

**Warehouse registration state:**

```graphql
query($w: WorkspaceInput!) {
  workspace(input: $w) {
    name
    services {
      warehouseServices {
        id
        name
        provider
        isDefault
        isRegisteredInBrighthive
      }
    }
  }
}
```

**Sample catalog routing (optional):**

```graphql
query($w: WorkspaceInput!) {
  workspace(input: $w) {
    dataAssets(pagination: { limit: 10, offset: 0 }) {
      resultCount
      dataAssets {
        id
        name
        warehouseServiceId
        connectionType
        tableFQN
        catalogPath
      }
    }
  }
}
```

**Read-only secret check (ops, SSO platform profile):**

```bash
aws secretsmanager describe-secret \
  --secret-id "workspace_secret_store/{workspaceId}" \
  --profile brighthive-prod --region us-east-1
```

Do not dump secret values into tickets or chat.

---

## Rollout order for production workspaces

Suggested order for platform / CS / workspace admins:

1. **Prod Test** (`1c814cd6-…`) — register + default Redshift; re-smoke RevOps pipeline.
2. **Prod Demo** (`cd0c14b7-…`) — same checklist before customer demos with SQL pipelines.
3. Any **Nestlé / customer** workspace on prod — per-workspace secret + register + default; then catalog sync.
4. When adding **second warehouse** to any of the above — register new id, then run **catalog sync / OM AutoPilot** and spot-check assets on the new warehouse for `warehouseServiceId`.

---

## Known product gap (for engineering backlog)

- **UI list** = secret store + registry (reconciled).
- **Pipeline SQL** = registry (and asset hints) only.

Aligning workflow resolution with `findConnectedWarehouseServices` would reduce “connected but pipeline broken” incidents. Until then, **`registerWarehouse` is mandatory** for prod workspaces using Project Flow / SQL steps.

Related tickets / areas: BH-1372 (reconcile read path), BH-1441 (`registerWarehouse` / `addWarehouseRecord`), BH-1362 (`setDefaultWarehouse`).

---

## Related docs

| Doc | Location |
|-----|----------|
| Environment UUIDs | `docs/ENVIRONMENTS.md` |
| Staging creds & traps | `docs/STAGING_LEARNINGS.md` |
| Warehouse reconcile tests | `brighthive-platform-core/tests/unit/warehouse-registry-reconcile.test.ts` |
| Workflow warehouse resolution | `brighthive-platform-core/src/graphql/service/workflow/warehouse-sql-execution.ts` |
