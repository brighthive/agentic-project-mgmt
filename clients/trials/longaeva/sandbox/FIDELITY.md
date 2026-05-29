# Sandbox fidelity — live tracker

> What's high-fidelity vs. thin in our Longaeva POC simulation, and what we're closing next.
> Updated as work lands. Source of truth for "are we trial-ready?"

**Last updated**: 2026-05-29
**Overall fidelity**: ~40% end-to-end / ~80% for `SnowflakeConnection` + introspection + semantic-view-DDL surface

## Snapshot

| Layer | Status | Fidelity | Notes |
|---|---|---|---|
| Snowflake account + role + warehouse | ✅ Live | High | Real account `bfddsko-dua97555`; not mocked |
| BRONZE / SILVER / GOLD / REF / SEMANTIC schemas | ✅ Live | High | 12 tables; canonical time-series shape |
| Semantic view DDL (compile path) | ✅ Live | High | `sv_daily_portfolio_exposure` compiles cleanly |
| Reference data (fiscal cal, identifier map, geo, classification) | ✅ Schema | Medium | Tables exist; **no rows yet** |
| Two-DB topology (warehouse + share-sim) | ✅ Live | Medium | Cross-DB grant ≠ real Data Share provisioning |
| Synthetic seed data (~5M rows) | ⏳ Open | — | **Highest-ROI gap**. Without data, semantic-view query correctness can't be validated. |
| dbt project skeleton | ⏳ Open | — | Scaffolder emits `sources.yml` but has nothing to merge into |
| Real S3 external stage (vs. internal stage stand-in) | ⏳ Open | — | `COPY INTO` semantics identical; IAM + storage integration differ |
| Real Snowflake Data Share (vs. simulated DB) | ⏳ Open | — | Same query shape, different provisioning flow |
| Dagster + OpenLineage | ⏳ Open | — | Self-healing reads Dagster logs; we have none |
| Great Expectations init | ⏳ Open | — | Quality contracts theoretical until GX wired |
| GitHub Enterprise base_url config | ⏳ Open | — | One of six BH-526 gaps; trivially testable once GHE creds arrive |
| Longaeva's *actual* extended YAML spec | ⏳ Blocked | — | We invented a representative spec; theirs lands Day 3 |
| Vendor file shapes (real schemas) | ⏳ Blocked | — | Guessed columns; real samples Day 4–5 |
| Their internal MCP server | ⏳ Blocked | — | Item 3 of POC; their provisioning Day 1–2 |

Legend: ✅ done · ⏳ open (in our court) · ⏳ blocked (waiting on Longaeva)

## What we get right (high-fidelity wins)

- **Real Snowflake account** — not a mock; the `SnowflakeConnection` factory will hit actual error paths
- **Medallion separation of concerns** — BRONZE / SILVER / GOLD with the right boundaries
- **Semantic view DDL** — Snowflake's actual `CREATE SEMANTIC VIEW` grammar; the scaffolder learns the *real* syntax (FACTS-before-DIMENSIONS, alias-first, RELATIONSHIPS clause)
- **Reference-data shape** — fiscal calendar with non-Jan FY cohorts, LEI/FIGI/CUSIP/ISIN→internal_issuer_id, geo + classification — the join targets the scaffolder must auto-detect
- **Two-database topology** — warehouse + inbound share, mirrors their pattern

## Where fidelity is thin (in our court)

| # | Gap | Trial impact | ETA | ROI |
|---|---|---|---|---|
| F1 | **No data** | Scaffolder validates compile but not query correctness (POC 2.3, 3.2). YAML can ship that compiles but returns empty/wrong results. | 0.5 d | 🔥 highest |
| F2 | **No dbt project** | Scaffolder emits `sources.yml` + staging models with nothing to merge into. POC 1.1–1.3 demand "merge-ready artifacts." | 1 d | high |
| F3 | **GHE base_url config** | One of six BH-526 gaps. Trivial flag, only testable when GHE creds arrive. | 1 h | medium |
| F4 | **Great Expectations init** | Quality contracts in POC 1.3 + 4.2 are theoretical without GX wired. | 0.5 d | medium |
| F5 | **Real S3 external stage** | Internal stage has identical `COPY INTO` semantics but no IAM / storage integration / S3 LIST polling. | 1 d | medium (deferrable to trial) |
| F6 | **Real Snowflake Data Share** | Cross-DB grant gives same query shape but skips `IMPORT SHARE` / `CREATE DATABASE FROM SHARE` provisioning. | 1 d | low (deferrable to trial) |
| F7 | **Dagster + OpenLineage** | Self-healing (POC 4.1) diagnoses Dagster logs; longitudinal monitoring (4.3) reads OpenLineage. We have neither. | 2 d | low (agent code testable without orchestrator) |

## Where fidelity is blocked on Longaeva

| # | Gap | Unblock by |
|---|---|---|
| B1 | Their **actual extended YAML spec** | Day 3 — context layer creation milestone |
| B2 | **Vendor file shapes** (real columns) | Day 4–5 — sample datasets milestone |
| B3 | **Their internal MCP server** access | Day 1–2 — system access provisioned milestone |

## Closure roadmap (in priority order)

1. **F1 — Synthetic seed** (0.5 d) — turns sandbox from "shape-only" to "actually verifiable end-to-end"
2. **F2 — dbt project skeleton** (1 d) — `dbt init`, project pointed at sandbox, committed under `sandbox/dbt/`; turns scaffolder output into mergeable artifacts
3. **F3 — GHE config flag** (1 h) — cheap close on a BH-526 gap
4. **F4 — GX init** (0.5 d) — makes POC 4.2 demonstrable pre-trial
5. **F5 — Real S3 storage integration** (1 d) — only if S3 ingestion must be merge-ready before Day 1
6. **F7 — Dagster compose** (2 d) — only if self-healing must demo pre-trial; otherwise unit-test the agent path
7. **F6 — Real Data Share** (1 d) — defer to trial unless provisioning becomes critical

Track each item as a discrete PR off `drchinca/BH-526/snowflake-sandbox-ddl` so the buildout is incremental and reviewable.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-05-29 | DDL-first, no seed data | Wanted Snowflake objects to merge against before trial; seed bumped to F1 close |
| 2026-05-29 | Internal stage stand-in for S3 | Avoid S3 credentials/IAM until needed; `COPY INTO` semantics are identical |
| 2026-05-29 | Cross-DB grant simulates Data Share | Real shares need provider-side configuration we don't run unilaterally |
| 2026-05-29 | YAML spec invented (representative, not Longaeva's actual) | Their spec lands Day 3; placeholder is good enough for scaffolder grammar testing |
