# Sprint 17 🥝 — Slack posts (reference copy)

Posted to `#releases` as four messages: one per person (Kuri first, then each engineer), then a short team wrap with the numbers and links.

---

## Post 1 — Kuri

🥝 BrightHive Sprint 17 Release — Kuri
Sprint Period: Aug 24 – Oct 6, 2026 · Release Date: Oct 6, 2026

🌟 Kuri (drchinca) — authorization, governance, and the agent surface
152 code PRs · 77.9% of the sprint · 7 repos · +84,163 / −4,722

🛡️ Workspace authorization, built and enforced on staging (BH-1464 epic)
• ✓ One `authorize()` decision point — tenant → admin → permission matrix, fail-closed, with matrix cache + race-safe invalidation (BH-1465, BH-1477)
• ✓ Permission matrix stored in Neo4j (ADR-016), editable live in the webapp, with an ABAC access-limit editor and an Access Control tab in Governance (BH-1466, BH-1469, BH-1476, BH-1502)
• ✓ Shadow → enforced rollout: decision telemetry, ADR-0003 verb ramp, `@authorized` default-deny, `checkAccess` GraphQL query, mutation verbs enforced on staging (BH-1467, BH-1468, BH-1472)
• ✓ Cross-tenant holes closed across data-plane reads/writes, Slack resolvers, on-prem jobs, routines, pipelines, catalog sync — plus 16 matrix gaps closed in the default seed (BH-1488, BH-1489, BH-1493–1501, BH-1517–1525)
• ✓ Real-behavior authz suite against staging now gates merges (BH-1518)

🔒 PII masking that holds up to real SQL
• ✓ Lineage-aware masking closes alias and CTE bypasses (BH-1478, BH-1484)
• ✓ Masking on query + parity results, samples, and MIN/MAX (BH-1480, BH-1481, BH-1483)
• ✓ Agent data reads gated on READ DATA_ASSET + sensitivity ABAC; role-aware tool context; `lookup_neo4j` scoped to the caller's workspace (BH-1523, BH-1470, BH-1485)

🔌 Projects over MCP — full lifecycle for any agent client (BH-1181 family)
• ✓ ~20 new MCP tools: list/get/create/update/delete project, status, contents, data-asset links, files/schemas/specs, runs, pipeline authoring + control, access + copy, destinations + governance gates (BH-1546–1551, BH-1571)
• ✓ Govern the platform over MCP (BH-1509); typed error envelopes; stateless HTTP transport (BH-853, BH-856, BH-1581)

📐 Projects 2.0 — spec-driven projects (BH-1255)
• ✓ Spec parser + per-section conformance API and a Spec tab in Projects (BH-1527, BH-1530)
• ✓ dbt WorkflowSpec authoring, staged quality-rule binding, and spec-conformance checks with webhook trigger (BH-1528, BH-1529)
• ✓ Self-healing remediation layers 0–1, project observation-cycle skill, project Skills routing (BH-1505, BH-1533)
• ✓ Workflows surface: project agent actions, review states, mobile review handoff

🩺 Health that never claims more than it knows
• ✓ Stale or unprobed health reports Unknown, end to end in core + webapp (BH-1555, BH-1559)
• ✓ Watchdog heartbeat + Redshift/Postgres liveness; fleet health stops reporting healthy with no monitors (BH-1557, BH-1560, BH-1562)
• ✓ New `source_connection_unreachable` signal through core + Slack (BH-1558)

🧾 Audit, routines, and warehouses
• ✓ Every GraphQL mutation and every HTTP write is now audited automatically (BH-1579, BH-1580)
• ✓ Owner-or-admin guard on schedule edit/run, locked controls for non-owners, ROUTINE permission kind (BH-1564, BH-1566, BH-1567, BH-1572)
• ✓ Snowflake key-pair auth for MFA-enforced accounts (BH-1535)
• ✓ Neo4j post-reboot incident resolved — no data lost (BH-1539)

---

## Post 2 — Marwan

🥝 BrightHive Sprint 17 Release — Marwan
Sprint Period: Aug 24 – Oct 6, 2026

