# Sprint 18 🍒 — Summary (Oct 7 – Nov 26, 2026)

> Unofficial date-range cut, the seventh in a row. Jira has had no sprint object since Sprint 8.
> The window starts the day after Sprint 17 🥝 (Aug 24 – Oct 6) ended, so no work goes unreported.
> Each person's section separates **🕒 Last 3 weeks (Nov 5 – Nov 26)** from **Earlier (Oct 7 – Nov 4)**.

```
┌──────────────────────────────────────────────────────────────┐
│ SPRINT 18 🍒 — Oct 7 → Nov 26, 2026 (51 days, unofficial)     │
├──────────────────────────────┬───────────────────────────────┤
│ PRs merged                   │ 412 (384 code + 28 carriers)  │
│ Code lines                   │ +290,650 / −66,998            │
│ Repos touched                │ 11                            │
│ Production release           │ Oct 16 (bot, core, webapp)    │
│ Staging promotion            │ Nov 12 (bot) · Nov 16 (core,  │
│                              │ webapp)                       │
│ Azure delivery releases      │ v0.1.0 Oct 29 · v0.2.0 Nov 16 │
│ Tickets → Done in window     │ 0                             │
│ Tickets referenced by PRs    │ 99 (85 Kuri, 1 Harbour, 13 —) │
│ Story points                 │ not estimated                 │
├──────────────────────────────┼───────────────────────────────┤
│ Code PRs                     │ last 3 weeks  │ whole sprint  │
│ Kuri                         │ 110           │ 323           │
│ Harbour                      │  24           │  53           │
│ Marwan                       │   8           │   8           │
│ Team                         │ 142           │ 384           │
└──────────────────────────────┴───────────────────────────────┘
```

## Per person

### 🌟 Kuri (drchinca): 323 code PRs · 11 repos · +245,976 / −61,842

**🕒 Last 3 weeks (Nov 5 – Nov 26): 110 PRs · +86,431 / −8,143**

