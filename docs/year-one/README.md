# Year One: Evidence That the Foundations Changed

Reproducible before/after record for the first-year review. Every number in these docs comes
from a script in `scripts/yearone/` and a JSON file in `docs/year-one/data/`.

**Windows:** before = 2024-10-23 → 2025-10-22, after = 2025-10-23 → 2026-10-22.
Kuri's first commit is 2025-10-23 (`brightbot`).

## Read in this order

| Doc | What it answers |
|---|---|
| [ACCOMPLISHMENTS.md](ACCOMPLISHMENTS.md) | The year in one reading: what shipped, what is still staging, and the caveats |
| [STORY.md](STORY.md) | The before/after storyline and the milestones, with verified dates |
| [PRACTICES.md](PRACTICES.md) | Which engineering practices we introduced, and what each one bought |
| [JIRA.md](JIRA.md) | How planning changed, and why Jira status understates shipped work |
| [CICD-AND-E2E.md](CICD-AND-E2E.md) | Pipelines (continuous integration and delivery, CI/CD), the end-to-end (e2e) suite, and the webapp |
| [AI-DRIVEN-ENGINEERING.md](AI-DRIVEN-ENGINEERING.md) | How one engineer covered project management, business analysis, QA and senior review with an agentic framework |
| [BEFORE-AFTER-KURI.md](BEFORE-AFTER-KURI.md) | What the codebase could do before and after: features, architecture, monitoring |
| [PRODUCT-IDEAS.md](PRODUCT-IDEAS.md) | The product ideas, traced to epics, specs and code |
| [MILESTONES.md](MILESTONES.md) | The epics Kuri led, in the order work began |
| [PRODUCTION-VALUE.md](PRODUCTION-VALUE.md) | User-facing changes verified in production, from the sprint release notes |
| [DATA-QUALITY.md](DATA-QUALITY.md) | What we corrected, what we cannot measure, and the weak spots |
| [business.md](business.md) | Revenue, customers, headcount. Filled in by hand, never guessed |
| [METRICS.md](METRICS.md) | Generated table of every metric (do not edit by hand) |

The spec behind this work is [`docs/specs/THEME-year-one-evidence.md`](../specs/THEME-year-one-evidence.md).

## Glossary

| Term | Meaning |
|---|---|
| BH, BPP, BL | Jira projects: Engineering, Platform Planning (idea backlog), Leadership |
| ADR | Architecture decision record |
| Core repos | `brightbot`, `brighthive-platform-core`, `brighthive-webapp` |
| Integration branch | `origin/develop`, where merged work lands before staging and production |
| Conventional commit | A subject in `type(scope): description` form |
| BrightRoutines, BrightSignals | Brighthive product features named in the story |

## Regenerate

```bash
python3 -I scripts/yearone/collect_github.py            # merged pull requests (PRs), releases, authors
python3 -I scripts/yearone/collect_commit_practices.py  # commit conventions, ramp-up (local git)
python3 -I scripts/yearone/collect_practices.py         # PR hygiene and review (GitHub, slow)
python3 -I scripts/yearone/collect_jira.py              # needs JIRA_USER, JIRA_TOKEN, JIRA_BASE
python3 -I scripts/yearone/collect_shipped_evidence.py  # Jira keys found in merged code
python3 -I scripts/yearone/collect_repo_structure.py    # tests, docs, specs, CI/CD files by month
python3 -I scripts/yearone/collect_cicd.py              # GitHub Actions (CI/CD) health
python3 -I scripts/yearone/collect_suites.py            # e2e suite and webapp inventory
python3 -I scripts/yearone/collect_codebase_reach.py    # before/after snapshots of the core repos
python3 -I scripts/yearone/collect_ai_engineering.py     # agent skills, Claude review, specs, sprint records
python3 -I scripts/yearone/collect_milestones.py        # epics tied to commits, Kuri share
python3 -I scripts/yearone/collect_product_ideas.py     # evidence per product idea
python3 -I scripts/yearone/collect_production_value.py  # release-note items vs production
python3 -I scripts/yearone/collect_shipped_prs.py       # release-note PRs vs production
python3 -I scripts/yearone/render_metrics.py            # writes METRICS.md
python3 -I scripts/yearone/render_reach_docs.py         # writes the four reach and value docs
```

The GitHub collectors need `gh` authenticated with read access to the `brighthive` org.
