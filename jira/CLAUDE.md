# Jira Sprint Tracking

## Structure

```
jira/
├── sprint/
│   ├── SPRINTS.md      # All sprints summary
│   ├── 1/
│   │   ├── stats.json  # Metrics (deterministic)
│   │   ├── tickets.json# Ticket list
│   │   └── SUMMARY.md  # Analysis (LLM-generated)
│   ├── 2/
│   └── 3/
└── scripts/            # Jira API scripts
```

## Files

### stats.json (deterministic)
Machine-readable metrics computed from Jira:
- `dates`: start, end, duration
- `tickets`: total, completed, in_progress, to_do, testing, out_of_scope
- `points`: total, completed, remaining
- `completion`: tickets_pct, points_pct
- `goals`: sprint objectives
- `team`: members
- `carry_over`: from_previous, to_next, ticket list
- `out_of_scope`: removed tickets
- `wip_analysis`: avg_hours, avg_days, by_ticket, distribution

### tickets.json
Minimal ticket data: key, summary, status, assignee, points

### SUMMARY.md (LLM-generated)
Analysis including:
- ASCII stats table
- WIP analysis with red flags
- Team breakdown
- Problems identified
- Recommendations

## Sprint Close Process

1. Export tickets from Jira → `tickets.json`
2. Compute metrics → `stats.json`
3. Generate analysis → `SUMMARY.md`
4. Update → `SPRINTS.md`
