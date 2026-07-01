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

> Full contract: `~/.claude/rules/spec-driven.md`. Sections 7–9 are conditional — keep them only
> when they apply (see each section's "Required when"); delete the heading if not applicable
> rather than leaving it empty. §10 is mandatory for every spec.

## 1. Context

What problem, for whom, why now. One paragraph max. For non-trivial state machines or
cross-actor flows, add a `mermaid` `sequenceDiagram` or `stateDiagram-v2` block here — GitHub
renders it natively.

### Use Case / Goal

What does success look like? Who benefits and how?

### How It Works Today

Current implementation, behavior, architecture. Name the real repos, services, data flows.

### Hard Limitations

What CANNOT be done with the current approach. Technical ceilings, architectural constraints.

### Gaps

What's missing — functionality, integration points, data, UX, observability. Be exhaustive.

## 2. Interface Contract (MDE)

Typed contracts at every boundary this spec touches — REST endpoint, GraphQL mutation, function
signature, CLI flag. Machine-checkable; becomes the source for generated Pydantic/TypeScript/
GraphQL types.

```
POST /api/v1/resource
  Request:  { field: Type, ... }
  Response 200: { ... }
  Response 4xx: { error: "code_1" | "code_2" }
```

## 3. Invariants (DbC)

What must ALWAYS hold. Becomes assertions, validators, property-based tests. Budget: ≤15 per
service boundary. EARS form is fine for state-machine rules:

```
WHEN <event>, THE System SHALL [NOT] <action>
```

## 4. Acceptance Criteria (BDD — Gherkin)

Given/When/Then. Becomes executable tests. Budget: ≤20 scenarios; split the spec if more.

```gherkin
Feature: [name]

  Scenario: [happy path]
    Given [precondition]
    When [action]
    Then [observable outcome]

  Scenario: [error path]
    Given [precondition]
    When [invalid action]
    Then [error response]
```

## 5. Out of Scope

Explicit non-goals. Prevents scope creep.

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| [service/API] | Blocking / Non-blocking | Ready / In progress / Not started |

## 7. Correctness Properties

**Required when** the spec involves a state machine, a security/safety boundary, or a
concurrency/time-sensitive guarantee. Otherwise delete this section.

```markdown
### Property 1: <one-line claim>

*For any* <quantifier>, <invariant statement>.

**Validates: §3 Invariant <n>, §4 Scenario "<name>"**
```

## 8. Eval Criteria

**Required when** the spec touches LLM/agent behavior (BrightBot graphs, tools, prompts).
Otherwise delete this section.

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| [name] | [graph/tool node] | GATE \| OBSERVE | score >= X | LLM judge / deterministic / hybrid |

## 9. Observability Contract

**Required when** the spec produces a production surface (new endpoint, tool, agent node).
Otherwise delete this section.

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=<name>` (OTel GenAI convention)
- **Attributes**: `workspace.id`, ...
- **Log events**: `<name>.started`, `<name>.success`, `<name>.failed`
- **Metrics**: none / [list]

## 10. Test Coverage Update

Mandatory. A spec is not "done" at §1–§9 — before implementation, extend the real test suites
that already exist for the repos this spec touches. No new spec ships without this. Only list
rows for the BrightHive repos this spec actually touches; delete the rest.

| Repo | Suite | What to add |
|---|---|---|
| `brightbot` | `brightbot/tests/` (unit/integration) + `brightbot/brightbot/evals/` (L0 surface / L1 routing / L2 behavior, per `brightbot/CLAUDE.md`) | One L0 case per §2 entry, one L1 case per §4 routing-observable scenario, one L2 case per §3 invariant + §8 evaluator |
| `brighthive-webapp` | `brighthive-webapp/tests/e2e` (Playwright) + `cypress/` | One Playwright spec for the §4 happy-path scenario against the real UI; Cypress for component-level checks |
| `brighthive-platform-core` | `brighthive-platform-core/tests/` | One test per §2 GraphQL/REST contract entry, one per §3 invariant observable via the API |
| `brighthive-e2e` | `brighthive-e2e/e2e/` (cross-repo, 8 surfaces, 3 envs) | One feature test for the §4 happy path end-to-end across real surfaces; one error-path test against the real backend |

**Real-behavior requirement** (`~/.claude/rules/test-behavior-real.md`): at least one L2/integration
case per repo row above must hit the real client/backend (or a captured replay), not a mock.
Construct-only tests (asserting shapes/paths/schemas) don't satisfy this row.

Before opening the implementation PR: run every suite listed above, confirm each new §2/§3/§4/§8
entry has a corresponding new test case, and confirm all suites are green.

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| BrightBot | `brightbot` | [what changes] |
| Web App | `brighthive-webapp` | [what changes] |
| Platform Core | `brighthive-platform-core` | [what changes] |

## Ticket Breakdown

Generated via `/create-jira-ticket` from this spec. Every row is an `issueType: "Task"` under
the epic in frontmatter — never `"Story"`.

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | [task 1] | 3 | BH-XXX |
| — | [task 2] | 2 | BH-XXX |

## Related

- **POC**: `docs/pocs/[slug].md` (if validated by experiment)
- **Feature doc**: `docs/features/[slug].md` (create after shipping)
- **Bedrock**: `docs/bedrock/[entry].md` (if migration-related)
