🍓 BrightHive Sprint 16 Release
Release Date: August 23, 2026
Sprint Period: August 17 - August 23, 2026

🔌 Sync Stops Failing Closed
• ✓ LANGGRAPH_BASE_URL + LANGGRAPH_API_KEY wired into the ECS runtime and the GraphQL Lambda after last week's cutover (BH-1461)
• ✓ Project-transformation run cards read lastRunAt from storage instead of computing it live (BH-1462)

🗄️ Warehouse Resolution, Off the Legacy Path
• ✓ Scheduled jobs and legacy SQL callers now resolve through the workspace default warehouse via OGM, not the public catalog
• ✓ Supervisor gets a dedicated warehouse-listing tool — no GraphQL introspection needed (BH-1454)

🚀 Infra
• ✓ GraphQL Core's Lambda warmer retired now that ECS carries staging traffic

🔔 Notifications
• ✓ slack-server delivers PDF/CSV/table artifacts on the direct channel-push path (BH-1452)

📊 By the Numbers
• Tickets Completed: 1 / 1 resolved (BH-1461)
• PRs Merged: 22 (13 code + 9 release/promotion)
• Lines Changed: +5,993 / -417 (code only)
• Repos Touched: 5 (platform-core, webapp, brightbot, slack-server, agentic-project-mgmt)
• Engineering Days: 7 — first release on the new weekly cadence

👥 Team Contributions
• Kuri — 7 code PRs across 5 repos (env wiring, supervisor tooling, artifact delivery, spec consolidation)
• Harbour — 4 code PRs (warehouse-routing cleanup, Apollo toast fix)
• Marwan — 2 code PRs (GraphQL ECS/CloudFront cutover continuation)

🎯 What's Next: Sprint 17 Focus
• Transition BH-1462, BH-1454, BH-1452, and BH-1036 to match shipped code
• Tag the 5 ticketless PRs against their real epics
• Keep the weekly cadence

⚠️ Sprint Health
• Completion: 1/1 resolved ticket Done — 4 more shipped code but stayed in Needs Refinement
• No tickets carrying over — none were formally scoped to this window
• First sprint cut to a clean 7-day week, by team decision

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/16/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/16/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
