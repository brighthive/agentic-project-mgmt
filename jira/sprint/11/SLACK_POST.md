🧪 BrightHive Sprint 11 Release
Release Date: June 2, 2026
Sprint Period: May 15 – June 2, 2026 (unofficial cut)

🤖 Data Profiler Agent — production-ready
• ✓ Auto-trigger on ingestion (BH-501)
• ✓ Run Profiler button + asset detail page (BH-522)
• ✓ Schedulable batch task + scheduler UI (BH-520)
• ✓ Workspace-scoped runs (BH-498)

🧭 Navigation + Permissions — fully correct
• ✓ Enterprise dashboard restructure (BH-376)
• ✓ Admin role guard on KB files (BH-513)
• ✓ /govern/schemas → /catalog/schemas links (BH-514)
• ✓ Governance detail routes aligned (BH-515)
• ✓ NavLink active state (BH-516)
• ✓ Role-based section visibility + sidebar guard (BH-517)
• ✓ Stale /home shortcuts + breadcrumbs (BH-556)

🔓 BrightStudio
• ✓ Collaborators can now manage custom agents (BH-548)

📡 Quality Signals
• ✓ Quality check completion → BrightSignals Slack (BH-530)

🛠 Local-Dev
• ✓ Seed data + mocks across platform-core + webapp
• ✓ Workspace-aware BrightBot requests + thread validation

🐛 Production Stability
• ✓ Hotfix BrightAgent S3 streaming mem0
• ✓ AG Grid aria sidebar layout fix

📊 By the Numbers
• Tickets Completed: 7 / 19 (47.4% incl. QC pipeline)
• PRs Merged: 27
• Lines Changed: 15,183 (excl. release-carrier PRs)
• Repos Touched: 3 (webapp · platform-core · brightbot)
• Engineering Hours: ~120h estimated

👥 Team Contributions
• Harbour — 7 done + 2 in QC (nav/perms hardening, profiler scheduler, BrightStudio collab)
• Kuri — 4 in pipeline (BH-376 nav, profiler port, feature flags, local-dev seeds)
• Marwan — 1 in pipeline + 2 hotfixes (quality Slack signals, dbt Cloud secrets)
• Ahmed — 1 in flight (BH-502 profiler E2E)

🎯 What's Next: Sprint 12
• Transition Needs-Refinement tickets to Done
• BH-359 Platform Analytics dashboard
• Unassigned bug fixes (BH-491, BH-495, BH-497)
• Formalize Sprint 12 in Jira

⚠️ Sprint Health
• 10 tickets in Needs Refinement with merged PRs (transition pass needed)
• 4 tickets unassigned heading into Sprint 12
• Cut excludes Longaeva PoC work — tracked separately

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/11/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/11/MARKETING_RELEASE_NOTES.md
📊 Summary: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/11/SUMMARY.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
