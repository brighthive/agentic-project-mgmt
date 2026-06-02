"""Tests for the longaeva tracker.

Pure-Python tests — no Jira / GitHub / Slack network calls. Uses the
ScaffoldResult-style approach (DI for dependencies; no @patch needed).

Required tests, per the 4-agent review pre-merge:
1. Manual sections survive a round-trip (architect + QA).
2. Status transition (In Progress → Done) shows up in the diff (QA).
3. Bootstrap diff is empty on first run (senior-python + QA).
4. Type-string smoke: every BH-XXX in scope routes through config constants.
"""

from __future__ import annotations

from datetime import datetime, timezone

from scripts.longaeva_tracker.github_client import GitHubPR
from scripts.longaeva_tracker.jira_client import JiraTicket
from scripts.longaeva_tracker.renderer import render_tracker
from scripts.longaeva_tracker.snapshot import (
    build_snapshot,
    diff_snapshots,
)


def _t(key: str, *, status: str = "To Do", category: str = "To Do") -> JiraTicket:
    return JiraTicket(
        key=key,
        summary=f"summary for {key}",
        status=status,
        status_category=category,
        assignee_name="Test User",
        assignee_email=None,
        priority="Medium",
        issue_type="Task",
        labels=(),
        parent_key="BH-526",
        points=1,
        updated="2026-06-01T12:00:00.000-0600",
        created="2026-05-29T09:00:00.000-0600",
    )


def _pr(repo: str, num: int, *, state: str = "OPEN", draft: bool = False) -> GitHubPR:
    return GitHubPR(
        repo=repo,
        number=num,
        title=f"PR {num}",
        state=state,
        is_draft=draft,
        author="drchinca",
        url=f"https://github.com/{repo}/pull/{num}",
        body_excerpt="",
        head_branch=f"x/{num}",
    )


def _now() -> datetime:
    return datetime(2026, 6, 2, 12, 0, 0, tzinfo=timezone.utc)


# ── 1. Manual sections survive round-trip ──────────────────────────


class TestManualSectionRoundTrip:
    def test_manual_body_preserved_across_refreshes(self):
        # First pass — placeholders.
        first = render_tracker(
            tickets=[_t("BH-527")], pr_map={}, existing_text=None, now=_now()
        )

        # Edit the blockers body in place — simulate a teammate adding a blocker.
        custom_blockers = "**🚨 BH-554** — staging Snowflake creds rotated, need refresh (raised 2026-06-02 by @ahmed)"
        edited = first.replace(
            "_No active blockers. Add lines in the form: `**🚨 BH-XXX** — short description (raised YYYY-MM-DD by @owner)`._",
            custom_blockers,
        )
        assert custom_blockers in edited

        # Refresh again — different ticket data — and assert body is preserved.
        second = render_tracker(
            tickets=[_t("BH-527", status="In Review", category="In Progress")],
            pr_map={"BH-527": [_pr("brighthive/brightbot", 488)]},
            existing_text=edited,
            now=_now(),
        )
        assert custom_blockers in second
        # And the auto section reflects the new ticket data.
        assert "🔵 In Review" in second

    def test_default_used_when_no_prior_text(self):
        out = render_tracker(tickets=[], pr_map={}, existing_text=None, now=_now())
        assert "_No active blockers" in out

    def test_partial_marker_strip_logs_warning(self, caplog):
        """Contributor strips an END marker — renderer should warn, not silently overwrite."""
        # Build a tracker with the BEGIN marker present but the END deleted.
        # Manual section contains "this-week" string (matches MANUAL_SECTION_NAMES check).
        broken = (
            "<!-- TRACKER:MANUAL:BEGIN this-week -->\n\n"
            "Marwan owns BH-527 + BH-528 this week\n\n"
            # END marker removed
        )
        with caplog.at_level("WARNING"):
            out = render_tracker(
                tickets=[], pr_map={}, existing_text=broken, now=_now()
            )
        assert any("partial markers" in r.getMessage() for r in caplog.records)


# ── 2. Status transition shows up in diff ──────────────────────────


class TestStatusTransitionDiff:
    def test_in_progress_to_done_is_a_status_change(self):
        before = build_snapshot(
            tickets=[_t("BH-527", status="In Progress", category="In Progress")],
            pr_map={},
        )
        after = build_snapshot(
            tickets=[_t("BH-527", status="Done", category="Done")],
            pr_map={},
        )
        diff = diff_snapshots(previous=before, current=after)
        assert ("BH-527", "In Progress", "Done") in diff.status_changes

    def test_no_change_means_empty_diff(self):
        snap = build_snapshot(tickets=[_t("BH-527")], pr_map={})
        diff = diff_snapshots(previous=snap, current=snap)
        assert diff.is_empty


