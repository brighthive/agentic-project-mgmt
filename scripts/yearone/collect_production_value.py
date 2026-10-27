"""Check which user-facing sprint release items reached production, and how much of each is Kuri's."""

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
WORKSPACE = REPO_ROOT.parent
SPRINT_DIR = REPO_ROOT / "jira" / "sprint"
OUTPUT_PATH = REPO_ROOT / "docs" / "year-one" / "data" / "production_value.json"
INTEGRATION_REFS = ("origin/develop", "origin/staging")
RELEASE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+\.\d+-release$")
KURI_RE = re.compile(r"kuri|chinca|drchinca|bado", re.IGNORECASE)
KEY_RE = re.compile(r"\bBH-\d+\b")
SKIPPED_SECTIONS = ("By the Numbers", "Team Contributions", "Sprint Health", "What's Next", "Known")
RECORD_SEP, FIELD_SEP = "\x1e", "\x1f"
STATUS_RELEASED, STATUS_ON_MAIN, STATUS_PRE_PRODUCTION, STATUS_NO_KEY, STATUS_NO_CODE = "released", "on_main", "pre_production", "no_ticket_key", "no_code_found"
STATUS_RANK = {STATUS_RELEASED: 4, STATUS_ON_MAIN: 3, STATUS_PRE_PRODUCTION: 2, STATUS_NO_CODE: 1, STATUS_NO_KEY: 0}
REPOS_BY_TAG = ("brighthive-platform-core", "brighthive-webapp")
REPOS_BY_MAIN = ("brightbot", "brightbot-slack-server", "brighthive-admin", "brighthive-data-organization-cdk", "brighthive-data-workspace-cdk", "brightagent-v3", "brighthive-e2e")
MAIN_REFS = ("origin/main", "origin/master")
KURI_LED_SHARE = 50.0


def git(*, repo: Path, args: list[str]) -> str:
    """Run a git command and return stdout, empty on failure."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def commits_on(*, repo: Path, revs: list[str]) -> list[dict]:
    """Non-merge commits reachable from revs, with referenced keys and Kuri flag."""
    if not revs:
        return []
    fmt = FIELD_SEP.join(["%H", "%aI", "%an", "%ae", "%B"]) + RECORD_SEP
    out = git(repo=repo, args=["log", *revs, "--no-merges", f"--format={fmt}"])
    rows = []
    for record in out.split(RECORD_SEP):
        parts = record.strip("\n").split(FIELD_SEP)
        if len(parts) == 5:
            sha, date, name, email, body = parts
            rows.append({"sha": sha, "date": date[:10], "kuri": bool(KURI_RE.search(f"{name} {email}")), "keys": set(KEY_RE.findall(body))})
    return rows


def existing(*, repo: Path, refs: tuple[str, ...]) -> list[str]:
    """Refs that exist in a repo."""
    return [r for r in refs if git(repo=repo, args=["rev-parse", "--verify", "-q", r]).strip()]


def production_commits(*, name: str) -> list[dict]:
    """Commits that count as production for a repo: release tags, or the main branch."""
    repo = WORKSPACE / name
    if name in REPOS_BY_TAG:
        tags = [t for t in git(repo=repo, args=["tag", "-l"]).split() if RELEASE_TAG_RE.match(t)]
        return commits_on(repo=repo, revs=tags)
    return commits_on(repo=repo, revs=existing(repo=repo, refs=MAIN_REFS))


def key_index(*, commits_by_repo: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Map each ticket key to the commits that mention it."""
    index: dict[str, list[dict]] = defaultdict(list)
    for repo, commits in commits_by_repo.items():
        for c in commits:
            for key in c["keys"]:
                index[key].append({**c, "repo": repo})
    return index


def parse_sprint_items() -> list[dict]:
    """User-facing sections of every sprint's marketing release notes."""
    items = []
    for path in sorted(SPRINT_DIR.glob("*/MARKETING_RELEASE_NOTES.md"), key=lambda p: int(p.parent.name)):
        sprint, text = int(path.parent.name), path.read_text()
        header = re.search(r"^# (.+)$", text, re.MULTILINE)
        window = re.search(r"\(([^)]*\d{4})\)", header.group(1)) if header else None
        for section in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
            title, _, body = section.partition("\n")
            if any(s.lower() in title.lower() for s in SKIPPED_SECTIONS):
                continue
            items.append({"sprint": sprint, "window": window.group(1) if window else "", "title": re.sub(r"^[^\w]+", "", title).strip(),
                          "keys": sorted(set(KEY_RE.findall(f"{title}\n{body}"))), "summary": " ".join(body.split())[:220]})
    return items


