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

> **Superseded specs:**
> - [sqlserver-health-watch.md](./sqlserver-health-watch.md)
> - [warehouse-health-snapshot.md](./warehouse-health-snapshot.md)
> - [warehouse-connectivity-monitoring-alerts.md](./warehouse-connectivity-monitoring-alerts.md)
> - [pipeline-connectivity-watchdog.md](./pipeline-connectivity-watchdog.md)
> - [longitudinal-drift-watchdog-wiring.md](./longitudinal-drift-watchdog-wiring.md)


> Delegation unit. One engineer, one theme. Cap 150 lines.

## The goal

Every warehouse a customer connects is actually being watched, the status they see on the
Health Checks page is true right now, and when something breaks they get told what broke and
what to do about it. Today all three of those fail: most connections are never polled, a
stale "Healthy" can sit on screen for weeks, and when an alert does fire it's a generic bell
with no useful text.

## Why now

Impact Capital, staging, 2026-08-18 (**BH-1457**): a warehouse was deleted outright on the cloud
side, and the dashboard still showed **Healthy** with a last-checked date 13 days old. If you
click "check this connection" the platform correctly reports it as down — so it already knew, and
the page still said it was fine. Same failure as the earlier Loop Capital outage behind BH-1363.

## What to build

1. `brightbot` — poll **every** configured warehouse in a workspace, not just whichever one the
   code happens to pick first. A workspace counts as reachable while at least one warehouse is
   reachable. **Decide and record:** what the workspace shows when the *default* warehouse is
   down but a secondary is up. Recommendation — the workspace is "Degraded", the default's row is
   "Down", and the default's status is the headline. Silently showing green because a secondary
   answered is the BH-1457 failure wearing a different hat.
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
7. `brightbot` — the drift watchdog emits zero signals on every poll because of two unwired
   inputs: `longitudinal_drift_pipeline_source.py:127` returns early whenever `history_provider`
   is unset, and every adapter is built with an empty config at
   `pipeline_watchdog_task.py:162` (`build_pipeline_source(source_type=source_type, config={})`),
   so it never gets one. Second, there is no trailing history to compare against until a
   workspace has run the longitudinal capability at least once. Connect both, and assert a
   non-zero signal count in the test.

## Done when

- [ ] A workspace with 3 warehouses and 1 down shows 2 healthy + 1 down — never a
      workspace-wide "unreachable"
- [ ] With the **default** warehouse down and a secondary up, the workspace shows Degraded and
      the default is the named cause — not green
- [ ] Deleting a database on a reachable server flips that connection to Down within one
      poll cycle
- [ ] A connection with no poll in >45 min shows "Unknown" on the real staging Analytics
      page, not a cached "Healthy"
- [ ] A down connection's Slack card names the connection and states the check to run
      (reachability, credentials, or whether the database still exists)
- [ ] "Check connection now" returns a live verdict and leaves the shared snapshot untouched
- [ ] Connecting a warehouse in a fresh workspace results in a watchdog schedule existing
- [ ] The drift watchdog emits a non-zero signal count on a workspace with seeded history
- [ ] Real-behavior test: create a scratch database, poll (passes), drop it, poll again
      (fails) against a real SQL Server — not a mock

## Don't do

- **Self-healing / remediation PRs** — owned by [Pipelines that fix themselves](THEME-fleet-self-healing.md).
- **The landing-page health band, catalog cards, and the scheduled digest** — owned by
  [The screen never lies](THEME-honest-surfaces.md). That theme also owns the `"Unknown"` label
  for never-checked services; this theme introduces it for *stale* readings. Same word, same
  meaning — coordinate wording, don't invent a second label.
- **Target-existence for Snowflake / Databricks / Redshift / Oracle** — SQL Server is the
  first engine. Audit the others and file per-engine follow-ups; don't build them here.
- **Cross-engine read/write/lineage correctness** — owned by
  [Same answers on every warehouse engine](THEME-cross-engine-correctness.md).
- **Per-connection schedule granularity** — the watchdog stays per-workspace.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | poll every warehouse, target-existence check, drift watchdog wiring |
| `brighthive-platform-core` | staleness gate, on-demand mutation, auto-schedule, inbox renderer |
| `brightbot-slack-server` | alert copy for two signal types |
| `brighthive-webapp` | check-now button, schedule option |
| `brighthive-e2e` | stale-renders-Unknown + dropped-target feature tests |

**Tickets:** BH-1363 (unmerged root-cause fix — land first), BH-1367, BH-1457
*(BH-1368 is owned by [The screen never lies](THEME-honest-surfaces.md) — don't pick it up here)*

---

## ⚠️ Decision 1 in [THEMES.md](THEMES.md) — settle before code starts

Two specs independently invented a way to poll every warehouse for item 1, and each defers to the
other:

- [`pipeline-self-healing-fleet.md`](./pipeline-self-healing-fleet.md) §2.2 — a `ConnectionDirectory` port + `build_sources_for_workspace`, keyed by `source_type`
- [`pipeline-connectivity-watchdog.md`](./pipeline-connectivity-watchdog.md) §2.3 — `poll_configured_warehouses` + `WAREHOUSE_TYPE_TO_SOURCE_TYPE`, keyed by warehouse and honoring `is_default`

Pick one and delete the other from its spec. Recommendation: **the warehouse-keyed one**, because
honoring `is_default` is the actual BH-1457 bug and `source_type` keying cannot express it.

Second, smaller conflict: [`sqlserver-health-watch.md`](./sqlserver-health-watch.md) INV-11 says `source_type` is a closed
`Literal` by design; [`pipeline-self-healing-fleet.md`](./pipeline-self-healing-fleet.md) §2.2 widens it to `str`. The widening won —
INV-11 needs deleting, not honoring.
