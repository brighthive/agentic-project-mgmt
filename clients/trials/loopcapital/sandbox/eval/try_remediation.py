"""Try the agentic-remediation decision core on YOUR OWN use case (offline).

This runs the REAL deterministic decision logic from the
agentic-remediation-sandbox.md spec (§2/§3) — the "brain" that decides how
BrightAgent responds to a failure: retry it, alert-only, ask Accept/Decline, or
auto-fix-with-Undo. No cloud, no creds, stdlib only.

It does NOT run the LLM fix-drafting or the AgentCore sandbox (those need creds +
the brightbot env and a deploy). It DOES let you see, for any failure you invent,
exactly which path the loop takes and why.

USAGE
-----
List the built-in scenarios:
    python try_remediation.py --list

Run a built-in scenario:
    python try_remediation.py --scenario schema_drift_first_time
    python try_remediation.py --scenario schema_drift_seen_before

Run YOUR OWN failure (this is the point):
    python try_remediation.py \
        --error "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'" \
        --reversible yes \
        --has-undo yes \
        --confidence 0.92 \
        --approved-count 4 \
        --last-verified-ok yes \
        --breaker closed

Flags for --error mode (all optional; sensible defaults shown):
    --reversible      yes|no|unknown   (default: unknown  -> conservative, never auto-exec)
    --has-undo        yes|no           (default: no        -> a compensating/Undo action exists?)
    --confidence      0..1             (default: 0.5       -> diagnosis confidence)
    --approved-count  N                (default: 0         -> times a human Accepted this fix before)
    --last-verified-ok yes|no          (default: no        -> did the last application actually work?)
    --breaker         closed|open      (default: closed    -> auto-exec circuit breaker)
    --attempts        N                (default: 0         -> transient retries already done)

Read the output: it shows the failure classification, whether it retries, the
gate decision, the BUTTONS the user would see, and the MESSAGE BrightAgent says —
plus the reasons (the audit trail).
"""

from __future__ import annotations

import argparse
import sys

from remediation_core.core import (
    AUTO_EXEC_MIN_APPROVALS,
    AUTO_EXEC_MIN_CONFIDENCE,
    MAX_TRANSIENT_RETRIES,
    CircuitBreakerStatus,
    FixMemoryRecord,
    GateDecision,
    OutcomeStatus,
    RemediationProposal,
    Reversibility,
    classify_execution_outcome,
    decide_gate,
    should_retry,
)

# --- Built-in scenarios (each is a realistic Loop Capital / Longaeva case) -----
SCENARIOS: dict[str, dict] = {
    "schema_drift_first_time": {
        "blurb": "Vendor added a column; first time we've seen it. Should ASK (Accept/Decline).",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "reversible": "reversible", "has_undo": True, "confidence": 0.9,
        "approved_count": 0, "last_verified_ok": False, "breaker": "closed",
    },
    "schema_drift_seen_before": {
        "blurb": "Same drift, approved 4x before, reversible + Undo. Should AUTO-FIX (Undo only).",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "reversible": "reversible", "has_undo": True, "confidence": 0.92,
        "approved_count": 4, "last_verified_ok": True, "breaker": "closed",
    },
    "irreversible_even_if_seen": {
        "blurb": "A destructive fix seen many times — must STILL ask (irreversible never auto-execs).",
        "error": "Contract enforcement failed for mart_daily_portfolio_exposure",
        "reversible": "irreversible", "has_undo": False, "confidence": 0.99,
        "approved_count": 20, "last_verified_ok": True, "breaker": "closed",
    },
    "transient_timeout": {
        "blurb": "A 429/timeout — should RETRY, not diagnose.",
        "error": "HTTP 429 Too Many Requests from dbt Cloud API; retry after 60s",
        "reversible": "unknown", "has_undo": False, "confidence": 0.5,
        "approved_count": 0, "last_verified_ok": False, "breaker": "closed",
    },
    "unclassifiable_permission": {
        "blurb": "A permission error — must ALERT-ONLY, never guess a fix.",
        "error": "Login failed for user 'brighthive_ro'. (SQL error 18456)",
        "reversible": "unknown", "has_undo": False, "confidence": 0.5,
        "approved_count": 0, "last_verified_ok": False, "breaker": "closed",
    },
    "seen_before_but_breaker_open": {
        "blurb": "Eligible to auto-fix, but breaker is OPEN — must fall back to Accept/Decline.",
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "reversible": "reversible", "has_undo": True, "confidence": 0.95,
        "approved_count": 9, "last_verified_ok": True, "breaker": "open",
    },
    "disk_low_loopcapital": {
        "blurb": "Frank's SQL Server disk-space signal — a real alert, but NOT a data-shape fix.",
        "error": "Disk space on volume C: is at 18% remaining (threshold 20%)",
        "reversible": "unknown", "has_undo": False, "confidence": 0.5,
        "approved_count": 0, "last_verified_ok": False, "breaker": "closed",
    },
}

_REV = {"yes": Reversibility.REVERSIBLE, "reversible": Reversibility.REVERSIBLE,
        "no": Reversibility.IRREVERSIBLE, "irreversible": Reversibility.IRREVERSIBLE,
        "unknown": Reversibility.UNKNOWN}
_YN = {"yes": True, "no": False, "true": True, "false": False}


