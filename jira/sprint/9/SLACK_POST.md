📡 BrightHive Sprint 9 Release (v2)
Release Date: May 4, 2026
Sprint Period: April 20 – May 4, 2026 (14 days, full planned window)

🔔 BrightSignals — Proactive Notifications (NEW PRODUCT SURFACE)
• ✓ Multi-tenant Slack auth, mention filter, async handlers, file attachments
• ✓ Subscriptions + poller + delivery infrastructure
• ✓ S3:// URI artifact handoff (Tier A) + <BH_ARTIFACTS> envelope parser (Tier B)
• ✓ Notification dispatcher Lambda — EventBridge + DynamoDB streams (BH-412)
• ✓ Asset UUID surfaced in Slack, operator install + ops guide
• ✓ BrightSignals product rebrand on operator surfaces

🎨 BrightStudio Skills — NEW MAJOR FEATURE (BH-445)
• ✓ Skills as first-class composable agent capabilities
• ✓ Webapp UI for Skill creation + persona attachment
• ✓ Brightbot runtime loads + uses Skills at execution time
  → Major BH-260 BrightStudio epic addition. Foundation for Skills marketplace.

🤖 Bedrock Converse Migration (BH-446)
• ✓ ChatBedrock → ChatBedrockConverse + deepagents framework upgrade (brightbot #457)
  → Foundation step for the LangGraph → Bedrock AgentCore migration

⏰ Task Scheduler MVP + UI Fixes + Result Display (BH-443, BH-444, BH-448)
• ✓ Agnostic scheduler service in platform-core
• ✓ Schedule UI in webapp (analytics + scheduler) with bug fixes
• ✓ Brightbot agent integration
• ✓ Scheduled run result display

📈 UAT Evals + Vega-Lite Visualization (NEW, May 4)
• ✓ Direct-call deterministic turn evals + HTTP scenario runner (slack-server #23)
• ✓ Render Vega-Lite to PNG, emit artifact envelope Tier B (brightbot #456)
  → Charts now flow end-to-end from BrightAgent to Slack

🧱 Streaming Platform Hardening (7 tickets — Kuri)
• ✓ FSM repair, STABILIZED reachable + linear guards (BH-437)
• ✓ Removed prototype "[refined]" placeholder from prod path (BH-438)
• ✓ Py 3.14 compliance + deduplicate SpanStreamProcessor (BH-439)
• ✓ Wire SpanStreamProcessor into suite + SSE ordering invariants (BH-440)
• ✓ Hypothesis property tests + clock injection — killed 21s of time.sleep (BH-441)
• ✓ Neo4jGraphStore + BrightHivePlatformAdapter + Cognito login/refresh (BH-431, BH-432)

🐛 Production Stability + Quality
• ✓ Slack createSlackServiceUser idempotent
• ✓ Mixed-case filename duplicate detection (BH-451)
• ✓ Upload duplicate check across data assets and files (BH-447)
• ✓ AG Grid serverside datasource fix (BH-450)
• ✓ Login PW redundant check removal (BH-449)
• ✓ Synapse role assumption + cross-account hardening (BH-452)

📊 By the Numbers (v2)
• Tickets Resolved: 17 (7 streaming + 10 retro tickets BH-443..452, all Done)
• Story Points: 39
• PRs Merged: 39
• Lines Changed: +42.5K / -11.7K (54.1K total)
• Repos Touched: 5 (slack-server, platform-core, webapp, brightbot, data-org-cdk)
• Authors: 4 — full team active
• Major Capabilities Shipped: 6
• PR-Ticket Linkage: 54% (up from 41% v1, 34% Sprint 8 mid)

👥 Team Contributions
• Kuri — 12 feature PRs (BrightSignals end-to-end, streaming platform, UAT framework, Vega-Lite, notifications dispatcher)
• Harbour — 9 feature PRs (Task Scheduler MVP + fixes, BrightStudio Skills, upload dedup, catalog schedule, login cleanup)
• Marwan — 2 feature PRs (Bedrock Converse migration, AG Grid fix)
• Ahmed — 2 feature PRs (mixed-case dedup, Synapse role assumption)

🎯 What's Next: Sprint 10 Focus
• Bedrock AgentCore PoC (next migration phase)
• BrightSignals Teams + Email channel adapters
• Scheduler v1 with retry policies + cron + audit
• Skills v2 — sharing, versioning, marketplace foundation
• Sprint 8 formal close + cadence reset

⚠️ Sprint Health
• Full 14-day cadence preserved (Apr 20 → May 4)
• Sprint 8 (Apr 14–28) still active in Jira — formal close pending
• 10 retro tickets created May 2-4 to capture Marwan/Harbour/Ahmed work — all transitioned to Done
• 3 still-untracked epics (BrightSignals, UAT framework, Vega-Lite) — Kuri to create

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/9/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/9/MARKETING_RELEASE_NOTES.md
📊 Board Report (Q4 2025 → Q2 2026 to date): https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/BOARD_REPORT_OCT_2025_MAY_2026.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
