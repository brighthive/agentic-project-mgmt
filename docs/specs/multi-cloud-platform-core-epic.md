---
title: "Multi-cloud Platform Core — full port epic"
epic: "Nestlé Azure / GCP / dedicated AWS"
status: "In progress"
created: "2026-10-17"
tags: [platform-core, azure, gcp, aws, kubernetes]
related:
  - deployment-profiles-cloud-adapters.md
---

# Multi-cloud Platform Core — full port epic

## Goal

One Platform Core codebase runs on **aws-saas**, **azure-k8s**, and **gcp-k8s** with cloud-specific adapters behind ports — not `#ifdef` SDK calls in resolvers.

## Branch / PR stack (review order)

**Integrated tip (Oct 2026):** `feature/multi-cloud-runtime-complete` on `brighthive-platform-core` contains commits 1–4 below plus Azure K8s deploy. Delivery record: [`docs/delivery/DELIVERY-multi-cloud-runtime-complete.md`](../delivery/DELIVERY-multi-cloud-runtime-complete.md). Narrative docs repo: **`brighthive-multi-cloud-runtime`**.

| # | Branch | Scope | Status |
|---|--------|--------|--------|
| 1 | `feature/multi-cloud-workspace-secrets` | `DEPLOYMENT_PROFILE`, `IWorkspaceSecretStore`, AWS/Azure/GCP workspace JSON | Merged into stack (`5aef2cf0`) |
| 2 | `feature/multi-cloud-saas-capability-guards` | `AwsSaasPlatformCapability`, guards | In stack (`0e9e378e`) |
| 3 | `feature/multi-cloud-platform-secrets` | `IPlatformSecretStore` | In stack (`a8d02f3b`) |
| 4 | `feature/multi-cloud-object-store` | `IObjectStore` presign; single-tenant blob/GCS | In stack (`d07eb331`) |
| 5 | `feature/multi-cloud-runtime-complete` | K8s runtime parity, Helm/Terraform bh-demo, CI, public URL | Active (`4c698b64`) — **not on `develop`** |
| 6 | `feature/multi-cloud-identity-config` | Entra production JWKS (beyond LOCAL_DEV_MODE) | Partial — docs + JIT; Entra app TBD |
| 7 | `feature/multi-cloud-workspace-storage-config` | Replace DynamoDB S3 bucket map for single-tenant | Partial — env/registry ports |
| 8 | `feature/multi-cloud-notifications-dynamo` | Optional Dynamo inbox on K8s | Neo4j default done; Dynamo optional |

Each PR MUST stay under `PR_RULES.md` line limits; split adapters from call-site migration if needed.

## Port inventory (done vs remaining)

| Concern | aws-saas | azure-k8s | gcp-k8s |
|---------|----------|-----------|---------|
| Workspace secrets | SM | Key Vault | Secret Manager (phase 2) |
| Platform secrets (org CDK, etc.) | SM | KV | SM — SaaS-only features stay gated |
| JWT / JWKS | Cognito | Entra via `JWKS_ENDPOINT` | OIDC via `JWKS_ENDPOINT` |
| User admin (Cognito APIs) | Live | Needs identity admin port or disable | Same |
| Object presign (workspace files) | STS + S3 | Blob SAS / GCS signed URL | GCS |
| Account registry (DynamoDB) | Live | Env / config port | Same |
| Redis, Neo4j, GraphQL | Live | Live (bring-your-own endpoints) | Live |
| Webhooks / Lambdas | Lambda | K8s deploy (infra repo) | GKE |

## Invariants

- Workspace JSON shape unchanged across clouds.
- Single-tenant profiles MUST NOT call STS into customer AWS accounts.
- SaaS-only capabilities remain on `aws-saas` only (see `DEPLOYMENT_CAPABILITIES.md`).
