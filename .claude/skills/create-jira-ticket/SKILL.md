---
name: create-jira-ticket
description: Build a BrightHive Jira ticket from conversation context — outputs a ready-to-run `mcp__jira__jira_create_issue` call.
allowed-tools: Read, Grep
---

# Create Jira Ticket Skill

Extract technical context from the current conversation and produce a Jira ticket that follows BrightHive conventions. The skill outputs a `mcp__jira__jira_create_issue(...)` call — the Jira MCP server defined in `.mcp.json` executes it.

## Rules

- **ONLY extract what was explicitly discussed** — no assumptions, no invented requirements.
- **Read referenced files** to get exact code, paths, and line numbers.
- **Omit fields** that have no real content from the conversation.
- **Find the right epic live** before producing the call:
  `mcp__jira__jira_get_epics(boardId=152, done=false)`. Pick the epic whose summary matches the area.
- **Always `issueType="Task"`** — never `Story`, `Bug`, or `Subtask`. All children of BrightHive epics are Tasks.
- **Always `projectKey="BH"`** and `parentKey="BH-XXX"` (required — no orphan tickets).
- **Use real newlines** in `description`. The MCP tool converts plain text to ADF.

See `jira/TICKET_TEMPLATE.md` for the canonical body format, escape-character rules, and three full examples (bug, feature, refactor).

## Output

Produce exactly one ready-to-run call:

```python
mcp__jira__jira_create_issue(
    projectKey="BH",
    issueType="Task",
    parentKey="BH-XXX",                     # the epic — required
    summary="<imperative, ≤72 chars>",
    priority="High",                        # Highest | High | Medium | Low
    labels=["..."],                         # optional
    assignee="<account-id-or-omit>",
    description="""📝 Description

<2-4 sentences on what + why>

📍 Scope
Include:
- <one-liner>

Exclude:
- <one-liner or delete section>

✅ Acceptance Criteria
- [ ] <measurable>

🔧 Technical Notes
<file paths, function names, hints — or delete if obvious>
""",
)
```

## Example

Conversation: *"The Synapse ingestion Step Function is creating duplicate IAM roles on redeploy — `lib/synapse-ingestion-stack.ts` L142 needs a `tryLookup` guard."*

```python
mcp__jira__jira_create_issue(
    projectKey="BH",
    issueType="Task",
    parentKey="BH-173",                     # Bugs & Fixes epic
    summary="fix(cdk): guard Synapse ingestion role creation against existing roles",
    priority="Medium",
    labels=["cdk", "synapse", "bug"],
    description="""📝 Description

When `brighthive-data-organization-cdk` is redeployed against an existing workspace, the Synapse ingestion Step Function creates a second IAM role with the same logical name. CloudFormation accepts it but the old role is orphaned.

📍 Scope
Include:
- Detect existing role in CDK lookup before create
- Add `removalPolicy: RETAIN` to existing role construct

Exclude:
- Cleaning up already-orphaned roles in prod (separate ticket)

✅ Acceptance Criteria
- [ ] Redeploy on existing workspace does not create duplicate role
- [ ] CloudFormation drift check shows no orphans

🔧 Technical Notes
File: lib/synapse-ingestion-stack.ts L142 — the `new iam.Role(...)` needs a `tryLookup` guard first.
""",
)
```
