# Agentic Project Management

BrightHive's agentic hub for sprint management, release automation, onboarding, and multi-repo coordination. Claude Code skills, agents, and vault-driven tooling replace traditional project management ceremony.

For permanent platform architecture, see [`../platform-saas-ai-context`](../platform-saas-ai-context).

---

## Quick Start — New Engineering Leader

```bash
git clone git@github.com:brighthive/agentic-project-mgmt.git
cd agentic-project-mgmt
make install-prereqs        # install brew, aws, lpass, gh, python3
cp .env.example .env        # fill in AWS profiles + LastPass user
make configure-aws-sso      # prints exact `aws configure sso` commands
make check-creds            # verify all sessions green
NAME=<you> make unpack      # decrypt vault package → {name}lead/
NAME=<you> make pull-secrets
NAME=<you> make localstack  # starts platform-core :4040 · brightbot :2024 · webapp :7420
```

See `ONBOARDING.md` for the full 7-step walkthrough.

---

## Repository Structure

```
agentic-project-mgmt/
├── Makefile                      # All orchestration — see `make help`
├── ONBOARDING.md                 # New-leader setup walkthrough (7 steps)
├── CLAUDE.md                     # Navigation contract for Claude Code
├── AGENTS.md                     # Agent contract (scope rules, cross-repo nav)
├── .env.example                  # Template: fill in your AWS profiles + LastPass user
│
├── config/
│   ├── siblings.txt              # Canonical list of sibling repos
│   └── env-templates/            # Per-repo .env templates (rendered by make env-*)
│       ├── brightbot-local.env.tmpl
│       ├── platform-core-local.env.tmpl
│       ├── webapp-local.env.tmpl
│       └── webapp-staging.env.tmpl
│
├── scripts/
│   ├── render_env.py             # Template materializer — resolves {{ vault.key }} tokens
│   ├── state.sh                  # Sentinel-file helpers for idempotent Makefile targets
│   └── package_kurilead.py       # Vault packager — make onboard NAME=matt
│
├── jira/                         # Sprint data & Jira tooling
│   ├── TICKET_TEMPLATE.md        # Canonical Jira ticket format
│   ├── CLAUDE.md                 # Sprint data schema + release artifact spec
│   └── sprint/
│       ├── SPRINTS.md            # Master velocity table (all sprints)
│       └── {1..10}/              # Per-sprint: stats, tickets, release notes, Slack post
│
├── docs/                         # Documentation & strategy hub
│   ├── CLAUDE.md                 # Spec/feature/POC workflow guide
│   ├── specs/                    # Implementation specs (written before code)
│   ├── features/                 # Shipped feature documentation
│   ├── bedrock/                  # Bedrock migration diary
│   └── pocs/                     # Proof-of-concept experiments
│
├── aws-secrets-vault/            # CLI: enumerate Secrets Manager across 4 AWS accounts
├── dynamo-vault/                 # CLI: DynamoDB workspace config scanner
├── lastpass-vault/               # CLI: LastPass credential vault
├── notion/                       # Notion workspace page map
├── clients/                      # Per-client trial + active-customer artifacts
│   └── trials/
│       └── longaeva/             # 14-day POC starting 2026-06-15 — see README.md
└── archive/                      # Historical sprints + old specs (read-only)
```

---

Run `make help` to see all available targets.

---

## Active trials

| Client | Stage | Day 1 | Index |
|---|---|---|---|
| Longaeva Partners LP | pre-trial-locked | 2026-06-15 | [`clients/trials/longaeva/README.md`](clients/trials/longaeva/README.md) |

Each trial folder follows the same convention: `README.md` is the entry point, with pointers to overview / scorecard / runbook / handoff docs and a cross-repo artifact table.

---

## Skills (Claude Code)