👤 Marwan (Marwan-Samih-Brighthive) — catalog search, multi-warehouse, and the production release
27 code PRs · 3 repos · +28,670 / −2,845 (excludes the regenerated OGM types file)

🔎 Catalog search
• ✓ Async, hierarchy-aware Redis vector index pipeline in platform-core, enriched with fields + warehouse context
• ✓ Read-only vector search in BrightAgent with optional `@` scoping
• ✓ Warehouse-aware Data Catalog (new) view with a multi-warehouse hierarchy tree, behind a feature flag

🏭 Multi-warehouse routing
• ✓ Asset-scoped multi-warehouse SQL routing — each query goes to the warehouse that owns the asset
• ✓ Background jobs routed to the asset's warehouse; routing fields on catalog assets
• ✓ Warehouse upsert validates secrets and merges node defaults; Redshift verify-connection + schema collection

📐 Projects 2.0 — from spec to running pipeline
• ✓ Spec author, conversational project bootstrap, and pipeline verifier
• ✓ Project 2.0 spec API + apply pipeline + smoke validation
• ✓ Spec tab, pipeline canvas, verify-pipeline, and catalog sync in the webapp
• ✓ dbt engineering pipeline specs, propose path, run diagnostics, run reconciliation, and run-history UX

🚀 Production release — Sep 30
• ✓ Drove the Staging → Production promotion across brightbot, platform-core, and webapp
• ✓ Production GraphQL cutover to ECS, Cognito MCP auth domain kept off prod, UserPool deploy recovered, CI env fixed
• ✓ Recovered the webapp promotion cleanly after a revert

---

## Post 3 — Harbour

🥝 BrightHive Sprint 17 Release — Harbour
Sprint Period: Aug 24 – Oct 6, 2026

👤 Harbour (Nano-233) — Brighthive speaks Spanish and Portuguese, and pipelines run on schedule
16 code PRs · 3 repos · +39,553 / −9,099 (mostly translation catalogs)

🌍 Internationalization
• ✓ Full UI in English, Spanish, and Portuguese
• ✓ BrightAgent stream status and output panel translated
• ✓ Workspace locale persisted; quality-check reports written in the workspace's language
• ✓ Language switcher on the login screen

⏰ Pipeline scheduling
• ✓ Schedule a project pipeline straight from chat, independent of dbt
• ✓ Scheduler runs in-process — no self-URL env, fixed on production
• ✓ Pipeline list/schedule/runs requests routed to the right agent
• ✓ Human-readable cadence and project labels on schedules

🧹 Everyday reliability
• ✓ Log out stays visible in an overflowing user menu
• ✓ Session list refreshes after delete; shared-link revoke asks first and reports failures
• ✓ Catalog shows a real load error instead of an empty "no match" grid
• ✓ One clear message on login failure — no raw Cognito errors, no duplicate toasts

---

## Post 4 — Team wrap

🥝 Sprint 17 — Team Wrap
Sprint Period: Aug 24 – Oct 6, 2026 · Release Date: Oct 6, 2026

📊 By the Numbers
• Code PRs Merged: 195 (+59 release/promotion)
• Code Lines: +152,386 / −16,666 (excludes release re-merges and one regenerated OGM types file)
• Repos Touched: 7 (brightbot, platform-core, webapp, e2e, slack-server, agentic-project-mgmt, platform-saas-ai-context)
• 🚀 Staging → Production promotion shipped Sep 30 across brightbot, platform-core, webapp

⚠️ Sprint Health
• Sixth unofficial (date-range) sprint in a row — no Jira sprint object
• Only 4 tickets transitioned to Done in 6 weeks against 195 code PRs; 35 sit in Testing (Dev), 46 in Needs Refinement
• Marwan's and Harbour's PRs carry no Jira keys — their work is invisible on the board
• Kuri authored 77.9% of code PRs (up from 75.2%)

🎯 What's Next: Sprint 18 Focus
• Ticket sweep: move the 35 Testing (Dev) authz/PII tickets to Done or Ready for Production
• Promote BH-1464 enforcement and project MCP tools from staging to production
• Every PR gets a `BH-XXX` in the branch or title — no exceptions

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/17/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/17/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
