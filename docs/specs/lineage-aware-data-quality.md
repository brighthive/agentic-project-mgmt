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
  │ Longitudinal  │              │  LineageSource PORT       │        │ Gold / Diamond    │
  │ monitoring    │   detects    │  (Ports & Adapters,       │  walk  │ tables named as   │
  │ (null_spike,  │─────────────▶│  engine-agnostic):        │───────▶│ "affected" in the │
  │ row_count_    │   anomaly    │                          │ forward│ SAME alert that   │
  │ drift, etc.)  │   on column  │  1. dbt manifest.json/    │        │ fired the anomaly  │
  │  SHIPPED      │   X          │     catalog.json          │        │  NEW (BH-1064)     │
  └──────────────┘              │     — BH-1062, CONFIRMED  │        └──────────────────┘
                                  │     buildable this pass   │
                                  │  2. Databricks Unity      │
                                  │     Catalog system tables │
                                  │     — DatabricksLineage-  │
                                  │     Source, greenfield    │
                                  │     connector, independent│
                                  │     of BH-1044 decision   │
                                  │  3. Snowflake ACCOUNT_    │
                                  │     USAGE (Snowpipe/Tasks/│
                                  │     Streams/Dynamic       │
                                  │     Tables) — BH-1068,     │
                                  │     CHEAPEST connection-   │
                                  │     wise (reuses live      │
                                  │     SnowflakeConnection,  │
                                  │     no new connector) BUT  │
                                  │     needs a permission/    │
                                  │     latency guard — least- │
                                  │     privilege roles fail   │
                                  │     ACCOUNT_USAGE reads    │
                                  │     silently (pass 45)     │
                                  │                          │
                                  │  All 3 feed the SAME       │
                                  │  LineageGraph shape →      │
                                  │  BrightHive: load into    │
                                  │  Neo4j as a queryable      │
                                  │  graph — NEW (BH-1063)     │
                                  └─────────────────────────┘

  Net result (CORRECTED pass 4, CONFIRMED pass 5 — no longer "unverified"): the
  anomaly's JSON metadata blob gains a new key —
  metadata["longitudinal"]["downstream_tables"] = ["mart.customer_ltv",
  "mart.revenue_by_segment"] — attached to the SAME notification event as the
  null_spike, before a human looks at the wrong number. CONFIRMED (BH-1065): NEITHER
  brightbot-slack-server NOR brighthive-webapp renders ANY anomaly/longitudinal
  notification into visible text today — this is a real, pre-existing gap, not
  merely unverified. BH-1066 (filed) builds the missing renderer.
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
  │ parse    │                   │ mutation │        │ LineageNode:  │    │ anomaly → │
  │ manifest │                   │ (existing│        │  workspaceId! │    │ graph walk│
  │ .json /  │                   │  ogm_api │        │  uniqueId!    │    │ (closes   │
  │ catalog  │                   │  .py     │        │  relationName │    │  BH-673)  │
  │ .json    │                   │  plumbing│        │  dependsOn    │    │ MATCH also│
  └──────────┘                   │  — no new│        │  + DEPENDS_ON │    │ filters   │
                                  │  driver, │        │  + delete-then│    │ workspaceId│
                                  │  ONE     │        │  MERGE, BOTH  │    └──────────┘
                                  │  SHARED  │        │  match clauses│
                                  │  session │        │  workspace-   │
                                  │  across  │        │  scoped)      │
                                  │  the loop│        └──────────────┘
                                  └──────────┘

"brightbot already      "brightbot calls a NEW       "platform-core owns the    "we already have
 knows how to fetch       platform-core mutation       Neo4j schema + upsert —    both halves —
 dbt Cloud artifacts —    the same way it calls        brightbot NEVER touches    longitudinal
 just never asked for     every other OGM write —      Neo4j directly for this.   monitoring fires
 manifest.json before"    no new Neo4j driver code,    workspaceId is NATIVE,     events, dbt
                          ONE session shared across    not inherited via a        already wrote
                          the per-model loop (pass 49) relationship — LineageNode its own lineage —
                          — the default idiom would    is the FIRST node type     this ticket is
                          re-authenticate per model"    with no relationship      purely the
                                                         path to WorkspaceNode,    connective glue,
                                                         so it needed its own     now with real
                                                         scoping field (pass 50)" tenant isolation"
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

