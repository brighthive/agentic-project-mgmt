#!/usr/bin/env python3
"""Fetch Sprint 1 and Sprint 2 information from Jira."""

import json
import requests
import yaml
from pathlib import Path
from datetime import datetime

def load_jira_config():
    config_path = Path.home() / ".config/jiratui/config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return {
        "base_url": config["jira_api_base_url"],
        "username": config["jira_api_username"],
        "token": config["jira_api_token"],
    }

config = load_jira_config()

# Fetch sprints
print("📅 Fetching sprints...")
boards_url = f"{config['base_url']}/rest/agile/1.0/board"
response = requests.get(boards_url, auth=(config["username"], config["token"]))
board_id = response.json()["values"][0]["id"]

sprints_url = f"{config['base_url']}/rest/agile/1.0/board/{board_id}/sprint"
response = requests.get(sprints_url, auth=(config["username"], config["token"]))
sprints = response.json()["values"]

sprint_1 = next((s for s in sprints if "Sprint 1" in s["name"]), None)
sprint_2 = next((s for s in sprints if "Sprint 2" in s["name"]), None)

def fetch_sprint_details(sprint_id):
    """Fetch detailed sprint information including all tickets."""
    # Get sprint info
    sprint_url = f"{config['base_url']}/rest/agile/1.0/sprint/{sprint_id}"
    response = requests.get(sprint_url, auth=(config["username"], config["token"]))
    sprint_info = response.json()
    
    # Get tickets in sprint
    jql = f"sprint = {sprint_id} ORDER BY key ASC"
    search_url = f"{config['base_url']}/rest/api/3/search/jql"
    payload = {
        "jql": jql,
        "fields": ["summary", "status", "assignee", "priority", "issuetype", "labels", "customfield_10016", "parent"],
        "maxResults": 1000
    }
    response = requests.post(
        search_url,
        auth=(config["username"], config["token"]),
        json=payload
    )
    
    issues = response.json()["issues"]
    
    # Format tickets
    tickets = []
    for issue in issues:
        ticket = {
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "status_category": issue["fields"]["status"]["statusCategory"]["name"],
            "type": issue["fields"]["issuetype"]["name"],
            "priority": issue["fields"]["priority"]["name"] if issue["fields"].get("priority") else None,
            "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"].get("assignee") else "Unassigned",
            "labels": issue["fields"].get("labels", []),
            "story_points": issue["fields"].get("customfield_10016"),
            "epic": issue["fields"]["parent"]["key"] if issue["fields"].get("parent") else None,
        }
        tickets.append(ticket)
    
    # Calculate stats
    total_tickets = len(tickets)
    story_points = sum(t["story_points"] for t in tickets if t["story_points"])
    
    status_breakdown = {}
    for ticket in tickets:
        status = ticket["status"]
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    type_breakdown = {}
    for ticket in tickets:
        issue_type = ticket["type"]
        type_breakdown[issue_type] = type_breakdown.get(issue_type, 0) + 1
    
    assignee_breakdown = {}
    for ticket in tickets:
        assignee = ticket["assignee"]
        assignee_breakdown[assignee] = assignee_breakdown.get(assignee, 0) + 1
    
    return {
        "sprint": {
            "id": sprint_info["id"],
            "name": sprint_info["name"],
            "state": sprint_info["state"],
            "start_date": sprint_info.get("startDate"),
            "end_date": sprint_info.get("endDate"),
            "goal": sprint_info.get("goal", ""),
        },
        "stats": {
            "total_tickets": total_tickets,
            "total_story_points": story_points,
            "status_breakdown": status_breakdown,
            "type_breakdown": type_breakdown,
            "assignee_breakdown": assignee_breakdown,
        },
        "tickets": tickets,
        "fetched_at": datetime.now().isoformat(),
    }

# Fetch Sprint 1
if sprint_1:
    print(f"\n📊 Fetching Sprint 1 (ID: {sprint_1['id']})...")
    sprint_1_data = fetch_sprint_details(sprint_1["id"])
    
    with open("sprint_1_snapshot.json", "w") as f:
        json.dump(sprint_1_data, f, indent=2)
    
    print(f"  ✓ Sprint 1: {sprint_1_data['sprint']['name']}")
    print(f"    State: {sprint_1_data['sprint']['state']}")
    print(f"    Tickets: {sprint_1_data['stats']['total_tickets']}")
    print(f"    Story Points: {sprint_1_data['stats']['total_story_points']}")
    print(f"    Status: {sprint_1_data['stats']['status_breakdown']}")
else:
    print("  ⚠️  Sprint 1 not found")

# Fetch Sprint 2
if sprint_2:
    print(f"\n📊 Fetching Sprint 2 (ID: {sprint_2['id']})...")
    sprint_2_data = fetch_sprint_details(sprint_2["id"])
    
    with open("sprint_2_snapshot.json", "w") as f:
        json.dump(sprint_2_data, f, indent=2)
    
    print(f"  ✓ Sprint 2: {sprint_2_data['sprint']['name']}")
    print(f"    State: {sprint_2_data['sprint']['state']}")
    print(f"    Tickets: {sprint_2_data['stats']['total_tickets']}")
    print(f"    Story Points: {sprint_2_data['stats']['total_story_points']}")
    print(f"    Status: {sprint_2_data['stats']['status_breakdown']}")
else:
    print("  ⚠️  Sprint 2 not found")

print(f"\n✅ Sprint snapshots saved:")
print(f"  - sprint_1_snapshot.json")
print(f"  - sprint_2_snapshot.json")
