---
title: "Niche 1 — Snowflake connector / BYOW"
epic: "BH-526"
prs: ["brightbot#488", "brightbot#489", "brighthive-platform-core#777"]
last_reviewed: "2026-06-05"
---

# Niche 1 — Snowflake connector / Bring-Your-Own-Warehouse

> **One-line intent:** make BrightHive able to point at a customer's own
> Snowflake — connect, profile, generate SQL, and ingest its catalog — so the
> Longaeva trial can run against their synthetic Snowflake env.

## Why this niche exists

Longaeva brings their own Snowflake. Before these PRs, BrightBot's warehouse
factory raised `ValueError("Unknown warehouse type: snowflake")` — the hard gate
for the trial. The work mirrors the already-shipped **Azure Synapse**
implementation (brightbot PR #433): same warehouse-agnostic "layer" pattern,
swapped driver and SQL dialect.

The warehouse-agnostic pattern has numbered layers. Snowflake needed Layers 3
(ingestion) and 5 (agent connection); the others were already generic.

## Synthetic Snowflake env (test target)

- **Console:** https://app.snowflake.com/bfddsko/dua97555/
- Auth scope for the trial is **username / password / account** (Phase 1). JWT /
  key-pair auth is explicitly Phase 2 (placeholder `TBC-B` in the spec) — do not
  block integration testing on it.
- The synthetic data + dbt models live under
  [`../sandbox/`](../sandbox/) (Silver tables, marts, seeds).

## PRs in this niche

### `brightbot#488` — SnowflakeConnection (Layer 5, agent side)

- **Tickets:** BH-527/528/549/550/553 (5 of 8 Phase-1 tickets under BH-526)
- **State:** OPEN · `REVIEW_REQUIRED` · ⚠️ **DIRTY — has a merge conflict against `develop`. Must be rebased before it can merge.**
- **Scope (+2247 / −1437, 9 files):**
  - `tools/warehouse_connections.py` — new `SnowflakeConnection` class
  - `utils/warehouse.py` — Snowflake config parsing (`warehouse_config` + env-var fallback)
  - `utils/warehouse_types.py` — **NEW** single source of truth for warehouse-type literals, secret type names, driver module, env vars
  - `prompts/retrieval_agent_prompts.py` — `DIALECT_SYNTAX_RULES['snowflake']` + examples (was a one-line stub): ANSI double-quotes, `LIMIT` not `TOP`, `ILIKE`, `INFORMATION_SCHEMA`
  - `tools/aws/secrets_manager.py` — Snowflake secret requires `username`, `password`, `account`
  - `pyproject.toml` + `uv.lock` — `snowflake-connector-python>=3.12.0` (pulls pyOpenSSL + cryptography)
  - `tests/unit/test_snowflake_warehouse.py` — 29 new tests
- **Security:** ships `assert_read_only_sql` — DELETE/INSERT/UPDATE/DROP and
  multi-statement rejected; SELECT/SHOW/WITH/DESC/DESCRIBE/EXPLAIN allowed
  (CTE-bypass body-keyword check).
- **Tests claimed:** 54 passing (29 new Snowflake + 25 Synapse regression).

### `brightbot#489` — Atlas semantic-view YAML scaffold (BH-531)

- **State:** OPEN · **draft**
- **Scope (+1292 / −0, 5 files):** new tool at
  `brightbot/agents/dbt_agent/tools/atlas_semantic_view/` — pure deterministic
  function (no LLM, no warehouse calls) that turns a Snowflake Silver-table
  schema + plain-language description into Atlas-shaped metric-store YAML
  matching Longaeva's contract (received 2026-06-01).
- Returns a `ScaffoldReport` (`grounded` / `guesses` / `warnings`) so a human
  reviews the YAML before commit. LLM enrichment of `custom_instructions` /
  `verified_queries` is a **separate** follow-up; the tool is **not yet wired
  into the dbt agent's tool registry** (deliberate — team decides routing).
- **Tests claimed:** 35 passing.
- **Trial relevance:** §2 Semantic View Enrollment. Spec at
  [`../artifacts/atlas-semantic-view-spec.md`](../artifacts/atlas-semantic-view-spec.md);
  examples at [`../artifacts/atlas-semantic-view-examples.yaml`](../artifacts/atlas-semantic-view-examples.yaml).

### `brighthive-platform-core#777` — SnowflakeSourceConfig (Layer 3, ingestion lambda) (BH-551)

- **State:** OPEN · `REVIEW_REQUIRED`
- **Scope (+301 / −12, 4 files):** mirrors `SynapseSourceConfig`
  (`@register_source(...)`). Adds Snowflake to the OpenMetadata (OMD) ingestion
  lambda so OMD can pull a Snowflake catalog for a Longaeva workspace.
  - `config_loader.py` — `SnowflakeSourceConfig` + `SOURCE_TYPE_*` constants
  - `main.py` — `SnowflakeConnection` import, `SERVICE_TYPE_MAP` + `SERVICE_NAME_SUFFIX_MAP`
  - `tests/test_config_loader.py` — **NEW**, 14 tests
- **Required fields:** Snowflake `account` and `warehouse` are required in the
  PUT `/openmetadata/team` request (400 if missing).
- **Trial relevance:** semantic enrollment §3 depends on OMD being able to
  ingest the Snowflake catalog.

## Dependency notes

- These three PRs are **independent of each other** for merge purposes — no
  cross-PR base-branch stacking. #488 and #777 are the two that must both land
  for an end-to-end Snowflake run; #489 (Atlas scaffold) is additive.
- **Blocker to clear first:** #488 is DIRTY. Rebase onto current `develop` and
  resolve the conflict (likely `uv.lock` + `warehouse.py`) before merge.
- This niche has **no dependency** on the GHE proxy or MCP work — it can land
  and be staging-tested in parallel.

## Staging verification (what "working" means)

See [`00-STAGING-INTEGRATION-RUNBOOK.md` → Gate A](00-STAGING-INTEGRATION-RUNBOOK.md#gate-a--snowflake-byow)
for exact steps. Acceptance in short:

1. A staging workspace configured with the synthetic Snowflake secret
   (`username`/`password`/`account`/`warehouse`) connects without
   `Unknown warehouse type`.
2. OMD ingestion lambda pulls the Snowflake catalog (tables visible in the
   workspace).
3. BrightBot generates a Snowflake-dialect SELECT (LIMIT, double-quoted
   identifiers) and a write statement is rejected by `assert_read_only_sql`.
4. (If #489 lands) Atlas scaffold produces YAML that validates against the
   Atlas SDK for one Silver table.

## Out of scope for the trial

- JWT / key-pair Snowflake auth (Phase 2, `TBC-B`).
- Wiring the Atlas scaffold tool into the agent routing layer (separate ticket).
- LLM enrichment of semantic-view descriptions / verified queries.

## References

- Epic: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)
- Reference impl: brightbot PR #433 (Synapse) — see memory `project_azure_synapse_byow`
- Spec: `brightbot/docs/specs/snowflake-full-integration.md` (Layer status table)
