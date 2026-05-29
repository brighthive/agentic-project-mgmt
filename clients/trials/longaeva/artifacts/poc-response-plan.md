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

| ID | Longaeva Requirement | Brighthive Capability | Agent | Coverage | Notes |
|---|---|---|---|---|---|
| 1.1 | S3 bucket ingestion: scaffold Snowflake external stage + dbt source | Ingestion Agent: 600+ connectors incl. S3; auto-generates stage config, Airbyte connector, dbt source YAML. Commits to GitHub Enterprise via PR. | Ingestion + Eng | FULL MATCH | |
| 1.2 | Completion-file detection, lookback windows, batch metadata tracking | Ingestion Agent manages full S3 lifecycle: partition detection, late-arriving data, run metadata. Configurable per-pipeline. | Ingestion | FULL MATCH | |
| 1.3 | REST API ingestion: paginated, date-partitioned, batched ID lookups, parallel download, retry, dbt source wiring | Generic REST API connector + Ingestion Agent. Pagination, partitioning, retry configurable. dbt source auto-generated. | Ingestion + Eng | FULL MATCH | Config req'd for Longaeva universe pattern |
| 1.4 | Snowflake Data Share: scaffold dbt source, staging model, data quality contracts | Engineering Agent reads share metadata and generates dbt source YAML, staging models, GX quality contracts. Version-controlled. | Eng + Quality | FULL MATCH | |
| 2.1 | Scaffold semantic view YAML from Silver table + plain-language description: infer dimensions, time dimensions, facts, metrics, custom metadata blocks | Engineering Agent generates dbt models and YAML from natural language + schema introspection. Custom YAML schema loaded into workspace context file. | Engineering | FULL MATCH | Custom YAML schema must be loaded into context |
| 2.2 | Resolve reference data joins: fiscal calendar, LEI/FIGI → internal issuer ID, geo/classification | Engineering Agent reads enterprise KG and workspace context to identify required joins. Reference schemas loaded into KG at setup. | Eng + KG | FULL MATCH | Reference schemas loaded in Day 3-5 context build |
| 2.3 | Validate semantic view: confirm compiles + executes against Snowflake; surface errors with remediation | Quality Agent runs validation checks against Snowflake post-scaffolding. dbt agent validates syntax and execution. Outputs are deterministic and rerunnable. | Quality + Eng | FULL MATCH | |
| 3.1 | Confirm all measures, dimensions, time dimensions queryable through Longaeva's internal MCP server | Brighthive's Neo4j KG is natively MCP-exposed. Platform can validate queryability through external MCP interface after enrollment. | KG + Quality | PARTIAL | Requires MCP server config access from Longaeva |
| 3.2 | Execute representative queries (filtered, metric aggregation, multi-dimension slice) and validate correctness + performance | Quality Agent executes test query suites post-enrollment. GX tests enforce correctness. Performance metrics in analytics dashboard. | Quality | FULL MATCH | |
| 3.3 | Identify gaps degrading agent quality: missing dimension sample values, absent query examples, missing plain-language instructions | Workspace Context File + Engineering Agent: missing context surfaced as gaps in KG completeness scoring. Plain-language instructions + query examples in YAML scaffolding output. | Eng + KG | FULL MATCH | |
| 3.4 | Single guided workflow: Silver table → enrolled, validated, PR-raised semantic view | BrightAgent Supervisor orchestrates full enrollment: schema ingest → YAML scaffold → reference join resolution → quality validation → MCP check → GitHub PR. | Supervisor | FULL MATCH | |
| 4.1 | Self-healing pipelines: diagnose failures, generate scoped surgical PR with plain-language explanation | Observability Agent monitors continuously, detects schema drift and contract violations. Generates targeted fix PRs via Engineering Agent. Demonstrated in live demos. | Observability + Eng | FULL MATCH | Self-healing PR generation is demo-ready; hardening in progress |
| 4.2 | Auto-author freshness gates and data quality tests at enrollment: dbt-native + GX suites, inferred from schema + semantic context | Quality Agent auto-generates test suites at enrollment. Tests in dbt and/or GX, version-controlled in GitHub, continuously enforced. | Quality | FULL MATCH | |
| 4.3 | Longitudinal anomaly monitoring: row count drift, dimension cardinality, distributional skew, unexpected nulls — trailing windows | Platform Analytics Dashboard + Quality Agent: longitudinal quality scoring tracked continuously. | Quality + Analytics | FULL MATCH | Trailing window config per dataset |
| 4.4 | Slack alerting: pipeline health, quality violations, anomaly detections — with enough context for triage without leaving Slack | BrightSignals (shipped Sprint 9): Slack DMs or channel posts with affected dataset, issue nature, severity, PR/run log links. Fully configurable. | BrightSignals | FULL MATCH | |
| 4.5 | Bidirectional Slack: ask about pipeline state, request re-run, trigger scaffolding from Slack | BrightAgent Slack integration: stays quiet until @mentioned, responds with full multi-tenant context. Pipeline state, re-run, scaffolding triggers all supported. | BrightAgent | FULL MATCH | |
| B.1 | Unified vendor and dataset registry: active contracts, team consumption, pipeline health SLA, consolidation opportunities | Data catalog (OpenMetadata) + Governance Agent tracks dataset-to-consumer lineage. Vendor registry maps to KG entity nodes. | Governance + Analytics | PARTIAL | Vendor CRM layer = roadmap item |
| B.2 | Agent permissioning and governance across heterogeneous stack (Snowflake, Postgres, external APIs) | Governance Agent enforces policies across all connected systems. Agent permission inheritance by user is default; scoped sub-permissions configurable. | Governance | FULL MATCH | |
| B.3 | Hosted semantic layer and KG: enterprise ontology, custom entity subgraphs, MCP-exposed to external agents | Neo4j KG deployed per workspace. KG exposed via MCP for external agent consumption. Brighthive agents curate; external agents (IBM WatsonX, etc.) consume via MCP. | KG + MCP | FULL MATCH | |

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
