# AGENTS.md - Agent Contract for `agentic-project-mgmt`

## Purpose

This repo is BrightHive's agentic project-management hub. Use it for:

- Sprint lifecycle: planning, release, Slack, Notion
- Jira ticket and epic management
- Multi-repo coordination and release notes
- Implementation specs, feature docs, POCs, Bedrock migration diary
- Engineering-leader onboarding and vault tooling
- Infrastructure inventory: AWS Secrets Manager, DynamoDB, LastPass

For permanent platform architecture, use `../platform-saas-ai-context`.

## Agent Compatibility

This file is the portable entry point for Claude Code, Codex, Cursor, Gemini,
Copilot, and humans. `CLAUDE.md` files remain as Claude-specific mirrors and
deeper workflow notes. If a task points at a `CLAUDE.md`, read it as a repo
workflow document even if your agent runtime does not auto-load it.

Slash-command names such as `/write-spec` and `/sprint-release` are Claude Code
accelerators. Agents without those skills must still follow the same lifecycle
manually: read the referenced guide, use the template, gather the same inputs,
and produce the same artifacts.

Examples using `kuri` or `kurilead/` are examples or historical caches. New
onboarding and vault flows must use the operator's own lowercased first name:
`NAME=<name>` and `{name}lead/`.

## Read First

1. `README.md` - repo overview, quick start, Makefile reference, team
2. `AGENTS.md` - this portable operating contract
3. `CLAUDE.md` - Claude navigation mirror with legacy details and lookup tables

Then load the task-specific contract:

- `ONBOARDING.md` - new-leader setup walkthrough
- `docs/AGENTS.md` - specs, feature docs, POCs, Bedrock journal workflows
- `jira/AGENTS.md` - sprint file schema and release artifact spec
- `clients/AGENTS.md` - lead, trial, and active-customer operational docs
- `dynamo-vault/INFRASTRUCTURE.md` - AWS account and workspace config lookup

## Scope Rules

| In scope | Out of scope |
|---|---|
| Sprint artifacts, release notes, Jira tickets | Core product code in sibling repos |
| Implementation specs before code | Permanent architecture docs, which belong in platform-saas-ai-context |
| Onboarding bootstrap, vault tooling | Editing sibling repo code from this repo |
| Bedrock migration diary | Changes to `archive/` |
| Multi-repo coordination | Credentials or secrets in committed files |
| Client trial operational tracking | Client architecture profiles, which belong in platform-saas-ai-context |

## Onboarding Protocol

Trigger this protocol when a user says "set me up", "onboard me", "help me get
started", "I'm new", or asks why local setup is broken and `make status` shows
all sentinels missing.

Follow `ONBOARDING.md` step by step. Run the command for each step, read the
output, fix errors before moving forward, and do not skip ahead because a later
target is likely to fail without earlier sentinels.

Execution order:

```bash
make check-prereqs
make install-prereqs
make configure-aws-sso
make check-creds
# Fix any failed credential check with the documented refresh command.
NAME=<name> make unpack
NAME=<name> make verify-lead
NAME=<name> make pull-secrets
NAME=<name> make env-brightbot-local
NAME=<name> make env-webapp-local
NAME=<name> make env-platform-core-local
make check-siblings
make clone-siblings
make status
make stackstatus
```

Decision rules:

- Ask for `NAME` once at the start if the user has not provided it. It is the
  user's first name lowercased, for example `matt`, `kuri`, or `ahmed`.
- Ask for the vault package path and password when `{name}lead/` does not
  exist. The user should have `{name}lead-export.zip.enc` plus a password from
  their TechLead.
- Pass the vault password by environment variable when running non-interactive
  automation: `VAULT_PASSWORD=<password> NAME=<name> make unpack`.
- Never fill in `.env` values for the user. Tell them which fields are missing
  and why.
- Stop on `[ERROR]`. Do not continue to the next setup step until the current
  error is resolved.
- Do not re-run steps that already show green in `make status`.
- If a secret token is unresolved in `make env-*`, run
  `FORCE=1 NAME=<name> make pull-secrets`, then retry. If it still fails,
  report the exact missing vault path and stop.
- If `make env-*` exits 3 with "Unmanaged file", run
  `ADOPT=1 NAME=<name> make env-brightbot-local` or the matching env target to
  take ownership without overwriting.
- Manual fields that resolve to `FILL_FROM_ENV_STAGING` must be copied by the
  user from the relevant sibling repo staging env file. Do not guess API keys.

Automation boundary:

