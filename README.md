# Agentic Project Management

Agentic replacement for traditional project managers and scrum masters. Claude Code skills, agents, and automation manage BrightHive's sprint lifecycle, release notes, Jira operations, infrastructure inventory, and stakeholder communication.

For permanent architectural knowledge, see: [`platform-saas-ai-context`](../platform-saas-ai-context)

---

## Repository Structure

```
jira/                    Sprint data, ticket template, velocity tracking
  sprint/{1..7}/         Per-sprint stats, tickets, summaries, release notes
  sprint/SPRINTS.md      Master velocity table
  TICKET_TEMPLATE.md     Canonical Jira ticket format
docs/                    Documentation & strategy
  specs/                 Feature/migration specs (write before code)
  features/              Platform feature docs & changelogs
  bedrock/               Bedrock migration execution tracking
  pocs/                  Proof-of-concept write-ups
notion/                  Notion workspace reference (page IDs, structure)
aws-secrets-vault/       CLI: AWS Secrets Manager inventory across 4 accounts
dynamo-vault/            CLI: DynamoDB workspace config scanner
lastpass-vault/          CLI: LastPass credential vault
archive/                 Completed sprints, old specs (read-only)
```

## Team

| Member | Focus |
|--------|-------|
| Hikuri | Tech Lead — Architecture, Slack, context engineering |
| Ahmed | Sr. Engineer — Infrastructure, DevOps, security |
| Marwan | Sr. Engineer — BrightAgent, frontend, data quality |
| Harbour | Engineer — BrightStudio, CDK, UI/UX |

## Key Integrations

| Tool | Purpose |
|------|---------|
| Jira (Board 152) | Sprint tracking, tickets, epics |
| GitHub (brighthive org) | 7 core + 10 infra + 7 Airbyte connectors |
| Slack (`#releases`) | Sprint release posts via bot token |
| Notion | Sprint pages, roadmap, CEO reports |
| AWS (4 accounts) | Secrets Manager, DynamoDB configs |

---

**Jira Board**: [BH Board](https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152)
