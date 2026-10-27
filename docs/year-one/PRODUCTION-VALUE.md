# What Reached Production: User-Facing Value Kuri Delivered

Every pull request (PR) linked in the sprint release notes (`jira/sprint/N/RELEASE_NOTES.md`, sprints 1 to 16) is checked against production. Source: `collect_shipped_prs.py` → `data/shipped_prs.json`, `collect_production_value.py` → `data/production_value.json`.

**Production means:** for `brighthive-platform-core` and `brighthive-webapp`, the merge commit is in a plain `-release` tag. For every other repo, it is on `main` or `master`. Git shows a change was released or is on the production branch. It does not prove the change is running. For example, `brightbot` production deploys failed repeatedly in July 2026 (internal notes), so "on main" is weaker evidence than "released".

## The count

| Measure | Count |
|---|---|
| PRs listed in the release notes (all merged) | 556 |
| User-facing changes: `feat`, `fix`, `perf`, excluding release carriers and internal tooling repos | 322 |
| …verified in production | 302 |
| User-facing changes authored by Kuri | 202 |
| …verified in production | 187 |
| Kuri's share of production-verified user-facing changes | 61.9% |

## Kuri's production-verified changes

| Repo | Changes |
|---|---|
| brighthive-webapp | 67 |
| brighthive-platform-core | 65 |
| brightbot | 44 |
| brightbot-slack-server | 8 |
| brighthive-admin | 1 |
| brighthive-data-organization-cdk | 1 |
| brighthive-data-workspace-cdk | 1 |

| Type | Changes |
|---|---|
| feat | 128 |
| fix | 58 |
| perf | 1 |

## By sprint

| Sprint | Kuri, verified in production | All authors, verified in production |
|---|---|---|
| 1 | 0 | 1 |
| 2 | 1 | 1 |
| 3 | 3 | 3 |
| 4 | 11 | 11 |
| 5 | 4 | 4 |
| 7 | 1 | 19 |
| 8 | 40 | 49 |
| 9 | 10 | 24 |
| 10 | 7 | 16 |
| 11 | 9 | 17 |
| 14 | 25 | 45 |
| 15 | 69 | 98 |
| 16 | 7 | 14 |

## Top 30 capabilities (release-note headings)

| Capability | Kuri PRs in production | Sprints |
|---|---|---|
| Warehouse identity & multi-database (BH-1432/1440/1443) | 11 | 15 |
| On-Prem Engineering Runner — warehouse registration & queue (BH-1403/1421/1426/1439–1441) | 9 | 15 |
| On-Prem Engineering Runner / warehouse targeting (BH-1362/1370/1371/1395/1396/1430) | 9 | 15 |
| Notifications / Signal Catalog / governance (BH-1331/1333/1340/1348) | 8 | 15 |
| Lineage & quality (BH-1036 / BH-1258 / BH-1265) | 7 | 14 |
| Routines & notifications (BH-1400/1330/1331/1337) | 7 | 15 |
| Routines & fleet health (BH-1329/1340/1341/1346/1348/1397/1398) | 7 | 15 |
| Reliability & cleanup (BH-1036/1350/1372) | 6 | 15 |
| BrightRoutines / scheduled agents | 5 | 14 |
| Project sync & agent output (BH-1330/1351/1361) | 5 | 15 |
| Observability & lineage UI (BH-1036 / BH-1262) | 4 | 14 |
| Auth & local dev | 3 | 14 |
| LANGGRAPH env wiring after the ECS cutover (BH-1461/1462) | 3 | 16 |
| Warehouse health (BH-1280) | 2 | 14 |
| Projects & performance | 2 | 14 |
| Projects & engine binding (BH-1244) | 2 | 14 |
| Routines delivery & provenance (BH-1399) | 2 | 15 |
| Project run-sync & admin (BH-1330/1352) | 2 | 15 |
| Other fixes | 2 | 15 |
| GraphQL ECS/CloudFront cutover continuation (Marwan) | 2 | 16 |
| Default-warehouse identity (BH-1362) | 1 | 15 |
| Supervisor tooling (Kuri) | 1 | 16 |

## Marketing release items

The curated, customer-facing sections of the sprint notes: 73 items. Verification status by ticket key: released 19, no ticket key 46, no code found 5, on main 2, pre production 1. Items with no ticket key cannot be verified this way, which is why the PR-level check above is the main evidence.

## Sprints without PR links (6, 12, 13)

These sprints list tickets, not PRs, so they are checked by ticket key instead. Ranges such as `BH-882–884` resolve only their first key, so this undercounts. Sprint 6 records no PRs or ticket keys at all.

| Status of listed tickets | Tickets |
|---|---|
| no_code_found | 32 |
| on_main | 14 |
| released | 6 |

Of these, 18 are in production with Kuri authoring half or more of the commits.

## Limits

- Sprint notes stop at Sprint 16 (Aug 2026). Later work is not counted until those notes land on the main branch.
- `feat`, `fix` and `perf` are a proxy for user-facing. Some are internal improvements.
- The share of Kuri's PRs reflects the concentration of work on one person (see [DATA-QUALITY.md](DATA-QUALITY.md)).
- Business impact (revenue, adoption) is not measured here. See [business.md](business.md).
