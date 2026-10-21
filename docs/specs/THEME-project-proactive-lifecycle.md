---
title: "An active project never goes quiet"
epic: "BH-1255"
owner: "drchinca"
status: "Draft"
created: "2026-09-03"
last-reviewed: "2026-09-04"
supersedes: []
---

# An active project never goes quiet

> Builds directly on [project-activate-sync-golden-nuggets.md](./project-activate-sync-golden-nuggets.md)
> (BH-1343, spec'd 2026-08-01, status **Needs Refinement**, **zero code written** — verified
> 2026-09-03 via grep: no `GoldenNugget`, `run_project_sync`, or `PROACTIVE_DIAGNOSTIC_BY_EXT` in
> `brightbot`). That spec designs the one-shot activation fan-out; this theme is what keeps
> running after it.

## The goal

Every fintech, insurance, and investment firm we sell into already runs an ELT/ETL pipeline —
that part isn't new to anyone. What none of them have is something watching **both ends of it**
without being asked: catching a source going bad before it's ingested, and catching a
transformation's output before it reaches a dashboard a customer or exec is looking at. A
BrightHive Project is where that watching lives.

Right now, a Project is exactly as smart as the last time someone opened it. Flip it ACTIVE, walk
away for a week, come back — it looks the same as the day you turned it on. This theme makes that
untrue. Once ACTIVE, a Project keeps working on its own: pipelines get watched, data products get
graded against the quality bar you set, and every finding becomes a **golden nugget** waiting in
the Project's agent view — not a report you go dig for, but something that was already there the
next time you looked.

The test that matters: leave an active Project alone for five days. Come back. It should know more
than when you left.

## Why now

Kuri: *"you active project go away, come in 5 days and you have a lot of new richness — we don't
want sessions to be reactive, we want it proactive."* And separately: *"projects are an extension
to existing ELT/ETL pipelines, which all big data companies have... we can add agentic behaviors
PRE-ELT and POST-ETL, which is a very powerful thing."*

That second idea isn't new — it's [lineage-aware-data-quality.md](./lineage-aware-data-quality.md)
(BH-1061), written 2026-07-12: *"BrightHive's job is to be the glue — connect what happens before
ingestion to what happens after transformation... because dbt/Databricks structurally cannot see
before their own input or after their own output."* And **schema enforcement on transformations**
is [THEME-governance-enforced.md](./THEME-governance-enforced.md) (BH-172) — a real design (one
enforcement point, called from the transform-run path, fails closed) that's been sitting in Draft
only because its five tickets were never filed. Neither of those needed inventing this week. What
was missing is the thing that keeps calling them: BH-1343 designs the *first* proactive moment
(activation); nothing designs day 2 through day N. A 4-repo audit (2026-09-03) also found the
`authorize()` engine's CREATE/DELETE ramp (BH-1464, ADR-0003) will break project↔resource linking
the moment it flips live — that bug sits directly in the data this theme's fan-out reads.

## What to build

1. `brightbot` — Ship **BH-1343** first (unbuilt foundation): `project.activated` →
   `run_project_sync` SYNC() → seeded sessions + roll-up signal. This theme adds nothing until
   that lands.
2. `brightbot` — **BH-1503**: add `quality_check_agent` + `data_profiler_agent`
   (`agents/governance_agent/`, Great Expectations, BH-503 Shipped) as a `GoldenNugget` source
   inside SYNC() — a failing expectation suite on a table/data-product surfaces a nugget the same
   way a bad `.dtsx` file does.
3. `brightbot` — **BH-1504**: recurring trigger — SYNC() re-runs on a cadence (start: nightly,
   reusing the existing longitudinal-monitoring nightshift scheduler, BH-503) while a project
   stays ACTIVE — not only on the DRAFT→ACTIVE edge. New nuggets since the last run seed new
   sessions; nothing-new re-runs produce zero nuggets silently (reuse BH-1343's
   `reason_if_empty`, never alert on quiet).
