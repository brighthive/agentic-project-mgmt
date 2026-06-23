# Sprint 12 — Customer-Facing Highlights
**BrightHive | June 13–23, 2026**

---

## 🔔 BrightSignals: Real-Time Notifications Are Live

Your data quality runs and agent actions now push instant Slack notifications — no more polling or waiting. BrightSignals delivers structured alerts the moment something happens across your workspace.

- Quality check completions surface in Slack automatically
- End-to-end observability with CloudWatch alarms and on-call runbook
- Notifications drawer in the webapp wired to live BrightSignals data

---

## 🔐 Enterprise SSO: Log In With Okta

BrightHive now supports federated login via Okta. Your team can sign in with their existing enterprise credentials — no separate BrightHive password required.

- "Log in with Okta" button live in the webapp
- Automatic user provisioning on first login (zero admin setup)
- Full PKCE + Cognito federation — enterprise security standards

---

## 🔌 MCP Connectivity: A2A Integration Is Real

The MCP connectivity card now shows your live toolset in real-time — every tool your AI agent has access to, visible and testable directly from the UI.

- Live tools/list rendering directly in the workspace settings card
- JSON-RPC test interface for validating MCP connections
- Dedicated `brightagent-mcp` subdomain for clean A2A integration

---

## 🤖 Engineering Agent Audit Trail

Every action your BrightAgent engineering agents take is now logged with a tamper-evident audit record — who asked, what was done, what data it touched.

- Decorator-based instrumentation on all mutation tools
- Dual-write to CloudWatch + DynamoDB for compliance-grade retention
- Citation chain links every agent action back to the retrieved context that informed it

---

## 📊 Data Catalog Improvements

- **Quality rule SQL preview**: see the exact SQL your quality rules will run before executing
- **Health indicators**: preview and profiler availability shown directly in the catalog grid
- **Tag management**: inline tag removal, overflow popovers, and bulk tag dialog
- **Case-insensitive search**: find assets regardless of how you capitalize the name
- **Cortex column removed**: cleaner, less confusing catalog for non-Cortex workspaces

---

## ❄️ Snowflake Reliability

A comprehensive compatibility pass ensures Snowflake workspaces no longer encounter crashes or incorrect behavior:

- TIMESTAMP_NTZ(9) overflow recovered gracefully instead of crashing queries
- Full table FQN fallback chain so assets without explicit warehouse names still resolve
- Warehouse-agnostic SQL generation for quality checks

---

## 👥 System Admin: Feature Flag Management

Admins can now toggle feature flags per workspace directly from the `/system-admin` portal — no code deploy needed to enable or disable capabilities for specific customers.

---

## 🛠️ dbt Cloud Agent: More Reliable, More Flexible

- Support for dbt Cloud account-specific access URLs (enterprise accounts)
- Token probe at agent startup with a clear admin error on 401/403 — no more silent failures
- Scaffold tool ValidationError fixed — dbt project scaffolding works reliably again

---

## By the Numbers

| Metric | Value |
|--------|-------|
| Feature PRs merged | 223 |
| Lines of code | +67,654 / −12,111 |
| Repositories | 7 |
| New Jira tickets | 27 (BH-713–739) |
| Engineering days | 10 |
