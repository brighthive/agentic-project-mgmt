---
title: "Lineage-Aware Data Quality — glue dbt/Databricks' own lineage to pre-ELT source health and post-ELT Gold/Diamond impact"
epic: "BH-1061"
author: "drchinca"
status: "Draft"
created: "2026-07-12"
generates: "tickets"
tags: [lineage, data-quality, longitudinal-monitoring, dbt, databricks, gold, diamond, brightbot, neo4j]
related:
  specs: ["longitudinal-monitoring.md", "longitudinal-monitoring-capability.md", "proactive-pipeline-ingestion-monitoring.md"]
---

# Lineage-Aware Data Quality

## Start Here

**The problem in one sentence**: a pipeline can run with ZERO errors while silently producing
WRONG numbers, because a source column degrading (NULLs where real values used to be) doesn't
crash anything — it just poisons every downstream table that touches it, with no alert anywhere.

**The reframe that shapes this whole spec**: BrightHive does **not** build lineage computation
from scratch. dbt and Databricks already compute their own lineage internally. BrightHive's
job is to be the **glue** — connect what happens *before* ingestion (is the source degrading)
to the lineage those tools already know, to what happens *after* transformation (does this
break a Gold/Diamond table, a dashboard, a number the CFO looks at) — because dbt/Databricks
structurally cannot see before their own input or after their own output.

**Not achievable by 2026-07-17** — this is genuinely new, multi-week work. Scoped into the
Loop Capital trial plan (`../../clients/trials/loopcapital/`) as an honest post-demo
workstream, not a demo-day deliverable.

## 1. Context

### The scenario that exposed the gap

A full ELT pipeline runs. Every stage succeeds — extraction, load, every dbt model compiles
and runs clean. Partway through, a source column that used to carry real values starts
sending NULLs (or garbage). Nothing crashes, because NULL is a valid value — there's no
exception to catch. That column flows through joins and aggregations into Gold/Diamond
(mart-layer, business-facing) tables. The resulting numbers are now wrong. Nobody finds out
until a human looks at a report and something looks off — by which point the damage (a wrong
number in front of a customer or exec) has already happened.

### What's real today (verified 2026-07-12, by reading actual code — not assumed)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  TODAY: three islands, no bridge between them                              │
└─────────────────────────────────────────────────────────────────────────────┘

  SOURCE                    ELT PIPELINE                  GOLD / DIAMOND
  ┌──────────┐              ┌──────────────┐              ┌──────────────┐
  │ column X │─────────────▶│ dbt models   │─────────────▶│ mart tables  │
  │ starts   │   (no error, │ run clean,   │  (no error,  │ now wrong,   │
  │ sending  │   NULL is a  │ zero job     │   silent     │ nobody knows │
  │ NULLs    │   valid type)│ failures     │   corruption)│ until a human│
  └──────────┘              └──────────────┘              │ notices      │
       │                           │                       └──────────────┘
       │                           │
       ▼                           ▼
  ┌─────────────────┐       ┌──────────────────┐
  │ Longitudinal     │       │ dbt's OWN lineage │      ◀── these two things
  │ monitoring       │       │ (manifest.json)   │          ALREADY EXIST,
  │ (GC-12) — CAN    │       │ ALREADY computed  │          BrightHive just
  │ catch this null  │       │ by dbt itself,    │          doesn't consume
  │ spike... IF a    │       │ never fetched/    │          either one for
  │ human already    │       │ parsed by         │          this purpose
  │ configured       │       │ brightbot today   │
  │ monitoring on    │       └──────────────────┘
  │ THIS column       │
  └─────────────────┘

  GAP 1: nobody watches an "obscure" source column by default — you configure
         monitoring on it only AFTER it has already broken something once.
  GAP 2: even if the anomaly IS caught, nothing today can answer "which Gold/
         Diamond tables does this actually poison" — no lineage traversal
         exists, column-level or even model-level (model-level degrades to a
         regex grep for ref(), spec-only, unbuilt — SPEC-DBT-LINEAGE-AND-STAGE-OPS.md).
  GAP 3: the connective tissue between "anomaly detected" and "here's the
         blast radius" is EXPLICITLY on record as deferred (BH-673) — someone
         already identified this exact gap and parked it.
