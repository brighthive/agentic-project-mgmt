"""Inventory the end-to-end suite and webapp test/CI surface from local git."""

import json
import re
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "suites.json"
TEST_FUNCTION_RE = re.compile(r"^\s*(async )?def test_", re.MULTILINE)
WEBAPP_TEST_RE = re.compile(r"\.(test|spec)\.(ts|tsx)$")
E2E_DIRS = ("e2e/surfaces", "e2e/features", "e2e/fixtures", "e2e/plugins", "e2e/core", "contracts", "scripts")


def git(*, repo: Path, args: list[str]) -> str:
    """Run a git command in a repo and return stdout."""
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def integration_ref(*, repo: Path) -> str:
    """origin/HEAD target of a repo."""
    return git(repo=repo, args=["rev-parse", "--abbrev-ref", "origin/HEAD"]).strip()


def files_in(*, repo: Path, ref: str, prefix: str) -> list[str]:
    """List files under a path at a ref."""
    return git(repo=repo, args=["ls-tree", "-r", "--name-only", ref, "--", prefix]).splitlines()


def count_test_functions(*, repo: Path, ref: str) -> int:
    """Count pytest test functions under e2e/."""
    out = subprocess.run(["git", "-C", str(repo), "grep", "-h", "-E", r"^\s*(async )?def test_", ref, "--", "e2e"],
                         capture_output=True, text=True, check=False).stdout
    return len(out.splitlines())


def main() -> None:
    """Write the suite inventory."""
    e2e = WORKSPACE / "brighthive-e2e"
    webapp = WORKSPACE / "brighthive-webapp"
    e2e_ref, web_ref = integration_ref(repo=e2e), integration_ref(repo=webapp)
    payload = {
        "e2e": {
            "ref": e2e_ref,
            "first_commit": git(repo=e2e, args=["log", e2e_ref, "--reverse", "--format=%ad", "--date=short"]).splitlines()[0],
            "files_by_area": {d: len(files_in(repo=e2e, ref=e2e_ref, prefix=d)) for d in E2E_DIRS},
            "test_functions": count_test_functions(repo=e2e, ref=e2e_ref),
            "workflows": [Path(p).name for p in files_in(repo=e2e, ref=e2e_ref, prefix=".github/workflows")],
        },
        "webapp": {
            "ref": web_ref,
            "test_files": sum(1 for p in git(repo=webapp, args=["ls-tree", "-r", "--name-only", web_ref]).splitlines() if WEBAPP_TEST_RE.search(p)),
            "workflows": [Path(p).name for p in files_in(repo=webapp, ref=web_ref, prefix=".github/workflows")],
        },
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
