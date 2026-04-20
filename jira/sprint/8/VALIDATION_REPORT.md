# Sprint 8 --- Validation Report (Mid-Sprint Checkpoint)

**Period**: Apr 14--28, 2026 | **Checkpoint**: Apr 20, 2026

---

## PR <-> Ticket Linkage Summary

| Metric | Count | % |
|--------|-------|---|
| Total Feature PRs | 82 | 100% |
| Matched to Jira tickets | 28 | 34% |
| Unmatched (no ticket ref) | 54 | 66% |
| **Linkage Rate** | **34%** | **Improved from 22%** |

---

## Matched PRs (BH-XXX in branch name or title)

| PR | Repo | Ticket(s) | Match Source |
|----|------|-----------|-------------|
| #445 | brightbot | BH-357 | Branch name |
| #721 | platform-core | BH-356 | Branch name |
| #1047, #1048 | webapp | BH-356 | Branch name |
| #444 | brightbot | BH-355 | Branch name |
| #1046, #1048 | webapp | BH-355 | Branch name |
| #1039 | webapp | BH-346 | Branch name |
| #713 | platform-core | BH-344, BH-345 | Branch name |
| #1040, #1041 | webapp | BH-344, BH-345, BH-346 | Branch name |
| #712 | platform-core | BH-339 | Branch name |
| #1037, #1038 | webapp | BH-339 | Branch name |
| #709 | platform-core | BH-330 | Branch name |
| #434 | brightbot | BH-325, BH-328 | Branch name |
| #1034 | webapp | BH-326, BH-331 | Branch name |
| #724 | platform-core | BH-347 | Branch name |
| #1049, #1058-1065 | webapp | BH-347 | Branch name |
| #440 | brightbot | BH-347 | Branch name |
| #1035 | webapp | BH-319 | Branch name |
| #449, #450 | brightbot | BH-360 | Branch name |
| #729 | platform-core | BH-374 | Branch name |
| #733 | platform-core | BH-375 | Branch name |
| #1057, #1069 | webapp | BH-375 | Branch name |
| #1055, #1068 | webapp | BH-359 | Branch name |
| #1067, #1073 | webapp | BH-376 | Branch name |
| #149 | data-org-cdk | BH-351 | Branch name |
| #1052 | webapp | BH-358 | Branch name |
| #719 | platform-core | BH-311 | Branch name |
| #720 | platform-core | BH-353 | Branch name |
| #443 | brightbot | BH-354 | Branch name |

---

## Tickets Done WITHOUT Matched PRs

These tickets were marked Done but have no PRs with their ticket key in the branch name:

| Ticket | Summary | Assignee | Notes |
|--------|---------|----------|-------|
| BH-342 | dbt agent auto-read TransformationService config | Hikuri | Likely covered by #434 (BH-325-328 branch) |
| BH-340 | Replace Job ID text field with dbt Cloud job dropdown | Hikuri | Likely covered by #1035 (BH-319 branch) |
| BH-322 | Azure Synapse T-SQL dialect support | Hikuri | Covered by #433, #722 (feature/azure-synapse branch) |
| BH-321 | Warehouse adapter pattern for webhook processing | Hikuri | Covered by #707 (feature/omd-warehouse-adapter branch) |
| BH-282 | Claude to Bedrock migration -- model routing | Hikuri | No matching PR branch found |
| BH-278 | EDL shutdown -- decommission legacy pipeline | Ahmed | No matching PR branch found -- may be infra/config change |
| BH-253 | OMD webhook enhanced event tracking | Ahmed | Covered by #730 (feat/event-tracking branch, no BH-XXX) |
| BH-240 | GraphQL capabilities for deep_agent supervisor | Marwan | Covered by #435 (feature/graphql-capabilities branch, no BH-XXX) |

---

## Orphan PRs (No Jira Ticket)

Major work shipped with no Jira tracking:

