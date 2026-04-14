---
title: "Platform Analytics, Monitoring & Reporting Dashboard"
epic: "BH-359"
author: "drchinca"
status: "In Progress"
created: "2026-04-13"
generates: "tickets"
tags: [analytics, monitoring, dashboard, enterprise, kpi, observability]
related:
  features: []
  pocs: []
  bedrock: []
---

# Platform Analytics, Monitoring & Reporting Dashboard

## Problem

BrightHive has no centralized visibility into platform health, usage, or value delivery. Monitoring is fragmented across 5+ external UIs (dbt Cloud for transformations, Airbyte UI for syncs, Sentry for errors, CloudWatch for logs, Apollo Studio for GraphQL). There is no way for a customer or internal team to answer: "How healthy is my data platform? What value have we created? What's broken?" This becomes critical at enterprise scale — a company with 1000s of data pipelines needs a command center, not a dozen disconnected dashboards.

## Use Case / Goal

A workspace admin opens `/workspace/:id/analytics` and sees a single dashboard answering:

1. **What do I have?** — Total data assets, sources, warehouses, projects, pipelines, members
2. **How healthy is it?** — Pipeline success rates, source connection status, transformation error rates
3. **What quality is the data?** — Quality check scores, pass rates, issues found, trends over time
4. **What value has been created?** — AI description coverage, embedding coverage, enrichment %, data products produced
5. **What needs attention?** — Proactive alerts for failures, SLA breaches, quality degradation

**Who benefits**: Workspace admins, data governance leads, BrightHive internal team (customer success), enterprise customers evaluating platform ROI.

**Success state**: A single page that replaces the need to check dbt Cloud, Airbyte, Sentry, and CloudWatch separately. Historical trends show platform trajectory. Alerts surface problems before users report them.

## Current Situation

### How It Works Today

**No analytics page exists.** The webapp (`brighthive-webapp`) has no route, component, or feature for platform-level analytics or monitoring.

The closest existing features are:

1. **Token Usage** (`brighthive-platform-core/src/graphql/models/usage-service.ts`): A `UsageServiceModel` queries a DynamoDB table `LangsmithTokenUsage` for LLM token consumption by workspace and date range. Exposed via `Workspace.usage` field resolver in `resolvers.ts`. This is the only "metrics" feature in the platform — it tracks AI token spend, not platform health.

2. **Data Catalog** (`brighthive-webapp/src/DataAssetCatalog/`): Lists data assets in an AG Grid table with name, description, owner, tags, access status, sensitivity. No columns for embeddings, quality scores, or enrichment status. No aggregate counts or KPIs.

3. **Project Overview** (`brighthive-webapp/src/Projects/ProjectOverviewPage/`): Shows project metadata (status, dates, members, issues). No enrichment metrics, no context coverage percentage.

4. **Quality Agent** (`brightbot/brightbot/agents/governance_agent/sub_agents/quality_check_agent.py`): Runs quality checks via Great Expectations, stores results as `AgentCapabilityExecutionNode` in Neo4j with `capabilityType: "quality_check"` and a JSON `result` field containing `{status, resultUrl, score, issuesFound, checksPerformed, timestamp}`. Results are accessible per-asset via presigned S3 URLs, but there is no dashboard aggregating quality across all assets.

5. **Agent Capability Executions** (`brighthive-platform-core/src/graphql/ogm/typedefs.ts`): `AgentCapabilityExecutionNode` stores results of AI agent runs (descriptions, embeddings, quality checks). Linked to `DataAssetNode` via `HAS_CAPABILITY_EXECUTION` relationship. The `capabilityType` field distinguishes: `"description_generation"`, `"quality_check"`, `"embedding"`. This is the raw data for "which assets have embeddings / quality checks / AI descriptions" — but no query aggregates these counts.

