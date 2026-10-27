---
name: "ACG"
slug: "acg"
stage: "lead"
champion: "John Sutton"
champion_email: ""
first_contact: "2026-07"
jira_epic: "BH-1658"
status: "active"
tags: [acg, lead, azure, vendor-feeds, ssis, asset-management]
---

# ACG: lead

Registered investment adviser (RIA) that has just moved off Guggenheim-hosted infrastructure into its own Azure tenant. Source: the July 2026 proposal that followed the first call. Nothing here is confirmed by ACG in writing.

## Contacts

| Name | Role | Notes |
|---|---|---|
| John Sutton | CTO, champion | Wants cleaner, faster vendor data without building a data team |
| Suzanne El-Moursi | CEO and co-founder, Brighthive | Owns the relationship; ran the first call |
| Diane | Leads the reporting team | Wants reconciliation and performance-anomaly detection. Surname and role to confirm. |

## Fit hypothesis

**Their pain:** vendor data (Advent APX, eVestment, FactSet, Morningstar, Bloomberg) arrives through slow, fragile FTP and SSIS feeds. They want fewer people chasing bad records and a morning list of exceptions. They plan to retire SSIS and SSRS for Data Factory and a cloud warehouse in 2026 to 2027.

**Why Brighthive:** the SSIS/SSRS diagnosis skill, data quality agent, scheduled monitoring and the governed dbt fix flow match the pain. The first gap is the environment: ACG is on Azure and the platform runs on AWS today.

**Qualification signals**
- [ ] Budget authority confirmed
- [ ] Decision timeline known
- [x] Technical champion engaged (John Sutton)
- [ ] Stack is compatible (Azure tenant, warehouse not chosen yet)

## Their stack (known)

| Layer | Technology | Source |
|---|---|---|
| Cloud | Own Azure tenant, isolated | First call |
| Vendor data in | FTP and SSIS feeds from the five vendors above | First call |
| Reporting | SSRS | First call |
| Target stack | Evaluating Azure Data Factory, Snowflake, Databricks | First call |
| Source control | Unknown | |
| Orchestration | Unknown | |

## What the proposal promises, and what exists today

Checked against brightbot `origin/develop` on 2026-10-27; paths are under `brightbot/brightbot/`. Fix the wording before anything goes to ACG again.

| The proposal says | What the code shows | Verdict |
|---|---|---|
| 650+ connectors, custom builds on demand | Ingestion runs through Airbyte, with a custom-connector agent (`agents/airbyte_custom_agent`). No eVestment, FactSet, Morningstar, Bloomberg or Advent connector code exists in our repos; the only hit is a `bloomberg_ticker` column-name pattern (`agents/dbt_agent/tools/atlas_semantic_view/constants.py:50,71`). Whether Airbyte's catalog covers them is unchecked. | Verify each vendor before promising |
| Great Expectations runs in the ingestion agent | It runs in the quality agent (`agents/governance_agent/sub_agents/quality_check_agent.py:91`, `agents/governance_agent/tools/quality_tools.py:18`), not in `ingestion_agent` | Partly true; reword |
| Schema profile, drift and quality score on every dataset at ingestion | `data_profiler_agent` and `schema_agent` exist. Automatic scoring at ingestion is not verified. | Verify |
| 7 agents plus a supervisor | 21 deployed graphs, counting scheduled tasks; the supervisor is `superduper_agent` / `deep_agent`. "7" is not a code concept. | Reword |
| "Night Shift" agent | No such agent. The real ones: `pipeline_watchdog_task`, `fleet_health_digest_task`, `profiler_task`, `quality_check_task`. | Rename to what exists |
| Morning list in Slack, Teams, MCP or inbox | Slack delivery and MCP read-back work. Teams is a read-only tool in the Slack router (`agents/slack_router_agent/intent_classifier.py:23`, `mcp_tool_node.py:1`), with no delivery code. The webapp inbox was flag-gated off in our June notes. | Teams and inbox not available |
| Agent writes SQL or dbt and commits to GitHub | dbt agent has GitHub commit tooling (`agents/dbt_agent/tools/github_commit_resolve.py`) | Supported, through a reviewed pull request |
| Works with Data Factory | Snowflake, Databricks, Synapse, Postgres and Redshift connections exist (`utils/warehouse_types.py:22-26`). No Data Factory code (0 matches). | Not supported |
| SSIS/SSRS diagnosis skill | `agents/analyst_agent/ssis_remediation_agent.py:104` and pipeline diagnostics tools exist, and shipped for another client | Supported. Do not name the other client. |
| Single tenant, own S3 bucket via AWS Bedrock, "full model copy in your environment" | A per-workspace bucket in the customer's AWS account through a cross-account role exists. ACG is on Azure. Nothing in our code or docs supports a model copy, and we know of no Bedrock feature for it. | Contradicts their Azure tenant; do not repeat the model-copy claim |
| Deployable in ACG's environment | AWS only today. Azure work is planned under [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640) for Nestlé. | Same blocker as Nestlé |

## Red team

- **The environment decides everything.** If ACG's security rules require data to stay in its Azure tenant, nothing runs until the Azure adapters exist. The Nestlé plan has 17 unstarted tickets for that.
- **A regulated RIA will ask about the model-copy sentence.** A claim we can't support is worse than a missing feature. Strike it.
- **The demo date has passed.** The proposal set a technical demo for Tuesday 14 July 2026. Its outcome is not recorded anywhere.
- **Reusing the Chicago asset manager as a reference** discloses another client's work. Get that client's consent or drop it.
- **Vendor feeds are the unproven centre.** We have no vendor-specific proof, so the first slice picks one feed and proves it.

## First call notes

**Date:** July 2026 (exact date unknown)

**What they said:** wants vendor data faster and cleaner; sees data quality as AI's biggest advantage; wants exception management ("what do I need to focus on this morning"); does not want to build a data team; plans to leave SSIS and FTP; just moved to an isolated Azure tenant.

**What we said:** the proposal above, including the 14 July technical demo.

**Open questions**
- What happened at the 14 July demo?
- Must data stay in ACG's Azure tenant? Is an AWS account acceptable at all?
- Which warehouse will ACG choose (Snowflake, Databricks, Synapse)?
- Which one vendor feed hurts most, and who owns it?
- What do they measure today (hours spent chasing bad records, feed lateness)?
- Who signs, and when do they decide?

## Next step

**Action:** confirm the demo outcome and the Azure-tenant rule with John Sutton, then agree one vendor feed for a first proof. See the [roadmap](roadmap.md), the [tickets](tickets.md) (epic [BH-1658](https://brighthiveio.atlassian.net/browse/BH-1658)) and the [pilot spec](../../../docs/specs/acg-vendor-data-pilot.md).
**Owner:** Suzanne El-Moursi (relationship), Kuri (technical plan)
**By:** to set
