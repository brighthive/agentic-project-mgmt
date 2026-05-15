🚀 BrightHive Sprint 10 Release
Release Date: May 15, 2026
Sprint Period: May 5 – May 15, 2026 (11 days, unofficial date-range cut)

🔥 HEADLINE: AWS Bedrock AgentCore Migration Plan — Locked In
• ✓ Spec v2 written + merged after 4-agent review (Solutions Architect, DevOps, AWS, BrightHive-AWS)
• ✓ Epic BH-453 created in Jira with 23 child tickets (BH-454 → BH-476)
• ✓ Target: June 1 AWS co-sell launch — "Deployed on AWS" badge unlock
• ✓ MCP servers on ECS Fargate (NOT Lambda — stdio constraints)
• ✓ CDK stacks in brighthive-platform-core (matches existing {Env}-BPC-* convention)
• ✓ CI/CD mirrors platform-core release-tag pattern (Staging + Production only, develop is off)

🎨 BrightStudio — Major Information Architecture Overhaul
• ✓ The Hive — new central hub for the BrightHive data fabric (BH-376)
• ✓ Governance section — quality, access, audit unified
• ✓ Notifications Inbox — dedicated home for BrightSignals deliveries
• ✓ 8-section navigation redistribution — clean structure, no new pages
• ✓ Asset Detail Profiler tab + Raw JSON view
  → webapp PRs #1087 (+4261), #1088 (+4124), #1091, #1097 (+675), #1098 (+5309), #1085

🔔 BrightSignals — Unified Activity Drawer + Notifications Spec (BH-409)
• ✓ Unified activity drawer in BrightStudio
• ✓ Notifications schema grounded in real BrightHive architecture
• ✓ Foundation for Teams + Email channel adapters next sprint

🤖 dbt — Multi-Repo + AWS Secrets Manager Credentials
• ✓ dbt multi-repo preview — BrightAgent works across multiple GitHub repos per workspace
• ✓ dbt Cloud credentials moved to AWS Secrets Manager (no more env vars)
• ✓ Per-session GitHub repo settings in BrightAgent
• ✓ Re-enable disabled GitHub repos
  → brightbot #470 (+11990/-3413), #478, platform-core #768 (+1960), #761, webapp #1089

⏰ Scheduler MVP — 4 Rounds of Webhook Hardening
• ✓ Scheduler webhook fix
• ✓ LangGraph webhook wiring
• ✓ Payload corrections
• ✓ Task graph returns results
• ✓ Stateful task results in platform-core
  → brightbot #463, #469, #472, #474, platform-core #759

📊 Analytics — Health Checks Wired to Real GraphQL Data (BH-359)
• ✓ ServiceHealthCheck GraphQL type + resolver landed in platform-core
• ✓ Webapp Health Checks page reads live data instead of mock fixtures

🧱 Local Dev Stack — LocalStack for Quality Check
• ✓ Full local quality_check stack with Postgres + LocalStack
• ✓ Iterate on AWS-adjacent behavior without burning Bedrock quota

📝 Sprint 9 Close + Bedrock Diary Catch-Up
• ✓ Sprint 9 v2 release artifacts (post May-4 cutoff, 10 retro tickets) committed
• ✓ 6 Bedrock weekly diary docs published to AWS-shared Drive (Weeks 6-11)

🐛 Production Stability + Quality
• ✓ Today's hotfix (May 15) — production BrightAgent S3 streaming Mem0 (brightbot #483)
• ✓ AG Grid sidebar aria layout (webapp #1103)
• ✓ Project retrieval bug (platform-core #764)
• ✓ Duplicate data asset hotfix (platform-core #757)
• ✓ Enhanced OMD VPC + security groups (platform-core #758)
• ✓ Airbyte destination retrieval fallback (platform-core #756)
• ✓ UI + permission bug fixes (webapp #1096)
• ✓ LangGraph state channel reducers (brightbot #476)
• ✓ Ingestion stack metadata cleanup (data-org-cdk #155)

📊 By the Numbers
• Feature PRs Merged: 34
• Total PRs (incl. promotions + reverts): 58
• Lines Changed: 246,430 (+161,890 / -84,540)
• Repos Touched: 5 (brightbot, webapp, platform-core, data-org-cdk, agentic-pm)
• Major Capabilities Shipped: 10
• AgentCore Epic: 1 (BH-453, 23 child tickets for AWS partnership visibility)

👥 Team Contributions
• Kuri — 14 feature PRs (AgentCore spec + epic, BrightStudio IA, BrightSignals, Analytics, profiler, local-dev stack, Bedrock diary)
• Marwan — 10 feature PRs (dbt enhancement +11990, Secrets Manager creds, session settings, deploy promotions, May 15 hotfix, AG Grid)
• Harbour — 8 feature PRs (scheduler hardening x4, project retrieval, permission/UI fixes)
• Ahmed — 4 feature PRs (OMD VPC + SGs, airbyte fallback, duplicate dataasset hotfix, ingestion stack cleanup)

🎯 What's Next: Sprint 11 Focus
• AgentCore migration execution — BH-454 spike + BH-468 Cognito Lambda first (unblocks 13 child tickets)
• AgentCore CDK stacks {Env}-BPC-AgentCore + {Env}-BPC-AgentCoreMCP
• BrightSignals Teams + Email channel adapters
• Scheduler v1 (post-bug-bash) — retry policies, cron, audit log
• Settings overhaul Phases 1-3 (BH-491, BH-492, BH-493)
• June 1 launch readiness review with AWS Bedrock team

✅ Sprint Health
• Engineering output high — 34 feature PRs across 5 repos in 11 days, full team active
• Fast production feedback loop — 5/12 brightbot deploy-detect-rollback-fix-redeploy in 24h, 5/15 same-day hotfix
• Scheduler MVP firmed up through 4 rounds of iterative webhook hardening — Sprint 11 v1 (retry + cron + audit) ready
• AgentCore migration planning complete — spec v2 merged, 23-ticket execution plan in Jira for AWS visibility

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/MARKETING_RELEASE_NOTES.md
🔍 Validation Report: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/VALIDATION_REPORT.md
🔥 AgentCore Epic BH-453: https://brighthiveio.atlassian.net/browse/BH-453
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
