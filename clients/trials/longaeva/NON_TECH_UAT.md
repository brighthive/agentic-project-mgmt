---
title: "Sarah's Monday morning — a real use case anyone can run"
audience: "Sales, exec, prospect — anyone who wants to see what BrightHive does without engineer-speak"
last_reviewed: "2026-06-17"
purpose: "A 20-minute live demo. One persona, four questions, real numbers, no jargon."
runs_against: "LONGAEVA_POC Snowflake — but the script is reusable against any FS prospect's data"
---

# Sarah's Monday morning

## Who Sarah is

**Sarah Chen.** Portfolio analyst. $12B multi-asset fund. She covers the North American equity sleeve.

It's Monday at 8:45am. The investment committee call is at 9:00am. She has fifteen minutes to figure out if anything moved meaningfully in her book over the weekend, and to walk in with a defensible point of view.

Sarah uses Bloomberg, Excel, and Slack. She does not know what a semantic view is. She does not care.

This persona is **synthetic and reusable**. Swap her name and the fund size to match any prospect you're showing.

## What she does in fifteen minutes

She opens Slack. DMs `@BrightBot`. Asks four questions in order. Reads the answers. Pastes a summary into her PM's DMs. Walks into the IC call.

That's the demo.

---

## The four questions

### Question 1 — *"What are my top 10 positions today, ranked by dollar exposure?"*

**What she sees back**:

| # | Issuer | Sector | Country | Exposure | % of book |
|---|---|---|---|---|---|
| 1 | Synthetic Issuer 0142 | Energy | Hong Kong | $1.27M | 8.0% |
| 2 | Synthetic Issuer 0109 | Comms | Spain | $1.24M | 7.8% |
| 3 | Synthetic Issuer 0038 | Real Estate | Poland | $1.19M | 7.5% |
| 4 | Synthetic Issuer 0082 | Energy | France | $1.19M | 7.5% |
| 5 | Synthetic Issuer 0001 | Financials | Canada | $1.13M | 7.1% |
| 6 | Synthetic Issuer 0032 | Energy | France | $1.11M | 7.0% |
| 7 | Synthetic Issuer 0129 | Comms | Argentina | $1.10M | 6.9% |
| 8 | Synthetic Issuer 0159 | Comms | Spain | $1.04M | 6.6% |
| 9 | Synthetic Issuer 0183 | Health | Switzerland | $1.01M | 6.3% |
| 10 | Synthetic Issuer 0192 | Energy | Hong Kong | $1.01M | 6.3% |

> *Top 10 represents 71% of P-000. Concentrated book, mostly cross-border.*

**Pass bar**: numbers match what she'd get from her Bloomberg query, to within $1K of rounding. No mention of databases, marts, or tools.

### Question 2 — *"Break those down by sector and by country — where is the concentration?"*

**What she sees back**:

By sector:

| Sector | % of book |
|---|---|
| Energy | 28.8% |
| Comms | 21.3% |
| Financials | 12.6% |
| Materials | 8.7% |
| Real Estate | 7.5% |
| Health | 6.3% |
| Industrials | 5.3% |
| Consumer | 5.3% |
| Utilities | 4.4% |

> *Concentration is in Energy + Comms — together 50% of the book. Tech is absent.*

By country: Spain, France, Hong Kong, and Canada each anchor a top-2 position. The book is geographically diversified within the concentrated sectors.

**Pass bar**: percentages sum to 100%. The "stands out" callout matches what the table shows.

### Question 3 — *"What changed in the last week? Anything I should look at first?"*

**What she sees back**:

| Issuer | Change | What happened |
|---|---|---|
| Synthetic Issuer 0167 | **−$681K (−55%)** | Materials cut back hard — likely trimmed for sector rebalance |
| Synthetic Issuer 0109 | **+$611K (+97%)** | Doubled position in Spanish comms |
| Synthetic Issuer 0159 | **+$520K (+99%)** | Doubled position in Spanish comms |
| Synthetic Issuer 0036 | **−$463K (−40%)** | Reduced utilities exposure |
| Synthetic Issuer 0137 | **−$434K (−34%)** | Reduced Swedish materials |

> *The book got more concentrated in Spanish comms this week, less in materials/utilities. Two of the five biggest moves (issuers 0109 and 0036) are on the watchlist — see next question.*

**Pass bar**: the five movers are the actual top-5 by absolute dollar change in the warehouse. The narrative sentence is honest.

### Question 4 — *"Any of these names on a watchlist I should know about?"*

**What she sees back**:

| Issuer | Severity | Reason |
|---|---|---|
| Issuer 0142 (top position) | 🔴 critical | Top position at 8.0% of P-000, above soft cap |
| Issuer 0109 (#2 + +97% mover) | 🟡 elevated | Position 7.78% of P-000, at soft cap |
| Issuer 0038 (#3) | 🟡 elevated | Position 7.5% of P-000, at soft cap |
| Issuer 0082 (#4) | 🟡 elevated | Top-10 position in 3 portfolios concurrently |
| Issuer 0001 (#5) | 🟡 elevated | Credit downgrade — Moody's cut to Baa3 |
| Issuer 0129 (#7) | 🟢 monitor | 6.91% of P-000, watching trajectory |
| Issuer 0159 (#8 + +99% mover) | 🟢 monitor | 6.56% of P-000 |
| Issuer 0183 (#9) | 🟢 monitor | 6.33% of P-000, monitor for trim |
| Issuer 0192 (#10) | 🟢 monitor | 6.32% of P-000, at watchpoint |
| Issuer 0036 (−40% mover) | 🟢 monitor | Q1 EPS below model, guidance maintained |

> *9 of the top 10 names are on the watchlist. The critical one is Issuer 0142 — above its concentration cap. Issuer 0109 doubled into the soft cap this week; that's the action item for the IC call.*

**Pass bar**: every flagged name appears in the watchlist table. Every unflagged name does NOT. The reasons match the table verbatim — no invention.

---

## What she does next

> *"Send this to my PM as a summary."*

**What she gets back** (one Slack message, ≤ 200 words, ready to forward):

> *Monday update — P-000.*
>
> *Book is concentrated: top 10 = 71%, Energy + Comms = 50%, all cross-border.*
>
> *Week's moves: doubled into Spanish comms (Issuers 0109 + 0159, +$1.1M combined), trimmed materials and utilities (Issuers 0167, 0036, 0137, −$1.6M combined). Net direction: deeper into comms, lighter in defensives.*
>
> *Watchlist hits in the top 10: 9 of 10. One critical — Issuer 0142, top position at 8.0%, above our soft cap. One elevated and trending up — Issuer 0109, doubled into the cap this week. Recommend discussing trim.*
>
> *No new positions opened, no closures. Full table available if helpful.*

She copies it. Pastes to her PM. Walks into the IC call at 8:58am.

**That's the demo.** Twenty minutes from cold open, four questions, a defensible point of view, no spreadsheet.

---

## Why this lands

| What buyers ask | What Sarah just got |
|---|---|
| "Will my analysts actually use this?" | Yes — Slack, plain English, two clicks to share. |
| "Is it pulling from real data?" | Yes — every number above is `snow sql` verifiable. No fixtures, no mocks. |
| "What about hallucinations?" | The watchlist names appear because they're in the ground-truth table. None invented. |
| "What's the platform doing under the hood?" | Doesn't matter for this demo. She never sees it. |
| "Can I run this myself?" | Yes — same Slack, same prompts. Doesn't need engineer help. |

---

## How to run the demo yourself (sales dry-run)

1. **Open Slack**. DM `@BrightBot` in `brighthive.slack.com`. Or use the `#longaeva-poc` channel for the customer-facing version.
2. **Ask the four questions verbatim**, in order. Don't paraphrase — the demo's strength is reproducibility.
3. **For each answer**, verify against the table above (numbers should match within $1K).
4. **Last step**: ask the summary question. Copy what comes back. That's the share artifact.

If anything in the answer mentions "semantic view", "Snowflake", "mart", "MCP", or any other internal name, **stop the demo** and ping `@kuri` — the prompt rule isn't holding.

If the numbers don't match within $1K, **stop the demo** — the data layer drifted.

If you're running this against a different customer's data, the persona stays the same. The numbers will differ. The four questions do not change.

---

## Where the numbers come from (only if asked)

A buyer occasionally asks "how did you know that?" Honest one-sentence answer:

> *"We connect to your warehouse, expose a small number of business views like 'positions' and 'changes', and the assistant queries them when you ask a question — same way a senior analyst would, just without the SQL step."*

That's the only platform sentence allowed in the demo. Everything else stays in Sarah's vocabulary.

---

## Files this demo depends on

| What | Where |
|---|---|
| Top-10 + sector + country | `LONGAEVA_POC.SEMANTIC.SV_DAILY_PORTFOLIO_EXPOSURE` |
| Week-over-week change | `LONGAEVA_POC.SEMANTIC.SV_WEEKLY_EXPOSURE_DELTA` (new, this PR) |
| Watchlist crosscheck | `LONGAEVA_POC.REF.WATCHLIST` (new, this PR) |
| The UAT script | [`UAT_GUIDE.md`](./UAT_GUIDE.md) Scenario 14 |
| Plan that produced this | `~/.claude/plans/wobbly-launching-widget.md` |

---

## Reusing this beyond Longaeva

Sarah is portable. The script is portable. For a new prospect:

1. Point the warehouse connection at their data
2. Reseed `REF.WATCHLIST` from their actual watchlist (or curate ~60 entries based on a first-call conversation)
3. The four questions don't change
4. Update the table in Question 1 with their real top 10
5. Run the dry-run, then run live

For the first-meeting deck: a one-page PDF version of this doc (just the four questions + the table snapshots), plus a 90-second screen recording of the actual Slack thread. Both are downstream artifacts; this doc is the source.
