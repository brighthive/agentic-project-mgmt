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

The three source specs total 2,593 lines and all read as shipped, which hides that real items are
still open inside them. Most urgent: before offering to automate a recurring request, the platform
is supposed to check that the person asking actually manages the people involved. **That check has
no source of org-chart data, so it never really runs** — and it is live in production right now. It
was recorded as a P0 follow-up on line 1,077 of a spec marked "implemented" and never turned into a
ticket, which is exactly why this consolidation is happening.

## What to build

1. `brightbot` — **P0**: fix the manager-to-reports check. **First answer one question: does the
   platform have any source of org-chart data at all?** If no — the likely answer — delete the
   check and say plainly in the code that we don't verify reporting lines, which is an hour's work.
   If yes, wire it. What must not survive is a check that looks present and never runs.
2. `brightbot` — record traces on the intent-capture path so we can see it working (BH-972).
3. `brighthive-webapp` — the two deferred pieces of the offer UI: show the quote that triggered the
   suggestion, and let the user adjust it before accepting.

## Done when

- [ ] The manager-to-reports check either verifies against a named real source, or is gone — and a
      test proves which
- [ ] BH-915/916 confirmed live on staging (needs the blocker below cleared first)
- [ ] Intent-capture traces visible in a real run
- [ ] The triggering quote and the Adjust control both render in the webapp
- [ ] The three source specs are moved to `docs/features/` — shipped work does not sit in the
      spec queue

## Don't do

- **Rebuild anything in the three source specs** — capture, detector, judge, suggestion API,
  scheduling substrate, and read-back all ship. Read them as reference, not as work.
- **Edit-in-place, Slack read-back parity, PAUSED state** — explicitly out of scope in
  `brightroutines-your-routines-persistence.md` §5. Leave them out.
- **Detector fan-out / queueing / per-tenant fairness**
  (`brightroutines-detector-fanout-fairness.md`) — premature. It designs for hundreds of
  simultaneous workspaces; staging runs 3–5. Park until workspace count or a real incident
  justifies it.
- **Online judge circuit breaker** (`brightroutines-online-judge-eval-circuit-breaker.md`) —
  same call. Park until there is a live judge-quality incident.
- **Routine delivery channels (Slack channel target, provenance, PDF, email)** — a separate
  BrightRoutines delivery theme not yet written; `brightroutines-delivery-target-and-provenance.md`
  and `brightroutines-email-delivery.md` remain its source specs. Email is lowest priority: it is
  the second unshipped email-channel effort here, and no adapter has ever sent a real message.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | gate-2 hierarchy check, capture spans |
| `brighthive-webapp` | anchor quote, Adjust affordance |

**Tickets:** BH-915, BH-916, BH-972, + a new P0 ticket for the manager-to-reports check

⚠️ **Blocked by, not built here:** BH-914 needs a secrets-edit approval from Kuri that has been
requested 8+ times and never answered. It is a decision, not engineering work, and BH-915/916
cannot be confirmed live until it clears.

---

## ⚠️ Decision 5 in [THEMES.md](THEMES.md) — settle before code starts

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
