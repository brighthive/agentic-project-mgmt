#!/usr/bin/env python3
"""Sprint Release Notes Generator with Validation.

Generates sprint release notes by:
1. Fetching Jira tickets for a sprint
2. Validating PR links exist for each ticket
3. Detecting orphan branches without PR links
4. Reporting issues before generating notes
5. Creating release notes for touched repos
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import urllib.request
import urllib.parse
import base64


class TicketStatus(Enum):
    LINKED = "linked"
    ORPHAN_BRANCH = "orphan_branch"
    MISSING = "missing"
    NO_CODE_EXPECTED = "no_code_expected"


@dataclass
class PRLink:
    url: str
    repo: str
    number: int
    status: str
    title: Optional[str] = None


@dataclass
class Branch:
    name: str
    repo: str


@dataclass
class Ticket:
    key: str
    id: str
    summary: str
    ticket_type: str
    assignee: str
    points: float
    status: str
    pr_links: list[PRLink] = field(default_factory=list)
    orphan_branches: list[Branch] = field(default_factory=list)
    validation_status: TicketStatus = TicketStatus.MISSING


@dataclass
class RepoStats:
    repo: str
    pr_count: int
    lines_changed: int
    prs: list[dict] = field(default_factory=list)


@dataclass
class ValidationReport:
    sprint_name: str
    sprint_number: int
    total_tickets: int
    linked_tickets: list[Ticket] = field(default_factory=list)
    orphan_tickets: list[Ticket] = field(default_factory=list)
    missing_tickets: list[Ticket] = field(default_factory=list)
    no_code_tickets: list[Ticket] = field(default_factory=list)
    repos_touched: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class JiraClient:
    def __init__(self) -> None:
        self.user = os.environ.get("JIRA_USER", "")
        self.token = os.environ.get("JIRA_TOKEN", "")
        self.base_url = "https://brighthiveio.atlassian.net"

        if not self.user or not self.token:
            raise ValueError("JIRA_USER and JIRA_TOKEN environment variables required")

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        credentials = base64.b64encode(f"{self.user}:{self.token}".encode()).decode()

        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        }

        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

    def get_sprint_tickets(self, sprint_name: str) -> list[Ticket]:
        jql = f'project = BH AND sprint = "{sprint_name}"'
        fields = ["key", "summary", "issuetype", "assignee", "customfield_10016", "status"]

        response = self._request("POST", "/rest/api/3/search/jql", {
            "jql": jql,
            "fields": fields,
            "maxResults": 200,
        })

        tickets: list[Ticket] = []
        for issue in response.get("issues", []):
            fields_data = issue.get("fields", {})
            tickets.append(Ticket(
                key=issue["key"],
                id=issue["id"],
                summary=fields_data.get("summary", ""),
                ticket_type=fields_data.get("issuetype", {}).get("name", "Unknown"),
                assignee=fields_data.get("assignee", {}).get("displayName", "Unassigned") if fields_data.get("assignee") else "Unassigned",
                points=fields_data.get("customfield_10016") or 0,
                status=fields_data.get("status", {}).get("name", "Unknown"),
            ))

        return tickets

    def get_ticket_prs(self, issue_id: str) -> list[PRLink]:
        endpoint = f"/rest/dev-status/latest/issue/detail?issueId={issue_id}&applicationType=GitHub&dataType=pullrequest"

        try:
            response = self._request("GET", endpoint)
        except Exception:
            return []

        pr_links: list[PRLink] = []
        for detail in response.get("detail", []):
            for pr in detail.get("pullRequests", []):
                url = pr.get("url", "")
                # Extract repo from URL: https://github.com/brighthive/repo-name/pull/123
                parts = url.replace("https://github.com/brighthive/", "").split("/")
                repo = parts[0] if parts else ""
                number = int(parts[2]) if len(parts) > 2 else 0

                pr_links.append(PRLink(
                    url=url,
                    repo=repo,
                    number=number,
                    status=pr.get("status", ""),
                    title=pr.get("title"),
                ))

        return pr_links


class GitHubClient:
    def __init__(self) -> None:
        self.org = "brighthive"

    def _gh_command(self, args: list[str]) -> str:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def search_branches(self, repo: str, ticket_key: str) -> list[Branch]:
        try:
            output = self._gh_command([
                "api", f"repos/{self.org}/{repo}/branches",
                "--jq", ".[].name",
            ])
            branches: list[Branch] = []
            for line in output.strip().split("\n"):
                if ticket_key.lower() in line.lower():
                    branches.append(Branch(name=line, repo=repo))
            return branches
        except Exception:
            return []

    def get_merged_prs(self, repo: str, since: str, until: str) -> list[dict]:
        try:
            output = self._gh_command([
                "pr", "list",
                "--repo", f"{self.org}/{repo}",
                "--state", "merged",
                "--search", f"merged:{since}..{until}",
                "--limit", "100",
                "--json", "number,title,author,additions,deletions,mergedAt",
            ])
            return json.loads(output) if output.strip() else []
        except Exception:
            return []


def validate_sprint(
    jira: JiraClient,
    github: GitHubClient,
    sprint_name: str,
    sprint_number: int,
    repos_to_check: list[str],
) -> ValidationReport:
    """Validate all tickets in a sprint have proper PR links."""

    report = ValidationReport(
        sprint_name=sprint_name,
        sprint_number=sprint_number,
        total_tickets=0,
    )

    # Get all tickets
    tickets = jira.get_sprint_tickets(sprint_name)
    report.total_tickets = len(tickets)

    print(f"\nValidating {len(tickets)} tickets in {sprint_name}...")

    repos_touched: set[str] = set()

    for ticket in tickets:
        print(f"  Checking {ticket.key}...", end=" ")

        # Get PR links from Jira
        ticket.pr_links = jira.get_ticket_prs(ticket.id)

        if ticket.pr_links:
            ticket.validation_status = TicketStatus.LINKED
            report.linked_tickets.append(ticket)
            for pr in ticket.pr_links:
                repos_touched.add(pr.repo)
            print(f"✓ {len(ticket.pr_links)} PR(s)")
        else:
            # Check for orphan branches
            for repo in repos_to_check:
                branches = github.search_branches(repo, ticket.key)
                ticket.orphan_branches.extend(branches)

            if ticket.orphan_branches:
                ticket.validation_status = TicketStatus.ORPHAN_BRANCH
                report.orphan_tickets.append(ticket)
                report.issues.append(
                    f"{ticket.key}: Branch exists but no PR linked - "
                    f"{', '.join(b.name for b in ticket.orphan_branches)}"
                )
                report.recommendations.append(
                    f"Create PR from branch or link existing PR to {ticket.key} in Jira"
                )
                print(f"⚠ Orphan branch in {ticket.orphan_branches[0].repo}")
            else:
                # Check ticket status - only flag Done tickets without PRs
                non_done_statuses = {"To Do", "In Progress", "Testing (Dev)", "Needs Refinement", "Canceled", "Blocked"}
                no_code_types = {"Epic", "Design", "Spike", "Sub-task"}

                if ticket.status in non_done_statuses:
                    ticket.validation_status = TicketStatus.NO_CODE_EXPECTED
                    report.no_code_tickets.append(ticket)
                    print(f"○ Not Done ({ticket.status})")
                elif ticket.status == "Canceled":
                    ticket.validation_status = TicketStatus.NO_CODE_EXPECTED
                    report.no_code_tickets.append(ticket)
                    print(f"○ Canceled")
                elif ticket.ticket_type in no_code_types:
                    ticket.validation_status = TicketStatus.NO_CODE_EXPECTED
                    report.no_code_tickets.append(ticket)
                    print(f"○ No code expected ({ticket.ticket_type})")
                else:
                    # This is a Done ticket (Task/Bug/Story) without PR - flag it
                    ticket.validation_status = TicketStatus.MISSING
                    report.missing_tickets.append(ticket)
                    report.issues.append(
                        f"{ticket.key} ({ticket.ticket_type}): Done but no PR found - verify if code was needed"
                    )
                    print(f"✗ Missing ({ticket.status})")

    report.repos_touched = sorted(repos_touched)
    return report


def print_validation_report(report: ValidationReport) -> None:
    """Print formatted validation report."""

    print(f"\n{'='*60}")
    print(f"SPRINT {report.sprint_number} VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Sprint: {report.sprint_name}")
    print(f"Total Tickets: {report.total_tickets}")
    print()

    # Summary
    print("SUMMARY:")
    print(f"  ✓ Linked:           {len(report.linked_tickets)}")
    print(f"  ⚠ Orphan Branches:  {len(report.orphan_tickets)}")
    print(f"  ✗ Missing:          {len(report.missing_tickets)}")
    print(f"  ○ No Code Expected: {len(report.no_code_tickets)}")
    print()

    # Repos touched
    if report.repos_touched:
        print("REPOS TOUCHED:")
        for repo in report.repos_touched:
            print(f"  - {repo}")
        print()

    # Linked tickets
    if report.linked_tickets:
        print("LINKED TICKETS:")
        for t in report.linked_tickets:
            prs = ", ".join(f"{pr.repo}#{pr.number}" for pr in t.pr_links)
            print(f"  {t.key}: {t.summary[:50]}... -> {prs}")
        print()

    # Issues
    if report.issues:
        print("ISSUES FOUND:")
        for issue in report.issues:
            print(f"  ⚠ {issue}")
        print()

    # Recommendations
    if report.recommendations:
        print("RECOMMENDATIONS:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
        print()

    # Missing tickets (potential problems)
    if report.missing_tickets:
        print("TICKETS WITHOUT CODE (verify if expected):")
        for t in report.missing_tickets:
            print(f"  - {t.key}: {t.summary[:60]}... ({t.ticket_type}, {t.status})")
        print()


def generate_release_notes(
    report: ValidationReport,
    github: GitHubClient,
    since_date: str,
    until_date: str,
    output_dir: str,
) -> None:
    """Generate release notes markdown files."""

    # Collect PR data for all touched repos
    repo_stats: list[RepoStats] = []
    total_prs = 0
    total_lines = 0

    for repo in report.repos_touched:
        prs = github.get_merged_prs(repo, since_date, until_date)
        lines = sum(pr.get("additions", 0) + pr.get("deletions", 0) for pr in prs)
        total_prs += len(prs)
        total_lines += lines

        repo_stats.append(RepoStats(
            repo=repo,
            pr_count=len(prs),
            lines_changed=lines,
            prs=prs,
        ))

    # Generate technical release notes
    os.makedirs(output_dir, exist_ok=True)

    with open(f"{output_dir}/RELEASE_NOTES.md", "w") as f:
        f.write(f"# Sprint {report.sprint_number} Release Notes\n\n")
        f.write(f"**Sprint:** {report.sprint_name}\n")
        f.write(f"**Period:** {since_date} to {until_date}\n\n")
        f.write("---\n\n")

        f.write("## Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Tickets Completed | {len(report.linked_tickets)} |\n")
        points = sum(t.points for t in report.linked_tickets)
        f.write(f"| Story Points | {points} |\n")
        f.write(f"| PRs Merged | {total_prs} |\n")
        f.write(f"| Lines Changed | {total_lines:,} |\n")
        f.write(f"| Repos Touched | {len(report.repos_touched)} |\n\n")

        f.write("---\n\n")
        f.write("## Repository Changes\n\n")
        for stats in repo_stats:
            f.write(f"### {stats.repo}\n")
            f.write(f"- PRs merged: {stats.pr_count}\n")
            f.write(f"- Lines changed: {stats.lines_changed:,}\n\n")

        f.write("---\n\n")
        f.write("## Completed Tickets\n\n")
        for t in report.linked_tickets:
            f.write(f"- **[{t.key}](https://brighthiveio.atlassian.net/browse/{t.key})** ")
            f.write(f"{t.summary} (@{t.assignee})\n")

        f.write("\n---\n\n")
        f.write("## Pull Requests by Repository\n\n")
        for stats in repo_stats:
            if stats.prs:
                f.write(f"### {stats.repo}\n")
                for pr in stats.prs:
                    author = pr.get("author", {}).get("login", "unknown")
                    f.write(f"- [#{pr['number']}](https://github.com/brighthive/{stats.repo}/pull/{pr['number']}) ")
                    f.write(f"{pr['title']} (@{author})\n")
                f.write("\n")

    # Generate marketing release notes
    with open(f"{output_dir}/MARKETING_RELEASE_NOTES.md", "w") as f:
        f.write(f"# Sprint {report.sprint_number} - What's New\n\n")
        f.write(f"**Release Date:** {until_date}\n\n")
        f.write("---\n\n")

        f.write("## Highlights for Customers\n\n")
        f.write("<!-- GTM TEAM: Fill in customer-facing highlights -->\n\n")
        f.write("### New Features\n- [ ] TODO: Add customer-facing features\n\n")
        f.write("### Improvements\n- [ ] TODO: Add improvements\n\n")
        f.write("### Bug Fixes\n- [ ] TODO: Add notable bug fixes\n\n")

        f.write("---\n\n")
        f.write("## Engineering Stats (for investors)\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Features Delivered | {len(report.linked_tickets)} tickets |\n")
        f.write(f"| Story Points | {points} pts |\n")
        f.write(f"| PRs Merged | {total_prs} |\n")
        f.write(f"| Lines Changed | {total_lines:,} |\n")
        f.write(f"| Repos Modified | {len(report.repos_touched)} |\n\n")

        f.write("---\n\n")
        f.write("## Repos Modified\n\n")
        for stats in repo_stats:
            f.write(f"- **{stats.repo}**: {stats.pr_count} PRs, {stats.lines_changed:,} lines\n")

    # Generate validation report
    with open(f"{output_dir}/VALIDATION_REPORT.md", "w") as f:
        f.write(f"# Sprint {report.sprint_number} Validation Report\n\n")

        if report.issues:
            f.write("## Issues Found\n\n")
            for issue in report.issues:
                f.write(f"- {issue}\n")
            f.write("\n")

        if report.recommendations:
            f.write("## Recommendations\n\n")
            for rec in report.recommendations:
                f.write(f"- {rec}\n")
            f.write("\n")

        if report.missing_tickets:
            f.write("## Tickets Without Code (verify if expected)\n\n")
            for t in report.missing_tickets:
                f.write(f"- {t.key}: {t.summary} ({t.ticket_type})\n")

    print(f"\nRelease notes generated in {output_dir}/")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: sprint_release.py <sprint_number> [--validate-only] [--dry-run]")
        print("  sprint_number: 1, 2, 3, 4, etc.")
        print("  --validate-only: Only run validation, don't generate notes")
        print("  --dry-run: Show what would be generated without writing files")
        sys.exit(1)

    sprint_number = int(sys.argv[1])
    validate_only = "--validate-only" in sys.argv
    dry_run = "--dry-run" in sys.argv

    # Sprint configuration
    sprint_config = {
        1: ("Sprint 1 🍇", "2026-01-13", "2026-01-20"),
        2: ("Sprint 2 🥝", "2026-01-20", "2026-01-27"),
        3: ("Sprint 3 🍎", "2026-01-27", "2026-02-03"),
        4: ("Sprint 4 🍍", "2026-02-03", "2026-02-10"),
    }

    if sprint_number not in sprint_config:
        print(f"Unknown sprint {sprint_number}. Known sprints: {list(sprint_config.keys())}")
        sys.exit(1)

    sprint_name, since_date, until_date = sprint_config[sprint_number]

    # Common repos to check for orphan branches
    repos_to_check = [
        "brighthive-platform-core",
        "brighthive-webapp",
        "brightbot",
        "brighthive-admin",
        "brightbot-slack-server",
        "brighthive-data-organization-cdk",
    ]

    # Initialize clients
    jira = JiraClient()
    github = GitHubClient()

    # Run validation
    report = validate_sprint(jira, github, sprint_name, sprint_number, repos_to_check)
    print_validation_report(report)

    if validate_only:
        print("Validation only mode - skipping release notes generation")
        sys.exit(0)

    if report.issues:
        print("\n" + "="*60)
        print("WARNING: Issues found during validation!")
        print("Review the issues above before generating release notes.")
        print("="*60)

        if not dry_run:
            response = input("\nContinue with release notes generation? [y/N] ")
            if response.lower() != "y":
                print("Aborted.")
                sys.exit(0)

    # Generate release notes
    output_dir = f"/Users/bado/iccha/brighthive/agentic-project-mgmt/jira/sprint/{sprint_number}"

    if dry_run:
        print(f"\nDry run - would generate notes in {output_dir}/")
        print("Files that would be created:")
        print("  - RELEASE_NOTES.md")
        print("  - MARKETING_RELEASE_NOTES.md")
        print("  - VALIDATION_REPORT.md")
    else:
        generate_release_notes(report, github, since_date, until_date, output_dir)
        print("\nDone! Review the generated files before committing.")


if __name__ == "__main__":
    main()