6. **External Monitoring**:
   - **Sentry** (`brightbot/utils/sentry.py`): Error tracking with 100% trace sampling. Agent-level tagging. No platform health dashboard.
   - **CloudWatch**: Lambda logs auto-captured, no custom dashboards defined.
   - **LangSmith** (optional): LLM agent tracing when enabled.
   - **dbt Cloud**: Transformation job history accessible only via dbt Cloud UI or API.
   - **Airbyte UI**: Sync status only via Airbyte's own dashboard.

### Hard Limitations

1. **No historical data for trends**: Neo4j stores current state only. There is no mechanism to answer "how many data assets did we have last Tuesday?" Point-in-time snapshots don't exist — you can't reconstruct historical counts from the current graph.

2. **OGM loads full objects into memory**: The `Node.find()` base class method (in `src/graphql/service/neo4j/node.ts`) returns complete node objects. For a workspace with 5000 data assets, calling `DataAsset.find()` loads all 5000 node objects into Lambda memory. This is acceptable for CRUD operations but will crash or timeout for dashboard aggregations at enterprise scale.

3. **Quality scores are JSON strings**: `AgentCapabilityExecutionNode.result` is stored as a `String!` in Neo4j — it's a JSON blob, not structured fields. Aggregating quality scores (average, distribution) requires parsing JSON for every quality check execution. Neo4j's `apoc.convert.fromJsonMap()` can help but adds complexity.

4. **No alerting infrastructure**: There is no mechanism to detect anomalies (failed pipelines, degraded quality) and surface them proactively. All problem detection is manual — someone has to notice in an external UI.

5. **Lambda cold start + Neo4j round-trips**: The GraphQL API runs on Lambda. A dashboard that makes 5-7 separate Cypher queries per page load will compound Lambda cold start times and Neo4j connection overhead. Without caching, this creates unacceptable latency for a dashboard UX.

### Gaps

**Data Gaps**:
- No aggregate counts exposed via GraphQL (total assets, sources, projects per workspace)
- No embedding coverage metric (which assets have vector embeddings vs. not)
- No quality score aggregation (average score, pass rate, distribution)
- No enrichment percentage (projects with context / total projects)
- No pipeline health aggregation (transformations by status, sources by connection status)
- No historical trend data (daily snapshots of platform metrics)

**Infrastructure Gaps**:
- No scheduled Lambda for snapshot collection or alert generation
- No Redis cache keys for analytics data
- No AlertNode in the graph database

**Frontend Gaps**:
- No `/analytics` route or navigation entry
- No KPI card component
- No dashboard layout page
- No chart components for distributions or trends (Vega and Recharts are in `package.json` but used only in BrightBot chat output, not in standalone dashboard views)

**Observability Gaps**:
- No proactive alerting for pipeline failures, quality degradation, or SLA breaches
- No notification channels (Slack, email) for platform health events
- No executive summary view for leadership

## Proposals / Solutions

### Recommended Approach

**Architecture**: Raw Cypher aggregation queries on the existing Neo4j graph, cached in Redis, served via a new `workspaceAnalytics` GraphQL query, rendered in a new `src/Analytics/` frontend module. Two new Neo4j node types (`MetricsSnapshotNode` for trends, `AlertNode` for alerts) store data that cannot be derived from current state. No new databases.

**Why this approach**:
- Neo4j already contains ~90% of the required data (assets, sources, projects, transformations, capability executions, workspace context)
- Raw Cypher `COUNT(DISTINCT ...)` aggregations avoid loading full objects into memory — critical for enterprise scale
- Redis caching (2-5 min TTLs) prevents dashboard loads from hammering Neo4j
- The existing frontend stack (React, MUI, Apollo, Vega, Recharts, AG Grid) has everything needed for charts, tables, and KPI cards
- Pre-computed daily snapshots via a scheduled Lambda solve the "no historical data" limitation

**Scale strategy for 1000s of pipelines**:

| Challenge | Solution |
|-----------|----------|
| Loading 5000+ nodes into JS memory | Raw Cypher COUNT aggregations, never `Node.find()` for analytics |
| Dashboard hammering Neo4j | Redis cache with 2-5 min TTLs per section |
| Rendering 1000s of pipeline rows | AG Grid server-side row model with cursor pagination |
| Historical trend computation | Pre-computed daily snapshots via Lambda, not live recomputation |
| Single GraphQL query overhead | Lazy field resolution — unused sub-fields don't execute their Cypher |
| Alert deduplication at scale | Check existing open alert by `category + metadata.entityId` before creating |

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| External dashboard (Grafana/Metabase) | Mature, battle-tested, rich visualizations | Requires new infra, separate auth, data export pipeline, not embedded in product | Adds operational complexity; doesn't ship as a platform feature customers see |
| CloudWatch Dashboards | Already in AWS, no code needed | Limited to infrastructure metrics, can't query Neo4j, no product-level KPIs | Wrong abstraction level — we need business metrics, not CPU usage |
| DynamoDB for analytics storage | Fast reads, serverless, pay-per-use | Requires duplicating Neo4j data, sync complexity, doesn't leverage graph relationships | Neo4j already has the data; adding DynamoDB creates consistency problems |
| Materialized views in Neo4j (APOC triggers) | Real-time aggregations without snapshots | APOC trigger complexity, Neo4j Community may not support all features, debugging difficulty | Too fragile for production; scheduled Lambda is simpler and more observable |

## KPI Inventory

### Category 1: Platform Overview (9 KPIs)

| # | KPI | Data Source | Cypher Path |
|---|-----|-------------|-------------|
| 1 | Total Data Assets | Neo4j | `(w:WorkspaceNode)-[:USES]->(da:DataAssetNode)` COUNT |
| 2 | Total Data Sources | Neo4j | `(w:WorkspaceNode)-[:USES]->(s:SourceNode)` COUNT |
| 3 | Total Warehouses | Neo4j | `(w:WorkspaceNode)-[:USES]->(wh:WarehouseServiceNode)` COUNT |
| 4 | Total Projects | Neo4j | `(w:WorkspaceNode)-[:GOVERNS]->(p:ProjectNode)` COUNT |
| 5 | Total Transformations | Neo4j | `(p:ProjectNode)-[:INCLUDES]->(t:TransformationNode)` COUNT |
| 6 | Total Members | Neo4j | Workspace role group users COUNT |
| 7 | Active Projects | Neo4j | `ProjectNode WHERE status = 'ACTIVE'` COUNT |
| 8 | Connected Sources | Neo4j | `SourceNode WHERE status = 'CONNECTED'` COUNT |
| 9 | Failed Sources | Neo4j | `SourceNode WHERE status = 'CONNECTION_FAILED'` COUNT |

### Category 2: Data Asset Analytics (6 KPIs)

| # | KPI | Data Source | Cypher Path |
|---|-----|-------------|-------------|
| 10 | Assets with Vector Embeddings | Neo4j | `(da)-[:HAS_CAPABILITY_EXECUTION]->(ace) WHERE ace.capabilityType = "embedding"` DISTINCT da COUNT |
| 11 | Assets with Quality Checks | Neo4j | `(da)-[:HAS_CAPABILITY_EXECUTION]->(ace) WHERE ace.capabilityType = "quality_check"` DISTINCT da COUNT |
| 12 | Assets with AI Descriptions | Neo4j | `(da)-[:HAS_CAPABILITY_EXECUTION]->(ace) WHERE ace.capabilityType = "description_generation"` DISTINCT da COUNT |
| 13 | Assets with Schemas | Neo4j | `(da:DataAssetNode)<-[:VALIDATES]-(s:SchemaNode)` DISTINCT da COUNT |
| 14 | Assets by Source (breakdown) | Neo4j | GROUP BY `SourceNode.type` with asset count per source |
| 15 | Assets by Type (SOURCE/INTERMEDIATE/PRODUCT) | Neo4j | GROUP BY `DataAssetNode.assetType` |

