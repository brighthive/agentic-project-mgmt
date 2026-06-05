"""Tests for the YAML loader + renderer integration.

Pure tests — don't hit Jira / GitHub / Slack. Validate the agnostic shape:
loading two different client YAML files produces two valid PocConfig objects
with no shared global state.
"""

from __future__ import annotations

import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.poc_tracker.github_client import GitHubPR
from scripts.poc_tracker.jira_client import JiraTicket
from scripts.poc_tracker.loader import (
    Auth,
    Expectation,
    PocConfig,
    load_config,
)
from scripts.poc_tracker.renderer import compute_phase_progress, render_tracker


@pytest.fixture(autouse=True)
def _set_jira_env(monkeypatch):
    monkeypatch.setenv("JIRA_USER_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "fake-token")
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)


def _write_yaml(*, repo_root: Path, slug: str, body: str) -> None:
    path = repo_root / "clients" / "trials" / slug
    path.mkdir(parents=True, exist_ok=True)
    (path / "poc.yaml").write_text(body)


def _now() -> datetime:
    return datetime(2026, 6, 2, 12, 0, 0, tzinfo=timezone.utc)


# ── Loader ─────────────────────────────────────────────────────────


class TestLoader:
    def test_loads_minimal_yaml(self, tmp_path):
        _write_yaml(
            repo_root=tmp_path,
            slug="acme",
            body=textwrap.dedent("""
                slug: acme
                trial_dates: "2026-07-01 → 2026-07-14"
                scope:
                  epic: BH-999
                repos:
                  - acme/repo
                slack:
                  channel_id: C123
            """).strip(),
        )
        config = load_config(slug="acme", repo_root=tmp_path)
        assert config.slug == "acme"
        assert config.epic == "BH-999"
        assert config.repos == ("acme/repo",)
        assert config.slack_channel_id == "C123"

    def test_slug_mismatch_raises(self, tmp_path):
        _write_yaml(
            repo_root=tmp_path, slug="acme",
            body="slug: not-acme\nscope:\n  epic: BH-1\n",
        )
        with pytest.raises(ValueError, match="slug mismatch"):
            load_config(slug="acme", repo_root=tmp_path)

    def test_missing_epic_raises(self, tmp_path):
        _write_yaml(
            repo_root=tmp_path, slug="acme",
            body="slug: acme\nscope: {}\n",
        )
        with pytest.raises(ValueError, match="scope.epic is required"):
            load_config(slug="acme", repo_root=tmp_path)

    def test_missing_yaml_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(slug="ghost", repo_root=tmp_path)

    def test_two_clients_dont_share_state(self, tmp_path):
        for slug, epic in (("acme", "BH-1"), ("widgets", "BH-2")):
            _write_yaml(
                repo_root=tmp_path, slug=slug,
                body=f"slug: {slug}\nscope:\n  epic: {epic}\nrepos: []\n",
            )
        a = load_config(slug="acme", repo_root=tmp_path)
        w = load_config(slug="widgets", repo_root=tmp_path)
        assert a.epic == "BH-1"
        assert w.epic == "BH-2"
        # Different config objects — agnosticism check
        assert a is not w


# ── Expectation logic ──────────────────────────────────────────────


class TestExpectationLogic:
    def test_green_when_all_linked_done(self):
        exp = Expectation(day="Day 1", outcome="x", linked=("BH-1", "BH-2"))
        assert exp.is_green(
            ticket_statuses={"BH-1": "Done", "BH-2": "Done"},
            merged_pr_keys=set(),
        ) is True

    def test_not_green_when_any_open(self):
        exp = Expectation(day="Day 1", outcome="x", linked=("BH-1", "BH-2"))
        assert exp.is_green(
            ticket_statuses={"BH-1": "Done", "BH-2": "In Progress"},
            merged_pr_keys=set(),
        ) is False

    def test_pr_link_green_when_merged(self):
        exp = Expectation(day="Day 1", outcome="x", linked=("repo#42",))
        assert exp.is_green(
            ticket_statuses={}, merged_pr_keys={"repo#42"},
        ) is True

    def test_manual_returns_none(self):
        exp = Expectation(day="Day 1", outcome="x", linked=())
        assert exp.is_green(ticket_statuses={}, merged_pr_keys=set()) is None


# ── Renderer end-to-end ────────────────────────────────────────────


def _config(*, tmp_path) -> PocConfig:
    _write_yaml(
        repo_root=tmp_path, slug="acme",
        body=textwrap.dedent("""
            slug: acme
            trial_dates: "TBD"
            scope:
              epic: BH-100
            repos:
              - acme/repo
            slack:
              channel_id: C123
            ownership:
              - owner: Alice
                lane: backend
            phases:
              - title: Phase 1
                description: First phase
                expectations:
                  - day: Pre-trial
                    outcome: ship feature
                    linked: [BH-101]
                  - day: Pre-trial
                    outcome: confirm date
        """).strip(),
    )
    return load_config(slug="acme", repo_root=tmp_path)


def _ticket(key: str, *, status: str, category: str) -> JiraTicket:
    return JiraTicket(
        key=key, summary=f"summary for {key}", status=status, status_category=category,
        assignee_name="Alice", assignee_email=None, priority=None, issue_type="Task",
        labels=(), parent_key=None, points=None,
        updated="2026-06-01T12:00:00+00:00", created="2026-06-01T12:00:00+00:00",
    )


class TestRenderer:
    def test_renders_tracker_with_phase_progress(self, tmp_path):
        config = _config(tmp_path=tmp_path)
        tickets = [_ticket("BH-101", status="Done", category="Done")]
        out = render_tracker(
            config=config, tickets=tickets, pr_map={}, existing_text=None, now=_now(),
        )
        assert "Acme — Live Tracker" in out
        assert "Phase 1 (1/1 🟢)" in out  # 1 auto green / 1 auto total (manual ignored)
        assert "🟢" in out  # auto-checked (done) row
        assert "🔲" in out  # manual row (no linked item)
        # Scoreboard
        assert "Alice" in out
        assert "🏁 Who's done what" in out

    def test_phase_progress_helper(self, tmp_path):
        config = _config(tmp_path=tmp_path)
        tickets = [_ticket("BH-101", status="To Do", category="To Do")]
        progress = compute_phase_progress(config=config, tickets=tickets, pr_map={})
        assert progress == [("Phase 1", 0, 0, 1)]  # (title, green, wip, total)

    def test_in_review_ticket_renders_wip(self, tmp_path):
        config = _config(tmp_path=tmp_path)
        tickets = [_ticket("BH-101", status="Code Review", category="In Review")]
        out = render_tracker(
            config=config, tickets=tickets, pr_map={}, existing_text=None, now=_now(),
        )
        assert "🟡" in out  # in-review ticket shows in-progress, not blank
        assert "Phase 1 (0/1 🟢, 1 🟡)" in out
        progress = compute_phase_progress(config=config, tickets=tickets, pr_map={})
        assert progress == [("Phase 1", 0, 1, 1)]
