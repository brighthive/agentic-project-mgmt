# Jira Ticket Template

How any team member (Kuri, Marwan, Ahmed, Harbour) creates a Jira ticket through Claude Code.

---

## The Rules

1. **Every ticket MUST belong to an Epic.** Set `parent: {key: 'BH-XXX'}` — the Epic's key.
2. **Use `issueType: "Task"` — never `"Story"`.** All children of epics are Tasks at BrightHive.
3. **Find the right Epic before creating the ticket.** Don't hardcode epic IDs in docs; look them up live:
   ```
   mcp__jira__jira_get_epics(boardId=152, done=false)
   ```
4. **Project key**: always `BH`.
5. **Assignee**: use the team member's account ID. Common IDs in `CLAUDE.md`. Or omit and assign in Jira UI.

---

## Escape Characters in Descriptions

Jira's REST API converts plain text to ADF. These characters break the conversion if not handled. The MCP `jira_create_issue` tool handles them automatically when you pass a Python string — but if you're writing a shell command yourself, escape them:

| Char | Breaks | How to write it in a Python/MCP string | How to write it in a shell command |
|---|---|---|---|
| `"` | JSON | `\"` | `\"` or `"'\"'"` |
| `'` | shell single-quoted strings | `'` (fine in Python) | `'\''` |
| `\` | both | `\\` | `\\\\` |
| `` ` `` | shell (command substitution) | `` ` `` (fine) | `` \` `` |
| `$` | shell (variable expansion) | `$` (fine) | `\$` |
| `\n` (literal) | ADF reads as text | use actual newline | use `$'\n'` or printf |
| `!` | bash history expansion | `!` (fine) | `\!` |

**Best practice**: write the description as a Python string and pass directly to `mcp__jira__jira_create_issue` — skip the shell entirely.

---

## Description Format (Body)

```
📝 Description

What needs to be done and why. 2-4 sentences.

📍 Scope

Include:
- What's in scope

Exclude:
- What's out of scope

🏗️ Areas

- BrightAgent | Webapp | Platform Core | Slack Server | CDK | Infra

✅ Acceptance Criteria

- [ ] Criterion 1 (measurable)
- [ ] Criterion 2
- [ ] Criterion 3

👥 Contact

Stakeholders: @Kuri @Marwan @Ahmed @Harbour

🔧 Technical Notes

Implementation hints, file paths, function names. Skip if obvious.

💼 Business Notes

Why it matters. Customer impact, priority context. Skip if obvious.

📎 Attachments

Links to specs, designs, screenshots, related PRs.

🔗 Related Issues

