# Agentic Project Management Repository

**Purpose**: Complete project management, sprint tracking, and workflow automation for BrightHive.

> **Note**: This is the **ephemeral project data** repository. For permanent SaaS architectural knowledge, see the `platform-saas-ai-context` repository.

---

## 🎯 What Is This Repository?

This repository contains all time-bound, project-specific information for BrightHive:

- **Sprint tracking** - Plans, assignments, progress
- **Jira automation** - Jira board syncing, scripting, dashboards
- **Notion integration** - Product specs, meeting notes, requirements
- **Agentic workflows** - AI-powered project coordination tools
- **Changelogs** - Release notes and version history
- **Retrospectives** - Post-sprint analysis and learnings

**Key Principle**: Everything here is **ephemeral** (changes weekly). Sprint data is archived, not permanent.

---

## 📚 Repository Structure

```
agentic-project-mgmt/
│
├── README.md                        # This file
├── CLAUDE.md                        # Claude navigation guide
├── .gitignore                       # Git exclusions
│
├── sprint/                          # Sprint Management
│   ├── AUTOMATION.md               # Sprint automation docs
│   ├── SPEC_DRIVEN_DEV_README.md  # Spec-driven development
│   ├── SPEC_IMPLEMENTATION_MAP.md  # Spec to implementation mapping
│   ├── SPEC_SPRINT_AUTOMATION.md  # Automation strategies
│   ├── scripts/                    # Sprint automation scripts
│   │
│   ├── sprint-1/                   # Sprint 1 (Jan 13-24, 2026)
│   │   ├── PLAN.md                # Sprint plan
│   │   ├── CHANGES_SUMMARY.md     # Summary of changes
│   │   ├── changelogs/            # Release notes per app
│   │   ├── RELEASE_NOTES.md       # Sprint 1 release notes
│   │   ├── MARKETING_RELEASE_NOTES.md  # Customer-facing notes
│   │   └── INDEX.md               # Sprint overview
│   │
│   ├── sprint-2/                   # Sprint 2 (Upcoming)
│   │   └── [TBD]
│   │
│   └── archive/                    # Completed sprints
│       └── SPRINT_1_REVISION.md    # Revision notes
│
├── jira/                            # Jira Integration & Automation
│   ├── README.md                   # Jira setup guide
│   ├── CLAUDE.md                   # Jira context for Claude
│   ├── QUICKSTART.md               # Quick start guide
│   ├── DASHBOARD_SETUP.md          # Dashboard configuration
│   │
│   ├── config/                     # Jira configuration
│   │   └── README.md               # Config documentation
│   │
│   ├── scripts/                    # Automation scripts
│   │   ├── epic_dates_mapping.json
│   │   ├── EPIC_DATES_SUMMARY.md
│   │   ├── MIGRATION_SUMMARY.md
│   │   └── README.md
│   │
│   ├── jira_lib/                   # Jira Python library
│   │   └── README.md               # Library documentation
│   │
│   ├── snapshots/                  # Board snapshots (JSON)
│   │   ├── sprint_1_snapshot.json
│   │   ├── sprint_1_active.md
│   │   ├── sprint_1_tickets.json
│   │   └── ...
│   │
│   ├── ASSIGNMENTS_SUMMARY.md      # Current team assignments
│   ├── SPRINT_1_READY.md          # Sprint readiness checklist
│   ├── SPRINT_1_ASSIGNMENTS.md    # Sprint 1 team assignments
│   ├── JIRA_STATUS.md             # Current board status
│   ├── FINAL_SPRINT_SETUP.md      # Sprint setup verification
│   │
│   ├── [Active/Completed/Backlog Snapshots]
│   ├── [Epic Snapshots]
│   ├── [Ticket JSON Exports]
│   └── [Audit & Tracking Data]
│
├── notion/                          # Notion Integration
│   ├── README.md                   # Notion setup guide
│   └── [Product specs, meeting notes, requirements]
│
├── lastpass-vault/                  # Secrets Management
│   ├── data/                       # Encrypted credential storage
│   └── [LastPass integration files]
│
└── .github/                         # GitHub Actions & CI/CD
    └── workflows/
        └── sprint-release.yml      # Sprint release automation
```

