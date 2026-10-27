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

## Azure tickets under BH-1640

| Ticket | Slice | Extends |
|---|---|---|
| BH-1641 | NZ-0 decision record: self-hosted LangGraph on AKS (Azure Kubernetes Service) | Orchestrator runtime |
| BH-1642 | NZ-1 one Helm chart for agents, MCP server, platform API | Deploy |
| BH-1643 | NZ-2 Azure infrastructure module for Nestlé's landing zone | Provisioning |
| BH-1644 | NZ-3 model-provider port and Azure AI Foundry adapter | `custom_llms/model_provider.py` |
| BH-1645 | NZ-4 Entra ID token validation, group-to-role mapping | Identity |
| BH-1646 | NZ-5 Blob, Key Vault, Postgres adapters | `backends/`, secrets |
| BH-1647 | NZ-6 OpenMetadata and OpenSearch on AKS | Catalog |
| BH-1648 | NZ-7 Neo4j StatefulSet with nightly backup | Graph |
| BH-1649 | NZ-8 read-only Synapse with managed identity | `tools/warehouse_connections.py` (Synapse exists) |
| BH-1650 | NZ-9 container logs and Azure Monitor alerts | Observability |
| BH-1651 | Redis Stack in AKS | Runtime |
| BH-1652 | Scheduled agents as AKS CronJobs | Scheduling |
| BH-1653 | Build once, push to ACR (Azure Container Registry), no stored keys | CI |
| BH-1654 | Alert delivery in a private-only network | Alerts |
| BH-1655 | Hardening after the pilot | Deferred |

Where the adapters go and the AWS-only cleanups that must come first: [cloud-agnostic adapters spec](../../../docs/specs/cloud-agnostic-adapters.md).

## Scorecard coverage

| Criterion | Journey (epic BH-1255) | Ticket | State |
|---|---|---|---|
| N-01 spec to data product | J1 | none | Needs client baseline |
| N-02 quality | J2 | none | Needs client baseline |
| N-03 reviewed repair | J3 | none | Weakest; no proof |
| N-04 recurring automation | J4 | BH-1652 (Azure only) | Open |
| N-05 governance | J5 | none | Open |
| N-06 cost and usage | none | none (BH-1657 overlaps) | No capability today |
| N-07 actionable alert | cross-cutting | BH-1654 (Azure only) | Open |
| N-08 next-division readiness | none | none | Untestable until a division is enrolled |

Journey evidence dates from 2026-10-07 and was captured on AWS staging.
