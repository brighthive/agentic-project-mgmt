---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "trial"
title: "Longaeva PoC — UAT Success Guide"
audience: "BrightHive (all teams) + Longaeva (Grant, Corinne, analysts)"
purpose: "Anyone in either company can run UAT, log a verdict, and move the scorecard."
trial_start: "2026-06-15"
last_reviewed: "2026-06-17"
notion_page: "TBD — mirror this file under the Longaeva GTM page"
---

# Longaeva PoC — UAT Success Guide

> **You do not need to be an engineer to run this.** If you can chat in Slack, open a webapp, and write a sentence in Notion, you can run UAT. The trial wins or loses on how many of the scenarios below come back ✅ from real human testers across both companies.

## TL;DR

| | |
|---|---|
| **What we're testing** | Does BrightAgent actually do the four things Longaeva is paying for: ingest data, enroll semantic views, validate via MCP, and self-maintain? |
| **Who tests** | Everyone at BrightHive (eng, sales, exec, ops). Grant + any Longaeva analyst Grant invites. |
| **How long per session** | 20–30 minutes per scenario. Pick one; you don't have to do all. |
| **Where you test** | Slack (BrightAgent) + the BrightHive webapp (staging). Both pre-configured against the `LONGAEVA_POC` Snowflake. |
| **Where feedback goes** | The **UAT Feedback** Notion database on the Longaeva GTM page. One row per scenario per tester. |
| **Honest state (cycle-21)** | ~55% of golden cases are fully live (up from 27% as of cycle-19), ~25% partial, ~20% intentionally out-of-scope for this trial window. Longitudinal monitoring + BrightSignals push went live since the last audit. We tell you which is which up front — no green-washing. |
| **Warehouse object names** | All UAT prompts reference **real** `LONGAEVA_POC` Snowflake objects (verified 2026-06-24): `GOLD.MART_DAILY_PORTFOLIO_EXPOSURE` (174,384 rows), `GOLD.MART_WEEKLY_EXPOSURE_DELTA` (692), `REF.WATCHLIST` (60), `REF.IDENTIFIER_MAP` (200), `BRONZE.RAW_REST_HOLDINGS` (4,536), `SEMANTIC.SV_DAILY_PORTFOLIO_EXPOSURE`, `SV_WEEKLY_EXPOSURE_DELTA`, `SV_SECURITY_PRICES`. **Issuer names are synthetic** (`Synthetic Issuer 0000`–`0199`) — that's the seed by design, not a doc bug. |

---

## 1. Setup (one-time, 5 minutes)

### 🟦 For BrightHive testers

1. You're already in `brighthive.slack.com`. BrightAgent is the `@BrightBot` user.
2. Open a DM with `@BrightBot` or use any channel where it's installed.
3. The Longaeva workspace context loads automatically when your message resolves to the `OneTen` staging workspace (now pointed at `LONGAEVA_POC`).
4. Webapp: `https://staging.brighthive.io` — log in with Okta, switch workspace to **OneTen / Longaeva PoC**.

### 🟨 For Longaeva testers

