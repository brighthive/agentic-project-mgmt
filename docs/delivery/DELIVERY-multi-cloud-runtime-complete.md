---
title: "Delivery record — multi-cloud runtime complete (Azure bh-demo)"
status: "In progress — not merged to develop"
updated: "2026-10-23"
owner: "Platform Core"
repos:
  - brighthive-platform-core
  - brighthive-multi-cloud-runtime (documentation)
branch: "feature/multi-cloud-runtime-complete"
---

# Delivery record — `feature/multi-cloud-runtime-complete`

Canonical **narrative + runbooks** live in the documentation repo:

**[brighthive-multi-cloud-runtime](https://github.com/brighthive/brighthive-multi-cloud-runtime)** (create/push if not yet on GitHub — see that repo’s README).

Epic spec: [`docs/specs/multi-cloud-platform-core-epic.md`](../specs/multi-cloud-platform-core-epic.md).

## Summary

Platform Core runs on **`DEPLOYMENT_PROFILE=azure-k8s`** in subscription **Brighthive-basic**, resource group **`bh-demo`**, with GraphQL on AKS, Neo4j/Redis in-cluster, Key Vault + Blob for workspace secrets and uploads, and a **public HTTP URL** (Azure `cloudapp.azure.com`, port 8080). Work is **stacked on one branch**; older `feature/multi-cloud-*` branch names are **tags on the same commit line**, not parallel codebases.

## Branch stack (all contained in `runtime-complete`)

| Order | Branch | Commit (tip) | What it added |
|------|--------|--------------|---------------|
| 1 | `feature/multi-cloud-workspace-secrets` | `5aef2cf0` | Deployment profiles, workspace secret store port + Azure/GCP/AWS adapters |
| 2 | `feature/multi-cloud-saas-capability-guards` | `0e9e378e` | `AwsSaasPlatformCapability` guards |
| 3 | `feature/multi-cloud-platform-secrets` | `a8d02f3b` | `IPlatformSecretStore` |
| 4 | `feature/multi-cloud-object-store` | `d07eb331` | Single-tenant object store / presign |
| 5 | *(runtime-complete only)* | `a9791cee` | Object storage + identity gate completion |
| 6 | *(runtime-complete only)* | `4c698b64` | Azure Terraform, Helm, AKS deploy, GitHub Actions |

**No unique commits** exist on branches 1–4 that are missing from `runtime-complete`.

## Implemented in platform-core (high level)

| Area | Location / notes |
|------|------------------|
| Profile + capabilities | `src/platform/deployment-profile.ts`, `deployment-capabilities.ts`, `docs/platform/DEPLOYMENT_CAPABILITIES.md` |
| Workspace KV | `azure-key-vault-workspace-secret-store.ts`, factory |
| Notifications (K8s) | Neo4j inbox/signal stores, optional Dynamo via flag |
| Entra JIT | `currentUser` + `SINGLE_TENANT_*` env |
| DBT on K8s | `dbt-validation-orchestrator.ts` (no Step Functions) |
| Azure infra | `deploy/azure/terraform/` — KV, storage, AKS, ACR, static IP, Front Door |
| K8s packaging | `deploy/k8s/helm/brighthive-platform/` |
| Local / ops scripts | `scripts/deploy-azure-lightweight.ps1`, `scripts/ci-azure-k8s-deploy.sh` |
| CI | `.github/workflows/deploy-azure-k8s.yml` → environment `azure-bh-demo` |

## Live Azure (bh-demo) — 2026-10-23

| Resource | Name / URL |
|----------|------------|
| AKS | `bhplat-aks-mj2te2` |
| ACR | `bhplatacrmj2te2.azurecr.io` |
| Key Vault | `bhplatkvmj2te2` |
| Storage | `bhplatstmj2te2` |
| Public GraphQL (HTTP) | `http://bhplatcoremj2te2.westus2.cloudapp.azure.com:8080/graphql` |
| Public health | `http://bhplatcoremj2te2.westus2.cloudapp.azure.com:8080/health` |
| HTTPS (Front Door) | `https://bhplat-core-mj2te2-e7amd7a7fkc6fqhv.z03.azurefd.net/` — verify origin health before relying on it |

Auth for smoke: **`LOCAL_DEV_MODE=true`** until **`JWKS_ENDPOINT`** (Entra) is configured in Helm env.

## CI status

- Workflow triggers on **`feature/multi-cloud-runtime-complete`** push and `workflow_dispatch`.
- Requires GitHub environment **`azure-bh-demo`** + Azure OIDC secrets — see `brighthive-platform-core/deploy/azure/CI.md`.
- **Not** triggered by the four older multi-cloud branch names.

## Explicitly not done / not AWS parity

See `DEPLOYMENT_CAPABILITIES.md`: managed Redshift/Snowflake, cross-account STS, org CDK secrets, Cognito admin on K8s, DynamoDB platform accounts, Airbyte org creds, OpenMetadata **service** on Azure (webhook **images** exist; OM URLs still placeholders in lightweight env), custom domain `api.*.brighthive.net`, production Entra.

## Recommended next steps

1. Configure **`azure-bh-demo`** secrets and confirm green CI deploy with image tag `ci-<sha>`.
2. Entra app + **`JWKS_ENDPOINT`**; disable `LOCAL_DEV_MODE` for external testers.
3. Single PR **`feature/multi-cloud-runtime-complete` → `develop`** (or split per `PR_RULES.md` if diff too large).
4. Optional: deploy OpenMetadata on Azure and enable `-RuntimeProfile K8sRuntime` OM sidecars.

## Related specs

- [`SPEC-multi-cloud-phase-3-runtime.md`](../../brighthive-platform-core/docs/specs/SPEC-multi-cloud-phase-3-runtime.md) (in platform-core repo)
- [`multi-cloud-platform-core-epic.md`](../specs/multi-cloud-platform-core-epic.md)
