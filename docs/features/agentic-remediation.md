---
title: "Agentic Remediation — proactive detect → investigate → propose → verify"
status: "In progress — backend + investigation + notification cards built & verified; action-receiver endpoints + live UI verification remain"
author: "Marwan Samih (with Claude)"
created: "2026-07-24"
last-updated: "2026-07-24"
epic: "BH-XXX (agentic-remediation — resolve live before ticketing)"
related:
  specs:
    - agentic-remediation-sandbox.md
    - self-healing-pipelines.md
    - proactive-pipeline-ingestion-monitoring.md
    - brightroutines-online-judge-eval-circuit-breaker.md
  strategy: docs/AGENTIC_REMEDIATION_STRATEGY.md
  reachability: clients/trials/loopcapital/sandbox/eval/SANDBOX_REACHABILITY.md
repos:
  - brightbot (backend: decision core, investigation, watchdog wiring)
  - brightbot-slack-server (Slack remediation_proposal card)
  - brighthive-webapp (inbox remediation_proposal card)
tags: [remediation, self-healing, agentcore, sandbox, brightsignals, hitl, progressive-trust]
---

# Agentic Remediation

> **One line:** BrightAgent, running a workflow unattended, detects a failure,
> tries the retryable ones, **investigates the rest against the real warehouse**,
> and either **asks the user to approve a fix (Accept/Decline)** or — for a fix
> it has safely done before — **applies it and offers Undo**, never claiming
> "job done" until it has *verified* the fix worked.

---

## 1. Why this exists — the customer ask

Loop Capital (Frank) and other prospects described BrightAgent as a proactive
companion in Slack/Teams/UI that runs observability + data-cleaning workflows and
behaves like a good data engineer when something breaks:

- **Optimal path:** does the job, says *"job complete."*
- **On a blocker:** tries a few times, then **drills down** — *"why am I blocked?
  what's broken?"* — and reports *"I tried X three times, it failed because Y,
  here's my suggested fix — are you cool with that?"* → user approves → it
  finishes and reports back.
- **The "aha":** if it has done that fix before, it just does it and tells you it
  handled it — **Undo**, not Accept.
- Frank's specific challenge: *"if the SQL server has no MCP or service to
  connect, how are you going to monitor/fix it?"*

**The gap this addressed:** BrightAgent was a LangGraph ReAct agent whose failure
handling was *prompt-driven* — on a tool error it fed the error text back to the
model and hoped it narrated the right next step. There was **no structured
failure detection, no retry policy, no way to investigate a failure against the
real system, and no learned trust.** The honest starting assessment: *it could
not reliably detect actual errors and fix them under our constraints.*

The full origin analysis and competitive research (Monte Carlo cedes remediation;
Paradime ships it but dbt-only; **no vendor ships learned/progressive trust**)
live in [`docs/AGENTIC_REMEDIATION_STRATEGY.md`](../AGENTIC_REMEDIATION_STRATEGY.md).

---

## 2. The core design decision

The tempting-but-wrong approach: *prompt* the LLM to "try 3 times, then diagnose,
then ask." That's exactly the unreliable mechanism we started with.

**The design instead: a deterministic control loop where the LLM is used only for
what it's genuinely good at (diagnosis + fix-drafting), never as the control loop
itself.** The loop is scaffolding; the model is a component inside it.

```
run workflow (unattended)
  → SUCCESS ........................ "job done" (only after VERIFY confirms it)
  → FAIL → classify (structured, not prose-parsed)
        → TRANSIENT?  retry with backoff (≤ N times)
        → DETERMINISTIC / retries exhausted?
              → INVESTIGATE against ground truth (read-only sandbox query)
              → build a RemediationProposal (diagnosis + fix + reversibility)
              → GATE (reversibility × prior-approval history × confidence × breaker):
                    → seen-before & reversible & confident & breaker-closed
                          → AUTO-EXECUTE → "I handled it" + [Undo Fix]
                    → else → [Accept] [Decline]
                    → unclassifiable / no fix → [Acknowledge] (alert-only, never guess)
              → after any fix applied → VERIFYING: re-check the signature
                    → cleared  → positive "confirmed fixed"
                    → recurred → escalate immediately (never silently suppress)
```

**"Less buttons, more logic":** the buttons (Accept/Decline/Undo) are trivial UI.
The product is the **logic that decides which buttons appear** — `decide_gate()`,
a pure function of reversibility × history × confidence × circuit-breaker.

---

## 3. What was built — component by component

