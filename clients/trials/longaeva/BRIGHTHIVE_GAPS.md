---
title: "Longaeva PoC — BrightHive gap analysis & next-sprint plan"
client: longaeva
jira_epic: BH-526
trial_start: "2026-06-15"
author: kuri
last_reviewed: "2026-06-08"
amended:
  - "2026-06-01 — GAP-3 (semantic view scaffolder) blocker resolved: Atlas YAML examples received from client; spec distilled at artifacts/atlas-semantic-view-spec.md"
  - "2026-06-03 — Self-hosting deployment simplified: Matt → Grant/Sumukh email confirms Terraform module as primary path (CDK becomes alternative). Trial-guide artifact extended with Path A (Terraform) + uv-based local install. New tickets BH-572 (TF module), BH-573 (setup doc), BH-574 (CLI/uv), BH-575 (MCP auth decision) queued in TRACKER.md."
  - "2026-06-05 — HONESTY AMENDMENT (multi-agent trial review). The original 'Confidence to win: HIGH' read was written before the Layer-A/B/C decomposition surfaced that the dbt engineering agent's authoring capability (POC §1+§2 headline) has ZERO PRs today, only 5 freshly-created tickets (BH-590..BH-594) plus 3 more identified by review (BH-595..BH-597). Honest confidence is MEDIUM, win-conditional on: (a) Grant call this week to reframe semantic-view as co-build Day 6-8, (b) BH-590/591/592 landing to demo-quality by Day 3, (c) GHE creds + MCP auth decision unblocked, (d) E2E eval harness (BH-597) catching hallucinations before Day 6. See artifacts/email-2026-06-05-grant-trial-reframe-DRAFT.md for the proposed Grant reframe."
  - "2026-06-08 — MERGE TRAIN LANDED (24 PRs across 4 repos squash-merged to develop). Tickets closed via merge: BH-527, BH-528, BH-529, BH-530, BH-549, BH-550, BH-551, BH-553, BH-554, BH-559, BH-560, BH-561, BH-562, BH-563, BH-564, BH-565, BH-567, BH-573, BH-574, BH-592, BH-594, BH-597. Specs signed off on develop: SPEC-GOLDEN-CASES, SPEC-SNOWFLAKE-E2E, SPEC-GENERATE-MART-MODEL, SPEC-BB-OKTA-FEDERATED, SPEC-GHE-MIGRATION-FINAL, SPEC-MCP-DCR-RFC7591. Live verdict on develop HEAD: GC harness 5 passed / 8 skipped / 2 strict-xfailed, L3 e2e 1 passed, semantic-view query alive ($174B exposure across 196 issuers). Composite ≥10-of-14 GCs demoed convincingly: 40% → ~70%. **Outstanding for Day 1**: staging deploy (auto-flips GC-10 S6/S7 + unblocks GC-9), BH-533 connectivity validation, demo-storyboard scope decision with Grant. **Audit-debt (not trial-blocking)**: SPEC-GHE-MIGRATION-FINAL impl (closes routes/dbt_routes.py + github_tools.py read-path PyGithub leaks), generate_mart_model impl (bb#513 spec only), bb#489 multi-table semantic view (orphaned draft). Full handoff: SESSION-HANDOFF-2026-06-08.md."
status: pre-trial-locked
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

- **Sandbox status**: ✅ 10/10 PoC use cases resolve (`./sandbox/validate_poc.sh`),
  full ELT stack live (Snowflake + dbt + **Dagster orchestration**), ~95% fidelity
- **BrightHive readiness**: 🔲 9 product gaps (GAP-1…9 below), of which **1 is the
  critical path** (Snowflake connectivity) and the rest are scoped wiring.
