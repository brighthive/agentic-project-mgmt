# Sprint 15 🍑 — BrightHive Release Notes (Aug 2–17, 2026)

## 🏭 On-Prem Engineering Runner — Loop Capital's dbt Plugin Goes Governed

The on-prem autonomous dbt lifecycle moved from prototype to something a
customer can actually install: an outbound-only job queue (no inbound port
ever opens on the customer network), a governed sandbox with a
scoped-reader/write-confined-engineer connection split (never `sa`), a
multi-database sandbox spanning OMS + TradeDW alongside LoopCapitalAM, legacy
SSIS/SSRS reads straight from the customer's filesystem, and dbt run
artifacts syncing back into platform-core lineage automatically. Windows
Server 2019 packaging and the outbound transport are staged and ready; the
full real-behavior end-to-end (MCP client → plugin → dbt Core → SQL Server →
lineage) is the one thing left before this epic closes. (BH-1403, BH-1421,
BH-1414/1418/1419/1422/1423/1425/1429/1430)

## 🗄️ Warehouse Identity — Name It, Verify It, Default It

A connected warehouse is now a first-class thing with a name and a state:
register it, verify the connection, see every database it can reach, and
pick which one is the default. In chat, `@warehouse` mentions now resolve
warehouses *and* databases by name — including names with spaces — and MCP
callers can target a specific warehouse instead of always hitting the
default. The webapp's warehouse table went from a cramped list to an
expandable, readable view with per-warehouse host and health context.
(BH-1362, BH-1430, BH-1432, BH-1439, BH-1440, BH-1441, BH-1443, BH-1446, BH-1447)

## 🔔 Routines & Notifications — Show Your Work

Scheduled routines now carry their delivery target end to end and show it —
a picker on the webapp, a delivered-channel chip, and the actual SQL that ran
plus a link to the artifact, landing directly in the Slack channel that asked
for it. Remediation PRs and fleet-health digests render as reviewable cards
instead of plain text, and drift/value-spike signals sync into the shared
Signal Catalog so severity and copy stay consistent everywhere they surface.
(BH-1331, BH-1333, BH-1334, BH-1340, BH-1346, BH-1348, BH-1397, BH-1398, BH-1399, BH-1400, BH-1401, BH-1402)

## 🚀 Infra — GraphQL Core Moves to ECS

The GraphQL API cut over to an ECS/CloudFront runtime in staging, with S3
trust sync and Lambda IAM parity carried across. The migration surfaced a
run of Neo4j connection-pool issues under the new topology — all closed this
window: a unified driver with a per-Lambda pool cap, fail-fast 503s instead
of silent hangs, and OpenMetadata enrichment concurrency capped to stop
catalog pool storms.

## 🎨 Product Surface — Streaming Chat & Project Activation

BrightAgent's chat bubble now streams tokens live over SSE instead of
waiting for a full response. Project activation checks run automatically the
moment a project flips to ACTIVE, with the result surfaced as a signal, a
toast, an inbox thread, and a Slack card — the same event, four surfaces,
one source of truth. The dbt agent got a round of resilience fixes: recovered
macro bodies, GitHub commit resolution from staged/artifact state, and a
4x increase to the ReAct model's token budget to stop mid-file truncation.

## 📊 By the Numbers

- **Tickets Resolved**: 8 Done, 1 Canceled (9 total) — 5 more carrying to Sprint 16
- **PRs Merged**: 181 (153 code, 28 release/promotion)
- **Lines Changed**: +87,472 / −44,270 (code only)
- **Repos Touched**: 8 (platform-core, webapp, brightbot, slack-server, data-organization-cdk, agentic-project-mgmt, e2e, platform-saas-ai-context)
- **Engineering days**: 16 (Aug 2–17)

## 👥 Team Contributions

- **Kuri** — 115 PRs across 7 repos: On-Prem Engineering Runner, warehouse identity, routines delivery
- **Marwan** — 19 PRs: ECS GraphQL cutover, Neo4j pool hardening, catalog sync
- **Harbour** — 19 PRs: project-activation pipeline, BrightAgent SSE streaming, dbt-agent resilience

## ⚠️ Sprint Health

- Completion: 88.9% of resolved tickets Done (8/9)
- 5 tickets carrying to Sprint 16, all On-Prem Runner sub-tasks
- Fifth unofficial (no formal Jira sprint object) release in a row
