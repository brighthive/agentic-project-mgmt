---
title: "Longitudinal Anomaly Monitoring — stateful quality agent + scheduled nightshift"
epic: "BH-503"
author: "drchinca"
status: "Draft"
created: "2026-06-15"
generates: "tickets"
tags: [quality, monitoring, longitudinal, anomaly, nightshift, brightbot, platform-core, snowflake, golden-cases]
related:
  features: []
  pocs: []
  specs: ["quality-rules-configurable.md", "byow-end-to-end-omd-native.md", "warehouse-agnostic-architecture.md"]
---

# Longitudinal Anomaly Monitoring (Golden Case 12 / GAP-8)

> Closes the single largest Longaeva PoC gap. GC-12 is currently `skip` — *no code, no ticket*. This spec defines how the **proven sandbox** (`clients/trials/longaeva/sandbox/monitoring/`) becomes a product capability: a **stateful** quality agent that persists per-run metrics and surfaces anomalies vs a trailing window, plus the **nightshift** scheduler that runs it unattended.

## Problem

BrightHive's quality agent is **stateless per run** — it regenerates a fresh Great Expectations suite from an LLM each invocation and emits one JSON blob. Nothing a workspace observed yesterday is comparable to today. That makes the entire class of *trend* questions — "did row count drift?", "did a key dimension's cardinality collapse?", "did null rate spike?", "did a metric's distribution shift?" — impossible to answer. Grant (Longaeva) named exactly these four as the PoC's use-case 4.3. GC-12's bar is **"≥1 anomaly surfaced from 4 families."** Today: 0 — there is no per-run history to trend against.

This is distinct from, but builds on, **BH-503 (configurable quality rules)**: that spec persists *rule definitions* + per-rule pass history; this one persists *per-run metric values* and does *statistical trend detection* over them.

## Use Case / Goal

A workspace's warehouse is scanned on a schedule (nightshift). Each run snapshots a small set of data-health metrics per dataset into history. The monitor compares the latest snapshot against a trailing window and writes an `anomaly_event` whenever a metric deviates beyond its tolerance. Surfaced anomalies notify the workspace (BrightSignals) and are answerable by the analyst agent ("what anomalies fired last night?"). Success = GC-12 flips from `skip` to `live`: ≥1 anomaly from the 4 families, surfaced end-to-end on staging, nothing dirty.

## Current Situation

### How it works today
- **Proven in the sandbox** (`clients/trials/longaeva/sandbox/monitoring/`, validated 4/4 in sim):
  - `00_monitoring_ddl.sql` — `MONITORING.metric_history` (PK `snapshot_ts, dataset, metric_name`) + `MONITORING.anomaly_events`.
  - `monitor.py` — `compute_metrics()` snapshots row_count / cardinality / null_rate / mean+stddev; `detect()` compares latest vs a `TRAILING_WINDOW = 7` window with per-metric fractional tolerances; writes `anomaly_events`.
  - Four families: `row_count_drift`, `cardinality_breakdown`, `distributional_skew`, `null_spike`.
