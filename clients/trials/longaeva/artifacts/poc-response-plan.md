# POC Response Plan: Longaeva Partners
## Platform Capability Mapping & Technical POC Execution Strategy

| Field | Value |
|---|---|
| Prospect | Longaeva Partners LP |
| Champion | Grant Langseth |
| Trial Duration | 14 Days / 2 Weeks |
| Document Date | May 26, 2026 |

---

## Executive Summary

Longaeva Partners has issued a detailed, technically sophisticated POC specification covering five workstreams:
1. Multi-pattern data ingestion
2. Snowflake semantic view enrollment
3. MCP downstream validation
4. Automated pipeline maintenance
5. Proactive Slack-native alerting

This document maps each Longaeva POC requirement to specific Brighthive platform capabilities, identifies where the platform delivers full coverage, where execution depth is the differentiator, and where targeted configuration work will be needed.

**The core thesis**: Longaeva's stack — Snowflake on AWS, dbt, Dagster, GitHub Enterprise, and a custom MCP server — is the reference deployment model that Brighthive's Engineering Agent, Ingestion Agent, and Quality Agent were designed around. This is not a stretch. It is a fit.

**North Star**: A data scientist goes from "I have a curated Silver table" to "my semantic view is enrolled, validated, and ready for AI and analytics use" — in a single guided workflow, with Brighthive handling the scaffolding and validation steps and raising a pull request for engineering review.

---

## 1. Platform Capability Map

> For the version with feature doc links and honesty coverage tags, see:
> `../../../../../platform-saas-ai-context/clients/longaeva/capability-map.md`

**Coverage tags**:
- **Shipped** — production, in live deployments
- **Ready** — code exists, deployable with small config change
- **Sprint to close** — pre-trial engineering work (1-2 weeks, scoped in BH-526)
- **Partial** — works for adjacent scope, edge cases may need iteration