4. `brightbot` — **BH-1505** (Shipped, PR [brightbot#1061](https://github.com/brighthive/brightbot/pull/1061)):
   `project` Skills affinity, so a user opening a seeded session and asking a follow-up gets
   governance/quality/schema Skills loaded instead of none.
5. `brighthive-platform-core` — **BH-1506 + BH-1507** (Shipped, PR
   [platform-core#1276](https://github.com/brighthive/brighthive-platform-core/pull/1276)):
   `addResourceToProject`/`removeResourceFromProject` now scope `workspaceId` correctly and
   invalidate the resource cache on link/unlink.
6. `brightbot` + `brighthive-platform-core` — **BH-1508**: move activation-check + run-sync + the
   new recurring trigger off bare FastAPI `BackgroundTasks` onto a queue with per-workspace
   fairness, before item 3 runs this fan-out on a schedule across every ACTIVE project.

**Not in this theme, but this is where it plugs in later** — once BH-172 files its tickets and
ships its enforcement point, and BH-1061 ships the pre-ELT/post-ETL lineage bridge, SYNC() (item
1) gains two more nugget sources for free: a blocked schema contract and a poisoned-source alert
naming its downstream Gold/Diamond tables both become golden nuggets the same way a quality-check
failure already does. No new mechanism — SYNC() already knows how to turn "something was found"
into "a session is waiting for you."

## Done when

- [ ] BH-1343's baseline works: upload a file, activate, see seeded sessions + a roll-up signal
- [ ] A project with a failing Great Expectations suite on one of its data products surfaces a
      quality nugget, seeded the same way a file diagnostic is
- [ ] A project left ACTIVE and untouched for 3+ days (staging: force a cadence tick) produces
      new sessions without a manual re-activation or Sync click, and produces zero new sessions
      when nothing changed
- [x] Opening a seeded session and asking a follow-up shows a Skills-load OTel span with
      `project`-affinity skills present — verified via new tests, brightbot#1061
- [x] `addResourceToProject` on a real Neo4j test instance correctly scopes `workspaceId`, and the
      Redis cache is invalidated within the same request — verified via new tests, platform-core#1276
- [ ] At least one test hits a real backend, not a mock (`~/.claude/rules/test-behavior-real.md`)

## Don't do

- **Auto-remediation from a nugget** — a session lets the admin invoke the SSIS remediation loop
  themselves; nothing here fires a PR unattended. Owned by BH-1329.
- **A new quality-check engine, a new schema-enforcement engine, or a new lineage engine** — BH-503
  (quality), BH-172 (schema/policy), and BH-1061 (lineage bridge) already own those designs. This
  theme is a caller, not a second implementation of any of them.
- **New pipeline engine adapters** — reuse `PipelineRunner` / `PIPELINE_SOURCE_ADAPTERS`.
- **Governance/RBAC unification itself** — owned by BH-1464; this theme only fixes the two bugs
  in its blast radius (item 5, shipped) because they corrupt the data SYNC() reads.
- **Legacy file formats beyond `.dtsx`/`.rdl`/`.xsd`/`.xsl`** — owned by
  [THEME-legacy-file-intake.md](./THEME-legacy-file-intake.md).

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | SYNC() composition + quality-nugget source + recurring trigger + `project` Skills affinity |
| `brighthive-platform-core` | `workspaceId` fix + cache invalidation on resource↔project link/unlink |

**Tickets:** BH-1343 (existing, build first) blocks BH-1503, BH-1504; BH-1505, BH-1506, BH-1507
**shipped**; BH-1508 open — all `issueType: Task` under BH-1255.

## Related

- [project-activate-sync-golden-nuggets.md](./project-activate-sync-golden-nuggets.md) — the
  one-shot foundation (BH-1343) this theme extends to recurring + quality-aware.
- [THEME-governance-enforced.md](./THEME-governance-enforced.md) — BH-172, Draft, blocked only on
  ticket creation. This is "enforce schemas in the transformations" — SYNC() calls it once it
  ships, does not rebuild it.
- [lineage-aware-data-quality.md](./lineage-aware-data-quality.md) — BH-1061, Partial, the
  pre-ELT/post-ETL lineage bridge. SYNC()'s second future nugget source, same reasoning.
- [quality-rules-configurable.md](./quality-rules-configurable.md) — BH-503, Shipped, the GE
  engine this theme wires into SYNC() as a nugget source today.
- [longitudinal-monitoring.md](./longitudinal-monitoring.md) — BH-503, Shipped, the nightshift
  cadence pattern item 3 reuses rather than inventing a new scheduler.
- [skills-extension-deep-agent.md](./skills-extension-deep-agent.md) — BH-860, Shipped, the
  Skills middleware item 4 wires `project_agent` into.
- ADR-0003 (governance-enforcement-ramp, `brighthive-platform-core/docs/adr/`) — the CREATE/DELETE
  ramp item 5 fixed ahead of.
