---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "pre-trial"
updated: "2026-05-29"
---

# Longaeva — Trial Scorecard

14-day POC. Start date: **June 2026, exact TBD with Grant**. Days are relative to the agreed start. Updated daily once trial begins.

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

### 2. Semantic View Enrollment
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 2.1 YAML dimension/time-dim/fact/metric inference | ≥80% correct first scaffold | — | — |
| 2.2 Custom metadata blocks populated (metric-store, filters, instructions, examples) | Against Longaeva's extended spec | — | — |
| 2.3 Reference join auto-detection | ≥2 of 3 types: fiscal calendar / LEI-FIGI / geo | — | — |
| 2.4 Compile + execute on Snowflake semantic engine | ≤3 revision cycles | — | — |
| 2.5 Errors surface with actionable remediation | All errors human-readable | — | — |

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
| 2. Semantic Enrollment | — | 5 | — |
| 3. MCP Validation | — | 3 | — |
| 4a. Self-Healing | — | 4 | — |
| 4b. Anomaly Monitoring | — | 4 | — |
| 4c. Slack | — | 2 | — |
| **Core total** | — | **21** | — |
| Bonus | — | 4 | — |

**Recommendation**: Won / Lost / Extended — _rationale here_
