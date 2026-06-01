---
title: "Atlas Semantic View YAML Contract — extracted from Longaeva's sanitized examples"
source: "clients/trials/longaeva/artifacts/atlas-semantic-view-examples.yaml"
source_provided: "2026-06-01 by client"
status: "authoritative — derived directly from client's POC enablement file"
extends: "Snowflake Semantic View YAML spec (https://docs.snowflake.com/en/user-guide/views-semantic/semantic-view-yaml-spec)"
---

# Atlas Semantic View YAML Contract

> Longaeva's **Atlas metric-store SDK** wraps Snowflake's native semantic-view
> spec with metadata that drives their metric store and downstream agent context.
> The `atlas:` keys are **stripped before Snowflake DDL generation** — they only
> influence Atlas / agent context.
>
> Every section below is grounded in real lines from `atlas-semantic-view-examples.yaml`.

---

## Top-level structure

A semantic view is one YAML document with these top-level keys:

```yaml
name: SVW__<UPPERCASE_DOMAIN__SUBJECT>     # required — Snowflake semantic view name
description: >- ...                         # required — multi-line description
custom_instructions: >- ...                 # required for agent quality — see §3
tables: [...]                               # required — one or more tables (§4)
verified_queries: [...]                     # strongly recommended — golden examples (§5)
atlas: {...}                                # Longaeva-specific block (§6)
```

Naming convention (from all 3 examples): `SVW__<DOMAIN>__<SUBJECT>` (e.g. `SVW__EXAMPLE_RETAIL_PANEL__UNIFIED_SPEND`). The semantic view's database/schema location lives on `tables[].base_table` below; the `name:` field is the semantic-view object name only.

---

## 1. Custom Instructions block (`custom_instructions`)

A multi-line natural-language block that is **injected into downstream agent context** (per the YAML header comment: *"critical for downstream AI-agent query quality"*).

Each example follows a consistent shape — section headers in UPPERCASE followed by rules. Patterns observed:

- **GRAIN rules** — when multiple grains coexist in one table, how to filter
- **CHANNEL / PLATFORM / GEOGRAPHY rules** — how to avoid double-counting across rollup dimensions
- **PERIODS** — supported `PERIOD_TYPE` values, weekly-boundary caveats
- **MEASURES / METRICS** — which facts are additive vs pre-computed (must not be summed)
- **STANDARD QUERY** — a recommended `WHERE` predicate template (Example 1)
- **TABLE SELECTION** — when the view has multiple tables, which to use for which question (Example 3)

The scaffolding tool MUST generate this block. Empty / placeholder text degrades agent quality directly.

---

## 2. `tables[]` block

Each table has this exact shape:

```yaml
tables:
  - name: <UPPERCASE_TABLE_NAME>           # logical name in the semantic view
    description: >- ...
    base_table:
      database: <SF_DATABASE>              # e.g. PREP_SANDBOX
      schema:   <SF_SCHEMA>                # e.g. RETAIL_PANEL
      table:    <SF_TABLE>                 # e.g. INT__EXAMPLE_RETAIL_PANEL__UNIFIED_SPEND
    primary_key:
      columns: [<col>, ...]                # explicit grain — REQUIRED
    dimensions:    [...]                   # see §2.1
    time_dimensions: [...]                 # see §2.2
    facts: [...]                           # see §2.3
    metrics: [...]                         # optional — pre-aggregated COUNT(DISTINCT ...) etc.
    filters: [...]                         # named reusable WHERE predicates — see §2.4
```

Multi-table semantic views are supported and used in practice (Example 3 has 3 tables: ACTIVITY_RAW, SALES_RAW, SWITCHING_RAW). When multiple tables exist, the `custom_instructions` block MUST contain a TABLE SELECTION section explaining when to use which.

### 2.1 Dimensions

```yaml
dimensions:
  - name: <UPPERCASE_DIM>                  # logical name
    description: <...>                     # one-line; LLM context
    expr: <COLUMN_EXPR>                    # raw column or SQL expr
    data_type: VARCHAR | DATE | FLOAT | NUMBER | TIMESTAMP_LTZ | ...
    sample_values: [...]                   # optional but critical for agent quality
    atlas:                                 # optional — Longaeva-specific binding
      target: <atlas_target_key>           # see §6 atlas target naming
```

`sample_values` is a list of strings showing the LLM what values to expect. Without it, agent query quality drops sharply.

### 2.2 Time dimensions

