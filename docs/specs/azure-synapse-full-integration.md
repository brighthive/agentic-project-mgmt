---
title: "Azure Synapse Analytics — Full Platform Integration"
epic: "BH-172"
author: "drchinca"
status: "Draft"
created: "2026-04-06"
generates: "epic"
tags: [warehouse, azure, synapse, byow, ingestion, destination]
related:
  features: []
  pocs: []
  bedrock: []
---

# Azure Synapse Analytics — Full Platform Integration

## Problem

BrightHive supports Redshift (managed) and Snowflake (BYOW) as warehouse backends, but customers running on Azure have no native path to connect their existing data warehouses or receive ingested data. Azure Synapse Analytics is the Azure-native equivalent of Redshift/Snowflake, and its absence blocks Azure-native customers from the platform. PR #706 on platform-core wires the MVP enum, types, and a basic Connect handler — but the full pipeline (ingestion, query API, managed provisioning, webapp UI, BrightBot query tools) is not implemented.

## Use Case / Goal

Two complementary capabilities:

1. **BYOW Read Source** (analog: Snowflake BYOW) — A customer connects their existing Azure Synapse instance. The platform can query/read data, create destinations (Connect), and expose table metadata via OpenMetadata. No BrightHive infrastructure is deployed in Azure.

2. **Ingestion Destination** (analog: Managed Redshift) — The platform ingestion pipeline (Airbyte → S3 → Glue → Step Functions) writes cataloged data into Azure Synapse. This requires cross-cloud data movement (AWS → Azure), schema-based multi-tenancy inside Synapse, and a Synapse-aware Datapiary integration.

**Success**: A customer on Azure can create a warehouse service, connect destinations, query data via BrightBot, and receive ingestion pipeline output — all without leaving the BrightHive platform.

## Current Situation

### How It Works Today

