# Sprint 12 🛠️ — What Shipped

**2026-06-03 → 2026-06-16** · The pre-trial platform build. Most of this sprint went into the capabilities that make a customer-owned warehouse (BYOW) work end-to-end — and they shipped as platform features, not one-off demo glue.

---

## 🤖 MCP Integration — dbt agent now reachable over MCP

The Model Context Protocol surface got its own front door and a hardening pass that finally made **dbt-via-MCP work end-to-end**.

- Dedicated `brightagent-mcp.{env}.brighthive.net` ingress — no longer sharing the assistant host
- Bedrock Converse schema sanitizer — strips unsupported `example` keys + cleans `toolConfig` so every agent model can call tools (BH-647)
- Webapp connectivity card redesigned: live `tools/list` rendering, JSON-RPC test console, prompt playground
- FastMCP mounted at `/bh-mcp` to dodge the LangGraph route shadow

## 📁 Bring-Your-Own-Warehouse Ingestion (OMD-native)

Customer Snowflake and Redshift warehouses now catalog themselves through OpenMetadata's native AutoPilot — no external scanner.

- AutoPilot trigger + full Snowflake connection forwarding, verified live (HTTP 200)
- Webhook workspace routing by service-name UUID prefix (UAT-verified re-routing)
- Catalog → description → 1536-dim embedding → retrieval, proven on staging (171 tables, 333 embeddings)
- AutoPilot scoped to production schemas — dbt dev sandboxes excluded (BH-642)
- Superadmin cascade-delete for warehouse switching (Snowflake ↔ Redshift teardown)

## 🔧 dbt Engineering Agent & Semantic Views

The dbt agent learned the full semantic-view lifecycle and can author-and-ship governed PRs.

- Read / mirror / deploy semantic views; write back to Snowflake (BH-641)
- `ship_semantic_view_to_github` — scaffold → governed PR with CI compile-check
- Semantic-view lineage: base tables + join graph exposed on `list_semantic_views`
- dbt sources.yml + staging model + schema.yml tests generated from introspected Silver tables

## 🛡️ Configurable Quality-Rule Library (BH-503 — shipped)

Quality checks moved from LLM-regenerated SQL to a real, governed rule library.

- 20+ seeded rule templates; agent reads from the library, not regen
- Full CRUD (REST + GraphQL), per-rule execution fanout, pass-rate aggregation
- Webapp: create/edit drawer, scope selector, activate/deactivate toggle, execution history, pass-rate sparkline

## 💬 Slack, Notifications & Human-in-the-Loop

- All 6 producer stages now classified in slack-server
- The dbt agent's full toolset (dbt-Cloud, GitHub author-and-ship, Airbyte connector build/test) surfaced in the Slack thinking indicator
- Real HITL input surface for `DBT-query_selection` interrupts
- CloudWatch metric filters + alarms + on-call runbook for `notif.*` events

## 🔐 Auth — Okta Federation for MCP

- Cognito + Okta federation for the MCP server (BH-573), with Route53 + ACM for `mcp/auth.brighthive.io` (BH-574)
- Okta-federated spec signed off

## 📈 Longitudinal Monitoring (GC-12)

- Pure longitudinal anomaly-detection core + warehouse-agnostic metric-snapshot SQL builder
- Stateful trailing-window detection agent wiring in progress (BH-600)

## 🐛 Security & Stability

A P0 security chain landed: multi-tenant exfil fix, PAT-leak-on-redirect prevention, JWT/Authorization-header scrubbing, structured error envelopes, and tenant-isolation fix for cross-workspace table attachment.

---

## By the Numbers

- **268** PRs merged · **485K** lines changed (excl. release-carriers)
- **6** repos · **18** tickets Done · **27** more in code-review/staging-QC pipeline
- Headline: **dbt-via-MCP works** · **quality-rule library shipped** · **OMD-native BYOW ingestion verified on staging**

## Sprint Health

Heavy build sprint with a large staging-QC pipeline (28 tickets) queued for the pre-trial deploy. Backlog grooming filed 54 follow-up tickets for the remaining golden-case + lifecycle work.
