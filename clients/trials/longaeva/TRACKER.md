# Longaeva — Live Tracker

_Last refreshed **2026-06-02 19:19 UTC** by `make longaeva-tracker`. Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved._

> **Trial dates**: TBD with Grant · **Epic**: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)

---

## 🚨 Blockers

<!-- TRACKER:MANUAL:BEGIN blockers -->

**🚨 BH-529 chain — 7 P0 fixes must merge before trial** (raised 2026-06-02 by @kuri)
- PR [#778](https://github.com/brighthive/brighthive-platform-core/pull/778) + [#490](https://github.com/brighthive/brightbot/pull/490) reviewed → CHANGES_REQUESTED
- Multi-tenant data exfil bug (BH-559), PAT-leak-on-redirect (BH-560), security headline FALSE on PR #490 because PyGithub still in pyproject + 4 modules (BH-562), JWT leak in `bh_platform_api.py:130` (BH-563)
- Full chain: BH-559, BH-560, BH-561, BH-562, BH-563, BH-564, BH-565
- Spec: [github-enterprise-host-config.md §11](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/github-enterprise-host-config.md#11-implementation-gaps-as-of-2026-06-02)
- Smoke test plan: [`artifacts/ghe-smoke-test-plan.md`](./artifacts/ghe-smoke-test-plan.md)

**⏳ Awaiting Grant** — GHE host URL, sandbox PAT, TLS chain confirmation (raised 2026-06-02 by @kuri)
- Without these, smoke test Phase B cannot run → trial cannot start

<!-- TRACKER:MANUAL:END blockers -->

## 🎯 This Week

<!-- TRACKER:MANUAL:BEGIN this-week -->

### Ownership map (locked 2026-06-02)

| Owner | Lane | Active tickets |
|---|---|---|
| **Marwan** | dbt + engineering agent + Snowflake / YAML executions | BH-527, BH-528, BH-529, BH-530, **BH-531** (Atlas YAML), BH-543, BH-544, BH-549, BH-550, BH-553 |
| **Ahmed** | MCP + AWS DevOps + workspace provisioning | BH-532 (MCP client), BH-533 (provisioning), BH-534 (context layer), BH-551 (OMD ingestion), BH-554 (org-CDK ingestion stack) |
| **Harbour** | Quality agent — granular per-asset/group + configurable + notifications | BH-504, BH-505, BH-506, BH-507, BH-508, BH-509, BH-510, BH-511, BH-537, BH-538, BH-541, BH-545, BH-546, BH-547, **BH-557** (quality→BrightSignals wiring), **BH-558** (webapp side-menu push-notifs live) |
| **Kuri** | Trial driver + cross-cutting | BH-535 (ingestion exec), BH-536 (semantic enroll exec), BH-552 (webapp Snowflake audit) |

### This week's commits

- **Marwan**: address PR #490 review — finish PyGithub removal (BH-562), redact JWT logs (BH-563), Pydantic + DI (BH-564), author migration guide (BH-565); ship Snowflake bundle (#488 → ready); BH-530 GX YAML output
- **Kuri**: address PR #778 review — workspaceId from JWT (BH-559), redirect-strip + token scrub (BH-560), truncated flag + structured errors (BH-561); push Grant for GHE PAT + TLS chain
- **Ahmed**: ship #777 (OMD SnowflakeSourceConfig) and #156 (org-CDK migration); pick up BH-570 (CA bundle) when triggered; start BH-532 MCP client config
- **Harbour**: BH-541 in progress; pull BH-557 + BH-558 next; pair with BrightSignals architecture doc

### Pre-trial GHE readiness gate

Phase A1 (CI smoke) → A2 (manual sandbox) → B (Longaeva sandbox) → C (Day 3 prod). See [`artifacts/ghe-smoke-test-plan.md`](./artifacts/ghe-smoke-test-plan.md). Phase A blocked on BH-559..565 merge; Phase B blocked on Grant creds.

<!-- TRACKER:MANUAL:END this-week -->

---

## 🗓️ Day-by-day — what to expect

_Auto-fills as linked tickets close and PRs merge. Manual rows (no linked items) are flipped by hand once the outcome lands._

### Pre-trial — Snowflake foundation must be merged (0/11)

_All Phase 1 Snowflake integration PRs land before Day 1. Without these, brightbot can't query Snowflake and the trial can't run §1 ingestion or §2 semantic-view enrollment._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | Pre-trial | brightbot Layer 5 (SnowflakeConnection + dialect + tests) merged | [BH-527](https://brighthiveio.atlassian.net/browse/BH-527), [BH-528](https://brighthiveio.atlassian.net/browse/BH-528), [BH-549](https://brighthiveio.atlassian.net/browse/BH-549), [BH-550](https://brighthiveio.atlassian.net/browse/BH-550), [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) |
| 🔲 | Pre-trial | Atlas semantic-view YAML scaffold tool merged (BH-531) | [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) |
| 🔲 | Pre-trial | OMD ingestion lambda Layer 3 (SnowflakeSourceConfig) merged | [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) |
| 🔲 | Pre-trial | Org-CDK ingestion stack reads workspace_secret_store | [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) |
| 🔲 | Pre-trial | Webapp Snowflake form audit signed off | [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) |
| 🔲 | Pre-trial | BH-529 GitHub proxy + 7 P0 follow-ups merged (PyGithub fully removed, tenant isolation fixed, redirect-strip fixed) | [BH-529](https://brighthiveio.atlassian.net/browse/BH-529), [BH-559](https://brighthiveio.atlassian.net/browse/BH-559), [BH-560](https://brighthiveio.atlassian.net/browse/BH-560), [BH-561](https://brighthiveio.atlassian.net/browse/BH-561), [BH-562](https://brighthiveio.atlassian.net/browse/BH-562), [BH-563](https://brighthiveio.atlassian.net/browse/BH-563), [BH-564](https://brighthiveio.atlassian.net/browse/BH-564), [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) |
| 🔲 | Pre-trial | GHE smoke test — dbt agent opens a PR against a BrightHive-internal GHE sandbox before Longaeva access | [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) |
| ⬜ | Pre-trial | Longaeva GHE PAT + host URL + TLS chain confirmed by Grant | _manual_ |
| 🔲 | Pre-trial | PR template compliance — dbt agent reads .github/pull_request_template.md | [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) |
| 🔲 | Pre-trial | GX output: serialize as YAML to repo branch (not Markdown to S3) | [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) |
| 🔲 | Pre-trial | Quality agent CRUD resolvers + service merged | [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) |
| 🔲 | Pre-trial | Quality → BrightSignals wiring + webapp side-menu live | [BH-557](https://brighthiveio.atlassian.net/browse/BH-557), [BH-558](https://brighthiveio.atlassian.net/browse/BH-558) |
| ⬜ | Pre-trial | Trial start date confirmed with Grant | _manual_ |
| ⬜ | Pre-trial | Trial-user list confirmed (1-2 DEs + 1-2 DSs) | _manual_ |

### Days 1-5 — Provision + context layer (0/3)

_Stack connectivity validated; reference schemas + Atlas YAML spec loaded into the workspace KG. Joint working session on Day 3._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Day 1 | Use cases + success criteria confirmed (joint kickoff) | _manual_ |
| ⬜ | Day 2 | Longaeva provisions stack access (Snowflake, S3, dbt, Dagster, GHE, MCP) | _manual_ |
| 🔲 | Day 3 | Workspace provisioned + Snowflake connectivity validated | [BH-533](https://brighthiveio.atlassian.net/browse/BH-533) |
| 🔲 | Day 3 | MCP client config to Longaeva's MCP server confirmed | [BH-532](https://brighthiveio.atlassian.net/browse/BH-532) |
| 🔲 | Day 4 | Context layer built — reference schemas + Atlas YAML spec in KG | [BH-534](https://brighthiveio.atlassian.net/browse/BH-534) |
| ⬜ | Day 5 | Environment mapping validated (joint review) | _manual_ |

### Days 6-10 — Trial executions (0/6)

_Run the three ingestion scenarios + semantic-view enrollment + MCP validation. This is where the platform shows up._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | Day 6-8 | Ingestion: S3 vendor bucket scenario merge-ready | [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) |
| 🔲 | Day 6-8 | Ingestion: REST API scenario merge-ready | [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) |
| 🔲 | Day 6-8 | Ingestion: Snowflake Data Share scenario merge-ready | [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) |
| 🔲 | Day 8-10 | Semantic view scaffolded for ≥1 Silver table (Atlas YAML) | [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) |
| 🔲 | Day 8-10 | Reference-data binding (LEI/FIGI / fiscal calendar / geo) auto-detected | [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) |
| 🔲 | Day 8-10 | MCP validation: enrolled view queryable through Longaeva's MCP | [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) |

### Days 11-14 — Maintenance demo + final evaluation (0/1)

_Self-healing PRs, longitudinal anomaly signals, Slack triage. Then joint scorecard review and commercial next-steps discussion._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Day 11-12 | Self-healing: schema drift → surgical fix PR demonstrated | _manual_ |
| ⬜ | Day 11-12 | Self-healing: missing partition / broken stage / dbt contract fail | _manual_ |
| ⬜ | Day 11-12 | Longitudinal anomaly: ≥1 of {row-count / cardinality / skew / nulls} | _manual_ |
| 🔲 | Day 11-12 | Slack alerts: triage-ready (dataset + severity + PR/run link) | [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) |
| ⬜ | Day 11-12 | Slack bidirectional: @brightagent answers pipeline-state question | _manual_ |
| ⬜ | Day 13 | Final scorecard filled (17 success criteria scored) | _manual_ |
| ⬜ | Day 14 | Commercial next-steps discussion scheduled | _manual_ |

### Post-trial — followups (0/0)

_Things tracked but not gated by the 14-day window. Update as the decision lands._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Post | Decision recorded (Won / Lost / Extended) with rationale | _manual_ |
| ⬜ | Post | JWT/key-pair Snowflake auth (Phase 2) | _manual_ |


## 🏁 Who's done what

**Lanes**
- **Marwan Samih** — dbt + engineering agent + Snowflake / YAML executions
- **Ahmed Elsherbiny** — MCP + AWS DevOps + workspace provisioning
- **Harbour Wang** — Quality agent — granular per-asset/group + configurable + notifications
- **Kuri Chinca** — Trial driver + cross-cutting

| Owner | ✅ Done | 🔵 In flight | 🟡 Queued | Last shipped |
|---|---|---|---|---|
| **Harbour Wang** | 3 | 4 | 12 | [BH-542](https://brighthiveio.atlassian.net/browse/BH-542) feat(core): seed 20+ QualityRuleTemplat… |
| **Ahmed Elsherbiny** | 0 | 2 | 4 | — |
| **Kuri Chinca** | 0 | 3 | 15 | — |
| **Marwan Samih** | 0 | 6 | 2 | — |
| **_unassigned_** | 0 | 0 | 2 | — |

## 📊 Summary

- **3/53** tickets done · 7 in progress · 43 to do
- PRs: 11 merged · 10 ready for review · 2 draft

## 📋 Tickets by status

### 🟡 To Do (35)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-302](https://brighthiveio.atlassian.net/browse/BH-302) | Create a PoC on how we will add infra to support platform notificatio… | Ahmed Elsherbiny | — |
| [BH-454](https://brighthiveio.atlassian.net/browse/BH-454) | Spike: AgentCore region + reference architecture + streaming POC +… | Kuri Chinca | — |
| [BH-504](https://brighthiveio.atlassian.net/browse/BH-504) | spec(quality): workspace-configurable rules — contracts, invariants,… | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-506](https://brighthiveio.atlassian.net/browse/BH-506) | feat(brightbot): REST CRUD endpoints for quality rules | Harbour Wang | — |
| [BH-507](https://brighthiveio.atlassian.net/browse/BH-507) | feat(brightbot): quality agent reads rules from library, not LLM regen | Harbour Wang | — |
| [BH-508](https://brighthiveio.atlassian.net/browse/BH-508) | feat(brightbot): per-rule execution fanout and pass rate aggregation | Harbour Wang | — |
| [BH-509](https://brighthiveio.atlassian.net/browse/BH-509) | feat(platform-core): GraphQL types and resolvers for quality rules | Harbour Wang | — |
| [BH-510](https://brighthiveio.atlassian.net/browse/BH-510) | feat(webapp): wire Quality Rules page to live GraphQL plus rule… | Harbour Wang | — |
| [BH-511](https://brighthiveio.atlassian.net/browse/BH-511) | feat(brightbot): seed library of 20 plus quality rule templates | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) | Fix GX output: serialize expectation suite as YAML and commit to… | Marwan Samih | [🟢 Merged brightbot#486](https://github.com/brighthive/brightbot/pull/486) |
| [BH-532](https://brighthiveio.atlassian.net/browse/BH-532) | Confirm and configure MCP client connectivity to Longaeva's… | Ahmed Elsherbiny | — |
| [BH-533](https://brighthiveio.atlassian.net/browse/BH-533) | Provision Longaeva trial workspace and validate end-to-end stack… | Ahmed Elsherbiny | — |
| [BH-534](https://brighthiveio.atlassian.net/browse/BH-534) | Build Longaeva context layer — load reference schemas and YAML spec… | Ahmed Elsherbiny | — |
| [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) | Execute ingestion POC scenarios (S3, REST API, Snowflake Data Share) | Kuri Chinca | — |
| [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) | Execute semantic view enrollment, MCP validation, and maintenance demo | Kuri Chinca | — |
| [BH-544](https://brighthiveio.atlassian.net/browse/BH-544) | feat(brightbot): governance agent routes to library tool with… | Marwan Samih | — |
| [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) | feat(webapp): replace MOCK_RULES with live qualityRules query;… | Harbour Wang | — |
| [BH-546](https://brighthiveio.atlassian.net/browse/BH-546) | feat(webapp): create/edit drawer with scope selector, asset picker,… | Harbour Wang | — |
| [BH-547](https://brighthiveio.atlassian.net/browse/BH-547) | feat(webapp): activate/deactivate toggle, execution history panel,… | Harbour Wang | — |
| [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) | audit(webapp): confirm Snowflake dropdown + form fields render | Kuri Chinca | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19) |
| [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) | feat(notifications): wire Quality Agent → BrightSignals end-to-end… | Harbour Wang | — |
| [BH-558](https://brighthiveio.atlassian.net/browse/BH-558) | feat(webapp): wire side-menu push-notifications to live BrightSignals… | Harbour Wang | — |
| [BH-559](https://brighthiveio.atlassian.net/browse/BH-559) | fix(platform-core): derive workspaceId from context.token in… | Kuri Chinca | — |
| [BH-560](https://brighthiveio.atlassian.net/browse/BH-560) | fix(platform-core): disable redirect-following + scrub PAT from… | Kuri Chinca | — |
| [BH-561](https://brighthiveio.atlassian.net/browse/BH-561) | feat(platform-core): truncated flag + structured errorCode/httpStatus… | Kuri Chinca | — |
| [BH-562](https://brighthiveio.atlassian.net/browse/BH-562) | chore(brightbot): finish PyGithub removal — pyproject + 4 modules +… | Kuri Chinca | — |
| [BH-563](https://brighthiveio.atlassian.net/browse/BH-563) | fix(brightbot): redact Authorization header + payload from… | Kuri Chinca | — |
| [BH-564](https://brighthiveio.atlassian.net/browse/BH-564) | refactor(brightbot): Pydantic responses + DI for PlatformAPISession… | Kuri Chinca | — |
| [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) | docs(brightbot): author BRIGHTBOT-GITHUB-PROXY-GUIDE.md (currently… | Kuri Chinca | — |
| [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) | feat(brightbot): dbt-agent reads pull_request_template.md +… | Kuri Chinca | — |
| [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) | test(platform-core): property-based tests for parseGitHubRepoUrl +… | Kuri Chinca | — |
| [BH-568](https://brighthiveio.atlassian.net/browse/BH-568) | chore(brightbot): migrate non-dbt agents off PyGithub (super_agent,… | Kuri Chinca | — |
| [BH-569](https://brighthiveio.atlassian.net/browse/BH-569) | feat(github-proxy): GitHub App installation flow — replace PAT for… | Kuri Chinca | — |
| [BH-570](https://brighthiveio.atlassian.net/browse/BH-570) | feat(platform-core): self-signed CA bundle support for GHE Server… | _unassigned_ | — |
| [BH-571](https://brighthiveio.atlassian.net/browse/BH-571) | feat(platform-core): per-host rate-limit metrics + adaptive backoff… | _unassigned_ | — |

### 🟢 In Progress (4)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-537](https://brighthiveio.atlassian.net/browse/BH-537) | [CORE] Expose QualityRule types in public GraphQL schema and run… | Harbour Wang | — |
| [BH-538](https://brighthiveio.atlassian.net/browse/BH-538) | [CORE] Implement QualityRule CRUD resolvers and service layer | Harbour Wang | — |
| [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) | feat(core): resolvers + service for quality rule CRUD, status… | Harbour Wang | — |
| [BH-543](https://brighthiveio.atlassian.net/browse/BH-543) | feat(brightbot): add execute_library_quality_rules_tool with… | Marwan Samih | — |

### 🔵 In Review (11)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-505](https://brighthiveio.atlassian.net/browse/BH-505) | feat(brightbot): QualityRuleNode and QualityRuleExecutionNode in… | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11)<br>[🟡 Draft brighthive-platform-core#771](https://github.com/brighthive/brighthive-platform-core/pull/771) |
| [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) | Longaeva Partners POC — 14-day pre-trial execution | Kuri Chinca | [🟢 Merged agentic-project-mgmt#17](https://github.com/brighthive/agentic-project-mgmt/pull/17)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) | Add SnowflakeConnection class to warehouse_connections.py and wire… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) | Add Snowflake SQL dialect rules to agent prompts | Kuri Chinca | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-529](https://brighthiveio.atlassian.net/browse/BH-529) | feat(dbt-agent): proxy all GitHub ops through Platform Core with… | Marwan Samih | [🔵 Review brightbot#490](https://github.com/brighthive/brightbot/pull/490)<br>[🔵 Review brighthive-platform-core#778](https://github.com/brighthive/brighthive-platform-core/pull/778) |
| [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) | Build Snowflake semantic view YAML scaffold tool | Marwan Samih | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#20](https://github.com/brighthive/agentic-project-mgmt/pull/20)<br>[🟡 Draft brightbot#489](https://github.com/brighthive/brightbot/pull/489) |
| [BH-549](https://brighthiveio.atlassian.net/browse/BH-549) | feat(brightbot): warehouse_config-aware Snowflake branch in… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-550](https://brighthiveio.atlassian.net/browse/BH-550) | test(brightbot): tests/unit/test_snowflake_warehouse.py mirror of… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) | feat(platform-core): SnowflakeSourceConfig in OMD ingestion lambda | Ahmed Elsherbiny | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) | feat(brightbot): data_profiler Snowflake-specific branches (verify;… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) | refactor(org-cdk): SnowflakeIngestionStack reads workspace_secret_sto… | Ahmed Elsherbiny | [🔵 Review brighthive-data-organization-cdk#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) |

### ✅ Done (3)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-539](https://brighthiveio.atlassian.net/browse/BH-539) | [CORE] Seed script: 20+ QualityRuleTemplate starter library nodes | Harbour Wang | — |
| [BH-540](https://brighthiveio.atlassian.net/browse/BH-540) | feat(core): add scope/context model to OGM, expose QualityRule… | Harbour Wang | — |
| [BH-542](https://brighthiveio.atlassian.net/browse/BH-542) | feat(core): seed 20+ QualityRuleTemplateNode starters with scope… | Harbour Wang | — |


## 🕒 Recent activity (14 days)

- **2026-06-02** · [BH-571](https://brighthiveio.atlassian.net/browse/BH-571) — Needs Refinement · _unassigned_
- **2026-06-02** · [BH-570](https://brighthiveio.atlassian.net/browse/BH-570) — Needs Refinement · _unassigned_
- **2026-06-02** · [BH-569](https://brighthiveio.atlassian.net/browse/BH-569) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-568](https://brighthiveio.atlassian.net/browse/BH-568) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-564](https://brighthiveio.atlassian.net/browse/BH-564) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-563](https://brighthiveio.atlassian.net/browse/BH-563) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-562](https://brighthiveio.atlassian.net/browse/BH-562) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-561](https://brighthiveio.atlassian.net/browse/BH-561) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-560](https://brighthiveio.atlassian.net/browse/BH-560) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-559](https://brighthiveio.atlassian.net/browse/BH-559) — Needs Refinement · Kuri Chinca
- **2026-06-02** · [BH-529](https://brighthiveio.atlassian.net/browse/BH-529) — Code Review · Marwan Samih
- **2026-06-02** · [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) — Code Review · Kuri Chinca
- **2026-06-02** · [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) — Code Review · Kuri Chinca
- **2026-06-02** · [BH-558](https://brighthiveio.atlassian.net/browse/BH-558) — Needs Refinement · Harbour Wang
- **2026-06-02** · [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) — Needs Refinement · Harbour Wang
- **2026-06-02** · [BH-511](https://brighthiveio.atlassian.net/browse/BH-511) — Needs Refinement · Harbour Wang
- **2026-06-02** · [BH-510](https://brighthiveio.atlassian.net/browse/BH-510) — Needs Refinement · Harbour Wang

_(+31 older updates not shown.)_

## 📝 Daily Notes

<!-- TRACKER:MANUAL:BEGIN daily-notes -->

_Filled during the trial — one entry per trial day. Use `### Day N — YYYY-MM-DD` headings._

<!-- TRACKER:MANUAL:END daily-notes -->

## ❓ Open Questions

<!-- TRACKER:MANUAL:BEGIN open-questions -->

| # | Question | For | Raised | Owner |
|---|---|---|---|---|
| 1 | Confirm exact June trial start date | Grant | 2026-05-29 | Kuri |
| 2 | Trial-user list — which 1-2 DEs + 1-2 DSs join Grant? | Grant | 2026-05-29 | Kuri |
| 3 | Atlas SDK strip rule — does it run on the Atlas side, or do we strip `atlas:*` keys before commit? | Grant | 2026-06-01 | Marwan |
| 4 | Are `metric_type` / `growth_type` enumerations bounded beyond `Feature` / `Level`? | Grant | 2026-06-01 | Marwan |
| 5 | Will Longaeva adopt Airbyte-managed S3 ingestion, or is the Snowflake external-stage pattern non-negotiable? | Grant | 2026-06-01 | Marwan |
| 6 | Does Longaeva's MCP server use the standard MCP protocol? | Grant | 2026-06-01 | Ahmed |
| 7 | Multi-rule failure on a single quality run — N Slack messages or 1 grouped? | team | 2026-06-02 | Harbour |

<!-- TRACKER:MANUAL:END open-questions -->
