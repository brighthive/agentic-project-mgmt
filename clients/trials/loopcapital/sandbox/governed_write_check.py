#!/usr/bin/env python3
"""Prove the governed read/write boundary holds on a REAL SQL Server (BH-1403).

Frank's trial grants BrightAgent "scoped read + optional governed-write" against his own
on-prem SQL Server 2019. This script is the evidence that the boundary is real: it connects
as each governed principal (never `sa`) over pymssql and asserts what each one can and — more
importantly — CANNOT do, letting SQL Server's own permission engine deliver the verdict.

Nothing here is mocked. Every FAIL below would be a real privilege escalation on a real
database, which is the point: per test-behavior-real.md, a boundary asserted only in a unit
test with a fake connection proves the fake, not the boundary. If SQL Server's permission
engine behaved differently tomorrow, this script goes red.

Assertions map 1:1 to docs/specs/loopcapital-onprem-read-write-sandbox.md §3:

    INV-1  reader cannot write anywhere
    INV-2  engineer CAN write inside the brightagent schema
    INV-3  engineer cannot write to dbo (the client's data)
    INV-4  neither principal holds sysadmin/db_owner
    INV-5  both principals CAN read dbo (a boundary that blocks reads is broken, not safe)

Exit codes (contract, §2):
    0  every assertion held
    1  a boundary assertion FAILED — something did what it must not
    2  could not connect / setup error

Usage:
    export MSSQL_SA_PASSWORD='<throwaway-local-password>'
    export BRIGHTAGENT_READER_PASSWORD='...' BRIGHTAGENT_ENGINEER_PASSWORD='...'
    uv run --with pymssql python governed_write_check.py
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Final

import pymssql

HOST: Final[str] = os.environ.get("LOOPCAPITAL_SQL_HOST", "127.0.0.1")
PORT: Final[int] = int(os.environ.get("LOOPCAPITAL_SQL_PORT", "1433"))
DATABASE: Final[str] = "LoopCapitalAM"
TDS_VERSION: Final[str] = "7.4"

READER: Final[str] = "brightagent_reader"
ENGINEER: Final[str] = "brightagent_engineer"
AGENT_SCHEMA: Final[str] = "brightagent"

# The table the engineer builds inside its own schema — named for what it is, an
# exposure check an engineer would actually write, not "test_table_1".
CHECK_TABLE: Final[str] = f"{AGENT_SCHEMA}.exposure_check"

# A client-owned table the engineer must never be able to modify.
CLIENT_TABLE: Final[str] = "dbo.mart_compliance_breaches"


@dataclass(frozen=True)
class Assertion:
    """One boundary check and how it turned out."""

    invariant: str
    description: str
    passed: bool
    detail: str = ""

    def render(self) -> str:
        mark = "PASS" if self.passed else "FAIL"
        tail = f" — {self.detail}" if self.detail else ""
        return f"{mark} {self.invariant} {self.description}{tail}"


def connect(*, user: str, password: str) -> pymssql.Connection:
    """Open a real TDS connection as the given principal."""
    return pymssql.connect(
        server=HOST,
        port=PORT,
        user=user,
        password=password,
        database=DATABASE,
        tds_version=TDS_VERSION,
        timeout=15,
        login_timeout=15,
    )


# SQL Server error numbers that mean "permission denied" — the ONLY reason a
# denial assertion may pass. Anything else (a typo'd table, a dropped fixture)
# also raises, and treating that as a pass would turn this whole script green
# for exactly the wrong reason.
PERMISSION_DENIED_ERRORS: Final[frozenset[int]] = frozenset(
    {
        229,  # The <perm> permission was denied on the object
        230,  # The <perm> permission was denied on the column
        262,  # <perm> permission denied in database (e.g. CREATE TABLE)
        300,  # VIEW SERVER STATE permission was denied
    }
)

# 208 = "Invalid object name". If a denial assertion hits this, the fixture is
# missing, not protected.
OBJECT_NOT_FOUND: Final[int] = 208

# 1088 = "Cannot find the object ... because it does not exist or you do not have
# permissions." SQL Server returns this for a DENIED ALTER *on purpose*: telling an
# unauthorized caller that an object exists is itself an information leak, so the
# engine collapses "absent" and "forbidden" into one message.
#
# That makes 1088 genuinely ambiguous, and blanket-accepting it would reopen the
# exact false-positive this module guards against — a typo'd table name would sail
# through as a PASS. So 1088 counts as a denial ONLY when the object is separately
# proven to resolve (see `target_object` below).
AMBIGUOUS_DENIED_OR_MISSING: Final[int] = 1088


def _error_number(exc: pymssql.Error) -> int | None:
    """Pull SQL Server's numeric error code out of a pymssql exception."""
    if exc.args and isinstance(exc.args[0], int):
        return exc.args[0]
    return None


