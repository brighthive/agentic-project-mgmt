# Sprint 8 --- Marketing Release Notes (Mid-Sprint Checkpoint)

**Period**: Apr 14--28, 2026

---

## dbt Agent & Transformation Pipeline -- Full Delivery

The flagship achievement of Sprint 8: the **dbt transformation pipeline** is now a complete, end-to-end workflow. Users can connect their GitHub repos, select dbt Cloud jobs from a dropdown (no more manual job IDs), view model-level metadata with SQL, lineage, and PR links, and trigger transformations -- all from within the platform. The dbt agent itself was migrated from a rigid deterministic graph to a flexible **ReAct pattern**, making it smarter about auto-reading workspace configurations and reducing unnecessary user interrupts.

- Complete dbt workflow: jobs, data products, GitHub repos, audit fixes (BH-330)
- dbt model detail view with SQL, PR link, lineage, origin badge (BH-346)
- TransformationNode model metadata + per-model run tracking (BH-344, BH-345)
- dbt agent auto-read config, reduce interrupts (BH-325, BH-328, BH-342)
- Replace Job ID text field with dbt Cloud job dropdown (BH-319, BH-340)
- Webapp dbt settings + GitHub repo management (BH-326, BH-327)
- Device Flow OAuth + disconnect for GitHub connection (BH-339)
- dbt agent migrated from deterministic graph to ReAct pattern

---

## Governance & Policy Enforcement

A new governance layer gives workspace administrators real control over data policies. Policies can now be toggled between Active, Enforced, and Admin Only states -- and they're automatically **injected into the AI agent's workspace context**, so the agent respects governance rules when answering questions or running queries. On-demand tools let the agent pull schemas, glossary terms, and policy definitions as needed.

- Inject governance policies into workspace context (BH-357)
- Add isActive field to CustomPolicyNode (BH-356)
- Policy enforcement toggles -- Active, Enforced, Admin Only (BH-356)
- On-demand governance context tools: schemas, glossary, policies (BH-347 -- in review)

---

## Azure Synapse BYOW Integration

BrightHive now supports **Azure Synapse** as a Bring-Your-Own-Warehouse (BYOW) target. The integration spans the full stack: T-SQL dialect support in the warehouse layer, a new Synapse ingestion pipeline with warehouse-type routing in CDK, Synapse querying in the quality check agent, and provider-specific warehouse icons and configuration forms in the UI. E2E tests validate the entire connect flow.

- Azure Synapse T-SQL dialect support (BH-322)
- Warehouse adapter pattern for extensibility (BH-321)
- WarehouseServiceProvider enum enforcement + Synapse BYOW (platform-core)
- Synapse ingestion pipeline with warehouse-type routing (data-org CDK)
- Synapse querying in quality check sub-agent (brightbot)
- Provider-specific warehouse icons, card picker, config forms (webapp)
- E2E tests for BYOW connect flow

---

## Platform Analytics & Health Checks

A new **Platform Analytics Dashboard** surfaces operational metrics, and a **Data Asset Health Check** system monitors the quality of ingested data. The webapp now has full Analytics sub-pages: Dashboards, Reports, Alerts, Notifications, and Health Checks. The catalog backend supports vector, metric, and quality status checks.

- Platform analytics dashboard (BH-359)
- Data asset health check fields (BH-374)
- Catalog backend for vector/metric/quality checks (BH-375)
- Project Observability tab with proactive insights, data contracts, pipeline runs (BH-359)

---

## Webapp UX -- Context, Analytics, Custom Personas

Three major new sections were added to the webapp behind feature flags:

**Context**: Knowledge Base, workspace context, formulas, library, and transcribes -- with real data sources and AWS service integrations. Brand-colored icons for transcription sources.

**Analytics**: Dashboards, reports, alerts, notifications, health checks -- a complete observability surface for workspace data.

**Custom Personas**: A visual flow builder (using React Flow) for creating custom AI personas in BrightStudio. Users can define persona behavior through an intuitive drag-and-drop interface.

- Context section with KB, workspace context, formulas, library, transcribes (BH-347)
- Custom Personas page with visual flow builder (BH-376)
- Context + Analytics KB page with rich mockup UX and BETA flags (BH-376)
- Feature flags for Context, Analytics, Custom Personas (BH-347)
- Airbyte icons + BYOW and Custom Upload coming soon indicators

---

## Bedrock Migration & AI Agent Improvements

Progress on the Bedrock migration: model routing from Claude to Bedrock is complete, and the GraphQL capabilities for the deep_agent supervisor open new interaction patterns. The credential form now supports Human-in-the-Loop (HITL) interrupts during ingestion, pausing the agent to collect credentials from the user.

- Claude to Bedrock migration -- model routing (BH-282)
- GraphQL capabilities for deep_agent supervisor (BH-240)
- Credential form HITL interrupt for ingestion (BH-355)

---

## Production Stability & Infrastructure

Legacy infrastructure cleanup, package fixes, and cross-repo improvements. The EDL (Extract Data Lake) pipeline was decommissioned, Slack bot behavior was tightened to only respond to @mentions, and the React framework was upgraded from v17 to v18.

- EDL shutdown -- decommission legacy data pipeline (BH-278)
- OMD webhook enhanced event tracking (BH-253)
- Slack bot: only respond to @mentions, DMs, thread replies
- Slack service user creation made idempotent
- React 17 to 18 upgrade (webapp)
- Redshift CATALOG_ID fix for cross-account external schemas
- Claude PR review workflows added to CDK repos
- DX readme rewrites for data-org and data-workspace CDK repos

---

## By the Numbers

| Metric | Value |
|--------|-------|
| Tickets Completed | 21 (mid-sprint) |
| PRs Merged | 103 (82 feature) |
| Repos Touched | 7 |
| Team Size | 4 engineers |
| Sprint Duration | 14 days (day 7 of 14) |
| New Sections | 3 (Context, Analytics, Custom Personas) |
| Warehouse Support | +1 (Azure Synapse) |
