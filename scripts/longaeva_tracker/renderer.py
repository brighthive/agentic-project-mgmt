"""TRACKER.md renderer.

Auto-sections are overwritten on every refresh. Manual sections (Blockers /
This Week / Daily Notes / Open Questions) are preserved across refreshes via
in-page HTML-comment markers — see config.MANUAL_SECTION_MARKER_*.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

from .config import (
    MANUAL_SECTION_MARKER_BEGIN,
    MANUAL_SECTION_MARKER_END,
    MANUAL_SECTION_NAMES,
    RECENT_ACTIVITY_DAYS,
    RECENT_ACTIVITY_MAX_ROWS,
    SNOWFLAKE_TICKET_KEYS,
    SUMMARY_CLIP_CHARS,
)
from .expectations import EXPECTATION_PLAN, Expectation, Phase
from .github_client import GitHubPR
from .jira_client import JiraTicket

logger = logging.getLogger(__name__)

# Default content for manual sections on first generation.
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
        "_Filled during the trial — one entry per trial day. Use `### Day N — "
        "YYYY-MM-DD` headings._"
    ),
    "open-questions": (
        "_Questions for Grant or for the team. Mark `(Grant)` or `(team)` "
        "and date-stamp on resolution._"
    ),
}


def render_tracker(
    *,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
    existing_text: str | None,
    now: datetime | None = None,
) -> str:
    """Compose the full TRACKER.md content."""
    now = now or datetime.now(timezone.utc)
    auto = _render_auto_sections(tickets=tickets, pr_map=pr_map, now=now)
    manual = _render_manual_sections(existing_text=existing_text or "")
    return _compose(auto=auto, manual=manual, now=now)


def _compose(*, auto: str, manual: dict[str, str], now: datetime) -> str:
    """Compose the doc — blockers + this-week first (top-of-page urgency)."""
    parts: list[str] = [
        "# Longaeva — Live Tracker",
        "",
        f"_Last refreshed **{now.strftime('%Y-%m-%d %H:%M UTC')}** by `make longaeva-tracker`. "
        "Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, "
        "📝 Daily Notes, ❓ Open Questions) are preserved across refreshes._",
        "",
        "> **Phase**: Pre-trial · **Trial dates**: TBD with Grant · **Epic**: "
        "[BH-526](https://brighthiveio.atlassian.net/browse/BH-526)",
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
    return "\n".join(parts)


def _wrap_marker(name: str, *, body: str) -> str:
    begin = MANUAL_SECTION_MARKER_BEGIN.format(name=name)
    end = MANUAL_SECTION_MARKER_END.format(name=name)
    return f"{begin}\n\n{body.strip()}\n\n{end}"


def _render_manual_sections(*, existing_text: str) -> dict[str, str]:
    """Extract manual sections from prior TRACKER.md, falling back to defaults.

    Logs a warning when a marker exists in the prior text but extraction fails —
    catches the "contributor stripped a marker" case described in the QA review.
    """
    out: dict[str, str] = {}
    for name in MANUAL_SECTION_NAMES:
        body = _extract_section(existing_text=existing_text, name=name)
        if body is None and existing_text and name in existing_text:
            logger.warning(
                "Manual section '%s' had partial markers in prior TRACKER.md "
                "but could not be extracted — falling back to default. "
                "If you intentionally cleared this section, ignore. Otherwise, "
                "check that BEGIN/END markers are intact.",
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


# ── Auto sections ───────────────────────────────────────────────────


def _render_auto_sections(
    *,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
    now: datetime,
) -> str:
    chunks: list[str] = [
        _render_day_by_day(tickets=tickets, pr_map=pr_map),
        "",
        _render_summary(tickets=tickets, pr_map=pr_map),
        "",
        _render_status_grid(tickets=tickets, pr_map=pr_map),
        "",
        _render_snowflake_group(tickets=tickets, pr_map=pr_map),
        "",
        _render_recent_activity(tickets=tickets, now=now),
    ]
    return "\n".join(chunks)


def _render_summary(*, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]) -> str:
    total = len(tickets)
    done = sum(1 for t in tickets if t.is_done)
    in_progress = sum(1 for t in tickets if t.status_category == "In Progress")
    todo = total - done - in_progress
    points_done = sum(t.points or 0 for t in tickets if t.is_done)
    points_total = sum(t.points or 0 for t in tickets)

    open_prs = sum(
        1 for prs in pr_map.values() for pr in prs if pr.state == "OPEN" and not pr.is_draft
    )
    draft_prs = sum(1 for prs in pr_map.values() for pr in prs if pr.is_draft)
    merged_prs = sum(1 for prs in pr_map.values() for pr in prs if pr.state == "MERGED")

    lines = [
        "## 📊 Summary",
        "",
        f"- **{done}/{total}** tickets done · {in_progress} in progress · {todo} to do",
    ]
    if points_total > 0:
        pct = points_done / points_total * 100
        lines.append(
            f"- **{points_done:.0f}/{points_total:.0f}** points complete ({pct:.0f}%)"
        )
    lines.append(f"- PRs: {merged_prs} merged · {open_prs} ready for review · {draft_prs} draft")
    return "\n".join(lines)


def _render_status_grid(
    *, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> str:
    """Bucket tickets in workflow order: To Do → In Progress → In Review → Done."""
    buckets: dict[str, list[JiraTicket]] = {
        "🟡 To Do": [],
        "🟢 In Progress": [],
        "🔵 In Review": [],
        "✅ Done": [],
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

    # Drop the Pts column entirely if no ticket has points (BrightHive board
    # doesn't always estimate). Keeps tables tight.
    show_points = any(t.points for t in tickets)

    lines = ["## 📋 Tickets by status", ""]
    for label, group in buckets.items():
        if not group:
            continue
        lines.append(f"### {label} ({len(group)})")
        lines.append("")
        if show_points:
            lines.append("| Key | Summary | Assignee | Pts | PR |")
            lines.append("|---|---|---|---|---|")
        else:
            lines.append("| Key | Summary | Assignee | PR |")
            lines.append("|---|---|---|---|")
        for t in sorted(group, key=lambda x: x.key):
            pr_links = _format_pr_links(pr_map=pr_map, key=t.key)
            assignee = t.assignee_name or "_unassigned_"
            summary = _clip(t.summary, max_len=SUMMARY_CLIP_CHARS)
            if show_points:
                points = f"{t.points:.0f}" if t.points else "—"
                lines.append(
                    f"| [{t.key}]({t.url}) | {summary} | {assignee} | {points} | {pr_links} |"
                )
            else:
                lines.append(
                    f"| [{t.key}]({t.url}) | {summary} | {assignee} | {pr_links} |"
                )
        lines.append("")
    return "\n".join(lines)


def _render_snowflake_group(
    *, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> str:
    in_scope = [t for t in tickets if t.key in SNOWFLAKE_TICKET_KEYS]
    if not in_scope:
        return ""
    done = sum(1 for t in in_scope if t.is_done)
    lines = [
        f"## ❄️ Snowflake integration ({done}/{len(in_scope)})",
        "",
        "| Key | Summary | Status | PR |",
        "|---|---|---|---|",
    ]
    for t in sorted(in_scope, key=lambda x: x.key):
        pr_links = _format_pr_links(pr_map=pr_map, key=t.key)
        summary = _clip(t.summary, max_len=SUMMARY_CLIP_CHARS)
        lines.append(
            f"| [{t.key}]({t.url}) | {summary} | {t.status} | {pr_links} |"
        )
    return "\n".join(lines)


def _render_recent_activity(*, tickets: list[JiraTicket], now: datetime) -> str:
    cutoff = now.timestamp() - RECENT_ACTIVITY_DAYS * 86400
    # Parse once per ticket and reuse for filter + sort.
    parsed = [(t, _parse_iso(t.updated)) for t in tickets]
    recent = [(t, ts) for t, ts in parsed if ts and ts.timestamp() >= cutoff]
    recent.sort(key=lambda pair: pair[1] or datetime.min, reverse=True)

    lines = [f"## 🕒 Recent activity ({RECENT_ACTIVITY_DAYS} days)", ""]
    if not recent:
        lines.append(f"_No ticket updates in the last {RECENT_ACTIVITY_DAYS} days._")
        return "\n".join(lines)

    capped = recent[:RECENT_ACTIVITY_MAX_ROWS]
    for t, ts in capped:
        when = (ts or now).strftime("%Y-%m-%d")
        assignee = t.assignee_name or "_unassigned_"
        lines.append(f"- **{when}** · [{t.key}]({t.url}) — {t.status} · {assignee}")
    if len(recent) > RECENT_ACTIVITY_MAX_ROWS:
        lines.append(
            f"\n_(+{len(recent) - RECENT_ACTIVITY_MAX_ROWS} older updates not shown.)_"
        )
    return "\n".join(lines)


# ── Helpers ─────────────────────────────────────────────────────────


# ── Day-by-day expectations matrix ────────────────────────────────


def _render_day_by_day(
    *, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> str:
    """Render the day-by-day expectation matrix — auto-checked from Jira/PRs.

    Goes from empty to green as tickets close and PRs merge. Manual
    expectations (linked=()) render as `[ ]` until a teammate flips them to
    `[x]` (preserved across refreshes — they live in the auto section but
    once flipped are themselves a stable pattern).
    """
    ticket_statuses = {t.key: t.status_category for t in tickets}
    merged_pr_keys = {
        f"{pr.short_repo}#{pr.number}"
        for prs in pr_map.values()
        for pr in prs
        if pr.state == "MERGED"
    }

    lines = [
        "## 🗓️ Day-by-day — what to expect",
        "",
        "_Auto-fills as linked tickets close and PRs merge. Manual rows "
        "(no linked items) are flipped by hand once the outcome lands._",
        "",
    ]
    for phase in EXPECTATION_PLAN:
        green, total = _phase_progress(
            phase=phase,
            ticket_statuses=ticket_statuses,
            merged_pr_keys=merged_pr_keys,
        )
        lines.append(f"### {phase.title} ({green}/{total})")
        lines.append("")
        lines.append(f"_{phase.description}_")
        lines.append("")
        lines.append("| | Day | Outcome | Linked |")
        lines.append("|---|---|---|---|")
        for exp in phase.expectations:
            checkbox = _expectation_checkbox(
                expectation=exp,
                ticket_statuses=ticket_statuses,
                merged_pr_keys=merged_pr_keys,
            )
            linked = _format_linked(linked=exp.linked, pr_map=pr_map)
            lines.append(f"| {checkbox} | {exp.day} | {exp.outcome} | {linked} |")
        lines.append("")
    return "\n".join(lines)


def _expectation_checkbox(
    *,
    expectation: Expectation,
    ticket_statuses: dict[str, str],
    merged_pr_keys: set[str],
) -> str:
    """Auto-checked when all linked items resolve; `[ ]` otherwise."""
    state = expectation.is_green(
        ticket_statuses=ticket_statuses, merged_pr_keys=merged_pr_keys
    )
    if state is True:
        return "✅"
    if state is False:
        return "🔲"
    return "⬜"  # manual — visually distinct from auto-pending


def _phase_progress(
    *,
    phase: Phase,
    ticket_statuses: dict[str, str],
    merged_pr_keys: set[str],
) -> tuple[int, int]:
    """Count green / total expectations in a phase, ignoring manual rows."""
    auto_total = 0
    auto_green = 0
    for exp in phase.expectations:
        result = exp.is_green(
            ticket_statuses=ticket_statuses, merged_pr_keys=merged_pr_keys
        )
        if result is None:
            continue
        auto_total += 1
        if result:
            auto_green += 1
    return auto_green, auto_total


def _format_linked(
    *,
    linked: tuple[str, ...],
    pr_map: dict[str, list[GitHubPR]],
) -> str:
    """Format linked items as Markdown links — Jira for tickets, PR URL for PRs."""
    if not linked:
        return "_manual_"
    parts: list[str] = []
    for item in linked:
        if item.startswith("BH-"):
            parts.append(f"[{item}](https://brighthiveio.atlassian.net/browse/{item})")
            continue
        # PR shorthand — find a matching PR in pr_map for the URL.
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


# ── Existing helpers ──────────────────────────────────────────────


def _has_open_pr(*, pr_map: dict[str, list[GitHubPR]], key: str) -> bool:
    return any(pr.state == "OPEN" for pr in pr_map.get(key, []))


def _format_pr_links(*, pr_map: dict[str, list[GitHubPR]], key: str) -> str:
    prs = pr_map.get(key, [])
    if not prs:
        return "—"
    # Most recent first by repo/number; cap at 3 to keep cells tight.
    sorted_prs = sorted(prs, key=lambda p: (p.repo, -p.number))[:3]
    return "<br>".join(f"[{pr.label}]({pr.url})" for pr in sorted_prs)


def _clip(text: str, *, max_len: int) -> str:
    """Trim with an ellipsis when over `max_len`. Prefers word-boundary endings."""
    if len(text) <= max_len:
        return text
    head = text[: max_len - 1].rstrip()
    # Snap back to the last whole word if there's a space within the last 12 chars.
    last_space = head.rfind(" ")
    if last_space >= max_len - 12:
        head = head[:last_space].rstrip()
    return head + "…"


def _parse_iso(value: str) -> datetime | None:
    """Parse Jira's ISO-8601 timestamp; return None on malformed input."""
    if not value:
        return None
    # Jira returns e.g. "2026-06-01T12:34:56.789-0600" — Python 3.11+ handles it.
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        logger.debug("Failed to parse Jira timestamp: %r", value)
        return None
