# Sprint 7 (Unofficial) — Release Notes

**Period**: Mar 4–24, 2026 | **Duration**: 20 days
**Note**: No formal Jira sprint — post-Sprint 6 development period

---

## Summary

| Metric | Value |
|--------|-------|
| Tickets Completed | 12 / 14 (85.7%) |
| Story Points | 33 / 43 (76.7%) |
| PRs Merged | 63 (36 feature + 27 build) |
| Repos Touched | 4 |
| Team | 4 engineers |

---

## Completed Tickets

| Key | Summary | Assignee | Points |
|-----|---------|----------|--------|
| [BH-295](https://brighthiveio.atlassian.net/browse/BH-295) | Investigate Subagents for custom agents | Harbour | 2 |
| [BH-294](https://brighthiveio.atlassian.net/browse/BH-294) | [CRITICAL] Fix system bugs for production push | Marwan | — |
| [BH-291](https://brighthiveio.atlassian.net/browse/BH-291) | [FE] Support creating custom agents in BrightStudio | Harbour | 5 |
| [BH-290](https://brighthiveio.atlassian.net/browse/BH-290) | [BE] Support creating custom agents | Harbour | 5 |
| [BH-289](https://brighthiveio.atlassian.net/browse/BH-289) | Investigate LangChain Assistants and custom agents | Harbour | 4 |
| [BH-284](https://brighthiveio.atlassian.net/browse/BH-284) | [WebApp] Refactor BrightAgent code on FE | Marwan | — |
| [BH-280](https://brighthiveio.atlassian.net/browse/BH-280) | [WebApp] Reconnect BrightAgent stream if connection lost | Marwan | — |
| [BH-277](https://brighthiveio.atlassian.net/browse/BH-277) | [CRITICAL] Indiana Supervisor vs DeepAgent Prod Release | Marwan | 3 |
| [BH-266](https://brighthiveio.atlassian.net/browse/BH-266) | [FE] BrightStudio - Investigate current state | Harbour | 3 |
| [BH-248](https://brighthiveio.atlassian.net/browse/BH-248) | [FE] BrightSide UI/UX polish | Harbour | 3 |
| [BH-242](https://brighthiveio.atlassian.net/browse/BH-242) | [FE] Projects - Agent interaction UI | Harbour | 3 |
| [BH-241](https://brighthiveio.atlassian.net/browse/BH-241) | [BE] Projects - BHAgent integration | Harbour | 5 |

---

## Repository Changes

### brightbot (26 PRs — 15 feature, 11 build)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#419](https://github.com/brighthive/brightbot/pull/419) | feature: Shareable Thread Links | Marwan | +643 / -8 |
| [#414](https://github.com/brighthive/brightbot/pull/414) | fix: Multiple fixes with studio and project | Harbour | +392 / -186 |
| [#412](https://github.com/brighthive/brightbot/pull/412) | feat: Custom agent studio + Project Agent | Marwan | +4,427 / -1,028 |
| [#411](https://github.com/brighthive/brightbot/pull/411) | feat(trace): propagate slack_trace_id end-to-end | Hikuri | +194 / -120 |
| [#406](https://github.com/brighthive/brightbot/pull/406) | fix: BH-300 quality check agent reliability + S3 paths | Marwan | +136 / -87 |
| [#405](https://github.com/brighthive/brightbot/pull/405) | feat: BH-297 refactor retrieval agent — inline eval, auto-save | Marwan | +525 / -198 |
| [#404](https://github.com/brighthive/brightbot/pull/404) | feat(auth): validate per-workspace Slack API key | Hikuri | +154 / -38 |
| [#402](https://github.com/brighthive/brightbot/pull/402) | fix(slack): JWT workspace propagation and token consolidation | Hikuri | +283 / -100 |
| [#399](https://github.com/brighthive/brightbot/pull/399) | feat: OpenMetadata ID validation tool | Marwan | +332 / -24 |
| [#397](https://github.com/brighthive/brightbot/pull/397) | BH-294 critical fix system bugs (3/3) | Marwan | +0 / -0 |
| [#396](https://github.com/brighthive/brightbot/pull/396) | BH-294 critical fix system bugs (2/3) | Marwan | +1,502 / -1,418 |
| [#395](https://github.com/brighthive/brightbot/pull/395) | fix: BH-294 critical fix system bugs (1/3) | Marwan | +110 / -510 |
| [#393](https://github.com/brighthive/brightbot/pull/393) | feat: reusable interruptible() wrapper with cancel support | Marwan | +158 / -15 |
| [#392](https://github.com/brighthive/brightbot/pull/392) | feat: BH-286 AWS Bedrock KB retrieval tool | Marwan | +258 / -1 |

### brighthive-webapp (21 PRs — 10 feature, 11 build)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#1016](https://github.com/brighthive/brighthive-webapp/pull/1016) | fix: limit CSV preview to 100 rows, improve modal UI | Marwan | +117 / -63 |
| [#1015](https://github.com/brighthive/brighthive-webapp/pull/1015) | fix: hide-tour page for agent-guest | Marwan | +2 / -2 |
| [#1014](https://github.com/brighthive/brighthive-webapp/pull/1014) | hotfix: stale share link between thread switch | Marwan | +6 / -0 |
| [#1012](https://github.com/brighthive/brighthive-webapp/pull/1012) | feature: Shareable Agent Conversations & Studio to My Agents | Marwan | +5,537 / -580 |
| [#1009](https://github.com/brighthive/brighthive-webapp/pull/1009) | fix: Hot fixes for production push | Marwan | +680 / -568 |
| [#1007](https://github.com/brighthive/brighthive-webapp/pull/1007) | fix: Fixes before production push | Marwan | +4,628 / -861 |
| [#1004](https://github.com/brighthive/brighthive-webapp/pull/1004) | feat: Custom agent studio + New BrightAgent UI + Project Agent | Marwan | +22,857 / -1,398 |
| [#1001](https://github.com/brighthive/brighthive-webapp/pull/1001) | feat: quality check header with UI and metadata chips | Marwan | +211 / -38 |
| [#999](https://github.com/brighthive/brighthive-webapp/pull/999) | fix: BH-301 quality check report fetching + sidebar layout | Marwan | +83 / -47 |
| [#997](https://github.com/brighthive/brighthive-webapp/pull/997) | fix: BH-294 critical fix system bugs | Marwan | +212 / -198 |

### brighthive-platform-core (12 PRs — 7 feature, 5 build)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#692](https://github.com/brighthive/brighthive-platform-core/pull/692) | fix: activate INVITED_TO edges for AGENT_GUEST flow | Marwan | +42 / -21 |
| [#691](https://github.com/brighthive/brighthive-platform-core/pull/691) | Hot deployment fix | Marwan | +3 / -2 |
| [#690](https://github.com/brighthive/brighthive-platform-core/pull/690) | fix: deprecated bundling | Marwan | +3 / -1 |
| [#688](https://github.com/brighthive/brighthive-platform-core/pull/688) | feature: external agent sharing with AGENT_GUEST role | Marwan | +6,437 / -898 |
| [#685](https://github.com/brighthive/brighthive-platform-core/pull/685) | fix: resource-project relationship + unlink mutations | Marwan | +229 / -72 |
| [#681](https://github.com/brighthive/brighthive-platform-core/pull/681) | security: remove S3 URI exposure from capability result API | Marwan | +108 / -42 |
| [#680](https://github.com/brighthive/brighthive-platform-core/pull/680) | feat(slack): generate per-workspace bhagent_api_key | Hikuri | +46,605 / -30,424 |

### brightbot-slack-server (4 PRs — all feature)

| PR | Title | Author | +/- |
|----|-------|--------|-----|
| [#11](https://github.com/brighthive/brightbot-slack-server/pull/11) | harden: type safety, rate limiting, autoscaling, monitoring | Hikuri | +3,947 / -360 |
| [#10](https://github.com/brighthive/brightbot-slack-server/pull/10) | feat(infra): add missing env vars + IAM task role to ECS | Hikuri | +98 / -25 |
| [#9](https://github.com/brighthive/brightbot-slack-server/pull/9) | feat(auth): send per-workspace bhagent_api_key to brightbot | Hikuri | +59 / -4 |
| [#7](https://github.com/brighthive/brightbot-slack-server/pull/7) | fix(slack): pass JWT in payload metadata, reject unresolved workspaces | Hikuri | +131 / -12 |

---

## In Progress

| Key | Summary | Assignee |
|-----|---------|----------|
| [BH-293](https://brighthiveio.atlassian.net/browse/BH-293) | Update unstructured data stack for workspace AWS accounts | Ahmed |
| [BH-210](https://brighthiveio.atlassian.net/browse/BH-210) | [FE] Project BrightAgent integration | Marwan |
