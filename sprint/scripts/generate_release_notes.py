#!/usr/bin/env python3
"""
Automated Sprint Release Notes Generator

Generates comprehensive release notes from:
- Git commit history across all repos
- Jira sprint snapshots
- Conventional commit parsing

Usage:
    python generate_release_notes.py --sprint 1 --output-dir ../sprint-1

Environment Variables:
    JIRA_API_TOKEN: Jira API token (optional)
    JIRA_EMAIL: Jira email (optional)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Repository configuration
REPOS = [
    "brighthive-platform-core",
    "brighthive-webapp",
    "brightbot",
    "brighthive-data-organization-cdk",
    "brighthive-data-workspace-cdk",
    "brightbot-slack-server",
]

# Conventional commit types
COMMIT_TYPES = {
    "feat": ("Features", "🚀"),
    "fix": ("Bug Fixes", "🐛"),
    "docs": ("Documentation", "📚"),
    "style": ("Styling", "💄"),
    "refactor": ("Refactoring", "♻️"),
    "perf": ("Performance", "⚡"),
    "test": ("Testing", "✅"),
    "build": ("Build System", "🔨"),
    "ci": ("Continuous Integration", "👷"),
    "chore": ("Chores", "🔧"),
    "revert": ("Reverts", "⏪"),
    "security": ("Security", "🛡️"),
}


def run_git_command(repo_path: Path, command: list[str]) -> str:
    """Run git command in repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path)] + command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Warning: Git command failed in {repo_path}: {e}")
        return ""


def parse_commit(commit_line: str) -> dict[str, str] | None:
    """Parse a git log line into structured commit data."""
    if not commit_line:
        return None

    parts = commit_line.split(" - ", 2)
    if len(parts) < 3:
        return None

    hash_val = parts[0]
    message = parts[1]
    author_date = parts[2].rsplit(", ", 1)

    author = author_date[0] if len(author_date) > 0 else "Unknown"
    date = author_date[1] if len(author_date) > 1 else ""

    # Parse conventional commit
    commit_type = "chore"
    scope = ""
    breaking = False

    if ":" in message:
        type_scope, message_body = message.split(":", 1)
        message = message_body.strip()

        if "!" in type_scope:
            breaking = True
            type_scope = type_scope.replace("!", "")

        if "(" in type_scope:
            commit_type, scope = type_scope.split("(", 1)
            scope = scope.rstrip(")")
        else:
            commit_type = type_scope

        commit_type = commit_type.strip().lower()

    return {
        "hash": hash_val,
        "type": commit_type,
        "scope": scope,
        "message": message,
        "author": author,
        "date": date,
        "breaking": breaking,
    }


def get_repo_commits(
    repo_path: Path, since_date: str, until_date: str
) -> list[dict[str, str]]:
    """Get commits for a repository in date range."""
    log_output = run_git_command(
        repo_path,
        [
            "log",
            f"--since={since_date}",
            f"--until={until_date}",
            '--pretty=format:%h - %s (%an, %ad)',
            "--date=short",
            "--no-merges",
        ],
    )

    if not log_output:
        return []

    commits = []
    for line in log_output.split("\n"):
        commit = parse_commit(line)
        if commit:
            commits.append(commit)

    return commits


def load_jira_snapshot(sprint_dir: Path) -> dict[str, Any] | None:
    """Load Jira sprint snapshot."""
    snapshot_file = sprint_dir / "jira" / f"sprint_{sprint_dir.name.split('-')[-1]}_snapshot.json"
    if not snapshot_file.exists():
        return None

    with open(snapshot_file) as f:
        return json.load(f)


def generate_repo_changelog(repo_name: str, commits: list[dict[str, str]]) -> str:
    """Generate markdown changelog for a repository."""
    if not commits:
        return f"# {repo_name} - Sprint Changelog\n\nNo changes in this sprint.\n"

    # Group commits by type
    commits_by_type: dict[str, list[dict[str, str]]] = {}
    for commit in commits:
        commit_type = commit["type"]
        if commit_type not in commits_by_type:
            commits_by_type[commit_type] = []
        commits_by_type[commit_type].append(commit)

    # Generate markdown
    md = [f"# {repo_name} - Sprint Changelog\n"]

    # Breaking changes first
    breaking_commits = [c for c in commits if c.get("breaking")]
    if breaking_commits:
        md.append("## ⚠️ Breaking Changes\n")
        for commit in breaking_commits:
            scope_str = f"**{commit['scope']}**: " if commit["scope"] else ""
            md.append(f"- {scope_str}{commit['message']} (`{commit['hash']}`)")
        md.append("")

    # Organize by commit type
    for commit_type, (section_name, emoji) in COMMIT_TYPES.items():
        if commit_type in commits_by_type:
            md.append(f"## {emoji} {section_name}\n")
            for commit in commits_by_type[commit_type]:
                scope_str = f"**{commit['scope']}**: " if commit["scope"] else ""
                md.append(f"- {scope_str}{commit['message']} (`{commit['hash']}`)")
            md.append("")

    # Add metrics
    md.append("---\n")
    md.append(f"**Total Commits**: {len(commits)}\n")

    return "\n".join(md)


