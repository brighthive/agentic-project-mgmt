"""Strip Longaeva SDK extensions from a semantic-view YAML and emit Snowflake DDL.

Mirrors Longaeva's deploy pipeline: the YAML is the canonical artifact; SDK fields
under `sdk_extensions:` are stripped before the `CREATE SEMANTIC VIEW` system call.

Usage:
    python strip_and_emit.py sv_daily_portfolio_exposure.yaml --emit-ddl
    python strip_and_emit.py sv_daily_portfolio_exposure.yaml --emit-ddl --apply

`--emit-ddl`  Print the generated CREATE SEMANTIC VIEW DDL to stdout.
`--apply`     Pipe the DDL to `snow sql` and execute it (requires `snow` on PATH).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


# Snowflake-native semantic-view clauses, in the order Snowflake's grammar expects:
# TABLES -> RELATIONSHIPS -> FACTS -> DIMENSIONS -> METRICS.
CLAUSE_ORDER = ("tables", "relationships", "facts", "dimensions", "metrics")


def load_spec(yaml_path: Path) -> dict:
    """Load YAML and return only the Snowflake-native `spec:` section."""
    with yaml_path.open() as fh:
        doc = yaml.safe_load(fh)
    if "spec" not in doc:
        raise ValueError(
            f"{yaml_path}: missing top-level `spec:` key. "
            "Has the YAML been migrated to the strip-boundary format?"
        )
    if "sdk_extensions" not in doc:
        print(
            f"warn: {yaml_path} has no `sdk_extensions:` block — nothing to strip.",
            file=sys.stderr,
        )
    return doc["spec"]


def _resolve_qualifier(expr: str, rel_alias_map: dict[str, str]) -> tuple[str, str]:
    """Split `expr` into (table_alias, column).

    - `rel_geo.region`  -> ("geo", "region")     via rel_alias_map
    - `portfolio_id`    -> ("exposure", "portfolio_id")  (bare column on base)
    """
    if "." in expr:
        rel_name, col = expr.split(".", 1)
        return rel_alias_map.get(rel_name, rel_name), col
    return "exposure", expr


def render_dimensions(rows: list[dict], rel_alias_map: dict[str, str]) -> str:
    """Snowflake syntax: `<table_alias>.<dim_alias> AS <column>`.

    Alias goes LEFT, the underlying column goes RIGHT (opposite of standard SQL).
    """
    lines = []
    for row in rows:
        alias = row["name"]
        table, col = _resolve_qualifier(row["expr"], rel_alias_map)
        lines.append(f"    {table}.{alias} AS {col}")
    return ",\n".join(lines)


def render_facts(rows: list[dict]) -> str:
    """Facts are always on the base table."""
    return ",\n".join(
        f"    exposure.{row['name']} AS {row['expr']}" for row in rows
    )


_AGG_RE = __import__("re").compile(
    r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(\s*(DISTINCT\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\)",
    flags=__import__("re").IGNORECASE,
)


def _qualify_metric_expr(expr: str, fact_names: set[str]) -> str:
    """Rewrite SUM(col) -> SUM(exposure.col) when col is a bare fact name."""

    def repl(match):
        agg, distinct, col = match.group(1), match.group(2) or "", match.group(3)
        qualified = f"exposure.{col}" if col in fact_names else col
        return f"{agg}({distinct}{qualified})"

    return _AGG_RE.sub(repl, expr)


def render_metrics(rows: list[dict], fact_names: set[str]) -> str:
    """Metrics live on `exposure` namespace; bare fact refs get qualified."""
    return ",\n".join(
        f"    exposure.{row['name']} AS {_qualify_metric_expr(row['expr'], fact_names)}"
        for row in rows
    )


def emit_ddl(spec: dict) -> str:
    """Render the Snowflake CREATE SEMANTIC VIEW DDL from the stripped spec."""
    base_table = spec["base_table"]
    pk = "as_of_date, portfolio_id, instrument_id"  # MVP: hardcoded for sv_daily_portfolio_exposure

    relationships_lines = []
    table_decls = [
        f"    exposure AS {base_table}\n        PRIMARY KEY ({pk})",
    ]

    rel_alias_map = {}
    for rel in spec.get("relationships", []):
        target_full = rel["join"]["target"]
        target_table, target_col = target_full.rsplit(".", 1)
        rel_alias = rel["name"].replace("rel_", "")  # rel_issuer -> issuer
        rel_alias_map[rel["name"]] = rel_alias
        table_decls.append(
            f"    {rel_alias} AS {target_table}\n"
            f"        PRIMARY KEY ({target_col})"
        )
        base_col = rel["join"]["base"]
        relationships_lines.append(
            f"    exposure ({base_col}) REFERENCES {rel_alias}"
        )

    parts = [
        f"USE ROLE LONGAEVA_POC_ROLE;",
        f"USE DATABASE LONGAEVA_POC;",
        f"USE SCHEMA SEMANTIC;",
        "",
        f"CREATE OR REPLACE SEMANTIC VIEW {spec['name']}",
        "  TABLES (",
        ",\n".join(table_decls),
        "  )",
    ]

    if relationships_lines:
        parts += [
            "  RELATIONSHIPS (",
            ",\n".join(relationships_lines),
            "  )",
        ]

    if "facts" in spec:
        parts += [
            "  FACTS (",
            render_facts(spec["facts"]),
            "  )",
        ]

    dims = list(spec.get("dimensions", [])) + list(spec.get("time_dimensions", []))
    if dims:
        parts += [
            "  DIMENSIONS (",
            render_dimensions(dims, rel_alias_map),
            "  )",
        ]

    if "metrics" in spec:
        fact_names = {row["name"] for row in spec.get("facts", [])} | {
            row["expr"] for row in spec.get("facts", []) if "." not in row["expr"]
        } | {
            "internal_issuer_id",  # COUNT DISTINCT on dim columns
            "instrument_id",
        }
        parts += [
            "  METRICS (",
            render_metrics(spec["metrics"], fact_names),
            "  )",
        ]

    description = spec.get("description", "").strip()
    if description:
        single_line = " ".join(description.split())
        parts.append(f"  COMMENT = '{single_line.replace(chr(39), chr(39)*2)}'")

    return "\n".join(parts) + ";\n"


def apply_ddl(ddl: str, connection: str = "brighthive") -> int:
    """Pipe DDL to `snow sql`; return its exit code."""
    if not shutil.which("snow"):
        print("error: `snow` CLI not on PATH", file=sys.stderr)
        return 127
    proc = subprocess.run(
        ["snow", "sql", "-c", connection, "--stdin"],
        input=ddl,
        text=True,
    )
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_path", type=Path, help="Path to extended-spec YAML")
    parser.add_argument(
        "--emit-ddl", action="store_true", help="Print generated DDL to stdout"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Run the DDL via `snow sql`"
    )
    parser.add_argument(
        "--connection", default="brighthive", help="snow CLI connection name"
    )
    args = parser.parse_args()

    spec = load_spec(args.yaml_path)
    ddl = emit_ddl(spec)

    if args.emit_ddl or not args.apply:
        print(ddl)

    if args.apply:
        return apply_ddl(ddl, connection=args.connection)
    return 0


if __name__ == "__main__":
    sys.exit(main())
