---
title: "Okta SSO + Cognito Federation + MFA2 (BH-674 / BH-675 / BH-676 / MFA2)"
epic: "BH-115"
author: "Kuri"
status: "In Progress"
created: "2026-06-22"
generates: "tickets"
tags: ["auth", "sso", "cognito", "okta", "mfa", "saas"]
related:
  features: []
  pocs: []
  bedrock: []
---

# Okta SSO + Cognito Federation + MFA2

## Problem

Federated SSO users (Okta → Cognito) authenticate successfully and receive a
valid Cognito JWT, but every BrightHive backend surface returns FORBIDDEN at
`currentUser`. Reason: every Platform Core and MCP surface resolves the caller
by `token.sub → Neo4j UserNode keyed by id`. Native (password) users get a
`UserNode` via `AdminCreateUser → create_user_neo4j_lambda` in
`brighthive-admin`. Federated users have a brand-new Cognito `sub` with no
`UserNode` and no path to create one.

The unblock-by-Cypher used during BH-575 dogfood is not productizable — it
requires Matt to manually `MATCH/CREATE` Neo4j nodes per user.

In parallel: enterprise customers expect MFA on the platform pool. Today
the pool has `MfaConfiguration: OFF` (Cognito default). V1 ships SMS only
(lowest-friction for the BrightHive CDO buyer persona); TOTP is V2 with a
placeholder spec already landed.

## Use Case / Goal

End state — verified by the captured Okta URL flowing end-to-end:

```
auth.staging.brighthive.net/oauth2/authorize?identity_provider=TrialOktaBH&...
  → Okta authentication
  → Cognito JWT with custom:workspace_id
  → webapp /auth/callback exchanges code via PKCE
  → currentUser query lands UserNode in Neo4j (JIT)
  → user lands in their workspace
```

Plus: SMS MFA (V1) available opt-in for any user who wants it on the platform pool. TOTP follows in V2.

## Current Situation

### How It Works Today

Direct AWS CLI inspection on 2026-06-22 (`aws cognito-idp ...`):

| Component | State |
|---|---|
| Pool `us-east-1_EAYUbZPFk` | Live; 3 clients |
| Client `7upotcb3b8nlljeahr6olfien7` (`staging-mcp-public-client`) | OAuth flows OFF; no IdPs |
| Client `3jd64bf11u3cf9vg095d01vcjn` (platform pool, password login) | OAuth flows ON (`code`, `implicit`); only `COGNITO` in `SupportedIdentityProviders`; callback URL is placeholder `https://example.com` |
| Client `2ombp747a1ejlsu5bbdqvvhvpi` (M2M) | n/a (client_credentials only) |
| Federated IdP `TrialOktaBH` | Attached to pool via `brighthive-okta-idp-cdk` (BH-676 ✅) |
| Pre-token-gen Lambda | Attached; writes `custom:workspace_id` from federated claim |
| MFA on platform pool | OFF |
| `currentUser` resolver | FORBIDDEN for federated users without `UserNode` |

### Hard Limitations

- Cognito CFN dynamic refs reject `ssm-secure` for `UserPoolIdentityProvider.ProviderDetails.client_secret` — must use Secrets Manager (BH-676 already pivoted).
- Cognito Lambda triggers have a 5s budget; would force compromises on the JIT path if we put it there.
- Cognito `update-user-pool-client` REPLACES every list it touches (not merge) — operator must read-modify-write the full set.
- Federated Cognito tokens skip Cognito-side MFA challenges by design; the IdP owns MFA on its side.

### Gaps