def _object_exists(*, connection: pymssql.Connection, target_object: str) -> bool:
    """Resolve an object by name on THIS principal's connection.

    OBJECT_ID() returns non-null for an object the caller can see; both governed
    principals hold SELECT on dbo, so a real table always resolves here. If it does
    not resolve, the fixture is missing and no boundary was exercised.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT OBJECT_ID(%s)", (target_object,))
            (object_id,) = cursor.fetchone()
    except pymssql.Error:
        return False
    return object_id is not None


def expect_denied(
    *,
    connection: pymssql.Connection,
    statement: str,
    invariant: str,
    description: str,
    target_object: str | None = None,
) -> Assertion:
    """Assert a statement is rejected BECAUSE OF PERMISSIONS — not for any other reason.

    The distinction matters more than it looks. If the target table simply does not exist,
    the statement still raises, and a naive `except` would record a triumphant PASS for a
    boundary that was never tested. That failure mode is silent and permanent, so the error
    number is checked rather than the mere fact of an exception.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(statement)
        connection.rollback()
    except pymssql.Error as exc:
        number = _error_number(exc)
        if number in PERMISSION_DENIED_ERRORS:
            return Assertion(invariant=invariant, description=description, passed=True, detail=f"denied ({number})")
        if number == AMBIGUOUS_DENIED_OR_MISSING and target_object:
            if _object_exists(connection=connection, target_object=target_object):
                return Assertion(
                    invariant=invariant,
                    description=description,
                    passed=True,
                    detail=f"denied ({number}; {target_object} resolves, so this is permission, not absence)",
                )
            return Assertion(
                invariant=invariant,
                description=description,
                passed=False,
                detail=f"{target_object} does not resolve — fixture missing, boundary NOT tested",
            )
        if number == OBJECT_NOT_FOUND:
            return Assertion(
                invariant=invariant,
                description=description,
                passed=False,
                detail="target table does not exist — fixture missing, boundary NOT tested",
            )
        return Assertion(
            invariant=invariant,
            description=description,
            passed=False,
            detail=f"rejected, but not by a permission check: {_first_line(exc)}",
        )
    return Assertion(
        invariant=invariant,
        description=description,
        passed=False,
        detail="statement SUCCEEDED but must have been denied",
    )


