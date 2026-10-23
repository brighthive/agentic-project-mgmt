# Kuri at Brighthive: One Year of Accomplishments

**Window:** 2025-10-23 → 2026-10-23 · **Scope:** Brighthive repositories only (`brighthive`, `brighthive-dbt` GitHub orgs) · **Prepared:** 2026-10-23

Every claim below points to a pull request (PR), commit, ticket or file you can open. Org-level numbers come from the other documents in this folder, so this narrative and those documents never disagree. Per-repo counts were measured with `git log` and the GitHub search API (commands in [Sources](#sources)).

**Legend:** 🟢 live in production · 🟡 on staging or merged to the integration branch · ⚪ built, not deployed or merged · ⚠️ caveat stated on purpose

---

## The year in numbers

| Metric | Year before (2024-10-23 → 2025-10-22) | This year | Source |
|---|---|---|---|
| Merged PRs authored by Kuri | 0 | **1,931** | `METRICS.md`, Delivery |
| Merged PRs, whole org | 927 | **2,861** (3.1×) | `METRICS.md` |
| Releases published, whole org | 145 | **378** (2.6×) | `METRICS.md` |
| Repos with merged PRs | 12 | **29** | `METRICS.md` |
| Test files: `brightbot` · `platform-core` · `webapp` | 10 · 3 · 37 | **413 · 237 · 220** | `METRICS.md`, Repo structure |
| End-to-end test suite | none | **571 tests across 8 surfaces**, 3 CI workflows | `CICD-AND-E2E.md` |
| Commits in conventional `type(scope): description` form | 12.3% | **72.8%** | `STORY.md` |
| Written engineering contracts (CLAUDE.md / AGENTS.md) | 0 | **35 across 8 repos** | `STORY.md` |
| Specs · architecture decision records (ADRs) | 0 · 0 | **126 specs · ADRs in 5 repos** | `STORY.md` |
| Planning record | 69-idea backlog, no delivery epics | **1,507 Jira issues under 48 epics**, 88.6% under an epic, 97.7% with a description | `METRICS.md`, Jira |

**Merged PRs by Kuri, per repo (this year):**

| Repo | Merged PRs | Repo | Merged PRs |
|---|---|---|---|
| `brightbot` (BrightAgent) | 557 | `brighthive-e2e` | 92 |
| `brighthive-platform-core` | 459 | `platform-saas-ai-context` | 46 |
| `brighthive-webapp` | 281 | `brightagent-engineering-runner` | 9 |
| `agentic-project-mgmt` | 194 | `loopcapital-dbt-demo` | 8 |
| `brightbot-slack-server` | 129 | `brighthive-scripts` | 6 |
| `brightagent-v3` | 111 | `brightportal-webapp` | 1 |

⚠️ Raw commit counts are much higher (about 15,000) and mostly hourly auto-save checkpoints. Quote merged PRs, never raw commits.

---

## Ten things that matter most

1. 🟢 **Shipped Brighthive 3.0 to production** (2026-07-21): live notifications on one shared Signal Catalog, across Slack, email, webhooks and Microsoft Teams.
2. 🟢 **Built BrightSignals and the Slack app**: BrightAgent inside customers' Slack, plus proactive data-quality and pipeline alerts.
3. 🟡 **Made every permission decision go through one default-deny check**, rolled out in shadow mode first, then enforced; closed 16 authorization gaps.
4. 🟡 **Gave agent actions a tamper-resistant audit trail and fail-closed personal-data (PII) masking** at every boundary.
5. 🟡 **Opened BrightAgent to outside AI clients over MCP (Model Context Protocol)**, with a permissions matrix and confirmation on write tools; enterprise Okta sign-in for it.
6. 🟡 **Taught BrightAgent to watch customer pipelines and propose fixes** as reviewable PRs; auto-merge is blocked in code.
7. 🟡 **Made BrightAgent warehouse-agnostic**: Snowflake, Azure Synapse, SQL Server, Redshift, Postgres, Databricks, with lineage per engine.
8. 🟢 **Created the platform's end-to-end suite from nothing**: 571 tests across 8 surfaces, including a read-only production smoke test.
9. **Rebuilt how engineering runs**: tests, CI, specs, ADRs, conventional commits, Claude PR review on 26+ repos, and project management as reproducible, agent-run artifacts.
10. ⚪ **Designed the next-generation BrightAgent (v3)** on CEMAF with AWS Bedrock as the only model provider; the foundation is built, cutover has not started.

---

## 1. Product shipped to customers

### Brighthive 3.0 and BrightSignals 🟢
- **Outcome:** customers get notifications they can trust, and BrightSignals, a new product surface, pushes data-quality and pipeline alerts to Slack, email, webhooks and Microsoft Teams.
- **How:** one shared Signal Catalog replaced each screen's own alert list, and a CI check blocks drift from it. A notification dispatcher (EventBridge and DynamoDB Stream) publishes with idempotency keys and severity filtering.
- **Evidence:** `brighthive-webapp` 3.0.0 bump #1353/#1356 and production promotion `76ae95d1` (2026-07-21); catalog #1343, drift guard #1345, severity #1346, Teams #1309/#1310; `brightbot-slack-server` #16, #17 (BrightSignals launch, 2026-04-24); `brighthive-platform-core` #747, #1104, #1108, #1067 (Teams).

### BrightAgent in Slack 🟡
- **Outcome:** customers use BrightAgent directly in their Slack workspace.
- ⚠️ Merged to `origin/main` (38 commits); which environment serves it was not verified in this pass.
- **How:** Slack OAuth install, three-tier workspace auth, multi-tenant bot tokens, an MCP router with fan-out search, streamed reasoning, and image, table and S3 attachments.
- **Evidence:** `brightbot-slack-server` `9fef655` (2026-01-29), router v2 (2026-02-04), OAuth install `1cd8fa5` (2026-02-10), #15, #20, #21, #38, #39.

### Real data instead of mock screens 🟡
- **Outcome:** dashboards, observability and health pages show measured data; signals nothing measures were removed instead of faked.
- **Evidence:** `brighthive-webapp` #1146 (observability), #1321/#1332 (KPIs), #1319/#1331 (context pages), #1066 (health checks), #1424 and #1483 (unmeasured or stale signals shown honestly), #1441/#1452 (fake "Enforced" toggles removed).

### Project health on the Workflows page 🟡
- **Outcome:** one page tells a team whether a data project is healthy: quality rules by stage, open problems per asset, agent runs waiting for input, and who owns it.
- **Evidence:** `brighthive-webapp` #1492, #1495, #1496, #1497, #1500, #1501 (BH-1626, 2026-10-12/13).

### BrightRoutines 🟡
- **Outcome:** BrightAgent notices requests that recur in chat and offers to schedule them.
- **How:** recurring-pattern detection with a model judge that must pass a recall floor and a calibration-error ceiling before promotion; scheduling, dismiss and delivery targets with SQL and artifact provenance.
- **Evidence:** epic BH-876 (157 commits in code repos, 64 of 118 tickets done, `MILESTONES.md`); `brightbot` #765–#795, #1026; `brighthive-platform-core` #981, #988–#1002, #1181; `brighthive-webapp` #1273–#1277, #1420.

---

## 2. Trust, security and governance

### One authorization engine, rolled out safely 🟡
- **Outcome:** every permission decision goes through one auditable, default-deny check, switched on one action at a time instead of all at once.
- **How:** a single `authorize()` decision backed by a permission matrix; a SHADOW mode that logs decisions before enforcing; attribute-based conditions (ABAC); a `checkAccess` query; agent-side READ checks with data-sensitivity rules.
- **Evidence:** `brighthive-platform-core` #1234, #1238–#1240 (2026-08-28), #1254, #1255, #1257, #1293 (default permission set, 16 enforced gaps closed, 2026-09-06), #1317, #1318; `docs/adr/0003-governance-enforcement-ramp.md`; `brightbot` #1046, #1064, #1109; admin editors in `brighthive-webapp` #1442, #1448, #1453; epic BH-1464.

### Audit trail and personal-data protection 🟡
- **Outcome:** agent actions leave a structured, tamper-resistant record, and personal data is masked wherever the agent touches data; masking fails closed.
- **How:** audit event types, an `@audit_action` decorator, citations carried through agent state, a write-once (WORM) log group; PII masking that follows column lineage (closing an alias bypass and a CTE gap); a credential scrubber fixed after an audit found it leaking; a read-only SQL guard.
- **Evidence:** `brightbot` #654–#668 (BH-695, 2026-06-22), #777, `274dcd73`, #946, #1047, #1051, #1057–#1059; specs `docs/specs/SPEC-AUDIT-LOG.md`, `SPEC-BH-1086-agent-pii-masking-boundary.md`; `brighthive-platform-core` #919; epic BH-1084.

### Enterprise sign-in with Okta 🟡
- **Outcome:** enterprise customers sign in through their own Okta to reach Brighthive and its MCP endpoint, with accounts created on first login.
- **How:** identity-provider setup as code (secrets resolved at deploy time, never in source), just-in-time account creation in platform-core, an opt-in SMS second factor, rollback runbooks.
- **Evidence:** `brighthive-okta-idp-cdk` `7e277ab` (2026-06-17), deployed to staging `4c9a063` (2026-06-21, SPEC-BH-676); `brighthive-platform-core` #910, #941 (BH-674); `brightbot` `docs/specs/SPEC-BB-OKTA-FEDERATED.md`; customer guides `brighthive-docs` #22, #24.

---

## 3. BrightAgent capabilities

### MCP tool platform for outside AI clients 🟡
- **Outcome:** Claude.ai, Cursor, Claude Code and custom clients can use BrightAgent's tools on workspace data under permission controls.
- **How:** a remote MCP server with two layers of auth; tools exposed in 7 phases behind a permissions matrix (scopes, profiles, per-tool cells), confirmation on write tools, default-deny scopes; production network routes; project lifecycle, run and health tools (Oct 2026).
- **Evidence:** `brightbot` #497, #572, #582–#591 (BH-115), #1062, #1095–#1101, #1150; `brighthive-platform-core` #887, #1079; epics BH-115 (77 commits) and BH-1181 (85 commits, 15 of 72 tickets done).

### Proactive pipeline monitoring and fix loop 🟡
- **Outcome:** BrightAgent watches customer pipelines on a schedule, diagnoses failures and opens a minimal fix PR for a human to approve. Agent PRs are never auto-merged.
- **Evidence:** `brightbot` #813, #815, #825, #826, #829, #835, #850 (2026-07-14/15), #955, #985, #1043, #1139, #1140, #1151; `brighthive-platform-core` #1062, #1172; epic BH-1036 (130 commits in code repos); live demo in `loopcapital-dbt-demo` fix PR #1 (`9eba3b8`, 2026-07-15).

### Warehouse-agnostic data engine 🟡
- **Outcome:** BrightAgent works across Snowflake, Azure Synapse, SQL Server, Redshift, Postgres and Databricks instead of being tied to one engine.
- **How:** Synapse T-SQL and SQL Server providers, a cross-engine write layer, native lineage per engine, a six-tier lineage model that assigns tiers from structure rather than table names, Snowflake key-pair auth and the semantic-view lifecycle; Synapse ingestion routed by warehouse type.
- **Evidence:** `brightbot` #433, #552, #931, #966–#976 (2026-07-31), #1077; `brighthive-platform-core` #706, #1069, ADRs `0001-engine-agnostic-lineage-and-staged-quality.md`, `0002-name-free-tiering-three-axis-lineage.md` (Accepted); `brighthive-data-organization-cdk` #139, #149, `9cd9e89`; `brighthive-webapp` #1031, #1311/#1312, #1414, #1429, #1430; epics BH-624, BH-1370.

### On-premises engineering runner ⚪
- **Outcome:** customers whose dbt and SSIS projects live on their own network can use BrightAgent with no inbound firewall rule.
- **How:** an MCP plugin that runs dbt Core next to the files, fences file access, has the agent draft while a human applies, and reports outward without losing runs; an outbound-only job queue in platform-core.
- **Evidence:** `brightagent-engineering-runner` #1–#9 (2026-08-13/14); `brighthive-platform-core` #1198, #1199; ADRs in `agentic-project-mgmt/docs/adr/0001–0003`; epics BH-1403, BH-1421.

### dbt agent and dbt MCP server 🟡
- **Evidence:** dbt agent rebuilt as a ReAct agent, `brightbot` #449 (2026-04-12), #510, #1068, #1069; dbt MCP server made deployable on ECS Fargate with per-environment deploys and closed auth gaps (keys only in headers, 503 when unconfigured), `brightbot-dbt-MCP-server` #31, `45261cf`, `6214253` (BH-324).

---

## 4. Next-generation architecture ⚪

### BrightAgent v3 on CEMAF and AWS Bedrock
- **Outcome:** a design for the next BrightAgent where every model call is auditable, costed and access-controlled per tenant through AWS.
- **How:** Brighthive's own framework CEMAF (Context Engineering Multi-Agent Framework) replaces LangGraph; Bedrock is the only model provider; a step-by-step run engine with prompt caching and streaming; evaluation checks that can stop a run; a 100-persona evaluation harness with nightly TPC-H runs and regression gates on PRs.
- **Evidence:** `brightagent-v3` `b4e46b7` (2026-04-20), `89c5fb4`, PRs #101–#115 (2026-05-28); ADRs `docs/adr/0001-cemaf-over-langgraph.md`, `0002-bedrock-only-for-llm.md`, `0006-governance-tax-over-raw-speed.md`; epic BH-453.
- ⚠️ **Not live.** The repo's own cutover gauge reads **9.6% on develop** (13.0% on a PR branch), and 174 capabilities are tracked for migration (`brightagent-v3/docs/MIGRATION_STATE.md`, `docs/MIGRATION_MAP.md`). Present this as architecture and foundation, not a finished migration.

### Leaving hosted LangGraph Cloud
- **Outcome:** a fallback that would retire the hosted LangGraph Cloud service: conversation threads in DynamoDB and streaming served by the app itself.
- **Evidence:** platform-core tables and session store merged, `brighthive-platform-core` #1036, #1033 (2026-07-17).
- ⚠️ The agent-side change lives on branch `drchinca/BH-477/langgraph-cloud-detach` and is **not merged** into `brightbot` develop (verified: 0 BH-477 commits on `origin/develop`).

---

## 5. Engineering foundations

### Quality and testing
- **Outcome:** the platform went from a handful of tests and almost no CI to tested, reviewed, gated delivery.
- **Evidence:** test files `brightbot` 10 → 413, `platform-core` 3 → 237, `webapp` 37 → 220; CI workflow files 1 → 7, 3 → 12, 1 → 3 (`METRICS.md`). A 16-scenario agent evaluation framework with SQL-injection and PII cases and LangSmith cost tracking (`brightbot`, January 2026, #623).

### The end-to-end suite 🟢
- **Outcome:** for the first time one repo verifies the deployed platform across auth, GraphQL, agent routes, agents, semantic views, MCP, graph integrity and the web app, in all three environments.
- **Evidence:** `brighthive-e2e` created `9e9b962` (2026-06-18); 571 tests (`CICD-AND-E2E.md`); `health-check.yml`, `prod-smoke.yml` (read-only production smoke, #68), `tracker.yml`; PII across MCP and agent boundaries #43, #85; cross-workspace refusals #102, #107; MCP governance end to end #88.

### Load testing infrastructure
- **Evidence:** `brighthive_testing_infrastructure_cdk` (2026-01-03/05): 5 CDK stacks (network, data lake, Redshift, EMR, monitoring), 16 scenarios, synthetic data, safe teardown (#2), for stress-testing BrightAgent (BH-107).

### How work is specified and reviewed
- **Evidence:** 126 specs and spec-driven templates (`agentic-project-mgmt` `d79848d`); ADRs in 5 repos; 35 CLAUDE.md/AGENTS.md contracts; conventional commits 12.3% → 72.8%; automated Claude PR review rolled out to 26+ repos on 2026-02-05, with fixes on 2026-02-09 and 2026-04-09; moves from Poetry and Pipenv to `uv`; a full local stack on LocalStack (`brighthive-platform-core` #769, #802, #804).

### Project management as code
- **Outcome:** sprint records, release notes, board reporting and year-one metrics are reproducible artifacts, not meetings and memory.
- **Evidence:** `agentic-project-mgmt` (created `975681b`, 2026-01-22): sprint folders 1–16 and `SPRINTS.md`, `BOARD_REPORT_OCT_2025_MAY_2026.md`, checked-in skills, the year-one evidence pack, with the collectors and renderers in `scripts/yearone/`.

### Onboarding and architecture knowledge
- **Evidence:** onboarding as a sequence of `make` commands with per-person encrypted credential bundles across 15 AWS accounts (`agentic-project-mgmt` #12, #71); the platform architecture and runbook reference `platform-saas-ai-context` (created `b5cd240`, 2026-01-19) with auth ADRs (#22), ADR-016 permission matrix on Neo4j (#48), ADR-009 Claude Code via Bedrock (#5), an engine-agnostic semantic-view standard (#26) and production runbooks (#25, #27, #28, #50); customer docs rewritten with the current brand (`brighthive-docs` PRs #19–#21).

---

## 6. Customer trials

Each trial below has engineering evidence in the repos. Outcomes (revenue, signatures) are not recorded there and belong in `business.md`.

| Trial | Engineering evidence | Status |
|---|---|---|
| Loop Capital | SQL Server and Teams support, the fix-it dbt demo (`loopcapital-dbt-demo`, PR #1, 2026-07-15), SQL Server EC2 and Bedrock knowledge-base stacks (`agentic-project-mgmt` #108, #128, #176), epic BH-1245 | 🟡 trial delivered |
| Longaeva | 14-day pre-trial and 14 golden success paths, epics BH-526 (74 commits in code repos) and BH-601 (32 commits); 10 of 10 use cases with gap analysis (`agentic-project-mgmt` #17) | 🟡 proof of concept |
| CPG demo (NUSA dataset) | dbt star schema, data-quality fixes and lineage to Power BI (`brighthive-demo-transform`, 2026-04-07/08) | 🟡 demo |

---

## Timeline

| Month | Milestone |
|---|---|
| Oct–Nov 2025 | First commit (2025-10-23, `brightbot`); CI rebuilt, `uv`, linting and code standards |
| Jan 2026 | Agent evaluation framework and cost tracking; load-test infrastructure; Slack server auth; architecture reference and project-management repos created |
| Feb 2026 | Slack OAuth install and MCP router v2; Claude PR review across 26+ repos; product docs rewrite and rebrand |
| Apr 2026 | BrightAgent v3 foundation; Synapse support; dbt ReAct agent; **BrightSignals launched (Apr 24)** |
| May 2026 | v3 agent workstreams and evaluation harness; navigation restructure; board report; Longaeva proof of concept |
| Jun 2026 | Remote MCP server and governed tools; Okta SSO on staging; audit epic; **end-to-end suite created (Jun 18)** |
| Jul 2026 | BrightRoutines; pipeline monitoring and fix loop; Loop Capital trial; cross-engine lineage; **Brighthive 3.0 in production (Jul 21)** |
| Aug 2026 | On-premises engineering runner; permission-matrix editor; authorization engine in shadow mode |
| Sep 2026 | Default-deny authorization with ABAC, 16 gaps closed; lineage-aware PII masking |
| Oct 2026 | Project lifecycle over MCP; project health on the Workflows page; year-one evidence pack |

---

## Stated plainly

- ⚠️ **Concentration risk.** 62% of Jira work items are assigned to Kuri, and he authored 75.2% of code PRs in Sprint 15. The foundations make hand-off possible; the team has not yet taken it up (`METRICS.md`, `SPRINTS.md`).
- ⚠️ **Jira understates delivery.** 362 items are marked Done, but 878 have merged code behind them; the true completed count sits in that range (`METRICS.md`, Jira status vs shipped code).
- ⚠️ **Human review fell.** PRs reviewed by someone other than the author went from 95.7% to 49.1%, and approvals from 95.7% to 11.5%. Kuri's own PRs were approved by someone else 0.7% of the time (`METRICS.md`). The sample is 2,641 of 2,861 merged PRs.
- ⚠️ **Not live yet:** BrightAgent v3 and the move off LangGraph Cloud (see section 4). The on-premises runner is built but not deployed to a customer.
- ⚠️ **Agent-assisted work.** Some trial artifacts were written by BrightAgent under Kuri's direction (for example 38 `BrightAgent[bot]` commits in `loopcapital-dbt-demo`).
- Revenue, customer signatures and headcount are not in any repo; see [business.md](business.md).

---

## Sources

- **Org metrics:** [METRICS.md](METRICS.md), [STORY.md](STORY.md), [MILESTONES.md](MILESTONES.md), [CICD-AND-E2E.md](CICD-AND-E2E.md) in this folder. Epic commit counts are code repos only, documentation repos excluded, regenerated 2026-10-23.
- **Merged PRs per repo:** one call per repo, `gh api "search/issues?q=repo:<owner>/<repo>+is:pr+is:merged+author:drchinca+merged:>=2025-10-23&per_page=1" --jq .total_count`, run 2026-10-23.
- **Commits:** `git log --all --no-merges -i --since=2025-10-23 --author=drchinca --author=kuri`, auto-save and WIP checkpoints excluded.
- **Spot-checked against git on 2026-10-23:** BH-477 not on `brightbot` `origin/develop`; 3.0 promotion `76ae95d1`; #1293 subject; 571 e2e tests; Okta staging deploy `4c9a063`; v3 cutover gauge (corrected from an outdated 37.9% to the current 9.6%).
