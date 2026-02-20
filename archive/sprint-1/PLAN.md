# Sprint 1 REFOCUSED: Data Lake Context Engineering

**Date**: 2026-01-12
**Core Focus**: Context management for multi-org data lakes, NOT user-facing features

---

## Critical Correction

**Previous error**: Over-invested in user-facing context (conversation history, user preferences, behavioral tracking)

**Actual M1 goal**: **Context engineering for data lake management**
- What is each dataset in our data lakes?
- Where did it come from (lineage)?
- How does it relate to other datasets (cross-org, cross-workspace)?
- What's its schema, quality, freshness?
- Who owns it, who can access it (governance)?

**AI-first features** (BH_V3.md) come AFTER we have rich data lake context to expose to agents.

---

## Context Engineering: The Core Problem

### Current State (Data Lake Context Gaps)

Looking at ARCHITECTURE.md, you have:

**Organization Accounts:**
- S3 buckets (brighthive-org-a-raw/, brighthive-org-a-staged/)
- Glue Data Catalog (schema metadata)
- Step Functions (data ingestion workflows)

**Workspace Accounts:**
- Redshift Serverless (queries across multiple org data lakes)
- Schema-based multi-tenancy (org_a.customers, org_b.sales)

**Platform-Core (Shared):**
- Neo4j (metadata SSOT)
- GraphQL API

**Current Context Tracking** (Existing in Neo4j):
```cypher
(DataAsset) - has basic metadata (name, s3_location, row_count)
(DataAsset)-[:BELONGS_TO]->(Organization)
(DataAsset)-[:IN_WORKSPACE]->(Workspace)
(DataAsset)-[:HAS_LINEAGE]->(DataAsset)  // basic lineage
```

**What's MISSING** (Context Engineering Gaps):

1. **Asset Context Richness**
   - What is the business purpose of this dataset?
   - What's the data quality score? (null rate, completeness, accuracy)
   - How fresh is it? (last updated, update frequency, SLA)
   - What's the schema evolution history?

2. **Cross-Organization Context**
   - How do datasets from Org A relate to Org B's datasets?
   - Which orgs share similar schemas? (customer table in Org A vs Org B)
   - What's the master data? (golden record for "customer" across orgs)

3. **Lineage Depth**
   - Current: Simple edges (DataAsset)-[:HAS_LINEAGE]->(DataAsset)
   - Needed: Transformation lineage (S3 → Glue → Redshift → DBT → Visualization)
   - Needed: Column-level lineage (which source columns create this derived column?)

4. **Governance Context**
   - Data classification (PII, sensitive, public)
   - Access policies (who can query? who can download?)
   - Compliance tags (GDPR, HIPAA, SOC2)
   - Owner/steward (who maintains this? who approves schema changes?)

5. **Versioning/History**
   - How to snapshot context at a point in time?
   - How to compare context between versions?
   - How to roll back to previous context state?

---

## Revised Sprint 1: Data Lake Context Engineering

**Theme**: Build rich context layer for multi-org data lakes

**Duration**: 3 weeks (Jan 13 - Jan 31)

**Focus**: Design context architecture that makes data lakes **understandable, governable, and queryable**

---

## Epic 1: BH-110 - Data Asset Context Model

**Goal**: Extend Neo4j to capture rich context about datasets in data lakes

### Part A: Asset Context Schema (Week 1)

#### Task 1: Design Asset Context Schema
**What**: Extend DataAsset node in Neo4j with context fields

```cypher
// Current (minimal)
(DataAsset {
  uuid, name, s3_location, row_count, created_at
})

// NEW (context-rich)
(DataAsset {
  uuid, name, s3_location, row_count, created_at,

  // Business context
  business_purpose: "Customer master data for CRM",
  business_owner: "jane@acme.com",
  technical_steward: "john@acme.com",

  // Quality context
  quality_score: 0.87,  // 0-1 scale
  completeness: 0.92,   // % non-null
  accuracy_last_checked: timestamp,
  quality_issues: ["5% nulls in email", "10 duplicates found"],

  // Freshness context
  last_updated: timestamp,
  update_frequency: "daily",  // daily, weekly, realtime
  update_sla: 24,  // hours
  sla_met: true,

  // Schema context
  schema_version: "v2.3",
  schema_hash: "abc123",  // detect schema drift
  column_count: 25,

  // Governance context
  data_classification: "PII",  // public, internal, confidential, PII
  compliance_tags: ["GDPR", "HIPAA"],
  access_tier: "restricted",  // open, restricted, private

  // Discoverability
  tags: ["customer", "crm", "master-data"],
  description: "...",
  sample_queries: ["SELECT * FROM org_a.customers LIMIT 10"]
})
```

**Deliverable**:
- Neo4j schema extension document
- OGM type definitions for platform-core
- Migration script (add new properties to existing DataAsset nodes)

**Owner**: Solutions Architect + Data Engineer

---

#### Task 2: Design Schema Metadata Structure
**What**: Track schema as first-class entity (not just property of DataAsset)

```cypher
// NEW node type
(SchemaVersion {
  schema_id: uuid,
  version: "v2.3",
  hash: "abc123",
  created_at: timestamp,
  columns: [
    {name: "customer_id", type: "INTEGER", nullable: false, primary_key: true},
    {name: "email", type: "VARCHAR(255)", nullable: true},
    {name: "created_at", type: "TIMESTAMP", nullable: false}
  ],
  breaking_changes: ["removed column: phone_number"],
  created_by: "etl_pipeline_v2"
})

// Relationships
(DataAsset)-[:HAS_SCHEMA]->(SchemaVersion)
(SchemaVersion)-[:EVOLVED_FROM]->(SchemaVersion)  // schema history
(SchemaVersion)-[:COMPATIBLE_WITH]->(SchemaVersion)  // cross-org schema matching
```

**Why this matters**:
- Track schema evolution over time (when did email become nullable?)
- Detect schema drift (Glue catalog changed, Neo4j not updated)
- Find compatible schemas across orgs (Org A customer schema vs Org B customer schema)
- Enable column-level lineage (next task)

**Deliverable**:
- SchemaVersion node design
- Schema comparison algorithm (diff between versions)
- Schema compatibility scoring (how similar are two schemas?)

**Owner**: Data Engineer

---

#### Task 3: Design Owner/Steward Model
**What**: Track who owns, maintains, and governs each dataset

```cypher
// NEW node types
(BusinessOwner {
  user_id, name, email, department, role
})

(TechnicalSteward {
  user_id, name, email, team, responsibilities
})

(DataGovernancePolicy {
  policy_id, name,
  access_rules: [{role: "analyst", permissions: ["read"]}, ...],
  retention_days: 365,
  encryption_required: true,
  compliance_frameworks: ["GDPR", "HIPAA"]
})

// Relationships
(DataAsset)-[:OWNED_BY]->(BusinessOwner)
(DataAsset)-[:MAINTAINED_BY]->(TechnicalSteward)
(DataAsset)-[:GOVERNED_BY]->(DataGovernancePolicy)
(BusinessOwner)-[:APPROVES_ACCESS_FOR]->(DataAsset)
```

**Why this matters**:
- Answer: "Who owns this dataset?" (for data requests)
- Answer: "Who can I ask about schema changes?" (steward)
- Enforce: "Can this user access this dataset?" (governance policy)
- Track: "What datasets does Jane own?" (ownership graph)

**Deliverable**:
- Owner/steward node design
- Governance policy schema
- Access control integration design (how does this affect GraphQL resolvers?)

**Owner**: Security Lead + Solutions Architect

---

### Part B: Lineage Context (Week 2)

#### Task 4: Design Multi-Level Lineage Graph
**What**: Track lineage at multiple levels (dataset, table, column, transformation)

**Current lineage** (simple):
```cypher
(DataAsset)-[:HAS_LINEAGE]->(DataAsset)  // just edges, no context
```

**NEW lineage** (rich):
```cypher
// Dataset-level lineage
(DataAsset)-[:DERIVED_FROM {
  transformation_type: "glue_crawler",  // or "dbt_model", "sql_transform"
  transformation_id: "crawler-abc-123",
  confidence: 1.0,  // how confident are we in this lineage?
  created_at: timestamp
}]->(DataAsset)

// Transformation nodes (capture HOW data flows)
(Transformation {
  transformation_id,
  type: "dbt_model",  // or "glue_job", "redshift_view", "lambda_etl"
  name: "customer_enrichment",
  sql_query: "SELECT ...",  // actual transformation logic
  config: {...},
  created_by: "dbt_pipeline_v2"
})

(DataAsset)-[:INPUT_TO]->(Transformation)
(Transformation)-[:OUTPUTS]->(DataAsset)

// Column-level lineage (advanced)
(Column {
  column_id, name, data_type
})

(Column)-[:DERIVED_FROM {
  transformation_logic: "CONCAT(first_name, last_name)"
}]->(Column)
```

**Why this matters**:
- Answer: "If Org A's customer table changes, what breaks downstream?"
- Answer: "Where does this dashboard number come from?" (trace back to source)
- Impact analysis: "What happens if I delete this dataset?"
- Debugging: "Why is this column null?" (trace lineage back to source)

**Deliverable**:
- Lineage graph schema (dataset, transformation, column levels)
- Lineage capture strategy (how do we ingest lineage from Glue, DBT, Redshift?)
- Lineage query patterns (upstream, downstream, impact analysis)

**Owner**: Data Engineer + Solutions Architect

---

#### Task 5: Design Lineage Capture from Existing Systems
**What**: How to automatically capture lineage from Glue, DBT, Redshift

**Sources of lineage**:

1. **Glue Crawler → Neo4j**
   ```python
   # When Glue crawler runs:
   # 1. Glue discovers table in S3
   # 2. Lambda triggers (existing: neo4j_metadata_sync)
   # 3. NEW: Lambda extracts lineage from Glue GetTable response
   # 4. Creates: (S3Dataset)-[:DISCOVERED_BY]->(GlueCrawler)-[:CREATES]->(GlueTable)
   ```

2. **DBT → Neo4j**
   ```python
   # DBT has manifest.json with lineage
   # manifest.json:
   # {
   #   "nodes": {
   #     "model.customer_enrichment": {
   #       "depends_on": ["source.raw_customers", "source.raw_addresses"]
   #     }
   #   }
   # }
   # Parse manifest.json, push lineage to Neo4j
   ```

3. **Redshift Views → Neo4j**
   ```sql
   -- Redshift system tables have view definitions
   SELECT definition FROM pg_views WHERE schemaname = 'org_a' AND viewname = 'customers_enriched';
   -- Parse SQL, extract source tables, create lineage edges
   ```

4. **OpenMetadata → Neo4j**
   ```python
   # OpenMetadata already tracks lineage
   # Sync OMD lineage to Neo4j via webhook (existing integration)
   ```

**Deliverable**:
- Lineage ingestion pipeline design (per source)
- Lambda functions to extract lineage from Glue, DBT, Redshift
- Lineage merge strategy (how to combine lineage from multiple sources?)

**Owner**: Data Engineer

---

### Part C: Cross-Org Context (Week 2-3)

#### Task 6: Design Cross-Organization Schema Matching
**What**: Find related datasets across organizations (Org A customer table vs Org B customer table)

**Problem**:
- Workspace has 10 organizations
- Each org has "customers" table with different schemas
- Need to find: Which schemas are similar? Which can be joined?

**Solution**: Schema similarity scoring

```python
# Algorithm
def schema_similarity(schema_a, schema_b):
    # 1. Column name overlap (Jaccard similarity)
    common_columns = set(schema_a.columns) & set(schema_b.columns)
    jaccard = len(common_columns) / len(set(schema_a.columns) | set(schema_b.columns))

    # 2. Data type compatibility
    type_match = sum(1 for col in common_columns if schema_a[col].type == schema_b[col].type)
    type_score = type_match / len(common_columns) if common_columns else 0

    # 3. Semantic similarity (using embeddings)
    desc_similarity = cosine_similarity(embed(schema_a.description), embed(schema_b.description))

    # Weighted score
    return 0.4 * jaccard + 0.3 * type_score + 0.3 * desc_similarity

# Store in Neo4j
(SchemaVersion)-[:SIMILAR_TO {score: 0.87}]->(SchemaVersion)
```

**Why this matters**:
- Agents can suggest: "Org A's customer table is 87% similar to Org B's - want to join them?"
- Data engineers can find: "Which orgs have similar data?" (for consolidation)
- Analysts can discover: "I need sales data - which orgs have it?"

**Deliverable**:
- Schema similarity algorithm
- Batch job to compute similarity scores (nightly)
- Neo4j schema for similarity edges

