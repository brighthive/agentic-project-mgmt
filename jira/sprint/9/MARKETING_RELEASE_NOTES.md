# Sprint 9 — Customer-Facing Highlights (v2)

**Release Date**: May 4, 2026 | **Sprint Period**: Apr 20 – May 4, 2026

---

## Headlines

### 🔔 BrightSignals is Here

For the first time, **BrightHive reaches out to you**.

BrightSignals is BrightHive's new proactive notification layer. Subscribe to a workspace, a data asset, or an agent run, and BrightHive will deliver updates straight to your Slack channel — no polling, no checking dashboards. The agent finds you when something matters.

**What you can do**:
- Subscribe to events (new data, quality alerts, agent completions)
- Receive Slack DMs or channel posts with asset UUIDs and artifact links
- Get attachments inline (CSV, dashboards, charts) via S3 hand-off
- Run BrightAgent in a channel — it stays quiet until @mentioned, then responds with full multi-tenant context

**Built for operators**: The release ships with a complete ops guide for installation and ongoing operations.

### 🎨 BrightStudio Skills

BrightStudio now has Skills — first-class, composable agent capabilities you can attach to any custom persona.

Build a Skill once (a chart-rendering skill, a SQL query skill, a domain-specific reasoning skill), then mix and match across your custom agents. This is the foundation for a Skills marketplace later this year.

### 📈 Charts and Visualizations in Slack

Ask BrightAgent for a visualization, get a rendered chart back in Slack. Vega-Lite specifications now render to PNG and flow through the BrightSignals attachment envelope, end-to-end.

---

## What Else Shipped

### 🤖 Smarter Agent Runtime — Bedrock Converse

BrightAgent now runs on AWS's modern Bedrock Converse interface. Same answers, faster streaming, better tool use, lower cost-per-call. This is a foundational upgrade that unblocks the next wave of agent capabilities — multi-step reasoning, structured tool outputs, and the AgentCore strategy we previewed at Q1 close.

### ⏰ Scheduled Tasks Are Live + Now with Result Display

The scheduling primitive shipped across all three layers — and got immediate UX upgrades:
- Core service for managing schedules
- Webapp UI for setting up recurring runs (with bug fixes)
- BrightAgent integration to trigger on schedule
- **NEW**: see the result of the last scheduled run, not just the schedule itself

Use it for recurring quality checks, periodic ingestion sweeps, or scheduled BrightAgent runs.

### 🧪 Deterministic Eval Framework

A new direct-call deterministic eval + HTTP scenario runner now lives in the Slack server. Use it to validate Slack flows end-to-end before deploys. (Internal/operator tooling.)

### 📤 Smarter Uploads

- Upload duplicate detection — the platform now flags duplicate data assets and files at upload time, before they hit the warehouse
- Mixed-case filename collision protection — `Report.csv` and `report.csv` no longer create duplicate assets

### 🔵 Azure Synapse Hardening

Synapse warehouse role assumption + permissions documentation. Customers running BrightHive on Synapse get a more reliable cross-account experience.

### 🛠 Behind-the-Scenes Reliability

- Streaming platform overhauled — span streaming FSM repaired, property-based tests added, 21 seconds of latency removed from internal test suites
- Slack service user creation hardened (no more duplicate errors on retry)
- AG Grid table fix for the server-side analytics view
- Login flow cleanup (removed redundant client-side validation)

---

## By the Numbers

| Metric | This Sprint |
|--------|-------------|
| Tickets Resolved | 17 (7 streaming + 10 retro) |
| Story Points Delivered | 39 |
| PRs Merged | 39 |
| Lines Changed | 54,145 |
| Repos Touched | 5 |
| Major Capabilities | 6 (BrightSignals, BrightStudio Skills, Bedrock Converse, Scheduler, UAT Evals, Vega-Lite) |
| Engineering Authors | 4 (full team) |

---

## Sprint Health

- **Full 14-day window** (Apr 20 → May 4) — original cadence preserved
- **PR-ticket linkage**: 41% (v1, May 2 snapshot) → 54% (v2, May 4 release). Boost driven by 10 retro tickets covering Marwan/Harbour/Ahmed's previously-untracked work
- **Cross-repo coordination**: BrightSignals (slack-server + core), Skills (webapp + brightbot), Scheduler (core + webapp + brightbot) all required tight coordination — successful execution
- **Bedrock momentum**: First production runtime change shipped; AgentCore PoC up next

---

## What's Next

Sprint 10 priorities under discussion:
- Bedrock AgentCore PoC (next migration phase)
- BrightSignals Teams + Email channel adapters
- Scheduler v1 with retry policies + cron + audit
- Skills v2 — sharing, versioning, marketplace foundation
- Sprint 8 formal close + cadence reset
