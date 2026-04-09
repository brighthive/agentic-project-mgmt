---
title: "Ingestion Agent (BrightAgent)"
epic: "BH-172"
status: "Shipped"
shipped_sprint: 7
shipped_date: "2026-03-24"
services:
  - brightbot
  - brighthive-webapp
  - brighthive-platform-core
tags:
  - airbyte
  - data-ingestion
  - multi-agent
  - brightagent
related:
  specs: []
  pocs: []
notion_page: "33d02437-dde4-8158-99b3-d21202928a45"
---

# Ingestion Agent (BrightAgent)

## What It Does

Connecting a new data source used to mean navigating config screens, looking up connector docs, and copy-pasting credentials into the right fields. Now you just tell BrightAgent where your data lives — "connect our Salesforce" or "pull from our PostgreSQL database" — and it does the rest. It finds the right connector, asks for your credentials in plain language, hooks everything up, runs the first sync, and confirms your data arrived in the warehouse. The whole process is a conversation, not a setup wizard. If a connector doesn't exist yet for your source, BrightAgent builds one on the spot.

## How It Works

The ingestion agent is a ReAct-pattern LangGraph agent powered by Claude Sonnet 4-6 (16k token limit). It operates in two modes depending on how the user accesses it.

```
                    ┌─────────────────────────┐
                    │     USER INTERACTION     │
                    └────────┬────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
    ┌─────────▼─────────┐       ┌──────────▼──────────┐
    │  Main Chat (Any   │       │  OmniPanel (Data    │
    │  Page)             │       │  Sources Page)       │
    │                    │       │                      │
    │  Supervisor routes │       │  Direct connection   │
    │  via keyword match │       │  graph_id:           │
    │  → subagent mode   │       │  "ingestion_agent"   │
    └─────────┬──────────┘       └──────────┬───────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │   AIRBYTE INGESTION AGENT   │
              │   (ReAct + Claude Sonnet)   │
              └──────────────┬──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
  ┌─────▼──────┐   ┌────────▼────────┐   ┌──────▼──────┐
  │ Platform   │   │ AWS Secrets     │   │ DynamoDB    │
  │ Core       │   │ Manager         │   │ Flow State  │
  │ (GraphQL)  │   │ (Credentials)   │   │ (Checkpts)  │
  └────────────┘   └─────────────────┘   └─────────────┘
```

**Entry 1 — Main Chat (any page):** The supervisor agent detects data-source keywords ("connect", "connector", "airbyte", "ingest", etc.) and delegates to the ingestion agent as a subagent. Session info comes from the supervisor's middleware.

**Entry 2 — OmniPanel (data-sources page):** The frontend `ingestionAdapter` opens a direct connection to the `standalone_ingestion_graph` with `graph_id: "ingestion_agent"`, bypassing the supervisor entirely. Its own `InitializationMiddleware` populates workspace context.

### Happy Path Protocol (5-step checkpoint flow)

Each step checkpoints to DynamoDB so interrupted flows can resume:

```
CONNECTOR_FOUND → SPEC_FETCHED → SOURCE_CREATED → CONNECTIONS_WIRED → SYNC_TRIGGERED → VERIFIED
```

1. **Find Connector** — Search workspace catalog (`list_platform_source_definitions_tool`), fallback to public Airbyte registry (`search_public_airbyte_connectors_tool`)
2. **Get Spec** — Fetch connector's JSON schema, identify secret fields (`airbyte_secret: true`), ask user for credentials
3. **Create Source** — Store credentials in AWS Secrets Manager, call Platform Core `addSource` mutation
4. **Wire Connections** — Link source to warehouse destination via `createConnections` mutation
5. **Sync & Verify** — Trigger first sync, delegate to retrieval agent for read test, show sample data

### Custom Connector Protocol

When no existing connector matches, the agent can build one from scratch:

1. Scaffold project structure (Airbyte CDK template)
2. Generate connector spec
3. Test in AWS Bedrock sandbox (check → discover → read)
4. Build Docker image
5. Register in workspace
6. Continue with Happy Path Step 2

## How to Use It

### For Users (UX Guide)

**From the Data Sources page (recommended):**

1. Navigate to **Connect > Data Sources** in your workspace
2. You'll see the **Ingestion assistant (BrightAgent)** checklist at the top of the page
3. Open the **Ask BrightAgent** side panel (OmniPanel)
4. Tell BrightAgent what you want to connect: "I want to connect our Salesforce instance"
5. BrightAgent searches for the connector automatically — no manual browsing
6. When asked, provide your credentials (API key, client secret, etc.) — they're stored securely in AWS Secrets Manager and never displayed in plain text
7. Confirm sync preferences (default: manual trigger, 24h schedule, all streams) or customize
8. BrightAgent triggers the first sync and can run a read test to verify data landed correctly

**From the main chat (any page):**

1. Open BrightAgent from any page in the platform
2. Say something like "Connect my PostgreSQL database" or "I need to ingest data from our SFTP server"
3. The supervisor automatically routes to the ingestion agent
4. Follow the same credential and sync flow

**Resuming an interrupted flow:**

- If a previous setup was interrupted, BrightAgent checks for saved progress automatically
- It will say: "I see we started connecting [name] before — left off at [status]. Want me to continue?"
- All credentials and partial progress are preserved

**Screenshots:** TODO — capture OmniPanel flow on data-sources page

### For Developers (Tech Guide)

**Backend (brightbot):**

| File | Purpose |
|------|---------|
| `brightbot/agents/airbyte_custom_agent/airbyte_custom_agent_react.py` | ReAct agent graph definition |
| `brightbot/agents/airbyte_custom_agent/prompts.py` | System prompt with protocol rules |
| `brightbot/agents/airbyte_custom_agent/models.py` | LLM config (Claude Sonnet 4-6, 16k tokens) |
| `brightbot/tools/ingestion/ingestion_tools.py` | Core tools: list, spec, add, connect, sync |
| `brightbot/tools/ingestion/ingestion_state.py` | DynamoDB checkpoint persistence |
| `brightbot/tools/ingestion/custom_connector_tools.py` | Custom Airbyte connector scaffolding |
| `brightbot/tools/ingestion/airbyte_registry.py` | Public connector catalog search (LRU cached) |
| `brightbot/tools/ingestion/source_discovery.py` | OpenAPI/docs HTTP fetch helpers |
| `brightbot/tools/platform_queries_ingestion.py` | Platform Core GraphQL operations |
| `brightbot/models/airbyte_custom.py` | `AirbyteCustomState` Pydantic model |

**Frontend (brighthive-webapp):**

| File | Purpose |
|------|---------|
| `src/BrightAgent/hooks/adapters/ingestionAdapter.ts` | OmniPanel adapter (`graph_id: "ingestion_agent"`) |
| `src/Sources/All/IngestionAssistantGuide.tsx` | Checklist component on data-sources page |
| `src/Sources/All/All.tsx` | Data sources grid with assistant guide |
| `src/graphql/queries/getDataAssetsForBrightAgent.graphql` | BrightAgent data asset queries |

**LangGraph registration (`langgraph.json`):**
- `ingestion_agent` graph → `standalone_ingestion_graph` (OmniPanel direct access)
- Subagent mode → delegated by supervisor via `deep_agent`

**Feature flag:** `FeatureFlag.AIRBYTE_CUSTOM_AGENT` — per-workspace toggle stored in workspace secrets.

**GraphQL operations (Platform Core):**

| Operation | Type | Purpose |
|-----------|------|---------|
| `sourceDefinitions` | Query | List available connectors |
| `sourceDefinitionSpecification` | Query | Get connector config JSON schema |
| `ingestionServices` | Query | Workspace Airbyte config (workspace IDs, API URLs) |
| `sources` | Query | List existing sources with connection IDs |
| `currentUser` | Query | Resolve manager/owner IDs |
| `addSource` | Mutation | Create source via Platform Core |
| `createConnections` | Mutation | Wire source to destination |
| `syncConnections` | Mutation | Trigger sync jobs |

