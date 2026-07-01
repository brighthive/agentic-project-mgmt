---
name: poc-drive
description: Drive one PoC scorecard criterion (e.g. Longaeva 2.5, 1.3, 4a.3) through its full delivery lifecycle — spec → Jira → branch → code → integration test → PR → Notion/scorecard update — with a verification gate at every step so you END 100% certain the criterion does what it's intended to. Use when the user says "drive PoC point X", "take criterion 2.5 to done", "implement and verify the next PoC item", or "run the lifecycle for <criterion>".
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent, TaskCreate, TaskUpdate, TaskGet, AskUserQuestion
---

# poc-drive — one PoC criterion, full lifecycle, verified end to end

Take a **single PoC scorecard criterion** from "intended" to "proven done" through
every lifecycle stage, with a hard verification gate between each. The output is
not "code written" — it is **evidence the criterion does what the scorecard says**,
linked across spec, Jira, PR, and scorecard.

> **Cardinal rule for this skill:** never mark a stage green on intent. Each gate
> has a *proof* — a passing test, a live `snow` query, a real PR URL, a deployed
> check. "PR merged" ≠ "deployed" ≠ "verified" (see memory `feedback_pr_state_honesty`).
> If you can't prove it, the stage stays open and you say so.

## When to use

The user says something like:
- "Drive PoC point 2.5" / "take criterion 1.3 to done"
- "Implement and verify the next PoC item end to end"
- "Run the full lifecycle for the Atlas verified-query criterion"
- "Make sure 4a.3 actually works, the whole way through"

Skip / redirect when:
- The user wants a *status readout* only → that's `poc-callouts` or just read the scorecard.
- The user wants to author a brand-new spec from scratch with no criterion → `/write-spec`.
- The ask spans many criteria at once → drive them **one at a time**; offer to loop.

## Inputs (for client `<slug>`, default `longaeva`)

Resolve these before doing anything. They are the contract.

| Input | Path | Role |
|---|---|---|
| **Scorecard** | `clients/trials/<slug>/scorecard.md` | The criterion list + pass targets. The criterion ID (e.g. `2.5`) is the unit of work. |
| **PoC config** | `clients/trials/<slug>/poc.yaml` | epic, adjacent epics, repos, ownership (owner + lane + slack_id). |
| **Tracker** | `clients/trials/<slug>/TRACKER.md` | live Jira/PR linkage; run `make poc-tracker-no-slack CLIENT=<slug>` to refresh (`make longaeva-tracker-no-slack` is the Longaeva alias). |
| **Gap analysis** | `clients/trials/<slug>/BRIGHTHIVE_GAPS.md` | maps criteria → GAP-N → tickets; the "why this isn't done yet". |
| **Integration runbook** | `clients/trials/<slug>/integration/00-STAGING-INTEGRATION-RUNBOOK.md` | gate ordering + staging verify steps. |
| **Merge order** | `clients/trials/<slug>/integration/06-MERGE-ORDER.md` | per-PR dependency chain. |
| **Impl specs** | `clients/trials/<slug>/integration/impl-specs/` | paste-ready, code-verified specs per ticket. |
| **Contract artifacts** | `clients/trials/<slug>/artifacts/` | e.g. `atlas-semantic-view-spec.md` — the format the criterion must satisfy. |
| **Sandbox** | `clients/trials/<slug>/sandbox/` | the known-good target to verify against (live Snowflake). |

Source repos are siblings at `../<repo>` (see root `CLAUDE.md` → Source Repositories).

## The lifecycle (8 gates — do them in order, prove each)

Track the whole run with `TaskCreate` (one task per gate) so progress is visible.
**Do not advance to gate N+1 until gate N's proof exists.** If a gate can't pass
(external blocker, missing creds), STOP, record why, and surface it — don't fake it.

### Gate 0 — Frame the criterion (what "done" means)