**Owner**: Data Engineer + AI/ML Lead

---

#### Task 7: Design Master Data / Golden Record Strategy
**What**: Identify "golden records" across organizations

**Problem**:
- 10 orgs have "customer" table
- Same customer (email: john@acme.com) appears in Org A, Org B, Org C
- Which is the source of truth? (master data)

**Solution**: Master data designation

```cypher
// NEW properties on DataAsset
(DataAsset {
  is_master_data: true,
  master_data_for: ["customer"],  // what entity is this master for?
  master_data_confidence: 0.95,   // how confident?
  master_data_source: "org_a_crm"  // original system
})

// Relationships
(DataAsset)-[:MASTER_FOR {entity: "customer"}]->(Workspace)
(DataAsset)-[:DERIVED_COPY]->(DataAsset)  // slave copy references master
```

**Deliverable**:
- Master data designation schema
- Algorithm to identify master data (heuristics: largest, most complete, most recent)
- UI for admins to manually designate master data

**Owner**: Solutions Architect + Data Engineer

---

### Part D: Context Versioning (Week 3)

#### Task 8: Design Context Snapshot Strategy
**What**: Snapshot entire context graph at a point in time

**Why**:
- Reproducibility: "Show me the data catalog as of Jan 1, 2025"
- Debugging: "What changed between v1 and v2?"
- Rollback: "Revert to previous context state"

**Solution**: Versioned context snapshots

```cypher
// NEW node
(ContextSnapshot {
  snapshot_id, version, created_at,
  snapshot_metadata: {
    workspace_id, created_by, reason: "monthly_snapshot"
  }
})

// Relationships
(ContextSnapshot)-[:INCLUDES]->(DataAsset)
(ContextSnapshot)-[:INCLUDES]->(SchemaVersion)
(ContextSnapshot)-[:INCLUDES]->(Transformation)

// Store full snapshot in S3 (for large graphs)
(ContextSnapshot {
  s3_snapshot_uri: "s3://brighthive-context-snapshots-prod/ws-123/2026-01-01.json.gz"
})
```

**Storage strategy**:
- Small changes: Store in Neo4j (node properties, relationships)
- Large snapshots: Export to S3 (compressed JSON)
- Index in DynamoDB for fast lookup

**Deliverable**:
- Snapshot schema design
- Snapshot export/import pipeline
- DynamoDB ContextVersions table design

**Owner**: Platform Engineer + Data Engineer

---

#### Task 9: Design Context Diff Algorithm
**What**: Compare two context snapshots, show what changed

```python
# ContextDiff algorithm
def diff_context(snapshot_a, snapshot_b):
    return {
        "added_assets": [...],      # new datasets
        "removed_assets": [...],    # deleted datasets
        "modified_assets": [        # changed datasets
            {
                "asset_id": "...",
                "changes": {
                    "schema": "v2.1 -> v2.2",
                    "row_count": "1M -> 1.2M",
                    "quality_score": "0.9 -> 0.85"
                }
            }
        ],
        "added_lineage": [...],     # new lineage edges
        "broken_lineage": [...]     # lineage edges removed
    }
```

**Why this matters**:
- Answer: "What changed in the data catalog this week?"
- Debugging: "Why did this dashboard break?" (compare context before/after)
- Audit: "Who changed the schema?" (context diff + audit logs)

**Deliverable**:
- Context diff algorithm
- Diff visualization (JSON report, UI visualization)

**Owner**: Data Engineer

---

## Epic 2: BH-113 - Audit & Monitoring (DATA-FOCUSED)

**Goal**: Track data lake context changes, not user behavior

### Task 10: Design Context Change Audit Log
**What**: Log every change to data lake context

```python
# DynamoDB AuditLogs table
{
  "workspace_id": "ws-123",      # partition key
  "timestamp": 1704672000000,    # sort key
  "event_type": "SCHEMA_CHANGED",  # or ASSET_ADDED, LINEAGE_UPDATED
  "resource_id": "asset-abc-123",
  "changed_by": "glue_crawler",  # or user_id, or "dbt_pipeline"
  "changes": {
    "schema_version": {"old": "v2.1", "new": "v2.2"},
    "columns_added": ["phone_number"],
    "columns_removed": []
  },
  "trace_id": "trace-xyz"  # for distributed tracing
}
```

