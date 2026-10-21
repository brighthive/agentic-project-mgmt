---
name: "Nestlé — Azure private deployment alignment"
slug: "nestle"
stage: "trial"
champion: ""
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: ""          # proposed — see ../../ALIGNMENT_2026-10.md (not yet created)
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [nestle, azure, single-tenant, private-only, aks, entra-id, mcp]
---

# Nestlé — Azure private deployment alignment

> Compares Nestlé's proposed Azure architecture with what Brighthive ships today, component by component, with proposed tickets.

**Source:** "Brighthive_Nestle_Azure_Technical_Architecture" (4 pages: Lightweight, Full, private-endpoint matrix,
subnet/NSG (network security group)/flows). All names, CIDRs and SKUs in it are proposals for Nestlé to confirm.
**Capability evidence as of:** 2026-10-17, read-only against `origin/develop` / release tags.

## What the design asks for

Single-tenant, private-only deployment in Nestlé's own Azure subscription (spoke VNet (virtual network), hub firewall, every PaaS
over Private Endpoints, no public IPs, no keys in pods). The primary interface is **Nestlé's own approved agents**
(Claude Code, Codex, NestléGPT) calling the Brighthive MCP (Model Context Protocol) server with Entra ID tokens — no Brighthive UI in
Lightweight. Existing data (ADLS (Azure Data Lake Storage) Gen2, Synapse, Databricks) is read in place.

- **Lightweight:** private AKS (Azure Kubernetes Service) running the agents, skill jobs, MCP server; OpenMetadata + OpenSearch; Neo4j;
  Postgres Flexible Server; Azure AI Foundry / OpenAI; Key Vault; ACR (Azure Container Registry); Log Analytics.
- **Full:** adds the web app behind App Gateway WAF (web application firewall) + APIM (Azure API Management), Airbyte, ADLS/Synapse/Data Factory/Event Grid/Cosmos
  DB/AI Search/AI Language, dbt + Great Expectations jobs, BrightAgent Studio, Visualization agent, optional Databricks.

## Headline

**Neither design is deliverable as drawn today.** Every Brighthive repo deploys to AWS (CDK (Cloud Development Kit), ECS (Elastic Container Service), Amplify,
LangGraph Cloud SaaS), there are no Helm charts, Kubernetes manifests, Bicep or Terraform for any component, and
identity, models, storage and secrets are AWS services (Cognito, Bedrock, S3, DynamoDB, Secrets Manager).
The **agents themselves, Neo4j, OpenMetadata, the Synapse read path, Great Expectations and SSIS diagnostics are
real** and port once containerised. Jira has **no** Nestlé or Azure deployment tickets.

## Component → capability → ticket (Lightweight first)

Legend: 🟢 shipped (on AWS) · 🟡 partial · ⚪ absent · size S/M/L

| Component | Today | Evidence | Work for Azure-private | Ticket | Size |
|---|---|---|---|---|---|
| Orchestrator runtime on AKS | ⚪ self-hosted | brightbot runs on LangGraph Cloud SaaS (`langgraph.json`, 21 graphs); brightagent-v3 (CEMAF, the BrightAgent v3 framework) not in prod | **Decide first:** self-host brightbot's LangGraph server + Postgres checkpointer, or finish CEMAF | **new** NZ-0 (ADR, architecture decision record) | S decision / L build |
| Supervisor + sub-agents | 🟢 | `super_agent/deep_agent.py`, `governance_agent/`, `dbt_agent/`, `analyst_agent/`, `airbyte_custom_agent/` | Port dependencies below; containerise | NZ-1 | L |
| Container images + Helm charts | ⚪ | No `Chart.yaml` / manifests in any repo; agent image built by LangGraph Cloud | Images + charts for agents, MCP, platform API, ingress, Key Vault CSI (Container Storage Interface) driver, workload identity | **new** NZ-1 | L |
| Azure IaC (infrastructure as code) | ⚪ | All AWS CDK / Pulumi-AWS | Terraform or Bicep: spoke VNet, private AKS, Private Endpoints + DNS, ACR, Key Vault, Postgres Flex, AMPLS (Azure Monitor Private Link Scope) | **new** NZ-2 | L |
| Model: Azure AI Foundry / OpenAI | ⚪ | brightbot builds `ChatBedrock*` directly in 12 files, no model port; v3 port has Bedrock + Ollama only | Model-provider port in brightbot + Azure adapter; re-test Bedrock-specific caching/thinking | **new** NZ-3 | M–L |
| Entra ID for MCP callers | 🟡 federation only | `mcp_idp_factory.py` federates OIDC (OpenID Connect, incl. Entra) **into Cognito**; MCP validates Cognito tokens (`mcp/auth.py`) | Native Entra token validation (issuer, audience `brighthive-mcp`, keys) + Entra → workspace/role mapping | **new** NZ-4 = shared with Loop LG-3; related BH-572, BH-588 | L |
| Storage, state, secrets | ⚪ | S3, DynamoDB, Secrets Manager, Redis-on-EC2 across platform-core `src` and brightbot | Ports + Azure adapters: Blob/ADLS, Postgres (or Cosmos) for sessions, Key Vault | **new** NZ-5 | L |
| MCP server | 🟢 (AWS) | brightbot MCP + CDK ingress | Runs behind internal ingress once NZ-1/NZ-4 land | covered | — |
| Platform API (GraphQL + Neo4j) | 🟢 (AWS) | ECS + Lambda; AWS SDK in ~40 `src` files | Behind the NZ-5 ports; drop Glue/Step Functions/Redshift paths for Lightweight | NZ-5 | L |
| Neo4j Enterprise StatefulSet | 🟢 compatible | `driver.ts` plain bolt driver; self-hosted today on EC2 | Enterprise licence, APOC, Azure Disk, nightly backup to Blob, ops runbook (BH-1539 lessons) | **new** NZ-7 | M |
| OpenMetadata (OM) + OpenSearch | 🟢 (AWS EC2) | `brighthive-openmetadata-stack` (OM 1.8.9) | Upstream OM Helm on AKS + Postgres Flex; re-home OM webhook Lambdas | **new** NZ-6 | M |
| Read-only ADLS / Synapse / Databricks | 🟡 | Synapse read shipped (SQL auth, no Entra); ADLS absent; Databricks not a query adapter (BH-1044 open) | Managed-identity auth + Private Endpoints; ADLS reader; Databricks SQL adapter | **new** NZ-8; related BH-1391, BH-1044 | M |
| PRs to Git remote | 🟢 GitHub / GHE (GitHub Enterprise) · ⚪ Azure DevOps | `github-enterprise-host-config.md` Shipped | Azure DevOps adapter only if Nestlé uses it | **new** NZ-11 (conditional) | M |
| Observability (Log Analytics + AMPLS) | ⚪ | LangSmith, Sentry, CloudWatch | OpenTelemetry → Azure Monitor | **new** NZ-9 | M |

