---
title: "GHE end-to-end smoke test — pre-Longaeva validation"
client: longaeva
related_epic: BH-526
related_ticket: BH-529
created: "2026-06-02"
last_reviewed: "2026-06-02"
---

# GHE smoke test plan — pre-Longaeva validation

> **Purpose**: prove the BH-529 GitHub proxy works end-to-end against a real GHE host *before* Longaeva provides their PAT + repo URL. Lets the team validate without trial-day pressure and surfaces edge cases (TLS, PR templates, branch protection) early.

## When this runs

| Phase | Trigger |
|---|---|
| **A — Internal sandbox smoke** | After the 7 P0 tickets (BH-559..565) merge. Before Longaeva is asked for credentials. |
| **B — Longaeva sandbox smoke** | After Grant provisions a sandbox PAT. Before Day 1 of trial. |
| **C — Longaeva production** | Day 3 of trial, joint session with their data team. |

Each phase gates the next.

## What we need

### Phase A — internal GHE sandbox

The team needs a GHE host BrightHive controls, with a populated dbt repo. Options:

- **Option 1 (preferred)**: spin up a `ghe-server-trial` instance via Docker (`ghcr.io/brighthive/ghe-trial:latest` or similar) on a workload AWS account. Free for 45-day trial; sufficient for sandbox.
- **Option 2 (faster)**: use a private GitHub.com org as the "fake GHE" — only verifies the dotcom path, NOT the host-derivation logic. Lower confidence.
- **Option 3 (cheap)**: WireMock fixture replaying recorded GHE responses. Verifies host routing but not real TLS or rate limits.

Recommendation: Phase A1 = Option 3 (in CI), Phase A2 = Option 1 (manual one-shot).

### Phase B — Longaeva GHE sandbox

Longaeva provides:
- GHE host URL (e.g., `https://ghe.longaeva.com`)
- A sandbox dbt repo (read + write + PR scope)
- A scoped PAT (paste once into webapp Settings)
- TLS chain confirmation (public CA vs internal)

## Smoke test scenarios

Each scenario is a Gherkin from spec §4 plus operational sanity checks. All run via the dbt agent in a real workspace, end-to-end through Slack OR the `/v1/agent/run` endpoint.

### S1 — read a file (lightest path)

```
Given a TransformationService with repoUrl = <sandbox repo>
And a valid PAT
When the dbt agent calls github_read_file(file_path="dbt_project.yml")
Then the file content is returned
And no api.github.com calls appear in CloudWatch for that turn
And the gen_ai.tool.github.host span attribute = sandbox host
```

### S2 — list branches + create branch (idempotent)

```
When the dbt agent calls github_list_branches
Then the list contains "main"
When github_create_branch(name="bh/smoke-test-<timestamp>")
Then the branch exists on GHE
When the same call is repeated
Then no error — idempotent (or surfaced as BRANCH_EXISTS errorCode for the LLM to skip)
```

### S3 — commit + open PR (full happy path)

```
When the dbt agent commits a one-line change to README.md on the new branch
And opens a PR with title "BH-XXX smoke test"
Then the PR exists on GHE
And the PR body matches .github/pull_request_template.md if present (BH-566)
And github_pr_number is returned (not pr_url)
And no PAT appears in any CloudWatch log
```

### S4 — error surface (negative path)

```
Given an invalid PAT (revoked or wrong scope)
When github_read_file is called
Then the response has errorCode = TOKEN_REVOKED + httpStatus = 401
And the error message does NOT echo the PAT
```

### S5 — host isolation (the security claim)

```
Given a workspace configured for the GHE sandbox
When any of the 8 dbt agent tools runs
Then CloudWatch log analytics confirms zero requests to api.github.com from this Lambda invocation
And gen_ai.tool.github.host = sandbox host on every span
```

This is the single most important assertion. If S5 fails, BH-529's value proposition is gone — even if all other tests pass.

### S6 — multi-tenant isolation (the BH-559 fix)

