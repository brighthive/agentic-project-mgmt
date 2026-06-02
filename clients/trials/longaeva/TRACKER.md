# Longaeva — Live Tracker

_Last refreshed **2026-06-02 14:50 UTC** by `make longaeva-tracker`. Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved across refreshes._

> **Phase**: Pre-trial · **Trial dates**: TBD with Grant · **Epic**: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)

---

## 🚨 Blockers

<!-- TRACKER:MANUAL:BEGIN blockers -->

_No active blockers. Add lines in the form: `**🚨 BH-XXX** — short description (raised YYYY-MM-DD by @owner)`._

<!-- TRACKER:MANUAL:END blockers -->

## 🎯 This Week

<!-- TRACKER:MANUAL:BEGIN this-week -->

_Weekly standup output. Update Monday morning with the week's ticket commitments by owner._

<!-- TRACKER:MANUAL:END this-week -->

---

## 📊 Summary

- **3/38** tickets done · 6 in progress · 29 to do
- PRs: 11 merged · 8 ready for review · 2 draft

## 📋 Tickets by status

### 🟡 To Do (21)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-302](https://brighthiveio.atlassian.net/browse/BH-302) | Create a PoC on how we will add infra to support platform notificatio… | Ahmed Elsherbiny | — |
| [BH-454](https://brighthiveio.atlassian.net/browse/BH-454) | Spike: AgentCore region + reference architecture + streaming POC +… | Kuri Chinca | — |
| [BH-504](https://brighthiveio.atlassian.net/browse/BH-504) | spec(quality): workspace-configurable rules — contracts, invariants,… | _unassigned_ | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-506](https://brighthiveio.atlassian.net/browse/BH-506) | feat(brightbot): REST CRUD endpoints for quality rules | _unassigned_ | — |
| [BH-507](https://brighthiveio.atlassian.net/browse/BH-507) | feat(brightbot): quality agent reads rules from library, not LLM regen | _unassigned_ | — |
| [BH-508](https://brighthiveio.atlassian.net/browse/BH-508) | feat(brightbot): per-rule execution fanout and pass rate aggregation | _unassigned_ | — |
| [BH-509](https://brighthiveio.atlassian.net/browse/BH-509) | feat(platform-core): GraphQL types and resolvers for quality rules | _unassigned_ | — |
| [BH-510](https://brighthiveio.atlassian.net/browse/BH-510) | feat(webapp): wire Quality Rules page to live GraphQL plus rule… | _unassigned_ | — |
| [BH-511](https://brighthiveio.atlassian.net/browse/BH-511) | feat(brightbot): seed library of 20 plus quality rule templates | _unassigned_ | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-529](https://brighthiveio.atlassian.net/browse/BH-529) | Configure GitHub Enterprise support in dbt agent PR creation | Kuri Chinca | — |
| [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) | Fix GX output: serialize expectation suite as YAML and commit to… | Kuri Chinca | [🟢 Merged brightbot#486](https://github.com/brighthive/brightbot/pull/486) |
| [BH-532](https://brighthiveio.atlassian.net/browse/BH-532) | Confirm and configure MCP client connectivity to Longaeva's… | Kuri Chinca | — |
| [BH-533](https://brighthiveio.atlassian.net/browse/BH-533) | Provision Longaeva trial workspace and validate end-to-end stack… | Kuri Chinca | — |
| [BH-534](https://brighthiveio.atlassian.net/browse/BH-534) | Build Longaeva context layer — load reference schemas and YAML spec… | Kuri Chinca | — |
| [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) | Execute ingestion POC scenarios (S3, REST API, Snowflake Data Share) | Kuri Chinca | — |
| [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) | Execute semantic view enrollment, MCP validation, and maintenance demo | Kuri Chinca | — |
| [BH-544](https://brighthiveio.atlassian.net/browse/BH-544) | feat(brightbot): governance agent routes to library tool with… | Harbour Wang | — |
| [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) | feat(webapp): replace MOCK_RULES with live qualityRules query;… | Harbour Wang | — |
| [BH-546](https://brighthiveio.atlassian.net/browse/BH-546) | feat(webapp): create/edit drawer with scope selector, asset picker,… | Harbour Wang | — |
| [BH-547](https://brighthiveio.atlassian.net/browse/BH-547) | feat(webapp): activate/deactivate toggle, execution history panel,… | Harbour Wang | — |
| [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) | audit(webapp): confirm Snowflake dropdown + form fields render | Kuri Chinca | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19) |

### 🟢 In Progress (4)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-537](https://brighthiveio.atlassian.net/browse/BH-537) | [CORE] Expose QualityRule types in public GraphQL schema and run… | Harbour Wang | — |
| [BH-538](https://brighthiveio.atlassian.net/browse/BH-538) | [CORE] Implement QualityRule CRUD resolvers and service layer | Harbour Wang | — |
| [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) | feat(core): resolvers + service for quality rule CRUD, status… | Harbour Wang | — |
| [BH-543](https://brighthiveio.atlassian.net/browse/BH-543) | feat(brightbot): add execute_library_quality_rules_tool with… | Harbour Wang | — |

### 🔵 In Review (10)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-505](https://brighthiveio.atlassian.net/browse/BH-505) | feat(brightbot): QualityRuleNode and QualityRuleExecutionNode in… | _unassigned_ | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11)<br>[🟡 Draft brighthive-platform-core#771](https://github.com/brighthive/brighthive-platform-core/pull/771) |
| [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) | Longaeva Partners POC — 14-day pre-trial execution | Kuri Chinca | [🟢 Merged agentic-project-mgmt#17](https://github.com/brighthive/agentic-project-mgmt/pull/17)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) | Add SnowflakeConnection class to warehouse_connections.py and wire… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) | Add Snowflake SQL dialect rules to agent prompts | Kuri Chinca | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) | Build Snowflake semantic view YAML scaffold tool | Kuri Chinca | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#20](https://github.com/brighthive/agentic-project-mgmt/pull/20)<br>[🟡 Draft brightbot#489](https://github.com/brighthive/brightbot/pull/489) |
| [BH-549](https://brighthiveio.atlassian.net/browse/BH-549) | feat(brightbot): warehouse_config-aware Snowflake branch in… | _unassigned_ | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-550](https://brighthiveio.atlassian.net/browse/BH-550) | test(brightbot): tests/unit/test_snowflake_warehouse.py mirror of… | _unassigned_ | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) | feat(platform-core): SnowflakeSourceConfig in OMD ingestion lambda | Kuri Chinca | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) | feat(brightbot): data_profiler Snowflake-specific branches (verify;… | _unassigned_ | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) | refactor(org-cdk): SnowflakeIngestionStack reads workspace_secret_sto… | _unassigned_ | [🔵 Review brighthive-data-organization-cdk#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) |

### ✅ Done (3)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-539](https://brighthiveio.atlassian.net/browse/BH-539) | [CORE] Seed script: 20+ QualityRuleTemplate starter library nodes | Harbour Wang | — |
| [BH-540](https://brighthiveio.atlassian.net/browse/BH-540) | feat(core): add scope/context model to OGM, expose QualityRule… | Harbour Wang | — |
| [BH-542](https://brighthiveio.atlassian.net/browse/BH-542) | feat(core): seed 20+ QualityRuleTemplateNode starters with scope… | Harbour Wang | — |


## ❄️ Snowflake integration (0/9)

| Key | Summary | Status | PR |
|---|---|---|---|
| [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) | Add SnowflakeConnection class to warehouse_connections.py and wire… | Code Review | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) | Add Snowflake SQL dialect rules to agent prompts | Code Review | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) | Build Snowflake semantic view YAML scaffold tool | Needs Refinement | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#20](https://github.com/brighthive/agentic-project-mgmt/pull/20)<br>[🟡 Draft brightbot#489](https://github.com/brighthive/brightbot/pull/489) |
| [BH-549](https://brighthiveio.atlassian.net/browse/BH-549) | feat(brightbot): warehouse_config-aware Snowflake branch in… | Needs Refinement | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-550](https://brighthiveio.atlassian.net/browse/BH-550) | test(brightbot): tests/unit/test_snowflake_warehouse.py mirror of… | Needs Refinement | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) | feat(platform-core): SnowflakeSourceConfig in OMD ingestion lambda | Needs Refinement | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) | audit(webapp): confirm Snowflake dropdown + form fields render | Needs Refinement | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19) |
| [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) | feat(brightbot): data_profiler Snowflake-specific branches (verify;… | Needs Refinement | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) | refactor(org-cdk): SnowflakeIngestionStack reads workspace_secret_sto… | Needs Refinement | [🔵 Review brighthive-data-organization-cdk#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) |

## 🕒 Recent activity (14 days)

- **2026-06-02** · [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) — Code Review · Kuri Chinca
- **2026-06-02** · [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) — Code Review · Kuri Chinca
- **2026-06-02** · [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) — In Progress · Harbour Wang
- **2026-06-02** · [BH-543](https://brighthiveio.atlassian.net/browse/BH-543) — In Progress · Harbour Wang
- **2026-06-02** · [BH-542](https://brighthiveio.atlassian.net/browse/BH-542) — Done · Harbour Wang
- **2026-06-02** · [BH-540](https://brighthiveio.atlassian.net/browse/BH-540) — Done · Harbour Wang
- **2026-06-02** · [BH-539](https://brighthiveio.atlassian.net/browse/BH-539) — Done · Harbour Wang
- **2026-06-02** · [BH-538](https://brighthiveio.atlassian.net/browse/BH-538) — Code Review · Harbour Wang
- **2026-06-02** · [BH-537](https://brighthiveio.atlassian.net/browse/BH-537) — Code Review · Harbour Wang
- **2026-06-01** · [BH-547](https://brighthiveio.atlassian.net/browse/BH-547) — Needs Refinement · Harbour Wang
- **2026-06-01** · [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) — Needs Refinement · Kuri Chinca
- **2026-06-01** · [BH-546](https://brighthiveio.atlassian.net/browse/BH-546) — Needs Refinement · Harbour Wang
- **2026-06-01** · [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) — Needs Refinement · Harbour Wang
- **2026-06-01** · [BH-544](https://brighthiveio.atlassian.net/browse/BH-544) — Needs Refinement · Harbour Wang
- **2026-06-01** · [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) — Needs Refinement · _unassigned_
- **2026-06-01** · [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) — Needs Refinement · _unassigned_
- **2026-06-01** · [BH-550](https://brighthiveio.atlassian.net/browse/BH-550) — Needs Refinement · _unassigned_
- **2026-06-01** · [BH-549](https://brighthiveio.atlassian.net/browse/BH-549) — Needs Refinement · _unassigned_

_(+8 older updates not shown.)_

## 📝 Daily Notes

<!-- TRACKER:MANUAL:BEGIN daily-notes -->

_Filled during the trial — one entry per trial day. Use `### Day N — YYYY-MM-DD` headings._

<!-- TRACKER:MANUAL:END daily-notes -->

## ❓ Open Questions

<!-- TRACKER:MANUAL:BEGIN open-questions -->

_Questions for Grant or for the team. Mark `(Grant)` or `(team)` and date-stamp on resolution._

<!-- TRACKER:MANUAL:END open-questions -->
