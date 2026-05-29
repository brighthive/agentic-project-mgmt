---
title: "POC Scope — Longaeva Partners × Brighthive"
source: "Grant Langseth, Longaeva Partners"
received: "2026-05-29"
status: "authoritative — client's words, not ours"
---

> **Note**: This is the client's POC scope, captured verbatim. Our internal
> response and capability mapping live in `poc-response-plan.md` and the
> honest capability map in `platform-saas-ai-context/clients/longaeva/`.

# POC Scope: Longaeva Partners × Brighthive

## 1. Dataset Ingestion (3 Source Types)

We'd like to evaluate Brighthive's ingestion capabilities across three source patterns that represent the majority of our vendor data surface area.

### Source Type 1 — Vendor-Managed S3 Bucket

Vendors provision an S3 bucket with credentials, and we land files into our Bronze layer via Snowflake's external stage pattern. These pipelines typically handle completion-file detection, lookback windows for late-arriving data, and batch metadata tracking. Files are generally structured (CSV or Parquet), daily partitioned, and range from tens of thousands to hundreds of millions of rows depending on the dataset.

**The POC question**: given S3 credentials and a sample file schema, can Brighthive scaffold the full ingestion pipeline — including the Snowflake stage configuration and dbt source definition — with minimal human authoring?

### Source Type 2 — REST API (Paginated, Partitioned)

Several vendors deliver data via REST APIs that require programmatic polling — typically partitioned by date, with batched ID lookups against our internal security universe of up to 20-30k instruments. Our standard pattern fetches a universe of IDs, chunks them, downloads in parallel, and writes to our data lake before loading into Snowflake. These pipelines need correct daily partitioning, retry logic, and downstream dbt source wiring.

**The POC question**: given an API specification or sample client, can Brighthive generate a correctly partitioned, production-ready ingestion asset with appropriate error handling and the downstream source definition?

### Source Type 3 — Snowflake Data Share

A number of vendors deliver data via Snowflake Data Shares, which land as read-only external databases in our Snowflake account. These require dbt source definitions, staging models that canonicalize field names and types, and data quality contracts.

**The POC question**: given a Snowflake share database name and target schema, can Brighthive scaffold the dbt source definition, staging model, and data quality contracts?

## 2. Snowflake Semantic View Enrollment

Semantic views sit on top of our Silver-layer dbt models and serve as the central interface between our data warehouse and downstream consumers — internal analytics tools, LLM agents, and APIs. Enrolling new datasets into this layer is currently the highest-friction step in our data science workflow, and a core use case we want to evaluate.

### Background

We have built a custom YAML contract on top of Snowflake's native semantic view specification (https://docs.snowflake.com/en/user-guide/views-semantic/semantic-view-yaml-spec) that serves as the interface between our curated data layer and our internal analytics and AI applications. Our schema extends the Snowflake spec with additional metadata for **metric store wiring**, **named reusable filter presets**, **plain-language query instructions that are injected into downstream agent context**, and **verified query examples**.

We currently have a small number of production semantic views in place — covering datasets such as daily consumer transaction data (daily grain, multi-dimensional with channel, geography, and card-type breakdowns) and web traffic metrics (daily grain, multi-domain with fiscal calendar alignment) — and are looking to scale enrollment significantly as more datasets reach our curated layer.

### The Enrollment Workflow We Want to Evaluate

The core POC scenario: a data scientist has a new dataset in our curated Silver layer and wants to enroll it into the semantic view layer. Today this requires familiarity with our YAML schema, reference data schemas, and metric store wiring conventions followed by downstream evaluation. We want to evaluate whether Brighthive can reduce this friction.

Specifically:

1. **Scaffold the semantic view YAML** given a Silver table schema and a plain-language description — correctly inferring dimensions, time dimensions, facts, and metrics, and populating the additional metadata blocks our schema requires.

2. **Resolve reference data joins** — our semantic views frequently need to join against companion tables in our security master and reference data schemas, including:
   - **Fiscal calendar tables** — for fiscal quarter alignment across issuers with non-standard fiscal years
   - **Identifier mapping tables** — e.g. mapping from industry-standard security identifiers such as **LEI or FIGI** to our internal issuer ID
   - **Standard geographic and classification code tables**

   Can Brighthive recognize when these joins are needed based on the dataset's content and generate the correct relationship definitions?

3. **Validate the semantic view** — after scaffolding, can Brighthive verify that the generated definition compiles and executes correctly against Snowflake's semantic view engine, and surface any errors with actionable remediation?

## 3. MCP Feedback Loop (Downstream Validation)

Our semantic view layer is the data source for an **internal MCP server** that exposes data to analysts and AI agents via a structured discovery and query workflow. A critical part of the POC is validating that a newly enrolled semantic view is not just syntactically valid, but functionally complete.

Specifically:

- Confirm that all measures, dimensions, and time dimensions are correctly surfaced and queryable through the MCP interface.
- Execute representative queries — filtered queries, metric aggregations, and multi-dimension slices — and validate that results are correct and performant.
- Identify gaps that would degrade agent query quality (e.g. missing sample values on key dimensions, absent query examples, or missing plain-language instructions) and suggest additions.

**Ideal end state**: a data scientist can go from "I have a curated Silver table" to "my semantic view is enrolled, validated, and ready for downstream AI and analytics use" in a single guided workflow, with Brighthive handling the scaffolding and validation steps and raising a pull request for engineering review.

## 4. Automated Maintenance

Explicitly in-scope for the two-week trial; core evaluation criteria.

### Self-Healing Pipelines

