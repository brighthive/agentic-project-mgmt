# Sprint 12 — Validation Report

**Window:** 2026-06-03 → 2026-06-16 · PR↔ticket matching is best-effort (branch/title/body `BH-XXX` scan).

## Linkage Summary

| Check | Result |
|-------|--------|
| Merged PRs in window | 268 |
| Feature/fix PRs | 235 |
| Release-carrier PRs (staging→main) | 33 — excluded from line totals to avoid double-count |
| Tickets Done | 18 |
| Tickets in Code-Review/Staging-QC | 27 |

## Notes & Red Flags

- **High PR-to-ticket ratio.** 235 feature PRs vs 46 active tickets — many BH-526/601/624 children ship across several PRs (spec → impl → test → release), and a large share of slack-server / platform-core PRs are refactor/test/infra work not individually ticketed. Expected for a heavy build sprint.
- **28 tickets stacked in review/QC.** Largest single risk: needs the pre-trial staging deploy to drain before Longaeva Day 1, or it becomes a carryover crunch.
- **54 Needs-Refinement** filed this window are backlog grooming (BH-601 golden cases, BH-624 lifecycle children), not regressions — they are specced, not started.
- **Longaeva exclusion is narrow** (Sprint 11 precedent): platform capability counted here; PoC-completeness/scorecard narrative tracked in `clients/trials/longaeva/TRACKER.md`.

## Estimation Gaps

- Story points not set on most BH-526/601/624 children (`customfield_10016` null). Velocity computed on ticket counts, not points, for this cut.
