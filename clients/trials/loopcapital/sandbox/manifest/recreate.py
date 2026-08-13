#!/usr/bin/env python3
"""Rebuild the whole local sandbox from the committed manifest, from git alone (BH-1405).

Manifest-mode orchestrator: boots the SQL Server container, waits for it to be healthy, then
applies the manifest's schema and deterministic synthetic rows via `synthesize.py`. Same
manifest + same `--seed` -> byte-identical database (INV-10). No staging access, no real rows,
no credentials — the container's `MSSQL_SA_PASSWORD` is a throwaway held only in the shell.

This owns CONTAINER lifecycle for manifest mode the way `setup.sh` does for scenario mode; the
schema+seed work is delegated to `synthesize.py` so there is one synthesis mechanism, not two.

Usage (from repo root, via `make sandbox-recreate`):
    export MSSQL_SA_PASSWORD='<throwaway-local-password>'
    uv run --with pymssql --with pydantic python \\
        clients/trials/loopcapital/sandbox/manifest/recreate.py --rows 200 --seed 42
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

from manifest_model import load_manifest
from synthesize import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_ROWS,
    DEFAULT_SEED,
    MANIFEST_PATH,
    apply_schema_and_seed,
    recreate_database,
)

SANDBOX_DIR: Final[Path] = Path(__file__).resolve().parent.parent
CONTAINER_NAME: Final[str] = "loopcapital-sql-sandbox"
HEALTH_TIMEOUT_S: Final[int] = 120
HEALTH_POLL_S: Final[int] = 2


def compose_up() -> None:
    """Start the sandbox container (idempotent — no-op if already running)."""
    print(f"Starting {CONTAINER_NAME} (docker compose up -d)...")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=SANDBOX_DIR, check=True)


def wait_healthy(*, timeout_s: int = HEALTH_TIMEOUT_S) -> None:
    """Block until the container's Docker healthcheck reports healthy, or fail loudly."""
    print(f"Waiting for {CONTAINER_NAME} healthcheck (timeout {timeout_s}s)...")
    elapsed = 0
    while elapsed < timeout_s:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", CONTAINER_NAME],
            capture_output=True, text=True,
        )
        if result.stdout.strip() == "healthy":
            print("  SQL Server is healthy.")
            return
        time.sleep(HEALTH_POLL_S)
        elapsed += HEALTH_POLL_S
    raise RuntimeError(
        f"{CONTAINER_NAME} did not become healthy within {timeout_s}s — "
        f"check `docker logs {CONTAINER_NAME}` (common causes: weak MSSQL_SA_PASSWORD, port 1433 in use)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS, help=f"rows per table (default: {DEFAULT_ROWS})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"RNG seed (default: {DEFAULT_SEED})")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="path to schema_manifest.json")
    parser.add_argument("--skip-boot", action="store_true", help="assume the container is already running")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running recreate.py", file=sys.stderr)
        return 1

    if not args.manifest.exists():
        print(f"manifest not found: {args.manifest} — run `make capture-loopcapital` or introspect_local first", file=sys.stderr)
        return 1

    host = os.environ.get("MSSQL_HOST", DEFAULT_HOST)
    port = int(os.environ.get("MSSQL_PORT", str(DEFAULT_PORT)))

    if not args.skip_boot:
        compose_up()
        wait_healthy()

    manifest = load_manifest(path=args.manifest)
    print(f"Recreating {manifest.database} from {args.manifest.name} "
          f"({len(manifest.tables)} tables, source={manifest.source.value}, rows={args.rows}, seed={args.seed})...")

    recreate_database(host=host, port=port, password=password, database=manifest.database)
    total = apply_schema_and_seed(
        host=host, port=port, password=password, manifest=manifest, rows=args.rows, seed=args.seed
    )
    print(f"\nRecreate complete — {len(manifest.tables)} tables, {total} synthetic rows, from git alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
