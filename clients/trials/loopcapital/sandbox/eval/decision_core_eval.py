"""Layer 0.5 eval — remediation DECISION-CORE correctness (offline, no cloud).

Companion to layer0_classifier_eval.py. That harness proves the classifier
*recognizes* what broke; this one proves the deterministic decision core
(remediation_core/core.py) makes the *right call* about what to DO — the
"which buttons appear" brain the customer feedback is really about.

Why this exists: `try_remediation.py` is a manual demo (you eyeball the
output). Safety-critical gate logic — "may this fix auto-execute against a
customer's production warehouse?" — must be ASSERTED, not eyeballed. This
harness encodes every invariant path from agentic-remediation-sandbox.md §3 as
a labeled case and fails loudly on any wrong decision.

Two labeled corpora:
  RETRY_CASES  — classify_failure_class + should_retry (Invariant 2)
  GATE_CASES   — decide_gate across Invariants 4, 5, 6, 7, 12

Run:
  python decision_core_eval.py
  python decision_core_eval.py --show-passes
Exit code 0 == all correct (GO); 1 == a wrong decision (NO-GO).
"""

from __future__ import annotations

import argparse
import sys

from remediation_core.core import (
    AUTO_EXEC_MIN_APPROVALS,
    AUTO_EXEC_MIN_CONFIDENCE,
    MAX_TRANSIENT_RETRIES,
    CircuitBreakerStatus,
    FailureClass,
    FixMemoryRecord,
    GateDecision,
    OutcomeStatus,
    RemediationProposal,
    Reversibility,
    classify_execution_outcome,
    classify_failure_class,
    decide_gate,
    should_retry,
)

# --------------------------------------------------------------------------- #
# Corpus 1 — failure-class taxonomy + retry decision (Invariant 2)            #
# Each: (error_text, expected_class, attempts_so_far, expected_should_retry)  #
# --------------------------------------------------------------------------- #
RETRY_CASES: list[tuple[str, FailureClass, int, bool]] = [
    # --- TRANSIENT -> retry while attempts remain -------------------------- #
    ("HTTP 429 Too Many Requests from dbt Cloud API; retry after 60s",
     FailureClass.TRANSIENT, 0, True),
    ("dbt run failed: connection timed out after 300s", FailureClass.TRANSIENT, 1, True),
    ("Databricks cluster terminated: DRIVER_UNRESPONSIVE", FailureClass.TRANSIENT, 0, True),
    ("Service temporarily unavailable (503)", FailureClass.TRANSIENT, 2, True),
    ("Deadlock detected; transaction was chosen as the deadlock victim",
     FailureClass.TRANSIENT, 0, True),
    # transient BUT retries exhausted -> stop retrying, go diagnose
    ("HTTP 429 Too Many Requests; retry after 60s", FailureClass.TRANSIENT,
     MAX_TRANSIENT_RETRIES, False),
    ("connection timed out", FailureClass.TRANSIENT, MAX_TRANSIENT_RETRIES + 1, False),
    # --- DETERMINISTIC -> never retry, always diagnose --------------------- #
    ("SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
     FailureClass.DETERMINISTIC, 0, False),
    ("Login failed for user 'brighthive_ro'. (SQL error 18456)",
     FailureClass.DETERMINISTIC, 0, False),
    ("Contract enforcement failed for mart_daily_portfolio_exposure",
     FailureClass.DETERMINISTIC, 0, False),
    ("Permission denied: VIEW SERVER STATE required", FailureClass.DETERMINISTIC, 0, False),
    # --- UNKNOWN -> treated as deterministic for safety, never retry ------- #
    ("Disk space on volume C: is at 18% remaining (threshold 20%)",
     FailureClass.UNKNOWN, 0, False),
    ("Segmentation fault in dbt adapter; process exited with code 139",
     FailureClass.UNKNOWN, 0, False),
    ("", FailureClass.UNKNOWN, 0, False),
]


