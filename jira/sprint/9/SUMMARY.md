# Sprint 9 — Release Summary (Unofficial) — v2

**Period**: Apr 20 – May 4, 2026 | **Duration**: 14 days (full planned window)
**Status**: Unofficial — no Jira sprint object created. Date-range release.
**Overlap**: Sprint 8 🫐 still active in Jira (Apr 14–28). Sprint 9 covers Sprint 8 tail end + 6 days of post-Sprint 8 work.
**Version**: v2 (May 4 cutoff, +12 PRs and +10 retro tickets vs. v1 May 2 snapshot)

---

## Sprint Stats

```
+-------------------------------------------------+
|         SPRINT 9 — APR 20 to MAY 4, 2026        |
|        14 days, full planned window             |
+-----------------------+-------------------------+
| Tickets Resolved      |  17                     |
|   - Streaming cluster |   7 (Kuri, BH-431..441) |
|   - Retro tickets     |  10 (BH-443..452)       |
| Story Points Done     |  39 (retro estimates)   |
| PRs Merged            |  39 (28 feat + 11 build)|
| Lines Changed         |  +42.5K / -11.7K (54.1K)|
| Repos Touched         |  5                      |
| Authors               |  4 (full team)          |
| PR-Ticket Linkage     |  53.8% (up from 41% v1) |
| Major Features        |  6 shipped              |
+-----------------------+-------------------------+
```

**The retro tickets recovered ~30 points of velocity** that was previously invisible in Jira. Linkage rose from 41% to 54%.

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

**Why it matters**: BrightSignals is BrightHive's first proactive surface — agent reaches out to user instead of user reaching to agent.

### 🤖 Bedrock Converse Migration (BH-446)

| PR | Description |
|----|-------------|
| brightbot #457 | Migrate ChatBedrock to ChatBedrockConverse, upgrade deepagents (+1,877/-2,300) |

**Why it matters**: Step in the LangGraph → Bedrock migration. First runtime change in production code path.

### 🎨 BrightStudio Skills (BH-445) — NEW MAJOR FEATURE (May 4)

| PR | Description |
|----|-------------|
| webapp #1017 | Add Skills surface to BrightStudio (+847/-26) |
| brightbot #421 | Skills runtime — agent loads + uses Skills at execution time (+629/-9) |

**Why it matters**: Skills become first-class composable agent capabilities. Major BH-260 BrightStudio epic addition. Owner: Harbour.

### ⏰ Task Scheduler MVP + UI Fixes (BH-443, BH-444, BH-448)

| PR | Description |
|----|-------------|
| platform-core #750 | Scheduler MVP — agnostic scheduler service (+881/-89) |
| webapp #1079 | Scheduler MVP — UI integration (+399/-232) |
| brightbot #458 | Scheduler MVP — agent integration (+579/-113) |
| platform-core #752 | Scheduler UI fixes + result display (+72/-24) |
| webapp #1082 | Scheduler UI fixes + result display (+727/-273) |
| brightbot #460 | Scheduler UI fixes + result display (+1,609/-1,468) |
| webapp #1076 | Schedule support in catalog UI (+484/-182) |

**Why it matters**: First scheduling primitive in the platform. Owner: Harbour.

### 🧪 UAT Eval Framework + Vega-Lite Visualization (May 4) — NEW

| PR | Description |
|----|-------------|
| slack-server #23 | Direct-call deterministic turn evals + HTTP scenario runner (+2,547/-138) |
| brightbot #456 | Render Vega-Lite to PNG, emit artifact envelope (Tier B) (+354/-66) |

**Why it matters**: Closes the loop between BrightAgent and Slack image rendering — chart artifacts now flow end-to-end. Plus a new deterministic UAT eval framework for slack-server. Owner: Kuri.

### 🧱 Streaming Platform Hardening (7 tickets — BH-431, 432, 437–441)

Span streaming subsystem repair: FSM repair, Hypothesis property tests (killed 21 seconds of test latency), Cognito + Neo4j adapter classes, Py 3.14 compliance.

### 🔵 Synapse + Ingestion Hardening (BH-451, BH-452)

| PR | Description |
|----|-------------|
| data-org-cdk #152 | Develop → Staging promotion — Synapse logic |
| data-org-cdk #153 | Synapse logic + role assumption documentation |
| platform-core #748 | Prevent duplicate data asset for mixed-case filenames (Ahmed) |

### 📤 Upload Duplicate Detection (BH-447)

| PR | Description |
|----|-------------|
| platform-core #746 | Duplicate check on data asset + files (+58/-0) |
| webapp #1077 | Duplicate check UI integration (+565/-60) |

### 🛠 Webapp Quality Fixes (BH-449, BH-450)

| PR | Description |
|----|-------------|
| webapp #1080 | AG Grid serverside datasource fix (Marwan, +22/-52) |
| webapp #1083 | Login PW redundant check removal (Harbour, +2/-7) |

