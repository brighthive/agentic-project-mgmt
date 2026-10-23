"""Snapshot repo structure (tests, docs, specs, CI, agent contracts) month by month from local git."""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "repo_structure.json"
FIRST_MONTH = (2024, 10)
LAST_MONTH = (2026, 10)
REPOS = (
    "brightbot", "brighthive-platform-core", "brighthive-webapp", "brighthive-e2e",
    "agentic-project-mgmt", "platform-saas-ai-context", "brightbot-slack-server", "brightagent-v3",
)
DEFAULT_REFS = ("origin/develop", "origin/master", "origin/main", "origin/production")
NON_CONTENT_NAMES = ("README.md", "THEMES.md")
NON_CONTENT_MARKER = "TEMPLATE"


@dataclass(frozen=True)
class Category:
    name: str
    matches: tuple[str, ...]


CATEGORIES = (
    Category(name="test_files", matches=("test_", ".test.", ".spec.")),
    Category(name="markdown_docs", matches=(".md",)),
    Category(name="agent_contracts", matches=("CLAUDE.md", "AGENTS.md")),
    Category(name="ci_workflows", matches=(".github/workflows/",)),
    Category(name="spec_files", matches=("docs/specs/",)),
    Category(name="adr_files", matches=("docs/adr/", "docs/decisions/")),
)


def git(*, repo: Path, args: list[str]) -> str:
    """Run a git command in a repo and return stdout."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def default_ref(*, repo: Path) -> str | None:
    """First existing integration branch ref."""
    return next((r for r in DEFAULT_REFS if git(repo=repo, args=["rev-parse", "--verify", "-q", r]).strip()), None)


def month_ends() -> list[tuple[str, datetime]]:
    """Month labels with the first instant of the following month."""
    out = []
    year, month = FIRST_MONTH
    while (year, month) <= LAST_MONTH:
        ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
        out.append((f"{year}-{month:02d}", datetime(ny, nm, 1, tzinfo=timezone.utc)))
        year, month = ny, nm
    return out


def is_non_content(*, path: str) -> bool:
    """True for READMEs, index files and templates, which are not specs or decision records."""
    name = Path(path).name
    return name in NON_CONTENT_NAMES or NON_CONTENT_MARKER in name


def count_category(*, paths: list[str], category: Category) -> int:
    """Count paths matching a category."""
    if category.name == "test_files":
        return sum(1 for p in paths if p.endswith((".py", ".ts", ".tsx", ".js")) and any(m in Path(p).name for m in category.matches))
    if category.name == "markdown_docs":
        return sum(1 for p in paths if p.endswith(".md"))
    if category.name == "agent_contracts":
        return sum(1 for p in paths if Path(p).name in category.matches)
    if category.name in ("spec_files", "adr_files"):
        return sum(1 for p in paths if any(m in p for m in category.matches) and not is_non_content(path=p))
    return sum(1 for p in paths if any(m in p for m in category.matches))


def snapshot(*, repo: Path, ref: str, before: datetime) -> dict | None:
    """Category counts at the last commit before a date, or None if the repo did not exist yet."""
    sha = git(repo=repo, args=["rev-list", "-1", f"--before={before.isoformat()}", ref]).strip()
    if not sha:
        return None
    paths = git(repo=repo, args=["ls-tree", "-r", "--name-only", sha]).splitlines()
    return {c.name: count_category(paths=paths, category=c) for c in CATEGORIES}


def main() -> None:
    """Write monthly structure snapshots for every repo that exists locally."""
    payload: dict[str, dict] = {}
    for name in REPOS:
        repo = WORKSPACE / name
        ref = default_ref(repo=repo) if repo.exists() else None
        if not ref:
            continue
        payload[name] = {"ref": ref, "months": {label: snapshot(repo=repo, ref=ref, before=end) for label, end in month_ends()}}
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    for name, data in payload.items():
        first = data["months"]["2024-10"] or {}
        last = data["months"]["2026-10"] or {}
        print(name, {k: (first.get(k), last.get(k)) for k in ("test_files", "markdown_docs", "agent_contracts", "ci_workflows", "spec_files", "adr_files")})


if __name__ == "__main__":
    main()
