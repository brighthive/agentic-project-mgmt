---
name: "Client alignment — Loop Capital + Nestlé (October 2026)"
slug: "alignment-2026-10"
stage: "trial"
champion: ""
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: "2026-10-21"
jira_epic: ""          # proposed epics below — not yet created
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [alignment, loopcapital, nestle, agent-governance, azure, proposed-tickets]
---

# Client alignment — Loop Capital + Nestlé (October 2026)

One page that keeps **clients, business, product and engineering** pointed at the same work.
Detail lives per client: [Loop Capital phase 1](trials/loopcapital/PHASE1_GOVERNANCE.md) ·
[Nestlé Azure architecture](trials/nestle/AZURE_ARCHITECTURE.md) · [Nestlé trial room](trials/nestle/overview.md).
Evidence date: 2026-10-17. Jira inventory: live JQL on BH, same date.

## Where each client stands

| | Loop Capital | Nestlé |
|---|---|---|
| **Client ask (latest doc)** | AI agent governance control plane across Claude, ChatGPT, Copilot (brief, 2026-10-16) | Single-tenant, private-only Azure deployment; Nestlé's own agents call our MCP server (architecture doc, Lightweight + Full) |
| **Next date** | Working session 2026-10-21, 10:00 Central | Trial target 2026-11-15, January fallback |
| **What's real today** | Multi-agent prod (supervisor + 7); permission matrix (shadow); approval on writes; per-action audit lines | The agents, Neo4j, OpenMetadata, Synapse read, Great Expectations, SSIS diagnostics — all on AWS |
| **Biggest gap** | Agent identity, Entra ID, skill risk rating, cross-vendor registry, control view | No Azure/Kubernetes packaging; Cognito, Bedrock and AWS storage in the core |
| **Jira today** | Only next-phase data-engineering tickets (BH-1245, 1403, 1421, 1036) | **Nothing** — no Nestlé or Azure ticket |
| **Client-doc accuracy** | Overstates "engine built, 20% left" and "ran these controls at seven agents" | Names that don't match our product; planned pieces drawn as existing |

## Shared capabilities — build once, serve both

These four items appear in both clients' asks. Building them once is the main capacity lever.

| Capability | Loop needs it for | Nestlé needs it for | Proposed home |
|---|---|---|---|
| **Entra ID sign-in and token validation** (native, not via Cognito) | R2 — agent ⊆ user permissions from Entra groups | MCP callers authenticate with Entra tokens | LG-3 = NZ-4, one ticket, parent BH-1464 |
| **Per-agent identity** | R1 | Agents acting on Nestlé data under their own scoped identity | LG-1 |
| **Durable audit store + query** | R9 control view | Nestlé architecture review asks for immutable audit log | existing BH-1580 / BH-1595 / BH-1510 |
| **Model-provider choice** (port + adapters) | Loop runs on Azure; may want its own models | Azure AI Foundry / OpenAI required | NZ-3 |

## Proposed Jira — for approval (nothing created yet)

Rules applied: project BH, board 152; children are **Task** with `parentKey`; default assignee Kuri until the
team splits work. Owner column is a suggestion from `CLAUDE.md` ownership.

### New epic A — "Loop Capital: AI agent governance (phase 1)"

| ID | Task | Req | Size | Suggested owner | Links |
|---|---|---|---|---|---|
| LG-1 | Agent identity: each agent gets its own identity; on-behalf-of the user; bound into `authorize()` and audit | R1 | L | Kuri | — |
| LG-2 | Agent permissions are the intersection of agent grant and user grant in `authorize()` | R2 | M | Kuri | BH-1465, BH-1470 |
| LG-3 | Native Entra ID token validation + Entra group → role mapping (shared with Nestlé NZ-4) | R2 | L | Ahmed | BH-572, BH-588, BH-1617 |
| LG-4 | Enforce the tool authorization check on the Loop workspace (leave shadow) | R2 | S | Kuri | BH-1590, BH-1471 |
| LG-5 | Microsoft Graph connector: SharePoint + OneDrive read with per-document permission pass-through | R3 | L | Marwan | — |
| LG-6 | Outbound policy point on every send (Slack, email, PR, model call) + file classification | R4 | L | Ahmed | BH-1084, BH-1060, BH-1478 |
| LG-7 | Skill eval sandbox v0: isolated runner, high-risk-action list, per-skill risk score | R5 | L | Kuri | — |
| LG-8 | Re-evaluate skills on change and on a schedule; flag drift | R6 | M | Kuri | LG-7 |
| LG-9 | Skill enabled + shareable flags, admin policy, enforced in skills middleware and web app | R7 | S–M | Harbour | BH-1599 |
| LG-10 | Skills registry v0: Claude first; ChatGPT next; Copilot per Loop's version | R8 | L | Marwan | Oct 21 Copilot answer |
| LG-11 | Runtime action risk scoring with Loop thresholds, block and alert | risk | M–L | Kuri | `ActionClass` |
| LG-12 | Control plane v0: agent activity, permissions, skill risk, trends (co-designed with Loop) | R9 | L | Harbour | BH-1580, BH-1595, BH-1510 |
| LG-13 | Weekly vendor-capability matrix (Claude, ChatGPT, Copilot, Gemini) owned by product | R10 | S | Product | — |
| LG-14 | *Optional* procedure graph: extend WorkflowSpec to send/write actions | opt | L | — | under BH-1463 (empty epic) |

