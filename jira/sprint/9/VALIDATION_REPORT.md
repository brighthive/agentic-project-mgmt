# Sprint 9 — Validation Report

**Period**: Apr 20 – May 2, 2026

---

## PR ↔ Ticket Linkage

| Metric | Count | % |
|--------|-------|---|
| Total PRs | 27 | 100% |
| Matched (BH-XXX in branch/title/body) | 11 | 41% |
| Unmatched | 16 | 59% |

**Trend**: Up from 34% in Sprint 8 mid-sprint. Still below the 70% target.

---

## Done Tickets Without Linked PRs

All 7 Done tickets have linked PRs (Kuri's `drchinca/BH-XXX/...` branch convention is consistent).

| Ticket | Status |
|--------|--------|
| BH-431 | Linked |
| BH-432 | Linked |
| BH-437 | Linked |
| BH-438 | Linked |
| BH-439 | Linked |
| BH-440 | Linked |
| BH-441 | Linked |

✅ No orphan tickets this sprint.

---

## Orphan PRs (merged but not matched to any ticket)

| PR | Repo | Author | Title |
|----|------|--------|-------|
| #745 | platform-core | Kuri | build: Develop => Staging (4/20/2026) — *promotion PR, not feature* |
| #746 | platform-core | Harbour | fix(upload): Add duplicate check to data asset and files |
| #748 | platform-core | Ahmed | fix: prevent duplicate data asset creation for mixed-case filenames |
| #749 | platform-core | Ahmed | Develop => Staging — *promotion PR* |
| #750 | platform-core | Harbour | feat(scheduler): MVP agnostic scheduler |
| #751 | platform-core | Harbour | Merge develop => staging — *promotion PR* |
| #16 | slack-server | Kuri | feat(brightsignals): proactive Slack notifications |
| #17 | slack-server | Kuri | docs(brightsignals): rebrand product surfaces |
| #18 | slack-server | Kuri | feat(notifications): surface asset UUID in Slack messages |
| #19 | slack-server | Kuri | docs(brightsignals): operator install + ops guide |
| #20 | slack-server | Kuri | feat(attachments): s3:// URI support |
| #21 | slack-server | Kuri | feat(attachments): parse <BH_ARTIFACTS> envelope |
| #22 | slack-server | Kuri | fix(ci): complete Pulumi config |
| #1076 | webapp | Harbour | feat(analytics): Add schedule support to UI |
| #1077 | webapp | Harbour | fix(upload): Add duplicate check to data asset and files |
| #1079 | webapp | Harbour | feat(scheduler): MVP agnostic scheduler |
| #1080 | webapp | Marwan | fix(ag-grid): pass serverSideDatasource as prop |
| #1081 | webapp | Harbour | Merge develop => staging — *promotion PR* |
| #457 | brightbot | Marwan | fix: migrate ChatBedrock to ChatBedrockConverse |
| #458 | brightbot | Harbour | feat: MVP agnostic scheduler |
| #459 | brightbot | Harbour | Merge develop => staging — *promotion PR* |
| #144 | data-org-cdk | Marwan | Staging => Main (4/8/2026) — *promotion PR* |
| #152 | data-org-cdk | Ahmed | Develop => Staging — *promotion PR* |
| #153 | data-org-cdk | Ahmed | Update: synapse logic with docs, role assumption |

**Categorization**:
- 6 promotion PRs (build: develop → staging → main) — expected to be unticketed
- BrightSignals (8 PRs) — major feature with no tickets created. Should have an epic + per-PR tickets.
- Task Scheduler (3 PRs across repos) — major feature with no tickets created. Should have a single tracking ticket.
- Bedrock Converse migration (1 PR) — strategic technical migration with no ticket. Should have a ticket linked to BH-271 / Bedrock epic.
- Bug fixes (5 PRs: duplicate check, AG Grid, mixed-case dedup) — small fixes commonly skipped for tickets. OK.

**Net assessment**: After excluding promotion PRs (6), the actual unmatched feature work is ~10 PRs. Most relate to **3 large untracked initiatives** (BrightSignals, Scheduler, Bedrock Converse) that should have epic-level tickets.

---

## Branch Naming Compliance

| Author | Pattern | Compliance |
|--------|---------|------------|
| Kuri | `drchinca/BH-XXX/desc` or `drchinca/BH-feat/desc` | High (always uses `BH` prefix) |
| Marwan | Mixed: `fix/bedrock-converse-migration-and-deepagents-upgrade` | Low |
| Harbour | `task-scheduler`, `duplicate-check`, `catalog-schedule` | Zero |
| Ahmed | `update/synapse-support-logic-and-docs`, `fix/sync-data-asset-duplicate-on-mixed-case-name` | Zero |

**Recurring gap**: Same as Sprint 7, Sprint 8 — only Kuri uses ticket-prefixed branches.

---

## Estimation Gaps

All 7 done tickets have **0 story points**. Same as Sprint 8 — points-based velocity is broken.

---

## Recommendations

1. **Create epic-level tickets for BrightSignals, Scheduler, and Bedrock Converse migration** retroactively. These are flagship Q2 deliverables invisible in Jira today.
2. **Standardize branch naming**: enforce `<author>/<BH-XXX>/<desc>` for all 4 engineers via PR template + CI check.
3. **Point the 7 streaming tickets retroactively**: BH-431, BH-432 are 5pt features; BH-437–441 are 3pt fixes/tests. ~30 points uncaptured.
4. **Sprint 8 needs to formally close in Jira**: It expired Apr 28 but is still active. Sprint 9 work overlaps Sprint 8 — both reference the same code.