- **CORRECTED pass 36 — this bullet's original framing was wrong: catalog.json never
  contains column-level LINEAGE (edges) at all, in ANY dbt version.** It only contains
  column-level METADATA (existence, type, per model) — a warehouse schema snapshot. What
  varies by dbt version/config is whether catalog.json exists or is populated for a given
  model at all (`has_column_metadata`), not whether it contains a column-DEPENDENCY graph —
  no dbt version's catalog.json has ever contained that. This spec's implementation
  degrades gracefully to MODEL-level tracing always (see Invariant 14) — column existence
  data (`LineageModelNode.columns`) is retained for future use (e.g. surfacing "column X in
  this affected table" in a future enrichment) but is NEVER the basis for the downstream
  traversal itself, which is model/table-level end to end.
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
    has_column_metadata: bool         # RENAMED pass 36, CRITICAL — see the correction before
                                       # LineageModelNode.columns below. This field means
                                       # "we know which columns EXIST per model," NOT
                                       # "we have column-to-column DEPENDENCY lineage" — dbt's
                                       # catalog.json contains no column-dependency data at
                                       # all. The old name has_column_lineage was a real,
                                       # unverified false claim about what this artifact
                                       # provides.
    fetch_error: str | None
    source_engine: str               # "dbt" | "databricks" | future engines — for observability only,
                                      # never branched on by downstream consumers (BH-1063/1064)

@dataclass(frozen=True)
class LineageNode:
    unique_id: str
    name: str
    depends_on: list[str]
    columns: dict[str, "ColumnMetadata"] | None  # CORRECTED pass 36 — see LineageModelNode's
                                       # own correction below for the full finding; this was
                                       # `list[str] | None`, which doesn't match dbt's real
                                       # catalog.json shape (a dict keyed by column name, not
                                       # a flat name list).
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

# CRITICAL CORRECTION, pass 45 (triple-click-zoom) — "SnowflakeConnection already exists and
# can run arbitrary SELECT against ACCOUNT_USAGE, no new connection type needed" is TRUE but
# is the wrong bar; it glosses over a real, likely-blocking permission gap, verified against
# actual repo history, not general Snowflake knowledge alone.
#
# `SnowflakeConnection.connect()` (warehouse_connections.py:803-806) treats `role` as OPTIONAL,
# pulled from whatever the workspace's Secrets Manager payload happens to contain — if unset,
# it falls back to the Snowflake user's default role, unverified. The class's own docstring
# (warehouse_connections.py:708-711) states the INTENDED posture — "the account binds to a
# role that should itself be SELECT-only at the grant level, defense in depth" — but nothing
# in the code checks the bound role's actual grants. That intended least-privilege posture is
# exactly the posture that BREAKS ACCOUNT_USAGE reads: those views require the querying role to
# either be ACCOUNTADMIN or hold `IMPORTED PRIVILEGES` on the `SNOWFLAKE` database — a
# privilege a "should be SELECT-only" role does NOT have by design.
#
# This is not hypothetical — it already happened in this org. The one real deployed instance
# on record, brighthive-platform-core/docs/SNOWFLAKE_POC_HANDOFF.md:32, runs as
# `LONGAEVA_POC_ROLE` (service user `BRIGHTHIVE_SERVICE`), and the SAME doc, line 64, records
# the team's own fix for this exact failure mode: `#825` dropped
# `raise_from_status(raise_warnings=True)` specifically because "a Snowflake scan emits
# per-sub-query failures for optional metadata (`ACCOUNT_USAGE.*` a least-privilege role can't
# read) even when tables ingest fine" — i.e., the fix was to SILENCE the permission failure,
# not to grant the privilege or detect the gap. Confirmed by grep across both repos: zero hits
# for "IMPORTED PRIVILEGES", zero for ACCOUNT_USAGE latency handling anywhere outside that one
# doc line.
#
# Second, independent risk in the same query surface: ACCOUNT_USAGE views have documented
# ingestion latency (Snowflake's own docs: up to ~45 min–3 hrs depending on the view) versus
# real-time `INFORMATION_SCHEMA`. A freshly-created Task/Dynamic Table/Snowpipe dependency can
# be genuinely absent from OBJECT_DEPENDENCIES for hours after creation — indistinguishable,
# without an explicit check, from "this object truly has no dependencies." BH-1064's
# downstream-impact traversal reading a false "no dependencies" would suppress a real alert,
# the same false-negative risk already called out for BH-1063's atomicity gap (Invariant 9).
#
# Invariant 16 (new): the SnowflakeNativeLineageSource adapter (BH-1068) SHALL verify
# `IMPORTED PRIVILEGES` (or ACCOUNTADMIN) on the bound role BEFORE relying on an empty
# ACCOUNT_USAGE result as "no dependencies" — a permission failure and a genuine empty result
# SHALL be distinguishable, never silently conflated. THE adapter SHALL also surface each
# ACCOUNT_USAGE view's last-refreshed timestamp (queryable via
# `ACCOUNT_USAGE.OBJECT_DEPENDENCIES`'s own metadata or `INFORMATION_SCHEMA.LOAD_HISTORY`-style
# freshness checks) so a caller can tell "just polled, not yet reflected" from "confirmed no
# dependencies." BH-1068's scope MUST include this permission-and-latency guard — it is not
# optional cleanup, it is the difference between the adapter working and the adapter silently
# reporting zero lineage for every real customer running least-privilege roles, which per this
# org's own docstring is the intended, recommended posture for this exact connection.

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
# a real error doesn't get silently absorbed into "has_column_metadata=False."
#
# GAP FOUND 3, pass 23 (triple-click-zoom) — a real scale mismatch, verified against
# _fetch_artifact()'s ACTUAL implementation, not assumed. `_fetch_artifact()`
# (dbt_cloud_tools.py:256-280) is a plain blocking `requests.get(..., timeout=30)` — NO
# `stream=True`, returns `response.text` (the entire decoded body as one string, line 278).
# Callers then do a SECOND full-memory pass: `json.loads(...)` on that string
# (dbt_cloud_tools.py:372's pattern for run_results.json). Zero size cap, zero chunking. This
# has NEVER been exercised at scale — `_fetch_artifact()`'s only 2 existing callers fetch
# run_results.json/sources.json, both typically KB-scale. manifest.json (and catalog.json,
# for large dbt projects with hundreds of models) can be TENS OF MEGABYTES — an order of
# magnitude+ larger than anything this function has ever actually handled in production.
# TWO CONCRETE RISKS BH-1062 MUST ACCOUNT FOR, not silently inherit:
#   (a) The hardcoded `timeout=30` (line 274) applies UNIFORMLY regardless of artifact size —
#       a slow/throttled multi-MB manifest.json download plausibly needs longer than 30s,
#       and this function gives BH-1062's implementer no seam to override it per-call.
#   (b) Double full-memory buffering (once in `requests`, once in `json.loads`) of a
#       tens-of-MB payload is a real memory-pressure risk. brightbot deploys to LangGraph
#       Cloud SaaS (`langgraph.json`, long-running container/service model, NOT a
#       Lambda-style hard memory ceiling per this repo's own docs) — this softens but does
#       NOT eliminate the risk, since this repo's docs don't state a per-instance memory
#       limit for LangGraph Cloud deployments either; the actual ceiling is UNVERIFIED, not
#       confirmed safe.
# RESOLUTION, same shape as GAP 2's thin-wrapper approach: do NOT modify `_fetch_artifact()`
# itself (other callers depend on its current behavior/timeout). BH-1062's own wrapper
# (`fetch_lineage_artifacts` below) should either (i) call a size-aware variant with a
# longer, artifact-specific timeout and streaming JSON parse (e.g. `ijson` or manual
# chunked `requests.get(..., stream=True)` + incremental decode) for manifest.json/
# catalog.json specifically, or (ii) if profiling against a REAL large project's manifest
# shows the existing blocking pattern is fine in practice, explicitly DOCUMENT that
# decision with the real measured size/latency, rather than silently reusing a
# small-artifact-tuned function at 100x the data volume without checking.
async def fetch_lineage_artifacts(
    *, workspace_id: str, job_id: str, run_id: str,
) -> LineageArtifacts: ...
# Reuses _fetch_artifact() (dbt_cloud_tools.py:256-280) with artifact_path="manifest.json"
# and artifact_path="catalog.json" — no new HTTP/auth code, just new artifact-name arguments
# PLUS the step-discovery + error-disambiguation logic above, which IS new code.
#
# CRITICAL, pass 44 (triple-click-zoom) — this function INHERITS the same
# multi-connection monitoring-scope gap already confirmed in the sibling
# proactive-pipeline-ingestion-monitoring.md spec (Invariant 16, passes 24/42/43) for
# BH-1043/1045. Traced the real credential path: `_fetch_artifact()` takes
# `api_endpoint`/`api_token`/`account_id` as explicit params — it does no resolution
# itself. Its real analog call site, `get_job_run_error` (`dbt_cloud_tools.py:647-725`),
# reads credentials via `_get_dbt_cloud_credentials(state)` (`dbt_cloud_tools.py:53-64`), a
# PURE STATE READ populated ONCE PER SESSION by `fetch_dbt_credentials()`
# (`credentials_tools.py:390`), which internally calls the SAME `_find_connected_dbt_
# service()` (`credentials_tools.py:154-163`) that picks the FIRST `CONNECTED`
# `DBT_CLOUD` service for a workspace. **CONFIRMED: `run_id` is NEVER used to select or
# validate which dbt Cloud account/service owns it — it is only interpolated into the
# artifact URL (`{api_endpoint}/api/v2/accounts/{account_id}/runs/{run_id}/artifacts/
# ...`) against WHATEVER account was cached at session-init time.** A naive hope that
# "run_id already scopes the account, so the ambiguity is resolved by fetch time" is
# WRONG — the ambiguity is resolved once per SESSION, not per run_id. If a workspace has
# 2 connected dbt Cloud services and BH-1054's watchdog (or a human) somehow triggers
# this fetch for a run_id belonging to the SECOND service while the session's cached
# credentials point at the FIRST, this function would either 404 (wrong account_id) or,
# worse, silently fetch the WRONG account's manifest.json for a DIFFERENT run_id's
# lineage — a genuinely dangerous cross-project data-shape confusion, not just a missed
# poll. BH-1062's implementer MUST either (a) confirm this fetch call always executes in
# the SAME session/state context that resolved the run_id in the first place (so the
# cached credentials are guaranteed consistent with the run_id's real owner — plausible
# if BH-1054's watchdog and BH-1062's fetch run in the same node invocation, but NOT
# verified in this pass — confirm before assuming), or (b) thread the actual account_id
# through explicitly from wherever the run_id was discovered, bypassing session-cached
# state entirely for this specific call. See the sibling spec's Invariant 16 for the
# cross-cutting requirement this closes.

@dataclass(frozen=True)
class LineageArtifacts:
    models: dict[str, LineageModelNode]       # keyed by unique_id
    has_column_metadata: bool             # RENAMED pass 36 — see CRITICAL note below.
                                           # False if catalog.json lacked column metadata
                                           # for this model.
    fetch_error: str | None               # NEW: non-None if a real error occurred (not a
                                           # genuine 404-absent-artifact case) — surfaced so
                                           # callers don't silently treat "errored" as "absent"

@dataclass(frozen=True)
class ColumnMetadata:                     # ADDED pass 36 — general dbt catalog.json
                                           # knowledge, confirmed: catalog.json's
                                           # nodes.<unique_id>.columns is a DICT keyed by
                                           # column name, each value a metadata object —
                                           # NOT a flat list of name strings.
    name: str
    type: str                             # the warehouse column type, e.g. "NUMBER", "VARCHAR"
    index: int
    comment: str | None

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
    columns: dict[str, ColumnMetadata] | None  # CRITICAL, CORRECTED pass 36 (triple-click-
                                           # zoom) — this was `list[str] | None`, WRONG on
                                           # two counts, verified against general dbt
                                           # platform knowledge (this repo has zero
                                           # catalog.json parsing precedent to check
                                           # against — confirmed by search, this shape was
                                           # never checked before this pass either):
                                           # (1) catalog.json's real shape is a DICT keyed
                                           # by column name, not a flat list — fixed above.
                                           # (2) MORE IMPORTANT: catalog.json contains ZERO
                                           # column-to-column DEPENDENCY information at all
                                           # — it only proves "this model currently HAS
                                           # these columns" (a warehouse schema snapshot via
                                           # information_schema), never "output column X is
                                           # DERIVED FROM upstream column Y." True
                                           # column-level lineage (the dependency graph) is
                                           # NOT available from catalog.json alone — it
                                           # would require dbt Cloud's separate, proprietary
                                           # "Column-Level Lineage" feature (SQL-compilation-
                                           # based, not a public JSON artifact) or a
                                           # third-party SQL parser (e.g. sqlglot) statically
                                           # analyzing compiled SQL. NEITHER is in scope for
                                           # this spec. See has_column_metadata's rename
                                           # above and Invariant 14 below for the full
                                           # consequence.
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
#    CRITICAL, found pass 49 (triple-click-zoom) — the `session or OGMAPISession()` default
#    is safe for the 9 existing call sites (each fires ONCE per agent turn) but is a genuine
#    cost/connection-leak risk for THIS ticket specifically, verified against the class's real
#    lifecycle, not assumed safe by precedent alone. `OGMAPISession.__init__`
#    (ogm_api.py:44-56) opens a real `requests.Session()` (a pooled connection) and
#    unconditionally calls `_authenticate()` (ogm_api.py:90-127) — a live Cognito
#    `USER_PASSWORD_AUTH` HTTP round-trip — on EVERY construction. There is NO module-level
#    or class-level token cache anywhere in `ogm_api.py` (confirmed by reading the full class
#    body) and NO `__enter__`/`__exit__`/`close()`/`__del__` — the connection pool is only
#    reclaimed by eventual Python GC, not deterministically. BH-1062/BH-1063's upsert is
#    naturally called ONCE PER MODEL in a manifest (a real dbt project can have hundreds), so
#    if BH-1069's caller loops over models and relies on the bare default (no session passed
#    in), each iteration performs a fresh Cognito login AND opens a new unclosed connection
#    pool — hundreds of logins and leaked sockets per manifest load, not the "authenticate
#    once" cost the existing 9 call sites incur. FIX, REQUIRED not optional: the caller loop
#    (wherever `upsert_lineage_graph` is invoked once per model) MUST construct ONE
#    `OGMAPISession` OUTSIDE the loop and pass it explicitly into every call — never rely on
#    the bare `session or OGMAPISession()` default inside a per-model loop body.
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
#    `ogm_api.py:44-116`), authenticated ONCE PER `OGMAPISession` INSTANCE (not cached across
#    instances — see pass 49's finding above point 1) and cached on that instance — NOT a
#    per-request/per-user token, and NOT free to construct repeatedly. No new auth CODE is
#    needed (this class already exists) — but per pass 49, the CALLER must ensure only ONE
#    instance is constructed across a per-model loop, or "no new auth code needed" silently
#    becomes "hundreds of new auth calls."
# SHARPENED pass 3 (triple-click-zoom) — verified against the REAL WorkflowStepNode OGM type
# and upsertWorkflowStep mutation, not a paraphrase:
#
# EXACT OGM type to model LineageNode after (WorkflowStepNode,
# platform-core/src/graphql/ogm/workflow-spec-typedefs.ts:79-97):
#   type LineageNode {
#     id: ID! @id
#     workspaceId: String!            # ADDED pass 50, CRITICAL — see the scoping-gap note
#                                      # above. LineageNode has NO relationship path to
#                                      # WorkspaceNode (dependsOn only points to other
#                                      # LineageNodes) — unlike every other precedent checked
#                                      # in this codebase. A plain scalar field is the fix:
#                                      # every read query filters `WHERE workspaceId: $ws`
#                                      # explicitly; the delete-then-MERGE upsert's MATCH
#                                      # clause (Invariant 9) MUST include it too, or a
#                                      # cross-tenant model with the same relation_name could
#                                      # silently match/delete another workspace's node. MUST
#                                      # be indexed (composite with relationName, since both
#                                      # are real query filters, not cosmetic).
#     uniqueId: String!              # dbt's fully-qualified unique_id, e.g. "model.proj.stg_orders"
#     name: String!
#     relationName: String            # ADDED pass 10, CRITICAL — see the bug note before
#                                      # find_downstream_impact below. Nullable: null for
#                                      # models genuinely lacking a materialized relation
#                                      # (e.g. ephemeral models). MUST be indexed
#                                      # (@constraint or a manual :LineageNode(relationName)
#                                      # index) since it's the traversal's match key, not
#                                      # a cosmetic field.
#     hasColumnMetadata: Boolean! @default(value: false)
#     createdAt: DateTime! @timestamp(operations: [CREATE])
#     modifiedAt: DateTime! @timestamp(operations: [CREATE, UPDATE])
#     dependsOn: [LineageNode!]! @relationship(type: "DEPENDS_ON", direction: OUT)
#   }
# CORRECTED pass 20 (triple-click-zoom) — this quoted type ALWAYS included the
# @relationship-decorated `dependsOn` shown above, and that is the RECOMMENDED final shape
# (see the decorated-vs-undecorated decision, resolved below) — earlier passes' prose
# elsewhere in this section said "leave dependsOn undecorated," which CONTRADICTED this
# quoted type. That contradiction is now resolved: keep `dependsOn` DECORATED as shown here.
#
# CORRECTED pass 50 (triple-click-zoom) — this paragraph was WRONG about WorkflowStepNode
# and understated the real design gap for LineageNode; re-verified against real code, not
# the earlier pass's paraphrase.
#
# WorkflowStepNode does NOT lack a natural parent — it has a real `spec: WorkflowSpecNode!`
# relationship (ogm/workflow-spec-typedefs.ts:91) chaining to `WorkflowSpecNode → ProjectNode
# → WorkspaceNode`. `UpsertWorkflowStepInput.workspaceId` (workflow-spec-typedefs.ts:212-224)
# and its `@authorized(workspaceIdLoc: ["args", "input", "workspaceId"])` directive
# (typedefs.ts:4819-4823, exact syntax: a path-segment ARRAY, not a dotted string, resolved
# via `getId(source, args, workspaceIdLoc)` in `directives/authorized.ts:113`) are
# DEFENSE-IN-DEPTH on top of that real relationship path, not a substitute for having none.
#
# This matters because it changes what "mirror the precedent" actually means for LineageNode.
# Moot for the PUBLIC-mutation question specifically — Option B (below) already means
# LineageNode never gets an `@authorized`/`workspaceIdLoc` mutation at all, since it's OGM-
# only, never public-schema. But the DEEPER scoping question survives Option B and is NOT
# yet resolved: `MetricSnapshotNode`/`AnomalyEventNode` — the actual OGM-only precedent this
# spec cites — scope tenancy via their `dataAsset: DataAssetNode!` relationship, which chains
# to `WorkspaceNode` (`metric-snapshot.ts:90-96,116,182`: writes connect via
# `dataAsset: { connect: { where: { node: { id: ... } } } }`; reads filter via
# `dataAsset: { workspaces_SOME: { id: $workspaceId } }`). A code comment there states this
# explicitly: workspace scoping comes from the dataAsset connect, `input.workspaceId` is
# intentionally NOT used in the write itself. LineageNode's own decorated relationship
# (`dependsOn`) points to OTHER LineageNodes, not to any workspace-scoped anchor like
# DataAssetNode — it does NOT close the same scoping loop `dataAsset` does for
# AnomalyEventNode/MetricSnapshotNode. Every real OGM node type checked in this codebase
# (WorkflowStepNode, MetricSnapshotNode, AnomalyEventNode) has at least one relationship
# chain reaching WorkspaceNode; LineageNode as currently spec'd would be the FIRST fully
# orphan node type with zero such path. See Invariant 18 (new) for the required fix.
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
#        AnomalyEventNode's shape at typedefs.ts:713-728).
#
#        CORRECTED pass 20 (triple-click-zoom) — the "undecorated vs. decorated" framing
#        below was internally self-contradictory (the quoted type above always showed
#        `dependsOn` WITH `@relationship`) and one precedent claim was imprecise. Resolved,
#        verified against real code:
#        - `AnomalyEventNode` (typedefs.ts:713-728) and `MetricSnapshotNode` (typedefs.ts:
#          698-711) are NOT relationship-free — both DO carry exactly ONE
#          `@relationship`-decorated field each (`dataAsset`, `HAS_ANOMALY_EVENT`/whatever
#          MetricSnapshotNode's equivalent is). Earlier passes' "OGM-only, no relationship"
#          description of this precedent was imprecise — the real precedent is "one
#          decorated relationship field alongside several plain scalar fields," which is
#          EXACTLY LineageNode's own shape (one `dependsOn` relationship + several scalars).
#        - Confirmed via `AnomalyEventNodeCreateInput` (ogm-types.ts:23085-23095): having a
#          `@relationship` field does NOT corrupt or complicate the generated mutation for
#          the type's OTHER fields — it's purely additive (the relationship gets its own
#          optional `connect`/`create` sub-input; the 9 scalar fields are untouched). The
#          earlier fear that decorating `dependsOn` would somehow break the whole type's
#          generated CRUD was UNFOUNDED.
#        - Confirmed: NO existing OGM type in this repo leaves a graph-shaped reference
#          undecorated as a plain scalar array (e.g. `dependsOnIds: [String!]!`) while
#          relying on hand-written Cypher to create the real relationship separately — this
#          would be a genuinely novel, unprecedented shape, not a pattern to copy from
#          anywhere. `TransformationNode.dbtDependencies` (typedefs.ts:843) LOOKS similar but
#          is confirmed to be a real plain-string-array PROPERTY (not edges) at
#          `transformation.ts:37` — a different, unrelated case, not evidence FOR the
#          undecorated approach.
#        - **DECISION, resolved pass 20: KEEP `dependsOn` DECORATED with `@relationship`**,
#          matching the quoted type above and the real AnomalyEventNode/MetricSnapshotNode
#          precedent exactly. Do NOT leave it undecorated — that path has no precedent and
#          was based on an incorrect premise (that decorating it would complicate the rest
#          of the type's generated mutation, which is false).
#        - Invariant 9's atomicity requirement STILL applies and is STILL not satisfiable
#          through the auto-generated `connectOrCreate` mutation alone (that part of the
#          original reasoning was correct) — but the fix is NOT "leave the field
#          undecorated." The fix is: the HAND-WRITTEN Cypher service (step 2 below) performs
#          the atomic delete-then-MERGE directly against the `:DEPENDS_ON` relationship type
#          the decorated field declares, using raw Cypher — NOT via the auto-generated
#          mutation's `connect`/`create` inputs. The OGM decorator and the write PATH are
#          separate concerns: decorate for schema/read-query correctness (so
#          `dependsOn` is queryable via the generated read API), but write through
#          hand-written Cypher for the atomicity guarantee, exactly like
#          `upsertWorkflowStep`/`deleteWorkflowStep` already do for `WorkflowStepNode`'s own
#          real, decorated `dependsOn` relationship — those functions bypass the
#          auto-generated mutation for writes too, while the type itself stays decorated for
#          reads. This is NOT a new pattern; it is the exact WorkflowStepNode precedent,
#          confirmed correctly cited from the start.
#     2. `src/graphql/service/neo4j/lineage-graph.ts` — NEW file: the delete-then-MERGE
#        upsert per Invariant 9, modeled on `metric-snapshot.ts`'s shape (194 lines), writing
#        directly against the `:DEPENDS_ON` relationship the decorated `dependsOn` field
#        declares — bypassing the auto-generated mutation for this specific write, per the
#        decision above.
#
#     RESOLVED pass 9 (triple-click-zoom) — the atomic-transaction API was under-specified;
#     now confirmed against real code, not generic Neo4j docs. `session.writeTransaction(...)`
#     (what earlier passes of this spec recommended) is DEPRECATED for this repo's actual
#     driver (`package.json:47`, `neo4j-driver: ^5.0.0` — v5 prefers `session.executeWrite`).
#     `workflow-spec.ts:557-581` (`deleteWorkflowStep`) proves ONE HALF of the needed
#     approach — a pure DELETE-only Cypher string, one `session.run()` call, auto-committed as
#     one implicit transaction, no new driver API. RECOMMENDATION, supersedes earlier
#     `writeTransaction` guidance: write the delete-then-MERGE as ONE multi-statement Cypher
#     string
#     (`MATCH (n:LineageNode {workspaceId: $workspace_id, uniqueId: $id})-[r:DEPENDS_ON]->()
#     DELETE r WITH n UNWIND $depIds AS depId MATCH (dep:LineageNode {workspaceId:
#     $workspace_id, uniqueId: depId}) MERGE (n)-[:DEPENDS_ON]->(dep)`), one `session.run()`
#     call. **`workspaceId` added to BOTH MATCH clauses pass 50** — without it on the `dep`
#     lookup specifically, a dependency edge could silently MERGE across workspaces if two
#     tenants' dbt projects happen to share a `uniqueId` (dbt's unique_id is
#     project-namespaced, not globally unique across unrelated customers' projects).
#     **CORRECTED pass 34 (triple-click-zoom) — this EXACT combined shape (DELETE + WITH +
#     UNWIND + MERGE, all in ONE string) has NO literal precedent anywhere in this repo,
#     verified by direct search — do not cite `deleteWorkflowStep` as proof it does.**
#     `deleteWorkflowStep` is DELETE-only (no MERGE, no UNWIND — confirmed by reading it in
#     full). The TWO real delete-then-recreate-from-a-list precedents that exist
#     (`upsertWorkflowStep`'s own DEPENDS_ON sync, `workflow-spec.ts:299-327`; and
#     `routine-ownership.ts:117-139`'s RECEIVES-edge sync, same shape) BOTH split delete and
#     recreate into TWO separate `session.run()` calls — the exact non-atomic pattern this
#     spec's Invariant 9 says NOT to copy. So: the GENERAL PRINCIPLE ("Neo4j auto-commits one
#     submitted multi-statement string as one implicit transaction, closing the crash window,
#     no new driver API needed") is real and correctly cited from `deleteWorkflowStep`. But
#     the SPECIFIC combined DELETE+UNWIND+MERGE query text above has no template anywhere in
#     this codebase to copy verbatim — BH-1063's implementer is writing this exact shape for
#     the first time in this repo, following the general pattern, not adapting an existing
#     example. Confirm the query syntax works as intended against a real Neo4j instance before
#     assuming it's "proven" merely because the general one-string principle is proven
#     elsewhere. Fall back to `session.executeWrite(tx => ...)` only if the upsert genuinely
#     needs to read an intermediate result back into JS before the MERGE (not expected here).
#     CONFIRMED pass 9: zero `executeWrite`/`writeTransaction`/`CALL {...} IN TRANSACTIONS`
#     usage exists anywhere in this repo today.
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
# version. FIX (confirmed pass 9, CORRECTED pass 34): the SAME repo proves the GENERAL
# PRINCIPLE elsewhere — `workflow-spec.ts:557-581` (`deleteWorkflowStep`) chains DELETE +
# further Cypher clauses as ONE multi-statement string in ONE `session.run()` call, which
# Neo4j auto-commits as one implicit transaction. BH-1063's upsert should follow THIS
# PRINCIPLE (one string, one call, not `upsertWorkflowStep`'s own two-call pattern — see
# Invariant 9 below) — but `deleteWorkflowStep` itself is DELETE-only, no MERGE/UNWIND, so it
# does NOT literally demonstrate BH-1063's actual delete-then-recreate-a-list shape. That
# combined shape has no template anywhere in this repo (confirmed pass 34) — write it fresh
# from the principle, don't expect a copy-paste source.

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
#   MATCH (start:LineageNode {workspaceId: $workspace_id, relationName: $anomaly_dataset})
#                   <-[:DEPENDS_ON*1..50]-(downstream:LineageNode)
#                   RETURN DISTINCT downstream
#
# CRITICAL, added pass 50 — `workspaceId` in the MATCH is NOT optional. relation_name alone
# is not guaranteed globally unique across workspaces (two customers' dbt projects can easily
# both have a model materializing to a same-named schema.table, e.g. "GOLD.mart_revenue").
# Without the workspace filter, this traversal could walk cross-tenant into a DIFFERENT
# workspace's lineage graph — a real data-isolation violation (PS-13), not merely a
# correctness nit. See Invariant 18.
#
# CORRECTED pass 33 (triple-click-zoom) — the original `*1..` (unbounded) query, verified
# against this repo's real Cypher conventions and general Neo4j semantics, needed two fixes:
#   1. **Bounded to `*1..50`**: confirmed NO precedent for variable-length hops exists
#      anywhere in this repo — every real DEPENDS_ON traversal (workflow-spec.ts:88,303,311,
#      336,576,597) is a fixed SINGLE-hop pattern, never `*`. At a real dbt project's actual
#      scale (a few hundred models, 10-20 hop depth), an unbounded `*1..` is NOT a
#      performance risk at Neo4j's execution-engine level (bounded by real graph size, not
#      the missing upper bound) — but it IS a real correctness risk: if the DAG is ever not
#      guaranteed acyclic (bad data, a bug, a self-referencing model), `MATCH` with an
#      unbounded variable-length pattern enumerates PATHS, not just reachable nodes, and can
#      blow up exponentially on a cycle. `*1..50` is defensive insurance — cheap, and a real
#      dbt DAG should never approach 50 hops of transitive depth in practice, so this bound
#      is not expected to ever clip a genuine result.
#   2. **`DISTINCT` added**: without it, a downstream node reachable via MULTIPLE paths
#      (a common, normal shape in any real DAG with diamond dependencies) would be RETURNED
#      MULTIPLE TIMES — the original query would have silently produced duplicate
#      downstream-table entries in the anomaly's enrichment metadata.
# RESOLVED pass 46 (was flagged here as an open "REMAINING GAP" — do not re-open without new
# evidence). dbt's `relation_name` format (`"DB"."SCHEMA"."TABLE"`, quoted, 3-part) is NOT
# repo-confirmed to string-match `asset_details.get("snowflakeTableName")`'s format directly —
# but this is no longer an unverified open question, because the SAME drift class (quoting,
# casing, 2-part vs 3-part) is CONFIRMED to already occur on the `AnomalyEventNode.dataset`
# side alone: traced end-to-end (quality_check_agent.py:362-366 -> longitudinal_node.py:348 ->
# metric_history_store.py:181, zero normalization anywhere in that path) and cross-referenced
# against the ALREADY-SHIPPED BH-743 fix (`_fqn_variants()`, longitudinal.py:150+), which
# exists precisely because Neo4j's exact-match filter does not case-fold or normalize on its
# own. See Invariant 10 for the full trace and required fix: BH-1064's traversal SHALL reuse
# `_fqn_variants()`'s existing normalization pattern rather than assume exact-match works.
#
# Writes into the metadata dict BEFORE publish_completion_notification's existing
# json.dumps(...) call (quality_check_agent.py:1663) — this ticket adds one new key, it does
# NOT touch or duplicate the existing publishNotification mutation call itself.
```

## 3. Invariants (DbC)

1. `WHEN manifest.json/catalog.json is fetched, THE System SHALL reuse the existing
   _fetch_artifact() plumbing — no new HTTP client, no new auth path.`
2. `IF catalog.json lacks column-level metadata for a model, THEN THE System SHALL degrade to
   model-level tracing and SHALL set has_column_metadata=False — it SHALL NOT silently produce
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
   from any other HTTP failure (auth error, 500, timeout) before recording has_column_metadata
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
   that suppresses a real alert). RESOLVED pass 9, CORRECTED pass 34: the GENERAL PRINCIPLE
   (one Cypher string, one session.run() call, auto-committed as one implicit transaction) is
   confirmed proven elsewhere in the SAME repo — workflow-spec.ts:557-581 (deleteWorkflowStep)
   chains DELETE + further clauses as one string, one call. Follow THAT PRINCIPLE (one
   string, one call), not upsertWorkflowStep's two-call shape. BUT: deleteWorkflowStep is
   DELETE-only (no MERGE/UNWIND) — the SPECIFIC combined DELETE+UNWIND+MERGE shape this
   invariant requires (delete existing edges, then recreate a NEW SET from a list) has NO
   literal template anywhere in this repo, confirmed pass 34 — the two real
   delete-then-recreate-from-a-list precedents that DO exist (upsertWorkflowStep's own
   DEPENDS_ON sync; routine-ownership.ts's RECEIVES-edge sync) both split delete and
   recreate into TWO separate calls, the exact non-atomic pattern this invariant forbids.
   Write the combined single-string shape fresh from the principle; verify it against a
   real Neo4j instance before assuming correctness. session.executeWrite(...) (the
   non-deprecated driver-v5 API, per package.json:47's neo4j-driver ^5.0.0 — NOT
   session.writeTransaction, which is deprecated at this version) is the fallback ONLY if the
   upsert needs to read an intermediate result back into JS before the MERGE, which is not
   expected here.

   RE-CONFIRMED pass 44 — `executeWrite`/`writeTransaction`/`beginTransaction` usage across
   platform-core's TypeScript `src/` is still zero (grep-confirmed again, not re-trusting the
   pass-9 finding blindly). The only place `write_transaction` (the driver's deprecated
   snake_case alias) is actually used in this org's codebase is two Python Lambdas —
   `openmetadata_webhook_lambda/utils/neo4j_client.py:158,176` and
   `neo4j_connector_lambda/db/neo4j_connector.py:77` — neither reachable from, nor precedent
   for, the TS OGM/GraphQL write path BH-1063 touches; do not cite them as proof this repo has
   an atomic-multi-statement pattern to copy. `neo4j_connector.py`'s
   `_create_and_connect_data_asset_tx` (lines 23-115) IS a real 5-statement atomic write inside
   one `write_transaction` call — but MERGE/CREATE-only, no DELETE, and in a different language
   and deploy unit. It demonstrates the driver CAN do this, not that this repo's TS layer ever
   has.`
10. `THE downstream-impact traversal (BH-1064) SHALL match a LineageNode against
    AnomalyEventNode.dataset using LineageNode.relation_name — it SHALL NOT match against
    LineageNode.unique_id or LineageNode.name. CRITICAL, found pass 10: unique_id/name live
    in dbt's model-identifier namespace ("model.my_project.stg_orders" / "stg_orders");
    anomaly.dataset lives in the warehouse-table namespace ("GOLD.mart_daily_portfolio_
    exposure", sourced from DataAssetNode's redshiftTableName/snowflakeTableName/tableFQN via
    quality_check_agent.py:362-366). Matching against the wrong field would silently return
    zero downstream tables for every real anomaly — no error, just a defeated epic. BH-1062
    MUST populate relation_name from dbt manifest.json's own relation_name field per node.

    RESOLVED pass 46 (triple-click-zoom) — the format-equality question is no longer
    hypothetical; confirmed against real code, and this org has ALREADY built and shipped the
    fix for the exact same drift class, just for a different pair of fields. Tracing
    `dataset`'s real value end to end: `quality_check_agent.py:362-366` resolves
    `dataset_table_name` via the SAME `DataAssetNode` fallback chain
    (redshiftTableName→snowflakeTableName→tableFQN→tableName) with ZERO normalization, flows
    unmodified through `longitudinal_node.py:348` and `metric_history_store.py:181` into
    `AnomalyEventNode.dataset`. Confirmed real-world drift, per
    `mcp/tools/longitudinal.py:100-110` and `tests/integration/golden_cases/
    test_longaeva_uat_mcp.py:340-346`: Snowflake actually stores this as 2-part, unquoted,
    mixed-case (`GOLD.mart_daily_portfolio_exposure`), while callers commonly pass 3-part,
    uppercase (`LONGAEVA_POC.GOLD.MART_DAILY_PORTFOLIO_EXPOSURE`) — and this exact
    casing/qualification drift was ALREADY a real bug (BH-743), already fixed client-side via
    `_fqn_variants()` (`longitudinal.py:150+`), because "the Neo4j `where: { dataset: <exact>
    }` filter is case-sensitive" (`longitudinal.py:109`) — Neo4j string equality does not
    case-fold or normalize on its own. dbt's `manifest.json` `relation_name` field is
    typically a quoted 3-part identifier (`"database"."schema"."table"`) — general dbt
    platform knowledge, NOT repo-confirmed, since zero manifest-parsing precedent exists here
    (unchanged from earlier passes). Given `dataset` is CONFIRMED to already vary in exactly
    the dimensions (quoting, casing, 2-part vs 3-part) `relation_name` would introduce, an
    exact-match Cypher lookup between the two is confirmed NOT safe to assume. FIX: BH-1064's
    traversal SHALL reuse the SAME variant-probe normalization pattern `_fqn_variants()`
    already established for this drift class (try exact form, then strip DB-prefix, then
    lowercase) rather than inventing a new one — either by calling an equivalent
    Cypher-side `toLower()`/prefix-stripped OR pattern, or by generating the same variant list
    client-side before the traversal query. This is a precedented fix to copy, not a new
    design problem.`
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
12. `WHEN fetching manifest.json/catalog.json for a real dbt project, THE System SHALL NOT
    assume _fetch_artifact()'s existing 30-second timeout and non-streaming
    requests.get()+json.loads() double-buffering pattern is safe at manifest.json scale
    (potentially tens of MB for large projects) merely because it works for run_results.json/
    sources.json (KB-scale, its only existing callers). CRITICAL, found pass 23: this
    function has NEVER been exercised at manifest.json's real scale in production. BH-1062
    SHALL EITHER (a) measure real latency/memory against an actual large project's
    manifest.json and explicitly document that the existing pattern is acceptable, with the
    measured numbers, OR (b) build a size-aware fetch path (longer artifact-specific
    timeout, streaming JSON parse) for manifest.json/catalog.json specifically — it SHALL
    NOT silently reuse the small-artifact-tuned function at 100x+ the data volume without
    doing one of these two things first.`
