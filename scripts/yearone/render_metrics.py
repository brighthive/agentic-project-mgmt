"""Render docs/year-one/METRICS.md from the collected JSON files."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "METRICS.md"
CORE_REPOS = ("brightbot", "brighthive-platform-core", "brighthive-webapp", "brighthive-e2e")
STRUCTURE_KEYS = (
    ("test_files", "Test files"), ("spec_files", "Spec files"), ("adr_files", "ADRs"),
    ("agent_contracts", "CLAUDE.md / AGENTS.md"), ("ci_workflows", "CI workflow files"), ("markdown_docs", "Markdown docs"),
)
PRACTICE_ROWS = (
    ("pct_conventional_title", "PR titles in `type(scope): description` form"),
    ("pct_ticket_in_title", "PR titles carrying a ticket key"),
    ("pct_structured_branch", "Branches named `name/TICKET/description`"),
    ("pct_described_body", "PRs with a real description (200+ chars)"),
    ("pct_human_review", "PRs reviewed by someone other than the author"),
    ("pct_human_approval", "PRs approved by someone other than the author"),
    ("pct_conventional_commits", "Commit headlines in conventional form"),
)


def load(*, name: str) -> dict | None:
    """Load a data file if it exists."""
    path = DATA_DIR / name
    return json.loads(path.read_text()) if path.exists() else None


def fmt(*, value: object) -> str:
    """Format a cell value."""
    if value is None:
        return "n/a"
    return f"{value:,}" if isinstance(value, int) else str(value)


def table(*, header: list[str], rows: list[list[object]]) -> str:
    """Render a markdown table."""
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(fmt(value=c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def delivery_section(*, github: dict) -> str:
    """Merged PRs, releases and repos before vs after."""
    t = github["totals"]
    rows = [
        ["Merged PRs (org-wide)", t["before"]["prs_merged"], t["after"]["prs_merged"]],
        ["Releases published", t["before"]["releases_published"], t["after"]["releases_published"]],
        ["Repos with merged PRs", t["before"]["repos_with_merges"], t["after"]["repos_with_merges"]],
        ["Merged PRs authored by Kuri", 0, t["after"]["prs_merged_by_kuri"]],
    ]
    for repo in github["repos"]:
        if repo["repo"] in CORE_REPOS:
            b, a = repo["windows"]["before"], repo["windows"]["after"]
            rows.append([f"Merged PRs: `{repo['repo']}`", b["prs_merged"], a["prs_merged"]])
    return table(header=["Metric", "Year before", "Year after"], rows=rows)


def practices_section(*, practices: dict | None) -> str:
    """Practice adoption percentages, or a pending note."""
    if not practices:
        return "⏳ Pending: `collect_practices.py` is waiting out a GitHub rate limit."
    p = practices["practices"]
    rows = [[label, p["before"]["everyone"][key], p["after"]["everyone"][key], p["after"]["everyone_else"][key]] for key, label in PRACTICE_ROWS]
    before_n, after_n = p["before"]["everyone"]["prs"], p["after"]["everyone"]["prs"]
    note = (
        f"Percentages use {before_n:,} merged PRs before and {after_n:,} after, bots excluded. "
        "`collect_practices.py` keeps at most 20 merged PRs per repo per day, so a busy day is short of the org-wide delivery count above. "
        "See [DATA-QUALITY.md](DATA-QUALITY.md)."
    )
    return table(header=["Practice (% of merged PRs)", "Year before", "Year after (all)", "Year after (everyone but Kuri)"], rows=rows) + "\n\n" + note


def jira_section(*, jira: dict) -> str:
    """Jira discipline, state mix and distribution, with the earlier planning record as the before."""
    d, t, bpp = jira["discipline"], jira["totals"], jira["other_projects"]["BPP"]
    assigned = jira["assignee_distribution"]
    work = t["work_items"]

    def share(count: int) -> str:
        return f"{count:,} ({round(100 * count / work)}%)"

    before = f"{bpp['created_before_2025_10_23']} ideas in BPP (2023-12 → 2025-10), an idea backlog only"
    rows = [
        ["Planning record", before, f"{t['issues']:,} issues / {t['epics']} epics in BH (first ticket 2026-01-11)"],
        ["Work items with a parent epic", "n/a", f"{d['pct_work_items_with_parent_epic']}%"],
        ["Work items with a real description", "n/a", f"{d['pct_work_items_with_description']}%"],
        ["Work items assigned", "n/a", f"{d['pct_work_items_assigned']}%"],
        ["Median days created → done", "n/a", d["median_days_created_to_resolved"]],
        ["Work items done", "n/a", share(t["work_items_done"])],
        ["Work items canceled", "n/a", share(t["work_items_canceled"])],
        ["Work items in flight (review, testing, staging)", "n/a", share(t["work_items_in_flight"])],
        ["Work items in backlog (mostly Needs Refinement)", "n/a", share(t["work_items_backlog"])],
        ["⚠️ Share of work items assigned to Kuri", "n/a", f"{round(100 * assigned['Kuri Chinca'] / work)}%"],
        ["⚠️ Unassigned work items", "n/a", f"{assigned['unassigned']:,}"],
    ]
    return table(header=["Metric", "Year before", "Year after"], rows=rows)


def shipped_section(*, shipped: dict) -> str:
    """Jira status versus merged-code evidence."""
    n = shipped["work_items"]
    nr = shipped["by_status"]["Needs Refinement"]
    rows = [
        ["Work items Jira marks Done", f"{shipped['done_in_jira']:,} ({round(100 * shipped['done_in_jira'] / n)}%)"],
        ["Open work items whose key appears in merged code", f"{shipped['open_with_merged_code']:,} of {shipped['open_in_jira']:,}"],
        ["…of which in a production branch", f"{shipped['open_with_code_in_production_branch']:,}"],
        ["'Needs Refinement' tickets with merged code", f"{nr['with_merged_code']:,} of {nr['tickets']:,}"],
        ["Any-status work items with merged code", f"{shipped['any_status_with_merged_code']:,} ({round(100 * shipped['any_status_with_merged_code'] / n)}%)"],
        ["Plausible completed range", f"{shipped['done_in_jira']:,} (Jira) to {shipped['done_in_jira'] + shipped['open_with_merged_code']:,} (Jira plus merged code)"],
    ]
    return table(header=["Metric", "Value"], rows=rows)


def structure_section(*, structure: dict) -> str:
    """Repo structure counts at the first and last month."""
    rows = []
    for repo in CORE_REPOS + ("agentic-project-mgmt", "brightagent-v3", "brightbot-slack-server"):
        months = structure.get(repo, {}).get("months", {})
        first, last = months.get("2025-10") or {}, months.get("2026-10") or {}
        if not last:
            continue
        for key, label in STRUCTURE_KEYS:
            if last.get(key):
                rows.append([f"`{repo}`: {label}", first.get(key) if first else "repo did not exist", last[key]])
    return table(header=["Metric", "Oct 2025 (start)", "Oct 2026"], rows=rows)


def cicd_section(*, cicd: dict) -> str:
    """CI/CD health, after-only (before-window runs were pruned)."""
    rows = []
    for repo, data in cicd["repos"].items():
        a = data["after"]
        if a["runs_completed"] < 10:
            continue
        rows.append([f"`{repo}`", a["runs_completed"], f"{a['pct_success_of_decided']}%", a["median_minutes"],
                     f"{a['deploy_success']}/{a['deploy_runs']}", a["pull_request_runs"]])
    return table(header=["Repo", "Completed runs", "Success of decided", "Median minutes", "Deploy runs ok/total", "PR-triggered runs"], rows=rows)


def suites_section(*, suites: dict) -> str:
    """e2e suite and webapp inventory."""
    e, w = suites["e2e"], suites["webapp"]
    rows = [
        ["e2e suite first commit", "did not exist", e["first_commit"]],
        ["e2e test functions", 0, e["test_functions"]],
        ["e2e feature files / surface modules", 0, f"{e['files_by_area']['e2e/features']} / {e['files_by_area']['e2e/surfaces']}"],
        ["e2e workflows", 0, ", ".join(e["workflows"])],
        ["Webapp workflows", "n/a", ", ".join(w["workflows"])],
    ]
    return table(header=["Metric", "Before", "After"], rows=rows)


def main() -> None:
    """Write METRICS.md."""
    github, jira, structure, cicd, suites, shipped = (load(name=f"{n}.json") for n in ("github", "jira", "repo_structure", "cicd", "suites", "shipped_evidence"))
    practices = load(name="practices.json")
    parts = [
        "# Year-one metrics",
        "Generated by `scripts/yearone/render_metrics.py` from `docs/year-one/data/*.json`. Do not edit by hand.\n"
        "Windows: year before = 2024-10-23 → 2025-10-22, year after = 2025-10-23 → 2026-10-22. ⚠️ = a weak spot, shown on purpose.",
        "## Delivery (GitHub)", delivery_section(github=github),
        "## Engineering practices (GitHub PRs)", practices_section(practices=practices),
        "## Project management (Jira)",
        "BH keys 1 to 109 are not retrievable (deleted or never existed), so BH is shown from its first visible ticket, BH-110 on 2026-01-11. "
        "BPP (Platform Planning) holds the earlier idea backlog. Canceled is counted separately from Done.", jira_section(jira=jira),
        "### Jira status vs. shipped code",
        "Jira status lags delivery. A ticket counts here when its key appears in a commit on develop, staging or a production branch of any org repo. "
        "That is evidence of merged work, not proof the ticket is complete.", shipped_section(shipped=shipped),
        "## Repo structure: tests, specs, ADRs, contracts, CI files", structure_section(structure=structure),
        "Counts are by file-name pattern, so treat them as approximate.",
        "## CI/CD health (year after only)",
        "Workflow runs before 2025-10-23 were pruned by GitHub and cannot be measured; success% is success/(success+failure).",
        cicd_section(cicd=cicd),
        "⚠️ Weak spots, causes not yet investigated: webapp success is under half, and brightbot and platform-core deploy-named "
        "workflows mostly did not succeed (deploy = workflow name containing deploy, release or promote, so this may include "
        "validation jobs). The gate gaps are tracked as BH-1140 to BH-1145.",
        "## End-to-end suite and webapp", suites_section(suites=suites),
    ]
    OUTPUT_PATH.write_text("\n\n".join(parts) + "\n")
    print(OUTPUT_PATH.read_text())


if __name__ == "__main__":
    main()