**Full-only (later epic, not sized for the trial):** web app with Entra sign-in (MSAL, Microsoft Authentication Library) on App Service behind App
Gateway + APIM; Airbyte on AKS with ADLS destination; Data Factory, Event Grid, Cosmos DB, AI Search, AI Language
adapters; Visualization agent push to Power BI/Tableau/etc. (today it only renders Vega-Lite/PNG); optional
Databricks workspace. Great Expectations and SSIS diagnostics are shipped and only need packaging.

## Top five blockers for Lightweight

1. No self-hostable orchestrator runtime (NZ-0 decision gates everything).
2. Identity is Cognito end to end; the design needs native Entra (NZ-4).
3. No Azure model path (NZ-3).
4. No Kubernetes or Azure packaging at all (NZ-1, NZ-2).
5. AWS storage/state/secrets inside the core (NZ-5).

## Redlines for the architecture document

| Where | Current | Suggested |
|---|---|---|
| np-agents | "CEMAF orchestrator (LangGraph)" | Contradictory — CEMAF replaces LangGraph. Use "BrightAgent orchestrator" and let NZ-0 pick the engine. |
| np-agents | "BrightAgent (Supervisor)" as a separate box | Same process as the orchestrator; show as one. |
| Full np-agents | "BrightStudio runtime" | "BrightAgent Studio" — a graph inside BrightAgent, not a separate runtime. |
| Ingress / flows | "MCP server + Context API" | "Context API" is not a product name; use "Brighthive Platform API" or drop it. |
| Full | Visualization agent → Power BI / Tableau / Superset / Looker / Mode | Mark as planned ⚪; today it renders charts only. |
| Full data plane | "Cosmos DB (memory & state)" | Mark as planned; our memory/state stores are different today. |
| Agents box | "Ingestion, Governance, Engineering, Analysis agents" | Names map to real agents (Airbyte connector builder, governance, dbt/engineering, analyst) — fine. |
| Whole doc | No real-vs-planned marking | Add 🟢 / ⚪ markers so Nestlé's architecture review sees what exists. |

## Decisions needed

These feed into [decisions-and-evidence.md](decisions-and-evidence.md).

| ID | Decision | Owner role | Needed by |
|---|---|---|---|
| O-09 | Trial on Nov 15 runs where? (a) Brighthive SaaS / staging with Nestlé's agents over MCP while Azure build runs in parallel, or (b) wait for Lightweight in Nestlé's Azure | Joint sponsors + Brighthive engineering lead | Before Day 1 |
| O-10 | Orchestrator engine for Azure: self-hosted LangGraph (faster) vs CEMAF (strategic) | Brighthive engineering lead (ADR) | Before NZ-1 starts |
| O-11 | Models available in Nestlé's Foundry (Claude on Foundry vs GPT family) | Nestlé platform owner | Before NZ-3 |
| O-12 | Git remote: GitHub or Azure DevOps | Nestlé engineering owner | Before NZ-11 |
| O-13 | Lightweight only for the trial, Full later — confirm | Joint sponsors | Scope sign-off |
