# Sprint 8 --- Release Notes (Mid-Sprint Checkpoint)

**Period**: Apr 7--21, 2026 | **Checkpoint**: Apr 20, 2026
**Sprint Goal**: Governance context tools, Azure Synapse integration, dbt agent GitHub commits, ticket hygiene

---

## Summary

| Metric | Value |
|--------|-------|
| Tickets Completed | 21 / 55 (38.2%) |
| Story Points | 5 / 41 (12.2%) -- 19 Done tickets unpointed |
| PRs Merged | 103 (82 feature + 21 build) |
| Repos Touched | 7 |
| Team | 4 engineers |
| Status | Mid-sprint checkpoint |

---

## Completed Tickets

| Key | Summary | Assignee | Points |
|-----|---------|----------|--------|
| [BH-357](https://brighthiveio.atlassian.net/browse/BH-357) | Inject governance policies into workspace context | Kuri | -- |
| [BH-356](https://brighthiveio.atlassian.net/browse/BH-356) | Add isActive field to CustomPolicyNode | Kuri | -- |
| [BH-355](https://brighthiveio.atlassian.net/browse/BH-355) | Credential form HITL interrupt for ingestion | Kuri | -- |
| [BH-346](https://brighthiveio.atlassian.net/browse/BH-346) | dbt model detail view with SQL, PR link, lineage, origin badge | Kuri | -- |
| [BH-345](https://brighthiveio.atlassian.net/browse/BH-345) | Extend TransformationNode with model metadata + per-model run tracking | Kuri | -- |
| [BH-344](https://brighthiveio.atlassian.net/browse/BH-344) | Extend TransformationNode with model metadata | Kuri | -- |
| [BH-342](https://brighthiveio.atlassian.net/browse/BH-342) | dbt agent auto-read TransformationService config | Kuri | -- |
| [BH-340](https://brighthiveio.atlassian.net/browse/BH-340) | Replace Job ID text field with dbt Cloud job dropdown | Kuri | -- |
| [BH-339](https://brighthiveio.atlassian.net/browse/BH-339) | Device Flow OAuth + disconnect for GitHub connection | Kuri | -- |
| [BH-330](https://brighthiveio.atlassian.net/browse/BH-330) | Complete dbt workflow -- jobs, data products, GitHub repos, audit fixes | Kuri | -- |
| [BH-328](https://brighthiveio.atlassian.net/browse/BH-328) | dbt agent flow improvements -- auto-read config, reduce interrupts | Kuri | -- |
| [BH-327](https://brighthiveio.atlassian.net/browse/BH-327) | Webapp dbt settings -- remove invoke checkbox + GitHub repo management | Kuri | -- |
| [BH-326](https://brighthiveio.atlassian.net/browse/BH-326) | Webapp dbt settings and GitHub repo management | Kuri | -- |
| [BH-325](https://brighthiveio.atlassian.net/browse/BH-325) | dbt agent flow improvements | Kuri | -- |
| [BH-322](https://brighthiveio.atlassian.net/browse/BH-322) | Azure Synapse T-SQL dialect support in warehouse | Kuri | -- |
| [BH-321](https://brighthiveio.atlassian.net/browse/BH-321) | Warehouse adapter pattern for webhook processing | Kuri | -- |
| [BH-319](https://brighthiveio.atlassian.net/browse/BH-319) | Replace Job ID text field with dbt Cloud job dropdown | Kuri | -- |
| [BH-282](https://brighthiveio.atlassian.net/browse/BH-282) | Claude to Bedrock migration -- model routing | Kuri | -- |
| [BH-278](https://brighthiveio.atlassian.net/browse/BH-278) | EDL shutdown -- decommission legacy data pipeline | Ahmed | 2 |
| [BH-253](https://brighthiveio.atlassian.net/browse/BH-253) | OMD webhook enhanced event tracking | Ahmed | -- |
| [BH-240](https://brighthiveio.atlassian.net/browse/BH-240) | GraphQL capabilities for deep_agent supervisor | Marwan | 3 |

---

## In Progress / Near Completion

| Key | Summary | Assignee | Status |
|-----|---------|----------|--------|
| [BH-347](https://brighthiveio.atlassian.net/browse/BH-347) | Governance context tools -- schemas, glossary, policies | Kuri | Code Review |
| [BH-286](https://brighthiveio.atlassian.net/browse/BH-286) | Bedrock Knowledge Base retrieval tool | Marwan | Code Review |
| [BH-293](https://brighthiveio.atlassian.net/browse/BH-293) | Update unstructured data stack for workspace AWS accounts | Ahmed | In Progress |
| [BH-285](https://brighthiveio.atlassian.net/browse/BH-285) | Azure Synapse ingestion pipeline | Ahmed | In Progress |
| [BH-251](https://brighthiveio.atlassian.net/browse/BH-251) | Support Azure Synapse querying in quality check sub-agent | Ahmed | In Progress |
| [BH-210](https://brighthiveio.atlassian.net/browse/BH-210) | [FE] Project BrightAgent integration | Marwan | In Progress |

---

## Repository Changes

### brighthive-platform-core (30 PRs -- 22 feature, 8 build)

#### Feature PRs

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#736](https://github.com/brighthive/brighthive-platform-core/pull/736) | fix(slack): make createSlackServiceUser idempotent | Kuri | +280/-30 |
| [#734](https://github.com/brighthive/brighthive-platform-core/pull/734) | Fix/GitHub auth secret upsert | Marwan | +29/-9 |
| [#733](https://github.com/brighthive/brighthive-platform-core/pull/733) | feat(Analytics): Fix catalog backend for Vec/Met/Qua (BH-375) | Harbour | +556/-35 |
| [#730](https://github.com/brighthive/brighthive-platform-core/pull/730) | Add: ingestion event tracking for enhanced OMD webhook lambda | Ahmed | +318/-54 |
| [#729](https://github.com/brighthive/brighthive-platform-core/pull/729) | feat(health): data asset health check fields (BH-374) | Kuri | +1657/-0 |
| [#728](https://github.com/brighthive/brighthive-platform-core/pull/728) | feat: Scheduler | Harbour | +202/-0 |
| [#726](https://github.com/brighthive/brighthive-platform-core/pull/726) | Update: graphql schema datatypes adding BIT for Azure SQL in OMD | Ahmed | +1/-0 |
| [#724](https://github.com/brighthive/brighthive-platform-core/pull/724) | feat(seeds): add Snowflake + Synapse warehouses and governance policies (BH-347) | Kuri | +152/-1 |
| [#722](https://github.com/brighthive/brighthive-platform-core/pull/722) | refactor(warehouse): enforce WarehouseServiceProvider enum + Synapse BYOW support | Kuri | +1052/-278 |
| [#721](https://github.com/brighthive/brighthive-platform-core/pull/721) | feat(governance): add isActive field to CustomPolicyNode (BH-356) | Kuri | +15/-0 |
| [#720](https://github.com/brighthive/brighthive-platform-core/pull/720) | feat(omd): add Synapse source config with registry-based routing | Kuri | +161/-83 |
| [#719](https://github.com/brighthive/brighthive-platform-core/pull/719) | test(synapse): add E2E tests for BYOW connect flow | Kuri | +239/-1 |
| [#714](https://github.com/brighthive/brighthive-platform-core/pull/714) | feat(seed): comprehensive workflow seeds matching real system output | Kuri | +319/-21 |
| [#713](https://github.com/brighthive/brighthive-platform-core/pull/713) | feat(dbt): extend TransformationNode with model metadata + per-model run tracking | Kuri | +4057/-2 |
| [#712](https://github.com/brighthive/brighthive-platform-core/pull/712) | feat(github): Device Flow OAuth + disconnect for GitHub connection (BH-339) | Kuri | +2684/-124 |
| [#742](https://github.com/brighthive/brighthive-platform-core/pull/742) | Update: s3_role_arn script with fallback mechanism | Ahmed | +47/-8 |
| [#740](https://github.com/brighthive/brighthive-platform-core/pull/740) | Update: retrieval method for notification table env var | Ahmed | +2/-1 |
| [#738](https://github.com/brighthive/brighthive-platform-core/pull/738) | Add: base notification endpoint, filtering by workspace or dataasset | Ahmed | +135/-1 |
| [#737](https://github.com/brighthive/brighthive-platform-core/pull/737) | Add: new type for tableFQN supporting generic warehouse | Ahmed | +87/-60 |
| [#711](https://github.com/brighthive/brighthive-platform-core/pull/711) | Update: addSource mutation logic to only look for workspace admin | Ahmed | +0/-3 |
| [#709](https://github.com/brighthive/brighthive-platform-core/pull/709) | feat(dbt): complete dbt workflow -- jobs, data products, GitHub repos, audit fixes | Kuri | +2357/-124 |
| [#708](https://github.com/brighthive/brighthive-platform-core/pull/708) | feat: Add data preview | Harbour | +440/-0 |

#### Build Promotion PRs

| PR | Title | Author |
|----|-------|--------|
| [#743](https://github.com/brighthive/brighthive-platform-core/pull/743) | Develop => Staging | Ahmed |
| [#741](https://github.com/brighthive/brighthive-platform-core/pull/741) | Develop => Staging | Ahmed |
| [#739](https://github.com/brighthive/brighthive-platform-core/pull/739) | Develop => Staging (4/17/2026) | Ahmed |
| [#735](https://github.com/brighthive/brighthive-platform-core/pull/735) | build: Develop => Staging (4/15/2026) | Marwan |
| [#731](https://github.com/brighthive/brighthive-platform-core/pull/731) | Develop to Staging | Harbour |
| [#723](https://github.com/brighthive/brighthive-platform-core/pull/723) | chore: promote develop to staging | Kuri |
| [#716](https://github.com/brighthive/brighthive-platform-core/pull/716) | chore: deploy develop to staging | Kuri |
| [#710](https://github.com/brighthive/brighthive-platform-core/pull/710) | Staging => Production (4/8/2026) | Marwan |

---

### brighthive-webapp (36 PRs -- 32 feature, 4 build)

#### Feature PRs

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#1073](https://github.com/brighthive/brighthive-webapp/pull/1073) | feat(context+analytics): KB page, rich mockup UX for Context/Analytics sub-tabs with BETA flags (BH-376) | Kuri | +1871/-123 |
| [#1070](https://github.com/brighthive/brighthive-webapp/pull/1070) | Fix/GitHub device flow polling | Marwan | +270/-118 |
| [#1069](https://github.com/brighthive/brighthive-webapp/pull/1069) | feat(Analytics): Update health check readme (BH-375) | Harbour | +43/-29 |
| [#1068](https://github.com/brighthive/brighthive-webapp/pull/1068) | feat(project): Observability tab -- proactive insights, data contracts, pipeline runs (BH-359) | Kuri | +446/-1 |
| [#1067](https://github.com/brighthive/brighthive-webapp/pull/1067) | feat(personas): visual flow builder with React Flow (BH-376) | Kuri | +1032/-3 |
| [#1065](https://github.com/brighthive/brighthive-webapp/pull/1065) | style(context): brand-colored icons for transcription sources (BH-347) | Kuri | +30/-12 |
| [#1064](https://github.com/brighthive/brighthive-webapp/pull/1064) | feat(context): Transcribes page with real data sources + AWS services (BH-347) | Kuri | +299/-21 |
| [#1063](https://github.com/brighthive/brighthive-webapp/pull/1063) | feat(flags): feature-flag Context, Analytics, Custom Personas (BH-347) | Kuri | +10/-1 |
| [#1062](https://github.com/brighthive/brighthive-webapp/pull/1062) | feat(studio): add Custom Personas page to BrightStudio (BH-347) | Kuri | +1031/-74 |
| [#1060](https://github.com/brighthive/brighthive-webapp/pull/1060) | feat(context): add Context section -- KB, workspace context, formulas, library, transcribes (BH-347) | Kuri | +332/-0 |
| [#1059](https://github.com/brighthive/brighthive-webapp/pull/1059) | feat(analytics): add Dashboards, Reports, Alerts, Notifications, Health Checks (BH-347) | Kuri | +237/-50 |
| [#1058](https://github.com/brighthive/brighthive-webapp/pull/1058) | feat(ingestion): Airbyte icons + BYOW and Custom Upload coming soon (BH-347) | Kuri | +130/-42 |
| [#1057](https://github.com/brighthive/brighthive-webapp/pull/1057) | docs: add Data Catalog DX readme with health check schema (BH-375) | Kuri | +63/-8 |
| [#1056](https://github.com/brighthive/brighthive-webapp/pull/1056) | fix(slack): use Vite env prefix for SLACK_SERVER_URL | Kuri | +1/-1 |
| [#1055](https://github.com/brighthive/brighthive-webapp/pull/1055) | feat(analytics): platform analytics dashboard (BH-359) | Kuri | +2266/-422 |
| [#1054](https://github.com/brighthive/brighthive-webapp/pull/1054) | feat: Scheduler | Harbour | +2475/-16 |
| [#1052](https://github.com/brighthive/brighthive-webapp/pull/1052) | fix(brightagent): reset session on workspace switch (BH-358) | Kuri | +20/-4 |
| [#1051](https://github.com/brighthive/brighthive-webapp/pull/1051) | fix: dead imports + keyboard a11y for warehouse card picker | Kuri | +17/-11 |
| [#1049](https://github.com/brighthive/brighthive-webapp/pull/1049) | feat(warehouse): provider-specific icons, card picker, config forms (BH-347) | Kuri | +520/-396 |
| [#1048](https://github.com/brighthive/brighthive-webapp/pull/1048) | feat(governance): policy enforcement toggles + credential HITL interrupt (BH-355, BH-356) | Kuri | +261/-110 |
| [#1047](https://github.com/brighthive/brighthive-webapp/pull/1047) | feat(governance): policy enforcement toggles -- Active, Enforced, Admin Only (BH-356) | Kuri | +261/-110 |
| [#1046](https://github.com/brighthive/brighthive-webapp/pull/1046) | feat(brightagent): credential form HITL interrupt (BH-355) | Kuri | +457/-9 |
| [#1042](https://github.com/brighthive/brighthive-webapp/pull/1042) | fix(workflow): pass workspaceId to GetDbtJobs + guard disabled node clicks | Kuri | +4/-2 |
| [#1041](https://github.com/brighthive/brighthive-webapp/pull/1041) | fix(codegen): restore query fields + suppress ResizeObserver overlay | Kuri | +120/-63 |
| [#1040](https://github.com/brighthive/brighthive-webapp/pull/1040) | chore(codegen): regenerate types for BH-344/345/346 schema | Kuri | +275/-42 |
| [#1039](https://github.com/brighthive/brighthive-webapp/pull/1039) | feat(ui): dbt model detail view with SQL, PR link, lineage, and origin badge (BH-346) | Kuri | +894/-266 |
| [#1038](https://github.com/brighthive/brighthive-webapp/pull/1038) | feat(ui): Device Flow OAuth + Disconnect in GitHub Connection settings (BH-339) | Kuri | +1813/-253 |
| [#1037](https://github.com/brighthive/brighthive-webapp/pull/1037) | feat(ui): add Device Flow OAuth to GitHub Connection settings (BH-339) | Kuri | +643/-54 |
| [#1035](https://github.com/brighthive/brighthive-webapp/pull/1035) | feat(transformation): replace Job ID text field with dbt Cloud job dropdown (BH-319) | Kuri | +194/-30 |
| [#1034](https://github.com/brighthive/brighthive-webapp/pull/1034) | feat(dbt): remove invoke checkbox + add GitHub repo management | Kuri | +29797/-6827 |
| [#1033](https://github.com/brighthive/brighthive-webapp/pull/1033) | feat: Add preview asset tab | Harbour | +159/-3 |
| [#1032](https://github.com/brighthive/brighthive-webapp/pull/1032) | refactor(warehouse): registry patterns for warehouse UI extensibility | Kuri | +58/-50 |
| [#1028](https://github.com/brighthive/brighthive-webapp/pull/1028) | Upgrade React 17 to 18 | Marwan | +43184/-86836 |

#### Build Promotion PRs

| PR | Title | Author |
|----|-------|--------|
| [#1071](https://github.com/brighthive/brighthive-webapp/pull/1071) | build: Develop => Staging (4/15/2026) | Marwan |
| [#1053](https://github.com/brighthive/brighthive-webapp/pull/1053) | Develop => Staging (4/10/2026) | Marwan |
| [#1044](https://github.com/brighthive/brighthive-webapp/pull/1044) | chore: deploy develop to staging | Kuri |
| [#1036](https://github.com/brighthive/brighthive-webapp/pull/1036) | Staging => Production (4/8/2026) | Marwan |

---

### brightbot (19 PRs -- 15 feature, 4 build)

#### Feature PRs

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#452](https://github.com/brighthive/brightbot/pull/452) | Add: support for Azure Synapse querying in quality check sub-agent | Ahmed | +161/-25 |
| [#453](https://github.com/brighthive/brightbot/pull/453) | docs: add .env.example with all env vars categorized | Kuri | +223/-0 |
| [#451](https://github.com/brighthive/brightbot/pull/451) | feat: Scheduler | Harbour | +703/-1 |
| [#450](https://github.com/brighthive/brightbot/pull/450) | docs(dbt): add DX readme for ReAct dbt agent (BH-360) | Kuri | +254/-0 |
| [#449](https://github.com/brighthive/brightbot/pull/449) | feat(dbt): migrate dbt agent from deterministic graph to ReAct pattern (BH-360) | Kuri | +2648/-41 |
| [#448](https://github.com/brighthive/brightbot/pull/448) | Update: deepagents package to be fixed for 0.4.5 | Ahmed | +1/-1 |
| [#447](https://github.com/brighthive/brightbot/pull/447) | Pin deepagent version to 0.4.5 (package mismatch fix) | Ahmed | +1/-1 |
| [#446](https://github.com/brighthive/brightbot/pull/446) | fix: update auth test signature + guard cursor.description None | Kuri | +17/-24 |
| [#445](https://github.com/brighthive/brightbot/pull/445) | feat(agent): inject governance policies into workspace context (BH-357) | Kuri | +77/-35 |
| [#444](https://github.com/brighthive/brightbot/pull/444) | feat(ingestion): credential form HITL interrupt (BH-355) | Kuri | +292/-11 |
| [#443](https://github.com/brighthive/brightbot/pull/443) | fix(warehouse): update WarehouseConnection ABC to match implementations | Kuri | +13/-8 |
| [#440](https://github.com/brighthive/brightbot/pull/440) | feat(agent): on-demand governance context tools -- schemas, glossary, policies | Kuri | +978/-2 |
| [#435](https://github.com/brighthive/brightbot/pull/435) | feat(graphql): add GraphQL capabilities to deep_agent supervisor | Marwan | +744/-0 |
| [#434](https://github.com/brighthive/brightbot/pull/434) | feat(dbt): auto-read TransformationService config, reduce interrupts | Kuri | +604/-276 |
| [#433](https://github.com/brighthive/brightbot/pull/433) | feat(warehouse): Azure Synapse T-SQL dialect support | Kuri | +903/-326 |

#### Build Promotion PRs

| PR | Title | Author |
|----|-------|--------|
| [#455](https://github.com/brighthive/brightbot/pull/455) | Develop => Staging (4/15/2026) | Ahmed |
| [#454](https://github.com/brighthive/brightbot/pull/454) | Develop -> Staging | Harbour |
| [#438](https://github.com/brighthive/brightbot/pull/438) | chore: deploy develop to staging | Kuri |
| [#436](https://github.com/brighthive/brightbot/pull/436) | Staging => Production (4/8/2026) | Marwan |

---

### brighthive-data-organization-cdk (9 PRs -- 7 feature, 2 build)

#### Feature PRs

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#151](https://github.com/brighthive/brighthive-data-organization-cdk/pull/151) | Update: dataingestion stack to include Synapse ingestion as optional | Ahmed | +117/-21 |
| [#150](https://github.com/brighthive/brighthive-data-organization-cdk/pull/150) | Update: synapse ingestion stack IAM permissions fix | Ahmed | +37/-10 |
| [#149](https://github.com/brighthive/brighthive-data-organization-cdk/pull/149) | refactor(ingestion): pluggable warehouse SMs + Synapse integration tests | Kuri | +234/-33 |
| [#145](https://github.com/brighthive/brighthive-data-organization-cdk/pull/145) | docs(readme): rewrite with deployment checklist and architecture | Kuri | +272/-71 |
| [#142](https://github.com/brighthive/brighthive-data-organization-cdk/pull/142) | feat: Update ingestion to have samples for preview | Harbour | +16/-1 |
| [#139](https://github.com/brighthive/brighthive-data-organization-cdk/pull/139) | feat(ingestion): Azure Synapse ingestion pipeline with warehouse-type routing | Kuri | +1107/-16 |
| [#119](https://github.com/brighthive/brighthive-data-organization-cdk/pull/119) | ci: add Claude PR review workflow | Kuri | +25/-0 |

#### Build Promotion PRs

| PR | Title | Author |
|----|-------|--------|
| [#147](https://github.com/brighthive/brighthive-data-organization-cdk/pull/147) | chore: deploy develop to staging | Kuri |
| [#143](https://github.com/brighthive/brighthive-data-organization-cdk/pull/143) | Develop => Staging (4/8/2026) | Marwan |

---

### brighthive-data-workspace-cdk (6 PRs -- 4 feature, 2 build)

#### Feature PRs

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#122](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/122) | fix(redshift): add CATALOG_ID to cross-account external schema creation | Kuri | +233/-144 |
| [#119](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/119) | Feat/metadata configs for unstructured data | Ahmed | +162/-4 |
| [#118](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/118) | docs(readme): rewrite with deployment checklist and architecture | Kuri | +231/-143 |
| [#111](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/111) | ci: add Claude PR review workflow | Kuri | +25/-0 |

#### Build Promotion PRs

| PR | Title | Author |
|----|-------|--------|
| [#121](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/121) | Staging => main | Ahmed |
| [#120](https://github.com/brighthive/brighthive-data-workspace-cdk/pull/120) | Feat/metadata configs for unstructured data (#119) | Ahmed |

---

### brightbot-slack-server (2 PRs -- all feature)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#14](https://github.com/brighthive/brightbot-slack-server/pull/14) | fix(slack): only respond to @mentions, DMs, and thread replies | Kuri | +11/-1 |
| [#13](https://github.com/brighthive/brightbot-slack-server/pull/13) | fix(slack): only respond to @mentions, DMs, and thread replies | Kuri | +11/-1 |

---

### brighthive-admin (1 PR -- build only)

| PR | Title | Author |
|----|-------|--------|
| [#88](https://github.com/brighthive/brighthive-admin/pull/88) | chore: deploy develop to staging | Kuri |