- **Confidence to win**: **MEDIUM, win-conditional** (amended 2026-06-05 after
  multi-agent trial review surfaced 8 tickets, not 4, with ZERO PRs covering
  POC §1+§2 authoring). Was previously stated as HIGH; that read was written
  before the Layer-A/B/C decomposition exposed the missing dbt-agent
  authoring layer. Sandbox de-risks the *target* (the artifacts BrightHive
  must emit are real and reachable); it does NOT de-risk the *agent's ability
  to emit them under LLM non-determinism*. See "Honest probability per POC
  section" below.

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
| **✅ Reference exists** | `sandbox/brighthive_adapter/snowflake_connection.py` — a **validated, parity implementation** of the `WarehouseConnection` ABC, self-tested against live `LONGAEVA_POC` (connects, queries the semantic view, SELECT-guard blocks DELETE, INFORMATION_SCHEMA introspection). The brightbot PR is now a **mechanical drop-in** with zero design risk — copy the class, register it, run multi-agent review. Promotion steps in `sandbox/brighthive_adapter/README.md`. |
| **Effort** | ~1 day (drop in proven class + register + review; was 1–2d) |
| **Owner** | Marwan / Ahmed |
| **Test target** | `sandbox/brighthive_adapter/snowflake_connection.py` self-test already passes against `LONGAEVA_POC`; promote and run the existing warehouse scenario tests. |

### GAP-2 — Snowflake schema introspection via INFORMATION_SCHEMA

| | |
|---|---|
| **Sandbox proves** | `LONGAEVA_POC.INFORMATION_SCHEMA.{TABLES,COLUMNS}` returns the full medallion shape; the sandbox seeds 16 tables across BRONZE/SILVER/GOLD/REF + MONITORING. |
| **BrightHive gap** | Introspection today targets Redshift/Synapse system tables. Needs a Snowflake `INFORMATION_SCHEMA` path (and `SHOW ... IN SCHEMA` for stages/semantic views). |
| **✅ Reference exists** | The adapter self-test (GAP-1) already runs `INFORMATION_SCHEMA.TABLES` introspection against `LONGAEVA_POC` and returns the GOLD base tables — the query path is proven; remaining work is mapping to the metadata model. |
| **Work** | Add Snowflake introspection queries; map to the existing metadata model the Ingestion + Engineering agents consume. |
| **Effort** | 2–3 days |
| **Owner** | Marwan |
| **Test target** | Introspect `LONGAEVA_POC.*`; assert it finds the same 16 tables + 2 stages + 1 semantic view the sandbox created. |

---

## P1 — Section-specific (each blocks one PoC use case)

### GAP-3 — Snowflake Semantic View YAML scaffolder

| | |
|---|---|
| **Sandbox proves** | `sandbox/semantic/sv_daily_portfolio_exposure.yaml` is a structurally-aligned reference (`spec:` / `sdk_extensions:` strip boundary, `baseline_expectations`, `metric_store`, `filter_presets`, etc.). `strip_and_emit.py` proves it round-trips. |
| **✅ Real client contract received** | Grant delivered the **Atlas YAML examples** 2026-06-01 (3 sanitized semantic views — retail, digital usage, healthcare). Authoritative artifacts: `artifacts/atlas-semantic-view-examples.yaml` (raw) + `artifacts/atlas-semantic-view-spec.md` (distilled inference rules + naming conventions). **Blocker resolved.** |
| **Naming reconciliation** | Their actual conventions: `name: SVW__<DOMAIN>__<SUBJECT>`, Silver table `INT__<DOMAIN>__<SUBJECT>`, top-level `atlas:` block (not `sdk_extensions:`), field-level `atlas.target` bindings + `atlas.metric.aggregations` for fact-to-metric promotion. The sandbox's `sv_daily_portfolio_exposure.yaml` is structurally close but uses different block names — reconcile before final scaffolding tests. |
| **DDL ownership** | **BrightHive does NOT emit `CREATE SEMANTIC VIEW`** — the Atlas SDK strips `atlas:*` and owns DDL. Our tool emits Atlas-shaped YAML; validation is by running a `verified_query` end-to-end through MCP. |
| **BrightHive gap** | No tool today emits Atlas-shaped YAML from a Silver table + description. This is the **headline PoC capability** (use case 2.1). |
| **Work** | New Engineering-agent tool: read Silver schema (via `SnowflakeConnection`, BH-527 ✅ merged) + the Atlas inference table from spec, populate all Atlas blocks (`dataset_key`, `entities.primary`, `defaults`, `dagster_dep`, `owners`, field-level `atlas.target` + `atlas.metric.aggregations`), generate ≥1 `verified_query` in Snowflake `SEMANTIC_VIEW(...)` syntax, emit. |
| **Effort** | 1 sprint (5 pts — bumped from 3 with the concrete scope from real examples) |
| **Owner** | Marwan + AI/ML |
| **Ticket** | BH-531 (description rewritten 2026-06-01 with the concrete contract) |
| **Test target** | Scaffold from `LONGAEVA_POC.SILVER.int_enriched_holdings`; YAML must validate against the Atlas contract (PyYAML round-trip + all required blocks present) and round-trip a `verified_query` through MCP. |

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

## Confidence statement (amended 2026-06-05)

> Previously read "HIGH". Amended after the multi-agent trial review surfaced
> the dbt-agent authoring layer (POC §1+§2 headline) as zero-PR, eight-ticket
> work with non-deterministic LLM steps. See `amended:` log at top.

We state with **MEDIUM, win-conditional** confidence that the PoC is winnable,
because:

1. **The environment is no longer a question mark** — live Snowflake parity
   account, every use case resolves against `validate_poc.sh` (10/10). The
   *target* is de-risked.
2. **Each BrightHive gap has a golden reference** — agent work is "emit what
   the sandbox proved valid", not "figure out what valid looks like."
3. **Layer A (Snowflake plumbing) is bounded and mechanical** — BH-527 is
   1–2d wiring on existing plumbing. This piece is honestly LOW-risk.

We caveat with **THREE risk factors not in the original read**:

1. **Layer B (dbt-agent authoring) is 8 tickets, 0 PRs, ~25 engineering-days
   of work** before the trial. BH-590..597 cover POC §1.1, §1.3, §2, §4.2 —
   but §1.2 (REST API) is at risk and POC §3 (MCP feedback loop) is gated on
   Grant's auth decision.
2. **LLM non-determinism is uncovered.** Hallucination risk is concentrated
   in `verified_queries[].sql`, `atlas.target` bindings, and `sample_values`.
   BH-596 (grounding validator + compile harness) + BH-597 (E2E eval harness)
   are the quality gates that turn "21 PRs merged, gates green" into "demo
   works the first time, every time" — they MUST land before Day 6.
3. **The "co-build" framing is now the proposed plan, not the original
   black-box demo.** See `artifacts/email-2026-06-05-grant-trial-reframe-DRAFT.md`
   — Day 6–8 reframed from "agent autonomously enrolls" to "joint workshop
   with Longaeva data scientist." Win-condition (a): Grant agrees.

**Honest probability per POC section (multi-agent review, 2026-06-05):**

| Section | Realistic prob. E2E on real data |
|---|---|
| §1 Ingestion (S3 / REST / Data Share) | 20% |
| §2 Semantic view (headline) | 15% |
| §3 MCP feedback loop | 30% |
| §4 Maintenance | 25% |
| **All four on real data** | ~5% |
| **≥2 of 4 demoed convincingly** | ~45% |

**External dependencies still owned by Grant** — GHE host URL + sandbox PAT +
TLS chain (gates BH-593 verify), MCP auth-workflow decision (gates Gate D).
The Grant call this week (see Grant email draft) exists to unblock both.

## Reproduce

```bash
cd clients/trials/longaeva/sandbox
./test_pipeline.sh      # infra/DDL/dbt/RBAC — 27/27
./validate_poc.sh       # every PoC use case — 10/10

# Full ELT orchestration (Dagster asset graph, all 7 assets):
(cd sources/rest-stub && uv run --with fastapi --with uvicorn python -m uvicorn main:app --port 8000 &)
cd orchestration && DAGSTER_HOME=$(mktemp -d) uv run --python 3.12 \
  --with 'dagster>=1.7,<1.9' --with dbt-snowflake --with snowflake-connector-python \
  --with httpx --with pyyaml \
  dagster asset materialize --select '*' -m longaeva_dagster.definitions
```

See [`sandbox/FIDELITY.md`](sandbox/FIDELITY.md) for the build journal and
[`sandbox/README.md`](sandbox/README.md) for topology.
