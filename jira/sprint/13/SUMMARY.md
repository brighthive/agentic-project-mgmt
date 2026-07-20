# Sprint 13 — Routines, Signals & Trust Hardening
**Period**: June 23 – July 20, 2026 (28 days) | **Unofficial** (no Jira sprint object)

---

## Stats

```
┌─────────────────────────────────────────────────────────────┐
│  Sprint 13 — Routines, Signals & Trust Hardening            │
│  June 23 – July 20, 2026 · 28 days                          │
├──────────────────────────────┬──────────────────────────────┤
│  PRs Merged (total)          │  579                         │
│  Feature/Fix PRs             │  499                         │
│  Staging release carriers    │  80                          │
│  Lines changed               │  +355,423 / -91,481          │
│  Repos touched               │  6 (of 7 scanned)             │
├──────────────────────────────┼──────────────────────────────┤
│  Tickets (scope)             │  446 in window                │
│    Done                      │  141                         │
│    Needs Refinement          │  235 (merged, not transitioned)│
│    Code Review               │  25                          │
│    Staging QC                │  18                          │
│    Testing (Dev)             │  8                           │
│    Ready for Staging         │  4                           │
│    In Progress               │  4                           │
│    To Do                     │  4                           │
│    Blocked                   │  2                           │
│    Canceled                  │  5                           │
│  Story Points                │  43 / 43 (only 13 tickets estimated) │
├──────────────────────────────┼──────────────────────────────┤
│  Ticket range                │  BH-737 → BH-1137            │
└──────────────────────────────┴──────────────────────────────┘
```

---

## Goals Assessment

| Goal | Status | Evidence |
|------|--------|----------|
| BrightRoutines end-to-end | ✅ | Epic BH-876 (108 sub-tickets, 64 Done): detector, schedulability judge, ownership model, Slack cards, e2e coverage |
| BrightSignals maturation | ✅ | Signal Catalog refactor (BH-1124–1129 all Done), notification preferences (BH-1106), unread-count fix (BH-980/981) |
| Longaeva trust hardening | ⚠️ | Grounding/disambiguation tickets (BH-758–761) still Needs Refinement; MCP tool-contract fixes (BH-780–833) largely unresolved |
| Monitoring Agents | ⚠️ | Watchdog poller + auto-remediation loop reached Staging QC (BH-1043–1054) but epic BH-1036 mostly Needs Refinement (23 sub-tickets, only 1 Done) |
| Skills Extension Framework | ✅ | Epic BH-860 fully Done (14/14 sub-tickets) — SSIS/SSRS diagnostics shipped and staged |
| PII enforcement sweep | ⚠️ | P0 bug BH-1078 and follow-through epic BH-1084 still Needs Refinement — masking sweep not yet closed out |
| Semantic View lifecycle fixes | ⚠️ | 13 sub-tickets under BH-624, only 1 Done — most MCP/GraphQL parity bugs still open |

---

## PR ↔ Ticket Linkage Report

| Category | Count |
|----------|-------|
| Feature/fix PRs merged | 499 |
| PRs with BH-XXX ref in title/branch | 385 |
| Staging release-carrier PRs (excluded from ref-matching) | 80 |
| Remaining unmatched (non-carrier) PRs | 133 |

Unmatched PRs are mostly small fixes, docs, CI, or merge-commit noise (`Merge pull request #713…`, `dev => staging (08/07/2026)`, `docs(claude): staging session learnings`) — consistent with the pattern in Sprint 12. Full breakdown in `VALIDATION_REPORT.md`.

---

## Team Breakdown

| Member | PRs (feature) | Tickets Done | Tickets in pipeline | Key themes |
|--------|---------------|--------------|----------------------|------------|
| Kuri   | 417 | 74  | 230 | BrightRoutines, BrightSignals/Signal Catalog, monitoring agents, PII enforcement, lineage, MCP fixes |
| Harbour | 71  | 54  | 3   | Skills Extension Framework, notification preferences, catalog/UX bug sweep, quality-check fixes |
| Marwan | 88  | 0 (assigned Done not observed) | 16  | Studio agent fixes, Bedrock timeout retry, visualization multi-panel, notification footer |
| Ahmed  | 3   | 0   | 7   | Warehouse default-flag property, OnboardDataAsset workflow, ingestion sources |

