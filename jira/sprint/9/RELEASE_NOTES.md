# Sprint 9 Release Notes — v2

**Period**: Apr 20 – May 4, 2026 | **Duration**: 14 days
**Status**: Unofficial release — date-range close, Sprint 8 still active in Jira
**Theme**: BrightSignals ships, BrightStudio Skills, Bedrock Converse migration, Task Scheduler MVP, UAT evals + Vega-Lite

---

## Summary Metrics (v2)

| Metric | Value |
|--------|-------|
| Tickets Resolved | 17 (7 streaming + 10 retro) |
| Story Points Done | 39 (retro estimates) |
| PRs Merged | 39 |
| Lines Added | 42,492 |
| Lines Deleted | 11,653 |
| Repos Touched | 5 |
| Engineering Authors | 4 (full team) |
| Major Capabilities Shipped | 6 |
| PR-Ticket Linkage | 53.8% |

---

## Completed Tickets (17 total)

### Streaming/Adapter cluster (7 — Kuri)

| Ticket | Summary | Resolved |
|--------|---------|----------|
| [BH-431](https://brighthiveio.atlassian.net/browse/BH-431) | feat(adapter): Neo4jGraphStore + Neo4jConnectionConfig | 2026-04-25 |
| [BH-432](https://brighthiveio.atlassian.net/browse/BH-432) | feat(adapter): BrightHivePlatformAdapter + Cognito login/refresh | 2026-04-25 |
| [BH-437](https://brighthiveio.atlassian.net/browse/BH-437) | fix(streaming): repair state machine — STABILIZED reachable + linear FSM guards | 2026-04-30 |
| [BH-438](https://brighthiveio.atlassian.net/browse/BH-438) | fix(streaming): remove prototype "[refined]" placeholder from production path | 2026-05-01 |
| [BH-439](https://brighthiveio.atlassian.net/browse/BH-439) | refactor(streaming): Py 3.14 compliance + deduplicate SpanStreamProcessor | 2026-05-01 |
| [BH-440](https://brighthiveio.atlassian.net/browse/BH-440) | test(streaming): wire SpanStreamProcessor into suite + SSE ordering invariants | 2026-05-02 |
| [BH-441](https://brighthiveio.atlassian.net/browse/BH-441) | test(streaming): Hypothesis property tests + clock injection | 2026-05-02 |

### Retroactive tickets (10 — created May 2-4, transitioned Done)

| Ticket | Summary | Assignee | Epic | Pts |
|--------|---------|----------|------|-----|
| [BH-443](https://brighthiveio.atlassian.net/browse/BH-443) | [RETRO] Task Scheduler MVP — agnostic cross-repo | Harbour | BH-172 | 8 |
| [BH-444](https://brighthiveio.atlassian.net/browse/BH-444) | [RETRO] Scheduler UI bug fixes + result display | Harbour | BH-172 | 5 |
| [BH-445](https://brighthiveio.atlassian.net/browse/BH-445) | [RETRO] Skills for BrightStudio | Harbour | BH-260 | 5 |
| [BH-446](https://brighthiveio.atlassian.net/browse/BH-446) | [RETRO] Bedrock Converse migration | Marwan | BH-172 | 8 |
| [BH-447](https://brighthiveio.atlassian.net/browse/BH-447) | [RETRO] Upload duplicate detection (cross-repo) | Harbour | BH-172 | 3 |
| [BH-448](https://brighthiveio.atlassian.net/browse/BH-448) | [RETRO] Schedule support in catalog UI | Harbour | BH-172 | 3 |
| [BH-449](https://brighthiveio.atlassian.net/browse/BH-449) | [RETRO] Login PW redundant check removal | Harbour | BH-173 | 1 |
| [BH-450](https://brighthiveio.atlassian.net/browse/BH-450) | [RETRO] AG Grid serverside fix | Marwan | BH-173 | 1 |
| [BH-451](https://brighthiveio.atlassian.net/browse/BH-451) | [RETRO] Mixed-case filename duplicate fix | Ahmed | BH-173 | 2 |
| [BH-452](https://brighthiveio.atlassian.net/browse/BH-452) | [RETRO] Synapse role assumption + docs | Ahmed | BH-171 | 3 |

---

## Pull Requests by Repository (39 total)

### brightbot-slack-server (10 PRs) — BrightSignals + UAT framework

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#15](https://github.com/brighthive/brightbot-slack-server/pull/15) | Apr 21 | +1,569/-378 | Kuri | feat(slack): multi-tenant auth, mention filter, async handlers, file attachments |
| [#16](https://github.com/brighthive/brightbot-slack-server/pull/16) | Apr 25 | +2,443/-0 | Kuri | feat(brightsignals): proactive Slack notifications — subscriptions, poller, delivery |
| [#17](https://github.com/brighthive/brightbot-slack-server/pull/17) | Apr 25 | +52/-5 | Kuri | docs(brightsignals): rebrand product surfaces |
| [#18](https://github.com/brighthive/brightbot-slack-server/pull/18) | Apr 25 | +7/-2 | Kuri | feat(notifications): surface asset UUID in Slack messages |
| [#19](https://github.com/brighthive/brightbot-slack-server/pull/19) | Apr 26 | +238/-1 | Kuri | docs(brightsignals): operator install + ops guide |
| [#20](https://github.com/brighthive/brightbot-slack-server/pull/20) | Apr 26 | +1,089/-32 | Kuri | feat(attachments): s3:// URI support (Tier A) |
| [#21](https://github.com/brighthive/brightbot-slack-server/pull/21) | Apr 27 | +596/-6 | Kuri | feat(attachments): parse <BH_ARTIFACTS> envelope (Tier B) |
| [#22](https://github.com/brighthive/brightbot-slack-server/pull/22) | Apr 27 | +16/-0 | Kuri | fix(ci): complete Pulumi config |
| [#23](https://github.com/brighthive/brightbot-slack-server/pull/23) | May 4 | +2,547/-138 | Kuri | feat(uat): direct-call deterministic turn evals + HTTP scenario runner |
| [#24](https://github.com/brighthive/brightbot-slack-server/pull/24) | May 4 | +9,276/-998 | Kuri | Promote develop to staging |

### brighthive-platform-core (10 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#736](https://github.com/brighthive/brighthive-platform-core/pull/736) | Apr 20 | +280/-30 | Kuri | fix(slack): make createSlackServiceUser idempotent |
| [#745](https://github.com/brighthive/brighthive-platform-core/pull/745) | Apr 20 | +306/-62 | Kuri | build: Develop => Staging |
| [#746](https://github.com/brighthive/brighthive-platform-core/pull/746) | Apr 29 | +58/-0 | Harbour | fix(upload): duplicate check on data asset and files (BH-447) |
| [#747](https://github.com/brighthive/brighthive-platform-core/pull/747) | Apr 25 | +648/-0 | Kuri | feat(notifications): dispatcher Lambda for EventBridge + DynamoDB streams |
| [#748](https://github.com/brighthive/brighthive-platform-core/pull/748) | Apr 23 | +36/-1 | Ahmed | fix: prevent duplicate data asset for mixed-case filenames (BH-451) |
| [#749](https://github.com/brighthive/brighthive-platform-core/pull/749) | Apr 23 | +602/-63 | Ahmed | Develop => Staging |
| [#750](https://github.com/brighthive/brighthive-platform-core/pull/750) | Apr 29 | +881/-89 | Harbour | feat(scheduler): MVP agnostic scheduler (BH-443) |
| [#751](https://github.com/brighthive/brighthive-platform-core/pull/751) | Apr 29 | +1,587/-89 | Harbour | Merge develop => staging |
| [#752](https://github.com/brighthive/brighthive-platform-core/pull/752) | May 4 | +72/-24 | Harbour | feat(scheduler): UI bug fixes + scheduler result (BH-444) |
| [#753](https://github.com/brighthive/brighthive-platform-core/pull/753) | May 4 | +72/-24 | Harbour | dev => staging |

### brighthive-webapp (9 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#1017](https://github.com/brighthive/brighthive-webapp/pull/1017) | May 4 | +847/-26 | Harbour | feat(skills): Add skills to BrightStudio (BH-445) |
| [#1076](https://github.com/brighthive/brighthive-webapp/pull/1076) | Apr 24 | +484/-182 | Harbour | feat(analytics): Add schedule support to UI (BH-448) |
| [#1077](https://github.com/brighthive/brighthive-webapp/pull/1077) | Apr 29 | +565/-60 | Harbour | fix(upload): duplicate check (BH-447) |
| [#1079](https://github.com/brighthive/brighthive-webapp/pull/1079) | Apr 29 | +399/-232 | Harbour | feat(scheduler): MVP agnostic scheduler (BH-443) |
| [#1080](https://github.com/brighthive/brighthive-webapp/pull/1080) | Apr 29 | +22/-52 | Marwan | fix(ag-grid): serverSideDatasource as prop (BH-450) |
| [#1081](https://github.com/brighthive/brighthive-webapp/pull/1081) | Apr 29 | +3,325/-632 | Harbour | Merge develop => staging |
| [#1082](https://github.com/brighthive/brighthive-webapp/pull/1082) | May 4 | +727/-273 | Harbour | feat(scheduler): UI bug fixes + result (BH-444) |
| [#1083](https://github.com/brighthive/brighthive-webapp/pull/1083) | May 4 | +2/-7 | Harbour | fix(login): Remove login pw check (BH-449) |
| [#1084](https://github.com/brighthive/brighthive-webapp/pull/1084) | May 4 | +1,576/-306 | Harbour | dev => staging |

### brightbot (7 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#421](https://github.com/brighthive/brightbot/pull/421) | May 4 | +629/-9 | Harbour | feat(skills): Add skills to BrightStudio (BH-445) |
| [#456](https://github.com/brighthive/brightbot/pull/456) | May 4 | +354/-66 | Kuri | feat(visualization): render Vega-Lite to PNG, emit artifact envelope (Tier B) |
| [#457](https://github.com/brighthive/brightbot/pull/457) | Apr 28 | +1,877/-2,300 | Marwan | fix: migrate ChatBedrock to ChatBedrockConverse + deepagents (BH-446) |
| [#458](https://github.com/brighthive/brightbot/pull/458) | Apr 29 | +579/-113 | Harbour | feat: MVP agnostic scheduler (BH-443) |
| [#459](https://github.com/brighthive/brightbot/pull/459) | Apr 29 | +2,456/-2,413 | Harbour | Merge develop => staging |
| [#460](https://github.com/brighthive/brightbot/pull/460) | May 4 | +1,609/-1,468 | Harbour | feat(scheduler): UI bug fixes + result (BH-444) |
| [#461](https://github.com/brighthive/brightbot/pull/461) | May 4 | +2,238/-1,477 | Harbour | dev => staging |

### brighthive-data-organization-cdk (3 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#144](https://github.com/brighthive/brighthive-data-organization-cdk/pull/144) | Apr 21 | +1,848/-48 | Marwan | Staging => Main (4/8/2026) |
| [#152](https://github.com/brighthive/brighthive-data-organization-cdk/pull/152) | Apr 21 | +566/-43 | Ahmed | Develop => Staging |
| [#153](https://github.com/brighthive/brighthive-data-organization-cdk/pull/153) | Apr 29 | +14/-4 | Ahmed | Update: Synapse logic + role assumption (BH-452) |

---

## Capability Highlights

### BrightSignals — Proactive Notifications (NEW PRODUCT SURFACE)

BrightHive's first proactive product surface. Subscriptions + poller + S3 artifact handoff + dispatcher Lambda. Multi-tenant Slack auth with mention filtering and async handlers.

### BrightStudio Skills (May 4) — NEW MAJOR FEATURE (BH-445)

Skills become first-class composable agent capabilities in BrightStudio. Webapp UI to create + attach Skills to personas; brightbot runtime loads + uses them at execution.

### Bedrock Converse Migration (BH-446)

`ChatBedrock` → `ChatBedrockConverse` migration in brightbot, plus deepagents framework upgrade. Foundation for AgentCore.

### Task Scheduler MVP + UI Fixes (BH-443, BH-444, BH-448)

First scheduling primitive. Cross-repo: agnostic core service + UI + agent integration. Plus follow-up UI bug fixes + scheduled run result display.

### UAT Eval Framework + Vega-Lite Visualization (May 4)

Direct-call deterministic turn evals + HTTP scenario runner in slack-server. Vega-Lite render to PNG + artifact envelope emission in brightbot — chart artifacts now flow end-to-end.

### Streaming Platform Hardening

7 backend tickets: FSM repair, Hypothesis property tests, 21s of test latency removed, Py 3.14 compliance, prototype removal.

### Production Stability

- Slack `createSlackServiceUser` made idempotent
- Mixed-case filename duplicate detection (BH-451)
- Upload duplicate check (BH-447)
- AG Grid serverside datasource fix (BH-450)
- Login PW redundant check removal (BH-449)
- Synapse role assumption hardening (BH-452)

---

## Links

- [Sprint 9 Summary](./SUMMARY.md)
- [Marketing Release Notes](./MARKETING_RELEASE_NOTES.md)
- [Validation Report](./VALIDATION_REPORT.md)
- [Slack Post](./SLACK_POST.md)
- [Q4 2025 → Q2 2026 Board Report](../BOARD_REPORT_OCT_2025_MAY_2026.md)