When a pipeline failure or data quality violation is detected, we want to evaluate whether Brighthive can autonomously diagnose the root cause — reading pipeline run logs, asset lineage, and schema context — and generate a targeted fix as a pull request. The engineer's role should shift from authoring a fix to reviewing one: the agent proposes the change, the engineer approves and merges.

Common failure modes we want demonstrated:

- **Schema drift** from a vendor changing their delivery format
- **Missing partition**
- **Broken external stage**
- **dbt model failing a data contract**

The PR should be scoped and surgical — not a rewrite — and should include a plain-language explanation of the diagnosed issue.

### Longitudinal Monitoring of Data Anomalies

Beyond pass/fail quality gates, evaluate whether Brighthive can monitor datasets over time for statistical anomalies that would not trigger a hard test failure but nonetheless signal a data problem. Specific patterns:

- **Abnormal increases or decreases in row counts** relative to historical norms
- **Breakdowns in the cardinality of key dimensions** (e.g. a geography or category dimension that suddenly contains far fewer distinct values than expected)
- **Distributional skew in numeric metrics** that deviates significantly from the trailing window
- **Unexpected nulls or value-range violations** in columns that are typically well-populated

These signals should be tracked longitudinally so gradual data degradation is caught before it compounds into a downstream model or agent failure.

### Alerting and Slack Integration

Our engineering and data science teams operate primarily out of Slack. Evaluate whether Brighthive can deliver pipeline health alerts, data quality violations, and anomaly detections directly to configured Slack channels — with enough context in the notification itself (**affected dataset, nature of the issue, severity, link to relevant PR/run log**) that the on-call engineer can triage without leaving Slack.

Beyond passive alerting, can engineers and data scientists communicate directly with Brighthive agents from within Slack — asking questions about pipeline state, requesting a re-run, or triggering a scaffolding workflow — without needing to open a separate UI.

## 5. Trial Users

Full user list TBC. Plan for 4-5 participants: Grant + 1-2 data engineering + 1-2 data science.

## 6. Bonus — Areas for Further Evaluation

Not gating criteria, but meaningful longer-term value drivers.

### Unified Vendor and Dataset Registry

As the vendor data portfolio grows, maintaining visibility across active contracts, dataset health, and consumption patterns becomes increasingly difficult. Can Brighthive serve as a unified operational registry — surfacing which datasets are under active contract, which internal teams and workflows are consuming each dataset, pipeline health/SLA adherence, and opportunities to consolidate overlapping or underutilized subscriptions? Ideally extending to a lightweight vendor relationship layer: key contacts, communication history, renewal dates alongside the technical catalog.

### Data Governance and the Agentic Layer

As they move toward agentic workflows, governing agent access across a heterogeneous stack — data warehouse, transactional stores, third-party APIs — is open and important. Evaluate how Brighthive approaches agent permissioning: do agents inherit human user permissions or operate under a deliberately scoped subset; how is runaway query behavior prevented; how are consistent access semantics maintained across different systems. Also: how does Brighthive enforce data contracts and lineage policies in an environment where agents (not just humans) are initiating data operations.

### Rapid Data Quality Test Construction

Auto-authoring of freshness gates and DQ tests is explicitly **in-scope for the core trial** (§4). Beyond the trial, evaluate the broader platform capability for continuously enforcing quality standards at scale across the full vendor portfolio — automatically generating and maintaining test suites as datasets evolve, rather than manual authoring per source.

### Hosted Semantic Layer and Knowledge Graph

Early-stage internal efforts around a knowledge graph and semantic layer. Evaluate how Brighthive's managed graph instance and metadata catalog could complement or accelerate this work:

- How the enterprise ontology is established and enriched over time
- How their own entity subgraphs (**instruments, counterparties, vendors**) can be grafted onto the base model
- How the graph is exposed via MCP so other agents in their orchestration layer can consume it

**Key evaluation criterion**: the degree to which this compresses months of in-house infrastructure work into an immediately production-ready deployment.

## 7. Proposed Timeline

> **Note from Brighthive**: client's pasted message proposed "beginning Monday, May 18th"
> but the actual trial start has slipped — current target is **June 2026 (exact date TBD)**.
> Days below are *relative* to the agreed start date.

| # | Milestone | Description | Owner | Day |
|---|---|---|---|---|
| 1 | Use cases & success criteria confirmed | Align on three ingestion source types, semantic view enrollment, MCP validation. Define measurable success criteria. | Brighthive + Longaeva | Day 1 |
| 2 | System access provisioned | Longaeva provisions Snowflake, S3, dbt project, Dagster env access. | Longaeva | Day 1–2 |
| 3 | Brighthive environment setup | Configure trial environment, connect to systems, validate end-to-end connectivity. | Brighthive | Day 2–3 |
| 4 | Context layer creation | Ingest pipeline lineage, dbt source definitions, Snowflake schema metadata, existing semantic view definitions. | Brighthive | Day 3–5 |
| 5 | Environment mapping validation | Joint review of Brighthive's understanding of the stack. | Joint | Day 5 |
| 6 | Ingestion use case execution | Run three ingestion scenarios (S3, REST API, Snowflake Data Share). Evaluate scaffolding quality, correctness, time-to-PR. | Joint | Day 6–8 |
| 7 | Semantic view enrollment & MCP validation | Execute enrollment on 1-2 target datasets. Validate downstream MCP queryability, completeness, agent response quality. | Joint | Day 8–10 |
| 8 | Feedback & iteration | Review outputs. Identify gaps, refine artifacts, test bonus areas. | Joint | Day 10–12 |
| 9 | Final evaluation & results review | Consolidate findings against Day 1 success criteria. | Joint | Day 13–14 |
| 10 | Next steps discussion | Commercial path, open questions, production deployment decision. | Brighthive | Day 14 |
