---
title: "The screen never lies"
epic: "BH-409 — BrightSignals: proactive Slack notifications (decided home per ROADMAP board 2026-08-19; the degraded-badge/alert work fits BrightSignals. Tracked under consolidation epic BH-1036. BH-1340 reparent into BH-409 is a ~30s manual Jira UI move — team-managed project)"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - hive-health-landing-indicator.md
  - honest-observe-surface.md
  - fleet-health-digest-push.md
  - pipeline-run-logs-observability-surfacing.md
  - derived-metrics-compute-framework.md
  - profiler-metrics-landing-e2e.md
---

# The screen never lies

> **Superseded specs:**
> - [hive-health-landing-indicator.md](./hive-health-landing-indicator.md)
> - [honest-observe-surface.md](./honest-observe-surface.md)
> - [fleet-health-digest-push.md](./fleet-health-digest-push.md)
> - [pipeline-run-logs-observability-surfacing.md](./pipeline-run-logs-observability-surfacing.md)
> - [derived-metrics-compute-framework.md](./derived-metrics-compute-framework.md)
> - [profiler-metrics-landing-e2e.md](./profiler-metrics-landing-e2e.md)


> Delegation unit. Cap 150 lines.

## The goal

Everything the platform shows a customer is either true or honestly marked as unknown. Entering a
workspace answers "is my data estate healthy?" at a glance, run logs are actually readable, and a
weekly summary arrives without anyone asking. No green dot that means "we didn't check."

## Why now

Several surfaces currently state things they haven't verified: a status indicator shows healthy
when nothing was checked, a page-level badge says "Degraded" without saying which service is
degraded, and a perfectly normal never-checked-yet state renders as actively degraded — which
sends people looking for a fault that doesn't exist. Meanwhile the fleet-health summary exists but
only if someone thinks to ask for it.

## What to build

1. `brighthive-platform-core` — a never-checked state renders as neutral ("Unknown"/"Pending"),
   never as "Degraded". Use the same wording as the warehouse-health theme; one vocabulary.
2. `brighthive-platform-core` + `brighthive-webapp` — when a rollup badge says something is
   degraded, name which service caused it. An aggregate word with no detail is not information.
3. `brighthive-webapp` — a health band on workspace entry: service health, a profiler roll-up,
   medallion mix, and how much of the catalog the agents have enriched.
4. `brighthive-platform-core` — the band reads its expensive numbers from a stored row refreshed
   on a schedule, not by aggregating live on page load. Target: **first paint under 500ms at the
   95th percentile on a workspace with 1,000+ assets**, refreshed every 15 minutes. When the stored
   row is older than one refresh interval, show the number with its age — never hide staleness, and
   never block the page waiting for a fresh one.
5. `brighthive-webapp` — make run logs genuinely readable: wire the Observability tab to the real
   run data instead of partial fragments.
6. `brightbot-slack-server` — push the fleet-health summary on a schedule instead of on request.

## Done when

- [ ] A never-checked service shows neutral, not "Degraded" — verified on real staging data
- [ ] A "Degraded" badge names the responsible service
- [ ] The health band loads on workspace entry with real numbers, not mock data
- [ ] First paint under 500ms p95 on a 1,000+ asset workspace, measured on staging
- [ ] A roll-up older than one refresh interval displays its age rather than passing as current
- [ ] A run's logs are readable end-to-end in the Observability tab
- [ ] The weekly fleet summary arrives in Slack unprompted
- [ ] Real-behavior test: profiler numbers reach the landing surface on two engines against real
      staging data

## Don't do

- **Invent staleness for surfaces that have no polling mechanism.** The API row is hardcoded and
  transformation status is derived from connection state — those are separate, unaddressed gaps.
  Don't fake a timestamp to satisfy a UI.
- **Revive the 30-KPI analytics dashboard.** It has been on mock data since April with every
  follow-on ticket unstarted. Either it gets a real backend as its own decision, or it stays
  parked — it is not part of this theme.
- **Author or edit medallion tiers** — tier is derived from lineage depth. Display only.
- **New alert channels** — this theme is about existing surfaces telling the truth.
- **Warehouse staleness detection itself** — owned by
  [Warehouse health you can trust](THEME-warehouse-health-truth.md). **That theme lands first**;
  this one adopts whatever label it ships.

## Where it lives

| Repo | What changes |
|---|---|
| `brighthive-platform-core` | neutral-state mapping, service attribution, roll-up computation |
| `brighthive-webapp` | health band, run-log wiring, badge detail |
| `brightbot-slack-server` | scheduled fleet summary |
| `brighthive-e2e` | profiler-numbers-reach-the-landing regression test |

**Tickets:** BH-1331, BH-1340, BH-1368 (badge attribution + the Unknown mislabel — **this theme
owns BH-1368**, not the warehouse-health one), BH-1036

---

## Notes for whoever picks this up

**Item 1 shares vocabulary with the warehouse-health theme.** That theme introduces "Unknown" for
a reading that has gone stale; this one uses it for a reading that never happened. Same word, same
customer meaning: *we are not claiming to know.* Do not introduce a second label for the same idea
— check what that theme shipped before naming anything here.

**Item 4 was nearly orphaned.** The derived-metrics compute framework had no obvious home until you
notice that the health band's profiler roll-up is exactly the expensive read it was designed for.
Build it as that band's backing store, with the cross-engine profiler test as its regression cover
— not as a standalone framework looking for a consumer.

Two of the source specs use a different frontmatter shape (`name`/`slug`/`jira_epic`) than the rest
of the repo, and one has no frontmatter at all. Normalise when folding.
