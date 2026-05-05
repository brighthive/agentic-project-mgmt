# Sprint 9 — Validation Report (v2)

**Period**: Apr 20 – May 4, 2026
**Update**: v2 May 4 — extended cutoff + 10 retro tickets created and transitioned to Done.

---

## PR ↔ Ticket Linkage (v2)

| Metric | v1 (May 2) | v2 (May 4) |
|--------|------------|------------|
| Total PRs | 27 | 39 |
| Feature PRs | 22 | 28 |
| Build/Promotion PRs | 5 | 11 |
| Matched (BH-XXX) | 11 (41%) | 21 (54%) |
| Unmatched feature PRs | 11 (50%) | 7 (25%) |

**Trend**: PR-ticket linkage rose from 41% → 54% after retro ticket creation. Unmatched feature PRs dropped from 11 to 7.

---

## Done Tickets (17 total)

### Original 7 (resolved Apr 25 - May 2)
BH-431, BH-432, BH-437, BH-438, BH-439, BH-440, BH-441 — all Kuri's streaming/adapter work, all PR-linked via `drchinca/BH-XXX/...` branch convention.

### Retro 10 (created May 2-4, transitioned May 4)
BH-443 → BH-452 — see `tickets.json` for full mapping.

✅ **All 17 Done tickets have linked PRs.** Zero orphan tickets.

---

## Remaining Orphan PRs (build/promotion + minor cleanup)

| PR | Repo | Author | Title | Category |
|----|------|--------|-------|----------|
| #745 | platform-core | Kuri | build: Develop => Staging (4/20) | Promotion |
| #749 | platform-core | Ahmed | Develop => Staging | Promotion |
| #751 | platform-core | Harbour | Merge develop => staging | Promotion |
| #753 | platform-core | Harbour | dev => staging | Promotion |
| #1081 | webapp | Harbour | Merge develop => staging | Promotion |
| #1084 | webapp | Harbour | dev => staging | Promotion |
| #459 | brightbot | Harbour | Merge develop => staging | Promotion |
| #461 | brightbot | Harbour | dev => staging | Promotion |
| #144 | data-org-cdk | Marwan | Staging => Main | Promotion |
| #152 | data-org-cdk | Ahmed | Develop => Staging | Promotion |
| #24 | slack-server | Kuri | Promote develop to staging | Promotion |
| #736 | platform-core | Kuri | fix(slack): make createSlackServiceUser idempotent | Minor cleanup |
| #17 | slack-server | Kuri | docs(brightsignals): rebrand product surfaces | Docs |
| #18 | slack-server | Kuri | feat(notifications): surface asset UUID in Slack | Could be sub-ticket of BH-447 |
| #19 | slack-server | Kuri | docs(brightsignals): operator install + ops guide | Docs |
| #22 | slack-server | Kuri | fix(ci): complete Pulumi config | CI cleanup |
| #16 | slack-server | Kuri | feat(brightsignals): proactive Slack notifications | **MAJOR** — BrightSignals epic ticket pending |
| #23 | slack-server | Kuri | feat(uat): direct-call deterministic turn evals | **MAJOR** — UAT framework ticket pending |
| #456 | brightbot | Kuri | feat(visualization): render Vega-Lite to PNG | **MAJOR** — Visualization ticket pending |
| #20 | slack-server | Kuri | feat(attachments): s3:// URI support (Tier A) | Could be sub-ticket of BrightSignals |
| #21 | slack-server | Kuri | feat(attachments): <BH_ARTIFACTS> envelope (Tier B) | Could be sub-ticket of BrightSignals |
| #747 | platform-core | Kuri | feat(notifications): dispatcher Lambda | Could be sub-ticket of BrightSignals |

**Categorization**:
- 11 promotion PRs — expected, excluded from linkage rate
- ~5 minor cleanup/docs PRs — typically skipped for tickets
- **3 major Kuri-shipped initiatives still without epic tickets**: BrightSignals, UAT eval framework, Vega-Lite visualization

**Recommendation**: Kuri to create 3 epic-level tickets:
1. **BrightSignals** epic (under BH-172) — link 8 slack-server PRs + dispatcher Lambda
2. **UAT eval framework** epic (under BH-170 SDLC) — slack-server #23
3. **Vega-Lite visualization** epic (under BH-172) — brightbot #456

---

## Branch Naming Compliance (v2)

| Author | Pattern | Compliance |
|--------|---------|------------|
| Kuri | `drchinca/BH-XXX/desc` or `drchinca/BH-feat/desc` | High (always uses `BH` prefix) |
| Marwan | Mixed: `fix/bedrock-converse-migration-and-deepagents-upgrade` | Low |
| Harbour | `task-scheduler`, `agent-skills`, `catalog-improvements`, `login-fix` | Zero |
| Ahmed | `update/synapse-support-logic-and-docs`, `fix/sync-data-asset-duplicate-on-mixed-case-name` | Zero |

**Recurring gap**: Same as Sprint 7, Sprint 8 — only Kuri uses ticket-prefixed branches. Retro tickets compensate but don't fix the upstream behavior.

---

## Estimation Coverage (v2)

| Source | Tickets | Pointed |
|--------|---------|---------|
| Original 7 (streaming) | 7 | 0 |
| Retro 10 (BH-443..452) | 10 | 10 (39 pts total) |
| **Total** | **17** | **10 (59%)** |

**Improvement**: From 0 pointed in v1 to 59% pointed in v2 (via retro ticket estimation by Kuri).

---

## Recommendations (v2)

1. **Kuri to create 3 missing epic tickets** (BrightSignals, UAT framework, Vega-Lite). Linkage will jump from 54% → ~85%.
2. **Retro the 7 streaming tickets** with point estimates: BH-431, 432 = 5pt features; BH-437–441 = 3pt fixes/tests. Adds ~30 points.
3. **Standardize branch naming** across all 4 engineers — PR template + CI check. This is the only mechanism that fixes the Marwan/Harbour/Ahmed pattern at source.
4. **Sprint 8 needs to formally close in Jira this week.** Sprint 9 fully overlaps Sprint 8's tail end + 6 days post-end.
5. **Capture going-forward**: each cross-repo feature should have a parent ticket *before* the first PR — even if it's a stub.
