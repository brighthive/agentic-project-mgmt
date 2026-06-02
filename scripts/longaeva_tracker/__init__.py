"""Longaeva trial tracker — joins Jira + GitHub PRs into a live tracker doc.

Reads:
  - Jira REST API: BH-526 children, Snowflake spec children, BH-503 children,
    and any open ticket whose summary/description mentions Longaeva or POC.
  - GitHub PRs across the BrightHive repos the trial touches.

Writes:
  - clients/trials/longaeva/TRACKER.md — single source of truth.
  - Manual sections (Blockers / This Week / Daily Notes / Open Questions) are
    preserved across refreshes via in-page markers.

Refresh:
  - Manual: `make longaeva-tracker`
  - Cron:   nightly 6am ET via `crontab`.

Slack:
  - One-liner to #engineering on every refresh, diff-aware so noise stays low.

Auth (env vars consumed by config.load):
  - JIRA_BASE_URL       https://brighthiveio.atlassian.net
  - JIRA_USER_EMAIL     you@brighthive.io
  - JIRA_API_TOKEN      Atlassian API token
  - GITHUB_TOKEN        passed through to `gh`
  - SLACK_BOT_TOKEN     optional; posts to #engineering when set
"""
