# Agentic Remediation — Test Plan (How We Prove It)

> **Audience:** Kuri + leadership; companion to `AGENTIC_REMEDIATION_STRATEGY.md`.
> **Date:** 2026-07-21 · **Author:** Marwan
> **Purpose:** turn "will it work?" into a measurable, staged go/no-go — cheapest
> and most honest test first, so we learn whether the *hard part* (reliable
> diagnosis on real failures) works **before** investing in the parts that don't
> exist yet.
> **Status:** proposal — nothing run yet.

---

## The principle

We do **not** find out if this works by planning harder. We find out by making
"what we want" a **measurable bar** and proving it on a **narrow scope** before
betting on it. Each layer below is a gate: if it fails, we stop and fix *that*
before spending on the next — turning a quarter-long bet into a series of
cheap, early signals.

Critically, the layers are ordered so the **highest-uncertainty, lowest-cost**
test runs first. The open research question is *"can BrightAgent reliably
diagnose a real failure?"* — Layer 0 answers exactly that, in an afternoon, with
no cloud spend and no side effects.

## What already exists (so testing can start now, not after a build)

- **`classify_data_shape_mode(error_text)`** — deterministic classifier, the
  first step of the shipped remediation loop
  (`brightbot/agents/governance_agent/tools/root_cause_classifier.py`,
  called from `agents/dbt_agent/remediation_agent.py`).
- **`remediation_agent_graph`** — the two-node `dbt_initialise → draft_or_alert`
  loop (`agents/dbt_agent/remediation_agent.py`, dated 2026-07-15). Drafts a
  surgical fix + opens a PR; **never merges, never guesses** (returns
  "cannot auto-diagnose" when unclassifiable).
- **`failure_modes.py`** — all 4 Longaeva failure modes with
  `inject()`/`detect()`/`heal()` + the *exact expected fix*
  (`clients/trials/longaeva/sandbox/self_healing/failure_modes.py`).
- **Loop Capital SQL Server sandbox** — local Docker fixture
  (`clients/trials/loopcapital/sandbox/`), incl. `fill_disk.sh` for the
  disk-space demo and SQL Agent jobs.

Layers 0–2 test the loop we've designed **on real Loop Capital / Longaeva use
cases** because these fixtures and the classifier are already in the tree.
Layer 3 (the AgentCore sandbox + progressive trust) is net-new and is where the
spec is needed.

---

## Layer 0 — Diagnosis classification (offline, no cloud, no side effects)

**Question it answers:** *Can BrightAgent even recognize what broke?* — the
foundation of everything downstream.

| | |
|---|---|
| **What runs** | `classify_data_shape_mode(error_text)` against a labeled corpus |
| **Corpus** | ~20–40 real dbt/warehouse error strings: the 4 modes (schema_drift, missing_partition, broken_stage, dbt_contract) + **deliberately unclassifiable** cases (timeouts, cluster OOM, permission errors) that MUST return `None` |
| **Needs** | brightbot Python env only. No Bedrock, no Snowflake, no network. |
| **Metric** | Precision + recall per class; **and** the "correctly abstains" rate on unclassifiable cases (a false-confident classification is worse than an abstention — Invariant 4) |
| **Pass bar (proposed)** | ≥ 90% correct on the 4 known modes **AND** ≥ 95% correct abstention on the unclassifiable set. Numbers to confirm with Kuri. |
| **Cost** | ~an afternoon |
| **Honest caveat** | `classify_data_shape_mode` may be keyword/heuristic-based rather than an LLM — if so, this is a *unit* test of coverage, and Layer 1 becomes where real diagnosis intelligence is measured. Either way the result is informative: it tells us whether the current classifier is fit for real error text or needs replacing. |

**Why first:** cheapest possible test of the single riskiest assumption. If the
system can't tell schema-drift from a broken stage on *real* error text, nothing
downstream matters — and we'd know within hours.

---

## Layer 1 — Fix drafting quality (needs Bedrock; no Snowflake)

**Question it answers:** *Given a correctly classified failure, does the agent
draft a correct, surgical fix — or a plausible-but-wrong one?*

| | |
|---|---|
| **What runs** | `remediation_agent_graph`'s `draft_or_alert` node against each of the 4 modes' real error + diagnosis, PR tool stubbed or pointed at a throwaway repo |
| **Needs** | Bedrock model access (staging creds or local). A disposable GitHub repo if we exercise the real PR tool. **No Snowflake.** |
| **Metric** | Does the drafted diff match the fixture's `fix_summary` / `fix_ddl` intent? Is it **surgical** (scoped to the failure, no incidental rewrites)? Accept-without-edit rate. |
| **Pass bar (proposed)** | On the 4 modes, drafted fix is correct-and-surgical ≥ 3/4, with zero destructive-scope violations. Confirm with Kuri. |
| **Cost** | ~1–2 days incl. corpus + a throwaway repo |
| **Honest caveat** | This is LLM-driven → non-deterministic. Run N=3+ per case and report variance, not a single lucky pass. This is the layer where "diagnosis quality on real failure modes" — the thing research could NOT measure — becomes a real number. |

