# Agentic Remediation — Strategy Brief

> **Audience:** Kuri + leadership; usable in the Loop Capital conversation.
> **Date:** 2026-07-21 · **Author:** Marwan (with research synthesis)
> **Status:** Direction proposal — precedes the implementation spec
> (`docs/specs/agentic-remediation-sandbox.md`, not yet written).
> **Companion specs this connects:** `self-healing-pipelines.md` (GC-11),
> `proactive-pipeline-ingestion-monitoring.md` (BH-1036).

---

## 1. The problem, in the customer's words

Loop Capital (and prospects generally) describe BrightAgent as a side companion in
Slack/Teams/UI that runs observability and data-cleaning workflows, and:

- On the **optimal path**: does the job and says *"job complete."*
- On a **blocker**: tries, and if it keeps failing, **drills down** — "why am I blocked?
  what's broken?" — then communicates *"I tried X three times, it failed because Y,
  here's my suggested fix, are you cool with that?"* → user approves → it finishes and
  reports back.
- The **"aha"**: if it has *done this fix before*, it just does it and tells you it
  handled it — **Undo**, not Accept.

**Today BrightAgent cannot do this reliably.** It is a LangGraph ReAct agent whose "hands"
are a fixed set of pre-built tools. On a tool error it feeds the error text back to the
model and *hopes it narrates the right next step*. There is no structured failure
detection, no retry policy, no diagnosis-against-reality, no learned trust. That gap is
the subject of this brief.

---

## 2. What the market actually ships (researched, not assumed)

Four research fronts — frontier coding agents, data-observability competitors, enterprise
agent platforms, and the standards bodies — converge cleanly. Sources cited inline.

### 2.1 The loop every serious agent uses

The frontier coding agents all describe the **same loop** in near-identical words:

- **Anthropic:** "gather context → take action → **verify results** → repeat"; agents are
  "just LLMs using tools based on environmental feedback in a loop." Verification is
  "anything that returns a signal Claude can read — a test suite, a build exit code, a
  linter." (`anthropic.com/engineering/building-effective-agents`,
  `code.claude.com/docs/en/how-claude-code-works`)
- **OpenAI Codex:** container-per-task, "runs terminal commands **in a loop**," reads
  `AGENTS.md` for the test/lint commands, validates its own work, presents a diff → PR.
  (`learn.chatgpt.com/docs/environments/cloud-environment`)
- **Devin:** sets up the env, **reproduces the bug**, codes and **tests the fix on its
  own**, in a Linux VM with shell+editor+browser. (`docs.devin.ai`)
- **Google Android-Studio agent:** "builds the project to **verify** the solution, and
  **iterates until the issue is resolved**." (`developer.android.com/studio/preview/gemini/agent-mode`)

**The insight:** the power isn't the model or the shell — it's that the shell **closes the
loop against ground truth.** The agent is reliable because it reacts to a *real* error, not
a hypothesized one. This is exactly what BrightAgent lacks.

### 2.2 The data-observability competitors — where the whitespace is

| Product | Detect | Diagnose | **Fix** | Model |
|---|---|---|---|---|
| **Monte Carlo** (category leader) | ✅ | ✅ strong | ❌ **hosted product refuses on principle** — *"agents never directly manipulate data or systems"* | detect + diagnose |
| Anomalo, Soda | ✅ | ✅ | ⚠️ "**coming soon**" | not shipped |
| Bigeye, Metaplane (Datadog), Sifflet | ✅ | ⚠️ | ❌ | detect + alert |
| **Paradime (DinoAI)** | ✅ | ✅ | ✅ **ships it** — generate fix → **sandbox-validate** (`dbt build`) → open **PR** → human approves → rollback; tiered by risk | **dbt-only** |

Sources: `montecarlo.ai/platform/observability-agents`, `anomalo.com`, `soda.io`,
`paradime.io/guides/dbt-self-healing-pipeline-ai-agents`.

**Two strategic facts:**
1. **The leader has deliberately ceded remediation.** Monte Carlo won't touch customer
   systems in its managed product. Open flank.
2. **The one player shipping detect→diagnose→fix (Paradime) does it exactly like the
   coding agents** — sandbox-validate → PR → approve → rollback — but is **single-engine
   (dbt only).**

### 2.3 The enterprise platforms — the governance table-stakes, and the novelty gap

- **Salesforce Agentforce / MS Copilot Studio:** autonomy is **binary and set at design
  time** — once published, autonomous agents "react automatically… no per-action human
  approval by default" (MS Learn). Oversight = test-before-deploy + admin kill-switch.
- **MS Entra Agent ID:** each agent = a single-tenant service principal, **no shared
  credentials**, **mandatory human "sponsor."** (`learn.microsoft.com` / entra-docs)
- **Azure AI Foundry:** VM-isolated sandbox per session + BYO-VNet.
- **Google ADK:** the *only* platform with a **threshold-conditional** approval gate —
  `require_confirmation(lambda args: args.amount > 1000)` — approval fires only on
  high-impact actions. (`adk.dev/tools-custom/confirmation`)

