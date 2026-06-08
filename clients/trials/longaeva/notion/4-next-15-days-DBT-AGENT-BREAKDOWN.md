---
title: "🛠️ Snowflake + dbt Engineering Agent — atomic breakdown"
intended_target: "Notion page '🗓️ 4 · Next 15 Days' (37202437dde48100889fd7467c0313e0)"
status: "DRAFT — pending Notion auth refresh; paste-ready"
last_reviewed: "2026-06-05"
---

> **Why this file exists.** This block is queued to be appended to the Notion
> "4 · Next 15 Days" page. The notion-brighthive token expired mid-write and
> token refresh hasn't restored the auth yet. Once you reconnect via /mcp or
> the notion-drchinca OAuth flow completes, I'll push this exact content via
> `insert_content` at end position. In the meantime, source-of-truth lives
> here in the repo.

---

## 🛠️ Snowflake + dbt Engineering Agent — atomic breakdown (added 2026-06-05)

> The "SnowflakeConnection" + "Atlas YAML scaffolder" rows on the source page each hide ~7 atomic pieces. This section breaks them out so the team can track real progress, not pre-trial averages. **Every row below is a Jira ticket under Epic [BH-601](https://brighthiveio.atlassian.net/browse/BH-601) (Golden Success Paths) unless noted.**

### A. Snowflake foundation — the 7 warehouse-agnostic layers (4 PRs)

*"BrightAgent reads Snowflake" turns on when these 4 merge + a Snowflake secret lands in `workspace_secret_store/{ws-uuid}` with `type=SNOWFLAKE`. 168 unit tests green. **Path: rebase bb#488 (DIRTY) → review-approve all 4 → squash → deploy → drop secret.***

| Status | Layer | Task | Ticket | PR |
|---|---|---|---|---|
| 🟡 | 5 — BrightBot Connection + dialect + tests + security guard | SnowflakeConnection (BH-527/528/549/550/553) | [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) | bb#488 (⚠️ DIRTY — needs rebase) |
| 🟡 | 3 — OMD Ingestion Source Config | SnowflakeSourceConfig in OMD lambda | [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) | pc#777 |
| 🟡 | 7 — Org-CDK Ingestion Pipeline | `workspace_secret_store` migration | [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) | data-organization-cdk#156 |
| 🟡 | dbt-agent tool | Atlas semantic-view YAML scaffold (deterministic) | [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) | bb#489 (draft) |

### B. dbt Engineering Agent — Layer-B authoring capability (the trial centerpiece)

*This is the actual dbt-agent work that makes GC-1..GC-10 demoable. Today: **0 PRs**. Implementation specs paste-ready at `agentic-project-mgmt/clients/trials/longaeva/integration/impl-specs/` for BH-590, BH-591, BH-593.*

| Status | Capability | Golden Case | Ticket |
|---|---|---|---|
| ⬜ | Snowflake `INFORMATION_SCHEMA` introspection mapped to BH metadata model + Neo4j writer | GC-3, GC-6, GC-7 prerequisite | [BH-590](https://brighthiveio.atlassian.net/browse/BH-590) — 2-3d, Marwan, blocked by BH-527 |
| ⬜ | Wire `scaffold_atlas_semantic_view_tool` into dbt_agent ReAct list + system-prompt LLM-enrichment guidance | **GC-6 ⭐** semantic enrollment, GC-7 reference-join detection | [BH-591](https://brighthiveio.atlassian.net/browse/BH-591) — 1.5d, Marwan/Kuri, blocked by BH-531 + BH-590 |
| ⬜ | Generate dbt `sources.yml` + staging model from a NEW Silver table | GC-1, GC-3, GC-4, GC-5 | [BH-592](https://brighthiveio.atlassian.net/browse/BH-592) — 3-4d, Marwan, blocked by BH-590 |
| ⬜ | Generate dbt `schema.yml` tests (`not_null` / `unique` / `accepted_values` / `relationships`) inferred from schema | GC-3 DQ contracts | [BH-594](https://brighthiveio.atlassian.net/browse/BH-594) — 3-4d, Marwan, blocked by BH-590 |
| ⬜ | Generate partitioned REST API ingestion asset (Dagster) + dbt source from spec | GC-2 | [BH-595](https://brighthiveio.atlassian.net/browse/BH-595) — 5-7d, Marwan + AI/ML, blocked by BH-590 |
| ⬜ | Atlas binding **grounding validator** + **`verified_query` Snowflake compile harness** | **GC-8 ⭐** validation | [BH-596](https://brighthiveio.atlassian.net/browse/BH-596) — 4-6d, Marwan + AI/ML, blocked by BH-591 |
| ⬜ | GHE `base_url` thread-through (so PRs land in Longaeva's GHE, not github.com) | GC-10 PR routing | [BH-593](https://brighthiveio.atlassian.net/browse/BH-593) — 2-3d, Ahmed, blocked by BH-529 chain |
| ⬜ | **End-to-end agent eval harness** for the 6-step trial DAG | **GC-10 ⭐ win-condition gate** | [BH-597](https://brighthiveio.atlassian.net/browse/BH-597) — 5-7d, Marwan + AI/ML + QA, blocked by BH-591 + BH-596 |

### C. Atomic Atlas YAML scaffold flow (per spec — `atlas-semantic-view-spec.md`)

*The 7 atomic enrichment steps the agent must perform end-to-end for GC-6. Deterministic tool (BH-531/bb#489) covers steps 1-2; LLM enrichment (BH-591) covers 3-5; validation (BH-596) covers 6; PR (BH-593 + BH-529 chain) covers 7.*

| Step | Atomic capability | What populates it |
|---|---|---|
| 1 | Introspect Silver table (columns, types, PK, sample_values from `SELECT DISTINCT`) | BH-590 |
| 2 | Deterministic YAML skeleton: `name`, `tables[].base_table`, `dimensions/time_dimensions/facts` split, `atlas.target` defaults from registry, `atlas.metric.aggregations` heuristics, `atlas.dataset_key`, `atlas.entities.primary`, `atlas.defaults`, `atlas.dagster_dep`, `atlas.owners` | BH-531 (built, in bb#489) |
| 3 | LLM enrichment of `custom_instructions` with UPPERCASE sections: GRAIN / CHANNEL / GEOGRAPHY / PERIODS / MEASURES / TABLE SELECTION | BH-591 |
| 4 | LLM enrichment of `verified_queries[]` in Snowflake `SEMANTIC_VIEW(...)` syntax with `DIMENSIONS / FACTS / METRICS` blocks, table-qualified column refs | BH-591 |
| 5 | Reference-data binding inference: LEI/FIGI → `lngv_issuer_id`, `BLOOMBERG_TICKER` → `bloomberg_ticker`, geo cols → `metric_attributes.geography.*`, fiscal calendar | BH-591 |
| 6 | **Grounding validation**: every `atlas.target` ∈ vocabulary; every `expr` references a real column; every `sample_value` ∈ `SELECT DISTINCT`; every `verified_query` compiles (`EXPLAIN`) + executes (`LIMIT 1`) | BH-596 |
| 7 | Commit YAML to `models/semantic/<svw_name>.yml`, open PR via GHE proxy with template + CODEOWNERS-aware body | BH-529 chain + BH-593 + BH-566 |

### D. Maintenance + governance (POC §4)

*GC-11 + GC-12 had ZERO Jira tickets until 2026-06-05 — discovered during goal-to-ticket reconciliation. Both gating per Notion's scoreboard.*

| Status | Capability | Golden Case | Ticket |
|---|---|---|---|
| ⬜ | Self-healing detect→diagnose→surgical-PR loop for 4 failure modes (schema drift / missing partition / broken stage / dbt contract fail) | GC-11 | [BH-599](https://brighthiveio.atlassian.net/browse/BH-599) — ~1 sprint, Marwan + AI/ML |
| ⬜ | Longitudinal anomaly monitoring (4 families: row-count drift, cardinality breakdown, distributional skew, null spike) with stateful trailing-window detection | GC-12 | [BH-600](https://brighthiveio.atlassian.net/browse/BH-600) — ~1 sprint, Marwan + Harbour |

### E. Cleanup / migration (discovered while writing impl specs)

| Status | Task | Ticket |
|---|---|---|
| ⬜ | Migrate `super_agent` + `dbt_tools` off legacy `dbt_agent.py` (2 imports), then delete the file. Currently still imported at `super_agent/nodes/agents/dbt.py:15` and `dbt_tools.py:22`. | [BH-598](https://brighthiveio.atlassian.net/browse/BH-598) — 2-3d after bb#496 |

---

## 🗓️ Trial Day 6-12 — atomic breakdown (was BH-535 + BH-536; now mapped to Golden Cases)

### Day 6-8 — Ingestion (was 1 row "BH-535")

| Day | Atomic milestone | GC | Ticket gating it |
|---|---|---|---|
| 6 | S3 vendor bucket → external stage + dbt source merge-ready ≤1 revision | GC-1 | BH-527 + BH-592 |
| 6-7 | REST API → 25k-instrument run with pagination + 500-ID batching + retry, dbt source wired | GC-2 | BH-595 |
| 7-8 | Snowflake Data Share → introspection + staging + DQ contracts pass first run | GC-3 | BH-590 + BH-592 + BH-594 |
| 8 | All 3 source patterns merge-ready, demoed jointly | BH-535 (rolls up GC-1+2+3) | — |

### Day 8-10 — Semantic enrollment + MCP (was 1 row "BH-536")

| Day | Atomic milestone | GC | Ticket gating it |
|---|---|---|---|
| 8 | Silver table → Atlas YAML scaffolded (deterministic tool invoked from agent) | GC-6 step 1-2 | BH-590 + BH-591 |
| 8-9 | LLM enrichment: `custom_instructions` + ≥1 `verified_query` with table-qualified `SEMANTIC_VIEW(...)` SQL | GC-6 step 3-4 | BH-591 |
| 9 | Reference-data bindings auto-detected: LEI/FIGI → `lngv_issuer_id`, geo, fiscal | GC-7 | BH-591 step 5 |
| 9 | YAML grounded (vocab + columns + sample_values) + `verified_queries` compile against Snowflake | GC-8 | BH-596 |
| 9-10 | All measures/dims queryable through Longaeva's MCP; representative query suite ≤5% error | GC-9 | BH-532 (needs Grant's MCP creds) |
| 10 | **End-to-end**: Silver table → enrolled → validated → PR raised to GHE without leaving guided workflow | **GC-10 ⭐** | BH-597 + the full chain above |
| 10 | Semantic enrollment + MCP validation demoed jointly | BH-536 (rolls up GC-6..10) | — |

### Day 10-12 — Automated maintenance (was 1 row, no ticket)

| Day | Atomic milestone | GC | Ticket gating it |
|---|---|---|---|
| 10-11 | Schema drift detected + surgical fix PR with plain-language diagnosis | GC-11 mode 1 | BH-599 |
| 11 | Missing partition detected + backfill PR | GC-11 mode 2 | BH-599 |
| 11 | Broken external stage diagnosed + DDL update PR | GC-11 mode 3 | BH-599 |
| 11-12 | dbt contract failure analyzed + targeted PR (model OR contract, not both) | GC-11 mode 4 | BH-599 |
| 12 | ≥1 anomaly surfaced from 4 families (row-count / cardinality / skew / nulls) over trailing window | GC-12 | BH-600 |

---

## 🚨 Honest delta vs. the original page

The original "Pre-trial progress" table had **1 row** for SnowflakeConnection and **1 row** for the Atlas scaffolder. Reality is 4 PRs + 8 atomic dbt-agent capabilities + 2 maintenance tickets — **14 distinct units of work** under the headline "Snowflake + dbt agent" surface. Most have **no PR today** and need to land before the Day 6-12 trial windows.

**The single biggest risk: GC-10 (the ⭐ win condition) has no end-to-end code path today.** BH-597 (E2E eval harness) is the gate; without it the demo is a coin flip. Recommend Marwan + AI/ML scope it this sprint.

> Source: traceability matrix at the bottom of [🏆 7 · Golden Success Paths](https://app.notion.com/p/brighthive/7-Golden-Success-Paths-37202437dde481c9a1a6cf8191195059) + impl specs at `agentic-project-mgmt/clients/trials/longaeva/integration/impl-specs/`.
