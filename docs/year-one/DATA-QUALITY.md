# Data Quality: Corrections, Limits, and Weak Spots

This doc lists what was wrong in earlier passes, what we cannot measure, and what the data says
that does not flatter us. It exists so the review case cannot be undone by something we already knew.

## Corrections made

| Earlier claim | Problem | Fix |
|---|---|---|
| "422 of 1,459 work items done (29%)" | Counted Canceled as Done | Done 362 (25%), Canceled 60 (4%), reported separately |
| "Jira starts 2026-01-11, no before" | Ignored the BPP idea backlog and BL, and overstated: BH keys 1 to 109 are unreadable, not provably absent | Before-state is the BPP backlog (69 ideas); BH shown from BH-110 |
| "Jira status shows how much is done" | Status lags delivery: 516 open tickets have merged code | Jira Done shown beside the merged-code range |
| CI (continuous integration) counts of exactly 1,000 runs | GitHub caps filtered queries at 1,000 results | Collector splits date ranges until under the cap |
| CI before-year runs (e.g. 571,240-minute median) | Runs from before 2025-10-23 were pruned | CI shown for the year after only |
| Webapp "152 workflows" | Counted run names that were commit messages | Column removed |

## Limits

- Test, docs, spec and ADR (architecture decision record) counts match on file-name patterns and are approximate.
- Commit ramp-up matches authors by email, so one person with two emails counts twice.
- A Jira key in a commit message is evidence of merged work, not proof of completion.
- Line counts include lockfiles and generated files, so they are not used.
- Revenue, contract values and headcount are not in any queryable system. See [business.md](business.md).

## Weak spots, shown on purpose

| Finding | Number |
|---|---|
| Work concentration | Top author's share of merged pull requests (PRs) 25.4% → 67.5% (azahid89 before, Kuri after) |
| Jira ownership | 62% of work items assigned to Kuri, 285 unassigned |
| Backlog | 59% of work items in backlog |
| Ticket traceability | 59% of commits carry no ticket key |
| Hotfix rate | 0.4% → 1.2% of commits |
| New-contributor ramp | Median commits in first 30 days 10 → 4 |
| Webapp CI | 46.7% success |
| Review latency | Median time from PR open to merge fell from 0.7–2.3 hours to about 0.1 hours in the core repos, which probably means self-merged PRs. Review coverage (`practices.json`, not collected yet) is the check |
| Controls not yet enforced | Authorization checks are log-only in production, and the Usage and Audit page shows mock data (internal audit, 2026-10-21) |

## Context a reader needs

- The team changed between the two years. Most merged PRs before came from people with few or none after.
- Agent-assisted work inflates commit and PR counts, so volume is context, not a headline.
- Everything here compares two windows. None of it proves the practices caused the change.

## Sources outside `data/`

| Claim | Source |
|---|---|
| Q1 roadmap 65% delivered, 6 of 10 epics at 80%+ | `jira/sprint/BOARD_REPORT_OCT_2025_MAY_2026.md` |
| 16 sprints, Sprint 16 is the first weekly cut | `jira/sprint/SPRINTS.md` |
| "Brighthive 3.0" decided 2026-07-21, and no real staging-to-main gate on the five app repos | `docs/RELEASE_MANIFEST.json` |
| Customer facts (Loop Capital, Nestlé, Virginia, Longaeva) | Internal working notes. Verify before external use |
| Authorization checks log-only in production, Usage and Audit page on mock data | Internal audit of 2026-10-21 |
