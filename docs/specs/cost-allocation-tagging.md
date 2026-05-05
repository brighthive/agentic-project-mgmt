---
title: "AWS Cost Allocation Tagging"
epic: "BH-171"
author: "Kuri"
status: "Draft"
created: "2026-04-16"
generates: "tickets"
tags: [infrastructure, cost, observability, nestle]
related:
  features: []
  pocs: []
  bedrock: []
---

# AWS Cost Allocation Tagging

## Problem

BrightHive cannot answer "how much does it cost to run one workspace?" with real data. No cost allocation tags exist on AWS resources. Cost Explorer shows total account spend but cannot break down by workspace, organization, service tier, or cost category (ingestion vs. querying vs. hosting vs. AI usage). This blocks enterprise sales (Nestle asked for a volume matrix) and internal margin analysis.

## Use Case / Goal

Any BrightHive engineer or sales lead can pull real per-workspace, per-category cost data from AWS Cost Explorer within 24 hours of the billing period closing. The data feeds a volume matrix that maps data volume tiers to actual infrastructure cost.

## Current Situation

### How It Works Today

Resources are deployed via CDK across 224 AWS accounts. No cost allocation tags are applied. The only cost visibility is per-account totals in AWS Organizations consolidated billing. Shared platform resources (Neo4j, Redis, Lambda, API Gateway) on account `104403016368` are not attributed to any workspace.

### Hard Limitations

- AWS Cost Explorer tags take 24 hours to propagate after activation
- Tags must be activated in the billing console before they appear in Cost Explorer
- Cross-account tag enforcement requires AWS Organizations tag policies
- Retroactive tagging is not possible — only future costs will be tagged

### Gaps

1. No `bh:workspace-id` tag on any resource
2. No `bh:organization-id` tag on any resource
3. No `bh:cost-category` tag (ingestion | querying | hosting | ai-usage)
4. No `bh:environment` tag (prod | staging | dev)
5. No `bh:component` tag (webapp | platform-core | brightbot | admin | org-cdk | workspace-cdk)
6. Shared resources (Neo4j, Redis) have no allocation model
7. LLM token costs (Bedrock, Anthropic API) are not attributed per workspace

## Proposals / Solutions

### Recommended Approach

Add a standard tag set to all CDK stacks via CDK Aspects (automatic tag propagation to all child resources).

**Tag schema**:

| Tag Key | Example Value | Applied By | Required |
|---------|--------------|-----------|----------|
| `bh:workspace-id` | `1c814cd6-c88f-40f6-8c1c-12b75a73758e` | workspace-cdk, org-cdk | Yes |
| `bh:organization-id` | `f16c138a-4d35-41e5-ac2b-191c41127a51` | org-cdk | Yes |
| `bh:environment` | `prod` | All CDK stacks | Yes |
| `bh:component` | `workspace-cdk` | All CDK stacks | Yes |
| `bh:cost-category` | `querying` | Per-resource | Yes |
| `bh:client-name` | `ProdTestWorkspace` | workspace-cdk, org-cdk | Yes |

**Cost category assignment**:

| Resource | Category |
|----------|----------|
| Redshift Serverless | `querying` |
| S3 buckets | `ingestion` |
| Glue jobs + crawlers | `ingestion` |
| Step Functions (ingestion) | `ingestion` |
| Lambda (Redshift APIs) | `querying` |
| Lambda (platform-core) | `hosting` |
| Neo4j EC2 | `hosting` |
| Redis | `hosting` |
| Aurora pgvector | `ai-usage` |
| Bedrock (KB + Code Interpreter) | `ai-usage` |
| API Gateway | `hosting` |
| Amplify | `hosting` |
| Cognito | `hosting` |

**Shared resource allocation**: Neo4j and Redis are single-instance shared. Allocate proportionally by workspace count (simple) or by API call volume per workspace from CloudWatch metrics (accurate).

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| Per-account billing only | Zero work | Can't break down shared platform costs or by category | Doesn't answer the question |
| Third-party cost tool (Kubecost, Vantage) | Richer UI | Additional vendor, cost, integration | Overkill for current scale |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Workspace CDK | `brighthive-data-workspace-cdk` | Add CDK Aspect for tagging all 9 stacks |
| Organization CDK | `brighthive-data-organization-cdk` | Add CDK Aspect for tagging all 7 stacks |
| Admin | `brighthive-admin` | Add tags to platform-level stacks |
| Platform Core | `brighthive-platform-core` | Add tags to CDK stacks in `brighthive_core/` |
| AWS Organizations | Console / CLI | Activate cost allocation tags, create tag policy |

## Acceptance Criteria

- [ ] All resources in workspace-cdk and org-cdk have all 6 tags applied
- [ ] Cost allocation tags activated in AWS billing console (PROD + STAGE)
- [ ] AWS Organizations tag policy enforces required tags on new resources
- [ ] Cost Explorer query by `bh:cost-category` returns data within 48 hours of deployment
- [ ] Cost Explorer query by `bh:workspace-id` returns per-workspace costs
- [ ] Shared platform resources tagged with `bh:cost-category` and allocated via documented model

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| AWS Organizations tag policy access | Blocking | Requires MAIN account admin |
| Cost Explorer activation | Blocking | Requires billing console access |
| CDK deploy to all 169 org + 49 workspace accounts | Non-blocking | Rolls out incrementally via CodeBuild |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| -- | Add CDK Aspect for cost tags to workspace-cdk | 3 | BH-171 |
| -- | Add CDK Aspect for cost tags to org-cdk | 3 | BH-171 |
| -- | Add tags to platform-core CDK stacks | 2 | BH-171 |
| -- | Add tags to brighthive-admin CDK stacks | 2 | BH-171 |
| -- | Activate cost allocation tags in billing console (PROD + STAGE) | 1 | BH-171 |
| -- | Create AWS Organizations tag policy for required tags | 2 | BH-171 |
| -- | Document shared resource allocation model | 1 | BH-171 |
