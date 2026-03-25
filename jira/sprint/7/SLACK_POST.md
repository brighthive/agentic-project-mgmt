🔧 BrightHive Sprint 7 (Unofficial) Release
Release Date: March 24, 2026
Sprint Period: Mar 4 – Mar 24, 2026

🎨 BrightStudio & Custom Agents
• ✓ LangChain Assistants & subagent architecture research (BH-289, BH-295)
• ✓ Backend custom agent creation infrastructure (BH-290)
• ✓ Frontend BrightStudio custom agent builder (BH-291)
• ✓ Custom Agent Studio + Project Agent full integration
• ✓ New BrightAgent UI Architecture

🤝 Agent Sharing & Collaboration
• ✓ Shareable agent conversations via links
• ✓ Shareable agents from Studio → My Agents page
• ✓ External agent sharing with AGENT_GUEST role
• ✓ Shareable Thread Links in BrightBot

📁 Projects v1 — Complete
• ✓ BHAgent integration — agents work within project context (BH-241)
• ✓ Agent interaction UI for Projects (BH-242)
• ✓ BrightSide UI/UX polish — chat colors, tooltips, query titles (BH-248)
• ✓ Resource-project relationship + unlink mutations

💬 Slack Integration — Production Ready
• ✓ Type safety, rate limiting, autoscaling, monitoring hardening
• ✓ Per-workspace bhagent_api_key authentication (3 repos)
• ✓ JWT workspace propagation and token consolidation
• ✓ End-to-end slack_trace_id propagation
• ✓ ECS infrastructure with IAM task role

🤖 Agent Quality & Reliability
• ✓ Quality check agent reliability + S3 path restructure (BH-300)
• ✓ Retrieval agent refactor — inline eval, auto-save (BH-297)
• ✓ Quality Check tab + metadata chips UI (BH-301)
• ✓ OpenMetadata ID validation tool
• ✓ Interruptible agent wrapper with cancel support
• ✓ AWS Bedrock Knowledge Base retrieval tool (BH-286)

🐛 Production Stability
• ✓ [CRITICAL] System bugs fixed for production push (BH-294)
• ✓ [CRITICAL] Indiana Supervisor vs DeepAgent prod release (BH-277)
• ✓ BrightAgent stream reconnection on connection loss (BH-280)
• ✓ BrightAgent FE code refactor (BH-284)
• ✓ S3 URI exposure removed from API (BH-298)
• ✓ CSV preview limited to 100 rows

📊 By the Numbers
• Tickets Completed: 12 / 14
• Story Points: 33 / 43 pts
• PRs Merged: 63 (36 feature + 27 build)
• Repos Touched: 4 (brightbot, webapp, platform-core, slack-server)
• Engineering Hours: ~66h estimated

👥 Team Contributions
• Harbour — 8 done (30 pts) — BrightStudio end-to-end, Projects v1, Custom Agents
• Marwan — 4 done + 1 in pipeline — Production stability, Agent sharing, BrightAgent refactor
• Hikuri — 8 PRs across 3 repos — Slack hardening, auth, trace propagation
• Ahmed — 1 in pipeline — Unstructured data stack migration

🎯 What's Next: Sprint 8 Focus
• Resume formal sprint cadence
• Background agents & scheduled cron jobs (Q2 roadmap)
• Unstructured data stack → workspace AWS accounts
• Agent Sharing rollout & polish

⚠️ Sprint Health
• Completion: 85.7% — strong despite no formal sprint
• 2 tickets carrying over (BH-293, BH-210)
• PR-ticket linkage at 22% — needs immediate branch naming enforcement
• No formal sprint = no estimation, no scope control

📎 Links
📋 Release Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/7/RELEASE_NOTES.md
📣 Marketing Notes: https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/7/MARKETING_RELEASE_NOTES.md
📊 Notion Sprint 7: https://www.notion.so/32e02437dde48133a1f8d3f7120ee877
🎯 Jira Board: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
