---
title: "Niche 1 — Snowflake connector / BYOW"
epic: "BH-526"
prs: ["brightbot#488", "brightbot#489", "brighthive-platform-core#777", "brighthive-data-organization-cdk#156"]
last_reviewed: "2026-06-05"
---

## Capability reality — can BrightAgent read & write to Snowflake? (2026-06-05)

**Read: yes, once 4 PRs merge** (`bb#488`, `pc#777`, `data-organization-cdk#156`, `bb#489`) **and a Snowflake secret is dropped into `workspace_secret_store/{workspace-uuid}` with `type=SNOWFLAKE`.** Code built, 168 unit tests green, sandbox adapter proves connection works against live Snowflake (`LONGAEVA_POC`). Path to staging: rebase `bb#488` (DIRTY) → review-approve all 4 → squash-merge → deploy → drop secret.

**Write: no, by design.** `bb#488` ships `assert_read_only_sql` rejecting DELETE / UPDATE / INSERT / DROP / multi-statement (CTE-bypass guard included). Allowed: SELECT / SHOW / WITH / DESC / EXPLAIN. **This is the trial's security boundary** — the agent reads Snowflake, never mutates it. Mutations to the warehouse happen via dbt models the agent commits to GitHub (separate path through the GHE proxy — see Niche 2 + 3).

## Engineering agent end-to-end pipeline-transformation PR flow

**Status: split. Not end-to-end yet.**

| Capability | Status | Why | Ticket |
|---|---|---|---|
| Update an existing dbt source | ✅ Works today | `tools/source_tools.py` already in dbt ReAct agent | — |
| Generate Snowflake-dialect SELECT | ✅ Once `bb#488` merges | Dialect rules + ANSI quotes + LIMIT/ILIKE in `bb#488` | BH-528 (in `bb#488`) |
| Read Silver schema via `INFORMATION_SCHEMA` | ⚠️ Connection works (sandbox proven), mapping to BH metadata model needed | 2-3d wire-up post `bb#488` | **BH-590** (no PR) |
| Generate `sources.yml` + staging from a NEW Silver table | ❌ No code | 3-4d build | **BH-592** (no PR) |
| Generate `schema.yml` tests (`not_null`/`unique`/`accepted_values`) | ❌ No code | 3-4d build | **BH-594** (no PR) |
| Scaffold Atlas semantic-view YAML (deterministic) | ✅ Code built, **orphaned** | Not registered in dbt_agent ReAct tool list | **BH-591** wires it (no PR) |
| LLM enrichment of `custom_instructions` / `verified_queries` | ❌ No code | bb#489 explicitly punts to agent layer | **BH-591** (no PR) |
| Validate Atlas YAML doesn't hallucinate | ❌ No code | Vocabulary validator + Snowflake compile harness | **BH-596** (no PR) |
| Open a PR via GHE proxy with agent's output | ⚠️ Code in flight, CHANGES_REQUESTED | `bb#496` (super_agent path) depends on `bb#494` | BH-529 chain |
| GHE `base_url` routing (Longaeva GHE, not github.com) | ❌ No code | 18+ hardcoded URL touchpoints | **BH-593** (no PR) |
| End-to-end test of full 6-step chain | ❌ No code | The quality gate | **BH-597** (no PR) |

**Practical minimum for Day-1 demo with co-build framing**: BH-590 + BH-591 + BH-593 + the BH-529 chain landing. Implementation specs at [`impl-specs/`](impl-specs/).

## What is truly built today (2026-06-05)

The Snowflake integration is **built and tested across 4 PRs, all in review,
168 unit tests green**. Per `scorecard.md` EOD 2026-06-01: "all 7 layers of
the warehouse-agnostic pattern are Snowflake-compliant."