| Feature | PRs | Repo(s) | Author |
|---------|-----|---------|--------|
| **React 17 to 18 upgrade** | #1028 | webapp | Marwan |
| **Scheduler (cron jobs)** | #451, #728, #1054 | brightbot, core, webapp | Harbour |
| **Data preview asset tab** | #708, #1033 | core, webapp | Harbour |
| **Notification endpoint + filtering** | #738, #740, #742 | platform-core | Ahmed |
| **tableFQN generic warehouse type** | #737 | platform-core | Ahmed |
| **Synapse ingestion CDK stack** | #139, #150, #151 | data-org-cdk | Ahmed/Hikuri |
| **Metadata configs for unstructured data** | #119 | data-workspace-cdk | Ahmed |
| **Redshift CATALOG_ID fix** | #122 | data-workspace-cdk | Hikuri |
| **Claude PR review workflow** | #119, #111 | data-org-cdk, data-workspace-cdk | Hikuri |
| **DX readme rewrites** | #145, #118 | data-org-cdk, data-workspace-cdk | Hikuri |
| **Slack idempotent service user** | #736 | platform-core | Hikuri |
| **Slack bot mention-only filter** | #13, #14 | slack-server | Hikuri |
| **deepagent package pin** | #447, #448 | brightbot | Ahmed |
| **addSource mutation fix** | #711 | platform-core | Ahmed |
| **GitHub auth secret upsert fix** | #734 | platform-core | Marwan |
| **GitHub device flow polling fix** | #1070 | webapp | Marwan |
| **Warehouse registry patterns** | #1032 | webapp | Hikuri |
| **.env.example docs** | #453 | brightbot | Hikuri |
| **Seed data (workflow entities)** | #714 | platform-core | Hikuri |
| **BIT datatype for Azure SQL** | #726 | platform-core | Ahmed |
| **Slack Vite env fix** | #1056 | webapp | Hikuri |
| **Auth test + cursor guard** | #446 | brightbot | Hikuri |
| **Dead imports + a11y fix** | #1051 | webapp | Hikuri |

---

## Estimation Gaps

| Ticket | Summary | Points |
|--------|---------|--------|
| BH-357 | Inject governance policies into workspace context | **Unpointed** |
| BH-356 | Add isActive field to CustomPolicyNode | **Unpointed** |
| BH-355 | Credential form HITL interrupt for ingestion | **Unpointed** |
| BH-346 | dbt model detail view with SQL, PR link, lineage, origin badge | **Unpointed** |
| BH-345 | Extend TransformationNode with model metadata | **Unpointed** |
| BH-344 | Extend TransformationNode with model metadata | **Unpointed** |
| BH-342 | dbt agent auto-read TransformationService config | **Unpointed** |
| BH-340 | Replace Job ID text field with dbt Cloud job dropdown | **Unpointed** |
| BH-339 | Device Flow OAuth + disconnect for GitHub connection | **Unpointed** |
| BH-330 | Complete dbt workflow | **Unpointed** |
| BH-328 | dbt agent flow improvements | **Unpointed** |
| BH-327 | Webapp dbt settings + GitHub repo management | **Unpointed** |
| BH-326 | Webapp dbt settings and GitHub repo management | **Unpointed** |
| BH-325 | dbt agent flow improvements | **Unpointed** |
| BH-322 | Azure Synapse T-SQL dialect support | **Unpointed** |
| BH-321 | Warehouse adapter pattern for webhook processing | **Unpointed** |
| BH-319 | Replace Job ID text field with dbt Cloud job dropdown | **Unpointed** |
| BH-282 | Claude to Bedrock migration -- model routing | **Unpointed** |
| BH-253 | OMD webhook enhanced event tracking | **Unpointed** |

**19 of 21 Done tickets are unpointed.** Velocity tracking is non-functional this sprint.

---

## Recommendations

1. **Retroactively point all 19 unpointed Done tickets** to restore velocity tracking. Even 1/2/3 estimates are better than nothing.
2. **Create Jira tickets for**: React 18 upgrade, Scheduler, Data preview, Notification endpoints, Synapse CDK stack, Claude PR review workflow.
3. **Enforce `BH-XXX/` branch prefix** across all team members -- currently only Hikuri follows the convention consistently.
4. **Bundle awareness**: #1034 (+29K/-7K) contains multiple tickets' worth of work (BH-326, BH-327, BH-331). Future PRs should be split per ticket.
5. **The React 18 upgrade** (#1028, +43K/-87K lines) needs a Jira ticket, testing ticket, and documentation -- this is a major framework migration with zero audit trail.
