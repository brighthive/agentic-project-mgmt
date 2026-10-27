# Clients

Master index of all leads, active trials, and paying customers.

For navigation rules and integration wiring, see `CLAUDE.md`.
For client architecture profiles and capability maps, see `../platform-saas-ai-context/clients/`.

---

## Active Trials

| Prospect | Champion | Trial Window | Jira Epic | Status |
|---|---|---|---|---|
| [Longaeva Partners](trials/longaeva/overview.md) | Grant Langseth | May 26 – Jun 9, 2026 | [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) | Active |
| [Loop Capital](trials/loopcapital/overview.md) | Frank Sung | MVP trial goal passed → vendor evaluation for a paid co-build ([fit](trials/loopcapital/GOVERNANCE_REQUIREMENTS_FIT.md)); phase 1 = [AI agent governance](trials/loopcapital/PHASE1_GOVERNANCE.md); working session 2026-10-21 | Phase-1 epic proposed ([alignment](ALIGNMENT_2026-10.md)); data-engineering work (BH-1036, BH-1245) is next phase | Active |
| [Nestlé Global](trials/nestle/overview.md) | To confirm | Six weeks; target Nov 15, 2026, January fallback (years provisional); [Azure private deployment](trials/nestle/AZURE_ARCHITECTURE.md) | Epics proposed ([alignment](ALIGNMENT_2026-10.md)); none in Jira yet | Preparation; dates/scope to confirm |
| [Safe-Guard Products International](trials/safe-guard/overview.md) | To confirm | To confirm; technical evaluation / trial | None yet (required before Day 1) | Snowflake governance and metadata monitoring |

---

## Leads

| Prospect | Champion | First Contact | Qualification | Next Step |
|---|---|---|---|---|
| [ACG](leads/acg/overview.md) | John Sutton (CTO) | July 2026 | Technical champion engaged; budget, timeline and environment open | Confirm demo outcome and Azure-tenant rule, then pick one vendor feed ([roadmap](leads/acg/roadmap.md), [tickets](leads/acg/tickets.md), epic [BH-1658](https://brighthiveio.atlassian.net/browse/BH-1658)) |
| [TransUnion](leads/transunion/overview.md) | To confirm | To confirm | Discovery / demo planning | Semantic and knowledge layer for enterprise agents |
| [OCC](leads/occ/overview.md) | To confirm | To confirm | Introductory; meeting being scheduled | Data engineering workflows, multi-agent harness |
| [Colibri Group (Calibri)](leads/colibri-group/overview.md) | To confirm | To confirm | Evaluation, pricing and ROI | Data engineering automation and stack optimization |
| [Cooperators](leads/cooperators/overview.md) | To confirm | To confirm | Discovery; potential POC | Data governance, quality, observability, self-healing |
| [Sabin](leads/sabin/overview.md) | To confirm | To confirm | Paid POC proposal | InterSystems IRIS, unified records, self-healing pipelines |

---

## Active Customers

| Customer | Workspace ID | AWS Account | Contract Start | Owner |
|---|---|---|---|---|
| [Virginia DSS / Virginia Works](active/virginia-dss/overview.md) | _(DynamoDB)_ | _(DynamoDB)_ | To confirm | UAT / integration; Workforce Data Trust and historical data preparation |
| [Indiana Tech](active/indiana-tech/overview.md) | _(DynamoDB)_ | _(DynamoDB)_ | To confirm | Production migration planning; owner to confirm |

> Live account data lives in DynamoDB `AdminConfig` (PROD account `104403016368`).
> See `../platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md` for the full registry.

---

## Archive

Won and lost trials move to `archive/` once closed. See `archive/` folder.
