"""Collect GitHub Actions (CI/CD) health per repo, before vs after, into one JSON file."""

import json
import statistics
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ORG = "brighthive"
REPOS = (
    "brightbot", "brighthive-platform-core", "brighthive-webapp", "brighthive-e2e",
    "brightbot-slack-server", "agentic-project-mgmt", "brightagent-v3", "brighthive-admin",
    "brighthive-data-organization-cdk", "brighthive-data-workspace-cdk",
)
START = datetime(2025, 10, 23, tzinfo=timezone.utc)
END = datetime(2026, 10, 23, tzinfo=timezone.utc)
BASELINE_START = datetime(2024, 10, 23, tzinfo=timezone.utc)
WINDOWS = {"before": (BASELINE_START, START), "after": (START, END)}
DEPLOY_WORDS = ("deploy", "release", "promote")
E2E_WORDS = ("e2e", "health")
RATE_LIMIT_PAUSE_S = 120
MAX_RETRIES = 30
WORKERS = 3
API_RESULT_CAP = 1000
MIN_SPLIT_SECONDS = 3600
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "cicd.json"
RUN_JQ = ".workflow_runs[] | [.name, (.conclusion // \"none\"), .created_at, (.run_started_at // .created_at), .updated_at, .event] | @tsv"


def run_gh(*, args: list[str]) -> str:
    """Run a gh command, pausing and retrying while GitHub rate-limits us."""
    for _ in range(MAX_RETRIES):
        result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout
        if "rate limit" not in result.stderr.lower():
            raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()[:300]}")
        print(f"rate limited; sleeping {RATE_LIMIT_PAUSE_S}s", file=sys.stderr)
        time.sleep(RATE_LIMIT_PAUSE_S)
    raise RuntimeError("rate limit retries exhausted")


def parse_ts(*, value: str) -> datetime:
    """Parse a GitHub timestamp."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_range(*, repo: str, lo: datetime, hi: datetime) -> list[dict]:
    """Fetch completed runs in [lo, hi), halving the range whenever the API result cap is hit."""
    created = f"{lo.isoformat(timespec='seconds')}..{hi.isoformat(timespec='seconds')}".replace("+00:00", "Z")
    raw = run_gh(args=["api", "--paginate", f"repos/{ORG}/{repo}/actions/runs?status=completed&per_page=100&created={created}", "--jq", RUN_JQ])
    runs = []
    for line in raw.splitlines():
        name, conclusion, created_at, started_at, updated_at, event = line.split("\t")
        minutes = (parse_ts(value=updated_at) - parse_ts(value=started_at)).total_seconds() / 60
        runs.append({"name": name, "conclusion": conclusion, "created": created_at, "minutes": minutes, "event": event})
    if len(runs) < API_RESULT_CAP or (hi - lo).total_seconds() <= MIN_SPLIT_SECONDS:
        return runs
    mid = lo + (hi - lo) / 2
    return fetch_range(repo=repo, lo=lo, hi=mid) + fetch_range(repo=repo, lo=mid, hi=hi)


def fetch_runs(*, repo: str, window: str) -> list[dict]:
    """Fetch completed workflow runs created in a window."""
    lo, hi = WINDOWS[window]
    return fetch_range(repo=repo, lo=lo, hi=hi)


def pct(*, part: int, whole: int) -> float | None:
    """Percentage rounded to 1 decimal."""
    return round(100 * part / whole, 1) if whole else None


def summarize(*, runs: list[dict]) -> dict:
    """Aggregate run health for one repo and window."""
    decided = [r for r in runs if r["conclusion"] in ("success", "failure")]
    deploys = [r for r in decided if any(w in r["name"].lower() for w in DEPLOY_WORDS)]
    e2e = [r for r in decided if any(w in r["name"].lower() for w in E2E_WORDS)]
    minutes = [r["minutes"] for r in decided]
    return {
        "runs_completed": len(runs),
        "pct_success_of_decided": pct(part=sum(r["conclusion"] == "success" for r in decided), whole=len(decided)),
        "median_minutes": round(statistics.median(minutes), 1) if minutes else None,
        "distinct_workflows": len({r["name"] for r in runs}),
        "pull_request_runs": sum(r["event"] == "pull_request" for r in runs),
        "deploy_runs": len(deploys),
        "deploy_success": sum(r["conclusion"] == "success" for r in deploys),
        "e2e_or_health_runs": len(e2e),
        "e2e_or_health_success": sum(r["conclusion"] == "success" for r in e2e),
        "runs_by_month": dict(sorted(Counter(r["created"][:7] for r in runs).items())),
        "top_workflows": dict(Counter(r["name"] for r in runs).most_common(8)),
    }


def collect_repo(*, repo: str) -> dict:
    """Collect both windows for one repo."""
    out = {w: summarize(runs=fetch_runs(repo=repo, window=w)) for w in WINDOWS}
    print(f"done {repo}: {out['before']['runs_completed']} -> {out['after']['runs_completed']} runs", file=sys.stderr)
    return out


def main() -> None:
    """Collect all repos and write the CI/CD file."""
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(lambda r: collect_repo(repo=r), REPOS))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Only completed runs; success% is success/(success+failure), cancelled and skipped excluded.",
        "repos": dict(zip(REPOS, results)),
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
