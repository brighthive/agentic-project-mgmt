"""BH-596 seed — verified_query compile-and-run validator.

Takes a scaffolded Atlas semantic-view YAML document and machine-validates its
`verified_queries[]` exactly the way Longaeva's enrollment harness will: run
each query's SQL against Snowflake and confirm it compiles + returns (or at
least executes without a compilation error).

This is the grounding gate. A verified_query that doesn't round-trip blocks
enrollment, so catching it here — before the PR, before the client's harness —
is the difference between a clean enrollment and a bounced one.

Pure-ish: the warehouse call is injected (executor callable), so this is unit
testable with a fake executor AND runnable live via the snow CLI.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Callable, Protocol


class QueryExecutor(Protocol):
    """Runs SQL, returns rows or raises on a compilation/runtime error."""

    def __call__(self, sql: str) -> list[dict]: ...


@dataclass(frozen=True)
class VerifiedQueryResult:
    """Outcome of validating one verified_query."""

    name: str
    passed: bool
    row_count: int | None
    error: str | None


@dataclass(frozen=True)
class ValidationReport:
    """Aggregate outcome over all verified_queries in a document."""

    results: tuple[VerifiedQueryResult, ...]

    @property
    def all_passed(self) -> bool:
        return bool(self.results) and all(r.passed for r in self.results)

    @property
    def summary(self) -> str:
        passed = sum(1 for r in self.results if r.passed)
        return f"{passed}/{len(self.results)} verified_queries round-trip"


def validate_verified_queries(
    *,
    document: dict,
    executor: QueryExecutor,
) -> ValidationReport:
    """Run every verified_query in the scaffolded doc through the executor.

    A query 'passes' when the executor returns without raising. Compilation
    errors (invalid identifier, unknown semantic view) raise → recorded as failures.
    """
    results: list[VerifiedQueryResult] = []
    for vq in document.get("verified_queries", []):
        name = vq.get("name", "<unnamed>")
        sql = vq.get("sql", "")
        if not sql.strip():
            results.append(VerifiedQueryResult(name=name, passed=False, row_count=None,
                                               error="empty sql"))
            continue
        try:
            rows = executor(sql)
            results.append(VerifiedQueryResult(name=name, passed=True,
                                               row_count=len(rows), error=None))
        except Exception as exc:  # compilation or runtime error → fails the gate
            results.append(VerifiedQueryResult(name=name, passed=False, row_count=None,
                                               error=str(exc).strip().splitlines()[0][:200]))
    return ValidationReport(results=tuple(results))


def make_snow_executor(connection: str = "brighthive") -> Callable[[str], list[dict]]:
    """A live QueryExecutor backed by the snow CLI."""

    def _run(sql: str) -> list[dict]:
        proc = subprocess.run(
            ["snow", "sql", "-c", connection, "-q", sql, "--format", "json"],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(_extract_snow_error(proc.stderr or proc.stdout))
        out = proc.stdout.strip()
        return json.loads(out) if out else []

    return _run


def _extract_snow_error(raw: str) -> str:
    """Pull the meaningful message out of snow CLI's box-drawn error output.

    The CLI wraps errors in ─/│ box characters; strip those and join the real
    text so callers (and assertions) see e.g. 'invalid identifier ...'.
    """
    box_chars = "╭╮╰╯─│ "
    lines = []
    for line in raw.splitlines():
        # Strip box-drawing chars from both ends, then drop the "Error" header.
        cleaned = line.strip().strip(box_chars).strip()
        if cleaned.startswith("Error"):
            cleaned = cleaned.lstrip("Error").strip(box_chars).strip()
        # Skip pure-border / empty lines.
        if not cleaned or set(cleaned) <= set(box_chars):
            continue
        lines.append(cleaned)
    return " ".join(lines).strip() or raw.strip()[:200]
