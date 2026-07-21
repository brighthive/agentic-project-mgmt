# Brighthive 3.0 — UAT Release Notes

> **Status: DRAFT — not a confirmed release.** Blocked on [PR #912](https://github.com/brighthive/brightbot/pull/912) (PII masking hotfix, ready for review, awaiting human approval) and two more fixes below that are live on `develop`/`staging` but not yet on `main`. This document previews what UAT testers will see once those land — do not treat this as "shippable today."

**Covers**: Sprint 13 window (June 23 – July 20, 2026) plus a few days of freshness past that cutoff.

---

## What to test

### 🔁 BrightRoutines — automation that notices patterns for you
BrightAgent watches how you use the platform and proactively suggests turning repeated actions into a scheduled routine. Look for a "want to automate this?" suggestion card in Slack or the webapp — it shows what the routine does, who owns it, and who it notifies. One click to schedule, adjust, or dismiss, with a full audit trail. Check "Your Routines" in the webapp to see what's running on your behalf, persisted across sessions.

**Test**: trigger a repeated action a few times and watch for the suggestion; accept one and confirm it fires on schedule.

### 🔔 Notifications — one consistent voice everywhere (Signal Catalog)
Slack and webapp notifications now pull from a single shared catalog, so severity levels and wording finally match across surfaces. You can tune delivery per category (quality, profiling, routines) instead of an all-or-nothing switch, and the inbox unread count now matches what's actually in the bell/drawer.

**Test**: compare a notification's severity/wording in Slack vs. the webapp inbox; adjust per-category preferences and confirm delivery changes; check unread count accuracy.

### 🧪 Quality Agent — real-time alerts, live in the side menu
Quality check passes/failures now deliver instantly, per-rule and per-asset, with human-readable failure reasons instead of raw error dumps. The webapp's side-menu quality notifications are now wired to live data (previously a placeholder).

**Test**: run a quality check that's expected to fail and confirm you get a readable alert in Slack + the side menu within moments, not on next check-in.

### 📊 Alerts page — now shows real data
The Alerts page reads from the live notification feed rather than a stale analytics table — counts reflect actual catalog severity.

**Test**: confirm counts on the Alerts page match what's happening in real time, not a lagging snapshot.

### 🔌 MCP (data source) connections — visibility upgrades
The connected-server carousel is now shown by default, with enriched cards and a refreshed Health Checks view, plus grid copy/paste support.

**Where**: wherever your MCP/data-source connections are listed.
**Test**: check the carousel renders your connected sources and health-check status is current.

### 🗂️ Workspace & Project Context pages — rebuilt with real data
These pages moved off placeholder/mock content to real workspace and project data.

**Test**: confirm the numbers and details shown reflect your actual workspace/projects, not generic sample data.

### 🧩 Skills Extension Framework — diagnostic superpowers (enterprise ETL)
The analyst agent can now load specialized diagnostic skills on demand, starting with SSIS/SSRS pipeline diagnostics.

**Test**: for SSIS/SSRS-connected workspaces, ask the analyst a pipeline-diagnostic question and confirm it routes to the specialized skill.

### 🧹 UAT bug-fix wave — papercuts fixed
- Upload modal click-to-browse now works (not just drag-and-drop)
- Update/Edit and Add/Create button labels are now consistent
- Green-background button text is now readable
- Delete confirmations added for projects and schemas
- "BrightHive" branding casing fixed app-wide (note: casing convention itself changed mid-cycle — see engineering notes)
- Password show/hide toggle added on login
- Projects Grid/Table views now show matching data
- Stale "beta/preview/coming soon" tags removed everywhere

---

## Built but not yet visible — ask your lead to enable

- **Analytics Dashboard**: wired to real KPI data behind the scenes, but was deliberately hidden from navigation again after testing surfaced gaps — ask your lead for a feature flag if you need to test it directly.
- **Access Control & Usage/Audit pages** (under Govern): also hidden from nav pending further work.
- **Monitoring Agents / pipeline watchdog**: auto-detection and auto-fix for dbt/Databricks pipeline failures is in staging validation, not yet fully rolled out — ask your lead before relying on it.

## Known gaps — expect these, don't file as new bugs

- PII-masking hardening on a few sample-data surfaces, Longaeva grounding/disambiguation fixes, and Semantic View lifecycle bugs are tracked and in progress. If you hit something in these areas, check with your lead before filing — it's likely already known.

## Why this is still a draft, not a release

Three fixes verified this cycle exist on `develop`/`staging` but have **not reached `main`**:

| Fix | Ticket | Where it lives | Status |
|---|---|---|---|
| PII masking on dbt sample-row endpoints, preview tool, description agent | BH-1078 | `main` via [PR #912](https://github.com/brighthive/brightbot/pull/912) | Ready for review, CI green, **not merged** |
| Analyst checks data exists before disambiguating | BH-776 | `develop`/`staging` (PR #737) | Not yet promoted to `main` |
| Fast-path for "no data" answers, KB relevance floor | BH-777 | `develop`/`staging` (same PR #737) | Not yet promoted to `main` |

UAT testing against `staging` will see all of the above already working. UAT testing against `main`/prod will not, until these are promoted. See `docs/releases/3.0/ENGINEERING_NOTES.md` for the full technical picture.