13. `WHEN BH-1064's downstream-impact traversal walks LineageNode's DEPENDS_ON edges, THE
    System SHALL use a BOUNDED variable-length pattern (e.g. *1..50, not an unbounded *1..)
    AND SHALL return DISTINCT results. CRITICAL, found pass 33: confirmed no precedent for
    variable-length Cypher hops exists anywhere in platform-core - every real DEPENDS_ON
    traversal is a fixed single-hop pattern. An unbounded variable-length MATCH enumerates
    PATHS, not just reachable nodes - if the DAG is ever not guaranteed acyclic (bad data, a
    bug, a self-referencing model), this can blow up exponentially on a cycle. Without
    DISTINCT, a downstream node reachable via multiple paths (a normal shape in any DAG with
    diamond dependencies) would be returned multiple times, producing duplicate
    downstream-table entries in the anomaly's enrichment metadata.`
14. `THE System SHALL NOT claim, imply, or name any field as "column lineage" for data
    sourced from dbt's catalog.json — catalog.json contains ZERO column-to-column
    DEPENDENCY information (general dbt platform knowledge, confirmed pass 36: it is a
    warehouse schema snapshot — "this model has these columns, with these types" — sourced
    from information_schema, not from parsing SQL derivation logic). `has_column_metadata`
    (RENAMED pass 36 from the misleading `has_column_lineage`) means ONLY "we know which
    columns exist for this model" — column EXISTENCE metadata, never column-level lineage
    (which output column derives from which upstream column). This spec's downstream-impact
    traversal (BH-1064) operates at the MODEL level only — it names which Gold/Diamond
    TABLES are affected, never which specific COLUMN within them is affected — and this
    invariant makes that limitation an explicit, permanent contract, not a temporary gap
    "flagged for a future pass." True column-level lineage would require dbt Cloud's
    separate, proprietary Column-Level Lineage feature or a third-party SQL parser (e.g.
    sqlglot) statically analyzing compiled SQL — genuinely new scope, out of this spec
    entirely (see §5 Out of Scope).`
