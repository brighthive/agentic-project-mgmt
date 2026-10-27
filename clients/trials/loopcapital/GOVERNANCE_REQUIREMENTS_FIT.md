---
name: "Loop Capital — AI governance requirements fit and co-build partnership"
slug: "loopcapital"
stage: "trial"
champion: "Frank Sung"
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: ""          # proposed epic A in ../../ALIGNMENT_2026-10.md — not yet created
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [agent-governance, vendor-evaluation, partnership, co-build, entra-id, mcp]
---

# Loop Capital — AI governance requirements fit and co-build partnership

> Loop Capital has passed the first MVP trial goal. It is now comparing Brighthive with NROC, CrowdStrike, Proofpoint
> and Zscaler for AI governance, and weighing a **paid co-build partnership** with us. Kuri leads.
> Requirements (verbatim): [artifacts/2026-10-16-ai-governance-requirements-from-client.md](artifacts/2026-10-16-ai-governance-requirements-from-client.md).
> Our build detail: [PHASE1_GOVERNANCE.md](PHASE1_GOVERNANCE.md). Evidence date 2026-10-20.

## Our lane, in one sentence

**The other vendors govern the road to AI tools — network, endpoint, browser, prompt. Brighthive governs what AI
agents do once they are inside Loop's data — which databases, tables and rows an agent may touch, under its own
identity, using only tested skills, inside approved workflows — and reports it into the tools Loop already runs.**

We complement Zscaler / Microsoft Purview / Entra, we do not replace them. Competing on websites and prompt DLP would
be a losing, redundant pitch; the agent and data layer is open ground none of them covers.

## Fit against Frank's four sections

Legend: 🟢 Brighthive today · 🔨 co-build in the partnership (ticket from [PHASE1](PHASE1_GOVERNANCE.md)) ·
🤝 integrate with what Loop owns or buys · ⚪ out of scope for us.

### 1. AI access control

| Requirement | Fit | How |
|---|---|---|
| Allow Work/Team/Business/Enterprise accounts, deny Personal/Free/Anonymous | 🤝 | Entra tenant restrictions v2 (Global Secure Access) or Zscaler tenant restrictions — the standard mechanism; Loop likely owns the Microsoft one |
| Enforce by user identity, not device | 🔨 | Agents act under an Entra-linked **agent identity** bound to its user (LG-1, LG-3); people's AI access stays with Entra Conditional Access 🤝 |
| Internal network, firm laptops, firm mobile, personal mobile | 🤝 | Network/endpoint/MAM: Zscaler or Entra GSA + Intune MAM for unmanaged phones. No vendor fully covers personal mobile |
| Visibility: AI websites, AI browsers, mobile apps, browser/VS Code extensions, Office add-ins | 🤝 | Proxy/endpoint/extension vendors |
| Visibility: AI agents, CLI agents, cloud AI agents | 🔨 | Every agent that reaches Loop data through the Brighthive MCP layer is identified and logged (LG-1, LG-12) |

### 2. AI risk monitoring

| Requirement | Fit | How |
|---|---|---|
| Unapproved AI tools or services | 🤝 + 🔨 | Discovery from Zscaler / Defender for Cloud Apps logs; shown in our control view (LG-12) |
| Untrusted MCPs, connectors, plugins, skills | 🔨 **core** | Skill/MCP eval sandbox: synthetic data, scored behavior, re-run on change, turn off / unshareable (LG-7, LG-8, LG-9) |
| Agents with excessive access to data, systems, repos, cloud | 🔨 **core** | Agent permissions never exceed the user's, narrowed per agent (LG-2); scope down to database/table (data-scope spec, agentic-project-mgmt #206) |
| Prompt injection from sites, docs, email, files, repos, connectors, agent workflows | 🔨 partial · 🤝 | We score and block risky **agent actions** at runtime (LG-11) — the consequence of an injection; content inspection on web/email belongs to CrowdStrike / Microsoft Prompt Shield |
| Risk by user, app, network, device, data access, connector, sensitivity; alert or block | 🔨 / 🤝 | We own *data access* and *connector*; network and device come from partners, joined in the control view |

### 3. DLP and oversharing

| Requirement | Fit | How |
|---|---|---|
| Prompt text, file uploads, pasted content, browser extensions, add-ins | 🤝 | Purview (strong inside M365 and Copilot), Zscaler inline DLP, Proofpoint endpoint |
| Connectors, plugins, AI agents, indirect access through integrations | 🔨 **core** | Outbound policy point on every agent send — Slack, email, PR, model call (LG-6); column masking extended to files (BH-1084) |
| Sensitive types: client info, financial, MNPI, PII, source code, secrets | 🔨 + 🤝 | Classification from Purview sensitivity labels 🤝; enforced where agents read data 🔨; secrets scrubbing exists today 🟢 |

### 4. Reporting and integration

| Requirement | Fit | How |
|---|---|---|
| Central policy, logging, alerting, dashboards, audit reports | 🔨 | Control plane v0, co-designed with Loop (LG-12) on a durable audit store (BH-1580 / BH-1595) |
| Identity provider | 🔨 | Native Entra ID (LG-3 — also needed by Nestlé) |
| SIEM / SOAR | 🔨 / 🤝 | Export agent and audit events to Loop's SIEM (Sentinel or Splunk — to confirm); SOAR consumes them 🤝 |
| Endpoint, DLP, CASB, SWG | 🤝 | Read their verdicts/labels; we don't duplicate them |
| Deployment model | 🟢 / 🔨 | Brighthive SaaS today; inside Loop's Azure tenant is the same work as Nestlé's private deployment ([AZURE_ARCHITECTURE](../nestle/AZURE_ARCHITECTURE.md)) |
| Limitations, licensing, roadmap | — | This page's limits section; licensing is a commercial decision (Suzanne / Matt) |

