# AGENTS.md - Client Operations Contract

This directory owns operational tracking for leads, trials, and active
customers. It is the agent-neutral entry point for the flow also described in
`clients/CLAUDE.md`.

For client architecture profiles, stack maps, and integration patterns, use
`../../platform-saas-ai-context/clients/`.

## Read First

- `AGENTS.md` - this portable contract
- `CLAUDE.md` - detailed legacy navigation table
- `README.md` - index of all leads, trials, and active clients
- The matching template before creating a new record:
  - `_templates/LEAD.md`
  - `_templates/TRIAL.md`
  - `_templates/CLIENT.md`

## Lifecycle

```text
leads/{slug}/ -> trials/{slug}/ -> active/{slug}/
```

Move the folder when the stage changes. Do not duplicate client records across
stages. Rename the slug only when it was wrong; stable paths matter for git
history and cross-links.

## Repo Split

| This repo | platform-saas-ai-context |
|---|---|
| POC plans, contacts, success criteria | Client tech stack and architecture |
| Milestone scorecards and blockers | Capability maps |
| Trial artifacts and handoffs | Integration pattern references |
| Active customer operational notes | Durable platform/customer context |

Rule: if it can go stale within a sprint, it belongs here. If it describes how
the client's system is built, it belongs in platform-saas-ai-context.

## Frontmatter

All client content files need YAML frontmatter with these fields:

```yaml
---
name: ""
slug: ""
stage: "lead | trial | active"
champion: ""
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: ""
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: []
---
```

Dates use `YYYY-MM-DD`. `jira_epic` is required before trial Day 1.

## Integration Rules

- Every trial must have a Jira epic before Day 1.
- Trial engineering work goes under that epic.
- Find live epics with `mcp__jira__jira_get_epics(boardId=152, done=false)`.
- Use `../jira/TICKET_TEMPLATE.md` for ticket shape.
- Link Notion GTM pages by ID; do not duplicate Notion content here.
- DynamoDB remains the source of truth for live workspace and account data.
- Feature coverage claims should link to platform feature docs or be marked as
  missing feature-doc work.

## Safety

- Do not commit credentials, private vault exports, or raw customer secrets.
- Keep client-provided artifacts only when they are already intended for this
  repo and do not contain secrets.
- Do not move a trial to `active/` or mark it won/lost without explicit user
  direction or a linked source of truth.
