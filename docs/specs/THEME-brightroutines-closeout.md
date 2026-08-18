---
title: "Finish BrightRoutines"
epic: "BH-876"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - brightroutines-intent-loop.md
  - brightroutines-execute-workflow-schedule.md
  - brightroutines-your-routines-persistence.md
---

# Finish BrightRoutines

> Delegation unit. Cap 150 lines. **BH-876 is already `Done` in Jira and the three source
> specs say `implemented-verified-staging`** — this theme is the short tail of real work
> left behind them, not a rebuild.

## The goal

BrightRoutines works today: the platform spots a recurring request, offers to turn it into a
routine, and runs it on a schedule. Four things are still loose behind that — one of them is a
live correctness risk. Close them and the feature is genuinely finished.

## Why now

The three source specs total 2,593 lines and all read as shipped, which hides the fact that
real items are still open inside them. Most urgent: the intent detector's gate 2
(manager → direct-reports check) **fails closed with no hierarchy data source** and is live in
production right now — recorded in `brightroutines-intent-loop.md` §17.4 as a P0 follow-up that
was never lifted out into a ticket. A P0 buried on line 1,077 of a spec marked "implemented" is
exactly why this consolidation is happening.

## What to build

1. `brightbot` — **P0**: fix gate 2's manager→reports check. It currently fails closed with no
   hierarchy source, so the live detector has no hierarchy check at all. Either wire a real
   source or remove the gate honestly — do not leave a check that silently never runs.
2. **Unblock BH-914** — a secrets-edit approval that has been requested 8+ times and never
   answered. This is a decision from Kuri, not engineering work, and it is what keeps
   BH-914/915/916 from confirming live on staging.
3. `brightbot` — capture OTel spans on the intent-capture path (BH-972).
4. `brighthive-webapp` — the deferred UX polish from §17.1/§17.3: anchor-quote display and the
   Adjust affordance.

## Done when

- [ ] Gate 2 either performs a real hierarchy check against a named source, or is gone — and a
      test proves which
- [ ] BH-914 answered; BH-915/916 confirmed live on staging
- [ ] Intent-capture spans visible in a real trace
- [ ] Anchor quote and Adjust render in the webapp
- [ ] The three source specs are moved to `docs/features/` — shipped work does not sit in the
      spec queue

## Don't do

- **Rebuild anything in the three source specs** — capture, detector, judge, suggestion API,
  scheduling substrate, and read-back all ship. Read them as reference, not as work.
- **Edit-in-place, Slack read-back parity, PAUSED state** — explicitly out of scope in
  `brightroutines-your-routines-persistence.md` §5. Leave them out.
- **Detector fan-out / SQS / per-tenant fairness** (`brightroutines-detector-fanout-fairness.md`)
  — premature. It designs against a thundering herd for hundreds of workspaces; staging runs
  3–5. Park until workspace count or a real incident justifies it.
- **Online judge circuit breaker** (`brightroutines-online-judge-eval-circuit-breaker.md`) —
  same call. Park until there is a live judge-quality incident.
- **Email delivery** — see the delivery theme; treat as stretch, not scope.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | gate-2 hierarchy check, capture spans |
| `brighthive-webapp` | anchor quote, Adjust affordance |

**Tickets:** BH-914 (blocked on approval), BH-915, BH-916, BH-972, + a new P0 for gate 2

---

## ⚠️ One decision before code starts

Two specs build **competing write paths for "human approves a routine → it gets scheduled"**,
and only one can exist:

- `slack-routine-suggestion-scheduling.md` (BH-1001–1004, **largely shipped**) — Slack button →
  slack-server → platform-core `scheduleRoutineSuggestion` mutation → brightbot. Goes through
  platform-core, so Neo4j ownership edges get written.
- `brightroutine-approve-schedule.md` (BH-1255, Draft) — a **second, parallel** OFFERED →
  SCHEDULING → SCHEDULED state machine using LangGraph `interruptible()` that POSTs straight to
  brightbot's `create_schedule`, **bypassing platform-core's mutation and the ownership edges
  entirely**.

Recommendation: **keep the shipped platform-core path**. Bypassing it loses the ownership edges
and splits the audit trail — and BH-1255's own §5 already assumes the Slack path resolved the
approver identity. Do not hand both to engineers in parallel.

Also: `brightroutines-naming-proposal.md` is self-described on line 19 as *"not a spec — a
decision doc"*. Move it to an ADR or delete it once BH-953 resolves; it should not hold a slot
in the spec queue.
