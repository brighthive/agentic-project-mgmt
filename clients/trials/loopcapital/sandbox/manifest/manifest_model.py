#!/usr/bin/env python3
"""Typed contract for the Loop Capital sandbox schema manifest (BH-1404/1405/1406).

The manifest is the git-only source of truth for MANIFEST MODE: `make sandbox-recreate`
rebuilds a local SQL Server purely from a committed `schema_manifest.json` plus a deterministic
synthetic seed — zero staging access, no real rows, no credentials. It is captured READ-ONLY
either from the staging platform (`capture_from_staging.py`, the production path) or, for local
bootstrap and the round-trip smoke test, from our own sandbox container (`introspect_local.py`).
It NEVER connects to Loop Capital's real on-prem server.

Manifest mode is a distinct front door from the existing SCENARIO MODE (`setup.sh` -> `reset.py`,
which drives the golden-case fixtures in `sql/*.sql`). The two never run together, preserving the
sandbox's "one seeding mechanism, not two" rule: scenario mode seeds from `sql/*.sql`; manifest
mode seeds only from this manifest.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Final

from pydantic import BaseModel, Field

MANIFEST_VERSION: Final[str] = "1"
SANDBOX_DATABASE: Final[str] = "LoopCapitalAM"
DEFAULT_SCHEMA: Final[str] = "dbo"


class KeyRole(str, Enum):
    """A column's role in the table's key structure — drives synthetic uniqueness."""

    PRIMARY = "pk"
    FOREIGN = "fk"
    NONE = "none"


class CaptureSource(str, Enum):
    """Where a manifest was captured from — provenance, stamped on every manifest."""

    STAGING = "staging"  # production path: platform-core GraphQL (capture_from_staging.py)
    LOCAL_INTROSPECT = "local-introspect"  # dev bootstrap / round-trip proof (introspect_local.py)


class ColumnSpec(BaseModel):
    """One column's shape — enough to regenerate faithful DDL and synthesize typed rows."""

    name: str
    sql_type: str  # SQL Server type incl. length/precision, e.g. "DECIMAL(18,4)", "VARCHAR(20)"
    nullable: bool
    key: KeyRole = KeyRole.NONE
    identity: bool = False  # IDENTITY column — recreated as IDENTITY, skipped on INSERT
    computed: bool = False  # computed column — materialized as a plain column, never inserted


class TableSpec(BaseModel):
    """One table's schema-qualified shape. `row_estimate` is a COUNT (a number), never row data."""

    name: str  # schema-qualified, e.g. "dbo.raw_positions"
    columns: list[ColumnSpec]
    row_estimate: int = 0

    @property
    def schema_name(self) -> str:
        """The schema part of the qualified name (e.g. 'dbo')."""
        return self.name.split(".", 1)[0] if "." in self.name else DEFAULT_SCHEMA

    @property
    def bare_name(self) -> str:
        """The table part of the qualified name, without schema (e.g. 'raw_positions')."""
        return self.name.split(".", 1)[1] if "." in self.name else self.name


class ArtifactRefs(BaseModel):
    """Paths to transformation/report artifacts discovered alongside the schema — refs only."""

    dbt_models: list[str] = Field(default_factory=list)
    ssis: list[str] = Field(default_factory=list)
    ssrs: list[str] = Field(default_factory=list)


class SchemaManifest(BaseModel):
    """The committed, git-only shape of the Loop Capital sandbox — no rows, no secrets."""

    manifest_version: str = MANIFEST_VERSION
    captured_at: str  # ISO 8601 UTC, e.g. "2026-08-12T00:00:00Z"
    source: CaptureSource
    database: str = SANDBOX_DATABASE
    tables: list[TableSpec]
    artifacts: ArtifactRefs = Field(default_factory=ArtifactRefs)


def load_manifest(*, path: Path) -> SchemaManifest:
    """Load and validate a schema manifest from disk."""
    return SchemaManifest.model_validate_json(path.read_text())


def dump_manifest(*, manifest: SchemaManifest, path: Path) -> None:
    """Write a schema manifest to disk as pretty JSON with a trailing newline."""
    path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2) + "\n")
