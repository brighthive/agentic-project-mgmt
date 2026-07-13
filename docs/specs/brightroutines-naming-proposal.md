---
title: "BrightRoutines DTO naming proposal — decision doc for Marwan/Nano review"
epic: "BH-876"
author: "Kuri Chinca"
status: "Draft"
created: "2026-07-07"
generates: "tickets"
tags: ["brightroutines", "naming", "refactor"]
related:
  specs:
    - brightroutines-intent-loop.md
  features: []
  pocs: []
  bedrock: []
---

# BrightRoutines DTO naming proposal

> Not a spec — a decision doc. BH-953 asks for "naming review with Marwan + Nano — pick concrete
> new names." This proposes one concrete name per item so the review is approve/counter-propose,
> not brainstorm-from-scratch. No code is renamed by this doc; it's a proposal awaiting sign-off.

## Contents

- [Status](#status)
- [Why now](#why-now)
- [Proposal](#proposal)
- [Blast radius (verified against current code)](#blast-radius-verified-against-current-code)
- [What does NOT change](#what-does-not-change)
- [Decision needed](#decision-needed)
- [Related](#related)

## Status

BH-953's explicit blocker — "do NOT rename while the BH-884→BH-950→BH-946→BH-948 stack is in
review" — is now cleared. All four are `Done` in Jira. The rename is sequencing-unblocked; the
only remaining gate is a naming decision.

## Why now

Kuri's "developer first" feedback during the BH-884 self-review (commit `6dd482c6`) already
renamed `SchedulabilityJudge` → `RoutineJudge`. Four DTOs still carry spec-jargon prefixes that
were deliberately deferred rather than force-pushed onto in-review PRs. This doc proposes closing
that gap.

## Proposal

| Current | Proposed | Rationale |
|---|---|---|
| `ProactiveSignal` | `ChatSignal` | "Proactive" describes the *feature's* posture (proactive suggestions), not the *object's* nature — a developer reading `signal.workspace_id` cold has no way to know what it's "proactive" versus. `ChatSignal` names what it actually is: a signal captured from a chat turn. (Ticket's own alternative `UserTurnSignal` is more precise but longer for no added clarity over `ChatSignal`; bare `Signal` is too generic given `RoutineScore`/`JudgeVerdict`/`GateResult` are all "signal-shaped" in this same package.) |
| `AutomationIntent` | `RoutineIntent` | "Automation" is redundant inside `brightbot/routines/` — every object in this package IS about automation. `RoutineIntent` matches the already-renamed `RoutineJudge`/`RoutineSuggestion`/`RoutinePattern` (see next row) family, giving the whole DTO chain one consistent noun. |
| `AutomationSignature` | `IntentSignature` | Same redundancy issue; `IntentSignature` (ticket's own alternative) reads better than bare `Signature` once `AutomationIntent` becomes `RoutineIntent` — it's literally `RoutineIntent.signature: IntentSignature`, which parses cleanly at the call site (`intent.signature`). |
| `RecurringAutomationPattern` | `RoutinePattern` | 27 chars → 13. "Recurring" and "Automation" are both redundant once the enclosing concept is "a routine" — a `RoutinePattern` is inherently about recurrence by definition (see `RecurringAutomationPatternStatus`, which also shortens — see below). Matches the `Routine*` family started by `RoutineJudge`/`RoutineSuggestion`. |
| `dtos.py` bucket file | **No change** | Ticket itself reconsidered — 230 lines of Pydantic in one file is idiomatic for this size, not a bucket-file problem. |

### Cascading enum/status renames (not named explicitly in the ticket, but required by the DTO renames above)

| Current | Proposed | Why it must move too |
|---|---|---|
| `AutomationIntentKind` | `RoutineIntentKind` | Enum lives on `AutomationIntent` → `RoutineIntent`; leaving the enum's old prefix would make `RoutineIntent.intent_kind: AutomationIntentKind` — the exact "which spec-jargon prefix survived and which didn't" inconsistency this ticket exists to eliminate. |
| `RecurringAutomationPatternStatus` | `RoutinePatternStatus` | Same reasoning — status enum on `RecurringAutomationPattern` → `RoutinePattern`. |

### Secondary items from the ticket

| Current | Proposed | Rationale |
|---|---|---|
| `ScoreScope` class name | **No change** — keep `ScoreScope` | Ticket's own alternative `RoutineScoreLevel` is longer with no clarity gain; `ScoreScope` already reads correctly at every call site (`scope=ScoreScope.WORKSPACE`). The `WORKSPACE`/`PROJECT`/`USER` enum values are fine as-is per the ticket's own note. |
| `build_pattern_and_suggestion` | `materialize_offer` | Ticket's own first alternative. Verb-and-verb (`build_...and...`) names the mechanism, not the outcome; `materialize_offer` names what the function produces from the caller's perspective — a candidate group that cleared every gate becomes a concrete offer. (Second alternative `emit_offer_from_group` is more precise but the extra `_from_group` doesn't earn its length — the function already takes `group` as its first positional arg, so the name doesn't need to repeat it.) |
| `compute_scores_for_workspace` | `compute_workspace_scores` | Ticket's own proposal — word order matches the existing `RoutineScore`/`ScoreScope.WORKSPACE` family (`compute_<scope>_scores`, not `compute_scores_for_<scope>`) and reads as a single noun phrase rather than a preposition chain. |

## Blast radius (verified against current code, 2026-07-07)

Grep counts — not estimates, actual current usage:

| Name | Files referencing it |
|---|---|
| `ProactiveSignal` | 20 (brightbot + tests) |
| `AutomationIntent` | 18 |
| `AutomationIntentKind` | 16 (heaviest — the enum is used far more than the DTO itself) |
| `AutomationSignature` | 13 |
| `RecurringAutomationPattern` | 13 |

**Cross-repo blast radius**: exactly one file outside `brightbot` —
`brighthive-e2e/e2e/features/scheduler/test_brightroutines_chain.py` (BH-947's chain e2e, already
named in this ticket's own AC). Zero references in `brighthive-platform-core/src` or
`brighthive-webapp/src` — confirmed via grep across both repos.

**Spec text**: `agentic-project-mgmt/docs/specs/brightroutines-intent-loop.md` references these
names 37 times — a mechanical find-and-replace pass, not a rewrite.

**Contract snapshot**: `brightbot/routines/contracts/routine_suggestion.json` uses only snake_case
field names (`pattern_id`, `routine_suggestion_id`, etc.) — **the wire shape does not change**.
Renaming the Python classes does not touch this file's contents; it only needs regenerating if
the regeneration script itself references the old class names by import.

## What does NOT change

- `RoutineSuggestion`, `RoutineSuggestionStatus`, `RoutineEvidenceSummary`,
  `ScheduleRoutineRequest`, `RoutineJudge`, `RoutineScore` — already correctly named, no `Routine*`
  prefix issue.
- Every field name on every DTO (all snake_case, none carry the debated class-name prefixes).
- The GraphQL/wire contract — `routine_suggestion.json`'s actual JSON shape.
- `CadenceHint`, `DeliveryHint`, `ProactiveSignalSource` — not flagged in the original ticket;
  out of scope for this proposal (a future naming pass could reconsider `ProactiveSignalSource`
  once `ProactiveSignal` itself is renamed, but that's a new decision, not implied by this one).

## Decision needed

This is not a ticket to implement — it is the input BH-953's AC asks for ("naming review with
Marwan + Nano — pick concrete new names"). Once Marwan and Nano review this table (approve as
proposed, or counter-propose any row), the decision becomes:

1. Rename applied across `brightbot/routines/`, `brightbot/evals/routines/`, all tests (BH-953 AC item 2).
2. Spec text in `brightroutines-intent-loop.md` synced (37 references, mechanical) (AC item 3).
3. BH-947's e2e chain test updated for the one cross-repo reference (AC item 4).
4. Migration notes for any consumer pinned to old names (AC item 5) — verified above: none exist
   outside brightbot + the one e2e file, so this should be a short note, not a deprecation shim.

## Related

- **Parent ticket**: BH-953
- **Precedent**: `SchedulabilityJudge` → `RoutineJudge` rename, commit `6dd482c6` (BH-884 self-review)
- **Spec**: `docs/specs/brightroutines-intent-loop.md` (needs the mechanical sync once approved)
