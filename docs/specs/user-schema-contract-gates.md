---
title: "User Schema Contracts as Enforcement Gates — input/output validation for transformations, analysis, visualization, joins"
epic: "BH-624"
author: "drchinca"
status: "Draft"
created: "2026-06-24"
last_reviewed: "2026-06-24"
generates: "tickets"
tags: [schema, data-contract, target-schema, governance, enforcement, transformations, joins, brightbot, platform-core]
related:
  features: []
  pocs: []
  bedrock: []
---

# User Schema Contracts as Enforcement Gates

## Terminology (canonical — used throughout this spec)

Two distinct concepts the platform (and prior analysis) repeatedly conflated. This spec pins names:

- **`OMDSchemaTable`** — the OpenMetadata-derived structure of a *real warehouse table*: its physical columns and types. Bound 1:1 to a `DataAsset`. Surfaced via `DataAsset.fields`. Answers "what columns exist in table X". **Out of scope here** (introspection already works).
- **`StandaloneSchemaWorkspace`** — a *user-authored JSON Schema contract*, created at will on the catalog Schemas page. NOT bound to any table; abstract, workspace-level. Surfaced via `Query.schemas` → `TargetSchema.jsonSchema` (a String) with `SchemaType { INPUT | OUTPUT }`. Answers "what shape must data conform to". **This spec is about these.**

| | `OMDSchemaTable` | `StandaloneSchemaWorkspace` (this spec) |
|---|---|---|
| Source | OpenMetadata — physical columns of a real table | User-authored JSON, catalog Schemas page |
| Bound to a table? | Yes — it *is* the table's structure (`DataAsset.fields`) | **No** — standalone, workspace-level, abstract |
| Purpose | "what columns exist in table X" | A **contract** to validate input/output against |
| GraphQL | `DataAsset.fields` (from OMD) | `Query.schemas` → `TargetSchema.jsonSchema` (String) |

## Problem

A user can author **`StandaloneSchemaWorkspace`** contracts on the catalog Schemas page (`Query.schemas` → `TargetSchema`, `SchemaType { INPUT | OUTPUT }`) — e.g. "CRM Tickets Schema", "Customer360 Target Schema", "HL7 Data Contract for Ingest". The intent — visible in the data model itself (`SchemaType` has `INPUT`/`OUTPUT`; `WorkflowInputDataAssetGroup.targetSchema`) — is that these contracts **gate** operations: a transformation's input must conform to an INPUT schema, its output to an OUTPUT schema, etc.

**Today nothing enforces them.** No agent operation — transformation, analysis, visualization, or join — accepts a `StandaloneSchemaWorkspace` as an input/output gate and validates against it. The contracts are decorative catalog entries: created, versioned, described, and then ignored at execution time. This is the same "created but never applied" gap as governance policies (BH-766), but for the structural data contract.

A `StandaloneSchemaWorkspace` is deliberately NOT an `OMDSchemaTable`: it does not describe an existing table, it prescribes a shape that inputs/outputs must satisfy. Table-schema introspection (`OMDSchemaTable`) is a separate, already-working concern.

## Use Case / Goal

A user (or another agent) can bind a named `StandaloneSchemaWorkspace` to any of four operation types:

- **Transformation**: "Build a dbt model whose output conforms to the *Customer360 Target Schema*." → the generated/validated output columns+types must satisfy the OUTPUT contract; the source must satisfy the INPUT contract.
- **Analysis / query**: "Answer this, and return a result matching the *CRM Tickets Schema*." → result columns+types validated against the contract; loud, precise failure on mismatch.
- **Visualization**: "Chart this, expecting fields per *<schema>*." → the chart's input frame is validated against the contract before rendering.
- **Join**: "Join A and B and produce output conforming to *<schema>*." → the joined projection is validated against the OUTPUT contract.

Success = binding a `StandaloneSchemaWorkspace` to any of the four operations produces a **deterministic conformance verdict** (pass, or a precise diff of missing/extra/mismatched columns), and the operation refuses-or-flags on mismatch rather than silently returning non-conforming data.

## Current Situation

### How It Works Today

- Contracts exist: `Query.schemas(schemaId)` returns workspace `TargetSchema`s with `jsonSchema` (String), `status`, `versionNumber`, `types: [SchemaType]` (`INPUT`/`OUTPUT`). The model already links a contract to a transformation group (`WorkflowInputDataAssetGroup.targetSchema`).
- The agent can *list* them via `fetch_workspace_schemas` (`brightbot/tools/governance_context_tools.py:45`). BH-774 just fixed that tool to actually surface the field names (it was dropping them — a prerequisite for any enforcement).
- **No operation consumes a contract as a gate.** SQL generation (`get_sql_generation_prompt`), the analyst result evaluator (subjective "does this answer the question?"), the visualization tool, and dbt model generation all run without reference to any user schema.

### Hard Limitations

- No `schema_contract` parameter on any agent operation (transform / analyze / visualize / join).
- No conformance validator: nothing compares a result's columns+types to a `TargetSchema.jsonSchema`.
- INPUT vs OUTPUT typing (`SchemaType`) is stored but never consulted.
- `jsonSchema` is a raw String blob — no shared parser/typed model for "contract → expected columns+types".

