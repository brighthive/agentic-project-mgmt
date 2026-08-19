---
title: "Routine results land where the team already works"
epic: "BH-876"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - brightroutines-delivery-target-and-provenance.md
  - brightroutines-email-delivery.md
---

# Routine results land where the team already works

> **Superseded specs:**
> - [brightroutines-delivery-target-and-provenance.md](./brightroutines-delivery-target-and-provenance.md)
> - [brightroutines-email-delivery.md](./brightroutines-email-delivery.md)


> Delegation unit. Cap 150 lines.

## The goal

When a routine runs, its result goes to the place the team actually watches — a specific Slack
channel, not just the person who set it up — and it says where the numbers came from, so nobody has
to take it on trust. A recurring report becomes something a team relies on rather than something one
person forwards.

## Why now

Today a routine's result reaches whoever created it. That makes it a personal reminder, not a team
report — which is what customers actually asked for. And because the result arrives without saying
which query produced it, the first question back is always "where is this from?", which the sender
can't answer without digging.

## What to build

1. `brighthive-platform-core` — a routine remembers **where its results go**: a Slack channel, the
   in-app inbox, or both. Set per routine, changeable after creation.
2. `brightbot` — every result carries its provenance: the query that produced it and any file it
   generated, stored alongside the result rather than reconstructed later.
3. `brightbot-slack-server` — the card shows the numbers *and* a way to see the query behind them.
4. `brightbot` — results that are naturally a document (a monthly digest, an exposure report) can be
   delivered as a PDF rather than a wall of text in a message.

## Done when

- [ ] A routine delivers to a named Slack channel that the creator is not the only member of
- [ ] Changing a routine's destination takes effect on the next run, without recreating it
- [ ] Every delivered result can show the query that produced it
- [ ] A digest-shaped routine delivers a readable PDF
- [ ] A delivery failure (channel deleted, bot removed) is reported to the routine owner rather
      than silently dropped
- [ ] Real-behavior test: a real routine run delivers to a real Slack channel and the provenance
      opens

## Don't do

- **Email delivery — build it last, or not at all this pass.** Two separate email efforts have been
  specced here and neither ever sent a real message; the mail-provider choice was never settled.
  Slack and the in-app inbox are the live channels. Only add email against a named customer ask.
- **Fix anything in the shipped routine engine** — detection, offering, scheduling, and read-back
  all work. Residual items there are owned by
  [Finish BrightRoutines](THEME-brightroutines-closeout.md).
- **Generating the routine's content from intent** — owned by
  [Describe a routine and get one](THEME-routine-authoring.md).
- **New alert types** unrelated to routines — that's the notification surface, not this.

## Where it lives

| Repo | What changes |
|---|---|
| `brighthive-platform-core` | destination stored per routine, provenance stored with the result |
| `brightbot` | attach provenance, render PDF output |
| `brightbot-slack-server` | channel delivery + provenance affordance on the card |
| `brighthive-webapp` | pick a destination when creating or editing a routine |

**Tickets:** BH-876 (epic, `Done` — this is next-phase work under it; confirm whether it needs a
new epic before creating children)

---

## Notes for whoever picks this up

Both source specs are `status: proposed`, not Draft — they were written as proposals and never
picked up, so treat their designs as suggestions rather than decisions. They are cleanly layered:
the delivery-target spec routes, and defers all email rendering to the email spec. That layering is
fine; the priority order is what changes here — routing and provenance are the customer ask, email
is the part with a two-for-two record of never shipping.

**On item 1:** the destination belongs to the routine, not to the person. That's the whole point of
this theme, and it is the one thing to get right before the rest — everything else is rendering.
