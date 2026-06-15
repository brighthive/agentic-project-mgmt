---
title: "BYOW End-to-End on OM 1.8.9 Native Ingestion (catalog → embeddings → retrieval → analysis)"
epic: "BH-526"
author: "drchinca"
status: "Draft"
created: "2026-06-15"
generates: "tickets"
tags: [warehouse, byow, openmetadata, ingestion, embeddings, retrieval, snowflake, redshift, synapse]
related:
  features: []
  pocs: []
  specs: ["warehouse-agnostic-architecture.md", "warehouse-extensibility-pattern.md", "snowflake-full-integration.md", "azure-synapse-full-integration.md"]
---

# BYOW End-to-End on OM 1.8.9 Native Ingestion

## Problem

A connected warehouse must become **fully usable** end-to-end: catalog assets → descriptions → embeddings → schemas → retrievable + analyzable by the agents. Today the chain breaks at step 1 — OneTen's Snowflake catalog is **empty** — and the cause was misattributed.

**The corrected architecture (verified 2026-06-15, confirmed by Ahmed):** the team moved OFF external scanner lambdas. OM **1.8.9 scans natively** (Airflow `openmetadata/ingestion:1.8.9` container; `PIPELINE_SERVICE_CLIENT_ENABLED=true`). Platform-core registers a DatabaseService and triggers OM's native **AutoPilotApplication** via `src/data-source/openmetadata/v2.ts::upsertDatabaseService`. The two external scanners (`openmetadata_ingestion_lambda` SDK 0.12.2, `snowflake_ingestion_lambda`) are **DEPRECATED** (banners + DEPRECATED.md merged, core #842; inventory in saas ARCHITECTURE.md, saas #12).

