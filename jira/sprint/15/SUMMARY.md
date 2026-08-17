# Sprint 15 🍑 — Per-Person Summary (Aug 2–17, 2026)

> **Unofficial, date-range cut.** No Jira sprint object exists for this window —
> the last release was Sprint 14 (🍯, Aug 1). This is the **fifth unofficial
> sprint in a row** (11–15). Opening a formal Jira sprint object is overdue.
>
> This document is organized **per person** — Kuri first, then one section per engineer.

```
┌──────────────────────────────────────────────────────────────┐
│  SPRINT 15 🍑  —  On-Prem Runner, Warehouse Identity & Routines│
│  Aug 2 – Aug 17, 2026  (16 days)                                │
├──────────────────────────────────────────────────────────────┤
│  PRs merged .............................. 181                 │
│    · code PRs ............................ 153                 │
│    · release / promotion PRs ............. 28                  │
│  Tickets resolved ........................ 9 (8 Done, 1 Canceled) │
│  Tickets in flight ....................... 5                   │
│  Repos touched ........................... 8                   │
│  Code lines (excl. release re-merges) .... +87,472 / -44,270   │
│  Team .................................... Kuri, Marwan, Harbour│
└──────────────────────────────────────────────────────────────┘
```

**Reading the line counts:** raw merged-line totals are dominated by 28
release-promotion PRs (`chore(release)` / `Develop => Staging` / `dev => staging`)
that re-merge an entire branch. Every number below is **code-only** (release PRs
excluded) so it reflects work authored, not branches re-shipped. One webapp PR
(#1423, warehouse table rewrite) alone accounts for -37,874 of the code-only
deletion total — a real large refactor, not a release artifact.

---

## Kuri (drchinca) — the through-line of the whole sprint, again

**115 PRs** · code-only **+74,357 / -42,726** · **7 repos**
(webapp 28, brightbot 27, platform-core 26, apm 22, e2e 8, slack-server 3,
platform-saas-ai-context 1) · **75.2% of all code PRs merged this sprint**

Kuri drove three converging initiatives:

1. **On-Prem Engineering Runner (BH-1403/1421 epics)** — the Loop Capital
   on-prem dbt plugin: outbound-only job queue so the plugin never needs an
   inbound port, warehouse register/verify/list-databases on platform-core,
   governed connection principals (scoped reader + write-confined engineer),
   multi-database sandbox (OMS + TradeDW alongside LoopCapitalAM), legacy
   SSIS/SSRS filesystem reads, artifact sync back into platform-core lineage,
   and a reproducible sandbox harness (manifest capture / synthesize / nuke)
   landed in `agentic-project-mgmt`. 8 of 9 tickets resolved this window sit
   under this epic. Windows Server 2019 packaging and outbound transport are
   Ready for Staging; the real-behavior MCP-to-plugin-to-dbt-to-SQL-Server-to-lineage
   e2e is Needs Refinement — the epic isn't closed yet.
2. **Warehouse identity & multi-database targeting (BH-1362/1432/1439-1441/1443/1446/1447)**
   — default-warehouse badge + admin set-default, verify/register/list-databases
   flow end to end (platform-core to webapp to brightbot chat addressing), naming
   a warehouse *and* database with `@` in chat, honoring database names with
   spaces, MCP callers choosing which warehouse to target.
3. **Routines delivery & notification provenance (BH-1399-1402, 1397/1398)** —
   per-routine delivery target passthrough, executed SQL + artifact link
   threaded into Slack notifications (closing the loop with slack-server
   #176), delivery-target picker + delivered-channel chip on the webapp,
   rich run cards, remediation-PR fix cards, fleet-health digest and drift
   watchdog wiring across brightbot/platform-core/webapp/slack-server.

## Marwan (Marwan-Samih-Brighthive) — infra & data-quality hardening

**19 PRs** · code-only **+8,175 / -1,116** · **4 repos**
(platform-core 14, webapp 2, brightbot 2, data-organization-cdk 1)

Cut over GraphQL Core to an ECS/CloudFront runtime for staging (S3 trust sync,
Lambda IAM parity, explicit log groups, SAM Docker build fixes), then chased a
string of Neo4j pool-exhaustion issues surfaced by that migration (unify
driver + cap connection pool per Lambda, fail-fast 503 instead of hanging,
stop health-check writes on every field resolution, cap OpenMetadata
enrichment concurrency to stop catalog pool storms). Also shipped the async
workspace catalog sync job API and a Sync-catalog button with polling on the
webapp, plus an upload-retry fix for onboardResource S3 PUT failures.

## Harbour (Nano-233) — product-surface craftsman

**19 PRs** · code-only **+4,940 / -428** · **3 repos**
(brightbot 13, webapp 3, platform-core 2, slack-server 1)

Shipped the project-activation-check pipeline end to end (signal + toast on
platform-core, inbox/thread UX + activation-check notification on webapp,
Slack card renderer on slack-server), landed BrightAgent's live SSE token
streaming into the chat bubble (Phase 1), and put in a run of dbt-agent
resilience fixes: recovering dropped macro bodies from write_file scratch,
resolving GitHub commit files from staged/artifact state when tools omit
content, raising the ReAct model's max_tokens to stop file-body truncation,
and a new SQL Server diagnostics analyst skill plus the XSD warehouse
reconciliation gate.

---

## PR-to-Ticket Linkage — the gap is total, not partial

All **9 tickets resolved** and all **5 tickets in flight** this window sit under
two epics: **BH-1403** (Autonomous dbt Project Lifecycle on On-Prem SQL Server)
and **BH-1421** (On-Prem Engineering Runner). That's the *only* initiative with
Jira coverage. The other ~145 code PRs this window — warehouse identity,
routines delivery, notifications/Signal Catalog, the ECS cutover, Neo4j
hardening, BrightAgent streaming — **have no matching Jira ticket in Done/
Canceled state for this window**, even though several reference ticket IDs in
PR titles (BH-1330, BH-1331, BH-1340, BH-1341, BH-1346, BH-1348, BH-1362,
BH-1371, BH-1372, BH-1395, BH-1396, BH-1432, BH-1437+). Those tickets exist but
weren't captured by the resolution-date query because they either resolved in
an earlier window (carried-forward work continuing to ship PRs) or were never
formally transitioned. This is the same PR-ahead-of-Jira pattern flagged in
Sprints 11-14, now running its fifth consecutive sprint.

## Sprint Health

- **Completion**: 8/9 resolved tickets Done (88.9%), 1 Canceled (SQL Server
  disk-pressure health tool superseded by the connection-health verb shipped
  on brightbot).
- **5 tickets carrying into Sprint 16**, all On-Prem Runner: 2 Ready for
  Staging (Windows packaging, outbound transport), 2 In Progress (the two
  parent epics themselves — expected, they won't close until the sub-tasks
  do), 1 Needs Refinement (the real-behavior e2e).
- **Concentration risk unchanged**: Kuri authored 75.2% of code PRs (115/153),
  consistent with Sprints 11-14 (69.5-72%). No sign of this diffusing.
- **Fifth unofficial sprint in a row.** The board-152 Jira sprint object hasn't
  been used since Sprint 8 (Apr 28). Ticket tracking for anything outside the
  On-Prem Runner epic is effectively not happening in near-real-time.

## Recommendations for Sprint 16

1. Open a formal Jira sprint object on board 152 — five sprints of "date-range
   cut, unofficial" is no longer a one-off, it's the process.
2. Sweep the ~145 un-linked code PRs from this window and retroactively
   transition their tickets (BH-1330/1331/1340/1341/1346/1348/1362/1371/1372/
   1395/1396/1432 families) so sprint stats reflect actual delivery, not just
   the On-Prem Runner epic.
3. Close out the On-Prem Runner epic: Windows Server packaging and outbound
   transport are Ready for Staging — land them; the real-behavior e2e
   (BH-1428) is the one gating item before the epic can be called done.
