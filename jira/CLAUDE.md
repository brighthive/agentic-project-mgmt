# Claude Instructions - Jira Sprint Tracking

## Directory Structure

```
jira/
├── CLAUDE.md           # This file
├── sprint/
│   ├── SPRINTS.md      # Top-level summary (human-readable)
│   ├── 1/              # Sprint 1
│   │   ├── stats.json  # Deterministic metrics
│   │   ├── tickets.json# Raw ticket data
│   │   └── SUMMARY.md  # LLM-generated analysis
│   ├── 2/
│   ├── 3/
│   └── N/
├── active.json         # Current sprint tickets from Jira API
├── completed.json      # Done tickets
├── ready.json          # Backlog
└── epics.json          # Epics
```

---

## File Purposes

### Deterministic Files (Machine-generated)

**`stats.json`** - Computed from Jira data, never manually edited:
```json
{
  "sprint": 3,
  "dates": {"start": "2026-01-27", "end": "2026-02-03", "duration_days": 7},
  "tickets": {"total": 23, "completed": 12, "in_progress": 1, ...},
  "points": {"total": 30, "completed": 13, "remaining": 17},
  "completion": {"tickets_pct": 52.2, "points_pct": 43.3},
  "goals": ["Goal 1", "Goal 2"],
  "team": ["Hikuri", "Marwan"],
  "carry_over": {"from_previous": 4, "to_next": 4, "tickets": ["BH-XXX"]},
  "out_of_scope": {"count": 1, "tickets": ["BH-YYY"]},
  "wip_analysis": {
    "avg_days": 6.4,
    "by_ticket": [{"key": "BH-199", "days": 19.6, "status": "Done", "flag": "multi-sprint"}],
    "distribution": {"under_1_day": 1, "1_to_3_days": 2, "4_to_7_days": 4, "over_7_days": 6}
  }
}
```

**`tickets.json`** - Raw ticket list from Jira:
```json
[
  {"key": "BH-206", "summary": "...", "status": "Done", "assignee": "Harbour", "points": 3}
]
```

### LLM-Generated Files

**`SUMMARY.md`** - Analysis and insights:
- ASCII stats table
- WIP analysis with red flags
- Problems identified
- Team breakdown
- Recommendations
- What worked / what didn't

**`SPRINTS.md`** - Quick reference of all sprints

---

## How to Generate Sprint Summary

### 1. Gather Data
```bash
# Export from Jira API (or use existing JSON)
cat active.json completed.json | jq ...
```

### 2. Create stats.json
Compute deterministic metrics:
- Count tickets by status
- Sum story points
- Calculate completion percentages
- Extract WIP times from Jira transitions

### 3. Generate SUMMARY.md
Using stats.json, generate analysis:

```markdown
# Sprint N Summary

## Final Stats
[ASCII table from stats.json]

## WIP Analysis
[Red flags for tickets > 7 days in WIP]
[Distribution histogram]

## Problems Identified
[LLM analysis of patterns]

## Recommendations
[Actionable next steps]
```

---

## WIP Analysis Rules

### Flags
- `quick-win`: < 1 day in WIP
- `normal`: 1-3 days
- `full-sprint`: 4-7 days
- `multi-sprint`: > 7 days (RED FLAG)
- `stuck`: In Testing > 3 days

### Distribution Buckets
```
< 1 day:   Quick wins
1-3 days:  Normal flow
4-7 days:  Full sprint items
7+ days:   Problem tickets
```

---

## Sprint Close Process

When a sprint ends:

1. **Export Jira data** → `active.json`, `completed.json`
2. **Compute stats** → `sprint/N/stats.json`
3. **Copy tickets** → `sprint/N/tickets.json`
4. **Generate summary** → `sprint/N/SUMMARY.md`
5. **Update index** → `sprint/SPRINTS.md`

---

## Queries for Claude

### Quick Status
> "What's the current sprint completion rate?"
→ Read `sprint/SPRINTS.md` or latest `stats.json`

### WIP Analysis
> "Which tickets took too long?"
→ Read `stats.json` → `wip_analysis.by_ticket` where `flag` != null

### Team Load
> "Who has the most in progress?"
→ Read `active.json`, group by assignee

### Sprint Health
> "Is this sprint on track?"
→ Compare current date vs `dates.end`, tickets done vs total

### Generate Retrospective
> "Create sprint 3 retro"
→ Read `sprint/3/stats.json` + `SUMMARY.md`, synthesize insights

---

## Anti-Patterns

**Don't**:
- Manually edit `stats.json` (regenerate from source)
- Include full Jira descriptions in `tickets.json` (keep minimal)
- Store sensitive data (no tokens, passwords)
- Duplicate data between files

**Do**:
- Keep `stats.json` as single source of truth for metrics
- Use `SUMMARY.md` for human-readable insights
- Update `SPRINTS.md` after each sprint close
- Archive old sprints (keep structure)

---

## Integration Points

- **Jira API**: Source for `active.json`, `completed.json`
- **Notion**: Sprint planning pages link to these summaries
- **Slack**: Status updates pull from `SPRINTS.md`
- **Retrospectives**: Generated from `SUMMARY.md`
