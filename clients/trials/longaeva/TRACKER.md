# Longaeva — Live Tracker

_Last refreshed **2026-06-15 13:58 UTC** by `make longaeva-tracker`. Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved._

> **Trial dates**: TBD with Grant · **Epic**: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)

---

## 🚨 Blockers

<!-- TRACKER:MANUAL:BEGIN blockers -->

**🟢 RESOLVED 2026-06-08 — BH-529 P0 chain landed in pc#793 + bb#510**
- Multi-tenant exfil (BH-559), PAT-leak-on-redirect (BH-560), structured errorCode + httpStatus envelope (BH-561), PyGithub purge (BH-562), JWT leak scrubbing (BH-563) all merged via the 06-08 megaconsolidation
- Audit-debt #10 (selection-set drift) closed in bb#520 (cycle-5) — dbt-agent now gets typed errorCode + BRANCH_EXISTS retry path revived
- Audit-debt #11 (token redaction extension to `ghu_*`, `?access_token=`, `&pat=`) closed in pc#803 (cycle-5)
- 70-test CI gate added in pc#805 — Properties 1, 2, 4 locked on every future PR

**🟢 RESOLVED 2026-06-08 — Self-hosting deployment path simplified to Terraform** (Matt → Grant/Sumukh email, 11:29 AM ET)
- BrightHive committed Terraform module as primary supported path; CDK remains alternative
- `artifacts/trial-guide-tech-prep.md` extended with Path A (Terraform) + Path B (CDK) + uv-based local install section
- BH-572 / BH-573 / BH-574 / BH-575 in flight per the cycle-7 merge train

**🟢 RESOLVED 2026-06-08 — MCP auth workflow** via pc#793 (Cognito MCP clients) + pc#794 (SPEC-MCP-DCR-RFC7591 signed off, 5 §10 questions resolved). DCR Lambda implementation deferred to post-trial (BH-588 replaced-by ref).

**🟢 RESOLVED 2026-06-09 cycle-17 — GC-6 demo loop fulfills its purpose end-to-end**
- 20 PRs across 4 repos shipped in autonomous cycles 1-17 on top of the 06-08 merge train
- `make verify-pristine` opens a real GitHub PR against `brighthive/longaeva-semantic-views` in ~30s on a fresh laptop
- Property 1 (PAT redaction) + Property 2 (yamlHash continuity) locked under CI
- Operator runbook + dry-run script + per-customer provisioning all shipped
- Engineering Slack updated 2026-06-09 ts `1781011761.012769`
- Full audit trail: [`BRIGHTHIVE_GAPS.md` `amended[]`](./BRIGHTHIVE_GAPS.md), [`OPERATOR-RUNBOOK-DAY-1.md`](./OPERATOR-RUNBOOK-DAY-1.md)

**🚨 BLOCKING DAY 1 (humans-only, none session-reachable)** — raised 2026-06-09 by @kuri
1. **Staging deploy** of pc#797..806 + bb#520 — auto-flips GC-10 S6/S7, unblocks GC-9 MCP downstream. Owner: ops/SRE. **Target: by Day -2 (Sat 2026-06-13).**
2. **BH-533 connectivity validation** post-deploy. Exercises full Longaeva-side stack (Snowflake, GHE, Slack, Airbyte, Dagster). Hours of work after #1 lands.
3. **Demo storyboard scope decision with Grant** — single-table vs schema-wide GC-6 framing. Single-table is defensible today; pitching schema-wide without bb#489 is a credibility risk.
4. **`LONGAEVA_AGENT_ROLE` runtime** — switch agents off KURICHINCA admin to read-only per GC-14 sandbox parity. CDK config + smoke test.
5. **Customer creds handover from Longaeva** — GHE host URL + PAT + TLS chain (Grant), Longaeva MCP creds (Grant), customer Okta tenant for IdP federation (Grant + IT). Tracked via BH-533.

**🟡 Sprint-sized deferrals (intentionally NOT shipping for Day 1)**
- bb#489 multi-table semantic view — would lift GC-6 from `single-table defensible` → `walk-away win`; orphaned draft
- generate_mart_model (GC-5) — bb#513 spec signed off, ~400 lines, 2-3 days
- Snowflake auto-trigger — ~50 lines pc + SSM export per SPEC-SNOWFLAKE-E2E §2.6
- Webapp BH-615 (admin panel for binding) + BH-616 (Save & Open PR button) — paused per "no UI mess" decision; demo runs against GraphQL API directly

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

