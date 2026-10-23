# CI/CD, End-to-End Suite, and Webapp

CI/CD means continuous integration (CI) and delivery. End-to-end is shortened to e2e. Source: `scripts/yearone/collect_cicd.py` →
`data/cicd.json`, `collect_suites.py` → `data/suites.json`, `collect_repo_structure.py` → `data/repo_structure.json`.

## What we can and cannot measure

GitHub pruned workflow runs from before 2025-10-23, so run counts, success rates and durations
exist for the year after only. For the year before, the evidence is workflow files in git.
GitHub also caps a filtered query at 1,000 runs, so the collector splits date ranges until each chunk is under the cap.

## Pipelines (workflow files)

| Repo | Oct 2025 | Oct 2026 |
|---|---|---|
| `brightbot` | 1 | 7 |
| `brighthive-platform-core` | 3 | 12 |
| `brighthive-webapp` | 1 | 3 |
| `brighthive-e2e` | did not exist | 3 |

## CI health, year after

| Repo | Completed runs | Success of decided | Median minutes |
|---|---|---|---|
| `brightbot` | 7,037 | 90.4% | 0.2 |
| `brighthive-platform-core` | 6,500 | 85.5% | 1.1 |
| `brightbot-slack-server` | 924 | 70.2% | 2.5 |
| `agentic-project-mgmt` | 837 | 69.8% | 0.9 |
| `brighthive-e2e` | 343 | 67.9% | 0.5 |
| `brightagent-v3` | 2,717 | 66.0% | 0.4 |
| `brighthive-webapp` | 1,922 | 46.7% | 3.1 |

Success is success divided by (success plus failure). Cancelled and skipped runs are excluded.

⚠️ Webapp success is under half. Deploy-named workflows in `brightbot` (1 of 50) and
`platform-core` (1 of 5) mostly did not succeed. "Deploy-named" means the workflow name contains
deploy, release or promote, so this may include validation jobs. Causes are not investigated yet.

## End-to-end suite

| Metric | Value |
|---|---|
| First commit | 2026-06-18 |
| Test functions | 571 |
| Feature files / surface modules | 108 / 8 |
| Surfaces | Auth, GraphQL, custom routes, agents, semantic views, MCP (Model Context Protocol), Neo4j integrity, webapp |
| Environments | dev, staging, production |
| Workflows | health-check, prod-smoke, tracker |

Not measured yet: failing health or smoke runs that led to a fix. That is the metric that would
show the suite catching regressions before customers.

## Webapp

199 test files at the integration branch (37 → 220 by the structure collector's file-name pattern, which counts differently).
Workflows: `deploy.yml`, `catalog-check.yml`, `claude-review.yml`.

## Known gate gaps (tracked)

The July 2026 release manifest records that none of the five app repos had a real
staging-to-main promotion gate (unit, integration, e2e, environment-variable health). Tickets:
BH-1140 (`brightbot`), BH-1141 (`platform-core`), BH-1142 (webapp, deploy workflow test job ran zero tests),
BH-1143 (`brightbot-slack-server`), BH-1144 (`brighthive-admin`), BH-1145 (e2e gate not wired to any repo).
