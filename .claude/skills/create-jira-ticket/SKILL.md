---
name: create-jira-ticket
description: Generate technical notes from conversation context for Jira tickets
allowed-tools: Read, Grep
---

# Create Jira Ticket Skill

Extract technical context from conversation. Output a `jira-ticket` command.

## Rules

- **ONLY extract what was explicitly discussed** - no assumptions
- **Read files** to get exact code if referenced
- **Omit fields** if no relevant info exists
- **Escape for shell**: `!` → `\!`, `"` → `\"`, `` ` `` → `` \` ``

## Output a ready-to-copy command:

```bash
jira-ticket --code-context "<technical-notes>"
```

## Technical Notes Template

```
**File(S):** <path>:<lines>
**Module(S):** <path>:<lines>

**Context:** <what was discussed>

**Code:**
<exact snippet from file>

**Technical Notes:**
<errors, changes, or implementation details>
```

Only include fields that have actual content from conversation.

## Example

Conversation: "The owner field needs an emoji like the others for the rust cli tool"

```bash
jira-ticket --code-context "**File:** src/main.rs:616-619

**Context:** Add emoji to owner prompt

**Code:**
Text::new(\"Owner:\")

**Technical Notes:**
Change to match other prompts with emoji prefix"
```
