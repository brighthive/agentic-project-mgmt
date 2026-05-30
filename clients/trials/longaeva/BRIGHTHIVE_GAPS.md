---
title: "Longaeva PoC — BrightHive gap analysis & next-sprint plan"
client: longaeva
jira_epic: BH-526
trial_start: "2026-06-15"
author: kuri
last_reviewed: "2026-05-30"
status: pre-trial
---

# Longaeva PoC — What's missing on the BrightHive side

> **Purpose**: the sandbox (`sandbox/`) proves *the environment and every PoC use
> case is resolvable* — 10/10 use cases pass against live Snowflake. This doc is
> the other half: **what BrightHive's own product must do to plug into that
> sandbox and win the trial**, scoped as next-sprint work.

## TL;DR

The sandbox is the **target**; BrightHive is the **agent that must hit it**. We
have validated that the target is real and every use case is solvable. The
remaining work is wiring BrightHive's agents to *produce* the artifacts the
sandbox proves are valid.

- **Sandbox status**: ✅ 10/10 PoC use cases resolve (`./sandbox/validate_poc.sh`)
- **BrightHive readiness**: 🔲 6 pre-trial gaps (BH-526), of which **1 is the
  critical path** (Snowflake connectivity) and the rest are scoped wiring.
- **Confidence to win**: HIGH *if* the critical path + 3 P1 items land before
  June 15. The sandbox de-risks everything downstream because we can now
  develop the agents against a known-good environment instead of guessing.

## How to read this

Each gap maps a **sandbox capability we proved** → **the BrightHive code that
must produce it** → **effort + owner + ticket**. The sandbox file referenced is
the golden reference / test target for that piece of agent work.

---

## Critical path (blocks Sections 1 + 2 — must land first)

### GAP-1 — `SnowflakeConnection` in the warehouse factory

| | |
|---|---|
| **Sandbox proves** | All SQL (`COPY INTO`, `CREATE SEMANTIC VIEW`, queries) runs against real Snowflake via `snow`/`snowflake-connector-python`. |
| **BrightHive gap** | `brightbot/brightbot/tools/warehouse_connections.py:484` — `CONNECTION_CLASSES` has `redshift`, `azure_synapse`, `postgres`. **No `snowflake`.** `SnowflakeConnectionParams` is modeled in `query_retrieval.py:64` but never wired to a connection class, so any Snowflake SQL raises `ValueError`. |
| **brightagent-v2** | `bright_contracts/warehouse.py:20` `Warehouse` Protocol names Snowflake, but only the Redshift adapter/spec exists (`SPEC-SERVICE-redshift.md`). A `SnowflakeAdapter` is needed there too if the trial runs on v2/CEMAF. |
| **Work** | Implement `SnowflakeConnection(WarehouseConnection)` mirroring `RedshiftConnection`/`SynapseConnection`; register in `CONNECTION_CLASSES`. Use `snowflake-connector-python`. Honor SELECT-only enforcement that the other connections have. |
| **Effort** | 1–2 days (plumbing exists, factory entry + connector + tests) |
| **Owner** | Marwan / Ahmed |
| **Test target** | Point it at `LONGAEVA_POC` with the `~/.snowflake/config.toml` `brighthive` connection; run the existing warehouse scenario tests against it. |

### GAP-2 — Snowflake schema introspection via INFORMATION_SCHEMA

| | |
|---|---|
| **Sandbox proves** | `LONGAEVA_POC.INFORMATION_SCHEMA.{TABLES,COLUMNS}` returns the full medallion shape; the sandbox seeds 16 tables across BRONZE/SILVER/GOLD/REF + MONITORING. |
| **BrightHive gap** | Introspection today targets Redshift/Synapse system tables. Needs a Snowflake `INFORMATION_SCHEMA` path (and `SHOW ... IN SCHEMA` for stages/semantic views). |
| **Work** | Add Snowflake introspection queries; map to the existing metadata model the Ingestion + Engineering agents consume. |
| **Effort** | 2–3 days |
| **Owner** | Marwan |
| **Test target** | Introspect `LONGAEVA_POC.*`; assert it finds the same 16 tables + 2 stages + 1 semantic view the sandbox created. |

---

## P1 — Section-specific (each blocks one PoC use case)

### GAP-3 — Snowflake Semantic View YAML scaffolder

