"""BH-596 validator tests — unit (fake executor) + live (snow CLI) proof.

The live tests carry @pytest.mark.live and hit LONGAEVA_POC; they prove the
validator both PASSES a correct verified_query and CATCHES the table-qualification
bug (EXPOSURE.region) that only a live run surfaces.
"""

from __future__ import annotations

import pytest

from verified_query_validator import (
    make_snow_executor,
    validate_verified_queries,
)

_SV = "LONGAEVA_POC.SEMANTIC.SV_DAILY_PORTFOLIO_EXPOSURE"

_GOOD_SQL = f"""
SELECT * FROM SEMANTIC_VIEW(
  {_SV}
  DIMENSIONS EXPOSURE.asset_class_code, EXPOSURE.as_of_date
  METRICS EXPOSURE.total_exposure_usd
) LIMIT 5
"""

# region lives on the joined rel_geo table, NOT EXPOSURE → invalid identifier
_BAD_SQL = f"""
SELECT * FROM SEMANTIC_VIEW(
  {_SV}
  DIMENSIONS EXPOSURE.region
  METRICS EXPOSURE.total_exposure_usd
) LIMIT 5
"""


# ── Unit: fake executor, deterministic ──────────────────────────────


def test_all_pass_when_executor_returns_rows():
    doc = {"verified_queries": [{"name": "q1", "sql": "SELECT 1"}]}
    report = validate_verified_queries(document=doc, executor=lambda sql: [{"x": 1}])
    assert report.all_passed
    assert report.results[0].row_count == 1


def test_compilation_error_fails_the_gate():
    def boom(sql):
        raise RuntimeError("invalid identifier 'EXPOSURE.REGION'")

    doc = {"verified_queries": [{"name": "bad", "sql": "SELECT bad"}]}
    report = validate_verified_queries(document=doc, executor=boom)
    assert not report.all_passed
    assert "invalid identifier" in report.results[0].error


def test_empty_sql_fails():
    doc = {"verified_queries": [{"name": "empty", "sql": "  "}]}
    report = validate_verified_queries(document=doc, executor=lambda sql: [])
    assert not report.all_passed
    assert report.results[0].error == "empty sql"


def test_no_queries_is_not_a_pass():
    report = validate_verified_queries(document={"verified_queries": []},
                                       executor=lambda sql: [])
    assert not report.all_passed  # nothing to prove ≠ proven


def test_mixed_results_summary():
    doc = {"verified_queries": [
        {"name": "ok", "sql": "SELECT 1"},
        {"name": "bad", "sql": "SELECT 2"},
    ]}

    def selective(sql):
        if "2" in sql:
            raise RuntimeError("invalid identifier")
        return [{"x": 1}]

    report = validate_verified_queries(document=doc, executor=selective)
    assert report.summary == "1/2 verified_queries round-trip"


# ── Live: real Snowflake (proves the gate catches the real bug) ──────


@pytest.mark.live
def test_live_good_query_passes():
    doc = {"verified_queries": [{"name": "good", "sql": _GOOD_SQL}]}
    report = validate_verified_queries(document=doc, executor=make_snow_executor())
    assert report.all_passed, report.results[0].error
    assert report.results[0].row_count and report.results[0].row_count > 0


@pytest.mark.live
def test_live_bad_query_is_caught():
    doc = {"verified_queries": [{"name": "bad_region", "sql": _BAD_SQL}]}
    report = validate_verified_queries(document=doc, executor=make_snow_executor())
    assert not report.all_passed
    assert "invalid identifier" in (report.results[0].error or "").lower()
