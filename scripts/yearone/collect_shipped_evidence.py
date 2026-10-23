"""Cross-reference Jira tickets with merged commits to find shipped work still shown as open."""

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data"
OUTPUT_PATH = DATA_DIR / "shipped_evidence.json"
REPOS = (
    "brightbot", "brighthive-platform-core", "brighthive-webapp", "brighthive-e2e", "brightbot-slack-server",
    "agentic-project-mgmt", "brightagent-v3", "brighthive-admin", "brighthive-data-organization-cdk",
    "brighthive-data-workspace-cdk", "platform-saas-ai-context", "brightagent-engineering-runner",
)
INTEGRATION_REFS = ("origin/develop", "origin/staging", "origin/master", "origin/main", "origin/production")
PRODUCTION_REFS = ("origin/master", "origin/main", "origin/production")
TICKET_RE = re.compile(r"\bBH-(\d+)\b")
OPEN_STATES = ("backlog", "in_flight")


def existing_refs(*, repo: Path, refs: tuple[str, ...]) -> list[str]:
    """Refs that exist in a repo."""
    return [r for r in refs if subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", r], capture_output=True).returncode == 0]


def ticket_keys_in(*, repo: Path, refs: list[str]) -> set[str]:
    """BH keys mentioned in any commit message reachable from the refs."""
    if not refs:
        return set()
    out = subprocess.run(["git", "-C", str(repo), "log", *refs, "--format=%B"], capture_output=True, text=True, check=False).stdout
    return {f"BH-{n}" for n in TICKET_RE.findall(out)}


def main() -> None:
    """Classify non-done work items by whether merged code references them."""
    issues = [i for i in json.loads((DATA_DIR / "jira_issues.json").read_text()) if i["type"] != "Epic"]
    integrated: set[str] = set()
    in_production: set[str] = set()
    for name in REPOS:
        repo = WORKSPACE / name
        if repo.exists():
            integrated |= ticket_keys_in(repo=repo, refs=existing_refs(repo=repo, refs=INTEGRATION_REFS))
            in_production |= ticket_keys_in(repo=repo, refs=existing_refs(repo=repo, refs=PRODUCTION_REFS))
    by_status: dict[str, dict[str, int]] = {}
    for status in sorted({i["status"] for i in issues}):
        rows = [i for i in issues if i["status"] == status]
        by_status[status] = {"tickets": len(rows), "with_merged_code": sum(i["key"] in integrated for i in rows),
                             "with_code_in_production_branch": sum(i["key"] in in_production for i in rows)}
    open_rows = [i for i in issues if i["state"] in OPEN_STATES]
    shipped_open = [i for i in open_rows if i["key"] in integrated]
    payload = {
        "method": "A ticket counts as having shipped evidence when its BH key appears in a commit message on develop, staging or a production branch of any org repo. Evidence of merged work, not proof the ticket is complete.",
        "work_items": len(issues),
        "done_in_jira": sum(i["state"] == "done" for i in issues),
        "open_in_jira": len(open_rows),
        "open_with_merged_code": len(shipped_open),
        "open_with_code_in_production_branch": sum(i["key"] in in_production for i in open_rows),
        "any_status_with_merged_code": sum(i["key"] in integrated for i in issues),
        "by_status": by_status,
        "open_with_merged_code_by_status": dict(Counter(i["status"] for i in shipped_open)),
        "sample_needs_refinement_with_code": [i["key"] for i in shipped_open if i["status"] == "Needs Refinement"][:15],
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps({k: v for k, v in payload.items() if k != "method"}, indent=2))


if __name__ == "__main__":
    main()