```yaml
time_dimensions:
  - name: PERIOD_START_DATE                # always uppercase
    description: ...
    expr: PERIOD_START_DATE
    data_type: DATE | TIMESTAMP_LTZ
    atlas:
      target: period_start_date            # standard atlas target
```

Standard time dimensions across all examples: `PERIOD_START_DATE`, `PERIOD_END_DATE`. Example 2 adds `DATA_KNOWLEDGE_TS` (the freshness signal).

### 2.3 Facts (and the fact→metric promotion)

```yaml
facts:
  - name: SPEND_AMT
    description: ...
    expr: SPEND_AMT
    data_type: FLOAT
    atlas:
      metric:
        aggregations:
          # Two equivalent forms — both observed in the examples
          # (a) shorthand list of aggregation function names:
          - sum
          # (b) full object with explicit metric name:
          - fn: sum
            name: total_spend
```

`atlas.metric.aggregations` **promotes the fact into a named Snowflake semantic-view metric** during DDL generation. Multiple aggregations per fact are supported (Example 2's `REVENUE_USD` has `[sum, avg]`).

If `aggregations` is omitted, the fact stays as a raw fact — not promoted to a metric.

### 2.4 Filters (named reusable WHERE predicates)

```yaml
filters:
  - name: MONTHLY
    description: Monthly period type.
    expr: PERIOD_TYPE = 'Month'
  - name: STANDARD_COMPANY_TOTALS
    description: Standard filter for issuer-level global totals.
    expr: PLATFORM = 'unified' AND GEOGRAPHY = 'WW' AND GEOGRAPHY_TYPE = 'REGION' AND APP_NAME = 'All Apps'
```

These become Snowflake semantic-view filters. They're the canonical filter presets Longaeva mentioned in the POC scope.

---

## 3. `verified_queries[]` block (golden examples)

```yaml
verified_queries:
  - name: category_monthly_yoy_by_source
    question: Pull monthly total-channel YoY spend for Grocery across all providers, last 12 months.
    sql: >-
      SELECT ...
      FROM SEMANTIC_VIEW(
        <database>.<schema>.<semantic_view_name>
        DIMENSIONS <table>.<dim>, ...
        FACTS <table>.<fact>, ...
        WHERE <table>.<dim> = '<value>'
          AND ...
      )
      ORDER BY ...
```

Two semantic notes about the SQL:

1. They use Snowflake's native `SEMANTIC_VIEW(…)` table-function syntax — three sections: `DIMENSIONS`, `FACTS`, optional `METRICS`.
2. Every column reference is **table-qualified** (`UNIFIED_SPEND.PERIOD_START_DATE`) so multi-table views work consistently.

The scaffolding tool should generate at least one `verified_query` per major use-case implied by `custom_instructions`. These are gold for both agent context and human enrollment confidence.

---

## 4. `atlas:` top-level block (Longaeva-specific)

```yaml
atlas:
  dataset_key: <namespace>.<dataset_slug>   # e.g. example.retail_panel_unified_spend
  display_name: "<Pretty | Display Name>"
  owners:
    - "team:<team-slug>"                    # always team:* form
  entities:
    primary: <atlas_target_key>             # which dimension's atlas.target is the primary entity
  defaults:
    metric_type:  Feature                   # observed values: Feature
    growth_type:  Level                     # observed values: Level
    period_type:  Month | Week              # default time grain
  dagster_dep: ["dbt", "<dbt_model_name>"]  # orchestration dependency — couples to Dagster
  warehouse_size: S | M | L | XL            # optional — Example 2 sets L
```

`dagster_dep` is a tuple `[orchestrator, dep_name]`. In all examples the orchestrator is `"dbt"` and the dep is the upstream dbt model. **Confirms Dagster is in scope** for the trial — BrightHive's lineage agent needs to understand the dbt→Dagster→semantic-view chain.

`owners` uses an `<entity-type>:<slug>` form (`team:example-data`). Treat as a free-form string — don't enforce the prefix list in validation.

---

## 5. Atlas `target` namespace (field-level bindings)

Standard atlas targets observed across the examples:

| Target | Used on dimension type | Notes |
|---|---|---|
| `entity_name` | The primary entity column (category name, product name, etc.) | Required for the row's primary entity. The top-level `atlas.entities.primary` points to this. |
| `bloomberg_ticker` | Bloomberg ticker dimension | **Reference-data identifier — Longaeva trial join requirement** |
| `lngv_issuer_id` | Their internal issuer ID | **The LEI/FIGI → internal issuer ID mapping target — exactly what the trial scope §2.2 asked about** |
| `period_type` | PERIOD_TYPE dimension | "Day" / "Week" / "Month" / "Fiscal Quarter" |
| `period_start_date` | First day of period | Standard time-dim binding |
| `period_end_date` | Last day of period | Standard time-dim binding |
| `data_knowledge_ts` | Freshness timestamp | Example 2 only |
| `metric_attributes.dataset_attributes.app_id` | App identifier | Nested namespace under metric_attributes |
| `metric_attributes.dataset_attributes.app_name` | App name | |
| `metric_attributes.dataset_attributes.platform` | App platform (ios / android / unified) | |
| `metric_attributes.geography.region` | Region/country code | Two-level: `metric_attributes.<group>.<key>` |

The atlas target namespace is dotted — supports nesting (`metric_attributes.dataset_attributes.app_id`). The scaffolding tool needs to recognize this convention when inferring target bindings.

---

## 6. What this means for BrightHive engineering

### BH-531 (semantic view scaffold tool) — exact contract

The brightbot scaffolding tool for Snowflake semantic views MUST:

1. **Accept**: a Silver table schema (from INFORMATION_SCHEMA) + plain-language description
2. **Emit**: a YAML document matching §1-§6 above, with:
   - `tables[].base_table.{database,schema,table}` from the Silver table reference
   - `primary_key.columns` inferred from PK constraints OR from a "primary_key:" hint in the description
   - `dimensions` / `time_dimensions` / `facts` separated by data_type and column name (heuristic: `*_DATE`/`*_TS` → time_dim; numeric → fact; varchar → dimension)
   - `sample_values` populated by `SELECT DISTINCT col LIMIT 10` on the Silver table (or a configurable cap)
   - `atlas.target` inferred from the column name via a known-mapping table (LEI/FIGI → `lngv_issuer_id`, bloomberg → `bloomberg_ticker`, geography columns → `metric_attributes.geography.*`)
   - `atlas.metric.aggregations` defaulted from fact name (counts → sum, prices → avg, percentages → null)
   - `custom_instructions` — first pass scaffolded from the description; flagged for human review
   - At least one `verified_query` — generated from the plain-language description

3. **Output**: a YAML string PLUS a structured "scaffold report" listing every field the LLM had to guess vs every field grounded in catalog data (so a human can review the inferred bits).

### Reference-data join requirement (clarified)

The trial scope says BrightHive should auto-detect joins to **fiscal calendar**, **LEI/FIGI → internal issuer ID**, **geographic/classification codes**. The Atlas YAML gives the concrete artifacts:

- LEI/FIGI mapping is realised as a `BLOOMBERG_TICKER` ↔ `LNGV_ISSUER_ID` pair on the same row (Example 2). The "join" they want is actually **column population from a reference table** that's already done upstream in dbt — the semantic view inherits both columns.
- Fiscal calendar joins are NOT in any of the 3 examples (might be a different dataset pattern); revisit when they share a fiscal calendar example.
- Geographic codes are realised as `GEOGRAPHY` + `GEOGRAPHY_TYPE` dimensions with atlas targets under `metric_attributes.geography.*`.

So the "reference-data join detection" requirement is actually: **detect when an upstream Silver column matches a known reference identifier and bind its atlas.target correctly**. That's a simpler, more tractable problem than runtime joins.

### Dagster integration scope (clarified)

`atlas.dagster_dep` is the only Dagster coupling in the YAML. It's a hint that the semantic view's upstream is a Dagster-orchestrated dbt asset. BrightHive doesn't need to drive Dagster execution to support this — it just needs to write the correct dep tuple. **Reduces BH-554 / Dagster scope materially.**

---

## 7. Open questions to confirm with Grant

1. Is the **stripping rule** for `atlas.*` keys done by the Atlas SDK before Snowflake DDL generation, or do we strip in our scaffolding tool? (We should not emit Snowflake DDL ourselves; we emit the YAML and Atlas handles DDL.)
2. Are `metric_type` / `growth_type` enumerations bounded? Only `Feature` and `Level` appear in the examples — confirm full vocabulary.
3. Is the `dataset_key` namespace structure flat (`<namespace>.<slug>`) or hierarchical (>2 dots)? All 3 examples use 2 levels.
4. Are `verified_queries` machine-validated (compiled against Snowflake) at enrollment time, or human-curated only?
5. What's the canonical name for the entity-type prefix in `owners`? Only `team:*` appears in examples.
