---
title: ""
epic: "BH-XXX"
owner: ""
status: "Draft | Ready to delegate | In progress | Done"
created: "YYYY-MM-DD"
supersedes: []          # specs this theme replaces — they get archived, not left to rot
---

# [Theme name — what a customer gets, in plain words]

> **A theme spec is a delegation unit, not a design document.** One engineer reads it
> once and starts working. Hard cap: **150 lines**. If it needs more, it is two themes.
> Simple and clear beats detailed and vague — length is a cost, not a credential.

## The goal

One paragraph. What a customer can do after this ships that they cannot do today.
No architecture, no types, no file paths. If a non-engineer cannot follow it, rewrite it.

## Why now

The real evidence — an incident, a client blocker, a live bug. Link the ticket or the
captured proof. Two or three sentences. If there is no concrete trigger, this theme is
not ready to delegate.

## What to build

Numbered, concrete, each item a thing an engineer can finish and demo. Name the real
repo and the real file where known. This is the only long section, and it is still a
list — not prose.

1. `repo` — [the change]
2. `repo` — [the change]

## Done when

A checklist anyone can verify by running something or looking at a screen. Each line is
observable, not internal. This replaces exhaustive Gherkin at theme level — write real
scenarios in the implementation ticket if the behavior is genuinely subtle.

- [ ] [observable outcome, verifiable by a named command or screen]
- [ ] [error path behaves correctly]
- [ ] at least one test hits the real backend, not a mock (`~/.claude/rules/test-behavior-real.md`)

## Don't do

Explicit non-goals — the boundary that keeps this theme finishable. Name the adjacent
theme that owns each excluded thing, so nothing looks forgotten.

## Where it lives

| Repo | What changes |
|---|---|
| `repo` | [one line] |

**Tickets:** BH-XXXX, BH-XXXX (all `issueType: Task` under the epic above)

---

## When to write MORE than this

Reach for the full `SPEC_TEMPLATE.md` sections — typed contracts, invariants, correctness
properties, observability contract — only for the individual implementation ticket, and
only when it genuinely has:

- a **state machine** (real status transitions that can go wrong), or
- a **security or tenancy boundary** (cross-workspace, credentials, write paths), or
- a **concurrency or time guarantee** (deadlines, TTLs, fan-out fairness).

Everything else — a read path, a UI surface, a config change, a new field — ships from
the theme spec plus the ticket. Adding invariants to a CRUD read to satisfy a template
is the exact failure this file exists to prevent.
