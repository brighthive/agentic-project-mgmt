"""CLI entry: `python -m scripts.longaeva_tracker [--no-slack]`.

Pipeline:
  1. Load env config.
  2. Fetch tickets from Jira and PRs from `gh`.
  3. Render TRACKER.md (preserving manual sections).
  4. Compute diff vs prior snapshot, post to Slack if non-empty.
  5. Persist new snapshot.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from .config import (
    LONGAEVA_REPOS,
    SNAPSHOT_RELATIVE_PATH,
    TRACKER_GITHUB_URL,
    TRACKER_RELATIVE_PATH,
    load_from_env,
)
from .github_client import fetch_prs_referencing_tickets
from .jira_client import fetch_longaeva_tickets
from .renderer import render_tracker
from .slack_notify import post_to_slack_if_changed
from .snapshot import build_snapshot, diff_snapshots, load_snapshot, save_snapshot

logging.basicConfig(level=logging.INFO, format="[tracker] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _check_preconditions() -> int:
    """Verify `gh` is on PATH and authenticated. Return non-zero if anything's off."""
    if not shutil.which("gh"):
        logger.error(
            "`gh` CLI not found on PATH. Install with `brew install gh` and run "
            "`gh auth login` to authenticate."
        )
        return 127
    # Strip token env so `gh` falls back to the keyring auth — same as the PR
    # fetcher does. Local shells often have a fine-grained PAT that doesn't
    # cover all 4 repos.
    import os
    env = {**os.environ}
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        logger.error(
            "`gh` is installed but not authenticated. Run `gh auth login`. "
            "(stderr: %s)",
            exc.stderr.strip(),
        )
        return 126
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="longaeva-tracker",
        description="Refresh clients/trials/longaeva/TRACKER.md.",
    )
    parser.add_argument("--no-slack", action="store_true", help="Skip Slack post.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files.",
    )
    args = parser.parse_args(argv)

    precond = _check_preconditions()
    if precond:
        return precond

    try:
        config = load_from_env()
    except ValueError as exc:
        logger.error("%s", exc)
        return 2

    logger.info("Fetching Jira tickets…")
    tickets = fetch_longaeva_tickets(config=config)
    logger.info("Got %d tickets in scope.", len(tickets))

    ticket_keys = {t.key for t in tickets}
    logger.info("Fetching PRs referencing %d ticket keys…", len(ticket_keys))
    pr_map = fetch_prs_referencing_tickets(ticket_keys=ticket_keys)
    pr_count = sum(len(prs) for prs in pr_map.values())
    logger.info("Linked %d PR references across %d repos.", pr_count, len(LONGAEVA_REPOS))

    tracker_path = REPO_ROOT / TRACKER_RELATIVE_PATH
    snapshot_path = REPO_ROOT / SNAPSHOT_RELATIVE_PATH

    existing_text = tracker_path.read_text() if tracker_path.exists() else None
    new_content = render_tracker(
        tickets=tickets,
        pr_map=pr_map,
        existing_text=existing_text,
    )

    if args.dry_run:
        logger.info("--dry-run: would write %d bytes to %s", len(new_content), tracker_path)
        return 0

    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    tracker_path.write_text(new_content)
    logger.info("Wrote %s (%d bytes).", tracker_path, len(new_content))

    previous = load_snapshot(path=snapshot_path)
    current = build_snapshot(tickets=tickets, pr_map=pr_map)
    diff = diff_snapshots(previous=previous, current=current)
    save_snapshot(snapshot=current, path=snapshot_path)
    logger.info(
        "Diff: %d new ticket(s), %d status change(s), %d new PR(s), %d merged PR(s).",
        len(diff.new_tickets),
        len(diff.status_changes),
        len(diff.new_prs),
        len(diff.merged_prs),
    )

    if not args.no_slack:
        posted = post_to_slack_if_changed(
            diff=diff, config=config, tracker_url=TRACKER_GITHUB_URL
        )
        logger.info("Slack: %s", "posted" if posted else "skipped (empty diff or no token)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