| ID | Longaeva Requirement | Brighthive Capability | Agent | Coverage | Sprint work to close before Day 1 |
|---|---|---|---|---|---|
| 1.1 | S3 — Snowflake external stage + dbt source | Ingestion Agent: 25 tools for Airbyte-managed S3 (credentials, sources, syncs, checkpoints). dbt agent emits `sources.yml`. PR-raised to GitHub. | Ingestion + Eng | **Ready** | Snowflake `CREATE STAGE` DDL generator tool — Airbyte path is shipped, external-stage path needs new tool. Confirm with Grant which pattern they want. |
| 1.2 | S3 lifecycle: completion-file detection, lookback windows, batch metadata | DynamoDB-backed checkpoint protocol (`ingestion_state.py`). Completion files, lookback, retries already modeled. | Ingestion | **Shipped** | — |
| 1.3 | REST API — paginated, date-partitioned, 20-30k instrument universe, retry, dbt wiring | Airbyte CDK + custom-connector scaffolder (`scaffold_custom_connector_tool`) generates 7-file Python project + Docker build + sandbox test + registration. dbt source wired. | Ingestion + Eng | **Ready** | Validate at 20-30k scale Day 5. Dagster `@asset` generation is a gap; their pattern uses Airbyte-equivalent. |
| 1.4 | Snowflake Data Share — dbt source + staging + DQ contracts | dbt agent generates source YAML + staging SQL; quality agent emits GX contracts. | Eng + Quality | **Sprint to close** | `SnowflakeConnection` factory class (`warehouse_connections.py:405`). Params already parsed; CONNECTION_CLASSES missing entry. ~1-2 days. |
| 2.1 | Semantic view YAML from Silver table + plain-lang description: dims, time-dims, facts, metrics, custom metadata | LLM-driven YAML generation against custom schema loaded into workspace context. | Engineering | **Sprint to close** | New semantic view scaffolding tool: reads Silver schema + their YAML spec from context, emits YAML against extended spec. ~1 sprint. |
| 2.2 | Reference joins: fiscal calendar, LEI/FIGI→issuer ID, geo/classification codes | KG-driven join detection from workspace reference schemas. | Eng + KG | **Ready** | Reference schemas (fiscal calendar, LEI/FIGI map, geo codes) loaded Days 3-5. Depends on 2.1 tool. |
| 2.3 | Validate semantic view compiles + executes on Snowflake; surface errors | Quality agent runs DDL + executes test queries; remediation messages from compile errors. | Quality + Eng | **Sprint to close** | Same `SnowflakeConnection` gap (1.4). `CREATE SEMANTIC VIEW` DDL execution path. |
| 3.1 | Measures/dims/time-dims queryable via Longaeva's internal MCP server | `BrightAgentMCPClient` wraps `langchain-mcp-adapters.MultiServerMCPClient`. | KG + Quality | **Sprint to close** | Add their MCP server endpoint + auth to `mcp_config.py`. 1-2 day config IF their server uses standard MCP protocol — confirm Day 1. |
| 3.2 | Representative query suite correctness (filtered, aggregated, multi-dim) | Quality agent runs test query suites; GX enforces correctness. | Quality | **Ready** | Depends on 3.1 connectivity. |
| 3.3 | Detect gaps degrading agent quality: missing samples / examples / instructions | Context-completeness scoring in workspace context file. | Eng + KG | **Ready** | Surfaced in enrollment PR — checklist format. |
| 3.4 | Single workflow: Silver table → enrolled, validated, PR-raised | Supervisor orchestrates: schema ingest → YAML scaffold → join resolution → validation → MCP check → PR. | Supervisor | **Ready** | Depends on 2.1, 2.3, 3.1 sprint work closing. |
| 4.1 | Self-healing: diagnose failure → surgical PR for schema drift / missing partition / broken stage / dbt contract fail | Observability agent + Engineering agent on alert → PR. | Observability + Eng | **Sprint to close** | Schema drift detection is currently a gap (zero matches for `schema_drift` in codebase). Detect→fix loop is not auto-triggered. ~1 sprint to wire the loop; drift detection itself can ride on schema-version comparison from KG. |
| 4.2 | Auto-author dbt test suites + GX contracts at enrollment | Quality agent emits GX YAML to repo. dbt `schema.yml` test generation is the gap. | Quality | **Sprint to close** | dbt schema.yml generator with `not_null`, `unique`, `accepted_values` inference. ~3-4 days. GX side is Ready (needs output-format fix to YAML-to-repo). |
| 4.3 | Longitudinal anomaly monitoring: row count / cardinality / skew / nulls vs trailing window | Quality agent today is stateless per run. Platform analytics dashboard tracks pass rates. | Quality + Analytics | **Sprint to close** | Persist per-run metrics as `QualityRuleExecutionNode` (already specced in BH-503 quality rules epic). Trend computation. ~1 sprint; can demo 1 anomaly category on Day 12 even if others stub. |
| 4.4 | Slack alerts: dataset + issue + severity + PR/run link | BrightSignals — shipped Sprint 9, 9 PRs merged. | BrightSignals | **Shipped** | Set `NOTIFICATIONS_ENABLED=true` for Longaeva workspace. |
| 4.5 | Slack bidirectional: pipeline state, re-run, scaffolding triggers from @mention | BrightAgent Slack integration, Socket Mode, multi-tenant auth. | BrightAgent | **Shipped** | — |
| B.1 | Vendor + dataset registry: contracts, consumption, SLA, consolidation | OpenMetadata + Governance Agent track lineage. Vendor entity in KG. | Governance + Analytics | **Partial** | Vendor CRM layer (contacts, comms history, renewal dates) = roadmap item. Demo on dataset side, defer CRM. |
| B.2 | Agentic governance: permissioning, runaway prevention, consistent semantics across stack | Governance agent + agent identity model. Permission inheritance by user is default; scoped sub-permissions configurable. | Governance | **Partial** | Bonus demo. Permission model walkthrough is doable; runaway-query prevention needs explicit limits config per workspace. |
| B.3 | Hosted KG: enterprise ontology, entity subgraphs (instruments, counterparties, vendors), MCP exposure | Neo4j KG per workspace; OGM nodes via platform-core; MCP exposes KG to external agents. | KG + MCP | **Ready** | Bonus demo. Subgraph grafting workflow needs short tutorial — not built-in UX, but Neo4j-native operation. Compresses months → days IF their ontology is straightforward. |
| B.4 | Rapid DQ test construction at scale across full vendor portfolio | BH-503 Configurable Quality Agent epic (8 tickets, spec Ready). | Quality | **Sprint to close (post-trial)** | In-scope for trial as 4.2. The "at scale across portfolio" framing is the quality rules epic landing in Q3. |

