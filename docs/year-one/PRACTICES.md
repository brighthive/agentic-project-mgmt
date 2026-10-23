# Engineering Practices: What We Introduced and What It Bought

Each practice has an **adoption** metric (did we do it?) and a **value** metric (what did it
buy?). A practice is claimed as value only when its value metric improved, or held while
volume grew. Otherwise it reads "adopted, value not shown yet".

Source for commit numbers: `scripts/yearone/collect_commit_practices.py` → `data/commit_practices.json`
(non-merge commits on `origin/develop` of `brightbot`, `brighthive-platform-core`, `brighthive-webapp`).
Pull-request (PR) hygiene and review numbers come from `collect_practices.py` → `data/practices.json`, which is still being collected (GitHub rate limit), so review coverage is not reported yet.

## Ledger

| Practice introduced | Adoption | Value metric | Reading |
|---|---|---|---|
| Conventional commits and PR titles | Conventional subjects 12.3% → 72.8% | Readable history, release notes per sprint | ✅ adopted |
| Ticket key in commits and PRs | Commits with a key 28.6% → 41.0% | Work traceable to a ticket | ⚠️ 59% still untraced |
| Tests | `brightbot` 10 → 413 test files, `platform-core` 3 → 237 | Revert rate 0.8% → 0.8% while commits grew 37% (1,423 → 1,950) | ✅ quality held at higher volume |
| Hotfix discipline | n/a | Hotfix commits 0.4% → 1.2% of commits | ⚠️ went up, investigate before claiming |
| CI (continuous integration) and gates | Workflow files `brightbot` 1 → 7, `platform-core` 3 → 12 | CI success rate (year after only) | ⚠️ see [CICD-AND-E2E.md](CICD-AND-E2E.md) |
| End-to-end (e2e) and health suite | 571 tests, 8 surfaces, 3 environments | Regressions caught before customers | ✍️ not measured yet |
| Spec-driven development | 126 specs, 4 ADRs (architecture decision records) here, 11 in `brightagent-v3` | Canceled share of work items 4%; roadmap delivered vs planned | ⚠️ no before for rework |
| Epics and the ticket template | 88.6% of work items under an epic | Q1 roadmap: 65% delivered, 6 of 10 epics at 80%+ | ✅ delivery measured against a plan |
| Sprint cadence and release automation | 16 sprints, weekly cuts from Sprint 16 | Release notes produced per cut | ✅ |
| Docs and agent contract files | 0 → 35 CLAUDE.md or AGENTS.md files across 8 repos | Commits in a new contributor's first 30 days, median 10 → 4 | ❌ no evidence of value |
| Shared work | Top author's share of merged PRs 25.4% → 67.5% | Work not stuck on one person | ❌ got worse |

## Commit profile (three core repos)

| | Year before | Year after |
|---|---|---|
| Commits | 1,423 | 1,950 |
| Conventional | 12.3% | 72.8% |
| With a ticket key | 28.6% | 41.0% |
| Reverts | 0.8% | 0.8% |
| Hotfix mentions | 0.4% | 1.2% |
| `fix` share of typed commits | 30.9% | 39.6% |

The `fix` share rising may reflect better labeling and not more bugs. We cannot separate the two with this data.

## Contributor ramp-up

Commits in the first 30 days, for contributors with 10+ commits whose first commit fell in the window.

| | New contributors | Median commits in first 30 days |
|---|---|---|
| Year before | 13 | 10 |
| Year after | 12 | 4 |

Authors are matched by email, so one person with two emails counts twice. The after number does
not show faster onboarding, so we do not claim it.

## Caveats

- The team changed between the two years. These are before/after comparisons, not proof of cause.
- Agent-assisted work makes PR and commit counts weaker evidence of effort, which is why volume is not a headline.
- Test and docs counts match on file-name patterns and are approximate.
