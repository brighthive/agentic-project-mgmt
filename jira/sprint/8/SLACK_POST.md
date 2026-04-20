🫐 BrightHive Sprint 8 Release (Mid-Sprint)
Release Date: Apr 20, 2026
Sprint Period: Apr 14–28, 2026 • Mid-sprint checkpoint

🔧 dbt Agent & Transformation Pipeline
• ✓ Complete dbt workflow: jobs, data products, GitHub repos (BH-330)
• ✓ dbt model detail view — SQL, PR links, lineage, origin badge (BH-346)
• ✓ TransformationNode metadata + per-model run tracking (BH-344, BH-345)
• ✓ Device Flow OAuth + disconnect for GitHub connection (BH-339)
• ✓ Auto-read workspace config, reduce interrupts (BH-325, BH-328)
• ✓ dbt agent migrated to ReAct pattern — smarter, fewer steps

🏛️ Governance & Policy Enforcement
• ✓ Policies injected into AI agent workspace context (BH-357)
• ✓ Policy toggles — Active, Enforced, Admin Only (BH-356)
• ✓ Credential HITL interrupt for secure ingestion (BH-355)
• 🔄 On-demand governance tools: schemas, glossary, policies (BH-347 — in review)

🔗 Azure Synapse BYOW Integration
• ✓ T-SQL dialect + warehouse adapter pattern (BH-322, BH-321)
• ✓ Synapse ingestion pipeline + routing (data-org CDK)
• ✓ Quality check agent Synapse support (brightbot)
• ✓ Provider-specific icons, card picker, config forms (webapp)
• ✓ E2E tests for BYOW connect flow

🎨 Webapp — Context, Analytics, Custom Personas
• ✓ Context section: KB, workspace context, transcribes (BH-347)
• ✓ Analytics: dashboards, reports, alerts, health checks (BH-359)
• ✓ Custom Personas visual flow builder with React Flow (BH-376)
• ✓ Platform analytics dashboard (BH-359)
• ✓ Data asset health check backend (BH-374, BH-375)

🤖 Bedrock & AI Agent
• ✓ Claude → Bedrock model routing complete (BH-282)
• ✓ GraphQL capabilities for deep_agent supervisor
• 🔄 Knowledge Base integration with BrightAgent (BH-286 — in review)
• 🔄 Unstructured data webapp integration (BH-285 — in progress)

🐛 Production Stability
• ✓ EDL pipeline decommissioned (BH-278)
• ✓ React 17 → 18 upgrade (+43K/-87K lines)
• ✓ Slack bot: only respond to @mentions/DMs/threads
• ✓ Redshift CATALOG_ID fix for cross-account schemas
• ✓ Claude PR review workflows added to CDK repos

📊 By the Numbers
• Tickets Completed: 21 / 55 (mid-sprint)
• PRs Merged: 103 (82 feature)
• Repos Touched: 7
• New Sections: 3 (Context, Analytics, Personas)
• Warehouse Support: +1 (Azure Synapse)
• Sprint Day: 7 of 14

👥 Team Contributions
• Hikuri — 18 done (dbt pipeline, governance, Synapse, analytics, webapp UX)
• Ahmed — 1 done + 6 in pipeline (Bedrock KB, unstructured data, infra)
• Marwan — 1 done + 5 in pipeline (Bedrock models, agent fixes, React upgrade)
• Harbour — 1 done + 1 in testing (scheduler, data preview, catalog health)

🎯 Sprint 8 Remaining (Week 2)
• BH-347: Governance context tools — land the PR
• BH-286: Bedrock Knowledge Base ↔ BrightAgent integration
• BH-293: Unstructured data stack workspace deployment
• BH-299/298/297: Critical production bug fixes through staging
• BH-201: Onboarding/offboarding — complete testing

⚠️ Sprint Health
• Completion: 38% at mid-sprint — on track (21/55 done, 16 in pipeline)
• 10 tickets canceled (Q1 cleanup — zombie tickets cleared)
• 9 needs-refinement tickets are planned dbt provisioning phases
• 19/21 done tickets unpointed — velocity is ticket-based, not points

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/8/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/8/MARKETING_RELEASE_NOTES.md
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
