# Sprint 18 🍒 — Slack posts (reference copy)

Posted to `#releases` as four messages: one per person (Kuri first, then each engineer), then a short team wrap with the numbers and links. Each person's post leads with **🕒 Last 3 weeks (Nov 5 – Nov 26)**, followed by **Earlier (Oct 7 – Nov 4)**.

---

## Post 1 — Kuri

🍒 Brighthive Sprint 18 Release — Kuri
Sprint Period: Oct 7 – Nov 26, 2026 · Release Date: Nov 26, 2026

🌟 Kuri (drchinca) — self-hosted BrightAgent on Azure, project health, every warehouse watched
Code PRs merged — last 3 weeks: 110 · whole sprint: 323 (11 repos)

🕒 Last 3 weeks (Nov 5 – Nov 26)
☁️ Self-hosted BrightAgent on Azure
• ✓ MCP behind Entra sign-in, answering from Synapse, governed in IaC, proven with a foreign caller in an isolated workspace (AZ-098, AZ-101)
• ✓ Customer install package: connect an existing Synapse over private TLS, provision the runtime, install reviewed bundles, preflight + trial guide, launch audit closed (AZ-008, AZ-105–111)
• ✓ Projects over self-hosted MCP, proven live against staging (AZ-104) · brighthive-deploy v0.2.0
• ✓ brightbot serves standalone MCP: isolated tool registries, optional Agent Server, container image, Azure AI Foundry model provider (AZ-101, AZ-113, AZ-114)
🏭 Every warehouse, watched
• ✓ Governance watches every Snowflake and SQL Server warehouse and pulls lineage from each; stalled polls report Down (BH-1380)
• ✓ Databases are now nodes under their warehouse, backfilled (BH-1371, BH-1373)
🌐 Multi-cloud runtime merged into platform-core develop (#1367) and promoted to staging Nov 16
🧠 Claude models moved to Opus 5.5 / Sonnet 5.5 / Haiku 5.5 (BH-1656) · BrightAgent v4-on-CEMAF ADRs (BH-453)

Earlier (Oct 7 – Nov 4)
🩺 Project health: a watchdog per active project, a health headline, rules, problems and runs over MCP and in the webapp (BH-1626, BH-1634)
✅ Quality rules saved, activated and read back over MCP; group/tag rules run on the asset's warehouse (BH-1255, BH-1631)
🔧 Self-repairing monitoring with one actionable proposal per repair PR and Slack actions (BH-1255)
🛡️ Every project read/write scoped to its workspace, with live suites (BH-1584–1589, BH-1627, BH-1637)
🚀 Staging → Production on Oct 16 across brightbot, platform-core, webapp
🏗️ brighthive-deploy bootstrapped from zero to v0.1.0: foundation, sandbox, operations tool, IaC gates

---

## Post 2 — Harbour

🍒 Brighthive Sprint 18 Release — Harbour
Sprint Period: Oct 7 – Nov 26, 2026

👤 Harbour (Nano-233) — Teams notifications, Azure runtime parity, pipelines that repair themselves
Code PRs merged — last 3 weeks: 24 · whole sprint: 53 (5 repos)

🕒 Last 3 weeks (Nov 5 – Nov 26)
🔁 Pipelines that build and repair themselves
• ✓ Spec apply no longer builds broken pipelines; the author gets real columns, types and the SQL dialect, on Sonnet
• ✓ New `repair_project_pipeline_sql` MCP tool rewrites failed SQL steps
• ✓ First-pass identity-resolution SQL on Azure, plus Synapse step fixes
☁️ Azure runtime parity
• ✓ Workspace secrets from Key Vault; scheduled agents + project watchdog on Table Storage with an Azure cron dispatcher
• ✓ Live notifications stream with Entra JWT validation, proxied through platform-core
🔐 MCP access from the permission matrix
• ✓ MCP access follows the permission matrix on every profile; risky tools locked on Azure
• ✓ New `schedule_asset_monitor` and `run_scheduled_agent_now` tools

Earlier (Oct 7 – Nov 4)
📣 Microsoft Teams as a notification channel, with webhook validation (Microsoft hosts only)
☁️ Azure build-out for Nestlé: agent files in Blob, Entra service token, analyst Python on AKS, governance diagnostic sandbox, BrightSignals inbox
🧹 Catalog rebuild dropped from asset writes; failed asset-group loads now throw instead of failing silently

---

## Post 3 — Marwan

🍒 Brighthive Sprint 18 Release — Marwan
Sprint Period: Oct 7 – Nov 26, 2026

👤 Marwan (Marwan-Samih-Brighthive) — dbt Cloud per service, Azure hardening
Code PRs merged — last 3 weeks: 8 · whole sprint: 8 (3 repos)

🕒 Last 3 weeks (Nov 5 – Nov 26) — all merged Nov 11–12
🧱 dbt Cloud per service
• ✓ dbt Cloud project and environment ids stored per dbt service, editable in Settings, preferred by BrightAgent over repo matching
☁️ Azure hardening
• ✓ Azure webapp branch merged into develop
• ✓ GitHub tokens stored through the platform secret store
• ✓ OpenMetadata volume sized at 20Gi and grown in place
• ✓ Entra name claims set up by script
👤 User names are never blank; they're derived when the identity provider sends none

Earlier (Oct 7 – Nov 4): no merged PRs

---

## Post 4 — Team wrap

🍒 Sprint 18 — Team Wrap
Sprint Period: Oct 7 – Nov 26, 2026 · Release Date: Nov 26, 2026

📊 By the Numbers
• Code PRs Merged: 142 in the last 3 weeks · 384 across the whole sprint (+28 release/promotion)
• Code Lines: +290,650 / −66,998
• Repos Touched: 11 (incl. new brighthive-deploy, brightagent, brightagent-selfhost)
• 🚀 Staging → Production Oct 16 · staging promotions Nov 12 + Nov 16 · brighthive-deploy v0.1.0 + v0.2.0

👥 Code PRs merged, per person
Last 3 weeks (Nov 5 – 26) — team total 142
• Kuri — 110
• Harbour — 24
• Marwan — 8
Whole sprint (Oct 7 – Nov 26) — team total 384
• Kuri — 323
• Harbour — 53
• Marwan — 8 (none before Nov 11)

⚠️ Sprint Health
• Seventh unofficial (date-range) sprint in a row; no Jira sprint object
• 0 tickets reached Done in 7 weeks; 68 PR-linked tickets sit in Needs Refinement, 15 in To Do
• 85 code PRs carry no ticket key (Harbour 51, Kuri 26, Marwan 8)
• brightbot `feat/deployment-profile` (18 PRs incl. the Nov 24–25 pipeline fixes) has no PR to develop yet
• Kuri authored 84.1% of code PRs (up from 77.9%)

🎯 What's Next: Sprint 19 Focus
• Ticket sweep: move shipped project-health, scoping, quality and warehouse-watch tickets to Done
• Merge `feat/deployment-profile` to develop, then promote the Nov 16 staging cut to production
• First customer Azure install from the self-host package
• Every PR gets a `BH-XXX` or `AZ-XXX`, no exceptions

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/18/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/18/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
