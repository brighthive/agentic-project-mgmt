---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "trial"
champion: "Grant Langseth"
champion_email: ""
trial_start: "2026-06-TBD"
trial_end: "2026-06-TBD+14d"
decision_date: "2026-06-TBD+14d"
jira_epic: "BH-526"
notion_page: ""
workspace_id: ""
aws_account: ""
status: "pre-trial"
tags: [financial-services, snowflake, dbt, dagster, github-enterprise, mcp]
last_reviewed: "2026-05-29"
---

# Longaeva Partners LP — Trial

## What They Need (Their Words)

Longaeva's POC scope (full text in `artifacts/poc-scope-from-client.md`):

### Core (gating evaluation criteria)

1. **Ingestion — 3 source patterns**
   - **S3 vendor bucket** — given S3 creds + sample schema, scaffold Snowflake external stage + dbt source. Files: CSV/Parquet, daily-partitioned, 10K–100M rows.
   - **REST API** — paginated, date-partitioned, batched ID lookups against their 20-30k instrument universe; parallel download; retry; dbt source wiring.
   - **Snowflake Data Share** — given share DB name + target schema, scaffold dbt source + staging model + DQ contracts.

2. **Snowflake Semantic View Enrollment** — scaffold YAML against their **custom-extended schema** (extends Snowflake's spec with metric-store wiring, named reusable filter presets, plain-language agent context instructions, verified query examples). Specific reference-data joins required:
   - **Fiscal calendar tables** — for non-standard fiscal year alignment
   - **Identifier mapping** — LEI / FIGI → their internal issuer ID
   - **Geographic + classification code tables**
   - Brighthive must auto-detect when joins are needed and emit correct relationship definitions.

3. **MCP Feedback Loop** — after enrollment, validate the semantic view is **queryable through their internal MCP server** (not ours). Confirm measures/dimensions/time-dimensions surface; run representative queries (filtered, aggregated, multi-dim slice); identify gaps that would degrade agent quality (missing sample values, missing examples, missing instructions).

4. **Automated Maintenance** — explicit in-scope, evaluation criteria:
   - **Self-healing pipelines** — autonomously diagnose + open scoped surgical PR for these failure modes: schema drift from a vendor, missing partition, broken external stage, dbt model failing a contract.
   - **Longitudinal anomaly monitoring** — track over time, not pass/fail: row-count vs historical, dimension cardinality breakdowns, distributional skew in numeric metrics, unexpected nulls in well-populated columns.
   - **Slack alerting** — pipeline health, DQ violations, anomaly detections delivered to Slack channels with enough context (dataset, issue nature, severity, PR/run-log link) to triage without leaving Slack.
   - **Slack bidirectional** — engineers/data scientists can talk to BrightAgent in Slack to ask pipeline state, request re-runs, trigger scaffolding workflows.

### Bonus (non-gating but valued)

- **B.1 Unified vendor + dataset registry** — active contracts, team consumption, pipeline health/SLA, consolidation opportunities, lightweight vendor CRM layer (contacts, comms history, renewal dates).
- **B.2 Agentic governance** — how agents inherit permissions vs scoped subsets; runaway query prevention; consistent access semantics across warehouse + transactional + 3rd-party APIs; data contract / lineage enforcement when agents (not humans) initiate operations.
- **B.3 Hosted semantic layer + knowledge graph** — how Brighthive's managed graph instance complements their early-stage internal KG efforts. Specifically: enterprise ontology establishment + enrichment, grafting their entity subgraphs (instruments, counterparties, vendors) onto the base model, exposing the graph via MCP so other agents in their orchestration layer can consume it. Key eval criterion: **does this compress months of in-house infra work into immediately production-ready deployment?**
- **B.4 Rapid DQ test construction at scale** — beyond trial, continuously enforce quality across their full vendor portfolio (auto-generating + maintaining test suites as datasets evolve), not manual authoring per source.

### Participants

5 people: Grant + 1-2 data engineers + 1-2 data scientists.

Full honest capability map: `../../../../platform-saas-ai-context/clients/longaeva/capability-map.md`

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

### 1. Ingestion (3 source types)
- [ ] **S3**: Snowflake external stage SQL + dbt `sources.yml` generated; merge-ready with ≤1 revision
- [ ] **REST API**: connector handles their 20-30k instrument universe — pagination, batched ID lookups, parallel download, retry; dbt source wired
- [ ] **Snowflake Data Share**: dbt source + staging model SQL + DQ contracts generated; staging model passes first validation

### 2. Semantic View Enrollment
- [ ] YAML scaffold infers ≥80% of dimensions, time-dimensions, facts, metrics from Silver schema + plain-language description
- [ ] Custom metadata blocks (metric-store wiring, filter presets, agent instructions, verified queries) populated against Longaeva's extended schema
- [ ] Reference joins auto-detected — at least 2 of 3 types: **fiscal calendar**, **LEI/FIGI → internal issuer ID**, **geographic codes**
- [ ] Generated definition compiles + executes against Snowflake's semantic view engine within ≤3 revision cycles
- [ ] Compilation errors surface with actionable remediation messages

### 3. MCP Validation *(via Longaeva's internal MCP server)*
- [ ] All measures, dimensions, time-dimensions queryable through their MCP interface
- [ ] Representative query suite passes — filtered, aggregated, multi-dimension slice
- [ ] Quality gaps detected automatically: missing sample values, absent query examples, missing plain-language instructions — surfaced in the enrollment PR

### 4. Automated Maintenance

#### 4a. Self-Healing — must demonstrate on all 4 failure modes:
- [ ] **Schema drift** from vendor changing delivery format → diagnosed + surgical fix PR (not a rewrite)
- [ ] **Missing partition** → detected + fix PR with plain-language explanation
- [ ] **Broken external stage** → root cause identified + corrected DDL in PR
- [ ] **dbt contract failure** → contract analyzed + model or contract update PR

#### 4b. Longitudinal Anomaly Monitoring — track over time, not pass/fail:
- [ ] **Row count drift** vs historical baseline (specific window TBD with Grant)
- [ ] **Cardinality breakdown** on key dimensions (e.g. sudden drop in distinct geographies)
- [ ] **Distributional skew** in numeric metrics vs trailing window
- [ ] **Unexpected nulls** in typically-well-populated columns

#### 4c. Slack
- [ ] Alerts include dataset, issue nature, severity, PR/run-log link — triageable without leaving Slack
- [ ] Bidirectional: engineer can `@brightagent` to ask pipeline state, request re-run, trigger scaffolding workflow

### Bonus (optional; pursued only if core finishes early)
- [ ] **B.1** Vendor + dataset registry demo against ≥3 active datasets
- [ ] **B.2** Agentic governance: agent permission model walkthrough vs human inheritance
- [ ] **B.3** Hosted KG: subgraph grafting demo with their instruments/counterparties; MCP exposure verified
- [ ] **B.4** Rapid DQ test construction at scale demo

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

| # | Blocker | Owner | Raised | Status |
|---|---|---|---|---|
| 1 | Confirm exact June trial start date with Grant | Kuri | 2026-05-29 | 🚧 Open |
| 2 | Snowflake connectivity layer — `SnowflakeConnection` factory class | Brighthive eng | 2026-05-28 | 🚧 BH-526 |
| 3 | MCP client config for Longaeva's MCP server — confirm protocol, scope | Brighthive eng | 2026-05-28 | 🚧 BH-526 |
| 4 | GitHub Enterprise host config (`base_url`) — 1 day | Brighthive eng | 2026-05-28 | 🚧 BH-526 |
| 5 | GX output: YAML to repo, not Markdown to S3 — 2-3 days | Brighthive eng | 2026-05-28 | 🚧 BH-526 |
| 6 | Snowflake semantic view YAML scaffold tool — 1 sprint | Brighthive eng | 2026-05-28 | 🚧 BH-526 |
| 7 | dbt schema.yml test generation — currently absent in dbt agent | Brighthive eng | 2026-05-29 | 🆕 |
| 8 | Schema drift detection for self-healing PR loop — currently a Gap | Brighthive eng | 2026-05-29 | 🆕 |
| 9 | Longitudinal anomaly monitoring — quality agent is stateless today | Brighthive eng | 2026-05-29 | 🆕 |
| 10 | Dagster integration (vendor uses Dagster, not Airflow) — zero code refs | Brighthive eng | 2026-05-29 | 🆕 |
| 11 | Grant's email not confirmed | Kuri | 2026-05-28 | 🚧 Open |
| 12 | Trial-user list (the 1-2 DE + 1-2 DS) — to confirm with Grant | Kuri | 2026-05-29 | 🚧 Open |

## Decision

*Filled at Day 14.*

**Outcome**: —
**Rationale**: —
**Next Steps**: —