# --------------------------------------------------------------------------- #
# Corpus 2 — the gate decision (Invariants 4, 5, 6, 7, 12)                     #
# Each case names the invariant it guards. `expected_buttons` is asserted too #
# because the buttons ARE the product contract (Accept/Decline vs Undo Fix).  #
# --------------------------------------------------------------------------- #
def _proposal(*, mode_present: bool, reversibility: Reversibility, confidence: float,
              has_undo: bool) -> RemediationProposal | None:
    if not mode_present:
        return None
    return RemediationProposal(
        failure_signature="sig:test",
        diagnosis="a surgical fix addresses it.",
        reversibility=reversibility,
        confidence=confidence,
        has_compensating_action=has_undo,
    )


def _history(*, approved: int, verified_ok: bool,
             reversibility: Reversibility) -> FixMemoryRecord | None:
    if approved == 0 and not verified_ok:
        return None
    return FixMemoryRecord(
        failure_signature="sig:test",
        approved_count=approved,
        auto_executed_count=0,
        last_verified_ok=verified_ok,
        reversibility=reversibility,
    )


GATE_CASES: list[dict] = [
    {
        "name": "unclassifiable -> ALERT_ONLY (Inv 4)",
        "error": "Login failed for user 'brighthive_ro'. (SQL error 18456)",
        "mode_present": False, "reversibility": Reversibility.UNKNOWN,
        "confidence": 0.5, "has_undo": False, "approved": 0, "verified_ok": False,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.ALERT_ONLY, "buttons": ("Acknowledge",),
    },
    {
        "name": "disk-low unknown -> ALERT_ONLY (Inv 4)",
        "error": "Disk space on volume C: is at 18% remaining (threshold 20%)",
        "mode_present": False, "reversibility": Reversibility.UNKNOWN,
        "confidence": 0.5, "has_undo": False, "approved": 0, "verified_ok": False,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.ALERT_ONLY, "buttons": ("Acknowledge",),
    },
    {
        "name": "first-time reversible fix -> AWAIT_APPROVAL (Inv 5/6: no history)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": 0.9, "has_undo": True, "approved": 0, "verified_ok": False,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
    {
        "name": "seen-before reversible confident -> AUTO_EXECUTE (Inv 6/7)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": 0.92, "has_undo": True,
        "approved": AUTO_EXEC_MIN_APPROVALS + 1, "verified_ok": True,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AUTO_EXECUTE, "buttons": ("Undo Fix",),
    },
    {
        "name": "irreversible even if seen 20x -> AWAIT_APPROVAL (Inv 5, the safety line)",
        "error": "Contract enforcement failed for mart_daily_portfolio_exposure",
        "mode_present": True, "reversibility": Reversibility.IRREVERSIBLE,
        "confidence": 0.99, "has_undo": False, "approved": 20, "verified_ok": True,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
    {
        "name": "no compensating action blocks auto-exec (Inv 6)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": 0.95, "has_undo": False,  # <-- the only failing gate
        "approved": AUTO_EXEC_MIN_APPROVALS + 5, "verified_ok": True,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
    {
        "name": "confidence below floor blocks auto-exec (Inv 6)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": AUTO_EXEC_MIN_CONFIDENCE - 0.01,  # <-- just under the bar
        "has_undo": True, "approved": AUTO_EXEC_MIN_APPROVALS + 5, "verified_ok": True,
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
    {
        "name": "too few prior approvals blocks auto-exec (Inv 6)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": 0.95, "has_undo": True,
        "approved": AUTO_EXEC_MIN_APPROVALS - 1,  # <-- one short
        "verified_ok": True, "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
    {
        "name": "last application NOT verified blocks auto-exec (Inv 6)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": 0.95, "has_undo": True, "approved": AUTO_EXEC_MIN_APPROVALS + 5,
        "verified_ok": False,  # <-- last run didn't clear the signature
        "breaker": CircuitBreakerStatus.CLOSED,
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
    {
        "name": "breaker OPEN forces approval even when fully eligible (Inv 12)",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "mode_present": True, "reversibility": Reversibility.REVERSIBLE,
        "confidence": 0.98, "has_undo": True, "approved": AUTO_EXEC_MIN_APPROVALS + 9,
        "verified_ok": True,
        "breaker": CircuitBreakerStatus.OPEN,  # <-- kill switch engaged
        "expect": GateDecision.AWAIT_APPROVAL, "buttons": ("Accept", "Decline"),
    },
]


def run_retry_corpus(show_passes: bool) -> list[str]:
    failures: list[str] = []
    for error, expected_class, attempts, expected_retry in RETRY_CASES:
        got_class = classify_failure_class(error)
        outcome = classify_execution_outcome(
            status=OutcomeStatus.FAILED, error_text=error,
            workspace_id="ws", source_type="dbt", job_id="job",
        )
        got_retry = should_retry(outcome, attempts)
        ok = got_class == expected_class and got_retry == expected_retry
        if ok:
            if show_passes:
                print(f"  PASS  {expected_class.value:13s} retry={expected_retry!s:5s} <- {error[:56]!r}")
        else:
            failures.append(
                f"class exp={expected_class.value} got={got_class.value} | "
                f"retry(attempts={attempts}) exp={expected_retry} got={got_retry} | {error[:70]!r}"
            )
    return failures


def run_gate_corpus(show_passes: bool) -> list[str]:
    failures: list[str] = []
    for c in GATE_CASES:
        outcome = classify_execution_outcome(
            status=OutcomeStatus.FAILED, error_text=c["error"],
            workspace_id="ws", source_type="dbt", job_id="job",
        )
        # The eval fixes mode presence explicitly (mode_present) so a gate case
        # is independent of the classifier's own coverage — a gate bug can't
        # hide behind a classifier miss, or vice versa.
        proposal = _proposal(mode_present=c["mode_present"], reversibility=c["reversibility"],
                             confidence=c["confidence"], has_undo=c["has_undo"])
        history = _history(approved=c["approved"], verified_ok=c["verified_ok"],
                          reversibility=c["reversibility"])
        # Force the outcome's mode to match the case's intent (decouple from classifier).
        from dataclasses import replace
        outcome = replace(outcome, data_shape_mode=("schema_drift" if c["mode_present"] else None))

        result = decide_gate(outcome=outcome, proposal=proposal, history=history,
                             breaker=c["breaker"])
        ok = result.decision == c["expect"] and result.buttons == c["buttons"]
        if ok:
            if show_passes:
                print(f"  PASS  {c['name']}")
        else:
            failures.append(
                f"{c['name']}\n      decision exp={c['expect'].value} got={result.decision.value}"
                f" | buttons exp={c['buttons']} got={result.buttons}"
            )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--show-passes", action="store_true")
    args = ap.parse_args()

    print(f"Thresholds: MAX_TRANSIENT_RETRIES={MAX_TRANSIENT_RETRIES}  "
          f"AUTO_EXEC_MIN_APPROVALS={AUTO_EXEC_MIN_APPROVALS}  "
          f"AUTO_EXEC_MIN_CONFIDENCE={AUTO_EXEC_MIN_CONFIDENCE}\n")

    print("Corpus 1 — failure-class + retry decision (Invariant 2)")
    retry_failures = run_retry_corpus(args.show_passes)
    print("Corpus 2 — gate decision (Invariants 4/5/6/7/12)")
    gate_failures = run_gate_corpus(args.show_passes)

    print("\n" + "=" * 72)
    all_failures = retry_failures + gate_failures
    if all_failures:
        print("FAILURES")
        print("=" * 72)
        for f in all_failures:
            print(f"  {f}")
    else:
        print("No failures.")

    retry_total = len(RETRY_CASES)
    gate_total = len(GATE_CASES)
    print("\n" + "=" * 72)
    print("HEADLINE")
    print("=" * 72)
    print(f"  Retry corpus : {retry_total - len(retry_failures)}/{retry_total} correct")
    print(f"  Gate corpus  : {gate_total - len(gate_failures)}/{gate_total} correct")
    verdict = "GO" if not all_failures else "NO-GO"
    print(f"\n  Decision-core verdict: {verdict}")
    print("=" * 72)
    return 0 if not all_failures else 1


if __name__ == "__main__":
    sys.exit(main())