### Pre-trial — Snowflake foundation must be merged (1/13 🟢, 6 🟡)

_All Phase 1 Snowflake integration PRs land before Day 1. Without these, brightbot can't query Snowflake and the trial can't run §1 ingestion or §2 semantic-view enrollment._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🟡 | Pre-trial | brightbot Layer 5 (SnowflakeConnection + dialect + tests) merged | [BH-527](https://brighthiveio.atlassian.net/browse/BH-527), [BH-528](https://brighthiveio.atlassian.net/browse/BH-528), [BH-549](https://brighthiveio.atlassian.net/browse/BH-549), [BH-550](https://brighthiveio.atlassian.net/browse/BH-550), [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) |
| ⬜ | Pre-trial | Atlas semantic-view YAML scaffold tool merged (BH-531) | [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) |
| 🟡 | Pre-trial | OMD ingestion lambda Layer 3 (SnowflakeSourceConfig) merged | [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) |
| 🟡 | Pre-trial | Org-CDK ingestion stack reads workspace_secret_store | [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) |
| ⬜ | Pre-trial | Webapp Snowflake form audit signed off | [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) |
| 🟡 | Pre-trial | BH-529 GitHub proxy + 7 P0 follow-ups merged (PyGithub fully removed, tenant isolation fixed, redirect-strip fixed) | [BH-529](https://brighthiveio.atlassian.net/browse/BH-529), [BH-559](https://brighthiveio.atlassian.net/browse/BH-559), [BH-560](https://brighthiveio.atlassian.net/browse/BH-560), [BH-561](https://brighthiveio.atlassian.net/browse/BH-561), [BH-562](https://brighthiveio.atlassian.net/browse/BH-562), [BH-563](https://brighthiveio.atlassian.net/browse/BH-563), [BH-564](https://brighthiveio.atlassian.net/browse/BH-564), [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) |
| 🟡 | Pre-trial | GHE smoke test — dbt agent opens a PR against a BrightHive-internal GHE sandbox before Longaeva access | [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) |
| 🔲 | Pre-trial | Longaeva GHE PAT + host URL + TLS chain confirmed by Grant | _manual_ |
| ⬜ | Pre-trial | PR template compliance — dbt agent reads .github/pull_request_template.md | [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) |
| 🟡 | Pre-trial | GX output: serialize as YAML to repo branch (not Markdown to S3) | [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) |
| 🟢 | Pre-trial | Quality agent CRUD resolvers + service merged | [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) |
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
| **Harbour Wang** | 17 | 0 | 4 | [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) feat(webapp): replace MOCK_RULES with… |
| **Kuri Chinca** | 3 | 13 | 28 | [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) docs(brightbot): author BRIGHTBOT-GITHU… |
| **Ahmed Elsherbiny** | 0 | 2 | 6 | — |
| **Marwan Samih** | 0 | 4 | 4 | — |
| **_unassigned_** | 0 | 0 | 2 | — |

## 📊 Summary

- **20/83** tickets done · 19 in progress · 44 to do
- PRs: 44 merged · 0 ready for review · 26 draft

## 📋 Tickets by status

### 🟡 To Do (44)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-302](https://brighthiveio.atlassian.net/browse/BH-302) | Create a PoC on how we will add infra to support platform notificatio… | Ahmed Elsherbiny | — |
| [BH-454](https://brighthiveio.atlassian.net/browse/BH-454) | Spike: AgentCore region + reference architecture + streaming POC +… | Kuri Chinca | — |
| [BH-504](https://brighthiveio.atlassian.net/browse/BH-504) | spec(quality): workspace-configurable rules — contracts, invariants,… | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) | Longaeva Partners POC — 14-day pre-trial execution | Kuri Chinca | [🟢 Merged agentic-project-mgmt#17](https://github.com/brighthive/agentic-project-mgmt/pull/17)<br>[🟢 Merged brightbot#518](https://github.com/brighthive/brightbot/pull/518)<br>[🟢 Merged brighthive-platform-core#798](https://github.com/brighthive/brighthive-platform-core/pull/798) |
| [BH-531](https://brighthiveio.atlassian.net/browse/BH-531) | Build Snowflake semantic view YAML scaffold tool | Marwan Samih | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#20](https://github.com/brighthive/agentic-project-mgmt/pull/20)<br>[🟢 Merged brightbot#510](https://github.com/brighthive/brightbot/pull/510) |
| [BH-532](https://brighthiveio.atlassian.net/browse/BH-532) | Confirm and configure MCP client connectivity to Longaeva's… | Ahmed Elsherbiny | — |
| [BH-533](https://brighthiveio.atlassian.net/browse/BH-533) | Provision Longaeva trial workspace and validate end-to-end stack… | Ahmed Elsherbiny | — |
| [BH-534](https://brighthiveio.atlassian.net/browse/BH-534) | Build Longaeva context layer — load reference schemas and YAML spec… | Ahmed Elsherbiny | — |
| [BH-535](https://brighthiveio.atlassian.net/browse/BH-535) | Execute ingestion POC scenarios (S3, REST API, Snowflake Data Share) | Kuri Chinca | — |
| [BH-536](https://brighthiveio.atlassian.net/browse/BH-536) | Execute semantic view enrollment, MCP validation, and maintenance demo | Kuri Chinca | — |
| [BH-544](https://brighthiveio.atlassian.net/browse/BH-544) | feat(brightbot): governance agent routes to library tool with… | Marwan Samih | — |
| [BH-550](https://brighthiveio.atlassian.net/browse/BH-550) | test(brightbot): tests/unit/test_snowflake_warehouse.py mirror of… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-552](https://brighthiveio.atlassian.net/browse/BH-552) | audit(webapp): confirm Snowflake dropdown + form fields render | Kuri Chinca | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19) |
| [BH-553](https://brighthiveio.atlassian.net/browse/BH-553) | feat(brightbot): data_profiler Snowflake-specific branches (verify;… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) | feat(notifications): wire Quality Agent → BrightSignals end-to-end… | Harbour Wang | — |
| [BH-558](https://brighthiveio.atlassian.net/browse/BH-558) | feat(webapp): wire side-menu push-notifications to live BrightSignals… | Harbour Wang | — |
| [BH-566](https://brighthiveio.atlassian.net/browse/BH-566) | feat(brightbot): dbt-agent reads pull_request_template.md +… | Kuri Chinca | — |
| [BH-568](https://brighthiveio.atlassian.net/browse/BH-568) | chore(brightbot): migrate non-dbt agents off PyGithub (super_agent,… | Kuri Chinca | — |
| [BH-569](https://brighthiveio.atlassian.net/browse/BH-569) | feat(github-proxy): GitHub App installation flow — replace PAT for… | Kuri Chinca | — |
| [BH-570](https://brighthiveio.atlassian.net/browse/BH-570) | feat(platform-core): self-signed CA bundle support for GHE Server… | _unassigned_ | — |
| [BH-571](https://brighthiveio.atlassian.net/browse/BH-571) | feat(platform-core): per-host rate-limit metrics + adaptive backoff… | _unassigned_ | — |
| [BH-584](https://brighthiveio.atlassian.net/browse/BH-584) | feat(infra): Terraform module brighthive-longaeva-trial-tf —… | Ahmed Elsherbiny | — |
| [BH-585](https://brighthiveio.atlassian.net/browse/BH-585) | docs(longaeva): simplified self-hosting setup doc — Terraform-first,… | Kuri Chinca | — |
| [BH-586](https://brighthiveio.atlassian.net/browse/BH-586) | feat(cli): publish brighthive CLI wheel to PyPI; smoke uv tool… | Ahmed Elsherbiny | — |
| [BH-587](https://brighthiveio.atlassian.net/browse/BH-587) | feat(slack): bidirectional @brightagent — pipeline-state Q&A +… | Harbour Wang | — |
| [BH-590](https://brighthiveio.atlassian.net/browse/BH-590) | feat(warehouse): wire Snowflake INFORMATION_SCHEMA introspection… | Kuri Chinca | [🟡 Draft brightbot#508](https://github.com/brighthive/brightbot/pull/508)<br>[🟡 Draft brightbot#506](https://github.com/brighthive/brightbot/pull/506)<br>[🟡 Draft brightbot#505](https://github.com/brighthive/brightbot/pull/505) |
| [BH-591](https://brighthiveio.atlassian.net/browse/BH-591) | feat(dbt-agent): wire scaffold_atlas_semantic_view_tool into… | Kuri Chinca | [🟡 Draft brightbot#505](https://github.com/brighthive/brightbot/pull/505)<br>[🟢 Merged brightbot#504](https://github.com/brighthive/brightbot/pull/504) |
| [BH-593](https://brighthiveio.atlassian.net/browse/BH-593) | feat(github-proxy): thread GITHUB_BASE_URL through GHE client… | Kuri Chinca | — |
| [BH-595](https://brighthiveio.atlassian.net/browse/BH-595) | feat(ingestion-agent): generate partitioned REST API ingestion… | Kuri Chinca | — |
| [BH-596](https://brighthiveio.atlassian.net/browse/BH-596) | feat(dbt-agent): Atlas binding grounding validator + verified_query… | Kuri Chinca | — |
| [BH-598](https://brighthiveio.atlassian.net/browse/BH-598) | chore(dbt-agent): migrate super_agent + dbt_tools off legacy… | Kuri Chinca | — |
| [BH-599](https://brighthiveio.atlassian.net/browse/BH-599) | feat(self-healing): detect→diagnose→surgical-PR loop for 4 pipeline… | Kuri Chinca | — |
| [BH-600](https://brighthiveio.atlassian.net/browse/BH-600) | feat(quality-agent): longitudinal anomaly monitoring with stateful… | Kuri Chinca | — |
| [BH-601](https://brighthiveio.atlassian.net/browse/BH-601) | Longaeva PoC — 14 Golden Success Paths (GC-1..14) explicit tracking | Kuri Chinca | [🟢 Merged brightbot#541](https://github.com/brighthive/brightbot/pull/541)<br>[🟢 Merged brightbot#540](https://github.com/brighthive/brightbot/pull/540) |
| [BH-610](https://brighthiveio.atlassian.net/browse/BH-610) | test(brightbot): rewrite test_dbt_react_tools.py post PyGithub… | Kuri Chinca | [🟢 Merged brightbot#519](https://github.com/brighthive/brightbot/pull/519) |
| [BH-611](https://brighthiveio.atlassian.net/browse/BH-611) | Add LocalStack to docker-compose.local.yml so secrets/cognito/s3… | Kuri Chinca | [🟢 Merged brighthive-platform-core#802](https://github.com/brighthive/brighthive-platform-core/pull/802) |
| [BH-612](https://brighthiveio.atlassian.net/browse/BH-612) | Auth directive ignores role hierarchy — admin denied by CONTRIBUTOR/e… | Kuri Chinca | — |
| [BH-613](https://brighthiveio.atlassian.net/browse/BH-613) | [BH-NEW-1] WorkspaceGitHubBindingNode + setWorkspaceGitHubBinding +… | Kuri Chinca | [🟢 Merged brighthive-platform-core#801](https://github.com/brighthive/brighthive-platform-core/pull/801)<br>[🟢 Merged brighthive-platform-core#800](https://github.com/brighthive/brighthive-platform-core/pull/800)<br>[🟢 Merged brighthive-platform-core#799](https://github.com/brighthive/brighthive-platform-core/pull/799) |
| [BH-614](https://brighthiveio.atlassian.net/browse/BH-614) | [BH-NEW-2] commitSemanticViewToGitHub orchestrator | Kuri Chinca | [🟢 Merged brighthive-platform-core#801](https://github.com/brighthive/brighthive-platform-core/pull/801)<br>[🟢 Merged brighthive-platform-core#800](https://github.com/brighthive/brighthive-platform-core/pull/800)<br>[🟢 Merged brighthive-platform-core#799](https://github.com/brighthive/brighthive-platform-core/pull/799) |
| [BH-615](https://brighthiveio.atlassian.net/browse/BH-615) | [BH-NEW-3] webapp WorkspaceSettings/GitHubBinding admin panel | Kuri Chinca | [🟢 Merged brighthive-platform-core#799](https://github.com/brighthive/brighthive-platform-core/pull/799) |
| [BH-616](https://brighthiveio.atlassian.net/browse/BH-616) | [BH-NEW-4] webapp SemanticViewYamlEditor "Save & Open PR" + binding… | Kuri Chinca | — |
| [BH-617](https://brighthiveio.atlassian.net/browse/BH-617) | [BH-NEW-5] Per-customer semantic-views repo provisioning script | Kuri Chinca | — |
| [BH-618](https://brighthiveio.atlassian.net/browse/BH-618) | [BH-NEW-6] Eval harness for SPEC-SEMANTIC-VIEW-AUTHORING §7… | Kuri Chinca | [🟢 Merged brighthive-platform-core#801](https://github.com/brighthive/brighthive-platform-core/pull/801) |
| [BH-621](https://brighthiveio.atlassian.net/browse/BH-621) | Project-scoped dbt MCP: bind project_id → dbt-mcp config so BA MCP… | Kuri Chinca | — |

### 🟢 In Progress (19)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-527](https://brighthiveio.atlassian.net/browse/BH-527) | Add SnowflakeConnection class to warehouse_connections.py and wire… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#22](https://github.com/brighthive/agentic-project-mgmt/pull/22)<br>[🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🟢 Merged brightbot#510](https://github.com/brighthive/brightbot/pull/510) |
| [BH-528](https://brighthiveio.atlassian.net/browse/BH-528) | Add Snowflake SQL dialect rules to agent prompts | Kuri Chinca | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-529](https://brighthiveio.atlassian.net/browse/BH-529) | feat(dbt-agent): proxy all GitHub ops through Platform Core with… | Marwan Samih | [🟡 Draft brightbot#496](https://github.com/brighthive/brightbot/pull/496)<br>[🟡 Draft brightbot#495](https://github.com/brighthive/brightbot/pull/495)<br>[🟡 Draft brightbot#493](https://github.com/brighthive/brightbot/pull/493) |
| [BH-530](https://brighthiveio.atlassian.net/browse/BH-530) | Fix GX output: serialize expectation suite as YAML and commit to… | Marwan Samih | [🟢 Merged brightbot#486](https://github.com/brighthive/brightbot/pull/486) |
| [BH-543](https://brighthiveio.atlassian.net/browse/BH-543) | feat(brightbot): add execute_library_quality_rules_tool with… | Marwan Samih | — |
| [BH-549](https://brighthiveio.atlassian.net/browse/BH-549) | feat(brightbot): warehouse_config-aware Snowflake branch in… | Marwan Samih | [🔵 Review brightbot#488](https://github.com/brighthive/brightbot/pull/488) |
| [BH-551](https://brighthiveio.atlassian.net/browse/BH-551) | feat(platform-core): SnowflakeSourceConfig in OMD ingestion lambda | Ahmed Elsherbiny | [🟢 Merged agentic-project-mgmt#19](https://github.com/brighthive/agentic-project-mgmt/pull/19)<br>[🔵 Review brighthive-platform-core#777](https://github.com/brighthive/brighthive-platform-core/pull/777) |
| [BH-554](https://brighthiveio.atlassian.net/browse/BH-554) | refactor(org-cdk): SnowflakeIngestionStack reads workspace_secret_sto… | Ahmed Elsherbiny | [🟢 Merged brighthive-data-organization-cdk#157](https://github.com/brighthive/brighthive-data-organization-cdk/pull/157)<br>[🟢 Merged brighthive-data-organization-cdk#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156) |
| [BH-559](https://brighthiveio.atlassian.net/browse/BH-559) | fix(platform-core): derive workspaceId from context.token in… | Kuri Chinca | [🟢 Merged brighthive-platform-core#793](https://github.com/brighthive/brighthive-platform-core/pull/793)<br>[🟡 Draft brighthive-platform-core#792](https://github.com/brighthive/brighthive-platform-core/pull/792)<br>[🟡 Draft brighthive-platform-core#780](https://github.com/brighthive/brighthive-platform-core/pull/780) |
| [BH-560](https://brighthiveio.atlassian.net/browse/BH-560) | fix(platform-core): disable redirect-following + scrub PAT from… | Kuri Chinca | [🟡 Draft brighthive-platform-core#781](https://github.com/brighthive/brighthive-platform-core/pull/781) |
| [BH-561](https://brighthiveio.atlassian.net/browse/BH-561) | feat(platform-core): truncated flag + structured errorCode/httpStatus… | Kuri Chinca | [🟡 Draft brighthive-platform-core#782](https://github.com/brighthive/brighthive-platform-core/pull/782) |
| [BH-563](https://brighthiveio.atlassian.net/browse/BH-563) | fix(brightbot): redact Authorization header + payload from… | Kuri Chinca | [🟡 Draft brightbot#492](https://github.com/brighthive/brightbot/pull/492) |
| [BH-567](https://brighthiveio.atlassian.net/browse/BH-567) | test(platform-core): property-based tests for parseGitHubRepoUrl +… | Kuri Chinca | [🟢 Merged brighthive-platform-core#805](https://github.com/brighthive/brighthive-platform-core/pull/805)<br>[🟡 Draft brighthive-platform-core#783](https://github.com/brighthive/brighthive-platform-core/pull/783) |
| [BH-592](https://brighthiveio.atlassian.net/browse/BH-592) | feat(dbt-agent): generate dbt sources.yml + staging model from… | Kuri Chinca | [🟢 Merged brightbot#510](https://github.com/brighthive/brightbot/pull/510)<br>[🟡 Draft brightbot#503](https://github.com/brighthive/brightbot/pull/503)<br>[🟡 Draft brightbot#502](https://github.com/brighthive/brightbot/pull/502) |
| [BH-594](https://brighthiveio.atlassian.net/browse/BH-594) | feat(dbt-agent): infer dbt schema.yml tests (not_null/unique/accepted… | Kuri Chinca | [🟡 Draft brightbot#507](https://github.com/brighthive/brightbot/pull/507) |
| [BH-597](https://brighthiveio.atlassian.net/browse/BH-597) | feat(eval): end-to-end agent eval harness for the 6-step Longaeva… | Kuri Chinca | [🟢 Merged brightbot#512](https://github.com/brighthive/brightbot/pull/512) |
| [BH-619](https://brighthiveio.atlassian.net/browse/BH-619) | SV lineage: expose base_tables + join graph on list_semantic_views | Kuri Chinca | [🟢 Merged brightbot#538](https://github.com/brighthive/brightbot/pull/538)<br>[🟢 Merged brightbot#535](https://github.com/brighthive/brightbot/pull/535)<br>[🟢 Merged brightbot#534](https://github.com/brighthive/brightbot/pull/534) |
| [BH-620](https://brighthiveio.atlassian.net/browse/BH-620) | SV edits land as governed PRs — CI compile-check on PR, apply-on-merge | Kuri Chinca | [🟢 Merged brightbot#537](https://github.com/brighthive/brightbot/pull/537)<br>[🟢 Merged brightbot#536](https://github.com/brighthive/brightbot/pull/536) |
| [BH-622](https://brighthiveio.atlassian.net/browse/BH-622) | SV QC: compare upstream base tables vs data product (row counts,… | Kuri Chinca | [🟢 Merged brightbot#539](https://github.com/brighthive/brightbot/pull/539)<br>[🟢 Merged brightbot#538](https://github.com/brighthive/brightbot/pull/538) |

### ✅ Done (20)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-505](https://brighthiveio.atlassian.net/browse/BH-505) | feat(brightbot): QualityRuleNode and QualityRuleExecutionNode in… | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11)<br>[🔵 Review brighthive-platform-core#771](https://github.com/brighthive/brighthive-platform-core/pull/771) |
| [BH-506](https://brighthiveio.atlassian.net/browse/BH-506) | feat(brightbot): REST CRUD endpoints for quality rules | Harbour Wang | — |
| [BH-507](https://brighthiveio.atlassian.net/browse/BH-507) | feat(brightbot): quality agent reads rules from library, not LLM regen | Harbour Wang | — |
| [BH-508](https://brighthiveio.atlassian.net/browse/BH-508) | feat(brightbot): per-rule execution fanout and pass rate aggregation | Harbour Wang | — |
| [BH-509](https://brighthiveio.atlassian.net/browse/BH-509) | feat(platform-core): GraphQL types and resolvers for quality rules | Harbour Wang | — |
| [BH-510](https://brighthiveio.atlassian.net/browse/BH-510) | feat(webapp): wire Quality Rules page to live GraphQL plus rule… | Harbour Wang | — |
| [BH-511](https://brighthiveio.atlassian.net/browse/BH-511) | feat(brightbot): seed library of 20 plus quality rule templates | Harbour Wang | [🟢 Merged agentic-project-mgmt#11](https://github.com/brighthive/agentic-project-mgmt/pull/11) |
| [BH-537](https://brighthiveio.atlassian.net/browse/BH-537) | [CORE] Expose QualityRule types in public GraphQL schema and run… | Harbour Wang | — |
| [BH-538](https://brighthiveio.atlassian.net/browse/BH-538) | [CORE] Implement QualityRule CRUD resolvers and service layer | Harbour Wang | — |
| [BH-539](https://brighthiveio.atlassian.net/browse/BH-539) | [CORE] Seed script: 20+ QualityRuleTemplate starter library nodes | Harbour Wang | — |
| [BH-540](https://brighthiveio.atlassian.net/browse/BH-540) | feat(core): add scope/context model to OGM, expose QualityRule… | Harbour Wang | — |
| [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) | feat(core): resolvers + service for quality rule CRUD, status… | Harbour Wang | — |
| [BH-542](https://brighthiveio.atlassian.net/browse/BH-542) | feat(core): seed 20+ QualityRuleTemplateNode starters with scope… | Harbour Wang | — |
| [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) | feat(webapp): replace MOCK_RULES with live qualityRules query;… | Harbour Wang | — |
| [BH-546](https://brighthiveio.atlassian.net/browse/BH-546) | feat(webapp): create/edit drawer with scope selector, asset picker,… | Harbour Wang | — |
| [BH-547](https://brighthiveio.atlassian.net/browse/BH-547) | feat(webapp): activate/deactivate toggle, execution history panel,… | Harbour Wang | — |
| [BH-562](https://brighthiveio.atlassian.net/browse/BH-562) | chore(brightbot): finish PyGithub removal — pyproject + 4 modules +… | Kuri Chinca | [🟡 Draft brightbot#496](https://github.com/brighthive/brightbot/pull/496)<br>[🟡 Draft brightbot#495](https://github.com/brighthive/brightbot/pull/495) |
| [BH-564](https://brighthiveio.atlassian.net/browse/BH-564) | refactor(brightbot): Pydantic responses + DI for PlatformAPISession… | Kuri Chinca | [🟡 Draft brightbot#494](https://github.com/brighthive/brightbot/pull/494) |
| [BH-565](https://brighthiveio.atlassian.net/browse/BH-565) | docs(brightbot): author BRIGHTBOT-GITHUB-PROXY-GUIDE.md (currently… | Kuri Chinca | [🟡 Draft brightbot#493](https://github.com/brighthive/brightbot/pull/493) |
| [BH-583](https://brighthiveio.atlassian.net/browse/BH-583) | refactor(brightbot): quality check graph cleanup — SQL datasource,… | Harbour Wang | — |


## 🕒 Recent activity (14 days)

- **2026-06-12** · [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) — Needs Refinement · Kuri Chinca
- **2026-06-11** · [BH-622](https://brighthiveio.atlassian.net/browse/BH-622) — Staging QC · Kuri Chinca
- **2026-06-11** · [BH-620](https://brighthiveio.atlassian.net/browse/BH-620) — Staging QC · Kuri Chinca
- **2026-06-11** · [BH-619](https://brighthiveio.atlassian.net/browse/BH-619) — Staging QC · Kuri Chinca
- **2026-06-09** · [BH-621](https://brighthiveio.atlassian.net/browse/BH-621) — Needs Refinement · Kuri Chinca
- **2026-06-09** · [BH-557](https://brighthiveio.atlassian.net/browse/BH-557) — Needs Refinement · Harbour Wang
- **2026-06-09** · [BH-545](https://brighthiveio.atlassian.net/browse/BH-545) — Done · Harbour Wang
- **2026-06-09** · [BH-547](https://brighthiveio.atlassian.net/browse/BH-547) — Done · Harbour Wang
- **2026-06-09** · [BH-541](https://brighthiveio.atlassian.net/browse/BH-541) — Done · Harbour Wang
- **2026-06-09** · [BH-505](https://brighthiveio.atlassian.net/browse/BH-505) — Done · Harbour Wang
- **2026-06-09** · [BH-583](https://brighthiveio.atlassian.net/browse/BH-583) — Done · Harbour Wang
- **2026-06-08** · [BH-618](https://brighthiveio.atlassian.net/browse/BH-618) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-617](https://brighthiveio.atlassian.net/browse/BH-617) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-616](https://brighthiveio.atlassian.net/browse/BH-616) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-615](https://brighthiveio.atlassian.net/browse/BH-615) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-614](https://brighthiveio.atlassian.net/browse/BH-614) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-613](https://brighthiveio.atlassian.net/browse/BH-613) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-612](https://brighthiveio.atlassian.net/browse/BH-612) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-611](https://brighthiveio.atlassian.net/browse/BH-611) — Needs Refinement · Kuri Chinca
- **2026-06-08** · [BH-610](https://brighthiveio.atlassian.net/browse/BH-610) — Needs Refinement · Kuri Chinca

_(+59 older updates not shown.)_

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

### Day 1 — 2026-06-15 (Snowflake/OMD ingestion — root cause found, NOT yet fixed)

> Corrects an earlier draft of this entry that overstated status as "found + fixed / wired end-to-end" and mislabeled the day. Accurate status below.

**Root cause of OneTen's empty Snowflake catalog FOUND; fix NOT yet wired in.** The old shared scan lambda (`openmetadata_ingestion_lambda`, SDK `openmetadata-ingestion==0.12.2`, 2022) **cannot talk to the live OM 1.8.9 server** — its version probe 500s, so catalog scans fail for **every** warehouse type (Redshift/Glue callers hit the same 500; nobody noticed because no fresh scan ran). OneTen's Snowflake catalog is still **0 assets**.

**Built + deployed (dev/staging only), but NOT routed:**
- **#819** — new `snowflake_ingestion_lambda` (Docker, py3.11, SDK 1.8.9) exists but is Snowflake-hardcoded and only deployed in non-prod; **no live caller points at it yet**. Every live scan caller still POSTs the dead old lambda.
- **#816** — enhanced webhook migrated to OM 1.8.9 `/v1/events/subscriptions` (warehouse-agnostic, working).
- **#837/#839** — enhanced webhook triggers description+embedding for scanned tables + DynamoDB mapping (working, downstream of the scan).

**ARCHITECTURE FORK (2026-06-15, per Ahmed):** the team has shifted to **OM 1.8.9 native ingestion (Airflow pipeline service) + enhanced webhook lambda + MCP** — the external warehouse-specific scan lambda is the *old* pattern. OM 1.8.9 ships a live `openmetadata/ingestion:1.8.9` Airflow container (`PIPELINE_SERVICE_CLIENT_ENABLED=true`), i.e. OM scans natively; the enhanced webhook (`new_openmetadata_webhook_lambda`, deployed as `EnhancedOmWebhookLambda`) is warehouse-agnostic by design. **The lambda-generalization plan is shelved pending confirmation with Ahmed.** Real fix likely = configure OM's native per-warehouse ingestion pipeline, an OMD/infra-owned concern.

**Still open:**
- Confirm with Ahmed (infra/OMD owner): does OM native Airflow do the per-warehouse scan now? Is the container lambda dead? What is meant to populate OneTen's catalog?
- platform-core #841 (OM 1.8 webhook payload parsing) — independent, verified mergeable, review-gated.

Architecture: `platform-saas-ai-context/docs/architecture/SNOWFLAKE_OMD_INGESTION.md` (corrected).

### Day 1 — 2026-06-15 (UPDATE: OMD/BYOW fixed + deployed + verified)

Supersedes the "root cause found, NOT yet fixed" note above — it's now **fixed, merged, and deployed to staging**. The live path is OM 1.8.9 **native AutoPilot** ingestion (no external scanner): `v2.ts` registers the DatabaseService under a canonical `<workspaceId>_<provider>_ingestion` name + triggers AutoPilot → table-sync webhook → workspace-resolver routes by uuid prefix → enrichment (description + 1536-dim embedding in Redis) → retrieval/analysis.

**Merged + deployed to staging (platform-core):**
- #842 — deprecate the 2 dead OMD scanners (banners + DEPRECATED.md)
- #843 — AutoPilot trigger interpolation + full Snowflake connection forwarding (v2.9.0.17; AutoPilot contract verified live, HTTP 200)
- #847 — webhook workspace routing via service-name uuid prefix, not the static header (v2.9.0.19; **UAT-verified live** — wrong-header event re-routed to correct workspace)
- #849 — canonical service naming so ALL warehouses auto-route, idempotent rename no duplicates (v2.9.0.20)
- #818 — superadmin cascade-delete (`deleteTransformationServiceAsAdmin` + `deleteDataAssetAsAdmin`) for **warehouse switching** (Snowflake↔Redshift teardown) (v2.9.0.21)
- #841 — OM 1.8 single-event payload parse + py3.9 fix (table-sync webhook) — merged, promote pending

**Verified live on staging:** OM 1.8.9 = 171 catalogued tables; Redis = 333 asset embeddings; Snowflake auto-route+embed proven end-to-end (webhook replay). The dev.test+system.admin.1 user IS_A SuperAdmin/SystemAdmin (drives the cascade-delete mutations without workspace membership).

**Still open:** Redshift full live UAT (code-complete + deployed; needs a real Redshift warehouse-add to exercise end-to-end). Embeddings store = Redis/RediSearch, not Neo4j (`graphrag_retrieval` queries Redis).

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
