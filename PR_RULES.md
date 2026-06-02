# BrightHive PR Size Rules

> Single source of truth for PR sizing across **every BrightHive repo** and **every AI agent** (Claude Code, Cursor, Gemini, GitHub Copilot, anyone else).
>
> If you're a human: same rules. The team trusts that small PRs review faster, ship faster, and break less.

## The hard limit

```
< 500 lines      → ✅ Good — proceed
500–700 lines   → ⚠️  Warning — consider splitting
700–900 lines   → 🛑 Stop — split now
≥ 900 lines     → ❌ BLOCKED — must split before requesting review
```

PRs over 900 lines do not get reviewed. Period. No "but it's all generated code", no "but it's mostly tests", no "but the diff is small in spirit". The reviewer's brain has the same fatigue limit whether your lines are GraphQL typedefs, Python tests, or YAML.

## Red flags that mean "split immediately"

- 15+ changed files
- Multiple unrelated changes ("while I was here…")
- Schema change + business logic + tests + new module all in one PR
- The PR description has more than 3 distinct "What" bullets

## How to split

| Symptom | Split shape |
|---|---|
| Schema + resolver + caller all changed | PR1: schema (additive, default values) → PR2: resolver implementation → PR3: caller migration |
| Tests are huge | PR1: feature behind feature flag (off) + minimal smoke test → PR2: full test suite + flip flag |
| Cross-repo work | One PR per repo, sequenced. Reference the spec in each. |
| New service / module | PR1: scaffolding + interfaces + 2-3 contract tests → PR2: implementation → PR3: integration |
| Refactor + feature | PR1: pure refactor (zero behavior change) → PR2: feature on the new shape |

## Templates

| PR Size | Files | Lines | Template |
|---|---|---|---|
| Small | 1–3 | < 200 | Minimal — *What & Why* + *Tests* checkbox |
| Medium | 4–10 | 200–500 | Standard — *What & Why* + *Changes* + *Tests* + *Review Steps* |
| Large | 10+ | 500+ | Full — Ticket link, Description, Changelog, Unit Tests, Steps to Review, Notes |

Templates live in `~/.claude/rules/pr-templates.md`. Mirror at `agentic-project-mgmt/PR_RULES.md` (this file). If you're an agent without access to the user's home dir, the relevant excerpts are in the *Templates* section below.

## Specifically for AI agents

If you are Claude Code, Cursor, Gemini, Copilot, or any other agent generating code into a BrightHive repo:

1. **Track diff size as you work.** When you've added 400 lines, stop and ask the human whether to split.
2. **If the user asks for something that obviously exceeds 900 lines**, propose a split shape *before* writing any code. The human will say yes.
3. **Refactor + feature in one PR is forbidden.** Split. Even if the user told you to do both.
4. **Generated code (GraphQL types, OpenAPI clients, codegen) does not count toward the limit IF it's gitignored.** If it's committed, it counts.
5. **Vendor / dependency changes** are their own PR. Don't bundle a pyproject bump into a feature PR.
6. **If you're 700+ lines deep and the work isn't done**, save state, write a follow-up PR description, ship the partial work, open the next PR.

## Recent examples (good and bad)

**Bad — `feat/BH-529-github-enterprise-support` (PR #778, 3,692 lines, 9 files)**
This PR mixes: GraphQL schema additions, 7 resolver implementations, a 622-line proxy service, transformation-service model changes, and zero tests. Should have been:
- PR1: schema additions only (typedefs.ts +134 lines, default-pass coalescing) — ~200 lines
- PR2: `github-proxy.ts` core + `parseRepoInfo` with property-based tests — ~400 lines
- PR3: resolver wiring with workspace-tenant check + integration tests — ~400 lines
- PR4: `transformation-service.ts` model fields — ~200 lines

**Bad — `BH-529-dbt-agent-github-proxy-via-platform-core` (PR #490, 1,904 lines changed, 15 files)**
Same problem: mixes 8 tool rewrites, 190 lines of new GraphQL client, state migration, and test updates. Should have been 3 PRs minimum.

**Good — `harbour/BH-548/fix-collaborator-agent-permissions` (PR #776, 10 lines)**
One file, one resolver-permission change, one ticket. Reviewed and merged in under an hour.

**Good — `harbour/BH-516/fix-nav-active-state` (PR #1108, 48 lines)**
One bug, scoped fix, mergeable in 15 min.

## Enforcement

- **Reviewers**: if a PR is over 900 lines, comment `BLOCKED: PR exceeds 900-line limit per /Users/bado/iccha/brighthive/agentic-project-mgmt/PR_RULES.md — please split` and do not review further.
- **Authors**: don't request review on a 900+ PR. CI may or may not warn; the social rule is that reviewers will refuse.
- **AI agents**: same as authors. You get the same rules a human does.

## Templates (excerpts)

### Small (< 200 lines)

```markdown
## What & Why
- **What**: [1-2 sentences]
- **Why**: [1 sentence]

## Tests
- [ ] Unit tests added/modified
- [ ] Tests passing locally
```

### Medium (200–500 lines)

```markdown
## What & Why
**What does this do?** [Bullet points]
**Why was this needed?** [Brief context — link to ticket/spec]

## Changes
- **Added**: [files/features]
- **Modified**: [files/changes]
- **Removed**: [if applicable]

## Tests
- [ ] Unit tests added/modified
- [ ] All tests passing

## Review Steps
[specific commands to verify the feature]

## Notes
- [Edge cases, risks, follow-ups]
```

### Large (500–900 lines, only when split is genuinely impossible)

```markdown
# Pull Request
_`type(scope): brief description`_

## Ticket
[Jira link]

## Description
### What does this PR do?
[Comprehensive overview]

### Why was this needed?
[Context]

### Why couldn't this be split?
[Required for any PR over 700 lines — explain to the reviewer why the work
cannot be broken into smaller PRs. If you can't answer this convincingly,
the PR can be split.]

## Unit Tests
- [ ] Added / [ ] Modified

## Steps to Review
[Setup + run + verify]

## Risks / Notes
[Edge cases, follow-ups]
```

---

**Source**: this rule originates from `~/.claude/rules/pr-templates.md` in the user's global Claude Code config. This repo file is the authoritative shareable copy for the team and any AI agent.
