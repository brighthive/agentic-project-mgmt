# Sprint 12 Release Notes — Auth, MCP & BrightSignals
**Period**: June 13–23, 2026 | **Repos**: 7 | **PRs**: 223 feature/fix (299 total)

---

## Summary

| Metric | Value |
|--------|-------|
| Feature/Fix PRs merged | 223 |
| Lines changed | +67,654 / −12,111 |
| Repos touched | 7 |
| Tickets in scope | ~75 |
| Tickets Done | 18 |
| Tickets retroactively created | 27 (BH-713–739) |

---

## Completed Tickets

### BrightSignals (BH-409)
- **BH-713** — SSE push delivery + end-to-end observability in slack-server
- **BH-714** — CloudWatch alarms + on-call runbook + monitoring infra
- **BH-715** — Notifications MVP cross-repo (brightbot + platform-core + webapp)

### Audit Trail (BH-695)
- **BH-696** — AuditEvent dataclass + ActionClass/OutcomeStatus enums + AuditEmitter Protocol
- **BH-697** — Fix session_info gap — persist user_id + user_email in initialization_middleware
- **BH-698** — @audit_action decorator with STARTED/SUCCESS/FAILURE/CANCELLED emission
- **BH-699** — CloudWatchDynamoDBAuditEmitter — dual-write production implementation
- **BH-700** — IaC for audit DynamoDB + WORM CloudWatch log group (subsequently cleaned up)
- **BH-701** — Instrument 6 engineering agent mutation tools with @audit_action
- **BH-702** — Citation chain carrier — propagate retrieval node IDs into AuditCitation
- **BH-704** — Integration tests — moto-backed AWS DynamoDB + CloudWatch

### Auth & SSO (BH-115)
- **BH-675** — Webapp "Log in with Okta" PKCE callback route
- **BH-674** — Federated SSO resolver-side JIT provisioning into Neo4j

### Longaeva PoC — GC-12 Longitudinal Monitoring (BH-601)
- **BH-668** — MetricSnapshotNode + AnomalyEventNode persistence (platform-core)
- **BH-669** — Longitudinal monitoring as quality-agent capability node (brightbot)
- **BH-671** — Analyst read path for AnomalyEventNode
- **BH-672** — longitudinal_anomaly QualityRule type (platform-core + webapp editor)

### Quality & Catalog
- **BH-666** — previewAvailable + profilerAvailable health indicators in catalog grid
- **BH-667** — Inline tag removal, overflow popover, bulk tag dialog, tag search fix
- **BH-683** — Engine-agnostic data asset preview for BYOW (Snowflake/Redshift/BigQuery)
- **BH-687** — Fix cooldown returning 503 on OGM failure
- **BH-688** — Warehouse-agnostic quality SQL + workspace picking fix
- **BH-689** — Surface generated SQL in quality-check responses
- **BH-690** — Quality-check FQN fallback when filter fields empty
- **BH-691** — Fail open with clear message on core API timeout during quality check
- **BH-712** — Fix data catalogue search to be case-insensitive
- **BH-677** — Fix slackConnection FORBIDDEN for non-admin roles

### Infrastructure
- **BH-716** — ECS deploy reliability: immutable image digest + desiredCount fight fix
- **BH-717** — ECS infra: INTERRUPTS_ENABLED + IAM hardening + SSRF allowlist split
- **BH-726** — brightagent-mcp dedicated ingress ({env}.brighthive.net)
- **BH-737** — Redshift connector v2.17 SOC compliance + audit IaC cleanup

### Platform Features
- **BH-720** — Thinking indicator: full agent fleet + dbt/MCP/Longaeva tools
- **BH-721** — CORS preflight fixes (7 PRs — MCP session, agent-run, files, scheduled-agents)
- **BH-722** — dbt agent account-specific URLs + scaffold ValidationError fix
- **BH-723** — Snowflake: tableFQN fallback + TIMESTAMP_NTZ overflow + compat pass
- **BH-724** — Multi-workspace auth: thread access, run tagging, X-Workspace-Id header
- **BH-725** — MCP connectivity card: tools/list live + JSON-RPC test + streamable-http parser
- **BH-727** — System admin portal: per-workspace feature flag management
- **BH-728** — Webapp auth: error toasts, logout cookie clear, workspace-switch cascade fix
- **BH-729** — platform-core getWorkspaces OGM 20-cap fix (raw Cypher)
- **BH-730** — OM webhook: OM 1.8 parse + embeddings trigger for scanned tables
- **BH-731** — Lambda 504 fix: remove assertConstraints from request path
- **BH-732** — Superadmin cleanup: dedup assets, purge embeddings, BYOW preview
- **BH-733** — Slack workspace connect: bhagent_api_key provisioning + disconnect cleanup
- **BH-734** — Webapp Slack connect: progress legends + state polling (no 504)
- **BH-735** — RBAC: honest 5-role display + members error state + BbAssistant deprecation
- **BH-736** — Governance: SQL preview for quality rules + Data Drift Monitor flag
- **BH-738** — HITL interrupts: DBT query_selection input surface in Slack
- **BH-739** — Playwright e2e auth suite + Amplify CI fix
- **BH-718** — Slack-server auth: Cognito JWT + x-api-key primary chain
- **BH-719** — OAuth workspace guard: refuse re-point to unprovisioned workspace