## The field, honestly (researched 2026-10-20 from vendor pages and press)

| Vendor | Strong at | Leaves open |
|---|---|---|
| **Zscaler** — AI Protect, AI Broker + Agent Registry, Endpoint AI Security, AI Access Graph | Sections 1 and 3 on managed devices and networks; MCP red-teaming | June-2026 launches not confirmed GA; maps identity → data but doesn't enforce inside it; personal mobile |
| **CrowdStrike** — Falcon Guardian (Sep 2026, successor to Falcon AIDR) | Shadow-agent discovery, runtime prompt-injection detection on managed endpoints, SIEM | Endpoint-only (no personal mobile); AI Gateway not yet shipped; nothing inside warehouses |
| **Proofpoint** — Data Security Complete, AI Data Governance, Secure Agent Gateway | DLP for email, endpoint and prompts | Agent Gateway GA unconfirmed; CLI, mobile, agent identity weak |
| **NROC Security** | Governing employee use of GenAI websites | Little public detail on CLI, IDE, MCP, agents; smaller vendor |
| **Microsoft (already owned)** — Purview DSPM, Entra GSA + Prompt Shield, Entra Agent ID, Agent 365 | Everything inside M365/Copilot; tenant restrictions; Sentinel | Agent ID covers only Copilot Studio / Foundry agents; much of it needs E5/E7 or Agent 365, not Copilot Basic; Prompt Shield in preview; no MCP/skill sandbox |

Sources: Zscaler IR and Network World (Zenith Live 2026-06-09); SiliconANGLE 2026-09-01 and CrowdStrike IR (AIDR GA);
Proofpoint press and blog; Microsoft Learn "what's new" in Security for AI; itbrief / Northamber for NROC. Grades are
our reading of public material — no product was tested. **None of them governs what an agent does inside a
warehouse, SQL Server or SharePoint, scopes a non-Microsoft agent's data rights apart from its user, or tests an MCP or
skill in a sandbox before approval.** That is the partnership.

## Proposed co-build partnership

| | |
|---|---|
| **What Loop gets** | Agent identity on Entra; least-privilege agent data access down to database/table; MCP and skill risk ratings with recurring re-tests; outbound policy on agent sends; a control view co-designed with Loop's team; events into Loop's SIEM |
| **What Loop brings** | Design-partner time (short review cycles); an Entra test tenant or app registration; Loop's risk categories and thresholds; a sandbox copy of representative data; named approver for phase-1 success |
| **Works alongside** | Zscaler or Entra GSA for access control; Purview for prompt/file DLP and sensitivity labels; CrowdStrike for endpoint runtime — we consume their signals |
| **Out of scope** | Network/endpoint/browser enforcement; personal-device control; prompt DLP on AI websites; Gemini until adopted |
| **Success criteria to agree** | Measured against the rows marked 🔨 above only — each with a baseline, a target and a Loop signatory |
| **Commercials** | Paid co-build — structure and price owned by Suzanne / Matt; engineering sizing is in [ALIGNMENT_2026-10.md](../../ALIGNMENT_2026-10.md) (epic A, mostly L-sized items) |

## Limits we state up front

- Agent identity, Entra integration, the skill sandbox, the registry and the control view are **builds**, not shipping
  features — phase one delivers them with Loop, in short cycles.
- Our permission checks run in log-only mode by default today; turning enforcement on for Loop is part of phase one.
- Personal mobile, browser extensions and prompt DLP on AI websites are partner territory, by design.
- Copilot: with M365 Copilot Basic and a few Premium users (no Copilot Studio), Copilot governance runs through
  Microsoft's own controls (Purview, Entra); we cover agents that reach Loop data through Brighthive.

## Questions for the Oct 21 session

1. Which of Zscaler, Purview (and at what Microsoft licence level), CrowdStrike or Proofpoint does Loop already run?
2. Which SIEM — Sentinel, Splunk, other?
3. Which agents touch Loop data today (the M365 MCP mail-attachment job, scheduled Claude workflows) — our phase-one test set.
4. Deployment: Brighthive SaaS, or inside Loop's Azure tenant?
5. How will Loop score vendor proposals — and does a co-build partner get scored differently from a product vendor?

## Draft reply to Frank (for Kuri / Suzanne to adapt — not sent)

> Hi Frank — thank you for the clarification on Copilot and for sharing the full requirements. Reading them against
> the other tools you're evaluating, we see two layers: controlling how people reach AI tools (networks, devices,
> browsers, prompts), which Zscaler, Purview and similar tools already handle well, and governing what AI agents do
> once they are inside Loop's data — which databases and tables they touch, under whose identity, with which skills
> and connectors. That second layer is where Brighthive is built to lead, and where we'd propose to co-build with you,
> plugged into the identity and security tools you already run. Tomorrow we'll walk through each requirement and
> show plainly which we deliver, which we'd build with you, and which we'd integrate. — Kuri
