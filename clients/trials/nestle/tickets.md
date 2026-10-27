---
name: "Nestlé tickets"
slug: "nestle"
jira_epic: "BH-1639"
last_reviewed: "2026-10-27"
---

# Nestlé: what we must prove, and the work to get there

Jira is the source of truth for status. [All epics in Jira](https://brighthiveio.atlassian.net/issues/?jql=project%3DBH%20AND%20issuetype%3DEpic%20ORDER%20BY%20created%20DESC).

## In one minute

- **Two epics, 15 tickets, none started.** Every ticket was in "Needs Refinement" on 27 Oct 2026.
- **Eight things Nestlé would judge the trial on.** None is agreed with Nestlé yet, and none has a baseline or a named person who signs it off.
- **Two of the eight have no pilot test at all:** cost and usage, and readiness of the next division.
- **Only two of the eight have any Jira work behind them,** and both are Azure-only.
- **The trial target is 15 Nov 2026,** with January 2027 as the fallback ([plan](trial-plan.md)).

## Epics

| Epic | What it covers |
|---|---|
| [BH-1639](https://brighthiveio.atlassian.net/browse/BH-1639) | The six-week Nestlé trial across divisions |
| [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640) | Running Brighthive privately inside Nestlé's Azure (the "Lightweight" version) |

## 1. What Nestlé must see, and where we stand

The full wording and the evidence each item needs are in the [trial scorecard](https://github.com/brighthive/agentic-project-mgmt/blob/master/clients/trials/nestle/scorecard.md#proposed-acceptance-criteria) (ids N-01 to N-08). The pilot tests are acceptance scenarios in the [pilot journeys spec](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md), under epic [BH-1255](https://brighthiveio.atlassian.net/browse/BH-1255).

A passing pilot test is necessary but not enough. Nestlé still has to agree the target and sign it off.

**Status key:** 🟡 test exists, needs input from Nestlé · 🔴 no test or no proof yet

| # | What Nestlé would see | Pilot test that proves it | Jira work | Status | Next step |
|---|---|---|---|---|---|
| N-01 | A trusted data product built from a written specification, by an agreed deadline | [Specification to verified output](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-02-specification-to-verified-output) | None yet | 🟡 | Nestlé gives today's cycle time as the baseline |
| N-02 | Quality monitoring that catches problems on their most important data | [Recurring quality coverage](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-03-recurring-quality-coverage), [Truthful scheduled outcomes](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-01-truthful-scheduled-outcomes) | None yet | 🟡 | Nestlé names the critical data and the problems to catch |
| N-03 | A real failure diagnosed and repaired, with human approval | [Reviewed remediation](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-04-reviewed-remediation) | None yet | 🔴 | Weakest area: we have no proof yet. Run it before promising it. |
| N-04 | Recurring work that runs on its own and cuts manual effort | [Managed recurring work](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-05-managed-recurring-work) | [BH-1652](https://brighthiveio.atlassian.net/browse/BH-1652) (Azure scheduling only) | 🟡 | Nestlé picks one recurring task and how its effort is measured today |
| N-05 | Access, write and classification rules enforced, with an audit trail | [Enforced governance](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-06-enforced-governance) | None yet | 🟡 | Nestlé states the rules to enforce |
| N-06 | Real usage and cost figures that support an expansion decision | None | None yet ([BH-1657](https://brighthiveio.atlassian.net/browse/BH-1657) covers Bedrock cost controls and overlaps) | 🔴 | We cannot attribute cost per workspace today. Decide whether this stays in scope. |
| N-07 | Alerts a business user can act on without reading technical detail | [Actionable notification](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-07-actionable-notification-with-verified-context) | [BH-1654](https://brighthiveio.atlassian.net/browse/BH-1654) (Azure private-network alerts only) | 🟡 | Name who receives alerts and who approves actions. The earlier Slack test did not count. |
| N-08 | The next Nestlé division can run within agreed reliability and support limits | None | None yet | 🔴 | Cannot be tested until a division is enrolled |

The pilot tests were last run on 7 October on the AWS staging environment, not on Azure.

## 2. The Azure work, grouped by what it does

Alignment ids (NZ-0 to NZ-9) come from the [October alignment doc](https://github.com/brighthive/agentic-project-mgmt/blob/master/clients/ALIGNMENT_2026-10.md). AKS is Azure Kubernetes Service, the managed place containers run. ACR is Azure Container Registry, where built images are stored.

| Group | Ticket | Plain-language description | Alignment id |
|---|---|---|---|
| **Decide** | [BH-1641](https://brighthiveio.atlassian.net/browse/BH-1641) | Decision record: run the agent engine (LangGraph) ourselves on AKS instead of the hosted service | NZ-0 |
| **Package and deploy** | [BH-1642](https://brighthiveio.atlassian.net/browse/BH-1642) | One installable package (a Helm chart) for the agents, tool server and platform API on AKS | NZ-1 |
| | [BH-1643](https://brighthiveio.atlassian.net/browse/BH-1643) | Azure infrastructure module that deploys into Nestlé's existing Azure environment | NZ-2 |
| | [BH-1653](https://brighthiveio.atlassian.net/browse/BH-1653) | Build once and push to ACR without stored passwords | |
| **Connect to Azure services** | [BH-1644](https://brighthiveio.atlassian.net/browse/BH-1644) | Use Azure AI Foundry for the AI models | NZ-3 |
| | [BH-1645](https://brighthiveio.atlassian.net/browse/BH-1645) | Sign in with Nestlé's Microsoft accounts (Entra ID) and map their groups to roles | NZ-4 |
| | [BH-1646](https://brighthiveio.atlassian.net/browse/BH-1646) | Store files in Azure Blob, secrets in Key Vault, sessions in Postgres | NZ-5 |
| | [BH-1649](https://brighthiveio.atlassian.net/browse/BH-1649) | Read-only access to Nestlé's Synapse warehouse | NZ-8 |
| **Data services we run** | [BH-1647](https://brighthiveio.atlassian.net/browse/BH-1647) | The data catalog and search (OpenMetadata, OpenSearch) on AKS | NZ-6 |
| | [BH-1648](https://brighthiveio.atlassian.net/browse/BH-1648) | The graph database (Neo4j) with nightly backups | NZ-7 |
| | [BH-1651](https://brighthiveio.atlassian.net/browse/BH-1651) | Redis, used for retrieval and tool state | |
| **Run and watch** | [BH-1650](https://brighthiveio.atlassian.net/browse/BH-1650) | Logs and alerts in Azure Monitor, with outside telemetry switched off | NZ-9 |
| | [BH-1652](https://brighthiveio.atlassian.net/browse/BH-1652) | Scheduled agents as AKS scheduled jobs, with a failure alert | |
| | [BH-1654](https://brighthiveio.atlassian.net/browse/BH-1654) | Alerts that still reach people on a private-only network | |
| **Later** | [BH-1655](https://brighthiveio.atlassian.net/browse/BH-1655) | Hardening after the pilot, deferred from the first slim version | |

Where the code needs to change so each of these is an adapter and not a rewrite: [cloud-agnostic adapters spec](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/cloud-agnostic-adapters.md).