TICKET_LEVEL_SPRINTS = (6, 12, 13)
TICKET_LINE_RE = re.compile(r"\*\*(BH-\d+)\*\*\s*[\u2014-]\s*(.+)")


def parse_ticket_level_items() -> list[dict]:
    """Ticket lines from sprints whose technical notes list tickets instead of PR links."""
    items = []
    for sprint in TICKET_LEVEL_SPRINTS:
        path = SPRINT_DIR / str(sprint) / "RELEASE_NOTES.md"
        if not path.exists():
            continue
        for key, title in TICKET_LINE_RE.findall(path.read_text()):
            items.append({"sprint": sprint, "window": "", "title": title.strip()[:120], "keys": [key], "summary": ""})
    return items


def classify(*, item: dict, prod: dict[str, list[dict]], pre: dict[str, list[dict]], all_commits: dict[str, list[dict]]) -> dict:
    """Production status and Kuri share for one release item."""
    if not item["keys"]:
        return {**item, "status": STATUS_NO_KEY, "commits": 0, "kuri_share_pct": None, "first_production_date": None, "kuri_led": False, "production_repos": []}
    in_prod = [c for k in item["keys"] for c in prod.get(k, [])]
    in_pre = [c for k in item["keys"] for c in pre.get(k, [])]
    everything = {(c["repo"], c["sha"]): c for k in item["keys"] for c in all_commits.get(k, [])}.values()
    status = STATUS_RELEASED if any(c["repo"] in REPOS_BY_TAG for c in in_prod) else STATUS_ON_MAIN if in_prod else STATUS_PRE_PRODUCTION if in_pre else STATUS_NO_CODE
    unique = {(c["repo"], c["sha"]): c for c in everything}.values()
    kuri = sum(c["kuri"] for c in unique)
    share = round(100 * kuri / len(unique), 1) if unique else None
    return {**item, "status": status, "commits": len(unique), "kuri_share_pct": share,
            "first_production_date": min((c["date"] for c in in_prod), default=None),
            "kuri_led": bool(share is not None and share >= KURI_LED_SHARE), "production_repos": sorted({c["repo"] for c in in_prod})}


def main() -> None:
    """Classify every release item and write the production-value file."""
    names = REPOS_BY_TAG + REPOS_BY_MAIN
    prod = key_index(commits_by_repo={n: production_commits(name=n) for n in names})
    pre = key_index(commits_by_repo={n: commits_on(repo=WORKSPACE / n, revs=existing(repo=WORKSPACE / n, refs=INTEGRATION_REFS)) for n in names})
    allc = key_index(commits_by_repo={n: commits_on(repo=WORKSPACE / n, revs=existing(repo=WORKSPACE / n, refs=INTEGRATION_REFS + MAIN_REFS + ("origin/production",))) for n in names})
    items = [classify(item=i, prod=prod, pre=pre, all_commits=allc) for i in parse_sprint_items()]
    ticket_items = [classify(item=i, prod=prod, pre=pre, all_commits=allc) for i in parse_ticket_level_items()]
    by_status: dict[str, int] = defaultdict(int)
    for i in items:
        by_status[i["status"]] += 1
    payload = {
        "method": "Items are the user-facing sections of jira/sprint/N/MARKETING_RELEASE_NOTES.md (sprints 1 to 16). Production means: platform-core and webapp, a commit in a plain -release tag; other repos, a commit on main or master. Git shows released or on the production branch, not that the change is running. Kuri share is the share of commits mentioning the item's tickets, matched by author name or email.",
        "items": len(items), "by_status": dict(by_status),
        "released_and_kuri_led": sum(i["status"] in (STATUS_RELEASED, STATUS_ON_MAIN) and i["kuri_led"] for i in items),
        "sprints_covered": sorted({i["sprint"] for i in items}), "release_items": items,
        "ticket_level_sprints": list(TICKET_LEVEL_SPRINTS), "ticket_level_items": ticket_items,
        "ticket_level_status": dict(Counter(i["status"] for i in ticket_items)),
        "ticket_level_kuri_led_in_production": sum(i["kuri_led"] and i["status"] in (STATUS_RELEASED, STATUS_ON_MAIN) for i in ticket_items),
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, default=list))
    print(json.dumps({k: payload[k] for k in ("items", "by_status", "released_and_kuri_led", "ticket_level_status", "ticket_level_kuri_led_in_production")}))


if __name__ == "__main__":
    main()
