# Claude Navigation Guide - Agentic Project Management

**Purpose**: How Claude navigates the project management repository for coordination and reporting.

---

## Quick Answer Table

| Question | Location |
|----------|----------|
| **What's this sprint's plan?** | `sprint/sprint-1/PLAN.md` |
| **Who's working on what?** | `jira/ASSIGNMENTS_SUMMARY.md` or `jira/SPRINT_1_ASSIGNMENTS.md` |
| **What's the board status?** | `jira/JIRA_STATUS.md` |
| **What changed this sprint?** | `sprint/sprint-1/CHANGES_SUMMARY.md` |
| **Release notes?** | `sprint/sprint-1/RELEASE_NOTES.md` |
| **How to sync Jira?** | `jira/QUICKSTART.md` |
| **Sprint automation?** | `sprint/SPEC_SPRINT_AUTOMATION.md` |
| **System architecture?** | `../platform-saas-ai-context/docs/architecture/` |
| **Team ownership?** | `../platform-saas-ai-context/docs/team/TEAM.md` |
| **Quarterly roadmap?** | `../platform-saas-ai-context/docs/roadmap/ROADMAP.md` |

---

## Repository Purpose

This is the **Ephemeral Project Management** repository:

- **Scope**: Sprint planning, Jira tracking, assignments, release notes
- **Lifecycle**: Changes weekly (not permanent)
- **Update Frequency**: Daily during sprints, weekly syncs
- **Archive Pattern**: Complete sprints → `sprint/archive/`
- **Paired With**: `platform-saas-ai-context/` (permanent SaaS knowledge)

---

## Navigation Patterns for Claude

### **Scenario 1: Get Current Sprint Status**
1. Read `sprint/sprint-1/PLAN.md` (sprint goals)
2. Read `jira/JIRA_STATUS.md` (board health)
3. Read `jira/ASSIGNMENTS_SUMMARY.md` (team capacity)
4. Reference `../platform-saas-ai-context/docs/roadmap/ROADMAP.md` (milestone context)

### **Scenario 2: Find Team Assignments**
1. Read `jira/SPRINT_1_ASSIGNMENTS.md` (current sprint)
2. Check `jira/ASSIGNMENTS_SUMMARY.md` (summary view)
3. Cross-reference with `../platform-saas-ai-context/docs/team/TEAM.md` (expertise areas)

### **Scenario 3: Generate Status Report**
1. Read current sprint plan: `sprint/sprint-1/PLAN.md`
2. Get board status: `jira/JIRA_STATUS.md`
3. Check assignments: `jira/ASSIGNMENTS_SUMMARY.md`
4. Reference roadmap: `../platform-saas-ai-context/docs/roadmap/ROADMAP.md`
5. Compile report from these sources

### **Scenario 4: Plan Next Sprint**
1. Review current roadmap: `../platform-saas-ai-context/docs/roadmap/ROADMAP.md`
2. Check backlog in Jira board
3. Review retrospectives from last sprint
4. Create new `sprint/sprint-N/PLAN.md`
5. Generate assignments using team capacity data

### **Scenario 5: Generate Release Notes**
1. Get changes: `sprint/sprint-N/CHANGES_SUMMARY.md`
2. Get app changelogs: `sprint/sprint-N/changelogs/`
3. Use: `sprint/sprint-N/RELEASE_NOTES.md` (main)
4. Cross-check with: `sprint/sprint-N/MARKETING_RELEASE_NOTES.md` (customer-facing)

### **Scenario 6: Understand System Before Planning**
1. Go to: `../platform-saas-ai-context/`
2. Read: `docs/architecture/ARCHITECTURE.md`
3. Read: `docs/team/TEAM.md`
4. Read: `docs/roadmap/ROADMAP.md`
5. Return to this repo for specific sprint planning

---

## Key Files Reference

### **Sprint Directory** (`sprint/`)

| File | Purpose | Size | Content |
|------|---------|------|---------|
| `sprint-1/PLAN.md` | Sprint 1 goals, tickets, dependencies | ~10KB | Goals, milestones, blockers |
| `sprint-1/CHANGES_SUMMARY.md` | What changed in Sprint 1 | ~5KB | Feature summary per app |
| `sprint-1/RELEASE_NOTES.md` | Release notes for Sprint 1 | ~3KB | Technical release info |
| `sprint-1/MARKETING_RELEASE_NOTES.md` | Customer-facing release notes | ~2KB | Business-focused summary |
| `sprint-1/changelogs/` | Per-app release notes | ~20KB | App-specific changes |
| `AUTOMATION.md` | Sprint automation guide | ~3KB | How automation works |
| `SPEC_SPRINT_AUTOMATION.md` | Automation specifications | ~5KB | Technical specs |