**Events to track**:
- ASSET_ADDED (new dataset discovered)
- ASSET_REMOVED (dataset deleted)
- SCHEMA_CHANGED (columns added/removed/modified)
- LINEAGE_UPDATED (new dependency discovered)
- QUALITY_DEGRADED (quality score dropped below threshold)
- FRESHNESS_SLA_VIOLATED (data not updated on time)
- GOVERNANCE_POLICY_CHANGED (access rules modified)

**Deliverable**:
- Audit log schema (DynamoDB + CloudWatch Logs)
- Event emission design (where in code to emit events?)
- Audit log query API (GraphQL resolver for audit history)

**Owner**: Platform Engineer

---

### Task 11: Design Data Quality Monitoring
**What**: Continuously monitor data quality metrics

**Metrics to track**:
```python
# Data quality dimensions
{
  "asset_id": "asset-abc-123",
  "timestamp": 1704672000000,
  "completeness": 0.92,     # % non-null
  "uniqueness": 0.88,       # % unique (for columns that should be unique)
  "accuracy": 0.95,         # % matching expected patterns (email format, phone format)
  "consistency": 0.90,      # % consistent with referential integrity
  "timeliness": 0.85,       # % meeting SLA
  "validity": 0.93          # % passing validation rules
}
```

**How to compute**:
- Run Glue DQ checks (AWS Glue Data Quality)
- Run DBT tests (schema tests, data tests)
- Custom Lambda functions (query Redshift, compute metrics)

**Store in**:
- DynamoDB DataQualityMetrics table (fast lookup)
- CloudWatch custom metrics (for alerting)

**Deliverable**:
- Data quality metric schema
- Quality computation pipeline (Glue DQ, DBT tests, custom checks)
- Quality score algorithm (weighted average of dimensions)

**Owner**: Data Engineer

---

### Task 12: Design Monitoring Decision (DATA-FOCUSED)
**What**: Monitor data lake health, not just system health

**Monitoring stack**: CloudWatch + X-Ray (confirmed)

**Data lake metrics** (CloudWatch custom metrics):
```python
Namespace: BrightHive/DataLake

Metrics:
  - AssetsIngested (count, per workspace/org)
  - SchemaChanges (count, per workspace/org)
  - QualityScoreDrop (count, threshold: <0.8)
  - FreshnessSLAViolations (count)
  - LineageEdgesAdded (count)
  - LineageEdgesBroken (count, alert if >0)
```

**Alarms**:
- Critical: QualityScoreDrop > 5 in 5 minutes
- Critical: FreshnessSLAViolations > 0 (data not updated on time)
- Warning: SchemaChanges > 10 in 1 hour (too many changes, investigate)
- Warning: LineageEdgesBroken > 0 (lineage broken, fix immediately)

**Deliverable**:
- Monitoring metric specification (data lake focus)
- CloudWatch alarm definitions
- Monitoring dashboard design (Grafana or CloudWatch Dashboard)

**Owner**: Platform Engineer + Data Engineer

---

## Epic 3: BH-114 - UX (DATA CATALOG FOCUS)

**Goal**: Expose rich data lake context in UI, NOT build AI-first interface yet

### Task 13: Design Context-Rich Data Catalog UI
**What**: Show asset context in catalog (quality, freshness, lineage)

**Current catalog** (basic):
- List of datasets (name, row count, created_at)

**NEW catalog** (context-rich):
```
Dataset: org_a.customers
├─ Business Context
│  ├─ Purpose: Customer master data for CRM
│  ├─ Owner: jane@acme.com (Business)
│  └─ Steward: john@acme.com (Technical)
├─ Quality
│  ├─ Quality Score: 87/100 ⚠️
│  ├─ Completeness: 92%
│  ├─ Last Checked: 2 hours ago
│  └─ Issues: 5% nulls in email, 10 duplicates
├─ Freshness
│  ├─ Last Updated: 3 hours ago ✅
│  ├─ Update Frequency: Daily
│  └─ SLA: Met (24h)
├─ Schema
│  ├─ Version: v2.3
│  ├─ Columns: 25
│  └─ Recent Changes: Added phone_number (3 days ago)
├─ Lineage
│  ├─ Upstream: s3://org-a-raw/customers.parquet
│  └─ Downstream: dbt_model.customer_enrichment, dashboard.sales_by_region
└─ Governance
   ├─ Classification: PII
   ├─ Compliance: GDPR, HIPAA
   └─ Access: Restricted (request access)
```