All backend code is behind a **default-off feature flag** (`FEATURE_FLAG_REMEDIATION_GATE`).
Flag off = existing production behavior, byte-for-byte. Flag on (per-workspace) =
the new gated loop.

### 3.1 brightbot (backend) — branch `remediation-layer0-classifier-recall-gaps`

| Module (`brightbot/agents/governance_agent/tools/`) | Role |
|---|---|
| `root_cause_classifier.py` | Deterministic regex classifier: error text → one of 4 DATA_SHAPE modes (`schema_drift`, `missing_partition`, `broken_stage`, `dbt_contract`) or `None`. **Recall fixed 83% → 100%**, precision held 1.00 (never misclassifies a runtime/permission failure into a fix path). |
| `remediation_decision.py` | The deterministic brain: `ExecutionOutcome` (structured detection), `FailureClass` (TRANSIENT/DETERMINISTIC/UNKNOWN) + `should_retry` (the "try 3 times"), `Reversibility`, `RemediationProposal`, and `decide_gate()` (the "which buttons" function). Named thresholds: `MAX_TRANSIENT_RETRIES=3`, `AUTO_EXEC_MIN_APPROVALS=3`, `AUTO_EXEC_MIN_CONFIDENCE=0.85`. |
| `fix_memory_store.py` | The "I've done this before" record, keyed `(workspace_id, failure_signature)`. Protocol + DynamoDB adapter + in-memory fake. Workspace-isolated (one tenant can't inherit another's trust). |
| `diagnostic_sandbox.py` | The "computer": `DiagnosticSandbox` port + `AgentCoreCodeInterpreterSandbox` adapter (wraps the shipped `invoke_bedrock_code_interpreter`). Exposes **READ_ONLY only** — refuses MUTATE at the boundary (Invariant 5 by construction). |
| `investigation.py` | `investigate_sql` — validates read-only via the shipped `assert_read_only_sql` guard, resolves warehouse creds, generates the driver+query code (psycopg2/snowflake/pymssql), runs it in the sandbox, parses rows. |
| `investigation_agent.py` | The LLM step: `investigate_and_propose` — a bounded loop where the model proposes read-only queries, runs them, and concludes with a `RemediationProposal`. **Safety-critical: `reversibility` is derived deterministically from the classified mode, never from the model** — a model cannot talk the system into auto-executing an irreversible fix. `make_model_propose_step` binds the real Bedrock Sonnet. |
| `remediation_planner.py` | `plan_remediation` — composes classify → retry → investigate → gate in order. Optional `investigator` seam (default None = back-compat). |
| `verifying_loop.py` | The `VERIFYING` state machine (Invariant 8): a fix marks its signature VERIFYING; next observation either CONFIRMS (positive "job done") or ESCALATES (recurred, bypasses cooldown). Confirm/escalate fire exactly once. |
| `pipeline_watchdog_task.py` (edited) | Wires the above into the live autonomous watchdog, gated. On a produced PR: marks VERIFYING + publishes the actionable `remediation_proposal` signal. |
| `notification_constants.py` (edited) | `STAGE_REMEDIATION_PROPOSAL` — with the metadata-key contract the cards read. |

### 3.2 brightbot-slack-server — branch `feat/remediation-proposal-card`

