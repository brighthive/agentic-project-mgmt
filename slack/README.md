# Slack Engineering Intelligence

Weekly snapshots of engineering Slack channels for project context and sprint analysis.

## Structure

```
slack/
  channels.json         # Channel registry + team member IDs
  README.md
  snapshots/
    2026-W16.md         # Weekly snapshot (ISO week number)
    2026-W17.md
```

## What's captured

- **#engineering** — priorities, blockers, demos, cross-team coordination
- **#backend-work** — technical discussions, platform-core, APIs
- **#releases** — sprint release posts, deployments
- **#general** — company-wide context

## Usage

Snapshots are generated weekly and provide context for:
- Sprint planning and retrospectives
- Ticket triage (matching Slack discussions to Jira tickets)
- Understanding what the team is focused on
- Capturing decisions made in chat that aren't in tickets

## Generation

Snapshots are generated via the `/sprint-release` skill or manually:
```bash
# Bot token from ~/.claude/slack/tokens.json
# Channels defined in channels.json
```

Bot: `bright_agent` on `brighthivedata.slack.com`
