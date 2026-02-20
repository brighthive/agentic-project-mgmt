# Agentic Project Management

Sprint planning, Jira automation, AWS infrastructure tooling, and project tracking for BrightHive.

For permanent architectural knowledge, see: [`platform-saas-ai-context`](../platform-saas-ai-context)

---

## Repository Structure

```
.github/workflows/       Sprint release automation (CI/CD)
jira/                    Sprint data, ticket template, velocity tracking
  sprint/{1..5}/         Per-sprint stats, tickets, summaries, release notes
  TICKET_TEMPLATE.md     Canonical Jira ticket format
  SPRINTS.md             Master velocity table
scripts/                 Production automation scripts
  sprint_release.py      Jira+GitHub release notes generator (backs the workflow)
notion/                  Notion workspace reference (page IDs, structure)
aws-secrets-vault/       CLI: AWS Secrets Manager inventory across 4 accounts
dynamo-vault/            CLI: DynamoDB workspace config scanner
  INFRASTRUCTURE.md      AWS accounts, tables, client registry
lastpass-vault/          CLI: LastPass credential vault
archive/                 Completed sprints, old specs (read-only reference)
```

## Quick Navigation

| Goal | Location |
|------|----------|
| Sprint velocity | `jira/sprint/SPRINTS.md` |
| Sprint N data | `jira/sprint/N/stats.json` + `SUMMARY.md` |
| Release notes | `jira/sprint/N/RELEASE_NOTES.md` |
| Ticket template | `jira/TICKET_TEMPLATE.md` |
| AWS infrastructure | `dynamo-vault/INFRASTRUCTURE.md` |
| System architecture | `../platform-saas-ai-context/docs/architecture/` |
| Team structure | `../platform-saas-ai-context/docs/team/TEAM.md` |
| Quarterly roadmap | `../platform-saas-ai-context/docs/roadmap/ROADMAP.md` |

## Team

| Member | Focus |
|--------|-------|
| Hikuri | Platform Lead, DevOps, AI |
| Ahmed | Backend, Infrastructure |
| Marwan | Frontend, UX |
| Harbour | Data, Quality |

## Sprint Release Workflow

The GitHub Actions workflow (`.github/workflows/sprint-release-v2.yml`) automates end-of-sprint:

1. Queries Jira for Done tickets with linked PRs
2. Collects git history from touched repos
3. Generates `RELEASE_NOTES.md` + `MARKETING_RELEASE_NOTES.md`
4. Updates per-repo `CHANGELOG.md`
5. Posts summary to Slack

Trigger: `workflow_dispatch` with sprint number and date range.

---

**Jira Board**: [BH Board](https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152)
