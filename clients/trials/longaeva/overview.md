---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "trial"
champion: "Grant Langseth"
champion_email: ""
trial_start: "2026-05-26"
trial_end: "2026-06-09"
decision_date: "2026-06-09"
jira_epic: "BH-526"
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [financial-services, snowflake, dbt, dagster, github-enterprise, mcp]
---

# Longaeva Partners LP — Trial

## What They Need (Their Words)

Longaeva has four questions:

1. **Ingestion** — Given credentials and a schema, can Brighthive scaffold the full pipeline (Snowflake stage config, dbt source, quality contracts) for three vendor patterns: S3, REST API, Snowflake Data Share?

2. **Semantic Enrollment** — Can Brighthive reduce the friction of enrolling a curated Silver table into their Snowflake semantic view layer — handling YAML scaffolding, reference join detection, and validation?

3. **MCP Validation** — After enrollment, can Brighthive confirm the semantic view is queryable through their internal MCP server and surface any gaps in the definition?

4. **Automated Maintenance** — Schema drift detection, auto-generated quality tests, longitudinal anomaly monitoring, and Slack-native triage + interaction.

Full capability map: `../../../../platform-saas-ai-context/clients/longaeva/capability-map.md`

## Contacts

| Name | Role | Email |
|---|---|---|
| Grant Langseth | Champion, technical decision-maker | — |
| TBC | Data engineering | — |
| TBC | Data science | — |

5 participants total (Grant + 1-2 data engineers + 1-2 data scientists).

## The Gap to Resolve Before Day 1

**Brightbot's SQL execution layer does not connect to Snowflake today.**

The Snowflake connection params are already modelled (`SnowflakeConnectionParams`
in `query_retrieval.py`) and env vars are read (`warehouse.py:337`). But the
`WarehouseConnectionFactory` only has `"redshift"` and `"azure_synapse"` in
`CONNECTION_CLASSES` — Snowflake is parsed but never executed. Any attempt to
run SQL against Snowflake currently raises `ValueError`.

This is closer than a full sprint: the plumbing exists, the factory just needs a
`SnowflakeConnection` class wired in. Realistic estimate: **1-2 weeks of
engineering**, not 1-2 months. But it must happen before the trial — not during it.

**Options before signing the trial SOW:**

| Option | What it means |
|---|---|
| **A — Pre-trial sprint** | Brighthive completes Snowflake connectivity layer (2-3 weeks) before trial starts. Trial runs on solid ground. Recommended. |
| **B — Scoped trial** | Trial proceeds with Sections 3 and 4 (monitoring, Slack, KG) which are production-ready. Sections 1 and 2 are treated as a co-development engagement with working prototypes by Day 8. Honest with Grant about the difference. |
| **C — Trial as-is** | Start Day 1 without Snowflake layer. Risk: Sections 1 and 2 fail or disappoint on Day 6-8 when dependencies surface. Not recommended. |

## What Is Genuinely Production-Ready Today

These deliver real value with zero engineering pre-work:

- **Schema drift detection + alerting** — GA since Feb 2026
- **BrightSignals Slack notifications** — shipped Sprint 9, 9 PRs merged
- **BrightAgent bidirectional Slack** — Socket Mode, multi-tenant auth confirmed
- **Data lineage + consumption registry** — OpenMetadata + Governance Agent
- **Neo4j KG + MCP server** — per-workspace, external agents consuming today
- **dbt model SQL generation + GitHub PR** — real code, needs GHE config (1 day)
- **GX quality suite generation** — real code, needs output format fix (2-3 days)
- **Longitudinal anomaly monitoring** — Platform Analytics Dashboard, production

## Pre-Trial Engineering Checklist

| Task | Effort | Blocks | Status |
|---|---|---|---|
| `SnowflakeConnection` in warehouse factory (plumbing exists, factory missing) | 1-2 days | Sections 1 + 2 | 🔲 |
| Snowflake schema introspection via INFORMATION_SCHEMA | 2-3 days | 1.1, 1.3, 2.3 | 🔲 |
| Snowflake semantic view YAML scaffolding tool | 1 sprint | Section 2 | 🔲 |
| dbt sources.yml generation from scratch (not just update) | 3-4 days | 1.1, 1.3 | 🔲 |
| GX output: write YAML to repo branch, not Markdown to S3 | 2-3 days | 1.3, 4.2 | 🔲 |
| GitHub Enterprise `base_url` config (one param) | 1 day | All PR creation | 🔲 |
| MCP client status — confirm or scope sprint | Confirm first | Section 3.1 | 🔲 |

