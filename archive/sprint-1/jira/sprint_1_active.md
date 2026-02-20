# Sprint 1: Jan 13-24, 2026 (REFOCUSED)

**Sprint Goal**: Build rich context layer for multi-org data lakes (design phase)

**Duration**: 2 weeks (Jan 13-24)
**Milestone**: M1 - End of January
**Focus**: Data lake context engineering (NOT user-facing features)

**Core Insight**: Context engineering = data lake management intelligence (asset metadata, lineage, schema evolution, quality, governance)

---

## Epic: BH-110 - Data Asset Context Model (9 tasks)

**Goal**: Extend Neo4j to capture rich context about datasets in data lakes

### Part A: Asset Context Schema (Week 1)

- [ ] **[BH-150](https://brighthiveio.atlassian.net/browse/BH-150)**: Design Asset Context Schema
  - Extend DataAsset node with business context, quality, freshness, schema, governance fields
  - Deliverable: Neo4j schema extension, OGM types, migration script
  - Owner: Solutions Architect + Data Engineer

- [ ] **[BH-151](https://brighthiveio.atlassian.net/browse/BH-151)**: Design Schema Metadata Structure
  - Track schema as first-class entity (SchemaVersion nodes)
  - Schema evolution history, compatibility scoring, drift detection
  - Deliverable: SchemaVersion node design, diff algorithm, compatibility scoring
  - Owner: Data Engineer

- [ ] **[BH-152](https://brighthiveio.atlassian.net/browse/BH-152)**: Design Owner/Steward Model
  - Track BusinessOwner, TechnicalSteward, DataGovernancePolicy nodes
  - Access control integration with GraphQL
  - Deliverable: Owner/steward schema, governance policy, access control design
  - Owner: Security Lead + Solutions Architect

### Part B: Lineage Context (Week 2)

- [ ] **[BH-153](https://brighthiveio.atlassian.net/browse/BH-153)**: Design Multi-Level Lineage Graph
  - Dataset-level, transformation-level, column-level lineage
  - Transformation nodes (Glue, DBT, Redshift, Lambda)
  - Deliverable: Lineage graph schema, query patterns (upstream/downstream/impact)
  - Owner: Data Engineer + Solutions Architect

- [ ] **[BH-154](https://brighthiveio.atlassian.net/browse/BH-154)**: Design Lineage Capture from Existing Systems
  - Automatic lineage extraction from Glue, DBT, Redshift
  - Lambda functions for lineage ingestion, merge strategy
  - Deliverable: Lineage ingestion pipeline design per source
  - Owner: Data Engineer

### Part C: Cross-Org Context (Week 2-3)

- [ ] **[BH-155](https://brighthiveio.atlassian.net/browse/BH-155)**: Design Cross-Organization Schema Matching
  - Schema similarity scoring (Jaccard, type compatibility, semantic)
  - Batch job to compute similarity scores
  - Deliverable: Similarity algorithm, Neo4j similarity edges
  - Owner: Data Engineer + AI/ML Lead

- [ ] **[BH-156](https://brighthiveio.atlassian.net/browse/BH-156)**: Design Master Data / Golden Record Strategy
  - Identify golden records across organizations
  - Master data designation, confidence scoring
  - Deliverable: Master data schema, identification algorithm, admin UI spec
  - Owner: Solutions Architect + Data Engineer

### Part D: Context Versioning (Week 3)

- [ ] **[BH-157](https://brighthiveio.atlassian.net/browse/BH-157)**: Design Context Snapshot Strategy
  - Snapshot entire context graph at point in time
  - Storage in Neo4j + S3 + DynamoDB for fast lookup
  - Deliverable: Snapshot schema, export/import pipeline, DynamoDB ContextVersions table
  - Owner: Platform Engineer + Data Engineer

- [ ] **[BH-158](https://brighthiveio.atlassian.net/browse/BH-158)**: Design Context Diff Algorithm
  - Compare two context snapshots, show what changed
  - Added/removed/modified assets, lineage changes
  - Deliverable: Diff algorithm, JSON report, visualization design
  - Owner: Data Engineer

---

## Epic: BH-113 - Audit & Monitoring (3 tasks, data-focused)

**Goal**: Track data lake context changes, monitor data quality

- [ ] **[BH-159](https://brighthiveio.atlassian.net/browse/BH-159)**: Design Context Change Audit Log
  - Log every change to data lake context (schema, lineage, quality, governance)
  - DynamoDB AuditLogs table + CloudWatch Logs
  - Events: ASSET_ADDED, SCHEMA_CHANGED, LINEAGE_UPDATED, QUALITY_DEGRADED, etc.
  - Deliverable: Audit log schema, event emission design, GraphQL query API
  - Owner: Platform Engineer

- [ ] **[BH-160](https://brighthiveio.atlassian.net/browse/BH-160)**: Design Data Quality Monitoring
  - Continuously monitor quality metrics (completeness, accuracy, consistency, timeliness)
  - Glue DQ checks, DBT tests, custom Lambda functions
  - Store in DynamoDB DataQualityMetrics + CloudWatch custom metrics
  - Deliverable: Quality metric schema, computation pipeline, score algorithm
  - Owner: Data Engineer

- [ ] **[BH-161](https://brighthiveio.atlassian.net/browse/BH-161)**: Design Monitoring Decision (data lake focus)
  - Monitor data lake health (not just system health)
  - CloudWatch custom metrics: AssetsIngested, SchemaChanges, QualityScoreDrop, FreshnessSLAViolations
  - Alarms for critical issues (quality drop, SLA violations, lineage broken)
  - Deliverable: Metric specification, alarm definitions, dashboard design
  - Owner: Platform Engineer + Data Engineer

---

## Epic: BH-114 - UX WebApp Re-design (3 tasks, catalog-focused)

**Goal**: Expose rich data lake context in UI

- [ ] **[BH-162](https://brighthiveio.atlassian.net/browse/BH-162)**: Design Context-Rich Data Catalog UI
  - Show asset context: business purpose, quality, freshness, schema, lineage, governance
  - Component design: AssetContextCard, QualityBadge, FreshnessBadge
  - Deliverable: UI mockup, GraphQL query requirements, component design
  - Owner: UX Designer + Frontend Engineer

- [ ] **[BH-163](https://brighthiveio.atlassian.net/browse/BH-163)**: Design Lineage Visualization
  - Interactive graph showing upstream/downstream dependencies
  - Click to expand, highlight impacted assets, show transformation logic
  - Graph rendering library choice (D3.js, Cytoscape.js, vis.js)
  - Deliverable: Lineage UI mockup, library choice, GraphQL lineage API
  - Owner: UX Designer + Frontend Engineer

- [ ] **[BH-164](https://brighthiveio.atlassian.net/browse/BH-164)**: Design Enterprise Context Configuration View
  - Admin UI for workspace-level configuration
  - Data quality rules, governance policies, lineage capture settings, master data designation
  - Deliverable: Configuration UI mockup, DynamoDB WorkspaceConfig table, GraphQL mutations
  - Owner: UX Designer + Platform Engineer

---

## Epic: BH-115 - Interconnect-ability (3 tasks, connector spec)

**Goal**: Standardize how connectors push context metadata to Neo4j

- [ ] **[BH-165](https://brighthiveio.atlassian.net/browse/BH-165)**: Audit Existing Connector Context Flow
  - Document how Glue, Airbyte, Snowflake push metadata today
  - Identify context gaps (schema, quality, lineage, business context)
  - Deliverable: Connector audit report, gap analysis, integration points diagram
  - Owner: Solutions Architect

- [ ] **[BH-166](https://brighthiveio.atlassian.net/browse/BH-166)**: Define Rich Connector Metadata Spec
  - Standardize metadata format (asset, schema, lineage, quality, governance)
  - JSON schema, OpenAPI spec, GraphQL mutation spec
  - Deliverable: Connector metadata JSON schema, GraphQL spec, developer guide
  - Owner: Solutions Architect + Technical Writer

- [ ] **[BH-167](https://brighthiveio.atlassian.net/browse/BH-167)**: Design Connector Developer Guide
  - Documentation for building custom connectors
  - Architecture, auth, examples, testing, troubleshooting
  - Deliverable: Connector guide (Markdown), code examples (Python, TypeScript)
  - Owner: Technical Writer

---

## BONUS (if time): Agent Integration (2 tasks, lightweight)

**Goal**: Enable agents to consume data lake context (minimal, not overbuilt)

- [ ] **[BH-168](https://brighthiveio.atlassian.net/browse/BH-168)**: Design Agent Context Query API
  - GraphQL queries for agents to access data lake context
  - findDatasetsByPurpose, getDatasetQuality, getDatasetSchema
  - Deliverable: GraphQL schema extension, example agent queries
  - Owner: Solutions Architect + AI/ML Lead

- [ ] **[BH-169](https://brighthiveio.atlassian.net/browse/BH-169)**: Design Context Injection for Agents (SIMPLE)
  - Add workspace_context field to BBState (minimal)
  - Fetch once per conversation, cache in Redis (5-min TTL)
  - NOT overbuilt: no user behavior tracking, no multi-tier memory
  - Deliverable: BBState extension spec, context fetch function
  - Owner: AI/ML Lead

---

## Sprint Summary

**Total Tasks**: 20 tasks across 4 epics (+2 bonus)

**Progress**: 0/20 completed (0%)

**Critical Path** (15 tasks for 2-week sprint):
- Epic 1 (BH-110): Tasks 1-7 (asset context, lineage, cross-org)
- Epic 2 (BH-113): Tasks 10-11 (audit, quality monitoring)
- Epic 3 (BH-114): Tasks 13-14 (catalog UI, lineage viz)
- Epic 4 (BH-115): Tasks 16-17 (connector audit, spec)

**Defer to Sprint 2**:
- Task 9 (Context Diff Algorithm) - lower priority
- Task 12 (Monitoring Decision) - can finalize in Sprint 2
- Task 15 (Config UI) - lower priority
- Task 18 (Connector Guide) - documentation can follow implementation
- Tasks 19-20 (Agent Integration) - bonus if time allows

---

## What We're Building

✅ **Data Lake Context Engineering**:
- Rich metadata for datasets (quality, freshness, lineage, governance)
- Cross-org schema matching and master data strategy
- Lineage capture from Glue, DBT, Redshift
- Context versioning and auditing
- Context-rich data catalog UI

❌ **What We're NOT Building** (yet):
- User behavioral tracking (defer to BH_V3 Phase 1 in M2)
- Conversation history tracking (defer to M2)
- Proactive notifications (defer to M3)
- Recommendation engine (defer to M4)

**Why this is right**:
- M1 goal: "Core architecture + foundations"
- Can't build AI-first features without rich data lake context
- Can't track user behavior on datasets that have no context
- Can't recommend datasets that have no quality/freshness scores

---

## Definition of Done

- [ ] Design document written and reviewed
- [ ] Neo4j schema extensions documented
- [ ] GraphQL API spec defined
- [ ] UI mockups approved (for UX tasks)
- [ ] Integration points validated
- [ ] No critical architectural gaps

---

## Sprint Ceremonies

- **Sprint Planning**: Jan 13 (Monday) - 10:00 AM
- **Daily Standups**: 9:00 AM daily
- **Mid-Sprint Check-in**: Jan 17 (Friday) - 2:00 PM
- **Sprint Review**: Jan 24 (Friday) - 2:00 PM
- **Sprint Retro**: Jan 24 (Friday) - 3:30 PM

---

## Risks & Dependencies

**Risks**:
- Design scope creep (stay focused on data lake context, not user features)
- Over-engineering agent integration (keep it lightweight)
- Schema evolution complexity (start simple, iterate)

**Dependencies**:
- Neo4j schema must support new node types (SchemaVersion, BusinessOwner, etc.)
- CloudWatch vs Prometheus decision confirmed (CloudWatch + X-Ray for M1)
- Lineage capture depends on access to Glue, DBT, Redshift metadata

**Mitigations**:
- Daily standup to catch scope creep early
- Expert reviews (Solutions Architect, Data Engineer) on complex designs
- Integration validation upfront (Task 16: Audit existing connectors)

---

## Storage Strategy (Finalized)

**Context Metadata**: Neo4j (fast graph queries, matches existing pattern)
**Context Versions**: DynamoDB ContextVersions (fast point-in-time lookup)
**Context Snapshots**: S3 with Glacier lifecycle (cheap archival)
**Audit Logs**: DynamoDB AuditLogs + CloudWatch Logs
**Schema Metadata**: Neo4j as properties/nodes
**Quality Metrics**: DynamoDB DataQualityMetrics + CloudWatch custom metrics

---

## Notes

- This is the first sprint of M1 (3 weeks total: Sprint 1 + Sprint 2)
- Sprint 1 focus: **Design** context architecture
- Sprint 2 focus: **Implement** context architecture + UX
- AI-first features (BH_V3.md) come AFTER rich data lake context exists
- Keep stakeholders updated on design decisions (especially storage strategy)