| Gap | Impact | Fix |
|---|---|---|
| Webapp client (`3jd64...`) has no `TrialOktaBH` in `SupportedIdentityProviders` | Authorize URL rejects `identity_provider=TrialOktaBH` before reaching Okta | Sherbiny CDK PR + `aws cognito-idp update-user-pool-client` |
| Webapp client has placeholder callback `https://example.com` | Token exchange has nowhere to land | Sherbiny CDK PR (add real webapp + localhost callbacks) |
| MCP public client (`7upot...`) has OAuth flows OFF | All federated logins via this client return `unauthorized_client` | Either enable flows OR keep this client MCP-only and route webapp via `3jd64...` |
| Federated user has no `UserNode` after Cognito JWT issuance | `currentUser` returns FORBIDDEN | BH-674 resolver-side JIT (PR `platform-core#910` ready) |
| `UserNode.emailAddress` unique constraint blocks email-shared accounts | Every BrightHive engineer with a password account hits a hard collision when first dogfooding Okta | `cognito_sub_aliases: [String!]` schema field on `UserNode` (GA blocker) |
| Webapp has no "Log in with Okta" button or `/auth/callback` route | Customer can't initiate SSO from the product | BH-675 (PR `webapp#1207` ready) |
| Cognito sign-up/sign-in error page is the default Cognito one | Enterprise SSO needs branded copy | Cognito Hosted-UI customization (GA blocker) |
| Pool has no MFA configured | Enterprise expectation gap | MFA2 spec (PR `platform-core#911`, Sherbiny-gated) |
| Resolver trusts `custom:workspace_id` from IdP claim verbatim | Malicious customer Okta admin could grant their users access to another customer's workspace by claiming that workspace's UUID | `WorkspaceNode.allowedFederatedIdps` allow-list (BH-674 P0, ✅ included in PR `platform-core#910`) |

## Proposals / Solutions

### BH-676 — Per-customer IdP CDK (✅ Landed on staging)

`brighthive-okta-idp-cdk` repo. One PR per customer onboarding. Per-IdP
`enabled: bool` flag lets a customer be staged in config without going live.
TrialOktaBH adopted via `cdk import` with zero downtime.

### BH-674 — Resolver-side federated Neo4j JIT provisioning

PR `platform-core#910`, ready for review.

When `currentUser` is called by a federated user (token has `identities`
claim) and no `UserNode` exists, the resolver creates the `UserNode` (and the
`IS_A → WorkspaceAdminNode` edge if `custom:workspace_id` is present) inline.

Feature-flagged behind `FEATURE_FEDERATED_JIT_PROVISIONING` env var (default
`False` per env). Self-healing on every call covers transient edge failures
and the pre-existing federated cohort.

Rejected alternative: PostConfirmation Lambda in `brighthive-admin` (the
original v1/v2 design, closed as `brighthive-admin#90`). Multi-agent review
collapsed it to a resolver branch — one repo, ~30 LOC, no cross-stack
SSM-ARN-publishing dance, no Cognito 5s budget concern.

P0 fix included: `WorkspaceNode.allowedFederatedIdps: [String!]` allow-list
guards against IdP claim spoofing for cross-tenant workspace access.

### BH-675 — Webapp "Log in with Okta" + `/auth/callback`

PR `webapp#1207`, ready for review.

Config-driven: `VITE_SSO_PROVIDERS` env var (JSON array). Empty/unset =
existing password-only login UI byte-identical. Callback handler does PKCE
token exchange, stores tokens in same `localStorage` keys as password login.

### MFA2 V1 — Staging pool SMS

PR `platform-core#911`, Sherbiny-gated draft.