**Warehouse Service Lifecycle** (`brighthive-platform-core`):
- `WarehouseServiceProvider` enum includes `REDSHIFT`, `SNOWFLAKE`, `AZURE_SYNAPSE` (PR #706).
- `WarehouseServiceModel` CRUD operations create Neo4j `WarehouseServiceNode` with `datapiaryServiceId` bridging to Datapiary.
- Credentials stored in AWS Secrets Manager per workspace; config synced to OpenMetadata.
- `IWarehouseServiceAzureSynapseConfig` defined: `{ server, database, schema, port, username, password }`.

**Destination Service** (`brighthive-platform-core/src/graphql/service/destination_service/`):
- Strategy pattern: `DestinationHandler` interface with `handleDownload()` and `handleConnect()`.
- `RedshiftDestination` — PostgreSQL via `pg`, UNLOAD to S3, GRANT SELECT for Connect.
- `SnowflakeDestination` — Snowflake SDK, JWT auth via Lambda, COPY INTO stage, role-based Connect.
- `AzureSynapseDestination` (PR #706) — `mssql` driver, Connect checks INFORMATION_SCHEMA, Download returns "not implemented".

**Ingestion Pipeline** (`brighthive-data-organization-cdk`):
- Main ingestion: S3 raw → Glue `s3_to_delta.py` → Delta Lake → Glue Crawler → Catalog.
- Snowflake ingestion: 9-step Step Functions state machine — Glue metadata → DynamoDB org lookup → Secrets Manager → JWT generation → Datapiary `create_warehouse` API.
- No Synapse ingestion state machine exists.

**Workspace Infrastructure** (`brighthive-data-workspace-cdk`):
- Redshift Serverless: `RedshiftNamespaceStack` + `RedshiftWorkgroupStack` (16 RPU base).
- REST API Lambdas: `redshift_schema_query_lambda` (JWT auth, psycopg2), `redshift_schemas_lambda` (external schema creation via Spectrum), `redshift_credential_creation_lambda` (user/role creation, Secrets Manager, Core API registration).
- Schema-based multi-tenancy: one Redshift instance, `database_{org_aws_account_id}` schemas.
- No Azure Synapse workspace infrastructure exists.

**Webapp** (`brighthive-webapp`):
- `AddWarehouse.tsx` — two-step wizard: provider selection → config fields.
- `MethodForm.tsx` — Download/Connect/API radio with data storage dropdown.
- AZURE_SYNAPSE partially wired in generated types but no UI tiles or config forms merged to develop.

**BrightBot** (`brightbot`):
- `warehouse.py` query tools use Redshift/Snowflake SQL dialects.
- No T-SQL support for Azure Synapse queries.

### Hard Limitations

1. **No Redshift-style UNLOAD for Synapse** — Synapse has no single-command "export to external storage" equivalent. Download destinations require CETAS (CREATE EXTERNAL TABLE AS SELECT) targeting Azure Blob/ADLS, or BCP bulk copy — both fundamentally different from Redshift UNLOAD to S3.

2. **Cross-cloud networking** — AWS → Azure connectivity requires either: public Synapse endpoints (firewall-gated), Azure ExpressRoute + AWS Direct Connect peering, or VPN tunnels. No platform-level cross-cloud networking exists today.

3. **Authentication model mismatch** — Redshift uses IAM roles; Snowflake uses JWT/key-pair. Synapse supports SQL auth (username/password), Azure AD (Entra ID), and Managed Identity. The platform's auth layer (STS assume-role, Secrets Manager) is AWS-native; Azure AD integration requires new infrastructure.

4. **Datapiary is Snowflake/Redshift-native** — The Datapiary API (`create_warehouse`, `get_service_uuid`) was built for Snowflake's REST API and Redshift's JDBC. Synapse support in Datapiary is unverified and likely requires server-side changes.

5. **Glue Data Catalog is AWS-only** — Synapse uses its own metadata store (Synapse workspace metadata / Azure Purview). Cross-cloud catalog sync doesn't exist natively.

### Gaps

| Area | Gap |
|------|-----|
| **Platform Core** | `AzureSynapseDestination.handleDownload()` returns "not implemented" |
| **Platform Core** | No managed Synapse in `validateAndReturnWarehouseManagedServiceConfigs` |
| **Platform Core** | BYO admin credentials in `destinationUrl` JSON (not Secrets Manager) |
| **Platform Core** | `dwhConnectConfigFromDict` defaults work but no Synapse-specific auth flow |
| **Organization CDK** | No `synapse_ingestion.py` Step Functions state machine |
| **Organization CDK** | No Lambda for Synapse authentication (SQL auth or AAD token) |
| **Organization CDK** | No Glue → Synapse data sync pipeline |
| **Workspace CDK** | No Synapse REST API Lambdas for query execution |
| **Workspace CDK** | No credential creation Lambda for Synapse |
| **Workspace CDK** | No external schema equivalent for cross-tenant Synapse access |
| **Webapp** | No `AddWarehouse` tile for Azure Synapse provider |
| **Webapp** | No `AddWarehouseConfig` fields for Synapse (host, port, database) |
| **Webapp** | No `MethodForm` Synapse entries in Download/Connect dropdowns |
| **Webapp** | `destinationUrl` JSON input for Synapse Connect is raw text (no structured form) |
| **BrightBot** | No T-SQL query tools in `warehouse.py` |
| **Datapiary** | Synapse provider support unverified server-side |
| **OpenMetadata** | No Synapse database service type registered |
| **Networking** | No AWS → Azure connectivity path defined |

## Proposals / Solutions

### Recommended Approach

**Phase 1: BYOW Read Source (MVP)** — 2-3 sprints
Wire Azure Synapse as a customer-managed warehouse that the platform can connect to and query. No BrightHive Azure infrastructure needed — the customer provides their Synapse endpoint.

- Platform Core: Complete Connect destination, move BYO credentials to Secrets Manager, validate managed configs
- Webapp: AddWarehouse tile + config form, MethodForm Synapse entries, structured destination form
- BrightBot: T-SQL dialect support in warehouse query tools
- OpenMetadata: Register Synapse as database service type (MSSQL-compatible)

**Phase 2: Ingestion Destination** — 3-4 sprints
Build the pipeline that writes ingested data (from Airbyte/S3/Glue) into a customer's Synapse instance.

- Organization CDK: Synapse ingestion Step Functions (mirror `snowflake_ingestion.py`)
- Organization CDK: SQL auth Lambda (AAD token generation is Phase 3)
- Datapiary: Verify/extend `create_warehouse` for AZURE_SYNAPSE provider
- Networking: Document customer-side firewall rules for AWS → Synapse connectivity

**Phase 3: Managed Synapse + Advanced Auth** — future
Platform-provisioned Synapse workspaces, Azure AD/Entra ID integration, CETAS-based Download destinations, cross-cloud VPN automation.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| Azure SQL Database instead of Synapse | Simpler setup, same TDS/T-SQL | Not a warehouse — no MPP, no scale-out, wrong product category | Customers expect Synapse for analytics workloads |
| Fabric/OneLake integration | Microsoft's strategic direction | Too early, APIs unstable, different paradigm than warehouse | Revisit in 6 months when Fabric APIs mature |
| JDBC-only adapter (no mssql) | Reuse existing pg-like patterns | JDBC in Node.js requires Java bridge or tedious driver; mssql is native | mssql npm package is battle-tested and already added |
| Skip Phase 2, BYOW-only | Faster delivery, no cross-cloud complexity | Customers who want managed ingestion into Azure are blocked | Phase 2 is critical for parity with Redshift/Snowflake |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Platform Core | `brighthive-platform-core` | Destination handler completion, Secrets Manager migration, managed config validation, Datapiary client |
| Web App | `brighthive-webapp` | Warehouse UI tiles, config forms, destination method forms, schema.graphql + codegen |
| BrightBot | `brightbot` | T-SQL query tools in warehouse.py, dialect detection |
| Data Org CDK | `brighthive-data-organization-cdk` | Synapse ingestion Step Functions, SQL auth Lambda, Glue→Synapse pipeline |
| Data Workspace CDK | `brighthive-data-workspace-cdk` | (Phase 3) Synapse query API Lambdas, credential creation |
| Datapiary | (server-side, external) | Verify AZURE_SYNAPSE provider support in warehouse service API |
| OpenMetadata | `brighthive-openmetadata-stack` | Register MSSQL/Synapse database service type |

## Acceptance Criteria

### Phase 1: BYOW Read Source
- [ ] Customer can add an Azure Synapse warehouse via webapp (provider tile + config form with host, port, database, schema, username, password)
- [ ] Warehouse config stored in Secrets Manager (not in destinationUrl JSON)
- [ ] Connect destination works end-to-end: creates Synapse user/grants, returns connection settings
- [ ] BrightBot can execute T-SQL queries against a connected Synapse warehouse
- [ ] OpenMetadata shows Synapse tables/schemas in data catalog
- [ ] `validateAndReturnWarehouseUnmanagedServiceConfigs` passes for valid Synapse configs and rejects invalid ones

### Phase 2: Ingestion Destination
- [ ] Ingested data (Airbyte → S3 → Glue) lands in customer's Synapse instance via Step Functions pipeline
- [ ] Schema-based multi-tenancy: each organization gets a dedicated Synapse schema
- [ ] Datapiary `create_warehouse` successfully provisions Synapse warehouse service
- [ ] SQL auth credentials managed via Secrets Manager with rotation support
- [ ] Cross-cloud connectivity documented with customer-side firewall configuration guide

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| PR #706 (platform-core enum/types/handler) | Blocking Phase 1 | In Review |
| mssql npm package | Non-blocking | Installed |
| Datapiary AZURE_SYNAPSE support | Blocking Phase 2 | Not verified |
| Customer Azure Synapse instance (for testing) | Blocking Phase 1 QA | Need test instance |
| AWS → Azure network path | Blocking Phase 2 | Not started |
| OpenMetadata MSSQL service type | Non-blocking Phase 1 | Not started |

## Ticket Breakdown

### Phase 1: BYOW Read Source

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | Move BYO Synapse admin credentials from destinationUrl to Secrets Manager | 3 | BH-172 |
| — | Add managed Synapse validation in validateAndReturnWarehouseManagedServiceConfigs | 2 | BH-172 |
| — | Webapp: AddWarehouse tile and AddWarehouseConfig form for Azure Synapse | 3 | BH-172 |
| — | Webapp: MethodForm Synapse entries in Download/Connect dropdowns with structured JSON form | 3 | BH-172 |
| — | Webapp: CreateDestination forward destinationUrl for Synapse + schema.graphql codegen stability | 2 | BH-172 |
| — | BrightBot: T-SQL dialect support in warehouse.py query tools | 5 | BH-172 |
| — | OpenMetadata: Register Synapse/MSSQL as database service type | 2 | BH-172 |
| — | E2E test: BYOW Synapse warehouse creation → Connect destination → query | 3 | BH-172 |

**Phase 1 Total: 23 points**

### Phase 2: Ingestion Destination

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | Organization CDK: Synapse ingestion Step Functions state machine (mirror snowflake_ingestion.py) | 8 | BH-172 |
| — | Organization CDK: SQL auth Lambda for Synapse credential generation | 3 | BH-172 |
| — | Organization CDK: Glue catalog → Synapse table sync pipeline | 5 | BH-172 |
| — | Verify/extend Datapiary create_warehouse API for AZURE_SYNAPSE provider | 3 | BH-172 |
| — | Document AWS → Azure Synapse network connectivity requirements | 2 | BH-171 |
| — | Platform Core: Synapse ingestion event handling in DataIngestionStack parallel map | 3 | BH-172 |
| — | E2E test: Airbyte → S3 → Glue → Synapse ingestion pipeline | 5 | BH-172 |

**Phase 2 Total: 29 points**

**Grand Total: 52 points (~5-7 sprints)**

## Related

- **PR**: brighthive/brighthive-platform-core#706 (MVP enum, types, Connect handler)
- **Analog (Snowflake BYOW)**: `brighthive-data-organization-cdk/brighthive_data_cdk/snowflake_ingestion.py`
- **Analog (Managed Redshift)**: `brighthive-data-workspace-cdk/brighthive_data_cdk/redshift_workgroup.py`
- **Feature doc**: `docs/features/azure-synapse.md` (create after Phase 1 ships)
