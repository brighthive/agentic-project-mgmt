---
title: "Longaeva integration — source of truth"
audience: "Marwan, Ahmed, Harbour, Kuri"
purpose: "One auditable map of the 21 PRs we must merge + deploy to staging for the Longaeva trial"
last_reviewed: "2026-06-04"
---

# Longaeva integration — source of truth

> **Read this first.** The trial needs five workstreams ("niches") landed on
> `develop` and deployed to **staging** before integration testing. This folder
> is the single map of *what each PR does*, *what depends on what*, and *how to
> verify it in staging*. The team will sit with these docs for a few hours and
> drive the integration test from them.

## How to use this folder

| Doc | What it gives you |
|---|---|
| [`00-STAGING-INTEGRATION-RUNBOOK.md`](00-STAGING-INTEGRATION-RUNBOOK.md) | **The merge + deploy order.** Cross-repo dependency gates, what to merge in what sequence, and the staging smoke test per gate. Start here when you're ready to integrate. |
| [`01-snowflake-byow.md`](01-snowflake-byow.md) | Niche 1 — Snowflake connector / Bring-Your-Own-Warehouse. PRs #488, #489, #777. |
| [`02-github-enterprise-proxy.md`](02-github-enterprise-proxy.md) | Niche 2 — GitHub Enterprise proxy foundation. PRs #490, #492, #778, #780. |
| [`03-dbt-github-proxy-migration.md`](03-dbt-github-proxy-migration.md) | Niche 3 — Moving dbt GitHub ops off the agent (PAT off the boundary). PRs #493, #494, #496, #781, #782, #783. |
| [`04-dead-code-removal.md`](04-dead-code-removal.md) | Niche 4 — Deleting the dead PyGithub surface. PR #495. |
| [`05-mcp-okta-federation.md`](05-mcp-okta-federation.md) | Niche 5 — Remote MCP server + Cognito/Okta federation. PRs #497, #501, #784, #788, #789, #790, #1132. |

## Glossary (load-bearing terms)

| Term | Meaning |
|---|---|
| **BYOW** | Bring Your Own Warehouse — customer points BrightHive at their own Snowflake/Synapse/Redshift instead of a BrightHive-hosted warehouse. |
| **Proxy / GitHub proxy** | Platform Core GraphQL mutations that perform GitHub operations server-side, so the GitHub PAT never enters the BrightBot agent process. |
| **GHE** | GitHub Enterprise (self-hosted GitHub). Longaeva runs GHE, hence the `base_url` routing work. |
| **PAT** | GitHub Personal Access Token — the credential we are getting *off* the agent boundary. |
| **MCP** | Model Context Protocol — the standard third-party clients (Claude.ai, Cursor, Claude Code) use to call BrightHive capabilities. |
| **Two-layer auth** | Layer 1 = tenant (Cognito federated to customer Okta); Layer 2 = user (bearer JWT validated per MCP call). |
| **DCR** | Dynamic Client Registration (RFC 7591) — MCP clients self-register instead of a manual CDK PR per integration. |
| **Atlas** | Longaeva's metric-store contract; semantic-view YAML that drives Snowflake DDL + agent context. |
| **Niche** | One of the five workstreams below. The team's mental grouping — note it does **not** always equal the merge-dependency chain (see runbook). |

## PR inventory (21 PRs across 4 repos)

State as of **2026-06-04**. `bb` = brightbot, `pc` = brighthive-platform-core, `wa` = brighthive-webapp.

