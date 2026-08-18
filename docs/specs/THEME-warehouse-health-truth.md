---
title: "Warehouse health you can trust"
epic: "BH-1036"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - sqlserver-health-watch.md
  - warehouse-health-snapshot.md
  - warehouse-connectivity-monitoring-alerts.md
  - pipeline-connectivity-watchdog.md
  - longitudinal-drift-watchdog-wiring.md
---

# Warehouse health you can trust

> Delegation unit. One engineer, one theme. Cap 150 lines.

## The goal

Every warehouse a customer connects is actually being watched, the status they see on the
Health Checks page is true right now, and when something breaks they get told what broke and
what to do about it. Today all three of those fail: most connections are never polled, a
stale "Healthy" can sit on screen for weeks, and when an alert does fire it's a generic bell
with no useful text.

## Why now

Impact Capital, staging, 2026-08-18 (**BH-1457**): the "SQLTest2019" warehouse was deleted
outright on the cloud side, and the dashboard still showed **Healthy** with a last-checked
date of 2026-08-05 — 13 days stale. The on-demand probe already returns `healthy:false` for
that same connection, so the platform *knew* and the page still lied. Same failure family as
the earlier Loop Capital outage that produced BH-1363.

## What to build

1. `brightbot` — poll **every** configured warehouse per workspace, not the first one
   `next(iter(...))` happens to return; honor the workspace's `is_default` as the headline
   connection. A workspace stays reachable while ≥1 warehouse is reachable.
2. `brightbot` — add a target-existence check to the poll: confirm the *configured* database
   still exists, not just that the server answers. Emit `source_target_missing` (critical),
   distinct from `source_connection_unreachable`. Implement for SQL Server first, behind a
   `TARGET_EXISTENCE` capability on the existing `PipelineSource` port.
3. `brighthive-platform-core` — staleness gate on `getHealthChecks()`: a reading older than
   the threshold renders `"Unknown"`, never its last cached value. Add `isStale` to the
   response. Default 45 min (3× the watchdog cadence).
4. `brightbot-slack-server` + `brighthive-platform-core` — real alert copy for
   `source_connection_unreachable` and `source_target_missing` in both Slack and the in-app
   inbox. No registered signal may fall through to the generic renderer.
5. `brighthive-platform-core` + `brighthive-webapp` — a "Check connection now" button that
   actually calls the existing probe (BH-1341), read-only, never writes the shared snapshot.
   Today's button is a placeholder toast that calls nothing.
6. `brighthive-platform-core` — auto-create the watchdog schedule when a workspace's first
   warehouse is connected (idempotent), and make it selectable in the schedule UI. This is
   why Impact Capital had no watchdog at all.
7. `brightbot` — wire the two dead connection points on the drift adapter so it stops
   silently emitting zero signals on every poll.

## Done when

- [ ] A workspace with 3 warehouses and 1 down shows 2 healthy + 1 down — never a
      workspace-wide "unreachable"
- [ ] Deleting a database on a reachable server flips that connection to Down within one
      poll cycle
- [ ] A connection with no poll in >45 min shows "Unknown" on the real staging Analytics
      page, not a cached "Healthy"
- [ ] A down connection produces a Slack card naming the connection and the likely fix
- [ ] "Check connection now" returns a live verdict and leaves the shared snapshot untouched
- [ ] Connecting a warehouse in a fresh workspace results in a watchdog schedule existing
- [ ] Real-behavior test: create a scratch database, poll (passes), drop it, poll again
      (fails) against a real SQL Server — not a mock

## Don't do

- **Self-healing / remediation PRs** — separate theme (fleet self-healing, BH-1255).
- **The landing-page Hive Health band and catalog card UI** — separate theme (observe-surface
  honesty).
- **Scheduled digest push** — separate theme.
- **Target-existence for Snowflake / Databricks / Redshift / Oracle** — SQL Server is the
  first adapter. Audit the others and file per-adapter follow-ups; don't build them here.
- **Per-connection schedule granularity** — the watchdog stays per-workspace.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | fan-out orchestration, target-existence check, drift adapter wiring |
| `brighthive-platform-core` | staleness gate, on-demand mutation, auto-schedule, inbox renderer |
| `brightbot-slack-server` | alert copy for two signal types |
| `brighthive-webapp` | check-now button, schedule option |
| `brighthive-e2e` | stale-renders-Unknown + dropped-target feature tests |

**Tickets:** BH-1363 (unmerged root-cause fix — land first), BH-1367, BH-1457, BH-1368
(shares the `"Unknown"` label — keep wording consistent)

---

## ⚠️ One decision before code starts

Two specs independently invented a fan-out mechanism for item 1, and each defers to the other:

- `pipeline-self-healing-fleet.md` §2.2 — a `ConnectionDirectory` port + `build_sources_for_workspace`, keyed by `source_type`
- `pipeline-connectivity-watchdog.md` §2.3 — `poll_configured_warehouses` + `WAREHOUSE_TYPE_TO_SOURCE_TYPE`, keyed by warehouse and honoring `is_default`

Pick one and delete the other from its spec. Recommendation: **the warehouse-keyed one**, because
honoring `is_default` is the actual BH-1457 bug and `source_type` keying cannot express it.

Second, smaller conflict: `sqlserver-health-watch.md` INV-11 says `source_type` is a closed
`Literal` by design; `pipeline-self-healing-fleet.md` §2.2 widens it to `str`. The widening won —
INV-11 needs deleting, not honoring.
