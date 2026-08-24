# Sprint 16 🍓 — Release Notes (Aug 17–23, 2026)

Technical release notes, grouped by repository. First release on the new
weekly cadence — see `SUMMARY.md` for the per-person breakdown and
`stats.json` for the raw numbers.

| Metric | Value |
|---|---|
| PRs merged | 22 (13 code + 9 release/promotion) |
| Tickets resolved | 1 (BH-1461, Done) |
| Repos touched | 5 |
| Code lines (excl. release re-merges) | +5,993 / −417 |
| Authors | Kuri (7), Harbour (4), Marwan (2) |

---

## brighthive-platform-core (10 PRs, 5 code)

**LANGGRAPH env wiring after the ECS cutover (BH-1461/1462)**
- [#1215](https://github.com/brighthive/brighthive-platform-core/pull/1215) fix(cdk): wire LANGGRAPH url + key into GraphQL Lambda + ECS (BH-1461)
- [#1217](https://github.com/brighthive/brighthive-platform-core/pull/1217) fix(cdk): keep LANGGRAPH env on ECS, drop from 4KB Lambda (BH-1461)
- [#1214](https://github.com/brighthive/brighthive-platform-core/pull/1214) fix(observability): select lastRunAt for project transformations (BH-1462)

**GraphQL ECS/CloudFront cutover continuation (Marwan)**
- [#1207](https://github.com/brighthive/brighthive-platform-core/pull/1207) feat(cdk): GraphQL ECS CloudFront cutover for staging
- [#1209](https://github.com/brighthive/brighthive-platform-core/pull/1209) fix(cdk): skip GraphQL Lambda warmer after ECS cutover

**Releases:** [#1219](https://github.com/brighthive/brighthive-platform-core/pull/1219), [#1218](https://github.com/brighthive/brighthive-platform-core/pull/1218), [#1216](https://github.com/brighthive/brighthive-platform-core/pull/1216), [#1210](https://github.com/brighthive/brighthive-platform-core/pull/1210), [#1208](https://github.com/brighthive/brighthive-platform-core/pull/1208)

---

## brighthive-webapp (3 PRs, 2 code)

- [#1433](https://github.com/brighthive/brighthive-webapp/pull/1433) fix(observability): run-card timestamps from stored lastRunAt + GitHub org from repo URL (BH-1462)
- [#1435](https://github.com/brighthive/brighthive-webapp/pull/1435) fix(webapp): suppress error toasts for background Apollo operations (Harbour)

**Releases:** [#1434](https://github.com/brighthive/brighthive-webapp/pull/1434)

---

## brightbot (7 PRs, 4 code)

**Warehouse routing off the legacy path (Harbour)**
- [#1041](https://github.com/brighthive/brightbot/pull/1041) fix(warehouse): resolve background warehouse config via OGM, not public catalog
- [#1039](https://github.com/brighthive/brightbot/pull/1039) fix(warehouse): route scheduled jobs through workspace default warehouse
- [#1035](https://github.com/brighthive/brightbot/pull/1035) fix(warehouse): route legacy SQL callers through catalog default and chat pin

**Supervisor tooling (Kuri)**
- [#1038](https://github.com/brighthive/brightbot/pull/1038) feat(chat): add supervisor warehouse-listing tool, no GraphQL introspection (BH-1454)

**Releases:** [#1042](https://github.com/brighthive/brightbot/pull/1042), [#1040](https://github.com/brighthive/brightbot/pull/1040), [#1036](https://github.com/brighthive/brightbot/pull/1036)

---

## brightbot-slack-server (1 PR, all code)

- [#177](https://github.com/brighthive/brightbot-slack-server/pull/177) feat(notifications): deliver artifacts on the direct channel-push path (BH-1452)

---

## agentic-project-mgmt (1 PR, all docs)

- [#179](https://github.com/brighthive/agentic-project-mgmt/pull/179) docs(spec): consolidate 92 specs into 14 delegatable themes (BH-1036)

---

## No activity this window

Checked, 0 merged PRs Aug 17–23: `brighthive-admin`, `brighthive-data-organization-cdk`,
`brighthive-e2e`, `brighthive-data-workspace-cdk`, `platform-saas-ai-context`.
