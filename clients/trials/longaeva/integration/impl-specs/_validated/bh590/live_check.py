"""Live end-to-end check: run the CORRECTED introspection against real LONGAEVA_POC.

Uses the `snow` CLI as the query executor (stand-in for SnowflakeConnection.execute_query)
so we exercise the actual list_tables/list_stages/list_semantic_views code paths — including
the SHOW PRIMARY KEYS merge — against the real bank sandbox. This is the test that caught
the KEY_COLUMN_USAGE bug; it proves the fix end to end.
"""

import json
import subprocess
import sys

from introspection import SnowflakeIntrospectionMixin


def snow_query(sql: str) -> list[dict]:
    """Execute SQL via the snow CLI, return rows as dicts (JSON format)."""
    proc = subprocess.run(
        ["snow", "sql", "-c", "brighthive", "-q", sql, "--format", "json"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"snow query failed:\n{proc.stderr or proc.stdout}")
    out = proc.stdout.strip()
    return json.loads(out) if out else []


class LiveSnowflake(SnowflakeIntrospectionMixin):
    """SnowflakeConnection stand-in backed by the real snow CLI."""

    def __init__(self):
        self.connection_params = {"database": "LONGAEVA_POC"}

    def execute_query(self, query: str) -> list[dict]:
        return snow_query(query)


def main() -> int:
    conn = LiveSnowflake()
    failures: list[str] = []

    def check(label, got, want):
        ok = got == want
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got!r}, want {want!r}")
        if not ok:
            failures.append(label)

    print("LIVE introspection of LONGAEVA_POC (corrected BH-590 code):\n")

    # --- list_tables, whole DB ---
    all_tables = conn.list_tables()
    schemas = sorted({t.schema for t in all_tables})
    print(f"• list_tables() → {len(all_tables)} user tables across schemas {schemas}")
    check("system schemas excluded", "INFORMATION_SCHEMA" not in schemas, True)
    check("PUBLIC excluded", "PUBLIC" not in schemas, True)

    # --- SILVER scope ---
    silver = conn.list_tables(schema="SILVER")
    print(f"• list_tables(schema=SILVER) → {len(silver)} tables: {sorted(t.name for t in silver)}")

    # --- PK detection: the original failure mode ---
    spx = next((t for t in silver if t.name == "STG_SECURITY_PRICES"), None)
    if spx:
        pk_cols = sorted(c.name for c in spx.columns if c.is_primary_key)
        print(f"• STG_SECURITY_PRICES PK columns → {pk_cols}")
        check("STG_SECURITY_PRICES has PKs (SHOW PRIMARY KEYS works)", len(pk_cols) > 0, True)
    else:
        failures.append("STG_SECURITY_PRICES not found")

    holdings = next((t for t in silver if t.name == "INT_ENRICHED_HOLDINGS"), None)
    if holdings:
        pk_cols = [c.name for c in holdings.columns if c.is_primary_key]
        print(f"• INT_ENRICHED_HOLDINGS PK columns → {pk_cols} (expected none — it's a dbt CTAS)")
        check("INT_ENRICHED_HOLDINGS has no PK (matches live reality)", pk_cols, [])

    # --- stages ---
    stages = conn.list_stages()
    print(f"• list_stages() → {len(stages)}: {[(s.schema, s.name, s.stage_type) for s in stages]}")
    check("2 stages found", len(stages), 2)

    # --- semantic views ---
    svs = conn.list_semantic_views()
    print(f"• list_semantic_views() → {len(svs)}: {sorted(s.name for s in svs)}")
    check("SV_DAILY_PORTFOLIO_EXPOSURE present",
          any(s.name == "SV_DAILY_PORTFOLIO_EXPOSURE" for s in svs), True)

    print()
    if failures:
        print(f"RESULT: {len(failures)} live check(s) FAILED: {failures}")
        return 1
    print("RESULT: all live checks PASSED ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
