---
title: "Niche 5 — MCP server + Okta identity federation"
epic: "BH-115 (children BH-572/573/574/575/588/589)"
prs: ["brightbot#497", "brighthive-platform-core#784", "brighthive-platform-core#788", "brighthive-platform-core#789", "brighthive-platform-core#790", "brighthive-webapp#1132", "brightbot#501"]
last_reviewed: "2026-06-05"
---

# Niche 5 — MCP server + Okta identity federation

> **One-line intent:** give third-party clients (Claude.ai, Cursor, Claude Code,
> enterprise A2S callers) a stable, authenticated MCP endpoint
> (`mcp.brighthive.io`) that federates each customer's own Okta into BrightHive's
> Cognito — so Longaeva users sign in with their Okta and reach their workspace
> data through Claude.

## The two-layer auth model (read this first)

```
┌───────────────────────────── Layer 1 — TENANT ─────────────────────────────┐
│ Cognito Hosted UI (auth.brighthive.io) federated to per-customer Okta        │
│ (SAML/OIDC). Pre-token-gen Lambda maps  Okta.org → Cognito custom:workspace_id│
│   PRs: pc#784 (Cognito clients + Lambda), pc#790 (DNS for auth.*), pc#788    │
│        (per-customer onboarding runbook)                                      │
└───────────────────────────────────────────────────────────────────────────┘
                                   │  issues bearer JWT
                                   ▼
┌───────────────────────────── Layer 2 — USER ───────────────────────────────┐
│ brightbot MCP server (mcp.brighthive.io/mcp) validates the JWT on EVERY      │
│ /mcp/* call via Platform Core currentUser. Principal in a contextvar; tools  │
│ read workspace_id from there, never from arguments.                          │
│   PR: bb#497 (MERGED ✅)                                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

**The pieces compose end-to-end only once Layer 1 (pc#784) + DNS (pc#790) are
deployed.** Until then, bb#497's server returns 401s pointing at an
authorization server / hostname that doesn't exist yet.

## PRs in this niche

### `brightbot#497` — remote MCP server, Layer-2 user auth (BH-572) — **MERGED** ✅

- **State:** **MERGED 2026-06-03**. The only landed PR in this whole bundle.
- **Scope (+2889 / −1716, 17 files):** FastMCP server at `brightbot/mcp/`
  mounted at `/mcp` on the brightbot FastAPI app.
  - `auth.py` — `MCPAuthMiddleware` + `MCPPrincipal` + contextvar
  - `metadata.py` — RFC 9728 `/.well-known/oauth-protected-resource`
  - `server.py` — FastMCP instance + tool registry
  - `tools/ping.py`, `tools/list_workspaces.py`, `tools/invoke_analyst.py` (stub)
  - `http/app.py` — wires lifespan, middleware, well-known router, mounts `/mcp`
  - adds `fastmcp>=2.0.0`
- **Tests:** unit tests for the middleware branches and the two-JWT integration
  test were marked **follow-up** — not in the merged PR. Worth confirming they
  landed since.
- **Note:** lives in brightbot for now; portable to brightagent-v3 later (no
  LangGraph coupling).

### `brighthive-platform-core#784` — Cognito MCP clients + Okta federation hook (BH-573)

- **State:** OPEN · draft · `REVIEW_REQUIRED` · base = `develop`
- **Scope (+1237 / −3, 6 files):**
  - `user_pool_stack.py` — `mcp_resource_server` with 4 scopes (`mcp:read`,
    `mcp:write`, `warehouse:read`, `agents:invoke`); `mcp-public-client`
    (auth_code + PKCE) for human clients; `mcp-m2m-client` (client_credentials)
    for A2S; `workspace_id` custom attribute on the user pool
  - `cognito_lambda_triggers/pre_token_generation.py` — maps federated IdP claim
    → `custom:workspace_id`, config-driven via `FEDERATED_CLAIM_KEYS_JSON` (new
    Okta tenant = no code change); manual attribute beats federated
  - 9 unit tests
- **This is the keystone of Layer 1.** #788/#789/#790 all stack on it.
- Custom-domain attachment is a gated NOTE block here, flipped on by #790.

### `brighthive-platform-core#790` — CDK DNS stack for auth./mcp. domains (BH-574)

