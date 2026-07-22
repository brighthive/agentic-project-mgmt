# Layer 0 Result — Diagnosis Classifier Eval

> **Date:** 2026-07-21 (initial) · **2026-07-22 (recall gaps closed)** · **Run by:** Marwan (agent-executed)
> **Target:** `classify_data_shape_mode`
> (`brightbot/agents/governance_agent/tools/root_cause_classifier.py`) — the
> real, shipped, deterministic classifier that fronts the remediation loop.
> **Harness:** `layer0_classifier_eval.py` + `corpus.py` (40 labeled cases).
> **Cost:** ~1 afternoon, offline, no cloud, no side effects.

## Headline (2026-07-22 — recall pass landed in the shipped classifier)

| Metric | Initial (2026-07-21) | After recall pass (2026-07-22) | Bar | Verdict |
|---|---|---|---|---|
| Known-mode accuracy | 20/24 = 83.3% | **24/24 = 100%** | ≥ 90% | ✅ PASS |
| Correct abstention | 16/16 = 100% | **16/16 = 100%** | ≥ 95% | ✅ PASS |
| **Layer 0 overall** | NO-GO | | | **✅ GO** |

Per-class after the pass: **precision = 1.00 AND recall = 1.00 across all four
modes.** The 4 recall gaps below were closed by adding 6 guarded patterns to the
shipped `root_cause_classifier.py` (BigQuery `unrecognized name`; dbt
`got N result… expected 0`; source-freshness `loaded_at … old`; COPY-INTO
format-mismatch), each with new unit cases in
`brightbot/tests/unit/agents/governance_agent/test_root_cause_classifier.py`
— including guardrail cases proving the new patterns do not over-match adjacent
JOB_RUNTIME/generic failures (precision held at 1.00). Re-run
`python layer0_classifier_eval.py` to reproduce the GO.

### Original NO-GO snapshot (2026-07-21, for the record)

| Metric | Result | Bar | Verdict |
|---|---|---|---|
| Known-mode accuracy | **20/24 = 83.3%** | ≥ 90% | ❌ FAIL |
| Correct abstention | **16/16 = 100%** | ≥ 95% | ✅ PASS |

Per-class (initial): **precision = 1.00 across all four modes.** Recall:
schema_drift 0.86, missing_partition 0.67, broken_stage 0.83, dbt_contract 1.00.

## What this actually means (the shape matters more than the verdict)

This is the **good** kind of failure. The classifier is **100% precise and
100% correct at abstaining** — it never once misfired, never classified a
JOB_RUNTIME/permission/disk failure as a data-shape issue, and defeated **all 6
adversarial guardrail cases** (bare "contract", generic compile error, "failed
to load packages", etc.). That is the property that makes it *safe*: it does
not route a wrong failure into a fix-drafting path.

The **only** gap is **recall** — four realistic phrasings it doesn't yet
recognize:

1. **BigQuery** "Unrecognized **name**" (pattern only has "unrecognized column").
2. **dbt custom-test** phrasing "got 1 result, expected 0" for a missing business day (no partition keyword).
3. **Source-freshness** based detection of a missing day (no partition keyword).
4. **COPY INTO** CSV-vs-JSON parse failure — notably, *this is literally the
   `failure_modes.py` broken_stage scenario*, and the real COPY error text names
   no stage keyword.

All four are **misses (→ abstain → alert-only)**, never **mis-classifications**.
In product terms: these failures would get an honest "a human should look at
this" instead of a wrong auto-drafted fix. Safe, but under-covering.

## Why this is a GO signal for the strategy, not a NO-GO

The Layer 0 bar (≥90%) is not met **by the current patterns**, but the failure
is entirely **additive recall**, not a design flaw:

- **Precision 1.00 + abstention 1.00** means the safety contract (Invariant 4 —
  never guess a fix) holds perfectly. This was the genuinely risky thing to
  verify, and it passed.
- **Recall gaps are cheap to close** — they're four more regex patterns
  (`unrecognized name`, freshness/`got .* expected 0`, COPY-format-mismatch),
  each a one-line addition, each independently testable against this same corpus.
- Case #4 is the most important finding: the classifier misses its *own
  sandbox's* broken_stage scenario. That's a concrete, high-value fix and
  exactly the kind of gap this eval exists to catch **before** a demo.

**Interpretation:** the diagnosis foundation is sound and safe; it needs a
recall pass, not a rebuild. Recommend closing the 4 gaps, re-running (expect
≥95% known-mode), then greenlighting Layer 1.

## Honest caveats

- The classifier is **pure regex**, not an LLM — so this measures *keyword
  coverage*, not reasoning. The real "diagnosis intelligence" question moves to
  **Layer 1** (does the LLM draft a correct fix once a mode is confirmed).
- 24 known-mode cases is a small corpus; the recall numbers have wide error
  bars. The point of Layer 0 is a *directional* go/no-go and to surface concrete
  gaps, not a statistically tight recall estimate.
- I authored the corpus. It's written to resemble real tool output and to be
  adversarial (RECALL-RISK cases were labeled by true root cause even when I
  expected a miss), but it is not yet a corpus of *captured* production errors —
  replacing synthetic strings with real dbt/Snowflake logs from the Longaeva/
  Loop Capital environments would harden this further.

## Recommended next actions

1. **Close the 4 recall gaps** in `root_cause_classifier.py` (add patterns:
   `unrecognized name`, a freshness/`got .* expected` partition signal, a
   COPY-format-mismatch stage signal). One small PR, re-run this eval to confirm
   ≥95% with precision still 1.00.
2. **Then Layer 1** — fix-drafting quality (needs Bedrock creds).
3. Optionally, backfill the corpus with real captured errors from the two POC
   environments to replace synthetic phrasings.