### **Jira Directory** (`jira/`)

| File | Purpose | Size | Update |
|------|---------|------|--------|
| `ASSIGNMENTS_SUMMARY.md` | Current team assignments | ~5KB | Weekly |
| `SPRINT_1_ASSIGNMENTS.md` | Sprint 1 specific assignments | ~3KB | Sprint start |
| `JIRA_STATUS.md` | Board status & health | ~4KB | Daily |
| `SPRINT_1_READY.md` | Sprint readiness checklist | ~2KB | Pre-sprint |
| `FINAL_SPRINT_SETUP.md` | Setup verification | ~3KB | After setup |
| `snapshots/sprint_1_snapshot.json` | Board snapshot | ~50KB | As needed |
| `snapshots/*.md` | Human-readable snapshots | ~20KB | As needed |

---

## Context Loading Strategy

### **Quick Status** (Use for daily updates)
- Load: `jira/JIRA_STATUS.md` + `jira/ASSIGNMENTS_SUMMARY.md`
- Size: ~10KB
- Time: <1 second
- Use: "What's the current board status?"

### **Sprint Overview** (Use for sprint planning)
- Load: `sprint/sprint-1/PLAN.md` + `jira/JIRA_STATUS.md` + assignments
- Size: ~25KB
- Time: ~1 second
- Use: "What's this sprint about?"

### **Full Report** (Use for comprehensive status)
- Load: All sprint files + Jira snapshots + platform-saas-ai-context roadmap
- Size: ~100KB
- Time: ~2 seconds
- Use: "Generate complete sprint status report"

### **Deep Context** (Use for architectural questions)
- Load: This repo + `platform-saas-ai-context/` docs
- Size: ~400KB
- Time: ~3 seconds
- Use: "How does sprint X impact architecture?"

---

## File Organization

```
agentic-project-mgmt/
├── README.md                     # Entry point
├── CLAUDE.md                     # This file
├── .gitignore                    # Git rules
│
├── sprint/                       # 📋 Sprint planning & tracking
│   ├── AUTOMATION.md
│   ├── SPEC_SPRINT_AUTOMATION.md
│   ├── sprint-1/                # Current/Recent sprint
│   │   ├── PLAN.md             # Start here for sprint goals
│   │   ├── CHANGES_SUMMARY.md
│   │   ├── RELEASE_NOTES.md
│   │   ├── MARKETING_RELEASE_NOTES.md
│   │   ├── changelogs/         # App-specific notes
│   │   └── ...
│   ├── sprint-2/                # Next sprint (TBD)
│   └── archive/                 # Completed sprints
│
├── jira/                        # 🔗 Jira board integration
│   ├── QUICKSTART.md           # Start here for Jira
│   ├── ASSIGNMENTS_SUMMARY.md  # Current assignments
│   ├── SPRINT_1_ASSIGNMENTS.md
│   ├── JIRA_STATUS.md
│   ├── snapshots/              # Board snapshots
│   ├── scripts/                # Automation scripts
│   └── jira_lib/               # Jira Python library
│
└── notion/                      # 📝 Notion integration
    └── [Product specs, requirements, meeting notes]
```

---

## Best Practices for Claude

1. **Always start with README.md** - Get oriented first
2. **Use Quick Answer table** at top for specific questions
3. **Know the scope** - Ephemeral project management (NOT permanent architecture)
4. **Reference platform-saas-ai-context** - For architecture/team/roadmap context
5. **Check update frequency** - Don't rely on stale data
6. **Use snapshots for historical data** - JSON files have complete board state
7. **Cross-reference** - Sprint plans reference architecture, roadmap

---

## Common Workflows for Claude

### **Daily Standup Report**
1. Load: `jira/JIRA_STATUS.md` + `jira/ASSIGNMENTS_SUMMARY.md`
2. Format: Who's assigned, status, blockers
3. Output: Daily standup summary

### **Sprint Status Report**
1. Load: `sprint/sprint-1/PLAN.md` + `jira/JIRA_STATUS.md`
2. Compare: Goals vs progress
3. Output: Weekly sprint status