Note: 13 tickets show "Unassigned" among Done (likely closed by whoever picked up the retroactive sweep) and 37 Unassigned in the active pipeline.

---

## Carried-Over / Still-Open Tickets

Largest open clusters heading into Sprint 14:

- **BH-1036 (Monitoring Agents)** — 22 of 23 sub-tickets still open; watchdog poller/auto-remediation reached Staging QC but the epic as a whole isn't closed.
- **BH-601 (Longaeva 14 Golden Paths)** — grounding, disambiguation, and hallucination P0s (BH-758–761, BH-776–777 Blocked) unresolved.
- **BH-624 (Semantic View lifecycle)** — 12 of 13 sub-tickets open; MCP/GraphQL tool-contract parity bugs (BH-792, BH-796, BH-807, BH-823, BH-831–833) unresolved.
- **BH-1084 (PII enforcement follow-through)** — the whole epic plus its P0 origin bug (BH-1078) still Needs Refinement.
- **BH-1061 (Lineage-Aware Data Quality)** — 9 of 10 sub-tickets open; Snowflake/Databricks lineage adapters not yet built.
- **BH-835 (Analytics Dashboard)** — 13 of 14 sub-tickets open; dashboard still mock-wired.

---

## Problems Identified

1. **Ticket linkage gap (recurring, 3rd sprint running)**: 235 tickets sit in "Needs Refinement" despite associated PRs already merged — same pattern flagged in Sprint 11/12. This is now a process debt, not a one-off.
2. **Estimation coverage near-zero**: only 13 of 446 tickets carry story points. Velocity tracking is effectively unusable across three consecutive unofficial sprints.
3. **No formal sprint object, third sprint running**: date-range cuts keep losing sprint-goal context in Jira itself. The recommendation from Sprint 12 ("create a Jira Sprint 13 object") wasn't acted on.
4. **Concentration risk unchanged**: Kuri authored 417 of 579 PRs (72%) and touched 230 of the open pipeline tickets. Same key-person risk flagged last sprint, still unaddressed.
5. **Several epics opened but far from closed**: BH-1036, BH-624, BH-1061, BH-835, BH-1084 were all created or expanded mid-sprint and remain mostly in Needs Refinement — scope is growing faster than it's closing.
6. **Two Blocked tickets on the analyst grounding path** (BH-776, BH-777) — a P0-adjacent trust issue (hallucinated/slow answers) with no resolution path recorded.

---

## Recommendations for Sprint 14

1. **Create a real Jira Sprint 14 object before starting work** — this is the third unofficial sprint in a row; the tracking gap compounds each cycle.
2. **Run a ticket-transition sweep**: 235 Needs Refinement tickets need a pass to mark actually-shipped work Done — 30–45 minutes, high leverage for future velocity numbers.
3. **Add story points retroactively to at least the Done tickets** from this window (128 have none) to restore a velocity baseline.
4. **Close out BH-1036 (Monitoring Agents)** — the watchdog/remediation core is in Staging QC; finish the epic instead of letting scope drift into Sprint 14.
5. **Prioritize the two Blocked analyst-trust tickets (BH-776, BH-777)** — these sit on the Longaeva PoC's credibility path and have been open since June 24.
6. **Distribute PII enforcement work (BH-1084)** — a P0 security bug (BH-1078) has been open since July 13 with no apparent owner movement; needs explicit prioritization.
7. **Same key-person-risk recommendation as Sprint 12**: onboard Harbour/Marwan onto Routines/Signals/monitoring-agent domains to reduce Kuri's 72%-of-PRs concentration.