```

### The proposal: BrightHive as the glue layer, not a lineage engine

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│  PROPOSED: BrightHive consumes dbt/Databricks' OWN lineage, glues before + after   │
└───────────────────────────────────────────────────────────────────────────────────┘

   PRE-ELT                        DURING ELT                         POST-ELT
   (BrightHive-native,            (dbt/Databricks compute            (BrightHive-native,
    already real — GC-12)         this themselves — we just          needs new lineage-
                                   consume it, don't rebuild it)      walk logic)

  ┌──────────────┐              ┌─────────────────────────┐        ┌──────────────────┐
  │ Longitudinal  │              │  dbt manifest.json /     │        │ Gold / Diamond    │
  │ monitoring    │   detects    │  catalog.json            │  walk  │ tables named as   │
  │ (null_spike,  │─────────────▶│  (model + column DAG,    │───────▶│ "affected" in the │
  │ row_count_    │   anomaly    │  dbt already wrote this) │ forward│ SAME alert that   │
  │ drift, etc.)  │   on column  │                          │        │ fired the anomaly  │
  │  SHIPPED      │   X          │  Databricks Unity        │        │  NEW (BH-1064)     │
  └──────────────┘              │  Catalog system tables   │        └──────────────────┘
                                  │  (table_lineage /        │
                                  │  column_lineage) — same   │
                                  │  idea, once a Databricks  │
                                  │  connection exists        │
                                  │                          │
                                  │  BrightHive: fetch +      │
                                  │  parse this artifact,     │
                                  │  load into Neo4j as a     │
                                  │  queryable graph          │
                                  │   NEW (BH-1062, BH-1063)  │
                                  └─────────────────────────┘

  Net result (CORRECTED pass 4 — no rendered Slack message exists to quote today):
  the anomaly's JSON metadata blob gains a new key —
  metadata["longitudinal"]["downstream_tables"] = ["mart.customer_ltv",
  "mart.revenue_by_segment"] — attached to the SAME notification event as the
  null_spike, before a human looks at the wrong number. Whatever renders that
  JSON into visible Slack/webapp text (if anything does today) is OUTSIDE
  brightbot/platform-core backend code — unverified, flagged for a future pass.
```

**CONFIRMED pass 5 (BH-1065), not merely "unverified" anymore — this is worse than flagged**:
checked `brightbot-slack-server` and `brighthive-webapp` directly. Neither has ANY code path
for a longitudinal/anomaly notification. Both repos' notification pipelines are closed switch
statements over a fixed stage enum (`quality_checks`, `pipeline_failure`, `dbt_run_*`,
`schema_drift`, etc.) — there is no `longitudinal_anomaly` case anywhere, and no code reads
`metadata.longitudinal` in either repo (zero grep hits). The one "longitudinal" code that
exists in the webapp (`Governance/components/longitudinalContract.ts`) is RULE-CONFIGURATION
UI (defining which columns to monitor) — completely disconnected from the notification
rendering pipeline, not wired to it at all.

**This means: if a real GC-12 anomaly fires TODAY, no human sees any anomaly detail —
independent of anything this Track C epic adds.** The mutation succeeds, a database row gets
written, and then it dead-ends: Slack renders (at best) a blank/generic fallback, the webapp
inbox shows a generic stage-title card with no anomaly_count/dataset/family content. This is
a pre-existing gap in GC-12 itself, not something introduced by this spec — but it means
**BH-1064's lineage enrichment currently has nothing to enrich that a human will ever see**,
until a NEW ticket (not yet filed, see below) adds a real `longitudinal_anomaly` case to both
repos' notification pipelines.

### Implementation sequence (the 3 new tickets, in order)

**CORRECTED, triple-click-zoom pass 1**: BH-1063 is genuinely 2-repo work, not brightbot-only
— brightbot has no direct Neo4j write access outside one narrow exception, and the original
"mirrors DataAssetNode" precedent doesn't exist. Diagram below reflects the real repo boundary.

```
  brightbot                      brightbot ──HTTP──▶ platform-core        brightbot
  ┌──────────┐                   ┌──────────┐        ┌──────────────┐    ┌──────────┐
  │ BH-1062  │                   │ BH-1063a │        │ BH-1063b     │    │ BH-1064  │
  │ Fetch +  │──────────────────▶│ call OGM │───────▶│ NEW           │───▶│ Wire      │
  │ parse    │                   │ mutation │        │ LineageNode│    │ anomaly → │
  │ manifest │                   │ (existing│        │ + DEPENDS_ON  │    │ graph walk│
  │ .json /  │                   │  ogm_api │        │ + delete-then-│    │ (closes   │
  │ catalog  │                   │  .py     │        │ MERGE mutation│    │  BH-673)  │
  │ .json    │                   │  plumbing│        │ (mirrors      │    │           │
  └──────────┘                   │  — no new│        │ WorkflowStep  │    └──────────┘
                                  │  driver) │        │ Node's own    │
                                  └──────────┘        │ DEPENDS_ON,   │
                                                        │ workflow-spec │
                                                        │ .ts:299-317)  │
                                                        └──────────────┘

"brightbot already      "brightbot calls a NEW       "platform-core owns the    "we already have
 knows how to fetch       platform-core mutation       Neo4j schema + upsert —    both halves —
 dbt Cloud artifacts —    the same way it calls        brightbot NEVER touches    longitudinal
 just never asked for     every other OGM write —      Neo4j directly for this"   monitoring fires
 manifest.json before"    no new Neo4j driver code"                               events, dbt
                                                                                   already wrote
                                                                                   its own lineage —
                                                                                   this ticket is
                                                                                   purely the
                                                                                   connective glue"
```

