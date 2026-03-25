# Sprint 7 (Unofficial) — Validation Report

**Period**: Mar 4–24, 2026

---

## PR ↔ Ticket Linkage Summary

| Metric | Count | % |
|--------|-------|---|
| Total Feature PRs | 36 | 100% |
| Matched to Jira tickets | 8 | 22% |
| Unmatched (no ticket ref) | 28 | 78% |
| **Linkage Rate** | **22%** | **CRITICAL** |

---

## Matched PRs (BH-XXX in branch or title)

| PR | Repo | Ticket | Match Source |
|----|------|--------|-------------|
| #395, #396, #397 | brightbot | BH-294 | Branch name |
| #392, #410 | brightbot | BH-286 | Branch name |
| #405 | brightbot | BH-297 | Branch name |
| #406 | brightbot | BH-300 | Branch name |
| #999 | webapp | BH-301 | Branch name |
| #997 | webapp | BH-294 | Branch name |
| #681 | platform-core | BH-298 | Branch name |

---

## Tickets Done WITHOUT Matched PRs

These tickets were marked Done but have no PRs with their ticket key in the branch name:

| Ticket | Summary | Assignee | Notes |
|--------|---------|----------|-------|
| BH-295 | Investigate Subagents for custom agents | Harbour | Research — may not need code |
| BH-291 | [FE] Support creating custom agents in BrightStudio | Harbour | Likely in #1004 (custom-agent-studio branch) |
| BH-290 | [BE] Support creating custom agents | Harbour | Likely in #412 (custom-agent-studio branch) |
| BH-289 | Investigate LangChain Assistants and custom agents | Harbour | Research — may not need code |
| BH-284 | [WebApp] Refactor BrightAgent code on FE | Marwan | Likely in #1004 or #1007 |
| BH-280 | [WebApp] Reconnect BrightAgent stream | Marwan | Likely in #1007 or #1009 |
| BH-277 | Indiana Supervisor vs DeepAgent Prod Release | Marwan | Likely in #395/#396 (BH-294 branch) |
| BH-266 | [FE] BrightStudio - Investigate current state | Harbour | Research ticket |
| BH-248 | [FE] BrightSide UI/UX polish | Harbour | Likely in #1004 |
| BH-242 | [FE] Projects - Agent interaction UI | Harbour | Likely in #1004 |
| BH-241 | [BE] Projects - BHAgent integration | Harbour | Likely in #412 |

---

## Orphan PRs (No Jira Ticket)

Major features shipped with zero Jira tracking:

| Feature | PRs | Repo(s) | Author |
|---------|-----|---------|--------|
| **Shareable Thread Links** | #419, #1012 | brightbot, webapp | Marwan |
| **Agent Sharing + AGENT_GUEST** | #688, #692 | platform-core | Marwan |
| **Slack trace propagation** | #411 | brightbot | Hikuri |
| **Slack per-workspace API key** | #404, #680, #9 | brightbot, core, slack | Hikuri |
| **Slack JWT fixes** | #402, #7 | brightbot, slack | Hikuri |
| **Slack hardening** | #11 | slack-server | Hikuri |
| **Slack ECS infra** | #10 | slack-server | Hikuri |
| **OMD validation tool** | #399 | brightbot | Marwan |
| **Interruptible wrapper** | #393 | brightbot | Marwan |
| **Quality check UI** | #1001 | webapp | Marwan |
| **CSV preview fix** | #1016 | webapp | Marwan |
| **Resource-project mutations** | #685 | platform-core | Marwan |
| **S3 URI security fix** | #681 | platform-core | Marwan |

---

## Estimation Gaps

| Ticket | Summary | Points |
|--------|---------|--------|
| BH-294 | [CRITICAL] Fix system bugs for production push | **Unpointed** |
| BH-284 | [WebApp] Refactor BrightAgent code on FE | **Unpointed** |
| BH-280 | [WebApp] Reconnect BrightAgent stream | **Unpointed** |

---

## Recommendations

1. **Create retroactive tickets** for: Shareable Links, Agent Sharing/AGENT_GUEST, Slack Hardening
2. **Enforce `BH-XXX/` branch prefix** via GitHub branch protection rules
3. **Point all tickets** before moving to In Progress
4. **Bundled PRs**: #412 and #1004 contain multiple ticket's worth of work — split in future
