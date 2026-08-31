---
title: "Multi-Warehouse Config Contract"
epic: "BH-172"
status: "Approved"
created: "2026-09-01"
tags: [warehouse, multi-warehouse, secrets, quality-check]
related:
  specs: ["warehouse-agnostic-architecture.md", "warehouse-extensibility-pattern.md"]
---

# Multi-Warehouse Config Contract

## Problem

Workspaces can hold multiple warehouses, each with its own database(s) and schema(s).
Background jobs (QC, profiler, longitudinal) resolved the workspace **default** warehouse
while assets may live on another. Secrets could be saved without `database`, and legacy
provisioning keyed credentials under the workspace UUID instead of `WarehouseServiceNode.id`.

## Invariants

1. **Secret key = `WarehouseServiceNode.id`** — never the workspace UUID.
2. **Runtime reads secrets only** — Neo4j `database`/`schema` enrich the secret on upsert when omitted.
3. **Asset-scoped resolution** — jobs use `DataAssetNode.warehouseServiceId`, else single provider match, else default.
4. **FQN overrides connect database** — a 3-part table FQN sets `database` (and `schema`) on the resolved config.
5. **Completeness** — host-based warehouses require `host`, `port`, `username`, `password`, `database` before upsert succeeds.

## Gherkin

```gherkin
Scenario: QC uses the asset warehouse, not the workspace default
  Given workspace W has default warehouse D and asset A on warehouse R
  When quality check runs for asset A
  Then credentials are loaded from secrets[W.warehouses[R.id]]
  And database is taken from A.table FQN when fully qualified

Scenario: Upsert merges Neo4j database when form omits it
  Given warehouse node N has database=workspace-database and schema=db_123
  When upsertWarehouseConfig sends host and credentials without database
  Then the stored secret includes database=workspace-database from node N

Scenario: Incomplete Redshift secret is rejected
  Given a Redshift upsert with no database field and no node database
  When upsertWarehouseConfig is called
  Then the mutation fails with warehouse_config_incomplete
```

## Implementation map

| Repo | Change |
|------|--------|
| platform-core | `warehouse-config-validate.ts`, upsert enrich + validate |
| workspace-cdk | CDK create passes real database/schema |
| brightbot | `warehouse_routing.py`, QC/profiler/quality_tools asset routing |
| webapp | Redshift schema field, verify-after-connect |
| platform-core/scripts | `reconcile-legacy-warehouse-secrets.ts` (Phase A ops) |
