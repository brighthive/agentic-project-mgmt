"""Measure commit conventions, traceability, reverts and contributor ramp-up from local git."""

import collections
import json
import re
import statistics
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "commit_practices.json"
CORE_REPOS = {"brightbot": "origin/develop", "brighthive-platform-core": "origin/develop", "brighthive-webapp": "origin/develop"}
WINDOWS = {"before": ("2024-10-23", "2025-10-23"), "after": ("2025-10-23", "2026-10-23")}
MIN_COMMITS_FOR_CONTRIBUTOR = 10
RAMP_DAYS = 30
FIELD_SEP = "\x1f"
CONVENTIONAL_RE = re.compile(r"^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\([^)]+\))?!?: ", re.IGNORECASE)
TICKET_RE = re.compile(r"\b[A-Z]{2,6}-\d+\b")
REVERT_RE = re.compile(r"^revert\b|^Revert \"", re.IGNORECASE)
HOTFIX_RE = re.compile(r"hotfix", re.IGNORECASE)


def git_log(*, repo: str, ref: str, extra: list[str]) -> list[list[str]]:
    """Non-merge commits as [email, author-date, subject] rows."""
    out = subprocess.run(["git", "-C", str(WORKSPACE / repo), "log", ref, "--no-merges", *extra, f"--format=%ae{FIELD_SEP}%aI{FIELD_SEP}%s"],
                         capture_output=True, text=True, check=True).stdout
    return [line.split(FIELD_SEP) for line in out.splitlines() if line]


def pct(*, part: int, whole: int) -> float | None:
    """Percentage rounded to 1 decimal."""
    return round(100 * part / whole, 1) if whole else None


def commit_profile(*, window: str) -> dict:
    """Convention, traceability, revert and hotfix rates across the core repos."""
    since, until = WINDOWS[window]
    subjects = [row[2] for repo, ref in CORE_REPOS.items() for row in git_log(repo=repo, ref=ref, extra=[f"--since={since}", f"--until={until}"])]
    typed = [m.group(1).lower() for s in subjects if (m := CONVENTIONAL_RE.match(s))]
    total = len(subjects)
    return {
        "commits": total,
        "pct_conventional": pct(part=len(typed), whole=total),
        "pct_with_ticket_key": pct(part=sum(bool(TICKET_RE.search(s)) for s in subjects), whole=total),
        "pct_reverts": pct(part=sum(bool(REVERT_RE.match(s)) for s in subjects), whole=total),
        "pct_hotfix": pct(part=sum(bool(HOTFIX_RE.search(s)) for s in subjects), whole=total),
        "type_mix_of_conventional": {t: pct(part=c, whole=len(typed)) for t, c in collections.Counter(typed).most_common(6)},
    }


def contributor_ramp(*, window: str) -> dict:
    """Commits in the first 30 days for contributors whose first commit falls in the window."""
    since, until = WINDOWS[window]
    ramps = []
    for repo, ref in CORE_REPOS.items():
        by_author: dict[str, list[datetime]] = collections.defaultdict(list)
        for email, stamp, _ in git_log(repo=repo, ref=ref, extra=[]):
            by_author[email].append(datetime.fromisoformat(stamp))
        for stamps in by_author.values():
            first = min(stamps)
            if since <= first.date().isoformat() < until and len(stamps) >= MIN_COMMITS_FOR_CONTRIBUTOR:
                ramps.append(sum((t - first).days < RAMP_DAYS for t in stamps))
    return {"new_contributors": len(ramps), "median_commits_first_30_days": statistics.median(ramps) if ramps else None, "values": sorted(ramps)}


def main() -> None:
    """Write the commit-practice file."""
    payload = {
        "method": "Non-merge commits on origin/develop of brightbot, brighthive-platform-core and brighthive-webapp. Ramp-up counts contributors with 10+ commits whose first commit falls in the window; authors are matched by email, so one person with two emails counts twice.",
        "windows": WINDOWS,
        "commit_profile": {w: commit_profile(window=w) for w in WINDOWS},
        "contributor_ramp": {w: contributor_ramp(window=w) for w in WINDOWS},
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps({k: payload[k] for k in ("commit_profile", "contributor_ramp")}, indent=2))


if __name__ == "__main__":
    main()