The `remediation_proposal` Slack card: `types.ts`, `classify.ts` (:wrench: "Fix
suggested — your call"), `formatter.ts` (diagnosis + PR link), `blocks.ts`
(Accept/Decline buttons, or Undo-Fix-only when `auto_applied`),
`remediation-proposal-action.ts` (shared-secret callback to brightbot), `app.ts`
(the three action handlers, ack-first), plus the signal-catalog entry.

### 3.3 brighthive-webapp — branch `feat/remediation-proposal-card`

The `remediation_proposal` inbox card: `RemediationProposalCard.tsx` (Accept/
Decline, or Undo Fix when `auto_applied`, busy-guarded, calls a
`resolveRemediationProposal` mutation), registered in the inbox `cardRegistry`,
plus the atomic catalog change (`types.ts` + `signal-catalog.json` +
`catalog.test.ts`) the CI drift-guards require.

---

## 4. Safety model (each traces to a standard or an invariant)

- **Structured detection, never prose-parsed** — success/failure comes from a typed `ExecutionOutcome`, not the model's narration (Invariant 1).
- **Reversibility is a hard boundary** — IRREVERSIBLE/UNKNOWN never auto-executes, regardless of history/confidence (Invariant 5). `github_merge_pull_request` is excluded from the remediation tool surface at the code level (GC-17).
- **"Accept" ≠ merge** — from Slack or webapp, Accept tells BrightAgent to *proceed* with the drafted fix through its existing human-gated path; merging stays a GitHub review. No UI merges anything.
- **Verify before "job done"** — the VERIFYING loop; a merged-but-wrong fix escalates rather than being silently suppressed (Invariant 8 / BH-1091).
- **Auto-execute requires a compensating (Undo) action** — no inverse ⇒ no auto-execute ⇒ fall back to Accept/Decline (Invariant 6).
- **Circuit breaker / kill switch** — OPEN breaker forces Accept/Decline fleet-wide (Invariant 12).
- **Workspace-scoped least privilege** — every sandbox + store keyed on the validated principal's workspace, never a caller-supplied id (Invariant 11, OWASP LLM06).
- **Idempotency** — remediation actions carry keys so a LangGraph resume can't double-apply.

Maps 1:1 onto OWASP LLM Top-10 "Excessive Agency" (#6) mitigations + NIST AI RMF
MANAGE 2.4 (kill switch). The **progressive-trust** interaction model (earn
autonomy over time + Undo) is ahead of Salesforce/Microsoft/Google, none of which
ship learned trust.

---

## 5. What was verified — and how

### 5.1 Offline (runs with no cloud) — all green
- Classifier: Layer 0 eval flipped **NO-GO (83%) → GO (100%)**, precision 1.00.
- Decision core, fix-memory, planner, investigation, verifying loop, sandbox adapter: **full unit coverage**, run via `uv run pytest tests/unit/agents/governance_agent/` — passing (99+ in the remediation suites; 31 in the watchdog suite; no regressions).
- Slack: **506 tests pass** (`npx vitest run tests/notifications/`).
- Webapp: card + catalog + inbox-drift suites pass (`npx jest`), `catalog:verify` OK.

### 5.2 Live against real infrastructure — CONFIRMED
Full detail in [`SANDBOX_REACHABILITY.md`](../../clients/trials/loopcapital/sandbox/eval/SANDBOX_REACHABILITY.md).

- **Sandbox reachability (the biggest risk, now retired):** a `Security: Public`
  AgentCore Code Interpreter reached and queried **all three real targets** from
  inside the sandbox — Snowflake (`SELECT 1` → `1`), Redshift Serverless
  (`SELECT 1` → `1`), dbt Cloud (Admin API `HTTP 200`).
  - Key finding: the *original* Sandbox-mode tool cannot reach warehouses (no
    egress); a **new Public-mode tool** was provisioned for investigation. Spec
    Invariant 3 was revised to match this reality (read-only safety comes from
    the SQL guard + read-only credential + READ_ONLY-only adapter, NOT network
    isolation).
- **Live LLM investigation loop (last creds-gated unknown, now closed):** the real
  Sonnet model investigated a real `invalid identifier 'SETTLEMENT_CCY'` failure
  against real Snowflake — twice. It queried `information_schema` across the
  warehouse, found the real naming pattern (`CURRENCY`, not `SETTLEMENT_CCY`),
  and produced a correct diagnosis (confidence 0.85–0.88). In one run it
  **recovered from a real mid-investigation error** rather than crashing.
  Reversibility stayed deterministic-from-mode in both runs.

---

## 6. What is NOT done (honest status)

Three real gaps remain. None is a small glue task; do not represent the feature
as fully live until these close.

1. **Action-receiver endpoints don't exist yet.** The cards render and the buttons
   click, but the *receivers* are unbuilt: the webapp calls a
   `resolveRemediationProposal` GraphQL mutation (needs a **platform-core**
   resolver) and the Slack handler POSTs to brightbot's
   `/manage/remediation-proposals/{id}/{decision}` (needs a **brightbot** route).
   Until these exist, an Accept/Decline/Undo click has nothing to land on. This
   also needs a design for *how* "Accept" resumes the paused remediation.
2. **Actual fix EXECUTION (MUTATE path) is deliberately not built.** Today the
   loop opens a **human-reviewed GitHub PR** (the existing safe path). True
   auto-apply (apply-then-Undo without a PR) needs a MUTATE sandbox capability +
   compensating-action execution — the highest-risk piece, intentionally deferred
   pending an explicit safety sign-off.
3. **Live UI verification.** The cards compile, render in tests, and match
   existing patterns, but no one has clicked them in a real Slack workspace or
   browser — needs a staging deploy.

---

## 7. How to test it — use cases

**Important framing:** this feature is **not triggered by a chat prompt.** It
fires when a *pipeline failure* (an error string) reaches the remediation loop.
So "what to test with" = "what failure to inject." The **error text** is the
variable that drives every branch.

### 7.1 Level A — offline decision core (runs now, no creds)
The fastest way to see all branches. Run the planner/decision tests, or feed error
strings through the decision core. Each scenario below can be exercised via
`plan_remediation` (see `tests/unit/agents/governance_agent/test_remediation_planner.py`
for the exact call shape).

| # | Inject this error text | Expected outcome | Why |
|---|---|---|---|
| 1 | `HTTP 429 Too Many Requests; retry after 60s` | **RETRY** (≤3×), no card | Transient — retrying is correct, not theatre |
| 2 | `Login failed for user 'x'. (SQL error 18456)` | **ALERT_ONLY**, buttons `[Acknowledge]` | Deterministic but no data-shape mode → never guess (Inv 4) |
| 3 | `Disk space on volume C: is at 18% remaining` | **ALERT_ONLY** `[Acknowledge]` | Frank's disk example — real alert, not a fixable data-shape issue |
| 4 | `SQL compilation error: invalid identifier 'SETTLEMENT_CCY'` | **AWAIT_APPROVAL**, buttons `[Accept] [Decline]` + PR link | First-time schema_drift, reversible, no history → ask |
| 5 | same as #4, but seeded with 3+ prior approvals | **AUTO_EXECUTE**, buttons `[Undo Fix]`, "I handled it" | Seen-before + reversible + confident + breaker-closed → earned autonomy |
| 6 | `Contract enforcement failed for mart_x` (dbt_contract → UNKNOWN reversibility), even seeded 20× | **AWAIT_APPROVAL** `[Accept] [Decline]` | Irreversible never auto-executes regardless of history (the safety line) |
| 7 | seen-before reversible fix, but circuit breaker OPEN | **AWAIT_APPROVAL** `[Accept] [Decline]` | Kill switch overrides learned trust (Inv 12) |

### 7.2 Level B — live LLM investigation (needs Bedrock + Snowflake creds)
Exercises the real model investigating against a real warehouse. Uses a local
gitignored creds file (never commit / never paste into chat):

```bash
cd brightbot
# creds sourced from a local .investigation_creds.local.sh (AWS Bedrock creds are
# already in brightbot's .env; add SPIKE_INVESTIGATION_TOOL_ID + SPIKE_SF_* for the warehouse)
uv run python -c "<the make_model_propose_step + investigate_and_propose harness>"
```
**Expect:** the model runs read-only `information_schema` queries against Snowflake
and returns a `RemediationProposal` with a plain-language diagnosis + a confidence,
reversibility derived from the mode. (Proven working 2026-07-24.)

### 7.3 Level C — full staging demo (needs staging deploy + flag on + §6.1 endpoints)
The real end-to-end. To simulate a failure you must **actually break something** a
dbt model depends on (e.g. rename a column so the next run fails with
`invalid identifier`), then wait for the watchdog cycle. With the flag on for the
test workspace:
1. Watchdog detects the failure, classifies it.
2. Investigation runs against the warehouse; a fix PR is drafted.
3. A `remediation_proposal` card appears in **Slack + the webapp inbox** with
   Accept/Decline (or Undo Fix if seen-before).
4. Clicking a button → callback → BrightAgent proceeds/declines/undoes.
5. Next watchdog cycle VERIFIES: signature gone → "confirmed fixed"; recurred →
   escalation.

> **Blocked until §6.1:** step 4's click currently has no receiver endpoint. Steps
> 1–3 (detection → card render) and 5 (verify loop) are built; the click-handling
> round-trip is the remaining work.

---

## 8. Branches / PRs

| Repo | Branch |
|---|---|
| brightbot | `remediation-layer0-classifier-recall-gaps` |
| brightbot-slack-server | `feat/remediation-proposal-card` |
| brighthive-webapp | `feat/remediation-proposal-card` |
| agentic-project-mgmt (specs/evals/this doc) | `docs/agentic-remediation-spec-and-evals` |

All flagged behind `FEATURE_FLAG_REMEDIATION_GATE` (default off). CI note: local
verification used direct-import / `uv run` / `npx` where full deps existed; a
green CI run in each repo is the formal gate before merge.

---

## 9. Recommended next steps (in order)

1. **Build the action-receiver endpoints** (§6.1) — platform-core
   `resolveRemediationProposal` mutation + brightbot
   `/manage/remediation-proposals/{id}/{decision}` route, incl. how Accept resumes
   the paused fix. This is what makes the clicks *do* something.
2. **Staging deploy + live UI verification** of the cards (§6.3).
3. **Then** the MUTATE/auto-apply path (§6.2), behind its own safety review.