**The novelty finding (falsifiable negative, checked across all platforms): no vendor
ships *learned/progressive* trust** — trust that increases automatically based on past
approved behavior. Everyone is either approve-every-time or approve-nothing-after-publish.
**BrightHive's "earn autonomy over time + Undo" is ahead of the market.**

### 2.4 The standards bodies — our safety design *is* the consensus

- **OWASP LLM Top-10 2025 ranks "Excessive Agency" #6** — damaging actions from an agent
  with excessive functionality / permissions / autonomy. This is *the* named risk of
  building this. Prescribed mitigations: **human approval for high-impact actions**,
  **least privilege / act in the user's security context**, **"complete mediation" (authz
  enforced downstream, not by the LLM)**, **prefer specific tools over open-ended shell**.
  (`genai.owasp.org/llmrisk/llm062025-excessive-agency/`)
- **NIST AI RMF MANAGE 2.4** makes a **kill switch** a *required* control.
- **Google SAIF, CSA, Anthropic, Wiz** all converge on: least privilege, human gate on
  high-impact, audit trail, bounded stopping conditions, named owner per agent.

Our design (below) maps 1:1 onto these. That is the strongest possible footing for an
enterprise buyer — we are building the *prescribed mitigations for the named top risk*,
not improvising.

---

## 3. The recommended solution

**Not Kubernetes pods. Not a raw computer.** The frontier coding-agent loop, applied to
data pipelines the way Paradime does, but **cross-platform**, built on the **AgentCore
Code Interpreter** we're already migrating to, and governed by **enterprise-grade
primitives** — with **progressive trust** as the interaction model none of them ship.

### 3.1 Three layers

**Layer 1 — Give it a computer (the missing capability).**
Adopt **AgentCore Code Interpreter** as BrightAgent's investigation-and-execution surface.
Confirmed real and GA (2025-10-13): per-session **microVM** (single-tenant, CPU/mem/fs
isolated, **memory sanitized + microVM destroyed on session end**), Python/JS/TS, returns
`stdout`/`stderr`/`exitCode`, 15min–8hr sessions, **`SANDBOX` mode (no internet; S3 via a
scoped IAM execution role)** vs `PUBLIC`, CloudTrail audit. This is the E2B/Firecracker
"sandbox per task" idea **as a managed AWS service you're already adopting** — not a K8s
platform to build and secure yourself. (`docs.aws.amazon.com/bedrock-agentcore/.../code-interpreter-tool.html`)

**Layer 2 — Close the loop against ground truth** (maps 1:1 to Paradime + the coding agents):
```
detect  (structured ExecutionOutcome — NOT parsed from the model's prose)
  → diagnose   ← sandbox runs READ-ONLY probes against the real warehouse
  → draft fix  → VALIDATE THE FIX IN THE SANDBOX before proposing it
  → gate       (see Layer 3)
  → execute the approved fix
  → VERIFY it actually worked  (re-check the failure signature — no silent "done")
```
**Highest-leverage, lowest-risk first step: a read-only diagnostic sandbox.** Let the
agent run investigative queries to answer *"why am I blocked?"* against reality, with
**zero write capability.** That alone delivers Loop Capital's "drill down and tell me
what's broken," and is safe enough to ship early.

**Layer 3 — The trust wrapper** (where the "buttons" question is answered by *logic*, not UI):

The button set is a **function of three axes: reversibility × prior-approval history ×
confidence.**

| Situation | Buttons | Behavior |
|---|---|---|
| First-time / complex / **irreversible** fix (merge, DROP, destructive DDL) | **Accept / Decline** | Propose, pause on LangGraph `interrupt()`, wait |
| Fix **seen-and-approved before** + **reversible** + high confidence | **Undo Fix** only | Auto-execute, then report *"I handled it"* |
| Optimal path | none | *"Job done"* (verified) |

Governed by, and *only* by, these non-negotiables (each traces to a standard or a
research finding):
- **Reversibility is a hard boundary.** Irreversible actions **never** auto-execute,
  regardless of history. `github_merge_pull_request` stays code-level-excluded (already a
  hard requirement in `proactive-pipeline-ingestion-monitoring.md`). *(OWASP: minimize
  autonomy on high-impact.)*
- **Auto-execute requires a compensating (Undo) action.** No inverse ⇒ no auto-execute ⇒
  fall back to Accept/Decline. Undo being real is what earns the right to be proactive.
- **Verify before "job done."** Auto-executing and reporting success without confirming it
  worked is the exact trust failure the feature exists to prevent. Adopt BH-1091's
  `VERIFYING` state (gone → positive confirmation; recurred → immediate escalation
  bypassing cooldown).
- **Circuit breaker + kill switch.** Fleet-wide, admin-triggerable, precision-driven —
  trips auto-execution back to Accept/Decline. *(NIST MANAGE 2.4 requires this.)*
