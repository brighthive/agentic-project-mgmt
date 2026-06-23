# Claude Navigation Guide - Agentic Project Management

---

## Onboarding Protocol

**Trigger**: User says anything like "set me up", "onboard me", "help me get started", "I'm new", or asks why something isn't working and `make status` shows all sentinels missing.

**What to do**: Follow `ONBOARDING.md` step by step. Do not summarize or paraphrase — execute. Each step has a command; run it, read the output, proceed or fix before moving on.

### Execution order

```
make check-prereqs          → see what's missing
make install-prereqs        → install only what's missing (idempotent)
make configure-aws-sso      → print setup commands if AWS profiles not configured
make check-creds            → verify AWS SSO + LastPass sessions
# (fix any ✗ with make refresh-aws / make refresh-lastpass)
NAME=<name> make unpack         → decrypt vault package into {name}lead/
NAME=<name> make verify-lead    → confirm all vault files present
NAME=<name> make pull-secrets   → populate secrets/ from vault
NAME=<name> make env-brightbot-local   → write ../brightbot/.env
NAME=<name> make env-webapp-local      → write ../brighthive-webapp/.env.local
make check-siblings         → see which sibling repos exist
make clone-siblings         → clone any missing
make status                 → confirm all sentinels green
```

### Decision rules for Claude

- **Ask for `NAME`** once at the start if the user hasn't mentioned it. It's their first name lowercased (e.g. `matt`, `kuri`, `ahmed`). Every `pull-*` and `env-*` command needs it.
- **Ask for the vault package path and password** when the user reaches Step 3 and `{name}lead/` doesn't exist. They should have a `{name}lead-export.zip.enc` file + password from their TechLead. If they don't have it yet, pause and tell them to request it. Once they have both, run: `VAULT_PASSWORD=<password> NAME=<name> make unpack` (pass the password via env var — `make unpack` cannot prompt interactively inside Claude Code).
- **Never fill in `.env` values for the user** — only tell them which fields need values and why.
- **Stop on `[ERROR]`** — do not continue to the next step until the current error is resolved.
- **Do not re-run steps that already show green** — `make status` is the ground truth.
- **If a secret token is unresolved** in `make env-*`: run `FORCE=1 NAME=<name> make pull-secrets` first, then retry. If it still fails, the key doesn't exist in the vault — report the exact missing path and stop.
- **If `make env-*` exits 3** ("Unmanaged file"): the `.env` was created before the bootstrap. Run `ADOPT=1 NAME=<name> make env-brightbot-local` to take ownership without overwriting. After adopt, subsequent runs are idempotent.
- **MANUAL fields in the template** resolve to `FILL_FROM_ENV_STAGING` — tell the user to copy those values from `../brightbot/.env_staging` manually. These are API keys (ANTHROPIC, OPENAI, etc.) that live in LastPass as group folders, not flat secrets.

### What Claude can do automatically vs. what needs the user

| Automatic (Claude runs it) | Needs user |
|---|---|
| `make check-prereqs` | Filling in `.env` (AWS profiles, LastPass user, GitHub token) |
| `make install-prereqs` | Running `aws configure sso` (interactive browser login) |
| `make configure-aws-sso` (prints commands) | Running `make refresh-aws` / `make refresh-lastpass` (opens browser) |
| `make check-siblings` | Providing the vault package + password |
| `make clone-siblings` | |
| `NAME=X make pull-secrets` | |
| `NAME=X make env-*` | |
| `make status` | |

---

## Quick Answer Table

