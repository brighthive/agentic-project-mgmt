---
title: "Longaeva — 23→4 PR consolidation plan"
audience: "Kuri, Marwan, Ahmed, Harbour"
purpose: "Collapse the ~23 stacked trial PRs into 4 reviewable integration PRs, in dependency order, without burying review feedback"
last_reviewed: "2026-06-06"
status: "PLAN — no branch surgery executed yet. Awaiting go per consolidation gate."
---

# Longaeva — 23→4 PR consolidation plan

> **What this is.** A written, auditable plan to fold the ~23 open trial PRs into
> **4 integration PRs**, one per workstream, in dependency-correct order. Nothing
> here is executed yet — this is the map to approve *before* any rebase/squash.
>
> **Why.** The PRs are stacked 3–6 deep on parent branches; reviewing 23 separately
> is untenable and the stacks compound. But two foundation PRs are
> **CHANGES_REQUESTED** (pc#778, bb#490) — consolidation must NOT bury that feedback.

## Live state (re-scanned 2026-06-06)

| PR | State | Review | Base | Workstream |
|---|---|---|---|---|
| bb#488 | OPEN | REVIEW_REQUIRED | develop | 1 Snowflake |
| bb#489 | OPEN·draft | REVIEW_REQUIRED | develop | 1 Snowflake (atlas) |
| bb#502 | OPEN·draft | — | drchinca/BH-531 (bb#489) | 1 Snowflake (BH-592 dialect) |
| pc#777 | OPEN | REVIEW_REQUIRED | develop | 1 Snowflake (OMD) |
| cdk#156 | OPEN | REVIEW_REQUIRED | develop | 1 Snowflake (secret store) |
| pc#778 | OPEN | **CHANGES_REQUESTED** | develop | 2 GHE proxy |
| pc#780/781/782/783 | OPEN·draft | — | feat/BH-529 (pc#778) | 2 GHE proxy hardening |
| bb#490 | OPEN | **CHANGES_REQUESTED** | develop | 2 GHE proxy consumer |
| bb#492/493/494/496 | OPEN·draft | — | BH-529 (bb#490) | 2/3 proxy + dbt migration |
| bb#495 | OPEN·draft | — | BH-529 (bb#490) | 4 dead code |
| bb#497 | **MERGED** | — | develop | 5 MCP/Okta |
| pc#784 | OPEN | REVIEW_REQUIRED | develop | 5 MCP/Okta |
| pc#788/789/790 | OPEN | — | BH-573 (pc#784) | 5 MCP/Okta |
| wa#1132 | OPEN | REVIEW_REQUIRED | develop | 5 MCP/Okta (spec) |
| bb#501 | OPEN | REVIEW_REQUIRED | develop | 5 MCP/Okta (docs) |

## The 4 target PRs

Each target = one squash-friendly integration branch off `develop`, absorbing its
stack's children. Niche → PR mapping (niches already defined in `README.md`):

### PR-1 — Snowflake / BYOW foundation
**Branch:** `integration/snowflake-byow` off `develop`
**Absorbs:** bb#488, bb#489, **bb#502 (BH-592 dialect)**, pc#777*, cdk#156*
(*pc + cdk land as their own repo PRs — "PR-1" is really one-per-repo, grouped by theme.)
**Order within:** bb#488 (SnowflakeConnection) → bb#489 (atlas scaffold, needs nothing from 488 at import) → bb#502 (dialect, currently stacked on bb#489 — collapses cleanly).
**Conflict surface:** none internal. bb#502 was authored on the bb#489 base, so it fast-forwards.
**Review debt:** none CHANGES_REQUESTED; all REVIEW_REQUIRED (fresh review, not rework).

### PR-2 — GitHub Enterprise proxy + dbt migration
**Branch:** platform-core `integration/ghe-proxy` (pc#778+780-783) and brightbot `integration/ghe-proxy` (bb#490+492-496).
**Absorbs:** pc#778, pc#780, pc#781, pc#782, pc#783 / bb#490, bb#492, bb#493, bb#494, bb#496.
**Order within (per runbook Gate B/C):** children onto parent branch, then parent squashes. bb#494 **before** bb#496 (496 imports 494's modules).
**⚠️ Conflict surface with PR-1:** bb#490 rewrites the SAME 5 dbt-agent files BH-592 (bb#502) edits — `dbt_tools.py`, `dbt_agent_prompts.py`, `state.py`, `dbt_agent_react.py`, `dbt_react_system_prompt.py`. **Resolution: rebase bb#502 onto bb#490's branch** (post-proxy-rewrite), resolve once, before either squashes. See "Collision" below.
**🛑 Review debt: pc#778 + bb#490 are CHANGES_REQUESTED.** These reviews MUST be resolved by the author before this PR consolidates — squashing does not clear them. This is the gating item for PR-2.

### PR-3 — MCP / Okta federation
**Branch:** platform-core `integration/mcp-okta` (pc#784+788-790), plus wa#1132 + bb#501 as their own small docs PRs.
**Absorbs:** pc#784, pc#788, pc#789, pc#790, wa#1132, bb#501. (bb#497 already MERGED.)
**Order within:** pc#784 (Cognito+Okta) → 788/789 (docs) → 790 (DNS CDK). Note pc#790 + pc#784 have **manual `cdk deploy`** steps (runbook Gate D) — not covered by squash-merge.
**Conflict surface:** independent of PR-1/PR-2.
**Review debt:** pc#784 + wa#1132 + bb#501 are REVIEW_REQUIRED (fresh).

### PR-4 — Layer-B dbt authoring capability
**Branch:** new work — **no PRs exist yet** (BH-590 introspection, BH-591 atlas wiring, BH-592 already in PR-1, BH-594 schema tests).
**Absorbs:** future PRs for BH-590, BH-591, BH-594.
**Depends on:** PR-1 deployed (needs SnowflakeConnection + atlas scaffold live).
**Honesty:** this PR is mostly *future work*, not consolidation. Listed so the 4-bucket model is complete; don't block PR-1/2/3 on it.

## The collision (bb#502 ↔ bb#490) — resolution

Both touch all 5 dbt-agent files. The decided fix (rebase bb#502 onto bb#490):

1. Confirm bb#490's review is resolved + its branch is current.
2. `git rebase --onto <bb#490-head> drchinca/BH-531 drchinca/BH-592/dbt-agent-snowflake-dialect`
3. Resolve conflicts in the 5 files: bb#490 moves dbt github ops to the proxy; BH-592 adds `warehouse_type` + dialect. These are **orthogonal concerns in the same files** — the merge keeps both (proxy routing AND dialect awareness). Re-run the 26 BH-592 tests + bb#490's tests after.
4. bb#502's PR base changes from `drchinca/BH-531` to bb#490's branch.

> Do this rebase **only after** bb#490 is review-clean — rebasing onto a branch
> that's about to change wastes the conflict resolution.

## Execution order (dependency-correct)

```
1. Resolve pc#778 CHANGES_REQUESTED ─┐
2. Resolve bb#490 CHANGES_REQUESTED ─┤ (human review actions — NOT git ops)
                                     │
3. PR-1 (Snowflake) ────────────────┼─ independent, can land first
   488 → 489 → 502                   │
4. PR-2 (GHE proxy) ─────────────────┘ after 1+2 resolved
   pc#778(+780-783) → deploy staging → bb#490(+492-496) [+ bb#502 rebased in]
5. PR-3 (MCP/Okta) ── independent; includes manual cdk deploy
6. PR-4 (Layer-B) ── future work, after PR-1 deployed
```

## What this plan will NOT do (guardrails)

- **Not** squash away CHANGES_REQUESTED feedback. pc#778/bb#490 reviews are resolved by their authors first.
- **Not** merge backward (`feature → develop → staging` only; never staging→develop).
- **Not** force-push anyone's branch without confirmation — the bb#502→bb#490 rebase pushes to bb#502's own branch, not bb#490's.
- **Not** collapse stacked children directly to develop — each parent squashes, carrying its children (per `06-MERGE-ORDER.md`).

## Open decisions for the team

1. **Who resolves pc#778 + bb#490 reviews** (Kuri/Marwan) and by when — gates PR-2.
2. **Per-repo vs per-niche PR**: "4 PRs" is really ~4 *per repo touched* (e.g. PR-1 spans brightbot + platform-core + cdk). Confirm the team wants one PR per (niche × repo), not a literal 4 across all repos.
3. **bb#502 timing**: land in PR-1 now (off BH-531) and accept the later rebase-into-PR-2, OR hold bb#502 until bb#490 lands and rebase first? Plan assumes the former (BH-592 is done + tested; don't block it).
