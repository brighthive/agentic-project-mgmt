# Sprint 4 🍍 — Release Notes

**Period**: Feb 3–10, 2026 | **Duration**: 7 days
**Team**: Hikuri, Marwan, Ahmed, Harbour

---

## Summary

| Metric | Value |
|--------|-------|
| Tickets Completed | 15 / 21 (71.4%) |
| Story Points | 41 / 65 (63.1%) |
| PRs Merged | 27 (18 feature + 9 build) |
| Repos Touched | 5 |
| Team | 4 engineers |

---

## Completed Tickets

| Key | Summary | Assignee | Points |
|-----|---------|----------|--------|
| [BH-255](https://brighthiveio.atlassian.net/browse/BH-255) | [BE] BUG causing login to fail on staging | Ahmed | — |
| [BH-250](https://brighthiveio.atlassian.net/browse/BH-250) | [BE] Slack Server - Update CLAUDE.md + environment docs | Hikuri | — |
| [BH-248](https://brighthiveio.atlassian.net/browse/BH-248) | [FE] BrightSide UI/UX polish - chat colors, error tooltips | Harbour | 3 |
| [BH-247](https://brighthiveio.atlassian.net/browse/BH-247) | Update GitHub workflows for stg/prod in platform core | Ahmed | — |
| [BH-246](https://brighthiveio.atlassian.net/browse/BH-246) | Setup proper local development environment and seeding | Harbour | 5 |
| [BH-244](https://brighthiveio.atlassian.net/browse/BH-244) | [BE] Slack Intent Router - MCP-based message routing | Hikuri | 5 |
| [BH-243](https://brighthiveio.atlassian.net/browse/BH-243) | Pre-Post Checks GitOps: Validate engineering standards | Hikuri | 3 |
| [BH-242](https://brighthiveio.atlassian.net/browse/BH-242) | [FE] Projects - Agent interaction UI | Harbour | 3 |
| [BH-241](https://brighthiveio.atlassian.net/browse/BH-241) | [BE] Projects - BHAgent integration | Harbour | 5 |
| [BH-237](https://brighthiveio.atlassian.net/browse/BH-237) | [Design] Slack Auth - OAuth flow design | Hikuri | 2 |
| [BH-236](https://brighthiveio.atlassian.net/browse/BH-236) | [BE] Background Agent Analyst - Design spec | Marwan | 3 |
| [BH-232](https://brighthiveio.atlassian.net/browse/BH-232) | Introduce GitOps approach for server resources (OMD, Airbyte) | Ahmed | 5 |
| [BH-231](https://brighthiveio.atlassian.net/browse/BH-231) | Resolve Airbyte Pulumi stack route table access issue | Ahmed | 2 |
| [BH-230](https://brighthiveio.atlassian.net/browse/BH-230) | Update OpenMetadata configuration lambda for autoclassification | Ahmed | 3 |
| [BH-226](https://brighthiveio.atlassian.net/browse/BH-226) | GetResources mutation failing - requires systemadmin fix | Ahmed | 2 |

---

## Repository Changes

### brightbot (11 PRs — 10 feature, 1 build)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#376](https://github.com/brighthive/brightbot/pull/376) | fix(ci): trigger Claude review on ready_for_review, concise prompt | Hikuri | +2 / -7 |
| [#374](https://github.com/brighthive/brightbot/pull/374) | fix(ci): restore pull_request opened trigger with max-turns cap | Hikuri | +9 / -0 |
| [#372](https://github.com/brighthive/brightbot/pull/372) | fix(ci): simplify Claude review to comment-triggered only | Hikuri | +1 / -10 |
| [#371](https://github.com/brighthive/brightbot/pull/371) | fix(ci): debug Claude review - add contents:write and show_full_output | Hikuri | +2 / -1 |
| [#370](https://github.com/brighthive/brightbot/pull/370) | fix(ci): add checkout step to Claude PR review workflow | Hikuri | +3 / -0 |
| [#369](https://github.com/brighthive/brightbot/pull/369) | fix(ci): add prompt to Claude PR review for auto-trigger | Hikuri | +6 / -0 |
| [#367](https://github.com/brighthive/brightbot/pull/367) | DEV => STAGING | Hikuri | +11,622 / -427 |
| [#366](https://github.com/brighthive/brightbot/pull/366) | feat(auth): add LOCAL_DEV_MODE to bypass auth for local development | Hikuri | +161 / -136 |
| [#365](https://github.com/brighthive/brightbot/pull/365) | make graphql mcp local docker run locally | Marwan | +300 / -15 |
| [#364](https://github.com/brighthive/brightbot/pull/364) | BH-199 cron jobs quality agent PoC | Marwan | +2,126 / -4 |
| [#359](https://github.com/brighthive/brightbot/pull/359) | feat(slack-mcp): adding a slack router agent for 3rd party services | Hikuri | +9,013 / -291 |

### brighthive-webapp (5 PRs — 3 feature, 2 build)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#979](https://github.com/brighthive/brighthive-webapp/pull/979) | fix(ci): update Claude review workflow | Hikuri | +7 / -2 |
| [#978](https://github.com/brighthive/brighthive-webapp/pull/978) | DEV => STAGING | Hikuri | +7,005 / -3,718 |
| [#977](https://github.com/brighthive/brighthive-webapp/pull/977) | fix(local-dev): improve local development experience | Hikuri | +897 / -1,142 |
| [#975](https://github.com/brighthive/brighthive-webapp/pull/975) | BH-214 Create Project Wizard | Harbour | +3,087 / -259 |
| [#974](https://github.com/brighthive/brighthive-webapp/pull/974) | BH-160 UX tab data asset quality | Marwan | +1,416 / -1 |

### brighthive-platform-core (9 PRs — 6 feature, 3 build)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#675](https://github.com/brighthive/brighthive-platform-core/pull/675) | Add: the missing package-lock.json file | Ahmed | +25,904 / -5 |
| [#673](https://github.com/brighthive/brighthive-platform-core/pull/673) | fix(ci): update Claude review workflow | Hikuri | +7 / -2 |
| [#672](https://github.com/brighthive/brighthive-platform-core/pull/672) | staging=>test_branch | Hikuri | +10,796 / -27,866 |
| [#671](https://github.com/brighthive/brighthive-platform-core/pull/671) | DEV => STAGING | Hikuri | +36,604 / -27,770 |
| [#670](https://github.com/brighthive/brighthive-platform-core/pull/670) | fix(local-dev): correct seed data and local Redis connection | Hikuri | +128 / -103 |
| [#669](https://github.com/brighthive/brighthive-platform-core/pull/669) | Gh actions/require tagging | Ahmed | +32 / -3 |
| [#668](https://github.com/brighthive/brighthive-platform-core/pull/668) | BH-206 Add or upload resources to project container | Harbour | +521 / -7 |
| [#667](https://github.com/brighthive/brighthive-platform-core/pull/667) | Feature/BH-205 agent capability tracking | Marwan | +2,894 / -206 |
| [#662](https://github.com/brighthive/brighthive-platform-core/pull/662) | BH-224 trigger OpenMetadata agents as lambda function | Ahmed | +916 / -0 |

### brightbot-slack-server (1 PR — feature)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#2](https://github.com/brighthive/brightbot-slack-server/pull/2) | fix(ci): update Claude review workflow | Hikuri | +8 / -2 |

### brighthive-admin (1 PR — feature)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#86](https://github.com/brighthive/brighthive-admin/pull/86) | fix(ci): add Claude review workflow | Hikuri | +31 / -0 |

---

## Not Completed

| Key | Summary | Assignee | Status |
|-----|---------|----------|--------|
| [BH-245](https://brighthiveio.atlassian.net/browse/BH-245) | [BE] Slack Auth - 3-tier auth system implementation | Hikuri | Needs Refinement |
| [BH-240](https://brighthiveio.atlassian.net/browse/BH-240) | [BE] Context Engineering - Workspace context API | Hikuri | Needs Refinement |
| [BH-239](https://brighthiveio.atlassian.net/browse/BH-239) | [FE] Workspace Portal - Context copywriting UI | Marwan | Needs Refinement |
| [BH-210](https://brighthiveio.atlassian.net/browse/BH-210) | [FE] Project BrightAgent integration | Marwan | In Progress |
| [BH-201](https://brighthiveio.atlassian.net/browse/BH-201) | Onboarding & Off-boarding 100% working | Ahmed | Testing (Dev) |
| [BH-136](https://brighthiveio.atlassian.net/browse/BH-136) | Audit performance monitoring and observability stack | Ahmed | Ready for Staging |