| Theme | What shipped | Tickets |
|---|---|---|
| ☁️ Self-hosted BrightAgent on Azure | MCP served behind Entra sign-in, answering from Synapse with governance defined in IaC. Covers an isolated MCP warehouse, a foreign-caller proof with a workspace-B identity, a private proof image and runner, and Synapse M1 acceptance. Released as brighthive-deploy v0.2.0 | AZ-097, AZ-098, AZ-101 |
| 📦 Customer install package | Connects to an existing customer Synapse over private TLS. Provisions the customer runtime, installs reviewed bundles, and supports both AKS install modes. Adds install guards, preflight checks, a trial guide and a readable front page. Launch audit closed. New `brightagent-selfhost` repo | AZ-008, AZ-105 – AZ-111 |
| 🔌 Projects over self-hosted MCP | New `brightagent` repo: Synapse workspace, discovery, health, project discovery and run-read tools. The Projects runtime is published with notices and proven live against AWS staging through IP-restricted HTTPS and VPN access | AZ-101, AZ-103, AZ-104 |
| 🧩 Standalone MCP in brightbot | Transport separated from model execution. Tool registries isolated per agent. Agent Server made optional. Process health, a container image, Azure AI Foundry as a model provider, and a Helm runtime profile so brightbot and BrightAgent plug into the same install | AZ-101, AZ-112 – AZ-115 |
| 🏭 Every warehouse, watched | Governance watches every Snowflake and SQL Server warehouse and fetches lineage from each. It fails closed on bad pins, reports stalled polls as Down, and uses the default warehouse, never the first one listed. Databases are now nodes under their warehouse, with a backfill | BH-1380, BH-1371, BH-1373 |
| 🌐 Multi-cloud runtime into develop | Merged the multi-cloud single-tenant runtime branch into platform-core develop (#1367), carrying Harbour's and Marwan's Azure work. Promoted to staging Nov 16 | — |
| 🧠 Models + v4 direction | Claude models moved to Opus 5.5, Sonnet 5.5 and Haiku 5.5. BrightAgent v4 on CEMAF: ADR, capability inventory, module contracts. v3 concurrency fixes, including an isolated run logger per run and Synapse `TOP` row bounds | BH-1656, BH-453, BH-1134 |

**Earlier (Oct 7 – Nov 4): 213 PRs**

| Theme | What shipped | Tickets |
|---|---|---|
| 🩺 Project health | Pipeline watchdog per active project, created on activation and synced with the project lifecycle. Fleet scan heals missing watchdogs. Project health headline, rules, problems and runs, exposed over MCP and as webapp health cards | BH-1626, BH-1634, BH-1636 |
| ✅ Quality rules over MCP | Save, activate and read back reviewed quality rules, with a shared retry store persisted in DynamoDB. Tag, all-asset and group rules run on the asset's own warehouse | BH-1255, BH-1631, BH-684 |
| 🔧 Self-repairing monitoring | Durable monitoring jobs, persisted repair claims and evidence, authorized repairs, one actionable proposal per repair PR, and Slack remediation actions | BH-1255 |
| 🛡️ Projects scoped to their workspace | Project reads and writes, pipelines, schemas, files and gates are all scoped to the workspace. Asset owners and managers are scoped too, quality-rule writes require membership, and ROUTINE turn-off is decided by `authorize()`. Live suites cover all of it | BH-1584 – BH-1589, BH-1627, BH-1637, BH-1572, BH-1573 |
| 🚀 Production release | Staging → Production on Oct 16 across brightbot, platform-core and webapp. Amplify release now verified from the build that is actually served. Production secret logs redacted | — |
| 🏗️ Azure delivery repo, from zero | brighthive-deploy bootstrapped: working rules, 48-task local backlog, AWS→Azure migration view, IaC design, foundation (state, budget, providers), up/down sandbox, an operations tool built on the Azure SDK, IaC quality gates, alerts, and one naming module. Released as v0.1.0 | AZ-000 – AZ-086 |
| 📝 Client + product specs | Nestlé trial room and Jira links, Loop AI governance fit, ACG vendor-data pilot, Q4→Q2 capacity roadmap, projects at enterprise scale, row-level data scope, year-one evidence | BH-1626, BH-1370, BH-1639, BH-1659, BH-170 |

### 👤 Harbour (Nano-233): 53 code PRs · 5 repos · +39,381 / −4,913

**🕒 Last 3 weeks (Nov 5 – Nov 26): 24 PRs · +23,131 / −2,914**

| Theme | What shipped |
|---|---|
| 🔁 Pipelines that build and repair themselves | Spec apply stops building broken pipelines. The pipeline author gets real columns, column types and the SQL dialect, runs on Sonnet, and has a 16k output limit. New `repair_project_pipeline_sql` MCP tool rewrites failed SQL steps. First-pass identity-resolution SQL on Azure. Step database, output table and smoke-table fixes for Synapse |
| ☁️ Azure runtime parity | Workspace secrets read from Key Vault. Scheduled agents run on Table Storage with an Azure cron dispatcher. Project watchdog store on Table Storage. SSE JWT validation with Entra JWKS, and browser SSE proxied through platform-core |
| 🔐 MCP access from the permission matrix | MCP access driven by the permission matrix on every profile, with risky tools locked on azure-k8s. New `schedule_asset_monitor` and `run_scheduled_agent_now` tools. Scheduled quality checks receive a service token. Service-key query for PII classifications |

**Earlier (Oct 7 – Nov 4): 29 PRs**

| Theme | What shipped |
|---|---|
| 📣 Microsoft Teams notifications | Teams added as a delivery channel. The dispatcher routes Teams through slack-server. Webhook URLs are validated and posted only to Microsoft hosts, and the webapp accepts a real Teams webhook URL |
| ☁️ Azure build-out (Nestlé) | AWS-only features gated. Agent files in Blob. Entra OGM service token, plus `mcp:write` for Entra workspace admins. Nestlé analyst Python on an AKS executor. Governance diagnostic sandbox (Path B). BrightSignals inbox and notifications stream on Azure. Logo upload, demo graph seed, local admin seed |
| 🧹 Reliability | Catalog rebuild dropped from asset writes. A data asset group that cannot be loaded now throws instead of failing silently. P2.0 MCP e2e wrap-up removed the legacy graph tools |

### 👤 Marwan (Marwan-Samih-Brighthive): 8 code PRs · 3 repos · +5,293 / −243

**🕒 Last 3 weeks (Nov 5 – Nov 26): 8 PRs, merged Nov 11–12**

| Theme | What shipped |
|---|---|
| 🧱 dbt Cloud per service | Optional dbt Cloud project and environment ids stored per dbt service (core), editable in Settings (webapp), and preferred over repo matching (brightbot) |
| ☁️ Azure-k8s hardening | Azure-k8s webapp feature branch merged into develop (#1510). GitHub auth tokens read and stored through the platform secret store. OpenMetadata MySQL volume sized at 20Gi and grown in place. Entra `given_name`/`family_name` claims set up by script |
| 👤 User names | User names are never empty or null. They are derived when the identity provider sends none |

**Earlier (Oct 7 – Nov 4):** no merged PRs.

### Ahmed

No merged PRs and no Jira activity in this window.

## Repository activity

| Repo | PRs | Code PRs | Code lines |
|---|---|---|---|
| brighthive-deploy | 113 | 111 | +48,256 / −3,760 |
| brightbot | 112 | 96 | +44,854 / −7,761 |
| brighthive-platform-core | 73 | 68 | +62,774 / −4,550 |
| brighthive-webapp | 30 | 25 | +80,282 / −48,786 |
| agentic-project-mgmt | 28 | 28 | +27,238 / −349 |
| brighthive-e2e | 17 | 17 | +3,840 / −364 |
| platform-saas-ai-context | 12 | 12 | +3,142 / −13 |
| brightagent-v3 | 8 | 8 | +2,587 / −123 |
| brightagent | 7 | 7 | +3,457 / −415 |
| brightbot-slack-server | 7 | 7 | +12,100 / −179 |
| brightagent-selfhost | 5 | 5 | +2,120 / −698 |

Two PRs account for much of the line count. webapp #1419 (+70,502 / −48,400) is a long-running auth branch that also carried the GraphQL schema and locale tooling. platform-core #1367 (+34,093 / −1,827) is the multi-cloud runtime merge.

## Problems identified

1. **Zero tickets reached Done in 7 weeks** against 384 code PRs. Of the 99 tickets that PRs reference, 68 sit in Needs Refinement and 15 in To Do.
2. **Seventh unofficial sprint.** There is still no Jira sprint object.
3. **Work is invisible on the board.** 85 code PRs carry no `BH-`/`AZ-` key — Harbour 51, Kuri 26, Marwan 8 (every one of his). Azure delivery is tracked in a local AZ backlog, so it never shows in Jira.
4. **Merged is not the same as in develop.** 48 PRs merged into feature branches. brightbot's `feat/deployment-profile` (18 of Harbour's PRs, including the Nov 24–25 pipeline fixes) has no open PR to develop.
5. **Concentration.** Kuri authored 84.1% of code PRs (77.9% in Sprint 17). Over the last 3 weeks the share is 77.5%, as Harbour's output rose.

## Recommendations

1. **Ticket sweep:** move the referenced tickets whose code has shipped (project health, project scoping, quality rules, warehouse watch) to Testing or Done.
2. Open a PR from `feat/deployment-profile` to brightbot develop so the Azure pipeline fixes reach staging.
3. Promote the Nov 16 staging cut (multi-cloud runtime, warehouse watch) to production.
4. Every PR gets a `BH-XXX` or `AZ-XXX` in its branch or title.
5. Open a real Jira sprint object for Sprint 19.