15. `WHEN BH-1062's fetch_lineage_artifacts() fetches manifest.json/catalog.json for a
    specific run_id, THE System SHALL NOT assume the session's cached dbt Cloud
    credentials (account_id/api_token, resolved once per session by
    _find_connected_dbt_service()'s first-match behavior) are guaranteed to match the
    run_id's actual owning account/service. CRITICAL, found pass 44: confirmed
    _fetch_artifact() takes account_id/api_token as explicit params with no internal
    resolution, and its real analog call site reads them via a pure state read populated
    ONCE PER SESSION — run_id is NEVER used to select or validate the account, only
    interpolated into the artifact URL against whatever was cached at init. IF a workspace
    has multiple connected dbt Cloud services, a mismatch between the cached session
    credentials and the run_id's real owner risks either a 404 or, worse, silently
    fetching a WRONG account's manifest.json for an unrelated run_id — a cross-project
    data-shape confusion, not merely a missed poll. BH-1062's implementer SHALL either
    confirm this fetch always executes in the same session/state context that resolved
    the run_id (verified, not assumed), or thread the real account_id through explicitly
    from wherever the run_id was discovered. This mirrors the sibling
    proactive-pipeline-ingestion-monitoring.md spec's Invariant 16 (the same class of gap,
    confirmed in 2 of its 3 adapters) — this spec's own fetch step is a THIRD confirmed
    instance, not a hypothetical extension.`

