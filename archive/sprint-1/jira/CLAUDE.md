# Jira Scripts - Claude Instructions

**CRITICAL**: This directory contains reusable Jira automation scripts. **NEVER create one-time scripts.**

---

## Core Principle: Reusable Tools, Not One-Time Scripts

### ❌ WRONG Approach
```bash
# Creating a new script for every operation
create_sprint_1_tasks.py
update_sprint_1_tickets.py
update_sprint_1_tickets_part2.py
remove_todo_from_sprint.py
remove_needs_refinement_from_sprint.py
fix_dashboard_metrics.py
... (42 one-time scripts and counting)
```

### ✅ RIGHT Approach
```bash
# Use generic tools with arguments
jira_update.py --jql "status='To Do'" --sprint null
jira_update.py --tickets BH-150-200 --story-points 3
jira_update.py --jql "status='Needs Refinement'" --sprint null
```

---

## Available Reusable Tools

### 1. **jira_update.py** - Generic Ticket Updater

**Purpose**: Update any field on any set of tickets

**Examples**:

```bash
# Remove tickets from sprint (move to backlog)
uv run python jira_update.py --jql "status='To Do' AND sprint=1012" --sprint null
uv run python jira_update.py --tickets BH-150-169 --sprint null

# Update status
uv run python jira_update.py --tickets BH-150,BH-151 --status "In Progress"

# Set story points
uv run python jira_update.py --jql "sprint=1012 AND 'Story Points'=null" --story-points 3

# Add labels
uv run python jira_update.py --tickets BH-150-160 --add-labels "security,feature"

# Combine multiple updates
uv run python jira_update.py --tickets BH-150-155 --status "To Do" --sprint 1012 --story-points 3

# Dry run (see what would change without changing)
uv run python jira_update.py --jql "status='Needs Refinement'" --sprint null --dry-run
```

**Ticket Selection**:
- Single: `--tickets BH-150`
- Multiple: `--tickets BH-150,BH-151,BH-152`
- Range: `--tickets BH-150-155` (expands to BH-150 through BH-155)
- JQL Query: `--jql "status='To Do' AND sprint=1012"`

**Field Updates**:
- `--sprint <id>` or `--sprint null` (remove from sprint)
- `--status "Status Name"` (transitions ticket)
- `--assignee <accountId>` or `--assignee null`
- `--story-points <number>`
- `--add-labels "label1,label2"`
- `--priority "High|Medium|Low"`

### 2. **fetch_all_issues.py** - Fetch Current Data

**Purpose**: Refresh local JSON files with latest Jira data

```bash
uv run python fetch_all_issues.py
```

**Output**:
- `../epics.json` - All epics
- `../active.json` - In Progress issues
- `../ready.json` - To Do/Ready issues
- `../completed.json` - Recently completed (last 30 days)

---

## When User Asks for Bulk Updates

### Step 1: Use Existing Tools First

**Before writing any code**, check if the request can be handled by `jira_update.py`:

- "Remove all To Do tickets from sprint" → `jira_update.py --jql "status='To Do' AND sprint=1012" --sprint null`
- "Add story points to design tasks" → `jira_update.py --jql "summary~'Design' AND sprint=1012" --story-points 3`
- "Move tickets to In Progress" → `jira_update.py --tickets BH-150-160 --status "In Progress"`

### Step 2: If Tool Doesn't Exist, Create Generic Version

If `jira_update.py` doesn't support the operation:

1. **DO NOT** create `do_specific_thing_for_sprint_1.py`
2. **DO** extend `jira_update.py` or create a new generic tool
3. **DO** add CLI arguments for flexibility
4. **DO** document in this file

### Step 3: Dry Run First

Always use `--dry-run` to preview changes:

```bash
uv run python jira_update.py --jql "sprint=1012" --sprint null --dry-run
```

---

## Architecture Patterns

### Reusable Script Structure

```python
#!/usr/bin/env python3
"""
Generic tool description.

Usage:
    python tool.py --arg1 value --arg2 value
"""

import argparse
import sys
from pathlib import Path

def load_config() -> dict[str, str]:
    """Load JIRA configuration from ~/.config/jiratui/config.yaml"""
    ...

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tool description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Add arguments
    parser.add_argument("--arg1", required=True, help="Description")
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    # Perform operation
    ...

if __name__ == "__main__":
    main()
```

### Key Principles

1. **CLI Arguments**: All inputs via argparse, no hardcoded values
2. **Dry Run**: Always support `--dry-run` flag
3. **JQL Support**: Accept both ticket lists and JQL queries
4. **Clear Output**: Show what's happening (✓ success, ✗ failure)
5. **Error Handling**: Continue on errors, report at end
6. **Documentation**: Usage examples in docstring

---

## Common Operations Reference

### Sprint Management

```bash
# Remove tickets from sprint (to backlog)
uv run python jira_update.py --jql "sprint=1012 AND status='To Do'" --sprint null

# Add tickets to sprint
uv run python jira_update.py --tickets BH-200-210 --sprint 1012

# Move active sprint tickets to next sprint
uv run python jira_update.py --jql "sprint=1012 AND status!='Done'" --sprint 1013
```

### Status Updates

```bash
# Move tickets to In Progress
uv run python jira_update.py --tickets BH-150-160 --status "In Progress"

# Move To Do tickets back to Needs Refinement
uv run python jira_update.py --jql "status='To Do'" --status "Needs Refinement"
```

### Story Points

```bash
# Add story points to all unestimated tickets
uv run python jira_update.py --jql "sprint=1012 AND 'Story Points'=null" --story-points 3

# Update specific tickets
uv run python jira_update.py --tickets BH-150-155 --story-points 5
```

### Labels

