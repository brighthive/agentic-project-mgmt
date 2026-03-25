# Sprint 7 (Unofficial) — Marketing Release Notes

**Period**: Mar 4–24, 2026

---

## BrightStudio & Custom Agents — Full Delivery

The biggest feature of the period: **BrightStudio** is now a fully functional custom agent workspace. Users can create, configure, and deploy custom AI agents with support for multiple LLM models. The team investigated LangChain Assistants and subagent architectures, then built both the backend agent creation infrastructure and the frontend Studio interface.

- Investigate LangChain Assistants and custom agents (BH-289)
- [BE] Support creating custom agents (BH-290)
- [FE] Support creating custom agents in BrightStudio (BH-291)
- Investigate Subagents for custom agents (BH-295)
- [FE] BrightStudio - Investigate current state (BH-266)
- Custom Agent Studio + Project Agent backend integration
- New BrightAgent UI Architecture

---

## Shareable Agents & Agent Collaboration

A new collaboration layer: users can now **share agent conversations** via links and publish custom agents from BrightStudio to a shared "My Agents" page. On the backend, a new **AGENT_GUEST** role enables external users to interact with shared agents without full workspace access.

- Shareable Agent Conversations & Shareable Agents via Studio
- External agent sharing with AGENT_GUEST role
- INVITED_TO edges on confirmUser for AGENT_GUEST flow
- Shareable Thread Links in BrightBot

---

## Projects v1 — Complete

Projects reached v1 maturity with full BrightAgent integration. Users can now interact with AI agents within project context, with proper resource-project relationships and a polished interaction UI.

- [BE] Projects - BHAgent integration (BH-241)
- [FE] Projects - Agent interaction UI (BH-242)
- [FE] BrightSide UI/UX polish (BH-248)
- Resource-project relationship and unlink mutations

---

## Slack Integration — Production Ready

The Slack server received a major hardening pass: type safety enforcement, rate limiting, autoscaling policies, and monitoring. Per-workspace API key authentication ensures secure multi-tenant agent access, and end-to-end trace IDs enable full request tracing from Slack message to agent response.

- Type safety, rate limiting, autoscaling, monitoring hardening
- Per-workspace bhagent_api_key generation and validation
- JWT workspace propagation and token consolidation
- End-to-end slack_trace_id propagation
- ECS infrastructure with IAM task role

---

## Data Quality & Agent Reliability

The quality check agent received reliability improvements: retry loops with LLM error feedback, proper S3 key path structure, and a new Quality Check tab in the web app with rich metadata chips UI. The retrieval agent was refactored with inline evaluation and auto-save.

- Quality check agent reliability and S3 key path fixes (BH-300)
- Retrieval agent refactor — inline evaluation, auto-save (BH-297)
- Quality check report fetching and sidebar layout fix (BH-301)
- Quality check header UI with metadata chips
- OpenMetadata ID validation tool
- Reusable interruptible() wrapper with cancel support
- AWS Bedrock Knowledge Base retrieval tool (BH-286)

---

## Production Stability & Security

Multiple critical production issues resolved, including the Indiana Supervisor vs DeepAgent release, system bug fixes, and security hardening (S3 URI exposure removal, CSV preview limits).

- [CRITICAL] Fix system bugs for production push (BH-294)
- [CRITICAL] Indiana Supervisor vs DeepAgent Prod Release (BH-277)
- [WebApp] Reconnect BrightAgent stream if connection lost (BH-280)
- [WebApp] Refactor BrightAgent code on FE (BH-284)
- Remove S3 URI exposure from capability result API (BH-298)
- Limit CSV preview to 100 rows

---

## By the Numbers

| Metric | Value |
|--------|-------|
| Tickets Completed | 12 |
| Story Points | 33 |
| PRs Merged | 63 (36 feature) |
| Repos Touched | 4 |
| Team Size | 4 engineers |
| Duration | 20 days |