- Parent epic context (BH-XXX is the formal parent — link only if blocking)
- Blocks BH-YYY
- Blocked by BH-ZZZ
```

---

## How to Create a Ticket (CLI — any team member, plain terminal)

For users outside Claude Code: the repo ships a Python CLI under `bin/jira-cli` that enforces every rule above and uses the same template. One-time setup in [`ONBOARDING.md` Step 6.5](../ONBOARDING.md). Then:

```bash
make epics                                              # list open epics live
make ticket EPIC=BH-260 TITLE="feat(studio): X"         # opens $EDITOR with skeleton
make my-tickets                                          # your open tickets
make transition KEY=BH-12345 STATE="In Progress"
```

The CLI mirrors the MCP-backed flow below — same template, same invariants, same output shape. Spec: `docs/specs/jira-cli-onboarding.md`.

---

## How to Create a Ticket (via Claude)

Three steps. Claude does them all if you say "make me a ticket for X":

### 1. Find the right Epic

```python
mcp__jira__jira_get_epics(boardId=152, done=false)
```

Pick the Epic whose summary matches the area (e.g. BH-453 for AgentCore migration, BH-260 for BrightStudio, BH-409 for BrightSignals).

### 2. Create the Task

```python
mcp__jira__jira_create_issue(
    projectKey="BH",
    issueType="Task",                       # NEVER Story
    parentKey="BH-453",                     # the Epic — REQUIRED
    summary="brief, imperative, <72 chars",
    priority="High",                        # Highest | High | Medium | Low
    labels=["onboarding", "infrastructure"],
    assignee="712020:b4b1b0de-...",         # account ID; or omit
    description="""📝 Description

The full ticket body. Use real newlines — do not escape \\n.
Embed code blocks with triple backticks.
Use plain text; the MCP tool converts to ADF.

📍 Scope
Include:
- ...
Exclude:
- ...

✅ Acceptance Criteria
- [ ] ...
"""
)
```

### 3. Confirm + add reviewers (optional)

If the ticket needs a sub-team review, comment with `@mentions` after creation.

---

## Team Account IDs (for `assignee=`)

Reference these from `CLAUDE.md` (single source of truth). Today:

| Member | Account ID |
|---|---|
| Kuri | `712020:b4b1b0de-6936-4d70-be9f-5d96ccec7264` |
| Marwan | look up via `mcp__jira__jira_search_users(query="Marwan")` |
| Ahmed | look up via `mcp__jira__jira_search_users(query="Ahmed")` |
| Harbour | look up via `mcp__jira__jira_search_users(query="Harbour")` |

Only Kuri's ID is in memory; the others should be queried once and added to `CLAUDE.md` when you confirm them.

---

## Example A — A bug Ahmed found in CDK

```python
mcp__jira__jira_create_issue(
    projectKey="BH",
    issueType="Task",
    parentKey="BH-173",                     # Bugs & Fixes epic
    summary="fix(cdk): Synapse stack creates duplicate ingestion roles on redeploy",
    priority="Medium",
    labels=["cdk", "synapse", "bug"],
    description="""📝 Description

When `brighthive-data-organization-cdk` is redeployed against an existing
workspace, the Synapse ingestion Step Function creates a second IAM role
with the same logical name. CloudFormation accepts it but the old role
is orphaned.

📍 Scope
Include:
- Detect existing role in CDK lookup before create
- Add `removalPolicy: RETAIN` to existing role construct

Exclude:
- Cleaning up already-orphaned roles in prod (separate ticket)

🏗️ Areas
- brighthive-data-organization-cdk

✅ Acceptance Criteria
- [ ] Redeploy on existing workspace does not create duplicate role
- [ ] CloudFormation drift check shows no orphans
- [ ] Tested in DEV account 531731217746

🔧 Technical Notes
File: lib/synapse-ingestion-stack.ts L142 — the `new iam.Role(...)`
needs a `tryLookup` guard.

🔗 Related Issues
- Related to BH-353 Synapse BYOW ingestion
"""
)
```

---

## Example B — A feature Harbour wants to start

```python
mcp__jira__jira_create_issue(
    projectKey="BH",
    issueType="Task",
    parentKey="BH-260",                     # BrightStudio epic
    summary="feat(skills): Skills marketplace v1 — listing + install button",
    priority="High",
    labels=["brightstudio", "skills", "frontend"],
    description="""📝 Description

After BH-445 shipped Skills as first-class composable agent capabilities,
the next step is letting workspaces browse + install Skills authored by
other teams. v1 is a flat listing with an Install button.

📍 Scope
Include:
- Skills listing page in BrightStudio
- Install button writes to workspace's installed_skills array
- "By me" / "Installed" filter tabs

Exclude:
- Skill authoring (already shipped in BH-445)
- Pricing / paywall (Phase 2)

🏗️ Areas
- brighthive-webapp
- brighthive-platform-core (GraphQL: listSkills query)

✅ Acceptance Criteria
- [ ] /studio/skills route renders all Skills with cards
- [ ] Install button persists to platform-core
- [ ] Installed Skills appear in workspace agent invocation menu

🔗 Related Issues
- Builds on BH-445 (BrightStudio Skills)
"""
)
```

---

## Example C — Marwan documenting a refactor

```python
mcp__jira__jira_create_issue(
    projectKey="BH",
    issueType="Task",
    parentKey="BH-453",                     # AgentCore migration epic
    summary="refactor(brightbot): extract LLM provider config from deep_agent setup",
    priority="Medium",
    labels=["bedrock", "agentcore", "refactor"],
    description="""📝 Description

The Bedrock Converse migration (BH-446) left LLM provider config
scattered across deep_agent.py + 4 sub-agent files. Centralize into a
single ChatModelFactory so the AgentCore migration (BH-453) only
touches one place.

📍 Scope
Include:
- New module: brightbot/agents/shared/chat_model_factory.py
- All sub-agents call factory.create_model(graph_name)
- Same behavior as today; no functional change

Exclude:
- Switching to AgentCore entrypoints (BH-455)

🏗️ Areas
- brightbot

✅ Acceptance Criteria
- [ ] ChatModelFactory in shared/
- [ ] 11 graphs in langgraph.json use the factory
- [ ] UAT suite from PR #23 passes with no regression
"""
)
```

---

## Common Mistakes to Avoid

| Mistake | Fix |
|---|---|
| Using `issueType="Story"` | Always `"Task"` |
| Omitting `parentKey` | Required — find the right Epic first |
| Using `customfield_10014` to set Epic Link | Use `parentKey="BH-XXX"` — `customfield_10014` is blocked by screen config |
| Hardcoding epic ID lists in docs | Query live: `mcp__jira__jira_get_epics(boardId=152, done=false)` |
| Escaping `\n` in the description | Pass real Python newlines; MCP tool handles ADF conversion |
| Single-quoting the entire description in bash | Use Python directly via the MCP tool — avoid bash entirely |
| Forgetting the assignee | Optional, but better to set so it shows on the right person's board |