| Question | Location |
|----------|----------|
| **New leader setup (full walkthrough)** | `ONBOARDING.md` |
| **Makefile targets reference** | `make help` |
| **Env template for brightbot** | `config/env-templates/brightbot-local.env.tmpl` |
| **Env template for webapp** | `config/env-templates/webapp-staging.env.tmpl` |
| **Env template for platform-core** | `config/env-templates/platform-core-local.env.tmpl` |
| **Sibling repo list** | `config/siblings.txt` |
| **Sprint velocity / stats** | `jira/sprint/SPRINTS.md` |
| **Sprint N tickets & metrics** | `jira/sprint/N/stats.json` + `tickets.json` |
| **Sprint N analysis** | `jira/sprint/N/SUMMARY.md` |
| **Sprint N release notes** | `jira/sprint/N/RELEASE_NOTES.md` |
| **Sprint N marketing notes** | `jira/sprint/N/MARKETING_RELEASE_NOTES.md` |
| **Jira ticket template** | `jira/TICKET_TEMPLATE.md` |
| **Sprint data format spec** | `jira/CLAUDE.md` |
| **Sprint close skill** | `/sprint-release` (Claude Code skill) |
| **AWS accounts & infrastructure** | `dynamo-vault/INFRASTRUCTURE.md` |
| **DynamoDB workspace configs** | `dynamo-vault/cli/secrets` |
| **AWS Secrets Manager inventory** | `aws-secrets-vault/cli/secrets` |
| **LangSmith deployment snapshots** | `langsmith-vault/` (shape only — no values) |
| **LangSmith mutation protocol** | `docs/LANGSMITH_DEPLOYMENT_SNAPSHOTS.md` |
| **Workspace user-role ops (promote/demote)** | `docs/WORKSPACE_USER_ROLES.md` |
| **Refresh ALL vaults (lastpass + AWS + dynamo + langsmith)** | `NAME=kuri make sync-vaults` |
| **Refresh LangSmith only** | `LANGCHAIN_API_KEY=... make sync-langsmith` |
| **Notion workspace page map** | `notion/pages.md` |
| **All leads, trials, active clients** | `clients/README.md` |
| **Active trials & scorecards** | `clients/trials/` |
| **Longaeva POC overview** | `clients/trials/longaeva/overview.md` |
| **Longaeva milestone scorecard** | `clients/trials/longaeva/scorecard.md` |
| **Longaeva full POC response doc** | `clients/trials/longaeva/artifacts/poc-response-plan.md` |
| **Longaeva UAT success guide** (whole-company testing) | `clients/trials/longaeva/UAT_GUIDE.md` |
| **Longaeva — Sarah's Monday morning** (non-tech sales demo) | `clients/trials/longaeva/SARAH_DEMO.md` |
| **Longaeva Snowflake standards** | `clients/trials/longaeva/SNOWFLAKE_STANDARDS.md` |
| **Trial template** | `clients/_templates/TRIAL.md` |
| **Client architecture profiles** | `../platform-saas-ai-context/clients/` |
| **Longaeva stack + capability map** | `../platform-saas-ai-context/clients/longaeva/` |
| **AgentCore migration spec** | `docs/specs/agentcore-deployment-migration.md` |
| **Onboarding bootstrap spec** | `docs/specs/onboarding-bootstrap.md` |
| **System architecture** | `../platform-saas-ai-context/docs/architecture/ARCHITECTURE.md` |
| **Bedrock migration strategy** | `../platform-saas-ai-context/docs/architecture/BEDROCK_MIGRATION_STRATEGY.md` |
| **Claude Code via Bedrock (dev tooling)** | `../platform-saas-ai-context/docs/decisions/decisions.md` ADR-009 + [`brighthive-claude-bedrock-cdk`](https://github.com/brighthive/brighthive-claude-bedrock-cdk) |
| **Bedrock AgentCore strategy** | `../platform-saas-ai-context/docs/architecture/BEDROCK_AGENTCORE_STRATEGY.md` |
| **Production AI architecture** | `../platform-saas-ai-context/docs/architecture/PRODUCTION_AI_ARCHITECTURE.md` |
| **Ingestion agent design** | `../platform-saas-ai-context/docs/architecture/INGESTION_AGENT_BRIGHTBOT.md` |
| **Team ownership** | `../platform-saas-ai-context/docs/team/TEAM.md` |
| **Quarterly roadmap** | `../platform-saas-ai-context/docs/roadmap/ROADMAP.md` |
| **AWS account hierarchy** | `../platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md` |
| **Spec template** | `docs/specs/SPEC_TEMPLATE.md` |
| **Feature doc template** | `docs/features/FEATURE_TEMPLATE.md` |
| **Bedrock journal template** | `docs/bedrock/BEDROCK_TEMPLATE.md` |
| **Bedrock topic index** | `docs/bedrock/INDEX.md` |
| **POC template** | `docs/pocs/POC_TEMPLATE.md` |
| **Docs workflow guide** | `docs/CLAUDE.md` |
| **Q1 roadmap scorecard** | `jira/sprint/Q1_ROADMAP_SCORECARD.md` |

---

## Repository Structure

```
agentic-project-mgmt/
├── Makefile                      # All orchestration — run `make help`
├── ONBOARDING.md                 # New-leader setup walkthrough (7 steps)
├── CLAUDE.md                     # This file — navigation contract
├── AGENTS.md                     # Agent contract (scope rules, cross-repo nav)
├── README.md                     # Entry point — overview + quick-start
├── .env.example                  # Fill in your AWS profiles + LastPass user
│
├── config/
│   ├── siblings.txt              # Canonical list of sibling repos (? = optional)
│   └── env-templates/            # Per-repo .env templates rendered by make env-*
│       ├── brightbot-local.env.tmpl
│       ├── platform-core-local.env.tmpl
│       ├── webapp-local.env.tmpl
│       └── webapp-staging.env.tmpl
│
├── scripts/
│   ├── render_env.py             # Template materializer — resolves {{ vault.key }} tokens
│   ├── state.sh                  # Sentinel-file helpers for idempotent targets
│   └── package_kurilead.py       # Vault packager — make onboard NAME=matt
│
├── jira/                         # Sprint data & tracking
│   ├── TICKET_TEMPLATE.md        # Canonical Jira ticket format
│   ├── CLAUDE.md                 # Sprint data schema + release artifact spec
│   └── sprint/
│       ├── SPRINTS.md            # Master velocity table (all sprints)
│       ├── Q1_ROADMAP_SCORECARD.md
│       └── {1..10}/              # Per-sprint: stats.json, tickets.json, SUMMARY.md, etc.
│
├── docs/                         # Documentation & strategy hub
│   ├── CLAUDE.md                 # Spec/feature/POC workflow guide
│   ├── specs/                    # Implementation specs (write before code)
│   │   ├── SPEC_TEMPLATE.md
│   │   ├── agentcore-deployment-migration.md
│   │   ├── onboarding-bootstrap.md
│   │   └── ...                   # (10 active specs)
│   ├── features/                 # Shipped feature docs
│   ├── bedrock/                  # LangGraph → Bedrock migration diary
│   │   └── INDEX.md
│   └── pocs/                     # Comparative experiments with numbers
│
├── notion/
│   └── pages.md                  # Notion workspace structure & page IDs
├── aws-secrets-vault/            # CLI: Secrets Manager across 4 AWS accounts
├── dynamo-vault/                 # CLI: DynamoDB workspace configs
│   └── INFRASTRUCTURE.md         # AWS accounts, tables, client registry
├── lastpass-vault/               # CLI: LastPass credential vault
├── archive/                      # Completed sprints, old specs (read-only)
└── kurilead/                     # Personal vault dump (gitignored)
```

---

## Navigation Patterns

### Sprint Status
1. `jira/sprint/SPRINTS.md` — velocity table, completion rates
2. `jira/sprint/N/stats.json` — machine-readable metrics
3. `jira/sprint/N/SUMMARY.md` — LLM analysis with red flags

### Release Notes
1. `jira/sprint/N/RELEASE_NOTES.md` — technical (C-exec stats)
2. `jira/sprint/N/MARKETING_RELEASE_NOTES.md` — GTM/sales facing
3. `jira/sprint/N/SLACK_POST.md` — reference copy of Slack post
4. Generated by `/sprint-release` skill

### Creating Jira Tickets

**For any team member (Kuri, Marwan, Ahmed, Harbour) making a ticket via Claude:** see [`jira/TICKET_TEMPLATE.md`](jira/TICKET_TEMPLATE.md) — it has the rules, escape-character handling, and three real examples (bug, feature, refactor).

Hard rules (also in the template):
1. **Every ticket MUST have `parentKey="BH-XXX"`** — the Epic key. Tickets without an epic parent are rejected.
2. **Always `issueType="Task"`. Never `"Story"`.** All children of epics at BrightHive are Tasks.
3. **Project key**: `BH`. Board ID: `152`.
4. **Find the epic live** before creating — never hardcode IDs: `mcp__jira__jira_get_epics(boardId=152, done=false)`
5. **`customfield_10014` is blocked** by screen config — use `parentKey="BH-XXX"` instead.

### AWS Infrastructure
1. `dynamo-vault/INFRASTRUCTURE.md` — accounts, tables, client configs
2. `dynamo-vault/cli/secrets list --account PROD` — query DynamoDB
3. `aws-secrets-vault/cli/secrets classify` — Secrets Manager inventory
4. `../platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md` — architectural reference

### LangSmith / LangGraph Cloud Deployments — HARD RULE

**Never modify a LangSmith deployment's `secrets`, `env_vars`, or revision config** without (1) a fresh pre-change snapshot committed to `langsmith-vault/data/{env}/`, (2) explicit per-edit approval from Kuri or Sherbiny, (3) a read-modify-write PATCH preserving the full array, and (4) a post-change snapshot committed in the same PR. Full protocol: `docs/LANGSMITH_DEPLOYMENT_SNAPSHOTS.md`. The 2026-06-18 incident (74 secrets → 1 secret on `brightagent-staging`) is why.

### Understanding the System
1. `../platform-saas-ai-context/docs/architecture/ARCHITECTURE.md`
2. `../platform-saas-ai-context/docs/team/TEAM.md`
3. `../platform-saas-ai-context/docs/roadmap/ROADMAP.md`

### Bedrock Migration & AI Strategy
1. `../platform-saas-ai-context/docs/architecture/BEDROCK_MIGRATION_STRATEGY.md` — Migration plan from LangGraph to AWS Bedrock
2. `../platform-saas-ai-context/docs/architecture/BEDROCK_AGENTCORE_STRATEGY.md` — AgentCore adoption strategy
3. `../platform-saas-ai-context/docs/architecture/PRODUCTION_AI_ARCHITECTURE.md` — Target production AI architecture
4. `../platform-saas-ai-context/docs/architecture/INGESTION_AGENT_BRIGHTBOT.md` — Ingestion agent design

### Spec-Driven Development
1. `docs/CLAUDE.md` — Full workflow guide for all 4 doc modules
2. `docs/specs/SPEC_TEMPLATE.md` — Write specs BEFORE implementation
3. `docs/features/FEATURE_TEMPLATE.md` — Document shipped capabilities
4. `docs/bedrock/BEDROCK_TEMPLATE.md` — Migration journal entries
5. `docs/pocs/POC_TEMPLATE.md` — Experiment write-ups (keep even if No-Go)
6. Lifecycle: `/write-poc` → `/write-spec` → `/create-jira-ticket` → Implement → `/write-feature-doc`

**Skills for doc generation:**
- `/write-spec` — Generate spec from conversation/Jira context
- `/write-feature-doc` — Document shipped features from sprint/PR data
- `/bedrock-journal` — Record migration decisions, phases, experiments
- `/write-poc` — Structure and record POC experiments

---

## Sprint Data Format

Each sprint directory `jira/sprint/N/` contains:

| File | Type | Content |
|------|------|---------|
| `stats.json` | Machine-generated | Dates, ticket counts, points, completion %, WIP analysis, carryovers |
| `tickets.json` | Machine-generated | Minimal: key, summary, status, assignee, points |
| `SUMMARY.md` | LLM-generated | ASCII stats, WIP analysis, team breakdown, red flags, recommendations |
| `RELEASE_NOTES.md` | Skill-generated | Technical release notes per repo |
| `MARKETING_RELEASE_NOTES.md` | Skill-generated | Customer-facing highlights |
| `SLACK_POST.md` | Skill-generated | Reference copy of Slack post |
| `VALIDATION_REPORT.md` | Skill-generated | Tickets Done without linked PRs |
| `PLAN.md` | Manual | Sprint goals, planned tickets, dependencies |

---

## Scope

This repo is the **agentic project management hub** — replaces traditional PMs and scrum masters with Claude Code skills, agents, and automation.

| This repo | platform-saas-ai-context |
|-----------|--------------------------|
| "What are we doing THIS sprint?" | "What are we building?" |
| Sprint stats, tickets, release notes | System architecture, team, roadmap |
| Spec-driven dev, feature specs | Permanent knowledge base |
| Bedrock migration tracking | Bedrock strategy & architecture docs |
| Business tool automation (Jira, Slack, Notion) | Technical reference |
| Changes weekly | Changes quarterly |

### What This Repo Manages Agentically
- **Sprint lifecycle**: Planning → execution → release notes → Slack/Notion publish
- **Release automation**: PR collection, changelog, marketing notes, validation
- **Jira operations**: Ticket creation, epic tracking, sprint board management
- **Documentation generation**: Spec-driven dev, feature specs before code
- **Infrastructure inventory**: AWS secrets, DynamoDB configs, credential vaults
- **Cross-repo coordination**: 7 core services + connectors + infra repos
- **Stakeholder communication**: Slack posts, Notion pages, CEO reports

---

## Source Repositories

GitHub org: `brighthive`. All repos live locally at `../` relative to this repo.

### Core Services (tracked by `/sprint-release`)

| Service | GitHub Repo | Local Directory | Description |
|---------|-------------|-----------------|-------------|
| BrightBot (AI Agent) | `brighthive/brightbot` | `../brightbot` | LangGraph → Bedrock agents, FastAPI, Slack routing |
| Web App | `brighthive/brighthive-webapp` | `../brighthive-webapp` | React frontend, BrightStudio, Projects UI |
| Platform Core | `brighthive/brighthive-platform-core` | `../brighthive-platform-core` | GraphQL API, Neo4j, auth, workspace mgmt |
| Slack Server | `brighthive/brightbot-slack-server` | `../brightbot-slack-server` | Slack OAuth, workspace resolution, ECS infra |
| Admin Portal | `brighthive/brighthive-admin` | `../brighthive-admin` | Admin dashboard |
| Data Org CDK | `brighthive/brighthive-data-organization-cdk` | `../brighthive-data-organization-cdk` | Step Functions, Lambda, Glue, data pipelines |
| Data Workspace CDK | `brighthive/brighthive-data-workspace-cdk` | `../brighthive-data-workspace-cdk` | Per-workspace AWS infrastructure |

### Infrastructure & Supporting Repos

| Service | GitHub Repo | Local Directory | Description |
|---------|-------------|-----------------|-------------|
| IBM WXO Integration | `brighthive/brighthive-ibm-wxo` | `../brighthive-ibm-wxo` | IBM watsonx Orchestrate partnership integration |
| Testing Infra CDK | `brighthive/brighthive_testing_infrastructure_cdk` | `../brighthive_testing_infrastructure_cdk` | Test infrastructure as code |
| Documentation | `brighthive/brighthive-docs` | `../brighthive-docs` | Public-facing documentation |
| Scripts | `brighthive/brighthive-scripts` | `../brighthive-scripts` | Shared automation scripts |
| Jobs Service | `brighthive/brighthive-jobs` | `../brighthive-jobs` | Background job processing |
| Mock Data | `brighthive/brighthive-mock-data` | `../brighthive-mock-data` | Test/demo data generation |
| Jupyter Stack | `brighthive/brighthive-jupyter-stack` | `../brighthive-jupyter-stack` | Jupyter notebook infrastructure |
| OpenMetadata | `brighthive/brighthive-openmetadata-stack` | `../brighthive-openmetadata-stack` | Data catalog / metadata management |
| Token Usage | `brighthive/brightagent_token_usage` | `../brightagent_token_usage` | LLM token usage tracking |
| GDrive MCP | `brighthive/gdrive-mcp-server` | `../gdrive-mcp-server` | Google Drive MCP server |

### Data Connectors (Airbyte)

| Connector | GitHub Repo | Description |
|-----------|-------------|-------------|
| Canvas | `brighthive/airbyte-source-canvas` | Canvas LMS data source |
| Credential Engine | `brighthive/airbyte-source-credential-engine` | Credential Engine registry |
| Indiana Tech Jenzabar | `brighthive/airbyte-source-indiana-tech-jenzabar` | Jenzabar SIS connector |
| IPEDS | `brighthive/airbyte-source-ipeds` | NCES IPEDS data |
| Job Post S3 | `brighthive/airbyte-source-job-post-s3` | Job posting data from S3 |
| NCES Scraper | `brighthive/airbyte-source-nces-scrapper` | NCES web scraper |
| SFTP Bulk | `brighthive/airbyte-source-sftp-bulk` | Bulk SFTP file ingestion |

### Context & Knowledge (not on GitHub)

| Repo | Local Directory | Description |
|------|-----------------|-------------|
| Platform Context | `../platform-saas-ai-context` | Architecture, team, roadmap, Bedrock strategy |
| Agentic Project Mgmt | `.` (this repo) | Sprint management, release automation, vault CLIs |

**Fetching PRs by date range** (used by `/sprint-release`):
```bash
gh pr list --repo brighthive/$REPO --state merged --search "merged:$START..$END" --limit 100 --json number,title,author,additions,deletions,mergedAt,headRefName
```

---

## Team

| Member | GitHub | Role | Ownership |
|--------|--------|------|-----------|
| Kuri | `drchinca` | Tech Lead | Architecture, AgentCore migration, context engineering, onboarding |
| Marwan Samih | `Marwan-Samih-Brighthive` | Sr. Engineer | BrightAgent, frontend, data quality |
| Ahmed Elsherbiny | `ahmed-brighthive` | Sr. Engineer | Infrastructure, unstructured data, DevOps, security |
| Harbour Wang | `Nano-233` | Engineer | Projects, BrightStudio, CDK, UI/UX |

**Jira IDs**: Kuri: `712020:b4b1b0de-6936-4d70-be9f-5d96ccec7264`

---

## Slack Integration

| Item | Value |
|------|-------|
| Channel | `#releases` |
| Channel ID | `C0AJXPYGJJ0` |
| Auth | Bot token from `~/.claude/slack/tokens.json` (`bot_token` field) |
| Token rotation | `~/.claude/slack/rotate.sh` (rotates user token, preserves bot_token) |
| Post method | `chat.postMessage` API with bot token (`xoxb-*`) |
| Bot scopes | `chat:write`, `chat:write.public` |

**Posting to Slack**:
```bash
SLACK_BOT_TOKEN=$(jq -r '.bot_token' ~/.claude/slack/tokens.json)
curl -s -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @payload.json | jq '{ok, ts, error}'
```

---

## Notion Integration

Sprint pages live under [Sprint Planning](https://www.notion.so/142bbca09ba04d849960420aa06889be) (ID: `142bbca09ba04d849960420aa06889be`).

| Page | Notion ID |
|------|-----------|
| Sprint Planning (parent) | `142bbca09ba04d849960420aa06889be` |
| Active Sprint | `2f202437-dde4-8110-8851-c7ce0cac1c89` |
| Sprint Archive | `2f202437-dde4-8191-b4a2-fe4b5d72f0e2` |
| Q1 Roadmap & Milestones | `2f202437-dde4-81f1-911a-fd4d7782e19d` |
| Q1 CEO Report | `32602437-dde4-8124-8ab2-e17283318cb4` |

Full page map with all sprint pages: `notion/pages.md`

---

## Q2 2026 Planning

Q1 ended March 24, 2026 (Sprint 7 was the last). Q2 starts April 2026.

**Q1 Results**: 65% delivery, 6/10 epics at 80%+ — see `jira/sprint/Q1_ROADMAP_SCORECARD.md`

**Q2 Strategic Priorities**:
- Bedrock migration: Move BrightBot from LangGraph to AWS Bedrock AgentCore
- BrightStudio: Custom agent builder (look up current epic in Jira)
- IBM WXO partnership integration
- Spec-driven development workflow (specs before code)

**Epics**: query Jira for the live list, don't copy IDs into this doc. `mcp__jira__jira_get_epics(boardId=152, done=false)` returns the current set. Specific IDs change — we're past BH-400 now and any list pasted here will age out in weeks.

---

## Bedrock Migration

BrightBot is migrating from LangGraph to AWS Bedrock. All strategy docs live in `platform-saas-ai-context`:

| Document | Path | Content |
|----------|------|---------|
| Migration Strategy | `../platform-saas-ai-context/docs/architecture/BEDROCK_MIGRATION_STRATEGY.md` | Phase plan, timeline, risk assessment |
| AgentCore Strategy | `../platform-saas-ai-context/docs/architecture/BEDROCK_AGENTCORE_STRATEGY.md` | Agent runtime, tool orchestration |
| Production Architecture | `../platform-saas-ai-context/docs/architecture/PRODUCTION_AI_ARCHITECTURE.md` | Target state: fully AWS AI-native |
| Ingestion Agent | `../platform-saas-ai-context/docs/architecture/INGESTION_AGENT_BRIGHTBOT.md` | Data ingestion agent design |

This repo tracks the migration execution — sprint tickets, PRs, release notes. The strategy docs are the source of truth for _what_ to build; this repo tracks _when_ and _how_ it ships.

---

## Git Workflow & Merge Strategy

- ALWAYS create a PR for feature branches — never push commits directly to main
- Use **squash merge** when merging PRs into main
- PR title becomes the single commit on the target branch — keep it clean and conventional (`type(scope): description`)
- This keeps main history readable: one commit per feature/fix

---

## Key References

- **Jira Board**: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
- **Board ID**: 152
- **Epics**: query live — `mcp__jira__jira_get_epics(boardId=152, done=false)`. Do not list IDs here; they change.