def run_case(*, error: str, reversible: str, has_undo: bool, confidence: float,
             approved_count: int, last_verified_ok: bool, breaker: str,
             attempts: int, blurb: str | None = None) -> None:
    rev = _REV[reversible.lower()]
    brk = CircuitBreakerStatus.OPEN if breaker.lower() == "open" else CircuitBreakerStatus.CLOSED

    outcome = classify_execution_outcome(
        status=OutcomeStatus.FAILED, error_text=error,
        workspace_id="ws_demo", source_type="dbt", job_id="job_demo",
    )

    print("=" * 74)
    if blurb:
        print(f"SCENARIO: {blurb}")
    print(f"ERROR    : {error!r}")
    print("-" * 74)
    print(f"  failure_class     : {outcome.failure_class.value}")
    print(f"  data_shape_mode   : {outcome.data_shape_mode}")
    print(f"  failure_signature : {outcome.failure_signature}")

    # Retry step (Invariant 2)
    retry = should_retry(outcome, attempts)
    if retry:
        print(f"\n  RETRY: yes — transient failure, {attempts}/{MAX_TRANSIENT_RETRIES} attempts used.")
        print("  (BrightAgent retries with backoff before diagnosing.)")
        print("=" * 74 + "\n")
        return
    if outcome.failure_class.value == "transient":
        print(f"\n  RETRY: exhausted ({attempts}/{MAX_TRANSIENT_RETRIES}) — now diagnosing.")
    else:
        print(f"\n  RETRY: no — {outcome.failure_class.value} failure, retrying is theatre; diagnosing.")

    # Build a proposal only if there's a classifiable mode (else gate alert-only)
    proposal = None
    history = None
    if outcome.data_shape_mode is not None:
        proposal = RemediationProposal(
            failure_signature=outcome.failure_signature,
            diagnosis=f"root cause looks like {outcome.data_shape_mode}; a surgical fix addresses it.",
            reversibility=rev, confidence=confidence, has_compensating_action=has_undo,
        )
        if approved_count > 0 or last_verified_ok:
            history = FixMemoryRecord(
                failure_signature=outcome.failure_signature,
                approved_count=approved_count, auto_executed_count=0,
                last_verified_ok=last_verified_ok, reversibility=rev,
            )

    result = decide_gate(outcome=outcome, proposal=proposal, history=history, breaker=brk)

    tag = {GateDecision.AUTO_EXECUTE: "AUTO-FIX (then Undo)",
           GateDecision.AWAIT_APPROVAL: "ASK FIRST (Accept/Decline)",
           GateDecision.ALERT_ONLY: "ALERT ONLY (no fix)"}[result.decision]
    print(f"\n  GATE DECISION : {result.decision.value}  ->  {tag}")
    print(f"  BUTTONS       : {'  '.join(result.buttons)}")
    print(f"\n  BrightAgent says:\n    \"{result.message}\"")
    print("\n  why:")
    for r in result.reasons:
        print(f"    - {r}")
    print("=" * 74 + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list built-in scenarios")
    ap.add_argument("--scenario", help="run a built-in scenario by name")
    ap.add_argument("--all", action="store_true", help="run every built-in scenario")
    ap.add_argument("--error", help="YOUR failure's error text")
    ap.add_argument("--reversible", default="unknown")
    ap.add_argument("--has-undo", default="no")
    ap.add_argument("--confidence", type=float, default=0.5)
    ap.add_argument("--approved-count", type=int, default=0)
    ap.add_argument("--last-verified-ok", default="no")
    ap.add_argument("--breaker", default="closed")
    ap.add_argument("--attempts", type=int, default=0)
    args = ap.parse_args()

    if args.list:
        print("Built-in scenarios:\n")
        for name, s in SCENARIOS.items():
            print(f"  {name:32s} {s['blurb']}")
        print(f"\nThresholds: MAX_TRANSIENT_RETRIES={MAX_TRANSIENT_RETRIES}  "
              f"AUTO_EXEC_MIN_APPROVALS={AUTO_EXEC_MIN_APPROVALS}  "
              f"AUTO_EXEC_MIN_CONFIDENCE={AUTO_EXEC_MIN_CONFIDENCE}")
        return 0

    if args.all:
        for name, s in SCENARIOS.items():
            run_case(error=s["error"], reversible=s["reversible"], has_undo=s["has_undo"],
                     confidence=s["confidence"], approved_count=s["approved_count"],
                     last_verified_ok=s["last_verified_ok"], breaker=s["breaker"],
                     attempts=0, blurb=f"[{name}] {s['blurb']}")
        return 0

    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"unknown scenario: {args.scenario}. Use --list.", file=sys.stderr)
            return 2
        s = SCENARIOS[args.scenario]
        run_case(error=s["error"], reversible=s["reversible"], has_undo=s["has_undo"],
                 confidence=s["confidence"], approved_count=s["approved_count"],
                 last_verified_ok=s["last_verified_ok"], breaker=s["breaker"],
                 attempts=0, blurb=s["blurb"])
        return 0

    if args.error:
        run_case(error=args.error, reversible=args.reversible,
                 has_undo=_YN.get(args.has_undo.lower(), False), confidence=args.confidence,
                 approved_count=args.approved_count,
                 last_verified_ok=_YN.get(args.last_verified_ok.lower(), False),
                 breaker=args.breaker, attempts=args.attempts)
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