1. Read the scorecard row for the criterion. Extract: the **target** (e.g. "≥1 query
   per major use case"), the **owner** (from `poc.yaml` ownership lane), and the
   **pass condition**.
2. Find its GAP in `BRIGHTHIVE_GAPS.md` and its ticket(s) in `poc.yaml` / tracker.
3. Write a one-paragraph **intent statement**: "Criterion X is done when <observable
   outcome> is true, proven by <proof method>." Show it to the user; this is the
   contract for the rest of the run. If the scorecard target is ambiguous, ask
   (`AskUserQuestion`) — don't guess a pass bar.

**Gate 0 proof:** a written, user-confirmed intent statement with a named proof method.

### Gate 1 — Spec (no code without a spec)

Per `~/.claude/rules/spec-driven.md`. Check `integration/impl-specs/<TICKET>.md` first.
- If a spec exists, **verify it against real code** (line numbers, symbols, imports) —
  specs go stale. Use a subagent (see "Verification via subagents" below) to confirm
  every falsifiable claim before trusting it.
- If no spec, write one (or invoke `/write-spec`): §2 interface contract, §3 invariants,
  §4 Gherkin acceptance criteria that *encode the scorecard pass condition*, §8 eval
  criteria if LLM behaviour is involved.

**Gate 1 proof:** a spec whose acceptance criteria, if all pass, satisfy the scorecard
target — and (if pre-existing) a subagent audit confirming it matches current code.

### Gate 2 — Jira (every ticket assigned, under the epic)

Per `rules/brighthive-jira.md`. Find the live epic: `mcp__jira__jira_get_epics(boardId=152, done=false)`.
- Ensure a ticket exists for the criterion (create with `parentKey="BH-XXX"`,
  `issueType="Task"`, assigned to the lane owner — never leave unassigned, per memory
  `feedback_always_assign_tickets`).
- Link the spec + scorecard criterion ID in the ticket description.
- Transition to In Progress when code starts.

**Gate 2 proof:** a real BH-XXX key, assigned, parented to the epic, referencing the criterion.

### Gate 3 — Branch (greenfield discipline + WIP safety)

- Confirm the target repo + base branch from `06-MERGE-ORDER.md` (usually `develop`,
  sometimes a stacked parent branch).
- **Before switching branches, protect uncommitted work**: `git status --short`. If the
  working tree is dirty, check whether the change is unique or a dup of another branch
  (`diff` against the branch's version); stash with a descriptive message, never discard.
- Branch name: `<name>/BH-XXX/<slug-desc>` (e.g. `marwan/BH-592/dbt-sources-generator`).

**Gate 3 proof:** on the right branch, off the right base, clean tree, WIP preserved.

### Gate 4 — Code (implement against the verified spec)

- Implement the spec's interface contract exactly. Match surrounding code style.
- **Reuse the proven pattern** — grep for how the codebase already does the adjacent
  thing (e.g. `get_warehouse_config_from_secrets` → factory is the warehouse-connection
  pattern; don't invent `get_warehouse_secret`). Verify every import resolves.
- Constants over magic strings; DI over singletons (`rules/testable-code.md`).
- Commit in logical units; ≤11 uncommitted files (`rules/git-workflow.md`).

**Gate 4 proof:** code compiles/imports clean; `ruff` + `mypy` pass; commits exist.

### Gate 5 — Test (unit first, then the real thing)

Two layers, both required where applicable:
1. **Unit** — `uv run pytest <path> -v` in the repo's `.venv`. Mock the *seam the code
   actually uses* (if the code calls `execute_query`, mock that — not a cursor it bypasses).
   Run until green. Report the count.
2. **Live / integration** — this is where intent meets reality. Use the **real target**:
   - Snowflake criteria → run the actual SQL via `snow sql -c brighthive` against
     `LONGAEVA_POC` (see `reference_snowflake_cli` memory). A query that compiles and
     returns rows is proof; a paper review is not. *This is how the KEY_COLUMN_USAGE and
     SEMANTIC_VIEW table-qualification bugs were caught — neither was visible on paper.*
   - Agent criteria → drive brightbot through a scoped harness or the repo's own test
     entrypoint and observe the real output.
   - dbt criteria → `dbt parse` / `dbt build` against the sandbox.
3. If live verification needs creds you don't have (e.g. Grant's GHE PAT), mark the live
   step **blocked**, name the blocker, and keep the gate open.

**Gate 5 proof:** unit suite green (with count) AND a live run transcript showing the
criterion's pass condition met against the real target — or an explicit blocked-on-X note.

### Gate 6 — PR (open as draft immediately, revise to green)

Per `rules/git-workflow.md` + `rules/pr-templates.md`.
- Push; open a **draft PR** immediately (`gh pr create --draft --base <base>`).
- Assignee: the PR author (self-assign); reviewers: the rest of the team roster (see `CONTRIBUTING.md`).
- PR body: link the spec, the Jira key, the scorecard criterion, and **paste the Gate 5
  proof** (test counts + live transcript). Size ≤900 lines; split if larger.
- Iterate on CI / review until green. Squash-merge only with explicit user go.

**Gate 6 proof:** a real PR URL, CI status, draft/ready state stated honestly.

### Gate 7 — Update the record (scorecard + Notion + tracker)

Only after Gates 0–6 have real proof:
- Flip the scorecard row's Result/Pass with the evidence (test count, query result, PR #).
  Keep the honesty header accurate — if it's verified on a branch but not deployed, say so.
- Update Notion (the trial's tech-input / scorecard page) via the `notion-brighthive` MCP —
  mirror the scorecard delta, don't invent. Authenticate if needed.
- Refresh the tracker: `make poc-tracker-no-slack CLIENT=<slug>` (Longaeva alias: `make longaeva-tracker-no-slack`).
- Comment on the Jira ticket with the proof + PR link.

**Gate 7 proof:** scorecard cell updated with evidence; Notion + tracker reflect it; Jira commented.

## Verification via subagents (use liberally — keeps main context clean)

For Gates 1 and 5, spawn a focused subagent per independent check (one criterion's
spec audit, or one repo's code verification). Give each subagent: the exact file/branch,
read-only `git show` instructions (never mutate the working tree), and a numbered list of
falsifiable claims to confirm/refute with VERDICT + evidence. Run independent audits in
parallel. This is how you stay 100% certain without bloating the driver's context. See
`rules/context-engineering.md` RULE CE-3 (handoff is a deliberate write).

## Multi-agent code review (Gate 4 → before PR ready)

Per `python-environment.md`: Solutions Architect → Senior Python → QA → Junior Dev, one
focused subagent each, on the diff. Required before flipping a PR from draft to ready.

## End-of-run readout

Always end with a per-gate table: `Gate | Status | Proof`. Mark green only what has proof.
State the single most important remaining blocker (if any) for standup. Never report
intended behaviour as shipped.

## Worked reference (Longaeva criterion 2.5 — verified queries)

> Intent: "2.5 is done when the scaffolded YAML's `verified_queries[]` use Snowflake
> `SEMANTIC_VIEW(...)` syntax and at least one round-trips live." Spec: `impl-specs/BH-591-wire-atlas-tool.md`.
> Gate 5 live proof: `snow sql -c brighthive -q "SELECT * FROM SEMANTIC_VIEW(LONGAEVA_POC.
> SEMANTIC.SV_DAILY_PORTFOLIO_EXPOSURE DIMENSIONS EXPOSURE.asset_class_code, EXPOSURE.as_of_date
> METRICS EXPOSURE.total_exposure_usd)"` → returns rows. **Cross-table dims must be qualified
> by their owning table** (`EXPOSURE.region` fails — `region` is on a joined table). That
> rule lives in the BH-591 prompt; the live query is the proof.

## House rules this skill always honors

- `feedback_pr_state_honesty` — open PR ≠ shipped. Verify `gh pr` state before any status claim.
- `feedback_always_assign_tickets` — every Jira ticket assigned on creation.
- `feedback_no_backward_merge` — `feature → develop → staging`, never backward.
- `feedback_squash_merge` — multi-commit features merge via squash, through a PR.
- `rules/spec-driven.md` — no code without a spec; update spec on drift, don't patch around it.
- `rules/testable-code.md` — if testing needs `patch()`, refactor; mock the real seam.
