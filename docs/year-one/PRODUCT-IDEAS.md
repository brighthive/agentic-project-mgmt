# Product Ideas Brought to the Platform

Each idea is traced to the roadmap epic that first wrote it down, the specs that defined it, the epics that built it, and the code modules it lives in. Source: `scripts/yearone/product_ideas.json` (the idea list, curated) and `collect_product_ideas.py` → `data/product_ideas.json`.

Spec authorship and commits show who wrote and built each idea. They do not show whose head it came from. Add that origin story where it applies.

| Idea | Written down as (Jira epic, date, creator) | Specs | First spec | Commits in listed epics, Kuri share | Modules, Kuri share |
|---|---|---|---|---|---|
| BrightSignals | BH-111 (2026-01-11, Kuri Chinca), BH-117 (2026-01-11, Kuri Chinca) | 5 (4 by Kuri) | 2026-07-12 | 138 at 58.7% | `src/notifications` 80.0%; `lambdas/notification_dispatcher` 81.8%; `src/Notifications` 38.5% |
| BrightRoutines | BH-111 (2026-01-11, Kuri Chinca) | 14 (14 by Kuri) | 2026-06-30 | 179 at 97.2% | `brightbot/routines` 100.0%; `brightbot/scheduled_agents` 80.0%; `lambdas/scheduled_agent_dispatcher` 50.0%; `src/Schedules` 45.0% |
| Fleet health and self-healing | BH-111 (2026-01-11, Kuri Chinca), BH-113 (2026-01-11, Kuri Chinca) | 6 (6 by Kuri) | 2026-06-16 | 174 at 98.3% | `brightbot/fleet_health` 100.0% |
| Project as the glue | BH-116 (2026-01-11, Kuri Chinca), BH-114 (2026-01-11, Kuri Chinca) | 12 (12 by Kuri) | 2026-07-29 | 91 at 95.6% | n/a |
| Multi-warehouse, multi-database | BH-115 (2026-01-11, Kuri Chinca) | 11 (11 by Kuri) | 2026-04-06 | 22 at 100.0% | n/a |
| Engine and framework agnosticism | BH-115 (2026-01-11, Kuri Chinca), BH-110 (2026-01-11, Kuri Chinca) | 6 (6 by Kuri) | 2026-06-24 | 37 at 100.0% | `brightbot/integrations` 100.0% |
| Orchestrated ELT with agents | BH-119 (2026-01-11, Kuri Chinca), BH-111 (2026-01-11, Kuri Chinca) | 10 (10 by Kuri) | 2026-07-16 | 123 at 93.5% | `brightbot/pipelines` 100.0% |

## Detail

### BrightSignals

Proactive notifications across the platform, one shared signal catalog for Slack and the webapp.

- `proactive-pipeline-ingestion-monitoring.md` (first added 2026-07-12)
- `chat-session-notifications.md` (first added 2026-07-15)
- `hive-health-landing-indicator.md` (first added 2026-07-19)
- `honest-observe-surface.md` (first added 2026-08-02)
- `THEME-honest-surfaces.md` (first added 2026-08-19)

Epics: BH-409 BrightSignals — proactive Slack notifications across the pla, BH-1131 On-Demand Alerts — agent-authored notification rules on the 

### BrightRoutines

The agent notices repeated work and proposes a scheduled, auditable routine.

- `brightroutines-execute-workflow-schedule.md` (first added 2026-06-30)
- `brightroutines-intent-loop.md` (first added 2026-06-30)
- `brightroutines-your-routines-persistence.md` (first added 2026-07-04)
- `brightroutines-ai-authored-workflowspec.md` (first added 2026-07-05)
- `slack-routine-suggestion-scheduling.md` (first added 2026-07-07)
- `brightroutines-detector-fanout-fairness.md` (first added 2026-07-12)
- `brightroutines-naming-proposal.md` (first added 2026-07-12)
- `brightroutines-online-judge-eval-circuit-breaker.md` (first added 2026-07-12)
- `brightroutines-email-delivery.md` (first added 2026-07-13)
- `brightroutine-approve-schedule.md` (first added 2026-07-29)
- `brightroutines-delivery-target-and-provenance.md` (first added 2026-08-10)
- `THEME-brightroutines-closeout.md` (first added 2026-08-19)
- `THEME-routine-authoring.md` (first added 2026-08-19)
- `routine-permissions-single-decision.md` (first added 2026-10-06)

Epics: BH-876 BrightRoutines — proactive schedule detection and workflow a, BH-1463 BrightRoutines next-phase — team-targeted delivery & AI-auth

### Fleet health and self-healing

Watch every pipeline and warehouse as a fleet, and fix failures through reviewed pull requests.

