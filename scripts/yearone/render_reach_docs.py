"""Render BEFORE-AFTER-KURI, PRODUCT-IDEAS, MILESTONES and PRODUCTION-VALUE docs from the data files."""

import json
from collections import Counter, defaultdict
from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent.parent / "docs" / "year-one"
DATA_DIR = DOCS_DIR / "data"
INTERNAL_REPOS = ("agentic-project-mgmt", "brighthive-e2e", "platform-saas-ai-context")
TOP_CAPABILITIES = 30
KURI_LED_MIN_SHARE_PCT = 50.0
SIGNAL_LABELS = {
    "tracing_and_evals": "Tracing and evals", "structured_logging": "Structured logging", "cost_and_token_metering": "Cost and token metering",
    "health_endpoints": "Health endpoints", "alarms_and_alerts": "Alarms and alerts", "audit_trail": "Audit trail",
    "registries": "Registries (adapter lookups)",
    "feature_flags": "Feature flags", "authorization_checks": "Authorization checks", "agent_graphs_and_tools": "Agent graphs and tools",
    "protocol_classes": "Protocol classes",
}


def load(name: str) -> dict:
    """Load a data file."""
    return json.loads((DATA_DIR / name).read_text())


def table(header: list[str], rows: list[list[object]]) -> str:
    """Render a markdown table."""
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join("n/a" if c is None else f"{c:,}" if isinstance(c, int) else str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def write(name: str, parts: list[str]) -> None:
    """Write a doc."""
    (DOCS_DIR / name).write_text("\n\n".join(parts) + "\n")


def before_after_doc(reach: dict) -> None:
    """Codebase before Kuri and now."""
    repos = reach["repos"]
    size = [[n, f"{r['before']['source_kb']:,} → {r['after']['source_kb']:,}", f"{r['before']['code_files']:,} → {r['after']['code_files']:,}",
             f"{r['before']['test_files']} → {r['after']['test_files']}", f"{r['before']['markdown_docs']} → {r['after']['markdown_docs']}"] for n, r in repos.items()]
    signals = []
    for group in ("observability", "architecture"):
        for key, label in SIGNAL_LABELS.items():
            row = [group.title(), label]
            cells = []
            for n, r in repos.items():
                b, a = r["before"]["signals"][group].get(key), r["after"]["signals"][group].get(key)
                cells.append(f"{b['files']} → {a['files']}" if b and a else "–")
            if any(c not in ("–", "0 → 0") for c in cells):
                signals.append(row + cells)
    all_modules = [(n, m) for n, r in repos.items() for m in r["modules_added"]]
    led = [(n, m) for n, m in all_modules if (m["kuri_share_pct"] or 0.0) >= KURI_LED_MIN_SHARE_PCT]
    added = [[n, f"{m['root']}/{m['module']}", m["commits"], f"{m['kuri_share_pct']}%"] for n, m in led]
    write("BEFORE-AFTER-KURI.md", [
        "# Before Kuri, After Kuri: What the Codebase Can Do",
        f"Each core repo is measured at the last commit on `develop` before {reach['cutoff']} and at `{reach['after_ref']}` now. "
        "Source: `scripts/yearone/collect_codebase_reach.py` → `data/codebase_reach.json`. Counts match code patterns, so treat them as approximate.",
        "## Size and tests", table(["Repo", "Source KB", "Code files", "Test files", "Markdown docs"], size),
        "## Monitoring, observability and architecture signals", "Files containing the pattern, before → after.",
        table(["Group", "Signal", *repos.keys()], signals),
                "## Kuri-led modules added since the cutoff",
        f"A module is a directory that did not exist before the cutoff. Kuri share is the share of commits touching it on `develop`, matched by author name or email. Listed: {len(led)} of {len(all_modules)} new modules, those with a Kuri share of {KURI_LED_MIN_SHARE_PCT:.0f}% or more (the same rule as [MILESTONES.md](MILESTONES.md)). The other {len(all_modules) - len(led)} were built mostly by others and are in `data/codebase_reach.json`. Some directories are moves, not new capability.",
        table(["Repo", "Module", "Commits", "Kuri share"], added),
        "## Limits", "- Pattern counts can miss renamed code and count tests and docs that mention a term.\n- Left out as unreliable: GraphQL field counts (the schema moved from a TypeScript file to a `.graphql` file, so the two counts are not comparable), \"port or adapter classes\" (the code names them differently) and \"error and product analytics\" (a keyword count).\n- A module's Kuri share counts commits, not value.\n- This compares two snapshots. It does not prove the change was caused by any one person.",
    ])


def ideas_doc(ideas: dict) -> None:
    """Product ideas and their evidence."""
    rows, details = [], []
    for i in ideas["ideas"]:
        origin = ", ".join(f"{e['epic']} ({e['created']}, {e['creator']})" for e in i["origin_epics"])
        mods = "; ".join(f"`{m['path']}` {m['kuri_share_pct']}%" for m in i["modules"]) or "n/a"
        fs = i["first_spec"]["first_added"] if i["first_spec"] else "n/a"
        rows.append([i["name"], origin, f"{len(i['specs'])} ({i['specs_added_by_kuri']} by Kuri)", fs,
                     f"{i['commits_in_keyed_epics']:,} at {i['kuri_share_of_keyed_epic_commits_pct']}%", mods])
        details.append(f"### {i['name']}\n\n{i['one_line']}\n\n" + "\n".join(f"- `{s['file']}` (first added {s['first_added']})" for s in i["specs"]) +
                       ("\n\nEpics: " + ", ".join(f"{e['epic']} {e['summary'][:60]}" for e in i["epics_by_key"]) if i["epics_by_key"] else ""))
    write("PRODUCT-IDEAS.md", [
        "# Product Ideas Brought to the Platform",
        "Each idea is traced to the roadmap epic that first wrote it down, the specs that defined it, the epics that built it, and the code modules it lives in. "
        "Source: `scripts/yearone/product_ideas.json` (the idea list, curated) and `collect_product_ideas.py` → `data/product_ideas.json`.",
        "Spec authorship and commits show who wrote and built each idea. They do not show whose head it came from. Add that origin story where it applies.",
        table(["Idea", "Written down as (Jira epic, date, creator)", "Specs", "First spec", "Commits in listed epics, Kuri share", "Modules, Kuri share"], rows),
        "## Detail", *details,
        "## Limits", "- Specs are matched by file name in `docs/specs`; a spec can serve more than one idea.\n- Epic commits are matched by ticket key in the commit message.\n- Commits are evidence of merged work, not proof an idea is finished.",
    ])


def milestones_doc(ms: dict) -> None:
    """Kuri-led epics as milestones."""
    led = sorted((e for e in ms["epics"] if e["kuri_led"]), key=lambda e: e["first_commit"])
    rows = [[e["epic"], e["summary"].replace("&amp;", "&")[:70], f"{e['first_commit']} → {e['last_commit']}", e["commits"], f"{e['kuri_share_pct']}%",
             f"{e['children_done']} of {e['children']}", ", ".join(r.replace("brighthive-", "") for r in e["repos"][:3])] for e in led]
    months = Counter(e["first_commit"][:7] for e in led)
    write("MILESTONES.md", [
        "# Milestones: Epics Kuri Led",
        f"{ms['kuri_led_epics']} of {ms['epics_with_code']} epics with merged code are Kuri-led: 10 or more commits and a 50% or higher share. Source: `collect_milestones.py` → `data/milestones.json`. "
        f"{ms['method']}",
        "## Epics, in the order work began", table(["Epic", "What", "Commits from → to", "Commits", "Kuri share", "Tickets done", "Repos"], rows),
        "## Epics started per month", table(["Month", "Kuri-led epics started"], sorted(months.items())),
        "## Limits", "- \"Tickets done\" is Jira status, which lags delivery (see [JIRA.md](JIRA.md)).\n- Commit share measures where the code came from, not who decided what to build.\n- Epics under 10 commits or under 50% Kuri share are left out, not judged.",
    ])


def production_doc(prs: dict, items: dict) -> None:
    """Production-verified user-facing changes."""
    value = [p for p in prs["prs"] if p.get("value_change") and p["repo"] not in INTERNAL_REPOS]
    shipped = [p for p in value if p["status"] in ("released", "on_main")]
    kuri_value, kuri_shipped = [p for p in value if p["kuri"]], [p for p in shipped if p["kuri"]]
    share = round(100 * len(kuri_shipped) / len(shipped), 1)
    by_repo = Counter(p["repo"] for p in kuri_shipped)
    by_type = Counter(p["type"] for p in kuri_shipped)
    by_sprint = Counter(p["sprint"] for p in kuri_shipped)
    totals_sprint = Counter(p["sprint"] for p in shipped)
    caps = defaultdict(lambda: {"prs": 0, "sprints": set()})
    for p in kuri_shipped:
        if p["capability"]:
            caps[p["capability"]]["prs"] += 1
            caps[p["capability"]]["sprints"].add(p["sprint"])
    top = sorted(caps.items(), key=lambda kv: -kv[1]["prs"])[:TOP_CAPABILITIES]
    marketing = items["by_status"]
    write("PRODUCTION-VALUE.md", [
        "# What Reached Production: User-Facing Value Kuri Delivered",
        "Every pull request (PR) linked in the sprint release notes (`jira/sprint/N/RELEASE_NOTES.md`, sprints 1 to 16) is checked against production. "
        "Source: `collect_shipped_prs.py` → `data/shipped_prs.json`, `collect_production_value.py` → `data/production_value.json`.",
        "**Production means:** for `brighthive-platform-core` and `brighthive-webapp`, the merge commit is in a plain `-release` tag. For every other repo, it is on `main` or `master`. "
        "Git shows a change was released or is on the production branch. It does not prove the change is running. For example, `brightbot` production deploys failed repeatedly in July 2026 (internal notes), so \"on main\" is weaker evidence than \"released\".",
        "## The count",
        table(["Measure", "Count"], [
            ["PRs listed in the release notes (all merged)", prs["prs_in_notes"]],
            ["User-facing changes: `feat`, `fix`, `perf`, excluding release carriers and internal tooling repos", len(value)],
            ["…verified in production", len(shipped)],
            ["User-facing changes authored by Kuri", len(kuri_value)],
            ["…verified in production", len(kuri_shipped)],
            ["Kuri's share of production-verified user-facing changes", f"{share}%"],
        ]),
        "## Kuri's production-verified changes", table(["Repo", "Changes"], by_repo.most_common()), table(["Type", "Changes"], by_type.most_common()),
        "## By sprint", table(["Sprint", "Kuri, verified in production", "All authors, verified in production"], [[s, by_sprint[s], totals_sprint[s]] for s in sorted(totals_sprint)]),
        f"## Top {TOP_CAPABILITIES} capabilities (release-note headings)",
        table(["Capability", "Kuri PRs in production", "Sprints"], [[c, v["prs"], ", ".join(map(str, sorted(v["sprints"])))] for c, v in top]),
        "## Marketing release items", f"The curated, customer-facing sections of the sprint notes: {items['items']} items. Verification status by ticket key: "
        + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in marketing.items()) + ". Items with no ticket key cannot be verified this way, which is why the PR-level check above is the main evidence.",
        "## Sprints without PR links (6, 12, 13)",
        "These sprints list tickets, not PRs, so they are checked by ticket key instead. Ranges such as `BH-882–884` resolve only their first key, so this undercounts. Sprint 6 records no PRs or ticket keys at all.",
        table(["Status of listed tickets", "Tickets"], sorted(items["ticket_level_status"].items())),
        f"Of these, {items['ticket_level_kuri_led_in_production']} are in production with Kuri authoring half or more of the commits.",
        "## Limits", "- Sprint notes stop at Sprint 16 (Aug 2026). Later work is not counted until those notes land on the main branch.\n- `feat`, `fix` and `perf` are a proxy for user-facing. Some are internal improvements.\n- The share of Kuri's PRs reflects the concentration of work on one person (see [DATA-QUALITY.md](DATA-QUALITY.md)).\n- Business impact (revenue, adoption) is not measured here. See [business.md](business.md).",
    ])


def main() -> None:
    """Render every doc."""
    before_after_doc(load("codebase_reach.json"))
    ideas_doc(load("product_ideas.json"))
    milestones_doc(load("milestones.json"))
    production_doc(load("shipped_prs.json"), load("production_value.json"))
    print("rendered 4 docs")


if __name__ == "__main__":
    main()
