# Moment-of-Truth Sweep — 3 Warehouse Engines (2026-07-31)

> One symbol set, three live staging warehouses, one pytest session each. This is
> the diagnosis pass: **read-only on the platform**, no platform code touched, no
> Jira filed. It exists to separate genuine engine-agnostic defects from
> per-workspace / test-harness noise, so the fixes that follow are prioritized by
> evidence, not guesswork.

## Legend

🟢 real platform defect (reproduces on the engine) · ⚠️ harness/config artifact
(the sweep's own gap, not the product) · ❄️ Snowflake · 🟦 SQL Server · 🔶 Redshift
· 🔁 shared across all 3 engines · ◧ subset of engines

## What ran

| Config | Engine | Workspace | Identity | Findings | Blocker | High |
|---|---|---|---|---|---|---|
| `oneten` | ❄️ Snowflake | OneTen "Longaeva PoC" (`4d7ffd13…`) | default `stage/login-user` | 48 | 7 | 28 |
| `loopcapital` | 🟦 SQL Server | "Scoop Capital" (`e3fc0917…`) on EC2 | `staging/loopcapital-demo/login-user` | 29 | 1 | 21 |
| `bh-demo` | 🔶 Redshift | "Brighthive Demo Environment" (`1c7cb12e…`) | default `stage/login-user` | 54 | 2 | 37 |

Command: `scripts/run_health_check.py --env=staging --configs oneten loopcapital bh-demo --skip-webapp`.
Each config = one isolated pytest session (410 selected / 432 collected). Reports:
`brighthive-e2e/findings/staging-20260731-{023127,024331,025659}.{json,md}`.

> Runner exit code was `2` per config — that is pytest's "tests failed" code, and
> **expected**: the health suite asserts real contracts and records findings
> rather than passing vacuously. Exit 2 = "findings were produced," not "the
> harness broke."

## The payoff — findings that reproduce on ALL 3 engines (🔁, real signal)

These are engine-agnostic. If it fails on Snowflake AND SQL Server AND Redshift,
it is the platform, not the warehouse — the highest-confidence bug tier.

| Sev | Finding | Surface |
|---|---|---|
| 🟢 BLOCKER | `scaffold_atlas_semantic_view` errors on a Silver asset — `bad_request: silver_schema.name is required` (single-table SV enrollment broken end-to-end) | semantic_views |
| 🟢 HIGH | `confirm_semantic_view_merge` missing from the shared MCP catalog (SV lifecycle can't reconcile a merged PR) | semantic_views |
| 🟢 HIGH | `materialize_dbt_project` did not open a GitHub PR for generated dbt code | data |
| 🟢 HIGH | `QualityRuleExecution` does not expose `executedSql` | data |
| 🟢 HIGH | valid `longitudinal_anomaly` QualityRule rejected (BH-672) | graphql |
| 🟢 HIGH | `current_workspace` status=None — expected 'ok' (BUG-042) | mcp |
| 🟢 HIGH | `discover_data_assets` returned no assets for the session workspace | agents |
| 🟢 HIGH | `list_platform_sources` leaks raw GraphQL response shape (`data.data.workspace…`) | mcp |
| 🟢 HIGH | `workspace.services.sources` returned `GRAPHQL_VALIDATION_FAILED` | graphql |
| 🟢 HIGH | `workspace.projects(filter:{status:'DRAFT'})` query failed | graphql |
| 🟢 HIGH | `DataAsset` cannot represent Snowflake share read-only access | graphql |
| 🟢 HIGH | `DataAsset` does not expose `partitionKey` for S3 vendor ingestion | graphql |
| 🟢 HIGH | REST ingestion row count not exposed in the catalog contract | graphql |
| 🟢 HIGH | `'Not Available'` sentinel leaks into asset table-name fields | semantic_views |
| 🟢 HIGH | 1 tool returned `structuredContent` without a valid status | mcp |
| 🟢 MED | `hasSemanticView` filter query failed | graphql |
| 🟢 MED | `generate_quality_expectations` returned isError=true with empty body | agents |
| 🟢 MED | `generate_sql_query_tool` returned isError=true with no error code | agents |
| 🟢 MED | real dbt DAG lineage (`get_lineage`) absent — only grep-based impact available | data |
| 🟢 MED | no dbt PR-state reconcile (parity gap vs `confirmSemanticViewMerge`) | data |
| 🟢 MED | `runPipelineSegment` error missing expected `no_path_a_to_b` code | data |

**21 shared findings.** This is the engine-agnostic defect backlog — the list a
"make it work on 3 warehouses" effort actually has to burn down.

## Reproduces on 2 of 3 (◧ — deployment-specific, not universal)

| Engines | Finding | Read |
|---|---|---|
| ❄️ 🔶 | `dataset profiling failed on a real asset` (BH-688) | absent on SQL Server run |
| ❄️ 🔶 | `fetch_dbt_sources` status `not_found`; `github_list_branches`/`github_list_files` status `error` | dbt/GitHub bridge wired for some workspaces only |
| ❄️ 🟦 | `get_semantic_view_yaml` YAML differs from GraphQL truth for `GT.ASSET_WITH_SV` | only where an SV-bearing asset exists (Redshift has none) |
| ❄️ 🔶 | 2 e2e test artifacts leaked into the workspace catalog | cleanup gap on 2 workspaces |

## Harness / config artifacts (⚠️ — the sweep's own gaps, NOT platform bugs)

Surfaced by *this run's* fixtures, not the product. Fixing these makes the next
sweep's signal trustworthy — they must not become platform tickets.

| Artifact | Root cause | Fix owner |
|---|---|---|
| ⚠️ ❄️ `current_workspace returns wrong workspace_id` + `list_platform_source(_definition)s`/`validate_openmetadata_id` wrong ws + `5 schedules leaked` + MCP introspect **221 vs 21** (diverge 200) | MCP session binds to the token's *other* (larger) workspace — `X-Workspace-Id` not pinned per session. See [[mcp-workspace-binding-and-flags]]. | e2e harness |
| ⚠️ 🟦 `GT.ASSET_WITHOUT_SV (None) not in workspace`; ⚠️ 🔶 `GT.ASSET_WITH_SV (None) not found` / `... not present` (blocker) / `get_semantic_view for None` | Optional-`None` SV slots leak into tests that should `skip` when the slot is `None`, instead asserting on the literal string `"None"`. | e2e harness |
| ⚠️ all `test_dbt_lifecycle.py` (~11 fails/config, identical) | `_DBT_REPO`/`_LINEAGE_GROUND_TRUTH` hardcoded to demo repo `brighthive-demo-transform` (dbt Cloud 395091); not keyed by `--workspace-config`, so it fails on every workspace not bound to that repo. → **task: per-config transformation slot.** | e2e harness (#11) |
| ⚠️ per-workspace data-quality counts (`N/A`/`Not Available` sentinels, empty `tableFQN`, null `connectionType`, `STG_STG_` double-prefix, asset-count ceilings) | Real *data-hygiene* observations about each workspace's catalog — valid, but per-workspace state, not cross-engine platform defects. Track as data-quality, separate from the engine-agnostic backlog. | data / per-workspace |
| ⚠️ findings written to `findings/*.md` root, not `findings/<config>/` | `_resolve_findings_out_dir` returns `path.parent` when the per-config dir doesn't exist yet — so `--findings-out=findings/oneten` collapses to `findings/`. Per-config isolation silently broken. | e2e harness |
| ⚠️ findings JSON carries no `workspace_id`/`config` tag | Can't attribute a finding to its engine from the JSON alone — only by reading titles. | e2e harness |

## What this changes about the plan

1. **Engine-agnostic backlog = the 21 shared findings.** That's the real
   "works on 3 warehouses" scope, evidence-ranked, blocker-first.
2. **Harness fixes come first** (workspace binding, `None`-slot skips,
   findings-out dir + per-finding config tag) so the *next* sweep's per-engine
   signal is clean and attributable — otherwise the noise re-litigates itself
   every run.
3. **Transformation/pipeline engine must be per-config** (dbt · Snowflake native
   pipelines · Databricks; multi-repo) — the hardcoded demo-repo lineage block is
   the single largest noise source and directly contradicts the engine-agnostic
   steer.
4. Fixes land as **small, single-concern PRs** (harness · transformation-config ·
   each platform defect), never one mega-PR.

## Provenance

- Fixtures: `brighthive-e2e/e2e/fixtures/ground_truth.py` (commit `1c3fd76`, warehouse-agnostic).
- Reports: `brighthive-e2e/findings/staging-20260731-{023127,024331,025659}.{json,md}`.
- Runner: `brighthive-e2e/scripts/run_health_check.py` (feature-tree targeting fixed this run).
