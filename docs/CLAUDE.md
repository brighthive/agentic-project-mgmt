# Docs — Documentation & Strategy Hub

> Agent-neutral instructions live in `AGENTS.md`. This file keeps the
> Claude Code skill mapping and detailed workflow notes.

## Directory Structure

```
docs/
├── AGENTS.md                        # Agent-neutral workflow contract
├── CLAUDE.md                        # This file
├── specs/                           # Context generation specs (write BEFORE code)
│   └── SPEC_TEMPLATE.md            # Spec template
├── features/                        # Product showcase + user manuals
│   ├── FEATURE_TEMPLATE.md         # Feature doc template
│   └── assets/{feature}/           # Screenshots, diagrams per feature
├── bedrock/                         # Insider migration engineering diary
│   ├── BEDROCK_TEMPLATE.md         # Weekly entry template
│   └── INDEX.md                    # Topic + chronological index
└── pocs/                            # Comparative experiments with qualifying numbers
    └── POC_TEMPLATE.md             # POC template
```

## Cross-Module Lifecycle

```
/write-poc ──numbers validate──→ /write-spec ──generates──→ /create-jira-ticket
     ↑                               ↑                            │
     └── refine loop ─────────────────┘                     implement
                                                                   │
                                                    /write-feature-doc
                                                     (after shipping)

/bedrock-journal tracks migration execution weekly throughout all phases
```

---

## specs/

**Purpose**: Context generation documents for machines and humans. Define the problem space, current limitations, and proposed solutions so AI agents can plan implementation.
**Skill**: `/write-spec`
**Template**: `specs/SPEC_TEMPLATE.md`
**Naming**: `{feature-slug}.md`

**Structure**: 10 sections per `~/.claude/rules/spec-driven.md` — (1) Context, (2) Interface
Contract (MDE), (3) Invariants (DbC), (4) Acceptance Criteria (Gherkin), (5) Out of Scope,
(6) Dependencies, (7) Correctness Properties (conditional), (8) Eval Criteria (conditional,
LLM/agent specs), (9) Observability Contract (conditional, production surfaces), (10) Test
Coverage Update (mandatory — extends real suites: `brightbot/tests/` + `brightbot/brightbot/evals/`,
`brighthive-webapp/tests/e2e` Playwright + `cypress/`, `brighthive-platform-core/tests/`,
`brighthive-e2e/e2e/` cross-repo).

**Workflow**:
1. Run `/write-spec` or `/write-spec feature-name` or `/write-spec --from BH-XXX`
2. Skill reads codebase, gathers context, fills template
3. Review with team or `/review-code`
4. §10 is not optional — new test cases land in the relevant repo's suite(s) above, and all suites run green before the spec is "done"
5. Generate Jira tickets with `/create-jira-ticket`
6. Plan sprint with `/scrum-master`
7. After shipping, run `/write-feature-doc`

**Engine-agnostic by default — no spec hardcodes one vendor/technology when more than one
exists or plausibly will.** Any spec integrating a pipeline engine (dbt, Databricks, Airflow),
a warehouse (Snowflake, Redshift, Synapse), a lineage/metadata source, or any other
swappable external system MUST define a PORT (a `Protocol`) first, with the first real vendor
as the FIRST ADAPTER behind a REGISTRY — never as hardcoded types/function names baked into
the domain logic. Concretely: `LineageSource` (the port), `DbtLineageSource` (adapter #1),
`LINEAGE_SOURCE_ADAPTERS` (the registry) — not `DbtLineageNode`/`fetch_dbt_lineage_artifacts`
sprinkled through the engine-agnostic code paths that walk/enrich/alert on the data, forcing a
second vendor's support to mean touching code that has nothing to do with that vendor. This
mirrors the existing `~/.claude/rules/pluggable-scalable.md` rule (Ports & Adapters, new
engines are config not code) — that rule already applies globally; this note exists because a
spec drifted into vendor-hardcoded naming before a second engine was even due, and the fix
required a mid-spec rename across every affected type/function/ticket. Catch this at DRAFT
time, not after 3 tickets already reference the wrong names: when writing §2 Interface
Contract, the FIRST thing on the page is the port + registry, and only THEN the first
adapter's concrete implementation, clearly labeled "the first adapter, not the design."

---

## features/

**Purpose**: Product showcase + user manual. Marketing pitch, UX walkthroughs with screenshots/videos, tech guides. Publishes to Notion Platform Features page.
**Skill**: `/write-feature-doc`
**Template**: `features/FEATURE_TEMPLATE.md`
**Naming**: `{feature-slug}.md`

**Structure**: What It Does → How It Works → How to Use It (UX Guide + Tech Guide) → Sub-Features → Limitations & Roadmap → Changelog

**Workflow**:
1. After ship, run `/write-feature-doc` or `/write-feature-doc --from BH-XXX`
2. Skill pulls sprint data, PRs, originating spec
3. Add screenshots to `features/assets/{feature}/`
4. Optionally publish to Notion with `--publish`

---

## bedrock/

**Purpose**: Insider engineering diary for the LangGraph → AWS Bedrock migration. Weekly entries with deep technical detail, current-state mapping, architecture diagrams, and lessons learned.
**Skill**: `/bedrock-journal`
**Template**: `bedrock/BEDROCK_TEMPLATE.md`
**Index**: `bedrock/INDEX.md` (auto-generated, grouped by topic + chronological)
**Naming**: `{NNN}-{slug}.md` (zero-padded sequence, e.g., `001-foundation-setup.md`)

**Structure**: This Week's Focus → Current State Mapping (BH ↔ Bedrock table) → What We Built (architecture diagrams, per-service detail) → What Worked → What Didn't Work → Decisions → Metrics → Next Week

**Workflow**:
1. Weekly: run `/bedrock-journal`
2. Skill reads previous entry for continuity, gathers PRs/tickets
3. "What Didn't Work" is enforced — most valuable section
4. INDEX.md auto-updated with topic grouping and chronological table

---

## pocs/

**Purpose**: Comparative experiments with qualifying numbers. Compare 2-3 methodologies objectively. Refine against specs in a loop until something becomes a feature.
**Skill**: `/write-poc`
**Template**: `pocs/POC_TEMPLATE.md`
**Naming**: `{topic-slug}.md`

**Structure**: Question → Methodologies (2-3 approaches) → Success Criteria (with thresholds) → Results Comparison Table (metrics per approach with winner) → Decision (backed by numbers) → Learnings → Next Steps

**Workflow**:
1. BEFORE experiment: run `/write-poc` to define Question + Success Criteria
2. Run the experiment, gather numbers
3. AFTER experiment: run `/write-poc --complete` to fill Results + Decision
4. If Go: run `/write-spec` to create implementation spec
5. If ambiguous: refine and re-test (POC ↔ Spec loop)
6. Never delete — even No-Go POCs have value

---

## Conventions

- File names: `kebab-case.md` for content, `UPPER_CASE.md` for templates
- YAML frontmatter required on all content files
- Link to Jira epic via `BH-XXX`
- One doc per feature, migration week, or POC
- Cross-reference via `related` frontmatter and Related section
- Dates in `YYYY-MM-DD` format
- Screenshots/assets in `features/assets/{feature-slug}/`
