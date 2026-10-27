---
name: "Cloud-agnostic adapters"
epic: "BH-1640"
status: Partial
roadmap: "Epic BH-1640 and clients/trials/nestle/tickets.md; registries exist today, Phase 0 cleanups and Azure adapters not started"
last_reviewed: "2026-10-27"
---

# Cloud-agnostic adapters

## 1. Context

Brightbot and platform-core run on AWS (Bedrock, S3, Secrets Manager, Cognito, AgentCore). The Nestlé pilot needs Azure (BH-1640). Four registries already exist, but cloud SDK calls bypass them in about 30 files. Azure should be an adapter added to a registry; GCP stays an open slot until a client needs it. Audit date 2026-10-27, from tracked files only.

## 2. Interface contract: registries to extend

| Capability | Where it lives today | Add |
|---|---|---|
| LLM | `brightbot/custom_llms/model_provider.py`: `LLMProvider`, tier map, `build_chat_model` | Enum value, model map, `_build_<provider>` (BH-1644) |
| Warehouse | `brightbot/tools/warehouse_connections.py` `CONNECTION_CLASSES` | BigQuery class for GCP; Synapse exists |
| Pipeline sources | `brightbot/agents/governance_agent/tools/pipeline_health.py` `PIPELINE_SOURCE_ADAPTERS` | None cloud-specific |
| Files | `brightbot/backends/s3_backend.py` implements `BackendProtocol` | `AzureBlobBackend` (BH-1646) |
| Core services | `platform-core/src/config/inversify.config.ts`: `IIdentityProvider`, `IServiceCredentialStore`, `IMailService` | Entra provider (BH-1645), Key Vault store (BH-1646) |

## 3. Invariants

- Cloud SDK imports (`boto3`, `@aws-sdk/*`, Azure and GCP SDKs) appear only under a per-provider package.
- An agent never builds a chat model directly; it calls `build_chat_model`.
- Secrets are read through one path, with no hardcoded region.
- Callers never see storage-specific types such as a bucket or key prefix.
- Token claims are read through configured issuers and claim names.
- A provider without a capability declares it unavailable instead of failing at call time.

## 4. Acceptance criteria

```gherkin
Feature: Cloud-agnostic adapters

  Scenario: Direct Bedrock models are gone
    Given the Phase 0 LLM slice is merged
    When the repo is searched for ChatBedrock outside the provider file
    Then no agent module matches

  Scenario: One secrets path
    Given the secrets slice is merged
    When a dbt agent tool loads warehouse credentials
    Then it calls the secrets port and no module calls get_secret_value directly

  Scenario: Guard test blocks new leaks
    Given a new file imports boto3 outside the AWS package
    When CI runs
    Then the guard test fails

  Scenario: Entra token resolves an identity
    Given a token captured from a real Entra sign-in
    When the audit identity resolver reads it
    Then the user id is non-empty
```

## 5. Out of scope

GCP adapters (no client, no ticket), a second orchestrator, webapp auth, AWS provisioning repos.

## 6. Dependencies

BH-1641 decides the runtime (self-hosted LangGraph on AKS). Claude availability on Azure AI Foundry in Nestlé's region is unverified; confirm before BH-1644 starts.

## 7. Slices (one PR each, under 300 lines)

**Phase 0, AWS behavior unchanged**

| # | Slice | Repo | Leaks to remove |
|---|---|---|---|
| 0.1 | Route direct Bedrock models through `build_chat_model` | brightbot | `slack_router_agent/mcp_tool_node.py:122`, `workflow_agent/agent.py:71`, `custom_llms/custom_claude.py:77`, `dbt_agent_react.py:365` |
| 0.2 | One secrets port with an AWS adapter | brightbot | `tools/aws/secrets_manager.py:97`, `async_secrets_manager.py:57`, `credentials_tools.py:184`, `super_agent/nodes/agents/dbt.py:699` |
| 0.3 | Pick the storage backend from `storage_kind` in workspace config | brightbot | `backend_factory.py:83,165`, `studio_backend.py:36`, `backend_utils.py:87` |
| 0.4 | Per-provider binding modules and neutral interface names | platform-core | `IS3Service`, `ICognitoService`, `ISecretsManagerService`, `IDynamoDBService` |
| 0.5 | Move direct SDK use onto the container, 3 to 4 files per PR | platform-core | about 10 files in `src/graphql/models/*`, about 10 in `src/graphql/service/aws/*` |
| 0.6 | Configurable token issuers and claims | brightbot | `audit/identity.py:62`, `simple_messaging_agent.py:59` |
| 0.7 | Guard test: SDK imports only under a provider package | both | none |

**Phase 1:** Azure adapters under BH-1644 to BH-1650. Add a sandbox port (today `utils/sandbox_utils.py:200` calls `bedrock-agentcore` directly) with an "unavailable" mode on Azure.

## 8. Risks

- Registries without a second adapter prove nothing; each Phase 0 slice needs its adapter slice behind it, and a contract test per port against the real adapter and a failure-injecting fake.
- Workspace config holds AWS-shaped fields (`s3_filesystem_name`, `bedrock_cross_account_role_arn`); a `cloud` discriminator is a schema change and needs the breaking-change review.
- Key Vault slices touch secrets and need a named approval each.
- Not audited: webapp auth, `brighthive-admin`, the CDK repos, `token_validator.py`, Neo4j, OpenMetadata and Airbyte deployment coupling.