### Use Case / Goal

A workspace has dbt Cloud connected (already true for most customers) and longitudinal
monitoring configured on at least one source column. A source system starts sending
degraded data on that column. Within one polling cycle: the anomaly fires, AND the alert
names the specific downstream Gold/Diamond tables now affected — using lineage dbt itself
already computed, not a new BrightHive-built lineage engine.

### How It Works Today

- **Anomaly detection** (longitudinal monitoring, GC-12): real, shipped, staging-verified.
  Per-column, opt-in only — see `longitudinal-monitoring.md`.
- **dbt's own lineage artifacts**: real, dbt computes and writes `manifest.json`
  (model-to-model `depends_on`) and `catalog.json` (column-level metadata, newer dbt
  versions) after every run. BrightHive's `_fetch_artifact()`
  (`brightbot/agents/dbt_agent/tools/dbt_cloud_tools.py:256-280`) has the auth/HTTP-GET
  plumbing to fetch ANY artifact by name — today it's only ever called with
  `run_results.json`/`sources.json` (`dbt_cloud_tools.py:364,399`). Manifest/catalog are
  never requested.
- **Databricks Unity Catalog lineage**: real, computed by Databricks itself via system
  tables (`system.access.table_lineage`, `system.access.column_lineage`). Zero brightbot
  code references it today (confirmed by grep, consistent with zero Databricks code
  existing at all — see BH-1044).
- **Model-level lineage inside brightbot**: spec-only, unbuilt
  (`SPEC-DBT-LINEAGE-AND-STAGE-OPS.md`, status `draft`, "Authorizes no code"). Today's
  `analyze_model_impact`/`validate_dbt_refs` do a regex grep for `ref()` — downstream-only,
  static, blind to macro-generated refs.
- **The anomaly→lineage bridge**: explicitly deferred (`longitudinal-monitoring.md:112`,
  BH-673, "Anomaly → dbt-agent self-healing bridge — DEFERRED").

### Hard Limitations

- Column-level lineage only exists in dbt's `catalog.json` for newer dbt versions/configs —
  older projects may only have model-level `depends_on`, not column-level edges. The
  implementation must degrade gracefully to model-level tracing when column data isn't
  available, not silently produce wrong/incomplete results.
- Databricks Unity Catalog lineage is gated on a Databricks connection existing at all
  (BH-1044, itself an open decision — see `proactive-pipeline-ingestion-monitoring.md`).
  This spec's Databricks half cannot start before that's resolved.
- This spec does NOT solve "which columns should be monitored in the first place" — that's
  the auto-discovery problem, explicitly out of scope here (see §5).

### Gaps

1. No manifest/catalog fetch or parse exists (BH-1062 closes this).
2. No dbt DAG in Neo4j (BH-1063 closes this).
3. No anomaly→lineage bridge (BH-1064 closes this, and closes the pre-existing BH-673 gap).
4. No Databricks lineage consumption at all (deferred until BH-1044 resolves).
5. No auto-discovery of which source columns are worth monitoring by default (explicitly
   out of scope — see §5 Out of Scope).

## 2. Interface Contract (MDE)