# ── 3. Bootstrap diff is empty on first run ────────────────────────


class TestBootstrapDiff:
    def test_first_run_with_no_prior_snapshot_is_empty(self):
        current = build_snapshot(
            tickets=[_t("BH-527"), _t("BH-528"), _t("BH-549")],
            pr_map={"BH-527": [_pr("brighthive/brightbot", 488)]},
        )
        diff = diff_snapshots(previous=None, current=current)
        assert diff.is_empty
        assert diff.new_tickets == []
        assert diff.new_prs == []


# ── 4. Type-string discipline ─────────────────────────────────────


class TestTypeStringDiscipline:
    def test_jira_browse_base_used_for_ticket_url(self):
        from scripts.longaeva_tracker.config import JIRA_BROWSE_BASE
        ticket = _t("BH-527")
        assert ticket.url == f"{JIRA_BROWSE_BASE}/BH-527"

    def test_snowflake_keys_match_ticket_format(self):
        import re
        from scripts.longaeva_tracker.config import SNOWFLAKE_TICKET_KEYS
        for key in SNOWFLAKE_TICKET_KEYS:
            assert re.fullmatch(r"BH-\d+", key), f"Malformed Snowflake key: {key}"

    def test_recent_activity_uses_constant(self):
        out = render_tracker(tickets=[], pr_map={}, existing_text=None, now=_now())
        from scripts.longaeva_tracker.config import RECENT_ACTIVITY_DAYS
        assert f"({RECENT_ACTIVITY_DAYS} days)" in out


# ── 5. Renderer: bucket order + empty-points-column suppression ────


class TestRendererBuckets:
    def test_workflow_order_to_do_first_done_last(self):
        out = render_tracker(
            tickets=[
                _t("BH-100", status="Done", category="Done"),
                _t("BH-200", status="To Do", category="To Do"),
                _t("BH-300", status="In Progress", category="In Progress"),
            ],
            pr_map={},
            existing_text=None,
            now=_now(),
        )
        idx_todo = out.find("🟡 To Do")
        idx_progress = out.find("🟢 In Progress")
        idx_done = out.find("✅ Done")
        assert idx_todo < idx_progress < idx_done

    def test_day_by_day_section_renders_at_top(self):
        out = render_tracker(tickets=[], pr_map={}, existing_text=None, now=_now())
        # Day-by-day matrix should appear before the summary section.
        idx_day = out.find("🗓️ Day-by-day")
        idx_summary = out.find("📊 Summary")
        assert idx_day != -1
        assert idx_summary != -1
        assert idx_day < idx_summary

    def test_day_by_day_auto_checks_when_ticket_done(self):
        # BH-552 is in the Pre-trial phase as a single-ticket expectation.
        out = render_tracker(
            tickets=[_t("BH-552", status="Done", category="Done")],
            pr_map={},
            existing_text=None,
            now=_now(),
        )
        # Find the row for the audit outcome and assert ✅.
        for line in out.split("\n"):
            if "Webapp Snowflake form audit" in line:
                assert "✅" in line, f"Expected ✅ in {line!r}"
                break
        else:
            raise AssertionError("Pre-trial audit expectation row not found")

    def test_day_by_day_open_when_ticket_not_done(self):
        out = render_tracker(
            tickets=[_t("BH-552", status="To Do", category="To Do")],
            pr_map={},
            existing_text=None,
            now=_now(),
        )
        for line in out.split("\n"):
            if "Webapp Snowflake form audit" in line:
                assert "🔲" in line, f"Expected 🔲 in {line!r}"
                break
        else:
            raise AssertionError("Pre-trial audit expectation row not found")

    def test_manual_outcome_renders_as_open_box(self):
        # "Trial start date confirmed" has no linked items — manual.
        out = render_tracker(tickets=[], pr_map={}, existing_text=None, now=_now())
        for line in out.split("\n"):
            if "Trial start date confirmed" in line:
                assert "⬜" in line, f"Expected ⬜ (manual) in {line!r}"
                break
        else:
            raise AssertionError("Manual expectation row not found")

    def test_pts_column_dropped_when_no_estimates(self):
        ticket = JiraTicket(
            key="BH-1", summary="x", status="To Do", status_category="To Do",
            assignee_name=None, assignee_email=None, priority=None, issue_type="Task",
            labels=(), parent_key=None, points=None,  # no points
            updated="2026-06-01T12:00:00+00:00", created="2026-06-01T12:00:00+00:00",
        )
        out = render_tracker(tickets=[ticket], pr_map={}, existing_text=None, now=_now())
        assert "Pts" not in out
