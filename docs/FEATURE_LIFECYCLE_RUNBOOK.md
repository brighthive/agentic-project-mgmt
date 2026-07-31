---
title: Feature Lifecycle Runbook — spec → ship → verify → capture
epic: BH-1320
last_reviewed: 2026-07-31
related:
  - ../platform-saas-ai-context/docs/infrastructure/DEPLOYMENT_GUIDE.md
  - ../platform-saas-ai-context/docs/architecture/MULTI_REPO_FEATURE_FLOW.md
  - docs/specs/SPEC_TEMPLATE.md
---

# Feature Lifecycle Runbook

> How one feature travels from an idea to live-on-staging, across several repos at once,
> without breaking a shared environment. This is the **operational loop** — the order of
> operations, the gates, and the discipline. It references the
> [Deployment Guide](../../platform-saas-ai-context/docs/infrastructure/DEPLOYMENT_GUIDE.md)
> for the deploy mechanics rather than repeating them, and the
> [Multi-Repo Feature Flow](../../platform-saas-ai-context/docs/architecture/MULTI_REPO_FEATURE_FLOW.md)
> for how the repos wire together.

## The loop at a glance

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                                                                          │
  ▼                                                                          │
① SPEC ──▶ ② REFINE ──▶ ③ TICKETS ──▶ ④ BRANCH+DRAFT PR ──▶ ⑤ BUILD ──▶      │
   (10-§)     (design)    (BH epic)     (per repo, small)     (+ tests)      │
                                                                             │
   ──▶ ⑥ PR MERGE ──▶ ⑦ CI ──▶ ⑧ STAGING DEPLOY ──▶ ⑨ e2e LIVE ──▶ ⑩ CAPTURE ┘
        (squash)      (green)   (per-repo topology)  (real backend)  (new tickets/bugs)
```

Nothing skips a stage. A green stage is not "probably fine" — it's proven before the next
stage starts. When work spans repos, every repo rides its own copy of ④–⑧ **in parallel**;
they only re-converge at ⑨ (one e2e run exercises them together).

**Legend:** 🟢 done/proven · ⚠️ caveat/manual gate · 🚫 blocked · 📄 spec · 🧪 test · ⚙️ CI/deploy · 🔒 needs named approval

---

## ① Spec — no code without one

Every feature starts as a **10-section spec** (`~/.claude/rules/spec-driven.md`), written
*before* any implementation, using [`docs/specs/SPEC_TEMPLATE.md`](specs/SPEC_TEMPLATE.md).
Skill: `/write-spec` or `/write-spec --from BH-XXX`.

| § | Section | What it locks down |
|---|---|---|
| 1 | Context | problem, who, why now (Mermaid for non-trivial flows) |
| 2 | Interface Contract (MDE) | typed boundaries — **port + registry first, adapter second** |
| 3 | Invariants (DbC) | what must always hold (≤15; EARS where it's a state rule) |
| 4 | Acceptance Criteria (BDD) | Gherkin scenarios (≤20) |
| 5 | Out of Scope | explicit non-goals |
| 6 | Dependencies | what must exist first (by ID) |
| 7 | Correctness Properties | state machine / safety / concurrency claims (conditional) |
| 8 | Eval Criteria | how we know an LLM capability works (conditional) |
| 9 | Observability Contract | spans/logs/metrics emitted (conditional) |
| 10 | **Test Coverage Update** | **mandatory** — extends real suites before code |

**Engine-agnostic gate at draft time:** any spec touching a warehouse, pipeline engine,
lineage source, or other swappable system defines a **Port (`Protocol`) + Registry FIRST**,
with the first vendor as adapter #1 — never vendor-hardcoded types sprinkled through domain
logic. Catch this on the first page of §2, not after three tickets already reference the
wrong names. (This is why the whole BH-1320 stack exists: dialect-branched code that silently
assumed Snowflake broke on Synapse/Redshift/Postgres.)

**A spec is done when you can implement it without asking a question.** Ambiguous → fix the
spec, don't guess in code.

---

## ② Refine — design & review before tickets

- Review the spec with the team or `/review-code`. Argue the §2 contract and §3 invariants
  *now*, on paper — it's the cheapest place to be wrong.
- If a POC was needed to prove the approach, it precedes the spec (`/write-poc` → numbers →
  `/write-spec`). Don't spec ahead of a proven approach (premature formalization).
- Multi-repo features: name **which repo owns which contract** here. A boundary that lives in
  platform-core's GraphQL typedefs is verified against *that* source — not re-derived from a
  brightbot dict that consumes it. (Real lesson: verify a claim in the layer that owns it.)

---

## ③ Tickets — spec-driven, epic-parented

Skill: `/create-jira-ticket`. Hard rules (also in [`jira/TICKET_TEMPLATE.md`](../jira/TICKET_TEMPLATE.md)):

1. **Every ticket has `parent: {key: "BH-XXX"}`** — the Epic. No orphans.
2. **`issueType="Task"`, never `"Story"`.** All epic children at Brighthive are Tasks.
3. Project key `BH`, board `152`. Find the epic live: `mcp__jira__jira_get_epics(boardId=152, done=false)` — never hardcode IDs.
4. Ticket body = spec sections distilled: Description · Scope (Include/Exclude) · Acceptance Criteria (Gherkin) · Dependencies · Size.
5. **One ticket = one shippable, reviewable unit.** If a ticket can't land in a <500-line PR, it's two tickets.

Each ticket maps to a §4 scenario cluster + the §10 test cases that prove it. The ticket is
the unit that flows through ④–⑩ below.

---

## ④ Branch + Draft PR — the very first commit

Per `~/.claude/rules/git-workflow.md`, **the moment work starts on a repo:**

```bash
git checkout -b drchinca/BH-XXX/short-description   # name/ticket/description
# first commit — even a placeholder is enough
git commit --allow-empty -m "chore(scope): scaffold BH-XXX"
git push -u origin HEAD
gh pr create --draft --base develop --title "type(scope): description (BH-XXX)"
gh pr edit <n> --add-assignee drchinca \
  --add-reviewer Marwan-Samih-Brighthive,Nano-233,matthewgee