---

## PR ↔ Ticket Linkage

```
+-------------------------------------------------+
|            PR-TICKET LINKAGE REPORT (v2)         |
+-----------------------+-------------------------+
| Total PRs             |  39                     |
| Feature PRs           |  28                     |
| Build/Promotion PRs   |  11 (excluded from rate)|
| Matched (BH-XXX)      |  21  (54%)              |
| Unmatched feature PRs |   7  (18%)              |
+-----------------------+-------------------------+
| TREND: 41% (v1, May 2) → 54% (v2, May 4)        |
| Boost driven by 10 retro tickets BH-443..452     |
+-------------------------------------------------+
```

**Net assessment**: With retro tickets added, all major capability work now has Jira coverage. Remaining unmatched PRs are minor cleanup or build promotion.

---

## Team Breakdown (v2)

| Member | Feature PRs | Tickets Done | Themes |
|--------|-------------|--------------|--------|
| **Kuri** | 12 | 7 streaming + UAT evals + Vega-Lite + BrightSignals + Notifications dispatcher | BrightSignals, Streaming Platform, UAT Evals, Vega-Lite |
| **Harbour** | 9 | 6 retro (scheduler ×3, skills, dedup, login, catalog) | Task Scheduler, BrightStudio Skills, Upload UX, Login |
| **Ahmed** | 2 | 2 retro (mixed-case dedup, Synapse) | Synapse, Ingestion fixes |
| **Marwan** | 2 | 2 retro (Bedrock Converse, AG Grid) | Bedrock Converse, Webapp fixes |

**Notes**:
- Full team active across the 14-day window.
- Kuri's solo BrightSignals delivery + concurrent UAT/Vega-Lite work make up the largest line-count contribution.
- Harbour's solo Skills feature is a major BH-260 epic addition that wasn't in any planning doc.
- Marwan's Bedrock Converse migration unblocks the AgentCore strategic priority.

---

## Repository Activity (v2)

| Repository | PRs (v1) | PRs (v2) | Δ |
|------------|----------|----------|---|
| brightbot-slack-server | 8 | 10 | +2 (UAT eval, dev→staging) |
| brighthive-platform-core | 8 | 10 | +2 (scheduler fixes, dev→staging) |
| brighthive-webapp | 5 | 9 | +4 (skills, scheduler fixes, login, dev→staging) |
| brightbot | 3 | 7 | +4 (skills, vega-lite, scheduler fixes, dev→staging) |
| brighthive-data-organization-cdk | 3 | 3 | 0 |

---

## Goals Assessment (v2)

| Goal | Status | Evidence |
|------|--------|----------|
| BrightSignals end-to-end | SHIPPED | Subscriptions, poller, S3 artifacts, dispatcher Lambda. Production ready. |
| Bedrock Converse migration | SHIPPED + TICKETED | brightbot #457 + BH-446 |
| Task scheduler MVP + UI fixes | SHIPPED + TICKETED | Cross-repo MVP + post-MVP UI fixes (BH-443, BH-444, BH-448) |
| BrightStudio Skills | SHIPPED + TICKETED | BH-445 — new major BH-260 capability |
| Streaming platform hardening | SHIPPED | 7 tickets, FSM repair, property tests |
| UAT eval framework | SHIPPED | slack-server #23 — deterministic turn evals + HTTP scenario runner |
| Vega-Lite visualization | SHIPPED | brightbot #456 — chart artifacts flow end-to-end |
| Synapse + ingestion fixes | SHIPPED + TICKETED | BH-451, BH-452 |

**8 capability goals shipped in 14 days. 10 retroactive tickets created and transitioned to Done.**

---

## Problems Identified (v2)

1. **Sprint 8 still not closed in Jira.** Sprint 8 expired Apr 28 but is still active May 4. Sprint 9 work overlaps. Same recommendation: close Sprint 8 this week.
2. **Most Sprint 9 work was discovered after-the-fact via PR archaeology.** The 10 retro tickets (BH-443 → BH-452) all cover *already-shipped* work. Going forward, the team needs to create tickets *before* PR — not after release.
3. **Harbour shipped 2 major features (Scheduler, Skills) without any Jira plan.** Both are now ticketed retroactively, but neither was visible to leadership during the sprint.

---

## Recommendations (v2)

1. **Close Sprint 8 in Jira immediately.** Recompute carryover, restart clean cadence in Sprint 10.
2. **Sprint 10 = AgentCore PoC + cadence reset + estimation discipline.** Bedrock momentum is real.
3. **Establish ticket-before-PR rule going forward.** Even a 1-line "Refine later" ticket is better than a 9-PR feature with zero Jira presence.
4. **Pair on BrightSignals operations (Marwan or Harbour shadow Kuri).** Bus factor mitigation.
5. **Make Skills a Q3 marketing priority.** First-class composable agent capabilities is a slide-worthy GTM differentiator.