---

## 🎯 Key Workflows

### **Sprint Management**

```bash
# View Sprint 1 plan
cat sprint/sprint-1/PLAN.md

# See current assignments
cat jira/SPRINT_1_ASSIGNMENTS.md

# Check sprint status
cat jira/JIRA_STATUS.md

# View release notes
cat sprint/sprint-1/RELEASE_NOTES.md
```

### **Jira Automation**

```bash
# Quick start
cat jira/QUICKSTART.md

# Sync with Jira board
cd jira
uv venv
source .venv/bin/activate
uv run python scripts/sync_jira.py

# Generate board snapshot
uv run python scripts/export_board.py
```

### **Team Communication**

```bash
# Current assignments
cat jira/ASSIGNMENTS_SUMMARY.md

# Retrospectives
cat sprint/sprint-N/RETROSPECTIVE.md

# Release notes (customer-facing)
cat sprint/sprint-N/MARKETING_RELEASE_NOTES.md
```

---

## 📊 Current Sprint Status

**Sprint 1**: Jan 13-24, 2026
- **Status**: In Progress
- **Focus**: Data Lake Context Engineering + Security Remediation
- **Team**: Hikuri (Backend), Ahmed (DevOps), Marwan (Frontend)
- **Tickets**: 62 total (20 design, 20 completed, 16 pending refinement)

**See**:
- Sprint Plan: `sprint/sprint-1/PLAN.md`
- Assignments: `jira/SPRINT_1_ASSIGNMENTS.md`
- Board Status: `jira/JIRA_STATUS.md`
- Release Notes: `sprint/sprint-1/RELEASE_NOTES.md`

---

## 🔗 Related Repositories

### **platform-saas-ai-context** (SaaS Knowledge)
**Purpose**: Permanent architectural knowledge
**Location**: `../platform-saas-ai-context/` or https://github.com/brighthive/platform-saas-ai-context

**Contains**:
- System architecture
- Team structure & ownership
- Quarterly roadmap
- Technical decisions (ADRs)

**Use When**: Understanding system design, making architectural decisions, onboarding new engineers

### **brighthive-platform-core** (Backend)
**Purpose**: Backend application code
**Location**: `../brighthive-platform-core/` or https://github.com/brighthive/brighthive-platform-core

**Contains**:
- Node.js backend code
- GraphQL API
- Neo4j integration

### **Other App Repositories**
- `brighthive-webapp` - Frontend
- `brightbot` - AI agents
- `brighthive-data-*` - Infrastructure

---

## 📋 Quick Reference

### **Common Questions**

| Question | Answer |
|----------|--------|
| What's this sprint's plan? | See `sprint/sprint-1/PLAN.md` |
| Who's working on what? | See `jira/ASSIGNMENTS_SUMMARY.md` |
| What's the Jira board status? | See `jira/JIRA_STATUS.md` |
| What changed in Sprint 1? | See `sprint/sprint-1/CHANGES_SUMMARY.md` |
| What are release notes? | See `sprint/sprint-1/RELEASE_NOTES.md` |
| How do I sync Jira? | See `jira/QUICKSTART.md` |
| What's the system architecture? | See `platform-saas-ai-context/docs/architecture/ARCHITECTURE.md` |
| Who owns the backend? | See `platform-saas-ai-context/docs/team/TEAM.md` |
| What are we building this quarter? | See `platform-saas-ai-context/docs/roadmap/ROADMAP.md` |