**Honest summary**: 5 items **Shipped** today, 5 **Ready** (small config), 6 require **sprint work** scoped in BH-526 to close before Day 1, 2 **Partial** bonuses for demo-only depth. The sprint work is bounded — none is "build from scratch", all are wiring or factory-class additions on top of architecture that already exists.

---

## 2. Workstream Execution Plan

### 2.1 Dataset Ingestion (Three Source Patterns)

**S3 Bucket**: Ingestion Agent accepts S3 credentials + sample file schema, generates: Snowflake external stage config, Airbyte connector definition, Dagster asset definition (via OpenLineage), dbt source YAML. Completion-file detection and lookback window handling are configurable. Commits to GitHub Enterprise as a PR.

**REST API (Paginated, Partitioned)**: Generic REST connector supports configurable pagination, date partitioning, batched ID lookups. For Longaeva's instrument universe (20-30k IDs, chunked parallel download), workspace context file is populated with batching parameters at setup so the agent generates correctly parameterized code. Retry logic and downstream dbt wiring are standard outputs.

**Snowflake Data Share**: Engineering Agent reads share DB name + target schema, introspects tables, generates: dbt source YAML, staging models with canonicalized field names/types, and GX quality contracts. Quality Agent validates all contracts before PR is raised.

### 2.2 Semantic View Enrollment

Four agent-orchestrated steps:

1. **Schema ingestion**: Supervisor reads Silver table schema + any plain-language description
2. **YAML scaffolding**: Engineering Agent generates full semantic view YAML; Longaeva's custom metadata blocks populated from workspace context file (loaded Day 3 with their YAML spec)
3. **Reference join resolution**: KG (loaded with Longaeva's reference schemas Days 3-5) allows Engineering Agent to detect required joins and generate correct relationship definitions
4. **Validation + PR**: Quality Agent compiles and executes against Snowflake, surfaces errors with remediation, runs MCP queryability checks, raises GitHub PR on success

**Context setup is the prerequisite**: Enrollment accuracy depends on Longaeva's reference schemas and YAML conventions being loaded Days 3-5.

### 2.3 MCP Downstream Validation

Brighthive's Neo4j KG is natively MCP-exposed. After enrollment, the Quality Agent executes a representative test query suite through Longaeva's MCP interface and validates results. Gaps (missing dimension sample values, absent query examples, missing plain-language instructions) are surfaced as structured feedback and included in the PR.

**Dependency**: Longaeva must provision read access to their MCP server for the trial environment. Scope in Milestone 2 (Day 1-2).

### 2.4 Automated Maintenance

**Self-Healing Pipelines**: Observability Agent monitors continuously. On failure, it reads pipeline run logs, asset lineage, and schema context to diagnose root cause. Engineering Agent generates a surgical fix PR — scoped to the affected component — with plain-language explanation.

Common Longaeva failure modes handled:
- Schema drift from vendor: detected at ingestion before data lands in Snowflake. PR updates stage config + dbt source definition
- Missing partition: detected in Dagster lineage via OpenLineage. Alert + re-run trigger to Slack
- Broken external stage: diagnosed from Snowflake error logs. Stage config fix PR generated
- dbt contract violation: Quality Agent detects, Engineering Agent generates targeted fix

**Auto-Authored Quality Tests**: Every enrolled dataset receives a baseline test suite inferred from schema (column types, nullability), statistical profiling (cardinality, distributions), and semantic context (daily-partitioned → freshness SLA tests; low-cardinality dimensions → accepted-values tests). Tests expressed in dbt and/or GX, version-controlled in GitHub.

**Longitudinal Anomaly Monitoring**: Platform Analytics Dashboard tracks per-dataset health: row count drift, cardinality breakdowns, distributional skew, null spikes — over trailing windows.

**Slack**: BrightSignals delivers all alerts to configured Slack channels. BrightAgent handles bidirectional interaction: pipeline state queries, re-runs, scaffolding triggers via @mention.

---

## 3. Context Setup Plan (Days 1-5)

| Context Element | Why It Matters | Owner | By Day |
|---|---|---|---|
| Longaeva custom YAML schema spec | Engineering Agent generates YAML matching their extended spec exactly | Longaeva | Day 3 |
| Fiscal calendar reference table schema + sample rows | Required for fiscal alignment join detection | Longaeva | Day 3 |
| Identifier mapping table schemas (LEI/FIGI → internal issuer ID) | Enables automatic identifier join resolution | Longaeva | Day 3 |
| Existing dbt project structure + conventions | Generated artifacts must match their project conventions | Longaeva | Day 3 |
| Dagster asset graph (OpenLineage export or direct connection) | Observability Agent reads lineage with correct semantics | Longaeva | Day 3-4 |
| Sample vendor datasets (one per source type) | Ingestion Agent reads schema to generate artifacts | Longaeva | Day 4-5 |
| Existing production semantic view definitions (2 examples) | Engineering Agent learns style before generating new ones | Longaeva | Day 4-5 |
| Brighthive workspace context file | Stack conventions, terminology, reference data glossary | Brighthive | Day 4-5 |

---

## 4. 14-Day Trial Timeline

| # | Milestone | Owner | Days |
|---|---|---|---|
| 1 | Use cases & success criteria confirmed | Joint | Day 1 |
| 2 | System access provisioned | Longaeva | Days 1-2 |
| 3 | Brighthive environment setup | Brighthive | Days 2-3 |
| 4 | Context layer creation | Brighthive | Days 3-5 |
| 5 | Environment mapping validation | Joint | Day 5 |
| 6 | Ingestion use case execution | Joint | Days 6-8 |
| 7 | Semantic view enrollment & MCP validation | Joint | Days 8-10 |
| 8 | Automated maintenance demonstration | Joint | Days 10-12 |
| 9 | Final evaluation & results review | Joint | Days 13-14 |
| 10 | Next steps discussion | Brighthive | Day 14 |

---

## 5. Success Criteria

### Ingestion
- S3 pipeline: generated Snowflake stage config + dbt source YAML is merge-ready with ≤1 round of engineer revision
- REST API pipeline: generated code handles pagination, date partitioning, and retry for a Longaeva-style instrument universe pattern
- Snowflake Data Share: staging model + quality contracts syntactically valid and pass Quality Agent validation on first run

### Semantic View Enrollment
- YAML scaffold correctly infers ≥90% of dimensions, time dimensions, and metrics without manual correction
- Fiscal calendar and identifier mapping joins detected and correctly defined automatically for at least one target dataset
- Generated definition compiles and executes against Snowflake semantic view engine without errors on first validation run

### MCP Validation
- All measures, dimensions, time dimensions from enrolled semantic view queryable through Longaeva's MCP interface
- Representative query suite (filtered, aggregated, multi-dimension) returns correct results with ≤5% error rate
- Gaps in query instructions and sample values surfaced automatically and included in enrollment PR

### Automated Maintenance
- Schema drift event triggers automated detection and fix PR within the same pipeline run cycle
- Fix PR is surgical (not a rewrite) and includes plain-language diagnosis
- Longitudinal anomaly monitoring surfaces at least one statistical signal during trial window
- Slack alerts arrive with sufficient context for triage without opening external tooling

---

## 6. Why Brighthive Wins This Evaluation

| Evaluation Dimension | Alternatives (point tools) | Brighthive |
|---|---|---|
| Context-aware scaffolding | Template-based, no understanding of your conventions | Workspace context file + KG populated with Longaeva conventions. Improves with every dataset. |
| Reference join resolution | Manual: engineers specify joins | KG-grounded: agent detects join requirements from dataset content against indexed reference schemas |
| End-to-end lifecycle | Separate tools for ingestion, dbt, quality, semantic layer | Single orchestrated workflow: ingestion → enrollment → MCP validation. Context compounds at every step. |
| Self-healing maintenance | Alerting only. Fix authoring remains with engineers. | Full loop: detect → diagnose → PR → engineer reviews. Engineers shift from authoring fixes to reviewing them. |
| Slack-native operation | Webhook alerts only, no bidirectional interaction | BrightSignals + BrightAgent: full bidirectional Slack. Triage, re-runs, scaffolding triggers from Slack. |

---

*Brighthive | Confidential | May 2026*