def expect_allowed(*, connection: pymssql.Connection, statement: str, invariant: str, description: str) -> Assertion:
    """Assert a statement is PERMITTED. A boundary that blocks legitimate work is broken too."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(statement)
        connection.commit()
    except pymssql.Error as exc:
        return Assertion(invariant=invariant, description=description, passed=False, detail=_first_line(exc))
    return Assertion(invariant=invariant, description=description, passed=True)


def _first_line(exc: pymssql.Error) -> str:
    """Collapse a multi-line SQL Server error to something readable on one line."""
    text = str(exc).replace("\n", " ").strip()
    return text[:160]


def check_reader(*, password: str) -> list[Assertion]:
    """INV-5 then INV-1: the reader reads everything and writes nothing."""
    results: list[Assertion] = []
    with connect(user=READER, password=password) as connection:
        results.append(
            expect_allowed(
                connection=connection,
                statement="SELECT TOP 1 portfolio_id FROM dbo.mart_daily_portfolio_exposure",
                invariant="INV-5",
                description=f"{READER} can read the client's data",
            )
        )
        results.append(
            expect_denied(
                connection=connection,
                statement=(
                    "INSERT INTO dbo.raw_positions (portfolio_id, security_id, quantity, as_of_date) "
                    "VALUES ('PORT-BREACH', 'SEC-BREACH', 1, '2026-01-01')"
                ),
                invariant="INV-1",
                description=f"{READER} cannot INSERT into the client's data",
            )
        )
        results.append(
            expect_denied(
                connection=connection,
                statement=f"UPDATE {CLIENT_TABLE} SET severity = 'BREACHED'",
                invariant="INV-1",
                description=f"{READER} cannot UPDATE the client's data",
            )
        )
        results.append(
            expect_denied(
                connection=connection,
                statement=f"CREATE TABLE {AGENT_SCHEMA}.reader_should_not_create (id INT)",
                invariant="INV-1",
                description=f"{READER} cannot CREATE tables",
            )
        )
    return results


def check_engineer(*, password: str, keep: bool) -> list[Assertion]:
    """INV-2 and INV-3: writes land inside the agent's own schema and nowhere else."""
    results: list[Assertion] = []
    with connect(user=ENGINEER, password=password) as connection:
        results.append(
            expect_allowed(
                connection=connection,
                statement="SELECT TOP 1 portfolio_id FROM dbo.mart_daily_portfolio_exposure",
                invariant="INV-5",
                description=f"{ENGINEER} can read the client's data",
            )
        )

        # Start from a clean slate so a prior --keep run cannot mask a real failure.
        _drop_check_table(connection=connection)

        results.append(
            expect_allowed(
                connection=connection,
                statement=(
                    f"CREATE TABLE {CHECK_TABLE} "
                    "(portfolio_id VARCHAR(20) NOT NULL, exposure_usd DECIMAL(18,2), "
                    "checked_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME())"
                ),
                invariant="INV-2",
                description=f"{ENGINEER} can CREATE inside its own schema",
            )
        )
        results.append(
            expect_allowed(
                connection=connection,
                # Literal values, deliberately NOT `INSERT ... SELECT FROM dbo`: sourcing from
                # a client table would make this assertion silently depend on seed state, and
                # an empty source would insert zero rows while still "succeeding".
                statement=(
                    f"INSERT INTO {CHECK_TABLE} (portfolio_id, exposure_usd) "
                    "VALUES ('PORT-001-GROWTH', 12500000.00), ('PORT-002-INCOME', 8750000.00)"
                ),
                invariant="INV-2",
                description=f"{ENGINEER} can INSERT into its own schema",
            )
        )
        results.append(_verify_rows_landed(connection=connection))

        results.append(
            expect_denied(
                connection=connection,
                statement=f"UPDATE {CLIENT_TABLE} SET severity = 'BREACHED'",
                invariant="INV-3",
                description=f"{ENGINEER} cannot UPDATE the client's data",
            )
        )
        results.append(
            expect_denied(
                connection=connection,
                statement="DELETE FROM dbo.raw_positions",
                invariant="INV-3",
                description=f"{ENGINEER} cannot DELETE the client's data",
            )
        )
        results.append(
            expect_denied(
                connection=connection,
                statement="ALTER TABLE dbo.raw_positions ADD injected_column INT",
                invariant="INV-3",
                description=f"{ENGINEER} cannot ALTER the client's schema",
                target_object="dbo.raw_positions",
            )
        )

        if not keep:
            _drop_check_table(connection=connection)  # INV-7: leave no residue
    return results


