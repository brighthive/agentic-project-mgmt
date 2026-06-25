# Open Semantic View (OSV) — Warehouse-Agnostic by Design

> Status: draft · Owner: BrightHive Platform · Last reviewed: 2026-06-24

## TL;DR

BrightHive's Semantic View (SV) YAML is an **open, engine-neutral standard** — not a Snowflake feature. It describes *what tables mean* (entities, dimensions, metrics, relationships, retrieval hints) independent of the warehouse that stores the data. Snowflake Semantic Views are one possible *backend binding*, not the format itself.

## Why this matters

BrightHive is platform- and warehouse-agnostic by mandate. The semantic surface is one of two canonical retrieval modes the platform offers; tying it to one engine breaks that promise on the most strategic surface.

| Surface | Strength |
|---|---|
| Vector embeddings | "things that read similar" — fuzzy, lossy, no joins |
| **Semantic structure (OSV)** | "what this table *is* — entities, dimensions, metrics, FKs" — exact, queryable, joinable |

Both must work across every warehouse BrightHive supports — Snowflake, Redshift, BigQuery, Postgres, DuckDB, Iceberg/Glue.

## Scope

**The OSV YAML carries:**
- Entities (logical tables) and their primary/natural keys
- Dimensions, with type + value domain
- Metrics, with grain + expression + unit + positive direction
- Relationships (FK graph) with cardinality hints
- PII / sensitivity tags + governance policy references
- Retrieval hints (intent → metric/dimension mapping for LLM grounding)

**The OSV YAML must NOT carry:**
- Engine-specific DDL syntax (`VARIANT`, `SUPER`, Snowflake `CREATE SEMANTIC VIEW` clauses)
- Vendor-specific dialect inside metric expressions where a portable form exists
- Physical storage details (clustering keys, compression, partition specs)

These belong in **adapters**, not in the canonical format.

## Adapter strategy

```
                       ┌────────────────────────┐
                       │  canonical OSV YAML    │
                       │  (engine-neutral)      │
                       └───────────┬────────────┘
                                   │
        ┌────────────┬─────────────┼─────────────┬───────────────┐
        ▼            ▼             ▼             ▼               ▼
   Snowflake     dbt MetricFlow  Cube.dev    LookML        Iceberg/Trino
   Semantic       semantic_models  cubes:    explores      glue catalog
   Views                                                    + dbt sl
```

Adapters are *lossy in one direction* — they emit engine-native artifacts from canonical OSV. They do not need to round-trip; canonical OSV is the source of truth.

## Where the format lives

| Concern | Location |
|---|---|
| Format spec (this doc + JSON Schema) | `agentic-project-mgmt/docs/specs/open-semantic-view.md` |
| Canonical Pydantic models | `brightbot/agents/dbt_agent/tools/atlas_semantic_view/` |
| Adapters (one module per backend) | `brightbot/agents/dbt_agent/tools/atlas_semantic_view/adapters/` |
| Conformance tests | `brightbot/evals/corpora/synth_warehouse/` (via the synth pipeline) |

## Implementation guidance

When extending OSV-related code:

- **The YAML schema is the API.** Engine-specific fields require an adapter, not a YAML extension.
- **`ScaffoldResult.yaml` must validate as canonical OSV** — no Snowflake-isms in entity/dimension/metric definitions. If the agent leaks engine syntax, that's a bug.
- **`SilverSchema` ingestion is one input shape, not the only one.** OSV must be authorable from any catalog source — `INFORMATION_SCHEMA`, Iceberg metadata, dbt manifest, Glue, OpenMetadata.
- **Engine couplings live in adapter layers.** `VARIANT`, `SUPER`, `JSON_PARSE`, `SEMANTIC VIEW` keywords in OSV-adjacent code are pry-points to push down into adapters.
- **Conformance tests assert engine-neutrality.** Canonical OSV must validate against at least two non-Snowflake adapters (DuckDB info_schema + dbt MetricFlow at minimum) without dropping entities or metrics.

## Conformance via the synthetic-warehouse pipeline

The synthetic-warehouse capability map (`agentic-project-mgmt/docs/pocs/synth-warehouse/CAPABILITY_MAP.md`) doubles as the OSV conformance test corpus:

- Each pack's `spec_truth.json` declares the canonical OSV the agent should produce.
- The eval harness scores agent SV YAML against canonical OSV directly, in a structural diff.
- Each pack runs through every adapter that claims support; missing entities, metrics, or relationships fail the conformance check.
- New niches automatically extend the conformance suite — no hand-curated test set.

This is how OSV avoids the "works on Snowflake, untested elsewhere" trap. Every adapter release must clear the same multi-pack conformance bar.

## Roadmap to a published spec

1. **v0.x** — internal: format stabilizes inside `atlas_semantic_view/`. The dbt+SV agent emits canonical OSV; adapters live alongside.
2. **v0.y** — at least two non-Snowflake adapters in production (DuckDB conformance + dbt MetricFlow), validated by the synth-warehouse conformance corpus.
3. **v1.0** — extract format spec + JSON Schema to its own surface (this doc → `specs/open-semantic-view/spec.md` + `schema.json`); publish externally as **BrightHive Open Semantic View**.

The v1.0 cut is gated on real cross-engine usage, not a calendar date.

## Anti-patterns

- **Snowflake fields creeping into the canonical YAML.** Push down into the Snowflake adapter.
- **"It works for Snowflake" as evidence the format is portable.** Portability is proven by a non-Snowflake adapter passing the same conformance suite.
- **Treating canonical OSV as a translation target.** It is the source. Engine artifacts derive from it, not the reverse.
- **Engine-specific retrieval hints.** Hints stay portable; engine-specific tuning is an adapter concern.

## See also

- `agentic-project-mgmt/docs/pocs/synth-warehouse/CAPABILITY_MAP.md` — the dogfood pipeline that doubles as OSV conformance
- `agentic-project-mgmt/docs/pocs/synth-warehouse/FLOWS.md` — flows + per-step contracts
- `agentic-project-mgmt/docs/pocs/synth-warehouse/ADR.md` — decision record
- `brightbot/agents/dbt_agent/tools/atlas_semantic_view/scaffold.py` — current canonical implementation
