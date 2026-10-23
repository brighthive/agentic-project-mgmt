"""Verify every PR listed in the sprint release notes against production, and attribute it."""

import json
import re
import subprocess
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
WORKSPACE = REPO_ROOT.parent
SPRINT_DIR = REPO_ROOT / "jira" / "sprint"
DATA_DIR = REPO_ROOT / "docs" / "year-one" / "data"
CACHE_DIR = DATA_DIR / ".cache_prs"
OUTPUT_PATH = DATA_DIR / "shipped_prs.json"
ORG = "brighthive"
KURI_LOGIN = "drchinca"
LINK_RE = re.compile(r"\[#(\d+)\]\(https://github\.com/brighthive/([\w.-]+)/pull/\d+\)")
HEADING_RE = re.compile(r"^\*\*(.+?)\*\*\s*$")
CONVENTIONAL_RE = re.compile(r"^(feat|fix|perf|docs|style|refactor|test|chore|ci|build|revert)(\([^)]+\))?!?:", re.IGNORECASE)
VALUE_TYPES = ("feat", "fix", "perf")
CARRIER_RE = re.compile(r"release|promot|bump version|merge .* into|^staging|^main", re.IGNORECASE)
RELEASE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+\.\d+-release$")
TAG_REPOS = ("brighthive-platform-core", "brighthive-webapp")
MAIN_REFS = ("origin/main", "origin/master")
WORKERS = 4
RETRY_PAUSE_S = 60
MAX_RETRIES = 20


def run_gh(*, args: list[str]) -> str | None:
    """Run gh; None when the PR does not exist, retrying on rate limits."""
    for _ in range(MAX_RETRIES):
        r = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
        if r.returncode == 0:
            return r.stdout
        if "rate limit" in r.stderr.lower():
            time.sleep(RETRY_PAUSE_S)
            continue
        return None
    return None


def parse_notes() -> list[dict]:
    """PR lines of every sprint's technical release notes, with capability heading."""
    rows = []
    for path in sorted(SPRINT_DIR.glob("*/RELEASE_NOTES.md"), key=lambda p: int(p.parent.name)):
        sprint, capability = int(path.parent.name), ""
        for line in path.read_text().splitlines():
            heading = HEADING_RE.match(line.strip())
            if heading:
                capability = heading.group(1)
            elif line.startswith("## "):
                capability = ""
            for number, repo in LINK_RE.findall(line):
                rows.append({"sprint": sprint, "capability": capability, "repo": repo, "number": int(number)})
    return rows


def pr_record(*, repo: str, number: int) -> dict | None:
    """Fetch (and cache) one PR's author, merge commit, title and dates."""
    cache = CACHE_DIR / f"{repo}-{number}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = run_gh(args=["api", f"repos/{ORG}/{repo}/pulls/{number}", "--jq", "{author: .user.login, merged: .merged, sha: .merge_commit_sha, title: .title, merged_at: .merged_at, base: .base.ref}"])
    if out is None:
        return None
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(out)
    return json.loads(out)


def git(*, repo: str, args: list[str]) -> str:
    """Run git in a repo and return stdout, empty on failure."""
    r = subprocess.run(["git", "-C", str(WORKSPACE / repo), *args], capture_output=True, text=True, check=False)
    return r.stdout if r.returncode == 0 else ""


def production_status(*, repo: str, sha: str) -> dict:
    """Release tag (platform-core, webapp) or main-branch membership (others) for a merge commit."""
    if not sha or not git(repo=repo, args=["cat-file", "-t", sha]).strip():
        return {"status": "commit_not_local", "release_tag": None, "release_date": None}
    if repo in TAG_REPOS:
        tags = [t for t in git(repo=repo, args=["tag", "--contains", sha, "--sort=creatordate"]).split() if RELEASE_TAG_RE.match(t)]
        if tags:
            date = git(repo=repo, args=["log", "-1", "--format=%as", tags[0]]).strip()
            return {"status": "released", "release_tag": tags[0], "release_date": date}
    else:
        on_main = any(git(repo=repo, args=["merge-base", "--is-ancestor", sha, ref]) == "" and subprocess.run(["git", "-C", str(WORKSPACE / repo), "merge-base", "--is-ancestor", sha, ref], capture_output=True).returncode == 0 for ref in MAIN_REFS)
        if on_main:
            return {"status": "on_main", "release_tag": None, "release_date": None}
    return {"status": "not_in_production", "release_tag": None, "release_date": None}


def classify(*, row: dict, record: dict | None) -> dict:
    """Merge note row, PR record and production status into one result."""
    if record is None or not record["merged"]:
        return {**row, "status": "not_merged_or_missing", "kuri": False, "title": None, "type": None, "value_change": False}
    match = CONVENTIONAL_RE.match(record["title"])
    ptype = match.group(1).lower() if match else "untyped"
    carrier = bool(CARRIER_RE.search(record["title"])) and ptype in ("chore", "ci", "untyped")
    return {**row, "title": record["title"], "type": ptype, "author": record["author"], "kuri": record["author"] == KURI_LOGIN,
            "merged_at": (record["merged_at"] or "")[:10], "carrier": carrier, "value_change": ptype in VALUE_TYPES and not carrier,
            **production_status(repo=row["repo"], sha=record["sha"])}


def main() -> None:
    """Verify every listed PR and summarize Kuri's production-verified user-facing changes."""
    rows = list({(r["repo"], r["number"]): r for r in parse_notes()}.values())
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        records = list(pool.map(lambda r: pr_record(repo=r["repo"], number=r["number"]), rows))
    prs = [classify(row=r, record=rec) for r, rec in zip(rows, records)]
    value = [p for p in prs if p.get("value_change")]
    shipped = [p for p in value if p["status"] in ("released", "on_main")]
    kuri_shipped = [p for p in shipped if p["kuri"]]
    by_cap = Counter((p["sprint"], p["capability"]) for p in kuri_shipped)
    payload = {
        "method": "PRs are every pull request linked in jira/sprint/N/RELEASE_NOTES.md (sprints 1 to 16). Value change = feat, fix or perf PR that is not a release carrier. Production: platform-core and webapp, merge commit in a plain -release tag; other repos, merge commit on main or master. Git shows released or on the production branch, not that the change is running.",
        "prs_in_notes": len(prs), "merged": sum(p["status"] != "not_merged_or_missing" for p in prs),
        "value_changes": len(value), "value_changes_in_production": len(shipped), "kuri_value_changes": sum(p["kuri"] for p in value),
        "kuri_value_changes_in_production": len(kuri_shipped),
        "status_of_value_changes": dict(Counter(p["status"] for p in value)),
        "status_of_kuri_value_changes": dict(Counter(p["status"] for p in value if p["kuri"])),
        "kuri_shipped_by_repo": dict(Counter(p["repo"] for p in kuri_shipped).most_common()),
        "kuri_shipped_by_type": dict(Counter(p["type"] for p in kuri_shipped)),
        "kuri_shipped_by_sprint_capability": [{"sprint": s, "capability": c, "prs": n} for (s, c), n in sorted(by_cap.items())],
        "prs": prs,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps({k: v for k, v in payload.items() if k not in ("prs", "kuri_shipped_by_sprint_capability", "method")}, indent=1))


if __name__ == "__main__":
    main()
