#!/usr/bin/env python3
"""Generate sprint release notes from JIRA and Notion, publish to Notion."""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import requests
import yaml


@dataclass
class SprintContext:
    """Sprint context from Notion."""

    sprint_name: str
    sprint_goals: list[str]
    highlights: list[str]
    challenges: list[str]


@dataclass
class JiraTicket:
    """JIRA ticket info."""

    key: str
    summary: str
    issue_type: str
    status: str
    assignee: str | None
    pr_url: str | None


def load_jira_config() -> dict[str, str]:
    """Load JIRA configuration."""
    config_path = Path.home() / ".config" / "jiratui" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return {
        "base_url": config["jira_api_base_url"],
        "username": config["jira_api_username"],
        "token": config["jira_api_token"],
    }


def get_notion_config() -> dict[str, str]:
    """Get Notion configuration from environment."""
    return {
        "token": os.getenv("NOTION_TOKEN", ""),
        "sprint_db_id": os.getenv("NOTION_SPRINT_DB_ID", ""),
        "releases_db_id": os.getenv("NOTION_RELEASES_DB_ID", ""),
    }


def fetch_sprint_context_from_notion(
    sprint_name: str, notion_config: dict[str, str]
) -> SprintContext | None:
    """Fetch sprint goals and context from Notion."""
    if not notion_config["token"] or not notion_config["sprint_db_id"]:
        return None

    headers = {
        "Authorization": f"Bearer {notion_config['token']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    query_url = f"https://api.notion.com/v1/databases/{notion_config['sprint_db_id']}/query"
    query_payload = {
        "filter": {"property": "Name", "title": {"equals": sprint_name}}
    }

    response = requests.post(query_url, headers=headers, json=query_payload)

    if response.status_code != 200:
        print(f"   ⚠ Failed to fetch Notion sprint: {response.text}")
        return None

    results = response.json().get("results", [])
    if not results:
        return None

    page_id = results[0]["id"]

    blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    blocks_response = requests.get(blocks_url, headers=headers)

    if blocks_response.status_code != 200:
        return None

    blocks = blocks_response.json().get("results", [])

    goals = []
    highlights = []
    challenges = []
    current_section = None

    for block in blocks:
        block_type = block.get("type")

        if block_type == "heading_2":
            heading_text = block["heading_2"]["rich_text"]
            if heading_text:
                text = heading_text[0]["plain_text"].lower()
                if "goal" in text:
                    current_section = "goals"
                elif "highlight" in text:
                    current_section = "highlights"
                elif "challenge" in text or "learning" in text:
                    current_section = "challenges"

        elif block_type == "bulleted_list_item":
            text = block["bulleted_list_item"]["rich_text"]
            if text:
                content = text[0]["plain_text"]
                if current_section == "goals":
                    goals.append(content)
                elif current_section == "highlights":
                    highlights.append(content)
                elif current_section == "challenges":
                    challenges.append(content)

    return SprintContext(
        sprint_name=sprint_name,
        sprint_goals=goals,
        highlights=highlights,
        challenges=challenges,
    )


def fetch_jira_sprint_tickets(sprint_name: str, jira_config: dict[str, str]) -> list[JiraTicket]:
    """Fetch completed tickets from JIRA sprint."""
    jql = f'project = BH AND sprint = "{sprint_name}" AND status = Done ORDER BY type DESC, key ASC'

    url = f"{jira_config['base_url']}/rest/api/3/search/jql"
    auth = (jira_config["username"], jira_config["token"])
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    payload = {
        "jql": jql,
        "fields": ["summary", "status", "issuetype", "assignee", "description"],
        "maxResults": 500,
    }

    response = requests.post(url, auth=auth, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error fetching JIRA tickets: {response.text}")
        return []

    issues = response.json().get("issues", [])
    tickets = []

    for issue in issues:
        fields = issue["fields"]
        description = fields.get("description", "")

        pr_url = extract_github_pr_from_description(description)

        assignee_name = None
        if fields.get("assignee"):
            assignee_name = fields["assignee"].get("displayName", "Unassigned")

        tickets.append(
            JiraTicket(
                key=issue["key"],
                summary=fields["summary"],
                issue_type=fields["issuetype"]["name"],
                status=fields["status"]["name"],
                assignee=assignee_name,
                pr_url=pr_url,
            )
        )

    return tickets


def extract_github_pr_from_description(description: str | dict | None) -> str | None:
    """Extract GitHub PR link from ticket description."""
    if not description:
        return None

    if isinstance(description, dict):
        content = description.get("content", [])
        text_parts = []
        for item in content:
            if item.get("type") == "paragraph":
                for text_item in item.get("content", []):
                    if text_item.get("type") == "text":
                        text_parts.append(text_item.get("text", ""))
        description = " ".join(text_parts)

    if isinstance(description, str):
        lines = description.split("\n")
        for line in lines:
            if "github.com" in line.lower() and "/pull/" in line.lower():
                parts = line.split("github.com")
                if len(parts) > 1:
                    pr_part = parts[1].split()[0].strip()
                    return f"https://github.com{pr_part}"

    return None


def categorize_tickets(tickets: list[JiraTicket]) -> dict[str, list[JiraTicket]]:
    """Categorize tickets by type."""
    categories = {
        "Epic": [],
        "Story": [],
        "Task": [],
        "Bug": [],
        "Other": [],
    }

    for ticket in tickets:
        if ticket.issue_type in categories:
            categories[ticket.issue_type].append(ticket)
        else:
            categories["Other"].append(ticket)

    return {k: v for k, v in categories.items() if v}


def generate_markdown_release_notes(
    context: SprintContext | None, tickets: list[JiraTicket]
) -> str:
    """Generate markdown release notes."""
    lines = [
        f"# {context.sprint_name if context else 'Sprint'} Release Notes",
        f"\n**Released:** {datetime.now().strftime('%Y-%m-%d')}",
    ]

    if context:
        if context.sprint_goals:
            lines.append("\n## Sprint Goals\n")
            for goal in context.sprint_goals:
                lines.append(f"- {goal}")

        if context.highlights:
            lines.append("\n## Highlights\n")
            for highlight in context.highlights:
                lines.append(f"- {highlight}")

    lines.append(f"\n## Completed Work ({len(tickets)} tickets)\n")

    categorized = categorize_tickets(tickets)

    for category, tickets_in_category in categorized.items():
        lines.append(f"\n### {category} ({len(tickets_in_category)})\n")

        for ticket in tickets_in_category:
            pr_link = f" - [PR]({ticket.pr_url})" if ticket.pr_url else ""
            assignee = f" (@{ticket.assignee})" if ticket.assignee else ""
            lines.append(f"- **[{ticket.key}]** {ticket.summary}{pr_link}{assignee}")

    if context and context.challenges:
        lines.append("\n## Challenges & Learnings\n")
        for challenge in context.challenges:
            lines.append(f"- {challenge}")

    lines.append("\n---")
    lines.append(f"\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    return "\n".join(lines)


def publish_to_notion(
    release_notes: str, sprint_name: str, notion_config: dict[str, str]
) -> str | None:
    """Publish release notes to Notion releases database."""
    if not notion_config["token"] or not notion_config["releases_db_id"]:
        return None

    headers = {
        "Authorization": f"Bearer {notion_config['token']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    blocks = markdown_to_notion_blocks(release_notes)

    payload = {
        "parent": {"database_id": notion_config["releases_db_id"]},
        "properties": {
            "Name": {"title": [{"text": {"content": f"{sprint_name} Release"}}]},
            "Date": {"date": {"start": datetime.now().date().isoformat()}},
        },
        "children": blocks,
    }

    response = requests.post(
        "https://api.notion.com/v1/pages", headers=headers, json=payload
    )

    if response.status_code not in [200, 201]:
        print(f"   ⚠ Failed to publish to Notion: {response.text}")
        return None

    page_url = response.json().get("url")
    return page_url


def markdown_to_notion_blocks(markdown: str) -> list[dict]:
    """Convert simple markdown to Notion blocks."""
    blocks = []
    lines = markdown.split("\n")

    for line in lines:
        line = line.strip()
        if not line or line == "---":
            continue

        if line.startswith("# "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]},
                }
            )
        elif line.startswith("## "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]},
                }
            )
        elif line.startswith("### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"text": {"content": line[4:]}}]},
                }
            )
        elif line.startswith("- "):
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:]}}]
                    },
                }
            )
        else:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": line}}]},
                }
            )

    return blocks


