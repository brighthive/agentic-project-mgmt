# Sprint 8 --- Mid-Sprint Checkpoint

**Period**: Apr 14--28, 2026 | **Duration**: 14 days | **Checkpoint**: Apr 20, 2026
**Sprint Goal**: Governance context tools, Azure Synapse integration, dbt agent GitHub commits, ticket hygiene

---

## Sprint Stats

```
+-------------------------------------------------+
|         SPRINT 8 --- MID-SPRINT CHECKPOINT       |
|           Apr 14 -- Apr 28, 2026 (14d)          |
+-----------------------+-------------------------+
| Tickets Completed     |  21 / 55        (38.2%) |
| Story Points Done     |  5 / 41 pts     (12.2%) |
| Unpointed Done        |  19 of 21 Done tickets  |
| PRs Merged            |  103 (82 feat + 21 build)|
| Repos Touched         |  7                      |
| In Progress           |  4                      |
| Code Review           |  2                      |
| Testing (Dev)         |  4                      |
| Staging QC            |  3                      |
| Ready for Staging     |  7                      |
| To Do                 |  8                      |
| Needs Refinement      |  9 (dbt provisioning)   |
| Canceled              |  10 (excluded from %)   |
+-----------------------+-------------------------+
```

**WARNING**: 19 of 21 Done tickets have no story points. The 12.2% points completion is meaningless -- the real signal is 38.2% ticket completion at mid-sprint, which is on track.

---

## Goals Assessment

| Goal | Status | Evidence |
|------|--------|----------|
| Governance context tools | IN PROGRESS | BH-357 Done, BH-347 in Code Review. Policies inject into context, on-demand schema/glossary/policy tools built. |
| Azure Synapse integration | IN PROGRESS | BH-322 (T-SQL dialect) Done, BH-285 (ingestion pipeline) In Progress, BH-251 (quality check) In Progress. E2E tests written. |
| dbt agent GitHub commits | SHIPPED | BH-325-346 cluster all Done. Full dbt workflow: jobs, repos, model metadata, DAG detail view, ReAct agent migration. |
| Ticket hygiene | PARTIAL | 10 tickets canceled (backlog cleanup), but 19/21 Done tickets unpointed -- estimation discipline still lacking. |

---

## PR <-> Ticket Linkage

```
+-------------------------------------------------+
|            PR-TICKET LINKAGE REPORT              |
+-----------------------+-------------------------+
| Total Feature PRs     |  82                     |
| Matched to Tickets    |  28  (34%)              |
| Unmatched PRs         |  54  (66%)              |
| Linkage Rate          |  34%                    |
+-----------------------+-------------------------+
| IMPROVEMENT: Up from 22% in Sprint 7            |
| Branch naming: drchinca/* branches use BH-XXX   |
| Gap: sherbiny-bh, Nano-233 branches unlinked    |
+-------------------------------------------------+
```

**Matched tickets**: BH-319, BH-325, BH-326, BH-327, BH-328, BH-330, BH-339, BH-344, BH-345, BH-346, BH-347, BH-351, BH-355, BH-356, BH-357, BH-358, BH-359, BH-360, BH-374, BH-375, BH-376

**Root cause of unmatched**: Hikuri's branches consistently use `drchinca/BH-XXX/description` pattern. Ahmed and Harbour use descriptive branch names without ticket references (`feat/synapse-stack-optional`, `scheduler-cron`, `preview-asset`).

---

## WIP Analysis

```
+-------------------------------------------------+
|               WIP TIME DISTRIBUTION              |
+-----------------------+-------------------------+
| Under 1 day           |  12 tickets (57%)       |
| 1--3 days              |  5 tickets  (24%)       |
| 4--7 days              |  3 tickets  (14%)       |
| 14+ days (multi-sprint)|  1 ticket   (5%)        |
+-----------------------+-------------------------+
| Average WIP: 2.5 days                           |
| Most tickets resolved in concentrated Apr 8-9   |
| batch -- Hikuri's dbt cluster all merged same    |
| day as a coordinated cross-repo release.         |
+-------------------------------------------------+
```

The Apr 8-9 batch release pattern is healthy -- cross-repo features (dbt, Synapse, governance) were merged together to ensure consistency across brightbot, platform-core, webapp, and CDK repos.

---

## Team Breakdown