## Context Setup (Days 1-5)

Quality of YAML scaffolding and join inference depends on what gets loaded here.
This is the most important prep work of the trial after pre-trial engineering is done.

| What | Why it matters | Owner | By |
|---|---|---|---|
| Longaeva's custom YAML schema spec | Agent generates to their extended spec, not base Snowflake spec | Longaeva | Day 3 |
| Fiscal calendar table schema + sample rows | Fiscal join detection | Longaeva | Day 3 |
| LEI / FIGI → internal issuer ID mapping schemas | Identifier join detection | Longaeva | Day 3 |
| Existing dbt project structure + naming conventions | Generated artifacts match their conventions | Longaeva | Day 3 |
| Dagster lineage (OpenLineage export or direct) | Observability Agent reads failures in context | Longaeva | Day 4 |
| Sample vendor datasets (one per source type) | Ingestion scaffolding reference | Longaeva | Day 5 |
| 2 existing production semantic view definitions | Style examples for YAML generation | Longaeva | Day 5 |

Day 3 has five Longaeva-owned items. Schedule a joint working session — not an async handoff.

## Success Criteria

### Ingestion
- [ ] S3: dbt source YAML + Airbyte connection generated, merge-ready with ≤1 revision
- [ ] REST API: Airbyte connector handles 20-30k instrument universe, pagination, retry
- [ ] Data Share: staging model SQL + GX contracts pass first validation

### Semantic Enrollment
- [ ] YAML scaffold infers ≥80% of dimensions and metrics (with engineer iteration)
- [ ] At least one reference join (fiscal calendar or identifier mapping) detected and surfaced
- [ ] Generated definition compiles against Snowflake within ≤3 revision cycles

### MCP Validation *(contingent on MCP client confirmation)*
- [ ] Enrolled semantic view queryable through Longaeva's MCP interface
- [ ] Representative queries return correct results
- [ ] Gaps surfaced automatically and included in the PR

### Automated Maintenance
- [ ] Schema drift event triggers detection and fix PR in the same pipeline run cycle
- [ ] Slack alert has dataset, severity, and PR link — triageable without leaving Slack

## Milestone Tracker

| # | Milestone | Owner | Day | Status | Notes |
|---|---|---|---|---|---|
| 1 | Use cases confirmed + Jira epic created | Joint | 1 | 🔲 | Pre-trial eng scope confirmed here |
| 2 | System access (Snowflake, S3, dbt, GHE, MCP) | Longaeva | 2 | 🔲 | |
| 3 | BH environment setup + Snowflake connectivity validated | Brighthive | 3 | 🔲 | |
| 4 | Context layer (ref schemas, YAML spec, dbt, Dagster lineage) | Joint | 5 | 🔲 | Joint session, not async |
| 5 | Environment mapping validated | Joint | 5 | 🔲 | |
| 6 | Ingestion execution (3 source types) | Joint | 8 | 🔲 | |
| 7 | Semantic view enrollment + MCP validation | Joint | 10 | 🔲 | |
| 8 | Automated maintenance demo (deliberate drift event) | Joint | 12 | 🔲 | |
| 9 | Final scorecard | Joint | 13 | 🔲 | |
| 10 | Next steps | Brighthive | 14 | 🔲 | |

Status: 🔲 Pending / 🔄 In Progress / ✅ Done / ⚠️ Blocked

## Open Blockers

| # | Blocker | Owner | Raised |
|---|---|---|---|
| 1 | Jira epic not created | Kuri | 2026-05-28 |
| 2 | Snowflake connectivity layer — engineering sprint required | Brighthive eng | 2026-05-28 |
| 3 | MCP client-side implementation status — confirm or scope sprint | Brighthive eng | 2026-05-28 |
| 4 | GitHub Enterprise host config — 1-day task before any PR creation | Brighthive eng | 2026-05-28 |
| 5 | GX output format — 2-3 day task to write YAML to repo | Brighthive eng | 2026-05-28 |
| 6 | Grant's email not confirmed | Kuri | 2026-05-28 |

## Decision

*Filled at Day 14.*

**Outcome**: —
**Rationale**: —
**Next Steps**: —
