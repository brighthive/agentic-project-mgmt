# Year One: The Story

**One line:** Brighthive had a working product held together by individuals. A year later it
runs on written standards: specs before code, tickets under epics, tests and pipelines around
the code, releases on a cadence, and named customer pilots. The standards are measurable,
and the weak spots are named.

Numbers below come from [METRICS.md](METRICS.md). Dates marked ✓ are verified in git or Jira.
Items marked (notes) come from internal working notes and need a source check before external use.

## Before (October 2025)

| Area | State |
|---|---|
| Tests | `brightbot` 10 test files, `brighthive-platform-core` 3 |
| CI (continuous integration) | `brightbot` 1 workflow file, `platform-core` 3 |
| Commit standard | 12.3% of commits in `type(scope): description` form |
| Written standards | No CLAUDE.md or AGENTS.md contract files, no specs, no ADRs (architecture decision records) |
| Planning | An idea backlog (Jira project BPP: 69 ideas created before the year, 2023-12 → 2025-10). No epics tied to delivery |
| Releases | `brightbot` had no published GitHub releases |
| End-to-end suite | None |

## Chapters

1. **Oct–Dec 2025, learn the stack.** First commits: `brightbot` 2025-10-23 ✓, `platform-core` 2025-11-17 ✓, `webapp` 2025-11-17 ✓. Software development lifecycle (SDLC) groundwork in the sprint reports: Poetry to uv, pre-commit hooks, branch protection, CI workflows.
2. **January 2026, an operating system for the team.** Jira BH epics created 2026-01-11 to 13 ✓. Architecture-context repo created 2026-01-19 ✓. This repo created 2026-01-22 ✓. Sprints 1 to 7 ran Jan 13 to Mar 24.
3. **Q1 2026, productization.** 65% of the original roadmap delivered, 6 of 10 epics at 80% or more, and two product surfaces the roadmap did not include (BrightStudio, agent sharing). Source: `jira/sprint/BOARD_REPORT_OCT_2025_MAY_2026.md`.
4. **Q2 2026, breadth and depth.** Bedrock/AgentCore migration, Synapse bring-your-own-warehouse, Okta single sign-on, the Longaeva pilot, BrightSignals and BrightRoutines (notes).
5. **June 2026, the safety net.** The cross-repo end-to-end suite starts 2026-06-18 ✓ (571 tests, 8 surfaces, 3 environments today).
6. **July 2026, one release label.** "Brighthive 3.0" decided 2026-07-21 ✓ (`docs/RELEASE_MANIFEST.json`).
7. **August 2026, weekly cadence.** Sprint 16 is the first weekly release cut ✓.
8. **September–October 2026, from features to trust.** Authorization and governance epic BH-1464, projects as the join point of every feature, and the platform north star of 2026-10-20 (notes).

## After (October 2026)

| Area | State |
|---|---|
| Tests | `brightbot` 413 test files, `platform-core` 237 |
| CI | `brightbot` 7 workflow files, `platform-core` 12 |
| Commit standard | 72.8% of commits conventional |
| Written standards | 35 CLAUDE.md or AGENTS.md files across 8 repos, 123 specs in this repo, ADRs in five repos |
| Planning | 1,507 Jira issues under 48 epics. 88.6% of work items sit under an epic, 97.7% have a description |
| Releases | 378 releases published org-wide in the year after, against 145 before |
| End-to-end suite | 571 tests across 8 surfaces |

## Customers and pilots (notes, verify before external use)

| Customer | State |
|---|---|
| Loop Capital | Proactive pipeline monitoring demo, then an AI-governance request on 2026-10-16 that became a co-build proposal |
| Nestlé | User acceptance testing (UAT) environment, Azure deployment path |
| Virginia Workforce Data Trust | Tier 1 client, 14 state agencies |
| Longaeva | Pilot with 14 defined acceptance cases |

Revenue, contract values and headcount are not in any system we can query. See [business.md](business.md).

## What the story must also say

- The team changed between the two years, so these are before/after comparisons, not proof of cause.
- Work concentrated on one person: Kuri authored 67.5% of merged pull requests (PRs) in the year after, against a top-author share of 25.4% the year before.
- Jira lags delivery. See [JIRA.md](JIRA.md).
- Several controls are built but not yet enforced in production (log-only authorization checks). See [DATA-QUALITY.md](DATA-QUALITY.md).
