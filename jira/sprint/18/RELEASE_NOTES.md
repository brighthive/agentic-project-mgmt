# Sprint 18 🍒 — Release Notes (Oct 7 – Nov 26, 2026)

Technical release notes, grouped by repository then author. Unofficial date-range cut — the previous release was Sprint 17 🥝 (Aug 24 – Oct 6). See `SUMMARY.md` for the per-person analysis and `stats.json` for the raw numbers.

🕒 marks a PR merged in the **last 3 weeks** (Nov 5 – Nov 26).

| Metric | Value |
|---|---|
| PRs merged | 412 (384 code + 28 release/promotion) |
| Production release | Staging → Production on Oct 16 (brightbot #1187, platform-core #1359, webapp #1505) |
| Azure delivery releases | brighthive-deploy v0.1.0 (Oct 29) and v0.2.0 (Nov 16) |
| Tickets transitioned to Done | 0 |
| Repos touched | 11 |
| Code lines (excl. release re-merges) | +290,650 / −66,998 |
| Code PRs — last 3 weeks (Nov 5 – 26) | Kuri 110 · Harbour 24 · Marwan 8 (team 142) |
| Code PRs — whole sprint (Oct 7 – Nov 26) | Kuri 323 · Harbour 53 · Marwan 8 (team 384) |

Release/promotion carriers (develop→staging, staging→production, versioned releases) are excluded from the lists below.

---

## brighthive-deploy (113 PRs, 111 code)

**Kuri** (111)
- 🕒 [#147](https://github.com/brighthive/brighthive-deploy/pull/147) feat(helm): describe each runtime in a profile so brightbot and BrightAgent plug in (AZ-112) — +1310/−207
- 🕒 [#146](https://github.com/brighthive/brighthive-deploy/pull/146) docs(mcp): give the customer package a readable front page (AZ-111) — +129/−30
- 🕒 [#145](https://github.com/brighthive/brighthive-deploy/pull/145) feat(mcp): gate the customer install and close the launch audit (AZ-105) — +3148/−72
- 🕒 [#142](https://github.com/brighthive/brighthive-deploy/pull/142) feat(network): admit a second cluster's overlay pod range for the rehearsal (AZ-008) — +85/−0
- 🕒 [#141](https://github.com/brighthive/brighthive-deploy/pull/141) feat(mcp): add an opt-in registry import path to the install root (AZ-008) — +34/−2
- 🕒 [#140](https://github.com/brighthive/brighthive-deploy/pull/140) feat(network): add optional endpoint DNS for the install rehearsal (AZ-008) — +100/−0
- 🕒 [#139](https://github.com/brighthive/brighthive-deploy/pull/139) fix(mcp): set the AKS image cleaner interval in the customer install (AZ-008) — +5/−0
- 🕒 [#138](https://github.com/brighthive/brighthive-deploy/pull/138) fix(deploy): record the current operator address in state access (AZ-104) — +2/−1
- 🕒 [#137](https://github.com/brighthive/brighthive-deploy/pull/137) feat(network): add an optional AKS private zone for the install rehearsal (AZ-008) — +84/−0
- 🕒 [#136](https://github.com/brighthive/brighthive-deploy/pull/136) fix(mcp): add offline checks and a wider example guard to the runbook (AZ-008) — +16/−6
- 🕒 [#135](https://github.com/brighthive/brighthive-deploy/pull/135) feat(mcp): make the customer install agent-operable (AZ-008) — +194/−1
- 🕒 [#134](https://github.com/brighthive/brighthive-deploy/pull/134) docs(mcp): explain customer inputs and existing-cluster checks (AZ-008) — +50/−8
- 🕒 [#133](https://github.com/brighthive/brighthive-deploy/pull/133) docs(spec): record the live Projects egress and Cognito path (AZ-104) — +13/−2
- 🕒 [#132](https://github.com/brighthive/brighthive-deploy/pull/132) feat(mcp): prepare the Azure installer rehearsal (AZ-008) — +85/−0
- 🕒 [#131](https://github.com/brighthive/brighthive-deploy/pull/131) feat(mcp): package the public warehouse self-install source (AZ-008) — +423/−3
- 🕒 [#130](https://github.com/brighthive/brighthive-deploy/pull/130) docs(mcp): make customer setup requirements explicit (AZ-008) — +494/−115
- 🕒 [#128](https://github.com/brighthive/brighthive-deploy/pull/128) docs(mcp): publish live connection proof and setup guide (AZ-104) — +390/−48
- 🕒 [#127](https://github.com/brighthive/brighthive-deploy/pull/127) fix(network): refresh the MCP operator address (AZ-104) — +2/−1
- 🕒 [#126](https://github.com/brighthive/brighthive-deploy/pull/126) fix(network): admit Azure Firewall instance sources (AZ-104) — +142/−33
- 🕒 [#125](https://github.com/brighthive/brighthive-deploy/pull/125) fix(network): admit MCP floating IP destinations (AZ-104) — +145/−3
- 🕒 [#124](https://github.com/brighthive/brighthive-deploy/pull/124) feat(mcp): prepare separate Synapse host access (AZ-104) — +417/−2
- 🕒 [#122](https://github.com/brighthive/brighthive-deploy/pull/122) feat(network): add IP-restricted Projects HTTPS access (AZ-104) — +504/−11
- 🕒 [#120](https://github.com/brighthive/brighthive-deploy/pull/120) docs(azure): publish product status and client access (AZ-104) — +89/−0
- 🕒 [#118](https://github.com/brighthive/brighthive-deploy/pull/118) feat(deploy): run Projects harness against AWS staging (AZ-104) — +421/−12
- 🕒 [#119](https://github.com/brighthive/brighthive-deploy/pull/119) feat(network): prepare private Projects VPN access (AZ-104) — +570/−1
- 🕒 [#116](https://github.com/brighthive/brighthive-deploy/pull/116) fix(deploy): restore state access for Projects rollout (AZ-104) — +34/−0
- 🕒 [#114](https://github.com/brighthive/brighthive-deploy/pull/114) feat(mcp): add the Azure Cognito Projects approach (AZ-104) — +437/−27
- 🕒 [#113](https://github.com/brighthive/brighthive-deploy/pull/113) docs(workflow): preserve migration approaches on branches (AZ-104) — +20/−0
- 🕒 [#112](https://github.com/brighthive/brighthive-deploy/pull/112) feat(mcp): prepare the self-hosted PROJECTS staging proof (AZ-104) — +848/−14
- 🕒 [#111](https://github.com/brighthive/brighthive-deploy/pull/111) docs(mcp): guide both customer AKS installation modes (AZ-008) — +364/−171
- 🕒 [#110](https://github.com/brighthive/brighthive-deploy/pull/110) test(mcp): exercise customer installation guards (AZ-008) — +311/−0
- 🕒 [#109](https://github.com/brighthive/brighthive-deploy/pull/109) feat(mcp): install reviewed customer runtime bundles (AZ-008) — +469/−0
- 🕒 [#107](https://github.com/brighthive/brighthive-deploy/pull/107) feat(mcp): serve the warehouse profile over private TLS (AZ-008) — +285/−19
- 🕒 [#108](https://github.com/brighthive/brighthive-deploy/pull/108) feat(mcp): provision the customer Azure runtime (AZ-008) — +696/−2
- 🕒 [#106](https://github.com/brighthive/brighthive-deploy/pull/106) feat(mcp): connect an existing customer Synapse (AZ-008) — +679/−13
- 🕒 [#105](https://github.com/brighthive/brighthive-deploy/pull/105) feat(mcp): publish the accepted private proof runner (AZ-101) — +697/−2
- 🕒 [#104](https://github.com/brighthive/brighthive-deploy/pull/104) fix(mcp): await command completion and retain proof (AZ-101) — +278/−11
- 🕒 [#95](https://github.com/brighthive/brighthive-deploy/pull/95) fix(mcp): complete private Synapse M1 acceptance (AZ-101) — +602/−92
- 🕒 [#96](https://github.com/brighthive/brighthive-deploy/pull/96) docs(specs): set the direction and first customer deployment (AZ-102) — +607/−30
- 🕒 [#103](https://github.com/brighthive/brighthive-deploy/pull/103) feat(mcp): run the isolated foreign caller proof (AZ-101) — +679/−19
- 🕒 [#102](https://github.com/brighthive/brighthive-deploy/pull/102) ci(envoy): collect bounded license source evidence (AZ-101) — +689/−3
- 🕒 [#101](https://github.com/brighthive/brighthive-deploy/pull/101) feat(mcp): verify the private candidate image (AZ-101) — +191/−18
- 🕒 [#100](https://github.com/brighthive/brighthive-deploy/pull/100) feat(mcp): add isolated workspace-B identity (AZ-101) — +475/−24
- 🕒 [#99](https://github.com/brighthive/brighthive-deploy/pull/99) feat(runtime): scope private proof image promotion (AZ-101) — +664/−34
- 🕒 [#98](https://github.com/brighthive/brighthive-deploy/pull/98) fix(runtime): align proof settings with Azure APIs (AZ-101) — +11/−5
- 🕒 [#97](https://github.com/brighthive/brighthive-deploy/pull/97) feat(sandbox): restore the isolated proof lifecycle (AZ-101) — +540/−84
- 🕒 [#94](https://github.com/brighthive/brighthive-deploy/pull/94) feat(azure): verify the private MCP proof resources (AZ-101) — +797/−72
- 🕒 [#93](https://github.com/brighthive/brighthive-deploy/pull/93) feat(mcp): prepare the Azure runtime handoff (AZ-101) — +800/−99
- 🕒 [#92](https://github.com/brighthive/brighthive-deploy/pull/92) feat(azure): provision the isolated MCP warehouse (AZ-101) — +843/−54
- 🕒 [#91](https://github.com/brighthive/brighthive-deploy/pull/91) feat(mcp): M1 MCP answers from Synapse, governed in IaC (AZ-101) — +796/−97
- 🕒 [#90](https://github.com/brighthive/brighthive-deploy/pull/90) feat(mcp): tell MCP clients where to sign in (AZ-098) — +121/−16
- 🕒 [#88](https://github.com/brighthive/brighthive-deploy/pull/88) fix(platform): keep the monitor scope private on every apply (AZ-099) — +80/−87
- 🕒 [#89](https://github.com/brighthive/brighthive-deploy/pull/89) feat(mcp): serve BrightAgent MCP behind Entra sign-in (AZ-098) — +402/−39
- 🕒 [#87](https://github.com/brighthive/brighthive-deploy/pull/87) docs(specs): check Azure connections with stand-ins (AZ-088) — +245/−4
- 🕒 [#86](https://github.com/brighthive/brighthive-deploy/pull/86) docs(adr): define self-hosted BrightAgent over MCP (AZ-087) — +381/−10
- 🕒 [#85](https://github.com/brighthive/brighthive-deploy/pull/85) feat(helm): reattach retained data disks through code (AZ-086) — +181/−11
- 🕒 [#84](https://github.com/brighthive/brighthive-deploy/pull/84) docs(architecture): link milestone tickets and the AWS map (AZ-070) — +1123/−27
- 🕒 [#83](https://github.com/brighthive/brighthive-deploy/pull/83) docs(architecture): show the work merged this week (AZ-070) — +8/−7
- 🕒 [#82](https://github.com/brighthive/brighthive-deploy/pull/82) fix(helm): run the auth proxy as a sidecar with one port (AZ-085) — +131/−49
- 🕒 [#81](https://github.com/brighthive/brighthive-deploy/pull/81) fix(helm): keep namespaces and volumes on uninstall (AZ-029) — +144/−25
- [#80](https://github.com/brighthive/brighthive-deploy/pull/80) feat(platform): ship container logs and workload alerts (AZ-021) — +356/−12
- [#79](https://github.com/brighthive/brighthive-deploy/pull/79) fix(helm): route MCP through the Entra proxy, close the bypass (AZ-027) — +366/−31
- [#77](https://github.com/brighthive/brighthive-deploy/pull/77) feat(naming): build every resource name in one module (AZ-078) — +684/−191
- [#78](https://github.com/brighthive/brighthive-deploy/pull/78) docs(backlog): add review follow-ups AZ-082 to AZ-084 (AZ-083) — +108/−4
- [#76](https://github.com/brighthive/brighthive-deploy/pull/76) docs(naming): name resources, settings and files plainly (AZ-078) — +412/−11
- [#70](https://github.com/brighthive/brighthive-deploy/pull/70) feat(platform-core): migrate working deployment packaging (AZ-065) — +839/−59
- [#75](https://github.com/brighthive/brighthive-deploy/pull/75) feat(platform): add health and capacity alerts, log cap (AZ-075) — +443/−65
- [#74](https://github.com/brighthive/brighthive-deploy/pull/74) fix(platform): deny storage access by default (AZ-074) — +28/−15
- [#73](https://github.com/brighthive/brighthive-deploy/pull/73) feat(tools): check capacity, limits and probes (AZ-073) — +481/−17
- [#72](https://github.com/brighthive/brighthive-deploy/pull/72) feat(tools): check Azure services for alerts and limits (AZ-073) — +1349/−1
- [#71](https://github.com/brighthive/brighthive-deploy/pull/71) chore(ci): add IaC quality gates (AZ-072) — +387/−11
- [#69](https://github.com/brighthive/brighthive-deploy/pull/69) fix(operations): check the spoke route with the network layer (AZ-071) — +50/−29
- [#68](https://github.com/brighthive/brighthive-deploy/pull/68) feat(operations): verify each layer from the Azure SDK (AZ-071) — +1027/−56
- [#67](https://github.com/brighthive/brighthive-deploy/pull/67) ci: keep architecture status and migration view current (AZ-070) — +582/−5
- [#66](https://github.com/brighthive/brighthive-deploy/pull/66) docs(azure): refresh the AWS to Azure migration view (AZ-003) — +25/−18
- [#65](https://github.com/brighthive/brighthive-deploy/pull/65) fix(platform): spot node pools take no surge setting (AZ-044) — +13/−3
- [#64](https://github.com/brighthive/brighthive-deploy/pull/64) feat(foundation): platform admins group for AKS, Postgres, state (AZ-007) — +100/−23
- [#63](https://github.com/brighthive/brighthive-deploy/pull/63) docs(backlog): close proven tasks, honest statuses (AZ-069) — +72/−72
- [#62](https://github.com/brighthive/brighthive-deploy/pull/62) docs(backlog): plan by milestone with a WIP limit (AZ-069) — +96/−6
- [#61](https://github.com/brighthive/brighthive-deploy/pull/61) fix(platform): audit fixes before the first apply (AZ-068) — +208/−130
- [#59](https://github.com/brighthive/brighthive-deploy/pull/59) feat(operations): quota check and fenced AKS stop/start (AZ-063) — +461/−1
- [#58](https://github.com/brighthive/brighthive-deploy/pull/58) feat(operations): month-to-date cost against the budget (AZ-063) — +217/−0
- [#57](https://github.com/brighthive/brighthive-deploy/pull/57) feat(operations): Azure SDK tool to watch and operate (AZ-063) — +1805/−4
- [#56](https://github.com/brighthive/brighthive-deploy/pull/56) fix(helm): requests and limits on every container (AZ-028) — +289/−42
- [#60](https://github.com/brighthive/brighthive-deploy/pull/60) feat(platform): platform-core identity, vault and containers (AZ-064) — +412/−17
- [#55](https://github.com/brighthive/brighthive-deploy/pull/55) fix(network): open admin and client paths, stop route bypass (AZ-041) — +176/−61
- [#54](https://github.com/brighthive/brighthive-deploy/pull/54) feat(sandbox): up and down by saved plan with destroy guard (AZ-062) — +298/−2
- [#53](https://github.com/brighthive/brighthive-deploy/pull/53) feat(sandbox): hub stand-in and up/down by saved plan (AZ-062) — +647/−21
- [#52](https://github.com/brighthive/brighthive-deploy/pull/52) feat(platform): sizing as input, lowest-cost sandbox shape (AZ-044) — +434/−77
- [#51](https://github.com/brighthive/brighthive-deploy/pull/51) feat(foundation): state account, budget and providers as code (AZ-005) — +703/−14
- [#50](https://github.com/brighthive/brighthive-deploy/pull/50) fix(platform): make the first Terraform apply succeed (AZ-039) — +30/−14
- [#49](https://github.com/brighthive/brighthive-deploy/pull/49) docs(adr): accept ADR-0001 and ADR-0002 (AZ-060) — +6/−6
- [#48](https://github.com/brighthive/brighthive-deploy/pull/48) docs: fold audit reports into a findings index (AZ-061) — +246/−299
- [#47](https://github.com/brighthive/brighthive-deploy/pull/47) docs(adr): record Azure first, multi-everything by design (AZ-060) — +63/−4
- [#46](https://github.com/brighthive/brighthive-deploy/pull/46) docs(readme): update the status and workflow after the first release (AZ-059) — +9/−6
- [#45](https://github.com/brighthive/brighthive-deploy/pull/45) docs(spec): plan the BrightAgent MCP server on CEMAF (AZ-059) — +287/−3
- [#44](https://github.com/brighthive/brighthive-deploy/pull/44) docs(adr): record the harness on CEMAF, self-hosted runtime decision (AZ-004) — +47/−9
- [#43](https://github.com/brighthive/brighthive-deploy/pull/43) docs(decisions): add the ingestion and enrichment runtime decision (AZ-058) — +91/−4
- [#42](https://github.com/brighthive/brighthive-deploy/pull/42) docs(decisions): record the headless harness direction and its MCP gaps (AZ-004) — +23/−2
- [#41](https://github.com/brighthive/brighthive-deploy/pull/41) docs(plan): update the cut list after the docs rewrite (AZ-038) — +1/−1
- [#39](https://github.com/brighthive/brighthive-deploy/pull/39) chore(backlog): close the schedule and docs tasks (AZ-055) — +8/−8
- [#38](https://github.com/brighthive/brighthive-deploy/pull/38) docs: rewrite the guide, customer asks and schedule in plain words (AZ-057) — +147/−332
- [#37](https://github.com/brighthive/brighthive-deploy/pull/37) docs: make the front-door docs say what is proven (AZ-038) — +279/−314
- [#36](https://github.com/brighthive/brighthive-deploy/pull/36) docs(plan): map the schedule at 15 points a week (AZ-055) — +423/−6
- [#35](https://github.com/brighthive/brighthive-deploy/pull/35) docs(iac): design the Azure IaC structure (AZ-049) — +620/−12
- [#34](https://github.com/brighthive/brighthive-deploy/pull/34) docs(azure): add the AWS to Azure migration view and design findings (AZ-003) — +651/−3
- [#30](https://github.com/brighthive/brighthive-deploy/pull/30) docs(agents): add Kubernetes and Azure agents, rules and the finish-task ceremony (AZ-048) — +632/−10
- [#29](https://github.com/brighthive/brighthive-deploy/pull/29) chore(repo): add working rules, agents, skills and task tooling with its CI checks (AZ-000) — +5278/−3
- [#32](https://github.com/brighthive/brighthive-deploy/pull/32) docs(audits): add red-team audits of Terraform, Helm, scripts and CI (AZ-000) — +144/−1
- [#33](https://github.com/brighthive/brighthive-deploy/pull/33) docs(backlog): add the Azure plan as 48 local tasks with an index (AZ-000) — +1714/−1
- [#31](https://github.com/brighthive/brighthive-deploy/pull/31) fix(ci): make validation pass on main and dev (AZ-000) — +9/−1


## brightbot (112 PRs, 96 code)

**Kuri** (71)
- 🕒 [#1237](https://github.com/brighthive/brightbot/pull/1237) feat(llm): add Azure AI Foundry as a model provider for Azure installs (AZ-114) — +810/−30
- 🕒 [#1236](https://github.com/brighthive/brightbot/pull/1236) build(mcp): add a container image for the standalone MCP server (AZ-113) — +181/−0
- 🕒 [#1215](https://github.com/brighthive/brightbot/pull/1215) build(mcp): make Agent Server an optional dependency (AZ-101) — +881/−528
- 🕒 [#1217](https://github.com/brighthive/brightbot/pull/1217) refactor(mcp): isolate agent tool registries (AZ-101) — +769/−478
- 🕒 [#1216](https://github.com/brighthive/brightbot/pull/1216) refactor(mcp): separate transport startup from model execution (AZ-101) — +502/−218
- 🕒 [#1218](https://github.com/brighthive/brightbot/pull/1218) feat(mcp): serve standalone MCP with process health (AZ-101) — +203/−5
- 🕒 [#1200](https://github.com/brighthive/brightbot/pull/1200) fix(mcp): restore Snowflake reads and catalog fallback — +163/−27
- 🕒 [#1198](https://github.com/brighthive/brightbot/pull/1198) feat(models): move Claude models to Opus 5.5, Sonnet 5.5 and Haiku 5.5 (BH-1656) — +169/−51
- 🕒 [#1196](https://github.com/brighthive/brightbot/pull/1196) fix(warehouse): never treat a typeless warehouse as Redshift (BH-1380) — +187/−68
- 🕒 [#1195](https://github.com/brighthive/brightbot/pull/1195) fix(governance): attach lineage to its own warehouse's assets (BH-1380) — +334/−39
- 🕒 [#1194](https://github.com/brighthive/brightbot/pull/1194) fix(governance): report stalled warehouse polls as Down (BH-1380) — +509/−135
- 🕒 [#1193](https://github.com/brighthive/brightbot/pull/1193) fix(governance): fail closed on bad pins, poll concurrently (BH-1380) — +378/−82
- 🕒 [#1192](https://github.com/brighthive/brightbot/pull/1192) feat(governance): fetch lineage from every warehouse (BH-1380) — +1549/−533
- 🕒 [#1191](https://github.com/brighthive/brightbot/pull/1191) feat(governance): watch every SQL Server warehouse (BH-1380) — +1163/−247
- 🕒 [#1190](https://github.com/brighthive/brightbot/pull/1190) feat(governance): watch every Snowflake warehouse (BH-1380) — +749/−130
- 🕒 [#1189](https://github.com/brighthive/brightbot/pull/1189) fix(warehouse): use the default warehouse, never the first (BH-1380) — +407/−85
- [#1186](https://github.com/brighthive/brightbot/pull/1186) fix(monitoring): publish one actionable proposal per repair PR (BH-1255) — +87/−148
- [#1185](https://github.com/brighthive/brightbot/pull/1185) fix(monitoring): clear only positively recovered incidents (BH-1255) — +178/−2
- [#1184](https://github.com/brighthive/brightbot/pull/1184) fix(monitoring): expose repair status over MCP (BH-1255) — +393/−5
- [#1183](https://github.com/brighthive/brightbot/pull/1183) fix(monitoring): preserve the verified repository (BH-1255) — +169/−23
- [#1182](https://github.com/brighthive/brightbot/pull/1182) fix(monitoring): reconcile repairs and retry notifications (BH-1255) — +424/−6
- [#1181](https://github.com/brighthive/brightbot/pull/1181) fix(monitoring): authorize repairs and publish member outcomes (BH-1255) — +292/−0
- [#1180](https://github.com/brighthive/brightbot/pull/1180) fix(monitoring): persist repair claims and execution evidence (BH-1255) — +349/−0
- [#1179](https://github.com/brighthive/brightbot/pull/1179) fix(monitoring): scope project polls and preserve error evidence (BH-1255) — +418/−21
- [#1178](https://github.com/brighthive/brightbot/pull/1178) fix(monitoring): dispatch durable monitoring jobs (BH-1255) — +402/−32
- [#1188](https://github.com/brighthive/brightbot/pull/1188) fix(ci): publish immutable releases and verify active deployments — +332/−115
- [#1177](https://github.com/brighthive/brightbot/pull/1177) test(remediation): un-stale the self-merge exclusion tripwire (BH-1047) — +14/−0
- [#1160](https://github.com/brighthive/brightbot/pull/1160) fix(mcp): preserve partial project health on watchdog failure (BH-1626) — +105/−5
- [#1165](https://github.com/brighthive/brightbot/pull/1165) feat(mcp): expose project health read tools (BH-1626) — +692/−0
- [#1164](https://github.com/brighthive/brightbot/pull/1164) feat(fleet): assemble a project's health headline and parts (BH-1626) — +592/−0
- [#1163](https://github.com/brighthive/brightbot/pull/1163) feat(fleet): read a project's health from the platform (BH-1626) — +442/−0
- [#1162](https://github.com/brighthive/brightbot/pull/1162) feat(fleet): project watchdog state and health headline (BH-1626) — +445/−0
- [#1161](https://github.com/brighthive/brightbot/pull/1161) feat(fleet): project rules and problems, webapp rules (BH-1626) — +560/−0
- [#1159](https://github.com/brighthive/brightbot/pull/1159) chore(mcp): bring staging's quality rule status tool to develop (BH-1631) — +334/−5
- [#1158](https://github.com/brighthive/brightbot/pull/1158) chore(mcp): bring staging's mutation retry store to develop (BH-1631) — +577/−0
- [#1157](https://github.com/brighthive/brightbot/pull/1157) fix(quality): find the workspace warehouse and report runs that can't start (BH-684) — +643/−123
- [#1156](https://github.com/brighthive/brightbot/pull/1156) fix(projects): only workspace members manage a project's watchdog (BH-1634) — +271/−6
- [#1154](https://github.com/brighthive/brightbot/pull/1154) chore(quality): remove duplicate quality rule status tool (BH-1631) — +3/−466
- [#1153](https://github.com/brighthive/brightbot/pull/1153) fix(auth): workspace members can see their project's agent runs (BH-1636) — +206/−0
- [#1152](https://github.com/brighthive/brightbot/pull/1152) fix(fleet): read full signal month and filter signals by project (BH-1626) — +147/−8
- [#1151](https://github.com/brighthive/brightbot/pull/1151) feat(fleet): scan every active project and heal missing watchdogs (BH-1626) — +567/−21
- [#1150](https://github.com/brighthive/brightbot/pull/1150) feat(mcp): add get_project_fleet per-project fleet read (BH-1626) — +672/−3
- [#1149](https://github.com/brighthive/brightbot/pull/1149) feat(fleet): scan each active project's watchdog, rules and runs (BH-1626) — +762/−0
- [#1147](https://github.com/brighthive/brightbot/pull/1147) feat(signals): send project ids and asset names with signals (BH-1634) — +430/−23
- [#1146](https://github.com/brighthive/brightbot/pull/1146) feat(mcp): run a project's pipeline watchdog on demand (BH-1634) — +372/−1
- [#1140](https://github.com/brighthive/brightbot/pull/1140) feat(projects): create the project watchdog on activation (BH-1634) — +377/−3
- [#1139](https://github.com/brighthive/brightbot/pull/1139) feat(scheduler): one pipeline watchdog per active project (BH-1634) — +693/−1
- [#1142](https://github.com/brighthive/brightbot/pull/1142) fix(projects): start spec-conformance review without a URL (BH-1636) — +69/−105
- [#1144](https://github.com/brighthive/brightbot/pull/1144) feat(quality): let BrightAgent turn a quality rule on (BH-1631) — +792/−15
- [#1138](https://github.com/brighthive/brightbot/pull/1138) fix(quality): run configured rules on the asset's warehouse (BH-684) — +26/−0
- [#1145](https://github.com/brighthive/brightbot/pull/1145) fix(mcp): surface saved pipeline issues and paused-run state (BH-1585) — +127/−17
- [#1141](https://github.com/brighthive/brightbot/pull/1141) fix(projects): start activation review without a public URL (BH-1636) — +804/−139
- [#1137](https://github.com/brighthive/brightbot/pull/1137) fix(quality): run tag, all-asset and group rules (BH-1631) — +185/−101
- [#1143](https://github.com/brighthive/brightbot/pull/1143) fix(warehouse): never null isDefault; fall back to the one configured warehouse (BH-1601) — +225/−21
- [#1129](https://github.com/brighthive/brightbot/pull/1129) fix(mcp): reauthorize schedule replay and isolate actors — +167/−53
- [#1131](https://github.com/brighthive/brightbot/pull/1131) fix(fleet): review missing quality targets before retry — +138/−5
- [#1132](https://github.com/brighthive/brightbot/pull/1132) fix(mcp): send workspaceId when unlinking project items (BH-1584) — +18/−4
- [#1134](https://github.com/brighthive/brightbot/pull/1134) fix(mcp): project tools say not found outside the workspace (BH-1587) — +369/−24
- [#1136](https://github.com/brighthive/brightbot/pull/1136) fix(flags): honor workspace opt-ins with false defaults — +81/−67
- [#1135](https://github.com/brighthive/brightbot/pull/1135) fix(mcp): project tools say not found outside the workspace (BH-1587) — +369/−24
- [#1133](https://github.com/brighthive/brightbot/pull/1133) fix(mcp): send workspaceId when unlinking project items (BH-1584) — +18/−4
- [#1130](https://github.com/brighthive/brightbot/pull/1130) fix(mcp): report quality persistence failures and control notifications — +124/−5
- [#1127](https://github.com/brighthive/brightbot/pull/1127) fix(scheduler): respect explicit delivery when subscribing — +76/−2
- [#1128](https://github.com/brighthive/brightbot/pull/1128) feat(mcp): persist mutation reservations in DynamoDB — +270/−5
- [#1125](https://github.com/brighthive/brightbot/pull/1125) feat(mcp): expose saved quality rules and execution evidence — +271/−1
- [#1126](https://github.com/brighthive/brightbot/pull/1126) feat(mcp): control quality rule activation with readback — +328/−1
- [#1124](https://github.com/brighthive/brightbot/pull/1124) feat(mcp): save reviewed quality rules with retry protection — +381/−4
- [#1123](https://github.com/brighthive/brightbot/pull/1123) feat(mcp): add shared mutation retry store — +303/−0
- [#1122](https://github.com/brighthive/brightbot/pull/1122) fix(mcp): preserve executable quality expectations — +85/−13
- [#1121](https://github.com/brighthive/brightbot/pull/1121) fix(monitoring): report skipped scheduled work truthfully — +116/−7
- [#1120](https://github.com/brighthive/brightbot/pull/1120) fix(mcp): flag sanitized tool failures as errors (BH-1581) — +44/−1

**Marwan** (1)
- 🕒 [#1214](https://github.com/brighthive/brightbot/pull/1214) feat(dbt): prefer stored dbt Cloud project/environment ids over repo match — +365/−5

**Harbour** (24)
- 🕒 [#1235](https://github.com/brighthive/brightbot/pull/1235) feat(pipeline-author): leave identity_resolution SQL to the platform (Azure) — +4/−1
- 🕒 [#1233](https://github.com/brighthive/brightbot/pull/1233) fix(pipeline): repair any warehouse SQL error except timeouts and access failures — +23/−6
- 🕒 [#1232](https://github.com/brighthive/brightbot/pull/1232) feat(mcp): repair_project_pipeline_sql rewrites failed SQL steps — +456/−0
- 🕒 [#1231](https://github.com/brighthive/brightbot/pull/1231) fix(pipeline): author pipelines with Sonnet instead of Haiku — +2/−1
- 🕒 [#1230](https://github.com/brighthive/brightbot/pull/1230) fix(pipeline): give the author column types and ban STRING_AGG(DISTINCT) on T-SQL — +11/−3
- 🕒 [#1229](https://github.com/brighthive/brightbot/pull/1229) fix(pipeline): raise pipeline author output limit to 16k tokens — +3/−2
- 🕒 [#1228](https://github.com/brighthive/brightbot/pull/1228) fix(pipeline): author SQL against listed columns in the warehouse dialect — +102/−7
- 🕒 [#1227](https://github.com/brighthive/brightbot/pull/1227) fix(pipeline): refuse to apply spec-parser fallback pipelines — +133/−13
- 🕒 [#1224](https://github.com/brighthive/brightbot/pull/1224) feat(azure-k8s): project watchdog store on Azure Table Storage — +224/−3
- 🕒 [#1213](https://github.com/brighthive/brightbot/pull/1213) feat(mcp): permission-matrix-driven MCP access on all profiles; lock risky tools on azure-k8s — +1228/−163
- 🕒 [#1223](https://github.com/brighthive/brightbot/pull/1223) feat(mcp): schedule_asset_monitor and run_scheduled_agent_now — +1234/−58
- 🕒 [#1219](https://github.com/brighthive/brightbot/pull/1219) fix(scheduler): pass service token to scheduled quality checks; add openai LLM provider — +324/−28
- 🕒 [#1212](https://github.com/brighthive/brightbot/pull/1212) feat(azure-k8s): scheduled agents Table Storage + Azure cron dispatcher — +1578/−259
- 🕒 [#1197](https://github.com/brighthive/brightbot/pull/1197) feat(azure): read workspace secrets from Key Vault — +7094/−2205
- [#1211](https://github.com/brighthive/brightbot/pull/1211) docs(azure-k8s): BrightSignals publisher env for Nestlé LangGraph — +72/−3
- [#1210](https://github.com/brighthive/brightbot/pull/1210) feat(governance): Path B AKS diagnostic sandbox (includes Path A analyst executor) — +1572/−181
- [#1209](https://github.com/brighthive/brightbot/pull/1209) feat(azure-k8s): route analyst Python to AKS executor — +1718/−181
- [#1208](https://github.com/brighthive/brightbot/pull/1208) P2.0 MCP E2E wrap-up (bundle with core + e2e) — +599/−7
- [#1207](https://github.com/brighthive/brightbot/pull/1207) fix(azure): SSIS Blob fetch + MCP project context notes — +266/−22
- [#1206](https://github.com/brighthive/brightbot/pull/1206) feat(azure): profile-only routing and blob follow-ups — +140/−154
- [#1205](https://github.com/brighthive/brightbot/pull/1205) fix(mcp): Entra workspace ADMIN gets mcp:write scope projection — +151/−5
- [#1202](https://github.com/brighthive/brightbot/pull/1202) feat(azure): Entra OGM service token (stacked on aws-only-gates) — +744/−153
- [#1201](https://github.com/brighthive/brightbot/pull/1201) feat(azure): store agent files in Blob — +424/−10
- [#1199](https://github.com/brighthive/brightbot/pull/1199) feat(azure): gate AWS-only BrightAgent features — +99/−0


## brighthive-platform-core (73 PRs, 68 code)

**Kuri** (42)
- 🕒 [#1387](https://github.com/brighthive/brighthive-platform-core/pull/1387) fix(ci): restore staging release and CI validation — +202/−10
- 🕒 [#1363](https://github.com/brighthive/brighthive-platform-core/pull/1363) feat(warehouse): backfill databases, link after catalog sync (BH-1373) — +187/−3
- 🕒 [#1367](https://github.com/brighthive/brighthive-platform-core/pull/1367) feat(platform): multi-cloud single-tenant runtime (NO-TICKET) — +34093/−1827
- 🕒 [#1362](https://github.com/brighthive/brighthive-platform-core/pull/1362) feat(warehouse): databases as nodes under their warehouse (BH-1371) — +6586/−675
- [#1358](https://github.com/brighthive/brighthive-platform-core/pull/1358) feat(notifications): promote remediation decisions to staging (BH-1255) — +316/−7
- [#1361](https://github.com/brighthive/brighthive-platform-core/pull/1361) fix: preserve canonical catalog table and warehouse identities — +97/−8
- [#1360](https://github.com/brighthive/brighthive-platform-core/pull/1360) fix: redact production role secret update log — +1/−1
- [#1357](https://github.com/brighthive/brighthive-platform-core/pull/1357) fix(auth): restore staging MCP token scopes (BH-1638) — +23/−1
- [#1355](https://github.com/brighthive/brighthive-platform-core/pull/1355) fix(auth): let per-env config decide the pre-token trigger (BH-1638) — +23/−1
- [#1354](https://github.com/brighthive/brighthive-platform-core/pull/1354) fix(authz): scope quality rule writes to workspace members (BH-1637) — +227/−10
- [#1352](https://github.com/brighthive/brighthive-platform-core/pull/1352) ci(deploy): free runner disk before the staging build (BH-1613) — +7/−0
- [#1350](https://github.com/brighthive/brighthive-platform-core/pull/1350) fix(projects): log every activation-check outcome (BH-1636) — +187/−13
- [#1348](https://github.com/brighthive/brighthive-platform-core/pull/1348) fix(projects): count direct asset links and save compile issues (BH-1585) — +165/−54
- [#1349](https://github.com/brighthive/brighthive-platform-core/pull/1349) feat(projects): sync project watchdog with project lifecycle (BH-1634) — +447/−1
- [#1346](https://github.com/brighthive/brighthive-platform-core/pull/1346) feat(signals): carry project ids on published signals (BH-1634) — +230/−11
- [#1342](https://github.com/brighthive/brighthive-platform-core/pull/1342) feat(signals): accept idempotencyKey on publishNotification (BH-1628) — +496/−20
- [#1344](https://github.com/brighthive/brighthive-platform-core/pull/1344) fix(quality): match group rules and share rule matching (BH-1631) — +351/−27
- [#1345](https://github.com/brighthive/brighthive-platform-core/pull/1345) fix(warehouse): never null isDefault; fall back to the one configured warehouse (BH-1601) — +412/−23
- [#1343](https://github.com/brighthive/brighthive-platform-core/pull/1343) fix(authz): asset edit rights need active workspace membership (BH-1627) — +75/−45
- [#1341](https://github.com/brighthive/brighthive-platform-core/pull/1341) fix(authz): scope asset owner and managers to the workspace (BH-1627) — +906/−30
- [#1318](https://github.com/brighthive/brighthive-platform-core/pull/1318) feat(routines): turn-off decided by authorize() on ROUTINE (BH-1573) — +346/−75
- [#1317](https://github.com/brighthive/brighthive-platform-core/pull/1317) feat(authz): ROUTINE resource kind and workspace binding (BH-1572) — +583/−45
- [#1316](https://github.com/brighthive/brighthive-platform-core/pull/1316) fix(routines): clear errors when turning off a routine fails (BH-1566) — +151/−2
- [#1323](https://github.com/brighthive/brighthive-platform-core/pull/1323) fix(projects): unblock asset, schema and destination writes (BH-1584) — +229/−20
- [#1338](https://github.com/brighthive/brighthive-platform-core/pull/1338) test(authz): live suite for scoped project writes (BH-1589) — +500/−0
- [#1337](https://github.com/brighthive/brighthive-platform-core/pull/1337) fix(authz): scope project updates, creates and attaches (BH-1589) — +158/−66
- [#1336](https://github.com/brighthive/brighthive-platform-core/pull/1336) fix(authz): addSchemaToProject takes its workspace, needs update (BH-1589) — +161/−19
- [#1332](https://github.com/brighthive/brighthive-platform-core/pull/1332) fix(authz): scope project deletes, runs and workflow view (BH-1589) — +121/−16
- [#1331](https://github.com/brighthive/brighthive-platform-core/pull/1331) fix(authz): scope project schemas, files and gates to the workspace (BH-1589) — +595/−23
- [#1327](https://github.com/brighthive/brighthive-platform-core/pull/1327) fix(auth): project checks require the project in the workspace (BH-1588) — +203/−4
- [#1325](https://github.com/brighthive/brighthive-platform-core/pull/1325) fix(workflow): scope project pipelines to their workspace (BH-1586) — +407/−0
- [#1340](https://github.com/brighthive/brighthive-platform-core/pull/1340) fix(authz): scope project updates, creates and attaches (BH-1589) — +658/−66
- [#1339](https://github.com/brighthive/brighthive-platform-core/pull/1339) fix(authz): addSchemaToProject takes its workspace, needs update (BH-1589) — +161/−19
- [#1335](https://github.com/brighthive/brighthive-platform-core/pull/1335) feat(notifications): record remediation decisions — +186/−1
- [#1334](https://github.com/brighthive/brighthive-platform-core/pull/1334) fix(authz): scope project deletes, runs and workflow view (BH-1589) — +121/−16
- [#1333](https://github.com/brighthive/brighthive-platform-core/pull/1333) fix(authz): scope project schemas, files and gates to the workspace (BH-1589) — +595/−23
- [#1330](https://github.com/brighthive/brighthive-platform-core/pull/1330) fix(project): deleteProject no longer reveals which ids exist (BH-1588) — +22/−4
- [#1329](https://github.com/brighthive/brighthive-platform-core/pull/1329) fix(workflow): a missing run in your own project is not found (BH-1586) — +26/−1
- [#1328](https://github.com/brighthive/brighthive-platform-core/pull/1328) fix(auth): project checks require the project in the workspace (BH-1588) — +181/−0
- [#1326](https://github.com/brighthive/brighthive-platform-core/pull/1326) fix(workflow): scope project pipelines to their workspace (BH-1586) — +382/−0
- [#1324](https://github.com/brighthive/brighthive-platform-core/pull/1324) fix(projects): unblock asset, schema and destination writes (BH-1584) — +229/−20
- [#1322](https://github.com/brighthive/brighthive-platform-core/pull/1322) feat(infra): add retained staging MCP mutation storage — +173/−0

**Marwan** (5)
- 🕒 [#1384](https://github.com/brighthive/brighthive-platform-core/pull/1384) chore(azure-k8s): configure Entra given_name/family_name claims via script and document it — +110/−3
- 🕒 [#1385](https://github.com/brighthive/brighthive-platform-core/pull/1385) fix(azure-k8s): size the OpenMetadata MySQL volume at 20Gi and grow existing clusters in place — +58/−1
- 🕒 [#1383](https://github.com/brighthive/brighthive-platform-core/pull/1383) fix(users): never expose empty/null user names; derive them when the IdP sends none — +416/−37
- 🕒 [#1381](https://github.com/brighthive/brighthive-platform-core/pull/1381) fix(azure-k8s): read and store GitHub auth tokens via the platform secret store — +346/−102
- 🕒 [#1380](https://github.com/brighthive/brighthive-platform-core/pull/1380) feat(dbt): optional per-service dbt Cloud project and environment ids — +1294/−0

**Harbour** (21)
- 🕒 [#1396](https://github.com/brighthive/brighthive-platform-core/pull/1396) fix(pipeline): drop leftover Synapse smoke tables before a re-run (Azure) — +8/−1
- 🕒 [#1395](https://github.com/brighthive/brighthive-platform-core/pull/1395) fix(pipeline): give transform steps an output table (Azure) — +118/−4
- 🕒 [#1394](https://github.com/brighthive/brighthive-platform-core/pull/1394) fix(pipeline): connect steps that only inherit tables to the right database (Azure) — +29/−1
- 🕒 [#1393](https://github.com/brighthive/brighthive-platform-core/pull/1393) feat(pipeline): first-pass identity resolution SQL (Azure) — +673/−7
- 🕒 [#1391](https://github.com/brighthive/brighthive-platform-core/pull/1391) fix(pipeline): give the pipeline author real columns and the SQL dialect — +142/−1
- 🕒 [#1390](https://github.com/brighthive/brighthive-platform-core/pull/1390) fix(pipeline): stop spec apply from building broken pipelines — +418/−43
- 🕒 [#1382](https://github.com/brighthive/brighthive-platform-core/pull/1382) feat(core): service-key query for workspace field PII classifications — +240/−0
- 🕒 [#1379](https://github.com/brighthive/brighthive-platform-core/pull/1379) Proxy browser SSE via platform-core to notifications-stream — +234/−5
- [#1378](https://github.com/brighthive/brighthive-platform-core/pull/1378) fix(ci): PAT for slack-server checkout on bh-demo deploy — +2/−0
- [#1377](https://github.com/brighthive/brighthive-platform-core/pull/1377) feat(azure-k8s): Tier 1 BrightSignals inbox + notifications-stream deploy — +914/−154
- [#1376](https://github.com/brighthive/brighthive-platform-core/pull/1376) feat(governance): Path B executor Jobs + governance-sandbox image (includes Path A) — +2117/−0
- [#1375](https://github.com/brighthive/brighthive-platform-core/pull/1375) feat(azure-k8s): Nestlé analyst AKS executor (Job + Blob sync) — +2224/−0
- [#1373](https://github.com/brighthive/brighthive-platform-core/pull/1373) P2.0 MCP E2E wrap-up: lightweight local admin seed — +507/−242
- [#1372](https://github.com/brighthive/brighthive-platform-core/pull/1372) fix(entra): skip Cognito admin sync on getCurrentUser for azure-k8s — +486/−242
- [#1371](https://github.com/brighthive/brighthive-platform-core/pull/1371) feat(azure): lightweight demo graph seed (warehouse + assets) — +430/−227
- [#1370](https://github.com/brighthive/brighthive-platform-core/pull/1370) feat(azure): logo PUT + blob presign gaps (single-tenant) — +362/−224
- [#1368](https://github.com/brighthive/brighthive-platform-core/pull/1368) feat(azure): mount /ogm on Core pod for Entra SystemAdmin tokens — +136/−0
- [#1366](https://github.com/brighthive/brighthive-platform-core/pull/1366) fix(notifications): validate and replace Teams webhook URLs — +178/−8
- [#1364](https://github.com/brighthive/brighthive-platform-core/pull/1364) fix: drop the catalog rebuild from asset writes — +25/−58
- [#1365](https://github.com/brighthive/brighthive-platform-core/pull/1365) fix: throw when a data asset group cannot be loaded — +66/−2
- [#1347](https://github.com/brighthive/brighthive-platform-core/pull/1347) feat(notifications): route Teams through slack-server from the dispatcher Lambda — +22/−1


## agentic-project-mgmt (28 PRs, 28 code)

**Kuri** (28)
- 🕒 [#217](https://github.com/brighthive/agentic-project-mgmt/pull/217) docs(mcp): define standalone Brightbot serving contract (AZ-101) — +130/−0
- [#216](https://github.com/brighthive/agentic-project-mgmt/pull/216) docs(clients): add pipeline clients to the index — +291/−1
- [#215](https://github.com/brighthive/agentic-project-mgmt/pull/215) docs(acg): add spec sections 7-10 and fix Nestlé ticket count (BH-1659) — +43/−2
- [#213](https://github.com/brighthive/agentic-project-mgmt/pull/213) docs(clients): add ACG lead, vendor-data pilot spec and roadmap — +270/−1
- [#214](https://github.com/brighthive/agentic-project-mgmt/pull/214) docs(specs): correct two citations in the cloud-agnostic adapters spec — +3/−3
- [#212](https://github.com/brighthive/agentic-project-mgmt/pull/212) docs(nestle): rewrite scorecard coverage in plain language with links (BH-1639) — +57/−42
- [#198](https://github.com/brighthive/agentic-project-mgmt/pull/198) docs(sprint-17): per-person release notes and slack posts (BH-170) — +763/−1
- [#207](https://github.com/brighthive/agentic-project-mgmt/pull/207) docs(clients): Loop AI governance requirements fit and co-build pitch — +220/−3
- [#208](https://github.com/brighthive/agentic-project-mgmt/pull/208) docs(roadmap): Q4 2026 to Q2 2027 capacity roadmap for Loop and Nestlé — +186/−0
- [#211](https://github.com/brighthive/agentic-project-mgmt/pull/211) docs(nestle): hyperlink every Jira epic and ticket key (BH-1639) — +29/−29
- [#210](https://github.com/brighthive/agentic-project-mgmt/pull/210) docs(nestle): link Jira epics and tickets, add cloud-agnostic adapters spec (BH-1639) — +151/−6
- [#209](https://github.com/brighthive/agentic-project-mgmt/pull/209) docs(year-one): before/after evidence for annual review (BH-170) — +21239/−0
- [#206](https://github.com/brighthive/agentic-project-mgmt/pull/206) docs(specs): data scope include/exclude down to the row (BH-1370) — +409/−0
- [#204](https://github.com/brighthive/agentic-project-mgmt/pull/204) docs(specs): projects at enterprise scale (BH-1626) — +498/−0
- [#196](https://github.com/brighthive/agentic-project-mgmt/pull/196) docs(specs): audit every mutation with one plugin (BH-1579) — +152/−0
- [#194](https://github.com/brighthive/agentic-project-mgmt/pull/194) docs(ops): enable staging project MCP tools (BH-1571) — +4/−3
- [#192](https://github.com/brighthive/agentic-project-mgmt/pull/192) docs(spec): rewrite BH-1343/BH-1504 sync spec against real activation-check + execute_workflow primitives (BH-1343) — +446/−206
- [#190](https://github.com/brighthive/agentic-project-mgmt/pull/190) docs(vision): AI Data Engineer 3-tier vision mapped to reality — +89/−0
- [#189](https://github.com/brighthive/agentic-project-mgmt/pull/189) docs(spec): file schema-contract-gates tickets under BH-172 (BH-1511-1515) — +29/−10
- [#188](https://github.com/brighthive/agentic-project-mgmt/pull/188) docs(spec): project proactive lifecycle theme (BH-1255) — +141/−0
- [#183](https://github.com/brighthive/agentic-project-mgmt/pull/183) docs(sprint-16): weekly release cut — env wiring, warehouse routing (Aug 17-23) — +442/−1
- [#202](https://github.com/brighthive/agentic-project-mgmt/pull/202) docs(mcp): require actionable pilot alerts and record rollout — +98/−5
- [#205](https://github.com/brighthive/agentic-project-mgmt/pull/205) docs(clients): align Loop governance and Nestlé Azure to tickets — +415/−2
- [#203](https://github.com/brighthive/agentic-project-mgmt/pull/203) docs(clients): create Nestle global trial room — +364/−0
- [#201](https://github.com/brighthive/agentic-project-mgmt/pull/201) docs(mcp): record active staging writes and positive validation — +104/−16
- [#200](https://github.com/brighthive/agentic-project-mgmt/pull/200) docs(mcp): track quality rollout and durable execution contract — +102/−15
- [#199](https://github.com/brighthive/agentic-project-mgmt/pull/199) docs(specs): executable MCP pilot journeys — +242/−3
- [#197](https://github.com/brighthive/agentic-project-mgmt/pull/197) docs(specs): MCP stateless transport (BH-1581) — +321/−0


## brighthive-webapp (30 PRs, 25 code)

**Kuri** (21)
- [#1504](https://github.com/brighthive/brighthive-webapp/pull/1504) feat(projects): promote conformance and pipeline evidence (BH-1255) — +200/−1
- [#1503](https://github.com/brighthive/brighthive-webapp/pull/1503) fix(projects): restore a route for the spec conformance view (BH-1530) — +25/−0
- [#1508](https://github.com/brighthive/brighthive-webapp/pull/1508) fix: verify production release from served build provenance — +23/−2
- [#1507](https://github.com/brighthive/brighthive-webapp/pull/1507) fix: limit Amplify release update output to app ID — +2/−1
- [#1506](https://github.com/brighthive/brighthive-webapp/pull/1506) ci: verify the production Amplify release build — +24/−0
- [#1498](https://github.com/brighthive/brighthive-webapp/pull/1498) feat(workflows): project health — fleet, watchdog, rules, signals and actions (BH-1626) — +654/−2
- [#1501](https://github.com/brighthive/brighthive-webapp/pull/1501) feat(workflows): add project health headline and fleet strip (BH-1626) — +415/−0
- [#1500](https://github.com/brighthive/brighthive-webapp/pull/1500) feat(workflows): show BrightAgent runs and runs waiting for input (BH-1626) — +549/−0
- [#1497](https://github.com/brighthive/brighthive-webapp/pull/1497) feat(workflows): show project open problems grouped per asset (BH-1626) — +404/−0
- [#1496](https://github.com/brighthive/brighthive-webapp/pull/1496) feat(workflows): show project quality rules by stage (BH-1626) — +629/−0
- [#1495](https://github.com/brighthive/brighthive-webapp/pull/1495) feat(workflows): show project watchdog with run now and resume (BH-1626) — +652/−0
- [#1494](https://github.com/brighthive/brighthive-webapp/pull/1494) feat(workflows): add project health card frame and data hooks (BH-1626) — +742/−0
- [#1499](https://github.com/brighthive/brighthive-webapp/pull/1499) feat(workflows): judge project watchdog and health headline (BH-1626) — +417/−0
- [#1492](https://github.com/brighthive/brighthive-webapp/pull/1492) feat(workflows): derive project health from rules and signals (BH-1626) — +675/−1
- [#1491](https://github.com/brighthive/brighthive-webapp/pull/1491) fix(workflows): show a project's agent runs to every member (BH-1625) — +44/−20
- [#1421](https://github.com/brighthive/brighthive-webapp/pull/1421) fix(apollo): correct v4 retry classification, make silent-retry toast work (BH-1364, BH-1366) — +391/−61
- [#1419](https://github.com/brighthive/brighthive-webapp/pull/1419) fix(auth): stop logout loop, add workspace-switcher logout, guard bypass-JWT misuse — +70502/−48400
- [#1484](https://github.com/brighthive/brighthive-webapp/pull/1484) feat(schedules): hide schedule controls from non-owners (BH-1567) — +454/−17
- [#1488](https://github.com/brighthive/brighthive-webapp/pull/1488) feat(workflows): one project picker filters every card (BH-1625) — +527/−165
- [#1487](https://github.com/brighthive/brighthive-webapp/pull/1487) fix(projects): send workspaceId on project item removal (BH-1584) — +90/−3
- [#1489](https://github.com/brighthive/brighthive-webapp/pull/1489) fix(projects): send workspaceId when attaching a schema (BH-1589) — +5/−0

**Marwan** (2)
- 🕒 [#1510](https://github.com/brighthive/brighthive-webapp/pull/1510) Feature/azure k8s webapp — +2354/−95
- 🕒 [#1512](https://github.com/brighthive/brighthive-webapp/pull/1512) feat(settings): dbt Cloud project and environment ids on dbt services — +350/−0

**Harbour** (2)
- [#1511](https://github.com/brighthive/brighthive-webapp/pull/1511) fix(webapp): workspace logo upload via presigned PUT — +18/−14
- [#1509](https://github.com/brighthive/brighthive-webapp/pull/1509) fix(notifications): accept a real Teams webhook URL — +136/−4


## brighthive-e2e (17 PRs, 17 code)

**Kuri** (16)
- 🕒 [#81](https://github.com/brighthive/brighthive-e2e/pull/81) test(e2e): warehouse arc — default-warehouse + n-to-n fan-out + agnostic sweep (BH-1362, BH-1371) — +721/−9
- 🕒 [#109](https://github.com/brighthive/brighthive-e2e/pull/109) test(mcp): assert project counts, run state and compile read-back (BH-1585) — +98/−3
- 🕒 [#93](https://github.com/brighthive/brighthive-e2e/pull/93) test(mcp): verify project write workflows on staging (BH-1571) — +394/−0
- [#111](https://github.com/brighthive/brighthive-e2e/pull/111) fix(e2e): align staging MCP reads and protect privacy evidence — +368/−193
- [#110](https://github.com/brighthive/brighthive-e2e/pull/110) feat(mcp): project health and actions over MCP (BH-1626) — +333/−5
- [#108](https://github.com/brighthive/brighthive-e2e/pull/108) fix(e2e): browser tests actually sign in (BH-1625) — +11/−3
- [#107](https://github.com/brighthive/brighthive-e2e/pull/107) test(e2e): GraphQL cross-workspace project operations (BH-1589) — +64/−0
- [#106](https://github.com/brighthive/brighthive-e2e/pull/106) test(e2e): project tools refuse unseen projects, no exceptions (BH-1587) — +3/−33
- [#105](https://github.com/brighthive/brighthive-e2e/pull/105) test(e2e): deleting a missing project is FORBIDDEN (BH-1588) — +7/−0
- [#104](https://github.com/brighthive/brighthive-e2e/pull/104) test(e2e): project files, graph refusals, runs, conversation drafts (BH-1585) — +120/−0
- [#103](https://github.com/brighthive/brighthive-e2e/pull/103) test(e2e): project goals, tags and compile issues over MCP (BH-1585) — +74/−0
- [#102](https://github.com/brighthive/brighthive-e2e/pull/102) test(e2e): cross-workspace and refusal coverage for project tools (BH-1586) — +330/−10
- [#101](https://github.com/brighthive/brighthive-e2e/pull/101) test(mcp): verify positive quality write lifecycle — +357/−5
- [#100](https://github.com/brighthive/brighthive-e2e/pull/100) test(e2e): cover building a project over MCP (BH-1585) — +628/−34
- [#99](https://github.com/brighthive/brighthive-e2e/pull/99) test(e2e): live audit check for project mutations (BH-1583) — +180/−0
- [#98](https://github.com/brighthive/brighthive-e2e/pull/98) fix(mcp): validate staging writes with scoped access tokens (BH-1581) — +147/−30

**Harbour** (1)
- [#112](https://github.com/brighthive/brighthive-e2e/pull/112) P2.0 MCP E2E wrap-up: legacy graph tools removed — +5/−39


## platform-saas-ai-context (12 PRs, 12 code)

**Kuri** (12)
- 🕒 [#57](https://github.com/brighthive/platform-saas-ai-context/pull/57) docs(adr): define v4 module contracts and operating flows (BH-453) — +274/−0
- 🕒 [#56](https://github.com/brighthive/platform-saas-ai-context/pull/56) docs(adr): inventory BrightAgent capabilities and product ownership (BH-453) — +696/−1
- 🕒 [#54](https://github.com/brighthive/platform-saas-ai-context/pull/54) docs(adr): rethink BrightAgent v4 on CEMAF (BH-453) — +580/−0
- 🕒 [#58](https://github.com/brighthive/platform-saas-ai-context/pull/58) docs(audit): retain BrightAgent v4 reuse evidence (BH-453) — +560/−0
- 🕒 [#55](https://github.com/brighthive/platform-saas-ai-context/pull/55) docs(adr): map v4 Company Brain and full product capabilities (BH-453) — +283/−0
- [#47](https://github.com/brighthive/platform-saas-ai-context/pull/47) docs(infra): capture local-against-staging boot learnings (BH-1330) — +31/−0
- [#46](https://github.com/brighthive/platform-saas-ai-context/pull/46) docs(adr): ADR-015 BrightAgent shared-core, four surface planes (BH-1255) — +87/−0
- [#43](https://github.com/brighthive/platform-saas-ai-context/pull/43) docs(infra): release-tag prod deploy + develop/main drift + branch/admin gotchas — +0/−0
- [#49](https://github.com/brighthive/platform-saas-ai-context/pull/49) docs(infra): document Cognito-healthy/missing-UserNode login failure pattern — +150/−8
- [#44](https://github.com/brighthive/platform-saas-ai-context/pull/44) docs(arch): multi-repo feature flow + deploy topology (BH-1320) — +341/−4
- [#53](https://github.com/brighthive/platform-saas-ai-context/pull/53) docs(infra): add Bedrock cost control and model rollout runbook (BH-1657) — +118/−0
- [#52](https://github.com/brighthive/platform-saas-ai-context/pull/52) docs(infra): record deployed staging MCP mutation storage — +22/−0


## brightagent-v3 (8 PRs, 8 code)

**Kuri** (8)
- 🕒 [#146](https://github.com/brighthive/brightagent-v3/pull/146) fix(runtime): per-run-isolated run logger — same-workspace concurrency (BH-1134) — +303/−25
- 🕒 [#147](https://github.com/brighthive/brightagent-v3/pull/147) fix(sql): bound rows dialect-correctly — Synapse TOP, not LIMIT (BH-453) — +104/−15
- 🕒 [#145](https://github.com/brighthive/brightagent-v3/pull/145) test(runtime): e2e concurrent chat DAG — finds same-workspace run-logger race (BH-453) — +150/−8
- 🕒 [#144](https://github.com/brighthive/brightagent-v3/pull/144) test(runtime): multi-tenant concurrency under parallel load (BH-453) — +171/−8
- 🕒 [#143](https://github.com/brighthive/brightagent-v3/pull/143) test(runtime): cross-tenant isolation leak test (BH-453) — +135/−9
- 🕒 [#142](https://github.com/brighthive/brightagent-v3/pull/142) feat(mcp): cache token validation via CEMAF TTLCache (BH-453) — +185/−20
- 🕒 [#141](https://github.com/brighthive/brightagent-v3/pull/141) feat(viz): wire cemaf.validation into Vega-Lite spec check (BH-453) — +250/−36
- 🕒 [#136](https://github.com/brighthive/brightagent-v3/pull/136) docs(plan): CEMAF autonomous context-brain execution plan (BH-453) — +1289/−2


## brightagent (7 PRs, 7 code)

**Kuri** (7)
- 🕒 [#7](https://github.com/brighthive/brightagent/pull/7) feat(release): publish the Projects runtime with notices (AZ-104) — +457/−2
- 🕒 [#4](https://github.com/brighthive/brightagent/pull/4) feat(mcp): prepare PROJECTS governance and staging proof (AZ-104) — +467/−208
- 🕒 [#6](https://github.com/brighthive/brightagent/pull/6) feat(mcp): add project run reads (AZ-104) — +257/−6
- 🕒 [#5](https://github.com/brighthive/brightagent/pull/5) feat(mcp): add workspace project discovery (AZ-104) — +418/−1
- 🕒 [#2](https://github.com/brighthive/brightagent/pull/2) feat(mcp): add discovery, health and workspace read tools (AZ-103) — +346/−31
- 🕒 [#3](https://github.com/brighthive/brightagent/pull/3) fix(synapse): ship an open-source proof image (AZ-101) — +661/−161
- 🕒 [#1](https://github.com/brighthive/brightagent/pull/1) feat(mcp): add read-only Synapse workspace tool (AZ-101) — +851/−6


## brightbot-slack-server (7 PRs, 7 code)

**Kuri** (2)
- 🕒 [#182](https://github.com/brighthive/brightbot-slack-server/pull/182) ci(tests): run the full suite with DynamoDB Local on PRs (BH-1628) — +29/−0
- [#180](https://github.com/brighthive/brightbot-slack-server/pull/180) feat(slack): add remediation proposal actions — +381/−8

**Harbour** (5)
- 🕒 [#187](https://github.com/brighthive/brightbot-slack-server/pull/187) fix(azure-k8s): SSE JWT validation via jwks-rsa (Core parity) — +8625/−75
- 🕒 [#186](https://github.com/brighthive/brightbot-slack-server/pull/186) fix(azure-k8s): SSE Entra JWKS + azurefd CORS for bh-demo — +228/−28
- [#185](https://github.com/brighthive/brightbot-slack-server/pull/185) feat(azure-k8s): Tier 2 notifications-stream (GraphQL poller + SSE) — +1994/−60
- [#184](https://github.com/brighthive/brightbot-slack-server/pull/184) fix(notifications): post Teams webhooks only to Microsoft hosts — +88/−1
- [#179](https://github.com/brighthive/brightbot-slack-server/pull/179) Add Microsoft Teams delivery channel for notifications — +755/−7


## brightagent-selfhost (5 PRs, 5 code)

**Kuri** (5)
- 🕒 [#6](https://github.com/brighthive/brightagent-selfhost/pull/6) feat: add install preflight and trial guide; open on a front page — +1817/−654
- 🕒 [#4](https://github.com/brighthive/brightagent-selfhost/pull/4) feat: add an opt-in registry import path to the install root — +51/−19
- 🕒 [#3](https://github.com/brighthive/brightagent-selfhost/pull/3) fix: set the AKS image cleaner interval in the install root — +13/−8
- 🕒 [#2](https://github.com/brighthive/brightagent-selfhost/pull/2) fix: add offline checks and a wider example guard to the runbook — +21/−11
- 🕒 [#1](https://github.com/brighthive/brightagent-selfhost/pull/1) feat: add the agent install runbook and Terraform tests — +218/−6

