"""Snapshot each core repo before Kuri joined and now; measure reach, architecture and observability."""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent.parent.parent
OUTPUT_PATH = Path(__file__).parent.parent.parent / "docs" / "year-one" / "data" / "codebase_reach.json"
BEFORE_CUTOFF = "2025-10-23"
AFTER_REF = "origin/develop"
KURI_AUTHOR_RE = "Kuri|Chinca|drchinca|Bado"
CODE_SUFFIXES = (".py", ".ts", ".tsx", ".js")
TEST_MARKERS = ("test_", ".test.", ".spec.")
CODE_GLOBS = ("*.py", "*.ts", "*.tsx")


@dataclass(frozen=True)
class RepoSpec:
    name: str
    module_roots: tuple[str, ...]


REPOS = (
    RepoSpec(name="brightbot", module_roots=("brightbot", "brightbot/agents", "brightbot/integrations", "brightbot/skills/system")),
    RepoSpec(name="brighthive-platform-core", module_roots=("src", "lambdas", "brighthive_core")),
    RepoSpec(name="brighthive-webapp", module_roots=("src", "src/features")),
)

SIGNALS = {
    "observability": {
        "tracing_and_evals": r"opentelemetry|langsmith|LANGSMITH|traceable|deepeval",
        "structured_logging": r"structlog|logging\.getLogger|get_logger",
        "cost_and_token_metering": r"cost_usd|token_usage|usage_metadata|prompt_tokens|input_tokens",
        "health_endpoints": r"/health|livez|readyz|health_check|healthcheck",
        "alarms_and_alerts": r"cloudwatch\.Alarm|Alarm\(|notify_slack|send_alert|alerting",
        "audit_trail": r"audit_log|AuditEvent|audit_event|write_audit|record_audit",
        "error_and_product_analytics": r"sentry|posthog",
    },
    "architecture": {
        "protocol_classes": r"class [A-Za-z0-9_]+\(.*Protocol.*\)",
        "port_or_adapter_classes": r"class [A-Za-z0-9_]*(Port|Adapter)[^A-Za-z0-9_]",
        "registries": r"_REGISTRY|ADAPTERS\s*[:=]|CONNECTION_CLASSES",
        "feature_flags": r"FEATURE_FLAG|feature_flag|featureFlag",
        "authorization_checks": r"authorize\(|AuthzDecision|checkSingleWorkspacePermission|@authorized",
        "agent_graphs_and_tools": r"@tool([^A-Za-z0-9_]|$)|create_react_agent|StateGraph\(|@mcp\.tool",
    },
}


