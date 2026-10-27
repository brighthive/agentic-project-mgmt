"""Tie Jira epics to the commits that reference their tickets and measure Kuri's share of each."""

import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data"
OUTPUT_PATH = DATA_DIR / "milestones.json"
REPOS = (
    "brightbot", "brighthive-platform-core", "brighthive-webapp", "brighthive-e2e", "brightbot-slack-server",
    "brightagent-v3", "brighthive-admin", "brighthive-data-organization-cdk",
    "brighthive-data-workspace-cdk", "brightagent-engineering-runner",
)
REFS = ("origin/develop", "origin/staging", "origin/master", "origin/main", "origin/production")
KURI_RE = re.compile(r"kuri|chinca|drchinca|bado", re.IGNORECASE)
KEY_RE = re.compile(r"\bBH-(\d+)\b")
RECORD_SEP, FIELD_SEP = "\x1e", "\x1f"
MIN_COMMITS_FOR_LED = 10
LED_SHARE_PCT = 50.0


def commits_of(*, repo: Path) -> list[dict]:
    """Non-merge commits on the integration refs with author, date and referenced BH keys."""
    refs = [r for r in REFS if subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", "-q", r], capture_output=True).returncode == 0]
    if not refs:
        return []
    fmt = FIELD_SEP.join(["%H", "%aI", "%an", "%ae", "%B"]) + RECORD_SEP
    out = subprocess.run(["git", "-C", str(repo), "log", *refs, "--no-merges", f"--format={fmt}"], capture_output=True, text=True, check=True).stdout
    rows = []
    for record in out.split(RECORD_SEP):
        parts = record.strip("\n").split(FIELD_SEP)
        if len(parts) != 5:
            continue
        sha, date, name, email, body = parts
        rows.append({"sha": sha, "date": date[:10], "kuri": bool(KURI_RE.search(f"{name} {email}")), "keys": {f"BH-{n}" for n in KEY_RE.findall(body)}})
    return rows


def main() -> None:
    """Aggregate commits per epic and write the milestone file."""
    issues = {i["key"]: i for i in json.loads((DATA_DIR / "jira_issues.json").read_text())}
    epic_of = {k: (i["key"] if i["type"] == "Epic" else i["parent"]) for k, i in issues.items()}
    agg: dict[str, dict] = defaultdict(lambda: {"commits": set(), "kuri_commits": set(), "dates": [], "repos": set(), "keys": set()})
    for name in REPOS:
        repo = WORKSPACE / name
        if not repo.exists():
            continue
        for commit in commits_of(repo=repo):
            for key in commit["keys"]:
                epic = epic_of.get(key)
                if not epic:
                    continue
                a, uid = agg[epic], f"{name}:{commit['sha']}"
                a["commits"].add(uid)
                a["dates"].append(commit["date"])
                a["repos"].add(name)
                a["keys"].add(key)
                if commit["kuri"]:
                    a["kuri_commits"].add(uid)
    rows = []
    for epic, a in agg.items():
        children = [i for i in issues.values() if i["parent"] == epic]
        total, kuri = len(a["commits"]), len(a["kuri_commits"])
        share = round(100 * kuri / total, 1) if total else 0.0
        rows.append({
            "epic": epic, "summary": issues[epic]["summary"], "jira_status": issues[epic]["status"],
            "children": len(children), "children_done": sum(c["state"] == "done" for c in children),
            "tickets_with_code": len(a["keys"]), "commits": total, "kuri_commits": kuri, "kuri_share_pct": share,
            "kuri_led": total >= MIN_COMMITS_FOR_LED and share >= LED_SHARE_PCT,
            "first_commit": min(a["dates"]), "last_commit": max(a["dates"]), "repos": sorted(a["repos"]), "jira_summary_raw": issues[epic]["summary"],
        })
    rows.sort(key=lambda r: -r["commits"])
    payload = {
        "method": "An epic's commits (code repos only, documentation repos excluded) are non-merge commits on develop, staging or a production branch whose message contains the key of the epic or of one of its child tickets. Kuri's commits are matched by author name or email. Kuri-led means 10+ commits and a 50%+ share. Commits are evidence of merged work, not proof an epic is complete.",
        "epics_with_code": len(rows), "kuri_led_epics": sum(r["kuri_led"] for r in rows), "epics": rows,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"{len(rows)} epics with code, {payload['kuri_led_epics']} Kuri-led")
    for r in rows[:20]:
        print(f"{r['epic']:8} {r['commits']:>4} commits  kuri {r['kuri_share_pct']:>5}%  {r['first_commit']}..{r['last_commit']}  {r['summary'][:60]}")


if __name__ == "__main__":
    main()