def _verify_rows_landed(*, connection: pymssql.Connection) -> Assertion:
    """A permitted INSERT is only proof if the rows are actually readable afterwards."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {CHECK_TABLE}")
            (count,) = cursor.fetchone()
    except pymssql.Error as exc:
        return Assertion(
            invariant="INV-2",
            description="rows written by the engineer are readable back",
            passed=False,
            detail=_first_line(exc),
        )
    return Assertion(
        invariant="INV-2",
        description="rows written by the engineer are readable back",
        passed=count > 0,
        detail=f"{count} row(s)" if count else "table is empty after a committed INSERT",
    )


def _drop_check_table(*, connection: pymssql.Connection) -> None:
    """Best-effort cleanup; never masks a boundary failure."""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {CHECK_TABLE}")
        connection.commit()
    except pymssql.Error:
        connection.rollback()


def check_cross_database(*, engineer_password: str) -> list[Assertion]:
    """The instance hosts more than one database — reads widen across it, writes must not.

    Doc 1 grants read on "in-scope DBs" (plural), so catalog and cross-database parity need
    SELECT on OMS and TradeDW. The risk that creates is obvious in hindsight and easy to ship
    by accident: granting reads across the instance while quietly granting writes with them.
    These assertions exist to make that regression impossible to miss.
    """
    results: list[Assertion] = []
    with connect(user=ENGINEER, password=engineer_password) as connection:
        for database, table in (("OMS", "OMS.dbo.Trades"), ("TradeDW", "TradeDW.dbo.FactTrade")):
            results.append(
                expect_allowed(
                    connection=connection,
                    statement=f"SELECT TOP 1 Symbol FROM {table}",
                    invariant="INV-5",
                    description=f"{ENGINEER} can read {table} (cross-database, three-part name)",
                )
            )
            results.append(
                expect_denied(
                    connection=connection,
                    statement=f"DELETE FROM {table}",
                    invariant="INV-3",
                    description=f"{ENGINEER} cannot write to {database} — reads widened, writes did not",
                    target_object=table,
                )
            )
    return results


def check_no_admin_rights(*, reader_password: str, engineer_password: str) -> list[Assertion]:
    """INV-4: a principal that can grant itself more permission has no boundary at all."""
    results: list[Assertion] = []
    for principal, password in ((READER, reader_password), (ENGINEER, engineer_password)):
        try:
            with connect(user=principal, password=password) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT IS_SRVROLEMEMBER('sysadmin'), IS_ROLEMEMBER('db_owner')")
                sysadmin, db_owner = cursor.fetchone()
        except pymssql.Error as exc:
            results.append(
                Assertion(
                    invariant="INV-4",
                    description=f"{principal} role membership is checkable",
                    passed=False,
                    detail=_first_line(exc),
                )
            )
            continue
        results.append(
            Assertion(
                invariant="INV-4",
                description=f"{principal} is neither sysadmin nor db_owner",
                passed=not sysadmin and not db_owner,
                detail=f"sysadmin={sysadmin} db_owner={db_owner}",
            )
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="leave the engineer's table in place for manual inspection (default: drop it)",
    )
    args = parser.parse_args()

    reader_password = os.environ.get("BRIGHTAGENT_READER_PASSWORD")
    engineer_password = os.environ.get("BRIGHTAGENT_ENGINEER_PASSWORD")
    if not reader_password or not engineer_password:
        print(
            "ERROR: export BRIGHTAGENT_READER_PASSWORD and BRIGHTAGENT_ENGINEER_PASSWORD "
            "(the values setup.sh created the logins with).",
            file=sys.stderr,
        )
        return 2

    print(f"Governed read/write boundary — {HOST}:{PORT}/{DATABASE}\n")
    try:
        results = [
            *check_reader(password=reader_password),
            *check_engineer(password=engineer_password, keep=args.keep),
            *check_cross_database(engineer_password=engineer_password),
            *check_no_admin_rights(reader_password=reader_password, engineer_password=engineer_password),
        ]
    except pymssql.Error as exc:
        print(f"ERROR: could not connect as a governed principal — {_first_line(exc)}", file=sys.stderr)
        print("Is the sandbox up (./setup.sh), and do the passwords match?", file=sys.stderr)
        return 2

    for result in results:
        print(result.render())

    failed = [result for result in results if not result.passed]
    print(f"\n{len(results) - len(failed)}/{len(results)} assertions held.")
    if failed:
        print(f"{len(failed)} BOUNDARY FAILURE(S) — a principal did something it must not.", file=sys.stderr)
        return 1
    print("Governed boundary holds: reads work, writes are confined to the agent's own schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