### Category 3: Pipeline Health (6 KPIs)

| # | KPI | Data Source | Cypher Path |
|---|-----|-------------|-------------|
| 16 | Healthy Pipelines | Neo4j | `TransformationNode WHERE lastRunStatus IN ['SUCCESS', 'COMPLETED']` + `SourceNode WHERE status = 'CONNECTED'` |
| 17 | Failed Pipelines | Neo4j | `TransformationNode WHERE lastRunStatus = 'ERROR'` + `SourceNode WHERE status = 'CONNECTION_FAILED'` |
| 18 | Stale Pipelines | Neo4j | Transformations/sources with no recent activity (configurable threshold) |
| 19 | Transformations by Status | Neo4j | GROUP BY `TransformationNode.lastRunStatus` |
| 20 | Sources by Status | Neo4j | GROUP BY `SourceNode.status` |
| 21 | Recent Failures (list) | Neo4j | Last 10 transformations/sources with error status, ordered by date |

### Category 4: Quality Metrics (5 KPIs)

| # | KPI | Data Source | Computation |
|---|-----|-------------|-------------|
| 22 | Total Quality Checks Run | Neo4j | COUNT `AgentCapabilityExecutionNode WHERE capabilityType = "quality_check"` |
| 23 | Average Quality Score | Neo4j | Parse `result` JSON → AVG of `score` field |
| 24 | Check Pass Rate | Neo4j | `status = "completed"` / total quality executions |
| 25 | Total Issues Found | Neo4j | Parse `result` JSON → SUM of `issuesFound` |
| 26 | Score Distribution | Neo4j | Bucketed counts: 0-20, 20-40, 40-60, 60-80, 80-100 |

### Category 5: Enrichment Metrics (4 KPIs)

| # | KPI | Data Source | Cypher Path |
|---|-----|-------------|-------------|
| 27 | Projects with Context | Neo4j | `(p:ProjectNode)` where workspace has `WorkspaceContextNode` |
| 28 | Context Enrichment % | Neo4j | projects with context / total projects × 100 |
| 29 | Description Coverage % | Neo4j | assets with description_generation capability / total assets × 100 |
| 30 | Total Data Products Created | Neo4j | `FinalDataProductGroupNode` COUNT per workspace |

### Data Freshness & Caching

| Section | Cache TTL | Computation |
|---------|-----------|-------------|
| Overview KPIs | 5 min (300s) | Real-time Cypher COUNT aggregations |
| Pipeline Health | 2 min (120s) | Real-time Cypher, volatile data |
| Quality Metrics | 10 min (600s) | Requires JSON parsing, heavier queries |
| Enrichment | 15 min (900s) | Less volatile, enrichment changes slowly |
| Historical Trends | 1 hour (3600s) | Pre-computed snapshots, immutable data |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Platform Core API | `brighthive-platform-core` | New OGM nodes (MetricsSnapshotNode, AlertNode), new GraphQL types (WorkspaceAnalytics + 10 sub-types), new analytics model with raw Cypher queries, new resolver, Redis cache extensions |
| Web App | `brighthive-webapp` | New `src/Analytics/` feature directory, KPICard components, Vega donut charts, AG Grid tables, Recharts trend charts, new route + nav entry, GraphQL query |
| Data Org CDK | `brighthive-data-organization-cdk` | New EventBridge-scheduled Lambdas: daily metrics snapshot, 15-min alert generation (Phase 2) |
| BrightBot | `brightbot` | No changes in Phase 1. Phase 3: Slack alert notifications via existing Slack integration |

## Acceptance Criteria

