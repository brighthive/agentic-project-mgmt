---
name: "ACG vendor data pilot"
epic: "BH-1658"
status: Partial
roadmap: "clients/leads/acg/roadmap.md; capabilities exist on AWS staging, ACG-specific proof and the Azure environment are not started"
last_reviewed: "2026-10-27"
---

# ACG vendor data pilot

## 1. Context

ACG, a registered investment adviser on its own Azure tenant, wants vendor data (Advent APX, eVestment, FactSet, Morningstar, Bloomberg) to arrive cleaner and faster, and wants a morning list of exceptions instead of people chasing bad records. This spec defines what the first proof must show. Lead record: [ACG overview](../../clients/leads/acg/overview.md).

## 2. Interface contract

| Boundary | Contract |
|---|---|
| Vendor feed in | One named vendor feed, delivered by file or API, lands in a workspace |
| Quality result out | Per dataset: schema profile, expectation results, drift flag, a pass/fail summary |
| Exception list out | One message per morning naming what failed, which feed, which field, and who decides |
| Fix proposal | A pull request with the SQL or dbt change, never a direct write |

## 3. Invariants

- Every exception names the dataset, the rule that failed, the measured value and when it was measured.
- A bad record never stops the feed silently; it becomes an exception.
- A fix is a reviewed pull request. No agent writes to ACG's warehouse or repository directly.
- Delivery uses only channels that exist. Today that is Slack and MCP read-back, not Teams.
- All evidence comes from the environment ACG agreed to, not from AWS staging alone.

## 4. Acceptance criteria

```gherkin
Feature: ACG vendor data pilot

  Scenario: Vendor feed is profiled on arrival
    Given the agreed vendor feed lands in the pilot workspace
    When the quality agent runs
    Then a schema profile and expectation results are stored for that dataset

  Scenario: Future-dated field becomes an exception
    Given a record with a future-dated field
    When the checks run
    Then the record appears as a named exception and the feed continues

  Scenario: Vendor schema change is caught early
    Given the vendor adds or renames a column
    When the next feed arrives
    Then a drift flag is raised before downstream reports refresh

  Scenario: Morning exception list
    Given overnight checks ran
    When the morning delivery time passes
    Then one Slack message lists what failed, where, and who decides

  Scenario: Slow SSIS job is diagnosed
    Given a sample ACG SSIS package and run history
    When the SSIS diagnosis skill runs
    Then it names the slow or failing step with evidence

  Scenario: Fix arrives as a pull request
    Given a failing transformation
    When the engineering agent proposes a fix
    Then a pull request is opened and nothing is written directly
```

## 5. Out of scope

Replacing ACG's warehouse choice, Teams delivery, Data Factory orchestration, client reporting content, any claim about copying a model into ACG's environment.

## 6. Dependencies

- Environment decision: AWS-hosted for the proof, or ACG's Azure tenant. The Azure path depends on the plan under [BH-1640](https://brighthiveio.atlassian.net/browse/BH-1640) and the [cloud-agnostic adapters spec](cloud-agnostic-adapters.md).
- One vendor feed, with sample files and a named ACG owner.
- ACG's baseline: hours spent on bad records and how late feeds arrive today.
- Existing capability to reuse: quality agent, data profiler and schema agents, scheduled watchdog and digest tasks, the SSIS diagnosis skill, dbt agent pull requests.

## 7. Eval criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| Exception completeness | morning delivery | GATE | every exception has dataset, rule, value, time | Deterministic |
| SSIS diagnosis accuracy | SSIS diagnosis | OBSERVE | agreed with ACG's developers on sample packages | Human review |
