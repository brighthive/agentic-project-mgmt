---
name: "ACG tickets"
slug: "acg"
jira_epic: "BH-1658"
last_reviewed: "2026-10-27"
---

# ACG: the work, in Jira

Jira is the source of truth for status. All tickets were in "Needs Refinement" on 27 Oct 2026, and none had started. [All epics in Jira](https://brighthiveio.atlassian.net/issues/?jql=project%3DBH%20AND%20issuetype%3DEpic%20ORDER%20BY%20created%20DESC).

## In one minute

- **One epic, five tickets.** Each ticket is one slice from the [roadmap](roadmap.md).
- **The first ticket is not code.** It settles facts we are missing: what happened at the July demo, whether data must stay in ACG's Azure tenant, which vendor feed to prove first, and ACG's baseline.
- **Nothing on Azure starts for ACG alone.** The Azure ticket waits behind the Nestlé work in [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640).

**Epic:** [BH-1658](https://brighthiveio.atlassian.net/browse/BH-1658): ACG vendor data pilot (lead)

| Slice | Ticket | What it proves | Size | Depends on |
|---|---|---|---|---|
| 0 | [BH-1659](https://brighthiveio.atlassian.net/browse/BH-1659) | We know the facts and the proposal no longer promises what we cannot deliver | S | Calls with ACG |
| 1 | [BH-1660](https://brighthiveio.atlassian.net/browse/BH-1660) | One vendor feed is profiled, checked for quality and drift, and a morning exception list reaches Slack | L | Slice 0 |
| 2 | [BH-1661](https://brighthiveio.atlassian.net/browse/BH-1661) | Our SSIS diagnosis names a slow or failing step on ACG's own packages | M | Sample packages from ACG |
| 3 | [BH-1662](https://brighthiveio.atlassian.net/browse/BH-1662) | A real feed failure becomes a fix that arrives as a reviewed pull request | M | Slice 1 |
| 4 | [BH-1663](https://brighthiveio.atlassian.net/browse/BH-1663) | The same pilot runs inside ACG's Azure tenant, if ACG requires it | XL | Slice 0, [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640) |

## Which acceptance scenario each ticket covers

The scenarios are in the [pilot spec](https://github.com/brighthive/agentic-project-mgmt/blob/master/docs/specs/acg-vendor-data-pilot.md#4-acceptance-criteria).

| Scenario | Ticket |
|---|---|
| Vendor feed is profiled on arrival | [BH-1660](https://brighthiveio.atlassian.net/browse/BH-1660) |
| Future-dated field becomes an exception | [BH-1660](https://brighthiveio.atlassian.net/browse/BH-1660) |
| Vendor schema change is caught early | [BH-1660](https://brighthiveio.atlassian.net/browse/BH-1660) |
| Morning exception list | [BH-1660](https://brighthiveio.atlassian.net/browse/BH-1660) |
| Slow SSIS job is diagnosed | [BH-1661](https://brighthiveio.atlassian.net/browse/BH-1661) |
| Fix arrives as a pull request | [BH-1662](https://brighthiveio.atlassian.net/browse/BH-1662) |

## Not ticketed on purpose

Microsoft Teams delivery (a sender exists but is disconnected), Azure Data Factory support (a webapp card with nothing behind it), and connectors for all five vendors. None works today, and ACG has not said it needs them. Decide with ACG first. See the [overview](overview.md#what-the-proposal-promises-and-what-exists-today).
