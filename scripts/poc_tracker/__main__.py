"""CLI entry: `python -m scripts.poc_tracker --client <slug> [--no-slack]`.

Reads `clients/trials/<slug>/poc.yaml` and writes
`clients/trials/<slug>/TRACKER.md`. Posts a state + diff message to the
configured Slack channel unless `--no-slack` is set.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from .github_client import fetch_prs_referencing_tickets
from .jira_client import fetch_tickets
from .loader import load_config
from .renderer import compute_phase_progress, render_tracker
from .slack_notify import post_to_slack
from .snapshot import build_snapshot, diff_snapshots, load_snapshot, save_snapshot

logging.basicConfig(level=logging.INFO, format="[tracker] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _check_preconditions() -> int:
    if not shutil.which("gh"):
        logger.error("`gh` CLI not found on PATH. Run `gh auth login` first.")
        return 127
    import os
    env = {**os.environ}
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            check=True, capture_output=True, text=True, timeout=10, env=env,
        )
    except subprocess.CalledProcessError as exc:
        logger.error("`gh` not authenticated. Run `gh auth login`. (%s)", exc.stderr.strip())
        return 126
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="poc-tracker",
        description="Refresh clients/trials/<slug>/TRACKER.md from Jira + GitHub PRs.",
    )
    parser.add_argument(
        "--client", "-c", default="longaeva",
        help="Client slug — must match a directory under clients/trials/",
    )
    parser.add_argument("--no-slack", action="store_true", help="Skip Slack post.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without writing files.",
    )
    args = parser.parse_args(argv)

    precond = _check_preconditions()
    if precond:
        return precond

    try:
        config = load_config(slug=args.client, repo_root=REPO_ROOT)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        return 2

    logger.info("Client: %s · Epic: %s · Repos: %d", config.slug, config.epic, len(config.repos))

    logger.info("Fetching Jira tickets…")
    tickets = fetch_tickets(config=config)
    logger.info("Got %d tickets in scope.", len(tickets))

    ticket_keys = {t.key for t in tickets}
    logger.info("Fetching PRs referencing %d ticket keys…", len(ticket_keys))
    pr_map = fetch_prs_referencing_tickets(ticket_keys=ticket_keys, repos=config.repos)
    pr_count = sum(len(prs) for prs in pr_map.values())
    logger.info("Linked %d PR references across %d repos.", pr_count, len(config.repos))

    tracker_path = REPO_ROOT / config.tracker_path
    snapshot_path = REPO_ROOT / config.snapshot_path
    existing_text = tracker_path.read_text() if tracker_path.exists() else None

    new_content = render_tracker(
        config=config,
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
        len(diff.new_tickets), len(diff.status_changes),
        len(diff.new_prs), len(diff.merged_prs),
    )

    if not args.no_slack:
        phase_progress = compute_phase_progress(
            config=config, tickets=tickets, pr_map=pr_map
        )
        posted = post_to_slack(
            config=config, diff=diff, tickets=tickets,
            pr_map=pr_map, phase_progress=phase_progress,
        )
        logger.info("Slack: %s", "posted" if posted else "skipped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
