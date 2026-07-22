# Agentic Remediation — offline prototype + testers

Runnable, credential-free prototypes of the deterministic core of
`docs/specs/agentic-remediation-sandbox.md`. Stdlib-only Python 3. No cloud, no
Bedrock, no deploy.

## What's here

| File | What it is |
|---|---|
| `layer0_classifier_eval.py` + `corpus.py` | Layer 0 eval of the **shipped** classifier (`brightbot/.../root_cause_classifier.py`). Result: `LAYER0_RESULT.md`. |
| `decision_core_eval.py` | **Layer 0.5 eval of the decision core** — asserts the retry taxonomy + `decide_gate` invariant paths (24/24 = **GO**). The automated counterpart to `try_remediation.py`'s manual demo. |
| `remediation_core/classifier.py` | Recall-improved classifier prototype (the 4 Layer 0 gaps). **These patterns are now LANDED in the shipped `brightbot` classifier** (branch `remediation-layer0-classifier-recall-gaps` → PR against `develop`); this copy is kept as the offline reference. |
| `remediation_core/core.py` | The decision core: `ExecutionOutcome`, failure-class taxonomy, retry rule, and `decide_gate` (progressive-trust logic — spec §2/§3). Not yet ported to `brightbot` (next ticket). |
| `try_remediation.py` | **The tester you run with your own use case.** |

## Run the evals (both should print GO)

```bash
python layer0_classifier_eval.py    # classifier: recognizes what broke
python decision_core_eval.py        # decision core: makes the right call
```

## Test YOUR OWN use case

List built-in scenarios (each a real Loop Capital / Longaeva case):
```bash
python try_remediation.py --list
python try_remediation.py --all
```

Feed your own failure and see how BrightAgent would respond:
```bash
python try_remediation.py \
  --error "your real error text here" \
  --reversible yes|no|unknown \
  --has-undo yes|no \
  --confidence 0.0..1.0 \
  --approved-count N \
  --last-verified-ok yes|no \
  --breaker closed|open
```

The output shows: failure class → retry-or-not → gate decision → **the buttons
the user sees** → **what BrightAgent says** → the reasons (audit trail).

## What this proves — and what it does NOT

**Proves (real, verified today):** the deterministic *brain* — classification,
retryable-vs-diagnose, and the Accept/Decline vs auto-fix+Undo gate — behaves per
the spec's safety invariants. Irreversible never auto-executes; unclassifiable
never guesses; breaker-open forces approval; transient retries.

**Does NOT (needs creds + env + a deploy, per the test plan):**
- **Layer 1** — the LLM actually *drafting a correct surgical fix* (needs Bedrock).
- **Layer 3** — the AgentCore Code Interpreter *investigating* a novel failure.
- **The UI** — this is a CLI; the Slack/webapp card + a staging deploy are how it
  reaches the BrightAgent UI.

## Known prototype limitations (honest)

- `failure_signature` in the CLI collides across the `None`-mode demo cases
  because they share a fixed demo `job_id`; production keys on the real per-failure
  `job_id`. Demo artifact, not a logic bug.
- `classifier.py` here is the offline **reference copy**; the 4 recall patterns
  are now landed in the shipped `brightbot` classifier (see the table above).
- `core.py` (the decision core) is verified offline (`decision_core_eval.py`, 24/24)
  and is **now ported to `brightbot`** (`governance_agent/tools/remediation_decision.py`
  + `fix_memory_store.py` + `remediation_planner.py`, all unit-tested), and **wired
  into the watchdog behind the default-off `FEATURE_FLAG_REMEDIATION_GATE`**
  (`pipeline_watchdog_task._attempt_remediation`). Flag-off = unchanged production
  behavior; flag-on = unclassifiable failures gated to alert-only before drafting.
  The full AUTO_EXECUTE + Undo path (needs the RemediationProposal card + VERIFYING
  loop) is still pending — see the two repos' PRs.
- `confidence` is supplied by you in the CLI; in production it comes from the
  diagnosis/judge (Layer 1).
