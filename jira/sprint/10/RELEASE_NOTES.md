# Sprint 10 — Release Notes (Technical)

**Period**: 2026-05-05 → 2026-05-15 (11 days, unofficial)
**Release Date**: May 15, 2026
**Status**: Closed (date-range release, no Jira sprint object)

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Feature PRs merged | 34 |
| Total PRs (incl. build promotions + reverts) | 58 |
| Repos touched | 5 |
| Lines added | 161,890 |
| Lines removed | 84,540 |
| Lines changed total | 246,430 |
| Contributors | 4 (Kuri, Marwan, Harbour, Ahmed) |

> Note: Jira is not used as the source of truth at BrightHive. Sprint health is measured by shipped PRs.

---

## Major Capabilities Shipped

### 1. AgentCore Migration Epic (BH-453)
Spec v2 written and merged after 4-agent review (Solutions Architect + DevOps + AWS Best-Practices + BrightHive-AWS). 23-ticket child plan created in Jira covering: spike, brightbot entrypoints, DynamoDB checkpointer, langsmith/Mem0AI removal, http/app.py rewrite, AgentCore CDK stack in platform-core, MCP Fargate stack, CI/CD pattern matching platform-core, salted-hash canary, BFF endpoint resolution, UAT statistical gate, cost observability, decommission, migration shim, Cognito pre-token Lambda, KB-ID resolver, trace propagation, rollback gameday, runbook, DR plan, load/soak test, VPC egress lockdown, drift detection.