| Skill | What it does |
|---|---|
| `/sprint-release` | Close sprint — generate all artifacts, post to Slack, update Notion, commit |
| `/write-spec` | Generate implementation spec from conversation / Jira context |
| `/write-feature-doc` | Document a shipped feature — publishes to Notion |
| `/bedrock-journal` | Create weekly Bedrock migration diary entry in Google Drive |
| `/write-poc` | Document a proof-of-concept experiment |
| `/create-jira-ticket` | Generate technical notes from conversation for Jira |
| `/bh-auth` | Generate BrightHive Cognito JWT for dev/staging/prod |
| `/aws-auth` | AWS SSO login + credential refresh across accounts |
| `/scrum-master` | Sprint planning assistant |

---

## Team

| Member | GitHub | Role | Owned areas |
|---|---|---|---|
| Kuri | `drchinca` | Tech Lead | Architecture, AgentCore migration, context engineering, onboarding |
| Marwan Samih | `Marwan-Samih-Brighthive` | Sr. Engineer | BrightAgent runtime, Bedrock migration, dbt, frontend |
| Ahmed Elsherbiny | `sherbiny-bh` | Sr. Engineer | AWS CDK, DevOps, infrastructure, unstructured data, security |
| Harbour Wang | `Nano-233` | Engineer | BrightStudio, Projects UI, scheduler, CDK |

---

## AWS Accounts

| Account | ID | Profile | Used for |
|---|---|---|---|
| Main / Payer | `396527728813` | `brighthive-main` | Consolidated billing, org root |
| Production | `104403016368` | `brighthive-production` | Live customer traffic |
| Staging | `873769991712` | `brighthive-staging` | Pre-prod testing, developer default |
| DEV | `531731217746` | `brighthive-development` | Spikes, POCs (workflow_dispatch only) |

---

## Key Integrations

| Tool | Purpose |
|---|---|
| Jira Board 152 | Sprint tracking, epics, tickets |
| GitHub `brighthive` org | Source across 7 core + 10 infra + 7 Airbyte repos |
| Slack `#releases` (`C0AJXPYGJJ0`) | Sprint release posts via bot token |
| Notion (Sprint Planning parent `142bbca0...`) | Sprint pages, roadmap, CEO reports |
| AWS Secrets Manager | Per-account secret inventory via `aws-secrets-vault/cli/secrets` |
| LastPass | Developer credential vault via `lastpass-vault/cli/secrets` |
| DynamoDB | Per-workspace platform configs via `dynamo-vault/cli/secrets` |
| Google Drive (CoBuild AWS folder) | Weekly Bedrock migration diary for AWS partnership |

---

## Sibling Repos

All repos are expected at `../` relative to this repo. `config/siblings.txt` is the canonical list.

| Repo | Local path | Role |
|---|---|---|
| `brightbot` | `../brightbot` | LangGraph → Bedrock agent runtime |
| `brighthive-webapp` | `../brighthive-webapp` | React frontend + BrightStudio |
| `brighthive-platform-core` | `../brighthive-platform-core` | GraphQL API, Neo4j, auth |
| `brightbot-slack-server` | `../brightbot-slack-server` | Slack OAuth + workspace resolution |
| `brighthive-data-organization-cdk` | `../brighthive-data-organization-cdk` | Step Functions, Lambda, Glue pipelines |
| `brighthive-data-workspace-cdk` | `../brighthive-data-workspace-cdk` | Per-workspace AWS infra |
| `brighthive-ibm-wxo` | `../brighthive-ibm-wxo` | IBM watsonx Orchestrate partnership |
| `brighthive-admin` | `../brighthive-admin` | Admin dashboard (optional) |

---

## Key References

- **Jira Board**: https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152
- **AgentCore Epic**: [BH-453](https://brighthiveio.atlassian.net/browse/BH-453) — BrightAgent → AWS Bedrock runtime migration
- **Sprint velocity**: `jira/sprint/SPRINTS.md`
- **Architecture**: `../platform-saas-ai-context/docs/architecture/`
- **Bedrock diary (AWS-facing)**: [CoBuild AWS Drive](https://drive.google.com/drive/folders/1fvLR8a160KK4-wuDk4JW0WIdgiqTxRV2)
