---
title: "Longaeva — knowing-the-order merge plan"
audience: "Marwan, Ahmed, Kuri"
purpose: "Land the existing 21 PRs in dependency order with a verify step between each block"
last_reviewed: "2026-06-05"
---

# Longaeva — knowing-the-order merge plan

> **What this is.** The exact PR-merge sequence with a verification step
> between each block. Built off the integration runbook (gates A→D) but
> written as a checklist a human follows on a Tuesday afternoon.
>
> **What this is NOT.** Not a plan to consolidate stacked PRs into one-per-topic
> (that's a separate decision). This plan ships what's already written.

## Block 1 — Snowflake foundation (4 PRs, unblocks "BrightAgent reads Snowflake")

These 4 PRs are independent of each other for code purposes but should be
landed close together to deploy as one staging promotion.

| # | PR | Layer | Owner | Pre-merge action |
|---|---|---|---|---|
| 1.1 | [`bb#488`](https://github.com/brighthive/brightbot/pull/488) — `SnowflakeConnection` (BH-527/528/549/550/553) | 5 brightbot | Marwan | **Rebase to clear DIRTY conflict** (`uv.lock` + `warehouse.py`) → mark Ready-for-review → review → squash to `develop` |
| 1.2 | [`pc#777`](https://github.com/brighthive/brighthive-platform-core/pull/777) — `SnowflakeSourceConfig` (BH-551) | 3 OMD | Ahmed | review → squash to `develop` |
| 1.3 | [`data-organization-cdk#156`](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) — `workspace_secret_store` migration (BH-554) | 7 org-CDK | Ahmed | review → squash to `develop` |
| 1.4 | [`bb#489`](https://github.com/brighthive/brightbot/pull/489) — Atlas YAML scaffold tool (BH-531) | dbt-agent tool | Kuri | mark Ready-for-review → review → squash to `develop` (note: tool is orphan until BH-591 wires it; that's fine to land separately) |

### After Block 1 — VERIFY before moving on

```bash
# 1) Promote develop → staging across all 3 repos (auto for brightbot + platform-core; manual webhook for data-org-cdk if needed)

# 2) Drop the Snowflake secret into workspace_secret_store
#    Format: { "username": ..., "password": ..., "account": "bfddsko-dua97555", "warehouse": "POC_WH" }
#    Path:   workspace_secret_store/{longaeva-staging-workspace-uuid}  with type=SNOWFLAKE

# 3) Smoke test on the staging workspace
```

Acceptance — none of these should error:

- [ ] BrightBot connects: no `Unknown warehouse type: snowflake`
- [ ] `assert_read_only_sql` rejects DELETE/UPDATE/INSERT/DROP; allows SELECT/SHOW/WITH/DESC/EXPLAIN
- [ ] BrightBot generates a Snowflake-dialect SELECT (LIMIT not TOP, ANSI double-quotes)
- [ ] OMD ingestion lambda runs against the configured Snowflake account → tables appear in workspace metadata
- [ ] Atlas scaffold tool importable from `brightbot.agents.dbt_agent.tools.atlas_semantic_view` (won't be invoked yet — fine)

**If any check fails, STOP. Do not move to Block 2.**

---

## Block 2 — GHE proxy foundation (platform-core side, 5 PRs as one chain)

This is Kuri's stacked chain on `feat/BH-529-…`. Land children-first onto the parent's branch, then squash the parent to `develop`.

> **External blocker for full verify**: Grant must deliver GHE host URL +
> sandbox PAT + TLS chain. Block 2 can MERGE without these (the proxy code
> works against github.com); only the GHE-routing smoke test is blocked.

### Pre-merge actions

- [ ] Address `pc#778`'s **CHANGES_REQUESTED** review feedback
- [ ] Confirm BH-559..567 children are all green in CI

### Merge order (children → parent → develop)

| # | PR | Ticket | Action |
|---|---|---|---|
| 2.1 | [`pc#780`](https://github.com/brighthive/brighthive-platform-core/pull/780) — tenant isolation (P0) | BH-559 | merge into `pc#778`'s branch |
| 2.2 | [`pc#781`](https://github.com/brighthive/brighthive-platform-core/pull/781) — redirect strip + scrub PAT (P0) | BH-560 | merge into `pc#778`'s branch |
| 2.3 | [`pc#782`](https://github.com/brighthive/brighthive-platform-core/pull/782) — errorCode + truncated flag | BH-561 | merge into `pc#778`'s branch |
| 2.4 | [`pc#783`](https://github.com/brighthive/brighthive-platform-core/pull/783) — 30 URL-parser tests + bug fix | BH-567 | merge into `pc#778`'s branch |
| 2.5 | [`pc#778`](https://github.com/brighthive/brighthive-platform-core/pull/778) — GHE proxy foundation | BH-529 (PC half) | **squash to `develop`** carrying #780-#783 |

### After Block 2 — VERIFY

- [ ] platform-core `develop` → `staging` deploy succeeds (auto)
- [ ] All 7 proxy mutations resolve against github.com
- [ ] **Tenant isolation (P0)**: workspace-A JWT calling `readGitHubFile` with `workspaceId=B` → `ForbiddenError`; with `workspaceId=A` → success
- [ ] grep staging CloudWatch for `Bearer `, `ghp_`, `github_pat_` on Platform Core calls → none
- [ ] (blocked on Grant) GHE `base_url` smoke test deferred — see Block 4

**If tenant isolation or PAT redaction fails, STOP. This is the security headline.**

---

## Block 3 — GHE proxy consumer (brightbot side, 6 PRs as one chain)

Marwan's stacked chain on `BH-529-…`. Same pattern: children-first onto the parent's branch, then squash the parent to `develop`.

> **Hard cross-repo dependency**: `bb#490` cannot be merged until Block 2 is
> deployed to staging. The proxy mutations bb#490 calls must be live on
> staging-platform-core first. Don't skip the Block 2 verify step.

### Pre-merge actions

- [ ] Address `bb#490`'s **CHANGES_REQUESTED** review feedback
- [ ] Confirm BH-562..566 children are all green in CI
- [ ] **`bb#494` MUST land before `bb#496`** (#496 imports #494's modules)

### Merge order (children → parent → develop)

| # | PR | Ticket | Action |
|---|---|---|---|
| 3.1 | [`bb#492`](https://github.com/brighthive/brightbot/pull/492) — redact JWT/PAT logs (P0) | BH-563 | merge into `bb#490`'s branch |
| 3.2 | [`bb#493`](https://github.com/brighthive/brightbot/pull/493) — proxy migration guide (docs) | BH-565 | merge into `bb#490`'s branch |
| 3.3 | [`bb#494`](https://github.com/brighthive/brightbot/pull/494) — Pydantic + injectable PlatformClient | BH-564 | merge into `bb#490`'s branch (BEFORE #496) |
| 3.4 | [`bb#495`](https://github.com/brighthive/brightbot/pull/495) — delete 4 dead PyGithub modules | BH-562 | merge into `bb#490`'s branch |
| 3.5 | [`bb#496`](https://github.com/brighthive/brightbot/pull/496) — super_agent dbt PR creation via proxy | BH-562 (PR1/2) | merge into `bb#490`'s branch |
| 3.6 | [`bb#490`](https://github.com/brighthive/brightbot/pull/490) — consume proxy | BH-529 (BB half) | **squash to `develop`** carrying #492-#496 |

### After Block 3 — VERIFY

- [ ] brightbot `develop` → `staging` deploy succeeds (LangGraph Cloud auto)
- [ ] super_agent dbt run **with** `transformation_service_id` set → PR created via proxy; grep state + traces for `ghp_`/`github_pat` → none
- [ ] super_agent run **without** `transformation_service_id` → still works via legacy path (backwards-compat until BH-568)
- [ ] dbt agent + super_agent both start cleanly on staging (imports resolve after dead-code removal)
- [ ] `tests/unit/tools/test_no_dead_pygithub_modules.py` green in CI

**If super_agent fails to start or the proxy path leaks PAT, STOP. Roll back bb#490 from develop.**

---

## Block 4 — Longaeva-specific config (BH-593, GHE base_url)

> **Status**: BH-593 has **no PR today**. 1d work, owner Ahmed (per
> BRIGHTHIVE_GAPS GAP-5).
>
> **External blocker**: needs Grant's GHE host URL + sandbox PAT + TLS chain
> before E2E verify.

### Action

- [ ] Open new branch: `ahmed/BH-593/ghe-base-url-config` off **post-Block-3 `develop`**
- [ ] Thread `GITHUB_BASE_URL` through:
  - brightbot `github_tools.py` / `github_operations.py` / `github_oauth.py`
  - platform-core github-proxy resolvers (per-workspace `ghe_base_url`)
  - workspace config Pydantic schema + DynamoDB write path
- [ ] Multi-agent review chain (SA → senior-python → QA → junior dev)
- [ ] PR review → squash to `develop`

### After Block 4 — VERIFY

- [ ] Workspace with no `ghe_base_url` set → proxy hits `https://api.github.com` (regression check)
- [ ] Workspace with `ghe_base_url = "https://ghe.longaeva.example.com"` → proxy hits `/api/v3` on that host
- [ ] (Grant-creds-dependent) Smoke test against Longaeva sandbox GHE: full createBranch → commitFiles → createPR

---

## Block 5 — Layer-B dbt-agent authoring (BH-590, BH-591, BH-592, BH-594)

Branch off **post-Block-1 `develop`** (Snowflake foundation must be live).

> **Status**: All 4 tickets have **no PR today**. ~10 engineering-days total.

| Ticket | Branch | Base | Order |
|---|---|---|---|
| BH-590 introspection metadata mapping | `marwan/BH-590/snowflake-introspection-metadata` | post-Block-1 develop | First — others depend on it |
| BH-591 wire Atlas tool + LLM enrichment | `kuri/BH-591/wire-atlas-into-dbt-agent` | post-Block-1 develop | After BH-590 |
| BH-592 sources.yml + staging generator | `marwan/BH-592/dbt-sources-staging-generator` | post-BH-590 develop | Parallel with BH-591 |
| BH-594 schema.yml test inference | `marwan/BH-594/dbt-schemayml-test-inference` | post-Block-1 develop | Parallel with BH-591/592 (only needs INFORMATION_SCHEMA, not BH-592 output) |

Each PR follows the standard 4-agent review chain.

### After Block 5 — VERIFY (Day 6 demo gate)

- [ ] Agent: "scaffold a semantic view for `LONGAEVA_POC.SILVER.int_enriched_holdings`"
- [ ] Tool invoked, LLM enriches `custom_instructions`, ≥1 `verified_query` round-trips through Snowflake `SEMANTIC_VIEW(...)`
- [ ] Generated `sources.yml` + `stg_*.sql` parse via `dbt parse`
- [ ] Generated `schema.yml` tests pass `dbt test` against live data

---

## Block 6 — Quality gates (BH-596, BH-597, BH-595)

Branch off post-Block-5 develop.

| Ticket | Why land last | Owner |
|---|---|---|
| BH-596 grounding validator + verified_query compile harness | Validates BH-591's output — needs BH-591 done | Marwan + AI/ML |
| BH-597 E2E eval harness | Asserts the full 6-step DAG — needs everything else done | Marwan + AI/ML + QA |
| BH-595 REST API ingestion authoring | POC §1.2 (1 of 3 ingestion source types). Lands when BH-590 + BH-592 are stable | Marwan + AI/ML |

---

## Block 7 — MCP/Okta (Gate D)

Mostly independent of Blocks 1–6. Defer to runbook Gate D unless Day-1 demo
explicitly requires Okta federation. Per multi-agent review (QA), recommended
to **descope Okta federation from Day-1 MCP demo** and use scoped service-account
JWT through default Cognito domain. Confirm with Grant on the call this week.

---

## Block 8 — Webapp Snowflake audit (BH-552)

Independent. `agentic-project-mgmt#19` already merged. Verify Snowflake
dropdown + form fields render correctly in webapp staging — sign off, close
ticket.

---

## Summary — top-of-stack action this week

1. **Marwan**: rebase `bb#488` to clear DIRTY (Block 1.1)
2. **Kuri**: address `pc#778` review feedback (Block 2 unblock)
3. **Marwan**: address `bb#490` review feedback (Block 3 unblock)
4. **Ahmed**: review `pc#777` + `data-organization-cdk#156` (Block 1.2 + 1.3)
5. **Kuri**: get Grant on a 30-min call (creds + MCP auth decision — gates Block 4 verify and Gate D scope)

Once Block 1 is on staging + verified, BrightAgent reads Snowflake. That's
the headline trial unblock and it can land **this week** if reviews move.
