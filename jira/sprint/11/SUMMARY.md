# Sprint 11 Summary 🧪

**Window**: May 15 → June 2, 2026 (18 days)
**Status**: Unofficial sprint cut — counted forward from Sprint 10 (May 5–15). Sprint 7 was the last formal Jira sprint object; we've been running cut-by-merge since.
**Exclusions**: Longaeva PoC work (epic BH-526, Snowflake integration, poc_tracker scaffolding) is tracked separately under `clients/trials/longaeva/TRACKER.md` and is not counted in this release.

---

## At a glance

```
┌─────────────────────────────────────────────────────────────┐
│ Sprint 11 🧪 — Profiler + Permissions Cut                   │
├─────────────────────────────────────────────────────────────┤
│ Tickets in scope:        19                                 │
│ Done:                     7  (36.8%)                        │
│ Staging QC:               2                                 │
│ Needs Refinement:        10  (carries to Sprint 12)         │
│ Done + QC pipeline:       9  (47.4%)                        │
├─────────────────────────────────────────────────────────────┤
│ PRs merged:              27                                 │
│  · feature/fix:          23                                 │
│  · staging release PRs:   4                                 │
│ Lines changed (real):    15,183                             │
│ Repos touched:            3  (webapp · platform-core ·      │
│                                brightbot)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Themes

1. **Data Profiler agent goes online** — ported onto develop, auto-triggered on ingestion, registered as a schedulable batch task, and surfaced in the scheduler UI. Now runnable on demand or on a cron. (BH-498, BH-501, BH-520)
2. **Navigation + permissions hardening** — enterprise dashboard restructure landed (BH-376), with five surgical role-guard and route fixes from Harbour. The whole nav stack is now correct under collaborator/admin/viewer. (BH-376, BH-513, BH-514, BH-515, BH-516, BH-517, BH-556)
3. **BrightStudio collaborator unlock** — agent CRUD permissions extended from `WORKSPACE_ADMIN` to `prohibits: [VIEWER, CONTRIBUTOR, GUEST]`. Collaborators can now manage custom agents. (BH-548)
4. **Quality check → BrightSignals wiring** — quality run completion now publishes to Slack via the BrightSignals notifications channel. (BH-530)
5. **Local-dev parity** — comprehensive seed data + mocks across platform-core and webapp; workspace-aware BrightBot requests; thread validation. Onboarding and PR review just got dramatically faster.
6. **Production hotfixes** — BrightAgent S3 streaming + mem0 hotfix, AG Grid aria sidebar fix.

---

## Goals assessment

| Goal | Status |
|---|---|
| Data Profiler runnable on demand + auto-trigger on ingestion | ✅ Shipped (PRs landed, BH-501/BH-520 in QC) |
| Nav restructure + permission correctness across roles | ✅ 5 BH-51x tickets Done, BH-376 in QC |
| BrightStudio collaborators can manage agents | ✅ BH-548 PR merged |
| Quality results visible in Slack | ✅ BH-530 notifications PR merged |
| Local-dev experience for seed data + mocks | ✅ Shipped (PR #774, #1119) |

---

## Team breakdown

| Member | Done | In Pipeline | Notable |
|---|---|---|---|
| Harbour Wang | 7 | 2 (Staging QC) | All nav/permission fixes; profiler scheduler UI; collaborator-perms fix |
| Kuri Chinca | 0 | 4 | BH-376 nav restructure (huge), profiler port, runtime feature flags, local-dev seeds — all in Needs Refinement state, PRs merged but tickets not transitioned |
| Marwan Samih | 0 | 1 | BH-530 GX YAML notifications + prod hotfixes |
| Ahmed Elsherbiny | 0 | 1 | BH-502 profiler E2E verification (in flight) |
| Unassigned | — | 4 | BH-491 Settings phase 1, BH-495 Coming Soon previews, BH-497 BrightAgent Vite/MUI, BH-548 collab perms |

**Red flag**: 10 tickets are in **Needs Refinement** despite their PRs being merged. The work is shipped — the tickets need transitioning. This pattern (Done-by-PR but not Done-by-Jira) is the same linkage gap that hurt Sprint 6.

---

## PR ↔ ticket linkage

| | Count |
|---|---|
| PRs with `BH-XXX` in branch/title/body | 23 |
| PRs without ticket link (release carriers + hotfixes) | 4 |
| Tickets with linked merged PR | 14 |
| Tickets Done with merged PR | 7 |
| Tickets in Needs Refinement with merged PR | 7 |

The 4 PRs without a ticket link are: 2 staging release PRs (#1113, #1115, #1117, #773), and 2 hotfixes (#483, #1103) where the work pre-dated ticket creation.

---

## What carries to Sprint 12

- **10 tickets in Needs Refinement** — all need a transition pass. Most are `Done-by-PR`.
- **BH-359** Platform Analytics dashboard — still untouched
- **BH-491 / BH-495 / BH-497** — Settings, Coming Soon, BrightAgent Vite/MUI — all unassigned
- **BH-502** profiler E2E — Ahmed in flight

---

## Recommendations

1. **Transition pass on Sprint 11 tickets**: 10 tickets need to move from Needs Refinement → Done where the PR has merged. ~15-min sweep.
2. **Assign the 4 unassigned tickets** (BH-491, 495, 497, 548) before Sprint 12 plan — three are bug fixes that should land fast.
3. **Formalize Sprint 12 in Jira** as a real sprint object so we stop "cut by merge date" and resume real velocity tracking.
4. **PR-title discipline**: 2 hotfixes shipped without ticket linkage. A 30-second JIRA chore before a hotfix would close the linkage gap completely.
