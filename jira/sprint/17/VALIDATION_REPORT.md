# Sprint 17 🥝 — Validation Report

## Tickets moved to Done without a matching in-window PR
- BH-1539 — Neo4j reboot incident (ops fix, no PR expected)

## Orphan PRs (merged, no `BH-XXX` in title or branch) — 48
- Nano-233 · brightbot [#1087](https://github.com/brighthive/brightbot/pull/1087) refactor(scheduler): shared in-process create seam + review polish (follow-up to #1086)
- Nano-233 · brightbot [#1086](https://github.com/brighthive/brightbot/pull/1086) fix(scheduler): call scheduled-agents in-process, drop the self-URL env
- Nano-233 · brightbot [#1081](https://github.com/brighthive/brightbot/pull/1081) feat(pipelines): chat-configurable project pipeline scheduling (decoupled from dbt)
- Marwan-Samih-Brighthive · brightbot [#1079](https://github.com/brighthive/brightbot/pull/1079) feat(pipeline): dbt engineering propose path and run diagnostics
- Nano-233 · brightbot [#1078](https://github.com/brighthive/brightbot/pull/1078) fix(routing): route pipeline lifecycle (list/schedule/runs) to dbt subagent
- Marwan-Samih-Brighthive · brightbot [#1071](https://github.com/brighthive/brightbot/pull/1071) feat(project): spec author, conversational bootstrap, and pipeline verifier
- Marwan-Samih-Brighthive · brightbot [#1066](https://github.com/brighthive/brightbot/pull/1066) feat(routing): asset-scoped multi-warehouse SQL routing
- Nano-233 · brightbot [#1063](https://github.com/brighthive/brightbot/pull/1063) feat(i18n): localize QC reports from workspace locale
- Marwan-Samih-Brighthive · brightbot [#1049](https://github.com/brighthive/brightbot/pull/1049) feat(warehouse): route background jobs to asset-scoped warehouse
- Marwan-Samih-Brighthive · brightbot [#1044](https://github.com/brighthive/brightbot/pull/1044) feat(catalog-search): read-only vector search with optional @ scope
- Marwan-Samih-Brighthive · brighthive-platform-core [#1311](https://github.com/brighthive/brighthive-platform-core/pull/1311) fix(ci): set ENV on prod and dev CDK deploy workflows
- Marwan-Samih-Brighthive · brighthive-platform-core [#1310](https://github.com/brighthive/brighthive-platform-core/pull/1310) Prod graphql ecs cutover
- Marwan-Samih-Brighthive · brighthive-platform-core [#1308](https://github.com/brighthive/brighthive-platform-core/pull/1308) fix(cognito): gate MCP auth domain off prod and recover UserPool deploy
- Marwan-Samih-Brighthive · brighthive-platform-core [#1303](https://github.com/brighthive/brighthive-platform-core/pull/1303) feat(workflow): dbt engineering pipeline specs and run reconciliation
- Nano-233 · brighthive-platform-core [#1302](https://github.com/brighthive/brighthive-platform-core/pull/1302) fix(login): don't rethrow raw Cognito exceptions on bad credentials
- Marwan-Samih-Brighthive · brighthive-platform-core [#1300](https://github.com/brighthive/brighthive-platform-core/pull/1300) feat(project): project 2.0 spec API, apply pipeline, and smoke validation
- Marwan-Samih-Brighthive · brighthive-platform-core [#1296](https://github.com/brighthive/brighthive-platform-core/pull/1296) feat(catalog): warehouse routing fields for multi-warehouse assets
- Nano-233 · brighthive-platform-core [#1277](https://github.com/brighthive/brighthive-platform-core/pull/1277) feat(i18n): persist workspace locale
- Marwan-Samih-Brighthive · brighthive-platform-core [#1244](https://github.com/brighthive/brighthive-platform-core/pull/1244) fix(warehouse): satisfy WarehouseSecretStore types on upsert
- Marwan-Samih-Brighthive · brighthive-platform-core [#1242](https://github.com/brighthive/brighthive-platform-core/pull/1242) feat(warehouse): validate secrets and merge node defaults on upsert
- drchinca · brighthive-platform-core [#1235](https://github.com/brighthive/brighthive-platform-core/pull/1235) fix(test): update stale purgeAssetEmbedding DEL assertion for the v2 key
- Marwan-Samih-Brighthive · brighthive-platform-core [#1232](https://github.com/brighthive/brighthive-platform-core/pull/1232) feat(graphql): expose catalog hierarchy fields on DataAsset
- Marwan-Samih-Brighthive · brighthive-platform-core [#1230](https://github.com/brighthive/brighthive-platform-core/pull/1230) fix initalization call
- Marwan-Samih-Brighthive · brighthive-platform-core [#1228](https://github.com/brighthive/brighthive-platform-core/pull/1228) fix(catalog-search): enrich Redis docs with fields and warehouse context
- Marwan-Samih-Brighthive · brighthive-platform-core [#1226](https://github.com/brighthive/brighthive-platform-core/pull/1226) fix(cdk): wire OPENAI_API_KEY into GraphQL ECS task env
- Marwan-Samih-Brighthive · brighthive-platform-core [#1224](https://github.com/brighthive/brighthive-platform-core/pull/1224) Feat/catalog search index
- Marwan-Samih-Brighthive · brighthive-platform-core [#1222](https://github.com/brighthive/brighthive-platform-core/pull/1222) fix(catalog-search): avoid closing shared Redis client in status query
- Marwan-Samih-Brighthive · brighthive-platform-core [#1220](https://github.com/brighthive/brighthive-platform-core/pull/1220) feat(catalog-search): async hierarchy-aware Redis index pipeline
- drchinca · brighthive-webapp [#1477](https://github.com/brighthive/brighthive-webapp/pull/1477) fix(workflows): verify context and mobile agent review handoff
- drchinca · brighthive-webapp [#1476](https://github.com/brighthive/brighthive-webapp/pull/1476) feat(workflows): expose execution, access and connection primitives
- drchinca · brighthive-webapp [#1475](https://github.com/brighthive/brighthive-webapp/pull/1475) feat(workflows): expose project context and missing primitives
- drchinca · brighthive-webapp [#1474](https://github.com/brighthive/brighthive-webapp/pull/1474) feat(workflows): show project agent actions and review states
- Nano-233 · brighthive-webapp [#1473](https://github.com/brighthive/brighthive-webapp/pull/1473) fix(schedules,brightagent): human-readable cadence, project labels, spec-chat clear + autoscroll
- Marwan-Samih-Brighthive · brighthive-webapp [#1471](https://github.com/brighthive/brighthive-webapp/pull/1471) feat(project-flow): dbt engineering step config and run history UX
- Nano-233 · brighthive-webapp [#1470](https://github.com/brighthive/brighthive-webapp/pull/1470) fix(auth): stop showing two contradictory toasts on login failure
- Nano-233 · brighthive-webapp [#1469](https://github.com/brighthive/brighthive-webapp/pull/1469) fix(catalog): show load error instead of a no-match empty grid
- Nano-233 · brighthive-webapp [#1468](https://github.com/brighthive/brighthive-webapp/pull/1468) fix(shared-links): confirm revoke and toast on failure
- Nano-233 · brighthive-webapp [#1466](https://github.com/brighthive/brighthive-webapp/pull/1466) fix(sessions): refresh the list after delete and surface failures
- Nano-233 · brighthive-webapp [#1465](https://github.com/brighthive/brighthive-webapp/pull/1465) feat(auth): globe language switcher on login + full locale on workspace select
- Nano-233 · brighthive-webapp [#1464](https://github.com/brighthive/brighthive-webapp/pull/1464) feat(navbar): keep Log out visible in overflowing user menu
- Marwan-Samih-Brighthive · brighthive-webapp [#1460](https://github.com/brighthive/brighthive-webapp/pull/1460) feat(project): spec tab, pipeline canvas, verify pipeline, and catalog sync
- Marwan-Samih-Brighthive · brighthive-webapp [#1457](https://github.com/brighthive/brighthive-webapp/pull/1457) feat(catalog): multi-warehouse hierarchy tree grouping
- Nano-233 · brighthive-webapp [#1456](https://github.com/brighthive/brighthive-webapp/pull/1456) feat(i18n): translate BrightAgent stream status and output panel chrome
- Marwan-Samih-Brighthive · brighthive-webapp [#1445](https://github.com/brighthive/brighthive-webapp/pull/1445) fix(webapp): resolve catalog and warehouse TypeScript errors
- Marwan-Samih-Brighthive · brighthive-webapp [#1443](https://github.com/brighthive/brighthive-webapp/pull/1443) feat(warehouse): verify connection and collect Redshift schema
- Marwan-Samih-Brighthive · brighthive-webapp [#1439](https://github.com/brighthive/brighthive-webapp/pull/1439) feat(catalog): add Data Catalog (new) to feature flags admin UI
- Marwan-Samih-Brighthive · brighthive-webapp [#1437](https://github.com/brighthive/brighthive-webapp/pull/1437) feat(catalog): add warehouse-aware Data Catalog (new) view
- Nano-233 · brighthive-webapp [#1436](https://github.com/brighthive/brighthive-webapp/pull/1436) feat(i18n): add English, Spanish, and Portuguese UI translations

## Ticket status drift
98 tickets referenced by merged PRs; only 5 are Done. 35 sit in Testing (Dev) and 46 in
Needs Refinement while their code is merged (and, for BH-1464, enforced on staging).

## Estimation gaps
No story points on any ticket in the window.

## Branch naming
Engineer branches use `feat/…`, `fix/…`, `feature/…` with no ticket id; the convention is
`name/BH-XXX/description`.
