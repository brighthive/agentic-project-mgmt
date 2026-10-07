---
title: BrightHive MCP user journeys and staging handoff
epic: BH-1181
tickets: [BH-1581]
status: Beta
shipped_date: "2026-10-06"
last_verified_utc: "2026-10-07"
services: [brightbot, brighthive-webapp, brighthive-e2e]
tags: [mcp, staging, user-journeys, handoff]
related:
  specs: [mcp-stateless-transport.md]
  pocs: []
---

# BrightHive MCP user journeys and staging handoff

## What It Does

BrightHive MCP lets an authenticated client discover workspace data, ask BrightAgent questions,
manage projects, build and operate pipelines, and use ingestion, quality and governance tools.
The staging identity used for this verification saw **131 tools**. Catalog membership varies
with identity, scopes and feature flags; it is a dated observation, not a fixed tool-count contract.

**Staging acceptance is green:** 150/150 raw calls returned HTTP 200; the MCP suite with writes
and the gate enabled reported 78 passed, 8 expected skips and zero findings. Confirmed project
create/update/archive/read/delete ran successfully. Production was not changed or verified.

## How It Works

The user selects an authenticated workspace, discovers the available tools, and previews changes
before confirming them. Tools enforce applicable scopes and workspace authorization. Data,
warehouse, GitHub and connector configuration determine which journeys can complete.