The empty catalog is two `v2.ts` bugs (fix in draft PR #843): (1) AutoPilot trigger posted a non-interpolated literal URL → scan never fired; (2) `upsertDatabaseService` dropped Snowflake `account/warehouse/role` → service unconnectable.

## Use Case / Goal

For **each of 4+ warehouses (Redshift, Snowflake, Azure Synapse/Mssql, + future BigQuery/Databricks)**, connecting it via `upsertWarehouseServiceConfig` produces, with **zero per-warehouse routing changes**:

1. **Catalog** — OM native AutoPilot scans the warehouse; tables land in OM.
2. **Sync** — OM events → table-sync webhook (`openmetadata_webhook_lambda`) → `DataAssetNode` in Neo4j + DynamoDB mapping.
3. **Enrichment** — enrichment webhook (`new_openmetadata_webhook_lambda`/EnhancedOmWebhookLambda) → **description + embedding (vector) + column descriptions + schema + quality + profile** on each node.
4. **Retrieval** — assets are findable via semantic catalog search (`brightbot graphrag_retrieval`).
5. **Analysis** — the analyst/dbt agents query the warehouse against those catalog assets (warehouse-agnostic connection via `brightbot CONNECTION_CLASSES` + dialect rules).

Success = a connected warehouse is queryable by natural language with grounded, embedding-retrieved schema context — for every supported warehouse, proven on staging.

## Current Situation

### How it works today (the live path)

```
upsertWarehouseServiceConfig (GraphQL, warehouse-service.ts)
  → normalizeWarehouseConfig + per-warehouse omdConnection            [✅ agnostic]
  → v2.ts upsertDatabaseService: register DatabaseService             [🔴 dropped Snowflake fields — PR #843]
  → v2.ts trigger AutoPilotApplication (OM native scan)               [🔴 literal URL, never fired — PR #843]
  → OM 1.8.9 scans warehouse natively (Airflow)                       [✅ once triggered]
  → OM change events → openmetadata_webhook_lambda (table-sync)       [✅ warehouse_adapter registry]
       → DataAssetNode + DynamoDB mapping (#827/#839)
  → new_openmetadata_webhook_lambda (enrichment)                      [✅ agnostic]
       → description (#837) → embedding/embedded_text
       → metadata-agent column descriptions → quality → profiler
  → brightbot graphrag_retrieval (semantic search over embeddings)    [✅ agnostic]
  → analyst/dbt agents query warehouse (CONNECTION_CLASSES + dialect) [✅ agnostic]
```

### What's verified agnostic already (the 7 layers, per warehouse-agnostic-architecture.md)
L1 destination handler, L2 webhook adapter registry, L4 `OMD_SERVICE_TYPE` map, L5 brightbot `CONNECTION_CLASSES` + dialect, L6 webapp registry — all warehouse-agnostic for Redshift/Snowflake/Synapse. The webhook enrichment chain is warehouse-agnostic by construction (operates on OM table entities, not warehouse type).

### The gaps (what this spec closes)
1. **v2.ts catalog trigger + connection** — PR #843 (draft; needs AutoPilot contract + staging UAT).
2. **AutoPilot payload contract unverified** — `{entityLink}` vs no-body vs `triggerConfig`. Spike or Ahmed.
3. **Per-warehouse e2e proof** — no warehouse has been driven catalog→embedding→retrieval→analysis on the native path. Needs staging UAT per warehouse.
4. **Embedding/description coverage on scanned (non-BrightHive-authored) tables** — #837/#839 closed it on the webhook side; must confirm it fires for each warehouse's scanned tables.
5. **Glue on 1.8.9** — does native OM ingest Glue? Determines whether the old lambda is fully retired.

## Proposals / Solutions

**Single path, data-driven by `source_type` / `serviceType`; no per-warehouse branches in routing.** Build order is risk-first: fix the shared control plane once, then prove each warehouse e2e, then retire the dead scanners.

- **Phase A — Fix the shared control plane** (PR #843): AutoPilot trigger interpolation + verbatim connection forwarding (`OmdConnectionConfig`). Verify the OM 1.8.9 AutoPilot payload (staging curl / Ahmed) before un-draft.
- **Phase B — Per-warehouse e2e proof on staging** (one ticket each): Redshift → Snowflake (LONGAEVA_POC, BH-526 acceptance) → Synapse. For each: connect → AutoPilot run created → tables in OM → DataAssetNode → description+embedding+schema → semantic retrieval returns it → analyst agent answers an NL question grounded in it. "Nothing dirty" = no orphan services, no half-synced nodes, embeddings non-null.
- **Phase C — Glue decision**: confirm native 1.8.9 Glue ingestion; cut over or document Glue-stays-on-old-lambda exception.
- **Phase D — Retire dead scanners**: once all live callers are on the native path + soaked, delete `openmetadata_ingestion_lambda` + `snowflake_ingestion_lambda` + their routes (banners/DEPRECATED.md already merged).
- **Phase E — Future warehouse (BigQuery/Databricks)**: prove the "zero routing change" claim by adding one via the checklist only.

## Areas Involved

| Area | Repo | Role |
|---|---|---|
| OMD control plane | platform-core `src/data-source/openmetadata/v2.ts` | register + AutoPilot trigger (PR #843) |
| Warehouse config | platform-core `graphql/models/warehouse-service.ts` | per-warehouse `omdConnection` (already agnostic) |
| Table-sync webhook | platform-core `openmetadata_webhook_lambda/` | OM event → DataAssetNode (keep) |
| Enrichment webhook | platform-core `new_openmetadata_webhook_lambda/` | description/embedding/quality/profile (keep) |
| Retrieval | brightbot `tools/graphrag_retrieval.py` | semantic search over embeddings |
| Analysis | brightbot `tools/warehouse_connections.py` (`CONNECTION_CLASSES`) + dialect prompts | warehouse-agnostic query |
| OMD stack | brighthive-openmetadata-stack | native Airflow ingestion 1.8.9 |
| Deprecated scanners | platform-core `openmetadata_ingestion_lambda/`, `snowflake_ingestion_lambda/` | DELETE in Phase D |

## Acceptance Criteria (per warehouse, all on staging)

```gherkin
Feature: BYOW end-to-end on OM 1.8.9 native ingestion

  Scenario Outline: connect a warehouse and use it end-to-end
    Given a <warehouse> connected via upsertWarehouseServiceConfig on staging
    When the DatabaseService is registered and AutoPilot is triggered
    Then an AutoPilotApplication run is created and completes
    And the warehouse's tables appear in the OM catalog
    And each table has a DataAssetNode in Neo4j with a DynamoDB mapping
    And each DataAssetNode has a non-null description, embedded_text, and embedding vector
    And the table schema (columns) is captured on the node
    When the analyst agent is asked a natural-language question about a table
    Then semantic retrieval returns the relevant asset by embedding
    And the agent answers grounded in the real schema, querying the live <warehouse>
    And no orphan OM services / half-synced nodes / null embeddings remain ("nothing dirty")

    Examples:
      | warehouse |
      | Redshift  |
      | Snowflake |
      | Synapse   |
```

## Dependencies

- **Staging AWS access** (`aws sso login --profile brighthive-staging`) + OM reachability (VPC-internal) — currently BLOCKING all of Phase B/C and un-draft of #843.
- **OM 1.8.9 AutoPilot trigger contract** — staging curl or Ahmed (draft Qs: `clients/trials/longaeva/artifacts/ahmed-omd-autopilot-questions.md`).
- Merged foundation: core #842 (deprecation), saas #12 (inventory). In flight: core #843 (v2.ts fix).

## Ticket Breakdown

| Ticket | Phase | Repo | Gate |
|---|---|---|---|
| v2.ts AutoPilot + connection fix (PR #843) | A | platform-core | unit ✅ + AutoPilot contract + staging UAT |
| Verify AutoPilot payload contract on staging | A | — | spike/Ahmed |
| Redshift e2e proof on staging | B | platform-core + brightbot | full Gherkin |
| Snowflake e2e proof (LONGAEVA_POC, BH-526 acceptance) | B | " | full Gherkin |
| Synapse e2e proof | B | " | full Gherkin |
| Glue native-1.8.9 decision + cutover-or-document | C | platform-core/org-cdk | per finding |
| Retire `openmetadata_ingestion_lambda` + routes | D | platform-core | post-soak, all callers migrated |
| Retire `snowflake_ingestion_lambda` + routes | D | platform-core | post-soak |
| Future-warehouse (BigQuery) via checklist only — prove zero routing change | E | all | checklist + e2e |

## Related
- `warehouse-agnostic-architecture.md` (7-layer pattern, BH-172)
- `warehouse-extensibility-pattern.md` (per-warehouse checklist — extend its L3 row to OM-native, not the old lambda)
- saas `docs/architecture/ARCHITECTURE.md` (OMD LIVE-vs-DEPRECATED inventory)
- saas `docs/architecture/SNOWFLAKE_OMD_INGESTION.md`
