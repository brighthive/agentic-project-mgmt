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
| **Honest state** | ~27% of golden cases are fully live, ~21% partial, ~50% intentionally out-of-scope for this trial window. We tell you which is which up front — no green-washing. |

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

## 2. The seven UAT scenarios

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
- **Expected**: Live read-only report against the 174k-row mart + 3 REF upstream tables. Real findings, including the `IDENTIFIER_MAP.EFFECTIVE_TO` 100%-null flag we surfaced in dev.
- **What "good" looks like**: You see at least one *real* anomaly flagged. If everything reports clean, the test isn't useful — tell us in the feedback row.

### Scenario 5 — "Build me a dbt model from raw data" 🟡

- **Persona**: data engineer
- **Maps to**: GC-4 (silver time-series) / dbt agent
- **What to do**:
  > *"Build a dbt staging model from `RAW.PORTFOLIO_DAILY` and open a PR"*
- **Expected**: dbt agent introspects schema, generates a staging model, opens a PR against the longaeva-dbt repo. Live verified end-to-end against `LONGAEVA_POC`.
- **Caveat**: Sometimes the `deep_agent` routes the question to memory instead of dbt — if your answer feels like a summary instead of a PR link, **that's the bug Marwan is fixing**. Log it. We need the data points.

### Scenario 6 — "Tell me when something breaks" 🔴

- **Persona**: ops lead, ML platform engineer
- **Maps to**: GC-12 (longitudinal monitoring) + GC-11 (self-healing) / Q5
- **What to do**: Don't run this in UAT this window. Tell us if you would have expected it to work.
- **Expected for this trial**: ❌ Not built. Approach spec exists (`docs/specs/longitudinal-monitoring.md`); the sandbox proves all 4 anomaly families detect; production scheduler + BrightSignals push is ~1 sprint of work.
- **Why we're telling you anyway**: This is on the table for the post-trial sprint. If you want it tested live, we want to hear that loudly.

### Scenario 7 — "Just chat with it like an analyst would" ✅

- **Persona**: anyone — sales, exec, marketing, finance
- **Maps to**: overall UX, trust calibration
- **What to do**: Ask any natural-language question about the Longaeva PoC data you'd ask a real analyst:
  - *"How many rows are in PORTFOLIO_DAILY for the last 30 days?"*
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
| MCP downstream query (calling tools from your IDE/agent) | 🟡 Auth live, tool call routing has bug | GC-9 — `deep_agent` routing fix in flight |
| Self-healing pipeline PRs | 🔴 Approach spec only | GC-11 — `docs/specs/self-healing-pipelines.md` |
| Longitudinal anomaly detection | 🔴 Sandbox proven, prod scheduler not built | GC-12 — `docs/specs/longitudinal-monitoring.md` |
| Slack-native bi-directional alerts (BrightSignals push) | 🟡 Scaffold only | GC-13 |

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
| 6 — Monitoring | Harbour | Future epic (Q3) |
| 7 — General chat | Kuri | Cross-cutting, trust calibration |

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

## Appendix — the six analyst questions, verbatim

These came from Grant's PoC scope doc and map 1:1 to the scenarios above:

1. **Q1** — "What semantic views exist in my workspace?" → Scenario 1
2. **Q2** — "What's the lineage of this semantic view?" → Scenario 1 (lineage included)
3. **Q3** — "Ship this semantic view as a PR to our governance repo." → Scenario 3
4. **Q4** — "Run quality checks on this semantic view." → Scenario 4
5. **Q5** — "Tell me when this semantic view drifts or anomalies appear." → Scenario 6 (🔴 not in window)
6. **Q6** — "Is the right person allowed to do this?" (RBAC) → tested implicitly in every scenario via Okta-gated auth

If your test doesn't map cleanly to one of these six, it's still valuable — log it under Scenario 7 (general chat).
