# Sprint 9 Release Notes

**Period**: Apr 20 – May 2, 2026 | **Duration**: 12 days
**Status**: Unofficial release — date-range close, Sprint 8 still active in Jira
**Theme**: BrightSignals ships, Bedrock Converse migration, Task Scheduler MVP

---

## Summary Metrics

| Metric | Value |
|--------|-------|
| Tickets Resolved (in window) | 7 |
| Story Points Done | 0 (all unpointed) |
| PRs Merged | 27 |
| Lines Added | 22,543 |
| Lines Deleted | 6,837 |
| Repos Touched | 5 |
| Engineering Authors | 4 (full team) |
| Major Capabilities Shipped | 4 |

---

## Completed Tickets

All 7 tickets are Kuri's streaming/adapter cluster (BH-431 through BH-441):

| Ticket | Summary | Resolved |
|--------|---------|----------|
| [BH-431](https://brighthiveio.atlassian.net/browse/BH-431) | feat(adapter): Neo4jGraphStore + Neo4jConnectionConfig | 2026-04-25 |
| [BH-432](https://brighthiveio.atlassian.net/browse/BH-432) | feat(adapter): BrightHivePlatformAdapter + Cognito login/refresh | 2026-04-25 |
| [BH-437](https://brighthiveio.atlassian.net/browse/BH-437) | fix(streaming): repair state machine — STABILIZED reachable + linear FSM guards | 2026-04-30 |
| [BH-438](https://brighthiveio.atlassian.net/browse/BH-438) | fix(streaming): remove prototype "[refined]" placeholder from production path | 2026-05-01 |
| [BH-439](https://brighthiveio.atlassian.net/browse/BH-439) | refactor(streaming): Py 3.14 compliance + deduplicate SpanStreamProcessor | 2026-05-01 |
| [BH-440](https://brighthiveio.atlassian.net/browse/BH-440) | test(streaming): wire SpanStreamProcessor into suite + SSE ordering invariants | 2026-05-02 |
| [BH-441](https://brighthiveio.atlassian.net/browse/BH-441) | test(streaming): Hypothesis property tests + clock injection (kill 21s of time.sleep) | 2026-05-02 |

---

## Pull Requests by Repository

### brighthive-platform-core (8 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#736](https://github.com/brighthive/brighthive-platform-core/pull/736) | Apr 20 | +280/-30 | Kuri | fix(slack): make createSlackServiceUser idempotent |
| [#745](https://github.com/brighthive/brighthive-platform-core/pull/745) | Apr 20 | +306/-62 | Kuri | build: Develop => Staging (4/20/2026) |
| [#746](https://github.com/brighthive/brighthive-platform-core/pull/746) | Apr 29 | +58/-0 | Harbour | fix(upload): Add duplicate check to data asset and files |
| [#747](https://github.com/brighthive/brighthive-platform-core/pull/747) | Apr 25 | +648/-0 | Kuri | feat(notifications): dispatcher Lambda for EventBridge + DynamoDB streams |
| [#748](https://github.com/brighthive/brighthive-platform-core/pull/748) | Apr 23 | +36/-1 | Ahmed | fix: prevent duplicate data asset creation for mixed-case filenames |
| [#749](https://github.com/brighthive/brighthive-platform-core/pull/749) | Apr 23 | +602/-63 | Ahmed | Develop => Staging |
| [#750](https://github.com/brighthive/brighthive-platform-core/pull/750) | Apr 29 | +881/-89 | Harbour | feat(scheduler): MVP agnostic scheduler |
| [#751](https://github.com/brighthive/brighthive-platform-core/pull/751) | Apr 29 | +1,587/-89 | Harbour | Merge develop => staging |

### brightbot-slack-server (8 PRs) — BrightSignals end-to-end

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#15](https://github.com/brighthive/brightbot-slack-server/pull/15) | Apr 21 | +1,569/-378 | Kuri | feat(slack): multi-tenant auth, mention filter, async handlers, file attachments |
| [#16](https://github.com/brighthive/brightbot-slack-server/pull/16) | Apr 25 | +2,443/-0 | Kuri | feat(brightsignals): proactive Slack notifications — subscriptions, poller, delivery |
| [#17](https://github.com/brighthive/brightbot-slack-server/pull/17) | Apr 25 | +52/-5 | Kuri | docs(brightsignals): rebrand product surfaces (engineering names unchanged) |
| [#18](https://github.com/brighthive/brightbot-slack-server/pull/18) | Apr 25 | +7/-2 | Kuri | feat(notifications): surface asset UUID in Slack messages |
| [#19](https://github.com/brighthive/brightbot-slack-server/pull/19) | Apr 26 | +238/-1 | Kuri | docs(brightsignals): operator install + ops guide |
| [#20](https://github.com/brighthive/brightbot-slack-server/pull/20) | Apr 26 | +1,089/-32 | Kuri | feat(attachments): s3:// URI support for BrightAgent artifacts (Tier A) |
| [#21](https://github.com/brighthive/brightbot-slack-server/pull/21) | Apr 27 | +596/-6 | Kuri | feat(attachments): parse <BH_ARTIFACTS> envelope, route by type (Tier B) |
| [#22](https://github.com/brighthive/brightbot-slack-server/pull/22) | Apr 27 | +16/-0 | Kuri | fix(ci): complete Pulumi config in deploy + preview workflow |

### brighthive-webapp (5 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#1076](https://github.com/brighthive/brighthive-webapp/pull/1076) | Apr 24 | +484/-182 | Harbour | feat(analytics): Add schedule support to UI |
| [#1077](https://github.com/brighthive/brighthive-webapp/pull/1077) | Apr 29 | +565/-60 | Harbour | fix(upload): Add duplicate check to data asset and files |
| [#1079](https://github.com/brighthive/brighthive-webapp/pull/1079) | Apr 29 | +399/-232 | Harbour | feat(scheduler): MVP agnostic scheduler |
| [#1080](https://github.com/brighthive/brighthive-webapp/pull/1080) | Apr 29 | +22/-52 | Marwan | fix(ag-grid): pass serverSideDatasource as prop instead of onGridRead |
| [#1081](https://github.com/brighthive/brighthive-webapp/pull/1081) | Apr 29 | +3,325/-632 | Harbour | Merge develop => staging |

### brightbot (3 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#457](https://github.com/brighthive/brightbot/pull/457) | Apr 28 | +1,877/-2,300 | Marwan | fix: migrate ChatBedrock to ChatBedrockConverse and upgrade deepagents |
| [#458](https://github.com/brighthive/brightbot/pull/458) | Apr 29 | +579/-113 | Harbour | feat: MVP agnostic scheduler |
| [#459](https://github.com/brighthive/brightbot/pull/459) | Apr 29 | +2,456/-2,413 | Harbour | Merge develop => staging |

### brighthive-data-organization-cdk (3 PRs)

| PR | Date | Lines | Author | Title |
|----|------|-------|--------|-------|
| [#144](https://github.com/brighthive/brighthive-data-organization-cdk/pull/144) | Apr 21 | +1,848/-48 | Marwan | Staging => Main (4/8/2026) |
| [#152](https://github.com/brighthive/brighthive-data-organization-cdk/pull/152) | Apr 21 | +566/-43 | Ahmed | Develop => Staging |
| [#153](https://github.com/brighthive/brighthive-data-organization-cdk/pull/153) | Apr 29 | +14/-4 | Ahmed | Update: synapse logic with docs, role assumption |

---

## Capability Highlights

### BrightSignals — Proactive Notifications (NEW)

BrightHive's first proactive product surface. Agent reaches out to user via Slack — not the other way around.

- Subscriptions + poller architecture (per-user, per-channel)
- Notification dispatcher Lambda (EventBridge + DynamoDB streams)
- S3 artifact handoff (Tier A: s3:// URIs)
- `<BH_ARTIFACTS>` envelope parser (Tier B: structured payload routing)
- Asset UUID surfaced in Slack messages
- Operator install + ops guide

**Architecture**: BrightAgent emits notification events → DynamoDB Stream → EventBridge → dispatcher Lambda → slack-server delivery → user channel.

### Bedrock Converse Migration

`ChatBedrock` → `ChatBedrockConverse` migration in brightbot, plus deepagents framework upgrade. Required for the LangGraph → Bedrock AgentCore migration path.

### Task Scheduler MVP

First scheduling primitive in the platform — agnostic scheduler service in core, UI in webapp, agent integration in brightbot. Foundational for recurring agent runs and periodic ingestion checks.

### Streaming Platform Hardening

7 backend tickets on the span streaming subsystem: FSM repair, property-based tests via Hypothesis, clock injection (eliminated 21 seconds of `time.sleep` from test suite), Py 3.14 compliance, prototype removal from production path.

### Production Stability

- Slack `createSlackServiceUser` made idempotent (BH-fix branch)
- Mixed-case filename duplicate detection
- Upload duplicate check (server + UI)
- AG Grid serverside datasource fix
- Synapse role assumption hardening

---

## Links

- [Sprint 9 Summary](./SUMMARY.md)
- [Marketing Release Notes](./MARKETING_RELEASE_NOTES.md)
- [Validation Report](./VALIDATION_REPORT.md)
- [Slack Post](./SLACK_POST.md)
- [Q4 2025 → Q2 2026 Board Report](../BOARD_REPORT_OCT_2025_MAY_2026.md)
