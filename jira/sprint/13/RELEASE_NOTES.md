# Sprint 13 Release Notes — Routines, Signals & Trust Hardening
**Period**: June 23 – July 20, 2026 | **Repos**: 6 (of 7 scanned) | **PRs**: 499 feature/fix (579 total)

---

## Summary

| Metric | Value |
|--------|-------|
| Feature/Fix PRs merged | 499 |
| Lines changed | +355,423 / −91,481 |
| Repos touched | 6 |
| Tickets in scope | 446 (BH-737 → BH-1137) |
| Tickets Done | 141 |
| Story points completed | 43 (only 13 tickets estimated) |

---

## Completed Tickets (highlights)

### BrightRoutines (BH-876) — 64 of 108 sub-tickets Done
Full proactive-schedule detection and workflow-automation stack:
- **BH-882–884** — DynamoDB signal/pattern/suggestion tables, IntentCaptureMiddleware, recurring-automation detector + schedulability judge
- **BH-885–887** — brightbot suggestion routes, webapp "Suggested Routines" section, slack-server suggestion cards
- **BH-877–881** — scheduler service-auth, terminal completion bridge, workflow schedule affordance, P1 e2e contract
- **BH-963–970** — action/artifact accountability model, Neo4j ownership edges, editable recipient at schedule time
- **BH-975–978** — scheduledRoutinesForWorkspace query, unscheduleRoutine mutation, "Your routines" persistence + e2e
- **BH-1001–1004** — service-key auth on schedule/dismiss mutations, x-acting-user-id mode, Slack schedule/dismiss route, e2e chain test
- Security/reliability sweep: **BH-919, 922, 926, 928, 933, 935, 937** — secret-comparison timing, mrkdwn injection, unauthenticated mutation, dedup keys, cron edge cases

### BrightSignals / Signal Catalog (BH-409) — 13 of 30 sub-tickets Done
- **BH-1124–1129** — Signal Catalog: `signal-catalog.json` + loader, severity on GraphQL wire, dispatcher severity_filter + CI drift-check, Python publisher const, slack-server + webapp adoption
- **BH-980/981** — unread-count drift fix, per-user inbox table as single source of truth
- **BH-1096–1100** — metric-free AI-only quality notification, neutral "Done" pill, LangGraph run-completion signal spike

### Configurable Quality Agent (BH-503) — Done
- **BH-557/558** — Quality Agent wired to BrightSignals end-to-end; webapp side-menu notifications now live (previously fake)

### Skills Extension Framework (BH-860) — 14 of 14 sub-tickets Done
- SkillModel schema extension, DeepAgentSkillsMiddleware, 3 SSIS/SSRS diagnostic skills, affinity-filtered delivery to analyst subagent, full L0/L1/L2 + e2e coverage, staging validation

### Platform & Catalog Bug Sweep (BH-173 / ungrouped)
- **BH-746, 748, 750, 751, 784, 787, 789** — Uppy upload fix, CSV S3 checksum fix, project tooltip/contrast fixes, cron/scheduler validation fixes
- **BH-813, 822, 827** — Pydantic validation-error leaks, RFC 6750 case-insensitive bearer auth
- **BH-892, 893** — quality report error surfacing, transient warehouse-timeout handling
- **BH-712** — case-insensitive catalog search

### Notification UX polish (ungrouped)
- **BH-1022, 1025** — canonical CRITICAL severity, slack-server poller hardening (lease-TTL, fetch timeout, SSE leak)
- **BH-1030–1035** — copy/label fixes (BrightHive casing, password show/hide, confirm dialogs, action-label consistency)
- **BH-1056, 1090, 1093–1095, 1106** — "Clear read," profiler category filters, curated failure reasons, per-category inbox toggles
- **BH-1122/1123** — Projects grid Managers row + createdAssetCount fix

---

## Repository Activity

### brightbot
221 PRs merged (183 feature/fix, 38 staging release carriers)

Key PRs:
- [#668, #680, #681] Structured action audit logging (OTel/CloudWatch) + JWT identity resolution
- [#672, #674, #675] Semantic View merge confirmation tool, dbt lineage/stage-ops spec, run_models_to_stage
- [#676] Snowflake TIMESTAMP_NTZ(9) overflow recovery
- [#678] Auth token validation cache + Platform Core timeout increase
- [#682] UAT-MCP regression suite for Longaeva PoC (14-scenario harness)
- Watchdog/monitoring-agent series (BH-1036): pipeline discovery, dbt/Databricks health pollers, auto-remediation loop, generic ETL adapter port
- PII masking sweep PRs (BH-1078 series): dbt sample-row masking, agent tool I/O boundary extension
- Signal Catalog adoption in slack-server classify refactor

### brighthive-platform-core
177 PRs merged (153 feature/fix, 24 staging release carriers)

Key PRs:
- [#924] Semantic View PR-state reconcile + confirmSemanticViewMerge
- [#925, #926] GraphQL schema fixes: warehouse fields exposure, createTransformation jobId contract
- [#927, #934] Case-insensitive data catalogue search + API latency fixes
- [#933] CSV upload S3 presigned-PUT checksum fix
- [#937, #938] Governance policy isActive persistence + read-type exposure (BH-766 gap closure)
- Signal Catalog: severity-on-wire stamping, dispatcher severity_filter, drift-check CI job
- Notification subscription CRUD, per-category inbox toggle resolvers
- Analytics dashboard resolver groundwork (BH-835): pipelineHealth, quality, enrichment resolvers (in progress)

### brighthive-webapp
129 PRs merged (116 feature/fix, 13 staging release carriers)

Key PRs:
- [#1210] Admin-only dbt API token rotation
- [#1216–1225] UAT round-1 bug-fix batch: scheduler pill/severity copy, data-preview loader, Uppy click-to-browse, contrast fixes, workspace-scoping fixes, profile role display
- [#1220, #1227] Playwright e2e expansion — 64 tests across 9 spec files + strict GraphQL fixture/lint framework
- [#1229] Feature-flag canonical catalog for runtime route/tab visibility
- Signal Catalog webapp adoption: vocab deletion, title switches
- "Your routines" persistence UI, RoutineSuggestion cards, notification preference toggles

### brightbot-slack-server
50 PRs merged (39 feature/fix, 11 staging release carriers)

Key PRs:
- [#102] Notification count drift fix (BH-858)
- [#104] Scheduled-workflow Slack notification formatting (BH-879)
- [#106] mrkdwn injection escaping for user-controlled fields
- [#109, #110] Notification delivery dedup + boundary validation
- [#112, #113] Slack connect atomic provisioning + self-service identity-linking UI (BH-907, BH-913)
- [#114, #115] Unified Slack message footer + targeted DM delivery for personal events (BH-971, BH-951)
- [#119] Scheduled-workflow dedup + no-raw-prompt-leak test coverage (BH-962)

### brighthive-admin (1 PR)
Single small PR in-window — no major feature work.

### brighthive-data-workspace-cdk (1 PR)
Unstructured-data-stack resource-bucket relocation update.

### brighthive-data-organization-cdk (0 PRs)
No merges in this window.
