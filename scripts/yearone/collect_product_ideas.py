"""Gather repo evidence for each product idea: first spec, epics, modules, and Kuri's share."""

import fnmatch
import html
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
WORKSPACE = REPO_ROOT.parent
DATA_DIR = REPO_ROOT / "docs" / "year-one" / "data"
SPEC_DIR = "docs/specs"
IDEAS_PATH = Path(__file__).parent / "product_ideas.json"
OUTPUT_PATH = DATA_DIR / "product_ideas.json"
KURI_RE = "Kuri|Chinca|drchinca|Bado"
INTEGRATION_REF = "origin/develop"


def git(*, repo: Path, args: list[str]) -> str:
    """Run a git command and return stdout, empty on failure."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def spec_files(*, globs: list[str]) -> list[str]:
    """Spec files in the repo matching any glob."""
    names = [Path(p).name for p in git(repo=REPO_ROOT, args=["ls-files", SPEC_DIR]).splitlines()]
    return sorted({n for n in names for g in globs if fnmatch.fnmatch(n, g)})


def first_added(*, name: str) -> dict:
    """Date and author of the commit that first added a spec file."""
    out = git(repo=REPO_ROOT, args=["log", "--diff-filter=A", "--follow", "--format=%ad|%an|%ae", "--date=short", "--", f"{SPEC_DIR}/{name}"]).splitlines()
    date, author, email = out[-1].split("|") if out else ("", "", "")
    return {"file": name, "first_added": date, "added_by_kuri": bool(re.search(KURI_RE, f"{author} {email}", re.IGNORECASE))}


def module_share(*, repo: str, path: str) -> dict:
    """Commits touching a module and Kuri's share of them."""
    root = WORKSPACE / repo
    total = len(git(repo=root, args=["log", INTEGRATION_REF, "--no-merges", "--format=%h", "--", path]).splitlines())
    kuri = len(git(repo=root, args=["log", INTEGRATION_REF, "--no-merges", "-i", "-E", f"--author={KURI_RE}", "--format=%h", "--", path]).splitlines())
    return {"repo": repo, "path": path, "commits": total, "kuri_commits": kuri, "kuri_share_pct": round(100 * kuri / total, 1) if total else None}


def matching_epics(*, idea: dict, milestones: list[dict]) -> list[dict]:
    """Milestone epics that match by key or by summary pattern."""
    pattern = re.compile(idea["epic_summary_regex"], re.IGNORECASE)
    rows = [m for m in milestones if m["epic"] in idea["epic_keys"] or pattern.search(html.unescape(m["summary"]))]
    return [{"epic": m["epic"], "summary": html.unescape(m["summary"]), "commits": m["commits"], "kuri_share_pct": m["kuri_share_pct"],
             "first_commit": m["first_commit"], "last_commit": m["last_commit"], "children": m["children"], "children_done": m["children_done"],
             "by_key": m["epic"] in idea["epic_keys"]} for m in rows]


def origin_epics(*, keys: list[str]) -> list[dict]:
    """Jira epics that first wrote the idea down: key, summary, creator and creation date."""
    issues = {i["key"]: i for i in json.loads((DATA_DIR / "jira_issues.json").read_text())}
    return [{"epic": k, "summary": html.unescape(issues[k]["summary"]), "created": issues[k]["created"], "creator": issues[k].get("creator"), "status": issues[k]["status"]} for k in keys if k in issues]


def main() -> None:
    """Write the product-idea evidence file."""
    ideas = json.loads(IDEAS_PATH.read_text())
    milestones = json.loads((DATA_DIR / "milestones.json").read_text())["epics"]
    out = []
    for idea in ideas:
        specs = sorted((first_added(name=n) for n in spec_files(globs=idea["spec_globs"])), key=lambda s: s["first_added"])
        epics = matching_epics(idea=idea, milestones=milestones)
        keyed = [e for e in epics if e["by_key"]]
        commits = sum(e["commits"] for e in keyed)
        out.append({
            "id": idea["id"], "name": idea["name"], "one_line": idea["one_line"],
            "origin_epics": origin_epics(keys=idea["origin_epics"]),
            "specs": specs, "first_spec": specs[0] if specs else None,
            "specs_added_by_kuri": sum(s["added_by_kuri"] for s in specs),
            "epics_by_key": keyed, "related_epics_by_summary": [e for e in epics if not e["by_key"]],
            "commits_in_keyed_epics": commits,
            "kuri_share_of_keyed_epic_commits_pct": round(sum(e["commits"] * e["kuri_share_pct"] for e in keyed) / commits, 1) if commits else None,
            "modules": [module_share(repo=m["repo"], path=m["path"]) for m in idea["modules"]],
        })
    OUTPUT_PATH.write_text(json.dumps({"method": "Specs are matched by file name in docs/specs; first_added is the commit that first added the file. Epics are matched by listed key (counted) and by summary pattern (listed as related, not counted). Spec authorship shows who wrote the spec, not who had the idea.", "ideas": out}, indent=2))
    for i in out:
        fs = i["first_spec"]
        print(f"{i['name']:34} specs {len(i['specs']):>2} (Kuri {i['specs_added_by_kuri']:>2}) first {fs['first_added'] if fs else '-'}  keyed-epic commits {i['commits_in_keyed_epics']:>4} Kuri {i['kuri_share_of_keyed_epic_commits_pct']}%  modules {[m['kuri_share_pct'] for m in i['modules']]}")


if __name__ == "__main__":
    main()
