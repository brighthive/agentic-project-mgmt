# Sprint Release Notes Automation

Automate generating release notes/changelog when sprint closes:
1. Pull sprint goals/context from Notion
2. Fetch completed JIRA tickets with GitHub PRs
3. Generate rich release notes
4. Publish back to Notion

## Quick Start: Notion + JIRA Script (Recommended)

**Best for:** Rich release notes with sprint context

### Setup

1. Configure Notion integration (see `NOTION_SETUP.md`):
   ```bash
   export NOTION_TOKEN="secret_..."
   export NOTION_SPRINT_DB_ID="..."
   export NOTION_RELEASES_DB_ID="..."
   ```

2. Run when sprint closes:
   ```bash
   cd /Users/bado/iccha/brighthive/jira
   uv run python scripts/generate_sprint_release_notes.py
   ```

3. Enter sprint name (e.g., "Sprint 1")

### What It Does

1. **Pulls from Notion**: Sprint goals, highlights, challenges
2. **Fetches from JIRA**: All completed tickets with assignees
3. **Extracts GitHub PRs**: From ticket descriptions
4. **Generates markdown**: Combined release notes
5. **Publishes to Notion**: Creates page in Releases database

### Example Output

```markdown
# Sprint 1 Release Notes

**Released:** 2026-01-13

## Sprint Goals
- Implement data lake foundation
- Set up multi-org architecture

## Highlights
- Zero downtime deployment
- 25% velocity increase

## Completed Work (47 tickets)

### Epic (3)
- **[BH-123]** Multi-org data lake - [PR](github.com/...) (@Ahmed)
- **[BH-124]** Security hardening - [PR](github.com/...) (@Ahmed)

### Task (32)
...

### Bug (12)
...

## Challenges & Learnings
- CDK deployment optimization needed
- Documentation gaps identified
```

---

## Option 2: GitHub Action (Alternative)

**Best for:** Automatic generation on every release/tag

### Setup Steps

1. **Connect JIRA to GitHub**
   - Go to: https://brighthiveio.atlassian.net/plugins/servlet/applinks/listApplicationLinks
   - Install "GitHub for Jira" app
   - Connect your GitHub organization

2. **Add GitHub Action Workflow**

Create `.github/workflows/sprint-release.yml`:

```yaml
name: Sprint Release Notes

on:
  push:
    tags:
      - 'sprint-*'  # Trigger on sprint-1, sprint-2, etc.

jobs:
  release-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate Release Notes
        uses: patrixr/jira-release-notes@v1
        with:
          jira-host: brighthiveio.atlassian.net
          jira-email: kuri@brighthive.io
          jira-token: ${{ secrets.JIRA_TOKEN }}
          jira-code: BH
          output-file: RELEASE_NOTES.md

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: RELEASE_NOTES.md
```

3. **Add JIRA Token to GitHub Secrets**
   - GitHub repo → Settings → Secrets → New secret
   - Name: `JIRA_TOKEN`
   - Value: Your JIRA API token

4. **Tag Sprint Completion**
```bash
git tag sprint-1
git push origin sprint-1
```

This automatically generates release notes from all commits with JIRA ticket IDs.

## Option 2: Script-Based (Simple)

**Best for:** Manual generation at sprint end

Create script that:
1. Fetches all JIRA tickets in completed sprint
2. Finds associated GitHub PRs (via ticket ID in PR title/branch)
3. Generates markdown changelog

See: `scripts/generate_sprint_release_notes.py`

## Option 3: JIRA Automation Rule

**Best for:** Automated without GitHub Actions

1. Go to: https://brighthiveio.atlassian.net/jira/settings/automation
2. Create new rule: **When sprint closes**
3. Add condition: **Issue has "Fix Version" or linked PRs**
4. Add action: **Send email with sprint summary**

**Template:**
```
Sprint {{sprint.name}} Complete!

{{#issues}}
- [{{key}}] {{summary}}
  GitHub PR: {{fields.customfield_github_pr}}
{{/issues}}
```

## Best Practice: Naming Convention

Your current convention: `username/BH-123/description`

### Branch Names (Already following this)
```bash
git checkout -b drchinca/BH-123/add-feature
```

### Commit Messages (Ticket ID OPTIONAL on feature branch)
```bash
# Simple - no ticket ID needed since branch has it
git commit -m "feat: add user auth endpoint"

# Detailed - include ticket ID for better traceability
git commit -m "feat: add user auth endpoint [BH-123]"
```

**You don't NEED ticket IDs in commits** if your branch name already has it. The PR will link everything together.

**BUT it's recommended** for:
- Better git history traceability
- Cherry-picking commits to other branches
- Understanding isolated commits

### PR Titles (REQUIRED)
```
feat(api): Add user authentication (BH-123)
```

**This is the most important** - automation tools primarily match PRs to tickets via:
1. PR title with ticket ID
2. Branch name with ticket ID
3. Commits with ticket ID (fallback)

### Summary
- ✅ Branch name: Has ticket ID (you already do this)
- ⚠️ Commits: Ticket ID optional but recommended
- ✅ PR title: MUST have ticket ID

## Adobe's JitNotes CLI

For advanced customization:

```bash
npm install -g jitnotes

jitnotes generate \
  --jira-host brighthiveio.atlassian.net \
  --jira-email kuri@brighthive.io \
  --sprint "Sprint 1" \
  --output CHANGELOG.md
```

Retrieves JIRA tickets, finds GitHub PRs, generates from template.

---

## Sources

- [Automating Release Updates with Jira and GitHub](https://dev.to/srinivasamcjf/automating-release-updates-with-jira-and-github-issue-tracking-a-practical-devops-guide-197c)
- [Jira Release Notes GitHub Action](https://github.com/marketplace/actions/jira-release-notes)
- [GitHub for Jira Automation](https://confluence.atlassian.com/automation/use-automation-with-github-1141480582.html)
- [Adobe JitNotes CLI](https://github.com/AdobeDocs/jitnotes)
- [Automated JIRA Release Notes](https://dev.to/patrixr/automated-jira-release-notes-4f20)
- [Release to JIRA Action](https://github.com/marketplace/actions/release-to-jira)