- [ ] `workspaceAnalytics` GraphQL query returns all 30 KPIs for a given workspace
- [ ] Overview dashboard renders 6 KPI cards, 2 distribution charts, and source health table
- [ ] Dashboard loads in <2 seconds for a workspace with 1000+ data assets (Redis cached)
- [ ] Quality metrics correctly parse AgentCapabilityExecution JSON results
- [ ] Historical trends display from MetricsSnapshotNode data (Phase 2)
- [ ] Proactive alerts generated for failed sources, errored transformations, quality degradation (Phase 2)
- [ ] Dashboard is mobile-responsive (320px+ screens)

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Neo4j graph with existing data (assets, sources, projects, transformations, capability executions) | Blocking | Ready |
| Redis cache (ElastiCache) | Blocking | Ready |
| AG Grid Enterprise license | Blocking | Ready (already in webapp) |
| Vega/Recharts libraries | Blocking | Ready (already in webapp package.json) |
| AgentCapabilityExecution with quality_check results | Non-blocking | Ready (quality agent deployed) |
| EventBridge + Lambda for snapshots | Blocking for Phase 2 | Not started |
| Slack integration for alert notifications | Blocking for Phase 3 | Ready (SlackServiceNode exists) |

## Ticket Breakdown

Generated from epic BH-359 — 14 tickets already created:

| Ticket | Summary | Points | Phase |
|--------|---------|--------|-------|
| BH-360 | Define analytics KPI inventory and data source mapping | 2 | Design |
| BH-361 | Add MetricsSnapshotNode and AlertNode to OGM schema | 2 | P1 Backend |
| BH-362 | Add WorkspaceAnalytics GraphQL types to Core API | 3 | P1 Backend |
| BH-363 | Create analytics model with Cypher aggregation queries | 5 | P1 Backend |
| BH-364 | Add Redis analytics cache layer | 2 | P1 Backend |
| BH-365 | Create analytics resolver and register | 3 | P1 Backend |
| BH-366 | Build Analytics overview dashboard with KPI cards | 8 | P1 Frontend |
| BH-367 | Add analytics route and navigation entry | 1 | P1 Frontend |
| BH-368 | Build pipeline health monitoring page | 5 | P2 Frontend |
| BH-369 | Build quality metrics dashboard page | 5 | P2 Frontend |
| BH-370 | Create metrics snapshot Lambda for historical trends | 5 | P2 Backend |
| BH-371 | Build alert generation system and management UI | 8 | P2 Full-stack |
| BH-372 | Add embeddings and quality score columns to Data Catalog | 3 | P2 Frontend |
| BH-373 | Build enrichment tracking and reporting pages | 5 | P3 Frontend |

**Total: 57 story points** across 3 phases.

**Phase 1 (MVP)**: BH-360 through BH-367 = 26 pts
**Phase 2 (Deep Analytics)**: BH-368 through BH-372 = 26 pts
**Phase 3 (Reporting)**: BH-373 = 5 pts

## Implementation Status (2026-04-14)

### What Shipped

| PR | Repo | What | Status |
|----|------|------|--------|
| webapp#1055 | brighthive-webapp | Analytics dashboard + Data Catalog improvements | **Merged → develop** |
| core#729 | brighthive-platform-core | Health check field resolvers on DataAsset | **Merged → develop** |
| brightbot#453 | brighthive/brightbot | .env.example (110+ vars documented) | **Merged → develop** |
| slack#14 | brightbot-slack-server | Fix bot responding to every channel message | **Merged → staging** |

### Architecture Decisions Made