---

## Layer 2 — Full detect→heal loop (needs live Snowflake POC)

**Question it answers:** *Does the whole loop close against ground truth on a
real warehouse — inject a failure, detect it, propose the fix, and confirm the
fix actually clears the failure?*

| | |
|---|---|
| **What runs** | `failure_modes.py run-all` (already proves inject→detect→heal 4/4), then wire the agent's drafted fix in place of the fixture's hard-coded `heal()` and confirm `detect()` clears |
| **Needs** | **Live Snowflake POC + `~/.snowflake/config.toml` creds.** `inject()` **mutates a real (disposable) Snowflake schema** — a genuine side effect on a shared environment. |
| **Metric** | For each mode: agent-produced fix applied → `detect()` returns healthy. The GC-11 bar: "4/4 failure modes → surgical fix that clears detection." |
| **Pass bar** | 4/4 modes heal via the agent's own fix (not the fixture's), matching GC-11. |
| **Cost** | ~2–3 days; **must run where the sandbox + creds live, not from an arbitrary dev seat** |
| **Honest caveats** | (1) Real mutation on a shared POC — only against a throwaway schema, never a customer prod. (2) The Loop Capital SQL Server sandbox (`fill_disk.sh` + SQL Agent jobs) is the parallel track for Frank's disk-space objection — same layer, different fixture. (3) **Idempotency risk**: re-running a partially-applied fix can double-apply — every remediation action needs an idempotency key (BrightRoutines already hit schedule-double-create). |

---

## Layer 3 — Sandbox + progressive trust (does not exist yet — needs the spec)

**Question it answers:** *Can the agent investigate a novel failure in a real
compute sandbox (read-only first), and can "seen-it-before → auto-execute + Undo"
be made safe?*

| | |
|---|---|
| **What runs** | Nothing yet — this is the net-new AgentCore Code Interpreter integration + the fix-memory store + the progressive-trust gate |
| **Needs** | The implementation spec (`agentic-remediation-sandbox.md`), then a build. Depends on confirming AgentCore Code Interpreter can reach a customer network (the VPC-mode question flagged in research). |
| **Metric** | (a) Read-only diagnostic: on a failure NOT in the 4 known modes, does sandbox investigation produce a correct root cause? (b) Auto-execute: does a known+reversible fix execute, verify, and offer Undo — with the circuit breaker tripping correctly under induced bad outcomes? |
| **Pass bar** | TBD in the spec |
| **Cost** | Weeks; gated on Layers 0–2 passing |
| **Honest caveat** | Devin's independent eval was 3/20 on open-ended tasks — a sandbox makes an agent able to *check itself*, not automatically *correct*. Layer 3 is the highest-risk layer and is deliberately last and flag-gated. |

---

## Decision gates (the go/no-go story)

```
Layer 0 pass?  ──no──▶  STOP. Classifier can't recognize real failures.
   │                     Fix classification before anything else. (Cost: 1 afternoon.)
  yes
   ▼
Layer 1 pass?  ──no──▶  STOP. Agent classifies but drafts wrong/unsafe fixes.
   │                     The Accept/Decline UX still ships (human catches bad drafts),
  yes                    but auto-execute is off the table until this passes.
   ▼
Layer 2 pass?  ──no──▶  Loop doesn't close on a real warehouse. Debug the
   │                     detect/heal wiring before committing to Layer 3.
  yes
   ▼
Build Layer 3 (sandbox + progressive trust), flag-gated, breaker live.
```

**The key property:** Layers 0–1 alone are enough to ship the **Accept/Decline**
experience — the interaction Loop Capital actually asked for — because a wrong
draft costs a "Decline," not an incident. Layer 2 confirms fixes really work.
Only Layer 3 (auto-execute) needs the full trust machinery. So we can deliver
the demonstrable leap early and prove each riskier step before paying for it.

---

## What each layer needs from whom

| Layer | Blocker on | Who unblocks |
|---|---|---|
| 0 | brightbot Python env access | Marwan (local) — can start immediately |
| 1 | Bedrock creds + throwaway GitHub repo | Kuri / infra |
| 2 | Live Snowflake POC creds + Loop Capital Docker sandbox | whoever owns the POC env |
| 3 | The implementation spec + AgentCore Code Interpreter (+ VPC-reach confirmation) | Kuri sign-off → build |

---

## Recommendation

Run **Layer 0 first** — it's an afternoon, needs nothing but the repo, and it
tests the single riskiest assumption. Its result is the most honest possible
input to the Kuri conversation: either "the classifier already recognizes real
failures, here are the numbers, greenlight Layer 1," or "it doesn't, and here's
exactly what needs fixing before this strategy is real." Everything after is
gated on that.
