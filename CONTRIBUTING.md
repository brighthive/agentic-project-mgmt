# Contributing to `agentic-project-mgmt`

> Repo-specific contribution rules. For onboarding (vault unpack, `.env` materialization, sibling-repo cloning) see [`ONBOARDING.md`](./ONBOARDING.md). For agent scope rules see [`AGENTS.md`](./AGENTS.md).

## What lives in this repo

| Type | Where |
|---|---|
| Sprint data + release notes | `jira/sprint/{N}/` |
| Active client trials + customers | `clients/trials/{slug}/`, `clients/active/{slug}/` |
| Implementation specs | `docs/specs/` |
| Feature documentation | `docs/features/` |
| Bedrock migration journal | `docs/bedrock/` |
| POC experiments | `docs/pocs/` |
| Vault CLIs (Secrets / DynamoDB / LastPass) | `aws-secrets-vault/`, `dynamo-vault/`, `lastpass-vault/` |
| Onboarding scripts | `scripts/` |
| Notion page map | `notion/pages.md` |

If your change doesn't fit one of these, ask in `#engineering` before opening a PR — it might belong in a sibling repo.

## Workflow

### 1. Sync + scan before branching

Always `git fetch`/`pull` before starting work — never branch off a stale local `master`. Then
skim recent team activity with `git log` so you know what landed since you last looked (avoids
duplicate work, conflicting specs, or missing a teammate's in-flight change on the same area):

```bash
git checkout master
git fetch origin
git pull --ff-only
git log --oneline -15                 # what's landed recently
git log --oneline origin/master..master   # catch any of YOUR unpushed commits before branching off them
```

If `master` is ahead of `origin/master` (an unpushed commit sitting locally), resolve that first —
push it or ask the author — before branching, so your new branch doesn't silently carry someone
else's unreviewed work into your PR.

### 2. Branch

Branch off `master`. Naming: `name/BH-XXX/short-description` — a ticket is mandatory, not optional. If no ticket exists yet, file one first (see `jira/TICKET_TEMPLATE.md`), then branch. Examples: `drchinca/BH-745/longaeva-operator-runbook`, `marwan/BH-409/sprint-9-release-notes`.

```bash
git checkout -b drchinca/BH-XXX/<short-description>
```

### 3. Commit using Conventional Commits

`type(scope): description` under 72 chars, imperative mood. Types: `feat | fix | docs | style | refactor | test | chore | perf | ci | build`. Example:

```
docs(longaeva): operator runbook for trial Day 1 — pre-flight + 4-mutation demo script
```

The first commit on the branch is meaningful work. After that commit, **push and open a draft PR immediately** before any further work — see §4.

Never amend a commit that's already been pushed. Never `git push --force` without explicit permission. Never commit AI attribution such as `Co-Authored-By: Claude`, `Co-Authored-By: Codex`, or "Generated with ..." text.

### 4. Open a draft PR on the first push

This is mandatory, not optional. After the first meaningful commit:

```bash
git push -u origin drchinca/BH-XXX/<short-description>
gh pr create --draft --base master --title "type(scope): description"
gh pr edit --add-assignee drchinca \
  --add-reviewer Marwan-Samih-Brighthive,sherbiny-bh,Nano-233,matthewgee
```

Why draft + reviewers immediately:
- CI runs from commit one — catches failures while the work is still in your head
- Reviewers see scope upfront and can flag direction issues before you've over-invested
- Visibility — no orphan branches with weeks of work hidden

Continue working with additional commits; each push updates the same draft PR. When you think it's done, mark **Ready for review**.

### 5. PR description

Match template to PR size (per [`PR_RULES.md`](./PR_RULES.md)):

| Size | Files | Lines | Template |
|---|---|---|---|
| Small | 1-3 | < 200 | What & Why + Tests |
| Medium | 4-10 | 200-500 | What & Why + Changes + Tests + Review Steps |
| Large | 10+ | 500+ | Full template (Description / Why / Changelog / Tests / Setup / Run / Verify / Notes) |

PRs over 900 lines must be split. PRs over 500 lines need a strong reason in the description.

### 6. Merge

Reviewer approves → squash-merge to `master`. The PR title becomes the single squash-commit message — keep it conventional and clean. Never merge directly without a PR. Never merge to `master` without explicit review approval (admin-merge override exists but should leave a comment explaining why).

## What gets reviewed

| Change type | Required reviewers |
|---|---|
| Sprint artifacts (`jira/sprint/{N}/`) | Whoever ran the sprint-release skill, plus one engineering lead |
| Client trial docs (`clients/trials/{slug}/`) | drchinca + the trial owner |
| Specs (`docs/specs/`) | drchinca + the senior engineer who'll implement |
| Vault CLI changes | drchinca + sherbiny-bh (security review) |
| Onboarding scripts | drchinca + one fresh joiner who can validate the flow |
| Notion / Jira tooling | Whoever uses the tooling most |

Default reviewer set for PRs that don't fit a category: `Marwan-Samih-Brighthive`, `sherbiny-bh`, `Nano-233`, `matthewgee`. Assignee always: `drchinca`.

## Standards

- **Conventional commits** for the title and any commit messages
- **Mobile-first responsive** for any UI work in sibling repos referenced from here (none in this repo, but the cross-repo standard holds)
- **No AI attribution** in commits or PR bodies
- **No proactive `.md` files** — this repo is a doc hub; create new `.md` only when there's a real consumer for it (a runbook, a spec, an index)
- **Bash standards** for `scripts/*.sh` per `~/.claude/rules/bash-scripts.md`: `set -euo pipefail`, quoted `"${vars}"`, `mktemp` + `trap` cleanup, `require_commands` gate
- **Frontmatter required** on client trial docs (see `clients/AGENTS.md`)

## Adding a new client trial

1. `cp -r clients/_templates/TRIAL.md clients/trials/<slug>/overview.md`
2. Add `clients/trials/<slug>/README.md` as the folder index (follow `clients/trials/longaeva/README.md` shape)
3. Update `clients/README.md` with the new client row
4. File the trial epic in Jira; link the epic key in the trial-folder frontmatter
5. Open a draft PR per §4

## Adding a new spec

1. `cp docs/specs/SPEC_TEMPLATE.md docs/specs/SPEC-<NAME>.md`
2. Fill all required sections from `docs/specs/SPEC_TEMPLATE.md` and `docs/AGENTS.md` (Context, Interface Contract, Invariants, Acceptance Criteria, Out of Scope, Dependencies, and required test coverage; add Correctness Properties / Eval / Observability when the template calls for them)
3. Open a draft PR — specs ship as PRs even when no code yet exists
4. Reviewer approves → §10 questions get resolved by the spec author and pasted back into the spec body
5. Squash-merge once §10 is signed off

## Adding a new sprint

The sprint-release skill (`/sprint-release`) handles this end-to-end in Claude Code. If you're authoring artifacts manually or using another agent, see `jira/AGENTS.md` for the process, `jira/CLAUDE.md` for legacy schema detail, and `jira/sprint/SPRINTS.md` for the velocity table.

## Reporting issues

This repo doesn't track engineering bugs — those go in Jira under their respective project epics. Use GitHub issues here only for repo-meta things (broken `make` target, stale onboarding step, vault-CLI bug).

## Questions

Ping `#engineering` on Slack. For the Longaeva trial specifically, drchinca is on point.
