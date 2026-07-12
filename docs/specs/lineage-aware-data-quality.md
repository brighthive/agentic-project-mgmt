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
  │ BH-1062  │                   │ BH-1069  │        │ BH-1063b     │    │ BH-1064  │
  │ Fetch +  │──────────────────▶│ call OGM │───────▶│ NEW           │───▶│ Wire      │
  │ parse    │                   │ mutation │        │ LineageNode│    │ anomaly → │
  │ manifest │                   │ (existing│        │ + DEPENDS_ON  │    │ graph walk│
  │ .json /  │                   │  ogm_api │        │ + delete-then-│    │ (closes   │
  │ catalog  │                   │  .py     │        │ MERGE mutation│    │  BH-673)  │
  │ .json    │                   │  plumbing│        │ (2-3 files,   │    │           │
  └──────────┘                   │  — no new│        │ NO public     │    └──────────┘
                                  │  driver) │        │ schema touch, │
                                  └──────────┘        │ mirrors       │
                                                        │ AnomalyEvent- │
                                                        │ Node OGM-only │
                                                        │ pattern)      │
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
- **CORRECTED pass 7 — Databricks is NOT "gated on BH-1044 resolving," it is a genuinely
  greenfield build regardless of that decision.** Verified by direct code check: zero
  Databricks code exists in brightbot or platform-core outside vendored third-party deps.
  Both `WarehouseType` (`brightbot/utils/warehouse_types.py:20`, Literal of `redshift`,
  `snowflake`, `azure_synapse`, `postgres`) and platform-core's
  `WarehouseServiceProvider` enum (`src/graphql/schema/gql-types.ts:5516-5520`, same 3
  values minus postgres) are CLOSED — Databricks is not a config flip, it requires NEW
  enum members on BOTH sides, a new driver constant, a new concrete
  `WarehouseConnection` subclass in `WarehouseConnectionFactory`
  (`warehouse_connections.py:1238`), and platform-core's OMD service-type mapping
  (`warehouse-service.ts:154-159`) extended too. BH-1044 (brightbot-only secret vs.
  platform-core schema change) decides WHERE credentials live — it does NOT decide
  whether the connection-type plumbing itself needs building, which it does, either way.
  Additionally (general Databricks platform knowledge, not verified in-repo since no
  Databricks code exists to check): `system.access.table_lineage`/`column_lineage` are
  Unity Catalog SYSTEM tables, disabled by default — an account/workspace admin must
  separately enable the `system.access` schema and grant `SELECT` on it, on top of the
  ordinary SQL-warehouse credentials/grants brightbot already uses for Snowflake/Redshift/
  Synapse. This is real, additional setup work per customer, not automatic once a
  Databricks connection exists at all.
- **ADDED pass 8 (user-raised)**: not every customer orchestrates via dbt — some run
  Snowflake-native pipelines directly (Snowpipe continuous ingestion, Tasks, Streams,
  Dynamic Tables). CONFIRMED: `SnowflakeConnection` already exists and can run arbitrary
  `SELECT` against `SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES`/`ACCESS_HISTORY`/
  `TASK_HISTORY` (`warehouse_connections.py:701,714,1233`) — this is a THIRD `LineageSource`
  adapter, cheaper than Databricks (same tier as BH-1062's dbt adapter: reuse an existing
  connection, write a new query + parser, no new connection type). CONFIRMED zero existing
  code queries these views today (grep: zero hits repo-wide for
  `OBJECT_DEPENDENCIES`/`ACCESS_HISTORY`/`TASK_HISTORY`/`Snowpipe`/`DYNAMIC_TABLE`) — this is
  new work, just cheap new work, not free. platform-core's `DataAssetNode`/`Transformation`
  schema has dbt-specific fields (`dbtModelName`, `dbtDependencies`,
  `data-asset.ts:554-596`, `transformation.ts:18-46`) but nothing naming Dynamic
  Table/Snowpipe/Task — new schema fields needed here too, mirroring how `LineageNode`
  itself stays engine-agnostic (§2's `source_engine` field already anticipates this: add
  `"snowflake_native"` as a third value, no port/registry-shape change).
- Also flagged pass 8, NOT scoped: Microsoft Fabric (OneLake/Data Factory/Spark/Power BI)
  was raised as a future candidate engine. Unverified in this codebase (zero Fabric-related
  code exists to check) — flagged as likely Databricks-tier cost (new connection type, no
  existing path) given Fabric's own multi-language internal split (T-SQL/PySpark/DAX/KQL/
  Power Query M), not Snowflake-native-tier cost. Do not build until a Fabric-committed
  customer actually requires it — this is a placeholder note, not a ticket.
- This spec does NOT solve "which columns should be monitored in the first place" — that's
  the auto-discovery problem, explicitly out of scope here (see §5).

### Gaps

1. No manifest/catalog fetch or parse exists (BH-1062 closes this).
2. No dbt DAG in Neo4j (BH-1063 closes this).
3. No anomaly→lineage bridge (BH-1064 closes this, and closes the pre-existing BH-673 gap).
4. No Databricks lineage consumption at all (deferred until BH-1044 resolves AND the
   connection-plumbing gap above is separately built).
