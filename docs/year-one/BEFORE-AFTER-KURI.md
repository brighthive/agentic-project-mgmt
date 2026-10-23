# Before Kuri, After Kuri: What the Codebase Can Do

Each core repo is measured at the last commit on `develop` before 2025-10-23 and at `origin/develop` now. Source: `scripts/yearone/collect_codebase_reach.py` → `data/codebase_reach.json`. Counts match code patterns, so treat them as approximate.

## Size and tests

| Repo | Source KB | Code files | Test files | Markdown docs |
|---|---|---|---|---|
| brightbot | 2,047 → 10,181 | 161 → 1,093 | 10 → 413 | 20 → 102 |
| brighthive-platform-core | 6,626 → 16,018 | 193 → 770 | 3 → 237 | 2 → 78 |
| brighthive-webapp | 4,963 → 10,668 | 1,078 → 1,828 | 37 → 220 | 5 → 33 |

## Feature reach: the GraphQL API (`brighthive-platform-core`)

| Metric | Before | After |
|---|---|---|
| GraphQL types | 142 | 285 |
| Query fields | 12 | 60 |
| Mutation fields | 82 | 207 |

The schema moved from `src/graphql/schema/typedefs.ts` to `src/graphql/schema/schema.graphql`. Counts are line-pattern estimates, and the newer file may include generated types, so read the growth as a direction, not an exact multiple.

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
| Observability | Error and product analytics | 5 → 2 | 1 → 2 | 4 → 7 |
| Architecture | Registries (adapter lookups) | 0 → 17 | 0 → 8 | 0 → 0 |
| Architecture | Feature flags | 0 → 46 | 0 → 2 | 0 → 22 |
| Architecture | Authorization checks | 0 → 23 | 12 → 107 | 0 → 5 |
| Architecture | Agent graphs and tools | 18 → 155 | 0 → 1 | 0 → 0 |
| Architecture | Protocol classes | 1 → 32 | 0 → 2 | 0 → 0 |
| Architecture | Port or adapter classes | 0 → 0 | 0 → 4 | 0 → 0 |

## Modules added since the cutoff

A module is a directory that did not exist before the cutoff. Kuri share is the share of commits touching it on `develop`, matched by author name or email. Some directories are moves, not new capability.

| Repo | Module | Commits | Kuri share |
|---|---|---|---|
| brightbot | brightbot/agent_tools | 4 | 0.0% |
| brightbot | brightbot/audit | 11 | 100.0% |
| brightbot | brightbot/backends | 21 | 9.5% |
| brightbot | brightbot/docs | 1 | 100.0% |
| brightbot | brightbot/evals | 12 | 50.0% |
| brightbot | brightbot/fleet_health | 15 | 100.0% |
| brightbot | brightbot/integrations | 2 | 100.0% |
| brightbot | brightbot/mcp | 77 | 87.0% |
| brightbot | brightbot/pipelines | 7 | 100.0% |
| brightbot | brightbot/routines | 6 | 100.0% |
| brightbot | brightbot/scheduled_agents | 5 | 80.0% |
| brightbot | brightbot/skills | 16 | 25.0% |
| brightbot | brightbot/validators | 2 | 0.0% |
| brightbot | brightbot/workspace_context | 2 | 50.0% |
| brightbot | brightbot/agents/airbyte_custom_agent | 7 | 57.1% |
| brightbot | brightbot/agents/brightagent_studio | 11 | 9.1% |
| brightbot | brightbot/agents/code_interpreter_agent | 6 | 16.7% |
| brightbot | brightbot/agents/pipeline_verifier_agent | 2 | 0.0% |
| brightbot | brightbot/agents/shared_middleware | 22 | 36.4% |
| brightbot | brightbot/agents/simple_messaging_agent | 12 | 33.3% |
| brightbot | brightbot/agents/slack_router_agent | 6 | 33.3% |
| brightbot | brightbot/agents/spec_author_agent | 1 | 0.0% |
| brightbot | brightbot/agents/summary_agent | 1 | 100.0% |
| brightbot | brightbot/agents/workflow_agent | 8 | 62.5% |
| brightbot | brightbot/skills/system/project-observation-cycle | 1 | 100.0% |
| brightbot | brightbot/skills/system/sql-server-diagnostics | 2 | 0.0% |
| brightbot | brightbot/skills/system/ssis-diagnostics | 2 | 50.0% |
| brightbot | brightbot/skills/system/ssrs-diagnostics | 2 | 50.0% |
| brightbot | brightbot/skills/system/storage-optimization | 3 | 66.7% |
| brightbot | brightbot/skills/system/xsd-nested-document | 4 | 0.0% |
| brightbot | brightbot/skills/system/xsd-table-schema | 9 | 0.0% |
| brighthive-platform-core | src/notifications | 5 | 80.0% |
| brighthive-platform-core | lambdas/notification_dispatcher | 11 | 81.8% |
| brighthive-platform-core | lambdas/scheduled_agent_dispatcher | 18 | 50.0% |
| brighthive-platform-core | lambdas/trigger_openmetdata_agents | 4 | 0.0% |
| brighthive-webapp | src/Analytics | 20 | 95.0% |
| brighthive-webapp | src/BrightAgent | 46 | 37.0% |
| brighthive-webapp | src/Context | 41 | 97.6% |
| brighthive-webapp | src/CustomAgents | 25 | 44.0% |
| brighthive-webapp | src/MyAgents | 4 | 25.0% |
| brighthive-webapp | src/Notifications | 26 | 38.5% |
| brighthive-webapp | src/Schedules | 20 | 45.0% |
| brighthive-webapp | src/SiteMap | 14 | 7.1% |
| brighthive-webapp | src/SystemAdmin | 5 | 40.0% |
| brighthive-webapp | src/apollo | 1 | 0.0% |
| brighthive-webapp | src/i18n | 25 | 60.0% |
| brighthive-webapp | src/shims | 1 | 0.0% |

## Limits

- Pattern counts can miss renamed code and count tests and docs that mention a term.
- A module's Kuri share counts commits, not value.
- This compares two snapshots. It does not prove the change was caused by any one person.