16. `WHEN BH-1068's SnowflakeNativeLineageSource adapter queries SNOWFLAKE.ACCOUNT_USAGE.*
    views, THE System SHALL distinguish a genuine "no dependencies found" result from a
    permission failure ("the bound role lacks IMPORTED PRIVILEGES / ACCOUNTADMIN") and from
    a latency gap ("the view has not yet ingested this recently-created object"). CRITICAL,
    found pass 45: `SnowflakeConnection`'s own docstring (warehouse_connections.py:708-711)
    states the account SHOULD bind to a SELECT-only, least-privilege role — exactly the
    posture ACCOUNT_USAGE views reject without an explicit IMPORTED PRIVILEGES grant. This
    already happened in this org: the real deployed Longaeva POC role
    (`LONGAEVA_POC_ROLE`, SNOWFLAKE_POC_HANDOFF.md:32) hit this precisely, and the
    documented fix (`#825`, same doc line 64) was to SILENCE the resulting per-query
    failures, not detect or resolve them. An adapter that treats a silenced permission
    failure as "confirmed zero lineage" reports false negatives for every customer running
    the recommended least-privilege posture — the majority case, not an edge case. THE
    adapter SHALL surface a distinct, typed error/status for a permission failure (never
    fold it into an empty result), and SHALL check each queried view's last-refresh
    freshness before treating an empty result for a recently-created object as
    authoritative.`

17. `WHEN BH-1069's upsert_lineage_graph() is called once per model in a loop (a real dbt
    project can have hundreds of models per manifest), THE System SHALL reuse ONE
    OGMAPISession instance constructed OUTSIDE the loop — it SHALL NOT rely on the bare
    `session or OGMAPISession()` default inside the loop body. CRITICAL, found pass 49:
    `OGMAPISession.__init__` (ogm_api.py:44-56) opens a `requests.Session()` and
    unconditionally performs a live Cognito `USER_PASSWORD_AUTH` HTTP round-trip
    (`_authenticate()`, ogm_api.py:90-127) on EVERY construction — confirmed no
    module/class-level token cache exists anywhere in `ogm_api.py`, and no
    `__enter__`/`__exit__`/`close()`/`__del__` exists to deterministically release the opened
    connection pool. This default idiom is safe for this repo's 9 EXISTING call sites (each
    fires once per agent turn) but would multiply into hundreds of Cognito logins and leaked
    connection pools per manifest load if copied unmodified into a per-model loop — a real
    cost and resource-leak risk, not a style nit.`

18. `LineageNode SHALL carry a native workspaceId: String! scalar field, and EVERY Cypher
    query targeting LineageNode (the delete-then-MERGE upsert per Invariant 9, and BH-1064's
    downstream-impact traversal per Invariant 10) SHALL filter on workspaceId in its MATCH
    clause, not merely on relationName/uniqueId. CRITICAL, found pass 50: every OGM node type
    checked in this codebase (WorkflowStepNode, MetricSnapshotNode, AnomalyEventNode) has at
    least one relationship chain reaching WorkspaceNode; LineageNode's own decorated
    relationship (dependsOn) points to OTHER LineageNodes, not to any workspace-scoped
    anchor — it does NOT close the same scoping loop dataAsset does for
    AnomalyEventNode/MetricSnapshotNode. Without an explicit workspaceId filter, dbt's
    unique_id (project-namespaced, not globally unique across unrelated customers) or a
    warehouse-side relation_name collision (two tenants both materializing to a
    similarly-named schema.table) could cause a cross-tenant MATCH — either silently deleting
    or MERGE-ing another workspace's edges (a write-side isolation violation), or walking
    BH-1064's downstream-impact traversal into a different workspace's graph (a read-side
    isolation violation). This is a data-isolation requirement (PS-13), not a correctness
    nit — LineageNode would otherwise be the first node type in this codebase with zero
    workspace-scoping mechanism of any kind.`

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

  Scenario: the traversal survives the SAME FQN drift already fixed once for this org (BH-743)
    Given a LineageNode with relation_name stored as dbt's quoted 3-part form
      ("db"."GOLD"."mart_daily_portfolio_exposure")
    And an AnomalyEventNode with dataset stored in the Snowflake 2-part unquoted mixed-case
      form ("GOLD.mart_daily_portfolio_exposure") — CONFIRMED real drift, per
      longitudinal.py:100-110 and the existing BH-743 fix for this exact class of mismatch
    When BH-1064's traversal looks up the starting node for this anomaly
    Then it finds the node by reusing the SAME variant-probe normalization _fqn_variants()
      already applies for this drift class (exact form, then DB-prefix stripped, then
      lowercased) — not a fresh, unproven normalization scheme
    And it does NOT silently return zero downstream tables merely because the two fields'
      quoting/casing/part-count differ

  Scenario: the traversal is bounded and deduplicated
    Given a LineageNode with two separate DEPENDS_ON paths converging on the SAME downstream
      node (a diamond-shaped dependency, a normal real-world DAG shape)
    When BH-1064's traversal walks DEPENDS_ON edges forward from the anomaly's starting node
    Then the downstream node appears EXACTLY ONCE in the result, not once per path
    And the traversal uses a bounded hop count (e.g. *1..50), not an unbounded *1.., so a
      future data bug introducing a DEPENDS_ON cycle cannot cause exponential path blowup

  Scenario: graceful degradation when column-level metadata isn't available
    Given a dbt project whose catalog.json lacks column-level metadata
    When an anomaly fires on a column in that project
    Then the system traces impact at the MODEL level only
    And has_column_metadata=False is recorded, not silently claimed otherwise
    And this is unaffected by Invariant 14 — the traversal is ALWAYS model-level regardless
      of has_column_metadata's value, since catalog.json never contains column-DEPENDENCY
      data in any dbt version

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
    And has_column_metadata is NOT silently set to False as if the artifact were simply absent

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

  Scenario: fetching a real, large manifest.json does not silently reuse an unproven pattern
    Given a dbt project with hundreds of models, whose manifest.json is tens of megabytes
    When BH-1062 fetches this manifest via a wrapper around _fetch_artifact()
    Then EITHER real latency/memory was measured against an actual large project's
      manifest.json and documented as acceptable, OR a size-aware fetch path (longer
      timeout, streaming parse) was built for this artifact class specifically
    And the existing 30-second timeout tuned for KB-scale run_results.json/sources.json is
      NOT silently assumed safe at 100x+ that data volume without one of the above

  Scenario: the manifest fetch never uses stale session-cached credentials for a mismatched run_id
    Given a workspace with TWO connected dbt Cloud services (accounts A and B)
    And the session's cached credentials currently point at account A (the first-matched
      service, per _find_connected_dbt_service()'s known first-match behavior)
    When BH-1062 fetches manifest.json for a run_id that actually belongs to account B
    Then the fetch does NOT silently succeed against account A's manifest.json for account
      B's run_id (a cross-project data-shape confusion)
    And EITHER the fetch call is confirmed to always execute in the same session context
      that resolved this specific run_id, OR the real account_id is threaded through
      explicitly rather than read from session-cached state

  Scenario: a least-privilege Snowflake role's permission failure is never read as "no dependencies"
    Given a Snowflake connection bound to a SELECT-only, least-privilege role — the posture
      SnowflakeConnection's own docstring recommends — which lacks IMPORTED PRIVILEGES on
      the SNOWFLAKE database
    When BH-1068's SnowflakeNativeLineageSource queries SNOWFLAKE.ACCOUNT_USAGE.
      OBJECT_DEPENDENCIES for a real table with real dependencies
    Then the query's permission failure is surfaced as a distinct, typed error/status
    And it is NOT silently swallowed or folded into an empty "zero dependencies" result,
      the way #825's fix (SNOWFLAKE_POC_HANDOFF.md:64) already did for this org's real
      Longaeva POC role
    And the adapter does not report "this table has no dependencies" when the true state is
      "this role cannot see dependencies"

  Scenario: a freshly-created Snowflake Task's dependency is never read as "does not exist"
    Given a Snowflake Task created less than the ACCOUNT_USAGE view's documented refresh
      latency window ago (up to ~45 min–3 hrs, view-dependent)
    When BH-1068 queries OBJECT_DEPENDENCIES for that Task immediately after creation
    Then an empty result is treated as "not yet reflected, latency window not elapsed" if
      the view's own freshness/last-refresh signal indicates so
    And BH-1064's downstream-impact traversal does NOT treat this empty result as
      authoritative proof "nothing depends on this" while the latency window is still open

  Scenario: upserting a full manifest's worth of models never re-authenticates per model
    Given a real dbt manifest.json with hundreds of models
    When BH-1069's caller loops over every model, calling upsert_lineage_graph() once per model
    Then exactly ONE OGMAPISession is constructed for the entire loop, passed explicitly into
      every call
    And the loop does NOT rely on the bare `session or OGMAPISession()` default per iteration,
      which would perform a fresh Cognito login and open a new unclosed connection pool on
      every single model

  Scenario: the lineage graph never leaks across workspaces on a colliding identifier
    Given workspace A has a LineageNode with uniqueId "model.shared_proj.stg_orders" and
      relation_name "GOLD.mart_revenue"
    And workspace B has a DIFFERENT LineageNode that happens to share the SAME uniqueId
      and/or relation_name (a real possibility — dbt's unique_id is project-namespaced, not
      globally unique across unrelated customers, and warehouse schema/table names commonly
      collide across tenants)
    When BH-1063's delete-then-MERGE upsert runs for workspace A, and separately when
      BH-1064's downstream-impact traversal runs for an anomaly in workspace A
    Then neither operation matches, deletes, merges, or returns workspace B's LineageNode or
      its edges
    And both operations' Cypher MATCH clauses filter on workspaceId, not merely on
      uniqueId/relationName alone
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
- **True column-level lineage (which output column derives from which upstream column).**
  ADDED pass 36, made explicit by Invariant 14 — confirmed dbt's `catalog.json` contains no
  column-dependency data at all, only column-existence metadata (a warehouse schema
  snapshot). This spec's downstream-impact traversal operates at the MODEL/TABLE level
  only. Real column-level lineage would require dbt Cloud's separate, proprietary
  Column-Level Lineage feature or a third-party SQL parser (e.g. sqlglot) statically
  analyzing compiled SQL — a genuinely new, separate initiative if ever pursued, not a
  natural extension of this spec's artifact-consumption approach.

## 6. Dependencies

| Dependency | Type | Status |
|---|---|---|
| Longitudinal monitoring (GC-12, BH-601) | Blocking (this spec enriches its alerts) | Shipped + staging-verified |
| BH-673 (anomaly→lineage bridge) | This spec's BH-1064 closes it | Deferred, now actively scoped |
| `_fetch_artifact()` plumbing (dbt_cloud_tools.py) | Non-blocking (reused, not built here) | Live |
| `WorkflowStepNode`'s `DEPENDS_ON` delete-then-MERGE precedent (`workflow-spec.ts:299-317`) | Non-blocking (pattern mirrored, not reinvented) — corrected pass 1, was wrongly cited as DataAssetNode | Live |
| brightbot's OGM HTTP path (`ogm_api.py:34-70`) | Blocking — BH-1063's brightbot half MUST go through this, no new Neo4j driver | Live |
| **platform-core engineering capacity** (verified pass 1: BH-1063 is 2-repo work) | Blocking — this spec cannot ship with brightbot-only resourcing | New dependency, not previously called out |
| BH-1044 (Databricks credential storage/lookup design) | Blocking for the Databricks half, but NOT sufficient by itself — see below | **RE-CHECKED pass 53 (fresh, not carried forward)**: no longer just an "open decision" — its own ticket (pass 24, in the sibling proactive-pipeline-ingestion-monitoring.md's Track B scope) resolved the design to a concrete pattern: mirror dbt's per-CONNECTION direct-boto3 secret read (`_retrieve_dbt_cloud_api_token()`, `credentials_tools.py:166-200`) keyed on `(workspace_id, service_id)`, not workspace_id alone, with no caching layer. Confirmed Jira status still `Needs Refinement` — the DESIGN is settled, the code is not yet built. This spec's Databricks lineage adapter (DatabricksLineageSource) should reuse this SAME resolved credential pattern once BH-1044 ships, not re-derive its own. |
| Databricks connection-type plumbing (new WarehouseType enum + connector + Unity Catalog system-schema enablement) | Blocking for the Databricks half, independent of BH-1044 | **CORRECTED pass 7**: confirmed zero Databricks code exists in brightbot or platform-core outside vendored deps — this is greenfield regardless of how BH-1044 resolves, not merely gated behind it |
| BH-1066 (anomaly-notification renderer, Slack + webapp) | Non-blocking for BH-1064's own code; blocking for the enrichment to ever be human-visible | Filed pass 5, **CORRECTED pass 48**: not a new `NotificationStage`/`BackendStage` case — the `metadata.longitudinal` blob already rides inside the existing `quality_asset_result` stage; this ticket enriches that stage's renderer to surface `anomaly_count`/`families` (real fields — `dataset`/`family`/`severity` do NOT exist on this blob, an earlier pass's ticket text was wrong), downgraded M→S |
| Existing `SnowflakeConnection` (`warehouse_connections.py:701,714,1233`) | Non-blocking for BH-1068 (Snowflake-native adapter, reused not built) | Live — permits arbitrary `SELECT` syntactically, but **CORRECTED pass 45**: its own docstring recommends a least-privilege role, and ACCOUNT_USAGE reads need IMPORTED PRIVILEGES/ACCOUNTADMIN — confirmed via SNOWFLAKE_POC_HANDOFF.md that the real Longaeva POC role already hit and silenced this exact permission gap (`#825`) |
| BH-1068 (Snowflake-native lineage adapter: Snowpipe/Tasks/Streams/Dynamic Tables via ACCOUNT_USAGE) | Non-blocking for 7/17; cheaper than the Databricks half (gap 4) but equally unbuilt | **Filed pass 8, CORRECTED pass 45**: "no new connection type" is true but understates the real gap — needs a new Invariant 16 permission/latency guard (least-privilege roles silently fail ACCOUNT_USAGE reads; views lag INFORMATION_SCHEMA by up to hours) or it will report false "zero lineage" for the recommended, common role posture |

