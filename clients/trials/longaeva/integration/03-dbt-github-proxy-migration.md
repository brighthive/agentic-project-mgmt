---
title: "Niche 3 — DBT GitHub proxy migration (PAT off the agent boundary)"
epic: "BH-529 (children BH-560..567, BH-568)"
prs: ["brighthive-platform-core#781", "brighthive-platform-core#782", "brighthive-platform-core#783", "brightbot#493", "brightbot#494", "brightbot#496"]
last_reviewed: "2026-06-05"
---

# Niche 3 — DBT GitHub proxy migration

> **One-line intent:** finish moving the dbt agent's GitHub work onto the
> Platform Core proxy — harden the proxy responses, type the client side, cover
> it with tests, and close the last place the PAT crosses an agent boundary
> (super_agent).

> The user's framing called this "Migrating DBT OAuth process from brightagent
> to -core." Mechanically it's the **hardening + correctness + test layer** on
> top of [Niche 2's](02-github-enterprise-proxy.md) proxy foundation, plus the
> super_agent PR-creation path. All of these are stacked on the same two
> branches as Niche 2 — they merge as one collapse. Keep both docs open.

## Where these sit in the stack

```
platform-core feat/BH-529-…:   #781 redirect-strip ─┐
                               #782 errorCode      ─┼─ all target #778's branch
                               #783 URL tests+bug  ─┘  (independent of each other)

brightbot BH-529-…:            #493 migration guide ─┐
                               #494 Pydantic + DI   ─┼─ all target #490's branch
                               #496 super_agent path ┘  (#496 depends on #494)
```

## PRs in this niche

### `brighthive-platform-core#781` — disable redirect + scrub Bearer (BH-560) — P0

- **State:** OPEN · draft
- **Why P0:** Node 20 `undici` follows redirects by default and **re-sends the
  `Authorization` header cross-origin**. CNAME-fronted GHE
  (`ghe.example.com → ghe-internal.example.com`) leaks the PAT to the redirect
  target. Separately, misconfigured GHE echoes the `Authorization` header in
  401/422 bodies — forwarding `err.message` raw surfaces the PAT in
  Sentry/CloudWatch.
- **Fix (+33 / −3, 1 file):** `redirect: 'manual'` on the single `fetch`;
  `scrubBearer()` on forwarded error messages.

### `brighthive-platform-core#782` — errorCode + truncated flag (BH-561)

- **State:** OPEN · draft
- **Scope (+139 / −13, 2 files):**
  - `truncated: Boolean` on `ReadGitHubFileOutput` — previously content over
    `MAX_FILE_CONTENT_CHARS` was silently sliced, so the dbt agent committed
    truncated models back to the repo unaware.
  - `errorCode: String` + `httpStatus: Int` on all 7 outputs — previously every
    catch block dropped HTTP status, so the agent couldn't tell 401/403/404/422
    apart to decide retry vs repair.
  - New `mapErrorCode()` — stable ~12-code taxonomy.
- Backwards compatible (nullable fields).

### `brighthive-platform-core#783` — 30 URL-parser tests + real bug fix (BH-567)

- **State:** OPEN · draft
- **Scope (+272 / −53, 3 files):** extracts `parseRepoInfo` into a pure
  `repo-url.ts` module (importing `github-proxy.ts` pulls the whole Neo4j/Apollo
  graph, uninstantiable in a unit test). 30 tests: dotcom + GHE HTTPS/SSH
  variants, case-sensitivity, 8 malformed-URL negatives, determinism.
- **Real bug found:** `https://github.com/org/repo.git/` (trailing slash after
  `.git`) wasn't normalized — `.git` survived. Customers paste this shape.
  Fixed by looping the strip until stable.
- Independent of #780/#781/#782; lands in any order.

### `brightbot#493` — proxy migration guide (BH-565) — docs

- **State:** OPEN · draft
- **Scope (+201 / −0, 1 file):** `docs/BRIGHTBOT-GITHUB-PROXY-GUIDE.md` — the
  guide bb#490's body *claims* exists but didn't ship. Sections: why the proxy
  exists, the 7 mutations, how BrightBot calls them, the 12-code error taxonomy,
  the security boundary, how to add an 8th mutation, what's still on PyGithub.
- Pure docs, zero behavior change.

### `brightbot#494` — Pydantic responses + injectable PlatformClient (BH-564)

- **State:** OPEN · draft
- **Why:** the shipped dbt tools violated two rules — `PlatformAPISession` was
  instantiated inline (testing needed `patch()`, forbidden by
  `testable-code.md`) and proxy responses were untyped dicts.
- **Scope (+638 / −57, 5 files):**
  - `tools/github_proxy_models.py` — 7 frozen Pydantic models matching #782's
    envelope; `ProxyErrorCode` StrEnum; `parse_proxy_response()` with graceful
    fallback
  - `tools/platform_client.py` — `PlatformClient` Protocol + factory; tests
    inject a stub via state, production falls through (no `patch()`)
  - `github_tools.py` — 8 inline sessions + 7 dict accesses replaced;
    `BRANCH_EXISTS` treated as success (idempotent retry)
  - 18 unit tests
- **`#496` depends on this** — #496's tests import these two modules.

### `brightbot#496` — super_agent dbt PR creation via proxy (BH-562 PR1/2)

- **State:** OPEN · draft · **depends on #494**
- **Why:** the BH-529 security headline ("PAT never enters BrightBot") was still
  *false* on this branch because `super_agent/nodes/agents/dbt.py` read
  `state['github_pat']` and instantiated `Github(github_pat)`. This adds the
  alternate proxy path.
- **Scope (+463 / −10, 3 files):** new `dbt_pr_proxy.py` —
  `super_agent_state_has_proxy_creds()` + `invoke_pr_creation_via_proxy()`
  (3-mutation chain: createBranch → commitFiles → createPR, all through the
  injected `PlatformClient`). Legacy PyGithub fallback retained with a
  `DEPRECATED` docstring for customers without `transformation_service_id`.
  6 unit tests including a regression that asserts no PAT-shaped substring in
  any mutation variable.
- **Explicitly NOT in this PR (→ BH-568):** removing `from github import Github`,
  dropping `pygithub` from `pyproject.toml`, removing the `state['github_pat']`
  reads. Those wait until every super_agent customer has
  `transformation_service_id` populated.

## Dependency notes

- **Within brightbot:** #496 → needs #494 (imports its modules). #493 is pure
  docs, lands anytime. All three target #490's branch.
- **Within platform-core:** #781, #782, #783 are mutually independent, all
  target #778's branch.
- **Cross-repo:** same gate as Niche 2 — brightbot side needs platform-core
  side deployed to staging first.

## Staging verification

See [runbook Gate C](00-STAGING-INTEGRATION-RUNBOOK.md#gate-c--dbt-proxy-hardening).
Short form:

1. `mapErrorCode` returns the right code for 401/403/404/422 (unit + a live
   call against a bad repo).
2. `truncated: true` returned when a file exceeds the char cap (commit a >20k
   file, read it back).
3. super_agent dbt run with `transformation_service_id` set creates a PR via the
   proxy; regression: grep agent state + traces for `ghp_`/`github_pat` → none.
4. super_agent run *without* `transformation_service_id` still works via the
   legacy path (backwards-compat until BH-568).

## Out of scope

- BH-568 — full PyGithub removal from super_agent (after all customers have
  `transformation_service_id`).
- Integration tests of the 7 mutations against a mocked GHE (needs `nock`/`msw`).

## References

- Epic: [BH-529](https://brighthiveio.atlassian.net/browse/BH-529); follow-up [BH-568](https://brighthiveio.atlassian.net/browse/BH-568)
- Spec: `agentic-project-mgmt/docs/specs/github-enterprise-host-config.md` §11
