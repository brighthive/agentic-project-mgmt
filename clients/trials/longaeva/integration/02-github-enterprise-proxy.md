---
title: "Niche 2 — GitHub Enterprise proxy foundation"
epic: "BH-529"
prs: ["brighthive-platform-core#778", "brighthive-platform-core#780", "brightbot#490", "brightbot#492"]
last_reviewed: "2026-06-05"
---

# Niche 2 — GitHub Enterprise proxy foundation

> **One-line intent:** route every GitHub operation through Platform Core
> (server-side) instead of letting the BrightBot agent hold a GitHub PAT — and
> make that proxy work against **GitHub Enterprise** (self-hosted), which is
> what Longaeva runs.

## Why this niche exists

Longaeva runs GitHub Enterprise (GHE), not github.com. Two problems:

1. **GHE routing** — the dbt agent's GitHub calls must hit the customer's
   `ghe.example.com`, not `api.github.com`. That means a configurable
   `base_url`.
2. **PAT blast radius** — previously the PAT lived in BrightBot agent state /
   logs / Lambda memory. Anything that reads agent state could exfiltrate it.
   The fix: the PAT lives **only** in Platform Core, and BrightBot calls
   GraphQL mutations with its workspace JWT.

This is the **foundation** half of the BH-529 work. The agent-side consumption
and the dbt-specific migration are split into Niche 3.

