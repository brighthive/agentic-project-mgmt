# Sprint 13 Slack Post (Reference Copy)
Posted to #releases on July 20, 2026 | ts: 1784587327.739009

---

🧵 BrightHive Sprint 13 Release
Release Date: July 20, 2026 • Sprint Period: June 23–July 20, 2026 • 28-day execution window

---

🔁 BrightRoutines Ships
• ✓ Recurring-pattern detection + "want to automate this?" suggestion cards (BH-876 epic, 64/108 sub-tickets Done)
• ✓ Schedulability judge + ownership/accountability model
• ✓ One-click schedule/adjust/dismiss with full audit trail
• ✓ "Your Routines" page persists across sessions

🔔 Signal Catalog: One Source of Truth
• ✓ Canonical severity stamped end-to-end across Slack + webapp (BH-1124–1129)
• ✓ Per-category notification preferences — quality, profiling, routines (BH-1106)
• ✓ Inbox unread-count drift fixed (BH-980/981)

🧪 Configurable Quality Agent Goes Live
• ✓ Rule library drives real-time BrightSignals alerts, per-rule and per-asset
• ✓ Webapp side-menu notifications wired to live data (was placeholder)
• ✓ Curated, human-readable failure reasons replace raw error dumps

🩺 Monitoring Agents (in progress)
• ✓ Pipeline discovery adapters for dbt, Databricks, generic ETL — reached Staging QC (BH-1043–1054)
• ⚠️ Epic BH-1036 still mostly Needs Refinement (22 of 23 sub-tickets open) — full rollout targeted for Sprint 14

🧩 Skills Extension Framework
• ✓ SSIS/SSRS diagnostic skills for the analyst agent — fully shipped and staged (BH-860, 14/14 Done)

🐛 Production Stability / UAT Fixes
• ✓ Upload modal click-to-browse fix (BH-1072)
• ✓ Confirmation dialogs for project/schema deletion (BH-1035, BH-1073)
• ✓ Contrast + branding-casing fixes across webapp
• ⚠️ PII masking sweep still open — P0 bug BH-1078 unresolved since July 13

---

📊 By the Numbers
• Feature PRs Merged: 499
• Total PRs (incl. staging): 579
• Lines Changed: +355,423 / −91,481
• Tickets Touched: 446 (BH-737 → BH-1137)
• Repos Touched: 6
• Engineering Days: 28

👥 Team Contributions
• Kuri — Routines, Signal Catalog, monitoring agents, PII enforcement, lineage, MCP fixes (~417 PRs)
• Marwan — Studio agent fixes, Bedrock timeout retry, visualization multi-panel, notification footer (~88 PRs)
• Harbour — Skills Extension Framework, notification preferences, catalog/UX bug sweep (~71 PRs)
• Ahmed — Warehouse default-flag property, OnboardDataAsset workflow, ingestion sources (~3 PRs)

🎯 What's Next: Sprint 14 Focus
• Close out BH-1036 (Monitoring Agents) — watchdog/remediation core already in Staging QC
• Resolve the two Blocked analyst-trust tickets (BH-776, BH-777) — Longaeva credibility path
• Prioritize PII enforcement sweep (BH-1084 / BH-1078, open since July 13)
• Run a 30–45 min ticket-transition sweep on 235 Needs-Refinement tickets

⚠️ Sprint Health
• Completion: 141/446 tickets Done (31.6%) — understates delivery; most work ships via PR before ticket transitions
• 235 tickets in Needs Refinement (3rd consecutive sprint with this pattern — process debt, not one-off)
• Concentration risk unchanged: Kuri authored 72% of PRs
• Unofficial sprint (no Jira sprint object), third in a row — Sprint 14 should open a formal sprint

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/13/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/13/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