### **Key Files**

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `sprint/sprint-N/PLAN.md` | Sprint plan | Start of sprint |
| `jira/ASSIGNMENTS_SUMMARY.md` | Team assignments | Weekly |
| `jira/JIRA_STATUS.md` | Board status | Daily |
| `sprint/sprint-N/RELEASE_NOTES.md` | Sprint releases | End of sprint |
| `sprint/sprint-N/RETROSPECTIVE.md` | Post-sprint analysis | After sprint ends |
| `jira/snapshots/*.json` | Board snapshots | As needed |

---

## 🤖 For Claude (AI Context)

This repository is designed for **project management automation** using agentic tools:

**When Working Here**:
1. Read `CLAUDE.md` for navigation
2. Check current sprint directory for plans/status
3. Reference Jira snapshots and assignments
4. Use for coordinating with AI agents

**When to Reference platform-saas-ai-context**:
1. Understanding system design
2. Finding team ownership
3. Making architectural decisions
4. Architectural context

**Never Put Here**:
- Code (goes in app repos)
- System architecture docs (goes in platform-saas-ai-context)
- Permanent team structure (goes in platform-saas-ai-context)

---

## 📝 Agentic Workflows

This repository is set up to support agentic project management:

### **Jira Sync Agent**
- Syncs between Jira board and local snapshots
- Tracks ticket changes over time
- Generates reports and summaries

### **Sprint Planning Agent**
- Helps plan sprints based on capacity
- Suggests ticket assignments
- Tracks sprint progress

### **Release Notes Agent**
- Generates release notes from commits
- Tracks app changelog updates
- Creates customer-facing summaries

### **Retrospective Agent**
- Collects sprint feedback
- Analyzes blockers and learnings
- Generates retrospective reports

See `sprint/AUTOMATION.md` and `sprint/SPEC_SPRINT_AUTOMATION.md` for details.

---

## 🚀 Getting Started

### **View Current Sprint**
```bash
cat sprint/sprint-1/PLAN.md
cat jira/ASSIGNMENTS_SUMMARY.md
```

### **Check Team Capacity**
```bash
cat jira/SPRINT_1_ASSIGNMENTS.md
```

### **See Board Status**
```bash
cat jira/JIRA_STATUS.md
```

### **Review Releases**
```bash
cat sprint/sprint-1/RELEASE_NOTES.md
```

### **Setup Jira Automation**
```bash
cd jira
cat QUICKSTART.md
```

---

## 🔄 Context Lifecycle

### **During Sprint**
- Daily: Update Jira board
- Weekly: Generate status snapshots
- Weekly: Update ASSIGNMENTS_SUMMARY.md

### **End of Sprint**
- Generate RELEASE_NOTES.md
- Create RETROSPECTIVE.md
- Archive sprint data
- Close Jira sprint

### **Between Sprints**
- Refine backlog in Jira
- Plan next sprint
- Update ROADMAP.md in platform-saas-ai-context

### **Quarterly**
- Review quarterly roadmap
- Plan next quarter
- Archive old sprints

---

## 📚 Documentation

### **Sprint-Specific**
- `sprint/sprint-1/` - Sprint 1 data
- `sprint/sprint-2/` - Sprint 2 data (upcoming)
- `sprint/archive/` - Completed sprints

### **Jira**
- `jira/QUICKSTART.md` - Get started with Jira automation
- `jira/DASHBOARD_SETUP.md` - Configure dashboards
- `jira/scripts/` - Automation scripts
- `jira/snapshots/` - Historical board data

### **Automation**
- `sprint/AUTOMATION.md` - Sprint automation docs
- `sprint/SPEC_SPRINT_AUTOMATION.md` - Automation specifications

---

## 🔗 Key Links

| Resource | Purpose |
|----------|---------|
| **Jira Board** | https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152 |
| **Jira Project** | https://brighthiveio.atlassian.net/projects/BH |
| **SaaS Context Repo** | `../platform-saas-ai-context/` |
| **Platform Core** | `../brighthive-platform-core/` |

---

## 🎓 For Different Roles

