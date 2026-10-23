# Planning: Jira Structure and Why Its Status Understates Delivery

Source: `scripts/yearone/collect_jira.py` → `data/jira.json`, `data/jira_issues.json`;
`scripts/yearone/collect_shipped_evidence.py` → `data/shipped_evidence.json`.

## Three projects

| Project | Issues | Span | What it is |
|---|---|---|---|
| BH (Engineering) | 1,507 | first visible ticket BH-110 on 2026-01-11 | Delivery: 48 epics, 1,459 work items |
| BPP (Platform Planning) | 74 | 2023-12 → 2025-10 | An "Idea" backlog: 69 created before 2025-10-23. This is the before-state |
| BL (Leadership) | 18 | 2026-03 → 2026-04 | Leadership tasks |

BH keys 1 to 109 return 404 (deleted or never existed). BH is shown from its first visible ticket.

## Discipline in BH (work items, excluding epics)

| Metric | Value |
|---|---|
| Under a parent epic | 88.6% |
| With a real description (100+ characters) | 97.7% |
| Assigned | 80.5% |
| Median days from created to done | 2.9 |

## Status mix (1,459 work items)

| State | Items | Share |
|---|---|---|
| Done | 362 | 25% |
| Canceled | 60 | 4% |
| In flight (code review, testing, staging) | 174 | 12% |
| Backlog (mostly "Needs Refinement") | 863 | 59% |

Canceled is counted separately from Done. An earlier pass counted it as Done and reported 29%.

## Jira lags delivery

For each ticket we searched commit messages on `develop`, `staging` and the production branches of every repo listed in `shipped_evidence.json` (`repos_searched`) for its BH key.

| Jira status | Tickets | With merged code | In a production branch |
|---|---|---|---|
| Needs Refinement | 836 | 355 | 346 |
| Done | 362 | 215 | 213 |
| Testing (Dev) | 48 | 46 | 46 |
| Staging QC | 48 | 45 | 45 |
| Code Review | 44 | 37 | 36 |
| All open statuses | 1,037 | 516 | 506 |

737 of 1,459 work items (51%) have merged code behind them, against 362 that Jira marks Done.
The plausible completed range is **362 (Jira Done) to 878 (Jira Done plus open tickets with merged code)**.

A key in a commit message is evidence of merged work, not proof the ticket is complete. 147 Done
tickets have no matching code, which is plausible for specs, infrastructure and docs. The sprint
reports describe the same pattern as "pull requests (PRs) ahead of Jira".

## Weak spots

- 62% of work items are assigned to Kuri, and 285 (20%) are unassigned.
- 59% of work items are still in backlog.
- No Jira ticket has been changed by this work. Closing shipped tickets is a separate, reviewed step.
