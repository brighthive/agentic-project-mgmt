"""TRACKER.md renderer — config-driven via PocConfig.

Auto sections (day-by-day, scoreboard, summary, status grid, recent activity)
are overwritten on every refresh. Manual sections (Blockers / This Week /
Daily Notes / Open Questions) are preserved across refreshes via in-page
HTML comment markers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .github_client import GitHubPR
from .jira_client import JIRA_BROWSE_BASE, JiraTicket
from .loader import Expectation, Phase, PocConfig

logger = logging.getLogger(__name__)

# ── Manual section markers ──────────────────────────────────────────

MANUAL_SECTION_MARKER_BEGIN = "<!-- TRACKER:MANUAL:BEGIN {name} -->"
MANUAL_SECTION_MARKER_END = "<!-- TRACKER:MANUAL:END {name} -->"
MANUAL_SECTION_NAMES = ("blockers", "this-week", "daily-notes", "open-questions")
_MANUAL_DEFAULTS: dict[str, str] = {
    "blockers": (
        "_No active blockers. Add lines in the form: `**🚨 BH-XXX** — short "
        "description (raised YYYY-MM-DD by @owner)`._"
    ),
    "this-week": (
        "_Weekly standup output. Update Monday morning with the week's "
        "ticket commitments by owner._"
    ),
    "daily-notes": (
        "_Filled during the trial — one entry per trial day. Use "
        "`### Day N — YYYY-MM-DD` headings._"
    ),
    "open-questions": (
        "_Questions for the customer or for the team. Mark "
        "`(customer)` or `(team)` and date-stamp on resolution._"
    ),
}

# ── Render bounds ──────────────────────────────────────────────────

RECENT_ACTIVITY_DAYS = 14
RECENT_ACTIVITY_MAX_ROWS = 20
SUMMARY_CLIP_CHARS = 70


# ── Public entry ───────────────────────────────────────────────────


def render_tracker(
    *,
    config: PocConfig,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
    existing_text: str | None,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    auto = _render_auto_sections(
        config=config, tickets=tickets, pr_map=pr_map, now=now
    )
    manual = _read_manual_sections(existing_text=existing_text or "")
    return _compose(config=config, auto=auto, manual=manual, now=now)


def compute_phase_progress(
    *,
    config: PocConfig,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
) -> list[tuple[str, int, int, int]]:
    """Used by the Slack post to show per-phase progress without re-rendering."""
    ticket_statuses = {t.key: t.status_category for t in tickets}
    merged_pr_keys = _merged_pr_keys(pr_map=pr_map)
    open_pr_ticket_keys = _open_pr_ticket_keys(pr_map=pr_map)
    out = []
    for phase in config.phases:
        green, wip, total = _phase_progress(
            phase=phase,
            ticket_statuses=ticket_statuses,
            merged_pr_keys=merged_pr_keys,
            open_pr_ticket_keys=open_pr_ticket_keys,
        )
        out.append((phase.title, green, wip, total))
    return out


# ── Composition ─────────────────────────────────────────────────────


def _compose(
    *, config: PocConfig, auto: str, manual: dict[str, str], now: datetime
) -> str:
    return "\n".join(
        [
            f"# {config.slug.title()} — Live Tracker",
            "",
            f"_Last refreshed **{now.strftime('%Y-%m-%d %H:%M UTC')}** by "
            f"`make {config.slug}-tracker`. Auto sections are overwritten — "
            "manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, "
            "❓ Open Questions) are preserved._",
            "",
            f"> **Trial dates**: {config.trial_dates} · "
            f"**Epic**: [{config.epic}]({JIRA_BROWSE_BASE}/{config.epic})",
            "",
            "---",
            "",
            "## 🚨 Blockers",
            "",
            _wrap_marker("blockers", body=manual["blockers"]),
            "",
            "## 🎯 This Week",
            "",
            _wrap_marker("this-week", body=manual["this-week"]),
            "",
            "---",
            "",
            auto,
            "",
            "## 📝 Daily Notes",
            "",
            _wrap_marker("daily-notes", body=manual["daily-notes"]),
            "",
            "## ❓ Open Questions",
            "",
            _wrap_marker("open-questions", body=manual["open-questions"]),
            "",
        ]
    )


def _wrap_marker(name: str, *, body: str) -> str:
    begin = MANUAL_SECTION_MARKER_BEGIN.format(name=name)
    end = MANUAL_SECTION_MARKER_END.format(name=name)
    return f"{begin}\n\n{body.strip()}\n\n{end}"


def _read_manual_sections(*, existing_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in MANUAL_SECTION_NAMES:
        body = _extract_section(existing_text=existing_text, name=name)
        if body is None and existing_text and name in existing_text:
            logger.warning(
                "Manual section %r had partial markers; falling back to default.",
                name,
            )
        out[name] = body or _MANUAL_DEFAULTS[name]
    return out


def _extract_section(*, existing_text: str, name: str) -> str | None:
    begin = MANUAL_SECTION_MARKER_BEGIN.format(name=name)
    end = MANUAL_SECTION_MARKER_END.format(name=name)
    start = existing_text.find(begin)
    if start < 0:
        return None
    start += len(begin)
    stop = existing_text.find(end, start)
    if stop < 0:
        return None
    return existing_text[start:stop].strip()


# ── Auto sections ──────────────────────────────────────────────────


def _render_auto_sections(
    *,
    config: PocConfig,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
    now: datetime,
) -> str:
    chunks = [
        _render_day_by_day(config=config, tickets=tickets, pr_map=pr_map),
        "",
        _render_scoreboard(config=config, tickets=tickets, pr_map=pr_map),
        "",
        _render_summary(tickets=tickets, pr_map=pr_map),
        "",
        _render_status_grid(tickets=tickets, pr_map=pr_map),
        "",
        _render_recent_activity(tickets=tickets, now=now),
    ]
    return "\n".join(chunks)


def _render_day_by_day(
    *,
    config: PocConfig,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
) -> str:
    ticket_statuses = {t.key: t.status_category for t in tickets}
    merged_pr_keys = _merged_pr_keys(pr_map=pr_map)
    open_pr_ticket_keys = _open_pr_ticket_keys(pr_map=pr_map)

    lines = [
        "## 🗓️ Day-by-day — task / day / progress",
        "",
        "_Legend: 🟢 done (ticket closed / PR merged) · 🟡 in progress (PR open or "
        "ticket in review) · ⬜ not started · 🔲 awaiting external/manual. "
        "Auto-fills as tickets move and PRs merge._",
        "",
    ]
    for phase in config.phases:
        green, wip, total = _phase_progress(
            phase=phase,
            ticket_statuses=ticket_statuses,
            merged_pr_keys=merged_pr_keys,
            open_pr_ticket_keys=open_pr_ticket_keys,
        )
        wip_note = f", {wip} 🟡" if wip else ""
        lines.append(f"### {phase.title} ({green}/{total} 🟢{wip_note})")
        lines.append("")
        if phase.description:
            lines.append(f"_{phase.description}_")
            lines.append("")
        lines.append("| | Day | Outcome | Linked |")
        lines.append("|---|---|---|---|")
        for exp in phase.expectations:
            checkbox = _expectation_checkbox(
                expectation=exp,
                ticket_statuses=ticket_statuses,
                merged_pr_keys=merged_pr_keys,
                open_pr_ticket_keys=open_pr_ticket_keys,
            )
            linked = _format_linked(linked=exp.linked, pr_map=pr_map)
            lines.append(f"| {checkbox} | {exp.day} | {exp.outcome} | {linked} |")
        lines.append("")
    return "\n".join(lines)


def _render_scoreboard(
    *,
    config: PocConfig,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
) -> str:
    by_assignee: dict[str, list[JiraTicket]] = {}
    for ticket in tickets:
        by_assignee.setdefault(ticket.assignee_name or "_unassigned_", []).append(
            ticket
        )

    lines = ["## 🏁 Who's done what", ""]
    if config.ownership:
        lines.append("**Lanes**")
        for owner in config.ownership:
            lines.append(f"- **{owner.owner}** — {owner.lane}")
        lines.append("")

    lines.extend(
        [
            "| Owner | ✅ Done | 🔵 In flight | 🟡 Queued | Last shipped |",
            "|---|---|---|---|---|",
        ]
    )
    rows = []
    for owner, owner_tickets in by_assignee.items():
        done = [t for t in owner_tickets if t.is_done]
        in_flight = [
            t for t in owner_tickets
            if not t.is_done
            and (t.status_category == "In Progress" or _has_open_pr(pr_map=pr_map, key=t.key))
        ]
        queued = [
            t for t in owner_tickets
            if not t.is_done
            and t.status_category != "In Progress"
            and not _has_open_pr(pr_map=pr_map, key=t.key)
        ]
        rows.append((owner, done, in_flight, queued, _last_shipped(tickets=done)))

    rows.sort(key=lambda r: (r[0] == "_unassigned_", -len(r[1]), r[0]))
    for owner, done, in_flight, queued, last_shipped in rows:
        lines.append(
            f"| **{owner}** | {len(done)} | {len(in_flight)} | "
            f"{len(queued)} | {last_shipped} |"
        )
    return "\n".join(lines)


def _render_summary(
    *, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> str:
    total = len(tickets)
    done = sum(1 for t in tickets if t.is_done)
    in_progress = sum(1 for t in tickets if t.status_category == "In Progress")
    todo = total - done - in_progress
    open_prs = sum(
        1 for prs in pr_map.values() for pr in prs
        if pr.state == "OPEN" and not pr.is_draft
    )
    draft_prs = sum(1 for prs in pr_map.values() for pr in prs if pr.is_draft)
    merged_prs = sum(1 for prs in pr_map.values() for pr in prs if pr.state == "MERGED")
    return "\n".join(
        [
            "## 📊 Summary",
            "",
            f"- **{done}/{total}** tickets done · {in_progress} in progress · {todo} to do",
            f"- PRs: {merged_prs} merged · {open_prs} ready for review · {draft_prs} draft",
        ]
    )


def _render_status_grid(
    *, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> str:
    buckets: dict[str, list[JiraTicket]] = {
        "🟡 To Do": [], "🟢 In Progress": [], "🔵 In Review": [], "✅ Done": [],
    }
    for t in tickets:
        if t.is_done:
            buckets["✅ Done"].append(t)
        elif _has_open_pr(pr_map=pr_map, key=t.key):
            buckets["🔵 In Review"].append(t)
        elif t.status_category == "In Progress":
            buckets["🟢 In Progress"].append(t)
        else:
            buckets["🟡 To Do"].append(t)

    lines = ["## 📋 Tickets by status", ""]
    for label, group in buckets.items():
        if not group:
            continue
        lines.append(f"### {label} ({len(group)})")
        lines.append("")
        lines.append("| Key | Summary | Assignee | PR |")
        lines.append("|---|---|---|---|")
        for t in sorted(group, key=lambda x: x.key):
            pr_links = _format_pr_links(pr_map=pr_map, key=t.key)
            assignee = t.assignee_name or "_unassigned_"
            summary = _clip(t.summary, max_len=SUMMARY_CLIP_CHARS)
            lines.append(
                f"| [{t.key}]({t.url}) | {summary} | {assignee} | {pr_links} |"
            )
        lines.append("")
    return "\n".join(lines)


def _render_recent_activity(*, tickets: list[JiraTicket], now: datetime) -> str:
    cutoff = now.timestamp() - RECENT_ACTIVITY_DAYS * 86400
    parsed = [(t, _parse_iso(t.updated)) for t in tickets]
    recent = [(t, ts) for t, ts in parsed if ts and ts.timestamp() >= cutoff]
    recent.sort(key=lambda pair: pair[1] or datetime.min, reverse=True)
    lines = [f"## 🕒 Recent activity ({RECENT_ACTIVITY_DAYS} days)", ""]
    if not recent:
        lines.append(f"_No ticket updates in the last {RECENT_ACTIVITY_DAYS} days._")
        return "\n".join(lines)
    for t, ts in recent[:RECENT_ACTIVITY_MAX_ROWS]:
        when = (ts or now).strftime("%Y-%m-%d")
        assignee = t.assignee_name or "_unassigned_"
        lines.append(f"- **{when}** · [{t.key}]({t.url}) — {t.status} · {assignee}")
    if len(recent) > RECENT_ACTIVITY_MAX_ROWS:
        lines.append(
            f"\n_(+{len(recent) - RECENT_ACTIVITY_MAX_ROWS} older updates not shown.)_"
        )
    return "\n".join(lines)


# ── Helpers ────────────────────────────────────────────────────────


def _expectation_checkbox(
    *,
    expectation: Expectation,
    ticket_statuses: dict[str, str],
    merged_pr_keys: set[str],
    open_pr_ticket_keys: set[str],
) -> str:
    state = expectation.is_green(
        ticket_statuses=ticket_statuses, merged_pr_keys=merged_pr_keys
    )
    if state is None:
        return "🔲"  # manual / awaiting external (no linked item)
    if state is True:
        return "🟢"  # done — ticket closed / PR merged
    if expectation.is_wip(
        ticket_statuses=ticket_statuses,
        merged_pr_keys=merged_pr_keys,
        open_pr_ticket_keys=open_pr_ticket_keys,
    ):
        return "🟡"  # in progress — PR open or ticket in review
    return "⬜"  # linked but not started


def _phase_progress(
    *,
    phase: Phase,
    ticket_statuses: dict[str, str],
    merged_pr_keys: set[str],
    open_pr_ticket_keys: set[str],
) -> tuple[int, int, int]:
    auto_total = 0
    auto_green = 0
    auto_wip = 0
    for exp in phase.expectations:
        result = exp.is_green(
            ticket_statuses=ticket_statuses, merged_pr_keys=merged_pr_keys
        )
        if result is None:
            continue
        auto_total += 1
        if result:
            auto_green += 1
        elif exp.is_wip(
            ticket_statuses=ticket_statuses,
            merged_pr_keys=merged_pr_keys,
            open_pr_ticket_keys=open_pr_ticket_keys,
        ):
            auto_wip += 1
    return auto_green, auto_wip, auto_total


def _open_pr_ticket_keys(*, pr_map: dict[str, list[GitHubPR]]) -> set[str]:
    return {
        key
        for key, prs in pr_map.items()
        if any(pr.state == "OPEN" for pr in prs)
    }


def _merged_pr_keys(*, pr_map: dict[str, list[GitHubPR]]) -> set[str]:
    return {
        f"{pr.short_repo}#{pr.number}"
        for prs in pr_map.values()
        for pr in prs
        if pr.state == "MERGED"
    }


def _format_linked(
    *, linked: tuple[str, ...], pr_map: dict[str, list[GitHubPR]]
) -> str:
    if not linked:
        return "_manual_"
    parts: list[str] = []
    for item in linked:
        if item.startswith("BH-"):
            parts.append(f"[{item}]({JIRA_BROWSE_BASE}/{item})")
            continue
        pr_url: str | None = None
        for prs in pr_map.values():
            for pr in prs:
                if f"{pr.short_repo}#{pr.number}" == item:
                    pr_url = pr.url
                    break
            if pr_url:
                break
        parts.append(f"[{item}]({pr_url})" if pr_url else item)
    return ", ".join(parts)


def _has_open_pr(*, pr_map: dict[str, list[GitHubPR]], key: str) -> bool:
    return any(pr.state == "OPEN" for pr in pr_map.get(key, []))


def _format_pr_links(*, pr_map: dict[str, list[GitHubPR]], key: str) -> str:
    prs = pr_map.get(key, [])
    if not prs:
        return "—"
    sorted_prs = sorted(prs, key=lambda p: (p.repo, -p.number))[:3]
    return "<br>".join(f"[{pr.label}]({pr.url})" for pr in sorted_prs)


def _last_shipped(*, tickets: list[JiraTicket]) -> str:
    if not tickets:
        return "—"
    parsed = [(t, _parse_iso(t.updated)) for t in tickets]
    parsed.sort(key=lambda pair: pair[1] or datetime.min, reverse=True)
    t, _ = parsed[0]
    return f"[{t.key}]({t.url}) {_clip(t.summary, max_len=40)}"


def _clip(text: str, *, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    head = text[: max_len - 1].rstrip()
    last_space = head.rfind(" ")
    if last_space >= max_len - 12:
        head = head[:last_space].rstrip()
    return head + "…"


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
