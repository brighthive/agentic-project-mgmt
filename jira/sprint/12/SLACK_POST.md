🛠️ BrightHive Sprint 12 Release
Release Date: 2026-06-16
Sprint Period: 2026-06-03 - 2026-06-16

🤖 MCP Integration — dbt agent reachable over MCP
• ✓ Bedrock Converse tool-schema sanitizer — dbt-via-MCP works end-to-end (BH-647)
• ✓ Dedicated brightagent-mcp.{env} ingress + FastMCP on /bh-mcp
• ✓ Webapp connectivity card: live tools/list, JSON-RPC test, prompt playground

📁 BYOW Ingestion (OMD-native AutoPilot)
• ✓ Snowflake + Redshift catalog→embeddings→retrieval verified on staging (171 tables, 333 embeddings)
• ✓ AutoPilot scoped to prod schemas — dbt dev sandboxes excluded (BH-642)
• ✓ Webhook workspace routing by service-name UUID prefix (UAT-verified)

🔧 dbt Agent & Semantic Views
• ✓ Write semantic view back to Snowflake (BH-641)
• ✓ ship_semantic_view_to_github — governed PR + CI compile-check
• ✓ SV lineage: base_tables + join graph (BH-619)

🛡️ Configurable Quality-Rule Library (BH-503 — shipped)
• ✓ 20+ rule templates, CRUD, execution fanout, pass-rate aggregation
• ✓ Webapp: drawer, scope selector, history panel, sparkline

💬 Slack / Notifications / HITL
• ✓ 6 producer stages classified; dbt toolset in thinking indicator
• ✓ HITL input surface for DBT-query_selection interrupts
• ✓ CloudWatch alarms + on-call runbook for notif.* events

🔐 Auth — Okta Federation
• ✓ Cognito + Okta federation for MCP server (BH-573)
• ✓ Route53 + ACM for mcp/auth.brighthive.io (BH-574)

📈 Longitudinal Monitoring (GC-12)
• ✓ Anomaly-detection core + metric-snapshot SQL builder
• …agent wiring in progress (BH-600)

🐛 Production Stability & Security
• ✓ P0 chain: multi-tenant exfil (BH-559), PAT-leak (BH-560), JWT scrub (BH-563), tenant isolation (BH-646)

📊 By the Numbers — two weeks
• PRs Merged: 268 (235 feature/fix across 6 repos)
• Lines Changed: 485,074 (excl. release-carriers) — ~34K/day
• Tickets moved: 46 actively worked
   – 18 live on prod
   – 28 code-complete, shipped to staging / in review (awaiting the pre-trial deploy — done work, not started work)
• Plus 54 follow-up tickets specced & groomed, 7 specs signed off

That's a full BYOW platform — MCP, OMD-native ingestion, dbt agent, semantic-view lifecycle, quality-rule library, Okta federation, longitudinal monitoring — built end-to-end in 14 days.

👥 Team Contributions
• Kuri (drchinca) — 170 PRs 🔥 (MCP, OMD ingestion, dbt/semantic views, Okta federation, security P0s, longitudinal core)
• Marwan — 50 PRs (Slack notifications, HITL, dbt tool surfacing, OAuth invariants)
• Harbour — 13 PRs (quality-rule library FE+BE, profiler, studio guardrails)
• Ahmed — 2 PRs (CDK Snowflake ingestion stack)

🎯 What's Next: Sprint 13 Focus
• Drain the 28-ticket staging-QC pipeline via the Longaeva pre-trial deploy
• Land BH-600 longitudinal agent wiring (closes GC-12)
• Customer Okta tenant handover + BH-533 connectivity validation

⚠️ Sprint Health
• 18 Done, 28 in review/staging-QC ready to land
• Heavy build sprint; 54 follow-up tickets groomed into backlog
• Longaeva PoC narrative tracked separately in the live trial tracker

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/12/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/12/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