- **State:** OPEN · draft · base = `…/BH-573` (stacked on #784)
- **Scope (+471 / −13, 5 files):** `dns_stack.py` (`McpDnsStack`) — Route 53
  hosted zones for `auth.{env}.brighthive.io` + `mcp.{env}.brighthive.io`, one
  multi-SAN ACM cert in `us-east-1`. Flips #784's gated block to actually attach
  the Cognito Hosted UI custom domain.
- **Architecture decision (drchinca 2026-06-04):** `brighthive.io` apex is on
  **Cloudflare** (not AWS). Chosen path: **delegate `auth.*` / `mcp.*` sub-zones
  to Route 53** (apex untouched, CDK owns platform subdomains, ACM auto-validates).
  Requires a one-time Cloudflare NS-record edit per env per subdomain — covered
  in the deployment runbook.
- prod uses apex (`auth.brighthive.io`); other envs prefix (`auth.dev.…`).
- Adds `docs/MCP_DNS_DEPLOYMENT_RUNBOOK.md`. 6 unit tests.

### `brighthive-platform-core#788` — per-customer Okta onboarding runbook (BH-575) — docs

- **State:** OPEN · draft · base = `…/BH-573`
- **Scope (+342 / −0, 1 file):** `docs/MCP_OKTA_ONBOARDING_RUNBOOK.md` —
  five-phase operator runbook for adding one customer's Okta (or any OIDC/SAML)
  tenant as a Cognito federated IdP. #784 ships the factory + claim map; this
  tells ops the per-customer sequence.

### `brighthive-platform-core#789` — DCR mutation SPEC (BH-588) — docs/spec

- **State:** OPEN · draft · base = `…/BH-573`
- **Scope (+343 / −0, 1 file):** `docs/SPEC-MCP-DCR-MUTATION.md` — SDD spec for
  the RFC 7591 Dynamic Client Registration mutation (`registerMcpClient` +
  `/dcr` REST shim) so MCP clients self-register instead of one CDK PR per
  integration. Spec only — implementation is a later PR gated on §4 Gherkin +
  §7 property tests + multi-agent review.

### `brighthive-webapp#1132` — MCP integration UI SPEC (BH-589) — docs/spec

- **State:** OPEN · draft · `REVIEW_REQUIRED` · base = `develop`
- **Scope (+437 / −5, 3 files):** `docs/specs/mcp-integration.md` — SDD spec for
  an "AI / MCP Clients" section in Workspace Settings → Integrations. Lets a
  member self-connect Claude.ai / Cursor / Claude Code (and revoke) without a
  ticket. Includes a new platform-core query `mcpWorkspaceState` (to be filed as
  BH-590). Spec only; three open questions for reviewers in §10.

### `brightbot#501` — cross-link MCP docs across repos (BH-115) — docs

- **State:** OPEN · draft · base = `develop`
- **Scope (+47 / −12, 2 files):** makes `brightbot/docs/OKTA_AUTH.md` the
  canonical index — refreshes the rollout-status block to name #784/#788/#790,
  adds a "Where things live" table pointing at every MCP doc/spec/source across
  the four repos, de-dupes the Layer-1 procedure into pointers.

## Dependency notes

- **Merge order within platform-core:** #784 first (keystone), then #788, #789,
  #790 (all stacked on it; #790 must land for the custom domain to attach).
- **bb#497 is already merged** but is **non-functional end-to-end** until #784 +
  #790 deploy — it validates JWTs that nothing can issue yet.
- **wa#1132 and pc#789** are specs — they can merge now; their *implementations*
  are separate future PRs and are **not part of this integration test**.
- **bb#501** is docs — merge anytime.

## Staging verification

See [runbook Gate D](00-STAGING-INTEGRATION-RUNBOOK.md#gate-d--mcp--okta-federation).
Short form (functional pieces only — specs excluded):

1. pc#784 deployed: Cognito resource server + 4 scopes + 2 app clients exist;
   pre-token-gen Lambda maps a federated Okta `org` claim → `custom:workspace_id`
   (the 9 unit tests cover the logic; confirm in a staging token).
2. pc#790 deployed: `auth.staging.brighthive.io` + `mcp.staging.brighthive.io`
   resolve (after the Cloudflare NS delegation), ACM cert valid, Cognito custom
   domain attached.
3. End-to-end: an MCP client hits `mcp.staging.brighthive.io/.well-known/…` →
   200; an unauthenticated `tools/list` → 401 with a `WWW-Authenticate` pointing
   at the real `auth.staging…` issuer; an authenticated `ping` returns the
   principal's `workspace_id`.
4. Two-tenant isolation: same tool, two JWTs from two workspaces → workspace-
   scoped results differ.

## Out of scope for the trial

- DCR implementation (pc#789 is spec only).
- Webapp MCP UI implementation (wa#1132 is spec only) + its backend query
  (BH-590).
- Wiring `invoke_analyst` to the real LangGraph SDK runner.

## References

- Epic: [BH-115](https://brighthiveio.atlassian.net/browse/BH-115)
- DevOps plan: `brighthive-platform-core/docs/MCP_DOMAINS_DEVOPS_PLAN.md`
- Canonical doc index: `brightbot/docs/OKTA_AUTH.md` (after bb#501)
- Customer-facing MCP consume guide: `brightbot/docs/MCP_CONSUME.md`