> **Niche 2 vs Niche 3:** the original ticket grouping the user gave splits
> "GitHub enterprise PRs" (#490, #492, #778, #780) from "DBT OAuth migration"
> (#493, #494, #496, #781, #782, #783). In the **code**, all of these are one
> stacked chain per repo. This doc covers the foundation PRs; the follow-on
> hardening + dbt wiring is in [Niche 3](03-dbt-github-proxy-migration.md). Read
> both before integrating — they merge together.

## The stacking topology (critical)

```
platform-core:  develop ◄── pc#778  (GHE proxy: 7 GraphQL mutations)
                              ├── pc#780  @authorized tenant gate   (P0, Niche 2)
                              ├── pc#781  redirect strip + scrub     (P0, Niche 3 doc)
                              ├── pc#782  errorCode + truncated flag (Niche 3 doc)
                              └── pc#783  30 URL-parser tests + bug  (Niche 3 doc)

brightbot:      develop ◄── bb#490  (consume the 7 mutations, drop PyGithub)
                              ├── bb#492  redact JWT/PAT from logs   (P0, Niche 2)
                              ├── bb#493  migration guide (docs)     (Niche 3 doc)
                              ├── bb#494  Pydantic + injectable client (Niche 3 doc)
                              ├── bb#495  delete dead modules        (Niche 4)
                              └── bb#496  super_agent proxy path     (Niche 3 doc)
```

**Hard cross-repo gate:** bb#490 calls the 7 mutations that pc#778 defines. You
**cannot** integration-test bb#490 until pc#778 (with its stacked fixes) is
**deployed to staging platform-core**. See runbook Gate B.

## PRs in this niche

### `brighthive-platform-core#778` — GitHub proxy with GHE support (BH-529)

- **State:** OPEN · **CHANGES_REQUESTED** (senior review blocked merge; the
  stacked fixes #780–#783 exist to clear those blockers)
- **Scope (+3692 / −0, 9 files):**
  - `src/graphql/service/github/github-proxy.ts` — all git ops via Octokit with
    optional GHE `base_url`
  - 7 GraphQL mutations: `readGitHubFile`, `listGitHubFiles`,
    `listGitHubBranches`, `createGitHubBranch`, `commitGitHubFiles`,
    `createGitHubPR`, `mergeGitHubPR`
  - typedefs + resolvers + transformation-service model
  - `docs/BRIGHTBOT-GITHUB-PROXY-GUIDE.md`
- **Security boundary:** PAT read server-side only, never returned to BrightBot.

### `brighthive-platform-core#780` — @authorized tenant gate (BH-559) — P0

- **State:** OPEN · draft · base = `feat/BH-529-…` (stacked on #778)
- **Why P0:** the shipped #778 mutations had only `@authenticated`. The tenant
  check compared `input.workspaceId` (client-supplied) to the service's
  `workspace.id` — **both client-controlled, trivially bypassed**. Any user with
  a valid JWT for workspace A could pass `workspaceId: B` and reach B's
  PAT-mediated GitHub. **Multi-tenant data-exfiltration vector.**
- **Fix (+35 / −7, 1 file):** apply the existing `@authorized(requires:
  WORKSPACE_CONTRIBUTOR, workspaceIdLoc: ["args","input","workspaceId"])`
  directive to all 7 mutations — the same directive every other GitHub mutation
  already uses. CONTRIBUTOR (not ADMIN) so collaborators can still invoke the
  dbt agent.
- **Sequencing:** targets #778's branch so it merges *into* #778 before #778
  lands — closes the P0 without a revert.

### `brightbot#490` — consume the proxy, remove PyGithub from dbt_agent (BH-529)

- **State:** OPEN · **CHANGES_REQUESTED**
- **Scope (+1000 / −904, 15 files):**
  - Rewrites all 8 `dbt_agent` GitHub LangChain tools to call Platform Core
    GraphQL mutations instead of PyGithub directly
  - Removes the GitHub PAT from agent state, logs, and Lambda memory — auth is
    now workspace JWT only
  - `brightbot/tools/platform_queries.py` — **NEW**, the 7 mutations client-side
  - `github_merge_pull_request` now takes `pr_number (int)` not `pr_url (str)`
- **Test plan (from PR, unchecked):** full dbt run (explore→modify→PR) against a
  GHE instance; no `github_pat` in agent state or LangSmith traces; all 7
  mutations return expected responses.
- ⚠️ This PR's body claims a 342-line migration guide that **wasn't shipped in
  #490** — it's actually delivered by **bb#493** (Niche 3). The CodeRabbit/Claude
  attribution lines in the body are noise; ignore.

### `brightbot#492` — redact JWT + PAT from logs (BH-563) — P0

- **State:** OPEN · draft · base = `BH-529-…` (stacked on #490)
- **Why P0:** `brightbot/tools/bh_platform_api.py` logged the full
  `requests.Session` (Authorization: Bearer header) + payload at INFO on every
  Platform Core call (sync + async paths). **Streams JWTs to CloudWatch.**
- **Fix (+198 / −24, 2 files):** one-line POST log carrying URL + variable
  *keys* (not values); `_scrub_tokens()` strips `Bearer`, `ghp_*`, `ghs_*`,
  `github_pat_*`; `_redact()` masks sensitive keys at any depth; all exception
  logs scrubbed. 11 unit tests.

## P0 security inventory for this niche

| PR | P0 | Risk if not merged |
|---|---|---|
| pc#780 | BH-559 | Cross-tenant GitHub access via forged `workspaceId` |
| bb#492 | BH-563 | JWT leaked to CloudWatch on every Platform Core call |

Both are **required before staging exposure**. The proxy is worse than the old
path until #780 lands (it adds a forge-able tenant param).

## Staging verification

See [runbook Gate B](00-STAGING-INTEGRATION-RUNBOOK.md#gate-b--github-enterprise-proxy).
Short form:

1. pc#778 + #780 deployed to staging; the 7 mutations resolve.
2. Tenant test: workspace-A JWT calling `readGitHubFile` with `workspaceId=B`
   → `ForbiddenError`; with `workspaceId=A` → success.
3. GHE routing: `base_url` env var routes a `readGitHubFile` to the self-hosted
   instance (needs Longaeva GHE host URL + sandbox PAT — **outstanding from
   Grant**, see TRACKER blockers).
4. bb#490 deployed; a dbt agent run does explore→commit→PR through the proxy
   with **no `github_pat` in agent state or traces**.

## Out of scope / known follow-ups

- Integration tests for #778 mutations + schema snapshot — deferred (Niche 3
  #783 adds the URL-parser unit tests; full mutation integration tests need
  `nock`/`msw`).
- super_agent's PyGithub path — Niche 3 #496 + BH-568.

## References

- Epic: [BH-529](https://brighthiveio.atlassian.net/browse/BH-529)
- Cross-repo spec: `agentic-project-mgmt/docs/specs/github-enterprise-host-config.md` (§11 implementation gaps)
- Smoke test plan: [`../artifacts/ghe-smoke-test-plan.md`](../artifacts/ghe-smoke-test-plan.md)
- Migration guide (shipped by bb#493): `brightbot/docs/BRIGHTBOT-GITHUB-PROXY-GUIDE.md`
