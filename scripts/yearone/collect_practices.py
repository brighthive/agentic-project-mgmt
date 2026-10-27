"""Measure engineering-practice adoption (commits, PRs, reviews, releases) before vs after."""

import json
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ORG = "brighthive"
KURI_LOGIN = "drchinca"
START = datetime(2025, 10, 23, tzinfo=timezone.utc)
END = datetime(2026, 10, 23, tzinfo=timezone.utc)
BASELINE_START = datetime(2024, 10, 23, tzinfo=timezone.utc)
PAGE_LIMIT = 20
WORKERS = 2
RATE_LIMIT_PAUSE_S = 120
MAX_RETRIES = 30
CACHE_DIR = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / ".cache"
MIN_BODY_CHARS = 200
BASE_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "github.json"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "practices.json"
PR_FIELDS = "number,title,body,author,createdAt,mergedAt,headRefName,isDraft,reviews,assignees,reviewRequests,commits,mergedBy"

CONVENTIONAL_TYPES = "feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert"
CONVENTIONAL_RE = re.compile(rf"^({CONVENTIONAL_TYPES})(\([^)]+\))?!?: .+", re.IGNORECASE)
TICKET_RE = re.compile(r"\b[A-Z]{2,6}-\d+\b")
TICKET_BRANCH_RE = re.compile(r"^[^/]+/[A-Za-z]{2,6}-\d+/.+")
BOT_SUFFIXES = ("[bot]",)
BOT_PREFIX = "app/"

WINDOWS = {"before": (BASELINE_START, START), "after": (START, END)}
AUDIENCES = ("everyone", "kuri", "everyone_else")


def run_gh(*, args: list[str]) -> str:
    """Run a gh command, pausing and retrying while GitHub rate-limits us."""
    for _ in range(MAX_RETRIES):
        result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout
        if "rate limit" not in result.stderr.lower():
            raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
        print(f"rate limited; sleeping {RATE_LIMIT_PAUSE_S}s", file=sys.stderr)
        time.sleep(RATE_LIMIT_PAUSE_S)
    raise RuntimeError("rate limit retries exhausted")


def parse_ts(*, value: str | None) -> datetime | None:
    """Parse a GitHub ISO timestamp, or None when absent."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def is_bot(*, login: str) -> bool:
    """True for dependabot-style accounts."""
    return login.startswith(BOT_PREFIX) or login.endswith(BOT_SUFFIXES)


def has_human_approval(*, pr: dict, author: str) -> bool:
    """True when someone other than the author approved."""
    return any(r["state"] == "APPROVED" and r["author"]["login"] != author for r in pr["reviews"])


def has_human_review(*, pr: dict, author: str) -> bool:
    """True when someone other than the author left any review."""
    return any(r["author"]["login"] != author for r in pr["reviews"])


def score_pr(*, pr: dict) -> dict:
    """Score one PR against each practice."""
    author = (pr["author"] or {}).get("login", "unknown")
    commits = [c["messageHeadline"] for c in pr["commits"]]
    return {
        "conventional_title": bool(CONVENTIONAL_RE.match(pr["title"])),
        "ticket_in_title": bool(TICKET_RE.search(pr["title"])),
        "ticket_in_title_or_branch": bool(TICKET_RE.search(pr["title"]) or TICKET_RE.search(pr["headRefName"])),
        "structured_branch": bool(TICKET_BRANCH_RE.match(pr["headRefName"])),
        "described_body": len((pr["body"] or "").strip()) >= MIN_BODY_CHARS,
        "human_approval": has_human_approval(pr=pr, author=author),
        "human_review": has_human_review(pr=pr, author=author),
        "assignee_set": bool(pr["assignees"]),
        "commit_count": len(commits),
        "conventional_commits": sum(1 for c in commits if CONVENTIONAL_RE.match(c)),
    }


def audience_of(*, author: str) -> tuple[str, ...]:
    """Which audience buckets a PR author belongs to."""
    return ("everyone", "kuri") if author == KURI_LOGIN else ("everyone", "everyone_else")


def pct(*, part: int, whole: int) -> float | None:
    """Percentage rounded to 1 decimal, None if whole is zero."""
    return round(100 * part / whole, 1) if whole else None


def aggregate(*, scored: list[dict]) -> dict:
    """Roll scored PRs into practice percentages."""
    n = len(scored)
    commits = sum(s["commit_count"] for s in scored)
    flags = (
        "conventional_title", "ticket_in_title", "ticket_in_title_or_branch", "structured_branch",
        "described_body", "human_approval", "human_review", "assignee_set",
    )
    out = {"prs": n, **{f"pct_{f}": pct(part=sum(s[f] for s in scored), whole=n) for f in flags}}
    out["pct_conventional_commits"] = pct(part=sum(s["conventional_commits"] for s in scored), whole=commits)
    return out


def fetch_merged_range(*, repo: str, lo: datetime, hi: datetime) -> list[dict]:
    """Fetch merged PRs in [lo, hi), halving the range whenever a page fills up."""
    query = f"merged:{lo.date().isoformat()}..{(hi - timedelta(days=1)).date().isoformat()}"
    raw = run_gh(args=["pr", "list", "--repo", f"{ORG}/{repo}", "--state", "merged", "--search", query,
                       "--limit", str(PAGE_LIMIT), "--json", PR_FIELDS])
    prs = json.loads(raw)
    if len(prs) < PAGE_LIMIT or (hi - lo).days <= 1:
        return prs
    mid = lo + (hi - lo) / 2
    return fetch_merged_range(repo=repo, lo=lo, hi=mid) + fetch_merged_range(repo=repo, lo=mid, hi=hi)


def collect_repo(*, repo: str) -> list[dict]:
    """Score one repo's merged PRs, resuming from a per-repo cache file."""
    cache_file = CACHE_DIR / f"{repo}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    rows = []
    for window, (lo, hi) in WINDOWS.items():
        for pr in fetch_merged_range(repo=repo, lo=lo, hi=hi):
            author = (pr["author"] or {}).get("login", "unknown")
            if not is_bot(login=author):
                rows.append({"repo": repo, "window": window, "author": author, "score": score_pr(pr=pr)})
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(rows))
    print(f"done {repo}: {len(rows)} PRs", file=sys.stderr)
    return rows