1. Grant invites you to the shared `#longaeva-poc` Slack channel (hosted on BrightHive's Slack — no install needed on your side).
2. Chat with `@BrightBot` in that channel. Threads are isolated per tester.
3. Webapp access via Okta SSO using your Longaeva email. Grant has the invite link.
4. If you can't log in: ping `@kuri` in the channel and we fix within an hour.

> **Privacy note.** All UAT runs hit the `LONGAEVA_POC` Snowflake (your own data, your own warehouse). BrightHive logs prompts and tool calls for debugging — we do not log your warehouse rows.

---

## 2. The fourteen UAT scenarios

> Scenarios 1–13 are engineering acceptance. **Scenario 14 (the non-technical UAT) is the one a non-technical user can run cold** — analyst, ops, exec. See `NON_TECH_UAT.md` for the full bars.

Each scenario maps to a **golden case** in the PoC scorecard. Run any scenario in any order. **You do not have to be technical** — if your role lines up with the persona, just follow the prompt.

Legend: ✅ live · 🟡 partially live · 🔴 not in this window (we tell you what to expect)

### Scenario 1 — "Show me my semantic views" ✅

- **Persona**: data analyst, anyone curious
- **Maps to**: GC-6 (semantic view list) / Q1
- **What to do**: In Slack, ask BrightAgent:
  > *"What semantic views do I have in the Longaeva workspace?"*
- **Expected**: A list including `SV_DAILY_PORTFOLIO_EXPOSURE` with base tables and join graph.
- **Known caveat**: Names are surfaced via Atlas YAML, not Snowflake DDL — both are correct, just different shapes.

### Scenario 2 — "Show me the YAML for one of them" ✅

- **Persona**: data analyst, governance lead
- **Maps to**: GC-6 (semantic view read) / BH-633
- **What to do**: Follow up with:
  > *"Show me the YAML of SV_DAILY_PORTFOLIO_EXPOSURE"*
- **Expected**: Full byte-identical Atlas YAML with `atlas:*` tags, owners, dataset key, verified queries.
- **Why it matters**: Proves BrightHive preserves your contract — we don't reshape your governance metadata.

### Scenario 3 — "Open a PR with this semantic view" 🟡

- **Persona**: data engineer, dbt lead
- **Maps to**: GC-6 (lifecycle) / Q3 / BH-614
- **What to do** (webapp path, since no UI button yet — Slack works too):
  > *"Open a PR for SV_DAILY_PORTFOLIO_EXPOSURE against the longaeva-semantic-views repo"*
- **Expected**: Real GitHub PR opens within ~30 seconds against `github.com/brighthive/longaeva-semantic-views`. PR contains the YAML, no secrets leaked, idempotent on retry.
- **Caveat**: The auto-merge safety today is prompt-only (BH-645 filed for a code-level HITL gate). Don't request auto-merge in UAT unless you mean it.

### Scenario 4 — "QC this semantic view" ✅

- **Persona**: analyst, quality lead
- **Maps to**: GC-3 (Snowflake DQ) + Q4 / BH-622
- **What to do**:
  > *"Run QC on SV_DAILY_PORTFOLIO_EXPOSURE — row counts, nulls, freshness"*
- **Expected**: Live read-only report against the 174,384-row `GOLD.MART_DAILY_PORTFOLIO_EXPOSURE` + 3 REF upstream tables (`FISCAL_CALENDAR`, `GEO_CODES`, `IDENTIFIER_MAP`). Real findings, including the `IDENTIFIER_MAP.EFFECTIVE_TO` 100%-null flag (verified live via `qc_semantic_view_pipeline` MCP tool against staging on 2026-06-24).
- **What "good" looks like**: You see at least one *real* anomaly flagged. If everything reports clean, the test isn't useful — tell us in the feedback row.

### Scenario 5 — "Build me a dbt model from raw data" 🟡

- **Persona**: data engineer
- **Maps to**: GC-4 (silver time-series) / dbt agent
- **What to do**:
  > *"Build a dbt staging model from `BRONZE.RAW_REST_HOLDINGS` and open a PR"*
- **Expected**: dbt agent introspects schema, generates a staging model, opens a PR against the longaeva-dbt repo. Live verified end-to-end against `LONGAEVA_POC`.
- **Caveat**: Sometimes the `deep_agent` routes the question to memory instead of dbt — if your answer feels like a summary instead of a PR link, **that's the bug Marwan is fixing**. Log it. We need the data points.

### Scenario 6 — "Tell me when something breaks" 🟡

- **Persona**: ops lead, ML platform engineer
- **Maps to**: GC-12 (longitudinal monitoring) + Q5
- **What to do**: Subscribe to a table or semantic view, then wait for the nightly run:
  > *"Watch SV_DAILY_PORTFOLIO_EXPOSURE for anomalies — row counts, cardinality, null spikes, distributional drift"*
- **Expected**: Per-run metrics persist; trailing-window detection fires when a metric goes out-of-band; alert lands in your Slack channel.
- **State as of cycle-21**: longitudinal monitoring **live** — all 4 anomaly families (row-count drift, cardinality, distributional skew, null spike) detect in production. Scheduler is wired via EventBridge.
- **What we still want to validate**: noise calibration. We'd rather over-alert and tune down than miss a real signal. Tell us if you get a false positive.

### Scenario 7 — "Just chat with it like an analyst would" ✅

- **Persona**: anyone — sales, exec, marketing, finance
- **Maps to**: overall UX, trust calibration
- **What to do**: Ask any natural-language question about the Longaeva PoC data you'd ask a real analyst:
  - *"How many rows are in `GOLD.MART_DAILY_PORTFOLIO_EXPOSURE` for the last 30 days?"*
  - *"What's the largest position by exposure right now?"*
  - *"Which tables have an `EFFECTIVE_TO` column?"*
- **Expected**: Conversational answer with the SQL it ran, citations to the tables, honest "I don't know" when the data isn't there. **No hallucinations.**
- **What we want from you**: This is the trust scenario. If the answer feels wrong, even a little, flag it. We'd rather chase one false positive than miss one false negative.

---

## 3. How to log a verdict

For every scenario you run, add **one row** to the **UAT Feedback** Notion database on the Longaeva GTM page.

### Required columns

| Column | Example | Notes |
|---|---|---|
| **Scenario** | `2 — Show YAML` | Match the heading above |
| **Tester** | `Corinne (Longaeva)` | First name + company |
| **Date** | `2026-06-17` | When you ran it |
| **Verdict** | `✅ Met` / `🟡 Partial` / `🔴 Missed` / `⏸ Blocked` | Honest — see rubric below |
| **What you asked** | Verbatim prompt | Copy from Slack — we need the literal text |
| **What you got** | Paste of response (or screenshot link) | Truncate after ~500 chars; link a Slack permalink for the full thread |
| **Notes** | Free text | Surprise, friction, things you'd want differently |
| **Severity if missed** | `P0 blocker` / `P1 important` / `P2 nice` | Only fill if Verdict ≠ Met |

### Verdict rubric

- **✅ Met** — Did what you expected, you'd trust it in your day-to-day work.
- **🟡 Partial** — Got something usable but with caveats (wrong shape, missing field, slow, etc.). **Notes column mandatory.**
- **🔴 Missed** — Wrong answer, hallucination, error, or no answer at all. **This is the most valuable verdict — please be specific.**
- **⏸ Blocked** — Couldn't even start (login broken, BrightAgent down, etc.). Ping `@kuri` in Slack so we unblock fast.

> One scenario, one tester, one row. Re-run a scenario? New row. We want the time series, not the latest opinion.

---

## 4. What you should NOT expect to work this window

We are telling you this **before** you test so you don't waste a row on a known gap:

| Capability | State | Tracking |
|---|---|---|
| Auto-ingest from S3 / REST API / Snowflake Data Share | 🔴 Not in trial | GC-1, GC-2 — covered by BYOW spec, not in this PoC |
| Auto-generate gold marts | 🔴 Spec only | GC-5 — bb#513 spec, no impl yet |
| Reference-join resolution from KG | 🔴 Not built | GC-7 |
| MCP downstream query (calling tools from your IDE/agent) | 🟡 Auth + tools live; edge-case routing in flight | GC-9 / Scenario 8 |
| Self-healing pipeline PRs | 🔴 Approach spec only | GC-11 — `docs/specs/self-healing-pipelines.md` |
| Longitudinal anomaly detection | ✅ Live (cycle-21) — 4 anomaly families in prod | GC-12 / Scenario 6 |
| Slack-native bi-directional alerts (BrightSignals push) | ✅ Live (cycle-21) — wired to monitoring + PR events | GC-13 / Scenario 9 |
| Projects / BrightStudio (custom agent builder) | 🔴 Q2 epic, not in trial | BH-260 / Scenario 11 |

If you test one of these and it doesn't work, **that's expected**. Skip the row. The honest gap map lives in `clients/trials/longaeva/BRIGHTHIVE_GAPS.md`.

---

## 5. Sign-off

At the end of the trial window (or whenever we agree to call it), we tally the Notion DB:

- Count rows per Scenario × Verdict
- Compute weighted score: ✅ = 1.0, 🟡 = 0.5, 🔴/⏸ = 0
- Compare against the **success criteria** in `clients/trials/longaeva/artifacts/poc-response-plan.md §5`
- Post the result to `#engineering` + the Longaeva Notion page
- Joint decision call: **win / extend / pivot / part ways** — Grant + Kuri, on the books for Day 14

There is no hidden bar. The Notion DB is the bar. Every BrightHive employee and every Longaeva tester sees the same numbers.

---

## 6. Roles — who drives what

| Role | At BrightHive | At Longaeva |
|---|---|---|
| **UAT driver** | Kuri (`@kuri`) | Grant |
| **First responder for breakage** | Kuri → Marwan / Ahmed / Harbour by lane | Grant |
| **Test scenario owner** | One per scenario, see below | Any analyst Grant assigns |
| **Notion DB maintainer** | Kuri | — |

Scenario owners on the BrightHive side (so you know who to ping if something behaves weirdly):

| Scenario | BH owner | Why |
|---|---|---|
| 1, 2 — Semantic view read | Kuri | Shipped the read path BH-624 epic |
| 3 — PR pipeline | Marwan | Owns the orchestrator |
| 4 — QC | Marwan | Owns BH-622 |
| 5 — dbt model | Marwan | Owns dbt agent |
| 6 — Monitoring | Harbour | Longitudinal monitoring + nightshift scheduler |
| 7 — General chat | Kuri | Cross-cutting, trust calibration |
| 8 — MCP from IDE | Ahmed | Owns MCP server + Okta federation |
| 9 — Slack alerts (BrightSignals) | Harbour | Owns notifications layer |
| 10 — Memory + multi-turn | Kuri | Cross-cutting context engineering |
| 11 — Projects / BrightStudio | Harbour | Q2 epic owner (not in this trial) |
| 12 — RBAC | Ahmed | Owns Okta + tenant gate + role hierarchy |
| 13 — Governance | Kuri | PR orchestrator, audit trail, redaction |
| 14 — Non-technical UAT | Kuri | End-to-end product bar for non-technical users |

---

## 7. If something breaks

1. **Slack first**: post in `#longaeva-poc` with `@kuri` — fastest path, <1hr response in business hours.
2. **Severity P0** (nothing works, all UAT blocked): tag `@channel`. Triage within 15 min.
3. **Not sure if it's a bug**: log a `🔴 Missed` row with a `?` in Notes — we'll come back and reclassify.
4. **Customer-facing escalation**: Grant → Kuri direct (email/Slack DM). We do not surprise Grant with bugs on calls.

---

## 8. Where this guide lives

| Where | Why |
|---|---|
| **Source of truth**: `clients/trials/longaeva/UAT_GUIDE.md` (this file) | Versioned, reviewable, lives next to the scorecard |
| **Mirror**: Notion page under the Longaeva GTM section | Where Longaeva testers actually read it; sync after every edit |
| **Linked from**: `clients/trials/longaeva/scorecard.md`, `TEAM_GUIDE.md`, the Notion GTM page | One click from anywhere a tester might land |

**Updating**: edit this file in the repo, commit, then mirror to Notion. Do not edit the Notion copy and let the repo drift — repo is canonical.

---

## 10. Scenario 14 — Non-technical UAT ✅

**Persona**: any non-technical BrightAgent user — portfolio analyst, ops lead, exec. Slack + plain English only. No SQL, no platform terminology.

**Maps to**: end-to-end production bars for the non-technical user surface (positions + concentration + change + watchlist). Pulls from `SV_DAILY_PORTFOLIO_EXPOSURE` + `SV_WEEKLY_EXPOSURE_DELTA` + `REF.WATCHLIST`.

**Why this scenario exists**: scenarios 1–13 are engineering acceptance — schema, lineage, governance, monitoring. Scenario 14 is the contract for what BrightAgent must do for *any* non-technical user, every time. A jargon leak here is a P0.

**Full bars**: [`NON_TECH_UAT.md`](./NON_TECH_UAT.md).

### The five steps

For each step, tester says the prompt verbatim to `@BrightBot` and verifies the bar.

| # | Prompt | Pass bar | Fail signal |
|---|---|---|---|
| 1 | *"What are my top 10 positions today, ranked by dollar exposure?"* | Names + dollars + % reconcile within $1K of `SV_DAILY_PORTFOLIO_EXPOSURE` for latest `AS_OF_DATE` | Bot says "semantic view" / "Snowflake" / "mart" |
| 2 | *"Break those down by sector and by country — where is the concentration?"* | Two compact tables; percentages sum to 100% (±0.1%); callout matches table | Sums off; callout contradicts the table |
| 3 | *"What changed in the last week? Anything I should look at first?"* | Top-5 movers by absolute $ change; honest narrative sentence | "I don't have that data" (delta mart not wired); random-looking picks |
| 4 | *"Any of these names on a watchlist I should know about?"* | Every flagged issuer in `REF.WATCHLIST`; every unflagged NOT in it; reasons match the table | Bot invents reasons; misses flagged names |
| 5 | *"Send this to my PM as a summary."* | ≤ 200 words; Slack-formatted; copy-paste-ready; no engineer language | Walls of text; jargon leaks; >200 words |

### The hard prompt rule (jargon firewall)

In any of these five steps, if the bot uses *any* of these words in a user-facing reply, the test fails:

`semantic view` · `Snowflake` · `gold mart` · `mart` · `silver` · `bronze` · `MCP` · `deep_agent` · `subagent` · `database` · `query` · `SQL` · `Atlas` · `YAML` · `embedding` · `vector` · `Bedrock` · `LangGraph` · `agent loop`

The one allowed platform sentence — *only if the user asks "how did you know that?"* — is in `NON_TECH_UAT.md` under "The hard prompt rule".

### Tester verdict

Log to the **UAT Feedback** Notion DB (same as scenarios 1–13). Use scenario name `S14 — Non-tech UAT`. Verdict rubric is identical (✅ Met / 🟡 Partial / 🔴 Missed / ⏸ Blocked).

**One extra column** for this scenario: `Jargon leaked?` (Y/N). Any Y is a P0 — file under [BH-744](https://brighthiveio.atlassian.net/browse/BH-744), do not continue the test.

---

## Appendix — the six analyst questions, verbatim

These came from Grant's PoC scope doc and map 1:1 to the scenarios above:

1. **Q1** — "What semantic views exist in my workspace?" → Scenario 1
2. **Q2** — "What's the lineage of this semantic view?" → Scenario 1 (lineage included)
3. **Q3** — "Ship this semantic view as a PR to our governance repo." → Scenario 3
4. **Q4** — "Run quality checks on this semantic view." → Scenario 4
5. **Q5** — "Tell me when this semantic view drifts or anomalies appear." → Scenario 6 (🔴 not in window)
6. **Q6** — "Is the right person allowed to do this?" (RBAC) → tested implicitly in every scenario via Okta-gated auth

If your test doesn't map cleanly to one of these six, it's still valuable — log it under Scenario 7 (general chat).

---

## 9. Scenarios 8–13 — platform surfaces beyond the analyst questions

Six more scenarios covering the rest of the platform Longaeva touches. Same rubric: ✅ live · 🟡 partial · 🔴 not-in-window.

### Scenario 8 — "Call BrightHive tools from my own MCP client" 🟡

- **Persona**: Longaeva data engineer, anyone running Claude Desktop / Cursor / their own agent
- **Maps to**: GC-9 (MCP downstream) / Q3 of the integration story
- **What to do**: Add BrightHive as an MCP server to your client of choice:
  ```
  https://mcp.staging.brighthive.net/mcp
  ```
  Authenticate via Okta (one-time). Then from your client:
  > *"List my semantic views in the Longaeva workspace and run QC on one"*
- **Expected**: Your client lists BrightHive's tools (`list_semantic_views`, `get_semantic_view`, `qc_semantic_view_pipeline`, etc.) and calls them. Results come back inline.
- **State as of cycle-21**: ✅ MCP server live, ✅ OAuth handshake green, ✅ auth → agent → Bedrock inference verified live. 🟡 some tool calls still route through `deep_agent` memory instead of the dbt subagent on edge cases — log it if your call doesn't feel like it hit the warehouse.
- **Why it matters**: This is the *contract* — if your IDE can call BrightHive tools, BrightHive is now part of your developer surface, not a separate website.

### Scenario 9 — "Push me a Slack alert when something matters" 🟡

- **Persona**: ops lead, on-call engineer, anyone who lives in Slack
- **Maps to**: GC-13 (Slack-native bidirectional) + BrightSignals
- **What to do**: Subscribe to events in the `#longaeva-poc` channel:
  > *"Alert me when a semantic-view PR opens, a QC run fails, or a metric trips its threshold"*
- **Expected**: Pushed Slack messages with enough context to triage without leaving Slack — diagnosis sentence + link to the PR/run/dashboard.
- **State as of cycle-21**: ✅ BrightSignals push wired to longitudinal monitoring + PR lifecycle events. 🟡 still tuning what to push vs. suppress — your feedback drives the noise calibration.
- **What we want from you**: Tell us if an alert should have fired and didn't. False negatives are worse than false positives here.

### Scenario 10 — "Pick up where I left off" ✅

- **Persona**: any returning user, anyone who context-switches
- **Maps to**: BrightAgent memory + multi-turn coherence (cross-cutting, not a single GC)
- **What to do**: Have a real conversation across two sessions:
  - Day 1: *"I'm investigating exposure concentration in healthcare. Pull me the top 10 issuers."*
  - Day 2 (new thread): *"Continue where we left off — anything change since yesterday?"*
- **Expected**: The agent recalls the prior thread's context (the healthcare investigation), doesn't ask you to repeat yourself, gives you a delta-shaped answer.
- **What we want**: Note any time the agent forgets, hallucinates a remembered fact, or invents prior context. Memory boundaries are where trust is earned or lost.

### Scenario 11 — "Build a custom agent for my workflow" (Projects / BrightStudio) 🔴

- **Persona**: power user, analyst lead who wants to package a workflow for the team
- **Maps to**: BH-260 (BrightStudio + custom agents — Q2 2026 epic)
- **What to do**: Skip in this window. Tell us if you would have wanted to use it.
- **State as of cycle-21**: 🔴 not in trial. Projects/BrightStudio is the Q2 2026 epic — scaffolding exists in the webapp (`wa#1124` canvas), no end-user agent-builder loop wired yet.
- **Why we're telling you**: Several Longaeva analysts have asked. The trial outcome influences whether this is the Q3 priority or whether we push deeper into ingestion/governance first.

### Scenario 12 — "Make sure the wrong person can't see my data" (RBAC) ✅

- **Persona**: security lead, IT admin, anyone with compliance concerns
- **Maps to**: GC-9 RBAC half + Q6 / BH-612 (auth role hierarchy)
- **What to do**: Three checks anyone with two accounts can run:
  1. Log into the webapp with a Longaeva analyst account → confirm you see **only** the Longaeva workspace, not other tenants.
  2. Ask BrightAgent for a workspace you don't have access to:
     > *"Show me semantic views in the DemoCorp workspace"*
     → expect a clean "you don't have access" response, **not** a leak of any data or even the workspace's existence.
  3. Try to commit a PR via an unbound GitHub repo → expect `errorCode: BINDING_NOT_FOUND`, not a partial write.
- **Expected**: Tenant isolation holds in all three. Auth role hierarchy means workspace admin satisfies inherited role checks; non-admins are clamped.
- **State as of cycle-21**: ✅ Okta SSO live, ✅ `@authorized` tenant gate enforced on the GitHub proxy (BH-559), ✅ role hierarchy seeded (pc#797), ✅ token redaction extended to `ghu_*`, `?access_token=`, `&pat=` patterns in logs.
- **What we want**: Try to break it. Honestly. If you can see a workspace you shouldn't, that's a P0 — escalate immediately to `@kuri`.

### Scenario 13 — "Show me the audit trail and the redaction guarantees" (Governance) ✅

- **Persona**: governance lead, data-protection officer, anyone signing off on the trust contract
- **Maps to**: governance / audit / PII handling (cross-cutting, every scenario depends on it)
- **What to do**: Three governance checks:
  1. **PR-based audit trail**: Open the `longaeva-semantic-views` repo on GitHub. Every change to a semantic view is a PR with author, diff, and `yamlHash` continuity. No edits land without a PR.
  2. **PII redaction**: Run any scenario, then ask `@kuri` for the prompt log. Asset names appear in the structured logger; they **do not** appear in chat (hardened in cycle-20).
  3. **Secret redaction in logs**: Search staging logs for `ghu_`, `ghs_`, `?access_token=`, `&pat=`, `Bearer eyJ` — expect zero hits. 20 regression tests in CI lock this.
- **Expected**: Audit trail complete; PII contained to structured logs; secrets never leak in any surface (chat, logs, error messages, telemetry).
- **State as of cycle-21**: ✅ commitSemanticViewToGitHub orchestrator opens PRs with full audit metadata; ✅ PII removed from chat (asset names → logger only); ✅ Properties 1–4 (PAT redaction, yamlHash continuity, idempotent retry, partial-write honesty) locked in 20-test eval harness in CI.
- **Why it matters**: Most enterprise PoCs fail on the governance question last, not first. Run this scenario before you sign off, not after.