```bash
# Add labels to security tickets
uv run python jira_update.py --jql "summary~'security'" --add-labels "security,pentest"

# Add roadmap label to design tasks
uv run python jira_update.py --jql "summary~'Design' AND sprint=1012" --add-labels "roadmap"
```

---

## Cleanup Status ✅

### COMPLETED (2026-01-19)

✅ **36 one-time scripts moved to `scripts/archive/`**

All deprecated scripts have been archived. Only reusable tools remain.

```bash
# Sprint 1 specific (should use jira_update.py)
create_sprint_1_tasks.py
update_sprint_1_tickets.py
update_sprint_1_tickets_part2.py
fix_missing_file_refs.py
remove_todo_from_sprint.py
remove_needs_refinement_from_sprint.py

# Assignment specific (should use jira_update.py --assignee)
assign_marwan_tickets.py
assign_ahmed_tickets.py
assign_partnerships_tasks.py
assign_final_tasks.py
assign_unassigned_design_tasks.py
fix_all_assignments.py

# Sprint movement (should use jira_update.py --sprint)
add_to_sprint_1.py
move_to_sprint_1.py
move_to_active_sprint.py
add_tasks_to_sprint.py

# Status updates (should use jira_update.py --status)
fix_status_to_todo.py
move_completed_to_staging.py

# Ticket creation (keep these, but document patterns)
create_sprint_1_tasks.py
create_new_epics.py
create_recent_work_tickets.py
create_ahmed_tickets.py
create_partnerships_epic.py
create_quality_agent_cron_task.py
create_jedx_deactivation_task.py

# One-time fixes (should be documented and deleted)
fix_failed_tickets.py
fix_missing_file_refs.py
audit_and_fix_sprint_tickets.py
complete_sprint_setup.py
final_setup_actions.py

# Analysis/verification (keep these)
analyze_assignments.py
check_sprints.py
verify_assignments_direct.py

# Dashboard (needs work, document separately)
setup_dashboard.py
reconfigure_dashboard.py
simple_dashboard_fix.py
fix_dashboard_metrics.py
```

### What We Kept (9 scripts)

✅ **Reusable Tools**:
- `jira_update.py` - Generic ticket updater (NEW)
- `test_jira_update.py` - Test suite for jira_update.py
- `fetch_all_issues.py` - Data fetcher
- `fetch_jira_epics.py` - Specialized fetcher
- `analyze_assignments.py` - Assignment reporting
- `check_sprints.py` - Sprint verification
- `verify_assignments_direct.py` - Assignment verification
- `cleanup_scripts.py` - This cleanup script
- `__init__.py` - Python package marker

### What We Archived (36 scripts)

All moved to `scripts/archive/` with README explaining replacement:
- All `create_*` scripts
- All `update_*` scripts
- All `assign_*` scripts
- All `move_*` scripts
- All `fix_*` scripts
- All `remove_*` scripts
- All dashboard scripts

---

## Dashboard Management

**Note**: Jira dashboard API is problematic. Use manual configuration.

**Dashboard URL**: https://brighthiveio.atlassian.net/jira/dashboards/10068

**Manual Configuration** (5 minutes):
1. Go to dashboard → Edit
2. Add gadgets:
   - Sprint Health (configure for board 152)
   - Pie Chart: Status (JQL: `sprint=1012`)
   - Pie Chart: Assignee (JQL: `sprint=1012`)
   - Filter Results: In Progress (JQL: `sprint=1012 AND status='In Progress'`)

**Do NOT** create scripts to configure dashboard gadgets - the API is unreliable.

---

## File Organization

```
jira/
├── CLAUDE.md              # This file - instructions for Claude
├── README.md              # User-facing documentation
├── *.json                 # Data files (epics, active, ready, completed)
└── scripts/
    ├── jira_update.py     # ✅ Generic ticket updater (NEW)
    ├── test_jira_update.py # ✅ Test suite
    ├── fetch_all_issues.py # ✅ Data fetcher
    ├── fetch_jira_epics.py # ✅ Specialized fetcher
    ├── analyze_*.py       # ✅ Analysis/reporting tools
    ├── check_*.py         # ✅ Verification tools
    ├── verify_*.py        # ✅ Verification tools
    ├── cleanup_scripts.py # ✅ Cleanup utility
    └── archive/           # ⚠️  36 archived one-time scripts
        ├── README.md      # Explains why archived
        └── *.py           # Old scripts (DO NOT USE)
```

---

## Quick Reference Card

**Most Common Operations**:

```bash
# Remove tickets from sprint
uv run python jira_update.py --jql "status='To Do' AND sprint=1012" --sprint null

# Add story points
uv run python jira_update.py --tickets BH-150-200 --story-points 3

# Update status
uv run python jira_update.py --tickets BH-150-160 --status "In Progress"

# Fetch latest data
uv run python fetch_all_issues.py
```

**Remember**: Use `--dry-run` first!

---

## When to Create New Scripts

**Only create new scripts when**:
1. The operation is **fundamentally different** from updating tickets
2. It requires **complex business logic** beyond field updates
3. It's a **reporting/analysis** tool that needs to be run regularly

**Examples of valid new scripts**:
- Analytics reports (ticket velocity, team performance)
- Data migration tools
- Integration scripts (sync with external systems)
- Validation/audit scripts

**NOT valid reasons**:
- "I need to update tickets in Sprint 2" (use `jira_update.py --sprint 2`)
- "I need to assign tickets to a new person" (use `jira_update.py --assignee`)
- "I need to add labels to security tickets" (use `jira_update.py --add-labels`)

---

**Last Updated**: 2026-01-19
**Maintainer**: Hikuri Chinca (Bado)
**Review**: End of each sprint to cleanup unnecessary scripts
