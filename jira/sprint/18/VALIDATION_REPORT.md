# Sprint 18 🍒 — Validation Report

## Tickets moved to Done in window
None. Zero BH tickets resolved between Oct 7 and Nov 26.

## Tickets referenced by PRs — status today (99)

| Status | Count |
|---|---|
| Needs Refinement | 68 |
| To Do | 15 |
| Done | 8 |
| Code Review | 3 |
| Testing (Dev) | 3 |
| In Progress | 1 |
| Staging QC | 1 |

Tickets with shipped PRs still in To Do / Needs Refinement should be swept to Testing or Done.

## Orphan PRs (no `BH-XXX` / `AZ-XXX` in title, branch, or body) — 85
- Marwan-Samih-Brighthive · brightbot [#1214](https://github.com/brighthive/brightbot/pull/1214) feat(dbt): prefer stored dbt Cloud project/environment ids over repo match
- Marwan-Samih-Brighthive · brighthive-platform-core [#1385](https://github.com/brighthive/brighthive-platform-core/pull/1385) fix(azure-k8s): size the OpenMetadata MySQL volume at 20Gi and grow existing clusters in place
- Marwan-Samih-Brighthive · brighthive-platform-core [#1384](https://github.com/brighthive/brighthive-platform-core/pull/1384) chore(azure-k8s): configure Entra given_name/family_name claims via script and document it
- Marwan-Samih-Brighthive · brighthive-platform-core [#1383](https://github.com/brighthive/brighthive-platform-core/pull/1383) fix(users): never expose empty/null user names; derive them when the IdP sends none
- Marwan-Samih-Brighthive · brighthive-platform-core [#1381](https://github.com/brighthive/brighthive-platform-core/pull/1381) fix(azure-k8s): read and store GitHub auth tokens via the platform secret store
- Marwan-Samih-Brighthive · brighthive-platform-core [#1380](https://github.com/brighthive/brighthive-platform-core/pull/1380) feat(dbt): optional per-service dbt Cloud project and environment ids
- Marwan-Samih-Brighthive · brighthive-webapp [#1512](https://github.com/brighthive/brighthive-webapp/pull/1512) feat(settings): dbt Cloud project and environment ids on dbt services
- Marwan-Samih-Brighthive · brighthive-webapp [#1510](https://github.com/brighthive/brighthive-webapp/pull/1510) Feature/azure k8s webapp
- Nano-233 · brightbot [#1235](https://github.com/brighthive/brightbot/pull/1235) feat(pipeline-author): leave identity_resolution SQL to the platform (Azure)
- Nano-233 · brightbot [#1233](https://github.com/brighthive/brightbot/pull/1233) fix(pipeline): repair any warehouse SQL error except timeouts and access failures
- Nano-233 · brightbot [#1232](https://github.com/brighthive/brightbot/pull/1232) feat(mcp): repair_project_pipeline_sql rewrites failed SQL steps
- Nano-233 · brightbot [#1231](https://github.com/brighthive/brightbot/pull/1231) fix(pipeline): author pipelines with Sonnet instead of Haiku
- Nano-233 · brightbot [#1230](https://github.com/brighthive/brightbot/pull/1230) fix(pipeline): give the author column types and ban STRING_AGG(DISTINCT) on T-SQL
- Nano-233 · brightbot [#1229](https://github.com/brighthive/brightbot/pull/1229) fix(pipeline): raise pipeline author output limit to 16k tokens
- Nano-233 · brightbot [#1228](https://github.com/brighthive/brightbot/pull/1228) fix(pipeline): author SQL against listed columns in the warehouse dialect
- Nano-233 · brightbot [#1227](https://github.com/brighthive/brightbot/pull/1227) fix(pipeline): refuse to apply spec-parser fallback pipelines
- Nano-233 · brightbot [#1224](https://github.com/brighthive/brightbot/pull/1224) feat(azure-k8s): project watchdog store on Azure Table Storage
- Nano-233 · brightbot [#1223](https://github.com/brighthive/brightbot/pull/1223) feat(mcp): schedule_asset_monitor and run_scheduled_agent_now
- Nano-233 · brightbot [#1219](https://github.com/brighthive/brightbot/pull/1219) fix(scheduler): pass service token to scheduled quality checks; add openai LLM provider
- Nano-233 · brightbot [#1213](https://github.com/brighthive/brightbot/pull/1213) feat(mcp): permission-matrix-driven MCP access on all profiles; lock risky tools on azure-k8s
- Nano-233 · brightbot [#1212](https://github.com/brighthive/brightbot/pull/1212) feat(azure-k8s): scheduled agents Table Storage + Azure cron dispatcher
- Nano-233 · brightbot [#1211](https://github.com/brighthive/brightbot/pull/1211) docs(azure-k8s): BrightSignals publisher env for Nestlé LangGraph
- Nano-233 · brightbot [#1210](https://github.com/brighthive/brightbot/pull/1210) feat(governance): Path B AKS diagnostic sandbox (includes Path A analyst executor)
- Nano-233 · brightbot [#1209](https://github.com/brighthive/brightbot/pull/1209) feat(azure-k8s): route analyst Python to AKS executor
- Nano-233 · brightbot [#1208](https://github.com/brighthive/brightbot/pull/1208) P2.0 MCP E2E wrap-up (bundle with core + e2e)
- Nano-233 · brightbot [#1207](https://github.com/brighthive/brightbot/pull/1207) fix(azure): SSIS Blob fetch + MCP project context notes
- Nano-233 · brightbot [#1206](https://github.com/brighthive/brightbot/pull/1206) feat(azure): profile-only routing and blob follow-ups
- Nano-233 · brightbot [#1202](https://github.com/brighthive/brightbot/pull/1202) feat(azure): Entra OGM service token (stacked on aws-only-gates)
- Nano-233 · brightbot [#1201](https://github.com/brighthive/brightbot/pull/1201) feat(azure): store agent files in Blob
- Nano-233 · brightbot [#1199](https://github.com/brighthive/brightbot/pull/1199) feat(azure): gate AWS-only BrightAgent features
- Nano-233 · brightbot [#1197](https://github.com/brighthive/brightbot/pull/1197) feat(azure): read workspace secrets from Key Vault
- Nano-233 · brightbot-slack-server [#187](https://github.com/brighthive/brightbot-slack-server/pull/187) fix(azure-k8s): SSE JWT validation via jwks-rsa (Core parity)
- Nano-233 · brightbot-slack-server [#186](https://github.com/brighthive/brightbot-slack-server/pull/186) fix(azure-k8s): SSE Entra JWKS + azurefd CORS for bh-demo
- Nano-233 · brightbot-slack-server [#185](https://github.com/brighthive/brightbot-slack-server/pull/185) feat(azure-k8s): Tier 2 notifications-stream (GraphQL poller + SSE)
- Nano-233 · brightbot-slack-server [#184](https://github.com/brighthive/brightbot-slack-server/pull/184) fix(notifications): post Teams webhooks only to Microsoft hosts
- Nano-233 · brightbot-slack-server [#179](https://github.com/brighthive/brightbot-slack-server/pull/179) Add Microsoft Teams delivery channel for notifications
- Nano-233 · brighthive-e2e [#112](https://github.com/brighthive/brighthive-e2e/pull/112) P2.0 MCP E2E wrap-up: legacy graph tools removed
- Nano-233 · brighthive-platform-core [#1396](https://github.com/brighthive/brighthive-platform-core/pull/1396) fix(pipeline): drop leftover Synapse smoke tables before a re-run (Azure)
- Nano-233 · brighthive-platform-core [#1395](https://github.com/brighthive/brighthive-platform-core/pull/1395) fix(pipeline): give transform steps an output table (Azure)
- Nano-233 · brighthive-platform-core [#1394](https://github.com/brighthive/brighthive-platform-core/pull/1394) fix(pipeline): connect steps that only inherit tables to the right database (Azure)
- Nano-233 · brighthive-platform-core [#1393](https://github.com/brighthive/brighthive-platform-core/pull/1393) feat(pipeline): first-pass identity resolution SQL (Azure)
- Nano-233 · brighthive-platform-core [#1391](https://github.com/brighthive/brighthive-platform-core/pull/1391) fix(pipeline): give the pipeline author real columns and the SQL dialect
- Nano-233 · brighthive-platform-core [#1390](https://github.com/brighthive/brighthive-platform-core/pull/1390) fix(pipeline): stop spec apply from building broken pipelines
- Nano-233 · brighthive-platform-core [#1382](https://github.com/brighthive/brighthive-platform-core/pull/1382) feat(core): service-key query for workspace field PII classifications
- Nano-233 · brighthive-platform-core [#1379](https://github.com/brighthive/brighthive-platform-core/pull/1379) Proxy browser SSE via platform-core to notifications-stream
- Nano-233 · brighthive-platform-core [#1378](https://github.com/brighthive/brighthive-platform-core/pull/1378) fix(ci): PAT for slack-server checkout on bh-demo deploy
- Nano-233 · brighthive-platform-core [#1377](https://github.com/brighthive/brighthive-platform-core/pull/1377) feat(azure-k8s): Tier 1 BrightSignals inbox + notifications-stream deploy
- Nano-233 · brighthive-platform-core [#1376](https://github.com/brighthive/brighthive-platform-core/pull/1376) feat(governance): Path B executor Jobs + governance-sandbox image (includes Path A)
- Nano-233 · brighthive-platform-core [#1375](https://github.com/brighthive/brighthive-platform-core/pull/1375) feat(azure-k8s): Nestlé analyst AKS executor (Job + Blob sync)
- Nano-233 · brighthive-platform-core [#1373](https://github.com/brighthive/brighthive-platform-core/pull/1373) P2.0 MCP E2E wrap-up: lightweight local admin seed
- Nano-233 · brighthive-platform-core [#1371](https://github.com/brighthive/brighthive-platform-core/pull/1371) feat(azure): lightweight demo graph seed (warehouse + assets)
- Nano-233 · brighthive-platform-core [#1370](https://github.com/brighthive/brighthive-platform-core/pull/1370) feat(azure): logo PUT + blob presign gaps (single-tenant)
- Nano-233 · brighthive-platform-core [#1368](https://github.com/brighthive/brighthive-platform-core/pull/1368) feat(azure): mount /ogm on Core pod for Entra SystemAdmin tokens
- Nano-233 · brighthive-platform-core [#1366](https://github.com/brighthive/brighthive-platform-core/pull/1366) fix(notifications): validate and replace Teams webhook URLs
- Nano-233 · brighthive-platform-core [#1365](https://github.com/brighthive/brighthive-platform-core/pull/1365) fix: throw when a data asset group cannot be loaded
- Nano-233 · brighthive-platform-core [#1364](https://github.com/brighthive/brighthive-platform-core/pull/1364) fix: drop the catalog rebuild from asset writes
- Nano-233 · brighthive-platform-core [#1347](https://github.com/brighthive/brighthive-platform-core/pull/1347) feat(notifications): route Teams through slack-server from the dispatcher Lambda
- Nano-233 · brighthive-webapp [#1511](https://github.com/brighthive/brighthive-webapp/pull/1511) fix(webapp): workspace logo upload via presigned PUT
- Nano-233 · brighthive-webapp [#1509](https://github.com/brighthive/brighthive-webapp/pull/1509) fix(notifications): accept a real Teams webhook URL
- drchinca · agentic-project-mgmt [#216](https://github.com/brighthive/agentic-project-mgmt/pull/216) docs(clients): add pipeline clients to the index
- drchinca · agentic-project-mgmt [#214](https://github.com/brighthive/agentic-project-mgmt/pull/214) docs(specs): correct two citations in the cloud-agnostic adapters spec
- drchinca · agentic-project-mgmt [#208](https://github.com/brighthive/agentic-project-mgmt/pull/208) docs(roadmap): Q4 2026 to Q2 2027 capacity roadmap for Loop and Nestlé
- drchinca · agentic-project-mgmt [#207](https://github.com/brighthive/agentic-project-mgmt/pull/207) docs(clients): Loop AI governance requirements fit and co-build pitch
- drchinca · agentic-project-mgmt [#205](https://github.com/brighthive/agentic-project-mgmt/pull/205) docs(clients): align Loop governance and Nestlé Azure to tickets
- drchinca · agentic-project-mgmt [#203](https://github.com/brighthive/agentic-project-mgmt/pull/203) docs(clients): create Nestle global trial room
- drchinca · agentic-project-mgmt [#199](https://github.com/brighthive/agentic-project-mgmt/pull/199) docs(specs): executable MCP pilot journeys
- drchinca · agentic-project-mgmt [#190](https://github.com/brighthive/agentic-project-mgmt/pull/190) docs(vision): AI Data Engineer 3-tier vision mapped to reality
- drchinca · brightagent-selfhost [#4](https://github.com/brighthive/brightagent-selfhost/pull/4) feat: add an opt-in registry import path to the install root
- drchinca · brightagent-selfhost [#3](https://github.com/brighthive/brightagent-selfhost/pull/3) fix: set the AKS image cleaner interval in the install root
- drchinca · brightagent-selfhost [#2](https://github.com/brighthive/brightagent-selfhost/pull/2) fix: add offline checks and a wider example guard to the runbook
- drchinca · brightagent-selfhost [#1](https://github.com/brighthive/brightagent-selfhost/pull/1) feat: add the agent install runbook and Terraform tests
- drchinca · brightbot [#1200](https://github.com/brighthive/brightbot/pull/1200) fix(mcp): restore Snowflake reads and catalog fallback
- drchinca · brightbot [#1188](https://github.com/brighthive/brightbot/pull/1188) fix(ci): publish immutable releases and verify active deployments
- drchinca · brightbot-slack-server [#180](https://github.com/brighthive/brightbot-slack-server/pull/180) feat(slack): add remediation proposal actions
- drchinca · brighthive-e2e [#111](https://github.com/brighthive/brighthive-e2e/pull/111) fix(e2e): align staging MCP reads and protect privacy evidence
- drchinca · brighthive-e2e [#101](https://github.com/brighthive/brighthive-e2e/pull/101) test(mcp): verify positive quality write lifecycle
- drchinca · brighthive-platform-core [#1367](https://github.com/brighthive/brighthive-platform-core/pull/1367) feat(platform): multi-cloud single-tenant runtime (NO-TICKET)
- drchinca · brighthive-platform-core [#1361](https://github.com/brighthive/brighthive-platform-core/pull/1361) fix: preserve canonical catalog table and warehouse identities
- drchinca · brighthive-platform-core [#1360](https://github.com/brighthive/brighthive-platform-core/pull/1360) fix: redact production role secret update log
- drchinca · brighthive-webapp [#1508](https://github.com/brighthive/brighthive-webapp/pull/1508) fix: verify production release from served build provenance
- drchinca · brighthive-webapp [#1507](https://github.com/brighthive/brighthive-webapp/pull/1507) fix: limit Amplify release update output to app ID
- drchinca · brighthive-webapp [#1506](https://github.com/brighthive/brighthive-webapp/pull/1506) ci: verify the production Amplify release build
- drchinca · platform-saas-ai-context [#52](https://github.com/brighthive/platform-saas-ai-context/pull/52) docs(infra): record deployed staging MCP mutation storage
- drchinca · platform-saas-ai-context [#49](https://github.com/brighthive/platform-saas-ai-context/pull/49) docs(infra): document Cognito-healthy/missing-UserNode login failure pattern
- drchinca · platform-saas-ai-context [#43](https://github.com/brighthive/platform-saas-ai-context/pull/43) docs(infra): release-tag prod deploy + develop/main drift + branch/admin gotchas

## PRs merged into a feature branch, not develop — 56
These land on develop only when the feature branch itself merges (platform-core #1367 carried the `feature/multi-cloud-runtime-complete` work). Remaining open feature branches hold work that is merged but not yet in develop.

- `feature/multi-cloud-runtime-complete` — 22
- `feat/deployment-profile` — 19
- `production` — 5
- `feature/azure-k8s-notifications-runtime` — 3
- `feature/azure-k8s-webapp` — 2
- `drchinca/AZ-101/mcp-startup` — 1
- `drchinca/AZ-101/standalone-mcp-deps` — 1
- `drchinca/AZ-101/mcp-tool-registries` — 1
- `feat/aws-only-gates` — 1
- `drchinca/BH-453/brightagent-v4-decision` — 1

## Estimation gaps
No story points on any in-window ticket — team does not estimate.