def main() -> None:
    """Main execution."""
    print("Sprint Release Notes Generator")
    print("=" * 50)
    print()

    sprint_name = input("Enter sprint name (e.g., Sprint 1): ").strip()

    if not sprint_name:
        print("Error: Sprint name required")
        return

    print(f"\nGenerating release notes for {sprint_name}...")
    print()

    jira_config = load_jira_config()
    notion_config = get_notion_config()

    print("1. Fetching sprint context from Notion...")
    context = fetch_sprint_context_from_notion(sprint_name, notion_config)
    if context:
        print(f"   ✓ Found {len(context.sprint_goals)} goals, {len(context.highlights)} highlights")
    else:
        print("   ⚠ No Notion context (set NOTION_TOKEN and NOTION_SPRINT_DB_ID)")

    print("2. Fetching completed tickets from JIRA...")
    tickets = fetch_jira_sprint_tickets(sprint_name, jira_config)
    print(f"   ✓ Found {len(tickets)} completed tickets")

    if not tickets:
        print("\n⚠ No tickets found for this sprint!")
        return

    print("3. Generating release notes...")
    release_notes = generate_markdown_release_notes(context, tickets)

    output_file = Path(f"/Users/bado/iccha/brighthive/jira/RELEASE_{sprint_name.replace(' ', '_')}.md")
    with open(output_file, "w") as f:
        f.write(release_notes)
    print(f"   ✓ Saved to: {output_file}")

    if notion_config["token"] and notion_config["releases_db_id"]:
        print("4. Publishing to Notion...")
        notion_url = publish_to_notion(release_notes, sprint_name, notion_config)
        if notion_url:
            print(f"   ✓ Published: {notion_url}")
    else:
        print("4. Skipping Notion publish (set NOTION_TOKEN and NOTION_RELEASES_DB_ID)")

    print()
    print("=" * 50)
    print("✓ Release notes complete!")
    print()


if __name__ == "__main__":
    main()