def git(*, repo: Path, args: list[str]) -> str:
    """Run a git command and return stdout, empty on failure."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def before_sha(*, repo: Path) -> str:
    """Last integration-branch commit before the cutoff."""
    return git(repo=repo, args=["rev-list", "-1", f"--before={BEFORE_CUTOFF}", AFTER_REF]).strip()


def tree(*, repo: Path, ref: str) -> list[tuple[str, int]]:
    """All blobs at a ref as (path, bytes)."""
    rows = []
    for line in git(repo=repo, args=["ls-tree", "-r", "-l", ref]).splitlines():
        meta, path = line.split("\t", 1)
        size = meta.split()[3]
        rows.append((path, int(size) if size.isdigit() else 0))
    return rows


def child_dirs(*, paths: list[str], root: str) -> set[str]:
    """Immediate subdirectories of a root that contain at least one file."""
    prefix = f"{root}/"
    return {p[len(prefix):].split("/", 1)[0] for p in paths if p.startswith(prefix) and "/" in p[len(prefix):]}


def grep_stats(*, repo: Path, ref: str, pattern: str) -> dict:
    """Files and total matches of a pattern in code files at a ref."""
    out = git(repo=repo, args=["grep", "-c", "-E", pattern, ref, "--", *CODE_GLOBS])
    counts = [int(line.rsplit(":", 1)[1]) for line in out.splitlines() if ":" in line]
    return {"files": len(counts), "matches": sum(counts)}


GRAPHQL_SCHEMA_PATHS = ("src/graphql/schema/schema.graphql", "src/graphql/schema/typedefs.ts")


def graphql_surface(*, repo: Path, ref: str) -> dict | None:
    """Approximate GraphQL schema size from the first schema file found at a ref (the file moved from typedefs.ts to schema.graphql)."""
    found = next(((path, text) for path in GRAPHQL_SCHEMA_PATHS if (text := git(repo=repo, args=["show", f"{ref}:{path}"]))), None)
    if not found:
        return None
    schema_path, text = found
    types = len(re.findall(r"^\s*type (?!Query\b|Mutation\b|Subscription\b)\w+", text, re.MULTILINE))
    counts = {"Query": 0, "Mutation": 0}
    block, opener_indent = None, 0
    for line in text.splitlines():
        indent = len(line) - len(line.lstrip())
        opener = re.match(r"^\s*(?:extend )?type (Query|Mutation)\b.*\{", line)
        if opener:
            block, opener_indent = opener.group(1), indent
        elif block and line.strip() == "}" and indent <= opener_indent:
            block = None
        elif block and indent == opener_indent + 2 and re.match(r"^\s+\w+\s*[(:]", line):
            counts[block] += 1
    return {"schema_file": schema_path, "types": types, "query_fields": counts["Query"], "mutation_fields": counts["Mutation"]}


def snapshot(*, spec: RepoSpec, repo: Path, ref: str) -> dict:
    """Measure one repo at one ref."""
    blobs = tree(repo=repo, ref=ref)
    paths = [p for p, _ in blobs]
    code = [(p, s) for p, s in blobs if p.endswith(CODE_SUFFIXES)]
    return {
        "source_kb": round(sum(s for _, s in code) / 1024),
        "code_files": len(code),
        "test_files": sum(1 for p, _ in code if any(m in Path(p).name for m in TEST_MARKERS)),
        "markdown_docs": sum(p.endswith(".md") for p in paths),
        "skills": sum(p.endswith("SKILL.md") for p in paths),
        "modules": {root: sorted(child_dirs(paths=paths, root=root)) for root in spec.module_roots},
        "module_code_files": {root: {name: sum(1 for c, _ in code if c.startswith(f"{root}/{name}/")) for name in child_dirs(paths=paths, root=root)} for root in spec.module_roots},
        "graphql": graphql_surface(repo=repo, ref=ref) if spec.name == "brighthive-platform-core" else None,
        "signals": {group: {name: grep_stats(repo=repo, ref=ref, pattern=pat) for name, pat in items.items()} for group, items in SIGNALS.items()},
    }


def kuri_share(*, repo: Path, path: str) -> dict:
    """Commits touching a path on the integration branch, and the share by Kuri."""
    total = len(git(repo=repo, args=["log", AFTER_REF, "--no-merges", "--format=%h", "--", path]).splitlines())
    kuri = len(git(repo=repo, args=["log", AFTER_REF, "--no-merges", "-i", "-E", f"--author={KURI_AUTHOR_RE}", "--format=%h", "--", path]).splitlines())
    return {"commits": total, "kuri_commits": kuri, "kuri_share_pct": round(100 * kuri / total, 1) if total else None}


def added_modules(*, spec: RepoSpec, repo: Path, before: dict, after: dict) -> list[dict]:
    """Modules present now but not before, with Kuri's share of their commits."""
    added = []
    for root in spec.module_roots:
        for name in sorted(set(after["modules"][root]) - set(before["modules"][root])):
            added.append({"root": root, "module": name, "code_files": after["module_code_files"][root][name], **kuri_share(repo=repo, path=f"{root}/{name}")})
    return added


def main() -> None:
    """Write the before/after snapshots for every core repo."""
    payload: dict[str, dict] = {"cutoff": BEFORE_CUTOFF, "after_ref": AFTER_REF, "repos": {}}
    for spec in REPOS:
        repo = WORKSPACE / spec.name
        sha = before_sha(repo=repo)
        before, after = snapshot(spec=spec, repo=repo, ref=sha), snapshot(spec=spec, repo=repo, ref=AFTER_REF)
        payload["repos"][spec.name] = {
            "before_sha": sha, "before": before, "after": after,
            "modules_added": added_modules(spec=spec, repo=repo, before=before, after=after),
        }
        print(f"done {spec.name}: {len(payload['repos'][spec.name]['modules_added'])} modules added")
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
