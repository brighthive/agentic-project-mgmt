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
case that Brighthive's engineering and project-management foundations changed in year one:
how we commit, review, release, specify, plan, document, share work, test and ship. Every
number traces to a script and a raw data file. Weak spots appear in the report on purpose, so
nobody can poke a hole in it that we did not already show.

## Why now

The first pass collected seven datasets and rendered every number it had. The result was a
dump, not a case: volume metrics anyone can discount (agent-assisted PR counts), numbers that
are not comparable across the two years (CI runs were pruned, Jira starts in 2026), and a
status count that was simply wrong (Canceled counted as Done, Jira status lagging shipped
work). Rule going forward: **a number earns a place only if it proves a pillar claim.**

## The ten pillars (each is a claim, with 2 to 4 metrics at most)

| # | Pillar (the claim) | Metrics that prove it | Comparable before/after |
|---|---|---|---|
| 1 | We commit to a standard | % of merged-commit subjects in `type(scope): description` form; % carrying a ticket key | ✅ local git |
| 2 | PRs are reviewed and traceable | % of merged PRs approved by someone other than the author | ✅ GitHub search counts |
| 3 | We release on a cadence | Production releases per month; median days between them | ✅ GitHub releases |
| 4 | Specs come before code | Spec files, ADRs (architecture decision records), themes | ✅ local git (before = 0) |
| 5 | Planning has structure | % work items under an epic, with a description, assigned; Done vs. merged-code range | ⚠️ after only (BH starts 2026-01-11); before = BPP idea backlog |
| 6 | Everything is documented | Markdown docs; agent contract files (CLAUDE.md, AGENTS.md) | ✅ local git |
| 7 | Work is shared | Contributors with 10+ merged PRs; top author's share of merged PRs; share of Jira work items assigned to Kuri | ✅ GitHub, ⚠️ Jira after only |
| 8 | Software is designed to be tested | Test files per core repo; ports (Protocol classes) in the app core | ✅ local git |
| 9 | We ship through gates | CI workflow files; end-to-end suite size and surfaces; CI success rate | ✅ files, ⚠️ CI success after only |
| 10 | The business moved | Customers, pilots, revenue, headcount | ✍️ filled by hand in `business.yaml`, never guessed |

Dropped from the headline (kept as raw data): lines changed, org-wide PR counts, PRs authored
by Kuri, hours-to-merge, workflow run counts, per-repo markdown counts. They are volume or
noise and invite the wrong argument.

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
- Every metric states its source command and the date its raw file was generated.
- A `LOW` confidence metric never appears in the headline table.
- `AFTER_ONLY` and `MANUAL` metrics say why, in the row.
- Canceled is never counted as Done. Jira Done is shown next to the merged-code range, not replaced by it.
- Windows are fixed: before = 2024-10-23 to 2025-10-22, after = 2025-10-23 to 2026-10-22.
- The headline table has at most 12 rows. A metric where after is worse than before is flagged ⚠️, not hidden.

## Done when

- [ ] `python -m yearone build` regenerates `results.json` and `YEAR_ONE.md` from the raw files
- [ ] `python -m yearone check` passes, and fails when a metric loses its source or definition
- [ ] Each pillar has its metrics and a one-line verdict: ✅ proven, ⚠️ partly, ✍️ needs your input
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
