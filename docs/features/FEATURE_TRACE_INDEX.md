---
title: "Feature Trace Index"
description: "Cross-sprint catalog of shipped features with product one-liners, code trace pointers, PRs, and usage guides"
covers_sprints: "10-15"
covers_dates: "2026-05-05 to 2026-08-17"
generated_date: "2026-08-17"
tags: ["catalog", "release-notes", "trace"]
---

# Feature Trace Index (Sprints 10-15, May 5 - Aug 17, 2026)

A reference for confirming a shipped feature actually exists, where its code lives, which PR
shipped it, and how to trigger or find it. Built by tracing every sprint highlight in
[`jira/sprint/SPRINTS.md`](../../jira/sprint/SPRINTS.md) back to real files, routes, feature
flags, and MCP tools in the live repos — not paraphrased from release notes. 47 distinct
features across 8 repos.

## Table of Contents

- [Glossary](#glossary)
- [Warehouses & Data Connections](#warehouses--data-connections)
- [Routines, Signals & Alerting](#routines-signals--alerting)
- [Governance, Access & Trust](#governance-access--trust)
- [Data Pipelines, Lineage & Quality](#data-pipelines-lineage--quality)
- [AI Agent & Chat Experience](#ai-agent--chat-experience)
- [Platform Infrastructure](#platform-infrastructure)
- [Known Discrepancies](#known-discrepancies)

## Glossary

- **BrightSignals** — the alert/notification substrate: push alerts, severity catalog, delivery to Slack/webapp.
- **BrightRoutines** — the automation layer that detects, suggests, and schedules repeated agent work.
- **MCP (Model Context Protocol)** — the protocol BrightAgent tools and external clients use to call platform capabilities.
- **PII** — Personally Identifiable Information (SSN, email, etc.) — must be masked wherever a tool previews data.
- **SSIS / SSRS** — SQL Server Integration Services / SQL Server Reporting Services — legacy pipeline tooling BrightAgent can diagnose.
- **JIT (Just-In-Time) provisioning** — creating a user's account/permissions automatically on their first federated login, instead of requiring an admin to pre-add them.
- **PKCE** — Proof Key for Code Exchange, the OAuth flow used for "Log in with Okta."
- **SSE (Server-Sent Events)** — the one-way streaming protocol used for live token streaming and push notifications.
- **ECS** — AWS Elastic Container Service, the always-on hosting GraphQL Core moved to in Sprint 15.

## Warehouses & Data Connections

> **Deployment note.** This warehouse wave landed across Sprint 15 and is **live on staging** —
> where the Brighthive Demo workspace runs, so everything below is showcaseable there today. The
> brightbot PRs marked *(staging)* are merged to `develop`/`staging` but **not yet promoted to
> production** (prod `main` tip is #940, the 7/28 promotion); platform-core is verified through
> #1207 on `develop`; webapp through the #1432 release branch.

| Feature | One-liner | Trace pointer | Repo | PR(s) | How to use / where to see it |
|---|---|---|---|---|---|
| Warehouse Connect & Verify | Opens the connection, lists reachable databases, and reports who you're connected as — for any engine — before trusting it; a connected-but-unregistered warehouse still surfaces (registry ∪ secret store). | `verifyWarehouseConnection`/`registerWarehouse` — `warehouse-service.ts:337,193`; read-path union `warehouse-registry-reconcile.ts:describeConnectedWarehouse:88`; identity+liveness (MCP) `mcp/tools/connection_health.py:get_warehouse_connection_health_impl:37` | platform-core, brightbot | platform-core #1203, #1202, #1200, #1197, #1178; brightbot #986, #988, #1001 *(staging)* | Webapp → Workspace Settings → Services → a warehouse row → connection actions; or MCP `get_warehouse_connection_health`. |
| Default Warehouse | Marks one connected database as "the one we mean by default," and the whole stack (chat, MCP, legacy SQL paths) now honors it instead of guessing "first." | `setDefaultWarehouse` — `warehouse-service.ts:250`; shipped into served SDL `scripts/emit-schema-sdl.ts:85`; agent-side resolver `brightbot/tools/warehouse_catalog.py:resolve_warehouse_id:159` | platform-core, webapp, brightbot | platform-core #1176, #1196; webapp #1414, #1429, #1423; brightbot #1030, #1019, #1035 *(staging)* | Webapp → Workspace Settings → Services → Warehouses → expand a row → "Default" badge/action (per-database default via #1429). |
| Warehouse Operational Health | Shows disk space and failed jobs for any connected engine, right on the home screen; the webapp snapshot now matches the fields the backend actually emits (no null-crash). | `watchdog-typedefs.ts:153`; webapp health snapshot `common/Services/Service/ServiceConfiguration.tsx:224` | platform-core, webapp | platform-core #1146; webapp #1387, #1416 | Webapp → Home page (Hive Health band) or Analytics → Health Checks. |
| Warehouse Catalog Ladder (MCP) | Walk workspace → warehouses → databases → schemas → tables as discrete MCP steps — the discovery ladder external clients and the agent use to find data. | `brightbot/mcp/tools/warehouse_catalog.py:list_workspace_warehouses_impl:122`, `list_warehouse_databases_impl:168`, `list_warehouse_tables_impl:288` | brightbot | #1014, #1016 *(staging)* | MCP verbs `list_workspace_warehouses`, `list_warehouse_databases`, `list_warehouse_tables`. |
| Warehouse & Database Chat Targeting | Type `@warehouse.database` in chat to say exactly which database you mean — warehouse names with spaces work via `@[My Warehouse].db.table`. | `brightbot/utils/chat_addressing.py:parse_chat_addressing:232` (bracketed names `_SEGMENT_RE:89`); pin resolver `agents/super_agent/middleware/initialization_middleware.py:_resolve_pinned_warehouse_id:420`; webapp picker `BrightAgent/components/shared/ChatField/warehouseMentions.ts:74` | brightbot, webapp | brightbot #1010, #1032, #1033 *(staging)*; webapp #1430 | In BrightAgent chat, type `@` → pick a warehouse (+ database), e.g. `@ec2_mssql.demo_dbA` or `@[My Warehouse].db.table`. |
| Cross-Engine Warehouse Write | Create or replace a table in any connected engine (Snowflake, Redshift, Synapse, SQL Server) without hand-writing per-engine SQL. | `brightbot/tools/warehouse_writers.py:build_writer:149` (port `WarehouseWriter` Protocol:55) | brightbot | #976 *(staging)* | Internal to the workflow-agent write tools (`agents/workflow_agent/tools.py`). |
| XSD ↔ Warehouse Reconciliation Gate | Before generating warehouse DDL from an uploaded XSD schema, reconciles against the live warehouse and stops on mismatch — no blind table creation. | skill `brightbot/skills/system/xsd-table-schema/SKILL.md` (gate :140); enforced in `agents/dbt_agent/prompts/dbt_react_system_prompt.py:325` | brightbot | #993 *(staging)* | Fires inside dbt/XSD workflows whenever a schema file drives table creation. |
| Async Catalog Sync | Refresh a workspace's data-asset catalog after warehouse changes with one button (async job + polling) — or automatically after a warehouse-changing dbt run — instead of a manual re-scan. | platform-core `workspace-catalog-sync.ts:triggerWorkspaceCatalogSync:35`; webapp `DataAssetCatalog/useSyncWorkspaceCatalog.ts:34`; brightbot post-dbt hook `agents/dbt_agent/tools/catalog_sync_hook.py:schedule_workspace_catalog_sync_after_warehouse_change:100` | platform-core, webapp, brightbot | platform-core #1180; webapp #1418; brightbot #1025 *(staging)* | Webapp → Data Asset Catalog → "Sync catalog" (feature-flagged `CatalogSyncButton`); or fires on its own after a warehouse-changing dbt run. |
| On-Prem Job Queue | Sends dbt work to a customer's on-site server — their machine calls out, never the reverse. | `enqueueOnPremJob` — `onprem-job-queue.ts:OnPremJobQueueModel:28` | platform-core | #1199 | Not user-facing yet — GraphQL mutation only; the on-prem runner polls and drains it. |
| On-Prem Runner Lineage Ingestion | The on-site engineering runner posts its run reports into the same source-to-report lineage graph as cloud dbt runs (idempotent on `invocationId`, service-key auth). | `onprem-run-report.ts:OnPremRunReportModel.recordOnPremRunReport:25`; resolver `resolvers.ts:435` | platform-core | #1198 | `recordOnPremRunReport` mutation with `x-service-key` header — the on-prem runner calls it after each run. |
| Real-Warehouse MCP Hardening | Handles a real Redshift's quirks (hyphenated names, Spectrum tables) instead of failing silently. | `warehouse_base.py:50,355` | brightbot | #936, #937 | Call any warehouse-introspection MCP tool against a hyphenated-name or Spectrum-only Redshift DB. |
| dbt Multi-Repo + Secure Credentials | Connects more than one dbt/GitHub repo; keys live in AWS Secrets Manager. | `dbt-cloud-api-secret.ts:14` | brightbot, platform-core, webapp | brightbot #470, #478; platform-core #768; webapp #1089 | BrightAgent chat thread → session settings (gear icon) → GitHub repo picker. |

**Also in this wave (hardening, folded into the rows above):** brightbot #1029 (BH-1430) — the
database-size answer now names which host responded (`mcp/tools/database_size.py:get_database_size_impl:42`);
brightbot #992 (BH-1349) — a scheduled Warehouse Profiler behind `FEATURE_FLAG_WAREHOUSE_PROFILER_SCHEDULED`,
off by default (`agents/governance_agent/sub_agents/profiler_task.py:_route_from_start:334`); platform-core
#1196 (BH-1432) also emitted the previously-missing `isDefault` field + `setDefaultWarehouse` mutation into the
committed SDL (`schema.graphql:2949`, `:4681`) — the schema-backfill that made Default Warehouse actually
introspectable. Platform-core #1201 is boot plumbing (restores on-prem typedefs) for #1198/#1199, not a
capability.

## Routines, Signals & Alerting

| Feature | One-liner | Trace pointer | Repo | PR(s) | How to use / where to see it |
|---|---|---|---|---|---|
| Routine Suggestion Engine | Spots repeated work, judges if it's safe to automate, records who approved it. | `routines/detector.py`, `judge.py` | brightbot | #765, #668, #680, #792 +8 more | Runs automatically; output shows in the Workflows tab (below); auditable in CloudWatch. |
| Your Routines Page & Slack Cards | Schedule or dismiss a suggested routine from webapp or Slack. | `context/workflows` route; `blocks.ts:74` | webapp, slack-server | #1262, #1265, #1269, #120 +4 more | Webapp → Workspace → Context → Workflows tab; or Slack "Schedule"/"Dismiss" buttons. |
| Routine Delivery Provenance | A routine's Slack message shows its executed SQL and an artifact link. | `callback-handler.ts:32` | platform-core, brightbot, webapp, slack-server | platform-core #1184, #1181; brightbot #1026; slack-server #176; webapp #1420 | Webapp → Context → Routines → open a routine → set delivery target; Slack shows SQL + link on run. |
| Signal Catalog ⚠️ | One shared severity/wording list across webapp, Slack, backend. No CI drift-check found — only a unit test enforces parity. | `notifications/catalog.ts` | platform-core (+webapp, slack-server) | #1104, #1343, #150 | Compare an alert's color/wording in the webapp inbox vs. the same alert in Slack — identical, same catalog. |
| BrightSignals Notifications Drawer | One side panel for alerts, job updates, and to-dos. | `common/Notification/index.tsx` | webapp | #1097 | Webapp → click the bell icon in the top nav, any page. |
| BrightSignals Push Alerts | Slack + in-app alert the instant a quality run finishes or breaks. | `sse-routes.ts:63` | slack-server, brightbot, platform-core, webapp | slack-server #65, #63; brightbot #574; platform-core #890, #898/#900/#906-907; webapp #1177 | Webapp → Inbox nav item; same event also pushes to Slack in real time. |
| BrightSignals Alert History ⚠️ | Query a workspace's past alerts. No dedicated feature PR found — only a later staging-promotion PR. | `list_workspace_signals` — `workspace_signals.py:160` | brightbot | (only promotion PR #941 found) | Call the `list_workspace_signals` MCP tool with a `workspace_id`. |
| Notification Category Toggles | Mute one alert category without muting everything. | `NotificationsConfig.tsx:705-730` | webapp, platform-core | #1303, #1059, #1039 +1 more | Webapp → bell icon → settings/gear → Notification preferences → toggle a category off. |
| Quality Results → Slack | Posts a quality check's pass/fail to Slack automatically. | `quality_check_agent.py:1577` | brightbot | #486 | Run/wait for a Quality Check on an asset — result posts to Slack on its own. |
| Fleet Health Digest | Proactive "here's what needs attention" summary to a routine's owner, on schedule. | `digest_publisher.py:119` | brightbot, webapp | brightbot #985, #986; webapp #1394, #1402 | Webapp → System Admin → `/fleet-health`; or wait for the scheduled digest; or call `get_fleet_health` MCP tool. |
| Monitoring Agents Watchdog | Checks every pipeline for failures, drafts a fix for review — never auto-merges. | `pipeline_watchdog_task.py` | brightbot | #827, #829, #850, #860 +5 more | Runs on its own schedule; watch for a failure notification or a draft PR on the affected dbt project. |

## Governance, Access & Trust

| Feature | One-liner | Trace pointer | Repo | PR(s) | How to use / where to see it |
|---|---|---|---|---|---|
| BrightStudio Nav & Governance Pages | Pages for quality rules, access control, and audit trail. | `Governance/pages/*` | webapp | #1087, #1091, #1098 | Webapp → left nav "Governance" → Quality Rules / Access Control / Usage & Audit. |
| Enterprise Nav + Role Visibility | Menu adapts to what each role is allowed to see. | `genNav.tsx` (`isNavAllowed`) | webapp | #1100, #1107-#1110, #1116, #1121, #1122 | Just log in — sidebar content changes automatically by role. |
| BrightStudio Collaborator Agents | Collaborator-seat users can build/edit/delete their own agents. | `typedefs.ts:4954-4968` | platform-core | #776 (no matching webapp PR — UI already existed) | Log in as Collaborator → Custom Agents page → "New Agent" now enabled. |
| Configurable Quality Agent ⚠️ | Replaces a fake, hardcoded quality-rules screen with live data. Code actually shipped June 9/16 — before this sprint's official June 23 start; ticket transitioned Done in-window. | `QualityRulesPage.tsx:573` | webapp, brightbot | webapp #1136, brightbot #557 | Webapp → Govern → Quality Rules — live list, create/edit, enable/disable. |
| Agent Action Audit Log ⚠️ | Records agent data changes. Docs claim CloudWatch+DynamoDB dual-write — code is CloudWatch-only, no DynamoDB write exists. | `audit/decorator.py:74` | brightbot | #656, #659, #668 | Search CloudWatch Logs Insights for the `brightbot.audit` logger after any mutating agent action. |
| PII Masking Enforcement | Hides sensitive personal data anywhere an agent tool returns it. | `pii_masking.py` | brightbot | #808 (hardening PRs #917/#946 shipped after this sprint ended) | Ask any agent to preview warehouse rows with a PII column (SSN, email) — values return masked. |
| Log in with Okta | Sign in with company Okta login. | `SsoCallback.tsx` | webapp | #1207 | Click "Log in with Okta" on the login page. |
| Auto Account Setup (Okta JIT) | Creates account + permissions automatically on first Okta login. | `federated-provisioning.ts:160` | platform-core | #910 | Nothing to click — fires silently on a new Okta user's first login. |
| Slack Identity Linking | Connect your own Slack account to your login, self-service. | `install-provider.ts:63-135` | slack-server, platform-core | #105, #113, #966, #984 | Webapp → workspace settings → "Connect your Slack account" button. |

## Data Pipelines, Lineage & Quality

| Feature | One-liner | Trace pointer | Repo | PR(s) | How to use / where to see it |
|---|---|---|---|---|---|
| Pipeline Lineage + Safe Re-run | Maps source-to-report data flow; re-run just the broken stage. | `workflow-spec-typedefs.ts:512,522` | platform-core, webapp | platform-core #1140, #1141; webapp #1368, #1374 | Webapp → Project → Observability tab → lineage graph → "Re-run from here" on a failed step. |
| Semantic View Merge Confirmation | Confirms a data-model change merged, then promotes models as one step. | `semantic_view_commit_tools.py:202` | brightbot, platform-core | #672, #675, #924 +2 more | In dbt-agent chat: "has that Semantic View PR merged yet?" / "run these models to staging." |
| Knowledge Base Answer Reranking | Re-scores search answers with a second AI pass for relevance. | `knowledge_base.py:216` | brightbot | #935 | Call `query_knowledge_base` or ask BrightAgent a document question — reranked by default. |
| Schema-File (XSD/XML) Upload & Edit | Upload and edit a schema file directly in-browser. | `resourceContent` — `typedefs.ts:4391` | platform-core, webapp | platform-core #1144, #1148; webapp #1377, #1383 | Webapp → Project → Files → upload `.xsd`/`.xml` → click to open the editor. |
| Catalog & Projects Polish Sweep | Fixes broken toggles, wrong icons, missing schema tab. | `helpers.ts:207` | webapp | #1367, #1361 | Webapp → Project → Files → click a schema asset — icons/tabs now correct. |
| Atomic Project Creation | Cleans up automatically if project creation fails partway. | `CreateProjectModal.tsx:578-601` | webapp | #1382 | Webapp → Projects → "New Project" — no orphaned project left on failure. |

## AI Agent & Chat Experience

| Feature | One-liner | Trace pointer | Repo | PR(s) | How to use / where to see it |
|---|---|---|---|---|---|
| Data Profiler Agent | Checks new data's health on demand, on schedule, or automatically. | `data_profiler_agent.py` | brightbot, platform-core, webapp | brightbot #485, #487; platform-core #767, #775; webapp #1120 | Webapp → asset detail → Profiler tab → "Run Profiler"; or Schedules → Add Schedule → Data Profiler. |
| Skills Extension Framework | Pluggable specialist skills for the data agent (SSIS/SSRS diagnostics). | `deep_agent_skills_middleware.py:88` | brightbot | #747, #800, #823 +more | Ask the analyst agent an SSIS/SSRS troubleshooting question — the skill auto-loads. |
| Live Chat Token Streaming | Chat replies stream word-by-word instead of appearing all at once. | `live_token_streaming_middleware.py` | brightbot, webapp | brightbot #1000, #1003; webapp #1406, #1407 | Send any BrightAgent chat message — watch the reply stream in. |
| MCP Connectivity Card | Live in-app check of a workspace's MCP connection and tools. | `MCPConnectivityCard.tsx:218` | webapp | #1147, #1157/#1163, #1166, #1173/#1184/#1188 | Webapp → Workspace Settings → MCP (admin-only). |

## Platform Infrastructure

| Feature | One-liner | Trace pointer | Repo | PR(s) | How to use / where to see it |
|---|---|---|---|---|---|
| GraphQL Core on ECS | Main data API moved to an always-on setup behind a CDN. | `graphql_ecs_cutover_stack.py` | platform-core | #1207, #1186, #1191, #1163, #1167, #1169, #1166 | Nothing to click — staging's GraphQL endpoint is just served differently now. |
| Scheduler Webhook Reliability | Finished scheduled jobs reliably report back instead of looking stuck. | `scheduled_agents_routes.py:99` | brightbot, platform-core | brightbot #463, #469, #472, #474; platform-core #759 | Webapp → BrightAgent → Schedules — results now post back reliably. |
| Analytics Health Checks on Real Data | Health Checks page shows real live status, not placeholders. | `ServiceHealthCheck` type | platform-core, webapp | platform-core #732; webapp #1066 | Webapp → Analytics → Health Checks. |
| Local-Dev Seed Data | Realistic sample data for local development. | seed scripts, PR #774 | platform-core, webapp | platform-core #774; webapp #1119 | Engineer runs `localbank-full-boot.sh` against their local Neo4j. |
| AgentCore Migration Plan | Plan to move BrightHive's agents onto AWS's own infrastructure. | spec/doc only | agentic-project-mgmt | #6 (v2 spec) | Not user-facing — read `docs/specs/agentcore-deployment-migration.md` or Jira epic BH-453. |

## Known Discrepancies

Real gaps the trace surfaced between what the docs/release notes claimed and what the code actually does — worth ticketing rather than just noting:

1. **Agent Action Audit Log** — release notes describe a "CloudWatch+DynamoDB dual-write emitter." The shipped code (`brightbot/audit/decorator.py`, commit `006c17b4`, "replaces DynamoDB design") only writes structured JSON to CloudWatch. No DynamoDB write exists.
2. **Signal Catalog** — intended as the single source of truth for alert severity/copy across platform-core, webapp, and slack-server. No CI workflow enforces that the vendored copies stay in sync — only a unit test (`tests/unit/signal-catalog.test.ts`) exists.
3. **Configurable Quality Agent** — counted as a Sprint 13 (June 23 - July 20) delivery, but the shipping PRs (webapp #1136, brightbot #557) actually merged June 9 and June 16, before the sprint's official start. The ticket transitioned Done in-window; the code predates it.
4. **BrightSignals Alert History** (`list_workspace_signals` MCP tool) — no original feature PR could be traced; only a later `develop→staging` promotion PR (#941) references the commit.
5. **PII Masking Enforcement** — core enforcement shipped in-window (#808), but the real hardening passes (#917, #946) merged after Sprint 13 closed — the sprint doc's "still open" framing was directionally correct.

---

*Generated 2026-08-17 by tracing `jira/sprint/{10..15}/SUMMARY.md` and `RELEASE_NOTES.md` against live code in brightbot, brighthive-webapp, brighthive-platform-core, and brightbot-slack-server. Not auto-refreshed — re-run to pick up newer sprints.*
