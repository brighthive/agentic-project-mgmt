---
title: "Describe a routine and get one"
epic: "BH-1463 — BrightRoutines next-phase (opened 2026-08-19; BH-897 was a Task under Done-epic BH-876)"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - brightroutines-ai-authored-workflowspec.md
---

# Describe a routine and get one

> **Superseded specs:**
> - [brightroutines-ai-authored-workflowspec.md](./brightroutines-ai-authored-workflowspec.md)


> Delegation unit. Cap 150 lines.

## The goal

A customer describes what they want in their own words — *"every Monday, check the holdings table
loaded, compare it to last week, and tell the team if anything looks off"* — and the platform builds
the multi-step routine that does it. Today only single-step routines can be created this way;
anything with more than one step has to be assembled by hand.

## Why now

The platform already spots that someone keeps asking for the same thing and offers to automate it.
When they accept, it can only produce a one-step routine. Every genuinely useful recurring
request — check, compare, then report — is more than one step, so the offer leads to something less
capable than what the customer asked for. This is the gap between the promise and what lands.

## What to build

1. `brightbot` — gather the real context first: which tables, which warehouse, which schedule the
   customer actually said. Never guess a table name; if it's ambiguous, ask.
2. `brightbot` — draft the multi-step routine from that context.
3. `brightbot` — validate the draft before it is ever offered: every table exists, every step's
   input comes from a previous step or the gathered context, the schedule is expressible.
4. `brightbot` — a draft that fails validation is **not offered**. Say what was missing and ask,
   rather than presenting something that will fail on first run.
5. `brighthive-webapp` — show the customer the steps in plain language before they accept.

## Done when

- [ ] A three-step request produces a three-step routine that runs successfully
- [ ] A request naming a table that doesn't exist produces a question, not a broken routine
- [ ] A draft that fails validation is never offered to the customer
- [ ] The customer sees the steps in words they can check before accepting
- [ ] An accepted routine runs end-to-end on its schedule without hand-editing
- [ ] Eval: a set of real recurring requests produces routines that pass validation at an agreed
      rate, measured before this is enabled for customers — this is the one theme where an LLM
      writes something the customer relies on, so it needs a scored bar, not just tests

## Don't do

- **Replace the single-step path** until the multi-step one beats it on the eval above. Keep the
  simple wrapper for genuinely one-step intents.
- **Detection, offering, or scheduling** — all shipped; owned by
  [Finish BrightRoutines](THEME-brightroutines-closeout.md).
- **Where results are delivered** — owned by
  [Routine results land where the team already works](THEME-routine-delivery.md).
- **Letting the routine write to the warehouse.** Authoring produces read-and-report routines.
  Anything that writes goes through the human-approved path, not this one.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | context gathering, multi-step drafting, validation before offer |
| `brighthive-webapp` | plain-language step preview before accept |

**Tickets:** BH-897 (`Needs Refinement`, 0 of 7 started — genuinely greenfield). Note: BH-897 is a
Task, not an epic, and its parent BH-876 is `Done` — a new open epic is needed before children land.

---

## Notes for whoever picks this up

This is the **largest un-started theme** and the only one where a model authors something a customer
then depends on running unattended. That is why item 6 asks for a scored eval rather than a pass/fail
test: a routine that is subtly wrong but valid will run every week and nobody will notice.

Sequence matters — item 3 (validation) is worth building **before** item 2 (drafting). If you build
drafting first, you will spend the time debugging plausible-looking routines by hand; with validation
first, every draft gets an immediate verdict.

The source spec is sound on its ground-then-draft-then-validate shape and correctly explains why it
replaces the existing single-step wrapper rather than duplicating it. Its detail on prompt structure
is worth reading; its ticket breakdown is untouched.