### **Scrum Master / PM**
1. View `sprint/sprint-1/PLAN.md` for sprint overview
2. Check `jira/ASSIGNMENTS_SUMMARY.md` for team capacity
3. Review `jira/JIRA_STATUS.md` for blockers
4. Generate `sprint/sprint-1/RELEASE_NOTES.md` as sprint ends

### **Team Members**
1. Check `jira/SPRINT_1_ASSIGNMENTS.md` for your tickets
2. Reference Jira board for daily status
3. Review sprint plan: `sprint/sprint-1/PLAN.md`
4. Submit sprint retrospective feedback

### **Product Manager**
1. Check roadmap in `platform-saas-ai-context/docs/roadmap/ROADMAP.md`
2. View release notes: `sprint/sprint-1/RELEASE_NOTES.md`
3. Plan next sprint in Jira board

### **Platform Lead (Hikuri)**
1. Review sprint status: `jira/JIRA_STATUS.md`
2. Update roadmap progress in platform-saas-ai-context
3. Guide team through sprint planning
4. Review retrospectives

---

## ✅ Workflow Checklist

### **Sprint Planning**
- [ ] Create sprint in Jira
- [ ] Create `sprint/sprint-N/PLAN.md`
- [ ] Assign tickets to team
- [ ] Generate `jira/SPRINT_N_ASSIGNMENTS.md`

### **During Sprint**
- [ ] Update Jira board daily
- [ ] Generate weekly snapshots
- [ ] Track blockers and dependencies
- [ ] Update `jira/JIRA_STATUS.md` as needed

### **Sprint Closure**
- [ ] Generate `sprint/sprint-N/RELEASE_NOTES.md`
- [ ] Generate `sprint/sprint-N/RETROSPECTIVE.md`
- [ ] Update app changelogs
- [ ] Archive sprint data
- [ ] Close Jira sprint

### **Post-Sprint**
- [ ] Update roadmap in platform-saas-ai-context
- [ ] Plan next sprint
- [ ] Share learnings with team

---

## 🚫 What NOT to Do

- ❌ Don't store code here (goes in app repos)
- ❌ Don't store architecture docs here (goes in platform-saas-ai-context)
- ❌ Don't commit old Jira `.venv/` directories
- ❌ Don't store sensitive credentials (use secrets management)
- ❌ Don't mix sprint data with permanent docs (keep them separate)

---

## 🤝 Contributing

### **Updating Sprint Data**
1. Update relevant sprint directory
2. Commit with `chore(sprint):` prefix
3. Example: `chore(sprint): update sprint-1 assignments`

### **Adding New Sprint**
1. Create `sprint/sprint-N/` directory
2. Copy template from previous sprint
3. Update sprint plan and assignments
4. Commit with `chore(sprint): create sprint-N plan`

### **Jira Automation**
1. Update scripts in `jira/scripts/`
2. Test with: `uv run python scripts/test.py`
3. Commit with `chore(jira):` prefix

---

## ⚙️ Technical Setup

### **Dependencies**
```bash
cd jira
uv venv
source .venv/bin/activate
uv pip install requests pyyaml # Or see jira/requirements.txt
```

### **Environment Variables**
```bash
export JIRA_URL="https://brighthiveio.atlassian.net"
export JIRA_USER="your-email@brighthive.io"
export JIRA_TOKEN="your-jira-api-token"
```

### **Running Scripts**
```bash
cd jira
uv run python scripts/sync_board.py
uv run python scripts/generate_report.py
```

---

## 📞 Support

- **Questions about sprint?** Check `sprint/sprint-N/PLAN.md`
- **Jira help?** See `jira/QUICKSTART.md`
- **Automation issues?** Check `sprint/SPEC_SPRINT_AUTOMATION.md`
- **Architecture questions?** See `platform-saas-ai-context/`

---

**Last Updated**: 2026-01-22
**Repository Focus**: Ephemeral Project Management
**Related**: platform-saas-ai-context (Permanent SaaS Context)
**For Questions**: See Slack #engineering or create an issue
