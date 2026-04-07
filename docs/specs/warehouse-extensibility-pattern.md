---
title: "Warehouse Extensibility Pattern"
epic: "BH-172"
author: "drchinca"
status: "Draft"
created: "2026-04-06"
generates: "tickets"
tags: [warehouse, pattern, extensibility, architecture]
related:
  features: []
  pocs: []
  specs: ["azure-synapse-full-integration.md"]
---

# Warehouse Extensibility Pattern

## Problem

Adding a new warehouse type (e.g., BigQuery, Databricks) requires touching 9+ files across 4 repos. There's no single contract — each layer reinvents the routing. This makes expansion expensive and error-prone.

## Goal

Adding a new warehouse type should be a **checklist of isolated, additive changes** — no rewrites, no touching core routing logic. Each layer has a registry/adapter interface. The warehouse type string propagates from a single source of truth.

## Current Touch Points (per warehouse type)

| Layer | Repo | File | What To Add |
|-------|------|------|-------------|
| **GraphQL enum** | platform-core | `src/graphql/schema/typedefs.ts` | Enum value |
| **TypeScript types** | platform-core | `src/common/types.ts` | Config interface |
| **Generated types** | platform-core | `src/graphql/schema/gql-types.ts` | Enum value |
| **OMD service type** | platform-core | `src/data-source/openmetadata/v2.ts` | Union member |
| **OMD type mapping** | platform-core | `src/graphql/models/warehouse-service.ts` | Type → OMD name |
| **Validators** | platform-core | `src/common/validators.ts` | Managed + unmanaged validation |
| **Destination handler** | platform-core | `src/graphql/service/destination_service/` | New handler class |
| **Destination routing** | platform-core | `src/graphql/service/destination_service/destination.ts` | Route in handleConnect/handleDownload |
| **Webhook adapter** | platform-core | `openmetadata_webhook_lambda/utils/warehouse_adapter.py` | Adapter + registry entry |
| **Webapp enum** | webapp | `schema.graphql` + `src/generated.ts` | Enum value |
| **Webapp UI** | webapp | `AddWarehouse.tsx` + `AddWarehouseConfig.tsx` | Tile + config fields |
| **Webapp destinations** | webapp | `MethodForm.tsx` | Dropdown entries |
| **BrightBot type** | brightbot | `brightbot/utils/warehouse.py` | Literal union member |
| **BrightBot connection** | brightbot | `brightbot/tools/warehouse_connections.py` | Connection class + factory route |
| **BrightBot SQL dialect** | brightbot | `brightbot/prompts/retrieval_agent_prompts.py` | Dialect rules |
| **BrightBot config lookup** | brightbot | `brightbot/tools/aws/secrets_manager.py` | Required field validation |
| **Ingestion routing** | org-cdk | `warehouse_router_lambda/main.py` | Recognized type |
| **Ingestion SFn** | org-cdk | `brighthive_data_cdk/` | New stack (if write needed) |
| **Ingestion Choice** | org-cdk | `data_ingestion_stack.py` | Choice branch + SFn wiring |

## Pattern: Registry + Adapter at Every Layer

### Principle

Each layer has:
1. **A registry** (dict/map) keyed by warehouse type string
2. **An adapter interface** that each warehouse implements
3. **A single routing function** that does `registry[type]` — never `if/elif`

### Type String Contract

The warehouse type string flows from the **workspace secret store** (`workspace_secret_store/{workspaceId}.warehouses[id].type`) and is the single source of truth at runtime.

| Type String | OpenMetadata Name | Display Name | Default Port |
|-------------|-------------------|-------------|--------------|
| `REDSHIFT` | `Redshift` | Redshift | 5439 |
| `SNOWFLAKE` | `Snowflake` | Snowflake | 443 |
| `AZURE_SYNAPSE` | `Mssql` | Azure Synapse | 1433 |
| _(future)_ | _(future)_ | _(future)_ | _(future)_ |

### Layer Contracts

#### 1. Platform Core — Destination Service
```typescript
// Interface: src/graphql/service/destination_service/interfaces.ts
interface DestinationHandler {
  handleDownload(configDict: any): Promise<ResponseBody>;
  handleConnect(configDict: any): Promise<ResponseBody>;
}

// Registry: src/graphql/service/destination_service/destination.ts
const HANDLERS: Record<string, () => DestinationHandler> = {
  REDSHIFT: () => new RedshiftDestination(config),
  SNOWFLAKE: () => new SnowflakeDestination(config, awsSession, jwtLambda),
  AZURE_SYNAPSE: () => new AzureSynapseDestination(config),
};
```

#### 2. Platform Core — OpenMetadata Webhook
```python
# Interface: openmetadata_webhook_lambda/utils/warehouse_adapter.py
class WarehouseAdapter(ABC):
    def resolve_schema_id(self, owner_uuid, schema_name) -> str | None: ...
    def process_table(self, table_name, schema_name, owner_uuid, table_id) -> dict: ...

# Registry
WAREHOUSE_ADAPTERS: dict[str, WarehouseAdapter] = {
    "Redshift": RedshiftAdapter(),
    "Mssql": SynapseAdapter(),
    "Snowflake": SnowflakeAdapter(),
}
```

#### 3. Platform Core — Config Validation
```typescript
// src/common/validators.ts — should become:
const MANAGED_VALIDATORS: Record<string, (config) => ValidationResult> = {
  REDSHIFT: validateRedshiftManaged,
  SNOWFLAKE: validateSnowflakeManaged,
  AZURE_SYNAPSE: validateSynapseManaged,
};
```

#### 4. BrightBot — Warehouse Connection
```python
# brightbot/tools/warehouse_connections.py
class WarehouseConnection(ABC):
    def connect(self) -> Any: ...
    def execute_query(self, query: str) -> list[dict]: ...
    def close_connection(self) -> None: ...

# Factory routes by type string
CONNECTION_CLASSES: dict[str, type[WarehouseConnection]] = {
    "redshift": RedshiftConnection,
    "snowflake": SnowflakeConnection,  # future
    "azure_synapse": SynapseConnection,
}
```

#### 5. BrightBot — SQL Dialect
```python
# brightbot/prompts/retrieval_agent_prompts.py
DIALECT_RULES: dict[str, str] = {
    "redshift": "Only use Redshift compatible syntax",
    "snowflake": "Only use Snowflake compatible syntax",
    "azure_synapse": "Only use T-SQL syntax. Use TOP instead of LIMIT...",
}
```

#### 6. Org CDK — Ingestion Routing
```python
# warehouse_router_lambda reads type from secret store
# DataIngestionStack Choice state routes by string match
# Each warehouse type has its own SFn stack (or skip)
```

#### 7. Webapp — UI Registry
```typescript
// Provider options driven by enum — no hardcoded arrays
const WAREHOUSE_OPTIONS = Object.values(WarehouseServiceProvider).map(v => ({
  value: v,
  title: v.replaceAll("_", " "),
}));

// Config fields per provider
const CONFIG_FIELDS: Record<WarehouseServiceProvider, string[]> = {
  REDSHIFT: ["username", "password", "host", "port"],
  SNOWFLAKE: ["apiKey", "apiEndpoint", "accountId"],
  AZURE_SYNAPSE: ["host", "port", "database", "schema", "username", "password"],
};
```

## Adding a New Warehouse Type: Checklist

### Step 1: Platform Core (types + validation)
- [ ] Add enum value to `WarehouseServiceProvider` in `typedefs.ts`, `gql-types.ts`, `gql-types.d.ts`
- [ ] Add config interface to `common/types.ts`
- [ ] Add OMD name to `DataServiceConfig.serviceType` union in `openmetadata/v2.ts`
- [ ] Add type → OMD name mapping in `warehouse-service.ts`
- [ ] Add managed + unmanaged validation branches in `validators.ts`

### Step 2: Platform Core (destination handler)
- [ ] Create `new_warehouse.ts` handler implementing `DestinationHandler`
- [ ] Register in `destination.ts` handleConnect/handleDownload routing

### Step 3: Platform Core (OpenMetadata webhook)
- [ ] Create adapter class in `warehouse_adapter.py`
- [ ] Register in `WAREHOUSE_ADAPTERS` dict

### Step 4: Webapp
- [ ] Add enum value to `schema.graphql` + `generated.ts`
- [ ] Config fields render automatically from `CONFIG_FIELDS` registry
- [ ] MethodForm dropdown renders automatically from enum values

### Step 5: BrightBot
- [ ] Add connection class in `warehouse_connections.py`
- [ ] Register in `CONNECTION_CLASSES` factory
- [ ] Add dialect rules in `retrieval_agent_prompts.py`
- [ ] Add required field validation in `secrets_manager.py`

### Step 6: Org CDK (if write/ingestion needed)
- [ ] Add type to `warehouse_router_lambda` recognized types
- [ ] Create ingestion SFn stack
- [ ] Add Choice branch in `data_ingestion_stack.py`

## What's Done vs What's Needed

### Done (Azure Synapse implementation)
- [x] All Step 1-6 items implemented for AZURE_SYNAPSE
- [x] OMD webhook adapter pattern (PR #707)
- [x] BrightBot connection + dialect (PR #433)
- [x] Ingestion routing + write pipeline (PR #139)

### Needed (to make the pattern stick)
- [ ] Refactor `destination.ts` to use handler registry instead of if/elif
- [ ] Refactor `validators.ts` to use validator registry instead of if/elif
- [ ] Refactor webapp `AddWarehouseConfig.tsx` to use `CONFIG_FIELDS` registry
- [ ] Refactor webapp `MethodForm.tsx` to generate dropdowns from enum
- [ ] Refactor `WarehouseConnectionFactory` to use `CONNECTION_CLASSES` dict
- [ ] Add this checklist to platform CLAUDE.md for future reference
