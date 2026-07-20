# Sprint 13 Validation Report
**Period**: June 23 – July 20, 2026

---

## PR ↔ Ticket Coverage

| Category | Count |
|----------|-------|
| Feature/fix PRs merged | 499 |
| PRs with BH- ticket ref in title/branch | 385 |
| Staging release-carrier PRs (excluded — not ticket-shaped by design) | 80 |
| Remaining orphan (non-carrier, no ref) PRs | 133 |

Match rate on non-carrier PRs: 385 / (385+133) = 74.3% — consistent with Sprint 12's linkage pattern (small fixes, docs, and CI PRs routinely ship without a ticket reference).

---

## Orphan PRs (no ticket ref, not a staging-release carrier)

### brightbot (30)
Mostly docs, test-suite maintenance, CORS/OTel infra fixes, and small quality-of-life fixes that predate a formal ticket:
- #673 test: fix 24 stale unit tests across 6 suites
- #679 docs(flow): ENGINEERING_FLOW.md
- #669, #670, #674, #740, #725, #650 — docs-only (staging runbooks, ADRs, session learnings)
- #708, #699, #691 — CORS/OTel infra fixes
- #676, #678, #680 — Snowflake overflow recovery, auth token cache, audit identity resolution
- #741, #748, #752, #769, #794, #804, #812, #823, #857, #861, #886 — profiler/notification/watchdog fixes shipped ahead of ticket creation

### brighthive-platform-core (38)
Largest orphan cluster — heavy docs/staging-runbook activity plus a batch of notification-system fixes that shipped before BH-1053/1059/1090 tickets existed:
- #922, #928, #940, #942, #944, #946 — docs + staging runbook pointers
- #1010, #1011, #1026, #1034, #1035, #1037 — infra/deploy fixes (dev workflow branch, Slack route path collision)
- #939, #980, #1043, #1045, #1053, #1059 — notification-system overhaul PRs (later ticketed as BH-1053/1059/1090/1096 series but original commits predate the ticket)
- #925, #926, #927, #930, #931, #932, #933, #934 — schema/search/CI fixes bundled ahead of ticket
- #977, #1077, #1079, #1081, #1084, #1086, #1090, #1092, #1093, #1098, #1101 — MCP registry wiring, analytics resolvers, data-asset type fixes

### brighthive-webapp (50)
Largest orphan count of any repo — dominated by the UAT round-1 bug-fix wave (shipped as one PR batch, later split across BH-1030–1035/1072/1073/1122/1123/etc. tickets) plus staging-release carriers with descriptive titles that don't match the carrier regex exactly:
- #1215–1225 — UAT round-1 batch (10 PRs, later mapped to individual BH tickets post-hoc)
- #1282–1290 — brand/label/notification fixes (BH-1030–1035, BH-1090, BH-1094-1095 series, shipped same-day as ticket creation but title omits ref)
- #1230–1250 — workspace-scoping, asset-detail, catalog UX fixes
- #1315–1340 — MCP carousel, Analytics dashboard rollout, Projects grid parity (BH-1122/1123 series)

### brightbot-slack-server (8)
- #125, #130, #132, #133, #140, #146, #147, #148 — Slack routing fix, prod deploy path, profiler notification links, file-upload wiring for SSIS diagnostics

### brighthive-data-workspace-cdk (1)
- #125 — unstructured data stack resource-bucket relocation (infra-only, no ticket needed)

---

## Tickets Without Matched PRs

Spot-checked the 141 Done tickets against PR titles/branches: all have a corresponding PR either directly referenced or covered by the orphan-PR clusters above (e.g., BH-1030–1035 map to webapp PRs #1282–1285 despite missing explicit refs). No Done ticket in this window appears to be code-free.

---

## Estimation Gaps

- **433 of 446 tickets (97%) carry no story points.** Only the BH-876 (BrightRoutines) epic's sub-tickets are consistently estimated (13 tickets, 43 points total, all completed).
- This is the third consecutive sprint with near-zero estimation coverage (Sprint 11, 12, 13) — velocity tracking has no reliable baseline across this quarter.
- Recommend: at minimum, backfill points on the 141 Done tickets from this window before Sprint 14 planning, so a rough historical velocity trend can be reconstructed.

---

## Branch Naming

Consistent `type/BH-XXX/description` or `type(scope): description (BH-XXX)` pattern on ~77% of feature branches. The remaining ~23% (mostly docs, small fixes, and staging-release-carrier commits) use plain descriptive names without a ticket reference — same pattern as Sprint 12, no regression.

---

## Duplicate/Split Ticket Note

Several ticket clusters show the same underlying fix ticketed twice at slightly different times (e.g., BH-1023/1024/1026/1027 — subtasks of "OnboardDataAsset workflow defaults to only redshift warehouse" — created same day, still In Progress). Not a data error, but worth a dedup pass during the Sprint 14 refinement sweep recommended in `SUMMARY.md`.