### New epic B — "Nestlé: Azure private deployment (Lightweight)"

| ID | Task | Size | Suggested owner | Links |
|---|---|---|---|---|
| NZ-0 | ADR: orchestrator engine on AKS — self-hosted LangGraph vs CEMAF | S | Kuri | BH-1198, BH-1199 |
| NZ-1 | Container images + Helm charts: agents, MCP server, platform API, ingress, Key Vault CSI, workload identity | L | Ahmed | — |
| NZ-2 | Azure infrastructure as code: spoke VNet, private AKS, Private Endpoints + DNS, ACR, Key Vault, Postgres Flex, AMPLS | L | Ahmed | BH-584 (AWS pattern) |
| NZ-3 | Model-provider port in brightbot + Azure AI Foundry / OpenAI adapter | M–L | Marwan | — |
| NZ-4 | = LG-3 (Entra ID) — one ticket, linked from both epics | L | Ahmed | — |
| NZ-5 | Storage, state and secrets ports + Azure adapters (Blob/ADLS, Postgres sessions, Key Vault) | L | Kuri | — |
| NZ-6 | OpenMetadata + OpenSearch on AKS (upstream Helm, Postgres Flex) | M | Ahmed | — |
| NZ-7 | Neo4j Enterprise StatefulSet + nightly backup to Blob + runbook | M | Ahmed | BH-1539 |
| NZ-8 | Read-only ADLS / Synapse / Databricks via managed identity + Private Endpoints | M | Marwan | BH-1391, BH-1044 |
| NZ-9 | OpenTelemetry → Azure Monitor (Log Analytics via AMPLS) | M | Ahmed | — |
| NZ-10 | Nestlé trial epic (client delivery) — required by `clients/AGENTS.md` before Day 1; resolves trial-room O-06 | S | Kuri | trial room |
| NZ-11 | *Conditional* Azure DevOps PR adapter (only if Nestlé confirms Azure DevOps) | M | — | — |

**Epic C — "Nestlé: Azure Full"** is proposed as a placeholder only (web app with Entra sign-in, App Gateway +
APIM, Airbyte on AKS, Data Factory / Event Grid / Cosmos / AI Search / AI Language, BI push). Do not size it until
Lightweight is decided.

### Hygiene on existing tickets

| Action | Tickets |
|---|---|
| Label `loop-next-phase`, keep status | BH-1245 (+1246–1254, 1341, 1352), BH-1403, BH-1421, BH-1057, BH-1167, BH-1351, BH-1274, BH-1276, BH-1307 |
| Re-parent (no parent today) | BH-1459 → BH-173 |
| Fill the empty epic | BH-1463 ← LG-14 if Loop opts in |
| Reconcile conflict | BH-453 (AgentCore, AWS-only) vs CEMAF pivot vs Nestlé Azure — NZ-0 settles this |

## Capacity reality (four engineers)

Epic A is mostly L items; epic B is mostly L items; both touch the identity and auth core. **They cannot both
finish by their client dates.** What ships for each date:

| Date | Realistic | Not realistic |
|---|---|---|
| Oct 21 (Loop) | Honest capability walk-through; control-plane **design draft**; confirmed requirement rows and owners; Copilot/volume answers | Any working agent identity, Entra, eval sandbox or registry |
| Nov 15 (Nestlé) | Trial on Brighthive-hosted environment with Nestlé's agents over MCP, *if* Nestlé accepts that (O-09); NZ-0 decided; NZ-1/2 under way | Lightweight running in Nestlé's Azure |

## Decisions for business and product (owner: Kuri to route)

1. Approve, change or cut the proposed epics A and B and their tasks.
2. Sequence: Entra ID (LG-3 = NZ-4) first, since both clients need it — confirm.
3. Loop deployment target: SaaS or Loop's Azure tenant (ask on Oct 21).
4. Nestlé trial venue for Nov 15 (O-09) and orchestrator engine (O-10).
5. Who sends corrected wording to Loop (Suzanne) and to Nestlé's architecture reviewers — redlines are in each
   client file.
