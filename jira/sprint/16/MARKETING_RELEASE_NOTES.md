# Sprint 16 🍓 — BrightHive Release Notes (Aug 17–23, 2026)

## 🔌 Sync Stops Failing Closed

The GraphQL Core service's move to ECS last week left one gap: the
`LANGGRAPH_BASE_URL` and `LANGGRAPH_API_KEY` env values weren't reaching the
runtime, so sync calls failed closed. Both the ECS service and the GraphQL
Lambda now carry the wiring, and project-transformation run cards read their
`lastRunAt` from storage instead of recomputing it on every request. (BH-1461, BH-1462)

## 🗄️ Warehouse Resolution, Off the Legacy Path

Scheduled jobs and legacy SQL callers used to fall back to the public
catalog when no warehouse was explicitly named. Both now resolve through
the workspace's default warehouse via OGM — the same identity model the
rest of the platform already uses. brightbot's supervisor also picked up a
dedicated warehouse-listing tool, so "what warehouses do I have" never
needs a GraphQL introspection round-trip. (BH-1454)

## 🚀 Infra — GraphQL Core's ECS Cutover Continues

The Lambda warmer that used to keep GraphQL Core's cold path warm is now
retired now that ECS carries production traffic in staging.

## 🔔 Notifications — Artifacts on the Direct Channel

slack-server now delivers PDF/CSV/table artifacts on the direct
channel-push path, closing a gap where only the threaded-reply path could
carry a file. (BH-1452)

## 📊 By the Numbers

- **Tickets Resolved**: 1 Done (BH-1461) — 4 more shipped code but stayed in
  "Needs Refinement"
- **PRs Merged**: 22 (13 code, 9 release/promotion)
- **Lines Changed**: +5,993 / −417 (code only)
- **Repos Touched**: 5 (platform-core, webapp, brightbot, slack-server, agentic-project-mgmt)
- **Engineering days**: 7 (Aug 17–23 — first release on the new weekly cadence)

## 👥 Team Contributions

- **Kuri** — 7 PRs across 5 repos: LANGGRAPH env wiring, supervisor
  warehouse tooling, slack-server artifact delivery, spec consolidation
- **Harbour** — 4 PRs: warehouse-routing cleanup, Apollo toast noise fix
- **Marwan** — 2 PRs: GraphQL ECS/CloudFront cutover continuation

## ⚠️ Sprint Health

- Completion: 1/1 resolved ticket Done, but only 1 ticket formally resolved
  this window — 4 more shipped code without a matching Jira transition
- First release cut to a clean 7-day week, by team decision
- No tickets carrying over — none were formally scoped to this window
