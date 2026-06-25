# ADR — Spec-Driven Synthetic Warehouse as a Multi-Agent Capability Dashboard

> Status: proposed · Date: 2026-06-24 · Owner: BrightHive Platform

## Context

BrightHive ships a fleet of agents (retrieval, dbt+SV, governance, lineage, supervisor, deep-agent). Each agent has a contract and a ceiling, but the platform has no honest, comparable, reproducible measurement of those ceilings across niches. Demos rely on hand-curated data; evals rely on hand-curated cases; failures across agent boundaries are invisible.

A separate effort to build a synthetic-data generator for demos surfaced an opportunity: if we make the generator **spec-driven and deterministic**, with a hidden ground-truth oracle, the same artifact can drive demos *and* serve as the platform's first multi-agent capability dashboard.

We considered three designs:

- **v6.2 — single-agent test fixture.** Synth generator feeds the dbt+SV agent only; per-table eval; multi-table gaps deferred. Two days of work.
- **v7 — gap-as-finding.** Same as v6.2, but the eval keeps the spec rich and emits structured `GapFinding` records pointing at extension points in agent code. Roughly two and a half days.
- **v8 — multi-agent capability dashboard.** Synth generator feeds the entire agent fleet; eval scores per-agent and cross-agent dimensions; temporal dashboard tracks ceilings over time. Roughly four days.

## Decision

Adopt v8 as the target architecture; ship in stages.

| Stage | Scope | Estimated work |
|---|---|---|
| v0.1 | dbt+SV agent only, one pack (workforce_dev), DuckDB only, gap findings as JSON | 2 days |
| v0.2 | second pack (offshore_robotics) for niche elasticity; conversation corpus + supervisor scoring | +1 day |
| v0.3 | governance + lineage agents; cross-agent composition checks | +1 day |
| v0.4 | temporal dashboard (Notion + Slack); `runs.parquet` history | +0.5 day |
| v0.5+ | Snowflake/Redshift adapters via `seed_data/` extension; OSV conformance suite | +1-2 days |

v0.1 is essentially v6.2 in implementation but **shaped to the v8 contract** so subsequent stages are additive, not redesigns.

## Consequences

### What this enables

- **Niche elasticity is measurable.** "Does the platform generalize?" becomes a query against `runs.parquet`, not a slide.
- **Regression visibility.** Every agent change runs against the standing pack library; deltas surface immediately.
- **Roadmap auto-generation.** Low-scoring eval dimensions emit `GapFinding` records pointing at agent extension points; the synth pipeline becomes a roadmap source for the dbt+SV agent (and eventually all agents).
- **OSV conformance corpus.** The same packs validate the Open Semantic View standard across adapters.
- **Public benchmark path.** The internal dashboard is one fork away from a publishable benchmark for table-to-semantic-view agents.

### What this commits us to

- The pipeline must remain a **pure function** of `(spec, seed)`. No clock reads, no network calls, no host-specific behavior.
- The `DomainPackSpec` is an API surface. Breaking changes require a version bump and a migration path for existing packs.
- The eval harness must score honestly. Tuning packs to make agents look good defeats the purpose.
- Every new agent in the fleet implies a new eval dimension; agents shipped without spec-truth scoring will silently regress.

### What this rules out

- **Ad-hoc demo data.** Hand-curated synthetic data for one-off demos is allowed but does not inform the capability dashboard. It is parallel scaffolding.
- **LLM-judged structural checks.** Route correctness, entity match, governance decision are deterministic; LLM judges are reserved for free-text answer grounding.
- **Cross-pack inheritance in v0.x.** Each pack stands alone; pack-of-packs composition is post-v1.0.

### What we are explicitly accepting

- **The dbt+SV agent will fail relationship + cross-table-metric dimensions on day one.** This is the scaffold's known single-table ceiling; the design measures the gap rather than hiding it. Fixing it is a tracked extension, not a prerequisite.
- **Pack authoring is non-deterministic.** The LLM call to produce a `DomainPackSpec` is a one-shot author; the spec is then frozen. Drift between LLM versions does not affect already-frozen packs.
- **The standards-doc publication for OSV is gated on real cross-engine usage**, not the dashboard rollout.

## Alternatives considered and rejected

| Alternative | Why rejected |
|---|---|
| **Skip the synth pipeline; manually curate eval cases.** | Cannot scale to new niches; ceiling-tracking impossible across versions. |
| **Use the existing 22 generators in `brighthive-mock-data` as-is.** | Each generator invents its own schema; cross-pack queries impossible; no oracle. |
| **Build a Snowflake-only synth pipeline.** | Couples the dogfood to one engine; OSV conformance can't measure portability. |
| **Trim scope to per-table SV (v6.2 final).** | Hides the multi-table gap rather than measuring it; loses the roadmap-generator benefit. |
| **Auto-file Jira tickets from gap findings in v0.1.** | Premature; noise floor unknown. Defer to post-v0.4 once the eval has a track record. |

## Implementation plan (v0.1 → v0.4)

1. **v0.1 contracts.** Pydantic `DomainPackSpec`, `CapabilityReport`, `GapFinding` land in `brighthive-mock-data/canonical/spec/`. Frozen for v0.x.
2. **v0.1 pipeline.** `generate.py` emits the six artifacts in `./FLOWS.md`. DuckDB only.
3. **v0.1 eval.** New corpus dir `brightbot/evals/corpora/synth_warehouse/`. Scores entity / metric / PII / relationship-gap / cross-table-metric-gap dimensions.
4. **v0.1 first pack.** workforce_dev — small vocab, well-understood ground truth, exercises PII and segment paths.
5. **v0.2** adds offshore_robotics + conversation corpus + supervisor agent scoring.
6. **v0.3** adds governance + lineage agents + composition checks.
7. **v0.4** adds Notion + Slack rendering + `runs.parquet`.

## See also

- `./CAPABILITY_MAP.md` — architecture and rationale
- `./FLOWS.md` — flows + per-step contracts
- `agentic-project-mgmt/docs/specs/open-semantic-view.md` — OSV format
- `brightbot/agents/dbt_agent/tools/atlas_semantic_view/scaffold.py` — current agent contract (single-table)
