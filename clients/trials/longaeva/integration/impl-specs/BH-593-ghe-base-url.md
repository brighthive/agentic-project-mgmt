---
ticket: BH-593
title: "Thread GITHUB_BASE_URL through GHE client config"
owner: "Ahmed (per BRIGHTHIVE_GAPS GAP-5)"
estimated: "2-3 days (NOT 1 day — 18+ hardcoded URL touchpoints + cross-repo workspace config schema)"
depends_on: ["BH-529 (bb#490 + pc#778) on develop — proxy chain"]
last_reviewed: "2026-06-05"
---

# BH-593 — paste-ready implementation spec

> **Goal**: customer GitHub Enterprise hosts (`https://ghe.longaeva.example.com`)
> route correctly through both the brightbot agent's direct GitHub client AND
> the platform-core GHE proxy. Without this, every PR-creation flow on
> Longaeva fails with a 404 on `api.github.com`.
>
> **Branch**: `ahmed/BH-593/ghe-base-url-config` off **post-merge `develop`**
> (after the BH-529 proxy chain — bb#490 + pc#778 — squashes).

## What I found in the code (verified 2026-06-05)

GitHub URLs are hardcoded in **4 files**, **20 occurrences total**:

| File | Hits | Pattern |
|---|---|---|
| `brightbot/tools/github_tools.py` | 15 | f-strings like `f"https://api.github.com/orgs/{org}/repos"` |
| `brightbot/agents/dbt_agent/tools/github_tools.py` | 5 | One module-level constant `GITHUB_API_ROOT = "https://api.github.com"` (good!) + 4 stragglers in docstrings |
| `brightbot/tools/github_oauth.py` | 5 | Module-level `self.github_api_base`, `github_device_flow_url`, `github_token_url` |
| `brightbot/tools/warehouse_connections.py` | 0 | (false positive in earlier grep) |

**`brightbot/tools/github_operations.py`** uses `Github(access_token.token)` from PyGithub (line 42) — PyGithub takes `base_url=` as a constructor arg.

**Cross-repo touchpoints**:
- platform-core `github-proxy` resolvers — must honor a per-workspace `ghe_base_url` field
- workspace config schema (Pydantic + DynamoDB write path) needs a new optional `github_base_url` field
- BH-570 already exists for self-signed CA bundle support (`NODE_EXTRA_CA_CERTS`) — coordinate so they land together

## Design decision (please review with Ahmed before coding)

There are 3 places `base_url` could come from:

| Option | Source | Pros | Cons |
|---|---|---|---|
| A — Env var | `GITHUB_BASE_URL` set per deployment | Simplest. 1 line per file. | One workspace per deployment — breaks multi-tenant. |
| B — Per-workspace config | Read from workspace's DynamoDB `AdminConfig` | Multi-tenant safe. Aligns with how Snowflake creds are scoped. | Touches more files; requires reading workspace context in every github tool. |
| **C — Hybrid (Recommended)** | Workspace config takes precedence; env var fallback | Multi-tenant safe; supports BrightHive-internal dev sandbox via env var | Slightly more code than A. |

**Recommendation: Option C.** Snowflake creds work this way today (`workspace_secret_store/{uuid}`) — match the pattern.

## Diff 1 — central constant + resolver

New file: `brightbot/tools/github_config.py`

```python
"""GitHub host configuration — workspace-aware with env fallback.

Resolves the GitHub API + UI base URLs for a given workspace. Used by every
GitHub tool so a Longaeva workspace pointed at GHE
(https://ghe.longaeva.example.com) routes correctly without hardcoding the
host anywhere downstream.

Resolution order:
  1. Workspace config — `workspace.github.base_url` (multi-tenant production path)
  2. Environment variable — `GITHUB_BASE_URL` (BrightHive-internal dev sandbox)
  3. Default — github.com (cloud customers)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from brightbot.tools.bh_platform_api import get_workspace_config

DEFAULT_GITHUB_API_ROOT = "https://api.github.com"
DEFAULT_GITHUB_WEB_ROOT = "https://github.com"
DEFAULT_GITHUB_DEVICE_FLOW_URL = "https://github.com/login/device/code"
DEFAULT_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


@dataclass(frozen=True)
class GitHubHostConfig:
    """Resolved GitHub host endpoints for a workspace."""

    api_root: str         # e.g. https://api.github.com  OR  https://ghe.example.com/api/v3
    web_root: str         # e.g. https://github.com      OR  https://ghe.example.com
    device_flow_url: str  # OAuth device-flow endpoint
    token_url: str        # OAuth token endpoint

    @classmethod
    def for_github_dotcom(cls) -> "GitHubHostConfig":
        return cls(
            api_root=DEFAULT_GITHUB_API_ROOT,
            web_root=DEFAULT_GITHUB_WEB_ROOT,
            device_flow_url=DEFAULT_GITHUB_DEVICE_FLOW_URL,
            token_url=DEFAULT_GITHUB_TOKEN_URL,
        )

    @classmethod
    def for_ghe(cls, *, web_root: str) -> "GitHubHostConfig":
        """GHE Server convention: /api/v3 for REST, /login/* for OAuth."""
        web = web_root.rstrip("/")
        return cls(
            api_root=f"{web}/api/v3",
            web_root=web,
            device_flow_url=f"{web}/login/device/code",
            token_url=f"{web}/login/oauth/access_token",
        )


def resolve_github_host(*, workspace_id: str | None = None) -> GitHubHostConfig:
    """Resolve the GitHub host config for a workspace.

    Args:
        workspace_id: workspace UUID. If None, falls back to env var or default.

    Returns:
        GitHubHostConfig with the four endpoint URLs.
    """
    # 1. Workspace config (production multi-tenant path)
    if workspace_id is not None:
        cfg = get_workspace_config(workspace_id=workspace_id)
        ghe_url = cfg.get("github", {}).get("base_url")
        if ghe_url:
            return GitHubHostConfig.for_ghe(web_root=ghe_url)

    # 2. Env var (dev sandbox / BrightHive-internal smoke tests)
    env_url = os.getenv("GITHUB_BASE_URL")
    if env_url and "github.com" not in urlparse(env_url).netloc:
        return GitHubHostConfig.for_ghe(web_root=env_url)

    # 3. Default — github.com
    return GitHubHostConfig.for_github_dotcom()
```

## Diff 2 — `brightbot/tools/github_oauth.py`

Replace the hardcoded constructor (lines 21-23):

```python
class GitHubAuthManager:
    def __init__(self, *, workspace_id: str | None = None) -> None:
        from brightbot.tools.github_config import resolve_github_host
        host = resolve_github_host(workspace_id=workspace_id)
        self.github_api_base = host.api_root
        self.github_device_flow_url = host.device_flow_url
        self.github_token_url = host.token_url
```

All call sites must pass `workspace_id=`.

## Diff 3 — `brightbot/tools/github_tools.py` (15 hits)

**Refactor pattern**: every function that does `f"https://api.github.com/..."` must accept `workspace_id` and call `resolve_github_host(workspace_id=workspace_id).api_root` first.

Example before:
```python
def list_repos(org_name: str, ...) -> ...:
    url = f"https://api.github.com/orgs/{org_name}/repos?..."
```

Example after:
```python
def list_repos(org_name: str, *, workspace_id: str, ...) -> ...:
    from brightbot.tools.github_config import resolve_github_host
    host = resolve_github_host(workspace_id=workspace_id)
    url = f"{host.api_root}/orgs/{org_name}/repos?..."
```

15 occurrences — same mechanical edit each. **Watch the line 1185-1242 block** that parses `github.com` from URLs — that needs to also accept GHE hostnames. Loose check `if "github.com" not in github_folder_url:` (line 1200) becomes `if not _is_known_github_host(github_folder_url, host=host):`.

## Diff 4 — `brightbot/agents/dbt_agent/tools/github_tools.py`

The good news: this file already has `GITHUB_API_ROOT = "https://api.github.com"` as a module-level constant (line 35). Replace the constant + ensure every callsite has access to `workspace_id`:

```python
# Replace line 35 with:
from brightbot.tools.github_config import resolve_github_host

# Then in each tool function (these are LangChain @tool's):
@tool
def github_create_pull_request(
    *,
    workspace_id: str,        # NEW — must be threaded from agent state
    org_name: str,
    repo_name: str,
    ...
) -> str:
    host = resolve_github_host(workspace_id=workspace_id)
    api_root = host.api_root
    # ...rest unchanged, replace GITHUB_API_ROOT with api_root
```

**Important**: `workspace_id` must come from agent state. The dbt ReAct agent already has `workspace_id` in its state schema — confirm it's threaded into the tool calls (probably via `inject_state` or similar middleware).

## Diff 5 — `brightbot/tools/github_operations.py` PyGithub line 42

```python
# Before:
self.github_instance = Github(access_token.token)

# After:
from brightbot.tools.github_config import resolve_github_host
host = resolve_github_host(workspace_id=workspace_id)
if host.api_root == "https://api.github.com":
    self.github_instance = Github(access_token.token)
else:
    self.github_instance = Github(base_url=host.api_root, login_or_token=access_token.token)
```

## Diff 6 — workspace config schema (Pydantic + DynamoDB)

Add `github_base_url` to whatever Pydantic model represents workspace config. Locate via:

```bash
grep -rn "class.*WorkspaceConfig\|class.*AdminConfig" brightbot/ --include="*.py"
```

If the model lives in platform-core, this is a cross-repo PR. Otherwise add:

```python
class WorkspaceGitHubConfig(BaseModel):
    base_url: str | None = Field(
        default=None,
        description="GHE host root (e.g. https://ghe.example.com). None = github.com.",
    )

class WorkspaceConfig(BaseModel):
    # ...existing fields
    github: WorkspaceGitHubConfig | None = Field(default=None)
```

## Diff 7 — platform-core github-proxy resolvers

The platform-core side of the proxy (post-pc#778 merge) will already use a GitHub client wrapper. Locate it:

```bash
cd ../brighthive-platform-core
grep -rn "octokit\|@octokit\|GitHub.*Client" src/ --include="*.ts"
```

Pattern (TypeScript):

```typescript
// Before
const octokit = new Octokit({ auth: pat });

// After
const ghe_url = workspace.config?.github?.base_url;
const octokit = ghe_url
  ? new Octokit({ auth: pat, baseUrl: `${ghe_url}/api/v3` })
  : new Octokit({ auth: pat });
```

## Tests

### Unit (`tests/unit/tools/test_github_config.py` — new file)

```python
"""BH-593 — GitHub host config resolution."""

import pytest
from brightbot.tools.github_config import (
    GitHubHostConfig,
    resolve_github_host,
)


def test_default_resolves_to_dotcom() -> None:
    cfg = resolve_github_host(workspace_id=None)
    assert cfg.api_root == "https://api.github.com"
    assert cfg.web_root == "https://github.com"


def test_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_BASE_URL", "https://ghe.internal.brighthive.io")
    cfg = resolve_github_host(workspace_id=None)
    assert cfg.api_root == "https://ghe.internal.brighthive.io/api/v3"
    assert cfg.web_root == "https://ghe.internal.brighthive.io"


def test_workspace_config_takes_precedence_over_env(
    monkeypatch: pytest.MonkeyPatch,
    mock_workspace_config,
) -> None:
    monkeypatch.setenv("GITHUB_BASE_URL", "https://wrong.example.com")
    mock_workspace_config(workspace_id="ws-1", github={"base_url": "https://ghe.longaeva.example.com"})
    cfg = resolve_github_host(workspace_id="ws-1")
    assert cfg.api_root == "https://ghe.longaeva.example.com/api/v3"


def test_ghe_constructor_strips_trailing_slash() -> None:
    cfg = GitHubHostConfig.for_ghe(web_root="https://ghe.example.com/")
    assert cfg.api_root == "https://ghe.example.com/api/v3"


def test_dotcom_url_in_env_falls_through_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Setting GITHUB_BASE_URL to a github.com URL should be a no-op (typed-out default)."""
    monkeypatch.setenv("GITHUB_BASE_URL", "https://api.github.com")
    cfg = resolve_github_host(workspace_id=None)
    assert cfg.api_root == "https://api.github.com"  # default, not /api/v3
```

### Integration (`tests/integration/test_ghe_routing.py` — new file)

```python
"""BH-593 — GHE base_url routing E2E (requires Grant's sandbox creds)."""

import pytest


@pytest.mark.integration
@pytest.mark.requires_ghe_sandbox  # skipped until Grant's creds exist
def test_create_pr_against_ghe_sandbox(ghe_workspace, ghe_pat):
    """Full createBranch → commitFiles → createPR round-trip against Longaeva GHE."""
    # ...
```

## Acceptance criteria

```gherkin
Feature: GHE base_url routing

  Scenario: Workspace with no ghe_base_url → github.com (regression check)
    Given a workspace with no github config
    When the agent creates a PR
    Then the request goes to https://api.github.com

  Scenario: Workspace configured for GHE
    Given a workspace with github.base_url = "https://ghe.longaeva.example.com"
    When the agent creates a PR
    Then the request goes to https://ghe.longaeva.example.com/api/v3
    And the response is parsed correctly
    And no calls go to github.com

  Scenario: GHE sandbox smoke (Grant-creds-dependent)
    Given Grant's GHE sandbox PAT + host + TLS chain
    When the dbt agent runs full createBranch → commitFiles → createPR
    Then the round-trip succeeds without TLS or 404 errors
```

## Multi-agent review (per global rules)

1. solutions-architect — workspace config schema + cross-repo coordination with platform-core
2. senior-python — security check (no PAT logging, no URL injection)
3. qa-agent — regression coverage for github.com path; flag the 15 mechanical replacements as a high-risk diff
4. junior-developer — scan for missed hardcoded URLs

## Coordinate with these existing tickets

- **BH-570** — self-signed CA bundle support (`NODE_EXTRA_CA_CERTS`). Land alongside or just before BH-593 — both need Grant's TLS chain to verify.
- **BH-569** — GitHub App installation flow as PAT replacement. Future; do not block on this.

## Effort breakdown

| Phase | Days |
|---|---|
| Diff 1 (central resolver + tests) | 0.5 |
| Diffs 2-5 (4 brightbot files, 20 hardcoded URL fixes) | 1 |
| Diff 6 (workspace config schema, possibly cross-repo) | 0.5 |
| Diff 7 (platform-core resolver) | 0.5 |
| Multi-agent review iterations | 0.5 |
| Manual smoke (Grant-blocked) | held |
| **Total** | **2-3 days** (vs the 1-day estimate in BRIGHTHIVE_GAPS — was wrong) |
