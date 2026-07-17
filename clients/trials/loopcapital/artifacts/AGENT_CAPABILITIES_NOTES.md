# BrightAgent — Agent Capabilities Notes (raw dump for docs #1)

> **What this is**: an unpolished brain-dump of every agent capability + output I
> personally verified **live on Loop Capital's real staging workspace**
> (`e3fc0917-03a6-4ac6-aad4-ac265329bfb9`) during the overnight demo-prep session,
> 2026-07-17. For Ignacio + Marwan to mine when building the formal Full Agentic
> Documentation, and for matt on the Engineering/Data-Engineering agent detail.
>
> **Ground rule**: everything below was confirmed by a real GraphQL / LangGraph /
> warehouse call this session, not from reading code or memory. Where something is
> scoped-but-not-built, it says so explicitly. Don't promote a "NOT BUILT" line into
> the customer doc as shipped.
>
> **Not a spec, not customer copy** — it's source material. Rewrite into the real
> doc; don't paste verbatim.

---

## The workspace this was verified against

- **Loop Capital**, real staging workspace `e3fc0917-03a6-4ac6-aad4-ac265329bfb9`.
- **BYOW (Bring Your Own Warehouse)**: real Microsoft SQL Server on an EC2 box
  (`54.197.188.168:1433`, database `LoopCapitalAM`, self-signed cert by design).
  This is the Azure-relevant point for doc #2 — SQL Server is the source, reached
  over TDS, not Snowflake/Redshift.
- **11 real data assets**, medallion-tiered: 5 BRONZE (`holdings_raw`,
  `raw_counterparties`, `raw_market_prices`, `raw_positions`, `raw_security_master`),
  3 SILVER (`stg_holdings`, `stg_daily_pnl`, `stg_positions`), 3 GOLD
  (`mart_compliance_breaches`, `mart_daily_portfolio_exposure`,
  `mart_portfolio_risk_summary`).

---

## Per-agent capabilities (verified live)

### 1. Data Profiler Agent (`data_profiler_agent`)

- **Purpose**: builds a full statistical profile of a data asset — row count, column
  count, per-column null/distinct/min/max, duplicate-row detection, overall missing %.
- **Trigger**: `POST {LangGraph}/manage/agents/run` with
  `{graph_id: "data_profiler_agent", workspace_id, data_asset_id}`; async, returns a
  `run_id`. Also runs scheduled (batch variant `profiler_task`).
- **Output**: a `profiling` capability execution recorded on the asset (visible as the
  Profiler sub-agent tab), plus a JSON artifact in S3 (`profileSummary`,
  `dataAssetProfileV2`). Surfaces `rowCount`, `columnCount`,
  `overallMissingPercentage`, `duplicateRowCount`, warehouse-true distinct counts.
- **Verified**: 11/11 assets have a real `profiling` capability. Note the honest
  behavior — profiler **refuses to fabricate a profile on a 0-row table** (returns
  "No data found" rather than fake stats); this correctly gated 4 initially-empty
  tables until they had real rows.

### 2. Quality Check Agent (`quality_check_agent`)

- **Purpose**: samples the asset (50-row LLM context pull + warehouse metrics),
  generates Great Expectations-style quality expectations, validates them.
- **Trigger**: same `/manage/agents/run` endpoint, `graph_id: "quality_check_agent"`.
- **Output**: a `quality_check` capability execution on the asset (Quality Check
  sub-agent tab). Tolerates 0-row tables (passes with warnings) — distinct from the
  profiler's stricter behavior.
- **Verified**: 11/11 assets.

### 3. Data Asset Preview (`dataAssetPreview` query)

- **Purpose**: live first-10 + random-100 row preview pulled directly from the BYOW
  warehouse at view time — not a cached snapshot.
- **Output**: `{columns, firstRows, randomRows, generatedAt}`.
- **Verified**: real columns + rows returned for `holdings_raw`
  (`holding_id, portfolio_id, instrument_id, quantity, as_of_date, loaded_at`).
- **Engineering note for matt**: preview over a self-signed-cert SQL Server needed a
  `trustServerCertificate` opt-in on the warehouse secret (the `mssql`/Tedious driver
  defaults it to `false`; real customer connections stay strict). Fixed + deployed
  this session (`brighthive-platform-core#1089`/`#1091`).

