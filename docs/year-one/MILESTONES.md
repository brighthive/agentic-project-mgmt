# Milestones: Epics Kuri Led

24 of 40 epics with merged code are Kuri-led: 10 or more commits and a 50% or higher share. Source: `collect_milestones.py` → `data/milestones.json`. An epic's commits (code repos only, documentation repos excluded) are non-merge commits on develop, staging or a production branch whose message contains the key of the epic or of one of its child tickets. Kuri's commits are matched by author name or email. Kuri-led means 10+ commits and a 50%+ share. Commits are evidence of merged work, not proof an epic is complete.

## Epics, in the order work began

| Epic | What | Commits from → to | Commits | Kuri share | Tickets done | Repos |
|---|---|---|---|---|---|---|
| BH-172 | Platform Features & Enhancements | 2026-02-03 → 2026-10-12 | 134 | 91.8% | 50 of 132 | brightagent-v3, brightbot, data-organization-cdk |
| BH-111 | Proactive Multi Agents | 2026-02-03 → 2026-10-12 | 12 | 66.7% | 4 of 11 | brightbot, platform-core, webapp |
| BH-173 | Bugs & Fixes | 2026-03-10 → 2026-10-12 | 60 | 68.3% | 39 of 105 | brightbot, brightbot-slack-server, e2e |
| BH-117 | BH Omni integrations (Slack, Teams, Google) | 2026-03-16 → 2026-07-23 | 35 | 71.4% | 5 of 14 | brightbot-slack-server, e2e, platform-core |
| BH-359 | Platform Analytics, Monitoring & Reporting Dashboard | 2026-04-12 → 2026-10-12 | 43 | 88.4% | 1 of 19 | brightbot, e2e, platform-core |
| BH-260 | BrightStudio - AI-Powered Studio & Workspace Management | 2026-04-20 → 2026-07-21 | 10 | 90.0% | 11 of 22 | brightagent-v3, brightbot |
| BH-503 | Configurable Quality Agent — workspace rule library, curation, and his | 2026-05-27 → 2026-06-17 | 10 | 70.0% | 17 of 23 | brightbot, platform-core, webapp |
| BH-115 | Interconnect-ability: Source & Destinations (A2A) | 2026-06-03 → 2026-10-06 | 77 | 93.5% | 5 of 40 | brightagent-v3, brightbot, admin |
| BH-526 | Longaeva Partners POC — 14-day pre-trial execution | 2026-06-08 → 2026-10-13 | 74 | 98.6% | 3 of 62 | brightagent-v3, brightbot, data-organization-cdk |
| BH-601 | Longaeva PoC — 14 Golden Success Paths (GC-1..14) explicit tracking | 2026-06-08 → 2026-07-21 | 32 | 100.0% | 4 of 43 | brightagent-v3, brightbot, e2e |
| BH-624 | Semantic View Lifecycle: Read/Sync/Mirror/Write for Snowflake Tables | 2026-06-16 → 2026-07-21 | 27 | 96.3% | 2 of 26 | brightbot, e2e, platform-core |
| BH-695 | Engineering Agent Audit Trail — JWT-attributed tamper-evident action l | 2026-06-22 → 2026-07-21 | 18 | 100.0% | 0 of 16 | brightbot, e2e, platform-core |
| BH-876 | BrightRoutines — proactive schedule detection and workflow automation | 2026-07-02 → 2026-10-12 | 157 | 96.8% | 64 of 118 | brightagent-v3, brightbot, brightbot-slack-server |
| BH-1036 | Monitoring Agents — proactive pipeline discovery & health (dbt, Databr | 2026-07-13 → 2026-10-16 | 130 | 97.7% | 1 of 41 | brightbot, brightbot-slack-server, e2e |
| BH-1084 | Always-on PII enforcement across agent I/O (BH-1078 follow-through) | 2026-07-13 → 2026-07-23 | 19 | 94.7% | 0 of 3 | brightbot, platform-core |
| BH-1061 | Lineage-Aware Data Quality — glue dbt/Databricks' own lineage to pre-E | 2026-07-13 → 2026-10-13 | 18 | 100.0% | 1 of 12 | brightbot, brightbot-slack-server, platform-core |
| BH-1131 | On-Demand Alerts — agent-authored notification rules on the Signal Cat | 2026-07-19 → 2026-07-28 | 29 | 100.0% | 0 of 3 | brightbot, brightbot-slack-server, e2e |
| BH-1181 | MCP capability coverage & availability across environments | 2026-07-24 → 2026-10-14 | 85 | 100.0% | 15 of 72 | brightbot, e2e, platform-core |
| BH-1255 | Scheduled, Versioned, Lineage-Aware Pipeline Runs — configured & monit | 2026-07-29 → 2026-10-16 | 64 | 93.8% | 3 of 78 | brightbot, e2e, platform-core |
| BH-1168 | BUGS-V3 — BrightAgent v3 production bugs & e2e findings | 2026-07-31 → 2026-08-01 | 12 | 100.0% | 0 of 21 | brightbot, e2e |
| BH-1370 | Warehouse → Database → Table hierarchical identity | 2026-08-07 → 2026-10-12 | 17 | 100.0% | 0 of 28 | brightbot, e2e, platform-core |
| BH-1421 | On-Prem Engineering Runner — filesystem-resident dbt + legacy artifact | 2026-08-13 → 2026-10-12 | 21 | 100.0% | 4 of 30 | brightagent-engineering-runner, brightbot, e2e |
| BH-1403 | Autonomous dbt Project Lifecycle on On-Prem SQL Server — local dbt Cor | 2026-08-13 → 2026-10-12 | 15 | 100.0% | 4 of 19 | brightagent-engineering-runner, brightbot, platform-core |
| BH-1464 | Authorization & Governance Enforcement: configurable roles, per-resour | 2026-08-28 → 2026-10-12 | 74 | 97.3% | 0 of 57 | brightbot, e2e, platform-core |

## Epics started per month

| Month | Kuri-led epics started |
|---|---|
| 2026-02 | 2 |
| 2026-03 | 2 |
| 2026-04 | 2 |
| 2026-05 | 1 |
| 2026-06 | 5 |
| 2026-07 | 8 |
| 2026-08 | 4 |

## Limits

- "Tickets done" is Jira status, which lags delivery (see [JIRA.md](JIRA.md)).
- Commit share measures where the code came from, not who decided what to build.
- Epics under 10 commits or under 50% Kuri share are left out, not judged.