| | |
|---|---|
| **Sandbox proves** | `sandbox/semantic/sv_daily_portfolio_exposure.yaml` is the **golden reference**: a Longaeva-extended YAML with the explicit `spec:` / `sdk_extensions:` strip boundary, `baseline_expectations`, `metric_store`, `filter_presets`, `agent_instructions`, `verified_query_examples`. `strip_and_emit.py` proves it round-trips to valid `CREATE SEMANTIC VIEW` DDL. |
| **BrightHive gap** | No tool today emits this YAML from a Silver table + plain-language description. This is the **headline PoC capability** (use case 2.1). |
| **Work** | New Engineering-agent tool: read Silver schema (via GAP-2) + reference schemas, infer dimensions/time-dims/facts/metrics, populate the extended metadata blocks, emit YAML matching Longaeva's spec. Then call `strip_and_emit`-equivalent to validate compile. |
| **Effort** | ~1 sprint |
| **Owner** | Marwan + AI/ML |
| **Test target** | Scaffold from `LONGAEVA_POC.SILVER.int_enriched_holdings`; diff against the golden YAML; must infer ≥90% of dims/metrics and compile clean (the `validate.py` layer-1 gate). |
| **⚠️ Blocker** | Needs **Longaeva's actual YAML spec** (Grant to deliver ≤ June 8). Our golden reference is structurally aligned but invented — reconcile when theirs lands. |

### GAP-4 — dbt `sources.yml` + staging model generation from scratch

| | |
|---|---|
| **Sandbox proves** | `sandbox/dbt/` is a working dbt project: sources over BRONZE/REF/share, `int_enriched_holdings` join layer, 3 GOLD data products, 41 passing tests, custom singular tests mirroring `baseline_expectations`. `brightbot-dbt-MCP-server` already exists as the execution surface. |
| **BrightHive gap** | dbt agent can *update* sources but not *generate* a project/sources.yml + staging model from a newly introspected table. Use cases 1.1, 1.3. |
| **Work** | Generator that, given an introspected table, emits `sources.yml` + a staging model that canonicalizes field names/types + `schema.yml` tests inferred from column types & PKs. Pattern after `sandbox/dbt/models/staging/stg_vendor_security_master.sql`. |
| **Effort** | 3–4 days |
| **Owner** | Marwan |
| **Test target** | Generate staging for `LONGAEVA_VENDOR_SHARE_SIM.SHARED.vendor_security_master`; must match the sandbox's hand-written staging model + pass `dbt test`. |

### GAP-5 — GitHub Enterprise `base_url` config

| | |
|---|---|
| **Sandbox proves** | N/A (sandbox PRs go to github.com). |
| **BrightHive gap** | PR-raising hardcodes github.com; Longaeva is on GHE. One param. Blocks **all** PR creation (every use case ends in a PR). |
| **Work** | Thread a `GITHUB_BASE_URL` / GHE host through the GitHub client config. |
| **Effort** | 1 day (testable only once Longaeva provides a GHE token + host) |
| **Owner** | Ahmed |

### GAP-6 — MCP client config for Longaeva's MCP server

| | |
|---|---|
| **Sandbox proves** | `sandbox/semantic/mcp_check.py` simulates the downstream MCP loop: surfaces every measure/dim, runs filtered/aggregated/multi-dim queries, flags gaps. This is *our* stand-in; the real loop hits **their** MCP. |
| **BrightHive gap** | `BrightAgentMCPClient` wraps `MultiServerMCPClient`; needs Longaeva's MCP endpoint + auth in `mcp_config.py`. Use case 3. |
| **Work** | Add their server config; confirm protocol compatibility (standard MCP). 1–2 days IF standard. |
| **Effort** | 1–2 days |
| **Owner** | Ahmed |
| **⚠️ Blocker** | Needs Longaeva to provision MCP read access (Day 1–2). |

---

## P2 — Maintenance automation (Section 4; partially shipped)

### GAP-7 — Self-healing detect→PR loop wiring

| | |
|---|---|
| **Sandbox proves** | `sandbox/self_healing/failure_modes.py` encodes the 4 failure modes Grant named, each with a detection query + the exact surgical fix. 4/4 detect→fix loops verified. `sandbox/orchestration/` (Dagster) provides the **run-log + asset-lineage surface** the agent reads to diagnose — the same shape as Longaeva's Dagster + OpenLineage stack. |
| **BrightHive gap** | Observability agent alerts today; the **detect→diagnose→surgical-PR** loop is not auto-triggered. Schema-drift detection specifically has zero code refs. |
| **Work** | Wire the loop: on detected failure, Engineering agent reads Dagster run logs / asset lineage / schema, generates a scoped PR with plain-language diagnosis. The sandbox's `fix_summary` fields are the spec for "surgical, not rewrite"; the Dagster asset graph is the lineage to traverse. |
| **Effort** | ~1 sprint (drift detection can ride on GAP-2 schema-version comparison) |
| **Owner** | Marwan + AI/ML |
| **Test target** | Run each `failure_modes.py` mode; the agent must produce the same surgical fix the fixture encodes. |

### GAP-8 — Longitudinal anomaly monitoring (stateful quality agent)

