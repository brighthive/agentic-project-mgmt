# Sprint 9 — Customer-Facing Highlights

**Release Date**: May 2, 2026 | **Sprint Period**: Apr 20 – May 2, 2026

---

## Headline: BrightSignals is Here

For the first time, **BrightHive reaches out to you**.

BrightSignals is BrightHive's new proactive notification layer. Subscribe to a workspace, a data asset, or an agent run, and BrightHive will deliver updates straight to your Slack channel — no polling, no checking dashboards. The agent finds you when something matters.

**What you can do**:
- Subscribe to events (new data, quality alerts, agent completions)
- Receive Slack DMs or channel posts with asset UUIDs and artifact links
- Get attachments inline (CSV, dashboards, charts) via S3 hand-off
- Run BrightAgent in a channel — it stays quiet until @mentioned, then responds with full multi-tenant context

**Built for operators**: The release ships with a complete ops guide for installation and ongoing operations.

---

## What Else Shipped

### 🤖 Smarter Agent Runtime — Bedrock Converse

BrightAgent now runs on AWS's modern Bedrock Converse interface. Same answers, faster streaming, better tool use, lower cost-per-call. This is a foundational upgrade that unblocks the next wave of agent capabilities — multi-step reasoning, structured tool outputs, and the AgentCore strategy we previewed at Q1 close.

### ⏰ Scheduled Tasks Are Live (MVP)

The first scheduling primitive shipped across all three layers:
- Core service for managing schedules
- Webapp UI for setting up recurring runs
- BrightAgent integration to trigger on schedule

Use it for recurring quality checks, periodic ingestion sweeps, or scheduled BrightAgent runs.

### 📤 Smarter Uploads

- Upload duplicate detection — the platform now flags duplicate data assets and files at upload time, before they hit the warehouse.
- Mixed-case filename collision protection — `Report.csv` and `report.csv` no longer create duplicate assets.

### 🔵 Azure Synapse Hardening

Synapse warehouse role assumption + permissions documentation. Customers running BrightHive on Synapse get a more reliable cross-account experience.

### 🛠 Behind-the-Scenes Reliability

- Streaming platform overhauled — span streaming FSM repaired, property-based tests added, 21 seconds of latency removed from internal test suites.
- Slack service user creation hardened (no more duplicate errors on retry).
- AG Grid table fix for the server-side analytics view.

---

## By the Numbers

| Metric | This Sprint |
|--------|-------------|
| Tickets Resolved | 7 |
| PRs Merged | 27 |
| Lines Changed | 29,380 |
| Repos Touched | 5 |
| Major Capabilities | 4 (BrightSignals, Bedrock Converse, Scheduler, Streaming Hardening) |
| Engineering Authors | 4 (full team) |

---

## Sprint Health

- **Cadence change**: Sprint 9 ran 12 days (Apr 20 → May 2) instead of 14 (planned May 4) due to a release cadence shift.
- **Cross-repo coordination**: BrightSignals required slack-server, platform-core, and brightbot to coordinate end-to-end. Successful cross-team execution.
- **Bedrock momentum**: Sprint 9 marks the first Bedrock-native runtime change in production code path.

---

## What's Next

Sprint 10 priorities under discussion:
- Bedrock AgentCore PoC (next migration phase)
- BrightSignals Teams + Email channel adapters
- Scheduler v1 with retry policies
- BrightStudio v2 capabilities
