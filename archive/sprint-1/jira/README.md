# BrightHive Jira - Rust CLI Only 🦀

**CRITICAL**: This is a **Rust-only project**. NO Python scripts allowed.

All Jira operations use the unified Rust CLI: **`jira-ticket`**

---

## For Claude

**When working with Jira, you MUST:**
- ✅ Use `jira-ticket` CLI commands
- ❌ NEVER write Python scripts
- ❌ NEVER use `uv run python`
- ❌ NEVER create one-time scripts

**The only tool**: `jira-ticket` (installed at `~/.cargo/bin/jira-ticket`)

---

## Files Structure

```
jira/
├── README.md                    # This file
├── scripts/
│   ├── README.md               # Rust CLI guide
│   ├── epic_dates_mapping.json # Q1 2026 milestone mappings
│   └── EPIC_DATES_SUMMARY.md   # Epic dates documentation
├── sprint_1_snapshot.json      # Sprint 1 historical data
├── sprint_2_snapshot.json      # Sprint 2 historical data
└── *.json                      # Various Jira data exports
```

---

## Quick Reference

### Interactive Ticket Creation (User)
```bash
# Magical wizard mode
jira-ticket

# Tasks require epic linking + dates
jira-ticket create
```

### Batch Operations (Claude/Automation)
```bash
# Update tickets
jira-ticket update --tickets BH-150-160 --status "In Progress"
jira-ticket update --jql "sprint=1012 AND status='To Do'" --sprint null
jira-ticket update --tickets BH-150 --story-points 5 --add-labels security

# Sprint management
jira-ticket sprint create --name "Sprint 2" --start-date 2026-01-27 --end-date 2026-02-07
jira-ticket sprint start 1012
jira-ticket sprint complete 1012 --move-to 1013
jira-ticket sprint fetch --sprint 1012 --output sprint_1_snapshot.json

# Always dry-run first
jira-ticket update --tickets BH-150-160 --status "Done" --dry-run
```

---

## Common Operations for Claude

### Remove tickets from sprint
```bash
jira-ticket update --jql "status='To Do' AND sprint=1012" --sprint null --dry-run
jira-ticket update --jql "status='To Do' AND sprint=1012" --sprint null
```

### Add story points
```bash
jira-ticket update --jql "sprint=1012 AND 'Story Points'=null" --story-points 3 --dry-run
jira-ticket update --jql "sprint=1012 AND 'Story Points'=null" --story-points 3
```

### Move tickets to status
```bash
jira-ticket update --tickets BH-150-160 --status "In Progress" --dry-run
jira-ticket update --tickets BH-150-160 --status "In Progress"
```

### Add labels
```bash
jira-ticket update --jql "summary~'security'" --add-labels security,pentest --dry-run
jira-ticket update --jql "summary~'security'" --add-labels security,pentest
```

### Update epic dates
```bash
jira-ticket update --tickets BH-110 --start-date 2026-01-13 --end-date 2026-02-28 --dry-run
jira-ticket update --tickets BH-110 --start-date 2026-01-13 --end-date 2026-02-28
```

### Fetch sprint data for historical tracking
```bash
jira-ticket sprint fetch --sprint 1012 --output sprint_1_snapshot.json
jira-ticket sprint fetch --sprint 1013 --output sprint_2_snapshot.json
```

### Create new sprint
```bash
jira-ticket sprint create --name "Sprint 3" --start-date 2026-02-03 --end-date 2026-02-14
```

### Start/Complete sprint
```bash
jira-ticket sprint start 1013
jira-ticket sprint complete 1012 --move-to 1013
```

---

## Why Rust Only?

✅ **Single tool** - No script proliferation
✅ **Type safety** - Rust catches errors at compile time
✅ **Performance** - 10x faster than Python
✅ **No dependencies** - No Python/uv environment
✅ **Consistent** - Same patterns for all operations
✅ **Better errors** - Clear messages with context

---

## Installation

```bash
cd /Users/bado/iccha/jira-wizard
cargo build --release
cargo install --path .
```

Binary: `~/.cargo/bin/jira-ticket`

---

## Configuration

Uses jira-tui config: `~/.config/jiratui/config.yaml`

```yaml
jira_api_base_url: "https://brighthiveio.atlassian.net"
jira_api_username: "your-email@brighthive.io"
jira_api_token: "your-api-token"
```

---

## Historical Sprint Data

Sprint snapshots are saved as JSON for historical tracking:
- `sprint_1_snapshot.json` - Sprint 1 full data
- `sprint_2_snapshot.json` - Sprint 2 full data
- Future sprints follow same pattern

Fetch with: `jira-ticket sprint fetch --sprint <id> --output <file>`

---

**Last Updated**: 2026-01-19
**Maintained by**: Hikuri Chinca (Bado)
- `backlog.md` - See all epics and ready work
- `active-tickets.md` - Track current sprint (manual updates)
- `completed.md` - Archive finished work (manual updates)

## Workflow

### Daily/Weekly Updates

1. **Start of sprint**: Move tickets from `backlog.md` to `active-tickets.md`
2. **During sprint**: Update status in `active-tickets.md` as work progresses
3. **End of sprint**: Move completed tickets to `completed.md`
4. **Refresh from Jira**: Run `fetch_all_issues.py` to sync latest state

### Across Sessions

When starting a new Claude Code session for BrightHive work:

1. Open `/Users/bado/iccha/brighthive/context.md` to get project overview
2. Check `jira/backlog.md` for epics and upcoming work
3. Review `jira/active-tickets.md` for current sprint status
4. Reference `ARCHITECTURE.md` for technical context
5. Check `decisions.md` for past architectural decisions

## Jira Configuration

Jira credentials are stored in: `~/.config/jiratui/config.yaml`

```yaml
jira_api_base_url: https://brighthiveio.atlassian.net
jira_api_username: kuri@brighthive.io
jira_api_token: <token>
```

## Current State (2026-01-12)

- **Current Milestone**: M1 - End of January (Target: Jan 31)
- **Current Sprint**: Sprint 1 (Jan 13-24, 2026) - REFOCUSED
- **Sprint 1 Focus**: Data lake context engineering design (NOT user-facing features)
- **Sprint 1 Tasks**: 20 tasks across 4 epics (+2 bonus)
- **Critical Path**: 15 tasks for 2-week sprint
- **M1 Total Tasks**: 55 tasks across 5 epics
- **10 Epics**: Mapped to 4 milestones (Q1 2026)

## Structure

**Hierarchy**: Epics → Tasks (no stories layer)

Each epic contains a list of actionable tasks that can be tracked and completed.

### Strategic Epics (Q1 2026)

1. Context Engineering Architecture (BH-110)
2. Proactive Multi Agents (BH-111)
3. Custom Tailored Personas Insights (BH-112)
4. Internal improvements - Performance/Monitoring (BH-113)
5. UX WebApp Re-design (BH-114)
6. Interconnect-ability - Source & Destinations (BH-115)
7. Projects & automations tasks (BH-116)
8. Non-technical BH Omni integrations (BH-117)
9. Workspace/Orgs usage & pricing reporting (BH-118)
10. Big Data Highly Complex Tasks (BH-119)

## Links

- **Jira Project**: https://brighthiveio.atlassian.net/projects/BH
- **Jira Board**: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards
