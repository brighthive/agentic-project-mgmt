---
title: "Longitudinal Monitoring — cross-repo contract, deployment & testing reference"
epic: "BH-601"
parent_spec: "longitudinal-monitoring-capability.md"
author: "drchinca"
status: Shipped
created: "2026-06-17"
tags: [quality, monitoring, longitudinal, deployment, contract, testing, brightbot, platform-core, webapp]
related:
  specs: ["longitudinal-monitoring.md", "longitudinal-monitoring-capability.md", "quality-rules-configurable.md"]
roadmap: done — staging-verified with parent 2026-06-18
---

# Longitudinal Monitoring — Contract, Deployment & Testing

> The GC-12 capability spans **three repos that cannot import each other**. This doc is the single place that ties the seams together: the shared data contracts, the deploy order, and the testing posture. Read before merging any of the three PRs.

## Repos & PRs

| Repo | PR | Role |
|---|---|---|
| platform-core | #891 | `MetricSnapshotNode` + `AnomalyEventNode` persistence; `longitudinal_anomaly` rule validation |
| brightbot | #575 | capability node in the quality pipeline; `MetricHistoryStore`; MCP tools |
| webapp | #1178 | "Data Drift Monitor" rule editor |
| agentic-project-mgmt | #54 | specs (this doc + capability contract + parent) |

## 1. Data contracts (the seams)

### Seam A — OGM (brightbot → platform-core)
brightbot's `OGMMetricHistoryStore` issues GraphQL against platform-core's auto-generated OGM API. **Verified FULL MATCH** by building the actual `@neo4j/graphql@4.4.7` schema from `typedefs.ts`:

| brightbot emits | platform-core generates |
|---|---|
| `createMetricSnapshotNodes` / `createAnomalyEventNodes` | ✓ (from `MetricSnapshotNode`/`AnomalyEventNode`) |
| `metricSnapshotNodes` / `anomalyEventNodes` queries | ✓ |
| `dataAsset: { connect: { where: { node: { id }}}}` | ✓ (`DataAssetNodeConnectWhere.node`) |
| read scope `dataAsset: { workspaces_SOME: { id }}`, `detectedAt_GTE` | ✓ |

**Drift guard**: the only thing that breaks this seam is editing `typedefs.ts` node names/fields. A future change there MUST keep the field names brightbot's `metric_history_store.py` uses (single source: `_CREATE_SNAPSHOTS`/`_QUERY_*` constants + `SNAPSHOT_SELECTION`/`ANOMALY_SELECTION`). The live E2E in §3 is the real protection.

### Seam B — config (webapp → platform-core → brightbot)
The `longitudinal_anomaly` QualityRule `expectationParams` JSON:
```json
{ "metric_specs": [ {"name":"row_count","family":"row_count_drift","tolerance":0.20,"absolute":false} ], "trailing_window": 7 }
```
- **Tolerance is a FRACTION** end-to-end (webapp divides the % input by 100; brightbot compares fractional deviation). Verified — no 100× bug.
- **Family vocabulary** is a closed set hardcoded in three places, now each pinned by a test:
  - brightbot `AnomalyFamily` ← `tests/unit/agents/test_longitudinal_contract.py`
  - platform-core `ANOMALY_FAMILIES` ← `tests/unit/longitudinal-rule-validation.test.ts`
  - webapp `METRIC_FAMILIES` ← `src/Governance/components/longitudinalContract.test.ts`
  - **Source of truth**: `longitudinal-monitoring-capability.md` §2.2. Change all three + the spec in one PR.
- **Full-shape validation**: platform-core `validateLongitudinalParams` rejects malformed specs (bad family, empty name, non-positive tolerance, non-int window) at write time; brightbot `parse_metric_specs` re-validates (defense in depth) and raises a clear `ValueError` rather than crashing.

## 2. Deployment (ordered)

Deploy **platform-core first** — the brightbot store calls GraphQL operations that don't exist until platform-core ships.