**DynamoDB state table:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `workspace_id` (PK) | S | Workspace identifier |
| `source_name` (SK) | S | Source being configured |
| `status` | S | CONNECTOR_FOUND / SPEC_FETCHED / SOURCE_CREATED / CONNECTIONS_WIRED / SYNC_TRIGGERED / VERIFIED / FAILED |
| `metadata` | M | IDs, timestamps, error info |
| `updated_at` | S | ISO timestamp |

**Environment variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `INGESTION_STATE_TABLE` | `BrightbotIngestionFlows` | DynamoDB table name |
| `AIRBYTE_CUSTOM_AGENT_MAX_TOKENS` | `16384` | Token limit per turn |
| `AIRBYTE_CONNECTOR_REGISTRY_URL` | Airbyte OSS registry | Public connector catalog URL |

**Middleware stack (standalone mode):**
`InitializationMiddleware` → `OTelToolMiddleware` → `StudioContextMiddleware` → `SummarizationMiddleware` (175k trigger, keep last 6) → `FileSystemMiddleware` → `ModelLimiter` → `ToolLimiter` → `StreamingMiddleware` → `EndProcessingMiddleware`

## Sub-Features

### Connector Discovery

Searches two catalogs in sequence: the workspace's private connector catalog (Platform Core), then the public Airbyte OSS registry (~400+ connectors, LRU cached). Users just name the data source — they never browse a catalog manually.

### Checkpoint & Resume

Every step persists to DynamoDB with status and metadata. If a flow is interrupted (browser close, timeout, error), the agent detects the previous attempt on next interaction and offers to resume from the last completed step. Credentials remain in Secrets Manager.

### Custom Connector Builder

When no connector exists for a data source, the agent scaffolds a new Airbyte CDK connector, generates the spec, tests it in an AWS Bedrock sandbox (check, discover, read), builds a Docker image, and registers it in the workspace. The entire custom connector lifecycle happens within the conversation.

### Secure Credential Handling

All secrets are stored in AWS Secrets Manager at `connectors/{source_name}`. The agent identifies secret fields from the connector spec (`airbyte_secret: true`), never echoes credential values (displays `*****`), and passes real values only in tool calls to Platform Core.

### Read Test Verification

After sync triggers, the agent can delegate to the retrieval agent for a warehouse read test, showing the user a sample of data that landed. This closes the loop: connect → sync → verify.

## Limitations & Roadmap

| Limitation | Impact | Planned Fix | Sprint |
|-----------|--------|-------------|--------|
| No automatic sync status polling | User must manually check if sync completed | Add async sync monitoring with status callbacks | TBD |
| Custom connector builds require Bedrock sandbox | Limited to users with sandbox access enabled | Expand sandbox availability | TBD |
| Single destination per workspace assumed | Users with multiple warehouses must specify | Multi-destination selection in wire step | TBD |
| No connector version management | Can't update connector versions via agent | Add version check and upgrade tool | TBD |
| Screenshots not yet captured | UX guide lacks visual walkthrough | Capture OmniPanel flow screenshots | TBD |

## Changelog

- **Sprint 7** (2026-03-24): Shipped ingestion agent with 5-step protocol, dual entry points (supervisor + OmniPanel), DynamoDB checkpoints, custom connector builder, secure credential storage, and public Airbyte registry search.

## Related

- **Jira Epic**: [BH-172](https://brighthiveio.atlassian.net/browse/BH-172) (Platform Features & Enhancements)
- **Webapp Docs**: `brighthive-webapp/docs/INGESTION_AND_BRIGHTAGENT.md`
- **BrightBot CLAUDE.md**: Agent architecture reference in `brightbot/CLAUDE.md`