Two-line CDK delta on `user_pool_stack.py`: `mfa=cognito.Mfa.OPTIONAL` +
`MfaSecondFactor(sms=True, otp=False)`. Opt-in; native users only (federated
inherit IdP's MFA). Reversible. Spec at `SPEC-MFA2-staging-pool.md`.

### MFA2 V2 — TOTP alongside SMS (placeholder)

Placeholder spec at `SPEC-MFA2-V2-TOTP.md`. One-line delta from V1:
`MfaSecondFactor(sms=True, otp=True)`. Adds TOTP without removing SMS so
users pick. Open questions captured in the spec (recovery codes, default
factor, deprecating SMS for TOTP-enrolled users).

### Single Sherbiny-gated unblock for end-to-end staging

```bash
aws cognito-idp update-user-pool-client \
  --user-pool-id us-east-1_EAYUbZPFk \
  --client-id 3jd64bf11u3cf9vg095d01vcjn \
  --supported-identity-providers COGNITO TrialOktaBH \
  --callback-urls 'https://example.com' \
                  'http://localhost:7420/auth/callback' \
                  'https://app.staging.brighthive.io/auth/callback' \
  --allowed-o-auth-flows-user-pool-client \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes openid email profile \
  --explicit-auth-flows ALLOW_ADMIN_USER_PASSWORD_AUTH \
                       ALLOW_REFRESH_TOKEN_AUTH \
                       ALLOW_USER_PASSWORD_AUTH \
  --profile brighthive-staging
```

CDK equivalent in `brighthive-platform-core/brighthive_core/user_pool_stack.py`.
Reversible.

## Areas of BrightHive Affected

| Repo | What changes |
|---|---|
| `brighthive-okta-idp-cdk` | Per-customer IdP attached to pool (✅ landed) |
| `brighthive-platform-core` | Pool config (Sherbiny CDK PR), resolver JIT branch + workspace allow-list (BH-674), MFA2 pool flip (`platform-core#911`), env-var wiring (per-env config) |
| `brighthive-webapp` | Login button + callback route + PKCE (BH-675) |
| `brighthive-admin` | Doc-only update — federated users no longer routed through this repo (BH-674 supersedes the original Lambda-trigger design) |
| `brightbot` | Doc-only update — MCP token validator is unchanged; the gap closes upstream in `currentUser` |
| `brighthive-docs` | Customer-facing Okta admin guide already published (`platform/mcp-okta-setup.mdx`) |
| `platform-saas-ai-context` | This spec + `docs/architecture/AUTH_ARCHITECTURE.md` + ADR-005, ADR-006 (PR `#22`) |

## Tickets

| Ticket | Scope | PR | Status |
|---|---|---|---|
| BH-115 | Epic: Interconnect-ability A2A | — | In progress |
| BH-573 | Pre-token-gen Lambda V2_0 | merged | ✅ Shipped |
| BH-575 | Per-customer Okta onboarding runbook | merged | ✅ Shipped |
| BH-676 | `brighthive-okta-idp-cdk` codification of TrialOktaBH | `okta-idp-cdk#1` | ✅ Landed on staging |
| BH-674 | Resolver-side federated Neo4j JIT | `platform-core#910` | Ready for review |
| BH-675 | Webapp "Log in with Okta" button | `webapp#1207` | Ready for review |
| MFA2 V1 | Staging pool SMS | `platform-core#911` | Sherbiny-gated draft |
| MFA2 V2 | TOTP alongside SMS | placeholder spec landed | Not started |
| GA-1 | `cognito_sub_aliases` UserNode field for email-collision merging | — | Not started |
| GA-2 | Branded Cognito error page (Hosted-UI customization) | — | Not started |
| GA-3 | Per-workspace SSO toggle (`WorkspaceNode.ssoEnabled`) | — | Not started |
| Pre-flight | Verify `UserNode.emailAddress` UNIQUENESS constraint exists in Neo4j (Matt) | — | Pending |

## References

- `platform-saas-ai-context/docs/architecture/AUTH_ARCHITECTURE.md` — system-of-record
- `platform-saas-ai-context/docs/decisions/decisions.md` ADR-005, ADR-006
- `brighthive-platform-core/docs/architecture/SSO_ARCHITECTURE.md` — engineer-internal diagrams
- `brighthive-platform-core/docs/architecture/SSO_ENV_VARS.md` — multi-env env-var matrix
- `brighthive-platform-core/docs/local-dev/OKTA_LOCAL_TEST.md` — local E2E test runbook
- `brighthive-platform-core/docs/MCP_OKTA_ONBOARDING_RUNBOOK.md` — per-customer ops runbook
- `brighthive-platform-core/docs/specs/SPEC-BH-674-currentuser-federated-provisioning.md` — implementation spec
- `brighthive-platform-core/docs/specs/SPEC-MFA2-staging-pool.md` — MFA2 V1 spec (SMS)
- `brighthive-platform-core/docs/specs/SPEC-MFA2-V2-TOTP.md` — MFA2 V2 placeholder (TOTP)
- `brighthive-okta-idp-cdk/docs/specs/SPEC-BH-676-deploy-staging.md` — IdP CDK spec
- `brighthive-webapp/docs/specs/okta-sso-login.md` — webapp spec
- `brightbot/docs/OKTA_AUTH.md` — MCP token-validation reference
