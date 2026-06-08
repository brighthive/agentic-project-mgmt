# Longaeva — Live Tracker

_Last refreshed **2026-06-06 01:53 UTC** by `make longaeva-tracker`. Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved._

> **Trial dates**: TBD with Grant · **Epic**: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)

---

## 🚨 Blockers

<!-- TRACKER:MANUAL:BEGIN blockers -->

**🟢 RESOLVED 2026-06-03 — Self-hosting deployment path simplified to Terraform** (Matt → Grant/Sumukh email, 11:29 AM ET)
- After 2026-06-03 call, BrightHive committed to ship a **Terraform module** as the primary supported deployment path for Longaeva, given their cloud team's existing Terraform fluency
- CDK path remains supported as alternative; both produce identical AWS posture (IAM, S3, OMD topology)
- Target: simplified setup doc + working Terraform module delivered to Longaeva by **EOW 2026-06-05**
- Artifact updated: `artifacts/trial-guide-tech-prep.md` — new Path A (Terraform, recommended) + Path B (CDK, alternative); plus uv-based local install section (`uv tool install brighthive`, `uv add` for project-embedded, pip fallback only if policy-blocked)
- New Jira tickets needed: see "🎯 This Week" below

**🚨 BH-529 chain — 7 P0 fixes must merge before trial** (raised 2026-06-02 by @kuri)
- PR [#778](https://github.com/brighthive/brighthive-platform-core/pull/778) + [#490](https://github.com/brighthive/brightbot/pull/490) reviewed → CHANGES_REQUESTED
- Multi-tenant data exfil bug (BH-559), PAT-leak-on-redirect (BH-560), security headline FALSE on PR #490 because PyGithub still in pyproject + 4 modules (BH-562), JWT leak in `bh_platform_api.py:130` (BH-563)
- Full chain: BH-559, BH-560, BH-561, BH-562, BH-563, BH-564, BH-565
- Spec: [github-enterprise-host-config.md §11](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/github-enterprise-host-config.md#11-implementation-gaps-as-of-2026-06-02)
- Smoke test plan: [`artifacts/ghe-smoke-test-plan.md`](./artifacts/ghe-smoke-test-plan.md)

**⏳ Awaiting Grant** — GHE host URL, sandbox PAT, TLS chain confirmation (raised 2026-06-02 by @kuri)
- Without these, smoke test Phase B cannot run → trial cannot start

**⏳ MCP auth workflow — joint conversation with Grant/Sumukh before Grant goes on vacation** (raised 2026-06-03 by Matt via email)
- Open question: agent auth pattern for Longaeva's MCP — device-code OAuth, service token, or mTLS-only?
- Decision needed before vacation window so Sumukh can carry it through; owner: Ahmed (BH-532) + Kuri
- Slot to be confirmed; placeholder: 2026-06-04 60-min joint session

<!-- TRACKER:MANUAL:END blockers -->

## 🎯 This Week

<!-- TRACKER:MANUAL:BEGIN this-week -->

### Where we are right now (snapshot 2026-06-03)

- **Self-hosting deployment**: pivoted CDK → **Terraform-first** per Matt's email; module + simplified setup doc due to Longaeva by EOW 2026-06-05.
- **Local install UX**: `uv tool install brighthive` is now the recommended path; `uv add` for repo-embedded use; pip fallback documented but discouraged. See `artifacts/trial-guide-tech-prep.md` §"Local CLI / SDK Installation".
- **Snowflake foundation**: 4-PR bundle (brightbot #488/#489, platform-core #777, data-org-cdk #156) merge-ready; 168 unit tests green.
- **GHE proxy P0 chain**: 7 fixes (BH-559..565) drafted, in review on PRs #778 + #490; security-hardening continues.
- **Outstanding from Longaeva side**: GHE host URL + PAT + TLS chain (Grant); MCP auth-workflow decision (joint with Grant/Sumukh before Grant's vacation).

### Ownership map (locked 2026-06-02, amended 2026-06-03)

| Owner | Lane | Active tickets |
|---|---|---|
| **Marwan** | dbt + engineering agent + Snowflake / YAML executions | BH-527, BH-528, BH-529, BH-530, **BH-531** (Atlas YAML), BH-543, BH-544, BH-549, BH-550, BH-553 |
| **Ahmed** | MCP + AWS DevOps + workspace provisioning | BH-532 (MCP client), BH-533 (provisioning), BH-534 (context layer), BH-551 (OMD ingestion), BH-554 (org-CDK ingestion stack) |
| **Harbour** | Quality agent — granular per-asset/group + configurable + notifications | BH-504, BH-505, BH-506, BH-507, BH-508, BH-509, BH-510, BH-511, BH-537, BH-538, BH-541, BH-545, BH-546, BH-547, **BH-557** (quality→BrightSignals wiring), **BH-558** (webapp side-menu push-notifs live) |
| **Kuri** | Trial driver + cross-cutting | BH-535 (ingestion exec), BH-536 (semantic enroll exec), BH-552 (webapp Snowflake audit) |

### This week's commits

- **Marwan**: address PR #490 review — finish PyGithub removal (BH-562), redact JWT logs (BH-563), Pydantic + DI (BH-564), author migration guide (BH-565); ship Snowflake bundle (#488 → ready); BH-530 GX YAML output
- **Kuri**: address PR #778 review — workspaceId from JWT (BH-559), redirect-strip + token scrub (BH-560), truncated flag + structured errors (BH-561); push Grant for GHE PAT + TLS chain; drive Terraform-pivot artifact + new tickets below; lead MCP auth-workflow conversation with Grant/Sumukh
- **Ahmed**: ship #777 (OMD SnowflakeSourceConfig) and #156 (org-CDK migration); pick up BH-570 (CA bundle) when triggered; start BH-532 MCP client config; **own the new Terraform module** (`brighthive-longaeva-trial-tf`) with parity to existing CDK stacks
- **Harbour**: BH-541 in progress; pull BH-557 + BH-558 next; pair with BrightSignals architecture doc

### New tickets needed (for 2026-06-03 self-hosting pivot)

> ⚠️ **Ticket numbers TBD — do NOT assume BH-572..575.** Those keys are already taken by the
> in-flight MCP-auth epic (BH-572 remote MCP server [merged], BH-573 Cognito+Okta federation,
> BH-574 Route53/ACM for mcp.brighthive.io, BH-575 Okta IdP runbook). The Terraform/uv work
> below needs **fresh keys** — create under BH-526 and fill in once assigned.

| Proposed (key TBD) | Title | Owner | Due |
|---|---|---|---|
| TF module | feat(infra): Terraform module `brighthive-longaeva-trial-tf` — network/agent/openmetadata sub-modules with parity to CDK stacks | Ahmed | 2026-06-05 EOW |
| Setup doc | docs(longaeva): simplified self-hosting setup doc — Terraform-first, paste-back into Self-hosting Guide | Kuri | 2026-06-05 EOW |
| CLI/uv | feat(cli): publish `brighthive` CLI wheel to PyPI with `uv tool install` smoke-tested; SHA256 manifest for air-gapped mirroring | Marwan | 2026-06-08 |

**Note**: the MCP agent-auth workflow Matt raised is **already ticketed and partly shipped** — BH-572
(remote MCP server + two-layer auth) merged via brightbot #497; BH-573/574/575 are the Cognito+Okta
federation, DNS/TLS, and per-customer Okta runbook follow-ups. The "joint conversation" decision is
which Okta claim-mapping Longaeva uses, not a greenfield design.

### Pre-trial GHE readiness gate

Phase A1 (CI smoke) → A2 (manual sandbox) → B (Longaeva sandbox) → C (Day 3 prod). See [`artifacts/ghe-smoke-test-plan.md`](./artifacts/ghe-smoke-test-plan.md). Phase A blocked on BH-559..565 merge; Phase B blocked on Grant creds.

<!-- TRACKER:MANUAL:END this-week -->

---

## 🗓️ Day-by-day — task / day / progress

_Legend: 🟢 done (ticket closed / PR merged) · 🟡 in progress (PR open or ticket in review) · ⬜ not started · 🔲 awaiting external/manual. Auto-fills as tickets move and PRs merge._

### Pre-trial — Snowflake foundation must be merged (0/13 🟢, 7 🟡)

_All Phase 1 Snowflake integration PRs land before Day 1. Without these, brightbot can't query Snowflake and the trial can't run §1 ingestion or §2 semantic-view enrollment._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🟡 | Pre-trial | brightbot Layer 5 (SnowflakeConnection + dialect + tests) merged | [BH-527](https://brighthiveio.atlassian.net/browse/BH-527), [BH-528](https://brighthiveio.atlassian.net/browse/BH-528), [BH-549](https://brighthiveio.atlassian.net/browse/BH-549), [BH-550](https://brighthiveio.atlassian.net/browse/BH-550), [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) |
| 🟡 | Pre-trial | Atlas semantic-view YAML scaffold tool merged (BH-531) | [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) |
| 🟡 | Pre-trial | OMD ingestion lambda Layer 3 (SnowflakeSourceConfig) merged | [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) |
| 🟡 | Pre-trial | Org-CDK ingestion stack reads workspace_secret_store | [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) |
| ⬜ | Pre-trial | Webapp Snowflake form audit signed off | [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) |
| 🟡 | Pre-trial | BH-529 GitHub proxy + 7 P0 follow-ups merged (PyGithub fully removed, tenant isolation fixed, redirect-strip fixed) | [BH-529](https://brighthiveio.atlassian.net/browse/BH-529), [BH-559](https://brighthiveio.atlassian.net/browse/BH-559), [BH-560](https://brighthiveio.atlassian.net/browse/BH-560), [BH-561](https://brighthiveio.atlassian.net/browse/BH-561), [BH-562](https://brighthiveio.atlassian.net/browse/BH-562), [BH-563](https://brighthiveio.atlassian.net/browse/BH-563), [BH-564](https://brighthiveio.atlassian.net/browse/BH-564), [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) |
| 🟡 | Pre-trial | GHE smoke test — dbt agent opens a PR against a BrightHive-internal GHE sandbox before Longaeva access | [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) |
| 🔲 | Pre-trial | Longaeva GHE PAT + host URL + TLS chain confirmed by Grant | _manual_ |
| ⬜ | Pre-trial | PR template compliance — dbt agent reads .github/pull_request_template.md | [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) |
| ⬜ | Pre-trial | GX output: serialize as YAML to repo branch (not Markdown to S3) | [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) |
| 🟡 | Pre-trial | Quality agent CRUD resolvers + service merged | [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) |
| ⬜ | Pre-trial | Slack: quality/anomaly alerts wired through BrightSignals → channel (triage-ready: dataset + severity + PR/run link) | [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) |
| ⬜ | Pre-trial | Slack: webapp side-menu push-notifications live (BrightSignals feed) | [BH-558](https://brighthiveio.atlassian.net/browse/BH-558) |
| ⬜ | Pre-trial | Slack: bidirectional @brightagent — pipeline-state Q&A + re-run/scaffold trigger | [BH-587](https://brighthiveio.atlassian.net/browse/BH-587) |
| 🔲 | Pre-trial | Slack: @brightagent bot installed in Longaeva workspace + channel created | _manual_ |
| 🔲 | Pre-trial | Trial start date confirmed with Grant | _manual_ |
| 🔲 | Pre-trial | Trial-user list confirmed (1-2 DEs + 1-2 DSs) | _manual_ |

### Days 1-5 — Provision + context layer (0/3 🟢)

_Stack connectivity validated; reference schemas + Atlas YAML spec loaded into the workspace KG. Joint working session on Day 3._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | Day 1 | Use cases + success criteria confirmed (joint kickoff) | _manual_ |
| 🔲 | Day 2 | Longaeva provisions stack access (Snowflake, S3, dbt, Dagster, GHE, MCP) | _manual_ |
| ⬜ | Day 3 | Workspace provisioned + Snowflake connectivity validated | [BH-533](https://brighthiveio.atlassian.net/browse/BH-533) |
| ⬜ | Day 3 | MCP client config to Longaeva's MCP server confirmed | [BH-532](https://brighthiveio.atlassian.net/browse/BH-532) |
| ⬜ | Day 4 | Context layer built — reference schemas + Atlas YAML spec in KG | [BH-534](https://brighthiveio.atlassian.net/browse/BH-534) |
| 🔲 | Day 5 | Environment mapping validated (joint review) | _manual_ |

### Days 6-10 — Trial executions (0/6 🟢)

_Run the three ingestion scenarios + semantic-view enrollment + MCP validation. This is where the platform shows up._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Day 6-8 | Ingestion: S3 vendor bucket scenario merge-ready | [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) |
| ⬜ | Day 6-8 | Ingestion: REST API scenario merge-ready | [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) |
| ⬜ | Day 6-8 | Ingestion: Snowflake Data Share scenario merge-ready | [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) |
| ⬜ | Day 8-10 | Semantic view scaffolded for ≥1 Silver table (Atlas YAML) | [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) |
| ⬜ | Day 8-10 | Reference-data binding (LEI/FIGI / fiscal calendar / geo) auto-detected | [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) |
| ⬜ | Day 8-10 | MCP validation: enrolled view queryable through Longaeva's MCP | [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) |

### Days 11-14 — Maintenance demo + final evaluation (0/2 🟢)

_Self-healing PRs, longitudinal anomaly signals, Slack triage. Then joint scorecard review and commercial next-steps discussion._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | Day 11-12 | Self-healing: schema drift → surgical fix PR demonstrated | _manual_ |
| 🔲 | Day 11-12 | Self-healing: missing partition / broken stage / dbt contract fail | _manual_ |
| 🔲 | Day 11-12 | Longitudinal anomaly: ≥1 of {row-count / cardinality / skew / nulls} | _manual_ |
| ⬜ | Day 11-12 | Slack alerts: triage-ready (dataset + severity + PR/run link) | [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) |
| ⬜ | Day 11-12 | Slack bidirectional: @brightagent answers pipeline-state question + triggers re-run | [BH-587](https://brighthiveio.atlassian.net/browse/BH-587) |
| 🔲 | Day 13 | Final scorecard filled (17 success criteria scored) | _manual_ |
| 🔲 | Day 14 | Commercial next-steps discussion scheduled | _manual_ |

### Post-trial — followups (0/0 🟢)

_Things tracked but not gated by the 14-day window. Update as the decision lands._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | Post | Decision recorded (Won / Lost / Extended) with rationale | _manual_ |
| 🔲 | Post | JWT/key-pair Snowflake auth (Phase 2) | _manual_ |


## 🏁 Who's done what

**Lanes**
- **Marwan Samih** — dbt + engineering agent + Snowflake / YAML executions
- **Ahmed Elsherbiny** — MCP + AWS DevOps + workspace provisioning
- **Harbour Wang** — Quality agent — granular per-asset/group + configurable + notifications
- **Kuri Chinca** — Trial driver + cross-cutting

| Owner | ✅ Done | 🔵 In flight | 🟡 Queued | Last shipped |
|---|---|---|---|---|
| **Harbour Wang** | 6 | 5 | 10 | [BH-509](https://brighthiveio.atlassian.net/browse/BH-509) feat(platform-core): GraphQL types… |
| **Ahmed Elsherbiny** | 0 | 2 | 6 | — |
| **Kuri Chinca** | 0 | 11 | 20 | — |
| **Marwan Samih** | 0 | 6 | 2 | — |
| **_unassigned_** | 0 | 0 | 2 | — |

## 📊 Summary

- **6/70** tickets done · 9 in progress · 55 to do
- PRs: 11 merged · 10 ready for review · 14 draft

## 📋 Tickets by status

### 🟡 To Do (40)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-302](https://brighthiveio.atlassian.net/browse/BH-302) | Create a PoC on how we will add infra to support platform notificatio… | Ahmed Elsherbiny | — |
| [BH-454](https://brighthiveio.atlassian.net/browse/BH-454) | Spike: AgentCore region + reference architecture + streaming POC +… | Kuri Chinca | — |
| [BH-504](https://brighthiveio.atlassian.net/browse/BH-504) | spec(quality): workspace-configurable rules — contracts, invariants,… | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-508](https://brighthiveio.atlassian.net/browse/BH-508) | feat(brightbot): per-rule execution fanout and pass rate aggregation | Harbour Wang | — |
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
| [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) | feat(brightbot): dbt-agent reads pull_request_template.md +… | Kuri Chinca | — |
| [BH-568](https://brighthiveio.atlassian.net/browse/BH-568) | chore(brightbot): migrate non-dbt agents off PyGithub (super_agent,… | Kuri Chinca | — |
| [BH-569](https://brighthiveio.atlassian.net/browse/BH-569) | feat(github-proxy): GitHub App installation flow — replace PAT for… | Kuri Chinca | — |
| [BH-570](https://brighthiveio.atlassian.net/browse/BH-570) | feat(platform-core): self-signed CA bundle support for GHE Server… | _unassigned_ | — |
| [BH-571](https://brighthiveio.atlassian.net/browse/BH-571) | feat(platform-core): per-host rate-limit metrics + adaptive backoff… | _unassigned_ | — |
| [BH-583](https://brighthiveio.atlassian.net/browse/BH-583) | refactor(brightbot): quality check graph cleanup — SQL datasource,… | Harbour Wang | — |
| [BH-584](https://brighthiveio.atlassian.net/browse/BH-584) | feat(infra): Terraform module brighthive-longaeva-trial-tf —… | Ahmed Elsherbiny | — |
| [BH-585](https://brighthiveio.atlassian.net/browse/BH-585) | docs(longaeva): simplified self-hosting setup doc — Terraform-first,… | Kuri Chinca | — |
| [BH-586](https://brighthiveio.atlassian.net/browse/BH-586) | feat(cli): publish brighthive CLI wheel to PyPI; smoke uv tool… | Ahmed Elsherbiny | — |
| [BH-587](https://brighthiveio.atlassian.net/browse/BH-587) | feat(slack): bidirectional @brightagent — pipeline-state Q&A +… | Harbour Wang | — |
| [BH-590](https://brighthiveio.atlassian.net/browse/BH-590) | feat(warehouse): wire Snowflake INFORMATION_SCHEMA introspection… | Kuri Chinca | — |
| [BH-591](https://brighthiveio.atlassian.net/browse/BH-591) | feat(dbt-agent): wire scaffold_atlas_semantic_view_tool into… | Kuri Chinca | — |
| [BH-592](https://brighthiveio.atlassian.net/browse/BH-592) | feat(dbt-agent): generate dbt sources.yml + staging model from… | Kuri Chinca | — |
| [BH-593](https://brighthiveio.atlassian.net/browse/BH-593) | feat(github-proxy): thread GITHUB_BASE_URL through GHE client… | Kuri Chinca | — |
| [BH-594](https://brighthiveio.atlassian.net/browse/BH-594) | feat(dbt-agent): infer dbt schema.yml tests (not_null/unique/accepted… | Kuri Chinca | — |
| [BH-595](https://brighthiveio.atlassian.net/browse/BH-595) | feat(ingestion-agent): generate partitioned REST API ingestion… | Kuri Chinca | — |
| [BH-596](https://brighthiveio.atlassian.net/browse/BH-596) | feat(dbt-agent): Atlas binding grounding validator + verified_query… | Kuri Chinca | — |
| [BH-597](https://brighthiveio.atlassian.net/browse/BH-597) | feat(eval): end-to-end agent eval harness for the 6-step Longaeva… | Kuri Chinca | — |
| [BH-598](https://brighthiveio.atlassian.net/browse/BH-598) | chore(dbt-agent): migrate super_agent + dbt_tools off legacy… | Kuri Chinca | — |
| [BH-599](https://brighthiveio.atlassian.net/browse/BH-599) | feat(self-healing): detect→diagnose→surgical-PR loop for 4 pipeline… | Kuri Chinca | — |
| [BH-600](https://brighthiveio.atlassian.net/browse/BH-600) | feat(quality-agent): longitudinal anomaly monitoring with stateful… | Kuri Chinca | — |
| [BH-601](https://brighthiveio.atlassian.net/browse/BH-601) | Longaeva PoC — 14 Golden Success Paths (GC-1..14) explicit tracking | Kuri Chinca | — |

### 🟢 In Progress (5)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-506](https://brighthiveio.atlassian.net/browse/BH-506) | feat(brightbot): REST CRUD endpoints for quality rules | Harbour Wang | — |
| [BH-507](https://brighthiveio.atlassian.net/browse/BH-507) | feat(brightbot): quality agent reads rules from library, not LLM regen | Harbour Wang | — |
| [BH-537](https://brighthiveio.atlassian.net/browse/BH-537) | [CORE] Expose QualityRule types in public GraphQL schema and run… | Harbour Wang | — |
| [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) | feat(core): resolvers + service for quality rule CRUD, status… | Harbour Wang | — |
| [BH-543](https://brighthiveio.atlassian.net/browse/BH-543) | feat(brightbot): add execute_library_quality_rules_tool with… | Marwan Samih | — |

### 🔵 In Review (19)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-505](https://brighthiveio.atlassian.net/browse/BH-505) | feat(brightbot): QualityRuleNode and QualityRuleExecutionNode in… | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11)<br>[🟡 Draft brighthive-platform-core#771](https://github.com/brighthive/brighthive-platform-core/pull/771) |
| [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) | Longaeva Partners POC — 14-day pre-trial execution | Kuri Chinca | [🟢 Merged agentic-project-mgmt#17](https://github.com/brighthive/agentic-project-mgmt/pull/17)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) | Add SnowflakeConnection class to warehouse_connections.py and wire… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) | Add Snowflake SQL dialect rules to agent prompts | Kuri Chinca | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-529](https://brighthiveio.atlassian.net/browse/BH-529) | feat(dbt-agent): proxy all GitHub ops through Platform Core with… | Marwan Samih | [🟡 Draft brightbot#496](https://github.com/brighthive/brightbot/pull/496)<br>[🟡 Draft brightbot#495](https://github.com/brighthive/brightbot/pull/495)<br>[🟡 Draft brightbot#493](https://github.com/brighthive/brightbot/pull/493) |
| [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) | Build Snowflake semantic view YAML scaffold tool | Marwan Samih | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#20](https://github.com/brighthive/agentic-project-mgmt/pull/20)<br>[🟡 Draft brightbot#489](https://github.com/brighthive/brightbot/pull/489) |
| [BH-549](https://brighthiveio.atlassian.net/browse/BH-549) | feat(brightbot): warehouse_config-aware Snowflake branch in… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-550](https://brighthiveio.atlassian.net/browse/BH-550) | test(brightbot): tests/unit/test_snowflake_warehouse.py mirror of… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) | feat(platform-core): SnowflakeSourceConfig in OMD ingestion lambda | Ahmed Elsherbiny | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) | feat(brightbot): data_profiler Snowflake-specific branches (verify;… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) | refactor(org-cdk): SnowflakeIngestionStack reads workspace_secret_sto… | Ahmed Elsherbiny | [🔵 Review brighthive-data-organization-cdk#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) |
| [BH-559](https://brighthiveio.atlassian.net/browse/BH-559) | fix(platform-core): derive workspaceId from context.token in… | Kuri Chinca | [🟡 Draft brighthive-platform-core#780](https://github.com/brighthive/brighthive-platform-core/pull/780) |
| [BH-560](https://brighthiveio.atlassian.net/browse/BH-560) | fix(platform-core): disable redirect-following + scrub PAT from… | Kuri Chinca | [🟡 Draft brighthive-platform-core#781](https://github.com/brighthive/brighthive-platform-core/pull/781) |
| [BH-561](https://brighthiveio.atlassian.net/browse/BH-561) | feat(platform-core): truncated flag + structured errorCode/httpStatus… | Kuri Chinca | [🟡 Draft brighthive-platform-core#782](https://github.com/brighthive/brighthive-platform-core/pull/782) |
| [BH-562](https://brighthiveio.atlassian.net/browse/BH-562) | chore(brightbot): finish PyGithub removal — pyproject + 4 modules +… | Kuri Chinca | [🟡 Draft brightbot#496](https://github.com/brighthive/brightbot/pull/496)<br>[🟡 Draft brightbot#495](https://github.com/brighthive/brightbot/pull/495) |
| [BH-563](https://brighthiveio.atlassian.net/browse/BH-563) | fix(brightbot): redact Authorization header + payload from… | Kuri Chinca | [🟡 Draft brightbot#492](https://github.com/brighthive/brightbot/pull/492) |
| [BH-564](https://brighthiveio.atlassian.net/browse/BH-564) | refactor(brightbot): Pydantic responses + DI for PlatformAPISession… | Kuri Chinca | [🟡 Draft brightbot#494](https://github.com/brighthive/brightbot/pull/494) |
| [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) | docs(brightbot): author BRIGHTBOT-GITHUB-PROXY-GUIDE.md (currently… | Kuri Chinca | [🟡 Draft brightbot#493](https://github.com/brighthive/brightbot/pull/493) |
| [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) | test(platform-core): property-based tests for parseGitHubRepoUrl +… | Kuri Chinca | [🟡 Draft brighthive-platform-core#783](https://github.com/brighthive/brighthive-platform-core/pull/783) |

### ✅ Done (6)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-509](https://brighthiveio.atlassian.net/browse/BH-509) | feat(platform-core): GraphQL types and resolvers for quality rules | Harbour Wang | — |
| [BH-510](https://brighthiveio.atlassian.net/browse/BH-510) | feat(webapp): wire Quality Rules page to live GraphQL plus rule… | Harbour Wang | — |
| [BH-538](https://brighthiveio.atlassian.net/browse/BH-538) | [CORE] Implement QualityRule CRUD resolvers and service layer | Harbour Wang | — |
| [BH-539](https://brighthiveio.atlassian.net/browse/BH-539) | [CORE] Seed script: 20+ QualityRuleTemplate starter library nodes | Harbour Wang | — |
| [BH-540](https://brighthiveio.atlassian.net/browse/BH-540) | feat(core): add scope/context model to OGM, expose QualityRule… | Harbour Wang | — |
| [BH-542](https://brighthiveio.atlassian.net/browse/BH-542) | feat(core): seed 20+ QualityRuleTemplateNode starters with scope… | Harbour Wang | — |


## 🕒 Recent activity (14 days)

- **2026-06-05** · [BH-600](https://brighthiveio.atlassian.net/browse/BH-600) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-599](https://brighthiveio.atlassian.net/browse/BH-599) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-597](https://brighthiveio.atlassian.net/browse/BH-597) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-596](https://brighthiveio.atlassian.net/browse/BH-596) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-595](https://brighthiveio.atlassian.net/browse/BH-595) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-594](https://brighthiveio.atlassian.net/browse/BH-594) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-593](https://brighthiveio.atlassian.net/browse/BH-593) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-592](https://brighthiveio.atlassian.net/browse/BH-592) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-591](https://brighthiveio.atlassian.net/browse/BH-591) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-590](https://brighthiveio.atlassian.net/browse/BH-590) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-601](https://brighthiveio.atlassian.net/browse/BH-601) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-598](https://brighthiveio.atlassian.net/browse/BH-598) — Needs Refinement · Kuri Chinca
- **2026-06-05** · [BH-529](https://brighthiveio.atlassian.net/browse/BH-529) — Code Review · Marwan Samih
- **2026-06-05** · [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) — Needs Refinement · Marwan Samih
- **2026-06-05** · [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) — Code Review · Kuri Chinca
- **2026-06-04** · [BH-583](https://brighthiveio.atlassian.net/browse/BH-583) — Needs Refinement · Harbour Wang
- **2026-06-03** · [BH-587](https://brighthiveio.atlassian.net/browse/BH-587) — Needs Refinement · Harbour Wang
- **2026-06-03** · [BH-586](https://brighthiveio.atlassian.net/browse/BH-586) — Needs Refinement · Ahmed Elsherbiny
- **2026-06-03** · [BH-584](https://brighthiveio.atlassian.net/browse/BH-584) — Needs Refinement · Ahmed Elsherbiny
- **2026-06-03** · [BH-585](https://brighthiveio.atlassian.net/browse/BH-585) — Needs Refinement · Kuri Chinca

_(+48 older updates not shown.)_

## 📝 Daily Notes

<!-- TRACKER:MANUAL:BEGIN daily-notes -->

_Filled during the trial — one entry per trial day. Use `### Day N — YYYY-MM-DD` headings._

### Day -7 — 2026-06-08 (pre-trial weekend merge train)

**Code-locked in develop across all 4 repos.** 24 PRs squash-merged. 6 specs signed off. Live verified against `LONGAEVA_POC` Snowflake.

- **GC harness on develop HEAD**: 5 passed / 8 skipped / 2 strict-xfailed in 21s
- **L3 full-graph e2e**: 1 passed in 59s ($174B exposure / 196 issuers via `SEMANTIC_VIEW(...)`)
- **Composite ≥10-of-14 demoed convincingly**: ~70% (was 40%)
- **Demo bar holds** for "single Silver table → enrolled → PR-raised"; **NOT defensible** for "auto-infer schema-wide ≥90%" without bb#489

Full state + outstanding follow-ups + risks in [`SESSION-HANDOFF-2026-06-08.md`](./SESSION-HANDOFF-2026-06-08.md). **Read that doc first when resuming.**

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
