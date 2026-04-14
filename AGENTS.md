# AGENTS.md

Agent contract for `agentic-project-mgmt`.

## Purpose

- This repo is the agentic project-management hub for BrightHive.
- Use it for sprint status, Jira structure, release notes, specs, feature docs, Bedrock migration journaling, vault tooling, and delivery coordination across sibling repos.
- For permanent platform architecture, use `../platform-saas-ai-context` instead.

## Read First

1. `README.md`
2. `CLAUDE.md`

Then load the specialized guides that match the task:

- `jira/CLAUDE.md` for sprint file structure and release artifacts
- `docs/CLAUDE.md` for specs, feature docs, POCs, and Bedrock journal workflows
- `dynamo-vault/INFRASTRUCTURE.md` when the task touches AWS account or workspace config lookup

## Scope Rules

- This repo manages planning and delivery context, not core product implementation.
- Prefer writing specs, sprint artifacts, release notes, and coordination docs here.
- If the task is code in BrightBot, webapp, platform-core, or CDK repos, switch to that repo and use this repo only for planning or release coordination.
- Treat `archive/` as read-only historical context unless the task explicitly requires historical edits.

## Jira and Sprint Rules

- Follow `jira/TICKET_TEMPLATE.md` for Jira ticket structure.
- Follow `jira/CLAUDE.md` for required per-sprint files and schemas.
- Do not invent alternate sprint file formats.
- Keep generated sprint artifacts under `jira/sprint/{N}/`.

## Docs Workflow Rules

- Write specs before major implementation when the work is still being defined.
- Use `docs/specs/` for implementation specs.
- Use `docs/features/` for shipped feature documentation.
- Use `docs/pocs/` for comparative experiments backed by numbers.
- Use `docs/bedrock/` for the migration journal.

## Cross-Repo Navigation

When this repo references implementation work, use the owning sibling repo:

- `../brightbot`
- `../brighthive-webapp`
- `../brighthive-platform-core`
- `../brightbot-slack-server`
- `../brighthive-admin`
- `../brighthive-data-organization-cdk`
- `../brighthive-data-workspace-cdk`
- `../platform-saas-ai-context`

Use this repo to coordinate those repos, not to replace them.

## Safety and Local State

- Do not commit credentials, vault dumps, local exports, or secrets.
- Be careful around vault-related directories and any local-only data.
- Leave unrelated untracked or generated files alone.

## Claude / Agent Notes

- This repo already uses `CLAUDE.md` as the main navigation contract.
- Additional task-specific guidance exists in `docs/CLAUDE.md` and `jira/CLAUDE.md`.
- Preserve those nested contracts instead of flattening everything into one file.

## Avoidable Mistakes

- Mixing permanent architecture docs into this repo
- Editing sibling product code from here
- Changing sprint artifact formats ad hoc
- Treating `archive/` as active working space
- Copying secrets into tickets, specs, or release notes
