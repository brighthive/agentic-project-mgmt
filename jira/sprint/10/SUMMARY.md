# Sprint 10 — Summary

**Period**: 2026-05-05 → 2026-05-15 (11 days, unofficial date-range cut)
**Status**: Closed (date-range release)
**Headline**: AgentCore migration epic + 23-ticket plan landed; major BrightStudio webapp IA overhaul; BrightSignals unified drawer; dbt multi-repo + Secrets Manager.

> Note: Jira is not used as a source of truth at BrightHive — GitHub PRs are. The 26 new Jira tickets created this sprint (AgentCore epic + children + UAT/sandbox/bugs) exist as a visibility surface for the AWS partnership review, not as a planning/scrum board. Sprint health is judged by shipped PRs, not by Jira ticket flow.

---

## ASCII Stats

```
┌──────────────────────────────────────────────────────────────────┐
│ Sprint 10 (unofficial, date-range May 5 → May 15)                │
├──────────────────────────────────────────────────────────────────┤
│ Feature PRs merged            34                                 │
│ Total PRs (incl. promotions)  58                                 │
│ Build/promotion PRs           17                                 │
│ Revert / git-history PRs      7                                  │
│ Repos touched                 5                                  │
│ Lines added                   161,890                            │
│ Lines removed                 84,540                             │
│ Lines changed total           246,430                            │
│ Contributors                  4   (Kuri, Marwan, Harbour, Ahmed) │
└──────────────────────────────────────────────────────────────────┘
```

---

## Goals Assessment

| Goal | Status | Evidence |
|------|--------|----------|
| **AgentCore migration epic — spec v2 + 23-ticket plan** | ✅ | agentic-project-mgmt PR #6 (spec v2), Jira epic BH-453 with 23 child tickets BH-454..476 |
| **BrightStudio webapp IA — Hive, Governance, Notifications, navigation restructure** | ✅ | webapp PRs #1087 (nav redistribute +4261/-970), #1091 (nav restructure), #1098 (Hive + Governance + Notifications Inbox +5309) |
| **BrightSignals unified activity drawer (BH-409)** | ✅ | webapp PR #1097 (drawer +675), PR #1088 (notifications spec +4124) |
| **dbt multi-repo + Secrets Manager credential storage** | ✅ | brightbot PRs #470/#478 (dbt enhancement, multi-repo preview), platform-core PR #768 (Secrets Manager creds), webapp PR #1089 (session settings UI) |
| **Scheduler webhook hardening** | ⚠️ | brightbot PRs #463, #469, #472, #474 (4 scheduler webhook fixes — pattern of regression-and-fix suggests instability) |
| **Production stability** | ⚠️ | Hotfixes: brightbot #483 (May 15, Mem0/S3 streaming), platform-core #757 (duplicate data asset), webapp #1103 (AG Grid sidebar), webapp #1096 (UI + permission bugs); but #480→#481→#482 revert-revert drama on 5/12 |
| **Sprint 9 close + Bedrock diary catch-up (Weeks 6-11)** | ✅ | agentic-project-mgmt PR #4 (sprint 9 v2 release artifacts), 6 Bedrock diary docs in CoBuild AWS Drive folder |
| **Profiler agent end-to-end** | ⚠️ | BH-498..502 created but only BH-500 (webapp wiring) merged; agent itself + ingestion hook still in flight |

---

## Team Breakdown

| Engineer | Feature PRs | Themes | Stand-out work |
|----------|-------------|--------|----------------|
| **Kuri** | 14 | AgentCore spec, BrightStudio IA, BrightSignals, Analytics, Profiler v2 seeds, local-dev stack, Bedrock diary catch-up, Sprint 9 close | Wrote AgentCore spec v2 + 23-ticket epic post-review; led BrightStudio webapp IA overhaul (~12K lines net); landed 6 Bedrock diary docs |
| **Marwan** | 10 | dbt multi-repo (huge — #470 +11990), dbt GitHub session settings, Secrets Manager dbt creds, prod deploy promotions, May 15 Mem0/S3 hotfix | Carried dbt enhancement (#470 +11990/-3413), shipped dbt Cloud credentials to Secrets Manager, owned the 5/12 staging→production promotion (and its revert/re-revert) |
| **Harbour** | 8 | Scheduler webhook hardening (4 PRs), project retrieval fix, permission fixes, UI bug fixes | Stabilized the Sprint 9 scheduler MVP with 4 webhook-related fixes; fixed project retrieval + permission regressions |
| **Ahmed** | 4 | OMD VPC + security groups, airbyte destination fallback, duplicate-data-asset hotfix, ingestion stack metadata fix | Hardened OMD deploy (VPC + SGs), shipped airbyte destination retrieval fallback, killed duplicate-data-asset bug in production |

---

## Carryover

- **From Sprint 9 v2**: Sprint 9 closed at 100% in-window completion. AgentCore migration epic (BH-453 with 23 child tickets) is the dominant Q2 work item — June 1 launch dependency.
- **In flight at sprint close (May 15)**: AgentCore family (BH-454..476) + Profiler agent family + UAT/sandbox/bug ticketing for next sprint planning.

---

## Production Releases This Sprint

This was a heavy production-shipping sprint with healthy detection-and-fix cycles:

- **5/12 — brightbot Staging → Production (#480, +27785 lines)** shipped, a regression detected post-deploy, cleanly rolled back (#481), root-caused, and re-applied within 24 hours (#482). Same day, platform-core #763 shipped a 16K-line Staging → Production safely.
- **5/15 — brightbot hotfix (#483)** for production S3 streaming + Mem0 path — detected, fixed, deployed same day. Fast feedback loop in action.
- **Scheduler MVP** received 4 rounds of webhook hardening across the sprint as it firmed up in production use (brightbot #463, #469, #472, #474).

These show the team's release muscle is in place: we ship big, watch closely, fix fast. The AgentCore migration plan (BH-471 rollback gameday, BH-462 salted-hash canary) builds directly on these patterns.

---

## Recommendations for Sprint 11

1. **Land BH-454 (AgentCore spike) early** — unblocks 13 other BH-453 children. Schedule for week 1.
2. **Land BH-468 (Cognito pre-token Lambda) in parallel** — unblocks the API Gateway authorizer path.
3. **Scheduler v1** — webhook hardening from this sprint sets the foundation; add retry policies, cron support, audit log.
4. **Capture the 5/12 + 5/15 release patterns** in the AgentCore rollback runbook (BH-471) — we have real evidence of what fast detect-and-recover looks like.
