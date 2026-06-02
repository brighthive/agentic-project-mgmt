# Sprint 11 🧪 — What Shipped

**June 2, 2026** · the Profiler + Permissions cut

This sprint we hardened the foundation: the Data Profiler agent went from prototype to schedulable production tool, the navigation + permissions stack got correct across all roles, and BrightStudio finally lets collaborators manage agents — not just admins.

---

## 🤖 Data Profiler Agent — production-ready

The data profiler is no longer a manual script. This sprint it became:

- **Auto-triggered on ingestion** — runs in parallel with the quality check on every webhook (BH-501)
- **Manually runnable** — Run Profiler button works on every asset detail page (BH-522)
- **Schedulable** — registered as a batch task in the scheduler dispatcher, with UI in the scheduler page (BH-520)
- **Workspace-scoped** — every run is correctly scoped to its workspace (BH-498)

End-to-end: ingestion → profile → quality → Slack signal. No human in the loop.

## 🧭 Navigation + Permissions — fully correct

The enterprise nav restructure (BH-376) shipped with five surgical fixes that locked down the entire role-based experience:

- Admin role guard restored on KB file queries (BH-513)
- All `/govern/schemas` links updated to `/catalog/schemas` (BH-514)
- Governance policy detail routes aligned to new path (BH-515)
- NavLink active-state fixed (BH-516)
- Role-based section visibility preserved + sidebar guard added (BH-517)
- Stale `/home` shortcuts and breadcrumbs repaired (BH-556)

The whole nav now works correctly under admin, collaborator, contributor, and viewer.

## 🔓 BrightStudio — collaborators can manage agents

Previously, only `WORKSPACE_ADMIN` could create, update, or delete custom agents — collaborators saw a "user not authorized" toast even though Apollo's optimistic mutations succeeded. Now agent CRUD is gated by `prohibits: [VIEWER, CONTRIBUTOR, GUEST]` instead, opening the door for the full collaborator experience. (BH-548)

## 📡 Quality Signals → Slack

When a quality check finishes, the result now publishes through BrightSignals to the customer's Slack workspace. Quality has gone from "data team checks the dashboard" to "everyone sees it land in their channel". (BH-530)

## 🛠 Local-Dev Experience — dramatically faster

Comprehensive seed data + mock fixtures across platform-core and webapp. New engineers can spin up a fully populated workspace in under a minute, and PR reviewers can see real data in every screen. Workspace-aware BrightBot requests + thread validation also landed for local mode.

## 🐛 Production Stability

- BrightAgent S3 streaming + mem0 hotfix
- AG Grid aria description sidebar layout fix

---

## 📊 By the Numbers

| Metric | Sprint 11 |
|---|---|
| PRs Merged | 27 |
| Lines Changed | 15,183 (excl. release-carrier PRs) |
| Repos Touched | 3 (webapp · platform-core · brightbot) |
| Tickets Done | 7 |
| Tickets in QC | 2 |
| Engineering Hours | ~120h estimated |

---

## 👥 Team Contributions

- **Harbour** — 7 done, all the nav/permissions hardening + profiler scheduler UI + BrightStudio collab unlock
- **Kuri** — BH-376 nav restructure, profiler port + auto-trigger webhook, runtime feature flags, local-dev seeds (4 PRs in pipeline)
- **Marwan** — BH-530 quality signals, dbt Cloud secrets, BrightAgent + AG Grid hotfixes
- **Ahmed** — BH-502 profiler E2E verification (in flight)

---

## 🎯 What's Next: Sprint 12

- Transition the 10 Needs-Refinement tickets to Done
- Pick up BH-359 Platform Analytics dashboard
- Resolve unassigned bug fixes (BH-491, BH-495, BH-497)
- Formalize Sprint 12 in Jira (return to real sprint object tracking)

## 🚫 Not in this release

Longaeva PoC work (Snowflake integration, BH-526 epic, poc_tracker scaffolding) is tracked separately under `clients/trials/longaeva/TRACKER.md` — that work runs on its own cadence with the trial timeline.
