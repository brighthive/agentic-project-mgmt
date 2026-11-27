# Sprint 18 🍒 — What's New in Brighthive (Oct 7 – Nov 26, 2026)

## 🚀 A production release
On October 16, staging was promoted to production across BrightAgent, the platform API, and the web app. That release brought project health, workspace-scoped projects, and quality rules over MCP to production. Work merged after that date is on staging (Nov 12 and Nov 16) and will reach production with the next promotion.

## ☁️ BrightAgent, running in your own Azure
- Install BrightAgent inside your own Azure subscription. It connects to your existing Synapse warehouse over a private connection, and only people who sign in with Microsoft Entra can reach it.
- A packaged installer checks your environment before it runs, installs only reviewed bundles, and ships with a trial guide.
- Projects, warehouse reads, and health checks are all available to any MCP-ready agent from inside your network.

## 🩺 Know how every project is doing
- Every active project gets its own watchdog that checks its pipeline on a schedule.
- One health headline per project covers rules, open problems, and recent agent runs, in the web app and over MCP.
- When a pipeline breaks, BrightAgent proposes the repair as a reviewable change and posts it to Slack.

## 🏭 Every warehouse, watched
- Governance now watches every connected Snowflake and SQL Server warehouse, not only the first one, and pulls lineage from each.
- Databases appear under the warehouse they belong to.
- A warehouse that stops answering shows as Down instead of looking healthy.

## 🔁 Pipelines that fix themselves
- Pipelines are written against your real columns, in your warehouse's SQL dialect.
- When a step fails, BrightAgent can rewrite the failing SQL and try again.

## ✅ Quality rules your agents can manage
- Save, turn on, and check quality rules from Claude or any MCP-ready agent.
- Rules apply by tag, by group, or to every asset, and run on the warehouse that owns the data.

## 📣 Alerts in Microsoft Teams
- Notifications can now go to Microsoft Teams as well as Slack.

## 🧱 dbt Cloud, per service
- Point each dbt service at a specific dbt Cloud project and environment from Settings.

## 🛡️ Projects stay inside their workspace
- Every project action is checked against the workspace it belongs to, so nobody can read or change a project in a workspace they don't belong to.

## 📊 By the numbers
- 384 code changes merged across 11 repositories
- 1 production release, 2 staging promotions, 2 Azure delivery releases