**ARCHITECTURAL CORRECTION, pass 5 (Kuri's direct feedback) — this spec was drifting toward
dbt-hardcoded types/function names (originally `DbtLineageNode`, `fetch_dbt_lineage_artifacts`,
now renamed engine-agnostic below) with Databricks treated as an afterthought in prose ("same
idea, once a connection exists"), not a real pluggable seam. Per this org's own `pluggable-scalable.md` rule (Ports & Adapters
everywhere; new engines are config, not code), this spec must define a LINEAGE SOURCE PORT
first, with dbt as the FIRST ADAPTER — not the only path. Databricks (via Unity Catalog) and
any future engine (Apache Airflow lineage, Fivetran, etc.) are additional adapters behind the
SAME port, added by registry entry, not by touching the engine's own code.

```
# THE PORT — engine-agnostic. Every lineage source (dbt, Databricks, future engines) implements
# this Protocol. The engine that walks the graph and enriches alerts (BH-1064) NEVER references
# "dbt" or "Databricks" by name — it only calls this interface.
class LineageSource(Protocol):
    async def fetch_lineage(
        self, *, workspace_id: str, run_context: dict,
    ) -> LineageGraph: ...

@dataclass(frozen=True)
class LineageGraph:
    nodes: dict[str, LineageNode]   # keyed by a source-agnostic unique_id
    has_column_lineage: bool
    fetch_error: str | None
    source_engine: str               # "dbt" | "databricks" | future engines — for observability only,
                                      # never branched on by downstream consumers (BH-1063/1064)

@dataclass(frozen=True)
class LineageNode:
    unique_id: str
    name: str
    depends_on: list[str]
    columns: list[str] | None

# Registry (mirrors the EXACT convention this org already established for pipeline-health
# adapters in the sibling spec proactive-pipeline-ingestion-monitoring.md's
# PIPELINE_SOURCE_ADAPTERS, itself modeled on the real CONNECTION_CLASSES/
# WarehouseConnectionFactory pattern, brightbot/tools/warehouse_connections.py:1230-1259 —
# reuse the SAME registry shape here, don't invent a third variant):
LINEAGE_SOURCE_ADAPTERS: dict[str, type[LineageSource]] = {
    DBT: DbtLineageSource,           # BH-1062 implements this adapter — FIRST, not ONLY
    DATABRICKS: DatabricksLineageSource,  # future, once BH-1044's connection decision lands
}

def build_lineage_source(*, engine: str, config: dict) -> LineageSource:
    return LINEAGE_SOURCE_ADAPTERS[engine](config=config)

# Adding a NEW engine (Apache Airflow's own lineage API, Fivetran, etc.) later = one new
# adapter class + one registry line — the port, BH-1063's graph-write code, and BH-1064's
# walk-and-enrich code NEVER change. This is the concrete meaning of "low-effort to switch."
```

### BH-1062 as the dbt adapter (the FIRST implementation of LineageSource, not the design)

```
# BH-1062: manifest/catalog fetch + parse — SHARPENED pass 2 (triple-click-zoom), verified
# against the REAL _fetch_artifact() signature (dbt_cloud_tools.py:256-280), not assumed:
#
# GAP FOUND 1 — step selection is unaddressed and must be resolved before this is buildable.
# _fetch_artifact()'s real signature is:
#   def _fetch_artifact(api_endpoint, api_token, account_id, run_id, artifact_path,
#                        step: int | None = None) -> str | None
# `step` is OPTIONAL. dbt Cloud's artifact API scopes manifest.json to the STEP that produced
# it (usually the last `dbt run`/`dbt build`/`dbt compile` step) — earlier steps (`dbt deps`,
# `dbt seed`) never have one. brightbot's only 2 existing call sites always pass an explicit
# step_index they already have from a KNOWN failed step — there is no existing "find the step
# that ran dbt build" discovery logic anywhere to copy. RESOLUTION: BH-1062 must call
# `_fetch_run_details_with_logs()` first to get `run_steps`, then select the LAST step whose
# `name`/`run_id` (need to inspect the actual response — TODO: confirm exact field name against
# a real run's run_steps payload, do not assume) matches a compile-producing command
# (`dbt run`|`dbt build`|`dbt compile`), and pass THAT step's index explicitly. Omitting `step`
# entirely and hoping for "most recent artifact" default behavior is UNVERIFIED dbt Cloud API
# behavior — do not rely on it without testing against a real job.
#
# GAP FOUND 2 — 404-vs-real-error conflation. _fetch_artifact() returns None on BOTH a 404
# (artifact genuinely never generated, e.g. run failed before compiling) AND on any other
# requests.HTTPError (auth failure, 500, timeout) — the exception handler is a blanket catch
# that discards the status code. Per Invariant 2, this spec requires distinguishing "column
# lineage unavailable" from a real error — reusing _fetch_artifact() AS-IS would silently
# misreport a transient 500 as "no lineage data," which Invariant 2 explicitly forbids doing
# for column data and should not be allowed for the whole-artifact case either. RESOLUTION:
# BH-1062 needs a THIN wrapper around _fetch_artifact() (not a modification to the shared
# function, which other callers depend on) that re-derives the status code itself (a second,
# minimal precheck HTTP call, or logging a WARNING distinguishing 404 from other failures) so
# a real error doesn't get silently absorbed into "has_column_lineage=False."
async def fetch_lineage_artifacts(
    *, workspace_id: str, job_id: str, run_id: str,
) -> LineageArtifacts: ...
# Reuses _fetch_artifact() (dbt_cloud_tools.py:256-280) with artifact_path="manifest.json"
# and artifact_path="catalog.json" — no new HTTP/auth code, just new artifact-name arguments
# PLUS the step-discovery + error-disambiguation logic above, which IS new code.

@dataclass(frozen=True)
class LineageArtifacts:
    models: dict[str, LineageModelNode]       # keyed by unique_id
    has_column_lineage: bool              # False if catalog.json lacked column metadata
    fetch_error: str | None               # NEW: non-None if a real error occurred (not a
                                           # genuine 404-absent-artifact case) — surfaced so
                                           # callers don't silently treat "errored" as "absent"

@dataclass(frozen=True)
class LineageModelNode:
    unique_id: str                        # fully-qualified, e.g. "model.my_project.stg_orders"
                                           # (general dbt manifest schema knowledge — matches
                                           # dbt's public spec; NOT yet verified against a real
                                           # fetched manifest.json in this codebase, since no
                                           # parser exists yet. Confirm against a real artifact
                                           # before treating this shape as final.)
    name: str
    depends_on: list[str]                 # upstream unique_ids (manifest's depends_on.nodes)
    columns: list[str] | None             # None if catalog.json didn't have this model

# BH-1063: Neo4j load — CORRECTED pass 1 of the triple-click-zoom loop, verified against
# real code, not assumed:
# 1. "Mirrors DataAssetNode's sync pattern" was WRONG — DataAssetNode has no DEPENDS_ON/
#    LINEAGE relationship anywhere (confirmed by reading platform-core's OGM typedefs.ts).
#    "(DataAsset)-[:HAS_LINEAGE]->(DataAsset)" in platform-core's own CLAUDE.md architecture
#    diagram is ASPIRATIONAL — zero code hits, same doc-vs-reality gap found repeatedly
#    elsewhere in this investigation.
# 2. The REAL, concrete precedent is WorkflowStepNode's own DEPENDS_ON relationship —
#    delete-then-MERGE Cypher, hand-written (not OGM @relationship decorator):
#    platform-core/src/graphql/models/workflow-spec.ts:299-317. Same idempotent-replace
#    shape this ticket needs. Copy THIS, not a DataAssetNode pattern that doesn't exist.
# 3. CRITICAL ARCHITECTURAL CORRECTION: brightbot does NOT have general Neo4j write access.
#    It reaches Neo4j almost exclusively through platform-core's OGM GraphQL HTTP API
#    (brightbot/tools/ogm_api.py:34-70, Cognito-authed HTTP, not a direct driver). The one
#    exception (workflow_agent/tools.py:23,92-95, a direct bolt driver) is scoped to simple
#    :Column description writes, not OGM-typed node/relationship creation — NOT a precedent
#    to reuse for LineageNode. THEREFORE: this ticket is NOT purely a brightbot ticket as
#    originally scoped. The Neo4j-side schema + upsert mutation must be added to
#    PLATFORM-CORE (a new OGM type + a GraphQL mutation, following workflow-spec.ts's
#    delete-then-MERGE shape), and brightbot calls that mutation over its existing
#    Cognito-authed OGM HTTP path — the same way it reaches every other Neo4j write today.
async def upsert_lineage_graph(
    *, workspace_id: str, artifacts: LineageArtifacts,
) -> None: ...
# brightbot-side: calls a NEW platform-core GraphQL mutation over the existing OGM HTTP
# path (ogm_api.py) — it does not touch Neo4j directly.
# platform-core-side (NEW scope, not previously called out): a mutation implementing the
# delete-then-MERGE pattern from workflow-spec.ts:299-317, targeting a new LineageNode
# type + DEPENDS_ON relationship.
#
# SHARPENED pass 3 (triple-click-zoom) — verified against the REAL WorkflowStepNode OGM type
# and upsertWorkflowStep mutation, not a paraphrase:
#
# EXACT OGM type to model LineageNode after (WorkflowStepNode,
# platform-core/src/graphql/ogm/workflow-spec-typedefs.ts:79-97):
#   type LineageNode {
#     id: ID! @id
#     uniqueId: String!              # dbt's fully-qualified unique_id, e.g. "model.proj.stg_orders"
#     name: String!
#     hasColumnLineage: Boolean! @default(value: false)
#     createdAt: DateTime! @timestamp(operations: [CREATE])
#     modifiedAt: DateTime! @timestamp(operations: [CREATE, UPDATE])
#     dependsOn: [LineageNode!]! @relationship(type: "DEPENDS_ON", direction: OUT)
#   }
# CONFIRMED: WorkflowStepNode has NO native workspaceId field either — scoping is transitive
# via a parent relationship (step.spec.project.workspaceId). LineageNode has the same
# problem (no natural parent to scope through) — the mutation's INPUT must carry workspaceId
# explicitly and the @authorized directive must reference it there (see mutation shape below),
# mirroring upsertWorkflowStep's own pattern exactly.
#
# EXACT Cypher precedent (workflow-spec.ts:300-314, upsertWorkflowStep) — quoted verbatim,
# not paraphrased:
#   MATCH (step:WorkflowStepNode {id: $stepId})-[r:DEPENDS_ON]->() DELETE r
#   -- then, if there are new deps:
#   MATCH (step:WorkflowStepNode {id: $stepId})
#   UNWIND $depIds AS depId
#   MATCH (dep:WorkflowStepNode {id: depId})
#   MERGE (step)-[:DEPENDS_ON]->(dep)
#   RETURN count(dep) AS linked
#
# MUST be a NEW, independently-callable mutation, not a side effect — confirmed
# upsertWorkflowStep is its OWN public Core API mutation
# (schema/typedefs.ts:4819-4822, `@authorized(prohibits: [...], workspaceIdLoc: [...])`),
# not triggered internally by another mutation. BH-1063 needs its own equivalent
# `upsertLineageGraph(input: UpsertLineageGraphInput!)` mutation registered the same way.
#
# CRITICAL CORRECTNESS GAP FOUND IN THE PRECEDENT ITSELF — do not silently inherit this:
# the real workflow-spec.ts pattern is NOT atomic. The DELETE and the MERGE run as two
# SEPARATE auto-commit `session.run()` calls on the same session (`workflow-spec.ts:302-314`),
# not wrapped in `session.writeTransaction(...)` and not one multi-statement query. If the
# process crashes between the DELETE and the MERGE, a step is left with ZERO DEPENDS_ON edges
# — deleted but never re-created. For BH-1063, this same gap would mean a crash mid-upsert
# could silently leave a dbt model with NO lineage edges, which downstream (BH-1064) would
# read as "nothing depends on this" — a false negative that suppresses a real alert. THIS
# SPEC SHALL NOT silently copy the non-atomic version — see Invariant 9 below.

# BH-1064: the bridge (closes BH-673)
#
# MAJOR CORRECTION, pass 4 (triple-click-zoom) — verified against real code, not the earlier
# draft's assumption. "Reuses BH-1046's existing dual-write alert path — no new delivery
# mechanism" was WRONG in a way that changes this ticket's actual scope:
#
# AnomalyEventNode's REAL shape (platform-core/src/graphql/ogm/typedefs.ts:713-727):
#   type AnomalyEventNode {
#     id: ID! @id
#     detectedAt: DateTime!
#     dataset: String!        # e.g. "GOLD.mart_daily_portfolio_exposure" — the lookup key
#     metricName: String!     # e.g. "null_rate:customer_id" — column sometimes encoded, not structured
#     family: String!         # row_count_drift | cardinality_breakdown | distributional_skew | null_spike
#     severity: String!       # warning | error
#     currentValue: Float!
#     baselineValue: Float!
#     deviationPct: Float!
#     description: String!
#     runId: String!
#     dataAsset: DataAssetNode! @relationship(type: "HAS_ANOMALY_EVENT", direction: IN)
#   }
# `dataset` is the field BH-1064 reads to start the downstream lookup. Confirmed real, not
# aspirational.
#
# BUT: "BH-1046's alert path" does NOT format anomalies into a Slack message anywhere in
# brightbot or platform-core — confirmed by direct search, not assumed. What actually exists
# (GC-12/BH-669) is `LongitudinalResult.summary()` (longitudinal_node.py:79-88), a plain dict
# whose docstring SAYS "for Slack notification" but nothing downstream renders it as message
# text. It flows into `publish_completion_notification` (quality_check_agent.py:1526-1685),
# which fires a `publishNotification` mutation carrying a `json.dumps(...)` metadata blob —
# NOT a Slack text/blocks payload, and the anomaly detail folded in is just
# `{"longitudinal": {"anomaly_count": N, "families": [...]}}` (lines 1641-1647) — no dataset
# name, no per-anomaly detail, no rendered message anywhere. This whole path is ALSO
# feature-flag gated OFF by default (FeatureFlag.NOTIFICATIONS, lines 1532-1541) and
# short-circuits to a no-op if BH_API_URL/NOTIFICATIONS_API_KEY are unset.
#
# CONSEQUENCE FOR THIS TICKET'S SCOPE: BH-1064 cannot simply "add a clause to an existing
# alert" — there is no existing rendered alert to add a clause to on the backend. The
# insertion point is a NEW key inside the JSON metadata dict
# (e.g. metadata["longitudinal"]["downstream_tables"] = [...]), not a string splice into a
# message template, because no message template exists in brightbot/platform-core. Whatever
# renders this JSON into visible Slack/webapp text (if anything does today) lives outside
# these two repos' backend code — NOT verified in this pass, flag for a future pass to check
# brighthive-webapp and brightbot-slack-server specifically before assuming ANY of this is
# user-visible today, even without lineage enrichment.
async def find_downstream_impact(
    *, workspace_id: str, anomaly: AnomalyEventNode,
) -> list[LineageNode]: ...
# Cypher traversal, keyed off anomaly.dataset (confirmed real field):
#   MATCH (start:LineageNode {name: $anomaly_dataset})
#                   <-[:DEPENDS_ON*1..]-(downstream:LineageNode)
#                   RETURN downstream
# Writes into the metadata dict BEFORE publish_completion_notification's existing
# json.dumps(...) call (quality_check_agent.py:1663) — this ticket adds one new key, it does
# NOT touch or duplicate the existing publishNotification mutation call itself.
```

## 3. Invariants (DbC)

1. `WHEN manifest.json/catalog.json is fetched, THE System SHALL reuse the existing
   _fetch_artifact() plumbing — no new HTTP client, no new auth path.`
2. `IF catalog.json lacks column-level metadata for a model, THEN THE System SHALL degrade to
   model-level tracing and SHALL set has_column_lineage=False — it SHALL NOT silently produce
   a column-level claim it cannot back.`
3. `WHEN an AnomalyEventNode fires on a monitored column, THE System SHALL attempt a
   downstream-impact lookup via the lineage graph before publish_completion_notification's
   existing json.dumps(...) call — the impact list (possibly empty, if lineage data is
   unavailable) SHALL be written into the SAME metadata dict as a new key, not a separate
   notification call. CORRECTED pass 4: there is no rendered Slack/webapp message to append
   a "clause" to in brightbot/platform-core backend code — only a JSON metadata dict exists.
   Whatever renders that JSON into visible text (webapp/slack-server) is UNVERIFIED by this
   spec and must be checked in a future pass before assuming lineage data reaches a human at
   all today, even without this ticket's changes.`
4. `WHEN the Neo4j lineage graph is upserted, THE System SHALL treat each dbt run's manifest as
   the source of truth for that run — stale DEPENDS_ON edges from a prior run's now-removed
   dependency SHALL be removed, not merely added-to (idempotent replace per model, not
   append-only).`
5. `THE System SHALL NOT attempt to compute lineage independently of dbt/Databricks' own
   artifacts — if dbt's manifest doesn't have an edge, BrightHive does not infer one.`
6. `WHEN brightbot needs to write lineage data into Neo4j, THE System SHALL call platform-core's
   OGM GraphQL mutation over the existing Cognito-authed HTTP path (ogm_api.py) — it SHALL NOT
   open a new direct Neo4j driver connection. Verified pass 1 (triple-click-zoom loop): brightbot
   has exactly one existing direct-driver exception (workflow_agent/tools.py), scoped to plain
   :Column description writes only — this is NOT a precedent for creating typed nodes/relationships
   and must not be extended for this spec's LineageNode writes.`
7. `WHEN fetching manifest.json/catalog.json returns None from _fetch_artifact(), THE System
   SHALL distinguish a genuine 404 (artifact never generated — e.g. run failed pre-compile)
   from any other HTTP failure (auth error, 500, timeout) before recording has_column_lineage
   or fetch_error. Verified pass 2: _fetch_artifact()'s existing exception handling collapses
   ALL failure modes to None — this spec's wrapper (BH-1062) MUST NOT inherit that conflation;
   a real error surfaces as fetch_error, never silently as "column lineage unavailable."`
8. `WHEN selecting which dbt Cloud run STEP to fetch manifest.json/catalog.json from, THE
   System SHALL explicitly identify the last dbt run/build/compile step via run_steps (from
   _fetch_run_details_with_logs()) and pass that step's index to _fetch_artifact() — it SHALL
   NOT omit the step parameter and rely on unverified "most recent artifact" default API
   behavior. Verified pass 2: no existing brightbot code performs this step-discovery; it is
   new logic this ticket must build, not something to copy from an existing call site.`
9. `WHEN upserting a LineageNode's DEPENDS_ON edges, THE System SHALL perform the
   delete-and-recreate as a SINGLE atomic transaction (session.writeTransaction wrapping both
   the DELETE and the MERGE, or one multi-statement Cypher query) — it SHALL NOT copy
   workflow-spec.ts:300-314's own pattern verbatim, which runs the DELETE and MERGE as two
   separate auto-commit calls with a crash window between them. Verified pass 3: that
   precedent has a real correctness gap (a process crash mid-upsert leaves zero DEPENDS_ON
   edges, which BH-1064 would read as "nothing depends on this" — a false negative that
   suppresses a real alert). Model the SHAPE of the precedent (same Cypher, same node/edge
   pattern), not its transaction-boundary bug.`

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Lineage-aware data quality — glue dbt's own lineage to anomaly detection

  Scenario: null spike on a source column names the affected Gold tables
    Given a workspace with dbt Cloud connected and longitudinal monitoring on column X
    And dbt's manifest.json shows 2 Gold-layer models depend (transitively) on column X's table
    When a null_spike anomaly fires on column X
    Then the SAME alert names both downstream Gold models as affected
    And the alert reaches the user before they would have noticed the wrong number manually

  Scenario: graceful degradation when column-level lineage isn't available
    Given a dbt project whose catalog.json lacks column-level metadata
    When an anomaly fires on a column in that project
    Then the system traces impact at the MODEL level only
    And has_column_lineage=False is recorded, not silently claimed otherwise

  Scenario: stale lineage edges are replaced, not accumulated
    Given a model's manifest.json previously depended on table A
    And a new dbt run's manifest.json shows it no longer depends on table A
    When the lineage graph is upserted from the new manifest
    Then the DEPENDS_ON edge to table A is removed
    And no stale edge causes a false-positive downstream-impact claim later

  Scenario: a real fetch error is never mistaken for "no lineage available"
    Given dbt Cloud returns a 500 (not a 404) when fetching manifest.json for a run
    When BH-1062's fetch wrapper receives this failure
    Then fetch_error is set to a non-None value describing the real failure
    And has_column_lineage is NOT silently set to False as if the artifact were simply absent

  Scenario: the correct run step is selected before fetching artifacts
    Given a dbt Cloud run with 3 steps: "dbt deps", "dbt seed", "dbt build"
    When BH-1062 fetches manifest.json for this run
    Then it first calls run_steps to identify "dbt build" as the last compile-producing step
    And it passes that step's index explicitly to _fetch_artifact()
    And it does NOT omit the step parameter and rely on unverified default API behavior

  Scenario: a crash mid-upsert never leaves a model with zero lineage edges
    Given a LineageNode currently has 3 DEPENDS_ON edges from a prior manifest
    And the upsert transaction for a new manifest is interrupted after the DELETE but before the MERGE completes
    When the system recovers (retry or next scheduled upsert)
    Then the node never observably had zero edges in between — the whole delete-and-recreate is atomic
    And this differs deliberately from workflow-spec.ts's own non-atomic precedent, which has this exact gap
```

## 5. Out of Scope

- **Auto-discovery of which source columns are worth monitoring by default.** This spec
  answers "given an anomaly IS detected, where does it spread" — not "how do we know to watch
  this column in the first place." Related, separate problem; may warrant its own spec if
  pursued.
- **Computing lineage independently of dbt/Databricks.** BrightHive consumes their artifacts;
  it does not parse raw SQL to infer dependencies dbt itself doesn't already know about.
- **Databricks lineage consumption** until BH-1044's connection-model decision resolves.
- **Any UI/visualization of the lineage graph** — this spec is about the alert-enrichment
  bridge, not a lineage-browsing feature (that could be a natural follow-on, not in scope here).

## 6. Dependencies

| Dependency | Type | Status |
|---|---|---|
| Longitudinal monitoring (GC-12, BH-601) | Blocking (this spec enriches its alerts) | Shipped + staging-verified |
| BH-673 (anomaly→lineage bridge) | This spec's BH-1064 closes it | Deferred, now actively scoped |
| `_fetch_artifact()` plumbing (dbt_cloud_tools.py) | Non-blocking (reused, not built here) | Live |
| `WorkflowStepNode`'s `DEPENDS_ON` delete-then-MERGE precedent (`workflow-spec.ts:299-317`) | Non-blocking (pattern mirrored, not reinvented) — corrected pass 1, was wrongly cited as DataAssetNode | Live |
| brightbot's OGM HTTP path (`ogm_api.py:34-70`) | Blocking — BH-1063's brightbot half MUST go through this, no new Neo4j driver | Live |
| **platform-core engineering capacity** (verified pass 1: BH-1063 is 2-repo work) | Blocking — this spec cannot ship with brightbot-only resourcing | New dependency, not previously called out |
| BH-1044 (Databricks connection decision) | Blocking for the Databricks half only | Open decision, not yet confirmed |

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Manifest/catalog fetch + parse (BH-1062) | `brightbot` | New parser module, reuses existing artifact-fetch plumbing |
| Lineage graph schema + upsert mutation (BH-1063b) | **`brighthive-platform-core`** — corrected, was miscast as brightbot-only | New `LineageNode` OGM type + `DEPENDS_ON` relationship + delete-then-MERGE mutation, mirrors `WorkflowStepNode`'s real precedent (`workflow-spec.ts:299-317`), NOT a nonexistent DataAssetNode pattern |
| Lineage graph call site (BH-1063a) | `brightbot` | Calls the new platform-core mutation over the EXISTING `ogm_api.py` HTTP path — no new Neo4j driver code |
| Anomaly-alert enrichment (BH-1064) | `brightbot` (governance_agent) | Extends BH-1046's existing alert path, no new delivery mechanism |

## Ticket Breakdown

| Ticket | Summary | Status |
|---|---|---|
| BH-1061 | Epic: Lineage-Aware Data Quality | Needs Refinement |
| BH-1062 | feat: fetch + parse manifest.json/catalog.json | Needs Refinement |
| BH-1063 | feat: load parsed DAG into Neo4j as queryable lineage graph | Needs Refinement |
| BH-1064 | feat: wire anomalies to walk the graph forward (closes BH-673) | Needs Refinement |
| BH-1065 | verify: does anything render anomaly JSON into visible Slack/webapp text today? | Needs Refinement, filed pass 4 — answer determines whether this whole epic is demo-visible |

## Related

- `longitudinal-monitoring.md` — the anomaly-detection half this spec enriches
- `longitudinal-monitoring-capability.md` — the capability-node interface pattern this spec's
  Neo4j upsert mirrors
- `proactive-pipeline-ingestion-monitoring.md` — sibling spec, shares the BrightSignals alert
  path (BH-1046) this spec's enriched alerts reuse
- `clients/trials/loopcapital/overview.md` — this capability is scoped into Loop Capital's
  plan as an honest post-demo workstream, not a 7/17 deliverable