5. No Snowflake-native lineage consumption at all (Snowpipe/Tasks/Streams/Dynamic Tables via
   ACCOUNT_USAGE views) — NEW gap, added pass 8, not previously scoped. Cheaper than gap 4
   (reuses existing SnowflakeConnection) but equally unbuilt today.
6. No auto-discovery of which source columns are worth monitoring by default (explicitly
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
    relation_name: str | None         # ADDED pass 10, see LineageModelNode's field for the
                                       # full CRITICAL bug this closes — this is the field
                                       # BH-1064's traversal actually matches against, NOT
                                       # unique_id or name (neither matches
                                       # AnomalyEventNode.dataset's real format)

# Registry (mirrors the EXACT convention this org already established for pipeline-health
# adapters in the sibling spec proactive-pipeline-ingestion-monitoring.md's
# PIPELINE_SOURCE_ADAPTERS, itself modeled on the real CONNECTION_CLASSES/
# WarehouseConnectionFactory pattern, brightbot/tools/warehouse_connections.py:1230-1259 —
# reuse the SAME registry shape here, don't invent a third variant):
LINEAGE_SOURCE_ADAPTERS: dict[str, type[LineageSource]] = {
    DBT: DbtLineageSource,           # BH-1062 implements this adapter — FIRST, not ONLY
    DATABRICKS: DatabricksLineageSource,  # future — CORRECTED pass 7: greenfield regardless
                                           # of BH-1044 (credential-location decision only);
                                           # needs NEW WarehouseType enum members on BOTH
                                           # brightbot + platform-core (currently closed to
                                           # redshift/snowflake/azure_synapse/postgres) PLUS
                                           # a new connection path (no Databricks SQL
                                           # connector exists today) PLUS admin-side Unity
                                           # Catalog system-schema enablement per customer
    SNOWFLAKE_NATIVE: SnowflakeNativeLineageSource,  # ADDED pass 8 — a THIRD, CHEAPER lineage
                                           # source: Snowflake's own ACCOUNT_USAGE.
                                           # OBJECT_DEPENDENCIES/ACCESS_HISTORY views, for
                                           # customers whose pipeline is Snowflake-native
                                           # (Snowpipe/Tasks/Streams/Dynamic Tables) rather
                                           # than dbt-orchestrated. CONFIRMED CHEAP pass 8:
                                           # SnowflakeConnection ALREADY EXISTS and can run
                                           # arbitrary SELECT against ACCOUNT_USAGE
                                           # (warehouse_connections.py:701,714,1233) — unlike
                                           # Databricks, this needs ZERO new connection type,
                                           # only a new query + parser, same tier of cost as
                                           # BH-1062's dbt adapter, not Databricks' tier.
    # FUTURE CANDIDATE, not yet an adapter, flagged pass 8 (user-raised): Microsoft Fabric —
    # unifies OneLake/Data Factory/Spark/Power BI under one brand but FIVE distinct query
    # languages (T-SQL, PySpark, DAX, KQL, Power Query M) and no unified lineage API across
    # them that this investigation has verified — likely Databricks-tier cost (new connection
    # type(s), no existing BrightHive code path), possibly worse given the multi-engine
    # internal split. Do not scope until a Fabric-committed customer actually asks; this note
    # exists so a future adapter estimate isn't drafted from a blank slate.
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
# `name` matches a compile-producing command (`dbt run`|`dbt build`|`dbt compile`), and pass
# THAT step's `index` explicitly.
#
# PARTIALLY RESOLVED pass 7 (triple-click-zoom): existing brightbot code DOES use
# step["name"] and step["index"] as the field names (dbt_cloud_tools.py:358-359,
# _process_failed_step) - step_index = step.get("index") is fed straight into
# _fetch_artifact(..., step=step_index) at dbt_cloud_tools.py:365,400. This is a real,
# load-bearing internal precedent, not a guess. HOWEVER: every occurrence of these field
# names in this repo traces back to a HAND-WRITTEN unit-test fixture
# (tests/unit/agents/dbt_agent/test_dbt_cloud_internals.py:333,343-372,
# test_dbt_cloud_http_client.py:104-107) - never a captured live dbt Cloud API response.
# No fixture/cassette directory in this repo contains a real run_steps payload. REMAINING
# GAP: name's exact string values for compile-producing steps ("dbt build" verbatim? or a
# different field not present anywhere in this codebase?) is UNVERIFIED against a live API
# call - BH-1062's implementer MUST make one real
# GET /runs/{id}/?include_related=['run_steps'] call against a real job before hardcoding
# a match string, per test-behavior-real.md (a fixture invented from this repo's existing
# invented fixtures is still an invented fixture, not a captured real shape). Omitting `step`
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
    relation_name: str | None              # ADDED pass 10 — CRITICAL FIX, a real blocking bug
                                           # found by verification, not a nice-to-have. dbt's
                                           # manifest.json carries `relation_name` per compiled
                                           # node (general dbt knowledge, e.g.
                                           # `"MY_DB"."GOLD"."mart_daily_portfolio_exposure"`).
                                           # WITHOUT this field, BH-1064's traversal (below)
                                           # cannot find the LineageNode a real anomaly refers
                                           # to at all — see the CRITICAL note before
                                           # find_downstream_impact for the full bug. None if
                                           # the manifest node genuinely lacks it (e.g. a
                                           # non-materialized ephemeral model).

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
    *, workspace_id: str, artifacts: LineageArtifacts, session: OGMAPISession | None = None,
) -> None: ...
# brightbot-side: calls a NEW platform-core GraphQL mutation over the existing OGM HTTP
# path (ogm_api.py) — it does not touch Neo4j directly.
# platform-core-side (NEW scope, not previously called out): a mutation implementing the
# delete-then-MERGE pattern from workflow-spec.ts:299-317, targeting a new LineageNode
# type + DEPENDS_ON relationship.
#
# BH-1069's (formerly informally called "BH-1063a" — now filed as its own ticket, pass 11)
# REAL call-site shape, verified pass 11 (triple-click-zoom) — not paraphrased:
#
# 1. `session: OGMAPISession | None = None` param above is REQUIRED, not optional style —
#    confirmed this is the repo's actual compliant idiom (`session or OGMAPISession()`,
#    9 existing call sites, e.g. `longitudinal_node.py:147,309`, `metric_history_store.py:96`)
#    — NOT a bare `OGMAPISession()` singleton (the weaker variant at `quality_tools.py:820`,
#    `profiler_task.py:150`, which this ticket should NOT copy).
#
# 2. `ogm_api.py:146-160`'s real `OGMAPISession.mutation(graphql_mutation, variables,
#    timeout)` delegates to `_execute_request` (`:162-193`), which calls
#    `response.raise_for_status()` (raises on transport-level HTTP failure) and returns
#    `response.json()` VERBATIM — it does NOT check the returned dict's `"errors"` key.
#    **CRITICAL, found pass 11**: `_record_capability` (the precedent this ticket is told to
#    mirror) does NOT check for GraphQL-level errors either — a validation failure,
#    `@authorized` denial, or bad Cypher inside the mutation resolver would return
#    `{"data": null, "errors": [...]}` with HTTP 200, and the caller's `try/except Exception`
#    would never fire (no exception was raised — the request "succeeded"). Copying this
#    precedent AS-IS means `upsert_lineage_graph` could silently no-op on every call and
#    nothing would surface it. THIS TICKET MUST check `response.get("errors")` explicitly
#    and raise/log a real failure — do not inherit `_record_capability`'s silent-failure gap
#    just because it's the cited precedent. This is a NEW correctness requirement this spec
#    is adding on top of the precedent, not something already solved by copying it.
#
# 3. `ogm_queries.py:123-150`'s real query-building shape: a STATIC triple-quoted GraphQL
#    string (no f-string interpolation into the query body, no `gql()` call) plus a separate
#    `variables` dict — e.g. `mutation = """mutation UpsertLineageGraph($input: ...) {
#    ... }"""`, `variables = {"input": [...]}`, `return mutation, variables`. Replicate this
#    EXACT shape for the new `upsertLineageGraph`-equivalent mutation — values go in
#    `variables`, never string-interpolated into `mutation`.
#
# 4. Auth is a FIXED Cognito service-account credential (`OGM_USER`/`OGM_PASSWORD` env vars,
#    `ogm_api.py:44-116`), authenticated once at `OGMAPISession()` construction and cached on
#    the instance — NOT a per-request/per-user token. No new auth code needed; this is
#    already handled by the injected/default-constructed session.
# SHARPENED pass 3 (triple-click-zoom) — verified against the REAL WorkflowStepNode OGM type
# and upsertWorkflowStep mutation, not a paraphrase:
#
# EXACT OGM type to model LineageNode after (WorkflowStepNode,
# platform-core/src/graphql/ogm/workflow-spec-typedefs.ts:79-97):
#   type LineageNode {
#     id: ID! @id
#     uniqueId: String!              # dbt's fully-qualified unique_id, e.g. "model.proj.stg_orders"
#     name: String!
#     relationName: String            # ADDED pass 10, CRITICAL — see the bug note before
#                                      # find_downstream_impact below. Nullable: null for
#                                      # models genuinely lacking a materialized relation
#                                      # (e.g. ephemeral models). MUST be indexed
#                                      # (@constraint or a manual :LineageNode(relationName)
#                                      # index) since it's the traversal's match key, not
#                                      # a cosmetic field.
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
# TWO REAL PRECEDENTS EXIST, PICK DELIBERATELY (verified pass 6, triple-click-zoom) — the
# spec previously implied WorkflowStepNode's public-mutation shape was the only option; a
# CHEAPER, MORE RECENT precedent also exists and is the better fit here:
#
#   Option A — WorkflowStepNode style (workflow-spec.ts:299-317, schema/typedefs.ts:4819-4822):
#     public GraphQL mutation + resolver + OGM @relationship decorator + codegen'd
#     ogm-types.ts. More files, more ceremony, appropriate when the mutation needs to be
#     directly callable by end-user-facing GraphQL clients (e.g. webapp).
#
#   Option B — AnomalyEventNode/MetricSnapshotNode style (commits 9c25cd1f/206f56f7,
#     "feat(quality): ... BH-668"): OGM type in typedefs.ts ONLY, a plain service module
#     with raw Cypher (src/graphql/service/neo4j/metric-snapshot.ts, 194 lines — no
#     @relationship decorator, no public schema/typedefs.ts mutation, no ogm-types.ts
#     codegen). Exactly 4 files touched: typedefs.ts (new type), a new
#     service/neo4j/lineage-graph.ts (upsert logic), models/quality-rule.ts-equivalent
#     validation module if needed, common/types.ts (shared type refs).
#
#   DECISION for BH-1063b: Option B. LineageNode is written ONLY by brightbot's backend
#   call (never directly by a webapp GraphQL client), exactly like AnomalyEventNode/
#   MetricSnapshotNode's own access pattern — no end-user needs to call
#   `upsertLineageGraph` from the browser. Option A's public-mutation ceremony
#   (schema/typedefs.ts registration, resolver, codegen) is unjustified overhead for an
#   internal service-to-service write. Concrete file list for a cold engineer:
#   RESOLVED, pass 6 (was an open question in the prior pass — now confirmed against real
#   code, not assumed): platform-core runs TWO physically separate GraphQL servers on
#   separate API Gateway endpoints — a public one (`src/server.ts` → `src/graphql/schema/
#   typedefs.ts`, webapp-facing) and the OGM/internal one (`src/graphql/ogm/ogm-server.ts`
#   → `src/graphql/ogm/typedefs.ts`, brightbot-facing via `OgmApiGatewayUrl`, gated by a
#   `custom:isSystemAdmin` Cognito claim check in `ogm-server.ts:78-108` that the public
#   server does not apply). `createAgentCapabilityExecutionNodes` — the mutation
#   `ogm_queries.py:123-150` actually calls — exists ONLY in this OGM schema; it is not
#   registered anywhere under `src/graphql/schema/` and has no public counterpart. This
#   means BH-1063b needs NO public-schema touch at all, and is even cheaper than Option
#   B's raw-Cypher description above: `@neo4j/graphql` auto-generates the full CRUD
#   mutation set (including a `createLineageNodes`-shaped mutation) directly from ONE
#   `typedefs.ts` entry — confirmed by `createAgentCapabilityExecutionNodes`'s own
#   generated presence in `src/common/ogm-types.ts:1323`, with no hand-written resolver
#   for it anywhere in the codebase.
#
#   Concrete file list for a cold engineer implementing BH-1063b:
#     1. `src/graphql/ogm/typedefs.ts` — add `LineageNode` type (~15-20 lines, mirrors
#        AnomalyEventNode's shape at typedefs.ts:713-727). Decide here whether the
#        DEPENDS_ON edge is declared as an OGM `@relationship` directive (gets a
#        free auto-generated `connect`/`disconnect` mutation shape, but the auto-generated
#        upsert does NOT enforce the delete-then-MERGE replace semantics Invariant 4/9
#        require — @neo4j/graphql's `connectOrCreate` is additive, not idempotent-replace)
#        or left undecorated with a HAND-WRITTEN Cypher service (full control over the
#        atomic delete-then-MERGE transaction, costs one extra file). RECOMMENDATION:
#        undecorated + hand-written, because Invariant 9's atomicity fix is not
#        expressible through the auto-generated mutation — confirm this trade-off at
#        implementation time rather than defaulting to the decorator for convenience.
#     2. `src/graphql/service/neo4j/lineage-graph.ts` — NEW file if hand-written Cypher is
#        chosen (per step 1): the delete-then-MERGE upsert per Invariant 9, modeled on
#        `metric-snapshot.ts`'s shape (194 lines).
#
#     RESOLVED pass 9 (triple-click-zoom) — the atomic-transaction API was under-specified;
#     now confirmed against real code, not generic Neo4j docs. `session.writeTransaction(...)`
#     (what earlier passes of this spec recommended) is DEPRECATED for this repo's actual
#     driver (`package.json:47`, `neo4j-driver: ^5.0.0` — v5 prefers `session.executeWrite`).
#     BUT a simpler, ALREADY-PROVEN option exists in this exact repo and should be preferred:
#     `workflow-spec.ts:557-581` (`deleteWorkflowStep`) already chains
#     `OPTIONAL MATCH ... DELETE dep WITH step, b, iss DETACH DELETE step, b, iss` as ONE
#     Cypher string in a SINGLE `session.run()` call — Neo4j auto-commits one submitted
#     query string as one implicit transaction, closing the crash window without introducing
#     any new driver API. RECOMMENDATION, supersedes earlier `writeTransaction` guidance: write
#     the delete-then-MERGE as ONE multi-statement Cypher string
#     (`MATCH (n:LineageNode {uniqueId: $id})-[r:DEPENDS_ON]->() DELETE r WITH n UNWIND $depIds
#     AS depId MATCH (dep:LineageNode {uniqueId: depId}) MERGE (n)-[:DEPENDS_ON]->(dep)`), one
#     `session.run()` call — matches this repo's OWN existing style exactly
#     (`workflow-spec.ts:573-580`), needs zero new driver API, and is strictly simpler than
#     `executeWrite`. Fall back to `session.executeWrite(tx => ...)` only if the upsert
#     genuinely needs to read an intermediate result back into JS before the MERGE (not
#     expected here — confirm at implementation time, don't default to it for convenience).
#     CONFIRMED pass 9: zero `executeWrite`/`writeTransaction`/`CALL {...} IN TRANSACTIONS`
#     usage exists anywhere in this repo today — there is no other transactional precedent to
#     copy, which makes the single-string approach doubly preferable: it requires learning
#     nothing new, whereas `executeWrite` would be a first-of-its-kind pattern in this repo.
#     3. `src/common/types.ts` — shared type refs if `LineageNode`/`LineageGraph` types
#        need to cross module boundaries within platform-core.
#   Total: 2-3 files, zero public-schema files, zero resolver boilerplate if the
#   auto-generated mutation path is used for read-back queries (only the write path needs
#   the hand-written service).
#
# CRITICAL CORRECTNESS GAP FOUND IN THE PRECEDENT ITSELF — do not silently inherit this:
# the real workflow-spec.ts:299-317 pattern (upsertWorkflowStep) is NOT atomic — the DELETE
# and the MERGE run as two SEPARATE auto-commit `session.run()` calls on the same session
# (`workflow-spec.ts:302-314`). If the process crashes between the DELETE and the MERGE, a
# step is left with ZERO DEPENDS_ON edges — deleted but never re-created. For BH-1063, this
# same gap would mean a crash mid-upsert could silently leave a dbt model with NO lineage
# edges, which downstream (BH-1064) would read as "nothing depends on this" — a false
# negative that suppresses a real alert. THIS SPEC SHALL NOT silently copy the non-atomic
# version. FIX (confirmed pass 9): the SAME repo already proves the fix elsewhere —
# `workflow-spec.ts:557-581` (`deleteWorkflowStep`) chains DELETE + further Cypher clauses as
# ONE multi-statement string in ONE `session.run()` call, which Neo4j auto-commits as one
# implicit transaction. BH-1063's upsert should follow THIS precedent (one string, one call),
# not `upsertWorkflowStep`'s own two-call pattern — see Invariant 9 below.

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
#
# CRITICAL BUG FOUND AND FIXED, pass 10 (triple-click-zoom) — the match key below was WRONG
# in every prior pass of this spec, and would have shipped a traversal that silently matches
# ZERO nodes for virtually every real anomaly. Verified against real code, not assumed:
# `anomaly.dataset` is NOT a dbt identifier — traced its real origin to
# `longitudinal_node.py:348` (`dataset_fqn = state.get("dataset_table_name")`), itself set in
# `quality_check_agent.py:362-366` (`fetch_asset_details`) from
# `asset_details.get("redshiftTableName") or asset_details.get("snowflakeTableName") or
# asset_details.get("tableFQN") or asset_details.get("tableName")` — a WAREHOUSE-side
# `<schema>.<table>` identifier pulled from `DataAssetNode`'s own fields, e.g.
# "GOLD.mart_daily_portfolio_exposure". This NEVER matches `LineageNode.uniqueId`
# ("model.my_project.stg_orders") or `LineageNode.name` ("stg_orders") — neither field is in
# the same namespace as a warehouse-qualified table name. The ORIGINAL query below
# (`MATCH (start:LineageNode {name: $anomaly_dataset})`) is confirmed BROKEN — it would find
# zero matches for real anomalies, defeating this entire epic's purpose silently (no error,
# just an empty downstream list every time).
#
# FIX: this is exactly why `LineageNode.relation_name` was added above (mirrors dbt
# manifest.json's own `relation_name` field, general dbt knowledge — e.g.
# `"MY_DB"."GOLD"."mart_daily_portfolio_exposure"`, the SAME namespace `anomaly.dataset`
# lives in). BH-1062 must populate `relation_name` from the manifest node's own field; BH-1064
# must match against it, not `name`/`uniqueId`:
#   MATCH (start:LineageNode {relationName: $anomaly_dataset})
#                   <-[:DEPENDS_ON*1..]-(downstream:LineageNode)
#                   RETURN downstream
# REMAINING GAP, flagged not silently assumed solved: dbt's `relation_name` format
# (`"DB"."SCHEMA"."TABLE"`, quoted, 3-part) may not exactly string-match
# `asset_details.get("snowflakeTableName")`'s format (unverified in this pass — no code path
# in this repo currently produces or compares these two strings side by side, since this
# bridge has never existed before). BH-1062/1064's implementer MUST confirm the two strings'
# exact casing/quoting/part-count match on a REAL workspace with both a dbt connection and a
# DataAssetNode for the same physical table before trusting an exact-match Cypher lookup — a
# normalization step (strip quotes, uppercase/lowercase consistently, drop the DB part if
# `dataset` is 2-part) may be required. Do not assume string equality without this check.
#
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
   behavior. PARTIALLY VERIFIED pass 7: step["name"]/step["index"] ARE the real field names
   an existing call site relies on (dbt_cloud_tools.py:358-359,365,400) — this is new
   ASSEMBLY of an existing pattern, not code invented from nothing. REMAINING GAP: the exact
   string value(s) step["name"] takes for a compile-producing step ("dbt build" verbatim, or
   something else) is UNVERIFIED against a live dbt Cloud API response — every occurrence in
   this repo is a hand-written test fixture, never a captured real payload. BH-1062's
   implementer MUST confirm this against one real API call before hardcoding a match string.`
9. `WHEN upserting a LineageNode's DEPENDS_ON edges, THE System SHALL perform the
   delete-and-recreate as ONE multi-statement Cypher string in a SINGLE session.run() call
   (Neo4j auto-commits one submitted query as one implicit transaction) — it SHALL NOT copy
   workflow-spec.ts:300-314's own upsertWorkflowStep pattern verbatim, which runs the DELETE
   and MERGE as two separate auto-commit calls with a crash window between them. Verified
   pass 3: that precedent has a real correctness gap (a process crash mid-upsert leaves zero
   DEPENDS_ON edges, which BH-1064 would read as "nothing depends on this" — a false negative
   that suppresses a real alert). RESOLVED pass 9: the fix is confirmed already proven
   elsewhere in the SAME repo — workflow-spec.ts:557-581 (deleteWorkflowStep) chains its
   DELETE + further clauses as one string, one call. Follow THAT precedent's shape (one
   string, one call), not upsertWorkflowStep's two-call shape. session.executeWrite(...) (the
   non-deprecated driver-v5 API, per package.json:47's neo4j-driver ^5.0.0 — NOT
   session.writeTransaction, which is deprecated at this version) is the fallback ONLY if the
   upsert needs to read an intermediate result back into JS before the MERGE, which is not
   expected here.`
10. `THE downstream-impact traversal (BH-1064) SHALL match a LineageNode against
    AnomalyEventNode.dataset using LineageNode.relation_name — it SHALL NOT match against
    LineageNode.unique_id or LineageNode.name. CRITICAL, found pass 10: unique_id/name live
    in dbt's model-identifier namespace ("model.my_project.stg_orders" / "stg_orders");
    anomaly.dataset lives in the warehouse-table namespace ("GOLD.mart_daily_portfolio_
    exposure", sourced from DataAssetNode's redshiftTableName/snowflakeTableName/tableFQN via
    quality_check_agent.py:362-366). Matching against the wrong field would silently return
    zero downstream tables for every real anomaly — no error, just a defeated epic. BH-1062
    MUST populate relation_name from dbt manifest.json's own relation_name field per node;
    string-format equality between relation_name and anomaly.dataset (quoting, casing,
    2-part vs 3-part) is UNVERIFIED against a real workspace and MUST be confirmed — a
    normalization step may be required before the exact-match Cypher lookup is trustworthy.`
11. `WHEN brightbot's upsert_lineage_graph() calls platform-core's OGM mutation via
    OGMAPISession.mutation(), THE System SHALL check the returned response for a non-empty
    "errors" key and treat that as a failure (log + do not silently proceed) — it SHALL NOT
    rely on OGMAPISession.mutation() raising an exception for GraphQL-level failures.
    CRITICAL, found pass 11: ogm_api.py:146-193's real implementation only raises on
    transport-level HTTP failure (response.raise_for_status()) — it returns response.json()
    verbatim with no inspection of a GraphQL "errors" array. The cited precedent
    (_record_capability, longitudinal_node.py:299-323) does NOT check for this either — a
    validation failure or @authorized denial inside the mutation resolver returns HTTP 200
    with {"data": null, "errors": [...]}, and the precedent's try/except Exception never
    fires because no exception was raised. Copying this precedent as-is means the lineage
    upsert could silently no-op on every call, indistinguishable from success. THIS SPEC
    SHALL NOT inherit that silent-failure gap.`

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Lineage-aware data quality — glue dbt's own lineage to anomaly detection

  Scenario: null spike on a source column names the affected Gold tables
    Given a workspace with dbt Cloud connected and longitudinal monitoring on column X
    And dbt's manifest.json shows 2 Gold-layer models depend (transitively) on column X's table
    And each LineageNode's relation_name was populated from the manifest's own relation_name
      field, matching the SAME warehouse-qualified format AnomalyEventNode.dataset uses
    When a null_spike anomaly fires on column X
    Then the SAME alert names both downstream Gold models as affected
    And the alert reaches the user before they would have noticed the wrong number manually

  Scenario: the traversal never matches against the wrong identifier namespace
    Given a LineageNode with unique_id "model.my_project.stg_orders", name "stg_orders", and
      relation_name "GOLD.mart_daily_portfolio_exposure"
    And an AnomalyEventNode with dataset "GOLD.mart_daily_portfolio_exposure"
    When BH-1064's traversal looks up the starting node for this anomaly
    Then it matches on relation_name and finds this node
    And it would NOT have found this node had it matched on unique_id or name instead
      (CRITICAL, found pass 10 — this is the exact bug that silently returns zero downstream
      tables for every real anomaly if regressed)

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
    Given a dbt Cloud run with 3 steps, real step["name"] values confirmed against a live
      run before this test is written (per Invariant 8 — not hardcoded from assumption)
    When BH-1062 fetches manifest.json for this run
    Then it first calls run_steps and identifies the last compile-producing step by its
      real, confirmed step["name"] value
    And it passes that step's step["index"] explicitly to _fetch_artifact()
    And it does NOT omit the step parameter and rely on unverified default API behavior

  Scenario: a crash mid-upsert never leaves a model with zero lineage edges
    Given a LineageNode currently has 3 DEPENDS_ON edges from a prior manifest
    And the DELETE and MERGE for a new manifest are submitted as ONE multi-statement Cypher
      string in a single session.run() call (per Invariant 9 — not two separate calls)
    When the process crashes at any point during that single call
    Then the node never observably had zero edges in between — Neo4j either commits the
      whole string as one implicit transaction or none of it applies
    And this differs deliberately from workflow-spec.ts's upsertWorkflowStep (two-call,
      non-atomic), and instead follows workflow-spec.ts's OWN deleteWorkflowStep precedent
      (one-string, one-call) — both patterns exist in the same file, only one is safe to copy

  Scenario: a GraphQL-level mutation failure is never mistaken for success
    Given platform-core's upsertLineageGraph-equivalent mutation returns HTTP 200 with
      {"data": null, "errors": [{"message": "..."}]} (e.g. an @authorized denial or a Cypher
      validation error inside the resolver)
    When brightbot's upsert_lineage_graph() calls OGMAPISession.mutation() for this request
    Then the response's "errors" key is checked explicitly and treated as a failure
    And this differs deliberately from _record_capability's own precedent (longitudinal_
      node.py:299-323), which does NOT check "errors" and would silently treat this as success
      because OGMAPISession.mutation() only raises on transport-level HTTP failure, never on
      a GraphQL-level error inside a 200 response
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
| BH-1044 (Databricks credential-location decision) | Blocking for the Databricks half, but NOT sufficient by itself — see below | Open decision, not yet confirmed |
| Databricks connection-type plumbing (new WarehouseType enum + connector + Unity Catalog system-schema enablement) | Blocking for the Databricks half, independent of BH-1044 | **CORRECTED pass 7**: confirmed zero Databricks code exists in brightbot or platform-core outside vendored deps — this is greenfield regardless of how BH-1044 resolves, not merely gated behind it |
| BH-1066 (anomaly-notification renderer, Slack + webapp) | Non-blocking for BH-1064's own code; blocking for the enrichment to ever be human-visible | Filed pass 5, Needs Refinement — same class of gap as BH-1067 in the sibling proactive-pipeline-ingestion-monitoring.md spec |
| Existing `SnowflakeConnection` (`warehouse_connections.py:701,714,1233`) | Non-blocking for BH-1068 (Snowflake-native adapter, reused not built) | Live — already permits arbitrary `SELECT`, including against `ACCOUNT_USAGE` views |
| BH-1068 (Snowflake-native lineage adapter: Snowpipe/Tasks/Streams/Dynamic Tables via ACCOUNT_USAGE) | Non-blocking for 7/17; cheaper than the Databricks half (gap 4) but equally unbuilt | **Filed pass 8** — user-raised, confirmed real gap, confirmed cheap relative to Databricks |

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Manifest/catalog fetch + parse (BH-1062) | `brightbot` | New parser module, reuses existing artifact-fetch plumbing |
| Lineage graph schema + upsert mutation (BH-1063b) | **`brighthive-platform-core`** — corrected, was miscast as brightbot-only | **CONFIRMED pass 9**: 2-3 files, zero public-schema touch — `src/graphql/ogm/typedefs.ts` (new `LineageNode` OGM type) + `src/graphql/service/neo4j/lineage-graph.ts` (hand-written delete-then-MERGE as ONE multi-statement Cypher string, one `session.run()` call, per `workflow-spec.ts:557-581`'s own proven pattern — not `session.writeTransaction`, deprecated at this repo's `neo4j-driver ^5.0.0`) + optionally `src/common/types.ts`. Mirrors `AnomalyEventNode`/`MetricSnapshotNode`'s OGM-only pattern (BH-668), a cheaper precedent than `WorkflowStepNode`'s public-mutation shape (`workflow-spec.ts:299-317`) — platform-core runs the OGM schema on a physically separate, `isSystemAdmin`-gated API Gateway endpoint from the public/webapp schema, confirmed via `ogm-server.ts:78-108` |
| Lineage graph call site (BH-1069, formerly informal "BH-1063a") | `brightbot` | Calls the new platform-core mutation over the EXISTING `ogm_api.py` HTTP path — no new Neo4j driver code, plus the new GraphQL-`"errors"`-key check (Invariant 11) |
| Anomaly-alert enrichment (BH-1064) | `brightbot` (governance_agent) | Extends BH-1046's existing alert path, no new delivery mechanism |

## Ticket Breakdown

| Ticket | Summary | Status |
|---|---|---|
| BH-1061 | Epic: Lineage-Aware Data Quality | Needs Refinement |
| BH-1062 | feat: fetch + parse manifest.json/catalog.json | Needs Refinement |
| BH-1063 | feat: load parsed DAG into Neo4j as queryable lineage graph | Needs Refinement |
| BH-1064 | feat: wire anomalies to walk the graph forward (closes BH-673) | Needs Refinement |
| BH-1065 | verify: does anything render anomaly JSON into visible Slack/webapp text today? | **Done, pass 5 — answer confirmed NO**, see BH-1066 |
| BH-1066 | feat: render longitudinal anomaly notifications in Slack + webapp (currently dead-ends, confirmed) | Needs Refinement, filed pass 5 — blocks BH-1064's enrichment from being human-visible, does not block BH-1064's own code |
| BH-1068 | feat: Snowflake-native lineage adapter (Snowpipe/Tasks/Streams/Dynamic Tables via ACCOUNT_USAGE) | Needs Refinement, filed pass 8 — user-raised, confirmed cheaper than the Databricks adapter (reuses existing SnowflakeConnection, no new connection type) |
| BH-1069 | feat(lineage): brightbot call site for upsert_lineage_graph | Needs Refinement, filed pass 11 — formerly informal "BH-1063a," now its own trackable ticket |

## Track D: per-Project pipeline health view (proposed, genuinely new — NOT yet a committed scope)

**Added pass 11, user-raised**: "we need to surface this work to a PROACTIVE view on projects
... projects should have its own dedicated [timeline view] for pipelines." This is a real,
confirmed plug-in point in an existing product surface — NOT a new top-level page.

### What's real today (verified pass 11)

- **Project is a first-class surface** with a per-project tab bar
  (`brighthive-webapp/src/common/ProjectSidenav/ProjectNavBar.tsx:70-141`): Overview,
  Schemas, **Flow**, Input Data Assets, Files, Data Products. "Flow" already renders a
  **static structural DAG** via React Flow (`src/ProjectWorkflow/ProjectWorkflow.tsx:1-80`,
  columns: ORGANIZATION → INPUT_DATA → TRANSFORMATIONS → FINAL_DATA_PRODUCTS →
  DESTINATIONS) — it shows what feeds what, NOT run history over time. No
  timeline/run-history view exists anywhere in the webapp today (confirmed: zero "timeline"
  hits in `src/`).
- **`TransformationNode`** (`platform-core/src/graphql/ogm/typedefs.ts:825-860`) already
  carries `lastRunStatus`/`lastRunAt`/`jobId`, links to `ProjectNode`, to a dbt model
  (`dbtModelName`/`dbtModelSql`), and to upstream/downstream `transformations` (the DAG edge)
  — this is the closest existing backend hook for a time-based view, but nothing renders it
  as a timeline today.

### The proposal

A 7th per-project tab — plugging into the EXISTING `ProjectNavBar.tsx` tab convention, not a
new page — surfacing exactly the signals this epic (Track C) and the sibling
proactive-pipeline-ingestion-monitoring.md spec (Track B) already produce: watchdog
detections (BH-1054), longitudinal anomalies (GC-12), and this epic's downstream-impact
enrichment (BH-1064), scoped to the transformations/data assets that belong to THIS project.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PROPOSED: a 7th ProjectNavBar tab, reusing the existing tab convention  │
└─────────────────────────────────────────────────────────────────────────┘

  ProjectNavBar.tsx (existing, real)              NEW 7th tab (proposed)
  ┌────────┬─────────┬──────┬───────────┬───────┬──────────────┐  ┌──────────────┐
  │Overview│ Schemas │ Flow │Input Data │ Files │Data Products │  │  [name TBD]  │
  │        │         │(DAG) │  Assets   │       │              │  │ (time-based) │
  └────────┴─────────┴──────┴───────────┴───────┴──────────────┘  └──────────────┘
                                                                          │
                     reads FROM (no new backend types needed to START):  │
                     - TransformationNode.lastRunStatus/lastRunAt        │
                     - AnomalyEventNode (this project's DataAssetNodes)  │
                     - PipelineHealthSignal (BH-1042, sibling spec)      │
                     - this epic's downstream_tables enrichment (BH-1064)│
```

