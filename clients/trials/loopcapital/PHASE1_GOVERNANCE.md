---
name: "Loop Capital — Phase 1: AI agent governance"
slug: "loopcapital"
stage: "trial"
champion: "Frank Sung"
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: ""          # proposed — see ../../ALIGNMENT_2026-10.md (not yet created)
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [agent-governance, entra-id, skills-registry, control-plane, phase-1]
---

# Loop Capital — Phase 1: AI agent governance

> Maps each of Loop's phase-one governance requirements to what BrightAgent ships today, the gap, and the proposed ticket.

**Source:** "Loop Capital × Brighthive: AI Agent Governance Call Brief" (Suzanne El-Moursi → Frank Sung, 2026-10-16).
**Next session:** Wednesday 2026-10-21, 10:00 a.m. Central — review control-plane draft, confirm scope.
**Capability evidence as of:** 2026-10-17 (brightbot `v3.0.0.1-release`, platform-core `v3.1.1.5-release`, webapp `origin/develop`).

## What changed

Phase one is no longer the data-engineering trial. Loop wants a **governance control plane for every AI agent its
teams use** — Claude, ChatGPT, Copilot, later Gemini. Data engineering (SQL Server, SSIS/SSRS (SQL Server Integration / Reporting Services), dbt, monitoring)
moves to the *next* phase. Every Loop ticket in Jira today (BH-1245, BH-1403, BH-1421, BH-1036 children) is that
next-phase work; none tracks phase one.

## Requirement → capability → ticket

Legend: 🟢 shipped in prod · 🟡 partial / staging / shadow · ⚪ absent · size S/M/L · LG-* = proposed tickets in [the alignment page](../../ALIGNMENT_2026-10.md)

| # | Requirement (client words, shortened) | Today | Evidence | Gap to close | Ticket | Size |
|---|---|---|---|---|---|---|
| R1 | Each agent has its own identity, separate from its user | ⚪ | brightbot `mcp/auth.py:52-85` — the caller is always the user; `audit/decorator.py:103` logs agent name as a label only | Per-agent identity + on-behalf-of token, bound into every decision and audit record | **new** LG-1 | L |
| R2 | Agent permissions never exceed the user's, often narrower (Entra ID) | 🟡 | User role × resource matrix in prod (BH-1465–1469) but every verb is **shadow** by default (`service/authz/config.ts`); tool gate off by default (`feature_flags.py:326`) | Agent ⊆ user intersection; turn enforcement on; Entra group → role mapping | **new** LG-2, LG-3; existing BH-1590, BH-1471 | L |
| R3 | Granular agent access to SharePoint, OneDrive, local file shares | ⚪ (SQL Server read 🟡, sandbox only) | No Microsoft Graph code in any repo; on-prem bridge specs parked | Graph connector with per-document permission pass-through; file-share reach | **new** LG-5 | L |
| R4 | Confidential file/attachment data never leaves the firm | ⚪ | Only secret-shape scrubbing (`audit/redaction`); PII (personally identifiable information) redaction BH-1060 open; masking bypass BH-1478 | Outbound policy point on every send (Slack, email, PR (pull request), model call) + file classification | **new** LG-6; existing BH-1084 | L |
| R5 | Risk-rate skills/MCPs (Model Context Protocol servers)/plugins/connectors by observed behavior | ⚪ | `evals/` measures answer quality, not skill risk | Isolated eval sandbox, high-risk-action taxonomy, per-skill risk score | **new** LG-7 | L |
| R6 | Re-evaluate on a schedule as skills change | ⚪ | Depends on R5 | Re-score on change + schedule; flag drift | **new** LG-8 | M |
| R7 | Turn a skill off or make it unshareable | 🟡 delete only | `deep_agent_skills_middleware.py` has no enabled/share flag; webapp `SkillsSection` delete only | Enabled + shareable flags, admin policy, enforced in middleware | **new** LG-9; related BH-1599 | S–M |
| R8 | One skills registry + policy across Claude, ChatGPT, Copilot, Gemini | ⚪ | Skills serve Brighthive's own agents only | Registry + per-vendor sync (Claude first; Copilot depends on Loop's version) | **new** LG-10 | L |
| R9 | One view: agent activity, permissions, skill risk, trends | 🟡 fragments | Permission editor shipped (`AccessControlPage.tsx`); analytics runs on `MOCK_ANALYTICS`; audit is CloudWatch lines with no query UI | Durable audit store + control-plane v0 (co-designed with Loop) | **new** LG-12; existing BH-1580, BH-1595, BH-1510 | L |
| R10 | Keep pace with vendor features that change weekly | ⚪ | No vendor integrations exist yet | Weekly vendor-capability matrix owned by product | **new** LG-13 | S |
| — | Per-action risk classification, block-and-alert above threshold | 🟡 labels only | `audit/types.py:6` `ActionClass` is a fixed per-tool label; decorator never blocks | Runtime scorer + Loop thresholds + block + alert | **new** LG-11 | M–L |
| opt | Procedure graph: approved workflow can write/send, read-only elsewhere | 🟡 pipelines only | BrightRoutines WorkflowSpec + `checkPolicies()` (spec Partial) | Generalize to send/write actions; enforce at tool layer | BH-1463 (0 children) → LG-14 | L |
| — | Multi-agent from day one | 🟢 | `super_agent/deep_agent.py:221-308` — supervisor + 7 sub-agents | Agent-to-agent hops carry no per-hop identity/authorization (ties to R1) | covered by LG-1 | — |

