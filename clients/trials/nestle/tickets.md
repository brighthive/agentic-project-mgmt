---
name: "Nestlé tickets"
slug: "nestle"
jira_epic: "BH-1639"
last_reviewed: "2026-10-27"
---

# Nestlé tickets

Jira is the source of truth for status. Every ticket below was in **Needs Refinement** on 2026-10-27; none had started.
Epic list: <https://brighthiveio.atlassian.net/issues/?jql=project%3DBH%20AND%20issuetype%3DEpic%20ORDER%20BY%20created%20DESC>

## Epics

| Epic | Scope |
|---|---|
| [BH-1639](https://brighthiveio.atlassian.net/browse/BH-1639) | Nestlé trial: six-week global expansion |
| [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640) | Azure private deployment (Lightweight) |

## Azure tickets under [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640)

| Ticket | Slice | Extends |
|---|---|---|
| [BH-1641](https://brighthiveio.atlassian.net/browse/BH-1641) | NZ-0 decision record: self-hosted LangGraph on AKS (Azure Kubernetes Service) | Orchestrator runtime |
| [BH-1642](https://brighthiveio.atlassian.net/browse/BH-1642) | NZ-1 one Helm chart for agents, MCP server, platform API | Deploy |
| [BH-1643](https://brighthiveio.atlassian.net/browse/BH-1643) | NZ-2 Azure infrastructure module for Nestlé's landing zone | Provisioning |
| [BH-1644](https://brighthiveio.atlassian.net/browse/BH-1644) | NZ-3 model-provider port and Azure AI Foundry adapter | `custom_llms/model_provider.py` |
| [BH-1645](https://brighthiveio.atlassian.net/browse/BH-1645) | NZ-4 Entra ID token validation, group-to-role mapping | Identity |
| [BH-1646](https://brighthiveio.atlassian.net/browse/BH-1646) | NZ-5 Blob, Key Vault, Postgres adapters | `backends/`, secrets |
| [BH-1647](https://brighthiveio.atlassian.net/browse/BH-1647) | NZ-6 OpenMetadata and OpenSearch on AKS | Catalog |
| [BH-1648](https://brighthiveio.atlassian.net/browse/BH-1648) | NZ-7 Neo4j StatefulSet with nightly backup | Graph |
| [BH-1649](https://brighthiveio.atlassian.net/browse/BH-1649) | NZ-8 read-only Synapse with managed identity | `tools/warehouse_connections.py` (Synapse exists) |
| [BH-1650](https://brighthiveio.atlassian.net/browse/BH-1650) | NZ-9 container logs and Azure Monitor alerts | Observability |
| [BH-1651](https://brighthiveio.atlassian.net/browse/BH-1651) | Redis Stack in AKS | Runtime |
| [BH-1652](https://brighthiveio.atlassian.net/browse/BH-1652) | Scheduled agents as AKS CronJobs | Scheduling |
| [BH-1653](https://brighthiveio.atlassian.net/browse/BH-1653) | Build once, push to ACR (Azure Container Registry), no stored keys | CI |
| [BH-1654](https://brighthiveio.atlassian.net/browse/BH-1654) | Alert delivery in a private-only network | Alerts |
| [BH-1655](https://brighthiveio.atlassian.net/browse/BH-1655) | Hardening after the pilot | Deferred |

Where the adapters go and the AWS-only cleanups that must come first: [cloud-agnostic adapters spec](../../../docs/specs/cloud-agnostic-adapters.md).

## What Nestlé must see, and where we stand

Eight things we propose Nestlé judges the trial on. The full wording, with the evidence each one needs, is in the [trial scorecard](https://github.com/brighthive/agentic-project-mgmt/blob/master/clients/trials/nestle/scorecard.md#proposed-acceptance-criteria) (its ids are N-01 to N-08). Each row below says what Nestlé would see, which pilot test proves it, which Jira work exists, and where it stands.

The "pilot test" column links to the acceptance scenarios in the [pilot journeys spec](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md), which belongs to epic [BH-1255](https://brighthiveio.atlassian.net/browse/BH-1255). A passing pilot test is necessary but not enough: Nestlé still has to agree the target and sign it off.

| What Nestlé would see | Pilot test that proves it | Jira work | Where we stand |
|---|---|---|---|
| A trusted data product built from a written specification, by an agreed deadline (N-01) | [Specification to verified output](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-02-specification-to-verified-output) | None yet | Needs Nestlé's current cycle time as a baseline |
| Quality monitoring that catches problems on their most important data (N-02) | [Recurring quality coverage](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-03-recurring-quality-coverage), [Truthful scheduled outcomes](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-01-truthful-scheduled-outcomes) | None yet | Needs the list of critical data and a baseline |
| A real failure diagnosed and repaired with human approval (N-03) | [Reviewed remediation](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-04-reviewed-remediation) | None yet | Weakest area: no proof yet |
| Recurring work that runs on its own and cuts manual effort (N-04) | [Managed recurring work](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-05-managed-recurring-work) | [BH-1652](https://brighthiveio.atlassian.net/browse/BH-1652) (Azure scheduling only) | Open |
| Access, write and classification rules enforced, with an audit trail (N-05) | [Enforced governance](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-06-enforced-governance) | None yet | Open |
| Real usage and cost figures to support an expansion decision (N-06) | None: no pilot test exists | None yet; [BH-1657](https://brighthiveio.atlassian.net/browse/BH-1657) (Bedrock cost controls) overlaps | We cannot attribute cost per workspace today |
| Alerts a business user can act on without reading technical detail (N-07) | [Actionable notification](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/mcp-pilot-journeys.md#ac-pilot-07-actionable-notification-with-verified-context) | [BH-1654](https://brighthiveio.atlassian.net/browse/BH-1654) (Azure private-network alerts only) | Open; earlier Slack test did not count |
| The next Nestlé division can run within agreed reliability and support limits (N-08) | None: no pilot test exists | None yet | Cannot be tested until a division is enrolled |

The pilot tests were last run on 7 October, on the AWS staging environment, not on Azure.