| Member | Done | In Progress | Points | Focus Areas |
|--------|------|-------------|--------|-------------|
| **Hikuri** | 18 | 1 (BH-347 CR) | -- | dbt agent pipeline, governance tools, Synapse BYOW, analytics dashboard, custom personas, Slack fixes |
| **Ahmed** | 2 | 3 | 2 | EDL shutdown, OMD webhook tracking, Synapse ingestion, unstructured data stack |
| **Marwan** | 1 | 1 | 3 | GraphQL capabilities for deep_agent, GitHub auth fix, React 17->18 upgrade |
| **Harbour** | 0 | 0 | -- | Scheduler, data preview, catalog health checks (PRs merged, no tickets linked) |

**Notes**:
- Hikuri drove 86% of completed tickets (18/21) -- dominated dbt, governance, Synapse, and analytics work
- Ahmed has 3 active In Progress tickets on Synapse/unstructured data -- steady infrastructure work
- Harbour has 7+ PRs merged but 0 tickets linked -- all work under generic branch names
- Marwan shipped React 17-to-18 upgrade (massive PR: +43K/-87K lines) with no Jira ticket

---

## Repository Activity

| Repository | Feature PRs | Build PRs | Total |
|------------|-------------|-----------|-------|
| **brighthive-webapp** | 32 | 4 | 36 |
| **brighthive-platform-core** | 22 | 8 | 30 |
| **brightbot** | 15 | 4 | 19 |
| **brighthive-data-organization-cdk** | 7 | 2 | 9 |
| **brighthive-data-workspace-cdk** | 4 | 2 | 6 |
| **brightbot-slack-server** | 2 | 0 | 2 |
| **brighthive-admin** | 0 | 1 | 1 |
| **Total** | **82** | **21** | **103** |

**Highlight**: 7 repos touched this sprint (vs 4 in Sprint 7). Data CDK repos active again for Synapse infrastructure.

---

## Notable PRs (by size and impact)

| PR | Repo | Title | Author | Lines |
|----|------|-------|--------|-------|
| #1034 | webapp | dbt settings + GitHub repo management | Hikuri | +29.8K/-6.8K |
| #1028 | webapp | React 17 to 18 upgrade | Marwan | +43.2K/-86.8K |
| #713 | platform-core | TransformationNode model metadata + run tracking | Hikuri | +4.1K/-2 |
| #712 | platform-core | GitHub Device Flow OAuth | Hikuri | +2.7K/-124 |
| #709 | platform-core | Complete dbt workflow | Hikuri | +2.4K/-124 |
| #449 | brightbot | dbt agent ReAct migration | Hikuri | +2.6K/-41 |
| #1055 | webapp | Platform analytics dashboard | Hikuri | +2.3K/-422 |
| #729 | platform-core | Data asset health check fields | Hikuri | +1.7K/-0 |

---

## Problems Identified

1. **19/21 Done tickets unpointed**: Velocity tracking is broken. Points-based metrics (12.2%) are meaningless when 90% of done work has no points.
2. **Branch naming inconsistency**: Only Hikuri consistently uses `BH-XXX` in branches. Ahmed and Harbour use descriptive names without ticket references.
3. **Harbour's work invisible in Jira**: 7+ PRs merged (scheduler, preview, catalog health checks) with 0 ticket linkage.
4. **React 18 upgrade untracked**: Marwan's +43K/-87K line React upgrade has no Jira ticket -- this is a major framework migration.
5. **9 Needs Refinement tickets**: The dbt provisioning phases are planned but not yet refined -- risk of To Do pile-up in sprint's second half.
6. **Hikuri concentration**: 86% of done tickets assigned to one person. Bus factor = 1 for dbt, governance, and analytics work.

---

## Recommendations

1. **Point the 19 unpointed Done tickets retroactively**: Even rough estimates will restore velocity tracking.
2. **Create tickets for untracked work**: React 18 upgrade, scheduler, data preview, catalog health checks need Jira records.
3. **Enforce branch naming for all team members**: Not just Hikuri -- `BH-XXX/description` should be the standard.
4. **Refine the 9 dbt provisioning tickets NOW**: These are half the remaining backlog. If they stay in Needs Refinement, sprint completion will stall.
5. **Pair on governance and dbt**: Hikuri's concentration is a risk. Ahmed or Harbour should shadow the dbt agent work.
6. **Celebrate the dbt pipeline delivery**: BH-325 through BH-346 is a complete transformation pipeline shipped in one burst -- GitHub commits, model metadata, DAG views, ReAct agent. This is the sprint's flagship achievement.
