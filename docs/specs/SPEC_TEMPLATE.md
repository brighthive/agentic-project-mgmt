---
title: ""
epic: "BH-XXX"
author: ""
status: "Draft | Review | Approved | In Progress | Done"
created: "YYYY-MM-DD"
generates: "epic | tickets"
tags: []
related:
  features: []
  pocs: []
  bedrock: []
---

# [Feature/Migration Name]

## Problem

What's broken, missing, or needed? Why now? Be specific — this feeds into AI agents for implementation planning.

## Use Case / Goal

What does success look like? Who benefits and how? Describe the end state.

## Current Situation

### How It Works Today

Description of current implementation, behavior, architecture. Include relevant service names, repos, and data flows.

### Hard Limitations

What CANNOT be done with the current approach. Technical ceilings, architectural constraints, vendor limitations.

### Gaps

What's missing — functionality, integration points, data, UX, observability. Be exhaustive.

## Proposals / Solutions

Recommended approach with trade-offs. If multiple options, list them with pros/cons.

### Recommended Approach

High-level architecture. Why this path over alternatives.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| [approach] | [benefits] | [drawbacks] | [reason rejected] |

## Areas Involved

Which BrightHive services, repos, and infrastructure are touched.

| Area | Repo | Impact |
|------|------|--------|
| BrightBot | `brightbot` | [what changes] |
| Web App | `brighthive-webapp` | [what changes] |
| Platform Core | `brighthive-platform-core` | [what changes] |

## Acceptance Criteria

- [ ] Criterion 1 (measurable, verifiable)
- [ ] Criterion 2 (measurable, verifiable)
- [ ] Criterion 3 (measurable, verifiable)

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| [service/API] | Blocking / Non-blocking | Ready / In progress / Not started |

## Ticket Breakdown

Generated via `/create-jira-ticket` from this spec:

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | [task 1] | 3 | BH-XXX |
| — | [task 2] | 2 | BH-XXX |

## Related

- **POC**: `docs/pocs/[slug].md` (if validated by experiment)
- **Feature doc**: `docs/features/[slug].md` (create after shipping)
- **Bedrock**: `docs/bedrock/[entry].md` (if migration-related)