def generate_technical_release_notes(
    sprint_num: int,
    sprint_data: dict[str, Any],
    repo_commits: dict[str, list[dict[str, str]]],
) -> str:
    """Generate technical release notes."""
    jira_stats = sprint_data.get("stats", {}) if sprint_data else {}

    md = [
        f"# Sprint {sprint_num} Release Notes\n",
        f"**Release Date**: {datetime.now().strftime('%Y-%m-%d')}",
        f"**Sprint Period**: {sprint_data.get('sprint', {}).get('start_date', 'N/A')} to {sprint_data.get('sprint', {}).get('end_date', 'N/A')}\n" if sprint_data else "",
        "---\n",
        "## Executive Summary\n",
    ]

    # Jira metrics
    if jira_stats:
        md.append(f"- **Total Tickets**: {jira_stats.get('total_tickets', 0)}")
        md.append(f"- **Story Points**: {jira_stats.get('total_story_points', 0)}")
        md.append(f"- **Team Members**: {len(jira_stats.get('assignee_breakdown', {}))}\n")

    # Git metrics
    total_commits = sum(len(commits) for commits in repo_commits.values())
    md.append(f"- **Total Commits**: {total_commits}")
    md.append(f"- **Repositories Updated**: {len([r for r, c in repo_commits.items() if c])}\n")

    md.append("---\n")
    md.append("## Changes by Repository\n")

    # Summary per repo
    for repo_name, commits in repo_commits.items():
        if commits:
            md.append(f"### {repo_name}")
            md.append(f"- **Commits**: {len(commits)}")

            # Count by type
            type_counts = {}
            for commit in commits:
                ctype = commit["type"]
                type_counts[ctype] = type_counts.get(ctype, 0) + 1

            for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
                type_name = COMMIT_TYPES.get(ctype, (ctype, "📦"))[0]
                md.append(f"  - {type_name}: {count}")
            md.append("")

    md.append("---\n")
    md.append(f"**Generated**: {datetime.now().isoformat()}")

    return "\n".join(md)


def generate_marketing_release_notes(
    sprint_num: int,
    sprint_data: dict[str, Any],
    repo_commits: dict[str, list[dict[str, str]]],
) -> str:
    """Generate marketing-focused release notes."""
    md = [
        f"# Sprint {sprint_num} Release 🚀\n",
        f"**Release Date**: {datetime.now().strftime('%B %d, %Y')}",
        f"**Sprint Period**: Sprint {sprint_num}\n",
        "---\n",
        "## What's New\n",
    ]

    # Summarize features
    all_commits = [c for commits in repo_commits.values() for c in commits]
    features = [c for c in all_commits if c["type"] == "feat"]
    fixes = [c for c in all_commits if c["type"] == "fix"]
    security_commits = [c for c in all_commits if c["type"] == "security" or "security" in c["message"].lower()]

    if features:
        md.append("### ✨ New Features\n")
        for feat in features[:5]:  # Top 5
            md.append(f"- {feat['message']}")
        md.append("")

    if security_commits:
        md.append("### 🛡️ Security Improvements\n")
        md.append(f"- {len(security_commits)} security enhancement(s) implemented")
        md.append("")

    if fixes:
        md.append("### 🐛 Bug Fixes\n")
        md.append(f"- {len(fixes)} bug fix(es) delivered")
        md.append("")

    md.append("---\n")
    md.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d')}")

    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Generate sprint release notes")
    parser.add_argument("--sprint", type=int, required=True, help="Sprint number")
    parser.add_argument(
        "--since",
        help="Start date (YYYY-MM-DD)",
        default=(datetime.now().replace(day=1)).strftime("%Y-%m-%d"),
    )
    parser.add_argument(
        "--until",
        help="End date (YYYY-MM-DD)",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory",
        default=None,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent.parent.parent,
        help="Root directory containing repositories",
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(__file__).parent.parent / f"sprint-{args.sprint}"

    output_dir.mkdir(parents=True, exist_ok=True)
    changelogs_dir = output_dir / "changelogs"
    changelogs_dir.mkdir(exist_ok=True)

    print(f"Generating release notes for Sprint {args.sprint}...")
    print(f"Date range: {args.since} to {args.until}")
    print(f"Output directory: {output_dir}")

    # Collect commits from all repos
    repo_commits = {}
    for repo in REPOS:
        repo_path = args.repo_root / repo
        if not repo_path.exists():
            print(f"Warning: Repository {repo} not found at {repo_path}")
            continue

        print(f"Processing {repo}...")
        commits = get_repo_commits(repo_path, args.since, args.until)
        repo_commits[repo] = commits

        # Generate per-repo changelog
        changelog = generate_repo_changelog(repo, commits)
        changelog_file = changelogs_dir / f"{repo}.md"
        changelog_file.write_text(changelog)
        print(f"  ✓ Generated {changelog_file}")

    # Load Jira data
    print("Loading Jira sprint data...")
    sprint_data = load_jira_snapshot(output_dir)

    # Generate technical release notes
    print("Generating technical release notes...")
    technical_notes = generate_technical_release_notes(
        args.sprint, sprint_data, repo_commits
    )
    technical_file = output_dir / f"SPRINT_{args.sprint}_RELEASE_NOTES.md"
    technical_file.write_text(technical_notes)
    print(f"✓ Generated {technical_file}")

    # Generate marketing release notes
    print("Generating marketing release notes...")
    marketing_notes = generate_marketing_release_notes(
        args.sprint, sprint_data, repo_commits
    )
    marketing_file = output_dir / f"SPRINT_{args.sprint}_MARKETING_RELEASE_NOTES.md"
    marketing_file.write_text(marketing_notes)
    print(f"✓ Generated {marketing_file}")

    print("\n✅ Release notes generation complete!")
    print(f"\nFiles created in {output_dir}:")
    print(f"  - SPRINT_{args.sprint}_RELEASE_NOTES.md (technical)")
    print(f"  - SPRINT_{args.sprint}_MARKETING_RELEASE_NOTES.md (marketing)")
    print(f"  - changelogs/*.md ({len(repo_commits)} repositories)")


if __name__ == "__main__":
    main()
