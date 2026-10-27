"""Count the artifacts of AI-driven engineering (agent skills, agent review, specs, sprint records) from local git."""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "ai_engineering.json"
PROJECT_REPO = "agentic-project-mgmt"
REPOS = (
    "brightbot", "brighthive-platform-core", "brighthive-webapp", "brighthive-e2e",
    "agentic-project-mgmt", "platform-saas-ai-context", "brightbot-slack-server", "brightagent-v3",
    "brightagent-engineering-runner",
)
DEFAULT_REFS = ("origin/develop", "origin/master", "origin/main", "origin/production")
SKILL_PATTERN = re.compile(r"(^|/)\.claude/skills/[^/]+/SKILL\.md$")
CLAUDE_WORKFLOW_PATTERN = re.compile(r"\.github/workflows/[^/]*claude[^/]*\.ya?ml$", re.IGNORECASE)
CONTRACT_PATTERN = re.compile(r"(^|/)(CLAUDE|AGENTS)\.md$")
SPEC_PATTERN = re.compile(r"^docs/specs/(?!README|THEMES\.md)(?![^/]*TEMPLATE)[^/]+\.md$")
SPRINT_NOTES_PATTERN = re.compile(r"^jira/sprint/\d+/RELEASE_NOTES\.md$")
ADR_PATTERN = re.compile(r"^docs/adr/\d{4}-.+\.md$")
YEARONE_SCRIPTS_DIR = Path(__file__).parent
GHERKIN_MARKER = "Scenario:"
MAKE_TARGET_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+:.*##", re.MULTILINE)


def git(*, repo: Path, args: list[str]) -> str:
    """Run a git command in a repo and return stdout."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def default_ref(*, repo: Path) -> str | None:
    """First existing integration branch ref."""
    return next((r for r in DEFAULT_REFS if git(repo=repo, args=["rev-parse", "--verify", "-q", r]).strip()), None)


def count_matches(*, paths: list[str], pattern: re.Pattern[str]) -> int:
    """Count paths matching a pattern."""
    return sum(1 for path in paths if pattern.search(path))


def spec_scenario_counts(*, repo: Path, ref: str, spec_paths: list[str]) -> tuple[int, int]:
    """Return (specs with at least one Gherkin scenario, total Gherkin scenarios)."""
    with_scenarios = total = 0
    for path in spec_paths:
        found = git(repo=repo, args=["show", f"{ref}:{path}"]).count(GHERKIN_MARKER)
        total += found
        with_scenarios += 1 if found else 0
    return with_scenarios, total


def repo_snapshot(*, name: str) -> dict | None:
    """Agent-related artifact counts for one repo at its integration branch."""
    repo = WORKSPACE / name
    ref = default_ref(repo=repo) if (repo / ".git").exists() else None
    if ref is None:
        return None
    paths = git(repo=repo, args=["ls-tree", "-r", "--name-only", ref]).splitlines()
    return {
        "ref": ref,
        "agent_skills": count_matches(paths=paths, pattern=SKILL_PATTERN),
        "claude_review_workflows": count_matches(paths=paths, pattern=CLAUDE_WORKFLOW_PATTERN),
        "agent_contracts": count_matches(paths=paths, pattern=CONTRACT_PATTERN),
    }


def project_management_snapshot() -> dict:
    """Sprint, spec, ADR and automation counts for the project-management repo."""
    repo = WORKSPACE / PROJECT_REPO
    ref = default_ref(repo=repo)
    paths = git(repo=repo, args=["ls-tree", "-r", "--name-only", ref]).splitlines()
    spec_paths = [p for p in paths if SPEC_PATTERN.match(p)]
    specs_with_scenarios, scenarios = spec_scenario_counts(repo=repo, ref=ref, spec_paths=spec_paths)
    makefile = git(repo=repo, args=["show", f"{ref}:Makefile"])
    return {
        "ref": ref,
        "sprints_with_release_notes": count_matches(paths=paths, pattern=SPRINT_NOTES_PATTERN),
        "specs": len(spec_paths),
        "specs_with_gherkin_scenarios": specs_with_scenarios,
        "gherkin_scenarios": scenarios,
        "adrs": count_matches(paths=paths, pattern=ADR_PATTERN),
        "documented_make_targets": len(MAKE_TARGET_PATTERN.findall(makefile)),
        "year_one_collectors_and_renderers": len(list(YEARONE_SCRIPTS_DIR.glob("collect_*.py"))) + len(list(YEARONE_SCRIPTS_DIR.glob("render_*.py"))),
    }


def main() -> None:
    """Collect and write the AI-driven engineering snapshot."""
    repos = {name: snap for name in REPOS if (snap := repo_snapshot(name=name)) is not None}
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos": repos,
        "totals": {
            "agent_skills": sum(r["agent_skills"] for r in repos.values()),
            "repos_with_claude_review": sum(1 for r in repos.values() if r["claude_review_workflows"]),
            "agent_contracts": sum(r["agent_contracts"] for r in repos.values()),
        },
        "project_management": project_management_snapshot(),
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2) + "\n")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
