---
title: "Pipelines that fix themselves, with a human in the loop"
epic: "BH-1255"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - pipeline-self-healing-fleet.md
  - self-healing-pipelines.md
---

# Pipelines that fix themselves, with a human in the loop

> Delegation unit. Cap 150 lines.

## The goal

When a pipeline breaks for a reason the platform recognises, it diagnoses the cause and opens a
small, reviewable pull request with the fix — then waits for a human to merge. The customer wakes
up to a proposed fix with evidence, not a red dashboard. Adding a new fixable failure type is a
registry entry, not a rewrite.

## Why now

Detection already works: the watchdog spots failures across engines today. What's missing is the
loop that turns a detected failure into a proposed fix. Right now every failure ends at an alert,
so a customer with a recurring, well-understood breakage gets told about it every night and fixes
it by hand every night.

## What to build

1. `brightbot` — a pipeline registry: which pipelines we watch, per workspace, per engine, so
   healing is scoped to real known pipelines rather than whatever a poll happens to find.
2. `brightbot` — a healer registry: one entry per recognised failure type, each knowing how to
   diagnose and how to propose a fix. Start with the four data-shape failures already sandboxed.
3. `brightbot` — the remediation record: a pipeline moves through detected → diagnosed → PR open
   → merged → verified, and each state is persisted. No failure silently disappears between polls.
4. `brightbot` — post-merge verification: after a human merges the fix, re-check honestly and say
   whether it actually worked. A merged PR is not proof.
5. `brightbot` — **the agent must be structurally unable to merge its own PR.** Not a prompt
   instruction — the merge tool must be absent from the agent's toolset, enforced at registration
   and re-checked at dispatch.

## Done when

- [ ] A seeded data-shape failure produces a PR with a diagnosis a reviewer can follow
- [ ] The agent cannot self-merge — proven by a test that attempts it and fails at the tool layer,
      not by reading a prompt
- [ ] After a human merges, the platform re-checks and reports honestly, including reporting that
      a fix did **not** work
- [ ] The same failure detected twice does not open two PRs
- [ ] A new failure type is added by registering a healer, touching no dispatch or routing code
- [ ] Real-behavior test end-to-end against a real repo and a real pipeline run

## Don't do

- **Auto-merge, under any framing.** This gate is unconditional across every healer.
- **Warehouse connectivity and staleness** — owned by
  [Warehouse health you can trust](THEME-warehouse-health-truth.md). This theme consumes the
  signals it produces.
- **Job-runtime failures without a data-shape signature** — alert only. Don't invent a healer
  for a failure class we can't reliably diagnose.
- **The remediation-state prose in `self-healing-pipelines.md` §"Post-merge verification"** — the
  fleet spec already types this properly. Delete that section when folding, don't merge both.
- **SSIS/SSRS → dbt regeneration.** Explicitly out of trial scope and parked.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | pipeline registry, healer registry, remediation record, verification loop |
| `brighthive-platform-core` | persist remediation state |
| `brighthive-e2e` | seeded-failure → PR → merge → verify feature test |

**Tickets:** BH-1255 (epic), BH-1047 (the no-self-merge code lock), BH-1091, BH-1092

---

## Notes for whoever picks this up

**Blocked by decision 1 in [THEMES.md](THEMES.md)** — this theme's source spec defines a
`ConnectionDirectory` port for polling every warehouse, and the connectivity watchdog spec defines a
different mechanism for the same job. Settle that first; this theme should consume whichever wins
rather than carrying its own.

**On the self-merge gate (item 5):** this was previously a prompt-only instruction with **no
code-level enforcement** — the agent was told not to merge, and nothing stopped it. Treat the
tool-level exclusion as the actual requirement and the prompt as a courtesy. A test that asserts
the prompt contains the words "never merge" does not satisfy this.

**Fold, don't merge wholesale:** `self-healing-pipelines.md` (BH-526) contributes its four
sandboxed data-shape failure modes as healer registrations. Everything else in it — particularly
its verification-loop design — is superseded by the fleet spec's typed version.
