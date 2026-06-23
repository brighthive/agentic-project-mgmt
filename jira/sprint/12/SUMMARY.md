# Sprint 12 — Auth, MCP & BrightSignals
**Period**: June 13–23, 2026 (10 days) | **Unofficial** (no Jira sprint object)

---

## Stats

```
┌─────────────────────────────────────────────────────────────┐
│  Sprint 12 — Auth, MCP & BrightSignals                      │
│  June 13–23, 2026 · 10 days                                 │
├──────────────────────────────┬──────────────────────────────┤
│  PRs Merged (total)          │  299                         │
│  Feature/Fix PRs             │  223                         │
│  Staging release carriers    │  76                          │
│  Lines changed               │  +67,654 / -12,111           │
│  Repos touched               │  7                           │
├──────────────────────────────┼──────────────────────────────┤
│  Tickets (scope)             │  ~75 in window               │
│    Done                      │  18                          │
│    Needs Refinement          │  50 (merged, not transitioned)│
│    Code Review               │  3                           │
│    In Progress               │  2                           │
│  Story Points                │  N/A (not estimated)         │
├──────────────────────────────┼──────────────────────────────┤
│  Tickets retroactively added │  27 (BH-713–739)             │
└──────────────────────────────┴──────────────────────────────┘
```

---

## Goals Assessment

| Goal | Status | Evidence |
|------|--------|----------|
| BrightSignals end-to-end | ✅ | SSE push (slack-server #65), CloudWatch alarms (#63), Notifications MVP all 3 repos |
| Auth hardening (Okta SSO, Slack JWT) | ✅ | Okta PKCE webapp (#1207), resolver-side JIT platform-core (#910), x-api-key primary auth (#98) |
| MCP connectivity card | ✅ | tools/list live (#1163), streamable-http parser, dedicated brightagent-mcp ingress (#887) |
| dbt agent URL + scaffold fixes | ✅ | Account-specific URLs (#661), token probe (#644), scaffold fix (#663) |
| Audit trail BH-695 epic | ✅ | Full decorator + emitter stack shipped (BH-696–702, PRs brightbot #654–668) |

---

## Team Breakdown

| Member | Feature PRs | Key themes |
|--------|------------|------------|
| Kuri   | ~145 | Auth (Okta/JWT), Audit trail, MCP, dbt agent, platform-core reliability, infra |
| Marwan | ~30  | Snowflake TIMESTAMP_NTZ, dbt endpoints, Slack-server infra, feature flags |
| Harbour | ~24 | Quality checks SQL, catalog fixes (tags, preview indicators), cooldown, BYOW preview |
| Ahmed  | ~24  | CORS fixes, notifications stack pipeline, Redshift SOC upgrade, tableFQN |

---

## WIP Analysis

| Flag | Count | Notes |
|------|-------|-------|
| Quick-win (< 1 day) | ~80 | Many small targeted fixes (CORS, auth, labels) |
| Normal (1–7 days) | ~120 | BrightSignals arc, MCP card, Audit trail |
| Multi-sprint context | ~20 | GC-12 longitudinal monitoring (started sprint 11), Okta SSO (spec sprint 11) |

Average cycle time: ~2 days per PR cluster. Audit trail BH-695 epic (8 stacked PRs) shipped in a single day — exceptionally fast execution.

---

## Themes Delivered

### 🔔 BrightSignals End-to-End (BH-409)
Full push notification stack shipped: SSE delivery from brightbot-slack-server, per-workspace poll model, CloudWatch alarms with on-call runbook, notifications MVP in all three repos (brightbot, platform-core, webapp). Quality run completion now triggers Slack alerts via BrightSignals.

### 🔐 Auth Hardening
- Okta SSO: PKCE callback in webapp (BH-675), resolver-side JIT Neo4j provisioning (BH-674)
- Slack-server → brightbot: Cognito JWT → x-api-key primary chain
- OAuth workspace guard: refused silent team re-point to unprovisioned workspaces
- Multi-workspace: X-Workspace-Id header, thread isolation, run tagging

### 🔌 MCP Connectivity
Live tools/list rendering, JSON-RPC test, streamable-http parser, dedicated `brightagent-mcp.{env}.brighthive.net` ingress, FastMCP mounted at `/bh-mcp` to avoid LangGraph shadow. 3 read-only tools shipped (get_workspace_context, get_schema_details, analyze_model_impact).

### 🔍 Audit Trail (BH-695 epic)
Full decorator + emitter stack in brightbot: `@audit_action` decorator, CloudWatch+DynamoDB dual-write emitter, citation chain carrier, middleware user enrichment, 6 mutation tools instrumented. IaC shipped but subsequently cleaned up (WORM approach pivoted). BDD + moto integration tests included.

### 🏗️ Platform Reliability
504 fixes (Lambda assertConstraints removal), WorkspaceSwitcher OGM 20-cap fix (raw Cypher), OM webhook parse fixes for OM 1.8, embedding trigger for scanned tables, superadmin cleanup mutations (dedup, purge orphan embeddings, BYOW preview).

### ❄️ Snowflake Quality
tableFQN fallback chain across retrieval + quality-check, full compatibility pass (warehouse-agnostic SQL generation), TIMESTAMP_NTZ(9) overflow recovery.

---

## Problems Identified

1. **Ticket linkage gap (recurring)**: ~50 tickets in "Needs Refinement" = merged PRs not transitioned. Same pattern as Sprint 6/11. Needs a 15-min sweep to mark Done.
2. **No story points**: Fast-paced execution window — all 27 tickets created post-merge with no estimates. Velocity tracking degraded.
3. **No formal sprint object**: Sprint 12 has no Jira sprint container. Acceptable for the execution pace but makes JQL sprint queries miss this window.
4. **Solo-heavy**: Kuri authored ~65% of PRs. Concentration risk in auth/infra/audit domains.

---

## Recommendations for Sprint 13

1. **Transition the 50 Needs Refinement tickets to Done** — 15-minute sweep, not a sprint task.
2. **Add story points to BH-713–739** — even rough t-shirt sizing restores velocity tracking.
3. **Create a Jira Sprint 13 object** before starting work — date-range-only tracking loses sprint context.
4. **Distribute auth/MCP work** — Harbour and Marwan onboarding to the Okta/MCP domain would reduce key-person risk.
5. **BH-695 audit epic**: IaC pivot (WORM removed) needs final decision on persistence strategy before e2e tests can fully pass.
