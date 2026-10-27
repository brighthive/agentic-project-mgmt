"""Collect year-one before/after metrics from the GitHub org into one JSON file."""

import json
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ORG = "brighthive"
KURI_LOGIN = "drchinca"
START = datetime(2025, 10, 23, tzinfo=timezone.utc)
END = datetime(2026, 10, 23, tzinfo=timezone.utc)
BASELINE_START = datetime(2024, 10, 23, tzinfo=timezone.utc)
PR_LIMIT = 5000
RELEASE_LIMIT = 1000
WORKERS = 6
OUTPUT_PATH = Path(__file__).parent / "data" / "github.json"
PR_FIELDS = "number,title,author,createdAt,mergedAt,additions,deletions,changedFiles,baseRefName,isDraft"


@dataclass(frozen=True)
class WindowSpec:
    name: str
    start: datetime
    end: datetime


WINDOWS = (
    WindowSpec(name="before", start=BASELINE_START, end=START),
    WindowSpec(name="after", start=START, end=END),
)


def run_gh(*, args: list[str]) -> str:
    """Run a gh command and return stdout, raising on failure."""
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def parse_ts(*, value: str | None) -> datetime | None:
    """Parse a GitHub ISO timestamp, or None when absent."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def list_repos() -> list[dict]:
    """List non-archived org repos."""
    raw = run_gh(args=["repo", "list", ORG, "--limit", "500", "--json", "name,createdAt,pushedAt,isArchived,isFork"])
    return [r for r in json.loads(raw) if not r["isArchived"]]


def list_merged_prs(*, repo: str) -> list[dict]:
    """Fetch merged PRs for one repo."""
    raw = run_gh(
        args=["pr", "list", "--repo", f"{ORG}/{repo}", "--state", "merged", "--limit", str(PR_LIMIT), "--json", PR_FIELDS]
    )
    return json.loads(raw)


def list_release_dates(*, repo: str) -> list[datetime]:
    """Fetch publish dates of GitHub releases for one repo."""
    raw = run_gh(
        args=["release", "list", "--repo", f"{ORG}/{repo}", "--limit", str(RELEASE_LIMIT), "--json", "publishedAt"]
    )
    return [ts for item in json.loads(raw) if (ts := parse_ts(value=item["publishedAt"]))]


def in_window(*, ts: datetime | None, window: WindowSpec) -> bool:
    """True when ts falls in [start, end)."""
    return ts is not None and window.start <= ts < window.end


def summarize_window(*, prs: list[dict], releases: list[datetime], window: WindowSpec) -> dict:
    """Aggregate PR and release stats for one window."""
    merged = [p for p in prs if in_window(ts=parse_ts(value=p["mergedAt"]), window=window)]
    kuri = [p for p in merged if (p["author"] or {}).get("login") == KURI_LOGIN]
    hours = [
        (parse_ts(value=p["mergedAt"]) - parse_ts(value=p["createdAt"])).total_seconds() / 3600
        for p in merged
    ]
    authors: dict[str, int] = {}
    for p in merged:
        login = (p["author"] or {}).get("login", "unknown")
        authors[login] = authors.get(login, 0) + 1
    return {
        "prs_merged": len(merged),
        "prs_merged_by_kuri": len(kuri),
        "lines_added": sum(p["additions"] for p in merged),
        "lines_deleted": sum(p["deletions"] for p in merged),
        "lines_added_by_kuri": sum(p["additions"] for p in kuri),
        "median_hours_to_merge": round(statistics.median(hours), 1) if hours else None,
        "releases_published": sum(1 for r in releases if in_window(ts=r, window=window)),
        "distinct_authors": len(authors),
        "top_authors": dict(sorted(authors.items(), key=lambda kv: -kv[1])[:8]),
    }


def collect_repo(*, repo: dict) -> dict:
    """Collect both windows for one repo."""
    name = repo["name"]
    prs = list_merged_prs(repo=name)
    releases = list_release_dates(repo=name)
    return {
        "repo": name,
        "created_at": repo["createdAt"],
        "windows": {w.name: summarize_window(prs=prs, releases=releases, window=w) for w in WINDOWS},
    }


def total_windows(*, repos: list[dict]) -> dict:
    """Sum numeric stats across repos per window."""
    totals: dict[str, dict] = {}
    for window in WINDOWS:
        rows = [r["windows"][window.name] for r in repos]
        totals[window.name] = {
            key: sum(row[key] for row in rows)
            for key in ("prs_merged", "prs_merged_by_kuri", "lines_added", "lines_deleted", "lines_added_by_kuri", "releases_published")
        }
        totals[window.name]["repos_with_merges"] = sum(1 for row in rows if row["prs_merged"] > 0)
    return totals


def main() -> None:
    """Collect, aggregate and write the JSON file."""
    repos = list_repos()
    print(f"{len(repos)} repos", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        collected = list(pool.map(lambda r: collect_repo(repo=r), repos))
    active = [r for r in collected if any(r["windows"][w.name]["prs_merged"] for w in WINDOWS)]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "org": ORG,
        "kuri_login": KURI_LOGIN,
        "windows": {w.name: {"start": w.start.isoformat(), "end": w.end.isoformat()} for w in WINDOWS},
        "totals": total_windows(repos=active),
        "repos": sorted(active, key=lambda r: -r["windows"]["after"]["prs_merged"]),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload["totals"], indent=2))


if __name__ == "__main__":
    main()
