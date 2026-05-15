# Sprint 10 — Marketing Release Notes

**Released**: May 15, 2026
**Sprint Period**: May 5 – May 15, 2026 (11 days)
**Headline**: BrightHive's AWS Bedrock AgentCore migration plan is locked in, BrightStudio's UX gets a major IA overhaul, and BrightSignals levels up with a unified activity drawer.

---

## 🔥 Headline: AWS Bedrock AgentCore Migration — Plan Locked In

This sprint we closed the planning loop on the **biggest AWS infrastructure move of 2026** for BrightHive: migrating the entire BrightAgent runtime from LangChain's hosted services onto Amazon Bedrock AgentCore. After a 4-agent technical review (Solutions Architect, DevOps, AWS best-practices, BrightHive-AWS), we landed a 23-ticket execution plan targeting the **June 1 AWS co-sell launch**.

What this unlocks:
- AWS sellers can attribute commission to BrightHive (today they can't — runtime runs on LangChain)
- BrightHive becomes a "Deployed on AWS" partner
- Customer data path: BrightHive → Amazon Bedrock directly (no third-party vendor in the loop)

What's in the plan: Amazon Bedrock AgentCore for runtime, AWS API Gateway + Cognito for ingress, Amazon DynamoDB for agent checkpoints, AWS CloudWatch + X-Ray for observability via ADOT, Amazon ECS Fargate for MCP servers, salted-hash canary rollout (1%/10%/50%/100%), checkpoint-migration shim for zero-downtime cutover, full DR plan (PITR + cross-region AWS Backup + S3 Object Lock), and a rollback gameday in staging.

---

## 🎨 BrightStudio — Major IA Overhaul

The webapp got its biggest information-architecture refresh in 2026.

- **The Hive** — new central hub for the BrightHive data fabric
- **Governance** section — quality, access, audit in one place
- **Notifications Inbox** — a dedicated home for BrightSignals deliveries
- **8-section navigation redistribution** — clean structure, no new pages, just a smarter organization of existing capabilities
- **Asset Detail Profiler tab + Raw JSON view** — operators can now inspect profiled data with full transparency

Why it matters: BrightStudio is the operator surface. The cleaner this IA, the faster customers onboard and the more confidently they delegate work to BrightAgent.

---

## 🔔 BrightSignals — Unified Activity Drawer + Notifications Schema

The Sprint 9 BrightSignals AWS-native event pipeline shipped. This sprint added the **product surface**:

- **Unified activity drawer** — every BrightAgent event in one curated stream
- **Notifications schema grounded in real BrightHive architecture** — a formal spec covering all notification types, delivery channels, deduplication, retention, and the path from DynamoDB Streams → Lambda → EventBridge → Slack/Webapp

This is the foundation for Teams + Email channel adapters in Sprint 11.

---

## 🤖 dbt — Multi-Repo Support + Secrets Manager Credentials

A major dbt enhancement:

- **Multi-repo preview** — BrightAgent's dbt subagent can now work across multiple GitHub repositories per workspace, not just one
- **AWS Secrets Manager-stored dbt Cloud credentials** — credentials moved out of env vars and into the proper AWS-native vault
- **Per-session GitHub repo settings** in BrightAgent — operators pick the active repo for their dbt session
- **Re-enable disabled GitHub repos** — bug fix for the case where a repo was disconnected and reconnected

Why it matters: customers with multi-team / multi-data-domain setups can now point BrightAgent at the right dbt project per workspace.

---

## ⏰ Scheduler MVP — Production Hardening

The Sprint 9 scheduler MVP got four rounds of webhook hardening this sprint:

- Scheduler webhook fix (initial)
- LangGraph webhook wiring
- Payload corrections
- Task graph updated to return scheduled-run results

Plus platform-core was updated to return **stateful task results** so scheduler clients can see run output not just run status.

---

## 📊 Analytics — Health Checks Wired to Real Data

The Sprint 9 Health Checks UI in BrightStudio was wired to real GraphQL data this sprint. Platform-core gained a `ServiceHealthCheck` type + resolver; the webapp page now displays live status instead of mock fixtures.

---

## 🧱 Local Dev Stack — LocalStack for Quality Check

For engineers: a full local stack for the `quality_check` subagent with Postgres + LocalStack-emulated AWS. Iterate on AWS-adjacent behavior without burning Bedrock quota or RDS hours.

---

## 🐛 Production Stability + Quality

- **Today's hotfix (May 15)** — production BrightAgent S3 streaming Mem0 issue resolved (brightbot #483)
- **AG Grid sidebar layout fix** — accessibility regression in BrightAgent UI fixed (webapp #1103)
- **Project retrieval bug** — fixed in platform-core; some projects were not loading correctly
- **Duplicate data asset hotfix** — platform-core no longer creates duplicate assets on retry
- **OMD VPC + security groups** — Enhanced OpenMetadata deploy now runs in proper VPC with security groups
- **Airbyte destination retrieval fallback** — added safety net for missing destination config
- **UI + permission bug fixes** — multiple webapp UI and permission regressions resolved
- **LangGraph state channel reducers** — fixed state-channel mismatch causing brightbot errors
- **Ingestion stack metadata** — data-org-cdk ingestion stack cleanup

---

## 📊 By the Numbers

- **Feature PRs Merged**: 34
- **Total PRs (incl. promotions + reverts)**: 58
- **Lines Changed**: 246,430 (+161,890 / -84,540)
- **Repos Touched**: 5 (brightbot, brighthive-webapp, brighthive-platform-core, brighthive-data-organization-cdk, agentic-project-mgmt)
- **Contributors**: 4 — full team active
- **AgentCore Epic**: 1 (BH-453, 23 child tickets — visibility for AWS partnership)

---

## 👥 Team Contributions

- **Kuri** — 14 feature PRs (AgentCore spec v2 + 23-ticket epic, BrightStudio Hive/Governance/Nav IA, BrightSignals drawer + notifications spec, Analytics Health Checks GraphQL, profiler tab, local-dev quality_check stack, Bedrock diary catch-up weeks 6-11, Sprint 9 close)
- **Marwan** — 10 feature PRs (dbt multi-repo enhancement #470 — +11990 lines, dbt Cloud credentials in Secrets Manager, dbt GitHub session settings, production deploy promotions, May 15 Mem0/S3 hotfix, AG Grid fix, LangGraph state channel reducers)
- **Harbour** — 8 feature PRs (scheduler webhook hardening x4, project retrieval fix, permission/UI bug fixes)
- **Ahmed** — 4 feature PRs (OMD VPC + security groups, airbyte destination retrieval, duplicate data asset hotfix, ingestion stack cleanup)

---

## 🎯 What's Next: Sprint 11

- **AgentCore migration execution** — Land BH-454 (spike) and BH-468 (Cognito pre-token Lambda) early; unblocks 13 other child tickets
- **AgentCore CDK stacks** — `{Env}-BPC-AgentCore` and `{Env}-BPC-AgentCoreMCP` in brighthive-platform-core
- **BrightSignals Teams + Email channel adapters**
- **Scheduler v1** — retry policies, cron support, audit log (post-bug-bash)
- **Settings overhaul Phases 1-3** (BH-491, BH-492, BH-493) — critical bug fixes + architecture unification + IA restructure
- **June 1 launch readiness review** with AWS Bedrock team

---

## ✅ Sprint Health

- **Engineering output high** — 34 feature PRs across 5 repos in 11 days, full team active
- **Fast production feedback loop** — 5/12 brightbot Staging → Production cycle (deploy → detect → rollback → fix → redeploy in 24h) and 5/15 same-day hotfix both show healthy release muscle
- **Scheduler MVP firmed up** — 4 rounds of iterative webhook hardening from real production use; Scheduler v1 (retry + cron + audit) ready to build on stable foundation in Sprint 11
- **AgentCore migration planning complete** — spec v2 merged, 23-ticket execution plan in Jira for AWS partnership visibility

---

## 📎 Links

- 📋 [Release Notes](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/RELEASE_NOTES.md)
- 📊 [Summary](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/SUMMARY.md)
- 🔍 [Validation Report](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/10/VALIDATION_REPORT.md)
- 🎯 [Jira Board 152](https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152)
- 🔥 [AgentCore Epic BH-453](https://brighthiveio.atlassian.net/browse/BH-453)
- 📈 [Sprint Master Table SPRINTS.md](https://github.com/brighthive/agentic-project-mgmt/blob/master/jira/sprint/SPRINTS.md)
