# Sprint 4 🍍 — What's New for Customers

**Release:** February 2026
**Sprint:** Sprint 4 🍍 (Feb 3–10, 2026)

---

## Highlights for Customers

### Smarter Data Quality with AI
BrightHive now includes an **auto-classification agent for PII detection** — automatically scanning your data assets to identify personally identifiable information. No manual tagging required; the platform proactively flags sensitive data across your warehouse.

### Slack Integration Architecture
We're laying the groundwork for **native Slack integration**. This sprint delivered the authentication design and an intelligent message routing system that will allow your team to interact with BrightHive directly from Slack — ask questions, get data quality reports, and trigger workflows without leaving your workspace.

### Background Agent Intelligence
Design work completed for **proactive background agents** that continuously analyze your data quality without manual triggers. These agents will autonomously monitor data health and surface issues before they impact downstream systems.

---

## Platform Improvements

- **GitOps deployment automation** for server resources (OpenMetadata, Airbyte) — faster, more reliable infrastructure provisioning during customer onboarding
- **Semantic versioning** enforced across all release pipelines — clearer release tracking and rollback capabilities
- **Code quality standards** rolled out across 10 repositories — Claude-assisted code review, pre-commit hooks, and automated PR validation

---

## Bug Fixes

- Fixed authentication issue on staging environment that was impacting login workflows
- Resolved AWS credential conflicts affecting data pipeline connectivity

---

## What's Coming Next

- **Workspace Context Portal** — configure and manage workspace-level context for your AI agents
- **BrightSide chat improvements** — updated colors, error tooltips, and auto-generated query titles
- **Project-Agent integration** — connect BHAgent directly to project containers for targeted analysis
- **Full Slack integration** — workspace install, user identity linking, and conversational data access

---

*Sprint 4 🍍 delivered 31 story points across 12 completed tickets, with contributions from 4 engineers across 10 repositories.*
