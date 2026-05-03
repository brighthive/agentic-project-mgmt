# Sprint 9 — Release Summary (Unofficial)

**Period**: Apr 20 – May 2, 2026 | **Duration**: 12 days (planned 14, cut 2 days short — cadence change)
**Status**: Unofficial — no Jira sprint object created. Date-range release.
**Overlap**: Sprint 8 🫐 still active in Jira (Apr 14–28). This release covers Sprint 8 tail end + 4 days of post-Sprint 8 work.

---

## Sprint Stats

```
+-------------------------------------------------+
|         SPRINT 9 — APR 20 to MAY 2, 2026        |
|     12 days (cut 2 days short of May 4 plan)    |
+-----------------------+-------------------------+
| Tickets Resolved      |  7 (in window)          |
| Story Points Done     |  0 (all unpointed)      |
| PRs Merged            |  27                     |
| Lines Changed         |  +22.5K / -6.8K (29.4K) |
| Repos Touched         |  5                      |
| Authors               |  4 (full team)          |
| Major Features        |  3 shipped + 1 hardened |
+-----------------------+-------------------------+
```

**Caveat**: Ticket count is small because Sprint 9 is a release-by-date snapshot, not a planned sprint. Most code shipped this window is from Sprint 8 work (still active in Jira). The 7 resolved tickets are Kuri's streaming/adapter cluster (BH-431 through BH-441), all created and finished within this window.

---

## What Shipped — Major Capabilities

### 🔔 BrightSignals — Proactive Notifications (NEW PRODUCT SURFACE)

End-to-end proactive Slack delivery from BrightAgent to user channels. **9 PRs** across slack-server + platform-core. Owner: Kuri.

| PR | Description |
|----|-------------|
| slack-server #15 | Multi-tenant auth, mention filter, async handlers, file attachments |
| slack-server #16 | Subscriptions + poller + delivery infrastructure (+2,443 lines) |
| slack-server #17 | BrightSignals product rebrand on operator-facing surfaces |
| slack-server #18 | Surface asset UUID in Slack messages |
| slack-server #19 | Operator install + ops guide documentation |
| slack-server #20 | s3:// URI support for BrightAgent artifacts (Tier A) |
| slack-server #21 | <BH_ARTIFACTS> envelope parser, route by type (Tier B) |
| slack-server #22 | CI Pulumi config completion |
| platform-core #747 | Notification dispatcher Lambda for EventBridge + DynamoDB streams |

**Why it matters**: BrightSignals is BrightHive's first proactive surface — agent reaches out to user instead of user reaching to agent. Subscriptions + poller architecture, S3 artifact handoff, multi-tier envelope parsing. This is a foundational capability for the agentic platform.

### 🤖 Bedrock Converse Migration

| PR | Description |
|----|-------------|
| brightbot #457 | Migrate ChatBedrock to ChatBedrockConverse, upgrade deepagents (+1,877/-2,300) |

**Why it matters**: Step in the LangGraph → Bedrock migration. Converse API is AWS's modern unified streaming/tool-use interface. Required to unblock Bedrock AgentCore adoption strategy.

### ⏰ Task Scheduler MVP (Cross-Repo)

| PR | Description |
|----|-------------|
| platform-core #750 | Scheduler MVP — agnostic scheduler service (+881/-89) |
| webapp #1079 | Scheduler MVP — UI integration (+399/-232) |
| brightbot #458 | Scheduler MVP — agent integration (+579/-113) |

**Why it matters**: First scheduling primitive in the platform. Unblocks recurring agent runs, periodic ingestion checks, scheduled quality checks. Owner: Harbour.

### 🧱 Streaming Platform Hardening (7 tickets, Kuri)

| Ticket | Description |
|--------|-------------|
| BH-431 | Neo4jGraphStore + Neo4jConnectionConfig adapter |
| BH-432 | BrightHivePlatformAdapter + Cognito login/refresh |
| BH-437 | Repair FSM — STABILIZED reachable + linear guards |
| BH-438 | Remove prototype "[refined]" placeholder from production path |
| BH-439 | Py 3.14 compliance + deduplicate SpanStreamProcessor |
| BH-440 | Wire SpanStreamProcessor into suite + SSE ordering invariants |
| BH-441 | Hypothesis property tests + clock injection (kill 21s of time.sleep) |

**Why it matters**: The span streaming subsystem powers BrightAgent's UI updates. Removed 21 seconds of test-suite `time.sleep`, added property-based tests, hardened the FSM. Production reliability work.

### 🔵 Synapse + Ingestion Fixes (Ahmed)

| PR | Description |
|----|-------------|
| data-org-cdk #152 | Develop → Staging promotion — Synapse logic |
| data-org-cdk #153 | Synapse logic + role assumption documentation |
| platform-core #748 | Prevent duplicate data asset creation for mixed-case filenames |
| platform-core #749 | Develop → Staging promotion |

### 📤 Upload Duplicate Detection (Harbour)

| PR | Description |
|----|-------------|
| platform-core #746 | Duplicate check on data asset + files (+58/-0) |
| webapp #1077 | Duplicate check UI integration (+565/-60) |

---

## PR ↔ Ticket Linkage

