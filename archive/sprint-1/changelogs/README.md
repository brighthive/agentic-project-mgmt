# Sprint 1 Changelogs

This directory contains per-repository changelogs for Sprint 1 (January 13-20, 2026).

---

## Structure

Each repository that had commits during Sprint 1 has a dedicated changelog file:

- `brighthive-platform-core.md` - Backend platform security fixes
- `brighthive-webapp.md` - Frontend security and UX improvements
- `brightbot.md` - AI agent infrastructure modernization
- `brighthive-data-organization-cdk.md` - Organization CDK documentation
- `brighthive-data-workspace-cdk.md` - Workspace CDK documentation

---

## Repository Status

### Active Development (Sprint 1)
- **brightbot** - 19 commits, 21 story points (most activity)
- **brighthive-webapp** - 5 commits, 10 story points (security focus)
- **brighthive-platform-core** - 3 commits, 5 story points (security focus)
- **brighthive-data-organization-cdk** - 1 commit, 1 story point (docs)
- **brighthive-data-workspace-cdk** - 1 commit, 1 story point (docs)

### No Activity (Sprint 1)
- **brightbot-slack-server** - No commits (planning only)

---

## Global Sprint 1 Artifacts

For sprint-level overview:
- **Technical Release Notes:** `../SPRINT_1_RELEASE_NOTES.md`
- **Marketing Release Notes:** `../SPRINT_1_MARKETING_RELEASE_NOTES.md`
- **Sprint Plan:** `../PLAN.md`
- **Jira Snapshot:** `../jira/sprint_1_snapshot.json`

---

## Changelog Format

Each changelog follows this structure:

1. **Breaking Changes** - API or behavior changes requiring migration
2. **Features** - New functionality
3. **Security** - Security fixes and improvements
4. **Bug Fixes** - Defect resolutions
5. **Documentation** - Docs updates
6. **Chores** - Maintenance and cleanup
7. **Impact** - Business and technical impact summary

---

## Automation

Going forward, changelogs are automatically generated via GitHub Actions:
- **Workflow:** `.github/workflows/changelog.yml`
- **Config:** `cliff.toml`
- **Trigger:** Push to main/master branch
- **Tool:** git-cliff

---

**Last Updated:** 2026-01-20
**Sprint:** Sprint 1 🍇
**Total Commits:** 29 across 5 repositories
