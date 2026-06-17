# Sprint 12 🛠️ Release Notes — Longaeva Pre-Trial Platform Build

**Release Date:** 2026-06-16 · **Sprint Period:** 2026-06-03 → 2026-06-16

| Metric | Value |
|--------|-------|
| Tickets Done | 18 (of 46 active) |
| In Code-Review / Staging-QC | 27 |
| PRs Merged | 268 (235 feature/fix + 33 release-carriers) |
| Lines Changed | 485,074 (excl. release-carriers) |
| Repos Touched | 6 |

Epics in play: BH-526 (Longaeva pre-trial), BH-601 (14 Golden Cases), BH-624 (Semantic-View Lifecycle), BH-503 (Quality Rules), BH-409 (BrightSignals), BH-115 (MCP/Okta).

---

## Completed Tickets

- [BH-641](https://brighthiveio.atlassian.net/browse/BH-641) Write/overwrite semantic view back to Snowflake from BrightBot
- [BH-562](https://brighthiveio.atlassian.net/browse/BH-562) Finish PyGithub removal (P0)
- [BH-564](https://brighthiveio.atlassian.net/browse/BH-564) Pydantic responses + DI for PlatformAPISession
- [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) Author BRIGHTBOT-GITHUB-PROXY-GUIDE.md
- [BH-505](https://brighthiveio.atlassian.net/browse/BH-505) QualityRuleNode + QualityRuleExecutionNode (Neo4j OGM)
- [BH-506](https://brighthiveio.atlassian.net/browse/BH-506) REST CRUD endpoints for quality rules
- [BH-507](https://brighthiveio.atlassian.net/browse/BH-507) Quality agent reads rules from library, not LLM regen
- [BH-508](https://brighthiveio.atlassian.net/browse/BH-508) Per-rule execution fanout + pass-rate aggregation
- [BH-511](https://brighthiveio.atlassian.net/browse/BH-511) Seed library of 20+ quality-rule templates
- [BH-537](https://brighthiveio.atlassian.net/browse/BH-537) Expose QualityRule types in public GraphQL schema
- [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) Resolvers + service for quality-rule CRUD
- [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) Replace MOCK_RULES with live qualityRules query
- [BH-546](https://brighthiveio.atlassian.net/browse/BH-546) Create/edit drawer with scope selector + asset picker
- [BH-547](https://brighthiveio.atlassian.net/browse/BH-547) Activate/deactivate toggle + execution history + sparkline
- [BH-583](https://brighthiveio.atlassian.net/browse/BH-583) Quality-check graph cleanup (SQL datasource, dedup GX)
- [BH-517](https://brighthiveio.atlassian.net/browse/BH-517) Preserve role-based section visibility in refactored nav
- [BH-518](https://brighthiveio.atlassian.net/browse/BH-518) Studio critical frontend guardrails
- [BH-520](https://brighthiveio.atlassian.net/browse/BH-520) Add profiler_task as a schedulable batch task

## In Code-Review / Staging-QC (pipeline ready)

Security P0s: BH-559 (multi-tenant), BH-560 (PAT-leak), BH-561 (errorCode envelope), BH-563 (JWT scrub), BH-646 (tenant isolation), BH-650 (RBAC).
MCP/Okta: BH-647 (Bedrock sanitizer), BH-573 (Cognito+Okta federation), BH-574 (Route53/ACM).
Ingestion: BH-642/643/644/651 (AutoPilot scoping + OM→Neo4j sync), BH-551/554 (Snowflake ingestion).
Semantic views: BH-619/620/622 (lineage, governed PRs, QC), BH-527/528/529/530/549 (Snowflake conn + dialect + GHE proxy).
Eval/tests: BH-567, BH-592/594/597.

## Repository Changes (feature/fix PRs)

### brighthive-platform-core (82 PRs)

- [#885](https://github.com/brighthive/brighthive-platform-core/pull/885) fix(om): backfill description onto already-OM-linked nodes too (BH-651)
- [#883](https://github.com/brighthive/brighthive-platform-core/pull/883) fix(om): backfill OM table descriptions onto DataAssetNode during sync (BH-651)
- [#881](https://github.com/brighthive/brighthive-platform-core/pull/881) fix(om): scope getAllDataAssets to workspace's own services — tenant isolation (BH-646)
- [#879](https://github.com/brighthive/brighthive-platform-core/pull/879) fix(om): enforce schemaFilterPattern on AutoPilot ingestion pipeline (BH-644)
- [#877](https://github.com/brighthive/brighthive-platform-core/pull/877) fix(om): link legacy name-only DataAssetNodes to OpenMetadata tables (BH-643)
- [#876](https://github.com/brighthive/brighthive-platform-core/pull/876) Merge pull request #865 from brighthive/fix/data-assets-504-timeout
- [#875](https://github.com/brighthive/brighthive-platform-core/pull/875) fix(om): scope AutoPilot scan to production schemas — exclude dbt dev sandboxes (BH-642)
- [#873](https://github.com/brighthive/brighthive-platform-core/pull/873) feat(admin): repairWarehouseServiceAsAdmin — completes cleanup suite (BH-636)
- [#871](https://github.com/brighthive/brighthive-platform-core/pull/871) feat(admin): dedupDataAssetsAsAdmin — collapse dup assets to OM-backed copy
- [#869](https://github.com/brighthive/brighthive-platform-core/pull/869) feat(admin): superadmin cleanup mutations — reconcile + purge orphan embeddings
- [#868](https://github.com/brighthive/brighthive-platform-core/pull/868) fix(infra): restore isSuperAdmin + workspace_id Cognito custom attrib…
- [#867](https://github.com/brighthive/brighthive-platform-core/pull/867) docs(admin): spec — superadmin self-service cleanup + cross-store reconciliation
- [#866](https://github.com/brighthive/brighthive-platform-core/pull/866) fix(data-asset): purge Redis embedding on asset delete — stop ghost-catalog pollution
- [#865](https://github.com/brighthive/brighthive-platform-core/pull/865) perf(data-assets): fix 504 timeout on workspace.dataAssets query
- [#864](https://github.com/brighthive/brighthive-platform-core/pull/864) docs(om): step-by-step REMOVAL.md runbook for the OLD scanner lambda
- [#863](https://github.com/brighthive/brighthive-platform-core/pull/863) feat(om): SDK-free /team REST module (prereq to delete OLD scanner lambda) (BH-526)
- [#862](https://github.com/brighthive/brighthive-platform-core/pull/862) docs(om): clarify OLD lambda — /workflow scan DEAD, /team CRUD LIVE
- [#861](https://github.com/brighthive/brighthive-platform-core/pull/861) Develop => Staging
- [#860](https://github.com/brighthive/brighthive-platform-core/pull/860) feat(feature-flags): system admin resolver + workspace access guard
- [#858](https://github.com/brighthive/brighthive-platform-core/pull/858) refactor(om): remove never-live snowflake scanner lambda, clarify OMD deprecation (BH-526)
- [#857](https://github.com/brighthive/brighthive-platform-core/pull/857) Develop => Staging (6/16/2026)
- [#856](https://github.com/brighthive/brighthive-platform-core/pull/856) Deploy/develop/fix 504 start
- [#854](https://github.com/brighthive/brighthive-platform-core/pull/854) fix(om): remove destructive service rename — never orphan a live catalog (BH-526)
- [#852](https://github.com/brighthive/brighthive-platform-core/pull/852) fix(HOTFIX-PROD-perf): eliminate Lambda cold-start 504s — remove assertConstraints from request path
- [#849](https://github.com/brighthive/brighthive-platform-core/pull/849) feat(om): canonical OM service name — auto-route ALL BYOW (Redshift + future) (BH-526)
- [#847](https://github.com/brighthive/brighthive-platform-core/pull/847) fix(om-webhook): parse workspace uuid from OM service name (correct #845)
- [#845](https://github.com/brighthive/brighthive-platform-core/pull/845) fix(om-webhook): derive workspace from event entity, not static header (BH-526)
- [#843](https://github.com/brighthive/brighthive-platform-core/pull/843) fix(om): trigger native AutoPilot scan + forward full warehouse connection (BH-526)
- [#842](https://github.com/brighthive/brighthive-platform-core/pull/842) docs(omd): mark old OMD scanners DEPRECATED (banners + DEPRECATED.md)
- [#841](https://github.com/brighthive/brighthive-platform-core/pull/841) fix(om-webhook): parse OM 1.8 single-event payloads + py3.9 import fix
- [#840](https://github.com/brighthive/brighthive-platform-core/pull/840) chore(staging): scanned-table DynamoDB mapping (#839)
- [#839](https://github.com/brighthive/brighthive-platform-core/pull/839) fix(om-webhook): write DynamoDB mapping for scanned tables (embeddings fix)
- [#838](https://github.com/brighthive/brighthive-platform-core/pull/838) chore(staging): trigger embeddings on scanned-table DataAssetNodes (#837)
- [#837](https://github.com/brighthive/brighthive-platform-core/pull/837) feat(om-webhook): trigger description+embedding for warehouse-scanned tables
- [#836](https://github.com/brighthive/brighthive-platform-core/pull/836) chore(staging): real WorkspaceSwitcher fix in UserService (#835)
- [#835](https://github.com/brighthive/brighthive-platform-core/pull/835) fix(user): raw Cypher in UserService.getWorkspaces — fix WorkspaceSwitcher cap
- [#834](https://github.com/brighthive/brighthive-platform-core/pull/834) chore(staging): raw-Cypher getWorkspaces fix (#833)
- [#833](https://github.com/brighthive/brighthive-platform-core/pull/833) fix(workspace): use raw Cypher for getWorkspaces to escape OGM 20-cap
- [#832](https://github.com/brighthive/brighthive-platform-core/pull/832) chore(staging): getWorkspaces flat-list fix (#831)
- [#831](https://github.com/brighthive/brighthive-platform-core/pull/831) fix(workspace): use flat workspaceRoles list to escape connection cap
- [#830](https://github.com/brighthive/brighthive-platform-core/pull/830) chore(staging): getWorkspaces pagination fix + Snowflake POC handoff doc (#829)
- [#829](https://github.com/brighthive/brighthive-platform-core/pull/829) fix(workspace): return all workspaces not just first 20 in getWorkspaces
- [#828](https://github.com/brighthive/brighthive-platform-core/pull/828) chore(staging): scanned-table DataAssetNodes (#827)
- [#827](https://github.com/brighthive/brighthive-platform-core/pull/827) feat(om-webhook): surface scanned warehouse tables as DataAssetNodes
- [#826](https://github.com/brighthive/brighthive-platform-core/pull/826) chore(staging): Snowflake scan-success fixes (#825)
- [#825](https://github.com/brighthive/brighthive-platform-core/pull/825) fix(snowflake): jaraco.context pin + tolerate partial scan errors
- [#824](https://github.com/brighthive/brighthive-platform-core/pull/824) chore(staging): jaraco deps for Snowflake keyring (#823)
- [#823](https://github.com/brighthive/brighthive-platform-core/pull/823) fix(snowflake): pin jaraco deps for keyring in OM scan
- [#822](https://github.com/brighthive/brighthive-platform-core/pull/822) chore(staging): Snowflake route auth fix (#821)
- [#821](https://github.com/brighthive/brighthive-platform-core/pull/821) fix(snowflake): Cognito-authorize /snowflake/service routes
- [#820](https://github.com/brighthive/brighthive-platform-core/pull/820) chore(staging): promote Snowflake containerized OM ingestion (#819)
- [#819](https://github.com/brighthive/brighthive-platform-core/pull/819) feat(snowflake): isolated containerized OM ingestion component
- [#818](https://github.com/brighthive/brighthive-platform-core/pull/818) feat(admin): deleteTransformationServiceAsAdmin + deleteDataAssetAsAdmin
- [#816](https://github.com/brighthive/brighthive-platform-core/pull/816) fix(om-ingestion): migrate webhook → /v1/events/subscriptions (OM 1.8.9) — unblocks the webhook gate
- [#815](https://github.com/brighthive/brighthive-platform-core/pull/815) fix(warehouse): normalize Snowflake config keys so UI-connected warehouses work
- [#814](https://github.com/brighthive/brighthive-platform-core/pull/814) feat(admin): SUPERADMIN tier + full-reversal resource deletion mutations
- [#813](https://github.com/brighthive/brighthive-platform-core/pull/813) fix(om-ingestion): add future annotations so py3.9 lambda runtime can load config
- [#811](https://github.com/brighthive/brighthive-platform-core/pull/811) feat(slack): Slack workspace connect — fix race condition, Cognito service user, credential storage
- [#810](https://github.com/brighthive/brighthive-platform-core/pull/810) release: dns_stack hotfix for staging deploy (BH-574)
- [#809](https://github.com/brighthive/brighthive-platform-core/pull/809) fix(dns): unblock staging deploy + correct prod FQDNs to app.brighthive.net (BH-574)
- [#808](https://github.com/brighthive/brighthive-platform-core/pull/808) Develop => Staging (6/9/2026)
- [#807](https://github.com/brighthive/brighthive-platform-core/pull/807) feat(quality): Quality check overhaul
- [#806](https://github.com/brighthive/brighthive-platform-core/pull/806) docs(readme): add Unit Tests CI badge alongside the deploy badges
- [#805](https://github.com/brighthive/brighthive-platform-core/pull/805) ci(unit-tests): gate every PR on eval harness + scrub-bearer + url-parser tests
- [#804](https://github.com/brighthive/brighthive-platform-core/pull/804) feat(make): `make verify` and `make verify-pristine` for trial Day-1 pre-flight
- [#803](https://github.com/brighthive/brighthive-platform-core/pull/803) fix(security): extend token-redaction regex — ghu_ + URL query strings (audit-debt #11)
- [#802](https://github.com/brighthive/brighthive-platform-core/pull/802) feat(local-dev): LocalStack in compose + endpoint-aware AWS clients (BH-611)
- [#801](https://github.com/brighthive/brighthive-platform-core/pull/801) test(semantic-view): deterministic eval harness (BH-618)
- [#800](https://github.com/brighthive/brighthive-platform-core/pull/800) feat(github-binding): commitSemanticViewToGitHub orchestrator (BH-614)
- [#799](https://github.com/brighthive/brighthive-platform-core/pull/799) feat(github-binding): WorkspaceGitHubBindingNode + setWorkspaceGitHubBinding (BH-613)
- [#798](https://github.com/brighthive/brighthive-platform-core/pull/798) docs(spec): SPEC-SEMANTIC-VIEW-AUTHORING-E2E — author YAML, validate, ship to GitHub
- [#797](https://github.com/brighthive/brighthive-platform-core/pull/797) feat(local-dev): full OGM seed coverage + mutation parity inventory
- [#796](https://github.com/brighthive/brighthive-platform-core/pull/796) docs(spec): sign off SPEC-MCP-DCR-RFC7591 (5 resolved Qs)
- [#795](https://github.com/brighthive/brighthive-platform-core/pull/795) fix(warehouse): branch OMD connection shape per warehouse type
- [#794](https://github.com/brighthive/brighthive-platform-core/pull/794) docs(spec): SPEC-MCP-DCR-RFC7591 — replaces closed pc#789
- [#793](https://github.com/brighthive/brighthive-platform-core/pull/793) feat(pc): trial backend megaconsolidation — GHE proxy + MCP/Okta + Snowflake source config
- [#787](https://github.com/brighthive/brighthive-platform-core/pull/787) Staging => Production (6/5/2026)
- [#786](https://github.com/brighthive/brighthive-platform-core/pull/786) merge develop => staging
- [#785](https://github.com/brighthive/brighthive-platform-core/pull/785) feat(workflow): Workflow Spec Runtime, Compiler, Snowflake Cortex Adapter & MCP Tools
- [#779](https://github.com/brighthive/brighthive-platform-core/pull/779) docs(agents): PR size rules + AI agent guidance (Claude/Cursor/Gemini/Copilot)
- [#770](https://github.com/brighthive/brighthive-platform-core/pull/770) feat(studio): Studio template MVP
- [#769](https://github.com/brighthive/brighthive-platform-core/pull/769) feat(onboarding): add Makefile with make local/start/stop/status

### brightbot (51 PRs)

- [#564](https://github.com/brighthive/brightbot/pull/564) test(mcp): xfail heavy sync MCP tests on BH-648 gateway 504
- [#563](https://github.com/brighthive/brightbot/pull/563) feat(quality): metric-snapshot SQL builder for longitudinal monitoring (GC-12 / BH-600)
- [#561](https://github.com/brighthive/brightbot/pull/561) fix(auth): RBAC fail-closed — empty memberships can't pivot to a client workspace_id (BH-650)
- [#560](https://github.com/brighthive/brightbot/pull/560) test(mcp): extend PoC harness — full DBT lifecycle via MCP (BH-601)
- [#558](https://github.com/brighthive/brightbot/pull/558) fix(mcp): sanitize Bedrock toolConfig on ALL agent models (BH-647)
- [#557](https://github.com/brighthive/brightbot/pull/557) feat(quality): pure longitudinal anomaly detection core (GC-12 / BH-600)
- [#556](https://github.com/brighthive/brightbot/pull/556) fix(mcp): strip Bedrock-unsupported 'example' from agent tool schemas (BH-647)
- [#554](https://github.com/brighthive/brightbot/pull/554) docs(dbt-agent): document semantic view lifecycle capabilities (BH-624)
- [#552](https://github.com/brighthive/brightbot/pull/552) feat(brightbot): full semantic view lifecycle (read/mirror/deploy) — BH-624 epic
- [#549](https://github.com/brighthive/brightbot/pull/549) fix(auth): tag threads with the workspace the user is IN, not workspaces[0]
- [#548](https://github.com/brighthive/brightbot/pull/548) test(auth): isolate LOCAL_DEV_MODE so api-key/bearer paths are exercised
- [#547](https://github.com/brighthive/brightbot/pull/547) fix(description-gen): handle empty session_info from webhook triggers
- [#546](https://github.com/brighthive/brightbot/pull/546) test(snowflake): fix order-dependent flake in SnowflakeConnection.connect tests
- [#545](https://github.com/brighthive/brightbot/pull/545) develop => Staging 
- [#544](https://github.com/brighthive/brightbot/pull/544) feat(backends/agents): workspace-aware S3 bucket resolution via Secrets Manager
- [#543](https://github.com/brighthive/brightbot/pull/543) fix(snowflake): deploy dbt-agent warehouse fetch fix to staging (#542)
- [#542](https://github.com/brighthive/brightbot/pull/542) fix(snowflake): make dbt agent fetch real warehouse data — pin introspect + fix KeyError 'user'
- [#540](https://github.com/brighthive/brightbot/pull/540) test(gc): MCP-driven Golden Cases + Longaeva PoC E2E harness (BH-601)
- [#538](https://github.com/brighthive/brightbot/pull/538) feat(dbt-agent): qc_semantic_view_pipeline — read-only upstream-vs-product QC (BH-622)
- [#536](https://github.com/brighthive/brightbot/pull/536) feat(dbt-agent): ship_semantic_view_to_github — scaffold to governed PR (BH-620)
- [#534](https://github.com/brighthive/brightbot/pull/534) feat(introspection): surface SV lineage in tool summary (BH-619)
- [#532](https://github.com/brighthive/brightbot/pull/532) feat(introspection): semantic-view lineage — base_tables + join graph (BH-619)
- [#530](https://github.com/brighthive/brightbot/pull/530) fix(mcp): correct DEFAULT_AS_METADATA_URL to prod Cognito issuer
- [#529](https://github.com/brighthive/brightbot/pull/529) docs(mcp): correct BH_MCP_AUTH_SERVER_URL to Cognito issuer (custom-domain .well-known 404s)
- [#527](https://github.com/brighthive/brightbot/pull/527) Develop => Staging (6/10/2026)
- [#526](https://github.com/brighthive/brightbot/pull/526) fix(quality): use OGM API for quality rules fetch and execution write
- [#525](https://github.com/brighthive/brightbot/pull/525) feat(artifacts): BH_ARTIFACTS envelope emission — per-request opt-in for Slack client
- [#524](https://github.com/brighthive/brightbot/pull/524) fix(brightbot): resolve conflicts and sync develop with staging
- [#523](https://github.com/brighthive/brightbot/pull/523) Feat/filesystem codeinterpreter per workspace
- [#522](https://github.com/brighthive/brightbot/pull/522) Develop => Staging (6/9/2026)
- [#521](https://github.com/brighthive/brightbot/pull/521) feat(quality): Quality check overhaul
- [#520](https://github.com/brighthive/brightbot/pull/520) fix(github-proxy): select errorCode + httpStatus on all 7 mutations (audit-debt #10)
- [#519](https://github.com/brighthive/brightbot/pull/519) test(dbt-react): rewrite all stale tool tests for proxy architecture
- [#518](https://github.com/brighthive/brightbot/pull/518) docs(spec): sign off 3 brightbot specs (Snowflake, Mart, Okta-federated)
- [#517](https://github.com/brighthive/brightbot/pull/517) feat(warehouse): SnowflakeConnection.from_workspace() reader (SPEC-SNOWFLAKE-E2E §2.5)
- [#516](https://github.com/brighthive/brightbot/pull/516) docs(spec): SPEC-SNOWFLAKE-E2E — single contract for Add Snowflake flow (audit #1)
- [#515](https://github.com/brighthive/brightbot/pull/515) docs(gc): SPEC-GOLDEN-CASES + 13-case validation harness against live LONGAEVA
- [#514](https://github.com/brighthive/brightbot/pull/514) feat(platform-api): JWT refresh + retry adapter + connection pooling
- [#513](https://github.com/brighthive/brightbot/pull/513) docs(spec): SPEC-GENERATE-MART-MODEL — deterministic dbt mart generator (GC-5)
- [#512](https://github.com/brighthive/brightbot/pull/512) test(gc10): GC-10 harness — 7-stage Silver→PR contract (BH-597)
- [#511](https://github.com/brighthive/brightbot/pull/511) feat(dbt-agent): materialize_dbt_project tool — close GC-8 disk-write gap
- [#510](https://github.com/brighthive/brightbot/pull/510) feat: dbt-agent + GHE-proxy unified niche — full Snowflake/dbt + GitHub-proxy migration
- [#509](https://github.com/brighthive/brightbot/pull/509) Fix/vector search stale sentinel fallback
- [#504](https://github.com/brighthive/brightbot/pull/504) feat(dbt-agent): wire Atlas semantic-view scaffold into the agent (BH-591)
- [#501](https://github.com/brighthive/brightbot/pull/501) docs(mcp): cross-link MCP docs across repos + refresh rollout status (BH-115)
- [#500](https://github.com/brighthive/brightbot/pull/500) Staging => Production (6/5/2026)
- [#499](https://github.com/brighthive/brightbot/pull/499) merge develop => staging
- [#498](https://github.com/brighthive/brightbot/pull/498) feat: add workflow agent with artifact storage and profiler enhancements
- [#497](https://github.com/brighthive/brightbot/pull/497) feat(mcp): scaffold remote MCP server with two-layer auth (BH-572)
- [#491](https://github.com/brighthive/brightbot/pull/491) docs(agents): PR size rules + AI agent guidance (Claude/Cursor/Gemini/Copilot)
- [#484](https://github.com/brighthive/brightbot/pull/484) feat(onboarding): add make local/staging/start/stop/status

### brightbot-slack-server (54 PRs)

- [#80](https://github.com/brighthive/brightbot-slack-server/pull/80) fix(oauth): stop silent team re-point to unprovisioned workspaces + shutdown watchdog
- [#79](https://github.com/brighthive/brightbot-slack-server/pull/79) feat(chat): surface the dbt-mcp dynamic tools in the thinking indicator
- [#78](https://github.com/brighthive/brightbot-slack-server/pull/78) feat(chat): surface the dbt agent's dbt-Cloud + GitHub author-and-ship tools
- [#77](https://github.com/brighthive/brightbot-slack-server/pull/77) docs(slack): document INTERRUPTS_ENABLED + notification flags and the HITL flow
- [#76](https://github.com/brighthive/brightbot-slack-server/pull/76) fix(chat): label search_available_tools as capability lookup, not data search
- [#75](https://github.com/brighthive/brightbot-slack-server/pull/75) feat(chat): surface the dbt engineering agent's author-and-ship tools
- [#74](https://github.com/brighthive/brightbot-slack-server/pull/74) fix(infra): plumb INTERRUPTS_ENABLED into the ECS task environment
- [#73](https://github.com/brighthive/brightbot-slack-server/pull/73) feat(interrupts): give DBT-query_selection a real input surface in Slack
- [#72](https://github.com/brighthive/brightbot-slack-server/pull/72) feat(chat): surface the Longaeva PoC engineering-agent tools in the thinking indicator
- [#71](https://github.com/brighthive/brightbot-slack-server/pull/71) feat(chat): surface the full dbt engineering agent toolset in the thinking indicator
- [#70](https://github.com/brighthive/brightbot-slack-server/pull/70) fix(chat): label deep_agent's real tools in the thinking indicator
- [#69](https://github.com/brighthive/brightbot-slack-server/pull/69) fix(notifications): classify + Block-Kit the v4 quality_asset_result stage
- [#68](https://github.com/brighthive/brightbot-slack-server/pull/68) feat(observability): structured chat-path audit + CloudWatch alarms
- [#67](https://github.com/brighthive/brightbot-slack-server/pull/67) docs: document SSE push delivery + per-workspace poll model
- [#66](https://github.com/brighthive/brightbot-slack-server/pull/66) test(notifications): production-grade SSE coverage + fix multi-level subdomain CORS bug
- [#65](https://github.com/brighthive/brightbot-slack-server/pull/65) feat(notifications): SSE push delivery + observability merge (Harbour-Signals → develop)
- [#63](https://github.com/brighthive/brightbot-slack-server/pull/63) feat(monitoring): CloudWatch alarms + on-call runbook for BrightSignals
- [#62](https://github.com/brighthive/brightbot-slack-server/pull/62) feat(infra): split IAM from SSRF allowlist + aws:ResourceAccount + regex bucket validation
- [#61](https://github.com/brighthive/brightbot-slack-server/pull/61) test(notifications): poller + routes lifecycle integration tests + audit across all stages
- [#60](https://github.com/brighthive/brightbot-slack-server/pull/60) feat(auth): single-flight getWorkspaceToken to prevent Cognito stampede
- [#59](https://github.com/brighthive/brightbot-slack-server/pull/59) feat(observability): slack_trace_id naming, delivery_id fan-out, MSG=trace prefix, safe stringify
- [#58](https://github.com/brighthive/brightbot-slack-server/pull/58) fix(poller): share workspaceTokenManager with enricher (blocker)
- [#57](https://github.com/brighthive/brightbot-slack-server/pull/57) docs: update README + ops docs for observability, enricher retry, allowlist Pulumi config
- [#56](https://github.com/brighthive/brightbot-slack-server/pull/56) ci(deploy): sync ATTACHMENT_BUCKET_ALLOWLIST to Pulumi config
- [#55](https://github.com/brighthive/brightbot-slack-server/pull/55) feat(infra): add attachmentBucketAllowlist + ship BH_ALLOWED_S3_BUCKETS to ECS task
- [#54](https://github.com/brighthive/brightbot-slack-server/pull/54) fix(enricher): refresh JWT and retry on UNAUTHENTICATED + return EnrichmentResult
- [#53](https://github.com/brighthive/brightbot-slack-server/pull/53) feat(notifications): structured end-to-end observability + format audit field
- [#52](https://github.com/brighthive/brightbot-slack-server/pull/52) fix(s3): restore BH_ALLOWED_S3_BUCKETS allowlist for shared-platform …
- [#51](https://github.com/brighthive/brightbot-slack-server/pull/51) Develop => Staging (6/12/2026)
- [#50](https://github.com/brighthive/brightbot-slack-server/pull/50) Develop => Staging (6/12/2026)
- [#49](https://github.com/brighthive/brightbot-slack-server/pull/49) feat(s3): workspace-aware S3 bucket resolution via STS AssumeRole
- [#48](https://github.com/brighthive/brightbot-slack-server/pull/48) fix(staging-ci): use trigger-level branch guards instead of job-level ref checks
- [#47](https://github.com/brighthive/brightbot-slack-server/pull/47) Develop => Staging (6/11/2026)
- [#46](https://github.com/brighthive/brightbot-slack-server/pull/46) Develop => Staging
- [#45](https://github.com/brighthive/brightbot-slack-server/pull/45) ci(deploy): sanitize control chars + newlines in header secrets
- [#44](https://github.com/brighthive/brightbot-slack-server/pull/44) ci(deploy): pin Pulumi CLI to 3.245.0, commit infra lockfile, switch to npm ci
- [#43](https://github.com/brighthive/brightbot-slack-server/pull/43) ci(deploy): build on every branch push + sanitize non-ASCII secrets
- [#42](https://github.com/brighthive/brightbot-slack-server/pull/42) Develop => Staging (6/10/2026)
- [#41](https://github.com/brighthive/brightbot-slack-server/pull/41) feat: remove thread-reply trigger — bot responds only to @mentions and DMs
- [#40](https://github.com/brighthive/brightbot-slack-server/pull/40) feat(slack): disconnect eviction, dataset preview, LangGraph HITL interrupts
- [#39](https://github.com/brighthive/brightbot-slack-server/pull/39) perf(notifications): feature-flagged GSI-backed Query path in poller (BH-606)
- [#38](https://github.com/brighthive/brightbot-slack-server/pull/38) feat(notifications): Block Kit buttons for actionable stages (BH-607)
- [#37](https://github.com/brighthive/brightbot-slack-server/pull/37) refactor(notifications): split formatter into classify + render + actions (BH-603)
- [#36](https://github.com/brighthive/brightbot-slack-server/pull/36) fix(notifications): guard metadata accesses to prevent formatter throws (BH-602)
- [#35](https://github.com/brighthive/brightbot-slack-server/pull/35) docs(brightsignals): clean architecture doc drift; delete dead formatter code (BH-608)
- [#34](https://github.com/brighthive/brightbot-slack-server/pull/34) chore(prompts): extract Slack mrkdwn rules to versioned prompt module (BH-609)
- [#33](https://github.com/brighthive/brightbot-slack-server/pull/33) chore(aws): extract isAwsError helper and pin SDK resolutions (BH-604)
- [#32](https://github.com/brighthive/brightbot-slack-server/pull/32) fix(local-dev): centralize AWS clients, harden LOCAL_JWT, log tool errors on empty response
- [#31](https://github.com/brighthive/brightbot-slack-server/pull/31) feat(local-dev): support LocalStack S3/DynamoDB and LOCAL_JWT for full-local mode
- [#30](https://github.com/brighthive/brightbot-slack-server/pull/30) feat(notifications): plain-english quality-check copy and empty-response fallback
- [#29](https://github.com/brighthive/brightbot-slack-server/pull/29) fix(oauth): match AWS SDK errors by name/__type, not just instanceof
- [#28](https://github.com/brighthive/brightbot-slack-server/pull/28) docs(brightsignals): add notification architecture doc
- [#27](https://github.com/brighthive/brightbot-slack-server/pull/27) docs(onboarding): add reading-order path and day-1 setup
- [#26](https://github.com/brighthive/brightbot-slack-server/pull/26) feat(dx): add deployment origin tag to every response footer

### brighthive-webapp (44 PRs)

- [#1172](https://github.com/brighthive/brighthive-webapp/pull/1172) release: promote develop → staging (auth fixes + e2e suite)
- [#1171](https://github.com/brighthive/brighthive-webapp/pull/1171) test(e2e): playwright suite for auth + token lifecycle
- [#1169](https://github.com/brighthive/brighthive-webapp/pull/1169) release: promote develop → staging
- [#1166](https://github.com/brighthive/brighthive-webapp/pull/1166) feat(mcp): redesign connectivity card with prompt playground
- [#1165](https://github.com/brighthive/brighthive-webapp/pull/1165) release: MCP tools/list live rendering + JSON-RPC test (#1163)
- [#1164](https://github.com/brighthive/brighthive-webapp/pull/1164) fix(auth): categorized error toasts + InlineErrorBanner + workspace-switch cascade fix
- [#1163](https://github.com/brighthive/brighthive-webapp/pull/1163) feat(mcp): live tools/list rendering, JSON-RPC test, streamable-http parser
- [#1162](https://github.com/brighthive/brighthive-webapp/pull/1162) Develop => Staging (6/16/2026)
- [#1161](https://github.com/brighthive/brighthive-webapp/pull/1161) feat(system-admin): /system-admin portal with per-workspace feature flag management
- [#1160](https://github.com/brighthive/brighthive-webapp/pull/1160) Fix/develop/runtime feature flags polling
- [#1159](https://github.com/brighthive/brighthive-webapp/pull/1159) [HOTFIX-PROD] Fix/runtime feature flags polling
- [#1158](https://github.com/brighthive/brighthive-webapp/pull/1158) fix(auth): logout now clears cookies and sessionStorage
- [#1157](https://github.com/brighthive/brighthive-webapp/pull/1157) feat(mcp): surface all live MCP tools dynamically via tools/list
- [#1156](https://github.com/brighthive/brighthive-webapp/pull/1156) chore(backmerge): cherry-pick production hotfixes into develop
- [#1154](https://github.com/brighthive/brighthive-webapp/pull/1154) feat(HOT-FIX-asset-detail): add feature flags for all asset detail tabs
- [#1153](https://github.com/brighthive/brighthive-webapp/pull/1153) fix(setup): fix submit button always disabled on setup page
- [#1151](https://github.com/brighthive/brighthive-webapp/pull/1151) release: observability rewrite + MCP connectivity + polish (develop → staging)
- [#1150](https://github.com/brighthive/brighthive-webapp/pull/1150) fix(observability,mcp): security hardening, a11y, copy refinement, pure-fn tests
- [#1149](https://github.com/brighthive/brighthive-webapp/pull/1149) Develop => Staging (6/12/2026)
- [#1148](https://github.com/brighthive/brighthive-webapp/pull/1148) fix(markdown): remove className prop from ReactMarkdown, wrap in div instead
- [#1147](https://github.com/brighthive/brighthive-webapp/pull/1147) feat(mcp): MCP Connectivity card in Workspace Settings → Integrations [BH-589]
- [#1146](https://github.com/brighthive/brighthive-webapp/pull/1146) feat(observability): replace mocked Project Observability with real runs, dbt logs, and agent PRs
- [#1145](https://github.com/brighthive/brighthive-webapp/pull/1145) fix(warehouse): provider-aware step-1 validation (Snowflake)
- [#1143](https://github.com/brighthive/brighthive-webapp/pull/1143) fix(staging-mocking): align GitHubPR type names with generated casing (#1142)
- [#1142](https://github.com/brighthive/brighthive-webapp/pull/1142) fix(mocks): align GitHubPR type names with generated casing
- [#1140](https://github.com/brighthive/brighthive-webapp/pull/1140) feat(slack): Slack integration UI — connect/disconnect flow, connection status, immediate eviction
- [#1139](https://github.com/brighthive/brighthive-webapp/pull/1139) Develop => Staging (HOTFIX)
- [#1138](https://github.com/brighthive/brighthive-webapp/pull/1138) fix(semantic-view): add Apollo generic types to resolve TS2339 build errors
- [#1137](https://github.com/brighthive/brighthive-webapp/pull/1137) Develop => Staging (6/9/2026)
- [#1136](https://github.com/brighthive/brighthive-webapp/pull/1136) feat(quality): Quality check overhaul
- [#1135](https://github.com/brighthive/brighthive-webapp/pull/1135) Feat/feature flags full coverage
- [#1134](https://github.com/brighthive/brighthive-webapp/pull/1134) feat(feature-flags): full runtime flag coverage for all pages + fix default landing route
- [#1133](https://github.com/brighthive/brighthive-webapp/pull/1133) fix(warehouse): rename Snowflake form fields to match cdk lambda contract
- [#1132](https://github.com/brighthive/brighthive-webapp/pull/1132) docs(BH-589): SPEC for MCP integration UI in Workspace Settings
- [#1131](https://github.com/brighthive/brighthive-webapp/pull/1131) Staging => Production (6/5/2026)
- [#1130](https://github.com/brighthive/brighthive-webapp/pull/1130) Develop => Staging 
- [#1129](https://github.com/brighthive/brighthive-webapp/pull/1129) feat(feature-flags): add whitelist-only flags to hide Ask BrightAgent button and notification icon
- [#1128](https://github.com/brighthive/brighthive-webapp/pull/1128) develop => Staging (HOTFIX- UNAUTHENTICATED loop and login page spinner on staging)
- [#1127](https://github.com/brighthive/brighthive-webapp/pull/1127) fix(auth): prevent UNAUTHENTICATED redirect loop and login page spinner on staging
- [#1126](https://github.com/brighthive/brighthive-webapp/pull/1126) merge develop => staging
- [#1125](https://github.com/brighthive/brighthive-webapp/pull/1125) fix(projects): fix sidebar expansion
- [#1124](https://github.com/brighthive/brighthive-webapp/pull/1124) feat(BH-376): WorkflowSpec canvas, SemanticView YAML editor, Snowflake integration & nav refactor
- [#1123](https://github.com/brighthive/brighthive-webapp/pull/1123) docs(agents): PR size rules + AI agent guidance (Claude/Cursor/Gemini/Copilot)
- [#1102](https://github.com/brighthive/brighthive-webapp/pull/1102) fix(ci): claude review posts comments + auto-runs on PRs to develop (BH-498)

### brighthive-data-organization-cdk (2 PRs)

- [#158](https://github.com/brighthive/brighthive-data-organization-cdk/pull/158) docs(claude): note org /team connector is commented out; AutoPilot is scan path
- [#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) docs(BH-554): design for SnowflakeIngestionStack workspace_secret_store migration

### brighthive-data-workspace-cdk (2 PRs)

- [#123](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/123) docs(claude): clarify OMD /team route — OLD lambda (scan-dead/CRUD-live), AutoPilot is scan path
- [#109](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/109) Upgrade: redshfit connector package to v 2.17 for SOC complience requ…