### Naming note

"Brightlines" was the user's working name for this. Per this org's naming rule
(`~/.claude/rules/naming.md`: names must be brand/product/human-first, meaning what they
are) — "Brightlines" passes the four tests reasonably well (brand-inclined, evokes
"pipeline"/"timeline" without engineering jargon, human-readable) but has NOT been checked
against `brighthive-ux-voice`/`brighthive-product-voice` review, which this org's rules
require before a user-facing name ships. Treat "Brightlines" as a WORKING NAME for this spec
section, not a final product decision.

### Explicitly NOT yet scoped (genuinely new, this pass only proposes the shape)

- No ticket filed yet — this needs a `/write-spec` pass of its own (UI/UX design questions:
  what time range, what granularity, how does it relate to "Flow"'s existing DAG view) before
  Jira tickets are cut. Filing tickets against an unreviewed UI proposal would lock in
  decisions a designer/PM hasn't made yet.
- Frontend component design, React Flow vs. a different viz library for time-series (React
  Flow is DAG-oriented; a run-history timeline may want a different chart primitive —
  unverified which fits better).
- Whether this becomes a NEW tab or an enhancement to the EXISTING "Flow" tab (overlay
  run-status onto the DAG nodes already there, vs. a wholly separate view) — a real design
  decision, not decided here.

## Related

- `longitudinal-monitoring.md` — the anomaly-detection half this spec enriches
- `longitudinal-monitoring-capability.md` — the capability-node interface pattern this spec's
  Neo4j upsert mirrors
- `proactive-pipeline-ingestion-monitoring.md` — sibling spec, shares the BrightSignals alert
  path (BH-1046) this spec's enriched alerts reuse. Also shares this spec's exact class of
  gap: pass 35 of that spec confirmed 5 of its 6 new notification stages have the identical
  rendering dead-end found here for `longitudinal_anomaly` (BH-1065/1066) — that spec's fix
  is tracked as BH-1067
- `clients/trials/loopcapital/overview.md` — this capability is scoped into Loop Capital's
  plan as an honest post-demo workstream, not a 7/17 deliverable
