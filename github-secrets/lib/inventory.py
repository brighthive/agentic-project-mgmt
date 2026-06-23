"""GitHub Actions secrets inventory via the `gh` CLI.

IMPORTANT — GitHub Actions secrets are WRITE-ONLY by design. The API (and `gh`)
expose secret NAMES + last-updated timestamps only; secret VALUES can never be
read back. So this module inventories names/metadata for drift + audit, and the
AWS Secrets Manager vault remains the source of truth for values. Pushing a
value INTO GitHub (gh secret set, from the vault) is a separate, deliberate op.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class GitHubSecret:
    """One GitHub Actions secret as the API exposes it (NAME + timestamps only)."""

    name: str
    updated_at: str
    visibility: str = "repo"  # "repo" | "organization" | "environment"


@dataclass(frozen=True, slots=True)
class RepoSecretInventory:
    """Inventory of a single repo's Actions secrets."""

    repo: str
    captured_utc: str
    secret_count: int
    secrets: list[GitHubSecret]


def _gh_secret_list(*, repo: str, env: str | None = None) -> list[dict]:
    """Call `gh secret list --json name,updatedAt`; return [] on any failure."""
    cmd = ["gh", "secret", "list", "--repo", repo, "--json", "name,updatedAt"]
    if env:
        cmd += ["--env", env]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        return json.loads(out.stdout or "[]")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def inventory_repo(*, repo: str) -> RepoSecretInventory:
    """Inventory a repo's secret names + last-updated timestamps (no values)."""
    raw = _gh_secret_list(repo=repo)
    secrets = [
        GitHubSecret(name=s["name"], updated_at=s.get("updatedAt", ""))
        for s in sorted(raw, key=lambda s: s["name"])
    ]
    return RepoSecretInventory(
        repo=repo,
        captured_utc=datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        secret_count=len(secrets),
        secrets=secrets,
    )


def inventory_to_dict(inv: RepoSecretInventory) -> dict:
    return {**asdict(inv), "secrets": [asdict(s) for s in inv.secrets]}


def diff_inventories(old: RepoSecretInventory, new: RepoSecretInventory) -> dict:
    """Name-level drift between two inventories of the same repo."""
    old_names = {s.name for s in old.secrets}
    new_names = {s.name for s in new.secrets}
    old_ts = {s.name: s.updated_at for s in old.secrets}
    new_ts = {s.name: s.updated_at for s in new.secrets}
    return {
        "repo": new.repo,
        "added": sorted(new_names - old_names),
        "removed": sorted(old_names - new_names),
        "rotated": sorted(
            n for n in (old_names & new_names) if old_ts[n] != new_ts[n]
        ),
    }
