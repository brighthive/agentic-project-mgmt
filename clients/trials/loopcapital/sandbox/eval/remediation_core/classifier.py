"""Recall-improved data-shape classifier (PROTOTYPE).

Mirrors the shipped classifier
(brightbot/agents/governance_agent/tools/root_cause_classifier.py) exactly in
structure and intent — pure regex, "first match wins", abstains on no match
(Invariant 4). Adds the 4 patterns the Layer 0 eval exposed as recall gaps,
WITHOUT weakening the 3 CodeRabbit guardrails that kept precision at 1.00.

This is a prototype living in the POC eval package so we can prove NO-GO->GO
before touching the brightbot repo (which is a real PR gated on greenlight).
The additions below are the exact diff intended for that PR.

New patterns (each traces to a Layer 0 failure in LAYER0_RESULT.md):
  schema_drift      + "unrecognized name"          (BigQuery phrasing)
  missing_partition + "got .* result.* expected 0" (dbt custom-test phrasing)
  missing_partition + "freshness .* (old|stale)" / "loaded_at .* old"
  broken_stage      + "parse .* as csv" / "file format .* (json|csv|parquet)"
                       (COPY INTO format-mismatch — the failure_modes.py scenario)
"""

from __future__ import annotations

import re
from typing import Literal

DataShapeMode = Literal["schema_drift", "missing_partition", "broken_stage", "dbt_contract"]

# Ordered, most-specific-first. Guardrail patterns (co-occurrence requirements)
# are preserved verbatim from the shipped classifier; NEW patterns are marked.
_MODE_PATTERNS: list[tuple[DataShapeMode, tuple[str, ...]]] = [
    (
        "dbt_contract",
        (
            "contract enforcement failed",
            "data type mismatch",
            "column type mismatch",
            "contract.*(enforce|violat)",  # guardrail: 'contract' must co-occur w/ enforce|violat
        ),
    ),
    (
        "schema_drift",
        (
            "invalid identifier",
            "column .* does not exist",
            "unrecognized column",
            "unrecognized name",                 # NEW: BigQuery phrasing (Layer 0 miss #1)
            "does not have a column named",
            "compilation error.*(column|identifier)",  # guardrail: compile err must name a column/identifier
        ),
    ),
    (
        "missing_partition",
        (
            "no data found",
            "partition not found",
            "no such partition",
            "table .* is empty",
            # NEW (Layer 0 miss #2): dbt custom-test "got N result(s), expected 0".
            # Guarded to the business-day/partition test shape by requiring the
            # 'expected 0' assertion phrasing, not any 'got/expected' text.
            r"got \d+ result.*expected 0",
            # NEW (Layer 0 miss #3): source-freshness detection of a missing day.
            "freshness.*(old|stale|fail)",
            "loaded_at.*old",
        ),
    ),
    (
        "broken_stage",
        (
            "stage .* does not exist",
            "external stage",
            "failed to load (stage|file|from)",  # guardrail: 'failed to load' must name stage|file|from
            "file not found",
            "s3 bucket",
            # NEW (Layer 0 miss #4): COPY INTO format mismatch — the failure_modes.py
            # broken_stage scenario (CSV data, JSON stage format). Guarded to
            # parse/format-mismatch phrasing so it does not swallow generic parse errors.
            "(parse|read).*as csv",
            "file format.*(json|csv|parquet|avro)",
        ),
    ),
]


def classify_data_shape_mode(error_message: str | None) -> DataShapeMode | None:
    """Pattern-match a dbt/warehouse error into one of 4 DATA_SHAPE modes, else None.

    None == "cannot auto-diagnose" (Invariant 4) — never a default mode.
    """
    if not error_message:
        return None
    text = error_message.lower()
    for mode, patterns in _MODE_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, text):
                return mode
    return None
