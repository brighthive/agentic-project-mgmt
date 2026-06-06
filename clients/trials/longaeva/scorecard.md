---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "pre-trial"
updated: "2026-06-03"
---

# Longaeva — Trial Scorecard

14-day POC. Start date: **June 2026, exact TBD with Grant**. Days are relative to the agreed start. Updated daily once trial begins.

> **EOD 2026-06-01**: Snowflake integration shipped end-to-end across 4 PRs (brightbot [#488](https://github.com/brighthive/brightbot/pull/488) + [#489](https://github.com/brighthive/brightbot/pull/489), platform-core [#777](https://github.com/brighthive/brighthive-platform-core/pull/777), data-organization-cdk [#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156)). 168 unit tests green. All 7 layers of the warehouse-agnostic pattern Snowflake-compliant. Trial unblocked for §1 ingestion + §2 semantic-view enrollment.
>
> **EOD 2026-06-03**: Self-hosting deployment simplified. Per Matt's 11:29 ET email to Grant/Sumukh, BrightHive committed to ship a **Terraform module as the primary deployment path** for Longaeva (CDK remains as alternative). Trial-guide artifact extended with Path A (Terraform, recommended) + Path B (CDK), plus a uv-based local install section (`uv tool install brighthive` recommended; pip fallback documented). Simplified setup doc + Terraform module due to Longaeva by EOW 2026-06-05. New tickets **BH-584** (TF module — Ahmed), **BH-585** (setup doc — Kuri), **BH-586** (CLI/uv publish — Marwan) created under BH-526. MCP auth-workflow conversation to be held with Grant + Sumukh before Grant's vacation.
>
> **Honest engineering reality (2026-06-03)**: the FS-critical foundation is **open PRs in review, NOT merged** — Snowflake (`brightbot#488`), GHE proxy (`platform-core#778` + `brightbot#490`), P0 security chain (BH-559→565, drafts), Atlas scaffolder (`brightbot#489`, draft). Merged to `develop` so far: MCP server *scaffold* (`brightbot#497` — `invoke_analyst` still a stub), data profiler (`#485/#487`), BrightSignals notif (`#486`). Nothing is deployed to staging/prod. The PoC sandbox (11/11 use cases vs live Snowflake) de-risks the design; it is not the product running.

---

## Milestone Progress

| # | Milestone | Owner | Target | Status | Notes |
|---|---|---|---|---|---|
| 0 | Confirm exact June start date with Grant | Kuri | Pre-Day 1 | 🔲 | Was May 18 in original proposal, slipped to June |
| 1 | Use cases & success criteria confirmed | Joint | Day 1 | 🔲 | Use this scorecard as the contract |
| 2 | System access provisioned | Longaeva | Day 2 | 🔲 | Snowflake, S3, dbt repo, Dagster, GHE, their MCP server |
| 3 | Brighthive environment setup | Brighthive | Day 3 | 🔲 | Workspace + Snowflake connectivity validated |
| 4 | Context layer creation | Brighthive | Day 5 | 🔲 | Pipeline lineage, dbt sources, Snowflake schema, their YAML spec, existing semantic views |
| 5 | Environment mapping validation | Joint | Day 5 | 🔲 | Joint working session, NOT async |
| 6 | Ingestion execution (S3, REST API, Data Share) | Joint | Day 8 | 🔲 | Time-to-PR per source type |
| 7 | Semantic view enrollment + MCP validation | Joint | Day 10 | 🔲 | 1-2 datasets, end-to-end |
| 8 | Automated maintenance demo (deliberate drift event) | Joint | Day 12 | 🔲 | All 4 failure modes demonstrated |
| 9 | Final evaluation | Joint | Day 13 | 🔲 | Fill Success Criteria below |
| 10 | Next steps discussion | Brighthive | Day 14 | 🔲 | Commercial path |

Status: 🔲 Pending / 🔄 In Progress / ✅ Done / ⚠️ Blocked

---

## Success Criteria Scorecard

Filled at Day 13 evaluation (Milestone 9). 17 criteria across 4 core workstreams + 4 bonus.

### 1. Ingestion (3 source types)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 1.1 S3 — Snowflake external stage + dbt `sources.yml` | Merge-ready, ≤1 revision | — | — |
| 1.2 REST API — 20-30k instrument universe, pagination, batched IDs, parallel, retry | dbt source wired correctly | — | — |
| 1.3 Snowflake Data Share — dbt source + staging + DQ contracts | Passes validation on first run | — | — |

### 2. Semantic View Enrollment (grounded in Atlas YAML contract — `artifacts/atlas-semantic-view-spec.md`)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 2.1 YAML dimension/time-dim/fact inference from Silver schema | ≥80% correct first scaffold | — | — |
| 2.2 Atlas custom blocks populated (`dataset_key`, `entities.primary`, `defaults`, `dagster_dep`, `owners`, `custom_instructions`) | All required blocks present + non-empty `custom_instructions` | — | — |
| 2.3 `atlas.target` binding auto-inference | ≥2 of: `lngv_issuer_id`, `bloomberg_ticker`, `period_*`, `metric_attributes.geography.*` | — | — |
| 2.4 `atlas.metric.aggregations` defaulted from fact-name heuristics | counts→sum, prices→avg, percentages→raw | — | — |
| 2.5 `verified_queries[]` in Snowflake `SEMANTIC_VIEW(...)` syntax | ≥1 query per major use case | — | — |
| 2.6 YAML accepted by Atlas SDK (round-trips PyYAML; no DDL emission) | Accepted on first pass | — | — |
| 2.7 Validation via running a `verified_query` end-to-end through MCP | ≤3 revision cycles | — | — |
| 2.8 Errors surface with actionable remediation | All errors human-readable | — | — |

### 3. MCP Validation (Longaeva's internal MCP server)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 3.1 Measures, dimensions, time-dims queryable via their MCP | 100% surface | — | — |
| 3.2 Representative query suite correctness | ≤5% error rate; filtered + aggregated + multi-dim | — | — |
| 3.3 Gap detection in enrollment PR | Sample values / examples / instructions called out | — | — |

### 4a. Self-Healing — must demonstrate all 4 failure modes
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 4a.1 Schema drift from vendor | Surgical fix PR + plain-language diagnosis | — | — |
| 4a.2 Missing partition | Detected + fix PR | — | — |
| 4a.3 Broken external stage | Root cause + corrected DDL PR | — | — |
| 4a.4 dbt contract failure | Contract analyzed + targeted PR | — | — |

### 4b. Longitudinal Anomaly Monitoring
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 4b.1 Row count drift detection | Flagged vs historical baseline | — | — |
| 4b.2 Dimension cardinality breakdown | Flagged with affected dimension named | — | — |
| 4b.3 Distributional skew in numeric metric | Flagged with deviation magnitude | — | — |
| 4b.4 Unexpected nulls in well-populated column | Flagged before downstream impact | — | — |

### 4c. Slack
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 4c.1 Alert triage-ready | Dataset + issue + severity + PR/run link in message | — | — |
| 4c.2 Bidirectional `@brightagent` | Pipeline state Q&A, re-run, scaffold-trigger | — | — |

### Bonus (only if core finishes early)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| B.1 Vendor + dataset registry | Demo on ≥3 active datasets | — | — |
| B.2 Agentic governance walkthrough | Permission model + runaway prevention | — | — |
| B.3 KG subgraph grafting | Instruments / counterparties / vendors on base ontology, MCP-exposed | — | — |
| B.4 Rapid DQ at scale | Auto-generate + maintain test suites as datasets evolve | — | — |

---

## Daily Notes

_Days are filled in once the exact June start date is confirmed with Grant. Template below._

### Day 1 — [DATE]
_Set agenda, confirm success criteria, kick off access provisioning._

### Day 2 — [DATE]
_Access provisioned. First Snowflake connectivity smoke test._

### Day 3 — [DATE]
_Critical context handoff: their YAML spec, reference schemas, fiscal calendar, identifier maps. Joint session._

### Day 4 — [DATE]
### Day 5 — [DATE]
_Environment mapping validated. Context layer build complete._
### Day 6 — [DATE]
### Day 7 — [DATE]
### Day 8 — [DATE]
_Ingestion execution target — 3 source types done._
### Day 9 — [DATE]
### Day 10 — [DATE]
_Semantic view + MCP validation target._
### Day 11 — [DATE]
### Day 12 — [DATE]
_Automated maintenance demo — schedule deliberate drift event upstream._
### Day 13 — [DATE]
_Final evaluation — fill scorecard above._
### Day 14 — [DATE]
_Next steps discussion._

---

## Final Score

_Filled at Day 13._

| Workstream | Criteria Met | Total | Pass Rate |
|---|---|---|---|
| 1. Ingestion | — | 3 | — |
| 2. Semantic Enrollment | — | 8 | — |
| 3. MCP Validation | — | 3 | — |
| 4a. Self-Healing | — | 4 | — |
| 4b. Anomaly Monitoring | — | 4 | — |
| 4c. Slack | — | 2 | — |
| **Core total** | — | **24** | — |
| Bonus | — | 4 | — |

**Recommendation**: Won / Lost / Extended — _rationale here_
