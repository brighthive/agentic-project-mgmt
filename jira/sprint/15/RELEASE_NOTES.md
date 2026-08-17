# Sprint 15 🍑 — Release Notes (Aug 2–17, 2026)

Technical release notes, grouped by repository. Unofficial date-range cut — fifth
in a row; see `SUMMARY.md` for the per-person breakdown and `stats.json` for the
raw numbers.

| Metric | Value |
|---|---|
| PRs merged | 181 (153 code + 28 release/promotion) |
| Tickets resolved | 9 (8 Done, 1 Canceled) — all under the On-Prem Runner epic |
| Repos touched | 8 |
| Code lines (excl. release re-merges) | +87,472 / −44,270 |
| Authors | Kuri (115), Marwan (19), Harbour (19) |

---

## brighthive-platform-core (54 PRs, 42 code)

**On-Prem Engineering Runner — warehouse registration & queue (BH-1403/1421/1426/1439–1441)**
- [#1203](https://github.com/brighthive/brighthive-platform-core/pull/1203) feat(warehouse): register a connected warehouse so it has a Brighthive record
- [#1202](https://github.com/brighthive/brighthive-platform-core/pull/1202) feat(warehouse): verify a connection and persist the databases it reports
- [#1200](https://github.com/brighthive/brighthive-platform-core/pull/1200) feat(warehouse): list the databases a warehouse can actually reach
- [#1197](https://github.com/brighthive/brighthive-platform-core/pull/1197) feat(warehouse): say whether a warehouse is registered or credential-only
- [#1201](https://github.com/brighthive/brighthive-platform-core/pull/1201) / [#1196](https://github.com/brighthive/brighthive-platform-core/pull/1196) fix(schema): restore + emit the four on-prem typeDefs modules
- [#1199](https://github.com/brighthive/brighthive-platform-core/pull/1199) feat(queue): outbound-only job queue for the on-prem runner
- [#1198](https://github.com/brighthive/brighthive-platform-core/pull/1198) feat(lineage): accept on-prem engineering runner run reports
- [#1178](https://github.com/brighthive/brighthive-platform-core/pull/1178) fix(warehouse): pool connected warehouses from secret store, not just registry

**Default-warehouse identity (BH-1362)**
- [#1176](https://github.com/brighthive/brighthive-platform-core/pull/1176) feat(warehouse): isDefault + setDefaultWarehouse

**Routines delivery & provenance (BH-1399)**
- [#1184](https://github.com/brighthive/brighthive-platform-core/pull/1184) feat(workflow): persist executed SQL + thread it into routine notifications
- [#1181](https://github.com/brighthive/brighthive-platform-core/pull/1181) feat(routines): per-routine delivery target passthrough

**Notifications / Signal Catalog / governance (BH-1331/1333/1340/1348)**
- [#1172](https://github.com/brighthive/brighthive-platform-core/pull/1172) feat(notifications): render dbt_remediation_pr_ready as a fix-ready card
- [#1157](https://github.com/brighthive/brighthive-platform-core/pull/1157) feat(notifications): promote Signal Catalog sync + governance gate binding to staging
- [#1156](https://github.com/brighthive/brighthive-platform-core/pull/1156) feat(governance): GovernanceGateBinding anchor — declare mutation + read resolvers
- [#1155](https://github.com/brighthive/brighthive-platform-core/pull/1155) feat(notifications): sync value_drift/null_spike into the Signal Catalog
- [#1154](https://github.com/brighthive/brighthive-platform-core/pull/1154) / [#1153](https://github.com/brighthive/brighthive-platform-core/pull/1153) feat(notifications): fleet-health digest wiring
- [#1160](https://github.com/brighthive/brighthive-platform-core/pull/1160) / [#1159](https://github.com/brighthive/brighthive-platform-core/pull/1159) fix(catalog): cache + Preview health-dot fixes for BYOW assets

**Project run-sync & admin (BH-1330/1352)**
- [#1162](https://github.com/brighthive/brighthive-platform-core/pull/1162) feat(project): syncProjectRuns receiver for engine run-history backfill
- [#1161](https://github.com/brighthive/brighthive-platform-core/pull/1161) feat(admin): resetWorkspaceResources superadmin mutation
- [#1180](https://github.com/brighthive/brighthive-platform-core/pull/1180) feat(catalog): async workspace catalog sync job API
- [#1179](https://github.com/brighthive/brighthive-platform-core/pull/1179) feat(project): trigger activation check when status flips to ACTIVE (Harbour)

**Infra — ECS GraphQL cutover & Neo4j hardening (Marwan)**
- [#1207](https://github.com/brighthive/brighthive-platform-core/pull/1207) feat(cdk): GraphQL ECS CloudFront cutover for staging
- [#1191](https://github.com/brighthive/brighthive-platform-core/pull/1191) feat(ecs): add S3 trust sync and Lambda IAM parity for ECS
- [#1186](https://github.com/brighthive/brighthive-platform-core/pull/1186) feat(servers): add ECS production runtime for GraphQL Core
- [#1194](https://github.com/brighthive/brighthive-platform-core/pull/1194) / [#1189](https://github.com/brighthive/brighthive-platform-core/pull/1189) fix(ecs): SAM Docker build, explicit log group, npm prune
- [#1167](https://github.com/brighthive/brighthive-platform-core/pull/1167) infra(graphql): add Neo4j capacity controls for staging Lambda
- [#1166](https://github.com/brighthive/brighthive-platform-core/pull/1166) perf(catalog): cap OpenMetadata enrichment concurrency
- [#1165](https://github.com/brighthive/brighthive-platform-core/pull/1165) / [#1164](https://github.com/brighthive/brighthive-platform-core/pull/1164) fix(catalog): stop Neo4j health writes on field resolution; failfast 503
- [#1163](https://github.com/brighthive/brighthive-platform-core/pull/1163) fix(neo4j): unify driver and cap connection pool per Lambda
- [#1169](https://github.com/brighthive/brighthive-platform-core/pull/1169) fix(neo4j): eliminate catalog pool storms on staging
- [#1174](https://github.com/brighthive/brighthive-platform-core/pull/1174) feat(graphql): add resourceContentDownloadUrl for Project Files

**Other fixes**
- [#1133](https://github.com/brighthive/brighthive-platform-core/pull/1133) fix(data-asset): stop manual upload from creating ghost assets and timing out (Harbour)
- [#1158](https://github.com/brighthive/brighthive-platform-core/pull/1158) feat(github): attribute agent commits to BrightAgent[bot] identity
- [#1132](https://github.com/brighthive/brighthive-platform-core/pull/1132) feat(infra): wire prod MCP ingress
- [#1129](https://github.com/brighthive/brighthive-platform-core/pull/1129) fix(auth): gate currentUser Cognito admin-flag sync behind feature flag
- [#1171](https://github.com/brighthive/brighthive-platform-core/pull/1171) docs(spec): CDK provisioned concurrency for GraphQL API Lambda

**Releases:** #1206, #1195, #1192, #1190, #1188, #1185, #1177, #1175, #1173, #1170, #1168, #1152

---

## brighthive-webapp (39 PRs, 33 code)

**Warehouse identity & multi-database (BH-1432/1440/1443)**
- [#1423](https://github.com/brighthive/brighthive-webapp/pull/1423) feat(warehouse): expandable row and a readable warehouse table
- [#1430](https://github.com/brighthive/brighthive-webapp/pull/1430) feat(brightagent): name a warehouse and database with @ in the main chat
- [#1429](https://github.com/brighthive/brighthive-webapp/pull/1429) feat(warehouse): choose which database a warehouse resolves to
- [#1425](https://github.com/brighthive/brighthive-webapp/pull/1425) feat(home): show which warehouse each health card is about
- [#1414](https://github.com/brighthive/brighthive-webapp/pull/1414) feat(warehouse): surface default warehouse — badge + admin set-default action
- [#1428](https://github.com/brighthive/brighthive-webapp/pull/1428) / [#1427](https://github.com/brighthive/brighthive-webapp/pull/1427) / [#1426](https://github.com/brighthive/brighthive-webapp/pull/1426) fix(warehouse/home): copy + count + host-display corrections
- [#1424](https://github.com/brighthive/brighthive-webapp/pull/1424) / [#1422](https://github.com/brighthive/brighthive-webapp/pull/1422) / [#1416](https://github.com/brighthive/brighthive-webapp/pull/1416) fix(home): stop showing health signals nothing measures

**Routines & notifications (BH-1400/1330/1331/1337)**
- [#1420](https://github.com/brighthive/brighthive-webapp/pull/1420) feat(routines): delivery-target picker + delivered-channel chip
- [#1410](https://github.com/brighthive/brighthive-webapp/pull/1410) feat(notifications): render the remediation-PR fix as a reviewable card
- [#1396](https://github.com/brighthive/brighthive-webapp/pull/1396) feat(notifications): stage-agnostic richness in the bell-drawer card
- [#1405](https://github.com/brighthive/brighthive-webapp/pull/1405) feat(observability): rich run cards for live runs
- [#1402](https://github.com/brighthive/brighthive-webapp/pull/1402) feat(workflows): admin-only fleet capacity & status panel
- [#1394](https://github.com/brighthive/brighthive-webapp/pull/1394) feat(system-admin): fleet-health page over get_fleet_health MCP
- [#1412](https://github.com/brighthive/brighthive-webapp/pull/1412) fix(navbar): label notification bell for accessibility + stable e2e anchor
- [#1417](https://github.com/brighthive/brighthive-webapp/pull/1417) feat(notifications): inbox and thread UX for project activation check (Harbour)

**BrightAgent chat streaming (Harbour)**
- [#1407](https://github.com/brighthive/brighthive-webapp/pull/1407) fix(brightagent): live SSE token streaming in the chat bubble
- [#1406](https://github.com/brighthive/brighthive-webapp/pull/1406) BrightAgent streaming Phase 1: live SSE bubble and instant commit

**Reliability & cleanup (BH-1036/1350/1372)**
- [#1400](https://github.com/brighthive/brighthive-webapp/pull/1400) fix(apollo): automatic retry logic for transient API failures
- [#1397](https://github.com/brighthive/brighthive-webapp/pull/1397) fix(webapp): hide unreachable integration/tool tiles instead of disabling them
- [#1399](https://github.com/brighthive/brighthive-webapp/pull/1399) feat(home): hide Data Estate warehouse-health band per workspace
- [#1401](https://github.com/brighthive/brighthive-webapp/pull/1401) chore(repo): untrack .env.bak backups and fix ignore pattern
- [#1403](https://github.com/brighthive/brighthive-webapp/pull/1403) fix(upload): retry onboardResource and surface S3 PUT failures (Marwan)
- [#1418](https://github.com/brighthive/brighthive-webapp/pull/1418) feat(catalog): Sync catalog button with async job polling (Marwan)
- [#1395](https://github.com/brighthive/brighthive-webapp/pull/1395) feat(webapp): wire dormant onCreateRule on project observability lineage
- [#1393](https://github.com/brighthive/brighthive-webapp/pull/1393) fix(notifications): add value_drift + null_spike to signal catalog
- [#1411](https://github.com/brighthive/brighthive-webapp/pull/1411) test(e2e): cover workflow re-run-from-node affordance
- [#1409](https://github.com/brighthive/brighthive-webapp/pull/1409) / [#1408](https://github.com/brighthive/brighthive-webapp/pull/1408) docs(apollo): retry + error-classification specs
- [#1365](https://github.com/brighthive/brighthive-webapp/pull/1365) fix(scripts): correct prod GraphQL URL in feature-flags script

**Releases:** #1432, #1415, #1413, #1404, #1398, #1392

---

## brightbot (51 PRs, 42 code)

**On-Prem Engineering Runner / warehouse targeting (BH-1362/1370/1371/1395/1396/1430)**
- [#1033](https://github.com/brighthive/brightbot/pull/1033) feat(chat): honour the database named in a chat mention
- [#1032](https://github.com/brighthive/brightbot/pull/1032) feat(chat): address a warehouse whose name has spaces
- [#1010](https://github.com/brighthive/brightbot/pull/1010) feat(chat): pin the warehouse from an @warehouse:<id> chat mention
- [#1021](https://github.com/brighthive/brightbot/pull/1021) feat(chat): ChatVerb enum for the fan-out verb set
- [#1029](https://github.com/brighthive/brightbot/pull/1029) feat(mcp): target a chosen warehouse and name the host that answered
- [#1030](https://github.com/brighthive/brightbot/pull/1030) fix(mcp): honour the workspace default warehouse
- [#1014](https://github.com/brighthive/brightbot/pull/1014) feat(mcp): surface WORKSPACE→WAREHOUSE→DATABASE ladder as MCP verbs
- [#1016](https://github.com/brighthive/brightbot/pull/1016) feat(mcp): surface SCHEMA+TABLE rungs via list_warehouse_tables
- [#1019](https://github.com/brighthive/brightbot/pull/1019) fix(warehouse): request only deployed WarehouseServiceOutput fields
- [#1035](https://github.com/brighthive/brightbot/pull/1035) / [#1028](https://github.com/brighthive/brightbot/pull/1028) fix(warehouse): route legacy SQL callers through catalog default and chat pin
- [#1031](https://github.com/brighthive/brightbot/pull/1031) test(warehouse): isDefault is deployed, so stop asserting it is absent

**Routines & fleet health (BH-1329/1340/1341/1346/1348/1397/1398)**
- [#1026](https://github.com/brighthive/brightbot/pull/1026) feat(routines): per-routine delivery target + SQL/artifact provenance + PDF
- [#986](https://github.com/brighthive/brightbot/pull/986) feat(warehouse): connection-health verb — identity + liveness, engine-agnostic
- [#985](https://github.com/brighthive/brightbot/pull/985) feat(scheduler): fleet-health digest proactive push
- [#989](https://github.com/brighthive/brightbot/pull/989) feat(governance-agent): drift watchdog wiring + notification link-richness
- [#995](https://github.com/brighthive/brightbot/pull/995) feat(remediation): before+after engine run logs in surgical PRs via PipelineRunner port
- [#1001](https://github.com/brighthive/brightbot/pull/1001) fix(governance-agent): emit critical signal on warehouse connection failure
- [#992](https://github.com/brighthive/brightbot/pull/992) feat(governance-agent): feature-flag the scheduled Warehouse Profiler

**Project sync & agent output (BH-1330/1351/1361)**
- [#999](https://github.com/brighthive/brightbot/pull/999) feat(routes): POST /project/run-sync receiver for authorized forwarder
- [#997](https://github.com/brighthive/brightbot/pull/997) feat(pipelines): source SyncedRun run outputs via a capability-negotiated port verb
- [#994](https://github.com/brighthive/brightbot/pull/994) feat(agent): deterministic source↔target table-parity verb
- [#996](https://github.com/brighthive/brightbot/pull/996) fix(agents): guarantee dbt + analyst emit a turn-stamped Brightside output
- [#990](https://github.com/brighthive/brightbot/pull/990) feat(governance): declare_governance_gate chat tool over declareGovernanceGate mutation

**Product-surface & dbt-agent hardening (Harbour)**
- [#1024](https://github.com/brighthive/brightbot/pull/1024) feat(project): automated activation check when status flips to ACTIVE
- [#1027](https://github.com/brighthive/brightbot/pull/1027) feat(skills): SQL Server diagnostics analyst skill
- [#1003](https://github.com/brighthive/brightbot/pull/1003) feat(supervisor): stream work-panel heartbeats during long model calls
- [#1000](https://github.com/brighthive/brightbot/pull/1000) feat(streaming): stream supervisor LLM tokens live over SSE
- [#993](https://github.com/brighthive/brightbot/pull/993) feat(skills): XSD warehouse reconciliation gate
- [#1022](https://github.com/brighthive/brightbot/pull/1022) fix(tools): harden read_project_schema_file LLM fallback and test isolation
- [#1013](https://github.com/brighthive/brightbot/pull/1013) fix(dbt-agent): recover dropped macro bodies from write_file scratch on commit
- [#1008](https://github.com/brighthive/brightbot/pull/1008) fix(dbt-agent): resolve GitHub commit files from staged and artifact state
- [#1006](https://github.com/brighthive/brightbot/pull/1006) fix(dbt-agent): recover gracefully when github commit tools omit content
- [#1018](https://github.com/brighthive/brightbot/pull/1018) fix(dbt-agent): raise ReAct model max_tokens 4096→16384 to stop file-body truncation
- [#959](https://github.com/brighthive/brightbot/pull/959) chore(skills): tighten XSD skill descriptions and output contract

**Other (Marwan)**
- [#1025](https://github.com/brighthive/brightbot/pull/1025) feat(dbt-agent): auto-enqueue catalog sync after warehouse-changing dbt runs
- [#1004](https://github.com/brighthive/brightbot/pull/1004) feat(dbt): add interim warehouse XML load from Project Files

**Misc**
- [#1002](https://github.com/brighthive/brightbot/pull/1002) docs(readme): correct deploy section — LangGraph Cloud, not Pulumi
- [#998](https://github.com/brighthive/brightbot/pull/998) test: fix local unit-test collection collisions and stale skills assertion

**Releases:** #1036, #1034, #1023, #1020, #1017, #1009, #1007, #1005, #984

---

## brightbot-slack-server (4 PRs, all code)

- [#176](https://github.com/brighthive/brightbot-slack-server/pull/176) feat(notifications): routine result — SQL + artifact link in Slack channel (BH-1401)
- [#175](https://github.com/brighthive/brightbot-slack-server/pull/175) feat(notifications): project activation check signals and toast names (Harbour)
- [#174](https://github.com/brighthive/brightbot-slack-server/pull/174) feat(notifications): promote pipeline-watchdog link renderers to staging
- [#173](https://github.com/brighthive/brightbot-slack-server/pull/173) feat(notifications): render clickable links across pipeline-watchdog stages (BH-1348)

---

## agentic-project-mgmt (22 PRs, all docs/specs/demo)

**On-Prem Engineering Runner specs & Loop Capital sandbox (BH-1403/1404/1405/1406)**
- [#176](https://github.com/brighthive/agentic-project-mgmt/pull/176) feat(loopcapital): reproducible sandbox — manifest capture, synthesize, nuke/recreate
- [#175](https://github.com/brighthive/agentic-project-mgmt/pull/175) docs(spec): on-prem SQL Server + autonomous dbt lifecycle specs
- [#165](https://github.com/brighthive/agentic-project-mgmt/pull/165) docs(demo): LC runbook — source↔target 1:1 parity proof step
- [#160](https://github.com/brighthive/agentic-project-mgmt/pull/160) docs(loopcapital): demo runbook for Frank's 3+1 grounded in real xsd
- [#167](https://github.com/brighthive/agentic-project-mgmt/pull/167) docs(demo): multi-project demo fleet — distinct repos + dbt jobs per project

**Warehouse identity & chat-context specs (BH-172/1362/1371/1396/BH-1353)**
- [#173](https://github.com/brighthive/agentic-project-mgmt/pull/173) docs(spec): default-warehouse UI surfacing
- [#172](https://github.com/brighthive/agentic-project-mgmt/pull/172) docs(spec): warehouse SCHEMA+TABLE rungs over MCP
- [#171](https://github.com/brighthive/agentic-project-mgmt/pull/171) docs(spec): chat @-context injection grammar
- [#170](https://github.com/brighthive/agentic-project-mgmt/pull/170) docs(spec): table parity — structured multi-warehouse multi-database targeting
- [#169](https://github.com/brighthive/agentic-project-mgmt/pull/169) docs(spec): warehouse→database→table hierarchical identity epic
- [#168](https://github.com/brighthive/agentic-project-mgmt/pull/168) docs(spec): warehouse connectivity monitoring + real alerts
- [#164](https://github.com/brighthive/agentic-project-mgmt/pull/164) docs(spec): Context Anchors — inline entity references for BrightAgent chat
- [#162](https://github.com/brighthive/agentic-project-mgmt/pull/162) docs(spec): deterministic source↔target table-parity verb

**Routines, notifications & governance specs (BH-876/1331/1340/1341/1346/1352/1255)**
- [#174](https://github.com/brighthive/agentic-project-mgmt/pull/174) docs(spec): BrightRoutines delivery target, provenance & PDF
- [#161](https://github.com/brighthive/agentic-project-mgmt/pull/161) docs(spec): honest + stable observe surface
- [#159](https://github.com/brighthive/agentic-project-mgmt/pull/159) docs(spec): longitudinal drift watchdog wiring
- [#158](https://github.com/brighthive/agentic-project-mgmt/pull/158) docs(spec): project ACTIVE → SYNC() fan-out surfacing proactive golden nuggets
- [#157](https://github.com/brighthive/agentic-project-mgmt/pull/157) docs(spec): warehouse connection-health verb
- [#156](https://github.com/brighthive/agentic-project-mgmt/pull/156) docs(spec): fleet-health digest proactive push
- [#155](https://github.com/brighthive/agentic-project-mgmt/pull/155) docs(spec): project governance–observability convergence surface
- [#163](https://github.com/brighthive/agentic-project-mgmt/pull/163) docs(spec): resetWorkspaceResources — purge workspace to zero-state, zero orphans
- [#166](https://github.com/brighthive/agentic-project-mgmt/pull/166) docs(spec): correct §2.3 sync direction to brightbot→platform-core per ADR-015

---

## brighthive-e2e (8 PRs, all code)

- [#84](https://github.com/brighthive/brighthive-e2e/pull/84) test(warehouse): surface tests for verify, register, and default database
- [#83](https://github.com/brighthive/brighthive-e2e/pull/83) test(e2e): routines delivery-target + result-provenance chain
- [#82](https://github.com/brighthive/brighthive-e2e/pull/82) test(scheduler): §10b delivery-target chain e2e
- [#80](https://github.com/brighthive/brighthive-e2e/pull/80) test(mcp): §10b e2e for SCHEMA→TABLE rung — list_warehouse_tables
- [#78](https://github.com/brighthive/brighthive-e2e/pull/78) test(mcp): warehouse-catalog ladder e2e — WORKSPACE→WAREHOUSE→DATABASE
- [#77](https://github.com/brighthive/brighthive-e2e/pull/77) test(e2e): project run-sync link→sync→runs+data-products contract
- [#76](https://github.com/brighthive/brighthive-e2e/pull/76) test(e2e): before+after evidence on live agent remediation PRs
- [#75](https://github.com/brighthive/brighthive-e2e/pull/75) fix(e2e): guard two fixture-shape gaps found by full 4-config sweep

---

## brighthive-data-organization-cdk (2 PRs, 1 code)

- [#160](https://github.com/brighthive/brighthive-data-organization-cdk/pull/160) Marwan/graphql ecs s3 trust

**Releases:** #161

---

## platform-saas-ai-context (1 PR)

- [#45](https://github.com/brighthive/platform-saas-ai-context/pull/45) docs(infra+arch): Lambda concurrency setup + dbt Cloud multi-tenant patterns
