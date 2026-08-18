---
title: "Work where the customer's data lives"
epic: "BH-1421"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - autonomous-dbt-project-lifecycle.md
  - loopcapital-onprem-read-write-sandbox.md
---

# Work where the customer's data lives

> Delegation unit. Cap 150 lines.

## The goal

A customer whose SQL Server and dbt files sit inside their own network gets the full BrightAgent
experience — read their tables, run their dbt models, propose changes as reviewable PRs — without
moving data out or opening their firewall to us. Today this only works if the files happen to be
reachable from our cloud, which for Loop Capital they are not.

## Why now

Loop Capital's SQL Server sits on their own machine behind their firewall, and it is the live
trial. Today we only reach it by holding open a temporary public tunnel from a laptop — fine for a
demo, not something a bank will run. Two specs were written a day apart with **opposite
architectures**, and the newer one says the older is wrong (see the decision below); until that's
settled, nobody can build.

## What to build

1. `brightbot` — something the customer runs on their own machine, inside their network, where the
   dbt files and the SQL Server both live. It asks our cloud for queued work over an ordinary
   outbound HTTPS connection, runs it locally, and posts results back. **The customer never opens
   an inbound port.** Four things to decide and write down before coding, because each changes the
   shape of the thing: how it is packaged and delivered (a container is the obvious answer), how it
   authenticates outbound and how that credential is issued and revoked, how often it asks for work,
   and who is responsible for upgrading it. Scope it to one workspace per running copy.
2. `brightbot` — governed model management: the agent proposes a dbt model change as a PR a human
   reviews and merges. It never writes to the customer's repo or warehouse directly.
3. `brightbot` — a reproducible local SQL Server sandbox (Docker) with least-privilege logins, so
   this path is testable without the client's real server. The existing capture/synthesize/
   nuke-recreate tooling already covers most of this — extend it, don't restart it.
4. `brighthive-platform-core` — register the on-prem runner as a real engine so a project can be
   bound to it, and its runs show up like any other engine's.

## Done when

- [ ] A dbt model runs end-to-end against a SQL Server that is **not** reachable from our cloud,
      with no tunnel
- [ ] A proposed model change arrives as a PR with the before/after run logs attached
- [ ] The agent cannot write to the customer's warehouse or repo without a human merge — proven
      by a test that tries and fails
- [ ] `make`-level sandbox recreate produces a working local SQL Server from scratch
- [ ] Killing the network mid-run leaves the run marked failed with the reason, never "succeeded"
      and never stuck in a running state forever
- [ ] Real-behavior test: the full path runs against the real local SQL Server sandbox (item 3),
      not a mocked connection

## Don't do

- **Run dbt cloud-side against an on-prem server.** This is the corrected error — see the
  decision below. Do not carry it forward from `autonomous-dbt-project-lifecycle.md`.
- **Ship the public tunnel as product.** It stays a local dev convenience.
- **Add a new `sql_server` WarehouseType here** — owned by
  [Same answers on every warehouse engine](THEME-cross-engine-correctness.md), and it needs
  decision 3 in [THEMES.md](THEMES.md) settled first.
- **Legacy `.dtsx`/`.rdl` parsing** — owned by
  [Drop in your legacy pipeline files](THEME-legacy-file-intake.md).
- **New warehouse write/DDL abstraction** — deferred; nothing in this theme needs it.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | in-network runner, governed model proposals, sandbox tooling |
| `brighthive-platform-core` | register the on-prem engine, surface its runs |

**Tickets:** BH-1421 (epic, In Progress), BH-1403 (epic, In Progress), BH-1404/1405/1406 (sandbox
— already merged)

---

## ⚠️ Decision 4 in [THEMES.md](THEMES.md) — settle before code starts

Two specs, written one day apart, build opposite architectures — and the newer one explicitly
says the older is wrong:

- `autonomous-dbt-project-lifecycle.md` (2026-08-12) — `DbtCoreRunner.run_on_ref` shells out to
  `dbt build` **from brightbot in our cloud**, pointed at the customer's SQL Server.
- `on-prem-engineering-runner.md` (2026-08-13) — its ADR-0002 states that cloud-side execution
  against an on-prem server was **"the error"** of ADR-0001, and moves execution into the
  customer's network.

Recommendation: **ADR-0002 wins.** Cloud-side execution requires the customer to expose their
database to us, which is the thing enterprise buyers refuse. Mark
`autonomous-dbt-project-lifecycle.md` superseded, and salvage only its sandbox tooling and
governed-model-proposal halves — both are architecture-neutral.

Housekeeping while you're in there: `on-prem-engineering-runner.md`'s Test Coverage section is a
**completion report** (48 passing tests, ✅ rows) sitting inside a doc marked `Draft`. That
belongs in a feature doc — a spec that reports its own tests as already passing is not a spec.