## 7. Correctness Properties

**Added pass 14 (triple-click-zoom) — required per `spec-driven.md`'s §7 trigger: this spec
involves a state machine (LineageNode's DEPENDS_ON edges, delete-and-recreate per manifest
run) and a correctness-critical traversal (BH-1064's downstream-impact walk, whose match-key
bug was the CRITICAL finding of pass 10). Both conditions trigger the §7 requirement.**

### Property 1: a LineageNode's DEPENDS_ON edges never observably reach zero mid-upsert

*For any* LineageNode with N ≥ 1 existing DEPENDS_ON edges, a crash or failure during a
manifest-driven upsert SHALL NOT leave that node observably at 0 edges before the new edge
set is fully applied — the delete-and-recreate is atomic (one Cypher string, one
`session.run()` call).

**Validates: §3 Invariant 9, §4 Scenario "a crash mid-upsert never leaves a model with zero
lineage edges"**

### Property 2: the downstream-impact traversal never matches the wrong identifier namespace

*For any* AnomalyEventNode with a `dataset` value, the traversal that finds its starting
LineageNode SHALL match against `LineageNode.relation_name`, which SHALL be populated from
the same warehouse-qualified namespace as `AnomalyEventNode.dataset` — never against
`LineageNode.unique_id` or `LineageNode.name`, which live in dbt's own model-identifier
namespace and would silently match zero nodes for a real anomaly. **Extended pass 46**:
namespace-correctness alone is not sufficient — `dataset` is CONFIRMED (via the already-
shipped BH-743 fix) to vary in quoting/casing/part-count even within its own correct
namespace, so the match SHALL also apply the SAME `_fqn_variants()`-style normalization
already precedented for this drift class, not a bare exact-match. **Extended pass 50**:
correctness within a single workspace is also not sufficient — the match SHALL additionally
filter on `LineageNode.workspaceId`, since `relation_name` is not guaranteed unique ACROSS
workspaces (two tenants' warehouses can share a schema.table name); omitting this filter
risks a cross-tenant match, a data-isolation violation (PS-13) distinct from the
namespace/format-correctness this property already covers.

**Validates: §3 Invariant 10, §4 Scenarios "the traversal never matches against the wrong
identifier namespace" and "the traversal survives the SAME FQN drift already fixed once for
this org (BH-743)"**

### Property 3: a GraphQL-level mutation failure is never silently treated as success

*For any* call to platform-core's `upsertLineageGraph`-equivalent mutation via
`OGMAPISession.mutation()`, a response containing a non-empty `"errors"` key SHALL be treated
as a failure by the caller — regardless of the HTTP status code being 200.

**Validates: §3 Invariant 11, §4 Scenario "a GraphQL-level mutation failure is never mistaken
for success"**

### Property 4: a genuine fetch error is never conflated with "no lineage available"

*For any* `_fetch_artifact()` call that fails for a reason OTHER than a genuine 404
(artifact never generated), the resulting `LineageArtifacts.fetch_error` SHALL be non-None —
`has_column_metadata` SHALL NOT be silently set to `False` as if the artifact were simply
absent.

**Validates: §3 Invariant 7, §4 Scenario "a real fetch error is never mistaken for 'no
lineage available'"**

## 8. Eval Criteria

This spec's behavior is deterministic Cypher/HTTP logic, not LLM-judged output — per
`spec-driven.md`, §8 is required "for every agent/tool spec that touches LLM output," which
this spec's BH-1062/1063/1064 do NOT (they are parsers, graph mutations, and a Cypher
traversal — no LLM call in the critical path). **§8 is explicitly omitted per the spec
template's own stated exemption**, not skipped by oversight — this is a deliberate,
documented decision, not a gap. If a future pass adds an LLM-summarized "what changed
downstream" explanation (e.g. for BH-1066's rendered notification text), that addition would
require its own §8 entry at that time.

