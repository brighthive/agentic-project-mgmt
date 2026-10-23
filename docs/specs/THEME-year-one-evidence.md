---
title: "Year-one evidence: prove the foundations changed"
epic: "BH-170"
owner: "drchinca"
status: "Draft"
created: "2026-10-22"
supersedes: []
---

# Year-one evidence: prove the foundations changed

> Delegation unit, not a design document. Cap: 150 lines.

## The goal

For the annual review, anyone can run one command and get a short, defensible before/after
case that Brighthive's engineering and project-management foundations changed in year one,
and that the practices we introduced added value: how we commit, review, release, specify,
plan, document, share work, test and ship. Every
number traces to a script and a raw data file. Weak spots appear in the report on purpose, so
nobody can poke a hole in it that we did not already show.

## Why now

The first pass collected seven datasets and rendered every number it had. The result was a
dump, not a case: volume metrics anyone can discount (agent-assisted PR counts), numbers that
are not comparable across the two years (CI runs were pruned, Jira starts in 2026), and a
status count that was simply wrong (Canceled counted as Done, Jira status lagging shipped
work). Rule going forward: **a number earns a place only if it proves a pillar claim.**

## The practice ledger: what we introduced, and what it bought

Each row is one practice we introduced. **Adoption** says we did it. **Value** says what it
bought. A practice is claimed as value only when its value metric moved the right way, or held
while volume grew. Otherwise the row says "adopted, value not shown yet".

First readings (three core repos, non-merge commits on `develop`, year before → year after):

| Practice introduced | Adoption metric | Value it should buy, and the metric | Reading now |
|---|---|---|---|
| Conventional commits and PR titles | Conventional subjects 12.3% → 72.8% | Readable history; release notes generated per sprint (count of sprint release artifacts) | ✅ adopted, artifacts to count |
| Ticket key in commits and PRs | Commits with a key 28.6% → 41.0% | Work traceable to a ticket (the same %) | ⚠️ 59% still untraced; "PRs ahead of Jira" is documented in the sprint reports |
| Tests | Test files: brightbot 10 → 413, platform-core 3 → 237 | Change without breaking: revert rate 0.8% → 0.8% while commits grew 37% (1,423 → 1,950) | ✅ quality held at higher volume |
| Hotfix discipline | n/a | Hotfix commits as share of commits 0.4% → 1.2% | ⚠️ went up; investigate before claiming |
| CI and gates | Workflow files: brightbot 1 → 7, platform-core 3 → 12 | Failures caught before merge (CI success, after only) | ⚠️ webapp success under 50%; gate gaps BH-1140 to BH-1145 |
| End-to-end and health suite | 571 tests, 8 surfaces, 3 environments, since 2026-06-18 | Regressions caught before customers: failing health or smoke runs that led to a fix | ✍️ not measured yet |
| Spec-driven development | 123 specs, 3 ADRs (architecture decision records) here, 10 more in brightagent-v3 | Less rework: canceled share of work items (4%); roadmap delivered vs planned | ⚠️ partly: no before for rework |
| Epics, parent-epic rule, ticket template | 88.6% of work items under an epic | Delivery measured against a plan for the first time: Q1 roadmap 65% delivered, 6 of 10 epics at 80%+ | ✅ (source: `BOARD_REPORT_OCT_2025_MAY_2026.md`) |
| Sprint cadence and release automation | 16 sprints, weekly cut from Sprint 16 | Predictable releases: sprint release notes per cut | ✅ |
| Docs and agent contract files | CLAUDE.md or AGENTS.md files: 0 → 35 | Faster start for new people: commits in a new contributor's first 30 days, median 10 → 4 | ❌ no evidence of value; do not claim |
| AI-driven engineering (project management, business analysis, QA and review run by an agentic framework) | Agent skills, Claude PR review repos, specs with Gherkin scenarios, sprint records: `collect_ai_engineering.py` | Role work left as openable artifacts; see `docs/year-one/AI-DRIVEN-ENGINEERING.md` | ⚠️ partly: AI share of code and review quality are not measurable yet; reviewer roster lives outside the repos |
| Shared work | Contributors with 10+ PRs; top author share of PRs 25.4% → 67.5% | Work not stuck on one person | ❌ got worse; report as the next step |

Dropped from the headline (kept as raw data): lines changed, org-wide PR counts, PRs authored by
Kuri, hours-to-merge, workflow run counts. They are volume, not value.

Caveat stated in the report: the team changed between the two years, so every value metric is
a before/after comparison, not proof of cause.

## What to build

1. `scripts/yearone/` → a small package with one typed `Metric` record: `id`, `pillar`, `claim`,
   `definition`, `source`, `before`, `after`, `comparability` (`BOTH` | `AFTER_ONLY` | `MANUAL`),
   `confidence` (`HIGH` | `MEDIUM` | `LOW` plus the reason), `good_direction` (`UP` | `DOWN`).
2. `registry` — one function per metric, each reading only the raw JSON files, returning a `Metric`.
3. `build` — runs the registry, writes `results.json`, renders `YEAR_ONE.md` one section per pillar.
4. `check` — fails the build when an invariant below breaks.
5. Replace the commit and PR-title collector with local `git log` on the integration branches
   (no rate limit); keep GitHub only for review coverage via search counts.
6. `business.yaml` — nullable fields for revenue, customers, pilots, headcount; the report prints
   `TODO` for any empty field.

## Invariants

- Every rendered number comes from a registry metric. No number is typed into the report.
- Adoption and value are separate columns. A row with no value metric reads "adopted, value not shown yet".
- Every metric states its source command and the date its raw file was generated.
- A `LOW` confidence metric never appears in the headline table.
- `AFTER_ONLY` and `MANUAL` metrics say why, in the row.
- Canceled is never counted as Done. Jira Done is shown next to the merged-code range, not replaced by it.
- Windows are fixed: before = 2024-10-23 to 2025-10-22, after = 2025-10-23 to 2026-10-22.
- The headline table has at most 12 rows. A metric where after is worse than before is flagged ⚠️, not hidden.

## Done when

- [ ] `python -m yearone build` regenerates `results.json` and `YEAR_ONE.md` from the raw files
- [ ] `python -m yearone check` passes, and fails when a metric loses its source or definition
- [ ] Each practice row has an adoption metric, a value metric and a verdict: ✅ proven, ⚠️ partly, ❌ not shown, ✍️ needs your input
- [ ] At least one test builds the report from the real captured raw files (no hand-made fixture)
- [ ] The PR description shows the headline table and links `YEAR_ONE.md`

## Don't do

- Don't print a metric just because we can collect it.
- Don't transition any Jira ticket from this work. Closing shipped tickets is a separate, reviewed step.
- Don't claim business outcomes the data cannot show. Those come from `business.yaml` only.

## Where it lives

| Repo | What changes |
|---|---|
| `agentic-project-mgmt` | `scripts/yearone/` package, `docs/year-one/` data and report, this spec |

**Tickets:** under BH-170, `issueType: Task`, to be created once the pillar table is confirmed.
