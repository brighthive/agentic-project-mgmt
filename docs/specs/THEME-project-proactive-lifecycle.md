---
title: "An active project never goes quiet"
epic: "BH-1255"
owner: "drchinca"
status: "Draft"
created: "2026-09-03"
supersedes: []
---

# An active project never goes quiet

> Builds directly on [project-activate-sync-golden-nuggets.md](./project-activate-sync-golden-nuggets.md)
> (BH-1343, spec'd 2026-08-01, status **Needs Refinement**, **zero code written** — verified
> 2026-09-03 via grep: no `GoldenNugget`, `run_project_sync`, or `PROACTIVE_DIAGNOSTIC_BY_EXT` in
> `brightbot`). That spec designs the one-shot activation fan-out; this theme is the three things
> it doesn't cover.

## The goal

Today, activating a project is a one-time event — even once BH-1343 ships, a project that sits
ACTIVE and untouched for five days looks exactly the same as it did on day one. This theme makes
an ACTIVE project keep working: it re-checks itself on a cadence, its table/data-product quality
gates (Great Expectations, already shipped in BH-503) count as findings alongside file
diagnostics, and a user who opens a seeded session gets real Skills-driven help instead of a bare
agent with zero capabilities loaded.

## Why now

Kuri: *"you active project go away, come in 5 days and you have a lot of new richness — we don't
want sessions to be reactive, we want it proactive."* BH-1343 already designs the *first* proactive
moment (activation); nothing designs what happens on day 2 through day N. Separately, a 4-repo
audit (2026-09-03) found the `authorize()` engine's CREATE/DELETE ramp (BH-1464, ADR-0003) will
break project↔resource linking permanently the moment it flips live — that bug sits directly in
the data BH-1343's SYNC() reads, so it blocks this theme too.

## What to build

1. `brightbot` — Ship BH-1343 first (unbuilt foundation): `project.activated` → `run_project_sync`
   SYNC() → seeded sessions + roll-up signal. This theme adds nothing until that lands.
2. `brightbot` — Add `quality_check_agent` + `data_profiler_agent`
   (`agents/governance_agent/`, Great Expectations, BH-503 Shipped) as a `GoldenNugget` source
   inside SYNC() — a failing expectation suite on a table/data-product surfaces a nugget the same
   way a bad `.dtsx` file does.
3. `brightbot` — Recurring trigger: SYNC() re-runs on a cadence (start: nightly, reusing the
   existing longitudinal-monitoring nightshift scheduler, BH-503) while a project stays ACTIVE —
   not only on the DRAFT→ACTIVE edge. New nuggets since the last run seed new sessions;
   nothing-new re-runs produce zero nuggets silently (reuse BH-1343's `reason_if_empty`, never
   alert on quiet).
4. `brightbot` — Add `project` to `AGENT_SHORT` (`agents/constants.py:125`) and give it Skills
   affinity, so a user opening a seeded session and asking a follow-up gets governance/quality/
   schema Skills loaded (`DeepAgentSkillsMiddleware`, BH-860 Shipped) instead of none.
5. `brighthive-platform-core` — Fix `addResourceToProject`/`removeResourceFromProject`: add
   `workspaceId` to `ResourceProjectConnectInput`/`Disconnect` (currently resolves to `""`,
   `authorize()` fails closed forever once BH-1464 flips CREATE/DELETE live) and call
   `invalidateProjectResourcesCache` on link/unlink (today only `onboard`/`delete` do).
6. `brightbot` + `brighthive-platform-core` — Move activation-check + run-sync + the new
   recurring trigger off bare FastAPI `BackgroundTasks` onto a queue with per-workspace fairness,
   before item 3 runs this fan-out on a schedule across every ACTIVE project.

## Done when

- [ ] BH-1343's baseline works: upload a file, activate, see seeded sessions + a roll-up signal
- [ ] A project with a failing Great Expectations suite on one of its data products surfaces a
      quality nugget, seeded the same way a file diagnostic is
- [ ] A project left ACTIVE and untouched for 3+ days (staging: force a cadence tick) produces
      new sessions without a manual re-activation or Sync click, and produces zero new sessions
      when nothing changed
- [ ] Opening a seeded session and asking a follow-up shows a Skills-load OTel span with
      `project`-affinity skills present
- [ ] `addResourceToProject` on a real Neo4j test instance correctly scopes `workspaceId`, and the
      Redis cache is invalidated within the same request (not on the 300s TTL)
- [ ] At least one test hits a real backend, not a mock (`~/.claude/rules/test-behavior-real.md`)

## Don't do

- **Auto-remediation from a nugget** — a session lets the admin invoke the SSIS remediation loop
  themselves; nothing here fires a PR unattended. Owned by BH-1329.
- **A new quality-check engine** — Great Expectations via `quality_check_agent` already exists
  (BH-503, Shipped); this theme wires it into SYNC(), it does not build a second one.
- **New pipeline engine adapters** — reuse `PipelineRunner` / `PIPELINE_SOURCE_ADAPTERS`.
- **Governance/RBAC unification itself** — owned by BH-1464; this theme only fixes the two bugs
  in its blast radius (item 5) because they corrupt the data SYNC() reads.
- **Legacy file formats beyond `.dtsx`/`.rdl`/`.xsd`/`.xsl`** — owned by
  [THEME-legacy-file-intake.md](./THEME-legacy-file-intake.md).

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | SYNC() composition + quality-nugget source + recurring trigger + `project` Skills affinity |
| `brighthive-platform-core` | `workspaceId` fix + cache invalidation on resource↔project link/unlink |

**Tickets:** BH-1343 (existing, build first) + new tickets filed under BH-1255 (all `issueType:
Task`/`Bug` as noted, never `Story`)

## Related

- [project-activate-sync-golden-nuggets.md](./project-activate-sync-golden-nuggets.md) — the
  one-shot foundation (BH-1343) this theme extends to recurring + quality-aware.
- [quality-rules-configurable.md](./quality-rules-configurable.md) — BH-503, Shipped, the GE
  engine this theme wires into SYNC() as a nugget source.
- [longitudinal-monitoring.md](./longitudinal-monitoring.md) — BH-503, Shipped, the nightshift
  cadence pattern item 3 reuses rather than inventing a new scheduler.
- [skills-extension-deep-agent.md](./skills-extension-deep-agent.md) — BH-860, Shipped, the
  Skills middleware item 4 wires `project_agent` into.
- ADR-0003 (governance-enforcement-ramp, `brighthive-platform-core/docs/adr/`) — the CREATE/DELETE
  ramp item 5 fixes ahead of.
