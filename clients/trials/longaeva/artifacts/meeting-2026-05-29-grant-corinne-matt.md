# Meeting Notes — Workflow Alignment Review

**Date**: 2026-05-29
**Participants**: Grant Langseth (Longaeva), Matt (Brighthive), Corinne (Brighthive)
**Purpose**: Review POC scope piece, verify expected workflow, align on YAML/MCP interaction model

---

## Headline decisions

| # | Decision | Source |
|---|---|---|
| D1 | **POC kickoff: week of June 15, 2026** | "POC is targeted to go live the week of June 15" |
| D2 | **YAML is the canonical spec format** (not JSON Schema). Editing UX is YAML. | "current data spec is based on JSON schema, but the team prefers YAML for editing" |
| D3 | **YAML → strip SDK keywords → Snowflake `CREATE SEMANTIC VIEW` DDL** is the deploy pipeline | Grant: "single Snowflake system call to create semantic view from that YAML format" |
| D4 | SDK-extension keywords drive downstream routing (MCP / REST / SDK) and **must round-trip cleanly** through stripping | "those keywords get stripped before they're put into the snowflake create ddl function but are really important for all of the routing logic downstream" |
| D5 | **Internal assessment: 80% coverage**, 20% gap to close before POC start | "80% coverage of the ideal scenario, with a 20% gap that could potentially be bridged" |
| D6 | **MCP handles RBAC**. Agents get a **scoped subset** of the user's permissions (not pure inheritance). | "MCP will handle RBAC, with permissions inherited from users but potentially limited for agents" — D7 |
| D7 | **Slack default verbosity is empirically tested during POC**, not pre-decided | "uncertainty about the best default starting point for Slack responses, indicating a need for empirical testing" |

## Architectural picture (Grant's words, paraphrased)

> Heterogeneous mix of vendors → Snowflake → bronze/silver → **Gold = Snowflake Semantic Views (their YAML extends Snowflake's)** → SDK + MCP server → federated consumption (chat, REST, declarative SDK) → standardized **time-series primitives** → downstream compute engine → derivative time-series products + statistics.

Key implication: **one function should map across the entire semantic-view output**, treating the result as a time-series primitive. Our SILVER `(entity_id, metric_name, ts, value, currency, …)` schema already models this — keep it.

## YAML SDK extensions (what gets stripped before DDL)

Grant called these out as load-bearing for downstream routing:

- **Metric-store wiring** — how metrics register and are reused
- **Filter presets** — named, reusable filters
- **Plain-language agent instructions** — injected into agent context
- **Verified query examples** — hand-checked SQL for the LLM
- **Baseline expectations** — dbt-test-style assertions per metric/dimension ("under these conditions I would expect this thing")

These already exist in our `sandbox/semantic/sv_daily_portfolio_exposure.yaml` — call out the strip boundary explicitly so it's clear which fields go to Snowflake DDL vs. which are SDK-only.

## Validation harness (Grant is actively building this)

Three layers, in increasing rigor:

1. **Syntax checks** — does the YAML compile to a valid `CREATE SEMANTIC VIEW`? (Already in flight on Grant's side)
2. **Correctness checks on the data itself** — universal invariants (no nulls in PK columns, monotonic time series, etc.)
3. **Baseline expectations** — author-supplied assertions in the YAML, dbt-test-style, run pre-deploy AND post-refresh continuously

Implication for our scaffolder: the YAML must surface a **`baseline_expectations`** block (or equivalent — confirm exact field name with Grant) that holds these author-supplied assertions.

## Other items raised (lower priority but tracked)

- **Semantic inheritance / branching**: open question — single YAML per node vs. nested structure. Grant doesn't have a final answer. Our scaffolder should keep this in mind but doesn't need to commit yet.
- **Lineage for high-cardinality dimensions**: Grant wants traceability when a dimension's cardinality drifts. Maps to POC scorecard 4.3 (longitudinal anomaly monitoring on cardinality breakdowns).
- **Metric index** for query performance: roadmap item, not POC-gating.
- **GitHub hygiene for DQ tests**: Grant to share their conventions before June 8.

## Action items

| Owner | Action | By |
|---|---|---|
| Grant | Provide YAML editing prefs (their actual example file) | before 2026-06-08 |
| Grant | Clarify Slack ↔ MCP interaction expectations | before 2026-06-08 |
| Grant | Share GitHub hygiene + DQ-test conventions | before 2026-06-08 |
| Grant | Confirm POC start date + any blockers | before 2026-06-08 |
| Grant | Coordinate access/permissions provisioning | before 2026-06-15 |
| Brighthive | List of DevOps tasks for setup → Longaeva | before 2026-06-08 |
| Brighthive | Explore on-site engineer for POC support | before 2026-06-15 |

## What this changes in our sandbox

Triggered fidelity work — see [`../sandbox/FIDELITY.md`](../sandbox/FIDELITY.md):

- **F8 (new)** — Mark SDK-extension fields in our YAML so DDL-strip boundary is explicit
- **F9 (new)** — Add `baseline_expectations` block with at least one example assertion per metric
- **F10 (new)** — Add a strip-and-emit script: takes our extended YAML, strips SDK keywords, emits Snowflake-native `CREATE SEMANTIC VIEW` DDL, validates it compiles
- **B1 → unblocked path**: their actual YAML spec lands ≤ June 8 → reconcile our placeholder YAML against theirs
- **Blocker #1 (date) → resolved** by D1
