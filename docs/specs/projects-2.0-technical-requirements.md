---
title: "Brighthive Projects 2.0 — Technical Requirements"
status: "Source doc — reconciled, superseded in scope by docs/specs/THEME-spec-driven-pipelines.md"
created: "2026-09-16"
companion: "projects-2.0-design-spec.md"
---

> **Reconciliation note (2026-09-16):** this document proposed three requirements. Two of them
> (the pipeline-to-data-product visualizer, and proactive agentic monitoring) turned out to
> restate already-scoped, already-partially-shipped work —
> [THEME-honest-surfaces.md](THEME-honest-surfaces.md) +
> [THEME-governance-enforced.md](THEME-governance-enforced.md) item 6 for the visualizer, and
> [THEME-fleet-self-healing.md](THEME-fleet-self-healing.md) +
> [THEME-blast-radius-quality.md](THEME-blast-radius-quality.md) for the monitoring. Only the
> Spec-Driven Development requirement (§2) was genuinely new, and it went through three rounds of
> red-team correction before becoming [THEME-spec-driven-pipelines.md](THEME-spec-driven-pipelines.md) —
> see that file for the current, corrected build target. This document is kept as the original
> source/reference, not as a build target in its own right. Full reconciliation trail:
> `agentic-project-mgmt` PR #191.

Audience: Engineering team (implementation via Claude Code) Companion doc: projects-2.0-design-spec.md (Claude Design) Status: Draft — capability discipline applies: anything below marked [SIGN-OFF: Matt Gee] is a write-path or autonomy-expanding capability and must not be represented externally (demos, contracts, RFPs) until confirmed shipped.


0. Scope recap
Three requirements, building on the existing platform (five-layer context substrate, BrightAgent Supervisor + Ingestion/Engineering/Quality/Governance/Analysis agents, MCP two-plane interface, Project Spec/Pipeline/Observability tabs already in production):

Spec-Driven Development (SDD): narrative .md spec(s) → BrightAgent builds the pipeline → continuous verification against spec.
Pipeline-to-Data-Product Visualizer: a typed graph spanning source → transform → quality → product → consuming application.
Proactive Agentic Monitoring: root cause + impact analysis + fix authoring, using logs/dbt/Snowflake/GitHub, with verification agents gating every step.

This is additive to the existing Engineering Agent, Quality Agent, and MCP resource/tool plane documented in the Agentic Capability & MCP Spec — not a parallel system. New agents introduced here should be implemented as new skills on existing agents where possible, and new agents only where a genuinely distinct specialization is warranted (see §5).


1. Architecture overview
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (Projects 2.0 UI)                                       │
│  Spec tab · Graph tab · Observability tab                        │
│  React + graph canvas (existing pipeline-graph renderer, extended)│
└───────────────┬───────────────────────────────────────────────────┘
                │ REST/GraphQL (Platform Core API)
┌───────────────▼───────────────────────────────────────────────────┐
│ Platform Core API (brighthive-platform-core)                     │
│  Spec Service · Graph Service · Incident Service                 │
└───────────────┬───────────────────────────────────────────────────┘
                │
┌───────────────▼───────────────────────────────────────────────────┐
│ BrightAgent Supervisor (CEMAF orchestrator)                       │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐ ┌───────────┐│
│  │ Spec Agent  │ │ Engineering  │ │ Quality Agent │ │ Monitoring││
│  │ (new)       │ │ Agent        │ │ (existing +   │ │ Agent (new│
│  │             │ │ (existing)   │ │  RCA skills)  │ │ skills)   ││
│  └─────────────┘ └──────────────┘ └───────────────┘ └───────────┘│
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Verification Agents (Spec-Conformance, Fix, Impact) — new    │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────┬───────────────────────────────────────────────────┘
                │ MCP (read-only context) + governed write tools
┌───────────────▼───────────────────────────────────────────────────┐
│ Context substrate (existing): Enterprise Knowledge Graph (Neo4j,  │
│ extended with Projects 2.0 ontology) · Metadata Engine ·          │
│ Workspace Context File · User Memory · Smart Compaction           │
└───────────────┬───────────────────────────────────────────────────┘
                │
┌───────────────▼───────────────────────────────────────────────────┐
│ External systems (customer data plane): dbt Cloud/Core, Snowflake,│
│ Databricks, ADF, GitHub, Slack, SQL Server/SSIS                  │
└─────────────────────────────────────────────────────────────────┘

