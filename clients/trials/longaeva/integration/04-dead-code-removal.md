---
title: "Niche 4 — Dead PyGithub code removal"
epic: "BH-529 (child BH-562 PR2/2)"
prs: ["brightbot#495"]
last_reviewed: "2026-06-05"
---

# Niche 4 — Dead PyGithub code removal

> **One-line intent:** delete the unused PyGithub modules so the BH-529 security
> headline ("PyGithub never enters BrightBot") is *literally true* for the dead
> surface, with a regression test that stops them coming back.

## Why this niche exists

BH-529's whole point is getting GitHub PATs off the BrightBot agent. Part of
that is removing the legacy PAT-shaped code surface. An audit found four modules
with **zero callers** — ~1,264 lines of dead PyGithub code that can go in one
move. This is the cleanup half of BH-562 (the active-path half is bb#496 in
[Niche 3](03-dbt-github-proxy-migration.md)).

## The PR

### `brightbot#495` — delete 4 dead PyGithub modules (BH-562 PR2/2)

- **State:** OPEN · draft · base = `BH-529-…` (stacked on #490)
- **Scope (+37 / −1264, 5 files):**

  | Deleted file | Lines | Why dead |
  |---|---|---|
  | `brightbot/agents/dbt_agent/utils.py` | 488 | `_parse_github_url`, `get_models_list` only called within the same file; nothing else imports it |
  | `brightbot/tools/github_file_commiter.py` | 325 | Zero callers anywhere |
  | `brightbot/tools/github_operations.py` | 344 | Only imported by `github_llm_tool.py` (also dead) |
  | `brightbot/tools/github_llm_tool.py` | 107 | Zero callers anywhere |

  The chain `github_llm_tool → github_operations → github_file_commiter` is
  fully dead. Verified with:
  ```bash
  grep -rn 'github_llm_tool\|github_file_commiter\|github_operations.*GitHubTool\|dbt_agent\.utils' \
    brightbot/ tests/ --include='*.py'
  # (no results except the modules themselves)
  ```
- **Backstop:** `tests/unit/tools/test_no_dead_pygithub_modules.py` fails loudly
  if any of the 4 modules are reintroduced — forces a conversation about whether
  the proxy can serve the use case instead.
- Net negative diff — the cleanest kind of change.

## Important scope boundary (what this does NOT do)

These stay, deliberately, because they're still on the **live** path and belong
to BH-568:

- `super_agent/nodes/agents/dbt.py` still imports PyGithub (the legacy fallback
  — see bb#496 for the new path beside it).
- `brightbot/tools/github_tools.py` (1300+ legacy lines) still imported by
  super_agent + `super_agent/dbt_github_utils.py`.
- Removing `pygithub>=2.3.0` from `pyproject.toml` — **blocked** on the
  super_agent migration above.
- The full `import github raises ModuleNotFoundError` regression test — same
  blocker.

> So: after #495, PyGithub is still installed and still imported by super_agent.
> "PyGithub gone from BrightBot" is **not** true yet — it's true only for these
> 4 dead modules. Don't claim the dependency is removed in the trial readout.

## Dependency notes

- Stacked on #490's branch — collapses cleanly with the other BH-529 follow-ups
  (#492, #493, #494, #496).
- The 32 other unit-test failures on this branch are **pre-existing** on the
  parent branch (`feat/BH-529-…`), unrelated to the deletion (verified by the PR
  author).

## Staging verification

This is a deletion of unreferenced code — staging behavior should be
**unchanged**. Verification is a no-regression check, covered in
[runbook Gate C step 5](00-STAGING-INTEGRATION-RUNBOOK.md#gate-c--dbt-proxy-hardening):

1. After merge, the dbt agent and super_agent still start and run (imports
   resolve).
2. `test_no_dead_pygithub_modules.py` is green in CI.

## References

- Ticket: [BH-562](https://brighthiveio.atlassian.net/browse/BH-562) (PR2/2); follow-up [BH-568](https://brighthiveio.atlassian.net/browse/BH-568)
- Spec: `agentic-project-mgmt/docs/specs/github-enterprise-host-config.md` §11 findings #1–4