```

- **Draft PR on first commit is MANDATORY** — the 2nd step of any stream of work, not deferred
  until "there's something to show." CI starts running, the branch can't orphan, and everyone
  watching sees work is underway.
- **Base branch is `develop`** (feature → develop → staging → main, one-directional).
- **Check the branch first, every time** — never start on `develop`/`master`/`main`/`staging`.
- **Multi-repo:** one branch + one draft PR **per repo**, each named for the same `BH-XXX`.
  They advance independently; the ticket tracks the set.

---

## ⑤ Build — with tests, small, split proactively

- **Follow the spec.** If the code wants to diverge, stop and fix the spec first (spec drift is
  never silently patched in code).
- **§10 test coverage lands with the code, from the spec — not from the implementation.** At
  least one **real-behavior** L2 test per spec (real adapter/client, real backend or captured
  replay, assert the observable side effect) — mocked-everything tests don't count toward the
  contract. Fixtures mirror a **real captured sample**, never an invented shape.
- **PR-size discipline** (`~/.claude/rules/pr-templates.md`): <500 lines good, 500–700 warn,
  700–900 split now, 900+ must split. 15+ files or unrelated changes → split immediately.
- **File-size discipline:** no source file >1300 lines. Editing a file already over the limit
  means **splitting it first**, not growing it — the split is part of the task, not a blocker.
- **Commit discipline:** 11+ uncommitted files → stop and commit. Conventional commits, no AI
  attribution, no "WIP".

---

## ⑥ PR merge — squash into develop

- **Squash merge** feature → `develop`. PR title becomes the single develop commit — keep it
  `type(scope): description (BH-XXX)`.
- **CI must be green before merge — non-negotiable.** Never `--admin`-merge a red PR into
  develop. A failing PR is unfinished, not parked.
- Merge only with permission; never merge to `develop`/`staging`/`main` unprompted.
- **Multi-repo ordering:** merge the repo that *owns the contract* first (usually
  platform-core for a schema/typedef change), then the consumers (brightbot, webapp), so
  develop is never internally inconsistent between repos.

---

## ⑦ CI — green on the head commit

CI on develop's head must pass before anything promotes. If it's red, it's the top priority —
investigate, fix, push, confirm green. "Green CI without new test cases" means the spec wasn't
enforced — §10 cases must exist and pass.

---

## ⑧ Staging deploy — per-repo topology 🔒

> ⚠️ **Staging is the live client-PoC environment (Longaeva / Loop Capital).** A staging deploy
> is an outward-facing, hard-to-reverse action. **Pause and confirm by name before cutting any
> staging deploy tag or pushing the staging branch** — unless the user has explicitly cleared
> the gate for *this* deploy. See `~/.claude/rules/git-workflow.md` + the security block in the
> workspace `CLAUDE.md`.

The mechanism differs per repo — this is the crux of multi-repo work. Full detail in the
[Deployment Guide](../../platform-saas-ai-context/docs/infrastructure/DEPLOYMENT_GUIDE.md);
the shapes:

| Repo | How staging deploys | Trigger |
|---|---|---|
| **brightbot** | LangGraph Cloud rebuilds the revision | **auto on push to `staging` branch** — promote via PR `develop → staging` using a **merge commit (NOT squash)** to preserve commit identities |
| **platform-core** | `deploy-staging.yml` | cut a **prerelease tag `vX.Y.Z.W-pre-release` on the `staging` branch** 🔒 |
| **webapp** | prerelease-tag driven | same prerelease-tag pattern |

- **Merge ≠ deploy** for tag-driven repos: merging to `staging` doesn't deploy platform-core /
  webapp — publishing the prerelease does.
- **brightbot is the exception** — push to `staging` *is* the deploy.
- **Test before you deploy:** prefer booting the repo(s) on localhost pointed at staging's data
  plane and running e2e there first — see `RUN_LOCAL_AGAINST_STAGING.md`. Never
  deploy-to-staging-then-discover-it's-broken.
- One manual post-deploy step for platform-core (no migration runner): apply
  `setup/scripts/cypher/*-indexes.cypher` via SSM cypher-shell.

---

## ⑨ e2e live testing — real backend, all engines

Re-converge here: one e2e run exercises every repo's change together against **live staging**.

```bash
cd ../brighthive-e2e
export BH_ENV=staging AWS_PROFILE=brighthive-staging
uv run pytest e2e/features/<area> -p no:cacheprovider --workspace-config=<cfg> -rN
```

- **Per-engine coverage** via `--workspace-config`: `oneten` (Snowflake), `loopcapital`
  (SQL Server / Synapse), `bh-demo` (Redshift). Run the ones the feature touches — an
  engine-agnostic change runs **all three**.
- `-rN` shows skip reasons (infra gates ≠ failures). `@pytest.mark.writes` tests need
  `--writes`. `--gate` = fail-fast for CI.
- **Real-behavior bar:** these hit the real backend — the point is to catch what mocks miss.
  If the underlying client behaved differently tomorrow, an e2e test must fail.
- **A skip is not a pass.** Read every skip reason; distinguish an infra gate (quality-repo not
  provisioned) from a real "not reachable" defect.

---

## ⑩ Capture — new tasks & bugs, spec-driven

The run always surfaces something: a gap, a half-wired path, an engine that silently no-ops.
**Capture it as spec-driven work, not a mental note:**

- File each finding as a `BH-XXX` Task under the right epic (③ rules apply). Small, single-
  concern, one PR each.
- If the finding needs design, it re-enters at ① (spec) or ② (refine). The loop closes.
- **Honesty gate:** report outcomes faithfully — tests that failed, steps skipped, engines not
  covered. A finding hidden is a regression shipped.
- Document the finding where it's owned (a memory entry for a durable cross-session fact; the
  spec's §10 if it's a missing test; a Jira ticket for the work).

Real example from the BH-1320 sweep: `updateProject` returns `true` and stamps the
`transformationServiceId` scalar but **never writes the `CONFIGURES` graph edge** — so a
scalar read-back "works" while a relationship traversal reads null. Captured, not lost:
already specced under **BH-1244**.

---

## Multi-repo control — the discipline that keeps it legible

Working several repos at once is where this loop earns its keep. The rules:

1. **One epic, one ticket set, one `BH-XXX` per repo-branch.** The Jira epic is the single
   place the whole feature's state is legible.
2. **Contract owner merges first.** Schema/typedef/DTO change lands in the owning repo
   (usually platform-core) before consumers — develop is never cross-repo-inconsistent.
3. **Each repo rides its own ④–⑧.** Branches, PRs, CI, deploy topology are per-repo and
   independent. Don't block one repo's merge on another's unless there's a real contract
   dependency (then it's a §6 Dependency, tracked).
4. **Re-converge only at ⑨.** The e2e suite is the single cross-repo proof. It's the only place
   you assert the repos work *together* against a real environment.
5. **Deploy order follows dependency order.** Deploy the contract owner to staging, verify it's
   up, then the consumers — so a consumer never deploys against a contract that isn't live yet.

---

## Skills & references

| Need | Skill / Doc |
|---|---|
| Write a spec | `/write-spec` · [`docs/specs/SPEC_TEMPLATE.md`](specs/SPEC_TEMPLATE.md) |
| Prove an approach first | `/write-poc` · [`docs/pocs/POC_TEMPLATE.md`](pocs/POC_TEMPLATE.md) |
| File tickets | `/create-jira-ticket` · [`jira/TICKET_TEMPLATE.md`](../jira/TICKET_TEMPLATE.md) |
| Document a shipped feature | `/write-feature-doc` |
| Deploy mechanics (per repo, flags, promotion) | [DEPLOYMENT_GUIDE.md](../../platform-saas-ai-context/docs/infrastructure/DEPLOYMENT_GUIDE.md) |
| How repos wire together | [MULTI_REPO_FEATURE_FLOW.md](../../platform-saas-ai-context/docs/architecture/MULTI_REPO_FEATURE_FLOW.md) |
| Test local against staging data | [RUN_LOCAL_AGAINST_STAGING.md](../../platform-saas-ai-context/docs/infrastructure/RUN_LOCAL_AGAINST_STAGING.md) |
| Staging learnings / creds | [STAGING_LEARNINGS.md](../../platform-saas-ai-context/docs/infrastructure/STAGING_LEARNINGS.md) |
