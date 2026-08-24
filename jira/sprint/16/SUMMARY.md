# Sprint 16 🍓 — Per-Person Summary (Aug 17–23, 2026)

> **First release on the new weekly cadence.** Sprint 15 (🍑) ended Aug 17
> after 16 days, the fifth consecutive unofficial date-range cut running
> 11–16 days each. Starting this window, releases cut every 7 days — a
> deliberate team decision, not a placeholder until a formal Jira sprint
> object shows up. No Jira sprint object exists for this window, and none
> is planned.
>
> This document is organized **per person** — Kuri first, then one section
> per engineer.

```
┌──────────────────────────────────────────────────────────────────┐
│  SPRINT 16 🍓  —  Env Wiring, Warehouse Routing & Weekly Cadence  │
│  Aug 17 – Aug 23, 2026  (7 days)                                  │
├──────────────────────────────────────────────────────────────────┤
│  PRs merged .............................. 22                    │
│    · code PRs ............................ 13                    │
│    · release / promotion PRs ............. 9                     │
│  Tickets resolved ........................ 1 (1 Done)            │
│  Tickets shipped code, still Needs Refinement  4                 │
│  Tickets groomed only (no PR this window) . 8                    │
│  Repos touched ........................... 5                     │
│  Code lines (excl. release re-merges) .... +5,993 / -417         │
│  Team .................................... Kuri, Marwan, Harbour │
└──────────────────────────────────────────────────────────────────┘
```

**Reading the line counts:** `agentic-project-mgmt`#179 (spec consolidation,
+3,038/−149) is a docs PR, not application code — it dominates the additions
total the same way a single large refactor would. Every number below is
**code-only** (release PRs excluded).

---

## Kuri (drchinca) — 7 code PRs · +4,758/-239 · 5 repos

Closed the window's one formally-resolved ticket: wiring
`LANGGRAPH_BASE_URL`/`LANGGRAPH_API_KEY` into the core GraphQL Lambda and ECS
runtime after last week's ECS cutover left sync failing closed (BH-1461,
#1215/#1217). Companion fix: project-transformation run cards now read a
stored `lastRunAt` instead of computing it live (BH-1462, #1214). Shipped a
new supervisor warehouse-listing chat tool so brightbot never needs GraphQL
introspection to answer "what warehouses do I have" (BH-1454, #1038),
slack-server artifact delivery on the direct channel-push path (BH-1452,
#177), and the 92-spec→14-theme consolidation under the new Monitoring
Agents epic (BH-1036, agentic-project-mgmt#179).

## Marwan (Marwan-Samih-Brighthive) — 2 code PRs · +483/-19 · 1 repo

Continued the GraphQL Core ECS/CloudFront cutover from Sprint 15: cut the
CloudFront distribution over for staging (#1207) and disabled the GraphQL
Lambda warmer now that ECS carries the traffic instead (#1209). Neither PR
carries a ticket reference.

## Harbour (Nano-233) — 4 code PRs · +752/-159 · 2 repos

Suppressed error toasts firing on background Apollo operations that don't
need user-facing failure noise (#1435). Landed a 3-PR sweep routing
warehouse resolution off the legacy path: scheduled jobs and legacy SQL
callers now resolve through the workspace default warehouse via OGM instead
of the public catalog (#1035, #1039, #1041). None of the three carry a
ticket reference in the title, though they thematically match the
warehouse-default cluster (BH-1455–1458) groomed this week.

---

## PR-to-Ticket Linkage

Only **1 ticket resolved** this window (BH-1461), but **4 more shipped real
code** without a matching status transition: BH-1462, BH-1454, BH-1452, and
BH-1036 all merged PRs this window while sitting in "Needs Refinement." This
continues the same PR-ahead-of-Jira pattern flagged every window since
Sprint 11.

**5 code/release PRs carry no ticket reference at all** — #1035, #1039,
#1041 (brightbot warehouse routing), #1207, #1209 (platform-core ECS
cutover). The brightbot trio thematically matches the warehouse-default
cluster groomed this week (BH-1455–1458), but nothing in the PR ties that
back explicitly — it's an inference, not a confirmed link.

**8 tickets were groomed in Jira this week but shipped no code**
(BH-1453, BH-1455–1460, BH-1463) — pure backlog hygiene, no PRs to match.

## Sprint Health

- **Completion**: 1/1 resolved ticket Done (100%) — but that's the only
  ticket the resolution-date query surfaces; 4 more tickets shipped code
  this window without a status change.
- **Release pipeline stayed clean**: every platform-core and webapp code PR
  this window was followed by a matching develop→staging promotion PR the
  same day — no backlog of un-promoted work.
- **Concentration eased**: Kuri authored 53.8% of code PRs (7/13), down
  sharply from 75.2% in Sprint 15 and the most balanced distribution in
  several windows.
- **First sprint on the new weekly cadence.** No formal Jira sprint object —
  by team decision, not oversight.

## Recommendations for Sprint 17

1. Transition BH-1462, BH-1454, BH-1452, and BH-1036 to reflect that their
   code already shipped.
2. Tag the 5 ticketless PRs (#1035, #1039, #1041, #1207, #1209) against the
   epic they actually belong to — even retroactively — so next week's
   linkage report isn't inferring from PR titles.
3. Keep the weekly cadence. A 7-day cut produced a tighter, more legible
   release than the 12–16 day cuts of Sprints 13–15.
