# Sandbox fidelity — live tracker

> What's high-fidelity vs. thin in our Longaeva POC simulation, and what we're closing next.
> Updated as work lands. Source of truth for "are we trial-ready?"

**Last updated**: 2026-05-30 (F2 dbt project producing derived data products)
**Overall fidelity**: ~80% end-to-end / ~95% on Snowflake + dbt + semantic-view + RBAC + data-correctness surfaces
**Pipeline test**: `./test_pipeline.sh` — **27/27 passing** (connection, DDL, strip-and-emit, seed validation, dbt build with 34 tests, RBAC matrix)

## Snapshot

| Layer | Status | Fidelity | Notes |
|---|---|---|---|
| Snowflake account + role + warehouse | ✅ Live | High | Real account `bfddsko-dua97555`; not mocked |
| BRONZE / SILVER / GOLD / REF / SEMANTIC schemas | ✅ Live | High | 12 tables; canonical time-series shape |
| Semantic view DDL (compile path) | ✅ Live | High | `sv_daily_portfolio_exposure` compiles + queryable |
| **YAML strip-and-emit pipeline** | ✅ Live | High | `strip_and_emit.py`: extended YAML → strip SDK fields → Snowflake DDL → `snow sql` apply → compile success. Mirrors Grant's deploy flow exactly (per 2026-05-29 meeting). |
| **Extended YAML format** | ✅ Live | High | Explicit `spec:` / `sdk_extensions:` strip boundary; baseline_expectations block (validation harness layer 3); lineage + access_control hooks |
| **RBAC: scoped agent role** | ✅ Live | High | `LONGAEVA_AGENT_ROLE` boundary verified: queries semantic view ✓, blocked on BRONZE/SILVER/share/writes ✓ (in strict mode with `USE SECONDARY ROLES NONE`) |
| **End-to-end pipeline test** | ✅ Live | High | `test_pipeline.sh` — 17 assertions covering connection, schemas, stages, strip-and-emit round-trip, semantic-view query, RBAC matrix |
| Reference data (fiscal cal, identifier map, geo, classification) | ✅ Live | High | 25 geo + 14 classification + 24 fiscal periods (2 cohorts × FY24-26) + 200 issuers with LEI/FIGI/CUSIP/ISIN/cohort triples |
| **Synthetic seed data (~450k rows)** | ✅ Live | High | 1y daily; 200 instruments × 252 trading days prices, 30 portfolios × 252d × 15-35 holdings exposure mart, fiscal-aware. Random-walk prices, deterministic seed (RNG_SEED=42). Loader: `seed/seed.py --reset` |
| **dbt project (intermediate + data products)** | ✅ Live | High | `int_enriched_holdings` (SILVER, joined) + 3 derived data products in GOLD: regional exposure daily, top-50 issuers daily, fiscal-quarter exposure. 34 tests passing. Custom singular tests mirror YAML's baseline_expectations. Run: `cd dbt && source set_env.sh && dbt build` |
| Two-DB topology (warehouse + share-sim) | ✅ Live | Medium | Cross-DB grant ≠ real Data Share provisioning |
| ~~dbt project skeleton~~ | ✅ Live | — | Done 2026-05-30; see row above |
| Real S3 external stage (vs. internal stage stand-in) | ⏳ Open | — | `COPY INTO` semantics identical; IAM + storage integration differ |
| Real Snowflake Data Share (vs. simulated DB) | ⏳ Open | — | Same query shape, different provisioning flow |
| Dagster + OpenLineage | ⏳ Open | — | Self-healing reads Dagster logs; we have none |
| Great Expectations init | ⏳ Open | — | Quality contracts theoretical until GX wired |
| GitHub Enterprise base_url config | ⏳ Open | — | One of six BH-526 gaps; trivially testable once GHE creds arrive |
| Longaeva's *actual* extended YAML spec | ⏳ Blocked | — | Our placeholder is structurally aligned post-meeting; Grant to share theirs by 2026-06-08 |
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

1. ~~**F1 — Synthetic seed**~~ ✅ done 2026-05-30 — sandbox is now end-to-end verifiable; baseline_expectations enforced
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
| 2026-05-29 | YAML restructured into `spec:` / `sdk_extensions:` | Per Grant's meeting: their pipeline strips SDK keywords before Snowflake DDL; the strip boundary must be explicit, not buried in a comment |
| 2026-05-29 | `baseline_expectations` block added | Per Grant's validation harness layer 3 ("auto validation… continue running checks post data refresh"); supports universal invariants + author-supplied dbt-test-style assertions |
| 2026-05-29 | RBAC strict-mode requires `USE SECONDARY ROLES NONE` | KURICHINCA holds ACCOUNTADMIN; without disabling secondary-role auto-activation, the agent boundary is silently bypassed. Test script enforces this; MCP must do the same. |
| 2026-05-29 | `LONGAEVA_AGENT_ROLE` is read-only on GOLD + REF + SEMANTIC | Implements Grant's "scoped subset of user perms" model; agents can serve queries through semantic view but never see BRONZE/SILVER/share or write anything |
| 2026-05-30 | Seed: 1y x 200 issuers x 30 portfolios (~450k rows), not 2y x more | Hits XSMALL warehouse cost ceiling; covers fiscal-quarter trends across 2 cohorts (CALENDAR + NONCAL Apr-Mar); enough rows for cardinality drift testing |
| 2026-05-30 | Seed prices are pure random-walk, not market-correlated | Ingestion + semantic view + RBAC tests don't need realistic correlations; faster to generate; deterministic via RNG_SEED=42 |
| 2026-05-30 | Seed loader uses `snowflake-connector-python.write_pandas` not COPY INTO | Direct table-load is fastest path for our row counts; COPY INTO is exercised separately by the S3 ingestion pattern test |
