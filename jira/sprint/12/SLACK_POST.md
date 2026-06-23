# Sprint 12 Slack Post (Reference Copy)
Posted to #releases on June 23, 2026 | ts: 1782234512.949259

---

🫐 BrightHive Sprint 12 Release
Release Date: June 23, 2026 • Sprint Period: June 13–23, 2026 • 10-day execution window

---

🔔 BrightSignals End-to-End
• ✓ SSE push delivery — real-time Slack alerts from every quality run (BH-713)
• ✓ CloudWatch alarms + on-call runbook live (BH-714)
• ✓ Notifications MVP shipped across brightbot, platform-core, webapp (BH-715)
• ✓ Quality run completion → Slack via BrightSignals (BH-557)

🔐 Enterprise Auth
• ✓ "Log in with Okta" PKCE callback — enterprise SSO live (BH-675)
• ✓ Resolver-side federated JIT provisioning into Neo4j (BH-674)
• ✓ Slack-server auth chain: Cognito JWT → x-api-key primary (BH-718)
• ✓ OAuth workspace guard — stops silent re-point to unprovisioned workspaces (BH-719)
• ✓ Multi-workspace thread isolation + X-Workspace-Id header (BH-724)

🔌 MCP Connectivity
• ✓ Live tools/list rendering + JSON-RPC test in connectivity card (BH-725)
• ✓ Dedicated brightagent-mcp.{env}.brighthive.net ingress (BH-726)
• ✓ 3 read-only workspace tools live: get_workspace_context, get_schema_details, analyze_model_impact
• ✓ streamable-http parser + SSE EOF handling

🤖 Engineering Agent Audit Trail (BH-695 epic)
• ✓ @audit_action decorator — STARTED/SUCCESS/FAILURE/CANCELLED on all mutation tools (BH-698)
• ✓ CloudWatch + DynamoDB dual-write emitter (BH-699)
• ✓ Citation chain — retrieval node IDs propagated into every audit event (BH-702)
• ✓ 6 engineering agent tools instrumented (BH-701)
• ✓ moto-backed integration tests + BDD scenarios (BH-704)

🐛 Production Stability
• ✓ Lambda 504 timeout fix — assertConstraints removed from request path (BH-731)
• ✓ Snowflake TIMESTAMP_NTZ(9) overflow recovered gracefully (BH-723)
• ✓ WorkspaceSwitcher OGM 20-cap fix — raw Cypher (BH-729)
• ✓ CORS preflight hardening — 7 targeted fixes across MCP + agent routes (BH-721)
• ✓ dbt Cloud account-specific URLs + token probe + scaffold fix (BH-722)
• ✓ Quality-check FQN fallback + timeout clear message (BH-690, BH-691)
• ✓ ECS deploy: immutable image digest — no more manual force-rollouts (BH-716)

---

📊 By the Numbers
• Feature PRs Merged: 223
• Total PRs (incl. staging): 299
• Lines Changed: +67,654 / −12,111
• New Tickets Created: 27 (BH-713–739)
• Repos Touched: 7
• Engineering Days: 10

👥 Team Contributions
• Kuri — auth + audit trail + MCP + infra + platform-core reliability (~145 PRs)
• Marwan — Snowflake TIMESTAMP_NTZ + dbt endpoints + Slack infra + feature flags (~30 PRs)
• Harbour — quality checks SQL + catalog fixes + BYOW preview + cooldown (~24 PRs)
• Ahmed — CORS fixes + notifications stack + Redshift SOC + tableFQN (~24 PRs)

🎯 What's Next: Sprint 13 Focus
• Transition ~50 Needs-Refinement tickets to Done (15-min sweep)
• BH-695 audit trail: finalize persistence strategy + e2e tests
• Okta SSO: deploy okta-idp-cdk to staging (BH-676)
• MCP A2A: async run lifecycle + API key workspace binding (BH-657–665)
• AgentCore Bedrock migration: next phase (BH-453)

⚠️ Sprint Health
• Completion: Strong delivery — 223 feature PRs in 10 days
• ~50 tickets in Needs Refinement = merged PRs not yet transitioned (same pattern as S11)
• Unofficial sprint (no Jira sprint object) — Sprint 13 should open a formal sprint

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/12/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/12/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
