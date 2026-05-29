---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "trial"
updated: "2026-05-26"
---

# Longaeva — Trial Scorecard

14-day POC: May 26 – Jun 9, 2026. Updated daily.

---

## Milestone Progress

| # | Milestone | Owner | Target | Status | Notes |
|---|---|---|---|---|---|
| 1 | Use cases & success criteria confirmed | Joint | Day 1 | 🔲 | |
| 2 | System access provisioned | Longaeva | Day 2 | 🔲 | Snowflake, S3, dbt, GHE, MCP server |
| 3 | Brighthive environment setup | Brighthive | Day 3 | 🔲 | |
| 4 | Context layer creation | Brighthive | Day 5 | 🔲 | |
| 5 | Environment mapping validation | Joint | Day 5 | 🔲 | |
| 6 | Ingestion execution (3 patterns) | Joint | Day 8 | 🔲 | |
| 7 | Semantic view enrollment + MCP validation | Joint | Day 10 | 🔲 | |
| 8 | Automated maintenance demo | Joint | Day 12 | 🔲 | |
| 9 | Final evaluation | Joint | Day 13 | 🔲 | |
| 10 | Next steps discussion | Brighthive | Day 14 | 🔲 | |

Status: 🔲 Pending / 🔄 In Progress / ✅ Done / ⚠️ Blocked

---

## Success Criteria Scorecard

Updated at Day 13 evaluation (Milestone 9).

### Ingestion
| Criterion | Target | Result | Pass |
|---|---|---|---|
| S3 pipeline merge-ready | ≤1 revision | — | — |
| REST API pagination + retry | Correct for instrument universe | — | — |
| Snowflake Data Share validation | Passes on first run | — | — |

### Semantic View Enrollment
| Criterion | Target | Result | Pass |
|---|---|---|---|
| YAML dimension/metric inference | ≥90% correct | — | — |
| Reference join detection | At least 1 dataset auto-resolved | — | — |
| Compile + execute on Snowflake | No errors on first run | — | — |

### MCP Validation
| Criterion | Target | Result | Pass |
|---|---|---|---|
| Queryability through their MCP | All measures + dimensions surfaced | — | — |
| Query suite correctness | ≤5% error rate | — | — |
| Gap detection | Surfaced automatically in PR | — | — |

### Automated Maintenance
| Criterion | Target | Result | Pass |
|---|---|---|---|
| Schema drift detection → PR | Same pipeline run cycle | — | — |
| PR is surgical | Not a rewrite, has plain-language diagnosis | — | — |
| Longitudinal anomaly signal | ≥1 signal during trial | — | — |
| Slack alert quality | Triage-ready without leaving Slack | — | — |

---

## Daily Notes

### Day 1 — May 26, 2026
_Add notes here_

### Day 2 — May 27, 2026
_Add notes here_

### Day 3 — May 28, 2026
_Add notes here — critical context handoff day_

### Day 4 — May 29, 2026

### Day 5 — May 30, 2026

### Day 6 — Jun 1, 2026

### Day 7 — Jun 2, 2026

### Day 8 — Jun 3, 2026
_Ingestion execution target_

### Day 9 — Jun 4, 2026

### Day 10 — Jun 5, 2026
_Semantic view + MCP validation target_

### Day 11 — Jun 6, 2026

### Day 12 — Jun 7, 2026
_Automated maintenance demo_

### Day 13 — Jun 8, 2026
_Final evaluation — fill scorecard above_

### Day 14 — Jun 9, 2026
_Next steps discussion_

---

## Final Score

_Filled at Day 13._

| Workstream | Criteria Met | Total | Pass Rate |
|---|---|---|---|
| Ingestion | — | 3 | — |
| Semantic Enrollment | — | 3 | — |
| MCP Validation | — | 3 | — |
| Automated Maintenance | — | 4 | — |
| **Total** | — | **13** | — |

**Recommendation**: Won / Lost / Extended — _rationale here_
