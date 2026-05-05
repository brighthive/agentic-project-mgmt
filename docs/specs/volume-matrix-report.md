---
title: "Volume Matrix Report"
epic: "BH-172"
author: "Kuri"
status: "Draft"
created: "2026-04-16"
generates: "tickets"
tags: [reporting, cost, enterprise-sales, nestle]
related:
  features: []
  pocs: [cost-allocation-tagging, usage-metering-pipeline]
  bedrock: []
---

# Volume Matrix Report

## Problem

Enterprise prospects (Nestle) ask "what does it cost at my data volume?" and BrightHive has no answer grounded in real data. Estimated tables have been rejected as not credible. We need a report generated from actual production usage metrics that maps data volume to cost, broken down by category (ingestion, querying, hosting, AI usage), with real percentages.

## Use Case / Goal

A monthly report (automated) that produces a table like:

| Workspace | Data Volume | Ingestion $/mo (%) | Querying $/mo (%) | Hosting $/mo (%) | AI Usage $/mo (%) | Total $/mo |
|-----------|-------------|--------------------|--------------------|-------------------|---------------------|------------|
| Virginia WDT | 247 GB | $312 (18%) | $823 (47%) | $412 (24%) | $198 (11%) | $1,745 |
| Colorado | 89 GB | $94 (12%) | $401 (51%) | $206 (26%) | $87 (11%) | $788 |
| CredLens | 1.2 TB | $890 (22%) | $1,640 (41%) | $412 (10%) | $1,080 (27%) | $4,022 |

This is the real volume matrix. Every number comes from AWS Cost Explorer + CloudWatch metrics, not estimates.

## Current Situation

### How It Works Today

It doesn't. Sales uses back-of-napkin estimates. Engineering has no cost visibility per workspace.

### Hard Limitations

- Depends on cost allocation tagging being deployed (Spec 1)
- Depends on usage metering pipeline running for at least 1 billing cycle (Spec 2)
- Shared platform costs (Neo4j, Redis) require an allocation model — will always be an approximation
- LLM costs from Anthropic direct API (not Bedrock) are billed to a single account, not per-workspace

### Gaps

1. No report generation pipeline
2. No cost-per-GB regression model
3. No historical trend data
4. No export format suitable for sales decks or enterprise questionnaires

## Proposals / Solutions

### Recommended Approach

**Monthly Lambda** that reads from the `UsageMetrics` DynamoDB table (Spec 2), aggregates to monthly per-workspace totals, computes percentages and per-GB rates, and outputs:

1. **JSON** — raw data for programmatic use
2. **Markdown** — for docs repo and Notion
3. **CSV** — for spreadsheets and sales decks

**Report structure**:

```
Volume Matrix Report — March 2026
Generated: 2026-04-01T02:30:00Z
Source: UsageMetrics DynamoDB (PROD)

## Per-Workspace Breakdown

| Workspace | Data (GB) | Ingestion | Querying | Hosting | AI Usage | Total |
|-----------|-----------|-----------|----------|---------|----------|-------|
| [real data from UsageMetrics table]

## Cost-per-GB Analysis

| Data Tier | Workspaces | Avg $/GB/mo | Median $/GB/mo | Ingestion % | Querying % | Hosting % | AI % |
|-----------|-----------|-------------|----------------|-------------|------------|-----------|------|
| < 100 GB  | N         | $X.XX       | $X.XX          | XX%         | XX%        | XX%       | XX%  |
| 100-500 GB| N         | $X.XX       | $X.XX          | XX%         | XX%        | XX%       | XX%  |
| 500 GB-1 TB| N        | $X.XX       | $X.XX          | XX%         | XX%        | XX%       | XX%  |
| 1-5 TB    | N         | $X.XX       | $X.XX          | XX%         | XX%        | XX%       | XX%  |
| 5+ TB     | N         | $X.XX       | $X.XX          | XX%         | XX%        | XX%       | XX%  |

## Scaling Curve

| Per +100 GB | Ingestion Delta | Querying Delta | Hosting Delta | AI Delta | Total Delta |
|-------------|-----------------|----------------|---------------|----------|-------------|
| [computed from regression across workspace data points]

## Month-over-Month Trend

| Month | Total Workspaces | Total Data (TB) | Total Cost | Avg $/Workspace |
|-------|-----------------|-----------------|------------|-----------------|
| [rolling 6 months]
```

**Derived metrics** computed from raw data:
- `cost_per_gb` = `cost_total_usd / data_volume_gb`
- `ingestion_pct` = `cost_ingestion_usd / cost_total_usd * 100`
- `querying_pct` = `cost_querying_usd / cost_total_usd * 100`
- `hosting_pct` = `cost_hosting_usd / cost_total_usd * 100`
- `ai_usage_pct` = `cost_ai_usage_usd / cost_total_usd * 100`
- `marginal_cost_per_100gb` = linear regression slope across workspaces

**Output destinations**:
- S3: `brighthive-usage-reports-{env}/volume-matrix/{yyyy-mm}.{json|md|csv}`
- Notion: auto-publish via Notion MCP (optional)
- platform-saas-ai-context repo: commit updated matrix to `docs/infrastructure/VOLUME_MATRIX.md`

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| QuickSight dashboard | Interactive, AWS-native | Requires CUR setup, QuickSight license, learning curve | Too heavy for v1 |
| Manual spreadsheet | Flexible | Not reproducible, stale immediately | Not scalable |
| Grafana | Great for time-series | Needs Grafana infra, not suitable for sales decks | Better for internal ops later |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| New Lambda | `brighthive-admin` | New `generate_volume_matrix` Lambda + monthly EventBridge |
| S3 | Platform account | Output bucket (same as metering pipeline) |
| Docs repo | `platform-saas-ai-context` | Auto-committed `VOLUME_MATRIX.md` |
| Notion (optional) | MCP integration | Auto-published page |

## Acceptance Criteria

- [ ] Monthly report generates automatically on 1st of each month
- [ ] Per-workspace breakdown with real dollar amounts from Cost Explorer
- [ ] Category percentages (ingestion, querying, hosting, AI) computed from tagged costs
- [ ] Cost-per-GB tier analysis with at least 3 data-volume tiers
- [ ] Scaling curve showing marginal cost per +100 GB
- [ ] Output in JSON, Markdown, and CSV
- [ ] Report committed to platform-saas-ai-context repo as `VOLUME_MATRIX.md`
- [ ] First report generated within 30 days of metering pipeline going live
- [ ] Client names anonymized in any externally-shared version

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| Cost Allocation Tagging (Spec 1) | Blocking | Not started |
| Usage Metering Pipeline (Spec 2) | Blocking | Not started |
| At least 1 full billing cycle of tagged data | Blocking | Starts after Spec 1 deploys |
| Notion MCP access (optional) | Non-blocking | Available |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| -- | Build generate_volume_matrix Lambda | 5 | BH-172 |
| -- | Add monthly EventBridge schedule | 1 | BH-172 |
| -- | Implement per-workspace aggregation + category percentages | 3 | BH-172 |
| -- | Implement cost-per-GB tier analysis + regression | 3 | BH-172 |
| -- | Output formatters (JSON, Markdown, CSV) | 2 | BH-172 |
| -- | Auto-commit VOLUME_MATRIX.md to docs repo | 2 | BH-172 |
| -- | Client name anonymization for external sharing | 1 | BH-172 |
| -- | Notion auto-publish (optional) | 2 | BH-172 |