### platform-core (PR #891) — FIRST
1. **Deploy the Lambda** (`npm run deploy:<env>` / `deploy-dev.yml` `workflow_dispatch`). esbuild compiles TS at this step.
2. **`@id` unique constraints auto-create** on first cold start (`ogm-server.ts` `assertIndexesAndConstraints({create:true})`). No action.
3. **Composite indexes are MANUAL** — there is **no migration runner** in this repo (the BH-503 `quality-rules-indexes.cypher` precedent is also unwired). After deploy, apply against each env's Neo4j (idempotent, `IF NOT EXISTS`):
   ```bash
   cat setup/scripts/cypher/longitudinal-monitoring-indexes.cypher \
     | docker exec -i <neo4j-container> cypher-shell -u neo4j -p <pw>
   ```
   Without it, trailing-window/anomaly reads do label scans — correct but slow at scale.
4. **`ogm-types.ts` regen — deferred, COSMETIC (not a blocker)**: the runtime builds its schema from `typedefs.ts` directly (`ogm-server.ts`), and the new code uses raw Cypher + the base `Node` class — it imports nothing from the generated file. Regenerate as a follow-up cleanup for diff hygiene; it does not gate go-live.

### brightbot (PR #575) — SECOND
5. **Deploy the LangGraph app + MCP server** (normal brightbot path).
6. **No `langgraph.json` change** — the capability node is internal to the already-registered `quality_check_agent_graph`. Confirmed.
7. **MCP tools auto-surface** — `get_anomalies` / `run_longitudinal_analysis` register via `@mcp.tool()` decorators in `register(mcp)`; no manifest to update.

### webapp (PR #1178) — LAST
8. **Deploy via release** (Amplify; `npm run build` = `tsc && vite build` type-checks at deploy). **No webapp codegen needed** — `expectationType`/`expectationParams` are plain `String` in the GraphQL schema, not generated enums.

## 3. Testing posture

### What's covered now
| Layer | Coverage |
|---|---|
| brightbot unit (capability node, store, config, contract) | 31 tests, DI/no-patch — gating, INV-3 ordering, best-effort failure paths, tenant guard, contract pin |
| platform-core unit (validation + family pin) | 8 tests, wired into CI allowlist |
| webapp unit (contract pin) | 3 tests |
| OGM seam | statically verified (schema build) — see §1 Seam A |

### Gaps (tracked, not silently accepted)
- **brightbot CI is disabled** (`test.yaml` `if: false`, "Temporarily disabled") and **webapp has no PR test/lint/tsc gate**. The new tests pass locally but **do not run in CI** until those pipelines are re-enabled. → flag to the control-plane owner; not in this feature's reach to flip.
- **No live cross-repo E2E.** The GC-12 suite uses DI stubs (honest `live_partial`). The smallest real proof of Seam A:
  1. `docker compose -f brightbot/docker-compose.local.yml up neo4j`; point a local platform-core `ogm-server` at it.
  2. Apply the index cypher (also tests the migration step).
  3. Seed one `DataAssetNode` + its `(:WorkspaceNode)-[:USES]->` edge.
  4. Gate on `RUN_LIVE_MCP=1`; `OGMMetricHistoryStore(...).write_snapshot(...)` → `trailing_window(...)`; assert round-trip + workspace scoping.
  - This is the test that flips GC-12 `live_partial` → `live`. No Snowflake/LLM needed (warehouse is upstream of the store).

## 4. Go-live checklist
- [ ] platform-core #891 merged + deployed; index cypher applied per env
- [ ] brightbot #575 merged + deployed (LangGraph + MCP)
- [ ] webapp #1178 merged + released
- [ ] live E2E (§3) green on staging → flip GC-12 to `live`, recompute scorecard
- [ ] (follow-up) regenerate `ogm-types.ts`; re-enable brightbot/webapp CI gates
- [ ] (deferred) BH-673 anomaly → dbt-agent self-healing bridge