- **Scoped identity + named owner + full audit.** Per-workspace scoped sandbox credential
  (never shared); an owner accountable for every auto-executing routine; every
  proposed/executed/undone fix audited. *(MS Entra + OWASP + NIST.)*

### 3.2 Where each piece lives (all primitives already exist, disconnected)

| Capability | Reuse (already in `brightbot`) | New work |
|---|---|---|
| Agent loop | LangGraph `deepagents` supervisor | — |
| Human gate | `interruptible()` / LangGraph `interrupt()` (dbt-commit, quality-suites) | wire to a RemediationProposal |
| Diagnosis | `dbt_agent/remediation_agent.py` + `root_cause_classifier.py` (never merges, never guesses) | generalize beyond dbt |
| Alerts + buttons | BrightSignals `publishNotification` + Slack Block Kit (Schedule/Dismiss precedent) | RemediationProposal card type |
| Execution surface | — | **AgentCore Code Interpreter** (read-only first) |
| Structured failure detection | tool error envelopes (unstructured) | **`ExecutionOutcome` contract** (foundation) |
| Fix-memory ("seen it before") | BrightRoutines pattern-store shape | new `(workspace, failure_signature) → RemediationOutcome` store |
| Verify-it-worked | cooldown 4-tuple (spec'd) | **`VERIFYING` state** (BH-1091) |
| Circuit breaker | `brightroutines-online-judge-eval-circuit-breaker.md` (spec'd) | extend to auto-execution |

> **AgentCore has no native human-approval primitive** — keep the gate in LangGraph, not
> AgentCore. (Confirmed: only OAuth-consent / Policy / Payments-auth exist natively.)

---

## 4. Positioning — why this is a differentiator, not catch-up

- **Detection is table-stakes** — everyone has it.
- **Fixing is the frontier** — only Paradime ships it, and only for dbt.
- **BrightHive's defensible ground:** a **hosted, approval-gated, cross-platform** fix loop
  — dbt **+ Snowflake + Databricks + legacy SQL Server** (which nobody serves, and which
  is *literally Frank's objection*: "if the SQL server has no MCP, how do you monitor it?").
- **The interaction model no one ships:** progressive trust — start at Accept/Decline, earn
  auto-execute-with-Undo. Ahead of Salesforce, Microsoft, Google.

**One line:** *the leader won't remediate; the one who does is single-engine; and nobody
ships learned trust. That intersection is ours to take.*

---

## 5. Honest risks

- **A computer does not make an agent reliable.** Devin's independent eval landed **3/20
  tasks** (answer.ai, Jan 2025). What makes this shippable is **narrow scope +
  sandbox-validate + human gate** — Paradime's discipline — not "let it loose."
- **The sandbox will hold live customer production credentials.** Non-negotiable dividing
  line: **investigation is read-only and ungated; mutation is always gated.**
- **Detection must be structured, not prose-parsed.** The `ExecutionOutcome` contract is
  the foundation; nothing else works without it.
- **Idempotency.** LangGraph re-runs an interrupted node *from the start* on resume — every
  remediation action needs an idempotency key or a retry double-applies the fix
  (BrightRoutines already hit this: schedule double-create).
- **We're ahead of the standards on progressive trust** — which means the burden of proving
  it safe is on us. The reversibility boundary + `VERIFYING` + breaker are how we carry it.

---

## 6. Recommended sequencing

1. **`ExecutionOutcome` contract + outcome classifier** — structured failure detection.
   Nothing else works without it.
2. **Read-only diagnostic sandbox** (AgentCore Code Interpreter, `SANDBOX` mode, zero
   write) — delivers "drill down and tell me what's broken." Safe to ship early. **This is
   the demo-able leap.**
3. **Bounded retry policy** (retryable-transient vs deterministic) around workflow_agent +
   watchdog. Also closes the confirmed `dbt_cloud_tools.py` no-backoff gap.
4. **Generalize `remediation_agent`** into a `RemediationProposal` producer for any
   classified failure + **RemediationProposal card** (Slack + webapp) with the Accept/
   Decline gate. → delivers the "first-time fix" experience.
5. **Fix-memory store** + auto-execute-if-reversible-and-known + Undo. → the "aha."
6. **`VERIFYING` post-fix loop + circuit breaker** governing auto-execution. Ship behind a
   flag with the breaker live.

Steps 1–4 = the Accept/Decline experience (a demonstrable leap over today). Steps 5–6 =
the higher-risk "I already handled it / Undo" path.

---

## 7. Next artifact

Implementation spec: **`docs/specs/agentic-remediation-sandbox.md`** — the connective
tissue between `self-healing-pipelines.md` and
`proactive-pipeline-ingestion-monitoring.md`. It defines: AgentCore Code Interpreter as the
execution **port** (read-only first), the validate-in-sandbox loop, the progressive-trust
action gate (reversibility × history × confidence), and the governance contract (scoped
identity, owner/sponsor, circuit breaker, audit) — then generates Jira tickets via
`/create-jira-ticket`.