- `self-healing-pipelines.md` (first added 2026-06-16)
- `pipeline-self-healing-fleet.md` (first added 2026-07-29)
- `sqlserver-health-watch.md` (first added 2026-07-29)
- `fleet-health-digest-push.md` (first added 2026-08-01)
- `THEME-fleet-self-healing.md` (first added 2026-08-19)
- `pipeline-connectivity-watchdog.md` (first added 2026-08-19)

Epics: BH-1036 Monitoring Agents — proactive pipeline discovery & health (d

### Project as the glue

A Project is the join point of every platform capability, not a container.

- `project-files-dbt-github-bridge.md` (first added 2026-07-29)
- `project-files-pipeline-artifact-intake.md` (first added 2026-07-29)
- `project-activate-sync-golden-nuggets.md` (first added 2026-08-01)
- `project-engine-repo-binding.md` (first added 2026-08-01)
- `project-engine-run-sync.md` (first added 2026-08-01)
- `project-governance-observability-convergence.md` (first added 2026-08-01)
- `THEME-project-activation.md` (first added 2026-08-19)
- `PROJECT_V2_TRACKER.md` (first added 2026-09-22)
- `projects-2.0-design-spec.md` (first added 2026-09-22)
- `projects-2.0-technical-requirements.md` (first added 2026-09-22)
- `THEME-project-proactive-lifecycle.md` (first added 2026-10-20)
- `projects-at-scale.md` (first added 2026-10-20)

Epics: BH-1255 Scheduled, Versioned, Lineage-Aware Pipeline Runs — configur

### Multi-warehouse, multi-database

Warehouse, database and table identity that works the same across Snowflake, Redshift, Synapse and on-prem SQL Server.

- `azure-synapse-full-integration.md` (first added 2026-04-06)
- `aws-azure-network-connectivity.md` (first added 2026-04-14)
- `snowflake-full-integration.md` (first added 2026-06-01)
- `byow-end-to-end-omd-native.md` (first added 2026-06-15)
- `table-parity-verb.md` (first added 2026-08-02)
- `table-parity-cross-warehouse-database.md` (first added 2026-08-06)
- `default-warehouse-ui-surfacing.md` (first added 2026-08-07)
- `on-prem-sql-server-warehouse.md` (first added 2026-08-12)
- `loopcapital-onprem-read-write-sandbox.md` (first added 2026-08-13)
- `THEME-catalog-and-identity.md` (first added 2026-08-19)
- `THEME-cross-engine-correctness.md` (first added 2026-08-19)

Epics: BH-1370 Warehouse → Database → Table hierarchical identity

### Engine and framework agnosticism

Pipelines, lineage and semantic views defined once, independent of dbt, Databricks, SSIS or any single engine.

- `open-semantic-view.md` (first added 2026-06-24)
- `lineage-aware-data-quality.md` (first added 2026-07-12)
- `pipeline-artifact-parser-registry.md` (first added 2026-07-29)
- `engineering-agent-warehouse-agnostic.md` (first added 2026-08-01)
- `lineage-adapter-sql-server.md` (first added 2026-08-01)
- `THEME-spec-driven-pipelines.md` (first added 2026-09-22)

Epics: BH-1061 Lineage-Aware Data Quality — glue dbt/Databricks' own lineag

### Orchestrated ELT with agents

Up- and downstream data pipelines run, versioned and repaired by agents, including on the customer's own filesystem.

- `ssis-ssrs-proactive-pipeline-source.md` (first added 2026-07-16)
- `pipeline-run-lifecycle.md` (first added 2026-07-29)
- `ssis-ssrs-to-dbt-regeneration.md` (first added 2026-07-29)
- `pipeline-engine-full-lifecycle-control.md` (first added 2026-08-01)
- `project-engine-run-sync.md` (first added 2026-08-01)
- `remediation-pr-engine-run-logs.md` (first added 2026-08-01)
- `autonomous-dbt-project-lifecycle.md` (first added 2026-08-12)
- `on-prem-engineering-runner.md` (first added 2026-08-13)
- `THEME-legacy-file-intake.md` (first added 2026-08-19)
- `THEME-onprem-engineering.md` (first added 2026-08-19)

Epics: BH-1255 Scheduled, Versioned, Lineage-Aware Pipeline Runs — configur, BH-1421 On-Prem Engineering Runner — filesystem-resident dbt + legac, BH-860 Skills Extension Framework for deep_agent — Low-Effort Agent

## Limits

- Specs are matched by file name in `docs/specs`; a spec can serve more than one idea.
- Epic commits are matched by ticket key in the commit message.
- Commits are evidence of merged work, not proof an idea is finished.