```
Given workspace A with TransformationService A on the sandbox
And workspace B with no TransformationService
When a user authenticated as workspace B calls github_read_file with workspaceId=A
Then Platform Core rejects with 403
And no Secrets Manager read is attempted
```

### S7 — redirect handling (the BH-560 fix)

```
Given a sandbox host that redirects to a different hostname
When the dbt agent calls github_read_file
Then the request does NOT follow the redirect with the Authorization header
And errorCode = HOST_MISCONFIGURED
And the error message is admin-actionable (no host echo)
```

### S8 — PR template compliance (the BH-566 fix)

```
Given the sandbox has .github/pull_request_template.md with required JIRA-id field
When the dbt agent opens a PR
Then the PR body includes a JIRA-id field
And the PR is mergeable (not blocked on template compliance)
```

### S9 — TLS / self-signed CA (Longaeva-conditional)

Only runs if Grant confirms internal CA usage.

```
Given a sandbox served via self-signed cert in /opt/ca-bundle.pem
And NODE_EXTRA_CA_CERTS=/opt/ca-bundle.pem (per BH-570)
When github_read_file is called
Then the request succeeds (no UNABLE_TO_VERIFY_LEAF_SIGNATURE)
```

### S10 — rate limit (Longaeva-conditional)

Only runs against Longaeva sandbox if their PAT cap is < 200/hr.

```
Given a PAT capped at 60/hr
When the dbt agent runs commitGitHubFiles 10 times in 5 minutes (50+ API calls)
Then BH-571 backoff kicks in
And no calls fail with a generic 5xx
```

## Pass / fail criteria

Phase gate to next phase requires all of:

| Phase | Required scenarios | Gate |
|---|---|---|
| A1 (CI smoke) | S1, S5, S6 | Run on every PR to platform-core or brightbot |
| A2 (manual sandbox) | S1, S2, S3, S4, S5, S6, S7 | Sign-off before asking Longaeva for creds |
| B (Longaeva sandbox) | All except S10 if PAT cap unknown | Sign-off before Day 1 |
| C (Longaeva prod) | S3 (one PR opened end-to-end) | Trial Day 3 success criterion |

## Owners

- **A1 (CI smoke harness)**: covered by BH-567 (property + integration tests)
- **A2 (manual sandbox + GHE Docker)**: Ahmed
- **B (Longaeva sandbox)**: Kuri (drives the integration on the BrightHive side, Grant provisions creds)
- **C (Longaeva prod)**: joint session — Grant + Kuri

## What to do if a phase fails

| Failure | Response |
|---|---|
| S5 fails (api.github.com leak) | BLOCK trial. Reopen BH-559 / audit github-proxy.ts. The security claim is invalidated. |
| S6 fails (cross-tenant) | BLOCK trial. BH-559 didn't actually fix the bug. Re-review. |
| S7 fails (redirect leak) | BLOCK trial. BH-560 incomplete. |
| S3 PR created but unmergeable | Surface to Grant; either fix BH-566 (template compliance) or get Longaeva to relax sandbox protections |
| S9 TLS fails | Block until BH-570 lands AND CA bundle is in the Lambda layer |
| S10 rate-limit cascade | Soft-fail. Open dialogue with Grant about sandbox PAT caps. |

## Logging / evidence

Every smoke run produces:
- CloudWatch log filter export: `gen_ai.tool.github.execute` spans for the run window
- Output of `aws logs filter-log-events --filter-pattern "api.github.com"` over the run window — must be empty for GHE workspaces
- A markdown report at `clients/trials/longaeva/smoke-tests/{phase}-{date}.md` checking off scenarios

## Status (as of 2026-06-02)

```
[ ] Phase A1 — CI smoke harness        (blocked on BH-567)
[ ] Phase A2 — manual sandbox smoke    (blocked on BH-559..565 merge)
[ ] Phase B — Longaeva sandbox smoke   (blocked on Phase A2 + Grant creds)
[ ] Phase C — Longaeva prod day-3      (blocked on Phase B + trial start)
```