**Deliverable**:
- UI mockup for context-rich catalog
- Data requirements (what GraphQL queries needed?)
- Component design (AssetContextCard, QualityBadge, FreshnessBadge, LineageVisualization)

**Owner**: UX Designer + Frontend Engineer

---

### Task 14: Design Lineage Visualization
**What**: Visualize data lineage graph (upstream, downstream, impact)

**UI**: Interactive graph (like OpenMetadata lineage UI)

```
[S3: raw_customers]
     ↓
[Glue: org_a.customers]
     ↓
[Redshift: org_a.customers]
     ↓
[DBT: customer_enrichment] ← [S3: raw_addresses]
     ↓
[Dashboard: Sales by Region]
```

**Features**:
- Click to expand upstream/downstream
- Highlight impacted assets (if this changes, what breaks?)
- Show transformation logic (hover to see SQL query)
- Filter by lineage type (data flow, transformation, usage)

**Deliverable**:
- Lineage visualization mockup
- Graph rendering library choice (D3.js, Cytoscape.js, vis.js)
- Lineage query API (GraphQL resolver for upstream/downstream)

**Owner**: UX Designer + Frontend Engineer

---

### Task 15: Design Enterprise Context Configuration View
**What**: UI for admins to configure workspace-level context

**Configuration settings**:
```
Workspace Configuration
├─ Data Quality Rules
│  ├─ Minimum quality score: 80/100
│  ├─ Completeness threshold: 90%
│  └─ Freshness SLA: 24 hours
├─ Governance Policies
│  ├─ Default data classification: Internal
│  ├─ Compliance frameworks: GDPR, HIPAA
│  └─ Access approval required: Yes
├─ Lineage Capture
│  ├─ Enable DBT lineage: Yes
│  ├─ Enable Glue lineage: Yes
│  └─ Enable Redshift lineage: Yes (experimental)
└─ Master Data
   ├─ Designate master datasets: [org_a.customers]
   └─ Master data sync frequency: Daily
```

**Deliverable**:
- Configuration UI mockup
- Configuration schema (DynamoDB WorkspaceConfig table)
- Configuration API (GraphQL mutations)

**Owner**: UX Designer + Platform Engineer

---

## Epic 4: BH-115 - Connector Spec (DATA INGESTION FOCUS)

**Goal**: Standardize how connectors push context metadata to Neo4j

### Task 16: Audit Existing Connector Context Flow
**What**: Document how Glue, Airbyte, Snowflake push metadata today

**Current flow**:
```
1. Glue Crawler discovers table
   ↓
2. Lambda (neo4j_metadata_sync) triggered
   ↓
3. Lambda calls platform-core GraphQL API
   mutation createDataAsset(input: {name, s3_location, ...})
   ↓
4. GraphQL resolver creates DataAsset node in Neo4j
```

**What context is pushed** (currently):
- name, s3_location, row_count, created_at
- Organization, Workspace relationships

**What context is MISSING**:
- Schema (columns, types) → only in Glue, not Neo4j
- Quality metrics → not tracked
- Lineage → not captured from Glue
- Business context (purpose, owner) → not provided by connector

