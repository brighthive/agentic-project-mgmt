# Sprint 14 🍯 — Validation Report (July 21 – Aug 1, 2026)

PR ↔ ticket linkage, orphan detection, and data-quality flags for the Sprint 14
date-range cut.

## Method

- **PRs**: `gh pr list --state merged --search "merged:2026-07-21..2026-08-01"` across
  all core repos → 82 merged PRs.
- **Tickets**: Jira JQL on resolution/status-change date in the same window → 28 resolved
  (27 Done, 1 Canceled), plus 10 in flight.
- **Matching**: branch name → PR title → PR body → Jira dev-status fallback.

## Headline

| Check | Result |
|---|---|
| PRs merged | 82 |
| — code PRs | 62 |
| — release/promotion PRs (excluded from code stats) | 20 |
| Tickets resolved in window | 28 |
| PR-to-ticket match rate (code PRs) | ~60% branch/title carry `BH-XXX` |
| Orphan PRs (no ticket) | See below — mostly release + infra chores |
| Done tickets with no linked PR | See below |

## ⚠️ Linkage gaps

**Done tickets whose code shipped without a `BH-XXX`-tagged branch.**
This is the standing pattern (flagged Sprints 11–13): work ships via PR, the ticket flips
to Done afterward, and the branch often doesn't carry the key. Not a correctness problem —
a traceability one. Notable:
- The BH-1181 MCP-hardening family (13 tickets) landed largely in **brightbot** PRs whose
  branches name the fix, not the ticket. brightbot is not in the 5 repos this cut's code
  stats cover (those are platform-core/webapp/apm/e2e/platform-saas-ai-context) — the
  brightbot MCP PRs are tracked by ticket, not re-counted here.
- Harbour's BH-1154→1162 UX sweep: branches are descriptive (`fix/asset-switch-label`),
  tickets linked in PR body.

**Recommendation:** enforce `BH-XXX` in branch names or PR titles so date-range and
dev-status agree. This is the single highest-leverage traceability fix and has been
open since Sprint 11.

## ⚠️ Estimation gaps

- **27 of 28 resolved tickets are unpointed.** Only BH-233 (2 pts, still To Do) carries an
  estimate. The team measures by PRs + resolved tickets, not story points — so velocity
  can't be trended as points/sprint. Accepted team practice, flagged for visibility.

## ⚠️ Process flags

- **No Jira sprint object** for this window — fourth unofficial sprint in a row (11–14).
  Completion %, carry-over, and velocity are all reconstructed from date ranges, not read
  from a sprint board. **Open a formal sprint object before the Sprint 15 cut.**
- **Line-count honesty**: 20 release/promotion PRs (`chore(release)` / `Develop => Staging`)
  re-merge entire branches; one alone shows +262k. All per-person and total code figures in
  `stats.json` / `SUMMARY.md` **exclude** these — reported code delta is +41,813 / −4,316.
- **Canceled, not failed**: BH-1188 (Neo4j onboard-hang lock contention) was investigated by
  Harbour and retired as superseded — counted as resolved-Canceled, not as delivered work.

## ✅ Clean signals

- All 3 BH-1280 warehouse-health PRs (platform-core #1146, webapp #1387, e2e #72) shipped
  with real-behavior tests (13 resolver tests + 7 hook tests + 3-engine ground-truth
  fixtures) and reached staging by sprint end.
- The BH-1036 lineage chain shipped across platform-core + webapp with a boot-time schema
  guardrail (#1130) so an invalid directive enum can't crash staging again.
- Marwan's schema-file slice is fully paired: platform-core #1144/#1148 ↔ webapp #1377/#1383.