| | |
|---|---|
| **Sandbox proves** | `sandbox/monitoring/` persists per-snapshot metrics + detects all 4 anomaly families (row-count drift, cardinality breakdown, distributional skew, null spike) vs trailing window. 4/4 fire in simulation. |
| **BrightHive gap** | Quality agent is stateless per run; no trailing-window persistence. This maps to the `QualityRuleExecutionNode` already specced in the BH-503 quality-rules epic. |
| **Work** | Persist per-run metrics; trend computation vs window. The sandbox's `metric_history` + `anomaly_events` tables are a ready schema to mirror. |
| **Effort** | ~1 sprint (BH-503 overlap — sequence after it) |
| **Owner** | Marwan |

### GAP-9 — dbt `schema.yml` test generation

| | |
|---|---|
| **Sandbox proves** | `sandbox/dbt/` custom singular tests + `accepted_values`/`not_null`/`unique` schema tests mirror the YAML `baseline_expectations`. |
| **BrightHive gap** | dbt agent emits GX contracts but not dbt `schema.yml` tests with inferred `not_null`/`unique`/`accepted_values`. Use case 4.2. |
| **Work** | Test-suite inference from schema + profiling; emit `schema.yml`. |
| **Effort** | 3–4 days |
| **Owner** | Marwan |

---

## Shipped — no work needed (validated against sandbox where possible)

| Capability | Status | Sandbox corroboration |
|---|---|---|
| BrightSignals Slack alerts | ✅ Shipped (Sprint 9) | Out of sandbox scope (Slack-side) |
| BrightAgent bidirectional Slack | ✅ Shipped | Out of sandbox scope |
| Neo4j KG + MCP exposure | ✅ Shipped | `mcp_check.py` proves the queryability contract a KG would also satisfy |
| Agent RBAC scoping | ✅ Pattern proven | `sandbox` `LONGAEVA_AGENT_ROLE` — agents get a scoped subset, enforced in strict mode |
| GX quality suite generation | ✅ Ready (output-format fix) | dbt DQ contracts proven in `sandbox/dbt/` |

---

## Sprint plan — proposed ticket set under BH-526

Sequenced by dependency. Critical path first.

| # | Ticket | Gap | Effort | Owner | Depends on |
|---|---|---|---|---|---|
| 1 | `SnowflakeConnection` in warehouse factory | GAP-1 | 1–2d | Marwan | — |
| 2 | Snowflake INFORMATION_SCHEMA introspection | GAP-2 | 2–3d | Marwan | #1 |
| 3 | Semantic view YAML scaffolder | GAP-3 | 1 sprint | Marwan+AIML | #2, Longaeva spec |
| 4 | dbt sources.yml + staging generator | GAP-4 | 3–4d | Marwan | #2 |
| 5 | GHE base_url config | GAP-5 | 1d | Ahmed | Longaeva GHE token |
| 6 | Longaeva MCP client config | GAP-6 | 1–2d | Ahmed | Longaeva MCP access |
| 7 | Self-healing detect→PR loop | GAP-7 | 1 sprint | Marwan+AIML | #2 |
| 8 | Stateful anomaly monitoring | GAP-8 | 1 sprint | Marwan | BH-503 |
| 9 | dbt schema.yml test generation | GAP-9 | 3–4d | Marwan | #4 |

**Minimum viable for Day-1 success** (Sections 1 + 2 demoable): tickets **1, 2, 3, 4, 5**. Tickets 6–9 enrich Sections 3 + 4 and can land during the trial as co-development if needed.

## Confidence statement

We can state with high confidence that **the PoC is winnable with excellence**,
because:

1. **The environment is no longer a question mark** — we have a live Snowflake
   account with the exact medallion + semantic-view + share + RBAC shape
   Longaeva described, and every use case resolves against it (`validate_poc.sh`
   10/10).
2. **Each BrightHive gap has a golden reference to build against** — the agent
   work is no longer "figure out what correct looks like", it's "make the agent
   emit what the sandbox already proved is valid". That collapses the risk.
3. **The critical path is bounded and small** — GAP-1 is 1–2 days of wiring on
   plumbing that already exists, not a from-scratch build.

The two genuine external dependencies — Longaeva's **actual YAML spec** (GAP-3)
and **MCP access** (GAP-6) — are owned by Grant and due before/at Day 1; both
have sandbox stand-ins so BrightHive development is unblocked until they arrive.

## Reproduce

```bash
cd clients/trials/longaeva/sandbox
./test_pipeline.sh      # infra/DDL/dbt/RBAC — 27/27
./validate_poc.sh       # every PoC use case — 10/10
```

See [`sandbox/FIDELITY.md`](sandbox/FIDELITY.md) for the build journal and
[`sandbox/README.md`](sandbox/README.md) for topology.
