"""Collect Jira project-management metrics (read-only) into one JSON file."""

import base64
import json
import os
import statistics
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_KEY = "BH"
PAGE_SIZE = 100
MIN_DESCRIPTION_CHARS = 100
EPIC_TYPE = "Epic"
DONE_STATUS = "Done"
CANCELED_STATUS = "Canceled"
IN_PROGRESS_CATEGORY = "In Progress"
OTHER_PROJECTS = ("BL", "BPP")
STATE_DONE, STATE_CANCELED, STATE_IN_FLIGHT, STATE_BACKLOG = "done", "canceled", "in_flight", "backlog"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "jira.json"
ISSUES_PATH = OUTPUT_PATH.with_name("jira_issues.json")
FIELDS = "summary,issuetype,status,created,resolutiondate,assignee,creator,parent,description,labels,priority"


def jira_get(*, path: str, params: dict[str, str]) -> dict:
    """GET a Jira REST path using basic auth from the environment."""
    token = base64.b64encode(f"{os.environ['JIRA_USER']}:{os.environ['JIRA_TOKEN']}".encode()).decode()
    url = f"{os.environ['JIRA_BASE'].rstrip('/')}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_all_issues(*, project: str = PROJECT_KEY) -> list[dict]:
    """Page through every issue in a project."""
    issues: list[dict] = []
    page_token = ""
    while True:
        params = {"jql": f"project = {project} ORDER BY created ASC", "maxResults": str(PAGE_SIZE), "fields": FIELDS}
        if page_token:
            params["nextPageToken"] = page_token
        page = jira_get(path="/rest/api/3/search/jql", params=params)
        issues.extend(page["issues"])
        page_token = page.get("nextPageToken", "")
        if not page_token:
            return issues


def parse_ts(*, value: str | None) -> datetime | None:
    """Parse a Jira timestamp."""
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z") if value else None


def description_chars(*, description: dict | None) -> int:
    """Approximate description length from the ADF text nodes."""
    if not description:
        return 0
    total = 0
    stack = [description]
    while stack:
        node = stack.pop()
        total += len(node.get("text", ""))
        stack.extend(node.get("content", []))
    return total


def state_of(*, status: dict) -> str:
    """Map a Jira status to done, canceled, in flight or backlog (Canceled is not Done)."""
    if status["name"] == DONE_STATUS:
        return STATE_DONE
    if status["name"] == CANCELED_STATUS:
        return STATE_CANCELED
    return STATE_IN_FLIGHT if status["statusCategory"]["name"] == IN_PROGRESS_CATEGORY else STATE_BACKLOG


def pct(*, part: int, whole: int) -> float | None:
    """Percentage rounded to 1 decimal."""
    return round(100 * part / whole, 1) if whole else None


def month_of(*, ts: datetime) -> str:
    """YYYY-MM bucket."""
    return ts.strftime("%Y-%m")


def summarize(*, issues: list[dict]) -> dict:
    """Aggregate project-management discipline metrics."""
    rows = []
    for issue in issues:
        f = issue["fields"]
        rows.append({
            "key": issue["key"],
            "type": f["issuetype"]["name"],
            "status": f["status"]["name"],
            "state": state_of(status=f["status"]),
            "created": parse_ts(value=f["created"]),
            "resolved": parse_ts(value=f["resolutiondate"]),
            "assignee": (f["assignee"] or {}).get("displayName"),
            "creator": (f["creator"] or {}).get("displayName"),
            "parent": (f.get("parent") or {}).get("key"),
            "desc_chars": description_chars(description=f["description"]),
            "summary": f["summary"],
        })
    epics = [r for r in rows if r["type"] == EPIC_TYPE]
    work = [r for r in rows if r["type"] != EPIC_TYPE]
    children = Counter(r["parent"] for r in work if r["parent"])
    done_children = Counter(r["parent"] for r in work if r["parent"] and r["state"] == STATE_DONE)
    cycle_days = [(r["resolved"] - r["created"]).total_seconds() / 86400 for r in work if r["resolved"] and r["state"] == STATE_DONE]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": PROJECT_KEY,
        "first_issue_created": min(r["created"] for r in rows).isoformat(),
        "totals": {
            "issues": len(rows), "epics": len(epics), "work_items": len(work),
            **{f"work_items_{st}": sum(1 for r in work if r["state"] == st) for st in (STATE_DONE, STATE_CANCELED, STATE_IN_FLIGHT, STATE_BACKLOG)},
        },
        "by_type": dict(Counter(r["type"] for r in rows)),
        "discipline": {
            "pct_work_items_with_parent_epic": pct(part=sum(1 for r in work if r["parent"]), whole=len(work)),
            "pct_work_items_assigned": pct(part=sum(1 for r in work if r["assignee"]), whole=len(work)),
            "pct_work_items_with_description": pct(
                part=sum(1 for r in work if r["desc_chars"] >= MIN_DESCRIPTION_CHARS), whole=len(work)),
            "median_days_created_to_resolved": round(statistics.median(cycle_days), 1) if cycle_days else None,
        },
        "created_by_month": dict(sorted(Counter(month_of(ts=r["created"]) for r in rows).items())),
        "resolved_by_month": dict(sorted(Counter(month_of(ts=r["resolved"]) for r in rows if r["resolved"]).items())),
        "assignee_distribution": dict(Counter(r["assignee"] or "unassigned" for r in work).most_common()),
        "done_by_assignee": dict(Counter(r["assignee"] or "unassigned" for r in work if r["state"] == STATE_DONE).most_common()),
        "epics": sorted(
            ({"key": e["key"], "summary": e["summary"], "status": e["status"],
              "children": children[e["key"]], "children_done": done_children[e["key"]]} for e in epics),
            key=lambda e: -e["children"],
        ),
    }


def summarize_other_project(*, project: str) -> dict:
    """Counts, date span and status mix for a non-BH project."""
    issues = fetch_all_issues(project=project)
    created = [i["fields"]["created"][:10] for i in issues]
    return {
        "issues": len(issues), "first_created": created[0] if created else None, "last_created": created[-1] if created else None,
        "by_type": dict(Counter(i["fields"]["issuetype"]["name"] for i in issues)),
        "by_status": dict(Counter(i["fields"]["status"]["name"] for i in issues)),
        "created_before_2025_10_23": sum(1 for c in created if c < "2025-10-23"),
    }


def main() -> None:
    """Fetch, summarize and write the Jira metrics file."""
    issues = fetch_all_issues()
    ISSUES_PATH.write_text(json.dumps([
        {"key": i["key"], "type": i["fields"]["issuetype"]["name"], "status": i["fields"]["status"]["name"],
         "state": state_of(status=i["fields"]["status"]), "created": i["fields"]["created"][:10],
         "resolved": (i["fields"]["resolutiondate"] or "")[:10] or None,
         "assignee": (i["fields"]["assignee"] or {}).get("displayName")} for i in issues]))
    payload = summarize(issues=issues)
    payload["other_projects"] = {k: summarize_other_project(project=k) for k in OTHER_PROJECTS}
    payload["bh_keys_below_110_retrievable"] = False
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(json.dumps({k: payload[k] for k in ("totals", "discipline", "other_projects")}, indent=2))


if __name__ == "__main__":
    main()
