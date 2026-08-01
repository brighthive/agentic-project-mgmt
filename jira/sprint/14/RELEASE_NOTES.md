# Sprint 14 🍯 — Release Notes (July 21 – Aug 1, 2026)

Technical release notes, grouped by repository. Unofficial date-range cut; see
`SUMMARY.md` for the per-person breakdown and `stats.json` for the raw numbers.

| Metric | Value |
|---|---|
| PRs merged | 82 (62 code + 20 release/promotion) |
| Tickets resolved | 28 (27 Done, 1 Canceled) |
| Repos touched | 5 |
| Code lines (excl. release re-merges) | +41,813 / −4,316 |
| Authors | Kuri (57), Harbour (17), Marwan (8) |

---

## brighthive-platform-core (37 PRs)

**Lineage & quality (BH-1036 / BH-1258 / BH-1265)**
- [#1116](https://github.com/brighthive/brighthive-platform-core/pull/1116) feat(lineage): engine-agnostic lineage + staged quality rules to staging
- [#1124](https://github.com/brighthive/brighthive-platform-core/pull/1124) feat(lineage): service-key write path for pipeline lineage
- [#1140](https://github.com/brighthive/brighthive-platform-core/pull/1140) feat: lineage-scoped runPipelineSegment + reRunFromNode + immutability
- [#1141](https://github.com/brighthive/brighthive-platform-core/pull/1141) feat: derive pipeline tiers from declared structure, not table names
- [#1130](https://github.com/brighthive/brighthive-platform-core/pull/1130) test(schema): boot-time guardrail for invalid directive enum values
- [#1106](https://github.com/brighthive/brighthive-platform-core/pull/1106) fix(analytics): correct workspace graph edges in overview + KB counts
- [#1118](https://github.com/brighthive/brighthive-platform-core/pull/1118) / [#1119](https://github.com/brighthive/brighthive-platform-core/pull/1119) fix(lineage): AuthRole for staged-quality directives (+ staging hotfix)

**Warehouse health (BH-1280)**
- [#1146](https://github.com/brighthive/brighthive-platform-core/pull/1146) feat(warehouse-health): persist + fold engine-agnostic health snapshot

**BrightRoutines / scheduled agents**
- [#1014](https://github.com/brighthive/brighthive-platform-core/pull/1014) feat(routines): cadence override + adjustedFields feedback capture (BH-993)
- [#1015](https://github.com/brighthive/brighthive-platform-core/pull/1015) feat(notifications): shared correlation id across delivery surfaces (BH-939)
- [#1008](https://github.com/brighthive/brighthive-platform-core/pull/1008) fix(routines): reject empty ids + cap recipientUserIds before I/O
- [#1137](https://github.com/brighthive/brighthive-platform-core/pull/1137) fix(scheduled-agents): reclaim abandoned dispatcher locks (BH-1235)
- [#1136](https://github.com/brighthive/brighthive-platform-core/pull/1136) feat(brightroutines): provision GSI5 for routine-scores leaderboard (BH-1207)
- [#1122](https://github.com/brighthive/brighthive-platform-core/pull/1122) / [#1123](https://github.com/brighthive/brighthive-platform-core/pull/1123) ci(infra): one-shot cdk-import for prod scheduled-agent-dispatcher (BH-952)

**Projects & performance**
- [#1139](https://github.com/brighthive/brighthive-platform-core/pull/1139) feat(projects): persist transformation engine + linked repo on projects (BH-1244)
- [#1138](https://github.com/brighthive/brighthive-platform-core/pull/1138) perf(data-assets): gate OpenMetadata N+1 on field selection + partition cache (BH-1242)

**Schema-file intake (Marwan)**
- [#1144](https://github.com/brighthive/brighthive-platform-core/pull/1144) feat(resources): resourceContent query for raw schema-file reads
- [#1148](https://github.com/brighthive/brighthive-platform-core/pull/1148) feat(graphql): resourceContentUploadUrl for schema files

**Catalog (Harbour)**
- [#889](https://github.com/brighthive/brighthive-platform-core/pull/889) feat(catalog): previewAvailable + profilerAvailable fields with N+1 batch fix
- [#1147](https://github.com/brighthive/brighthive-platform-core/pull/1147) fix(projects): create projects with name in one mutation

**Auth & local dev**
- [#911](https://github.com/brighthive/brighthive-platform-core/pull/911) feat(auth): MFA2 V1 — opt-in SMS on staging pool (approval-gated)
- [#1074](https://github.com/brighthive/brighthive-platform-core/pull/1074) feat(seeds): add LocalBank workspace for local dev
- [#1117](https://github.com/brighthive/brighthive-platform-core/pull/1117) feat(notifications): route notifications DynamoDB to LocalStack in local dev

**Releases:** #1120, #1125, #1126, #1127, #1128, #1131, #1142, #1143, #1145, #1149, #1151

---

## brighthive-webapp (35 PRs)

**Observability & lineage UI (BH-1036 / BH-1262)**
- [#1370](https://github.com/brighthive/brighthive-webapp/pull/1370) feat(observability): pipeline lineage view + 6-tier medallion
- [#1368](https://github.com/brighthive/brighthive-webapp/pull/1368) feat(observability): surface pipeline lineage on project observability
- [#1336](https://github.com/brighthive/brighthive-webapp/pull/1336) fix(observability): render run status + logs; guard with real-capture e2e
- [#1344](https://github.com/brighthive/brighthive-webapp/pull/1344) refactor(quality): split QualityRuleDrawer to unblock staged-rule UI
- [#1374](https://github.com/brighthive/brighthive-webapp/pull/1374) feat(webapp): re-run from this node affordance on RunTimeline (BH-1262)

**Warehouse health (BH-1280)**
- [#1387](https://github.com/brighthive/brighthive-webapp/pull/1387) feat(home): warehouse operational health across home band + health checks
- [#1379](https://github.com/brighthive/brighthive-webapp/pull/1379) test(analytics): regression coverage for SQL Server health alerts

**Projects & engine binding (BH-1244)**
- [#1373](https://github.com/brighthive/brighthive-webapp/pull/1373) feat(projects): link transformation engine + repo from project settings
- [#1355](https://github.com/brighthive/brighthive-webapp/pull/1355) fix(projects): hide the Flow (Workflow Studio) tab — not GA

**Catalog + Projects UX sweep (Harbour — BH-1154 → BH-1162)**
- [#1358](https://github.com/brighthive/brighthive-webapp/pull/1358) show correct Overwrite label and highlight active write mode
- [#1359](https://github.com/brighthive/brighthive-webapp/pull/1359) replace fake toggle with real Switch, add asset-picker loading state
- [#1360](https://github.com/brighthive/brighthive-webapp/pull/1360) align Transform page title, stop Active switch label flip
- [#1361](https://github.com/brighthive/brighthive-webapp/pull/1361) / [#1362](https://github.com/brighthive/brighthive-webapp/pull/1362) align asset field casing + Projects JSON Schema tab
- [#1364](https://github.com/brighthive/brighthive-webapp/pull/1364) use the same styled Tab for New Asset and Update Asset
- [#1366](https://github.com/brighthive/brighthive-webapp/pull/1366) add Tags field to project file upload
- [#1367](https://github.com/brighthive/brighthive-webapp/pull/1367) fix resourceType() only matching first extension per type
- [#1372](https://github.com/brighthive/brighthive-webapp/pull/1372) 'Preparing…' state for quality/profiler while a run is in flight
- [#1382](https://github.com/brighthive/brighthive-webapp/pull/1382) fix(projects): create atomically, toast failures, rollback orphans
- [#1385](https://github.com/brighthive/brighthive-webapp/pull/1385) stop refetch loading flicker and restore grid cell ellipsis
- [#1386](https://github.com/brighthive/brighthive-webapp/pull/1386) point project file links at catalog/documents route
- [#1352](https://github.com/brighthive/brighthive-webapp/pull/1352) remove-member copy and UI now match reality (BH-1139)
- [#1176](https://github.com/brighthive/brighthive-webapp/pull/1176) Data catalogue healthcheck and bulk tagging assets

**Schema-file editor (Marwan)**
- [#1377](https://github.com/brighthive/brighthive-webapp/pull/1377) feat(projects): allow XSD/XML schema file uploads in Project Files
- [#1383](https://github.com/brighthive/brighthive-webapp/pull/1383) feat(project-files): XSD/XML schema file editor

**Releases:** #1353, #1356, #1363, #1369, #1371, #1375, #1376, #1378, #1384, #1389

---

## agentic-project-mgmt (7 PRs — specs & docs)

- [#144](https://github.com/brighthive/agentic-project-mgmt/pull/144) docs(spec): warehouse-health snapshot → landing band surfacing (BH-1280)
- [#141](https://github.com/brighthive/agentic-project-mgmt/pull/141) docs(spec): pipeline run lifecycle — lineage-scoped versioned re-runnable runs (BH-1255)
- [#142](https://github.com/brighthive/agentic-project-mgmt/pull/142) docs(spec): BH-1255 trial spec family → handover-ready (9 specs)
- [#143](https://github.com/brighthive/agentic-project-mgmt/pull/143) docs(spec): Project Files artifact intake + dbt GitHub bridge
- [#139](https://github.com/brighthive/agentic-project-mgmt/pull/139) docs(loopcapital): Trial (Doc 1) readiness pass — epic, spec, tickets, security gate (BH-1245)
- [#135](https://github.com/brighthive/agentic-project-mgmt/pull/135) docs(routines): notification xref, Sprint 13 release, secrets manifest (BH-1131)
- [#138](https://github.com/brighthive/agentic-project-mgmt/pull/138) feat(loopcapital): grant reranker IAM access on brightagent_kb_role (BH-1164) — *Harbour*

## brighthive-e2e (1 PR)

- [#72](https://github.com/brighthive/brighthive-e2e/pull/72) test(e2e): warehouse-agnostic ground-truth fixtures for 3-engine sweep (BH-1280)

## platform-saas-ai-context (2 PRs)

- [#41](https://github.com/brighthive/platform-saas-ai-context/pull/41) docs(infra): add cross-app deployment guide (flags + envs)
- [#42](https://github.com/brighthive/platform-saas-ai-context/pull/42) docs(infra): operational feature-flag reference + fix stale ENVIRONMENTS whitelist

---

## Resolved tickets (28)

**Kuri — MCP prod-test hardening (BH-1181 family):** BH-1191, BH-1192, BH-1202, BH-1209,
BH-1215, BH-1217, BH-1220, BH-1222, BH-1229, BH-1231, BH-1232, BH-1233, BH-1234, BH-1236, BH-1238.

**Harbour — catalog/projects/KB:** BH-1154, BH-1155, BH-1156, BH-1157, BH-1158, BH-1159,
BH-1160, BH-1161, BH-1162, BH-1163, BH-1164, BH-1165. *(BH-1188 Canceled.)*
