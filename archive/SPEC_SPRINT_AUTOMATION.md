# Sprint Automation Specification (SPEC)

**Version:** 1.0.0
**Date:** 2026-01-21
**Status:** DRAFT
**Audience:** Engineering Team, Platform Team

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Architecture](#architecture)
4. [API Specifications](#api-specifications)
5. [Configuration](#configuration)
6. [Data Formats](#data-formats)
7. [Error Handling](#error-handling)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)

---

## Overview

### Purpose

Automate sprint closure workflow including:
1. Release notes generation from git commits
2. Per-repository changelogs
3. Distribution to Slack and Notion
4. GitHub Release creation

### Scope

- **In Scope:**
  - Git commit parsing (conventional commits)
  - Release notes generation (technical + marketing)
  - Slack webhook posting
  - GitHub Actions automation
  - CHANGELOG.md generation

- **Out of Scope:**
  - Jira board updates (future)
  - Notion page creation (future - MCP integration)
  - Email distribution (future)
  - Custom domain/branding (future)

### Success Criteria

- [ ] Release notes generated in < 30 seconds
- [ ] All 6 repos have automated changelogs
- [ ] Slack posting works with webhook
- [ ] GitHub Release created automatically
- [ ] Zero manual steps for future sprints
- [ ] 100% of commits properly categorized

---

## Requirements

### Functional Requirements

#### FR1: Release Notes Generation
```
When: User pushes sprint-N tag
Then: System generates 3 artifacts:
  - SPRINT_N_RELEASE_NOTES.md (technical)
  - SPRINT_N_MARKETING_RELEASE_NOTES.md (marketing)
  - changelogs/*.md (per-repo)
```

**Details:**
- Parse git log from all repositories
- Extract conventional commits (feat:, fix:, docs:, etc.)
- Categorize by type
- Include commit hash and author
- Mark breaking changes
- Include Jira metrics (if snapshot exists)

#### FR2: Changelog Generation
```
When: Repository pushed to main/master
Then: CHANGELOG.md auto-generated using git-cliff
```

**Details:**
- Use git-cliff with conventional commits
- Parse cliff.toml configuration
- Group by commit type
- Link to GitHub issues
- Update on every push

#### FR3: Slack Integration
```
When: Release notes generated
Then: Post formatted message to Slack
```

**Details:**
- Use Slack Block Kit format
- Include key metrics
- Link to full release notes
- Support multiple channels (configurable)
- Handle webhook URL from secrets

#### FR4: GitHub Release
```
When: Tag pushed (e.g., sprint-2)
Then: Create GitHub Release
```

**Details:**
- Use marketing release notes as body
- Attach technical notes as artifact
- Set tag as release version
- Mark as latest release

### Non-Functional Requirements

#### NFR1: Performance
- Release notes generation: < 30 seconds
- Slack posting: < 5 seconds
- GitHub Release creation: < 10 seconds
- Changelog generation: < 20 seconds per repo

#### NFR2: Reliability
- Retry logic for network failures
- Graceful error handling
- Detailed logging
- No data loss on failure

#### NFR3: Security
- Webhook URLs in GitHub Secrets
- No credentials in logs
- HTTPS only for external APIs
- Signed commits (recommended)

#### NFR4: Maintainability
- Clear error messages
- Comprehensive documentation
- Easy to extend to new repos
- Configuration-driven (cliff.toml)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│          Git Tag Push (sprint-N)                    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│   GitHub Actions: sprint-release.yml                │
│  - Extract sprint number                            │
│  - Setup Python environment                         │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────────┐    ┌──────────────────┐
│  Generate Release│    │  Post to Slack   │
│  Notes (Python)  │    │  (Python)        │
│                  │    │                  │
│ - Parse git log  │    │ - Format message │
│ - Group commits  │    │ - Send webhook   │
│ - Create files   │    │ - Log result     │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Create GitHub        │
         │  Release              │
         └───────────────────────┘

Per-Repo Automation (continuous):
┌─────────────────────────────────────────┐
│  Push to main/master                    │
│  Triggers: .github/workflows/changelog.yml
│  - Run git-cliff                        │
│  - Generate CHANGELOG.md                │
│  - Commit & push                        │
└─────────────────────────────────────────┘
```

### Data Flow

```
git log (all repos)
        │
        ▼
generate_release_notes.py
        │
        ├─→ Parse commits
        ├─→ Extract metadata (type, scope, message)
        ├─→ Categorize by type
        ├─→ Load Jira snapshot (optional)
        │
        ├─→ Output: SPRINT_N_RELEASE_NOTES.md
        ├─→ Output: SPRINT_N_MARKETING_RELEASE_NOTES.md
        └─→ Output: changelogs/*.md
                │
                ▼
         post_to_slack.py
                │
                ├─→ Read release notes
                ├─→ Format as Slack blocks
                ├─→ POST to webhook URL
                └─→ Log result

GitHub Actions
                │
                ├─→ Create Release
                ├─→ Commit files
                └─→ Success/Failure notification
```

---

## API Specifications

### 1. Release Notes Generator

**Module:** `project/sprint/scripts/generate_release_notes.py`

#### CLI Interface

```bash
python generate_release_notes.py \
  --sprint <int> \
  [--since <date>] \
  [--until <date>] \
  [--output-dir <path>] \
  [--repo-root <path>]
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--sprint` | int | Yes | N/A | Sprint number (1, 2, 3, etc.) |
| `--since` | str (YYYY-MM-DD) | No | First of current month | Start date for commits |
| `--until` | str (YYYY-MM-DD) | No | Today | End date for commits |
| `--output-dir` | path | No | `../sprint-{N}` | Output directory |
| `--repo-root` | path | No | Auto-detect | Repository root |

#### Return Codes

```
0  - Success
1  - Missing required parameter
2  - Repository not found
3  - Git command failed
4  - Release notes generation failed
```

#### Output Files

```
{output_dir}/
├── SPRINT_{N}_RELEASE_NOTES.md           (technical)
├── SPRINT_{N}_MARKETING_RELEASE_NOTES.md (marketing)
└── changelogs/
    ├── README.md
    ├── brighthive-platform-core.md
    ├── brighthive-webapp.md
    ├── brightbot.md
    ├── brighthive-data-organization-cdk.md
    └── brighthive-data-workspace-cdk.md
```

#### Example

```bash
python generate_release_notes.py \
  --sprint 1 \
  --since 2026-01-13 \
  --until 2026-01-20
```

---

### 2. Slack Poster

**Module:** `project/sprint/scripts/post_to_slack.py`

#### CLI Interface

```bash
python post_to_slack.py \
  --sprint <int> \
  [--webhook-url <url>] \
  [--channel <name>] \
  [--release-notes <path>]
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `--sprint` | int | Yes | N/A | Sprint number |
| `--webhook-url` | str | No | SLACK_WEBHOOK_URL env | Slack webhook URL |
| `--channel` | str | No | #releases | Slack channel (display) |
| `--release-notes` | path | No | Auto-detect | Path to release notes |

#### Return Codes

```
0  - Success
1  - Webhook URL not provided
2  - Release notes not found
3  - Network error
4  - Slack API error
```

#### Example

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python post_to_slack.py --sprint 1
```

---

### 3. GitHub Actions Workflow

**File:** `.github/workflows/sprint-release.yml`

#### Trigger Events

```yaml
on:
  push:
    tags:
      - 'sprint-*'     # Semantic: sprint-1, sprint-2
  workflow_dispatch:
    inputs:
      sprint_number:   # Manual trigger
      since_date:      # Optional
      until_date:      # Optional
      post_to_slack:   # Boolean
```

#### Output Artifacts

```yaml
outputs:
  sprint_number:  # Extracted from tag or input
  sprint_dir:     # Generated directory
  technical_notes:  # Path to technical notes
  marketing_notes:  # Path to marketing notes
```

#### Environment Variables

```yaml
env:
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Configuration

### Git-Cliff Configuration

**File:** `cliff.toml` (in each repository)

#### Conventional Commits Types

```toml
[git.commit_parsers]
# Format: { message = "^type", group = "Display Name" }
{ message = "^feat", group = "Features" }
{ message = "^fix", group = "Bug Fixes" }
{ message = "^docs", group = "Documentation" }
{ message = "^perf", group = "Performance" }
{ message = "^refactor", group = "Refactoring" }
{ message = "^style", group = "Styling" }
{ message = "^test", group = "Testing" }
{ message = "^chore", group = "Chores" }
{ message = "^ci", group = "CI/CD" }
{ message = "^build", group = "Build" }
{ message = "^security", group = "Security" }
```

#### Breaking Changes

```toml
protect_breaking_commits = true
```

Breaking changes are flagged with "!" in commit message:
```
feat(auth)!: remove legacy OAuth endpoint
```

---

## Data Formats

### Release Notes Format

#### Technical Release Notes

```markdown
# Sprint N Release Notes

**Release Date:** YYYY-MM-DD
**Sprint Period:** YYYY-MM-DD to YYYY-MM-DD

## Executive Summary
- Total Tickets: X
- Story Points: Y
- Team Members: Z

## Changes by Repository

### Repository Name
- Commits: N
  - Features: X
  - Bug Fixes: Y
  - Docs: Z
```

#### Marketing Release Notes

```markdown
# Sprint N Release 🚀

**Release Date:** Month DD, YYYY

## What's New

### ✨ New Features
- Feature 1
- Feature 2

### 🛡️ Security Improvements
- Improvement 1
- Improvement 2

### 🐛 Bug Fixes
- Bug 1 fixed
- Bug 2 fixed
```

### Per-Repository Changelog

```markdown
# Repository Name - Sprint N Changelog

## ⚠️ Breaking Changes

## 🚀 Features

## 🐛 Bug Fixes

## 📚 Documentation

---
**Total Commits:** N
```

### Slack Message Format (Block Kit)

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚀 BrightHive Sprint N Release"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Key Metrics*\n• Story Points: X\n• Tickets: Y\n• Repositories: Z"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "📚 <link|Full Notes> | <link|Technical Details>"
        }
      ]
    }
  ]
}
```

---

## Error Handling

### Git Command Failures

```python
try:
    result = subprocess.run(
        ["git", "-C", repo_path, "log", ...],
        capture_output=True,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    logger.error(f"Git failed in {repo_path}: {e.stderr}")
    return []  # Return empty list, continue processing
```

### Network Errors (Slack Posting)

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            logger.error(f"Failed to post to Slack after {max_retries} attempts: {e}")
            return False
```

### File System Errors

```python
if not release_notes_path.exists():
    raise FileNotFoundError(f"Release notes not found: {release_notes_path}")

output_dir.mkdir(parents=True, exist_ok=True)
```

---

## Testing Strategy

### Unit Tests

```python
# test_generate_release_notes.py

def test_parse_conventional_commit():
    """Test parsing feat(scope): message"""
    assert parse_commit("abc123 - feat(auth): add SSO") == {
        "hash": "abc123",
        "type": "feat",
        "scope": "auth",
        "message": "add SSO"
    }

def test_group_commits_by_type():
    """Test grouping commits"""
    commits = [
        {"type": "feat", "message": "Add login"},
        {"type": "fix", "message": "Fix bug"},
        {"type": "feat", "message": "Add logout"},
    ]
    assert group_by_type(commits) == {
        "feat": 2,
        "fix": 1
    }

def test_breaking_change_detection():
    """Test detecting breaking changes"""
    assert parse_commit("abc123 - feat!: rename API endpoint")["breaking"] == True
```

### Integration Tests

```bash
# Test release notes generation
python generate_release_notes.py --sprint 1 --since 2026-01-13 --until 2026-01-20

# Verify output files exist
test -f project/sprint/sprint-1/SPRINT_1_RELEASE_NOTES.md
test -f project/sprint/sprint-1/SPRINT_1_MARKETING_RELEASE_NOTES.md
test -d project/sprint/sprint-1/changelogs

# Test Slack posting (with test webhook)
SLACK_WEBHOOK_URL="https://hooks.slack.com/test" python post_to_slack.py --sprint 1
```

### End-to-End Test

```bash
# Push test tag
git tag -a sprint-test -m "Test release"
git push origin sprint-test

# Wait for GitHub Actions
sleep 30

# Verify:
# 1. Release notes created
# 2. GitHub Release created
# 3. Slack message posted
# 4. Files committed to repo
```

---

## Deployment

### Deployment Steps

1. **Enable GitHub Actions**
   ```bash
   # Ensure .github/workflows/sprint-release.yml is on main branch
   git add .github/workflows/
   git commit -m "ci: add sprint release automation"
   git push origin main
   ```

2. **Deploy cliff.toml to All Repos**
   ```bash
   for repo in brighthive-{platform-core,webapp} brightbot \
               brighthive-data-{organization,workspace}-cdk \
               brightbot-slack-server; do
     cp cliff.toml $repo/
     cd $repo
     git add cliff.toml .github/workflows/changelog.yml
     git commit -m "ci: add changelog automation"
     git push
   done
   ```

3. **Configure GitHub Secrets**
   ```bash
   gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/..."
   ```

4. **Test Automation**
   ```bash
   # Create test tag
   git tag -a sprint-test -m "Test"
   git push origin sprint-test

   # Monitor GitHub Actions → Actions tab
   ```

5. **Cleanup (remove test tag)**
   ```bash
   git tag -d sprint-test
   git push origin :sprint-test
   ```

### Rollback Plan

**If automation fails:**

```bash
# Option 1: Manual release notes generation
python project/sprint/scripts/generate_release_notes.py --sprint N

# Option 2: Manual Slack posting
export SLACK_WEBHOOK_URL="..."
python project/sprint/scripts/post_to_slack.py --sprint N

# Option 3: Disable workflow (temporary)
# - GitHub UI: Actions → Disable workflow
# - File: Rename .github/workflows/sprint-release.yml.disabled
```

---

## Compliance & Standards

### Git Commit Standards

All commits must follow **Conventional Commits** (v1.0.0):

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting/style
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Tests
- `build` - Build system
- `ci` - CI/CD
- `chore` - Maintenance
- `security` - Security fixes

**Example:**
```
feat(auth): implement SSO login

Add support for OAuth 2.0 single sign-on.
Supports Google and GitHub providers.

Fixes #123
Breaking: Removed legacy token endpoint
```

### Documentation Standards

- Release notes use Markdown
- Comments in code use Python docstrings
- Configuration documented in README

---

## Appendix

### A. Repository List

The automation covers these 6 repositories:

1. `brighthive-platform-core` - Backend API
2. `brighthive-webapp` - Frontend
3. `brightbot` - AI agent system
4. `brighthive-data-organization-cdk` - Org infrastructure
5. `brighthive-data-workspace-cdk` - Workspace infrastructure
6. `brightbot-slack-server` - Slack integration

### B. Environment Variables Reference

| Variable | Required | Source | Used By |
|----------|----------|--------|---------|
| `SLACK_WEBHOOK_URL` | Yes | GitHub Secrets | post_to_slack.py, GitHub Actions |
| `GITHUB_TOKEN` | Auto | GitHub | GitHub Actions |
| `AWS_REGION` | No | Environment | (Future AWS integration) |

### C. Useful Commands

```bash
# Generate release notes locally
python project/sprint/scripts/generate_release_notes.py --sprint N

# Post to Slack
export SLACK_WEBHOOK_URL="..."
python project/sprint/scripts/post_to_slack.py --sprint N

# Test GitHub workflow
gh workflow run sprint-release.yml -f sprint_number=N

# View workflow runs
gh run list --workflow sprint-release.yml

# Manual git-cliff test
cd repo && git-cliff --output CHANGELOG_TEST.md
```

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-21
**Next Review:** 2026-02-20
**Owner:** Platform Team
