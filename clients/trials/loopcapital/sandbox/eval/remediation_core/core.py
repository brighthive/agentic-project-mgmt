"""Deterministic decision core of the agentic-remediation loop (PROTOTYPE).

Implements spec agentic-remediation-sandbox.md §2/§3 as runnable, stdlib-only
Python — no LLM, no cloud, no creds. This is the *brain* of the customer's
described behavior: given a failure and a few facts about the proposed fix,
decide WHICH buttons appear and WHAT BrightAgent says.

What this IS: the deterministic scaffolding (Invariants 2, 4, 5, 6, 7, 12) that
the spec insists must NOT be an LLM. What this is NOT: the LLM fix-drafting
(Layer 1) or the AgentCore sandbox (Layer 3) — those wrap around this core and
need creds/env. The gate logic here is exactly what makes Accept/Decline vs
"I-handled-it + Undo" correct.

Constants below are the named, overridable thresholds the spec requires
(no magic numbers).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum

from .classifier import classify_data_shape_mode

# --- Named thresholds (Invariant 2/6; workspace-overridable in production) -----
MAX_TRANSIENT_RETRIES = 3
AUTO_EXEC_MIN_APPROVALS = 3       # times a human Accepted this fix shape before auto-exec
AUTO_EXEC_MIN_CONFIDENCE = 0.85


# --- §2 enums ------------------------------------------------------------------
class OutcomeStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"


class FailureClass(str, Enum):
    TRANSIENT = "transient"          # retry with backoff
    DETERMINISTIC = "deterministic"  # do NOT retry; diagnose
    UNKNOWN = "unknown"              # treated as DETERMINISTIC for safety


class Reversibility(str, Enum):
    REVERSIBLE = "reversible"
    IRREVERSIBLE = "irreversible"
    UNKNOWN = "unknown"              # conservative == IRREVERSIBLE for gating


class GateDecision(str, Enum):
    AUTO_EXECUTE = "auto_execute"
    AWAIT_APPROVAL = "await_approval"
    ALERT_ONLY = "alert_only"


class CircuitBreakerStatus(str, Enum):
    CLOSED = "closed"
    OPEN = "open"


# --- §2 dataclasses ------------------------------------------------------------
@dataclass(frozen=True)
class ExecutionOutcome:
    status: OutcomeStatus
    failure_class: FailureClass | None
    error_text: str | None
    failure_signature: str
    data_shape_mode: str | None      # from the classifier, or None (unclassifiable)


@dataclass(frozen=True)
class FixMemoryRecord:
    failure_signature: str
    approved_count: int
    auto_executed_count: int
    last_verified_ok: bool
    reversibility: Reversibility


@dataclass(frozen=True)
class RemediationProposal:
    failure_signature: str
    diagnosis: str
    reversibility: Reversibility
    confidence: float
    has_compensating_action: bool    # the Undo; False => cannot auto-execute (Invariant 6)


@dataclass(frozen=True)
class GateResult:
    decision: GateDecision
    buttons: tuple[str, ...]
    message: str                     # what BrightAgent says to the user
    reasons: tuple[str, ...]         # why this decision (the audit trail)


# --- Failure-class taxonomy (Invariant 2) --------------------------------------
# Deterministic signals: retrying these is theatre. Ordered checks, first hit wins.
_TRANSIENT_PATTERNS = (
    r"\b429\b", "too many requests", "rate limit", "throttl",
    "timed out", "timeout", "deadlock", "connection reset",
    "temporarily unavailable", "please retry", "retry after",
    "service unavailable", r"\b503\b", "cluster.*(restart|unresponsive|terminat)",
)
_DETERMINISTIC_HINTS = (
    "invalid identifier", "does not exist", "permission", "denied",
    "login failed", "contract", "type mismatch", "not authorized",
    "compilation error", "syntax error", "not found",
)


def classify_failure_class(error_text: str | None) -> FailureClass:
    if not error_text:
        return FailureClass.UNKNOWN
    t = error_text.lower()
    for pat in _TRANSIENT_PATTERNS:
        if re.search(pat, t):
            return FailureClass.TRANSIENT
    for hint in _DETERMINISTIC_HINTS:
        if hint in t:
            return FailureClass.DETERMINISTIC
    return FailureClass.UNKNOWN


def _signature(workspace_id: str, source_type: str, job_id: str, mode: str | None,
               error_text: str | None) -> str:
    # Stable across polls: keyed on the failure shape, not the timestamp.
    basis = f"{workspace_id}|{source_type}|{job_id}|{mode or 'unclassified'}"
    return "sig:" + hashlib.sha256(basis.encode()).hexdigest()[:16]


def classify_execution_outcome(*, status: OutcomeStatus, error_text: str | None,
                               workspace_id: str, source_type: str,
                               job_id: str) -> ExecutionOutcome:
    """Structured detection (Invariant 1) — derived from inputs, never model prose."""
    if status == OutcomeStatus.SUCCESS:
        return ExecutionOutcome(status, None, None,
                                _signature(workspace_id, source_type, job_id, None, None), None)
    mode = classify_data_shape_mode(error_text)
    fclass = classify_failure_class(error_text)
    return ExecutionOutcome(
        status=status,
        failure_class=fclass,
        error_text=error_text,
        failure_signature=_signature(workspace_id, source_type, job_id, mode, error_text),
        data_shape_mode=mode,
    )


# --- Retry decision (Invariant 2) ----------------------------------------------
def should_retry(outcome: ExecutionOutcome, attempts_so_far: int) -> bool:
    if outcome.status == OutcomeStatus.SUCCESS:
        return False
    if outcome.failure_class != FailureClass.TRANSIENT:
        return False                                   # deterministic/unknown -> diagnose, don't retry
    return attempts_so_far < MAX_TRANSIENT_RETRIES


# --- The gate (Invariants 4,5,6,7,12) — the "which buttons" brain ---------------
def decide_gate(*, outcome: ExecutionOutcome, proposal: RemediationProposal | None,
                history: FixMemoryRecord | None,
                breaker: CircuitBreakerStatus) -> GateResult:
    # Invariant 4: unclassifiable / no fix drafted -> alert only, never guess.
    if outcome.data_shape_mode is None or proposal is None:
        return GateResult(
            decision=GateDecision.ALERT_ONLY,
            buttons=("Acknowledge",),
            message=(
                f"I hit a failure I can't safely auto-diagnose"
                f"{f' ({outcome.failure_class.value})' if outcome.failure_class else ''}. "
                "Here's what I saw — a human should take a look. I'm not drafting a guessed fix."
            ),
            reasons=("no known data-shape mode / no fix drafted (Invariant 4)",),
        )

    reasons: list[str] = [f"classified as {outcome.data_shape_mode}"]

    # Invariant 5: irreversible / unknown reversibility -> never auto-execute.
    if proposal.reversibility != Reversibility.REVERSIBLE:
        reasons.append(f"reversibility={proposal.reversibility.value} -> approval required (Invariant 5)")
        return GateResult(
            decision=GateDecision.AWAIT_APPROVAL,
            buttons=("Accept", "Decline"),
            message=_first_time_message(outcome, proposal),
            reasons=tuple(reasons),
        )

    # Invariant 6: auto-execute only if ALL hold.
    checks = {
        "has_compensating_action (Undo exists)": proposal.has_compensating_action,
        f"approved_count>={AUTO_EXEC_MIN_APPROVALS}":
            bool(history and history.approved_count >= AUTO_EXEC_MIN_APPROVALS),
        f"confidence>={AUTO_EXEC_MIN_CONFIDENCE}": proposal.confidence >= AUTO_EXEC_MIN_CONFIDENCE,
        "last application verified ok": bool(history and history.last_verified_ok),
        "circuit breaker CLOSED": breaker == CircuitBreakerStatus.CLOSED,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        reasons.append("auto-exec blocked: " + "; ".join(failed))
        # Invariant 12: breaker OPEN specifically forces approval.
        return GateResult(
            decision=GateDecision.AWAIT_APPROVAL,
            buttons=("Accept", "Decline"),
            message=_first_time_message(outcome, proposal),
            reasons=tuple(reasons),
        )

    # All gates pass -> auto-execute. Invariant 7: Undo, not Accept.
    reasons.append("all auto-exec gates passed (Invariant 6): reversible, seen-before, confident, breaker closed")
    return GateResult(
        decision=GateDecision.AUTO_EXECUTE,
        buttons=("Undo Fix",),
        message=(
            f"I saw this before and handled it: {proposal.diagnosis} "
            "The fix is applied and I've confirmed it cleared. If this wasn't right, hit Undo Fix."
        ),
        reasons=tuple(reasons),
    )


def _first_time_message(outcome: ExecutionOutcome, proposal: RemediationProposal) -> str:
    return (
        f"I tried to complete the job and it failed ({outcome.data_shape_mode}). "
        f"Here's what's wrong and my suggested fix: {proposal.diagnosis} "
        "Want me to apply it? — Accept / Decline."
    )
