# AGENTS.md — Agent Contract for `agentic-project-mgmt`

## Purpose

This repo is BrightHive's **agentic project-management hub**. Use it for:

- Sprint lifecycle (planning → release → Slack/Notion)
- Jira ticket and epic management
- Multi-repo coordination and release notes
- Implementation specs, feature docs, POCs, Bedrock migration diary
- Engineering-leader onboarding and vault tooling
- Infrastructure inventory (AWS Secrets Manager, DynamoDB, LastPass)

For permanent platform architecture, use `../platform-saas-ai-context`.

---

## Read First

1. `README.md` — repo overview, quick-start, Makefile reference, team
2. `CLAUDE.md` — full navigation contract, onboarding protocol, sprint data

Then load specialized guides that match the task:

- `ONBOARDING.md` — new-leader setup walkthrough
- `jira/CLAUDE.md` — sprint file schema and release artifact spec
- `docs/CLAUDE.md` — specs, feature docs, POCs, Bedrock journal workflows
- `dynamo-vault/INFRASTRUCTURE.md` — AWS account and workspace config lookup

---

## Scope Rules

| In scope | Out of scope |
|---|---|
| Sprint artifacts, release notes, Jira tickets | Core product code in sibling repos |
| Implementation specs (write before code) | Permanent architecture docs (use platform-saas-ai-context) |
| Onboarding bootstrap, vault tooling | Editing sibling repo code from this repo |
| Bedrock migration diary (Google Drive) | Any changes to archive/ |
| Multi-repo coordination | Mixing credentials or secrets into any committed file |

---

## Onboarding (Claude-specific)

When a user says "set me up", "onboard me", "I'm new", or make status shows all sentinels missing, follow the **Onboarding Protocol** section in `CLAUDE.md`. It defines exact execution order, decision rules, and what to ask vs. run automatically.

**Claude runs automatically**: `make check-prereqs`, `make install-prereqs`, `make configure-aws-sso`, `make check-siblings`, `make clone-siblings`, `NAME=X make pull-secrets`, `NAME=X make env-*`, `make status`, `make stackstatus`

**Claude asks the user for**: NAME, vault package + password, .env values.

---

## Sprint & Jira Rules

- Use `jira/TICKET_TEMPLATE.md` for all Jira tickets
- Use `jira/CLAUDE.md` for required per-sprint files and schemas
- Sprint artifacts live at `jira/sprint/{N}/` — do not invent alternate paths
- Epics: query live via `mcp__jira__jira_get_epics(boardId=152, done=false)` — never hardcode IDs
- Close sprints with `/sprint-release` skill (6 phases: DISCOVER → COLLECT → ANALYZE → RELEASE NOTES → PUBLISH → COMMIT)

---

## Docs Workflow

```
/write-poc  →  /write-spec  →  /create-jira-ticket  →  implement  →  /write-feature-doc
```

| Directory | What goes here |
|---|---|
| `docs/specs/` | Implementation specs (SDD format) |
| `docs/features/` | Shipped feature documentation |
| `docs/pocs/` | Comparative experiments with numbers |
| `docs/bedrock/` | LangGraph to Bedrock migration journal |

---

## Skills Reference

| Skill | Use when |
|---|---|
| `/sprint-release` | Closing a sprint — generates all 7 artifacts, posts to Slack, commits |
| `/write-spec` | Planning a feature or migration before any code |
| `/write-feature-doc` | Documenting a shipped capability |
| `/bedrock-journal` | Weekly Bedrock migration diary entry |
| `/write-poc` | Before or after a comparative experiment |
| `/create-jira-ticket` | Generating Jira notes from conversation context |
| `/bh-auth` | Getting a Cognito JWT for dev/staging/prod |
| `/aws-auth` | Refreshing AWS SSO sessions across accounts |
| `/scrum-master` | Sprint planning |

---

## Cross-Repo Navigation

| Repo | Use for |
|---|---|
| `../brightbot` | Agent runtime, LangGraph graphs, tool implementations |
| `../brighthive-webapp` | React frontend, BrightStudio, Projects UI |
| `../brighthive-platform-core` | GraphQL API, Neo4j schema, auth, workspace management |
| `../brightbot-slack-server` | Slack OAuth, workspace routing, BrightSignals dispatch |
| `../brighthive-data-organization-cdk` | Step Functions, Lambda, Glue data pipelines |
| `../brighthive-data-workspace-cdk` | Per-workspace AWS infra (Bedrock KB, Redshift, S3) |
| `../platform-saas-ai-context` | Architecture docs, team, roadmap (read-only reference) |

Use this repo to **coordinate** sibling repos via specs, tickets, and release notes — not to modify them directly.

---

## Safety Rules

- Never commit credentials, vault dumps, local exports, or secrets
- `secrets/` and `.state/` are gitignored — never stage them
- `kurilead/` and `{name}lead/` are personal vault caches — gitignored, never commit
- `*.zip.enc` vault packages are gitignored
- Leave `archive/` as read-only historical context
- Do not mix architecture docs into this repo — those belong in `platform-saas-ai-context`
