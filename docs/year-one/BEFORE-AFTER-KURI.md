# Before Kuri, After Kuri: What the Codebase Can Do

Each core repo is measured at the last commit on `develop` before 2025-10-23 and at `origin/develop` now. Source: `scripts/yearone/collect_codebase_reach.py` → `data/codebase_reach.json`. Counts match code patterns, so treat them as approximate.

## Size and tests

| Repo | Source KB | Code files | Test files | Markdown docs |
|---|---|---|---|---|
| brightbot | 2,047 → 10,181 | 161 → 1,093 | 10 → 413 | 20 → 102 |
| brighthive-platform-core | 6,626 → 16,018 | 193 → 770 | 3 → 237 | 2 → 78 |
| brighthive-webapp | 4,963 → 10,668 | 1,078 → 1,828 | 37 → 220 | 5 → 33 |

## Monitoring, observability and architecture signals

Files containing the pattern, before → after.

| Group | Signal | brightbot | brighthive-platform-core | brighthive-webapp |
|---|---|---|---|---|
| Observability | Tracing and evals | 1 → 46 | 0 → 1 | 0 → 1 |
| Observability | Structured logging | 69 → 329 | 0 → 16 | 0 → 0 |
| Observability | Cost and token metering | 0 → 6 | 0 → 0 | 0 → 0 |
| Observability | Health endpoints | 1 → 12 | 3 → 10 | 0 → 14 |
| Observability | Alarms and alerts | 0 → 9 | 0 → 3 | 0 → 0 |
| Observability | Audit trail | 0 → 9 | 0 → 0 | 0 → 1 |
| Architecture | Registries (adapter lookups) | 0 → 17 | 0 → 8 | 0 → 0 |
| Architecture | Feature flags | 0 → 46 | 0 → 2 | 0 → 22 |
| Architecture | Authorization checks | 0 → 23 | 12 → 107 | 0 → 5 |
| Architecture | Agent graphs and tools | 18 → 155 | 0 → 1 | 0 → 0 |
| Architecture | Protocol classes | 1 → 32 | 0 → 2 | 0 → 0 |

## Kuri-led modules added since the cutoff

A module is a directory that did not exist before the cutoff. Kuri share is the share of commits touching it on `develop`, matched by author name or email. Listed: 23 of 47 new modules, those with a Kuri share of 50% or more (the same rule as [MILESTONES.md](MILESTONES.md)). The other 24 were built mostly by others and are in `data/codebase_reach.json`. Some directories are moves, not new capability.

| Repo | Module | Commits | Kuri share |
|---|---|---|---|
| brightbot | brightbot/audit | 11 | 100.0% |
| brightbot | brightbot/docs | 1 | 100.0% |
| brightbot | brightbot/evals | 12 | 50.0% |
| brightbot | brightbot/fleet_health | 15 | 100.0% |
| brightbot | brightbot/integrations | 2 | 100.0% |
| brightbot | brightbot/mcp | 77 | 87.0% |
| brightbot | brightbot/pipelines | 7 | 100.0% |
| brightbot | brightbot/routines | 6 | 100.0% |
| brightbot | brightbot/scheduled_agents | 5 | 80.0% |
| brightbot | brightbot/workspace_context | 2 | 50.0% |
| brightbot | brightbot/agents/airbyte_custom_agent | 7 | 57.1% |
| brightbot | brightbot/agents/summary_agent | 1 | 100.0% |
| brightbot | brightbot/agents/workflow_agent | 8 | 62.5% |
| brightbot | brightbot/skills/system/project-observation-cycle | 1 | 100.0% |
| brightbot | brightbot/skills/system/ssis-diagnostics | 2 | 50.0% |
| brightbot | brightbot/skills/system/ssrs-diagnostics | 2 | 50.0% |
| brightbot | brightbot/skills/system/storage-optimization | 3 | 66.7% |
| brighthive-platform-core | src/notifications | 5 | 80.0% |
| brighthive-platform-core | lambdas/notification_dispatcher | 11 | 81.8% |
| brighthive-platform-core | lambdas/scheduled_agent_dispatcher | 18 | 50.0% |
| brighthive-webapp | src/Analytics | 20 | 95.0% |
| brighthive-webapp | src/Context | 41 | 97.6% |
| brighthive-webapp | src/i18n | 25 | 60.0% |

## Limits

- Pattern counts can miss renamed code and count tests and docs that mention a term.
- Left out as unreliable: GraphQL field counts (the schema moved from a TypeScript file to a `.graphql` file, so the two counts are not comparable), "port or adapter classes" (the code names them differently) and "error and product analytics" (a keyword count).
- A module's Kuri share counts commits, not value.
- This compares two snapshots. It does not prove the change was caused by any one person.