All new agent capabilities inherit the platform's existing invariants: run inside the customer data plane, authenticate through the platform IdP (Entra ID / Cognito), every write routes through governance + human PR review, every action audit-logged.


2. Requirement 1 — Spec-Driven Development
2.1 Spec file format
A project spec is one or more markdown files under a project's /spec directory. Required frontmatter + section conventions (parseable, not just human-readable):

---
project_id: <uuid>
spec_version: 3
depends_on: []            # other spec files in this project, for multi-file specs
owner: <user_id>
---

Canonical H2 sections a parser recognizes (files may split these across multiple documents; the parser merges by section name across all files in /spec):

Section
Purpose
Parsed into
Goal / Description
Narrative intent, business goal, success metric
Project.goal, Project.metrics
Source systems
Tables/feeds, join keys, connection refs
DataSource, Connector nodes
Key columns
Column-level semantics per source
Node properties on source/table nodes
Transform logic
Numbered steps: joins, filters, aggregations
SQLModel nodes + edges, in execution order
Data quality / expectations
Thresholds, null checks, uniqueness, freshness SLAs
DataQualityTest nodes, gating edges
Outputs
Output tables/marts, purpose
DataProduct nodes
Consumers / Applications
Downstream apps, dashboards, notify list
Application nodes, notification routing
Failure handling (optional)
What "same class of failure" means for this pipeline, escalation rules
Monitoring Agent config (see §4.4)


This schema is a formalization of the existing Spec tab content (already observed: Goal, Source systems, Key columns, Transform logic, Outputs) — it does not require re-authoring current specs, only adding recognizable section headers and optional frontmatter.
2.2 Spec Agent (new agent)
Capability: Parses one or more spec .md files into a canonical Pipeline Intent Graph (typed nodes/edges per the ontology in §3), diffs it against the current compiled graph, and hands the delta to the Engineering Agent to build.

Skills:

Skill
Inputs
Outputs
Sch
Pro
Handoffs
Spec Parsing & Merge
/spec/*.md, frontmatter
Pipeline Intent Graph (JSON)
N
N
→ Verification (conformance check)
Intent-to-Build Diff
Intent Graph, current compiled graph
Structured diff (add/remove/modify per node)
N
N
→ Eng (build), → UI (diff preview)
Spec Template Seeding
Project type selection
Pre-filled /spec file tree
N
N
← UI new-project flow
Natural-Language Spec Q&A
Free-text question about the spec
Answer grounded in parsed spec
N
N
none (read-only)


Non-negotiable: Spec Agent never writes dbt/SQL directly. It hands the diff to the existing Engineering Agent (propose_transformation, already gated, PR-only) to actually author models. This keeps write authority in one place.
2.3 Verification Agents (new)
Two distinct verifiers, both read-only, both scheduled + on-demand:

Spec-Conformance Verifier

Compares the live, deployed pipeline (actual dbt models, actual table schemas, actual tests as they exist in the warehouse/repo) against the current Pipeline Intent Graph.
Flags: nodes in spec but not deployed, nodes deployed but not in spec (drift/manual changes), transform logic mismatches (e.g., spec says LEFT JOIN, deployed model does INNER JOIN).
Output: VerificationResult (see §2.4) surfaced as the per-section badge in the Spec tab and the node-level status in the Graph tab.
Runs: on every spec save (debounced), on every dbt/model deploy webhook, and on a schedule (default daily).

Spec Coverage Verifier

Confirms every Data quality expectation in the spec has a corresponding deployed test (Great Expectations suite), and that every Outputs entry is registered as a DataProduct.
Prevents "spec says we validate freshness, nothing actually checks freshness" gaps.

Both verifiers are read-only against governed context (MCP get_structure_details, get_lineage, get_asset_quality) plus a new read tool, get_deployed_definition(asset_id), that pulls the actual dbt/SQL source for comparison — this needs to be added to the MCP tool table.
2.4 Data model additions
Spec              (id, project_id, files[], version, updated_at, updated_by)
SpecSection       (spec_id, heading, raw_markdown, parsed_json)
PipelineIntentGraph (spec_id, version, nodes[], edges[])   -- see §3 for node schema
VerificationResult (id, target_type[spec_section|node], target_id, verifier,
                     status[verified|drift|pending|not_built], detail_json, checked_at)
2.5 API surface (Platform Core additions)
GET /projects/{id}/spec — file tree + rendered content + per-section verification status
POST /projects/{id}/spec/compile — triggers Spec Agent parse → Engineering Agent build; returns diff preview (does not write until confirmed)
POST /projects/{id}/spec/compile/confirm — applies the previously previewed diff (opens PR via Engineering Agent — never auto-merges)
POST /projects/{id}/spec/verify — triggers Verification Agents on demand
GET /projects/{id}/spec/verification — current verification status per section/node


3. Requirement 2 — Pipeline-to-Data-Product Visualizer
3.1 Node ontology (v1)
This is the formal schema behind the design spec's visual palette (§5.2 of the design doc). All nodes are stored as typed entities in the Enterprise Knowledge Graph (Neo4j), extending the existing catalog/lineage model rather than creating a parallel store.

Type
Description
Key properties
Produced by
DataSource
External system of record
system, connection_ref, sensitivity
Ingestion Agent / manual registration
Connector
Scheduled/triggered ingestion job
schedule, last_run_status
Ingestion Agent
RawTable / StagedTable
Landed, pre-transform data
schema, row_count, freshness
Ingestion Agent
SQLModel (aka Transform)
A dbt model or equivalent transform
engine[dbt|ADF|Cortex|Databricks], sql_ref, materialization
Engineering Agent
View
Non-materialized read layer
sql_ref
Engineering Agent
SemanticView / Metric
OSI-defined semantic/metric definition
osi_ref, metric_formula
Engineering Agent
DataQualityTest
Great Expectations suite / test
suite_ref, last_result, pass_rate
Quality Agent
DataContract
Schema/SLA agreement between two nodes
schema_ref, sla
Ingestion/Quality Agent
DataProduct
Registered, cataloged, governed output
catalog_id, owner, consumers[]
Engineering Agent (auto-register)
Application
Downstream consumer (BI tool, dashboard, API, app)
consumer_type, endpoint_ref
Governance Agent (registration)
AgentAction
A discrete agent-executed step in the graph (e.g. an inline quality check)
agent, skill, status
Any agent
PullRequest
Overlay entity, not a structural graph node — attaches to the node(s) it modifies
repo, pr_number, status, diff_ref
Engineering Agent


Edges are typed: feeds_into, tested_by, governed_by, registered_as, consumed_by, depends_on (column-level where available, reusing existing OpenLineage-backed attribute lineage).

This ontology is v1 and intentionally extensible — new types (e.g., MLFeature, Notebook) should be addable without a schema migration that breaks existing nodes; use a node_type discriminator + JSON properties bag, not per-type tables.
3.2 Graph service
Extends the existing Enterprise Knowledge Graph (Neo4j) rather than introducing a second graph store.
New read API: GET /projects/{id}/graph?view=full|pipeline|products|impacted_by={incident_id} returns nodes/edges with current status overlay (last run, quality score, drift flag, open PR count) in one payload — avoid N+1 status calls from the frontend.
Graph writes only happen as a byproduct of Ingestion/Engineering/Quality agent actions (each agent already registers its outputs into the knowledge graph per current architecture) — the Graph tab is a read/visualize surface, not a direct-edit canvas, in v1. [SIGN-OFF: Matt Gee] if a future version allows drag-to-edit the graph as a way of authoring spec changes — that would be a new write path and needs explicit confirmation before any external representation.
3.3 Frontend rendering
Extend the existing pipeline-graph renderer (already rendering SQL/AGENT typed cards with In/Out counters, per current Pipeline tab) rather than adopting a new graph library — add the additional node types and swim-lane layout described in the design spec.
Diff/ghost rendering mode (spec-declared vs. deployed) is a client-side render mode over the same graph payload, driven by VerificationResult data — no separate backend endpoint needed beyond what §3.2 already returns.


4. Requirement 3 — Proactive Agentic Monitoring
4.1 Monitoring Agent (new agent, or new skill set on Quality Agent — recommend extending Quality Agent to avoid supervisor sprawl, since it already owns "Pipeline/Infra Health Monitoring" and "Drift & Anomaly Detection")
New/extended skills:

Skill
Inputs
Outputs
Handoffs
Multi-Source Log Aggregation
dbt Cloud/Core run logs, GitHub Actions logs, Snowflake query history, SSIS/ADF run history
Normalized failure event
→ RCA
Failure Fingerprinting & Recurrence Detection
Failure event, historical fingerprints
Failure class ID (new vs. recurring), match confidence
→ RCA, → UI (recurrence badge)
Root-Cause Diagnosis (existing, extended)
Failure event, lineage, logs
Plain-language RCA + evidence citations
→ Impact Analysis
Impact / Blast-Radius Analysis (new)
Failed node, dependency graph
Downstream break-set: affected tables, data products, applications, severity
→ Fix Proposal, → UI
Fix Proposal (existing, extended)
RCA + impact report
Scoped PR via Engineering Agent
→ Fix Verifier
Notification Routing
Incident, owner mapping (from spec Consumers/Failure handling section)
Slack message + notification-center entry
→ Sup

4.2 Log/system access requirements (new MCP read tools)
Tool
Access
Source
Returns
get_dbt_run_logs(run_id)
Read
dbt Cloud/Core API
Full run log, per-model status, compiled SQL
get_github_actions_log(repo, run_id)
Read
GitHub API
CI run log, step-level status
get_snowflake_query_history(query_id | time_range)
Read
Snowflake ACCOUNT_USAGE / Information Schema
Query text, error, warehouse, credits used
get_deployed_definition(asset_id)
Read
dbt manifest / warehouse
Actual deployed SQL/schema for conformance checks (shared with §2.3)


All are read-only, credential-stripped before any output reaches chat/Slack (matches existing Quality Agent alert redaction behavior), and pass through the same identity/RBAC gate as every other MCP call.
4.3 Root cause + impact analysis flow
Failure event (poller detects dbt/job failure)
   │
   ▼
Fingerprint failure (error signature + node + upstream state)
   │
   ├── Matches existing class? ──► Attach to existing Incident (no new alert spam)
   │                                └─► Check: has the same-class fix already been proposed/merged
   │                                     before? If yes and it recurred, escalate severity —
   │                                     the prior fix didn't hold.
   │
   └── New class ──► Create new Incident
   │
   ▼
Root-Cause Diagnosis
   - Pull logs (dbt, GitHub Actions, Snowflake query history)
   - Walk lineage upstream from failed node to find the actual break point
     (a failure surfacing at node D may originate at node A)
   - Produce plain-language RCA + cite evidence
   │
   ▼
Impact / Blast-Radius Analysis
   - Walk lineage DOWNSTREAM from the break point
   - Classify each downstream node: stale data / test failing / product unavailable /
     application-visible impact
   - Produce severity score (e.g., weighted by: is it a registered DataProduct? does it
     have Application consumers? SLA breach?)
   │
   ▼
Fix Proposal (Engineering Agent, existing gated path)
   - Scoped to the diagnosed root cause only — not a broad rewrite
   - PR description auto-includes: cause, diagnosis method, fix rationale (per project brief:
     "describe both what caused the failure, how you diagnosed it, and what the fix is")
   │
   ▼
Fix Verifier (new, see §4.4) ──► human review/merge (never auto-merged)
4.4 Verification Agents (monitoring path)
Fix Verifier

Runs the proposed fix in a sandboxed/dry-run environment (dbt --dry-run or an isolated schema/branch) before the PR is presented for human review.
Confirms: the specific failing test now passes; no new test failures introduced; no schema-breaking changes to nodes not in the diagnosed scope.
Result attached to the PR as a verification band (per design spec §6.2): ✅ Verified in sandbox / ⚠️ Verification incomplete.
[SIGN-OFF: Matt Gee] — sandbox/dry-run execution is a write-adjacent capability (it runs code, even if isolated) and must be confirmed shipped and scoped (which engines support dry-run, what isolation guarantee exists) before it's represented in any customer-facing material.

Impact Verifier

Re-runs the blast-radius analysis after the fix is drafted, confirming the fix doesn't introduce a new, different downstream break. Prevents "fixed A, silently broke B."

Post-Merge Regression Verifier

After a human merges the fix PR, re-checks the same-class failure fingerprint over the following N runs to confirm recurrence has actually stopped (feeds the "did the fix hold" signal referenced in §4.3).
4.5 Data model additions
Incident          (id, project_id, node_id, fingerprint_id, status, severity,
                    created_at, resolved_at)
Fingerprint       (id, error_signature, node_type, first_seen, occurrence_count)
RootCauseHypothesis (incident_id, summary, evidence_refs[], diagnosed_by, confidence)
ImpactReport      (incident_id, affected_nodes[], severity_score, generated_at)
FixProposal       (incident_id, pr_ref, scope_summary, status)
VerificationResult (reuse schema from §2.4; target_type extended to include fix_proposal)
4.6 API surface
GET /projects/{id}/incidents — incident feed (collapsed cards)
GET /projects/{id}/incidents/{incident_id} — full 4-tab detail (diagnosis, impact, fix, timeline)
POST /projects/{id}/incidents/{incident_id}/verify-fix — on-demand re-run of Fix/Impact Verifier
Webhook receivers: dbt Cloud job-finished, GitHub Actions workflow-run, Snowflake task failure (via existing polling/agentless monitoring pattern already used for legacy SQL Server)


5. Agent placement decision (for engineering to confirm during build)
Recommend not creating a large number of new top-level agents. Map new capability to existing agents where the responsibility already lives there:

New capability
Recommended home
Spec parsing, intent graph, diff
New Spec Agent (genuinely new specialization — no existing agent owns "narrative spec → structured intent")
Spec-Conformance / Spec-Coverage Verifier
New lightweight Verification Agent(s) — kept separate from Engineering/Quality specifically so a verifier is never the same agent that authored the thing it's checking (separation of duties, mirrors "Engineering Agent structurally unable to merge its own PR")
Log aggregation, fingerprinting, RCA, impact analysis
Extend Quality Agent (already owns pipeline/infra health monitoring, drift detection, root-cause diagnosis)
Fix authoring
Existing Engineering Agent — no change, already the sole write-path for transformations
Fix Verifier, Impact Verifier, Post-Merge Regression Verifier
Same new Verification Agent family as spec verifiers — one verification specialization, multiple skills, reused across both SDD and Monitoring requirements


This keeps the "verifier is never the author" principle structurally enforced (same pattern as the existing PR-merge restriction) and avoids agent sprawl.


6. Non-functional requirements
Governance parity: every new MCP tool (§4.2) is read-only and passes through the same RBAC/ABAC + audit logging as existing tools. No new tool bypasses the identity/enforcement layer described in the existing MCP spec.
No silent writes: Spec Agent's diff-then-confirm flow (§2.5) and every fix path terminate at a human-reviewed PR. There is no code path from "agent detects a problem" to "code is merged" without a human action in between, in this version.
Latency targets: Spec-Conformance Verifier debounced re-check ≤ 30s after spec save; incident RCA+impact analysis target ≤ 2 min from failure detection to a posted diagnosis (matches existing alert-delivery expectations).
Multi-tenancy: all new entities (Spec, Incident, PipelineIntentGraph, etc.) are scoped by project_id and inherit existing workspace-level tenant isolation — no cross-project graph traversal without explicit cross-project permission (relevant for Virginia Works-style federated deployments).
Backward compatibility: existing single-file specs and the current Pipeline tab's step-chain view must continue to work unmodified; multi-file specs and the full lifecycle Graph view are additive.


7. Phasing recommendation
Phase 1: Formalize spec parsing (§2.1–2.2) + Spec-Conformance Verifier (read-only, no new write path) + node ontology in the knowledge graph (§3.1) surfaced in the existing Pipeline tab with new node types. Lowest risk, no new sign-off items.
Phase 2: Full Graph tab (swim lanes, filters, diff mode) + Incident Workspace UI (§4, using existing Quality Agent RCA/fix-proposal skills, extended with fingerprinting and impact analysis).
Phase 3: Fix Verifier / sandboxed dry-run execution — gated on Matt Gee sign-off given the write-adjacent nature; do not schedule client-facing demos of this phase until confirmed.


8. Items requiring Matt Gee sign-off before any external representation
Sandbox/dry-run fix execution (§4.4, Fix Verifier)
Any future drag-to-edit authoring on the Graph canvas (§3.2)
Cross-engine dry-run support claims (which engines actually support isolated dry-run today — dbt vs. ADF vs. Cortex vs. Databricks may differ)
