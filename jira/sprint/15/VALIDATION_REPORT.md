# Sprint 15 🍑 — Validation Report (Aug 2–17, 2026)

## Methodology

- **Tickets**: Jira JQL on resolution date in the window `2026-08-02..2026-08-17`
  (project = BH) → 9 resolved. In-flight tickets pulled via status-transition
  query for the same window, filtered to non-terminal statuses → 5.
- **PRs**: GitHub `gh pr list --state merged --search "merged:2026-08-02..2026-08-17"`
  per repo, across the 8 repos with any activity this window.
- **Matching**: PR branch name / title / body scanned for `BH-XXX`.

## Tickets Without Matched PRs

None — all 9 resolved tickets (BH-1414, BH-1418, BH-1419, BH-1422, BH-1423,
BH-1424, BH-1425, BH-1429, BH-1430) trace to identifiable commits/PRs across
platform-core, brightbot, and agentic-project-mgmt, even where the individual
PR title didn't carry the exact ticket ID (several On-Prem Runner PRs are
titled by capability, e.g. "list the databases a warehouse can actually
reach", rather than by ticket number).

## Orphan PRs (merged, no ticket reference — by design this window)

**~145 of 153 code PRs** reference a ticket ID in title but that ticket did
not resolve in this window (it's a carried multi-window initiative) or has
no corresponding Jira ticket transition on record. This is not a data
error — it's the fifth consecutive unofficial sprint where PR shipping
outruns Jira ticket transitions. Notable ticket families with active PRs
this window but no Done/Canceled transition in-window:

| Ticket family | Theme | PRs this window |
|---|---|---|
| BH-1330 | Project run-sync + observability | 9 |
| BH-1331 | Notification richness / catalog health | 8 |
| BH-1332/1333/1334 | Governance gate binding | 3 |
| BH-1340/1341 | Fleet-health digest + connection-health verb | 6 |
| BH-1346/1348 | Drift watchdog + link-richness | 5 |
| BH-1362 | Default-warehouse identity | 5 |
| BH-1371/1372 | Chat @-mention grammar + home health cleanup | 6 |
| BH-1395/1396 | MCP warehouse-hierarchy verbs | 4 |
| BH-1432/1439-1441/1443/1446/1447 | Warehouse register/verify/multi-db | 14 |
| BH-1036 | Lineage / observability platform work | 5 |

## Branch Naming Issues

None observed — all Kuri/Marwan/Harbour feature branches either carry a
`BH-XXX` reference in the PR title or are clearly scoped release/promotion
carriers (`Develop => Staging`, `dev => staging`, `chore(release):`).

## Estimation Gaps

All 9 resolved tickets and all 5 in-flight tickets have **no story points
set** — consistent with the team's standing practice (velocity measured by
PRs + resolved tickets, not points; see stats.json note).

## Recommendation

Treat this report's "orphan PR" table as the Sprint 16 backlog-hygiene task:
a 30–60 minute sweep transitioning the listed ticket families to their real
current status would bring Jira substantially closer to matching what's
actually shipped.
