---
title: "Turn on a project and it knows its own history"
epic: "BH-1255"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - project-engine-repo-binding.md
  - project-activate-sync-golden-nuggets.md
  - dbt-cloud-project-links.md
---

# Turn on a project and it knows its own history

> **Superseded specs:**
> - [project-engine-repo-binding.md](./project-engine-repo-binding.md)
> - [project-activate-sync-golden-nuggets.md](./project-activate-sync-golden-nuggets.md)
> - [dbt-cloud-project-links.md](./dbt-cloud-project-links.md)


> Delegation unit. Cap 150 lines.

## The goal

A customer points a project at their transformation engine and their repo, flips it on, and the
platform pulls in what's already there — past runs, existing models, current failures — instead
of starting from an empty screen. They see their real estate on day one, not after a week of use.

## Why now

Activation today does nothing. A customer connects dbt Cloud, activates a project, and sees nothing
until new runs happen — so the first impression of a working integration is a blank page.
Separately, **a customer can currently see other customers' dbt Cloud projects** in the picker.

## What to build

1. `brighthive-platform-core` — bind a project to its engine and its repo, admin-gated. Support
   more than one repo per project; several customers have their models split.
2. `brighthive-platform-core` — make sure a customer only sees their own dbt Cloud projects, and
   make the project ↔ engine ↔ repo link reliable. Today `updateProject` saves the id but never
   writes the graph link, so the connection looks set and isn't. **Do this one first** — it's a
   cross-customer visibility bug, not a feature.
3. `brighthive-platform-core` + `brightbot` — **one** activation trigger (see the decision below).
   When a project goes active, it fires once.
4. `brightbot` — on activation, pull the engine's existing run history and register what's found,
   through the runner port that already exists.
5. `brightbot` — surface what the pull discovered as something the customer can act on: current
   failures, stale models, undocumented assets.

## Done when

- [ ] Activating a project with existing dbt Cloud history shows that history within 5 minutes,
      without the user reloading or re-activating
- [ ] A customer sees only their own dbt Cloud projects
- [ ] The project ↔ engine ↔ repo link survives a reload — the graph edge is really written
- [ ] Activation fires exactly once; re-activating does not duplicate the pull
- [ ] A project with two repos binds both
- [ ] Real-behavior test against a real dbt Cloud account with real run history

## Don't do

- **A new engine port.** `PipelineRunner` in `pipelines/core/port.py` is the one that exists and
  works. Two source specs propose alternatives (`PipelineEnginePort`, `ProjectPipelineEngine`) that
  **appear nowhere in the codebase** — do not build a third port to sit beside a working one.
- **Provisioning new engine resources** — this theme observes and binds; it does not create.
- **On-prem runners** — owned by
  [Work where the customer's data lives](THEME-onprem-engineering.md).
- **Legacy file parsing on activation** — owned by
  [Drop in your legacy pipeline files](THEME-legacy-file-intake.md). Keep activation to engine
  state only.

## Where it lives

| Repo | What changes |
|---|---|
| `brighthive-platform-core` | binding, tenant-scoped listing, the graph edge fix, activation event |
| `brightbot` | history pull via the runner port, findings surfacing |
| `brighthive-webapp` | binding UI (admin-gated) |

**Tickets:** BH-1323, BH-1343, BH-1330, BH-172

---

## ⚠️ Decision 6 in [THEMES.md](THEMES.md) — settle before code starts

**How does activation fire?** Two source specs each design a mechanism, neither is built:

- [`project-engine-repo-binding.md`](./project-engine-repo-binding.md) §2.2 — a direct `on_project_activated` hook.
- [`project-activate-sync-golden-nuggets.md`](./project-activate-sync-golden-nuggets.md) §2.1 — a `project.activated` pub/sub event that fans
  out to a `SYNC()` routine.

They are different epics (BH-172 vs BH-1255) and were written a day apart. Pick one. Recommendation:
**the direct hook**, unless something other than the history pull needs to react to activation — a
pub/sub fan-out for a single consumer is machinery without a payoff, and it can be introduced later
if a second consumer appears.

Related cleanup: the source specs' three separate file-type dispatch tables are the legacy-intake
theme's problem, not this one. Don't recreate one here for the activation path.