- **In the product (updated 2026-06-17 after code audit)**: two slices are **shipped as pure functions, called only in tests** — not yet wired into any production path:
  - `brightbot/brightbot/agents/governance_agent/tools/longitudinal_detect.py` (#557) — `detect_anomalies(current, history, specs)` ports the sandbox `detect()`; all 4 families covered by unit tests. The module owns *only* the statistical decision; the caller wires source + sink.
  - `brightbot/brightbot/agents/governance_agent/tools/metric_snapshot_sql.py` (#563) — `build_snapshot_sql(...)` returns dialect-templated metric SQL (Snowflake/Redshift/Postgres/Synapse). Returns a string; does not execute.
  - The quality agent (`quality_tools.py`) remains stateless. **Still ABSENT**: metric-history persistence, the caller that computes+stores snapshots, the scheduler, the anomaly surface, the analyst read path. `brightbot/tests/integration/golden_cases/test_gc_12_longitudinal_live.py` records GC-12 as `live_partial` for exactly this reason.

### Hard limitations / gaps
- **No state**: per-run metrics are not persisted, so no trend is computable.
- **No scheduler ("nightshift")**: nothing runs the monitor unattended on a cadence.
- **No anomaly surface**: BrightSignals notification scaffold (bb#486) exists but has no anomaly source to push from; the analyst agent has no `anomaly_events` to read.
- **Mapping (corrected 2026-06-17)**: GAP-8 originally said metric history maps to BH-503's `QualityRuleExecutionNode`. **Code audit refutes this**: that node (live in platform-core `quality-rule.ts`) stores per-rule *pass/fail* results (`evaluatedCount`, `successCount`, `passed`), not raw *metric values* (`row_count`, `cardinality`, `mean/stddev`). GC-12 needs its **own** `MetricSnapshotNode` keyed by `(snapshot_ts, dataset, metric_name)`. BH-503 is a sequencing dependency only for the **rule-library config surface** (which datasets/metrics a workspace opts into), not for the metric store itself.

## Proposals / Solutions

**Persist metrics where BH-503 persists rule results; detect with the sandbox's trailing-window algorithm; schedule with a nightshift cron.** Single warehouse-agnostic path (metric SQL is dialect-templated, same as the dbt agent's dialect map).

- **Persistence**: a dedicated `MetricSnapshotNode` (or a `metric_history` table in the workspace warehouse, mirroring `sandbox/monitoring/00_monitoring_ddl.sql`) keyed by `(snapshot_ts, dataset, metric_name)`. This is a **new store** — *not* BH-503's `QualityRuleExecutionNode`, which holds per-rule pass/fail rather than raw metric values. Attach `MetricSnapshotNode` to the same `DataAsset` relationship BH-503's `QualityRule.assets` uses, so a workspace marks "monitor this asset" through one surface.
- **Metrics**: per dataset per run — `row_count`, `cardinality:<dim>`, `null_rate:<col>`, `mean/stddev:<numeric>`. Configurable per workspace (rides BH-503's rule library).
- **Detection**: latest snapshot vs trailing window (default 7), per-metric fractional tolerance; emit `AnomalyEventNode` with family + observed/expected + severity.
- **Nightshift scheduler**: a scheduled trigger (EventBridge → the monitor) per workspace; cadence configurable. This is the missing "nightshift" .md — defined here, not yet built.
- **Surface**: anomaly → BrightSignals notification (wire bb#486 to the new source) + analyst agent reads `AnomalyEventNode` for NL questions.

## Areas Involved

| Area | Repo | Role |
|---|---|---|
| Metric snapshot + history | platform-core (Neo4j OGM) or workspace warehouse table | persist per-run metrics (share BH-503 store) |
| Detection engine | brightbot `governance_agent` | trailing-window compare (port `sandbox/monitoring/monitor.py::detect`) |
| Metric SQL (dialect) | brightbot | per-warehouse metric queries (reuse dbt dialect map) |
| Nightshift scheduler | data-workspace-cdk or platform-core | EventBridge schedule → monitor invocation per workspace |
| Notifications | brightbot BrightSignals (bb#486) | push on anomaly |
| Analyst read path | brightbot analyst agent | answer "what anomalies fired?" from AnomalyEventNode |
| Acceptance | brightbot `tests/integration/golden_cases/test_gc_12_longitudinal_anomaly.py` | flip skip → live |

## Acceptance Criteria

```gherkin
Feature: Longitudinal anomaly monitoring (GC-12 / GAP-8)

  Scenario: nightshift run surfaces a real anomaly from the 4 families
    Given a workspace warehouse with >= TRAILING_WINDOW prior metric snapshots
    When the nightshift scheduler triggers the monitor for a dataset
    Then per-run metrics are persisted to history (row_count, cardinality, null_rate, mean/stddev)
    And the latest snapshot is compared against the trailing window
    And at least one anomaly_event is written when a metric breaches its tolerance
    And the anomaly is classified into one of: row_count_drift, cardinality_breakdown, distributional_skew, null_spike

  Scenario: anomaly is surfaced to the workspace and answerable
    Given an anomaly_event was written
    When the workspace's notifications run
    Then a BrightSignals notification is emitted for the anomaly
    When the analyst agent is asked "what anomalies fired last night?"
    Then it answers grounded in the real anomaly_events, not an LLM guess

  Scenario: nothing dirty
    Given repeated nightshift runs
    Then no duplicate snapshots for the same (snapshot_ts, dataset, metric_name)
    And no anomaly_events without a backing metric_history row
```

## Dependencies

- **BH-503 (configurable quality rules)** — land first; share its execution-history persistence + rule library. Status: `quality-rules-configurable.md` Ready.
- **BYOW ingestion** (`byow-end-to-end-omd-native.md`) — datasets must be cataloged + queryable (Redshift + Snowflake already live on staging).
- **BrightSignals** (bb#486) — notification sink exists; needs the anomaly source.

## Ticket Breakdown

> **Status (2026-06-17, build landed).** The algorithm was already done (#557/#563 pure functions); the build wired it in as an **agentic capability** — monitoring is something the quality agent *does*, reachable through the platform's existing `run_context` surfaces (ingestion/scheduled/on-demand), NOT parallel infra. See `longitudinal-monitoring-capability.md` for the interface contract. Tickets roll up to BH-600 / GC-12 under epic BH-601.

| Ticket | What | Repo | PR | Status |
|---|---|---|---|---|
| BH-668 | `MetricSnapshotNode` + `AnomalyEventNode` persistence (own store — NOT BH-503's execution store, which holds pass/fail not raw metrics). Workspace-scoped reads. | platform-core | #891 | PR open |
| BH-669 | Longitudinal monitoring as a **capability node** in `quality_check_agent` (best-effort; INV-1 snapshot-every-run, INV-2 detect iff `run_context != INGESTION` + history). Consumes #557/#563. | brightbot | #575 | PR open |
| BH-670 | Runs on the **existing** scheduled dispatcher + `run_context` (reframed: no new EventBridge — the dispatcher already exists). Honors BH-503 `applyOnSchedule`. | platform-core | — | reframed, small |
| BH-671 | Analyst read path — `get_anomalies` MCP tool (grounded in `AnomalyEventNode`, workspace-scoped from principal). | brightbot | #575 | PR open |
| BH-672 | `longitudinal_anomaly` QualityRule type — validation (closed family set) + webapp "Data Drift Monitor" editor (mobile-first). The per-asset config surface. | platform-core + webapp | #891, #1178 | PR open |
| BH-673 | Anomaly → dbt-agent self-healing bridge — **DEFERRED** until GC-12 is live. | brightbot | — | deferred |
| — | Flip GC-12 `live_partial` → live (≥1 anomaly from 4 families, surfaced E2E on staging). | brightbot | — | blocked on merges + live E2E |

> GC-12 stays `live_partial` until the PRs merge AND a live-warehouse/OGM E2E proves the full loop on staging — the unit/integration suite uses DI stubs (honest, no overclaim).

## Related

- `quality-rules-configurable.md` — BH-503 parent (stateful quality foundation)
- `clients/trials/longaeva/BRIGHTHIVE_GAPS.md` §GAP-8 — gap inventory
- `clients/trials/longaeva/sandbox/monitoring/` — proven reference implementation (DDL + monitor)
- `brightbot/tests/integration/golden_cases/test_gc_12_longitudinal_anomaly.py` — acceptance bar
