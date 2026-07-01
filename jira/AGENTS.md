# AGENTS.md - Jira And Sprint Workflow Contract

This directory owns Jira ticket templates, sprint data, release artifacts, and
the sprint-close workflow. It is the agent-neutral entry point for the flows
also described in `jira/CLAUDE.md`.

## Read First

- `AGENTS.md` - this portable contract
- `CLAUDE.md` - detailed legacy sprint schema and release notes
- `TICKET_TEMPLATE.md` - canonical ticket shape and Jira MCP examples
- `sprint/SPRINTS.md` - master velocity table

## Jira Rules

- Project key is `BH`; board ID is `152`.
- Query epics live before creating tickets:
  `mcp__jira__jira_get_epics(boardId=152, done=false)`.
- Do not hardcode epic IDs from stale docs.
- Tickets under epics use issue type `Task`.
- Every ticket must have an epic parent key, for example `parentKey="BH-XXX"`.
- Do not use `customfield_10014`; Jira screen config blocks it.
- Use `TICKET_TEMPLATE.md` for ticket body structure and escaping rules.

## Sprint Directory Contract

Sprint artifacts live under `sprint/{N}/`. Do not create alternate paths.

Every closed sprint must have these seven files:

| File | Source | Content |
|---|---|---|
| `stats.json` | Jira API | Dates, ticket counts, points, completion, WIP, PR stats |
| `tickets.json` | Jira API | Key, summary, status, assignee, points, type, epic, resolved |
| `SUMMARY.md` | Analysis | Goals, WIP, PR linkage, team breakdown, problems, recommendations |
| `RELEASE_NOTES.md` | Jira and GitHub | Technical release notes per repo and ticket |
| `MARKETING_RELEASE_NOTES.md` | Curated | GTM and sales-facing highlights |
| `VALIDATION_REPORT.md` | GitHub and Jira | PR-ticket linkage, orphan PRs, estimation gaps |
| `SLACK_POST.md` | Curated | Reference copy of the release Slack post |

`PLAN.md` is optional pre-sprint planning.

## Sprint Close Process

The Claude `/sprint-release` skill automates this flow. Other agents must follow
the same phases manually:

1. DISCOVER - auto-detect sprint name, dates, and ID from Jira board 152.
2. COLLECT - gather Jira tickets in all statuses and merged GitHub PRs by date
   range.
3. ANALYZE - generate `SUMMARY.md` with stats, WIP, linkage, team notes, and
   recommendations.
4. RELEASE NOTES - generate `RELEASE_NOTES.md`,
   `MARKETING_RELEASE_NOTES.md`, and `VALIDATION_REPORT.md`.
5. PUBLISH - post to Slack `#releases`, create/update the Notion sprint page,
   and update Active Sprint.
6. COMMIT - write files to `sprint/{N}/`, update `sprint/SPRINTS.md`, and push
   through the normal PR flow unless the repo owner explicitly directs
   otherwise.

## PR Collection

Fetch PRs by merged date range from GitHub, not Jira development status. Jira
dev-status is unreliable when branches do not include a `BH-XXX` key.

```bash
gh pr list --repo brighthive/$REPO --state merged --search "merged:$START..$END" --limit 100 --json number,title,author,additions,deletions,mergedAt,headRefName
```

Match tickets by branch name, then PR title, then PR body, then Jira dev-status
as a fallback.

## Safety

- Do not invent sprint metrics. If data is missing, mark the field as unknown
  and record the gap.
- Do not rewrite historical sprint artifacts unless the user asks for a
  correction.
- Do not post to Slack or mutate Notion/Jira without valid credentials and a
  clear target sprint.
