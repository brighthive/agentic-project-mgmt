📡 BrightHive Sprint 9 Release
Release Date: May 2, 2026
Sprint Period: April 20 – May 2, 2026 (12 days — cadence-shortened by 2)

🔔 BrightSignals — Proactive Notifications (NEW PRODUCT SURFACE)
• ✓ Multi-tenant Slack auth, mention filter, async handlers, file attachments
• ✓ Subscriptions + poller + delivery infrastructure (slack-server #16, +2.4K lines)
• ✓ S3:// URI artifact handoff (Tier A) + <BH_ARTIFACTS> envelope parser (Tier B)
• ✓ Notification dispatcher Lambda — EventBridge + DynamoDB streams (BH-412)
• ✓ Asset UUID surfaced in Slack, operator install + ops guide
• ✓ BrightSignals product rebrand on operator surfaces

🤖 Bedrock Converse Migration
• ✓ ChatBedrock → ChatBedrockConverse + deepagents framework upgrade (brightbot #457)
  → Foundation step for the LangGraph → Bedrock AgentCore migration

⏰ Task Scheduler MVP (Cross-Repo)
• ✓ Agnostic scheduler service in platform-core
• ✓ Schedule UI in webapp (analytics + scheduler)
• ✓ Brightbot agent integration

🧱 Streaming Platform Hardening
• ✓ FSM repair — STABILIZED reachable + linear guards (BH-437)
• ✓ Removed prototype "[refined]" placeholder from prod path (BH-438)
• ✓ Py 3.14 compliance + deduplicate SpanStreamProcessor (BH-439)
• ✓ Wire SpanStreamProcessor into suite + SSE ordering invariants (BH-440)
• ✓ Hypothesis property tests + clock injection — killed 21s of time.sleep (BH-441)
• ✓ Neo4jGraphStore + BrightHivePlatformAdapter + Cognito login/refresh (BH-431, BH-432)

🐛 Production Stability
• ✓ Slack createSlackServiceUser made idempotent
• ✓ Mixed-case filename duplicate detection
• ✓ Upload duplicate check across data assets and files (server + UI)
• ✓ AG Grid serverside datasource fix
• ✓ Synapse role assumption + cross-account hardening

📊 By the Numbers
• Tickets Resolved (in window): 7
• PRs Merged: 27
• Lines Changed: +22.5K / -6.8K (29.4K total)
• Repos Touched: 5 (slack-server, platform-core, webapp, brightbot, data-org-cdk)
• Authors: 4 — full team active
• Major capabilities shipped: 4

👥 Team Contributions
• Kuri — 12 PRs (BrightSignals end-to-end, streaming platform, notifications dispatcher)
• Harbour — 7 PRs (Task scheduler MVP cross-repo, duplicate check, catalog schedule)
• Ahmed — 5 PRs (Synapse logic + role assumption, mixed-case dedup)
• Marwan — 3 PRs (Bedrock Converse migration, AG Grid fix)

🎯 What's Next: Sprint 10 Focus
• Bedrock AgentCore PoC (next migration phase)
• BrightSignals Teams + Email channel adapters
• Scheduler v1 with retry policies + audit
• Sprint 8 formal close + cadence reset

⚠️ Sprint Health
• Cadence shortened: 12 days vs 14 planned (cut 2 days, change in cadence)
• Sprint 8 (Apr 14–28) still active in Jira — overlap of 8 days, formal close pending
• PR-ticket linkage: 41% (up from 34% in Sprint 8 mid-sprint)
• 3 untracked Q2 epics (BrightSignals, Scheduler, Bedrock Converse) — retro tickets needed

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/9/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/9/MARKETING_RELEASE_NOTES.md
📊 Board Report (Q4 2025 → Q2 2026 to date): https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/BOARD_REPORT_OCT_2025_MAY_2026.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
