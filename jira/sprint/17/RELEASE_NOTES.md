# Sprint 17 🥝 — Release Notes (Aug 24 – Oct 6, 2026)

Technical release notes, grouped by repository then author. Unofficial date-range cut —
sixth in a row; the previous release was Sprint 16 🍓 (Aug 17–23). See `SUMMARY.md` for
the per-person analysis and `stats.json` for the raw numbers.

| Metric | Value |
|---|---|
| PRs merged | 254 (195 code + 59 release/promotion) |
| Production release | Staging → Production on Sep 30 (brightbot #1084, platform-core #1306, webapp #1479) |
| Tickets transitioned to Done | 4 (BH-1505, BH-1506, BH-1507, BH-1539) |
| Repos touched | 7 |
| Code lines (excl. release re-merges) | +218,197 / −53,750 — or +152,386 / −16,666 excluding the regenerated `ogm-types.ts` in platform-core #1220 |
| Authors | Kuri (152), Marwan (27), Harbour (16) |

Release/promotion carriers (develop→staging, staging→production, promote/* branches, reverts,
back-merges) are excluded from the lists below.

---

## brighthive-platform-core (103 PRs, 75 code)

**Kuri** (58)
- [#1321](https://github.com/brighthive/brighthive-platform-core/pull/1321) feat(audit): record every GraphQL mutation automatically (BH-1579) — +396/−2
- [#1320](https://github.com/brighthive/brighthive-platform-core/pull/1320) feat(routines): turn-off errors and ROUTINE permission kind to staging (BH-1566, BH-1572) — +734/−47
- [#1315](https://github.com/brighthive/brighthive-platform-core/pull/1315) feat(notifications): register source_connection_unreachable signal (BH-1558) — +80/−0
- [#1314](https://github.com/brighthive/brighthive-platform-core/pull/1314) fix(analytics): report Unknown for stale or unprobed health (BH-1555) — +762/−62
- [#1313](https://github.com/brighthive/brighthive-platform-core/pull/1313) feat(projects): expose dataProducts on ProjectOutput (BH-1543) — +106/−21
- [#1312](https://github.com/brighthive/brighthive-platform-core/pull/1312) feat(projects): filter workspace.projects by status (BH-830) — +126/−2
- [#1298](https://github.com/brighthive/brighthive-platform-core/pull/1298) feat(spec): per-section conformance read surface (BH-1530) — +1275/−0
- [#1297](https://github.com/brighthive/brighthive-platform-core/pull/1297) feat(spec): frontmatter + canonical-section parser for /spec/*.md (BH-1527) — +791/−0
- [#1295](https://github.com/brighthive/brighthive-platform-core/pull/1295) docs(authz): refresh GOVERNANCE.md for BH-1464 grid close-out — +31/−7
- [#1293](https://github.com/brighthive/brighthive-platform-core/pull/1293) feat(authz): complete SEED_DEFAULTS matrix — close 16 enforced authorization gaps (BH-1464) — +329/−52
- [#1291](https://github.com/brighthive/brighthive-platform-core/pull/1291) fix(authz): resolve workspace-granular resource scope uniformly (BH-1525) — +219/−36
- [#1290](https://github.com/brighthive/brighthive-platform-core/pull/1290) docs(authz): add top-level GOVERNANCE.md for the BH-1464 authorization epic — +672/−0
- [#1288](https://github.com/brighthive/brighthive-platform-core/pull/1288) fix(authz): seed UPDATE·WORKSPACE for WORKSPACE_ADMIN so the matrix editor can bootstrap (BH-1466) — +27/−6
- [#1286](https://github.com/brighthive/brighthive-platform-core/pull/1286) fix(authz): scope RUN transform+workflow to governed project (BH-1524) — +164/−8
- [#1284](https://github.com/brighthive/brighthive-platform-core/pull/1284) feat(authz): enforce mutation verbs on staging via CDK knobs (BH-1464) — +21/−0
- [#1283](https://github.com/brighthive/brighthive-platform-core/pull/1283) fix(authz): require service key on onPremJob query (BH-1521) — +67/−1
- [#1282](https://github.com/brighthive/brighthive-platform-core/pull/1282) fix(authz): block cross-tenant reads in 3 query resolvers (BH-1517) — +186/−3
- [#1281](https://github.com/brighthive/brighthive-platform-core/pull/1281) ci(authz): gate merges on the dataplane-authz real-behavior suite (BH-1518) — +116/−0
- [#1280](https://github.com/brighthive/brighthive-platform-core/pull/1280) fix(routines): gate Cognito path of suggestion mutations (BH-1520) — +308/−62
- [#1279](https://github.com/brighthive/brighthive-platform-core/pull/1279) fix(auth): enforce service-key on onPremJob read (BH-1519) — +78/−4
- [#1278](https://github.com/brighthive/brighthive-platform-core/pull/1278) fix(platform-core): gate 4 query-side cross-tenant reads on caller workspace membership (BH-1517) — +229/−175
- [#1276](https://github.com/brighthive/brighthive-platform-core/pull/1276) fix(projects): resource<->project link mutations fail closed once BH-1464 enforces (BH-1506, BH-1507) — +119/−2
- [#1275](https://github.com/brighthive/brighthive-platform-core/pull/1275) feat(auth): restrict linkedSlackIdentities to admin/collaborator (BH-1499) — +137/−24
- [#1274](https://github.com/brighthive/brighthive-platform-core/pull/1274) feat(authz): give the catalog-sync job an authorized identity (BH-1501) — +408/−7
- [#1273](https://github.com/brighthive/brighthive-platform-core/pull/1273) feat(auth): shadow-gate the @public Slack resolvers (BH-1499) — +476/−5
- [#1272](https://github.com/brighthive/brighthive-platform-core/pull/1272) docs(feature): workspace authorization capability doc (BH-1464) — +221/−0
- [#1269](https://github.com/brighthive/brighthive-platform-core/pull/1269) fix(graphql): gate syncDataAssets by workspace membership (BH-1497) — +568/−3
- [#1267](https://github.com/brighthive/brighthive-platform-core/pull/1267) fix(platform-core): gate getSyncStatuses on workspace membership (BH-1498) — +52/−1
- [#1266](https://github.com/brighthive/brighthive-platform-core/pull/1266) fix(platform-core): gate createQualityRuleExecution on workspace membership (BH-1495) — +189/−2
- [#1265](https://github.com/brighthive/brighthive-platform-core/pull/1265) fix(authz): give PIPELINE a captured resource-locator binding (BH-1493) — +147/−15
- [#1264](https://github.com/brighthive/brighthive-platform-core/pull/1264) test(authz): RBAC/ABAC + assignation real-behavior coverage against staging (BH-1464) — +270/−4
- [#1262](https://github.com/brighthive/brighthive-platform-core/pull/1262) fix(platform-core): gate createConnections/syncConnections on workspace membership (BH-1494) — +299/−4
- [#1261](https://github.com/brighthive/brighthive-platform-core/pull/1261) test(authz): make behavior suites compile together (BH-1496) — +11/−0
- [#1259](https://github.com/brighthive/brighthive-platform-core/pull/1259) fix(deps): declare dataloader as a production dependency (BH-1492) — +3/−2
- [#1257](https://github.com/brighthive/brighthive-platform-core/pull/1257) feat(authz): ABAC attribute conditions on authorize() (BH-1491) — +990/−76
- [#1256](https://github.com/brighthive/brighthive-platform-core/pull/1256) docs(governance): ADR-0003 shadow→enforced verb ramp (BH-1464) — +95/−0
- [#1255](https://github.com/brighthive/brighthive-platform-core/pull/1255) feat(authz): delegate @authorized to authorize() with default-deny (BH-1468) — +1077/−953
- [#1254](https://github.com/brighthive/brighthive-platform-core/pull/1254) feat(authz): expose authorize() over GraphQL as checkAccess query (BH-1472) — +574/−15
- [#1253](https://github.com/brighthive/brighthive-platform-core/pull/1253) fix(authz): gate six cross-tenant data-plane holes (BH-1489) — +749/−32
- [#1252](https://github.com/brighthive/brighthive-platform-core/pull/1252) fix(authz): bind authorize() decision to resource's real workspace (BH-1488) — +870/−77
- [#1251](https://github.com/brighthive/brighthive-platform-core/pull/1251) docs(authz): spec authorize() resource-in-workspace check — confused-deputy fix (BH-1488) — +244/−0
- [#1250](https://github.com/brighthive/brighthive-platform-core/pull/1250) fix(authz): workspace-membership authz on six data-plane paths — spec (BH-1489) — +230/−0
- [#1249](https://github.com/brighthive/brighthive-platform-core/pull/1249) docs(authz): expose authorize() over GraphQL as checkAccess (BH-1472) — +278/−0
- [#1248](https://github.com/brighthive/brighthive-platform-core/pull/1248) docs(governance): spec ABAC attribute conditions on authorize() (BH-1476) — +277/−0
- [#1247](https://github.com/brighthive/brighthive-platform-core/pull/1247) docs(authz): SPEC-BH-1468 default-deny + @authorized delegation (BH-1468) — +307/−0
- [#1246](https://github.com/brighthive/brighthive-platform-core/pull/1246) docs(governance): spec BH-1486 server-side PII masking for Data Preview — +215/−0
- [#1241](https://github.com/brighthive/brighthive-platform-core/pull/1241) fix(authz): close matrix-cache repopulation race + failed-open invalidation (BH-1477) — +912/−33
- [#1240](https://github.com/brighthive/brighthive-platform-core/pull/1240) feat(platform-core): SHADOW mode + authz.decision telemetry (BH-1467) — +773/−14
- [#1239](https://github.com/brighthive/brighthive-platform-core/pull/1239) feat(platform-core): authorize() decision function (tenant→admin→matrix, fail-closed) + matrix cache/invalidation (BH-1465) — +1032/−10
- [#1238](https://github.com/brighthive/brighthive-platform-core/pull/1238) feat(platform-core): permission-matrix GraphQL resolvers (BH-1466) — +552/−0
- [#1235](https://github.com/brighthive/brighthive-platform-core/pull/1235) fix(test): update stale purgeAssetEmbedding DEL assertion for the v2 key — +8/−2
- [#1234](https://github.com/brighthive/brighthive-platform-core/pull/1234) feat(platform-core): extend WorkspacePolicyNode to a cell-set (BH-1466) — +838/−0
- [#1213](https://github.com/brighthive/brighthive-platform-core/pull/1213) docs(spec): multiple transformation engines per workspace, one default (BH-1460) — +194/−0
- [#1212](https://github.com/brighthive/brighthive-platform-core/pull/1212) fix(pipeline): repair run-status write and health traversal (BH-1458) — +764/−66
- [#1211](https://github.com/brighthive/brighthive-platform-core/pull/1211) feat(admin): renameWorkspaceAsAdmin superadmin mutation (BH-1453) — +555/−0
- [#1205](https://github.com/brighthive/brighthive-platform-core/pull/1205) feat(lineage): on-prem models publish the tables they build as data products (BH-1434) — +214/−4
- [#1204](https://github.com/brighthive/brighthive-platform-core/pull/1204) fix(lineage): materialise dbt sources so on-prem edges resolve (BH-1444) — +255/−8
- [#1183](https://github.com/brighthive/brighthive-platform-core/pull/1183) fix(health): live MCP reachability probe, not stored UNKNOWN status (BH-1373) — +163/−17

**Marwan** (15)
- [#1311](https://github.com/brighthive/brighthive-platform-core/pull/1311) fix(ci): set ENV on prod and dev CDK deploy workflows — +4/−0
- [#1310](https://github.com/brighthive/brighthive-platform-core/pull/1310) Prod graphql ecs cutover — +556/−217
- [#1308](https://github.com/brighthive/brighthive-platform-core/pull/1308) fix(cognito): gate MCP auth domain off prod and recover UserPool deploy — +395/−184
- [#1303](https://github.com/brighthive/brighthive-platform-core/pull/1303) feat(workflow): dbt engineering pipeline specs and run reconciliation — +1997/−162
- [#1300](https://github.com/brighthive/brighthive-platform-core/pull/1300) feat(project): project 2.0 spec API, apply pipeline, and smoke validation — +8550/−170
- [#1296](https://github.com/brighthive/brighthive-platform-core/pull/1296) feat(catalog): warehouse routing fields for multi-warehouse assets — +384/−17
- [#1244](https://github.com/brighthive/brighthive-platform-core/pull/1244) fix(warehouse): satisfy WarehouseSecretStore types on upsert — +93/−7
- [#1242](https://github.com/brighthive/brighthive-platform-core/pull/1242) feat(warehouse): validate secrets and merge node defaults on upsert — +353/−16
- [#1232](https://github.com/brighthive/brighthive-platform-core/pull/1232) feat(graphql): expose catalog hierarchy fields on DataAsset — +12/−0
- [#1230](https://github.com/brighthive/brighthive-platform-core/pull/1230) fix initalization call — +13/−2
- [#1228](https://github.com/brighthive/brighthive-platform-core/pull/1228) fix(catalog-search): enrich Redis docs with fields and warehouse context — +804/−46
- [#1226](https://github.com/brighthive/brighthive-platform-core/pull/1226) fix(cdk): wire OPENAI_API_KEY into GraphQL ECS task env — +7/−0
- [#1224](https://github.com/brighthive/brighthive-platform-core/pull/1224) Feat/catalog search index — +10/−10
- [#1222](https://github.com/brighthive/brighthive-platform-core/pull/1222) fix(catalog-search): avoid closing shared Redis client in status query — +11/−4
- [#1220](https://github.com/brighthive/brighthive-platform-core/pull/1220) feat(catalog-search): async hierarchy-aware Redis index pipeline — +67349/−37197

**Harbour** (2)
- [#1302](https://github.com/brighthive/brighthive-platform-core/pull/1302) fix(login): don't rethrow raw Cognito exceptions on bad credentials — +13/−1
- [#1277](https://github.com/brighthive/brighthive-platform-core/pull/1277) feat(i18n): persist workspace locale — +105/−9

---

## brightbot (73 PRs, 59 code)

**Kuri** (49)
- [#1119](https://github.com/brighthive/brightbot/pull/1119) fix(mcp): use stateless HTTP transport (BH-1581) — +129/−4
- [#1118](https://github.com/brighthive/brightbot/pull/1118) feat(audit): record every HTTP write automatically (BH-1580) — +307/−1
- [#1116](https://github.com/brighthive/brightbot/pull/1116) fix(mcp): restore spec pipeline generation (BH-1571) — +200/−11
- [#1115](https://github.com/brighthive/brightbot/pull/1115) feat(mcp): add project destination and governance gate tools (BH-1551) — +8201/−11
- [#1114](https://github.com/brighthive/brightbot/pull/1114) feat(mcp): add project pipeline control tools (BH-1549) — +6548/−11
- [#1113](https://github.com/brighthive/brightbot/pull/1113) feat(mcp): add project access and copy tools (BH-1551) — +5301/−10
- [#1112](https://github.com/brighthive/brightbot/pull/1112) feat(mcp): add project pipeline authoring tools (BH-1571) — +4194/−10
- [#1111](https://github.com/brighthive/brightbot/pull/1111) feat(mcp): add delete_project tool with typed-back name (BH-1551) — +1534/−1
- [#1110](https://github.com/brighthive/brightbot/pull/1110) feat(mcp): add project file, schema and spec document tools (BH-1550) — +953/−1
- [#1109](https://github.com/brighthive/brightbot/pull/1109) feat(authz): typed workspace-role lookup for gated callers (BH-1564) — +78/−13
- [#1108](https://github.com/brighthive/brightbot/pull/1108) refactor(scheduler): move payload rules into their own module (BH-1564) — +157/−139
- [#1107](https://github.com/brighthive/brightbot/pull/1107) fix(scheduler): owner-or-admin guard on schedule edit and run (BH-1564) — +652/−25
- [#1106](https://github.com/brighthive/brightbot/pull/1106) feat(watchdog): liveness heartbeat for Redshift and Postgres warehouses (BH-1562) — +343/−0
- [#1105](https://github.com/brighthive/brightbot/pull/1105) docs(spec): warehouse health freshness — one definition across surfaces (BH-1561) — +149/−0
- [#1104](https://github.com/brighthive/brightbot/pull/1104) fix(fleet-health): stop reporting healthy with no monitors or a silent watchdog (BH-1560) — +194/−16
- [#1103](https://github.com/brighthive/brightbot/pull/1103) fix(watchdog): write Healthy heartbeat on clean polls (BH-1557) — +332/−21
- [#1102](https://github.com/brighthive/brightbot/pull/1102) fix(warehouse): import traceback so Snowflake connect errors surface (BH-1554) — +22/−0
- [#1101](https://github.com/brighthive/brightbot/pull/1101) feat(mcp): add project run read tools (BH-1549) — +601/−7
- [#1100](https://github.com/brighthive/brightbot/pull/1100) feat(mcp): add project file, schema and spec document tools (BH-1550) — +34/−45
- [#1099](https://github.com/brighthive/brightbot/pull/1099) feat(mcp): add project data asset link and unlink tools (BH-1550) — +497/−0
- [#1098](https://github.com/brighthive/brightbot/pull/1098) feat(mcp): add set_project_status tool (BH-1548) — +270/−5
- [#1097](https://github.com/brighthive/brightbot/pull/1097) feat(mcp): add project contents read tools (BH-1550) — +725/−0
- [#1096](https://github.com/brighthive/brightbot/pull/1096) feat(mcp): add create_project and update_project tools (BH-1548) — +748/−22
- [#1095](https://github.com/brighthive/brightbot/pull/1095) feat(mcp): add list_projects and get_project read tools (BH-1546) — +570/−0
- [#1094](https://github.com/brighthive/brightbot/pull/1094) fix(mcp): bind project write tools to the authz gate (BH-1547) — +277/−10
- [#1093](https://github.com/brighthive/brightbot/pull/1093) fix(mcp): typed error for get_semantic_view without table_name (BH-856) — +32/−2
- [#1092](https://github.com/brighthive/brightbot/pull/1092) fix(mcp): add status envelope to current_workspace (BH-804) — +58/−0
- [#1091](https://github.com/brighthive/brightbot/pull/1091) fix(mcp): typed error envelope for rejected tool calls (BH-853) — +148/−66
- [#1082](https://github.com/brighthive/brightbot/pull/1082) fix(routines): persist scheduled detector scores (BH-950) — +163/−7
- [#1077](https://github.com/brighthive/brightbot/pull/1077) feat(warehouse): add Snowflake key-pair auth for MFA-enforced accounts (BH-1535) — +389/−20
- [#1076](https://github.com/brighthive/brightbot/pull/1076) feat(governance): project-scope the drift watchdog's asset resolution (BH-1534) — +243/−20
- [#1074](https://github.com/brighthive/brightbot/pull/1074) feat(skills): add project-observation-cycle skill (BH-1533) — +206/−3
- [#1069](https://github.com/brighthive/brightbot/pull/1069) feat(dbt_agent): WorkflowSpec authoring + staged quality-rule binding (BH-1528) — +1052/−0
- [#1068](https://github.com/brighthive/brightbot/pull/1068) feat(dbt_agent): spec-conformance check — detection, agent tool, trigger + webhook (BH-1529) — +1110/−1
- [#1064](https://github.com/brighthive/brightbot/pull/1064) feat(brightbot): gate agent data reads on READ DATA_ASSET + sensitivity ABAC (BH-1523) — +967/−9
- [#1062](https://github.com/brighthive/brightbot/pull/1062) feat(mcp): governance control surface over MCP (BH-1509) — +1149/−1
- [#1061](https://github.com/brighthive/brightbot/pull/1061) feat(skills): project Skills-affinity for project_agent runs (BH-1505) — +135/−17
- [#1059](https://github.com/brighthive/brightbot/pull/1059) fix(governance): mask sample + MIN/MAX, add masking guard (BH-1483) — +450/−14
- [#1058](https://github.com/brighthive/brightbot/pull/1058) refactor(brightbot): make PII masking transport injectable (BH-1482) — +870/−786
- [#1057](https://github.com/brighthive/brightbot/pull/1057) fix(brightbot): CTE-aware column lineage for PII masking (BH-1484) — +580/−147
- [#1056](https://github.com/brighthive/brightbot/pull/1056) fix(brightbot): verify workspace before warehouse secret probe (BH-1473) — +492/−69
- [#1055](https://github.com/brighthive/brightbot/pull/1055) fix(brightbot): scope lookup_neo4j to caller workspace (BH-1485) — +278/−3
- [#1054](https://github.com/brighthive/brightbot/pull/1054) docs(governance): specs for injectable masking transport + warehouse-tool masking contract (BH-1482, BH-1483) — +428/−0
- [#1053](https://github.com/brighthive/brightbot/pull/1053) docs(authz): SPEC-BH-1473 verify workspace before warehouse secret probe (BH-1473) — +244/−0
- [#1052](https://github.com/brighthive/brightbot/pull/1052) docs(governance): specs for BH-1484 (CTE lineage) + BH-1485 (lookup_neo4j scope) — +425/−0
- [#1051](https://github.com/brighthive/brightbot/pull/1051) feat(warehouse): mask PII on query + parity results (BH-1480/1481) — +1115/−48
- [#1047](https://github.com/brighthive/brightbot/pull/1047) fix(brightbot): lineage-aware PII masking closes alias bypass (BH-1478) — +1465/−102
- [#1046](https://github.com/brighthive/brightbot/pull/1046) feat(brightbot): role-aware tool context + authorize RUN/write tools (BH-1470) — +1117/−25
- [#1043](https://github.com/brighthive/brightbot/pull/1043) feat(remediation): recover self-healing remediation layers 0-1 (BH-1255) — +3373/−0

**Marwan** (5)
- [#1079](https://github.com/brighthive/brightbot/pull/1079) feat(pipeline): dbt engineering propose path and run diagnostics — +585/−25
- [#1071](https://github.com/brighthive/brightbot/pull/1071) feat(project): spec author, conversational bootstrap, and pipeline verifier — +4486/−6
- [#1066](https://github.com/brighthive/brightbot/pull/1066) feat(routing): asset-scoped multi-warehouse SQL routing — +1486/−220
- [#1049](https://github.com/brighthive/brightbot/pull/1049) feat(warehouse): route background jobs to asset-scoped warehouse — +281/−41
- [#1044](https://github.com/brighthive/brightbot/pull/1044) feat(catalog-search): read-only vector search with optional @ scope — +351/−160

**Harbour** (5)
- [#1087](https://github.com/brighthive/brightbot/pull/1087) refactor(scheduler): shared in-process create seam + review polish (follow-up to #1086) — +111/−62
- [#1086](https://github.com/brighthive/brightbot/pull/1086) fix(scheduler): call scheduled-agents in-process, drop the self-URL env — +367/−438
- [#1081](https://github.com/brighthive/brightbot/pull/1081) feat(pipelines): chat-configurable project pipeline scheduling (decoupled from dbt) — +582/−21
- [#1078](https://github.com/brighthive/brightbot/pull/1078) fix(routing): route pipeline lifecycle (list/schedule/runs) to dbt subagent — +21/−2
- [#1063](https://github.com/brighthive/brightbot/pull/1063) feat(i18n): localize QC reports from workspace locale — +488/−26

---

## brighthive-webapp (50 PRs, 33 code)

**Kuri** (17)
- [#1486](https://github.com/brighthive/brighthive-webapp/pull/1486) fix(mcp): accept stateless MCP servers with no session id (BH-1581) — +8/−11
- [#1485](https://github.com/brighthive/brighthive-webapp/pull/1485) feat(schedules): lock schedule controls for non-owners to staging (BH-1567) — +454/−17
- [#1483](https://github.com/brighthive/brighthive-webapp/pull/1483) feat(webapp): show Unknown and stale service health honestly (BH-1559) — +888/−118
- [#1477](https://github.com/brighthive/brighthive-webapp/pull/1477) fix(workflows): verify context and mobile agent review handoff — +324/−13
- [#1476](https://github.com/brighthive/brighthive-webapp/pull/1476) feat(workflows): expose execution, access and connection primitives — +360/−65
- [#1475](https://github.com/brighthive/brighthive-webapp/pull/1475) feat(workflows): expose project context and missing primitives — +666/−3
- [#1474](https://github.com/brighthive/brighthive-webapp/pull/1474) feat(workflows): show project agent actions and review states — +592/−0
- [#1461](https://github.com/brighthive/brighthive-webapp/pull/1461) fix(projects): read the Spec tab flag at runtime, not from the build (BH-1530) — +50/−14
- [#1458](https://github.com/brighthive/brighthive-webapp/pull/1458) feat(projects): Spec tab showing per-section conformance (BH-1530) — +500/−6
- [#1453](https://github.com/brighthive/brighthive-webapp/pull/1453) feat(governance): add ABAC access-limit editor to permission matrix (BH-1476) — +488/−17
- [#1452](https://github.com/brighthive/brighthive-webapp/pull/1452) fix(governance): make policies real — retire dead toggles, surface enforced access (BH-1464) — +115/−97
- [#1451](https://github.com/brighthive/brighthive-webapp/pull/1451) test(governance): add staging permission-matrix write e2e (BH-1469) — +224/−0
- [#1450](https://github.com/brighthive/brighthive-webapp/pull/1450) fix(projects): pass workspaceId to resource↔project link mutations (BH-1506) — +24/−4
- [#1449](https://github.com/brighthive/brighthive-webapp/pull/1449) test(governance): prove Policies + Quality Rules nav RBAC on real staging (BH-1464) — +248/−0
- [#1448](https://github.com/brighthive/brighthive-webapp/pull/1448) feat(governance): surface Access Control tab in Governance nav (BH-1502) — +294/−14
- [#1442](https://github.com/brighthive/brighthive-webapp/pull/1442) feat(webapp): permission-matrix live editor; fix phantom role + local-dev bypass (BH-1469) — +1287/−464
- [#1441](https://github.com/brighthive/brighthive-webapp/pull/1441) fix(governance): remove fake Enforced toggle from policy card (BH-172) — +1/−31

**Marwan** (7)
- [#1471](https://github.com/brighthive/brighthive-webapp/pull/1471) feat(project-flow): dbt engineering step config and run history UX — +220/−12
- [#1460](https://github.com/brighthive/brighthive-webapp/pull/1460) feat(project): spec tab, pipeline canvas, verify pipeline, and catalog sync — +4256/−839
- [#1457](https://github.com/brighthive/brighthive-webapp/pull/1457) feat(catalog): multi-warehouse hierarchy tree grouping — +117/−38
- [#1445](https://github.com/brighthive/brighthive-webapp/pull/1445) fix(webapp): resolve catalog and warehouse TypeScript errors — +29/−23
- [#1443](https://github.com/brighthive/brighthive-webapp/pull/1443) feat(warehouse): verify connection and collect Redshift schema — +71/−20
- [#1439](https://github.com/brighthive/brighthive-webapp/pull/1439) feat(catalog): add Data Catalog (new) to feature flags admin UI — +1/−0
- [#1437](https://github.com/brighthive/brighthive-webapp/pull/1437) feat(catalog): add warehouse-aware Data Catalog (new) view — +2060/−513

**Harbour** (9)
- [#1473](https://github.com/brighthive/brighthive-webapp/pull/1473) fix(schedules,brightagent): human-readable cadence, project labels, spec-chat clear + autoscroll — +152/−21
- [#1470](https://github.com/brighthive/brighthive-webapp/pull/1470) fix(auth): stop showing two contradictory toasts on login failure — +43/−16
- [#1469](https://github.com/brighthive/brighthive-webapp/pull/1469) fix(catalog): show load error instead of a no-match empty grid — +134/−32
- [#1468](https://github.com/brighthive/brighthive-webapp/pull/1468) fix(shared-links): confirm revoke and toast on failure — +54/−20
- [#1466](https://github.com/brighthive/brighthive-webapp/pull/1466) fix(sessions): refresh the list after delete and surface failures — +44/−20
- [#1465](https://github.com/brighthive/brighthive-webapp/pull/1465) feat(auth): globe language switcher on login + full locale on workspace select — +68/−26
- [#1464](https://github.com/brighthive/brighthive-webapp/pull/1464) feat(navbar): keep Log out visible in overflowing user menu — +246/−135
- [#1456](https://github.com/brighthive/brighthive-webapp/pull/1456) feat(i18n): translate BrightAgent stream status and output panel chrome — +636/−76
- [#1436](https://github.com/brighthive/brighthive-webapp/pull/1436) feat(i18n): add English, Spanish, and Portuguese UI translations — +36489/−8194

---

## brighthive-e2e (12 PRs, 12 code)

**Kuri** (12)
- [#97](https://github.com/brighthive/brighthive-e2e/pull/97) fix(mcp): align project validation with shipped contracts (BH-1581) — +83/−47
- [#96](https://github.com/brighthive/brighthive-e2e/pull/96) fix(mcp): accept optional session headers in live contracts (BH-1581) — +15/−24
- [#95](https://github.com/brighthive/brighthive-e2e/pull/95) fix(e2e): send X-Workspace-Id so tests query the workspace under test (BH-1582) — +42/−9
- [#94](https://github.com/brighthive/brighthive-e2e/pull/94) fix(mcp): accept stateless servers, reopen session on 404 (BH-1581) — +276/−39
- [#92](https://github.com/brighthive/brighthive-e2e/pull/92) test(e2e): health rows never claim more than their evidence (BH-1563) — +275/−5
- [#91](https://github.com/brighthive/brighthive-e2e/pull/91) test(e2e): project MCP tools reads, previews, refusals (BH-1552) — +526/−8
- [#90](https://github.com/brighthive/brighthive-e2e/pull/90) test(mcp): cover the A2A MCP door on prod (BH-1545) — +251/−5
- [#89](https://github.com/brighthive/brighthive-e2e/pull/89) test(scheduler): cover get_fleet_health on prod (BH-1544) — +319/−5
- [#88](https://github.com/brighthive/brighthive-e2e/pull/88) test(mcp): govern the platform over MCP end-to-end (BH-1509) — +477/−0
- [#87](https://github.com/brighthive/brighthive-e2e/pull/87) test(e2e): make warehouse foreign-workspace probe shadow-aware (BH-1500) — +72/−14
- [#86](https://github.com/brighthive/brighthive-e2e/pull/86) test(e2e): matrix-edit deny + denied RUN returns BLOCK (BH-1471) — +624/−15
- [#85](https://github.com/brighthive/brighthive-e2e/pull/85) test(mcp): black-box run_warehouse_query PII masking e2e (BH-1480) — +323/−36

---

## brightbot-slack-server (1 PRs, 1 code)

**Kuri** (1)
- [#178](https://github.com/brighthive/brightbot-slack-server/pull/178) feat(notifications): register source_connection_unreachable stage (BH-1558) — +76/−2

---

## agentic-project-mgmt (12 PRs, 12 code)

**Kuri** (12)
- [#195](https://github.com/brighthive/agentic-project-mgmt/pull/195) docs(specs): routine permissions as one platform-core decision (BH-1565) — +282/−0
- [#193](https://github.com/brighthive/agentic-project-mgmt/pull/193) docs(runbook): local-first testing step and bring-up traps (BH-1553) — +31/−0
- [#191](https://github.com/brighthive/agentic-project-mgmt/pull/191) docs(specs): reconcile Projects 2.0 doc against real epics (BH-1255) — +1078/−1
- [#187](https://github.com/brighthive/agentic-project-mgmt/pull/187) docs(spec): correct stale PII-enforcement claim in governance-policy-enforcement (BH-766) — +3/−3
- [#186](https://github.com/brighthive/agentic-project-mgmt/pull/186) docs(adr): flip ADR-0002 Proposed -> Accepted (BH-1036) — +2/−2
- [#185](https://github.com/brighthive/agentic-project-mgmt/pull/185) docs(spec): classify warehouse-listing tool as Shipped (BH-1454) — +2/−1
- [#184](https://github.com/brighthive/agentic-project-mgmt/pull/184) docs(spec): access-decisions v1 — one decision point + editable matrix (BH-1464) — +449/−0
- [#182](https://github.com/brighthive/agentic-project-mgmt/pull/182) docs(specs): per-solution mermaid on each of the 14 theme specs (BH-1036) — +200/−0
- [#181](https://github.com/brighthive/agentic-project-mgmt/pull/181) chore(docs): spec-classification guard + CI enforcement to keep the roadmap delegatable (BH-1036) — +151/−1
- [#180](https://github.com/brighthive/agentic-project-mgmt/pull/180) docs(roadmap): escape ampersands in mermaid labels (BH-1036) — +4/−4
- [#178](https://github.com/brighthive/agentic-project-mgmt/pull/178) docs(spec): add staleness and target-existence gaps to warehouse monitoring (BH-1367) — +294/−17
- [#177](https://github.com/brighthive/agentic-project-mgmt/pull/177) docs(spec): warehouse-listing supervisor tool (BH-1454) — +183/−0

---

## platform-saas-ai-context (3 PRs, 3 code)

**Kuri** (3)
- [#51](https://github.com/brighthive/platform-saas-ai-context/pull/51) fix(runbook): pass --allow-blocking, document piped-output hang (BH-1570) — +8/−4
- [#50](https://github.com/brighthive/platform-saas-ai-context/pull/50) docs(infra): harden local-against-staging runbook + preflight script (BH-1553) — +254/−38
- [#48](https://github.com/brighthive/platform-saas-ai-context/pull/48) docs(adr): ADR-016 extend Neo4j for v1 permission matrix, not Cedar/OpenFGA (BH-1464) — +52/−1