**Deliverable**:
- Connector audit report (Glue, Airbyte, Snowflake)
- Context gap analysis (what's missing?)
- Integration points diagram

**Owner**: Solutions Architect

---

### Task 17: Define Rich Connector Metadata Spec
**What**: Standardize metadata format for connectors to push to Neo4j

**Connector metadata payload** (JSON schema):
```json
{
  "asset": {
    "name": "customers",
    "type": "table",  // or "view", "materialized_view", "file"
    "location": "s3://org-a-raw/customers.parquet",
    "format": "parquet",
    "row_count": 1000000,
    "size_bytes": 52428800,
    "created_at": "2026-01-10T10:00:00Z",
    "updated_at": "2026-01-12T08:00:00Z"
  },
  "schema": {
    "version": "v2.3",
    "columns": [
      {"name": "customer_id", "type": "INTEGER", "nullable": false, "primary_key": true},
      {"name": "email", "type": "VARCHAR(255)", "nullable": true},
      {"name": "created_at", "type": "TIMESTAMP", "nullable": false}
    ]
  },
  "lineage": {
    "upstream": [
      {"type": "s3_file", "location": "s3://org-a-raw/customers.csv"},
      {"type": "api", "source": "salesforce_api"}
    ],
    "transformation": {
      "type": "glue_crawler",
      "job_id": "crawler-abc-123",
      "logic": "Discovered schema from parquet file"
    }
  },
  "quality": {
    "completeness": 0.92,
    "null_counts": {"email": 50000},
    "duplicates": 10
  },
  "governance": {
    "classification": "PII",
    "tags": ["customer", "crm"],
    "owner": "jane@acme.com"
  }
}
```

**Deliverable**:
- Connector metadata JSON schema (OpenAPI spec)
- GraphQL mutation spec (createDataAssetWithContext)
- Connector developer guide

**Owner**: Solutions Architect + Technical Writer

---

### Task 18: Design Connector Developer Guide
**What**: Documentation for building custom connectors

**Sections**:
1. Architecture overview (how connectors integrate)
2. Metadata specification (JSON schema)
3. Authentication (Cognito JWT)
4. Example implementations (Glue, Airbyte, custom)
5. Testing guide (how to validate connector)
6. Troubleshooting (common errors)

**Deliverable**:
- Connector developer guide (Markdown)
- Code examples (Python, TypeScript)

**Owner**: Technical Writer

---

## What About AI-First Features?

**Good news**: By building rich data lake context (BH-110), you're setting up for AI-first features in M2-M4.

**How context engineering enables AI**:

1. **Agents can answer questions** about data lakes:
   - "What datasets have PII?" → Query Neo4j governance context
   - "Show me fresh datasets" → Query freshness context
   - "What's the quality of our data?" → Query quality metrics

2. **Agents can suggest datasets** based on context:
   - Retrieval Agent: "For your sales analysis, I recommend org_a.sales (quality: 95%, fresh: 2 hours ago)"
   - Analyst Agent: "Warning: org_b.customers has 20% nulls in email column"

3. **Proactive insights** (M2-M3) powered by context:
   - "Anomaly detected: org_a.customers quality dropped to 70% (was 90%)"
   - "Lineage broken: dbt_model.sales_summary is missing upstream dataset"

4. **User behavioral tracking** (BH_V3.md Phase 1) comes AFTER context:
   - Can't track "user accessed dataset X" until you have rich context for dataset X
   - Can't recommend datasets until you have quality, freshness, relevance context

**So Sprint 1 focus**: Build rich data lake context FIRST, enable AI consumption LATER

---

## Agent Integration (Lightweight, Not Overbuilt)

### Task 19: Design Agent Context Query API
**What**: GraphQL queries for agents to consume data lake context

**Queries agents need**:
```graphql
# Retrieval Agent: Find datasets by business purpose
query findDatasetsByPurpose($query: String!, $workspace_id: ID!) {
  datasets(workspace_id: $workspace_id, search: $query) {
    id, name, business_purpose, quality_score, freshness, lineage_summary
  }
}

# Analyst Agent: Get dataset quality before querying
query getDatasetQuality($asset_id: ID!) {
  dataAsset(id: $asset_id) {
    quality_score, completeness, quality_issues, last_updated
  }
}

# DBT Agent: Get schema for model generation
query getDatasetSchema($asset_id: ID!) {
  dataAsset(id: $asset_id) {
    schema { version, columns { name, type, nullable } }
  }
}
```

**Deliverable**:
- Agent query API spec (GraphQL schema)
- Example agent queries (documentation)

**Owner**: Solutions Architect + AI/ML Lead

---

### Task 20: Design Context Injection for Agents (SIMPLE)
**What**: How agents get workspace context when invoked

**Current BrightBot state**:
```python
class BBState(TypedDict):
    messages: list[dict]
    user_id: str
    workspace_id: str
    # ...existing fields...
```

**ADD** (minimal, not overbuilt):
```python
class BBState(TypedDict):
    # ...existing fields...

    # Data lake context (fetched once per conversation)
    workspace_context: dict | None  # {
    #   "workspace_id": "ws-123",
    #   "total_assets": 150,
    #   "master_datasets": ["org_a.customers"],
    #   "quality_sla": 0.80,
    #   "compliance_frameworks": ["GDPR", "HIPAA"]
    # }
```

**Fetch once**, cache in Redis (5-min TTL), inject into agent prompts.

**NOT overbuilt**:
- ❌ Don't fetch entire Neo4j graph (too slow)
- ❌ Don't track user behavior (not needed for M1)
- ❌ Don't build multi-tier memory system (over-engineering)

**Deliverable**:
- BBState extension spec (add workspace_context field)
- Context fetch function (query Neo4j/DynamoDB for workspace metadata)

**Owner**: AI/ML Lead

---

## Sprint Summary

### Epics: 4 (DATA-FOCUSED)
1. **BH-110**: Data Asset Context Model (9 tasks)
2. **BH-113**: Audit & Monitoring (3 tasks, data-focused)
3. **BH-114**: UX WebApp Re-design (3 tasks, catalog-focused)
4. **BH-115**: Connector Spec (3 tasks, data ingestion)

**Bonus** (if time):
5. **Agent Integration**: 2 tasks (lightweight, not overbuilt)

### Total Tasks: 20 (vs 40 in previous over-designed version)

### Focus: DATA LAKE CONTEXT, NOT USER BEHAVIOR

**What we're building**:
- Rich metadata for datasets (quality, freshness, lineage, governance)
- Cross-org schema matching
- Lineage capture from Glue, DBT, Redshift
- Context versioning and auditing
- Context-rich data catalog UI

**What we're NOT building** (yet):
- User behavioral tracking (defer to Phase 1 of BH_V3)
- Conversation history (defer to M2)
- Proactive notifications (defer to M3)
- Recommendation engine (defer to M4)

**Why this is right**:
- M1 goal: "Core architecture + foundations"
- Can't build AI-first features without rich data lake context
- Can't track user behavior on datasets that have no context
- Can't recommend datasets that have no quality/freshness scores

---

## Success Criteria

### Design Completeness
- [ ] Neo4j schema extended with asset context (quality, freshness, governance)
- [ ] SchemaVersion node design complete (schema evolution tracking)
- [ ] Lineage graph design complete (dataset, transformation, column levels)
- [ ] Cross-org schema similarity algorithm designed
- [ ] Context snapshot strategy designed (versioning)

### Integration Validation
- [ ] Lineage capture pipeline designed (Glue, DBT, Redshift)
- [ ] Connector metadata spec defined (JSON schema)
- [ ] Agent query API designed (GraphQL queries)
- [ ] Context audit log designed (DynamoDB + CloudWatch)

### Data Lake Monitoring
- [ ] Data quality metrics defined
- [ ] Monitoring stack decision (CloudWatch + X-Ray)
- [ ] Data lake alarms defined (quality, freshness, lineage)

### UI/UX
- [ ] Context-rich catalog UI designed
- [ ] Lineage visualization designed
- [ ] Configuration UI designed

### Documentation
- [ ] Connector developer guide written
- [ ] Agent query examples documented
- [ ] Monitoring runbook written

---

## What Moves to Sprint 2

**Implementation**:
- Write Neo4j migration scripts
- Implement lineage capture Lambdas
- Build context-rich catalog UI
- Set up CloudWatch alarms
- Implement connector metadata ingestion

**Agent Features** (lightweight, M2 prep):
- Context injection middleware
- Agent query API implementation

**Behavioral Tracking** (BH_V3.md Phase 1):
- Deferred to M2 (after rich data lake context exists)

---

## Alignment Check

**M1 Goal**: Core architecture + UX + foundations

**This Sprint 1**: ✅ Builds core context architecture for data lakes

**BH_V3.md Vision**: Transform to AI-first companion

**This Sprint 1**: ✅ Enables AI-first features by providing rich context data

**Expert Reviews**: CTO, AI/ML, AWS concerns

**This Sprint 1**: ✅ Addresses integration gaps, storage strategy, monitoring decisions

---

## Next Steps

1. **Review** this refocused plan with team
2. **Prioritize** tasks (which 15 tasks are critical path for 2-week sprint?)
3. **Workshop** (Jan 13): Review data lake context engineering goals
4. **Kickoff**: Start Sprint 1 with integration validation upfront

**Key message**: We're building **data lake intelligence** (context about assets, lineage, quality, governance), not **user-facing AI features** (yet).
