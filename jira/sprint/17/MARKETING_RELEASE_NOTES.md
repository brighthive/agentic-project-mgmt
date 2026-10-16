# Sprint 17 🥝 — What's New in Brighthive (Aug 24 – Oct 6, 2026)

## 🚀 A production release
On September 30, staging was promoted to production across BrightAgent, the platform API, and the web app. Work merged after that date (project tools over MCP, honest health, automatic audit) is merged and rides the next promotion.

## 🛡️ You decide who can see and do what
- One permission matrix per workspace, editable live from Governance → Access Control.
- Access limits based on data sensitivity, not just role.
- Every request is checked against the workspace it belongs to — no data crosses between workspaces.

## 🔒 Sensitive data stays masked
- Personal data stays masked in query results, previews, samples, and summaries, even when a query renames or reshapes columns.
- BrightAgent only reads data assets the user is allowed to read.

## 🔌 Run your projects from any agent
- A complete set of project tools over MCP: create, update, organize, run, and govern projects from Claude or any other MCP-ready agent.

## 📐 Projects that start from a spec
- Describe the project in conversation; Brighthive writes the spec, builds the pipeline, verifies it, and shows how well each section of the spec is met.
- Pipelines can be scheduled straight from chat.

## 🔎 Find any data asset, across every warehouse
- Search the catalog by meaning, scoped to a warehouse or project.
- A new catalog view (rolling out) that groups assets by warehouse, database, and schema.
- Queries go to the warehouse that actually owns the data.

## 🌍 Brighthive in Spanish and Portuguese
- The full interface, BrightAgent's progress messages, and quality reports now speak English, Spanish, and Portuguese.

## 🩺 Health you can trust
- When we haven't checked a connection recently, we say "Unknown" — never a green we can't back up.
- A new alert tells you when a source connection becomes unreachable.

## 🧾 A complete audit trail
- Every change made through the platform is recorded automatically.
- Only a schedule's owner or a workspace admin can change or run it.

## By the Numbers
- 195 code changes merged across 7 repositories
- 3 engineers shipping
- 1 production release
