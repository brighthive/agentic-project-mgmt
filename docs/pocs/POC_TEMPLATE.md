---
title: ""
date: "YYYY-MM-DD"
duration: ""
decision: "Go | No-Go | Pivot | Deferred"
status: "In Progress | Complete"
methodologies_compared: []
epic: "BH-XXX"
tags: []
related:
  specs: []
  bedrock: []
  features: []
---

# [POC Name]

## Question

What are we trying to answer? One clear question.

## Methodologies

What approaches are we comparing?

### Approach A: [Name]

How it works. Setup, configuration, dependencies.

### Approach B: [Name]

How it works. Setup, configuration, dependencies.

### Approach C: [Name] (if applicable)

How it works. Setup, configuration, dependencies.

## Success Criteria

| Metric | Target | Why This Matters |
|--------|--------|-----------------|
| [latency p50] | < 200ms | User experience |
| [accuracy] | > 95% | Data quality |
| [cost/month] | < $500 | Budget constraint |

## Results — Qualifying Numbers

### Comparison Table

| Metric | Approach A | Approach B | Approach C | Winner |
|--------|-----------|-----------|-----------|--------|
| Latency p50 | Xms | Yms | Zms | |
| Latency p99 | Xms | Yms | Zms | |
| Accuracy | X% | Y% | Z% | |
| Cost/month | $X | $Y | $Z | |
| Setup complexity | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] | |
| Maintenance burden | [Low/Med/High] | [Low/Med/High] | [Low/Med/High] | |

### Detailed Results

#### Approach A
Observations, edge cases, failure modes, scaling behavior.

#### Approach B
Observations, edge cases, failure modes, scaling behavior.

#### Approach C
Observations, edge cases, failure modes, scaling behavior.

## Decision

**[Go with Approach X / No-Go / Pivot / Deferred]**

Rationale: [backed by the numbers above — reference specific metrics]

## Learnings

What we learned that applies beyond this POC. This section is required even if the POC succeeded.

- Learning 1
- Learning 2

## Next Steps

- **If Go**: Create spec via `/write-spec`, generate tickets via `/create-jira-ticket`
- **If refining**: What to test next in the POC ↔ Spec loop
- **If No-Go**: Alternative approach or why we're stopping
- **If Deferred**: Conditions for revisiting

## Artifacts

- **Code branches**: [branch names or PR links]
- **Notebooks**: [path]
- **Data/benchmarks**: [path or link]
- **Screenshots**: [path]