| Agents can run | User must provide or perform |
|---|---|
| `make check-prereqs` | `NAME=<name>` |
| `make install-prereqs` | Vault package and password |
| `make configure-aws-sso` | Interactive AWS SSO browser login |
| `make check-creds` | Interactive LastPass login when required |
| `make check-siblings` | Manual `.env` values |
| `make clone-siblings` | Approval for production writes |
| `NAME=<name> make pull-secrets` | |
| `NAME=<name> make env-*` | |
| `make status` and `make stackstatus` | |

## Sprint And Jira Rules

- Use `jira/AGENTS.md` for sprint artifacts and release process.
- Use `jira/TICKET_TEMPLATE.md` for all Jira tickets.
- Sprint artifacts live at `jira/sprint/{N}/`. Do not invent alternate paths.
- Epics must be queried live with
  `mcp__jira__jira_get_epics(boardId=152, done=false)`. Never hardcode IDs.
- Every ticket needs an epic parent, uses project key `BH`, and uses issue type
  `Task` unless Jira policy changes.
- Closing a sprint follows the six-phase sprint-release flow:
  DISCOVER -> COLLECT -> ANALYZE -> RELEASE NOTES -> PUBLISH -> COMMIT.

## Docs Workflow

Use `docs/AGENTS.md` for details. The standard lifecycle is:

```text
write POC -> write spec -> create Jira ticket -> implement -> write feature doc
```

| Directory | What goes here |
|---|---|
| `docs/specs/` | Implementation specs |
| `docs/features/` | Shipped feature documentation |
| `docs/pocs/` | Comparative experiments with numbers |
| `docs/bedrock/` | LangGraph to Bedrock migration journal |

## Workflow Accelerators

| Claude skill | Portable equivalent |
|---|---|
| `/sprint-release` | Follow `jira/AGENTS.md` six-phase sprint close process |
| `/write-spec` | Fill `docs/specs/SPEC_TEMPLATE.md` from context and code |
| `/write-feature-doc` | Fill `docs/features/FEATURE_TEMPLATE.md` after ship |
| `/bedrock-journal` | Fill `docs/bedrock/BEDROCK_TEMPLATE.md` and update index |
| `/write-poc` | Fill `docs/pocs/POC_TEMPLATE.md` before or after experiment |
| `/create-jira-ticket` | Follow `jira/TICKET_TEMPLATE.md` and create via Jira MCP |
| `/bh-auth` | Use the repo's documented Cognito token helper flow |
| `/aws-auth` | Use `make refresh-aws` and documented AWS SSO profiles |
| `/scrum-master` | Plan sprint through `jira/AGENTS.md` and live Jira data |

## Cross-Repo Navigation

| Repo | Use for |
|---|---|
| `../brightbot` | Agent runtime, LangGraph graphs, tool implementations |
| `../brighthive-webapp` | React frontend, BrightStudio, Projects UI |
| `../brighthive-platform-core` | GraphQL API, Neo4j schema, auth, workspace management |
| `../brightbot-slack-server` | Slack OAuth, workspace routing, BrightSignals dispatch |
| `../brighthive-data-organization-cdk` | Step Functions, Lambda, Glue data pipelines |
| `../brighthive-data-workspace-cdk` | Per-workspace AWS infrastructure |
| `../platform-saas-ai-context` | Architecture docs, team, roadmap |

Use this repo to coordinate sibling repos through specs, tickets, and release
notes. Do not edit sibling repo code from this repo unless the user explicitly
asks for a cross-repo implementation.

## PR Size Rules

Read `PR_RULES.md` before opening any PR in this repo or any sibling repo.

```text
< 500 lines     -> proceed
500-700 lines   -> consider splitting
700-900 lines   -> split now unless there is a strong reason
>= 900 lines    -> blocked; split before review
```

If a task is approaching the limit mid-work, stop and propose a split shape to
the user before writing more code. Refactor plus feature in one PR is forbidden
unless explicitly approved and still under the line budget.

The same rules apply to Claude Code, Codex, Cursor, Gemini, Copilot, and humans.
`PR_RULES.md` is the canonical shareable copy.

## Safety Rules

- Never commit credentials, vault dumps, local exports, or secrets.
- `secrets/`, `.state/`, `*.zip.enc`, and root `*lead/` vault caches are
  gitignored. Never stage them.
- Leave `archive/` as read-only historical context.
- Do not mix architecture docs into this repo. They belong in
  `platform-saas-ai-context`.
- Do not write production data unless the user explicitly asks and the target
  account, environment, and rollback path are unambiguous.
- Preserve user and other-agent changes. Never revert unrelated work without
  explicit permission.
