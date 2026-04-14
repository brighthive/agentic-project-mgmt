---
title: "Warehouse-Agnostic Platform Architecture"
epic: "BH-172"
author: "drchinca"
status: "Approved"
created: "2026-04-09"
generates: "tickets"
tags: [warehouse, architecture, registry, adapter, synapse, extensibility]
related:
  specs: ["azure-synapse-full-integration.md", "warehouse-extensibility-pattern.md"]
  pocs: []
  features: []
---

# Warehouse-Agnostic Platform Architecture

## Problem

Adding Azure Synapse requires touching 18+ files across 5 repos with hardcoded if/elif chains at every layer. This makes every new warehouse type (BigQuery, Databricks) equally expensive. The platform needs a registry + adapter pattern so new warehouse types are additive-only.

## Goal

New warehouse type = one new class + one registry entry per layer. Zero changes to routing logic. Zero changes to existing warehouse code.

## Type String Contract

| Type String | OMD Service Type | Display Name | Default Port | SQL Dialect |
|---|---|---|---|---|
| `REDSHIFT` | `Redshift` | Redshift | 5439 | PostgreSQL |
| `SNOWFLAKE` | `Snowflake` | Snowflake | 443 | Snowflake SQL |
| `AZURE_SYNAPSE` | `Mssql` | Azure Synapse | 1433 | T-SQL |

Flows from `WarehouseServiceProvider` GraphQL enum -> workspace secret store -> every downstream layer.

---

## Layer-by-Layer Changes

### Layer 1: Platform Core — Destination Service

**Files:** `destination_service/destination.ts`, `destination_service/interfaces.ts`

Replace duplicated if/elif chains with handler registry:

```typescript
type HandlerFactory = (config: DwhConnectConfig, awsSession: AWSSession) => DestinationHandler;

const HANDLER_REGISTRY: Record<string, HandlerFactory> = {
  REDSHIFT: (config) => new RedshiftDestination(config),
  SNOWFLAKE: (config, aws) => new SnowflakeDestination(config, aws, "snowflake-jwt-generator-lambda"),
  AZURE_SYNAPSE: (config) => new AzureSynapseDestination(config),
};
```

Move hardcoded default port to: `const DEFAULT_PORTS: Record<string, string> = { ... }`

**Tickets:** NEW-1 -> BH-305

### Layer 2: Platform Core — OMD Webhook Lambda

**Files:** `openmetadata_webhook_lambda/main.py`, new `utils/synapse.py`

Replace `service_type == "Glue"` / `== "Redshift"` with processor registry:

```python
WEBHOOK_PROCESSORS: dict[str, WebhookTableProcessor] = {
    "Glue": GlueProcessor(),
    "Redshift": RedshiftProcessor(),
    "Mssql": SynapseProcessor(),
}
```

**Tickets:** NEW-2, part of BH-310

### Layer 3: Platform Core — OMD Ingestion Lambda

**Files:** `openmetadata_ingestion_lambda/main.py`, `config_loader.py`

Add `SynapseSourceConfig` + registry:

```python
SOURCE_CONFIGS = { "glue": GlueSourceConfig, "redshift": RedshiftSourceConfig, "synapse": SynapseSourceConfig }
SERVICE_TYPE_MAP = { "glue": DatabaseServiceType.Glue, "redshift": DatabaseServiceType.Redshift, "synapse": DatabaseServiceType.Mssql }
```

**Tickets:** NEW-6, part of BH-310

### Layer 4: Platform Core — OMD Service Type Mapping

**File:** `models/warehouse-service.ts` (line 146)

```typescript
const OMD_SERVICE_TYPE_MAP: Record<string, string> = { REDSHIFT: "Redshift", SNOWFLAKE: "Snowflake", AZURE_SYNAPSE: "Mssql" };
```

**Tickets:** BH-310

### Layer 5: BrightBot — Warehouse Connections

**Files:** `tools/warehouse_connections.py`, `utils/warehouse.py`, new `prompts/sql_dialect.py`

1. New `SynapseConnection(WarehouseConnection)` using `pymssql`
2. Refactor factory to type-string routing: `CONNECTION_CLASSES: dict[str, type[WarehouseConnection]]`
3. Update `WarehouseType` literal: add `"azure_synapse"`
4. SQL dialect rules for agent prompts (T-SQL: `TOP N` not `LIMIT`, `[]` identifiers, `CAST()`)

**Tickets:** BH-309, NEW-3

### Layer 6: Webapp

**Files:** `AddWarehouse.tsx`, `AddWarehouseConfig.tsx`, new `warehouseRegistry.ts`

Extract hardcoded options into registry:

```typescript
export const WAREHOUSE_OPTIONS: Record<WarehouseServiceProvider, WarehouseOption> = { ... };
export const CONFIG_FIELDS: Record<WarehouseServiceProvider, string[]> = { ... };
export const DEFAULT_VALUES: Record<WarehouseServiceProvider, Record<string, string>> = { ... };
```

**Tickets:** BH-306, BH-307, BH-308

### Layer 7: Org CDK — Ingestion Pipeline (Phase 2)

**Files:** `data_ingestion_stack.py`, new `synapse_ingestion.py`

1. New `SynapseIngestionStack` (Step Functions + Lambda for S3 -> Synapse via BCP/CETAS)
2. Refactor `DataIngestionStack` to accept `warehouse_state_machines: dict[str, sfn.IStateMachine]`

**Tickets:** NEW-4, BH-312, BH-313, BH-314, BH-316, BH-317, BH-318

---

## New Tickets

| ID | Title | Repo | Phase | Epic | Pts |
|----|-------|------|-------|------|-----|
| NEW-1 | Refactor destination_service to handler registry | platform-core | 1 | BH-172 | 3 |
| NEW-2 | Refactor OMD webhook lambda to processor registry + Synapse adapter | platform-core | 1 | BH-172 | 3 |
| NEW-3 | Refactor WarehouseConnectionFactory to type-string registry | brightbot | 1 | BH-172 | 2 |
| NEW-4 | Refactor DataIngestionStack to pluggable warehouse state machines | org-cdk | 2 | BH-171 | 5 |
| NEW-5 | Add warehouse extensibility checklist to repo CLAUDE.md files | all | 1 | BH-170 | 1 |
| NEW-6 | OMD ingestion lambda: Synapse source config + registry | platform-core | 1 | BH-172 | 2 |

**Total new: 16 pts across 6 tickets**

---

## Execution Order

### Phase 1: BYOW Read Source (current sprint)

```
BH-304 (creds to Secrets Manager)
  |
NEW-1 (handler registry)  <-- parallel -->  BH-306/307/308 (webapp)
  |                                               |
BH-305 (Synapse validation)                 BH-309 (BrightBot T-SQL)
  |                                               |
BH-310 + NEW-2 + NEW-6 (OMD registration + webhook + ingestion)
  |                                               |
NEW-3 (BrightBot factory)                   NEW-5 (CLAUDE.md checklist)
  |
BH-311 (E2E test)
```

### Phase 2: Ingestion Destination (next sprint)

```
BH-316 (AWS -> Azure networking)
  |
NEW-4 (pluggable warehouse SMs)
  |
BH-313 (SQL auth Lambda) -> BH-312 (Synapse SFn) -> BH-314 (Glue -> Synapse)
                                                          |
                                                    BH-317 (wire into DataIngestionStack)
                                                          |
                                                    BH-318 (E2E test)
```

---

## Test Environments

### Mock Synapse (local Docker)
- Location: `~/iccha/brighthive/mock-azure/`
- SQL Server 2022 at `localhost:1433`, database `brighthive_warehouse`, schema `bh`
- Credentials: `bh_admin` / `BhAdmin#2026!`

### Real Azure Synapse
- Workspace: `bh-synapse-workspace` (westus2)
- Endpoint: `bh-synapse-workspace.sql.azuresynapse.net`
- Dedicated pool: `brighthivepool` (DW100c), database `brighthivepool`, schema `bh`
- Credentials: `bhadmin` / `BhSynapse#2026!`
- Full details: `platform-saas-ai-context/docs/infrastructure/AZURE_INFRASTRUCTURE.md`

### Verification Steps

1. **Destination CONNECT**: GraphQL `createDestination` with `dataStorage: AZURE_SYNAPSE` -> verify connect user created
2. **OMD registration**: Run ingestion lambda with `source_type: "synapse"` -> verify Mssql service in OMD
3. **BrightBot query**: "top 5 CRM deals by value" -> verify T-SQL (`SELECT TOP 5` not `LIMIT 5`)
4. **Webapp**: Add Warehouse -> Azure Synapse tile -> fill form -> verify saved

---

## Validation: Adding BigQuery Later

| Layer | New File | Registry Addition |
|-------|----------|-------------------|
| Destination | `bigquery.ts` | 1 line in `HANDLER_REGISTRY` |
| OMD Webhook | `bigquery.py` | 1 line in `WEBHOOK_PROCESSORS` |
| OMD Ingestion | `BigQuerySourceConfig` | 1 line in `SOURCE_CONFIGS` |
| BrightBot | `BigQueryConnection` | 1 line in `CONNECTION_CLASSES` + `DIALECT_RULES` |
| Webapp | enum value | 1 entry in `WAREHOUSE_OPTIONS` + `CONFIG_FIELDS` |
| Org CDK | `bigquery_ingestion.py` | 1 entry in `warehouse_state_machines` |

Zero changes to routing logic. Zero changes to existing warehouse code.
