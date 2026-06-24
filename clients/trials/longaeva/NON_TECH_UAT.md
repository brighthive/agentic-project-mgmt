---
title: "Non-technical UAT — Longaeva PoC production bars"
audience: "Anyone running BrightAgent without engineering vocabulary — analysts, ops leads, exec testers"
last_reviewed: "2026-06-24"
purpose: "The contract for what BrightAgent must be able to do for a non-technical user, end-to-end, in production."
runs_against: "LONGAEVA_POC Snowflake (staging) via Slack `@BrightBot` or the BrightHive webapp"
ticket: "BH-745 — renamed from SARAH_DEMO.md (was framed as a sales asset; this is the production UAT)"
---

# Non-technical UAT — Longaeva PoC

> **This is a production UAT contract, not a demo script.** Every prompt below must work, every time, with the bars met. If a non-technical user asks one of these questions in Slack and the answer fails the bar, that is a production bug — file it under [BH-601](https://brighthiveio.atlassian.net/browse/BH-601).

## What this covers

A non-technical user (portfolio analyst, ops lead, exec) asks BrightAgent four questions in Slack, in order, and forwards the result to a colleague. No SQL, no platform terminology, no follow-ups required.

The four questions, in order:

1. *"What are my top 10 positions today, ranked by dollar exposure?"*
2. *"Break those down by sector and by country — where is the concentration?"*
3. *"What changed in the last week? Anything I should look at first?"*
4. *"Any of these names on a watchlist I should know about?"*

Then a summary request: *"Send this to my PM as a summary."*

## The hard prompt rule (jargon firewall)

In ANY of the five steps above, if the bot uses any of these words in a user-facing reply, the test **fails**:

`semantic view` · `Snowflake` · `gold mart` · `mart` · `silver` · `bronze` · `MCP` · `deep_agent` · `subagent` · `database` · `query` · `SQL` · `Atlas` · `YAML` · `embedding` · `vector` · `Bedrock` · `LangGraph` · `agent loop`

A jargon leak is a **P0** — file under [BH-744](https://brighthiveio.atlassian.net/browse/BH-744).

The one allowed platform sentence — *only if the user asks "how did you know that?"* — is:

> *"We connect to your warehouse, expose a small number of business views like 'positions' and 'changes', and the assistant queries them when you ask a question — same way a senior analyst would, just without the SQL step."*

Everything else stays in business vocabulary.

---

## Bar 1 — Top 10 positions

**Prompt**: *"What are my top 10 positions today, ranked by dollar exposure?"*

**Pass bar**:
- Returns a 10-row table: issuer name, sector, country, exposure ($), % of book.
- Numbers reconcile within $1K of `LONGAEVA_POC.SEMANTIC.SV_DAILY_PORTFOLIO_EXPOSURE` for the latest `AS_OF_DATE`.
- Reply contains zero firewall terms.

**Fail signals**:
- Bot says "semantic view" or "Snowflake" anywhere.
- A name appears that isn't actually in the warehouse for that date.
- Numbers don't sum to 100% (±0.1%) when the user asks for percentages.

**Source data**: `LONGAEVA_POC.SEMANTIC.SV_DAILY_PORTFOLIO_EXPOSURE` (built on `GOLD.MART_DAILY_PORTFOLIO_EXPOSURE`, 174,384 rows). Issuer names come from `REF.IDENTIFIER_MAP` (200 issuers, currently seeded as synthetic placeholders — the seed will be replaced when Longaeva provides their real issuer universe).

---

## Bar 2 — Concentration breakdown

**Prompt**: *"Break those down by sector and by country — where is the concentration?"*

**Pass bar**:
- Two compact tables: by sector, by country.
- Percentages sum to 100% (±0.1%).
- Narrative callout (1–2 sentences) matches the table — no contradictions.
- Reply contains zero firewall terms.

**Fail signals**:
- Sums off by more than 0.1%.
- Callout ("the book is concentrated in X") contradicts what the table shows.
- Bot mentions schema names, mart names, or join semantics.

**Source data**: same SV; aggregations done in-query, not invented post-hoc.

---

## Bar 3 — Week-over-week changes

**Prompt**: *"What changed in the last week? Anything I should look at first?"*

**Pass bar**:
- Top 5 movers by absolute dollar change (positions opened, closed, scaled).
- Honest narrative sentence summarizing direction (more X, less Y).
- Reply contains zero firewall terms.

**Fail signals**:
- "I don't have that data" (the delta mart is wired — see [BH-743](https://brighthiveio.atlassian.net/browse/BH-743) if it's not).
- The five movers don't match the actual top-5 by `|delta_amount_usd|` in `MART_WEEKLY_EXPOSURE_DELTA`.
- Random-looking picks not grounded in the warehouse.

**Source data**: `LONGAEVA_POC.SEMANTIC.SV_WEEKLY_EXPOSURE_DELTA` (built on `GOLD.MART_WEEKLY_EXPOSURE_DELTA`, 692 rows of week-over-week deltas across 30 portfolios).

---

## Bar 4 — Watchlist crosscheck

**Prompt**: *"Any of these names on a watchlist I should know about?"*

**Pass bar**:
- Every flagged issuer appears in `REF.WATCHLIST` (60 rows currently, seeded with realistic watchlist reasons across critical/elevated/monitor severities).
- Every unflagged issuer is NOT in `REF.WATCHLIST`.
- Severity and reason match the table verbatim — no inventing reasons.
- Reply contains zero firewall terms.

**Fail signals**:
- Hallucinated reasons ("Moody's downgrade" for an issuer not flagged for credit).
- Missing flagged names from the top-10.
- Inventing severity levels not in `REF.WATCHLIST.SEVERITY`.

**Source data**: `LONGAEVA_POC.REF.WATCHLIST` (60 issuers; columns: `INTERNAL_ISSUER_ID`, `ISSUER_NAME`, `WATCHLIST_REASON`, `SEVERITY`, `ADDED_DATE`, `ADDED_BY`).

---

## Bar 5 — Forwardable summary

**Prompt**: *"Send this to my PM as a summary."*

**Pass bar**:
- ≤ 200 words, Slack-formatted, copy-paste-ready.
- References the prior four answers without contradiction.
- One clear "watch this first" recommendation tied to the watchlist crosscheck.
- Reply contains zero firewall terms.

**Fail signals**:
- Walls of text > 200 words.
- Engineer language in what's supposed to be a PM-facing summary.
- "Recommendation" not tied to anything in the prior four answers.

---

## Where this fits in the regression suite

Codified as `tests/integration/golden_cases/test_longaeva_uat_mcp.py::test_uat_s14_sarah_no_jargon_in_chat` in brightbot. The test:

- Pulls the prompt verbatim from this file.
- Hits the live staging MCP (`brightagent-mcp.staging.brighthive.net/mcp`) via the `deep_agent` entrypoint.
- Checks the reply against the firewall list.
- Hard-fails on any leak.

Run:
```bash
BH_MCP_URL=https://brightagent-mcp.staging.brighthive.net/mcp \
BH_MCP_AUTH_VIA_GRAPHQL=1 \
BH_MCP_WORKSPACE_ID_HEADER=4d7ffd13-73d0-4f14-8f0e-63bfddceca7c \
RUN_LIVE_MCP=1 \
uv run pytest tests/integration/golden_cases/test_longaeva_uat_mcp.py::test_uat_s14_sarah_no_jargon_in_chat -v
```

Last run (2026-06-24): **failing** — `deep_agent` appeared in a user-facing reply. Tracked under [BH-744](https://brighthiveio.atlassian.net/browse/BH-744).

---

## Tester verdict

Log to the **UAT Feedback** Notion DB on the Longaeva GTM page. Use scenario name `S14 — Non-tech UAT`.

**Required columns** (same rubric as the other UAT scenarios — see `UAT_GUIDE.md §3`) plus one extra:

| Column | Notes |
|---|---|
| `Jargon leaked?` | Y/N. Any Y is a P0 — file under [BH-744](https://brighthiveio.atlassian.net/browse/BH-744), do not continue the test. |

---

## Issuer names — current state

The seeded `REF.IDENTIFIER_MAP` carries 200 placeholder names of the form `Synthetic Issuer 0000`–`0199`. The non-tech UAT therefore tests *the agent's behavior on real warehouse rows*, not the realism of the names. When Longaeva provides their actual issuer universe (or we curate a public-company list for general prospects), the seed will be replaced and this doc will not need to change — the bars are about behavior, not specific names.