## 9. Observability Contract

**Added pass 14, per `spec-driven.md`'s conditional trigger ("when spec produces a
production surface") — this spec produces the Neo4j lineage graph and the enriched anomaly
metadata, both production surfaces.**

- **Span**: none proposed in this pass — GC-12/longitudinal monitoring's own precedent
  (`quality_check_agent.py`) has ZERO OTel spans today (confirmed in the sibling
  proactive-pipeline-ingestion-monitoring.md spec's pass 30: "GC-12 has ZERO actual OTel
  observability to mirror... only plain `logger.info()` calls, no spans, no dotted log
  events"). This spec's BH-1062/1063/1064 SHOULD be the first real instrumentation of this
  capability-node class (mirroring that sibling spec's own §9 house-style precedent), not
  copy GC-12's absence of one.
- **Log events** (new, this spec): `lineage.fetch.started`, `lineage.fetch.success`,
  `lineage.fetch.error` (Invariant 7's fetch_error case), `lineage.upsert.started`,
  `lineage.upsert.success`, `lineage.upsert.graphql_error` (Invariant 11's `"errors"`-key
  case — this event is the DIRECT observability hook for Property 3 above; without it, a
  silent GraphQL failure has no operator-visible trace at all), `lineage.traversal.no_match`
  (when BH-1064's traversal finds zero downstream nodes — this event is what would have
  caught pass 10's original match-key bug in production, had it shipped; every occurrence
  should be reviewed as a potential normalization miss even AFTER Invariant 10's
  `_fqn_variants()`-style fix lands per pass 46 — that fix covers the KNOWN drift dimensions
  found so far, not a formal proof no other drift dimension exists).

  **ADDED pass 52 (triple-click-zoom)**: `lineage.workspace_scope.violation_prevented` —
  emitted whenever a Cypher query's `workspaceId` filter (Invariant 18, pass 50) is the
  DIFFERENCE between a match and a non-match, i.e. a `uniqueId`/`relationName` match existed
  in the graph but belonged to a DIFFERENT workspace than the caller's. This is a
  security-relevant signal, not a generic no-match case — folding it into
  `lineage.traversal.no_match` would hide a real cross-tenant collision behind a routine
  "nothing found" log, undermining the exact isolation guarantee Invariant 18 exists to
  provide observable proof of. Since Invariant 18 introduced the FIRST workspace-scoping
  mechanism on `LineageNode`, this event has no precedent to mirror in this codebase — it is
  new instrumentation, not a gap being closed on existing code.
- **Metrics**: none proposed in this pass — could be added later (e.g.
  `lineage_traversal_no_match_rate`) once real production volume exists to judge a threshold
  against; premature to define one now.

## 10. Test Coverage Update

**Verified pass 14 against real test-suite paths in both repos — not invented paths.**

### a. In-repo layered evals / unit tests

- **brightbot**: `brightbot/tests/unit/agents/test_longitudinal_node.py` is the REAL existing
  test file for `longitudinal_node.py` (BH-1064's own cited precedent). BH-1064's traversal
  logic (`find_downstream_impact`) should get its test cases added to a new sibling file
  (e.g. `test_pipeline_watchdog_node.py`-adjacent, or directly alongside if BH-1064's node
  lives in the same module) — NOT a new greenfield test file competing with this one.
  `brightbot/brightbot/evals/` exists (`evals/test_suites/{deterministic_tests.py,
  test_cases.py}`) but has ZERO existing GC-12/longitudinal-named eval cases (confirmed by
  grep) — there is no eval file to extend for this capability class yet; if BH-1062/1063/1064
  need eval-level coverage beyond unit tests, it starts a new pattern, not extends one.
- **brighthive-platform-core**: `tests/unit/workflow-spec-status-enum.test.ts` is
  `upsertWorkflowStep`'s only direct unit coverage (enum-focused, not the mutation logic
  itself) — `tests/integration/execute-workflow-as-owner.test.ts` exercises the mutation
  end-to-end. **CONFIRMED GAP**: `src/graphql/service/neo4j/metric-snapshot.ts`
  (AnomalyEventNode/MetricSnapshotNode, this spec's own cited OGM-only precedent for
  BH-1063b) has NO dedicated test file anywhere in `tests/unit/` or `tests/integration/` —
  BH-1063b's new `lineage-graph.ts` service would be extending an UNTESTED precedent. This
  spec's own §10 obligation is therefore to add BOTH `lineage-graph.ts`'s tests AND,
  separately, **BH-1070 filed pass 14** to close `metric-snapshot.ts`'s own test gap (not
  required by THIS spec's scope, but tracked so the precedent doesn't stay permanently
  untested).

### b. Cross-repo / end-to-end tests

- **brighthive-e2e** (confirmed real, checked out at `../brighthive-e2e`):
  `e2e/features/data/test_longitudinal.py` + `specs/data/SPEC-E2E-LONGITUDINAL.md` are the
  real longitudinal-monitoring e2e precedent to extend for the anomaly-detection half.
  `e2e/surfaces/test_neo4j_integrity.py` is the real surface test to extend for
  LineageNode/DEPENDS_ON graph-integrity assertions (Property 1/2 above should get surface
  cases here, not a new file). **ADDED pass 52**: Invariant 18's cross-tenant isolation case
  ("the lineage graph never leaks across workspaces on a colliding identifier") belongs here
  too, against a real two-workspace Neo4j fixture — a mocked/single-workspace test cannot
  exercise this invariant, since the whole risk is TWO real workspaces sharing a colliding
  `uniqueId`/`relationName`. **No workflow-spec-lineage-specific e2e test exists yet** —
  this spec's §10 obligation includes adding the FIRST such case, not extending one that
  doesn't exist.

### Anti-pattern check (per spec-driven.md's own list)

This section's obligation is NOT satisfied by unit tests alone — per `test-behavior-real.md`,
at least one L2 case must be a real-behavior test. For BH-1063b specifically, that means a
test against a REAL Neo4j instance (not a mocked driver) confirming the one-string
delete-then-MERGE actually behaves atomically under a real crash/interrupt simulation, not
just that the Cypher string is syntactically well-formed.

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Manifest/catalog fetch + parse (BH-1062) | `brightbot` | New parser module, reuses existing artifact-fetch plumbing |
| Lineage graph schema + upsert mutation (BH-1063b) | **`brighthive-platform-core`** — corrected, was miscast as brightbot-only | **CONFIRMED pass 9, CORRECTED pass 34**: 2-3 files, zero public-schema touch — `src/graphql/ogm/typedefs.ts` (new `LineageNode` OGM type) + `src/graphql/service/neo4j/lineage-graph.ts` (hand-written delete-then-MERGE as ONE multi-statement Cypher string, one `session.run()` call, per `workflow-spec.ts:557-581`'s proven GENERAL PRINCIPLE — not `session.writeTransaction`, deprecated at this repo's `neo4j-driver ^5.0.0` — but the SPECIFIC combined DELETE+UNWIND+MERGE query shape has no literal template anywhere in this repo, write it fresh) + optionally `src/common/types.ts`. Mirrors `AnomalyEventNode`/`MetricSnapshotNode`'s OGM-only pattern (BH-668), a cheaper precedent than `WorkflowStepNode`'s public-mutation shape (`workflow-spec.ts:299-317`) — platform-core runs the OGM schema on a physically separate, `isSystemAdmin`-gated API Gateway endpoint from the public/webapp schema, confirmed via `ogm-server.ts:78-108` |
| Lineage graph call site (BH-1069, formerly informal "BH-1063a") | `brightbot` | Calls the new platform-core mutation over the EXISTING `ogm_api.py` HTTP path — no new Neo4j driver code, plus the new GraphQL-`"errors"`-key check (Invariant 11) AND a single shared `OGMAPISession` across the per-model loop (Invariant 17, pass 49) |
| Anomaly-alert enrichment (BH-1064) | `brightbot` (governance_agent) | **CORRECTED pass 52 — this row was stale/wrong, contradicting this same spec's own pass-4 finding.** NOT "extends BH-1046's existing alert path" — confirmed (pass 4) there is no rendered Slack/webapp alert path to extend at all; the real insertion point is a new key inside `publish_completion_notification`'s existing JSON metadata dict (`quality_check_agent.py:1663`), and the base anomaly notification itself has zero human-visible rendering until BH-1066 ships (pass 5/48). This ticket adds `downstream_tables` data with nothing to render it until BH-1066 lands — not a delivery-mechanism extension. |

## Ticket Breakdown

| Ticket | Summary | Status |
|---|---|---|
| BH-1061 | Epic: Lineage-Aware Data Quality | Needs Refinement |
| BH-1062 | feat: fetch + parse manifest.json/catalog.json | Needs Refinement |
| BH-1063 | feat: load parsed DAG into Neo4j as queryable lineage graph | Needs Refinement |
| BH-1064 | feat: wire anomalies to walk the graph forward (closes BH-673) | Needs Refinement |
| BH-1065 | verify: does anything render anomaly JSON into visible Slack/webapp text today? | **Done, pass 5 — answer confirmed NO**, see BH-1066 |
| BH-1066 | feat: enrich the EXISTING quality_asset_result renderer (Slack + webapp) to surface metadata.longitudinal's real anomaly_count/families fields | Needs Refinement, filed pass 5, **CORRECTED pass 48** (not a new stage, real fields only, S not M) — blocks BH-1064's enrichment from being human-visible, does not block BH-1064's own code |
| BH-1068 | feat: Snowflake-native lineage adapter (Snowpipe/Tasks/Streams/Dynamic Tables via ACCOUNT_USAGE) | Needs Refinement, filed pass 8, **CORRECTED pass 45** — reuses existing SnowflakeConnection (no new connection type) but requires a permission/latency guard: the recommended least-privilege role posture already silently fails ACCOUNT_USAGE reads in this org's real Longaeva POC deployment (`#825`) |
| BH-1069 | feat(lineage): brightbot call site for upsert_lineage_graph | Needs Refinement, filed pass 11, **CORRECTED pass 49** — formerly informal "BH-1063a," now its own trackable ticket; per-model loop MUST share ONE OGMAPISession, not the bare default (real Cognito-login/connection-leak cost otherwise) |
| BH-1070 | test: add missing unit/integration coverage for metric-snapshot.ts | Needs Refinement, filed pass 14 — pre-existing tech debt found while writing §10, non-blocking for this epic's own tickets |

## Track D: per-Project pipeline health view (proposed, genuinely new — NOT yet a committed scope)

**Added pass 11, user-raised**: "we need to surface this work to a PROACTIVE view on projects
... projects should have its own dedicated [timeline view] for pipelines." **CORRECTED pass
13**: pass 11's premise was WRONG in a materially important way — this is NOT a greenfield
tab to add. A much richer "Flow" implementation already exists than pass 11 found, and it
already HAS run-history/timeline components; the real work here is fixing 7 confirmed defects
in that existing implementation, not building a new one.

### CORRECTION, pass 13 — pass 11's "no timeline/run-history view exists" claim was FALSE

Pass 11 investigated `src/ProjectWorkflow/ProjectWorkflow.tsx` and concluded "Flow" is a
static DAG with no run-history/timeline capability anywhere in the webapp. Re-verified pass
13: **`ProjectWorkflow.tsx` is legacy, effectively dead code today.**
`ProjectWorkflowPage.tsx:522-523`'s own comment ("For now: always prefer the spec page to
allow gradual migration") confirms the "Flow" tab (`project-workflow` route,
`ProjectNavBar.tsx:97-98`) now renders `WorkflowSpecPage.tsx` in every real case —
`workflowSpec` is either a real spec object or `null` after load, never staying `undefined`
long enough for the legacy `<ProjectWorkflow>` branch (line 567) to fire. `WorkflowSpecPage`
mounts BOTH `RunHistoryPanel.tsx` (a real, paginated run-history-over-time list with
per-run/per-step expansion, `LIST_WORKFLOW_RUNS` query) AND `RunTimeline.tsx` (a live,
floating run-status panel) directly (`WorkflowSpecPage.tsx:1024-1037`). **Timeline and
run-history capability already exists and already ships today** — it is not a gap Track D
needs to fill from scratch.

### What's REAL and CONFIRMED today (verified pass 13, superseding pass 11's investigation)

`WorkflowSpecPage.tsx` is a rich, already-shipped authoring/monitoring surface: a canvas
(`WorkflowSpecCanvas.tsx`) of step nodes (`WorkflowSpecStepNode.tsx`), a 3-tab step drawer
(Config / Bindings / Issues, `StepDetailDrawer.tsx`), a compile-readiness panel
(`CompilePanel.tsx`), the run-history panel and live run timeline above, and an artifact
viewer. This is dramatically more capable than pass 11's "static DAG" characterization.

**But a direct 7-point UI audit against this exact implementation (pass 13, all 7 CONFIRMED
against real code) found it has real, shipped defects that should be FIXED before any new
capability (lineage-aware alerts, watchdog signals) is layered on top:**

1. **Legacy fallback is dead code, not a real fallback.** `ProjectWorkflowPage.tsx:522-523`'s
   comment implies a fallback exists; the gating condition makes the legacy branch (line 567)
   unreachable in practice. Either remove the dead code or fix the condition — leaving it
   creates false confidence that a safety net exists.
2. **Not mobile-compatible.** Fixed pixel widths with zero responsive handling:
   `StepDetailDrawer.tsx:1587` (480px), `CompilePanel.tsx:140` (520px),
   `RunHistoryPanel.tsx:519` (680px), `RunTimeline.tsx:461` (560px, `position: fixed`). All
   overflow a 320px viewport — zero `@media`/`useMediaQuery`/breakpoint logic exists in any
   of these 4 files (grep, zero hits). Violates this org's own mobile-first rule
   (`code-style.md`/global CLAUDE.md: "Forms, drawers, modals must work on 320px+ screens").
3. **Header is overloaded.** `WorkflowSpecPage.tsx`'s header region injects 6 action controls
   (run-history icon, Add step, Compile, Run/Running, Schedule, overflow "More" menu) plus an
   Active/Paused toggle into a shared `HeaderContainer` grid that sets `overflow: "hidden"`
   (`ProjectAgentHeader/style.ts:11`) alongside the project tab bar and workflow title — a
   real crowding risk, confirmed structurally, not assumed.
4. **Feature visibility is inconsistent — a real access-control gap, not cosmetic.**
   `routeConstants.ts:177` hides "Flow" by default (`WHITELIST_ONLY_ROUTES`) and
   `ProjectAgentHeader/index.tsx:109` sets `strictAdminOnly: true` for its tab — but the
   ACTUAL route guard (`routes/index.tsx:588-591`) admits both `Admin` AND `Collaborator`
   roles. A Collaborator who knows/bookmarks the URL can reach a page the tab bar hides from
   them — the tab-level gate and the route-level gate disagree. This is a genuine
   inconsistency worth fixing regardless of Track D.
5. **No direct-manipulation authoring, despite looking like an editor.**
   `WorkflowSpecCanvas.tsx:234` sets `nodesDraggable={false}`; no `onConnect` handler exists
   anywhere in the file — nodes can't be moved, edges can't be drawn. The canvas visually
   invites interaction it doesn't support.
6. **Weak accessibility.** `WorkflowSpecStepNode.tsx:69` uses a plain `<Box onClick={...}>`
   with no `onKeyDown`/`role`/`tabIndex` — unreachable via keyboard. Zero `aria-*` attributes
   exist across all 7 audited files (grep, zero hits).
7. **No focused UI tests.** Zero `*.test.tsx` files exist for any of the 7 components. The
   only e2e coverage (`tests/e2e/project-workflow.spec.ts:219-251`) is a generic smoke test
   whose one substantive assertion self-skips with zero check when the expected button isn't
   found (lines 233-236) — a test that can silently pass while asserting nothing.

### The real proposal, corrected

Track D is now TWO separable pieces, not one:

- **D1 — fix the 7 confirmed defects above in the EXISTING `WorkflowSpecPage`** (mobile
  responsiveness, the dead legacy branch, the header crowding, the tab/route access-gate
  mismatch, direct-manipulation gaps, accessibility, test coverage). This is real,
  scoped, already-buildable work against a surface that exists today — closer to a bug/tech-
  debt backlog than a new-feature proposal.
- **D2 — surface THIS epic's signals (watchdog detections, longitudinal anomalies,
  downstream-impact enrichment) inside `WorkflowSpecPage`'s EXISTING run-history/timeline
  components**, rather than building a new 7th tab from scratch. `RunHistoryPanel`/
  `RunTimeline` already show `WorkflowRunOutput` step-level status over time — the natural
  extension is enriching THOSE existing panels with anomaly/watchdog data
  (`TransformationNode.lastRunStatus`/`lastRunAt`, `AnomalyEventNode`,
  `PipelineHealthSignal` from the sibling spec, this epic's `downstream_tables` enrichment),
  not adding a competing new tab. This reframes the proposal from "build a new view" to
  "enrich an existing, already-shipped view" — cheaper and avoids duplicating
  `RunHistoryPanel`'s own run-tracking logic.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  CORRECTED pass 13: enrich WorkflowSpecPage's EXISTING panels, don't      │
│  build a competing new tab                                                │
└───────────────────────────────────────────────────────────────────────────┘

  "Flow" tab (ProjectNavBar.tsx) → WorkflowSpecPage.tsx (REAL, already shipped)
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Canvas (WorkflowSpecCanvas) │  RunHistoryPanel  │  RunTimeline     │
  │  step nodes, drawers          │  (D2: enrich with │  (D2: enrich    │
  │  (D1: fix 7 defects first)   │  anomaly/watchdog │  with live       │
  │                                │  data per run)    │  watchdog status)│
  └─────────────────────────────────────────────────────────────────────┘
```

### Naming note

"Brightlines" was the user's working name for this. Per this org's naming rule
(`~/.claude/rules/naming.md`: names must be brand/product/human-first, meaning what they
are) — "Brightlines" passes the four tests reasonably well (brand-inclined, evokes
"pipeline"/"timeline" without engineering jargon, human-readable) but has NOT been checked
against `brighthive-ux-voice`/`brighthive-product-voice` review, which this org's rules
require before a user-facing name ships. Given the corrected scope (D2 enriches existing
panels rather than adding a new named surface), "Brightlines" may not even need to be a
user-facing name at all — flag this explicitly rather than assume a new brand name is needed.

### Explicitly NOT yet scoped (genuinely new, this pass only proposes the shape)

- No tickets filed yet for either D1 or D2 — D1 (defect fixes) could reasonably be ticketed
  now since it's bug-fix-shaped against existing code; D2 (signal enrichment) still needs a
  `/write-spec` pass (what data shows in the run-history row, what the live timeline shows
  during an in-progress run affected by an anomaly) before Jira tickets are cut.
- Whether D1's fixes are prioritized ahead of or independent of D2 — a real
  sequencing/resourcing decision, not decided here.
- The mobile-responsiveness fix (D1, item 2) is itself non-trivial: 4 components each need
  responsive breakpoints designed, not just copy-pasted fixed-width removal.

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
