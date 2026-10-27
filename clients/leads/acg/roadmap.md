---
name: "ACG roadmap"
slug: "acg"
last_reviewed: "2026-10-27"
---

# ACG roadmap

Thin slices, each ending in something ACG can see. Lead record: [overview](overview.md). Acceptance criteria: [pilot spec](../../../docs/specs/acg-vendor-data-pilot.md). Nothing below is committed with ACG or in Jira yet.

## Slice 0: settle the facts

| Done when | Owner |
|---|---|
| The 14 July demo outcome is recorded | Suzanne El-Moursi |
| ACG's rule on where data may live is known (their Azure tenant, or AWS allowed) | John Sutton |
| One vendor feed is chosen, with sample files and an ACG owner | John Sutton |
| ACG's baseline is written down: hours chasing bad records, how late feeds are | Diane's team |
| The proposal is corrected on the points in the [overview](overview.md#what-the-proposal-promises-and-what-exists-today) | Kuri |

## Slice 1: one vendor feed, end to end, on staging

Land the chosen feed, profile it, run expectations, flag drift, and post a morning exception list to Slack. Covers the first four scenarios in the spec. Blocked until Slice 0 names the feed. If the feed has no Airbyte connector, build one with the custom-connector agent and record how long it took.

## Slice 2: SSIS diagnosis on ACG's own packages

Run the existing SSIS diagnosis skill on sample ACG packages. Needs the packages and run history from ACG, under their data-handling rules. Covers the fifth scenario.

## Slice 3: a fix as a reviewed pull request

Take one real failure from Slice 1 and let the engineering agent open a pull request against ACG's repository or a sandbox copy. Covers the sixth scenario.

## Slice 4: ACG's own environment

Only if Slice 0 says data must stay in ACG's Azure tenant. This reuses the Nestlé Azure plan: epic [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640) and the [cloud-agnostic adapters spec](../../../docs/specs/cloud-agnostic-adapters.md). Do not start it for ACG alone; sequence it behind Nestlé.

## Not planned (decide with ACG first)

| Item | Why |
|---|---|
| Microsoft Teams delivery | Not built; only a read tool exists today |
| Azure Data Factory support | No code; ACG may still be evaluating it |
| Per-vendor connector library for APX, eVestment, FactSet, Morningstar, Bloomberg | Unverified; Slice 1 tests one |

## Jira

No ACG tickets exist. Proposed: one epic, with Slices 0 to 3 as tickets and Slice 4 linked to [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640).
