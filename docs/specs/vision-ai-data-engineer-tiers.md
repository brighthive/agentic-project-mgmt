---
title: "BrightAgent as a virtual Data Engineer — three tiers, mapped to what's real"
type: vision
author: "drchinca"
created: "2026-09-04"
source: "AI Agent for Data Engineering - DRAFT.pdf (~/Downloads)"
status: Parked
roadmap: parked — no confirmed client trigger for the "operate it" tier yet; hold as reference per this doc's own "Open question for Kuri" section
related:
  specs: ["THEMES.md", "sqlserver-health-watch.md", "THEME-fleet-self-healing.md", "THEME-project-proactive-lifecycle.md", "pipeline-connectivity-watchdog.md"]
---

# BrightAgent as a virtual Data Engineer

> A draft vision doc described the AI Data Engineer in three tiers: watch the estate, build on
> it, operate it. This maps each tier against what's actually alive in BrightHive today —
> `file:line` for what's real, honestly marked dormant for what isn't. No unfalsifiable green,
> per THEMES.md's own rule.

## The vision, in one line

An AI Data Engineer isn't a data-quality watchdog with extra steps — it's a virtual team member
across three tiers: **watch** the whole estate (infra, pipelines, data), **build** on it (models,
transformations, dashboards), and **operate** it (governed action, not just a recommendation).
BrightAgent is genuinely alive on two of the three. The third is a real, unbuilt frontier — not a
gap to patch, a pillar to decide on.

**Legend**: 🟢 Alive (shipped, real code) · 🟡 Partial (built, narrower than the vision) · ⚫ Dormant
(no code, no spec — a real gap, not yet a lie since nothing claims otherwise)

## Tier 1 — Watch the estate

| Capability (from the vision doc) | Status | Evidence |
|---|---|---|
| Scheduled job / pipeline monitoring (SQL Agent, SSIS, dbt, Databricks) | 🟢 Alive | `pipeline_watchdog_task.py`, `PIPELINE_SOURCE_ADAPTERS` registry, `ssis-ssrs-proactive-pipeline-source.md` |
| Anomaly detection, historical trend analysis | 🟢 Alive | `longitudinal-monitoring.md` (BH-503, Shipped) — nightshift scheduler, stateful quality agent |
| Intelligent recommendations (why, contributing factors, corrective action) | 🟢 Alive | The golden-nugget pattern — `project-activate-sync-golden-nuggets.md`, being made continuous by `THEME-project-proactive-lifecycle.md` |
| Enterprise dashboard (single pane of glass) | 🟡 Partial | Analytics Dashboard (BH-835) still "mock → live"; Platform Analytics epic (BH-359) in progress |
| Alerting via Slack | 🟢 Alive | BrightSignals (BH-409) |
| Alerting via Email / Teams / mobile | ⚫ Dormant | `BH Omni integrations (Slack, Teams, Google)` is epic BH-117 — backlog, zero specs written |
| SQL Server health (disk, failed jobs) | 🟡 Partial | `sqlserver-health-watch.md` (BH-1255) — scoped narrowly to disk-low + failed Agent jobs |
| Full DB/OS perf-counter suite (PLE, deadlocks, blocking sessions, buffer cache hit ratio, CPU/memory/disk-queue) | ⚫ Dormant | Zero grep hits anywhere in the spec corpus — genuinely unbuilt |
| Root-cause drill-down across infra → DB → pipeline → app | ⚫ Dormant | BrightAgent's RCA today is data/lineage-level (`lineage-aware-data-quality.md`), not infra-to-app correlated |

## Tier 2 — Build on it

| Capability | Status | Evidence |
|---|---|---|
| Pipeline/transformation generation, optimization, documentation, troubleshooting | 🟢 Alive | `dbt_agent_react` — and the vision doc's own words apply almost verbatim: *"similar to GitHub Copilot, Codex, and Claude Code."* **BrightAgent is the Claude Code of data pipelines** — a line worth keeping. |
| Data modeling (conceptual/logical/physical) | 🟡 Partial | Semantic View lifecycle (BH-624) covers logical/semantic; physical DDL generation exists via dbt |
| Auto-generated ERDs / data-flow / architecture diagrams | ⚫ Dormant | Zero hits. Notable because BrightAgent's Neo4j lineage graph already holds the relationship data an ERD needs — this one's cheap relative to its vision-doc billing |
| Data visualization / dashboards | 🟡 Partial | `visualization_agent` (Plotly + E2B), not Power BI/Fabric-native — a new adapter, not a new capability, if a Microsoft-stack client needs it |

## Tier 3 — Operate it

| Capability | Status | Evidence |
|---|---|---|
| Enterprise knowledge assistant (schemas, lineage, docs, impact analysis) | 🟢 Alive | Core strength — retrieval + governance agents over the Neo4j catalog |
| Code-level self-healing (detect → diagnose → propose a PR, human approves) | 🟡 Partial | `THEME-fleet-self-healing.md` — explicit design principle: *"never self-merge."* |
| Governed autonomous **infrastructure** action (restart a service, scale an Azure resource, kill a blocked session) | ⚫ Dormant | Zero hits for "restart service," "scale azure," "blocked session," "deadlock" anywhere in the spec corpus |

## The one real pillar — not a Projects v3 addition

Tiers 1 and 3's dormant rows aren't scattered gaps — they're one coherent thing: **BrightAgent
diagnoses and proposes; it has never touched infrastructure directly.** That's a different
capability class from anything currently building (Projects' proactive nuggets, fleet
self-healing's PR proposals, warehouse-health probing) — all of those stop at "here's what's
wrong," never "I fixed it live." The vision doc's own qualifier — *"through governed workflows and
proper authorization controls"* — matches BrightHive's existing philosophy (human-approved, never
silently autonomous); the novelty is the **action surface**, not the trust model. BH-1464's
`authorize()` engine could plausibly gate this the same way it's starting to gate everything else.

None of THEMES.md's 6 pillars (see the truth / one answer every engine / fix itself / govern for
real / automate in plain words / meet you where you are) quite name this. It reads like a
candidate 7th: **"Operate it, don't just watch it."**

## Open question for Kuri

This is exploratory, not a theme — per THEME_SPEC_TEMPLATE's own rule, a theme needs a real
forcing trigger (an incident, a client blocker) before it's delegatable, and this vision doc alone
isn't confirmed to be one yet. Before this goes further:

1. Is this draft vision doc describing a specific prospect/client (the Microsoft-stack detail —
   SQL Server, Windows Server, Fabric, Teams — reads like a real trial ask, not a generic brief)?
2. If yes: is "operate it" (governed infra actions) something that prospect actually needs for a
   deal, or is the SQL/OS perf-counter monitoring depth (Tier 1) the real near-term ask, with
   Tier 3 aspirational?
3. Either way — this is a 7th-pillar-sized decision, not a ticket. Recommend: hold this doc as the
   reference, don't file tickets against it until the trigger is confirmed.
