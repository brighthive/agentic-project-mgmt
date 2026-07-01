# AGENTS.md - Documentation Workflow Contract

This directory owns specs, feature docs, POCs, and the Bedrock migration
journal. It is the agent-neutral entry point for the flows also described in
`docs/CLAUDE.md`.

## Read First

- `AGENTS.md` - this portable contract
- `CLAUDE.md` - detailed legacy workflow guide and skill mapping
- The relevant template before creating or updating a document:
  - `specs/SPEC_TEMPLATE.md`
  - `features/FEATURE_TEMPLATE.md`
  - `pocs/POC_TEMPLATE.md`
  - `bedrock/BEDROCK_TEMPLATE.md`

## Lifecycle

```text
write POC -> write spec -> create Jira ticket -> implement -> write feature doc
```

`/bedrock-journal` is a parallel weekly migration diary flow, not a replacement
for implementation specs.

Claude slash commands are accelerators. Other agents must perform the same
steps manually with the templates and live repo context.

## Directory Ownership

| Directory | Purpose | When to edit |
|---|---|---|
| `specs/` | Implementation specs | Before product or migration code changes |
| `features/` | Shipped feature documentation | After a capability ships |
| `pocs/` | Comparative experiments with numbers | Before and after experiments |
| `bedrock/` | LangGraph to Bedrock migration diary | Weekly or phase milestone updates |

Do not put permanent architecture truth here. Architecture, environments,
accounts, ADRs, and roadmap docs belong in `../../platform-saas-ai-context`.

## Spec Rules

- Specs are written before code when a change affects product behavior,
  architecture, cross-repo contracts, AI-agent behavior, or migration strategy.
- Use `specs/SPEC_TEMPLATE.md`.
- Include acceptance criteria and a concrete test coverage update.
- Link Jira epics or tickets with `BH-XXX` keys.
- If the spec changes deployed architecture, update
  `../../platform-saas-ai-context` only after the implementation reality changes.

## Feature Doc Rules

- Feature docs describe shipped behavior, not planned behavior.
- Use `features/FEATURE_TEMPLATE.md`.
- Put screenshots or diagrams under `features/assets/{feature-slug}/`.
- Link back to the originating spec, Jira ticket or epic, and meaningful PRs.

## POC Rules

- Use `pocs/POC_TEMPLATE.md`.
- Define the question, methodologies, success criteria, and thresholds before
  running the experiment.
- Complete results with numbers, a decision, learnings, and next steps.
- Keep No-Go POCs. They are part of the decision record.

## Bedrock Journal Rules

- Use `bedrock/BEDROCK_TEMPLATE.md`.
- Read the previous entry first for continuity.
- Include what worked, what did not work, decisions, metrics, and next week.
- Update `bedrock/INDEX.md` when adding an entry.

## Naming And Format

- Content files use `kebab-case.md`.
- Templates use `UPPER_CASE.md`.
- YAML frontmatter is required for content files.
- Dates use `YYYY-MM-DD`.
- Cross-reference related docs through frontmatter and a Related section.