### **Release Notes Generation**
1. Load: `sprint/sprint-1/CHANGES_SUMMARY.md` + app changelogs
2. Format: Per-app features and fixes
3. Output: Release notes (technical + marketing)

### **Team Capacity Planning**
1. Load: `jira/ASSIGNMENTS_SUMMARY.md` + team expertise from platform-saas-ai-context
2. Analyze: Current load vs capacity
3. Output: Capacity recommendations for next sprint

### **Sprint Retrospective**
1. Gather: Sprint goals, actual progress, blockers, learnings
2. Output: Retrospective summary for team discussion

---

## Connecting to Other Repositories

### **platform-saas-ai-context**
- **Path**: `../platform-saas-ai-context/`
- **When to reference**:
  - Understanding system architecture
  - Finding team expertise/ownership
  - Quarterly roadmap context
  - Technical decisions affecting sprints
- **Key files**:
  - `docs/architecture/ARCHITECTURE.md` - System design
  - `docs/team/TEAM.md` - Team structure
  - `docs/roadmap/ROADMAP.md` - Quarterly planning

### **App Repositories** (brighthive-platform-core, brightbot, etc.)
- **When to reference**:
  - Understanding sprint ticket dependencies
  - Connecting to code changes
  - App-specific deployment notes
  - Release notes and changelogs

---

## What NOT to Do in This Repo

- ❌ Store code (goes in app repos)
- ❌ Store permanent architecture docs (goes in platform-saas-ai-context)
- ❌ Commit `.venv/` or cache files
- ❌ Store sensitive credentials
- ❌ Mix sprint data with architecture
- ❌ Use as source of truth for system design

---

## Context Quality Notes

### **Reliable Data**
- ✅ Sprint plans (captured at sprint start)
- ✅ Jira snapshots (point-in-time exports)
- ✅ Release notes (generated after sprint)
- ✅ Assignments (updated at sprint start/mid-sprint)

### **Real-Time Data**
- 🔄 Jira board status (check board for latest)
- 🔄 Ticket details (check Jira for current state)
- 🔄 Daily blockers (check standup notes)

### **Historical Data**
- 📚 Past sprints (in `sprint/archive/`)
- 📚 Old snapshots (in `jira/snapshots/`)
- 📚 Release history (in `sprint/sprint-N/`)

---

## Maintenance & Updates

### **During Sprint**
- `jira/JIRA_STATUS.md` - Updated daily
- `jira/ASSIGNMENTS_SUMMARY.md` - Updated weekly
- Jira board snapshots - Generated weekly

### **End of Sprint**
- Generate `sprint/sprint-N/RELEASE_NOTES.md`
- Generate `sprint/sprint-N/RETROSPECTIVE.md`
- Archive completed sprint to `sprint/archive/`

### **Between Sprints**
- Plan next sprint in Jira
- Create `sprint/sprint-N+1/PLAN.md`
- Create `sprint/sprint-N+1/ASSIGNMENTS.md`

---

## Tips for Effective Use

1. **Always cross-reference** with platform-saas-ai-context for system understanding
2. **Check update frequency** - Some data changes daily, some weekly
3. **Use Jira board** as source of truth (not these snapshots for real-time)
4. **Archive old sprints** to keep repo clean
5. **Commit sprint changes** with `chore(sprint):` prefix
6. **Keep summaries** updated for quick reference

---

## Quick Links

- 📋 [Sprint Plan](sprint/sprint-1/PLAN.md) - Current sprint goals
- 📊 [Board Status](jira/JIRA_STATUS.md) - Current board health
- 👥 [Assignments](jira/ASSIGNMENTS_SUMMARY.md) - Team assignments
- 🚀 [Release Notes](sprint/sprint-1/RELEASE_NOTES.md) - What shipped
- 🏗️ [System Architecture](../platform-saas-ai-context/docs/architecture/ARCHITECTURE.md) - System design
- 👤 [Team Structure](../platform-saas-ai-context/docs/team/TEAM.md) - Team roles
- 🗺️ [Roadmap](../platform-saas-ai-context/docs/roadmap/ROADMAP.md) - Quarterly planning

---

**Last Updated**: 2026-01-22
**Repository Type**: Ephemeral Project Management
**Paired With**: platform-saas-ai-context (Permanent SaaS Context)
**Update Frequency**: Daily during sprints, weekly syncs

---

## Remember

**This repo is for "What are we doing THIS sprint?"**
**SaaS context repo is for "What are we building? How does it work?"**

Always reference both for complete context.
