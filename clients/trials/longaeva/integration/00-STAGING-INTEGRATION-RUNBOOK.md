---
title: "Longaeva — staging integration runbook"
audience: "Marwan, Ahmed, Harbour, Kuri"
purpose: "The auditable merge + deploy + verify order for all 21 PRs onto staging"
last_reviewed: "2026-06-05"
---

# Longaeva — staging integration runbook

> **What this is.** The ordered, gated sequence to get the five niches onto
> `develop`, promoted to `staging`, deployed, and verified. Each gate is
> independently checkable — work top to bottom, don't skip a gate's
> verification. If a gate fails, stop and fix before the next.
>
> **What this is NOT.** Not a deploy automation. Not a substitute for code
> review. The CHANGES_REQUESTED PRs (pc#778, bb#490) still need their reviews
> resolved by a human before merge — this runbook tells you the *order*, not
> permission to bypass review.

## Read before you start

- The full PR map + niche docs are in [`README.md`](README.md).
- **Current reality (2026-06-05):** 1 of 21 PRs merged (bb#497). Nothing in
  niches 1–4 is on `develop`. Two foundation PRs are CHANGES_REQUESTED; bb#488
  has a merge conflict. So this runbook is a *plan to execute*, not a record of
  what happened.
- **The 21-PR bundle is NOT the full trial scope.** It covers Layer A
  (Snowflake plumbing — 3 PRs), Layer C (GHE proxy delivery — 10 PRs), and
  Layer D (MCP/Okta — 7 PRs). **Layer B — the dbt engineering agent's actual
  authoring capability — is mostly NOT in this bundle.** See the new
  [**Gate A.5 — dbt agent authoring capability**](#gate-a5--dbt-agent-authoring-capability-layer-b)
  below; it tracks 5 tickets (BH-590…BH-594) that gate Sections 1, 2, and 4 of
  the POC scope and have ZERO PRs today.
- **Outstanding external blockers** (from [`../TRACKER.md`](../TRACKER.md)) that
  gate full verification — surface these in standup:
  - **GHE host URL + sandbox PAT + TLS chain** from Grant → Gate B step 3 + BH-593 can't
    run without them.
  - **MCP auth-workflow decision** (joint with Grant/Sumukh) → affects Gate D.

## How staging deploy works (so the gates make sense)

| Repo | Promote by | Deploy target | Trigger |
|---|---|---|---|
| brighthive-platform-core | merge `develop` → `staging` | Lambda / API Gateway, STAGE acct `873769991712` | **auto** on `staging` push |
| brightbot | merge `develop` → `staging` | LangGraph Cloud | **auto** on `staging` push |
| brighthive-webapp | merge `develop` → `staging` | Amplify (`d1dk6ngojdo9gg`, MAIN acct) | webhook (manual trigger) |
| platform-core **CDK** (Cognito #784, DNS #790) | n/a — CDK | `cdk deploy` per env | **manual**, per AWS account |

> Two of the niche-5 PRs (#784 Cognito, #790 DNS) are **CDK**, not Lambda code.
> Merging to `staging` does **not** deploy them — someone runs `cdk deploy` with
> the right profile. Build that into Gate D.

## Branch / merge discipline (per team rules)

- Stacked PRs collapse onto their parent's branch, then the parent merges to
  `develop` via **squash**. Never merge the stacked children directly to
  `develop`.
- One-directional flow only: `feature → develop → staging`. **Never** merge
  `staging` back into `develop` (see memory `feedback_no_backward_merge`).
- Order of operations per niche is in each gate below.

---

## Gate A — Snowflake / BYOW

**Niche doc:** [`01-snowflake-byow.md`](01-snowflake-byow.md) · **PRs:** `bb#488`, `pc#777`, `data-organization-cdk#156`, `bb#489`

**Independent of every other gate.** Can run in parallel with B/C/D.

> **Reality (2026-06-05):** all 4 PRs **built and tested**, 168 unit tests
> green. Gating action is review approve → squash merge → deploy → drop a
> Snowflake secret into `workspace_secret_store/{longaeva-workspace-uuid}`
> with `type=SNOWFLAKE`. See `01-snowflake-byow.md` "What is truly built
> today" for the layer breakdown.

### Merge order
1. **Clear bb#488's conflict** — rebase onto current `develop`, resolve
   (`uv.lock` + `warehouse.py`), get review, squash-merge to `develop`.
2. Squash-merge **pc#777** (Layer 3 OMD ingestion source config) to `develop`.
3. Squash-merge **data-organization-cdk#156** (Layer 7 org-CDK
   `workspace_secret_store` migration) to `develop`.
4. Squash-merge **bb#489** (Atlas YAML scaffold tool, BH-531). Note: tool
   exists but is **orphaned** until BH-591 wires it into the dbt_agent
   registry — see Gate A.5.
5. Promote all 3 repos `develop` → `staging`.
6. Drop the Snowflake secret into `workspace_secret_store/{workspace-uuid}`
   with `type=SNOWFLAKE`.

### Verify on staging (OneTen workspace first)
- [ ] Configure a staging workspace with the synthetic Snowflake secret:
      `username`, `password`, `account`, `warehouse` (console
      https://app.snowflake.com/bfddsko/dua97555/).
- [ ] BrightBot connects — **no** `ValueError: Unknown warehouse type: snowflake`.
- [ ] OMD ingestion lambda pulls the Snowflake catalog → tables appear in the
      workspace.
- [ ] BrightBot generates a Snowflake-dialect SELECT (uses `LIMIT`, ANSI
      double-quotes — not `TOP`/brackets).
- [ ] A write statement (`DELETE`/`UPDATE`/`INSERT`/`DROP`) is **rejected** by
      `assert_read_only_sql`.
- [ ] (if #489) Atlas scaffold YAML validates against the Atlas SDK for one
      Silver table.

---

## Gate A.5 — dbt agent authoring capability (Layer B)

**Not in the 21-PR bundle. Five tickets, zero open PRs today. This gate exists
because Gate A only gives BrightHive *connectivity* to Snowflake — it does NOT
give the dbt engineering agent the ability to author the artifacts the trial
demands.**

**Tickets:** BH-590 (GAP-2), BH-591 (GAP-3b), BH-592 (GAP-4), BH-594 (GAP-9).
BH-593 (GAP-5, GHE base_url) overlaps with Gate B but is independent of the
proxy PRs.

**Why this gate is separate from A and B:**

| Layer | What it gives the trial | In the 21-PR bundle? |
|---|---|---|
| A — Snowflake plumbing | BrightBot can connect, SELECT, introspect | Yes (bb#488, pc#777, bb#489) |
| **A.5 — dbt agent authoring** | **Agent can author dbt sources, staging models, schema.yml tests, Atlas YAML — the actual POC §1 + §2 capabilities** | **No (5 tickets, 0 PRs)** |
| B/C — GHE proxy + dbt PR delivery | Agent's output reaches Longaeva's GHE repo without PAT leak | Partial (10 PRs, 0 merged) |

### Critical dependencies (block POC §1 + §2 demos)

| # | Ticket | What it unblocks | Depends on |
|---|---|---|---|
| 1 | **BH-590** (GAP-2) Snowflake `INFORMATION_SCHEMA` introspection → BH metadata model | Every Layer-B capability — agent needs to *see* Snowflake tables before it can author against them | bb#488 (Layer A) on develop |
| 2 | **BH-591** (GAP-3b) Wire `scaffold_atlas_semantic_view_tool` into dbt_agent registry + LLM enrichment prompt | POC §2 (Snowflake semantic view enrollment — the headline trial capability) | bb#489 (BH-531) lands; BH-590 lands |
| 3 | **BH-592** (GAP-4) Generate dbt `sources.yml` + staging model from introspected Silver table | POC §1.1 (S3 vendor) + §1.3 (Snowflake Data Share) — 2 of 3 ingestion source types | BH-590 |
| 4 | **BH-594** (GAP-9) Infer dbt `schema.yml` tests (`not_null`/`unique`/`accepted_values`) from introspected schema | POC §4.2 (rapid DQ test construction) | BH-590, BH-592 |

**BH-593** (GAP-5, GHE `base_url`) sits *between* this gate and Gate B — it's a
1-day config thread-through that gates every PR creation regardless of whether
the proxy work has landed. Land it on the same branch as the proxy code, but
don't let the proxy review timeline block it.

### Verify on staging (per ticket)

- [ ] **BH-590**: introspect `LONGAEVA_POC.*`; agent's metadata view shows the
      16 sandbox tables, 2 stages, 1 semantic view.
- [ ] **BH-591**: user says "scaffold a semantic view for
      `LONGAEVA_POC.SILVER.int_enriched_holdings`" → agent calls the tool, LLM
      enriches `custom_instructions` + `verified_queries`, at least one
      `verified_query` round-trips through `SEMANTIC_VIEW(...)` against
      Snowflake.
- [ ] **BH-592**: agent generates `sources.yml` + `stg_<table>.sql` for a
      Snowflake Data Share table; `dbt parse` succeeds; output structurally
      equivalent to `sandbox/dbt/models/staging/stg_vendor_security_master.sql`.
- [ ] **BH-594**: generated `schema.yml` tests pass against live data; scaffold
      report flags inferred-vs-grounded.
- [ ] **BH-593**: workspace with `ghe_base_url` set routes PR creation to GHE,
      not github.com.

### Honesty note

This gate has **no merge order** because nothing exists to merge. It's a
sequencing gate for *future PR work* that must land before the trial's
headline use cases (POC §1, §2, §4) can be demoed. If the trial starts before
these land, those sections are not demoable end-to-end — only sandbox stand-ins
work.

---

## Gate B — GitHub Enterprise proxy (foundation)

**Niche doc:** [`02-github-enterprise-proxy.md`](02-github-enterprise-proxy.md) · **PRs:** pc#778 (+#780), then bb#490 (+#492)

**This gate has the one hard cross-repo ordering rule in the whole bundle:
platform-core must deploy to staging _before_ brightbot can be tested.**

### Merge order — platform-core first
1. Resolve pc#778's **CHANGES_REQUESTED** review.
2. Merge the P0 fix **pc#780** (tenant gate) into #778's branch.
   *(Niche-3 hardening pc#781/#782/#783 collapse here too — see Gate C; you can
   bundle them into the same #778 merge if all reviews are clear.)*
3. Squash-merge **pc#778** (now carrying #780) to `develop`.
4. Promote platform-core `develop` → `staging`; confirm auto-deploy succeeded.

### Then — brightbot
5. Resolve bb#490's **CHANGES_REQUESTED** review.
6. Merge P0 **bb#492** (log redaction) into #490's branch.
   *(Niche-3 bb#493/#494/#496 and Niche-4 bb#495 also collapse onto #490's
   branch — see Gates C/E.)*
7. Squash-merge **bb#490** to `develop`; promote `develop` → `staging`
   (LangGraph Cloud auto-deploy).

### Verify on staging
- [ ] All 7 proxy mutations resolve against github.com.
- [ ] **Tenant isolation (P0):** workspace-A JWT calling `readGitHubFile` with
      `workspaceId=B` → `ForbiddenError`; with `workspaceId=A` → success.
- [ ] **GHE routing:** `base_url` env var routes a call to the self-hosted
      instance. ⛔ **Blocked on Grant's GHE host URL + PAT + TLS chain.**
- [ ] **PAT containment:** a full dbt run (explore→commit→PR) through the proxy
      shows **no `github_pat`** in agent state or LangSmith traces.
- [ ] **Log redaction (P0):** grep staging CloudWatch for `Bearer `, `ghp_`,
      `github_pat_` on Platform Core calls → none.

---

## Gate C — dbt proxy hardening + correctness

**Niche doc:** [`03-dbt-github-proxy-migration.md`](03-dbt-github-proxy-migration.md) · **PRs:** pc#781/#782/#783, bb#493/#494/#496

These collapse onto the **same two branches** as Gate B. Sequence within:

### platform-core (onto #778's branch, before the #778 squash in Gate B step 3)
- pc#781 (redirect strip, P0), pc#782 (errorCode/truncated), pc#783 (URL tests +
  trailing-slash bug). Mutually independent — any order.

### brightbot (onto #490's branch, before the #490 squash in Gate B step 7)
- bb#494 **first** (Pydantic models + injectable client), **then** bb#496
  (super_agent proxy path — imports #494's modules). bb#493 (docs) anytime.

### Verify on staging
- [ ] `mapErrorCode` returns the right code for 401 / 403 / 404 / 422 (force a
      call against a missing repo and a bad branch).
- [ ] `truncated: true` returned when a file exceeds the char cap (commit a
      >20k-char file, read it back via the proxy).
- [ ] super_agent dbt run **with** `transformation_service_id` set → PR created
      via the proxy; grep state + traces for `ghp_`/`github_pat` → none.
- [ ] super_agent run **without** `transformation_service_id` → still works via
      the legacy path (backwards-compat until BH-568).

---

## Gate E — dead code removal (verify-only)

**Niche doc:** [`04-dead-code-removal.md`](04-dead-code-removal.md) · **PR:** bb#495

Collapses onto #490's branch (Gate B). It's a pure deletion of unreferenced
code — no behavior change expected.

### Verify
- [ ] After the bb#490 squash to `develop`, the dbt agent and super_agent both
      start and run (imports resolve) on staging.
- [ ] `tests/unit/tools/test_no_dead_pygithub_modules.py` green in CI.
- [ ] **Do not** claim "PyGithub removed from BrightBot" — it's still imported by
      super_agent's legacy path (BH-568). Only the 4 dead modules are gone.

> Gate ordered after C because both ride #490's branch; verify together.

---

## Gate D — MCP + Okta federation

**Niche doc:** [`05-mcp-okta-federation.md`](05-mcp-okta-federation.md) · **PRs:** bb#497 (merged), pc#784 (+#788/#789/#790), wa#1132, bb#501

**Mostly independent of A/B/C.** bb#497 is already merged but non-functional
until Layer 1 deploys.

### Merge order — platform-core
1. Resolve pc#784 review; squash-merge **pc#784** (Cognito clients + Okta hook)
   to `develop`.
2. Merge stacked **pc#788** (Okta runbook, docs), **pc#789** (DCR spec, docs)
   — these are docs/specs, low risk.
3. Squash-merge **pc#790** (DNS CDK) — must land for the custom domain to attach.
4. Promote platform-core `develop` → `staging`.

### Deploy the CDK (manual — not covered by the staging auto-deploy)
5. `cdk deploy` the **DnsStack** (pc#790) for staging → grab the
   `AuthZoneNameservers` / `McpZoneNameservers` outputs.
6. **Cloudflare:** add the NS delegation records for `auth.staging.brighthive.io`
   + `mcp.staging.brighthive.io` (one-time, per the
   `MCP_DNS_DEPLOYMENT_RUNBOOK.md`). Wait for ACM validation.
7. `cdk deploy` the **UserPoolStack** (pc#784) with the cert/zone/fqdn wired →
   Cognito custom domain attaches.

### Docs / specs (merge anytime, not gating)
8. **bb#501** (cross-link MCP docs) → `develop`.
9. **wa#1132** (webapp MCP UI **spec**) → `develop`. *Spec only — the UI
   implementation is a future PR, NOT part of this integration test.*

### Verify on staging
- [ ] Cognito resource server + 4 scopes + 2 app clients exist.
- [ ] pre-token-gen Lambda maps a federated Okta `org` claim →
      `custom:workspace_id` in an issued staging token.
- [ ] `auth.staging.brighthive.io` + `mcp.staging.brighthive.io` resolve; ACM
      cert valid; Cognito custom domain attached.
- [ ] `GET mcp.staging.brighthive.io/.well-known/oauth-protected-resource` → 200.
- [ ] Unauthenticated `tools/list` → 401 with `WWW-Authenticate` pointing at the
      real `auth.staging…` issuer.
- [ ] Authenticated `ping` returns the principal's `workspace_id`.
- [ ] Two-tenant: same tool, two workspace JWTs → workspace-scoped results
      differ.

---

## Final integration-test checklist (the few-hours session)

Run after all gates pass. This is the "is the trial ready" readout.

| # | Check | Gate | Owner |
|---|---|---|---|
| 1 | Snowflake workspace connects + read-only enforced | A | |
| 2 | OMD ingests Snowflake catalog | A | |
| 3 | **Agent introspects Snowflake → BH metadata model populated (BH-590)** | **A.5** | |
| 4 | **Atlas YAML scaffold tool invoked via agent + LLM enrichment + verified_query round-trips (BH-591)** | **A.5** | |
| 5 | **Agent generates `sources.yml` + staging model from Silver table; `dbt parse` passes (BH-592)** | **A.5** | |
| 6 | **Generated `schema.yml` tests pass against live data (BH-594)** | **A.5** | |
| 7 | Proxy tenant isolation rejects cross-workspace | B | |
| 8 | GHE `base_url` routing works (needs Grant's creds; BH-593) | B / A.5 | |
| 9 | dbt run leaves no PAT in state/traces | B+C | |
| 10 | super_agent PR via proxy (with TSID) | C | |
| 11 | No-regression after dead-code deletion | E | |
| 12 | MCP endpoint live + authenticated + tenant-scoped | D | |
| 13 | Okta federation maps to workspace_id | D | |

> **Honesty gate for the readout:** mark a row green only when verified on
> staging. "PR merged" ≠ "deployed" ≠ "verified". Per
> `feedback_pr_state_honesty`, don't report intended behavior as shipped.

## Sign-off

- [ ] All gates verified on **OneTen** (dev sandbox) first.
- [ ] Promote to **DemoEnv** only after OneTen is clean (per
      `project_staging_environments`).
- [ ] TRACKER blockers resolved or explicitly accepted.
