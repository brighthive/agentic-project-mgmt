---
title: "Usage Metering Pipeline"
epic: "BH-171"
author: "Kuri"
status: "Draft"
created: "2026-04-16"
generates: "tickets"
tags: [infrastructure, cost, metering, observability, nestle]
related:
  features: []
  pocs: []
  bedrock: []
---

# Usage Metering Pipeline

## Problem

BrightHive has usage data scattered across 6+ systems with no aggregation. `LangsmithTokenUsage` and `AgentBasedUsageData` DynamoDB tables collect AI metrics but are never exported or joined with AWS cost data. CloudWatch has Lambda invocation counts, Redshift RPU-seconds, Glue DPU-hours — none of it flows into a single place. Without metering, we cannot build a real volume matrix or per-workspace cost model.

## Use Case / Goal

A nightly pipeline that collects usage metrics from all sources and writes them to a single DynamoDB table (or S3 dataset). Any engineer can query: "For workspace X in March 2026, how many Redshift RPU-seconds, Glue DPU-hours, Lambda invocations, S3 GB stored, LLM tokens consumed, and agent sessions were used?" This data, joined with Cost Explorer costs, produces the real volume matrix.

## Current Situation

### How It Works Today

| Data Source | Where It Lives | Exported? |
|-------------|---------------|-----------|
| LLM token usage | DynamoDB `LangsmithTokenUsage` | No |
| Agent session usage | DynamoDB `AgentBasedUsageData` | No |
| Redshift RPU-seconds | CloudWatch `redshift-serverless` namespace | No |
| Glue DPU-hours | CloudWatch `Glue` namespace | No |
| Lambda invocations | CloudWatch `Lambda` namespace | No |
| S3 storage size | S3 Storage Lens or CloudWatch `S3` namespace | No |
| Step Functions executions | CloudWatch `States` namespace | No |
| Bedrock token usage | CloudWatch `Bedrock` namespace + model invocation logs | No |
| AWS Cost Explorer | Billing API | No export configured |

### Hard Limitations

- CloudWatch metrics retention: 15 months at 1-hour resolution, 63 days at 1-minute
- Cost Explorer API: 12 months of history, max 1 request/second
- Cross-account CloudWatch requires per-account API calls or CloudWatch cross-account observability setup
- Bedrock model invocation logging must be explicitly enabled per account

### Gaps

1. No aggregation pipeline exists
2. No per-workspace usage rollup
3. No join between usage metrics and dollar costs
4. Bedrock invocation logging not enabled in workspace accounts
5. No historical baseline — once we start collecting, oldest data is whatever CloudWatch still has

## Proposals / Solutions

### Recommended Approach

**EventBridge Scheduler + Lambda pipeline** running nightly in each platform account (PROD, STAGE).

```
EventBridge (daily 02:00 UTC)
  → Lambda: collect_usage_metrics
    → For each workspace in PlatformAccountsTable:
      → CloudWatch GetMetricStatistics (Redshift RPU, Lambda, Glue, SFN)
      → S3 ListBuckets + GetBucketMetrics (storage)
      → DynamoDB scan LangsmithTokenUsage (filtered by workspace + date)
      → DynamoDB scan AgentBasedUsageData (filtered by workspace + date)
      → Cost Explorer GetCostAndUsage (tagged by bh:workspace-id) [depends on Spec 1]
    → Write to DynamoDB: UsageMetrics table
    → Write to S3: usage-reports/{yyyy-mm-dd}.json (archive)
```

**UsageMetrics DynamoDB table schema**:

| Field | Type | Description |
|-------|------|-------------|
| `PK` | String | `WS#{workspace-uuid}` |
| `SK` | String | `DATE#{yyyy-mm-dd}` |
| `redshift_rpu_seconds` | Number | Total RPU-seconds consumed |
| `glue_dpu_hours` | Number | Total DPU-hours consumed |
| `lambda_invocations` | Number | Total invocations across workspace Lambdas |
| `s3_storage_gb` | Number | Total GB stored across workspace buckets |
| `sfn_executions` | Number | Step Functions state transitions |
| `llm_tokens_input` | Number | Total input tokens (all providers) |
| `llm_tokens_output` | Number | Total output tokens (all providers) |
| `bedrock_tokens` | Number | Bedrock-specific token usage |
| `agent_sessions` | Number | BrightBot sessions initiated |
| `cost_ingestion_usd` | Number | Dollar cost for ingestion category |
| `cost_querying_usd` | Number | Dollar cost for querying category |
| `cost_hosting_usd` | Number | Dollar cost for hosting category (allocated share) |
| `cost_ai_usage_usd` | Number | Dollar cost for AI usage category |
| `cost_total_usd` | Number | Sum of all categories |
| `data_volume_gb` | Number | Total data under management |
| `collected_at` | String | ISO timestamp |

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| AWS Cost and Usage Report (CUR) to S3 | Most detailed billing data (line-item) | Complex Parquet files, needs Athena to query, 24h delay | Good for deep analysis later, too heavy for v1 |
| Third-party (CloudHealth, Spot.io) | Rich dashboards | Vendor cost, onboarding time | Overkill for current need |
| Manual monthly export | Zero infra | Doesn't scale, human error, not queryable | Not sustainable |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| New Lambda | `brighthive-admin` or new repo | New `collect_usage_metrics` Lambda + EventBridge rule |
| DynamoDB | Platform account | New `UsageMetrics` table |
| S3 | Platform account | New `brighthive-usage-reports-{env}` bucket |
| Workspace accounts | Cross-account | CloudWatch read access via existing STS roles |
| Cost Explorer | Platform account | API calls (requires `ce:GetCostAndUsage` permission) |

## Acceptance Criteria

- [ ] Nightly Lambda runs at 02:00 UTC in PROD and STAGE
- [ ] UsageMetrics DynamoDB table populated with per-workspace daily rows
- [ ] S3 archive contains JSON exports queryable by date
- [ ] Covers all 6 metric categories: Redshift RPU, Glue DPU, Lambda invocations, S3 storage, LLM tokens, agent sessions
- [ ] Dollar costs populated per workspace per category (requires cost-allocation-tagging spec)
- [ ] Backfill script runs once to capture available CloudWatch history (up to 15 months)
- [ ] Bedrock invocation logging enabled in all workspace accounts

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Cost Allocation Tagging (Spec 1) | Blocking for cost columns | Not started |
| Cross-account CloudWatch access | Blocking | Existing STS roles may need CloudWatch read policy |
| Bedrock invocation logging | Non-blocking | Can add later |
| Cost Explorer API permissions | Blocking | Requires IAM policy update |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| -- | Create UsageMetrics DynamoDB table + S3 bucket in platform CDK | 2 | BH-171 |
| -- | Build collect_usage_metrics Lambda (CloudWatch + DynamoDB sources) | 5 | BH-171 |
| -- | Add Cost Explorer integration to metering Lambda | 3 | BH-171 |
| -- | Add EventBridge nightly schedule | 1 | BH-171 |
| -- | Enable Bedrock invocation logging in workspace accounts | 2 | BH-171 |
| -- | Add CloudWatch read permissions to cross-account STS roles | 2 | BH-171 |
| -- | Backfill script for historical CloudWatch data | 3 | BH-171 |
| -- | CLI tool to query UsageMetrics table (per-workspace, date range) | 2 | BH-171 |
