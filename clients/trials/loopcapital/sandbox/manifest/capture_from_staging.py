#!/usr/bin/env python3
"""Capture the sandbox schema shape READ-ONLY from staging platform-core (BH-1404, production path).

Runs a single authenticated GraphQL query against `api.staging.brighthive.net` for one workspace's
data assets, then maps each asset's `fields` into a faithful `schema_manifest.json` (source=staging).
This is how the committed shape stays current with what the platform actually catalogued for Frank's
on-prem SQL Server stack — the assets land in the catalog via an OpenMetadata scan of the
Brighthive-owned stand-in, never by touching Loop Capital's real server (INV-11).

Guarantees baked in:
  * READ-ONLY — one GraphQL *query*, no mutation.
  * The bearer token is read from `$BH_API_TOKEN` and NEVER written to disk (INV-8). SSO separately
    (the token is minted by a normal staging login) and export it before running.
  * No real Loop Capital rows are ever produced (INV-9) — this captures shape only: table + column
    types. Row synthesis happens later, deterministically, in `synthesize.py`.

The staging catalog carries OpenMetadata-style *logical* column types (INT / DECIMAL / VARCHAR ...),
not the physical SQL Server DDL, so the emitted types are a documented approximation. For the
byte-faithful shape used by the round-trip smoke test, use `introspect_local.py` instead.

Usage (from repo root, via `make capture-loopcapital`):
    export BH_API_TOKEN='<staging bearer token from an SSO login>'
    uv run --with pymssql --with pydantic python \\
        clients/trials/loopcapital/sandbox/manifest/capture_from_staging.py \\
        --workspace-id <staging-loopcapital-workspace-uuid>
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Final

from manifest_model import (
    SANDBOX_DATABASE,
    CaptureSource,
    ColumnSpec,
    KeyRole,
    SchemaManifest,
    TableSpec,
    dump_manifest,
)

MANIFEST_PATH: Final[Path] = Path(__file__).resolve().parent.parent / "schema_manifest.json"
RAW_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "_raw"  # gitignored debug dumps

STAGING_API_URL: Final[str] = "https://api.staging.brighthive.net/graphql"
TOKEN_ENV: Final[str] = "BH_API_TOKEN"
API_URL_ENV: Final[str] = "BH_API_URL"
WORKSPACE_ENV: Final[str] = "BH_WORKSPACE_ID"
HTTP_TIMEOUT_S: Final[int] = 60
DEFAULT_SCHEMA: Final[str] = "dbo"

# Workspace-scoped, READ-ONLY. Column shape comes from `fields`; row data is never requested.
CAPTURE_QUERY: Final[str] = """
query CaptureLoopCapitalShape($input: WorkspaceInput!) {
  workspace(input: $input) {
    id
    name
    dataAssets {
      resultCount
      dataAssets {
        id
        name
        tableName
        tableFQN
        source
        connectionType
        assetType
        fields {
          name
          dataType
        }
      }
    }
  }
}
""".strip()

# OpenMetadata-style logical DataType (staging catalog) -> SQL Server physical type for the sandbox.
# A documented approximation: lengths/precision aren't in the catalog, so sane defaults are chosen.
_DATATYPE_TO_SQLSERVER: Final[dict[str, str]] = {
    "TINYINT": "TINYINT",
    "SMALLINT": "SMALLINT",
    "INT": "INT",
    "BIGINT": "BIGINT",
    "BYTEINT": "TINYINT",
    "NUMBER": "DECIMAL(18,4)",
    "DECIMAL": "DECIMAL(18,4)",
    "NUMERIC": "DECIMAL(18,4)",
    "FLOAT": "FLOAT",
    "DOUBLE": "FLOAT",
    "TIMESTAMP": "DATETIME2",
    "DATETIME": "DATETIME2",
    "TIME": "TIME",
    "DATE": "DATE",
    "INTERVAL": "VARCHAR(64)",
    "STRING": "VARCHAR(255)",
    "TEXT": "VARCHAR(MAX)",
    "MEDIUMTEXT": "VARCHAR(MAX)",
    "CHAR": "CHAR(10)",
    "VARCHAR": "VARCHAR(255)",
    "BOOLEAN": "BIT",
    "BINARY": "VARBINARY(MAX)",
    "VARBINARY": "VARBINARY(MAX)",
    "BYTES": "VARBINARY(MAX)",
    "BLOB": "VARBINARY(MAX)",
    "LONGBLOB": "VARBINARY(MAX)",
    "MEDIUMBLOB": "VARBINARY(MAX)",
    "ARRAY": "VARCHAR(MAX)",
    "MAP": "VARCHAR(MAX)",
}
_FALLBACK_SQLSERVER_TYPE: Final[str] = "VARCHAR(255)"


def to_sqlserver_type(*, data_type: str) -> str:
    """Map a staging OpenMetadata logical `DataType` to a SQL Server physical type (documented default)."""
    return _DATATYPE_TO_SQLSERVER.get(data_type.upper(), _FALLBACK_SQLSERVER_TYPE)


def qualified_table_name(*, asset: dict) -> str:
    """Best schema-qualified `schema.table` for an asset, from tableName / tableFQN / name."""
    raw = asset.get("tableName") or asset.get("tableFQN") or asset.get("name") or "unknown_table"
    parts = [p for p in str(raw).split(".") if p]
    if len(parts) >= 2:
        return f"{parts[-2]}.{parts[-1]}"  # last two segments: schema.table (drops service/db prefix)
    return f"{DEFAULT_SCHEMA}.{parts[-1]}" if parts else f"{DEFAULT_SCHEMA}.unknown_table"


def run_query(*, api_url: str, token: str, workspace_id: str) -> dict:
    """POST the READ-ONLY capture query with a bearer token; return the parsed JSON body."""
    payload = json.dumps(
        {"query": CAPTURE_QUERY, "variables": {"input": {"workspaceId": workspace_id}}}
    ).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("errors"):
        raise RuntimeError(f"GraphQL errors from {api_url}: {json.dumps(body['errors'])}")
    return body


def build_manifest(*, workspace: dict, captured_at: str) -> SchemaManifest:
    """Map a workspace's data assets into a shape-only manifest (source=staging, no rows)."""
    assets = (workspace.get("dataAssets") or {}).get("dataAssets") or []
    tables: list[TableSpec] = []
    for asset in assets:
        fields = asset.get("fields") or []
        if not fields:
            continue  # a shape sandbox needs typed columns; skip assets the catalog has no fields for
        columns = [
            ColumnSpec(
                name=field["name"],
                sql_type=to_sqlserver_type(data_type=field["dataType"]),
                nullable=True,  # staging catalog does not expose nullability — permissive default
                key=KeyRole.NONE,  # nor keys; introspect_local recovers PKs from the real backend
            )
            for field in fields
        ]
        tables.append(TableSpec(name=qualified_table_name(asset=asset), columns=columns, row_estimate=0))

    tables.sort(key=lambda table: table.name)  # diff-stable ordering
    return SchemaManifest(
        captured_at=captured_at,
        source=CaptureSource.STAGING,
        database=SANDBOX_DATABASE,
        tables=tables,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace-id", default=os.environ.get(WORKSPACE_ENV), help=f"staging workspace UUID (or ${WORKSPACE_ENV})")
    parser.add_argument("--out", type=Path, default=MANIFEST_PATH, help="output manifest path")
    parser.add_argument("--api-url", default=os.environ.get(API_URL_ENV, STAGING_API_URL), help=f"GraphQL endpoint (or ${API_URL_ENV})")
    args = parser.parse_args()

    token = os.environ.get(TOKEN_ENV)
    if not token:
        print(f"export {TOKEN_ENV} (a staging bearer token from an SSO login) before running", file=sys.stderr)
        return 1
    if not args.workspace_id:
        print(f"--workspace-id is required (or set ${WORKSPACE_ENV})", file=sys.stderr)
        return 1

    captured_at = datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    print(f"Capturing workspace {args.workspace_id} shape from {args.api_url} (READ-ONLY)...")
    body = run_query(api_url=args.api_url, token=token, workspace_id=args.workspace_id)

    workspace = (body.get("data") or {}).get("workspace")
    if not workspace:
        print(f"no workspace returned for {args.workspace_id} — check the id and the token's access", file=sys.stderr)
        return 1

    # Raw dump for debugging only — gitignored, and the token is NEVER part of the response body.
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"capture_{args.workspace_id}.json"
    raw_path.write_text(json.dumps(body, indent=2) + "\n")

    manifest = build_manifest(workspace=workspace, captured_at=captured_at)
    dump_manifest(manifest=manifest, path=args.out)

    total_columns = sum(len(t.columns) for t in manifest.tables)
    print(f"Captured {workspace.get('name', '?')} -> {args.out}")
    print(f"  {len(manifest.tables)} tables, {total_columns} columns, source={manifest.source.value}")
    print(f"  raw response: {raw_path} (gitignored)")
    for table in manifest.tables:
        print(f"    {table.name}: {len(table.columns)} cols")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