The transport and recovery contract is in the [stateless transport spec](../specs/mcp-stateless-transport.md).
Permanent platform architecture remains in [platform-saas-ai-context](https://github.com/brighthive/platform-saas-ai-context).

## How to Use It

### For Users

1. Connect an authenticated MCP client to `https://brightagent-mcp.staging.brighthive.net/mcp`.
2. Check the workspace with `current_workspace` and discover tools with `tools/list`.
3. Choose a journey below. Read and preview the proposed changes before confirming writes.
4. Inspect the resulting project, run, artifact or review PR to confirm the outcome.

| Journey | Example request | Tool path and outcome |
|---|---|---|
| Discover data | What data can we use for retention analysis? | `discover_data_assets`, `list_workspace_warehouses`, `list_warehouse_databases`, `list_warehouse_tables`, `introspect_warehouse_schema` identify assets and their structure. |
| Ask and visualize | Explain this trend and chart it. | `analyst_ask`, `generate_sql_query_tool`, `generate_vega_lite_chart_tool`; long agent requests use `analyst_ask_run_async` and `analyst_ask_poll`. SQL/chart generation alone does not execute SQL. |
| Manage projects | Create and organize a retention project. | `create_project`, `update_project`, asset/file attachment, `set_project_status`, `get_project`, `delete_project`. Setting ACTIVE starts a review; the validated lifecycle used ARCHIVED. |
| Build from a specification | Turn this specification into a pipeline. | `upsert_project_spec`, `propose_pipeline_from_spec`, `apply_pipeline_from_spec`, `get_project_spec_conformance`. Applying a proposal replaces existing steps after confirmation. |
| Refine a pipeline | Add a transformation and bind its inputs. | `create_project_pipeline`, `add_or_update_pipeline_step`, `bind_pipeline_step`, `connect_pipeline_steps`, `compile_project_pipeline`, `resolve_pipeline_issue`. |
| Operate a pipeline | Run this project and investigate a failed step. | `validate_project_pipeline`, `run_project_pipeline`, `list_project_runs`, `get_project_run`, `rerun_project_pipeline`, pause/resume. Requires a configured pipeline with runnable steps. |
| Assess quality | Profile this dataset and propose quality checks. | `analyze_dataset_structure`, `scan_warehouse_tables`, `generate_quality_expectations`, `infer_dbt_schema_tests`, `execute_library_quality_rules`. Rule execution is a confirmed write. |
| Develop dbt | Turn this SQL into a reviewed dbt model. | Inspect sources, generate/convert SQL, `validate_dbt_refs`, `review_sql_code`, `analyze_model_impact`, then GitHub commit and pull-request tools. Requires a linked repository. |
| Review semantic views | Draft a semantic view and open a review PR. | `get_semantic_view_yaml`, `scaffold_atlas_semantic_view`, `qc_semantic_view_pipeline`, `ship_semantic_view_to_github`, `check_semantic_view_status`. Native Snowflake view inspection requires that engine; YAML and QC need suitable assets. |
| Ingest data | Connect this source and synchronize it. | Discover connector definitions, inspect connection specs, `store_source_credentials`, `add_platform_source`, `create_platform_connections`, `sync_platform_connections`, `list_ingestion_flows`. |
| Inspect and govern access | Who manages this project and what rules apply? | Read members, permission matrix, policies and glossary; inspect project governance; `declare_project_governance_gate` and `change_project_owner_or_managers` are confirmed changes. |
| Deliver outputs | Configure where this project's outputs go. | Inspect `list_project_data_products`; add/update/remove project destinations. Actual delivery depends on the configured destination and pipeline. |
| Monitor operations | What needs attention today? | `get_fleet_health`, `list_workspace_signals`, pipeline/warehouse health, `get_anomalies`, `list_routines`, `list_scheduled_agents`. |

### For Developers

Start in the canonical **brighthive-e2e** checkout, whose default branch is **master**.
Select the `bh-demo` workspace explicitly; an ambient workspace override can otherwise test a
different workspace. Resolve credentials through the harness; never print tokens or commit them.

```bash
# From brighthive-e2e, on a checkout containing PR #98:
env -u BH_WORKSPACE_ID BH_ENV=staging AWS_PROFILE=brighthive-staging \
  uv run pytest e2e/features/mcp --workspace-config=bh-demo \
  --writes --gate --tb=short --capture=tee-sys -q
```

The login returns both ID and access tokens. The tested login's **access token** already carried
`mcp:write`; its ID token did not. Project write tests use `initialize_mcp(use_access_token=True)`.
GraphQL and the unscoped refusal probes retain ID-token behavior. Do not globally switch every MCP
probe to the access token: explicit scopes narrow permissions and may omit warehouse/agent scopes.

Refresh the catalog without executing tools:

```bash
BH_ENV=staging AWS_PROFILE=brighthive-staging uv run python - <<'PY'
from e2e.core.auth import resolve_auth_token
from e2e.core.env import Env, env_config
from e2e.core.mcp import initialize_mcp
cfg = env_config(Env.STAGING)
session = initialize_mcp(base_url=cfg.mcp_url, token=resolve_auth_token(env=cfg))
try:
    for tool in session.list_tools():
        print(tool["name"], tool.get("description", ""))
finally:
    session.close()
PY
```

For a fresh raw transport acceptance check, initialize five independent HTTP clients using the
harness-resolved bearer, assert `serverInfo.name == "brightbot-mcp"`, send `notifications/initialized`,
and make 30 `tools/list` requests per client. Accept JSON or SSE response framing. Use no retries;
count every HTTP status and RPC error. Expected: 150 HTTP 200, no RPC errors, and no session IDs
on initialization. This raw check complements the client recovery tests, which intentionally retry.

### Code and acceptance coverage

| Location | Purpose |
|---|---|
| [BrightBot transport](https://github.com/brighthive/brightbot/blob/staging/http/app.py) | Production mount uses `http_app(path="/", stateless_http=True)`. |
| [Tool registry](https://github.com/brighthive/brightbot/blob/staging/brightbot/mcp/server.py) | Feature registration and write-scope guard; implementations live under `brightbot/mcp/tools/`. |
| [Error middleware](https://github.com/brighthive/brightbot/blob/staging/brightbot/mcp/error_middleware.py) | Sanitized failure envelopes carry the MCP error flag. |
| [MCP client](https://github.com/brighthive/brighthive-e2e/blob/master/e2e/core/mcp.py) | Optional session header, bounded reopen-on-404, explicit access-token selection. |
| [Client unit tests](https://github.com/brighthive/brighthive-e2e/blob/master/e2e/core/test_mcp.py) | Fake transport recovery, refresh and token-choice regressions. |
| [Project acceptance](https://github.com/brighthive/brighthive-e2e/blob/master/e2e/features/mcp/test_projects.py) | Reads, previews, refusal and confirmed lifecycle with cleanup. |
| [MCP acceptance bucket](https://github.com/brighthive/brighthive-e2e/tree/master/e2e/features/mcp) | Catalog, auth, workspace binding, warehouse, governance and reads. |

## Sub Features

### Confirmed project lifecycle

Create a uniquely named throwaway project, rename it, set ARCHIVED, read back the result, then
delete with the exact current project name. Verify `get_project` returns `not_found` before
teardown. Cleanup callbacks drain in reverse order: delete resources before closing their client.

### Rollout and verification evidence

Verification completed on 2026-10-07 UTC, corresponding to October 6 in Costa Rica.

| Component | Merged changes and deployment |
|---|---|
| Webapp | [#1486](https://github.com/brighthive/brighthive-webapp/pull/1486) into staging; Amplify staging job 274 succeeded before the server switch. |
| BrightBot | [#1119](https://github.com/brighthive/brightbot/pull/1119) stateless transport; [#1120](https://github.com/brighthive/brightbot/pull/1120) error flag; both into staging. Active commit `483899c812f3a53d758c46f8f17441eba076586a`, revision DEPLOYED with active/latest IDs matching. |
| E2E | [#94](https://github.com/brighthive/brighthive-e2e/pull/94), [#96](https://github.com/brighthive/brighthive-e2e/pull/96), [#97](https://github.com/brighthive/brighthive-e2e/pull/97), [#98](https://github.com/brighthive/brighthive-e2e/pull/98) merged into master; verified head `1b3f73da5eb67410f145fe9b271eab2aabf46c39`. |

| Check | Result |
|---|---|
| Raw transport after replica drain | 5 clients × 30 calls; 150 HTTP 200, zero 404s, zero RPC errors; no session IDs. |
| Client retained across deployment | 49 successful catalog calls, including five after activation. |
| Full MCP suite with writes and gate | 78 passed, 8 skipped, zero findings, exit 0; all five project tests executed. |
| Cleanup | 3 succeeded, 0 failed. |
| Focused BrightBot unit tests | 88 passed across errors, transport, auth, scopes and permissions. |
| E2E core unit tests | 40 passed. |

The PR descriptions preserve the verification summary. Local `/tmp` logs and the catalog export
are supplementary evidence, not a dependency for future sessions. Recheck live deployment state
and the catalog before presenting this dated snapshot as current. Deployment verification must
check the revision's DEPLOYED status and active/latest identity, not only the desired source SHA.

## Limitations and Roadmap

- Catalog presence establishes that a tool is advertised. It does not establish that every complete
  journey or confirmed write has been exercised; the confirmed end-to-end write proof is project CRUD.
- Eight acceptance skips: viewer credentials (1), absent semantic-view asset (2), disabled governance
  writes (2), and absent PII fixtures (3). Provision those prerequisites to extend coverage.
- Workspace role-permission editing and scheduling/approval tools were not advertised in this catalog;
  routines and existing schedules could be inspected. Project manager changes are a separate tool.
- GitHub, ingestion, pipeline execution, semantic views and quality runs need their corresponding
  workspace configuration, permissions and data. This work did not validate client OAuth onboarding.
- Production promotion still requires explicit user approval. Staging success is not production proof.
- Older MCP consumption and environment docs describe a historical three-tool surface. Use the live
  catalog for availability and this dated handoff for the completed rollout evidence.

## Changelog

- **2026-10-06**: BH-1581 stateless transport and compatible clients deployed to staging; follow-up
  error contract and harness fixes completed verification on 2026-10-07 UTC.

## Related

- [Stateless transport spec](../specs/mcp-stateless-transport.md)
- [BH-1581](https://brighthiveio.atlassian.net/browse/BH-1581)
- [Spec and handoff PR 197](https://github.com/brighthive/agentic-project-mgmt/pull/197)
- [Permanent environment context](https://github.com/brighthive/platform-saas-ai-context/blob/master/docs/infrastructure/ENVIRONMENTS.md)