| Warehouse-agnostic layer | Status | PR |
|---|---|---|
| 1 — Destination Service | ✅ Already shipped | — |
| 2 — OMD Webhook Adapter | ✅ Already shipped | — |
| 3 — OMD Ingestion Source Config | ✅ Built, in review | [`pc#777`](https://github.com/brighthive/brighthive-platform-core/pull/777) — 14 tests |
| 4 — OMD Service Type Mapping | ✅ Already shipped | — |
| 5 — BrightBot Connection + dialect + tests + security guard | ✅ Built, in review (DIRTY — needs rebase) | [`bb#488`](https://github.com/brighthive/brightbot/pull/488) — 66 tests |
| 6 — Webapp Registry | ✅ Already shipped (verified, BH-552 audit) | — |
| 7 — Org-CDK Ingestion Pipeline (`workspace_secret_store` migration) | ✅ Built, in review | [`data-organization-cdk#156`](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) — 20 tests |
| §2 Atlas YAML scaffold tool (BH-531) | ✅ Built, draft (orphan — see Layer-B boundary below) | [`bb#489`](https://github.com/brighthive/brightbot/pull/489) — 35 tests |

**Auth scope (Phase 1)**: username / password / account / warehouse. JWT /
key-pair is Phase 2 (`TBC-B` in spec) — do NOT block trial on it.

**Path to "BrightBot can talk to Snowflake on staging" (per `overview.md`):**

1. Mark the 4 PRs Ready-for-review (rebase `bb#488` first to clear DIRTY)
2. Squash-merge to `develop`, promote `develop` → `staging`
3. Drop a Snowflake secret into `workspace_secret_store/{longaeva-workspace-uuid}`
   with `type=SNOWFLAKE`
4. That's it.

## How to test what's truly there

Run these in order — each one fails fast if a prior layer didn't deploy.

### Local — already passing (don't re-run unless reviewing)

```bash
# brightbot Layer 5 (bb#488) — 66 unit tests
cd brightbot && uv run pytest tests/unit/test_snowflake_warehouse.py -v

# Atlas scaffold (bb#489) — 35 unit tests
uv run pytest tests/unit/test_atlas_semantic_view_scaffold.py -v

# platform-core Layer 3 (pc#777) — 14 unit tests
cd ../brighthive-platform-core && pnpm test test_config_loader

# org-CDK Layer 7 (data-organization-cdk#156) — 20 unit tests
cd ../brighthive-data-organization-cdk && pytest tests/ -v
```

### Sandbox — already passing (proves target shape is real)

```bash
cd clients/trials/longaeva/sandbox
./test_pipeline.sh      # infra/DDL/dbt/RBAC — 27/27
./validate_poc.sh       # every PoC use case — 11/11 against live Snowflake
```

### Staging smoke (post-merge — does NOT exist yet)

```gherkin
Scenario: BrightBot connects to Snowflake on staging
  Given the 4 PRs are merged + deployed to staging
  And a workspace_secret_store entry exists for {workspace-uuid} with type=SNOWFLAKE
  When the agent invokes any Snowflake-bound tool
  Then connection succeeds
  And no `Unknown warehouse type: snowflake` error is raised

Scenario: Read-only enforcement
  When the agent attempts DELETE / UPDATE / INSERT / DROP / multi-statement
  Then assert_read_only_sql rejects with the appropriate error
  And SELECT / SHOW / WITH / DESC / EXPLAIN are allowed

Scenario: Snowflake dialect SELECT
  When the agent generates SQL for a SELECT against LONGAEVA_POC
  Then the SQL uses LIMIT (not TOP)
  And ANSI double-quoted identifiers (not bracket quotes)
  And ILIKE / INFORMATION_SCHEMA where appropriate

Scenario: OMD catalog ingestion
  When OMD ingestion lambda runs against the configured Snowflake account
  Then tables appear in the workspace metadata model
  And service type maps correctly per Layer-4 mapping
```

The above scenarios are **what Gate A verifies** — see
[`00-STAGING-INTEGRATION-RUNBOOK.md` → Gate A](00-STAGING-INTEGRATION-RUNBOOK.md#gate-a--snowflake--byow).
None have run; all are gated on the 4-PR merge.

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

## What this niche does NOT cover (Layer-A boundary)

This niche is **Snowflake plumbing only** — it lets BrightBot *talk to* a
Snowflake account (connect, SELECT, introspect, ingest catalog). It does NOT
give the dbt engineering agent any authoring capability. That work lives in
**Gate A.5** (see [runbook](00-STAGING-INTEGRATION-RUNBOOK.md#gate-a5--dbt-agent-authoring-capability-layer-b)).

The boundary, made concrete:

| Capability | In this niche? | Where it lives |
|---|---|---|
| BrightBot connects to Snowflake | ✅ bb#488 | Here |
| BrightBot generates Snowflake-dialect SELECT | ✅ bb#488 | Here |
| `assert_read_only_sql` blocks DELETE/INSERT | ✅ bb#488 | Here |
| OMD ingestion lambda registers Snowflake source | ✅ pc#777 | Here |
| Atlas YAML scaffold function exists | ✅ bb#489 (orphan tool) | Here, but **not wired** |
| Snowflake `INFORMATION_SCHEMA` → BH metadata model | ❌ no PR | **BH-590 (GAP-2)** |
| Atlas tool wired into dbt_agent + LLM enrichment | ❌ no PR | **BH-591 (GAP-3b)** |
| dbt `sources.yml` + staging model generation | ❌ no PR | **BH-592 (GAP-4)** |
| dbt `schema.yml` test inference | ❌ no PR | **BH-594 (GAP-9)** |

bb#489 sits awkwardly on this boundary — the *code* is in this niche's PR set
but the *capability it enables* belongs to Gate A.5. Until BH-591 lands, bb#489
ships dead code (the tool is never invoked).

## Out of scope for the trial

- JWT / key-pair Snowflake auth (Phase 2, `TBC-B`).
- Self-healing detect→PR loop (GAP-7, future epic).
- Longitudinal anomaly monitoring (GAP-8, sequenced after BH-503).

## References

- Epic: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)
- Reference impl: brightbot PR #433 (Synapse) — see memory `project_azure_synapse_byow`
- Spec: `brightbot/docs/specs/snowflake-full-integration.md` (Layer status table)
