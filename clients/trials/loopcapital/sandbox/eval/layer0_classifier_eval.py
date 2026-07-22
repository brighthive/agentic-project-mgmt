"""Layer 0 eval — diagnosis classification quality (offline, no cloud).

Tests the REAL, shipped classifier `classify_data_shape_mode`
(brightbot/agents/governance_agent/tools/root_cause_classifier.py) against a
labeled corpus of realistic dbt/Snowflake/warehouse error strings.

It answers the single riskiest question in the agentic-remediation strategy:
*can BrightAgent even recognize what broke, on real error text?* — and, just as
importantly, *does it correctly ABSTAIN* on failures that are NOT data-shape
issues (Invariant 4: a false-confident classification is worse than "I don't
know", because it routes a JOB_RUNTIME failure into a fix-drafting path).

Design choices (deliberate, for honesty):
- The classifier is loaded BY FILE PATH via importlib, bypassing the brightbot
  package __init__ chain — so this runs with only the Python stdlib (the
  classifier itself imports only `re` + `typing`). No langchain/boto3/Bedrock.
- Corpus strings are written to read like REAL tool output (Snowflake driver
  errors, dbt CLI failures, SQL Server / Databricks messages), NOT
  reverse-engineered to match the regexes. The point is to find recall gaps,
  not to flatter the classifier.
- `expected=None` rows are the abstention set: JOB_RUNTIME + generic failures
  the classifier MUST NOT classify. Adversarial near-misses target the three
  CodeRabbit guardrails (bare "contract" / "compilation error" / "failed to
  load").

Run:
  python layer0_classifier_eval.py
  python layer0_classifier_eval.py --brightbot /path/to/brightbot   # override repo location
  python layer0_classifier_eval.py --show-passes                    # verbose
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from corpus import CORPUS  # labeled cases live next to this file


def load_classifier(brightbot_root: Path):
    """Import classify_data_shape_mode by file path — no package import."""
    module_path = (
        brightbot_root
        / "brightbot"
        / "agents"
        / "governance_agent"
        / "tools"
        / "root_cause_classifier.py"
    )
    if not module_path.is_file():
        raise FileNotFoundError(
            f"root_cause_classifier.py not found at {module_path}. "
            f"Pass --brightbot with the correct brightbot repo root."
        )
    spec = importlib.util.spec_from_file_location("root_cause_classifier", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.classify_data_shape_mode, module_path


def default_brightbot_root() -> Path:
    # eval/ -> sandbox/ -> loopcapital/ -> trials/ -> clients/ -> agentic-project-mgmt/ -> BrightHive/
    here = Path(__file__).resolve()
    brighthive = here.parents[6]
    return brighthive / "brightbot"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--brightbot", type=Path, default=default_brightbot_root(),
                    help="Path to the brightbot repo root")
    ap.add_argument("--show-passes", action="store_true",
                    help="Print passing cases too, not just failures")
    args = ap.parse_args()

    try:
        classify, module_path = load_classifier(args.brightbot)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    print(f"Loaded classifier from: {module_path}")
    print(f"Corpus size: {len(CORPUS)} cases\n")

    # Confusion tracking
    classes = ["schema_drift", "missing_partition", "broken_stage", "dbt_contract"]
    per_class = {c: {"tp": 0, "fn": 0, "fp": 0} for c in classes}
    abstain_total = 0
    abstain_correct = 0
    known_total = 0
    known_correct = 0
    failures: list[tuple[str, object, object, str]] = []

    for case in CORPUS:
        text = case["error"]
        expected = case["expected"]  # a mode string, or None to mean "must abstain"
        note = case.get("note", "")
        got = classify(text)

        if expected is None:
            abstain_total += 1
            if got is None:
                abstain_correct += 1
                if args.show_passes:
                    print(f"  PASS  abstain            <- {text[:70]!r}")
            else:
                # false positive: classified something that should be None
                per_class[got]["fp"] += 1
                failures.append((text, expected, got, note))
        else:
            known_total += 1
            if got == expected:
                known_correct += 1
                per_class[expected]["tp"] += 1
                if args.show_passes:
                    print(f"  PASS  {expected:18s} <- {text[:70]!r}")
            else:
                per_class[expected]["fn"] += 1
                if got is not None:
                    per_class[got]["fp"] += 1
                failures.append((text, expected, got, note))

    # Report
    print("\n" + "=" * 72)
    print("FAILURES" if failures else "No failures.")
    print("=" * 72)
    for text, expected, got, note in failures:
        exp = expected if expected is not None else "ABSTAIN(None)"
        print(f"\n  expected: {exp}")
        print(f"  got:      {got}")
        print(f"  error:    {text[:120]!r}")
        if note:
            print(f"  note:     {note}")

    print("\n" + "=" * 72)
    print("PER-CLASS (precision / recall)")
    print("=" * 72)
    for c in classes:
        tp = per_class[c]["tp"]
        fn = per_class[c]["fn"]
        fp = per_class[c]["fp"]
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        rec = tp / (tp + fn) if (tp + fn) else float("nan")
        print(f"  {c:18s}  tp={tp:2d} fn={fn:2d} fp={fp:2d}   "
              f"precision={prec:.2f}  recall={rec:.2f}")

    known_acc = known_correct / known_total if known_total else float("nan")
    abstain_acc = abstain_correct / abstain_total if abstain_total else float("nan")

    print("\n" + "=" * 72)
    print("HEADLINE")
    print("=" * 72)
    print(f"  Known-mode accuracy   : {known_correct}/{known_total} = {known_acc:.1%}   (bar: >=90%)")
    print(f"  Correct-abstention    : {abstain_correct}/{abstain_total} = {abstain_acc:.1%}   (bar: >=95%)")

    known_pass = known_acc >= 0.90
    abstain_pass = abstain_acc >= 0.95
    verdict = "GO" if (known_pass and abstain_pass) else "NO-GO"
    print(f"\n  Layer 0 verdict: {verdict}")
    print(f"    known-mode bar  : {'PASS' if known_pass else 'FAIL'}")
    print(f"    abstention bar  : {'PASS' if abstain_pass else 'FAIL'}")
    print("=" * 72)

    return 0 if (known_pass and abstain_pass) else 1


if __name__ == "__main__":
    sys.exit(main())