| # | Repo | PR | Niche | State | Review | Base branch |
|---|---|---|---|---|---|---|
| 1 | bb | [#488](https://github.com/brighthive/brightbot/pull/488) | 1 Snowflake | OPEN | REVIEW_REQUIRED · **DIRTY (conflict)** | `develop` |
| 2 | bb | [#489](https://github.com/brighthive/brightbot/pull/489) | 1 Snowflake | OPEN · draft | — | `develop` |
| 3 | pc | [#777](https://github.com/brighthive/brighthive-platform-core/pull/777) | 1 Snowflake | OPEN | REVIEW_REQUIRED | `develop` |
| 4 | pc | [#778](https://github.com/brighthive/brighthive-platform-core/pull/778) | 2 GHE proxy | OPEN | **CHANGES_REQUESTED** | `develop` |
| 5 | pc | [#780](https://github.com/brighthive/brighthive-platform-core/pull/780) | 2 GHE proxy | OPEN · draft | — | `feat/BH-529-…` (#778) |
| 6 | bb | [#490](https://github.com/brighthive/brightbot/pull/490) | 2 GHE proxy | OPEN | **CHANGES_REQUESTED** | `develop` |
| 7 | bb | [#492](https://github.com/brighthive/brightbot/pull/492) | 2 GHE proxy | OPEN · draft | — | `BH-529-…` (#490) |
| 8 | pc | [#781](https://github.com/brighthive/brighthive-platform-core/pull/781) | 3 dbt migration | OPEN · draft | — | `feat/BH-529-…` (#778) |
| 9 | pc | [#782](https://github.com/brighthive/brighthive-platform-core/pull/782) | 3 dbt migration | OPEN · draft | — | `feat/BH-529-…` (#778) |
| 10 | pc | [#783](https://github.com/brighthive/brighthive-platform-core/pull/783) | 3 dbt migration | OPEN · draft | — | `feat/BH-529-…` (#778) |
| 11 | bb | [#493](https://github.com/brighthive/brightbot/pull/493) | 3 dbt migration | OPEN · draft | — | `BH-529-…` (#490) |
| 12 | bb | [#494](https://github.com/brighthive/brightbot/pull/494) | 3 dbt migration | OPEN · draft | — | `BH-529-…` (#490) |
| 13 | bb | [#496](https://github.com/brighthive/brightbot/pull/496) | 3 dbt migration | OPEN · draft | — | `BH-529-…` (#490) |
| 14 | bb | [#495](https://github.com/brighthive/brightbot/pull/495) | 4 dead code | OPEN · draft | — | `BH-529-…` (#490) |
| 15 | bb | [#497](https://github.com/brighthive/brightbot/pull/497) | 5 MCP/Okta | **MERGED** ✅ | — | `develop` |
| 16 | pc | [#784](https://github.com/brighthive/brighthive-platform-core/pull/784) | 5 MCP/Okta | OPEN · draft | REVIEW_REQUIRED | `develop` |
| 17 | pc | [#788](https://github.com/brighthive/brighthive-platform-core/pull/788) | 5 MCP/Okta | OPEN · draft | — | `…/BH-573` (#784) |
| 18 | pc | [#789](https://github.com/brighthive/brighthive-platform-core/pull/789) | 5 MCP/Okta | OPEN · draft | — | `…/BH-573` (#784) |
| 19 | pc | [#790](https://github.com/brighthive/brighthive-platform-core/pull/790) | 5 MCP/Okta | OPEN · draft | — | `…/BH-573` (#784) |
| 20 | wa | [#1132](https://github.com/brighthive/brighthive-webapp/pull/1132) | 5 MCP/Okta | OPEN · draft | REVIEW_REQUIRED | `develop` |
| 21 | bb | [#501](https://github.com/brighthive/brightbot/pull/501) | 5 MCP/Okta | OPEN · draft | — | `develop` |

> **Honesty note.** Of 21 PRs, **1 is merged** (bb#497). The rest are open;
> most are draft and stacked on a parent branch, not on `develop` directly. Two
> foundation PRs (pc#778, bb#490) are **CHANGES_REQUESTED**, and bb#488 has a
> **merge conflict (DIRTY)**. Nothing in niches 1–4 is on `develop` yet. Treat
> every "Shipped" claim in an individual PR body as *intended*, not *landed*,
> until the runbook gate confirms it.

## The dependency reality (why niche ≠ merge order)

The team thinks in five niches. The **merge graph** cuts across them:

```
                    ┌─────────────────────────────────────────┐
   NICHE 1          │ pc#777 ── bb#488 ── bb#489  (independent) │
   Snowflake        └─────────────────────────────────────────┘
                              (no cross-deps; bb#488 has a conflict to clear)

   NICHE 2 + 3      pc#778  (GHE proxy foundation, base develop)
   are ONE chain      ├── pc#780  tenant isolation     (P0)
   in platform-core   ├── pc#781  redirect strip        (P0)
                      ├── pc#782  errorCode + truncated
                      └── pc#783  30 URL-parser tests + bug fix
                            │
                            ▼ (must be DEPLOYED to staging first)
                    bb#490  (consume proxy, base develop)
                      ├── bb#492  redact JWT/PAT logs    (P0)
                      ├── bb#493  proxy migration guide (docs)
                      ├── bb#494  Pydantic + injectable client
                      ├── bb#495  delete 4 dead modules  → NICHE 4
                      └── bb#496  super_agent proxy path

   NICHE 5          bb#497  MERGED ✅  (MCP server, Layer-2 user auth)
   MCP/Okta         pc#784  Cognito clients + Okta hook (Layer-1, base develop)
                      ├── pc#788  Okta onboarding runbook (docs)
                      ├── pc#789  DCR mutation SPEC       (docs)
                      └── pc#790  CDK DNS stack (auth./mcp.brighthive.io)
                    wa#1132  webapp MCP UI SPEC (docs, base develop)
                    bb#501   cross-link MCP docs (docs, base develop)
```

**The single most important cross-repo gate:** bb#490 cannot be integration-tested
until pc#778's 7 mutations are **live in staging platform-core**. See the runbook.
