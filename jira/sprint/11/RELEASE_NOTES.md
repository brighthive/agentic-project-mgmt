# Sprint 11 🧪 Release Notes — Profiler + Permissions Cut

**Release Date**: June 2, 2026
**Sprint Window**: May 15 → June 2, 2026 (18 days)
**Status**: Unofficial cut (counted forward from Sprint 10). Excludes Longaeva PoC work.

---

## Summary

| Metric | Value |
|---|---|
| Tickets Done | 7 |
| Tickets in Staging QC | 2 |
| Tickets in Needs Refinement (PRs merged, awaiting transition) | 10 |
| PRs Merged | 27 |
| Lines Changed (excl. release-carrier PRs) | 15,183 |
| Repos Touched | 3 (webapp · platform-core · brightbot) |

---

## Completed Tickets

| Key | Summary | Assignee |
|---|---|---|
| [BH-513](https://brighthiveio.atlassian.net/browse/BH-513) | fix(studio): restore canAccessFiles admin role guard for KB file query and form props | Harbour |
| [BH-514](https://brighthiveio.atlassian.net/browse/BH-514) | fix(schemas): update all hardcoded /govern/schemas links to /catalog/schemas | Harbour |
| [BH-515](https://brighthiveio.atlassian.net/browse/BH-515) | fix(governance): align GovernancePolicyDetail route and back-links to new /govern path | Harbour |
| [BH-516](https://brighthiveio.atlassian.net/browse/BH-516) | fix(nav): add end prop to NavLinks | Harbour |
| [BH-517](https://brighthiveio.atlassian.net/browse/BH-517) | fix(nav): preserve role-based section visibility in refactored nav | Harbour |
| [BH-520](https://brighthiveio.atlassian.net/browse/BH-520) | Add profiler_task as a schedulable batch task | Harbour |
| [BH-556](https://brighthiveio.atlassian.net/browse/BH-556) | fix(webapp): repair stale routes on /home shortcuts and breadcrumb nav | Harbour |

## In Staging QC

| Key | Summary | Assignee |
|---|---|---|
| [BH-522](https://brighthiveio.atlassian.net/browse/BH-522) | Fix Run Profiler button on asset detail page | Harbour |
| [BH-523](https://brighthiveio.atlassian.net/browse/BH-523) | Fix Auto-trigger data profiler on data ingestion | Harbour |

## Needs Refinement (PR merged — awaiting transition)

| Key | Summary | Assignee |
|---|---|---|
| [BH-376](https://brighthiveio.atlassian.net/browse/BH-376) | Custom Personas Builder — visual flow + nav enterprise restructure | Kuri |
| [BH-498](https://brighthiveio.atlassian.net/browse/BH-498) | chore(brightbot): port data_profiler_agent + workspace-scoped runs onto develop | Kuri |
| [BH-501](https://brighthiveio.atlassian.net/browse/BH-501) | feat(platform-core): auto-trigger data_profiler_agent on ingestion | Kuri |
| [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) | Quality check completion → BrightSignals Slack notifications | Marwan |
| [BH-548](https://brighthiveio.atlassian.net/browse/BH-548) | fix(platform-core): extend agent CRUD permissions to collaborator role | — |

(Plus BH-359, BH-491, BH-495, BH-497, BH-502 — open work remaining.)

---

## Repository Activity

### brighthive-platform-core (7 PRs, 3,515 lines)

| PR | Title | Author |
|---|---|---|
| [#768](https://github.com/brighthive/brighthive-platform-core/pull/768) | Store dbt Cloud transformation credentials in Secrets Manager | Marwan |
| [#767](https://github.com/brighthive/brighthive-platform-core/pull/767) | feat(webhook): auto-trigger data_profiler_agent concurrently with quality check (BH-501) | Kuri |
| [#772](https://github.com/brighthive/brighthive-platform-core/pull/772) | feat(flags): runtime feature flags query + mutation | Kuri |
| [#773](https://github.com/brighthive/brighthive-platform-core/pull/773) | release(staging): runtime feature flags + perms fixes | Kuri |
| [#774](https://github.com/brighthive/brighthive-platform-core/pull/774) | feat(local-dev): comprehensive seed data + local dev mocks | Kuri |
| [#775](https://github.com/brighthive/brighthive-platform-core/pull/775) | feat(scheduler): register profiler_task in dispatcher action registry (BH-520) | Harbour |
| [#776](https://github.com/brighthive/brighthive-platform-core/pull/776) | fix(auth): extend agent CRUD permissions to collaborator role (BH-548) | Harbour |

### brighthive-webapp (16 PRs, 51,491 lines incl. release carriers)

| PR | Title | Author |
|---|---|---|
| [#1100](https://github.com/brighthive/brighthive-webapp/pull/1100) | feat(nav): enterprise dashboard restructure + Documents tabs + mock-data previews (BH-376) | Kuri |
| [#1103](https://github.com/brighthive/brighthive-webapp/pull/1103) | fix(BrightAgent): keep AG Grid aria description out of sidebar layout | Marwan |
| [#1107](https://github.com/brighthive/brighthive-webapp/pull/1107) | fix(webapp): role hidden routes and buttons (BH-513) | Harbour |
| [#1108](https://github.com/brighthive/brighthive-webapp/pull/1108) | fix(webapp): nav prop states (BH-516) | Harbour |
| [#1109](https://github.com/brighthive/brighthive-webapp/pull/1109) | fix(schemas): schema routes + save load bugs (BH-514) | Harbour |
| [#1110](https://github.com/brighthive/brighthive-webapp/pull/1110) | fix(govern): governance routes + bugs (BH-515) | Harbour |
| [#1111](https://github.com/brighthive/brighthive-webapp/pull/1111) | chore(sync): cherry-pick staging-only UI/permission fixes onto develop | Kuri |
| [#1113](https://github.com/brighthive/brighthive-webapp/pull/1113) | release(staging): nav restructure + UI/permission fixes (BH-376) | Kuri |
| [#1114](https://github.com/brighthive/brighthive-webapp/pull/1114) | feat(flags): runtime feature flags via Platform Core GraphQL | Kuri |
| [#1115](https://github.com/brighthive/brighthive-webapp/pull/1115) | release(staging): runtime feature flags + merge fixes | Kuri |
| [#1116](https://github.com/brighthive/brighthive-webapp/pull/1116) | fix(nav): restore BrightAgent panel + fix stale route paths (BH-376) | Kuri |
| [#1117](https://github.com/brighthive/brighthive-webapp/pull/1117) | release(staging): fix BrightAgent panel routes (BH-376) | Kuri |
| [#1119](https://github.com/brighthive/brighthive-webapp/pull/1119) | fix(local-dev): workspace-aware BrightBot requests + thread validation | Kuri |
| [#1120](https://github.com/brighthive/brighthive-webapp/pull/1120) | feat(scheduler): add Data Profiler task to scheduler UI (BH-520) | Harbour |
| [#1121](https://github.com/brighthive/brighthive-webapp/pull/1121) | fix(Perms): Navigation permissions + sidebar guard (BH-517) | Harbour |
| [#1122](https://github.com/brighthive/brighthive-webapp/pull/1122) | fix(webapp): breadcrumbs + shortcuts routes (BH-556) | Harbour |

### brightbot (4 PRs, 2,489 lines)

| PR | Title | Author |
|---|---|---|
| [#483](https://github.com/brighthive/brightbot/pull/483) | fix: hotfix prod brightagent S3 streaming mem0 | Marwan |
| [#485](https://github.com/brighthive/brightbot/pull/485) | feat(profiler): port data_profiler_agent onto develop (BH-501) | Kuri |
| [#486](https://github.com/brighthive/brightbot/pull/486) | feat(notifications): publish quality check completion to BrightSignals (BH-530) | Kuri |
| [#487](https://github.com/brighthive/brightbot/pull/487) | feat(profiler): runnable on demand + scheduled task (BH-520) | Harbour |

---

## Excluded from this release

The following are tracked under Longaeva PoC, not the platform release cycle:

- Longaeva epic **BH-526** and its children (BH-527, BH-528, BH-531, BH-549–BH-554)
- Snowflake integration PRs: brighthive-platform-core#777, brightbot#488 + #489, brighthive-data-organization-cdk#156
- PoC tracker scaffolding: agentic-project-mgmt#20–#28

See `clients/trials/longaeva/TRACKER.md` for PoC status.
