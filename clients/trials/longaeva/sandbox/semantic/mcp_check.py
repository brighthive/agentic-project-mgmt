"""MCP queryability check — simulates Longaeva's MCP feedback loop (POC use case 3).

Their internal MCP server exposes the semantic view to analysts + agents. This
harness stands in for that downstream validation:

  1. Surface check  — every dimension, time-dimension, and metric in the YAML
                       is actually queryable via SEMANTIC_VIEW(...)
  2. Representative  — run filtered / aggregated / multi-dimension-slice queries
     queries           and confirm they return sane (non-error, non-empty) results
  3. Gap detection  — flag quality gaps that degrade agent answers:
                       missing dimension sample values, absent query examples,
                       missing plain-language instructions

Output is a structured report; exit 0 if no ERROR-level gaps.

Run:
  uv run --with pyyaml --with snowflake-connector-python python mcp_check.py \\
    sv_daily_portfolio_exposure.yaml [--connection brighthive]
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

import yaml
import snowflake.connector

VIEW_FQN = "LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure"


def connect(connection: str):
    cfg_path = Path.home() / ".snowflake" / "config.toml"
    with cfg_path.open("rb") as f:
        c = tomllib.load(f)["connections"][connection]
    return snowflake.connector.connect(
        account=c["account"], user=c["user"], password=c["password"],
        role=c.get("role"), warehouse=c.get("warehouse"),
        database=c.get("database"), schema="SEMANTIC",
    )


def query_dim_metric(conn, dim: str, metric: str, where: str | None = None) -> tuple[bool, int, str]:
    """Run SEMANTIC_VIEW(view DIMENSIONS dim METRICS metric [WHERE ...])."""
    sql = f"SELECT * FROM SEMANTIC_VIEW({VIEW_FQN} DIMENSIONS {dim} METRICS {metric}"
    if where:
        sql += f" WHERE {where}"
    sql += ") LIMIT 100"
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return True, len(rows), ""
    except Exception as exc:  # noqa: BLE001
        return False, 0, str(exc).splitlines()[0]


def query_metric_only(conn, metric: str) -> tuple[bool, str]:
    sql = f"SELECT * FROM SEMANTIC_VIEW({VIEW_FQN} METRICS {metric})"
    try:
        conn.cursor().execute(sql)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, str(exc).splitlines()[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("yaml_path", type=Path)
    ap.add_argument("--connection", default="brighthive")
    args = ap.parse_args()

    with args.yaml_path.open() as fh:
        doc = yaml.safe_load(fh)
    spec = doc["spec"]
    sdk = doc.get("sdk_extensions", {})

    conn = connect(args.connection)

    dims = [d["name"] for d in spec.get("dimensions", [])]
    tdims = [d["name"] for d in spec.get("time_dimensions", [])]
    metrics = [m["name"] for m in spec.get("metrics", [])]
    anchor_metric = metrics[0]

    errors, warnings = [], []

    # ---- 1. Surface check -----------------------------------------------------
    print("==> 1. Surface check: every dimension + metric queryable")
    for dim in dims + tdims:
        ok, n, err = query_dim_metric(conn, dim, anchor_metric)
        mark = "✅" if ok else "❌"
        print(f"   {mark} DIM {dim}: {n} rows" + (f" — {err}" if err else ""))
        if not ok:
            errors.append(f"dimension {dim} not queryable: {err}")

    for metric in metrics:
        ok, err = query_metric_only(conn, metric)
        mark = "✅" if ok else "❌"
        print(f"   {mark} METRIC {metric}" + (f" — {err}" if err else ""))
        if not ok:
            errors.append(f"metric {metric} not queryable: {err}")

    # ---- 2. Representative queries --------------------------------------------
    print("\n==> 2. Representative query suite")
    # filtered
    ok, n, err = query_dim_metric(conn, "region", anchor_metric, "region = 'APAC'")
    print(f"   {'✅' if ok and n > 0 else '❌'} filtered (region='APAC'): {n} rows")
    if not ok or n == 0:
        errors.append(f"filtered query failed/empty: {err}")
    # aggregated multi-metric
    ok, n, err = query_dim_metric(conn, "sector_code",
                                  "total_exposure_usd, position_count_distinct_issuers")
    print(f"   {'✅' if ok and n > 0 else '❌'} aggregated (by sector, 2 metrics): {n} rows")
    if not ok or n == 0:
        errors.append(f"aggregated query failed/empty: {err}")
    # multi-dimension slice
    ok, n, err = query_dim_metric(conn, "region, fiscal_year, fiscal_quarter",
                                  anchor_metric, "region = 'EMEA'")
    print(f"   {'✅' if ok and n > 0 else '❌'} multi-dim slice (region+fiscal): {n} rows")
    if not ok or n == 0:
        errors.append(f"multi-dim query failed/empty: {err}")

    # ---- 3. Gap detection (agent answer quality) ------------------------------
    print("\n==> 3. Gap detection (degrades agent answer quality)")

    if not sdk.get("agent_instructions"):
        warnings.append("missing agent_instructions — agents lack plain-language guidance")
    else:
        print("   ✅ agent_instructions present")

    examples = sdk.get("verified_query_examples", [])
    if len(examples) < 3:
        warnings.append(f"only {len(examples)} verified_query_examples (recommend >= 3)")
    else:
        print(f"   ✅ {len(examples)} verified_query_examples")

    # Dimensions lacking sample values: check distinct count is small enough to
    # enumerate but no sample provided. We surface high-value categorical dims.
    sample_gaps = []
    for dim in ["region", "sector_code", "asset_class_code"]:
        ok, n, err = query_dim_metric(conn, dim, anchor_metric)
        if ok and n > 0:
            # categorical dim is queryable; flag if no description hints values
            d = next((x for x in spec["dimensions"] if x["name"] == dim), None)
            if d and "description" in d and any(
                tok in d["description"] for tok in ("/", "AMERICAS", "EQUITY")
            ):
                print(f"   ✅ {dim}: sample values implied in description")
            else:
                sample_gaps.append(dim)
    for dim in sample_gaps:
        warnings.append(f"dimension {dim} has no sample values for agent grounding")

    # metric_store registration coverage
    registered = set(sdk.get("metric_store", {}).get("register", []))
    unregistered = [m for m in metrics if m not in registered]
    if unregistered:
        warnings.append(f"metrics not registered in metric_store: {unregistered}")
    else:
        print("   ✅ all metrics registered in metric_store")

    conn.close()

    # ---- Report ---------------------------------------------------------------
    print(f"\n{'='*55}")
    print(f"MCP queryability: {len(errors)} errors, {len(warnings)} warnings")
    for e in errors:
        print(f"   ❌ {e}")
    for w in warnings:
        print(f"   ⚠️  {w}")
    print("=" * 55)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
