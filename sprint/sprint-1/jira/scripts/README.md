# Jira Scripts - Migrated to Rust CLI ✅

**Status**: All Python scripts deleted - migrated to unified Rust CLI

**Date**: 2026-01-19

---

## What Happened

🔥 **Deleted**: 10 Python scripts + 36 archived scripts + archive/ directory
✅ **Replaced with**: Single Rust binary `jira-ticket`

---

## Quick Start

### Interactive Ticket Creation (User)
```bash
# Magical interactive mode - for you to use manually
jira-ticket

# Tasks automatically require epic linking + dates
jira-ticket create
```

### Batch Operations (Claude/Automation)
```bash
# Update tickets
jira-ticket update --tickets BH-150-160 --status "In Progress"
jira-ticket update --jql "sprint=1012 AND status='To Do'" --sprint null
jira-ticket update --tickets BH-150 --story-points 5 --add-labels security,feature

# Sprint management
jira-ticket sprint create --name "Sprint 2" --start-date 2026-01-27 --end-date 2026-02-07
jira-ticket sprint start 1012
jira-ticket sprint complete 1012 --move-to 1013

# Always dry-run first
jira-ticket update --tickets BH-150-160 --status "Done" --dry-run
```

---

## Common Operations

```bash
# Remove tickets from sprint (to backlog)
jira-ticket update --jql "sprint=1012 AND status='To Do'" --sprint null

# Add story points to unestimated tickets
jira-ticket update --jql "sprint=1012 AND 'Story Points'=null" --story-points 3

# Move tickets to In Progress
jira-ticket update --tickets BH-150-160 --status "In Progress"

# Add labels
jira-ticket update --jql "summary~'security'" --add-labels security,pentest

# Update epic dates
jira-ticket update --tickets BH-110 --start-date 2026-01-13 --end-date 2026-02-28

# Create Sprint 2
jira-ticket sprint create --name "Sprint 2" --start-date 2026-01-27 --end-date 2026-02-07

# Complete sprint and move incomplete work
jira-ticket sprint complete 1012 --move-to 1013
```

---

## Features

### Update Command
- **Ticket selection**: `--tickets BH-150,BH-151` or `--tickets BH-150-160` or `--jql "..."`
- **Fields**: `--sprint`, `--status`, `--assignee`, `--story-points`, `--add-labels`, `--priority`, `--start-date`, `--end-date`
- **Dry run**: `--dry-run` to preview changes

### Sprint Command
- **create**: Create new sprint with name and dates
- **start**: Activate a sprint
- **complete**: Close sprint and optionally move incomplete issues

### Interactive Create (for Users)
- **Epic linking**: When creating a Task, MUST select an epic (fetches from Jira)
- **Dates**: Tasks MUST have start and end dates (validated YYYY-MM-DD)
- **Rich descriptions**: ADF format with sections, acceptance criteria, technical notes

---

## Benefits of Rust CLI

✅ **Single tool** - No more script proliferation
✅ **Type safety** - Rust catches errors at compile time
✅ **Performance** - Compiled binary, 10x faster than Python
✅ **No dependencies** - No Python/uv environment needed
✅ **Consistent interface** - Same patterns for all operations
✅ **Better errors** - Clear error messages with context
✅ **Dry run mode** - Preview changes before applying

---

## Installation

```bash
cd /Users/bado/iccha/jira-wizard
cargo build --release
cargo install --path .
```

Binary installed to: `~/.cargo/bin/jira-ticket`

---

## Configuration

Uses same config as jira-tui: `~/.config/jiratui/config.yaml`

```yaml
jira_api_base_url: "https://brighthiveio.atlassian.net"
jira_api_username: "your-email@brighthive.io"
jira_api_token: "your-api-token"
```

---

## Migration from Python

| Old Python Script | New Rust Command |
|------------------|------------------|
| `jira_update.py --tickets BH-150 --sprint 1012` | `jira-ticket update --tickets BH-150 --sprint 1012` |
| `update_epic_dates.py --epic BH-110` | `jira-ticket update --tickets BH-110 --start-date YYYY-MM-DD --end-date YYYY-MM-DD` |
| `remove_todo_from_sprint.py` | `jira-ticket update --jql "status='To Do' AND sprint=1012" --sprint null` |
| `fetch_all_issues.py` | JQL queries via jira-ticket or jira-tui |
| `check_sprints.py` | JQL queries: `sprint=1012` |
| `analyze_assignments.py` | JQL queries: `sprint=1012 AND assignee=currentUser()` |

---

## For Claude

When I ask you to perform Jira operations, use `jira-ticket` commands:

```bash
# "Move all To Do tickets to In Progress"
jira-ticket update --jql "status='To Do'" --status "In Progress"

# "Remove tickets from sprint"
jira-ticket update --tickets BH-150-160 --sprint null

# "Add labels to security tickets"
jira-ticket update --jql "summary~'security'" --add-labels security,pentest

# "Create Sprint 2"
jira-ticket sprint create --name "Sprint 2" --start-date 2026-01-27 --end-date 2026-02-07
```

Always use `--dry-run` first, then apply without `--dry-run`.

---

**Maintained by**: Hikuri Chinca (Bado)
**Last Updated**: 2026-01-19