def release_cadence(*, repo: str) -> dict:
    """Release counts and median gap in days per window for one repo."""
    raw = run_gh(args=["release", "list", "--repo", f"{ORG}/{repo}", "--limit", "1000", "--json", "publishedAt,isPrerelease"])
    out: dict[str, dict] = {}
    for name, (lo, hi) in WINDOWS.items():
        stamps = sorted(t for r in json.loads(raw) if (t := parse_ts(value=r["publishedAt"])) and lo <= t < hi)
        gaps = [(b - a).days for a, b in zip(stamps, stamps[1:])]
        out[name] = {"releases": len(stamps), "median_gap_days": statistics.median(gaps) if gaps else None}
    return out


def main() -> None:
    """Score every active repo and write the practices file."""
    base = json.loads(BASE_PATH.read_text())
    repos = [r["repo"] for r in base["repos"]]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        per_repo = list(pool.map(lambda r: collect_repo(repo=r), repos))
        cadence = list(pool.map(lambda r: release_cadence(repo=r), repos))
    rows = [row for chunk in per_repo for row in chunk]
    summary: dict[str, dict] = {}
    for window in WINDOWS:
        summary[window] = {}
        for audience in AUDIENCES:
            scored = [r["score"] for r in rows if r["window"] == window and audience in audience_of(author=r["author"])]
            summary[window][audience] = aggregate(scored=scored)
    authors = {w: {} for w in WINDOWS}
    for row in rows:
        authors[row["window"]][row["author"]] = authors[row["window"]].get(row["author"], 0) + 1
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "definitions": {
            "conventional_title": f"PR title matches type(scope): description, type in {CONVENTIONAL_TYPES}",
            "ticket_in_title": "Jira-style key such as BH-123 in the PR title",
            "structured_branch": "branch named name/TICKET/description",
            "described_body": f"PR body of at least {MIN_BODY_CHARS} characters",
            "human_approval": "an APPROVED review by someone other than the author",
            "human_review": "any review by someone other than the author",
            "conventional_commits": "share of commit headlines inside merged PRs that are conventional",
        },
        "practices": summary,
        "contributors_with_10plus_prs": {w: sum(1 for c in a.values() if c >= 10) for w, a in authors.items()},
        "author_counts": {w: dict(sorted(a.items(), key=lambda kv: -kv[1])[:15]) for w, a in authors.items()},
        "release_cadence": {repo: c for repo, c in zip(repos, cadence) if c["before"]["releases"] or c["after"]["releases"]},
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps({"practices": summary, "contributors_with_10plus_prs": payload["contributors_with_10plus_prs"]}, indent=2))


if __name__ == "__main__":
    main()
