🍑 BrightHive Sprint 15 Release
Release Date: August 17, 2026
Sprint Period: August 2 - August 17, 2026

🏭 On-Prem Engineering Runner
• ✓ Governed connection principals on the Loop Capital sandbox — scoped reader + write-confined engineer (BH-1418)
• ✓ Multi-database sandbox — OMS + TradeDW alongside LoopCapitalAM (BH-1419)
• ✓ MCP plugin runs dbt locally against the sandbox, governed as the scoped engineer, never sa (BH-1422/1423)
• ✓ Legacy SSIS/SSRS reads straight from the customer's filesystem (BH-1429)
• ✓ Artifact sync — local dbt run results flow back into platform-core lineage (BH-1425)
• Windows Server 2019 packaging + outbound-only transport ready for staging (BH-1427/1426)

🗄️ Warehouse Identity & Multi-Database Targeting
• ✓ Register, verify, and list databases for a connected warehouse
• ✓ Default-warehouse badge + admin set-default action
• ✓ Name a warehouse and database with @ in the main chat, including names with spaces
• ✓ MCP callers choose which warehouse connection to target (BH-1430)

🔔 Routines & Notification Provenance
• ✓ Per-routine delivery target passthrough + delivered-channel chip
• ✓ Executed SQL and artifact link threaded straight into Slack
• ✓ Remediation-PR and fleet-health digest render as reviewable cards

🚀 Infra & Stability
• ✓ GraphQL Core cut over to ECS/CloudFront runtime for staging
• ✓ Neo4j pool hardening — unified driver, fail-fast 503s, catalog pool-storm fix
• ✓ BrightAgent live SSE token streaming in the chat bubble

📊 By the Numbers
• Tickets Completed: 8 / 9 (1 Canceled)
• PRs Merged: 181 (153 code + 28 release/promotion)
• Lines Changed: +87,472 / -44,270 (code only)
• Repos Touched: 8 (platform-core, webapp, brightbot, slack-server, data-organization-cdk, agentic-project-mgmt, e2e, platform-saas-ai-context)
• Engineering Days: 16

👥 Team Contributions
• Kuri — 115 code PRs across 7 repos (On-Prem Runner, warehouse identity, routines delivery)
• Marwan — 19 code PRs (ECS GraphQL cutover, Neo4j hardening, catalog sync)
• Harbour — 19 code PRs (project-activation pipeline, BrightAgent SSE streaming, dbt-agent resilience)

🎯 What's Next: Sprint 16 Focus
• Close the On-Prem Runner epic — land Windows packaging + outbound transport, finish the real-behavior e2e (BH-1428)
• Open a formal Jira sprint object — fifth unofficial sprint in a row
• Sweep ~145 un-linked code PRs to retroactively transition their tickets

⚠️ Sprint Health
• Completion: 88.9% of resolved tickets Done
• 5 tickets carrying over to Sprint 16, all On-Prem Runner sub-tasks
• PR-to-ticket linkage gap is total this window — only the On-Prem Runner epic has Jira coverage

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/15/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/15/MARKETING_RELEASE_NOTES.md
📊 Notion Sprint 15: https://app.notion.com/p/3bf02437dde4817da0ddd88f5226ee2b
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
