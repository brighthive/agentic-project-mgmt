#!/usr/bin/env python3
"""
Post Sprint Release Notes to Slack

Usage:
    python post_to_slack.py --sprint 1
    python post_to_slack.py --sprint 2 --webhook-url <webhook>

Environment Variables:
    SLACK_WEBHOOK_URL: Slack webhook URL for posting
    SLACK_CHANNEL: Slack channel (e.g., #engineering, #releases)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


def create_slack_message(release_notes_path: Path) -> dict:
    """Create Slack message blocks from release notes."""

    # Read the marketing release notes
    with open(release_notes_path) as f:
        content = f.read()

    # Create Slack blocks (using Block Kit format)
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚀 BrightHive Sprint 1 Release",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Release Date:* January 20, 2026\n*Sprint Period:* January 13-20, 2026"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🛡️ Enhanced Security & Trust*\n• ✓ Addressed all critical security vulnerabilities\n• ✓ Fixed cross-workspace access controls\n• ✓ Removed debug information from production builds\n• ✓ Updated security dependencies"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🤖 BrightAgent Intelligence Upgrades*\n• Real-time cost tracking for every AI operation\n• Multi-provider support with optimized pricing\n• Faster dependency management (5x faster)\n• Improved testing infrastructure"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📊 Coming Soon: Data Lake Context Engineering*\n• Automatic schema versioning and lineage tracking\n• Cross-organization data matching and discovery\n• Enhanced metadata capture from all data sources"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*📈 By the Numbers*\n• Security Issues Resolved: *100%* of critical findings\n• Sprint Velocity: *78 story points*\n• Team Efficiency: *72%* completion rate"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🎯 What's Next: Sprint 2 Preview*\n• Projects Feature (v0)\n• Web App UX Improvements\n• Automated Onboarding\n• Connector Enhancements"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "📚 <https://github.com/brighthive/brighthive/blob/main/project/sprint/sprint-1/SPRINT_1_RELEASE_NOTES.md|Technical Release Notes> | <https://github.com/brighthive/brighthive/blob/main/project/sprint/sprint-1/SPRINT_1_MARKETING_RELEASE_NOTES.md|Marketing Release Notes>"
                }
            ]
        }
    ]

    return {
        "blocks": blocks,
        "text": "BrightHive Sprint 1 Release - January 20, 2026"  # Fallback text
    }


def post_to_slack(webhook_url: str, message: dict) -> bool:
    """Post message to Slack via webhook."""
    try:
        response = requests.post(
            webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        print("✓ Successfully posted to Slack")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error posting to Slack: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Post Sprint Release Notes to Slack"
    )
    parser.add_argument(
        "--sprint",
        type=int,
        help="Sprint number (e.g., 1, 2, 3)",
        default=1
    )
    parser.add_argument(
        "--webhook-url",
        help="Slack webhook URL (or set SLACK_WEBHOOK_URL env var)",
        default=os.getenv("SLACK_WEBHOOK_URL")
    )
    parser.add_argument(
        "--channel",
        help="Slack channel (optional, for display purposes)",
        default=os.getenv("SLACK_CHANNEL", "#releases")
    )
    parser.add_argument(
        "--release-notes",
        help="Path to marketing release notes (auto-detected if not provided)",
        default=None
    )

    args = parser.parse_args()

    # Auto-detect release notes path if not provided
    if args.release_notes is None:
        args.release_notes = (
            Path(__file__).parent.parent
            / f"sprint-{args.sprint}"
            / f"SPRINT_{args.sprint}_MARKETING_RELEASE_NOTES.md"
        )

    if not args.webhook_url:
        print("Error: Slack webhook URL not provided")
        print("Set SLACK_WEBHOOK_URL environment variable or use --webhook-url")
        print("\nTo create a webhook:")
        print("1. Go to https://api.slack.com/apps")
        print("2. Select your app (or create new)")
        print("3. Go to 'Incoming Webhooks'")
        print("4. Activate webhooks and add to workspace")
        print("5. Copy the webhook URL")
        sys.exit(1)

    release_notes_path = Path(args.release_notes)
    if not release_notes_path.exists():
        print(f"Error: Release notes not found at {release_notes_path}")
        sys.exit(1)

    print(f"Posting Sprint {args.sprint} release notes to Slack ({args.channel})...")
    message = create_slack_message(release_notes_path)

    success = post_to_slack(args.webhook_url, message)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
