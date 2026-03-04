# Sprint 6 Summary

## Final Stats

```
┌───────────────┬──────────────────────────┐
│    Metric     │          Value           │
├───────────────┼──────────────────────────┤
│ Duration      │ Feb 19 - Mar 4, 2026     │
├───────────────┼──────────────────────────┤
│ Total Tickets │ 28                       │
├───────────────┼──────────────────────────┤
│ Completed     │ 11 (39.3%)               │
├───────────────┼──────────────────────────┤
│ Story Points  │ 34/71 (47.9%)            │
├───────────────┼──────────────────────────┤
│ PRs Merged    │ 14 (3 repos)             │
├───────────────┼──────────────────────────┤
│ Lines Changed │ 220,336                  │
├───────────────┼──────────────────────────┤
│ Carried Over  │ 17 tickets               │
└───────────────┴──────────────────────────┘
```

## Goals Status

| Goal | Status |
|------|--------|
| BrightStudio | ✅ 4 tickets Done (BH-267, BH-268, BH-269, BH-270) |
| Slack release | ⚠️ Deployment design Done (BH-279), no runtime PRs |
| Projects release | ❌ BH-210 still In Progress, BH-241 was Sprint 5 |
| Unstructured Files Ingest | ✅ 3 tickets Done (BH-238, BH-273, BH-276) + Pulumi stack (BH-283) |
| CX Support (Indiana/EDL) | ✅ BH-287 Done (DB IP update) |

## PR ↔ Ticket Linkage (RED FLAG)

**Only 2 of 14 merged PRs are linked to Jira tickets.**

```
┌──────────────────────────────────┬─────────────────┬───────────┐
│             PR                   │  Matched Ticket │   Status  │
├──────────────────────────────────┼─────────────────┼───────────┤
│ brightbot#391                    │ BH-282          │ ✅ Matched │
├──────────────────────────────────┼─────────────────┼───────────┤
│ brighthive-webapp#994            │ BH-280          │ ✅ Matched │
├──────────────────────────────────┼─────────────────┼───────────┤
│ 12 other PRs                     │ —               │ ❌ No link │
└──────────────────────────────────┴─────────────────┴───────────┘
```

**Root cause**: Team is not following the convention of including `BH-XXX` in PR branch names or titles. Jira's dev-status API relies on this for auto-linking. Without it:
- Release notes show 0 PRs / 0 lines changed
- No traceability from ticket → code change
- Sprint velocity metrics are understated

**Recommendation**: Enforce branch naming convention `BH-XXX/short-description` (e.g., `BH-270/brightstudio-resources`). This is a single config change in GitHub branch protection or a pre-commit hook.

## WIP Analysis

**Average Time in WIP**: 8.3 days (199.2 hours) — well over half the sprint (13 days).

### Red Flags

```
┌────────┬───────────┬────────┬───────────────────────────────────────────────┐
│ Ticket │ WIP Time  │ Status │                    Issue                      │
├────────┼───────────┼────────┼───────────────────────────────────────────────┤
│ BH-238 │ 22.1 days │ Done   │ Multi-sprint! Started Sprint 5, finished S6  │
├────────┼───────────┼────────┼───────────────────────────────────────────────┤
│ BH-279 │ 12.0 days │ Done   │ Near full sprint (Slack deploy design)       │
├────────┼───────────┼────────┼───────────────────────────────────────────────┤
│ BH-270 │ 11.5 days │ Done   │ Near full sprint (BrightStudio resources)    │
├────────┼───────────┼────────┼───────────────────────────────────────────────┤
│ BH-276 │ 11.4 days │ Done   │ Near full sprint (Unstructured data mgmt)    │
├────────┼───────────┼────────┼───────────────────────────────────────────────┤
│ BH-273 │ 11.4 days │ Done   │ Near full sprint (Unstructured data ingest)  │
└────────┴───────────┴────────┴───────────────────────────────────────────────┘
```

### WIP Time Distribution

```
< 1 day:   2 tickets (BH-287, BH-281 — quick wins / hotfixes)
1-3 days:  0 tickets
4-7 days:  3 tickets (BH-268, BH-283, BH-267)
7+ days:   6 tickets (55% of completed work taking most of sprint)
```

## Team Breakdown

| Member | Done | In Progress | Testing/QC | To Do | Total |
|--------|------|-------------|------------|-------|-------|
| Ahmed | 5 | 3 | 1 | 2 | 11 |
| Harbour | 4 | 1 | 0 | 2 | 7 |
| Marwan | 1 | 2 | 2 | 1 | 6 |
| Hikuri | 1 | 0 | 0 | 0 | 1 |

**Notes**:
- Ahmed carried heaviest load (11 tickets) across infra + unstructured data
- Harbour shipped all BrightStudio work (4/4 Done)
- Marwan had most tickets stuck in testing/QC pipeline
- Hikuri focused on Slack deployment (1 ticket Done)

## Problems Identified

1. **39.3% ticket completion is the lowest across all sprints** — Sprint 3 was 52.2%, Sprint 1 was 72.4%
2. **17 tickets carrying over** — more than the 11 completed. Sprint scope was too ambitious (28 tickets / 71 pts for a 13-day sprint)
3. **PR-Ticket traceability is broken** — only 14% of PRs linked to Jira. Release automation cannot accurately report engineering output
4. **No tickets in 1-3 day WIP range** — work is either hotfixes (<1 day) or takes most of the sprint (7+ days). No mid-sized flow
5. **5 tickets in testing/staging limbo** — BH-280, BH-277, BH-282, BH-271, BH-286 all stuck in review/QC gates

## Recommendations

1. **Fix PR naming convention NOW** — Enforce `BH-XXX` in branch names via GitHub branch protection rules. This is blocking accurate sprint metrics
2. **Reduce sprint scope** — 28 tickets was too many. Target 15-18 tickets for Sprint 7 based on actual velocity (11 completed)
3. **Clear the testing queue** — 5 tickets in various QC states need explicit owners and deadlines
4. **Break down large tickets** — 6 tickets taking 7+ days suggests estimation gaps. Split into 2-3 day chunks
5. **Track carryover trend** — 17 carryovers is a record. If this continues, the backlog will outpace throughput

## What Worked

- BrightStudio shipped end-to-end (4 tickets, all Done)
- Unstructured data pipeline foundation laid (PoC + ingest + management)
- Production hotfixes handled quickly (BH-287, BH-281 both <1 day)
- Pulumi infra automation for unstructured data (BH-283)

## What Didn't Work

- 39.3% completion rate — worst sprint yet
- Sprint overloaded with 28 tickets (previous sprints: 23, 42, 29)
- PR ↔ Ticket linking not followed by anyone
- Projects release goal missed (BH-210 still In Progress)
- Testing pipeline is a bottleneck with no clear ownership