1. **Mock data first** — Dashboard uses `mockData.ts` matching the `types.ts` schema contract. When backend is built (BH-363), swap mock imports for Apollo `useQuery`. No rework needed.
2. **Health checks as field resolvers** — `metadataAvailable`, `embeddingAvailable`, `qualityReportAvailable` are resolved per-asset on the `DataAsset` GraphQL type (not a separate query). Each check is independent and error-tolerant (returns `false` on any failure).
3. **No new databases** — Everything derives from existing Neo4j graph. Only 2 new node types planned: `MetricsSnapshotNode` (trends, Phase 2) and `AlertNode` (alerts, Phase 2).
4. **Codegen limitation** — The webapp uses `graphql-codegen` to generate typed hooks from `.graphql` files. The codegen is currently broken for local dev due to pre-existing query validation errors in `getTransformation.graphql` and `workflow.graphql`. The health check fields were manually patched into `generated.ts`. When codegen is fixed, re-run `npm run codegen` against the updated schema.
5. **assetType heuristic bug** — `determineDataAssetType` in `data-asset.ts` ignores the `assetType` property from Neo4j and derives type from `redshiftTableName` patterns. Fix is in core#729 but only works when `assetType` is in the OGM SelectionSet (which it isn't — `assetType` is not a field in the OGM schema, it's derived). Full fix requires either adding `assetType` to the OGM or removing the heuristic entirely.

### What's Next (Not Started)

| Ticket | What | Blocks |
|--------|------|--------|
| **BH-363** | `workspaceAnalytics` Cypher aggregation query — replaces mock data with real counts | Dashboard shows real data |
| **BH-364** | Redis cache layer for analytics queries (2-5 min TTLs) | Scale to 1000s of assets |
| **BH-370** | MetricsSnapshotNode Lambda — daily snapshots for trend charts | Growth chart shows real history |
| **BH-371** | AlertNode system — Lambda generates alerts from anomalies | Alerts section goes live |
| **BH-374** | Health check improvements — currently checks Neo4j only, needs S3 + OpenMetadata verification | Health dots accurate on staging |

### Key Files

| File | What |
|------|------|
| `brighthive-webapp/src/Analytics/types.ts` | **Schema contract** — all metric interfaces |
| `brighthive-webapp/src/Analytics/mockData.ts` | Mock data (replace with API) |
| `brighthive-webapp/src/Analytics/AnalyticsDashboardPage.tsx` | Main dashboard page |
| `brighthive-webapp/src/Analytics/README.md` | DX documentation |
| `brighthive-platform-core/src/graphql/models/data-asset-health.ts` | Health check field resolvers |
| `brighthive-platform-core/src/graphql/schema/typedefs.ts` | GraphQL schema with health fields |
| `brighthive-platform-core/setup/scripts/cypher/seed-analytics-data.cypher` | Local dev seed (45 assets, 107 capabilities) |
| `agentic-project-mgmt/docs/specs/platform-analytics-dashboard.md` | This spec |

### Local Dev Setup

```bash
# 1. Start Neo4j + Redis
cd brighthive-platform-core
docker-compose -f docker-compose.local.yml up -d

# 2. Seed data
bash setup/scripts/seed-neo4j-comprehensive.sh
cat setup/scripts/cypher/seed-analytics-data.cypher | docker exec -i brighthive-neo4j cypher-shell -u neo4j -p brighthive-local-dev

# 3. Start Platform Core
npm run deploy:local

# 4. Start Webapp (in another terminal)
cd brighthive-webapp
cp .env.example .env.local  # Then fill in VITE_TOKEN_USER from generate-local-token.sh
npx vite --port 3001

# 5. Open http://localhost:3001/workspace/60c2e688-1d0b-5397-92fa-193a959415a6/analytics
```

## Related

- **DX README**: `brighthive-webapp/src/Analytics/README.md` — metric sources, file structure, how to add new metrics
- **Feature doc**: Create via `/write-feature-doc` after Phase 2 ships
- **Token usage model**: `brighthive-platform-core/src/graphql/models/usage-service.ts` — only existing "metrics" feature
- **Quality agent**: `brightbot/brightbot/agents/governance_agent/sub_agents/quality_check_agent.py` — produces AgentCapabilityExecution data
- **Ingestion notifications**: `brighthive-data-organization-cdk` branch `BD-87-statemachine-to-slack-notification` — EventBridge events for ingestion pipeline tracking
- **Env var audit**: All repos now have `.env.example` documenting new vars added in last 10 days