```
+-------------------------------------------------+
|            PR-TICKET LINKAGE REPORT              |
+-----------------------+-------------------------+
| Total Feature PRs     |  27                     |
| Matched (BH-XXX in    |                         |
|   branch/title)        |  11  (41%)              |
| Unmatched             |  16  (59%)              |
+-----------------------+-------------------------+
| TREND: Up from 34% in Sprint 8 (mid-sprint)     |
| BrightSignals work mostly unticketed (Kuri      |
| shipped end-to-end without per-PR tickets).      |
+-------------------------------------------------+
```

**Matched PRs**: BH-409 (rebrand), BH-412 (notifications dispatcher), BH-431, BH-432, BH-437, BH-438, BH-439, BH-440, BH-441, plus dbt cluster tail (BH-fix patterns).

**Unmatched but legitimate**:
- All Harbour scheduler PRs (no ticket — Sprint 8 BH-302 PoC went straight to MVP)
- Marwan's Bedrock Converse migration (no ticket — strategic technical debt)
- Marwan's AG Grid fix (no ticket)
- Ahmed's Synapse + duplicate fixes (no tickets — cleanup work)

---

## Team Breakdown

| Member | PRs | Lines (additions) | Themes |
|--------|-----|-------------------|--------|
| **Kuri** | 12 | ~7.5K | BrightSignals end-to-end, streaming platform hardening, notifications dispatcher |
| **Harbour** | 7 | ~7.4K | Task scheduler MVP (3 repos), upload duplicate check, develop→staging promotions, catalog schedule |
| **Ahmed** | 5 | ~3.0K | Synapse logic, role assumption, mixed-case dedup, develop→staging |
| **Marwan** | 3 | ~4.4K | Bedrock Converse migration (massive), AG Grid serverside fix, develop→staging |

**Notes**:
- Full team active. No bus factor concentration this window.
- Kuri shipped a full new product surface (BrightSignals) solo.
- Marwan's Bedrock Converse migration unblocks Bedrock AgentCore work (Q2 strategic priority).
- Harbour's scheduler MVP shows strong cross-repo execution capability.

---

## Repository Activity

| Repository | PRs | Notable |
|------------|-----|---------|
| brightbot-slack-server | 8 | BrightSignals end-to-end |
| brighthive-platform-core | 8 | Scheduler, notifications dispatcher, ingestion fixes |
| brighthive-webapp | 5 | Scheduler UI, duplicate check, catalog schedule |
| brightbot | 3 | Bedrock Converse, scheduler integration |
| brighthive-data-organization-cdk | 3 | Synapse promotion, role assumption |

---

## Goals Assessment

| Goal | Status | Evidence |
|------|--------|----------|
| BrightSignals end-to-end | SHIPPED | Subscriptions, poller, S3 artifacts (Tier A+B), dispatcher Lambda. Production ready. |
| Bedrock Converse migration | SHIPPED | brightbot #457 — ChatBedrock → ChatBedrockConverse + deepagents upgrade |
| Task scheduler MVP | SHIPPED | Cross-repo: core + webapp + brightbot |
| Streaming platform hardening | SHIPPED | 7 tickets, FSM repair, property tests, prod path cleanup |
| Synapse + ingestion fixes | SHIPPED | Mixed-case dedup, role assumption, develop→staging promotion |

**5/5 goals shipped in 12 days.** Cadence change cut 2 days but no slip on planned work.

---

## Problems Identified

1. **Cadence cut leaves Sprint 8 in Jira limbo**: Sprint 8 (Apr 14–28) was supposed to close Apr 28 in Jira but never formally closed. Sprint 9 work overlaps Apr 20–28 — same code being claimed by two release artifacts. Need to close Sprint 8 in Jira.
2. **Tickets dropped to 7**: Down from 21 done in Sprint 8 mid-sprint. Most Sprint 9 work was done without ticket creation (BrightSignals, Scheduler, Bedrock Converse, AG Grid).
3. **All 7 done tickets unpointed**: Same gap as Sprint 8 — BH-431 through BH-441 all unpointed despite representing concrete deliverables.
4. **Branch naming gap persists**: Kuri uses `drchinca/BH-XXX/desc`. Ahmed uses descriptive branches without ticket refs (`update/synapse-support-logic-and-docs`). Harbour uses descriptive names (`task-scheduler`, `duplicate-check`). Marwan inconsistent (`fix/bedrock-converse-migration-and-deepagents-upgrade` — no ticket).

---

## Recommendations

1. **Close Sprint 8 in Jira before Sprint 10 starts**: Sprint 8 has been "active" past its end date. Either complete it (Apr 28) or extend the dates.
2. **Create retrospective tickets for major Sprint 9 work**: BrightSignals, Task Scheduler, Bedrock Converse migration each deserve epic-level tickets. Currently invisible to leadership in Jira.
3. **Decide on cadence**: Apr 20 → May 2 (12 days) is fine but conflicts with the existing 14-day Sprint 8. Pick a cadence and align Jira sprints to it (suggest weekly mini-releases, biweekly sprint closes).
4. **Sprint 9 was Q2's strongest cross-repo coordination so far**: BrightSignals required slack-server + platform-core + brightbot to coordinate. Capture this in retro — what worked.
5. **Bedrock momentum is real**: Sprint 9 = ChatBedrockConverse + deepagents upgrade. Sprint 10 priority should be AgentCore PoC.
