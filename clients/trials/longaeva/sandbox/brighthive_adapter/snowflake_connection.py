"""Reference `SnowflakeConnection` — the GAP-1 drop-in for BrightHive.

This is a parity implementation of BrightHive's `WarehouseConnection` ABC
(`brightbot/tools/warehouse_connections.py`). It is the exact class that needs
to be added to `CONNECTION_CLASSES["snowflake"]` to close GAP-1 (see
`../../BRIGHTHIVE_GAPS.md`).

It mirrors the contract of `RedshiftConnection` / `SynapseConnection`:
  - connect() -> a live connection
  - execute_query() with the SAME SELECT-only security guard
  - close_connection()
  - rollback()

Kept here in the sandbox so we can prove it connects BrightHive's interface to
the live `LONGAEVA_POC` environment *before* touching the production repo
(which needs its own branch + multi-agent review). When promoted, this drops
into warehouse_connections.py verbatim (swap the local ABC import for the repo's).

Verify:
  uv run --with snowflake-connector-python python snowflake_connection.py
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import snowflake.connector

logger = logging.getLogger(__name__)


# --- Mirrors brightbot/tools/warehouse_connections.py:WarehouseConnection -----
# In the production repo this import is removed and the existing ABC is used.
class WarehouseConnection(ABC):
    """Abstract base class for stateful warehouse connections (BrightHive parity)."""

    @abstractmethod
    def connect(self) -> Any: ...

    @abstractmethod
    def execute_query(self, query: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def close_connection(self) -> None: ...

    def rollback(self) -> None:  # noqa: B027 — intentional no-op default
        return


# Same allowed-statement guard the Redshift/Synapse connections enforce.
ALLOWED_QUERY_STARTS = ("SELECT", "SHOW", "WITH", "DESC", "DESCRIBE", "EXPLAIN")


class SnowflakeConnection(WarehouseConnection):
    """Stateful Snowflake connection mirroring RedshiftConnection's contract.

    Expected connection_params (from SnowflakeConnectionParams in
    query_retrieval.py): account, user, password, warehouse, database, schema,
    role (all optional except account/user + an auth method).
    """

    def __init__(self, connection_params: dict[str, Any]):
        """Initialize SnowflakeConnection with connection parameters."""
        self.connection_params = connection_params
        self.connection: snowflake.connector.SnowflakeConnection | None = None

    def connect(self) -> snowflake.connector.SnowflakeConnection:
        """Establish connection to Snowflake."""
        logger.info("Initializing Snowflake connection")
        safe = {k: v for k, v in self.connection_params.items()
                if k not in ("password", "private_key", "token")}
        logger.debug(f"Connection parameters: {safe}")

        p = self.connection_params
        conn_kwargs: dict[str, Any] = {
            "account": p["account"],
            "user": p["user"],
        }
        # Auth: password or PAT/token. Snowflake connector accepts either.
        if p.get("password"):
            conn_kwargs["password"] = p["password"]
        if p.get("token"):
            conn_kwargs["token"] = p["token"]
            conn_kwargs["authenticator"] = p.get("authenticator", "oauth")
        # Optional session context
        for key in ("warehouse", "database", "schema", "role"):
            if p.get(key):
                conn_kwargs[key] = p[key]

        try:
            self.connection = snowflake.connector.connect(**conn_kwargs)
            logger.info("Successfully established Snowflake connection")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def rollback(self) -> None:
        """Roll back the current transaction if one exists."""
        if self.connection:
            try:
                self.connection.rollback()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Failed to rollback: {e}")

    def execute_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a read-only query and return results as dicts."""
        # SELECT-only enforcement — identical policy to RedshiftConnection.
        query_upper = query.lstrip().upper()
        if not any(query_upper.startswith(s) for s in ALLOWED_QUERY_STARTS):
            msg = (f"Security violation: only read-only statements allowed. "
                   f"Query must start with one of {ALLOWED_QUERY_STARTS}. "
                   f"Provided: {query[:100]}...")
            logger.error(msg)
            raise ValueError(msg)

        if not self.connection:
            self.connection = self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            if cursor.description is None:
                return []
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
            logger.info(f"Query executed successfully. Retrieved {len(results)} rows")
            return results
        finally:
            cursor.close()

    def close_connection(self) -> None:
        """Close the warehouse connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


# --- Self-test against the live sandbox -------------------------------------

def _load_sandbox_params() -> dict[str, Any]:
    import tomllib
    from pathlib import Path
    cfg = Path.home() / ".snowflake" / "config.toml"
    with cfg.open("rb") as f:
        c = tomllib.load(f)["connections"]["brighthive"]
    return {
        "account": c["account"], "user": c["user"], "password": c["password"],
        "warehouse": c.get("warehouse"), "database": c.get("database"),
        "schema": c.get("schema"), "role": c.get("role"),
    }


def _selftest() -> int:
    logging.basicConfig(level=logging.INFO)
    conn = SnowflakeConnection(connection_params=_load_sandbox_params())
    checks: list[tuple[str, bool]] = []

    # 1. connects + runs a SELECT
    rows = conn.execute_query("SELECT CURRENT_ROLE() AS role, CURRENT_DATABASE() AS db")
    ok_ctx = rows and rows[0]["ROLE"] == "LONGAEVA_POC_ROLE" and rows[0]["DB"] == "LONGAEVA_POC"
    checks.append(("connects + SELECT context", bool(ok_ctx)))

    # 2. queries the semantic view (the BrightHive retrieval path)
    sv = conn.execute_query(
        "SELECT * FROM SEMANTIC_VIEW(LONGAEVA_POC.SEMANTIC.sv_daily_portfolio_exposure "
        "DIMENSIONS region METRICS total_exposure_usd)"
    )
    checks.append(("queries semantic view", len(sv) >= 4))

    # 3. SELECT-only guard blocks writes
    blocked = False
    try:
        conn.execute_query("DELETE FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure")
    except ValueError:
        blocked = True
    checks.append(("SELECT-only guard blocks DELETE", blocked))

    # 4. introspection works (GAP-2 surface)
    tbls = conn.execute_query(
        "SELECT table_name FROM LONGAEVA_POC.INFORMATION_SCHEMA.TABLES "
        "WHERE table_schema = 'GOLD' AND table_type = 'BASE TABLE'"
    )
    checks.append(("INFORMATION_SCHEMA introspection", len(tbls) >= 2))

    conn.close_connection()

    print("\n=== SnowflakeConnection adapter self-test ===")
    all_ok = True
    for name, ok in checks:
        print(f"  {'✅' if ok else '❌'} {name}")
        all_ok = all_ok and ok
    print("=" * 45)
    print(f"{'✅ PASS' if all_ok else '❌ FAIL'} — BrightHive interface connects to live sandbox")
    return 0 if all_ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(_selftest())