---

## Repository Activity

### brightbot
100 PRs merged (53 feature/fix, 47 staging release carriers)

Key PRs:
- [#654–668] Audit trail epic: @audit_action, emitter, citation chain, instrumentation, tests
- [#640] MCP read-only tools: get_workspace_context, get_schema_details, analyze_model_impact
- [#619] Deep-agent: retrieval owns reads + warehouse-type capability gate
- [#625, #630, #635, #647, #676] Snowflake quality suite: tableFQN, compat, TIMESTAMP_NTZ
- [#568] FastMCP at /bh-mcp — dodge LangGraph /mcp shadow
- [#574] Notifications MVP
- [#580] Multi-workspace thread access + run tagging
- [#603–613] CORS preflight hardening (6 targeted fixes)
- [#570, #577] Supervisor JSONDecodeError + superduper_agent alias

### brightbot-slack-server
48 PRs merged (43 feature/fix, 5 staging carriers)

Key PRs:
- [#53, #59, #61, #65, #66, #68, #69, #83] BrightSignals full observability + SSE stack
- [#60, #93, #96, #97, #98] Auth hardening chain (single-flight token, JWT, x-api-key)
- [#63] CloudWatch alarms + on-call runbook
- [#70–82, #88, #95] Thinking indicator — full tool surface + elapsed clock
- [#80, #84, #85] OAuth workspace guard + invariant tests
- [#87, #89, #90, #92] ECS deploy reliability (desiredCount + immutable digest)
- [#62, #55, #56] IAM hardening + S3 allowlist + Pulumi CI sync

### brighthive-platform-core
90 PRs merged (62 feature/fix, 28 staging carriers)

Key PRs:
- [#910] Resolver-side federated SSO Neo4j JIT provisioning (BH-674)
- [#887, #888] brightagent-mcp dedicated ingress
- [#913, #914] Slack disconnect/reconnect + bhagent_api_key provisioning
- [#894, #903, #904] Semantic view: Snowflake→Neo4j sync + cache invalidation + legacy alias
- [#891] MetricSnapshotNode + AnomalyEventNode for GC-12 (BH-668)
- [#896] Slack service account Cognito sub lookup auth
- [#898, #900, #906] NotificationDataStack extraction + pipeline fix
- [#865, #852] 504 timeout fixes (assertConstraints + dataAssets query)
- [#837, #839, #841, #847] OM webhook: embeddings + parse fixes
- [#833, #835] getWorkspaces raw Cypher (OGM cap escape)
- [#866, #869, #871, #818] Superadmin cleanup suite
- [#860] System admin feature flag resolver
- [#908] Static GraphQL SDL emission (fixes prod introspection block BH-686)
- [#912] BYOW preview support

### brighthive-webapp
56 PRs merged (44 feature/fix, 12 staging carriers)

Key PRs:
- [#1207] "Log in with Okta" PKCE callback (BH-675)
- [#1163, #1184, #1188, #1173] MCP connectivity card full stack
- [#1157] Dynamic tools/list surface
- [#1177] Notifications MVP
- [#1161, #1159, #1160, #1154, #1204] System admin portal + feature flags
- [#1205] SQL preview for quality rules
- [#1208, #1199] RBAC surface + role rename
- [#1171] Playwright e2e auth suite
- [#1164, #1158, #1197, #1214] Auth fixes (toasts, logout, forbidden fix)
- [#1209, #1212, #1203] Data catalog + Slack connect UX

### brighthive-admin (2 PRs)
- [#89] Okta SSO federated provisioning gap docs
- [#91] Pivot design note to resolver-side JIT

### brighthive-data-workspace-cdk (2 PRs)
- [#109] Redshift connector v2.17 for SOC compliance

### brighthive-data-organization-cdk (1 PR)
- [#158] Note org /team connector is commented out; AutoPilot is scan path
