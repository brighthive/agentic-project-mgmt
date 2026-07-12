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

  Net result: "null_spike on raw.orders.customer_id" becomes
  "null_spike on raw.orders.customer_id — affects mart.customer_ltv,
  mart.revenue_by_segment (2 Gold tables)" — in one alert, before a human
  looks at the wrong number.
```

### Implementation sequence (the 3 new tickets, in order)

```
BH-1062                        BH-1063                         BH-1064
Fetch + parse          ──────▶ Load DAG into Neo4j    ──────▶  Wire anomaly → graph walk
manifest.json/                 as queryable graph               (closes BH-673, the
catalog.json                   (nodes = models/cols,             already-deferred bridge)
                                edges = depends_on)

"brightbot already      "we have a graph store       "we already have both halves —
 knows how to fetch       (Neo4j) and existing         longitudinal monitoring fires
 dbt Cloud artifacts —    DataAsset sync patterns —    events, dbt already wrote its
 just never asked for     add a sibling node type,     own lineage — this ticket is
 manifest.json before"    don't invent a new store"    purely the connective glue"
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

```
# BH-1062: manifest/catalog fetch + parse
async def fetch_dbt_lineage_artifacts(
    *, workspace_id: str, job_id: str, run_id: str,
) -> DbtLineageArtifacts: ...
# Reuses _fetch_artifact() (dbt_cloud_tools.py:256-280) with artifact_path="manifest.json"
# and artifact_path="catalog.json" — no new HTTP/auth code, just new artifact-name arguments.

@dataclass(frozen=True)
class DbtLineageArtifacts:
    models: dict[str, DbtModelNode]       # keyed by unique_id
    has_column_lineage: bool              # False if catalog.json lacked column metadata

@dataclass(frozen=True)
class DbtModelNode:
    unique_id: str
    name: str
    depends_on: list[str]                 # upstream unique_ids
    columns: list[str] | None             # None if catalog.json didn't have this model

# BH-1063: Neo4j load
async def upsert_dbt_lineage_graph(
    *, workspace_id: str, artifacts: DbtLineageArtifacts,
) -> None: ...
# New Neo4j node type DbtLineageNode (mirrors existing DataAssetNode sync pattern —
# idempotent upsert on every dbt run, not a one-time import).
# Relationship: (DbtLineageNode)-[:DEPENDS_ON]->(DbtLineageNode)

# BH-1064: the bridge (closes BH-673)
async def find_downstream_impact(
    *, workspace_id: str, anomaly: AnomalyEventNode,
) -> list[DbtLineageNode]: ...
# Cypher traversal: MATCH (start:DbtLineageNode {name: $affected_table})
#                   <-[:DEPENDS_ON*1..]-(downstream:DbtLineageNode)
#                   RETURN downstream
# Reuses BH-1046's existing dual-write alert path — no new delivery mechanism.
```

## 3. Invariants (DbC)

1. `WHEN manifest.json/catalog.json is fetched, THE System SHALL reuse the existing
   _fetch_artifact() plumbing — no new HTTP client, no new auth path.`
2. `IF catalog.json lacks column-level metadata for a model, THEN THE System SHALL degrade to
   model-level tracing and SHALL set has_column_lineage=False — it SHALL NOT silently produce
   a column-level claim it cannot back.`
3. `WHEN an AnomalyEventNode fires on a monitored column, THE System SHALL attempt a
   downstream-impact lookup via the lineage graph before finalizing the alert — the impact
   list (possibly empty, if lineage data is unavailable) SHALL be included in the SAME alert,
   not a separate notification.`
4. `WHEN the Neo4j lineage graph is upserted, THE System SHALL treat each dbt run's manifest as
   the source of truth for that run — stale DEPENDS_ON edges from a prior run's now-removed
   dependency SHALL be removed, not merely added-to (idempotent replace per model, not
   append-only).`
5. `THE System SHALL NOT attempt to compute lineage independently of dbt/Databricks' own
   artifacts — if dbt's manifest doesn't have an edge, BrightHive does not infer one.`

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
| Existing Neo4j DataAsset sync pattern | Non-blocking (mirrored, not reinvented) | Live |
| BH-1044 (Databricks connection decision) | Blocking for the Databricks half only | Open decision, not yet confirmed |

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Manifest/catalog fetch + parse | `brightbot` | New parser module, reuses existing artifact-fetch plumbing |
| Lineage graph | `brightbot` + Neo4j | New `DbtLineageNode`/`DEPENDS_ON` structure, mirrors DataAsset sync |
| Anomaly-alert enrichment | `brightbot` (governance_agent) | Extends BH-1046's existing alert path, no new delivery mechanism |

## Ticket Breakdown

| Ticket | Summary | Status |
|---|---|---|
| BH-1061 | Epic: Lineage-Aware Data Quality | Needs Refinement |
| BH-1062 | feat: fetch + parse manifest.json/catalog.json | Needs Refinement |
| BH-1063 | feat: load parsed DAG into Neo4j as queryable lineage graph | Needs Refinement |
| BH-1064 | feat: wire anomalies to walk the graph forward (closes BH-673) | Needs Refinement |

## Related

- `longitudinal-monitoring.md` — the anomaly-detection half this spec enriches
- `longitudinal-monitoring-capability.md` — the capability-node interface pattern this spec's
  Neo4j upsert mirrors
- `proactive-pipeline-ingestion-monitoring.md` — sibling spec, shares the BrightSignals alert
  path (BH-1046) this spec's enriched alerts reuse
- `clients/trials/loopcapital/overview.md` — this capability is scoped into Loop Capital's
  plan as an honest post-demo workstream, not a 7/17 deliverable