**Honest summary:** of the ten requirements, none is fully shipped; R2, R7, R9 and runtime risk classification
have real foundations; R1, R3–R6, R8, R10 are new builds. This is closer to 70–80% build than the brief's "20%".

## What we can honestly show on Oct 21

- Supervisor + seven sub-agents running in prod.
- Live permission-matrix editor (BH-1469) — explain it is in shadow mode and enforcement is a per-verb switch.
- Human approval on every write tool; agent PRs never auto-merge.
- A structured audit record per mutating action, tagged with the agent.
- MCP scope model: writes denied unless the token carries `mcp:write`.
- Generic OIDC (OpenID Connect) single sign-on federation (Okta live on staging) — Entra is the same pattern, not yet built.
- A control-plane **draft** (design mock), clearly labelled as the co-design starting point.

## Redlines for the 10/16 brief (before any re-send)

| Page | Current wording | Suggested wording |
|---|---|---|
| 5 | "The BrightAgent harness already contains the governance Loop is asking for" | "The BrightAgent harness already provides the foundations — multi-agent orchestration, a permission matrix, human approval on writes and per-action audit. Phase one extends these to agent-level identity, Entra ID, skill risk rating and a cross-vendor registry." |
| 5 | "Governance runs as each agent acts, not as a report after the fact" | Keep, but scope it: "Permission checks and approval gates run as each agent acts; risk classification is extended to block-and-alert in phase one." |
| 5 | Agent-level RBAC (role-based access control) "on top of Entra ID … one-click permission settings" | Mark Entra integration and agent identity as phase-one build. |
| 5 | Eval sandbox "thousands of simulated calls" | Already phrased as "we would add" — keep; do not promise a call count until LG-7 is sized. |
| 7 | "The governance engine is built; the remaining 20% is fitting it to Loop's environment" | "The governance foundations are built and running; phase one builds the agent-identity, skill-evaluation and registry layers on top, in short review cycles." |
| 8 | "Our harness has run these controls at the scale of seven coordinated agents" | "Our harness coordinates seven agents in production today; phase one will validate the new controls at Loop's agent volume and we will report results openly." |

## Open questions for Oct 21 (from the brief + ours)

1. Copilot versions in use (basic / premium / Studio / agents / Cowork) — decides LG-10 Copilot coverage.
2. Expected agent and scheduled-workflow volume over 6–12 months.
3. Deployment location: Brighthive SaaS, or inside Loop's Azure tenant? (Loop runs Azure; Nestlé's private-Azure
   work in [Nestlé Azure architecture](../nestle/AZURE_ARCHITECTURE.md) would serve both.)
4. Loop's risk categories and thresholds (brief assumes Loop supplies them).
5. Who at Loop signs off phase-one success, and against which requirement rows.

## Next-phase tickets (keep, re-label — do not close)

BH-1245 (+ BH-1246–1254, 1341, 1352), BH-1403, BH-1421, Loop items under BH-1036 (BH-1057, 1167, 1351),
BH-1274/1276/1307. Proposed: label `loop-next-phase`, leave status unchanged. BH-1418/1423 (scoped database logins)
and BH-1591 (workspace-scoped runner key) are patterns phase one reuses — keep visible.
