# Sprint 17 🥝 — Summary (Aug 24 – Oct 6, 2026)

> Unofficial date-range cut — sixth in a row, no Jira sprint object. Previous release:
> Sprint 16 🍓 (Aug 17–23, Slack-only). This sprint is written per person: Kuri first,
> then each engineer.

```
┌──────────────────────────────────────────────────────────────┐
│ SPRINT 17 🥝 — Aug 24 → Oct 6, 2026 (44 days, unofficial)     │
├──────────────────────────────┬───────────────────────────────┤
│ PRs merged                   │ 254 (195 code + 59 carriers)  │
│ Code lines                   │ +218,197 / −53,750            │
│   excl. generated OGM types  │ +152,386 / −16,666           │
│ Repos touched                │ 7                             │
│ Production release           │ Sep 30 (bot, core, webapp)    │
│ Tickets → Done in window     │ 4                             │
│ Tickets referenced by PRs    │ 98 (all Kuri-owned)           │
│ Story points                 │ not estimated                 │
├──────────────────────────────┼───────────────────────────────┤
│ Kuri                         │ 152 PRs · 77.9%               │
│ Marwan                       │  27 PRs · 13.8%               │
│ Harbour                      │  16 PRs ·  8.2%               │
└──────────────────────────────┴───────────────────────────────┘
```

## Per person

### 🌟 Kuri (drchinca) — 152 code PRs · 7 repos · +84,163 / −4,722

| Theme | What shipped | Tickets |
|---|---|---|
| 🛡️ Workspace authorization | One `authorize()` decision point (tenant → admin → matrix, fail-closed), Neo4j permission matrix (ADR-016), live matrix + ABAC editor, shadow → enforced ramp (ADR-0003), `@authorized` default-deny, `checkAccess` query, cross-tenant holes closed across data plane / Slack / on-prem / routines / pipelines, real-behavior authz suite gating merges, mutation verbs enforced on staging | BH-1464 epic: BH-1465–1477, BH-1488–1502, BH-1517–1525 |
| 🔒 PII masking | Lineage-aware masking (alias + CTE bypasses closed), masking on query/parity/sample/MIN-MAX, injectable masking transport, READ DATA_ASSET + sensitivity ABAC on agent reads, workspace-scoped `lookup_neo4j`, workspace verified before secret probe | BH-1470, BH-1473, BH-1478–1485, BH-1523 |
| 🔌 Projects over MCP | ~20 project lifecycle tools (CRUD, status, contents, assets, files/schemas/specs, runs, pipeline authoring + control, access/copy, destinations + governance gates), governance over MCP, typed error envelopes, stateless HTTP transport | BH-1509, BH-1546–1552, BH-1571, BH-1581, BH-853/856/804 |
| 📐 Projects 2.0 | Spec parser + per-section conformance + Spec tab, dbt WorkflowSpec authoring, staged quality-rule binding, spec-conformance check, self-healing remediation layers 0–1, observation-cycle skill, workflows primitives in webapp | BH-1255: BH-1505, BH-1527–1534 |
| 🩺 Honest health | Unknown for stale/unprobed health, watchdog heartbeat, Redshift/Postgres liveness, no false-healthy fleet, `source_connection_unreachable` signal, live MCP reachability probe | BH-1036: BH-1555–1563, BH-1373 |
| 🧾 Audit + routines | Automatic audit of every GraphQL mutation + HTTP write, owner-or-admin schedule guard + UI lock, ROUTINE permission kind, persisted detector scores | BH-1564–1567, BH-1572, BH-1579, BH-1580, BH-950 |
| 🏭 Warehouses + ops | Snowflake key-pair auth (MFA), warehouse-listing tool, renameWorkspaceAsAdmin, on-prem lineage → data products, Neo4j reboot incident, local-against-staging runbook hardening, spec roadmap guard | BH-1535, BH-1454, BH-1453, BH-1434/1444, BH-1539, BH-1553 |

### 👤 Marwan (Marwan-Samih-Brighthive) — 27 code PRs · 3 repos · +28,670 / −2,845 (excl. generated OGM types)

| Theme | What shipped |
|---|---|
| 🔎 Catalog search | Async hierarchy-aware Redis vector index (core), read-only vector search with `@` scope (brightbot), warehouse-aware Data Catalog (new) view + hierarchy tree (webapp, flagged) |
| 🏭 Multi-warehouse | Asset-scoped multi-warehouse SQL routing, background jobs to the asset's warehouse, routing fields on assets, secret validation on upsert, Redshift verify + schema collection |
| 📐 Projects 2.0 | Spec author + conversational bootstrap + pipeline verifier, spec API + apply pipeline + smoke validation, spec tab + pipeline canvas, dbt engineering pipeline specs + propose path + run diagnostics + run reconciliation + run-history UX |
| 🚀 Production | Led the Sep 30 Staging → Production promotion; prod GraphQL ECS cutover; Cognito MCP domain gated off prod; CI env fix; clean recovery after a webapp revert |

### 👤 Harbour (Nano-233) — 16 code PRs · 3 repos · +39,553 / −9,099 (mostly translation catalogs)

| Theme | What shipped |
|---|---|
| 🌍 Internationalization | Full UI in English, Spanish, Portuguese; translated BrightAgent stream status; persisted workspace locale; localized QC reports; login language switcher |
| ⏰ Pipeline scheduling | Chat-configurable project pipeline scheduling (decoupled from dbt), in-process scheduler fixed on prod, lifecycle routing to the dbt agent, human-readable cadence |
| 🧹 Reliability | Log-out visibility, session refresh after delete, shared-link revoke confirm, catalog load error vs empty grid, single login-failure message, no raw Cognito errors |

### Ahmed

No merged PRs and no Jira activity in this window.

## PR ↔ ticket linkage

| Author | Code PRs | With `BH-XXX` | Without |
|---|---|---|---|
| Kuri | 152 | 147 | 5 |
| Marwan | 27 | 0 | 27 |
| Harbour | 16 | 0 | 16 |

The 98 tickets referenced by PRs sit at: 35 Testing (Dev) · 3 Ready for Staging · 4 Code Review ·
1 Staging QC · 1 In Progress · 5 To Do · 46 Needs Refinement · 5 Done.

## Problems identified

1. **Board is not the source of truth.** 4 tickets reached Done in 6 weeks against 195 code PRs and a production release.
2. **43 engineer PRs have no ticket.** Marwan's and Harbour's work — catalog search, multi-warehouse, i18n, the prod release — is invisible in Jira.
3. **Concentration rising.** Kuri authored 77.9% of code PRs (75.2% in Sprint 15, 69.5% in Sprint 14).
4. **Sixth unofficial sprint.** Velocity is reconstructed from PRs, never planned.
5. **Production promotion was bumpy.** Webapp promotion reverted and re-applied; four follow-up PRs to land the prod GraphQL ECS cutover.

## Recommendations

1. 30-minute ticket sweep: move the 35 Testing (Dev) authz/PII tickets to their real state; close the BH-1464 children that are enforced on staging.
2. Create tickets retroactively for Marwan's catalog-search, multi-warehouse, and Projects 2.0 work and Harbour's i18n + scheduling — parent them under the right epics.
3. Enforce `BH-XXX` in branch or title at PR open (CI check), not at release time.
4. Open a real Jira sprint object for Sprint 18.
5. Write a short promotion runbook from the Sep 30 release — revert + four cutover fixes are the lessons.
6. Promote BH-1464 enforcement and the project MCP tools from staging to production.