### 4. Semantic View (Snowflake Cortex Semantic View YAML)

- **Purpose**: attaches a semantic layer (tables → dimensions / time_dimensions /
  facts / metrics / verified_queries) to an asset so the analyst agent can answer
  business questions with grounded column bindings.
- **Trigger**: `upsertSemanticView(input: {workspaceId, assetId, yaml, comment})`.
- **Output**: `hasSemanticView: true` on the asset (Semantic View sub-agent tab),
  an immutable version snapshot, and `SEMANTIC_REFERENCES` lineage edges from the
  base tables named in the YAML.
- **Verified**: 11/11 assets now carry a real semantic view YAML matching each
  table's actual columns.
- **Two bugs found + fixed this session** (matt / Marwan may want these in the
  engineering doc): (a) `hasSemanticView` had **no resolver** — always returned null
  (`#1094`); (b) `upsertSemanticView` never invalidated the catalog Redis cache, so
  the flag stayed stale on the catalog list (`#1095`). Both merged + deployed.

### 5. Longitudinal Drift Monitoring (value drift) — `get_anomalies` / `run_longitudinal_analysis`

- **Purpose**: detects a metric drifting outside its historical trailing-window
  baseline. Four families: `row_count_drift`, `cardinality_breakdown`,
  `distributional_skew`, `null_spike`.
- **Mechanism**: writes a `MetricSnapshotNode` per metric per run; compares the
  current run against the trailing window (default 7); writes an `AnomalyEventNode`
  when deviation exceeds tolerance (escalates to CRITICAL past 2× tolerance).
- **Output**: stored anomaly events readable via `get_anomalies` — metric name,
  family, severity, current vs baseline value, deviation %, human description.