- agentic-project-mgmt PR [#6](https://github.com/brighthive/agentic-project-mgmt/pull/6) — `docs(BH-453): AgentCore migration spec v2` (Kuri)
- Jira: [BH-453](https://brighthiveio.atlassian.net/browse/BH-453) + 23 child tickets BH-454..476

### 2. BrightStudio Webapp Information Architecture
Major navigation + section overhaul. New "The Hive" hub, Governance section (quality/access/audit), Notifications Inbox, and an 8-section navigation redistribution. Asset detail gained Profiler tab + Raw JSON view.

- webapp PR [#1098](https://github.com/brighthive/brighthive-webapp/pull/1098) — `feat(pages): The Hive + Governance + Notifications Inbox` (Kuri, +5309/-0)
- webapp PR [#1097](https://github.com/brighthive/brighthive-webapp/pull/1097) — `feat(signals): Bright Signals unified activity drawer (BH-376)` (Kuri, +675/-78)
- webapp PR [#1091](https://github.com/brighthive/brighthive-webapp/pull/1091) — `feat(nav): navigation restructure — clean sections (BH-376)` (Kuri)
- webapp PR [#1087](https://github.com/brighthive/brighthive-webapp/pull/1087) — `feat(nav): redistribute pages into 8 clean sections (BH-376)` (Kuri, +4261/-970)
- webapp PR [#1085](https://github.com/brighthive/brighthive-webapp/pull/1085) — `feat(asset-detail): Profiler tab + Raw JSON view, QC hardening` (Kuri)

### 3. BrightSignals — Notifications Spec + Unified Drawer
Notifications schema grounded in real BrightHive arch (BH-409) landed alongside the unified activity drawer in webapp.

- webapp PR [#1088](https://github.com/brighthive/brighthive-webapp/pull/1088) — `docs(spec): notifications schema grounded in real BrightHive arch (BH-409)` (Kuri, +4124/-580)
- webapp PR [#1097](https://github.com/brighthive/brighthive-webapp/pull/1097) — Bright Signals drawer

### 4. dbt Multi-Repo + Secrets Manager Credentials
Large dbt enhancement enabling multi-repo preview. dbt Cloud credentials moved into AWS Secrets Manager. Session-scoped GitHub repo settings in BrightAgent.

- brightbot PR [#470](https://github.com/brighthive/brightbot/pull/470) — `Dbt enhancement` (Marwan, +11990/-3413)
- brightbot PR [#478](https://github.com/brighthive/brightbot/pull/478) — `Feat/dbt multi repo preview` (Marwan)
- platform-core PR [#768](https://github.com/brighthive/brighthive-platform-core/pull/768) — `Store dbt Cloud transformation credentials in Secrets Manager` (Marwan, +1960)
- webapp PR [#1089](https://github.com/brighthive/brighthive-webapp/pull/1089) — `feat(brightagent): dbt GitHub repo session settings` (Marwan)
- platform-core PR [#761](https://github.com/brighthive/brighthive-platform-core/pull/761) — `fix: support re-enabling disabled GitHub repos` (Marwan)

### 5. Scheduler Webhook Hardening
Multiple fixes stabilizing the Sprint 9 scheduler MVP. State now returned to clients; webhook payloads corrected; task graph updated for results; langgraph webhook wiring fixed.

- brightbot PR [#463](https://github.com/brighthive/brightbot/pull/463) — `fix(scheduler): Scheduler webhook fix` (Harbour)
- brightbot PR [#469](https://github.com/brighthive/brightbot/pull/469) — `fix(scheduler): Fix langgraph webhook` (Harbour)
- brightbot PR [#472](https://github.com/brighthive/brightbot/pull/472) — `fix(scheduler): Add payload fixes` (Harbour)
- brightbot PR [#474](https://github.com/brighthive/brightbot/pull/474) — `feat(scheduler): Update task graph for results` (Harbour)
- platform-core PR [#759](https://github.com/brighthive/brighthive-platform-core/pull/759) — `feat(scheduler): Made task stateful to return results` (Harbour)

### 6. Analytics — Health Checks Wired to Real GraphQL Data (BH-359)
ServiceHealthCheck GraphQL type + resolver landed in platform-core; webapp Health Checks page now reads real data.

- platform-core PR [#732](https://github.com/brighthive/brighthive-platform-core/pull/732) — `feat(analytics): ServiceHealthCheck type and resolver (BH-359)` (Kuri)
- webapp PR [#1066](https://github.com/brighthive/brighthive-webapp/pull/1066) — `feat(analytics): wire Health Checks page to real GraphQL data (BH-359)` (Kuri)

### 7. Local-Dev Quality Check Stack
LocalStack-based local dev stack for the quality_check subagent (Postgres + LocalStack). Lets engineers iterate on AWS-adjacent behavior without burning Bedrock or RDS quota.

- brightbot PR [#466](https://github.com/brighthive/brightbot/pull/466) — `feat(local-dev): full quality_check stack with Postgres + LocalStack` (Kuri, +2521)
- platform-core PR [#754](https://github.com/brighthive/brighthive-platform-core/pull/754) — `chore(seeds): align profiler executions with v2 contract` (Kuri)
- platform-core PR [#760](https://github.com/brighthive/brighthive-platform-core/pull/760) — `chore(port): local dev server on :4040` (Kuri)

### 8. Sprint 9 Close + Bedrock Migration Diary Catch-Up
Sprint 9 v2 release artifacts (post May-4 cutoff with 10 retro tickets) committed. 6 Bedrock weekly diary docs (Weeks 6-11) published to AWS-shared Google Drive folder.

- agentic-project-mgmt PR [#4](https://github.com/brighthive/agentic-project-mgmt/pull/4) — `docs(sprint-9): finalize release artifacts and board report` (Kuri, +1094/-322)
- agentic-project-mgmt PR [#5](https://github.com/brighthive/agentic-project-mgmt/pull/5) — `docs(claude): reference Claude Code via Bedrock dev tooling` (Kuri)
- Bedrock diary: [CoBuild AWS Drive folder](https://drive.google.com/drive/folders/1fvLR8a160KK4-wuDk4JW0WIdgiqTxRV2) — Weeks 6-11

### 9. Production Stability + Quality
- brightbot PR [#483](https://github.com/brighthive/brightbot/pull/483) (May 15 hotfix) — `Hotfix prod brightagent s3 streaming mem0` (Marwan)
- brightbot PR [#476](https://github.com/brighthive/brightbot/pull/476) — `Fix/langgraph state channel reducers` (Marwan)
- webapp PR [#1103](https://github.com/brighthive/brighthive-webapp/pull/1103) (May 15) — `fix(BrightAgent): keep AG Grid aria description out of sidebar layout` (Marwan)
- webapp PR [#1096](https://github.com/brighthive/brighthive-webapp/pull/1096) — `fix(UI): Fixed UI bugs and permission bugs` (Harbour)
- platform-core PR [#764](https://github.com/brighthive/brighthive-platform-core/pull/764) — `fix(projects): Fixed project retrieval and overhead` (Harbour)
- platform-core PR [#757](https://github.com/brighthive/brighthive-platform-core/pull/757) — `Hotfix duplicate dataasset + postdeploy script` (Ahmed)
- platform-core PR [#758](https://github.com/brighthive/brighthive-platform-core/pull/758) — `enhanced OMD deploy configs with VPC and security groups` (Ahmed)
- platform-core PR [#756](https://github.com/brighthive/brighthive-platform-core/pull/756) — `fix: airbyte destination retrieval fallback` (Ahmed)
- data-org-cdk PR [#155](https://github.com/brighthive/brighthive-data-organization-cdk/pull/155) — `Fix ingestion stack delete type` (Ahmed)

### 10. Production Deploys (5/12)
- brightbot PR [#480](https://github.com/brighthive/brightbot/pull/480) — Staging => Production (5/12/2026) (Marwan, +27785/-3097)
- brightbot PR [#481](https://github.com/brighthive/brightbot/pull/481) — Revert "Staging => Production (5/12/2026)" (Marwan, -27785)
- brightbot PR [#482](https://github.com/brighthive/brightbot/pull/482) — Revert "Revert" — re-applied (Marwan, +27785)
- platform-core PR [#763](https://github.com/brighthive/brighthive-platform-core/pull/763) — Staging => production (Ahmed, +16562/-697)
- webapp PR [#1101](https://github.com/brighthive/brighthive-webapp/pull/1101) — Staging => Production (Marwan, +93638/-93632)

---

## Repository Activity

| Repo | PRs | Feature | Promotion | Lines (added) | Lines (removed) |
|------|-----|---------|-----------|---------------|-----------------|
| brightbot | 21 | 9 | 5 (+7 git-history/revert) | ~50,000 | ~32,000 |
| brighthive-webapp | 17 | 11 | 6 | ~115,000 | ~95,000 |
| brighthive-platform-core | 15 | 10 | 5 | ~21,000 | ~1,500 |
| brighthive-data-organization-cdk | 2 | 1 | 1 | 14 | 14 |
| agentic-project-mgmt | 3 | 3 | 0 | 1,383 | 322 |

---

## Tickets Resolved This Sprint

- [BH-500](https://brighthiveio.atlassian.net/browse/BH-500) — chore(webapp): open PR + land drchinca/BH-00/use-run-agent — workspace_id + data_profiler_agent in useRunAgent (Kuri, 5/12)

---

## Tickets Created This Sprint

**AgentCore migration epic family** (24 tickets): BH-453 (epic) + BH-454..476 (children).
**Profiler agent family** (5 tickets): BH-498..502.
**UAT + sandbox + routing bugs** (BH-477..490): 14 tickets — local subprocess sandbox, OTel GenAI spans on code execution, UAT scenario runner, routing bugs (chart-creation, top-N, SQL injection), SQL generation bugs (asset UUID, missing ORDER BY, empty SQL, date-filter streaming error), redshiftTableName seed bug, chart_kind UAT assertion gap.
**Settings overhaul** (BH-491..496): 6 tickets — Phase 1 critical bugs through Phase 5 UX polish.
**Webapp polish** (BH-495, BH-497): 2 tickets — Coming-Soon preview states, BrightAgent Session Error masking.

---

## Links

- 📋 [Sprint 10 SUMMARY.md](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/SUMMARY.md)
- 📣 [Sprint 10 MARKETING_RELEASE_NOTES.md](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/MARKETING_RELEASE_NOTES.md)
- 📊 [Sprint 10 VALIDATION_REPORT.md](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/VALIDATION_REPORT.md)
- 🎯 [Jira Board 152](https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152)
- 🔥 [AgentCore Epic BH-453](https://brighthiveio.atlassian.net/browse/BH-453)
