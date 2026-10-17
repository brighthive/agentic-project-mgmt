---
title: "Deployment profiles and cloud adapters (Platform Core)"
epic: "Nestlé Azure / multi-cloud"
status: "In progress — Phase 1 workspace port + Phase 1.5 SaaS capability guards"
created: "2026-10-16"
tags: [platform-core, azure, gcp, aws, kubernetes, secrets]
related:
  specs:
    - ../architecture/NESTLE_AZURE_LIGHTWEIGHT_DEPLOYMENT.md
---

# Deployment profiles and cloud adapters

## 1. Context

BrightHive Platform Core today assumes **AWS SaaS**: Cognito, Secrets Manager, DynamoDB, S3, Lambda sidecars. Single-tenant customers (Nestlé Azure, future GCP) need the **same GraphQL and business logic** on **Kubernetes** with **Entra ID**, **Key Vault**, etc.

This spec defines **deployment profiles** and **cloud adapter ports** so product code does not import cloud SDKs directly.

## 2. Deployment profiles

| Profile | Env value | Default | Use case |
|---------|-----------|---------|----------|
| AWS SaaS | `aws-saas` | yes | Lambda/ECS staging/prod |
| Azure K8s | `azure-k8s` | no | Nestlé private AKS |
| GCP K8s | `gcp-k8s` | no | Future private GKE |

**Env:** `DEPLOYMENT_PROFILE` (case-insensitive). Unknown values fail fast at startup.

## 3. Phase 1 — Workspace secret store port

### 3.1 Invariants

- Workspace JSON shape (`warehouses`, `snowflake_warehouses`, `services.openmetadata`, etc.) is **unchanged** across clouds.
- AWS secret id remains `workspace_secret_store/{workspaceId}`.
- Azure Key Vault secret name: `workspace-secret-store-{workspaceId}` (KV naming rules; no `/`).
- Callers use `IWorkspaceSecretStore` or `createWorkspaceSecretStore()` — not `new SecretsManagerService()` for reads on migrated paths.

### 3.2 Port (Phase 1 surface)

- `getWorkspaceSecretStore(workspaceId)`
- `putWorkspaceSecretStore(workspaceId, store)` — full document replace

All workspace document helpers (`storeSlackCredentials`, `storeWarehouseConfig`, Snowflake, GitHub PAT, …) live on `IWorkspaceSecretStore` via `AbstractWorkspaceSecretStore`. AWS `SecretsManagerService` extends the abstract class; Azure KV extends it for get/put only.

### 3.3 Azure env

- `AZURE_KEY_VAULT_URL` — required when `DEPLOYMENT_PROFILE=azure-k8s`
- Auth: `DefaultAzureCredential` (Workload Identity on AKS)

### 3.4 Gherkin (Phase 1)

```gherkin
Scenario: Default profile is AWS SaaS
  Given DEPLOYMENT_PROFILE is unset
  When createWorkspaceSecretStore is called
  Then the AWS adapter is returned

Scenario: OpenMetadata creds on Azure
  Given DEPLOYMENT_PROFILE is azure-k8s
  And AZURE_KEY_VAULT_URL is set
  And Key Vault contains workspace-secret-store-{id} with services.openmetadata
  When OpenMetadataApiV2DataSource loads workspace creds
  Then apiURL and token are returned without calling AWS Secrets Manager
```

## 4. Phase 1.5 — AWS SaaS capability guards

Single-tenant profiles (`azure-k8s`, `gcp-k8s`) use the **workspace secret store** but do **not** implement BrightHive SaaS multi-account AWS (STS into customer accounts, `cdk-admin-secret`, managed Redshift, DynamoDB `PlatformAccountsTable` for destinations, org-scoped ingestion AWS keys).

### 4.1 Invariants

- `AwsSaasPlatformCapability` enumerates SaaS-only features; user-facing messages are stable (`src/platform/deployment-capabilities.ts`).
- `StsClient.assumeRole` fails fast on non–`aws-saas` (LocalStack stub unchanged when `AWS_ENDPOINT_URL` is set).
- Managed warehouse validators, destination Download/Connect secret helpers, org AWS credentials, and org-scoped ingestion paths are gated before AWS SDK calls.
- BYOW Synapse via workspace JSON remains available on all profiles (no STS).

### 4.2 Capability matrix

Authoritative table: `brighthive-platform-core/docs/platform/DEPLOYMENT_CAPABILITIES.md`.

### 4.3 Gherkin

```gherkin
Scenario: Managed Redshift blocked on Azure
  Given DEPLOYMENT_PROFILE is azure-k8s
  When validateAndReturnWarehouseManagedServiceConfigs is called for REDSHIFT
  Then success is false
  And the message explains managed Redshift is unavailable

Scenario: STS assume role blocked on Azure
  Given DEPLOYMENT_PROFILE is azure-k8s
  And AWS_ENDPOINT_URL is unset
  When StsClient assumeRole is invoked
  Then a user-facing error is raised
  And AWS STS is not called
```

### 4.4 Follow-up (not Phase 1.5)

- `IPlatformSecretStore` for platform-wide secrets outside workspace JSON (only if Nestlé requires it).
- Azure-native destination Connect (per-user creds in Key Vault).
- Port or disable remaining DynamoDB / S3 / Cognito call sites for Core on AKS.

## 5. Later phases

- Phase 2: Remaining SaaS-only surfaces (presign, Glue, data onboarding) behind capability matrix or cloud ports.
- Phase 3: `ObjectStore`, `KeyValueStore`, `IdentityVerifier` ports.
- Phase 4: Webhook workers as containers; Helm profile `k8s-single-tenant`.

## 6. Repos

| Repo | Phase 1 / 1.5 |
|------|----------------|
| `brighthive-platform-core` | Profile, workspace port, capability guards, docs |
| `agentic-project-mgmt` | This spec |
| `brightbot` | No change (still HTTP to Core) |