- **Verified END-TO-END this session** (this is the "historical null → drift →
  proactive alert" demo moment): built 7 real clean baseline snapshots for
  `raw_counterparties.credit_rating` (0% null), then injected one run at 60% null →
  detected CRITICAL (60% dev vs 15% tol), persisted, read back — all live against
  real staging Neo4j.
- **Precondition to be honest about**: needs accumulated snapshot history; a fresh
  asset with no history returns a clean empty result (works, nothing to flag yet).

### 6. Proactive Pipeline Watchdog + Remediation (GC-14 → GC-17)

- **Purpose**: the headline "proactive" loop — detects a broken pipeline **before
  anyone asks**, diagnoses root cause, drafts a real fix as a GitHub PR, and holds a
  human-merge gate (never auto-merges).
- **GC-14**: watchdog detects a broken nightly dbt job → alert to Slack.
- **GC-15**: same proactive detection for a **SQL Server source with no MCP
  connector** (BYOW disk-pressure + job pass/fail). Proven on the real EC2 box.
- **GC-16**: real root-cause diagnosis → real dbt fix drafted → **real GitHub PR
  opened**.
- **GC-17**: safety gate — the agent's PR is left `open`, `mergedAt: null`; a human
  merges. Verified held live.

### 7. Legacy Analyst Analyzer — SSIS / SSRS / Storage Optimization

- **Purpose**: diagnoses legacy Microsoft BI artifacts — SSIS packages (`.dtsx`
  XML), SSRS reports (`.rdl` XML) — and drafts remediation, mirroring GC-16's
  dbt PR path.
- **Status**: diagnosis + PR-draft path is real (`ssis_remediation_agent.py`,
  deterministic `.dtsx`/`.rdl` parsers). **Azure-relevant** for Loop Capital's legacy
  estate.
- **Honest gap**: it consumes XML already in hand — there is **no PDF-with-embedded-
  XML ingestion** and no "drop a file in chat → diagnose" UI wired yet. Scoped, not
  built.

### 8. BrightRoutines (scheduled "nightshift" workflows)

- **Purpose**: platform proactively **suggests** recurring routines from observed
  workspace usage; user schedules them.
- **Key fact**: routines are **auto-suggested, not user-authored from a blank page** —
  there is no "create routine" mutation. `scheduleRoutineSuggestion` acts on a
  system-generated `RoutineSuggestion`.
- **Verified live this session**: after the session's real activity accumulated, Loop
  Capital's own workspace generated 4 routines total, and the split shifts as the
  platform advances them. As of last re-check (2026-07-17): **1 `OFFERED`** ("Daily
  stale-data check on holdings_raw") + **3 `SCHEDULED`** ("Monthly counterparty
  exposure digest", "Nightly compliance breach sweep", "Weekly earnings report").
  ("Monthly counterparty exposure digest" moved OFFERED → SCHEDULED between checks —
  the state is live and advances on its own.) Earlier in the session there were zero;
  they emerged from observation, exactly as designed. **Don't hard-code the per-status
  count in the customer doc — it's a live, moving number; describe the behavior, not
  the snapshot.**

### 9. Analyst / Conversational Agent (`deep_agent` supervisor + subagents)

- **Purpose**: natural-language Q&A over the workspace, routing to analyst /
  governance / retrieval / dbt / schema subagents.
- **Proactive "Next Steps" offers**: the supervisor's closing rule forces up to 3
  concrete follow-up offers on every final reply — **visualization is an explicitly
  listed example** (`generate_vega_lite_chart_tool` exists and is offerable).
- **Honest gaps** (scoped, not proactive today): "who owns/stewards this data" is
  answerable if asked (DataAsset.managers/owner exposed) but **never proactively
  offered**; "run an experiment on this table" as a user-facing capability **does not
  exist** (nearest is `scan_warehouse_tables_tool`, framed as health monitoring).

---

## Schema-drift → PR (asked by Suzanne's channel, important to get right in the doc)

- There are **two unconnected** "schema drift" concepts:
  1. A dbt-**error-text** classifier (`root_cause_classifier.py`) that recognizes
     phrases like "column does not exist" in a failed dbt run — this IS wired to
     GC-16's PR path.
  2. The longitudinal `AnomalyFamily` enum — has **no `SCHEMA_DRIFT` member**, and its
     value-drift families do **not** route to any PR remediation.
- **Bottom line for the doc**: a genuine "platform detected a column's type changed on
  a live source table → opened a PR" moment is **NOT demoable today** — it only exists
  for dbt build-failure error text. Do not claim the live-schema-change→PR flow as
  shipped.

---

## For doc #2 (matt + Suzanne — Azure implementation requirements) — seed facts

Not my deliverable, but these are the concrete environment facts I touched this
session that #2 will need:

- **Source**: Loop Capital runs **Microsoft SQL Server** (BYOW), reached over TDS
  (port 1433). The platform's warehouse layer treats SQL Server and Azure Synapse as
  one "Mssql-family" provider (`WarehouseServiceProvider`: `SQL_SERVER` vs
  `AZURE_SYNAPSE`, BH-1107) — matters for an Azure Synapse deployment target.
- **Self-signed TLS**: BYOW connections to a server presenting a self-signed cert need
  an explicit `trustServerCertificate` opt-in on the warehouse secret (per-connection,
  default off). Real Azure/customer connections with proper certs stay strict.
- **Secrets**: per-workspace `workspace_secret_store/{workspaceId}` in AWS Secrets
  Manager holds warehouse creds + service tokens (OpenMetadata, etc.). An Azure
  deployment needs the equivalent secret-store mapping.
- **Data plane**: OpenMetadata → Neo4j (OGM GraphQL) is the catalog/metadata backbone;
  `syncDataAssets` bridges OMD → Neo4j.
- **Agent runtime**: agents run on LangGraph Cloud (currently
  `brightagent-staging-*.us.langgraph.app`); Bedrock/AgentCore migration is in
  progress (separate strategy docs in `platform-saas-ai-context`).

---

## Bugs fixed live this session (for the engineering-agent doc / changelog)

| Area | Fix | PR / release |
|---|---|---|
| SQL Server not matching as a warehouse provider (catalog empty) | shared Mssql-family provider mapping | `#1082` |
| Catalog cache never invalidated on `syncDataAssets` | always invalidate | `#1087` |
| BYOW preview TLS rejection on self-signed cert | `trustServerCertificate` opt-in | `#1089` |
| `hasSemanticView` always null | added missing resolver | `#1094` |
| Catalog cache never invalidated on `upsertSemanticView` | invalidate on write | `#1095` |
| 4 empty source tables blocking profiling | seeded real referentially-consistent rows | (data seed, no PR) |

All merged + deployed to staging (`v2.9.0.87` → `v2.9.0.92-pre-release`) and
re-verified live.