### Gaps

1. No way to *address* a contract by name/id in a request ("using schema X").
2. No conformance check (columns present, types compatible, required fields, extra-column policy).
3. No INPUT-gate (validate source) vs OUTPUT-gate (validate result) distinction at execution.
4. No refuse/flag behavior on mismatch — operations would silently emit non-conforming data.

## Proposals / Solutions

### Recommended Approach

A single **contract-gate primitive**, reused across all four operations, shipped in slices (feature-flagged):

1. **Contract resolver + typed model (S).** `resolve_standalone_schema(name_or_id)` → fetch the `StandaloneSchemaWorkspace` (`TargetSchema`), `json.loads` the `jsonSchema` (BH-774 made this readable), produce a typed `SchemaContract(name, version, kind: INPUT|OUTPUT, fields: {name: type, required})`. One parser, reused everywhere. (Distinct from `OMDSchemaTable` introspection, which stays as-is.)

2. **Conformance validator (M).** `validate_conformance(columns_with_types, contract) → ConformanceVerdict(conforms, missing, extra, type_mismatches)`. Pure, dialect-aware type compatibility (warehouse type ↔ JSON Schema type). Deterministic — no LLM.

3. **Bind to analysis/query (M).** Optional `output_schema` (name/id) on the analyst/retrieval path. After execution, validate result columns+types; on mismatch return the verdict diff and refuse-or-flag (don't silently return non-conforming rows). For generation, inject the OUTPUT contract's expected columns into the SQL-gen prompt as the target projection.

4. **Bind to transformation (M).** dbt model generation accepts INPUT + OUTPUT contracts: validate source columns against INPUT, constrain/validate generated model output against OUTPUT. Leverages the existing `WorkflowInputDataAssetGroup.targetSchema` link.

5. **Bind to visualization + join (S each).** Visualization validates its input frame against a contract before rendering; join validates the joined projection against the OUTPUT contract. Both reuse slices 1–2.

Joins specifically: where join *keys* come from is a related but separate concern (declared relationships / semantic-view `relationships:`) — tracked in its own ticket; this spec governs the *output contract* of the joined result, not the join-key inference.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| LLM-judged conformance ("does this look like the schema?") | No validator code | Non-deterministic; the whole point is a hard gate | Conformance must be deterministic |
| Enforce only at transformation (the modeled link) | Smallest | Leaves analysis/visualization/join ungated — the user asked for all four | Build the reusable primitive once, bind to all four |
| Per-operation bespoke validation | Fast first cut | Four divergent implementations, drift | One `validate_conformance`, reused |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Agent tooling | `brightbot` | Contract resolver + typed model; conformance validator; bind to analyst/retrieval, dbt, visualization, join |
| Prompts | `brightbot` | Inject OUTPUT contract's expected columns into SQL-gen; analyst honors refuse-on-mismatch |
| Platform Core | `brighthive-platform-core` | (Likely none — `Query.schemas` + `TargetSchema.jsonSchema` already expose contracts; possibly a typed accessor later) |
| Prereq | `brightbot` | BH-774 (agent can read schema field names) — DONE |

## Acceptance Criteria

- [ ] A request can name a user schema contract ("using schema X") and the resolver returns its typed fields+types.
- [ ] An analysis bound to an OUTPUT contract validates result columns+types and returns a precise conformance diff; on mismatch it refuses-or-flags rather than returning non-conforming rows.
- [ ] A transformation validates source against an INPUT contract and output against an OUTPUT contract.
- [ ] Visualization and join operations can each be bound to a contract and validated.
- [ ] Conformance is deterministic (no LLM) and dialect-aware for type compatibility.
- [ ] All gating is feature-flagged (off by default).

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| BH-774 — fetch_workspace_schemas surfaces field names | Blocking | DONE (PR #720) |
| `Query.schemas` / `TargetSchema.jsonSchema` (platform-core) | Non-blocking | Ready |
| Join-key inference (declared relationships) | Non-blocking (separate) | Not started |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | Schema-contract resolver + typed SchemaContract model (parse TargetSchema.jsonSchema) | 3 | BH-624 |
| — | Deterministic conformance validator (columns/types, INPUT/OUTPUT, dialect-aware) | 5 | BH-624 |
| — | Bind OUTPUT contract to analysis/query: validate result + refuse-on-mismatch | 5 | BH-624 |
| — | Bind INPUT/OUTPUT contracts to dbt transformation generation | 5 | BH-624 |
| — | Bind contract gates to visualization + join output | 3 | BH-624 |

## Related

- **Prereq fix**: BH-774 (PR #720) — agent can now read catalog-schema field names.
- **Related (separate)**: join-key inference from declared relationships / semantic-view `relationships:`.
- **Sibling gap**: BH-766 governance-policy enforcement — same "created but never applied" pattern, different artifact.
- **Standard**: `platform-saas-ai-context/docs/standards/open-semantic-view.md` (PR #26).
