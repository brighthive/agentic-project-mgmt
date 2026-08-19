# ADR-0003: SQL_SERVER is an identity-only warehouse type; TDS dispatch is shared

**Date:** 2026-08-19
**Status:** Proposed
**Who:** @drchinca (Kuri)

## The Problem

Loop Capital connects a Microsoft SQL Server. We have to answer one question consistently across
two codebases: **is `SQL_SERVER` its own warehouse type, or an alias for `azure_synapse`?** Both
speak the same TDS wire protocol and the same T-SQL dialect, so the temptation is to fold them into
one. But the two layers that ask the question want different answers, and today they disagree.

- **Identity** (what the customer connected, shown in the UI/OMD service type) wants them
  **distinct** — a Loop Capital admin who connected SQL Server should not see "Azure Synapse".
- **Dispatch** (which SQL dialect, which quoting, which connector) wants them **the same** — the
  bracket-quoting and TDS connection are identical, so branching on two names doubles every case.

The roadmap flagged this as the one genuinely-open decision. Verifying it against code shows it is
**already decided on one side and unmade on the other**, which is the real hazard.

## Our Decision

**`SQL_SERVER` is a member of the one `Warehouse` concept — never a bespoke per-vendor service,
never a hardcoded literal branch.** Two parts:

1. **Identity is explicit.** `SQL_SERVER` is its own `Warehouse` member so the UI/OMD reflects what
   the customer actually connected.
2. **Dispatch is resolved, not branched.** No call site switches on `== "azure_synapse"` or
   `== "sql_server"`. Each `Warehouse` adapter *declares its own dialect/connection capability*
   (T-SQL bracket quoting, the TDS connection), and call sites ask the adapter. Adding SQL Server is
   then registering an adapter, not editing 37 branches — the end state has **zero name-branches**.

This honors the BrightHive doctrine: wrap every vendor in the main concept (`Warehouse`), opt off
hardcoded/deterministic dispatch, and let the adapter/capability — agent- and DAG-resolvable —
decide. Platform-core already shipped the identity half under BH-1107; its `MSSQL_FAMILY_PROVIDERS`
set is a valid *waypoint*, but the endpoint is capability-on-the-adapter, not a second hardcoded
family list copied into Python.

## Why This Choice

**Platform-core already made this exact call, correctly, and it works.** `SQL_SERVER` is a distinct
enum value at `warehouse-provider-typedefs.ts:23`, and the file's own comment (`:8-13`) states why:
it exists *"so the UI/OMD service type accurately reflects what the user connected, while the
underlying [protocol is shared]."* The dispatch side is handled by a family set, not duplicated
branches — `warehouse-provider-mapping.ts:22`:

```ts
/** Provider values that share the Mssql/TDS connection + dialect shape. */
export const MSSQL_FAMILY_PROVIDERS = ["AZURE_SYNAPSE", "SQL_SERVER"] as const;
```

Its comment (`:7-12`) describes the precise failure the family set prevents: *"a caller matching
… only `AZURE_SYNAPSE` … a workspace whose only warehouse is `SQL_SERVER` (e.g. Loop Capital) fails
every lookup."* That is the pattern. The decision on the identity/wire boundary is not open — it is
shipped and load-bearing for a live customer.

**Brightbot's Python side never got the member — and that is worse than an alias.** `warehouse_types.py:20`
is `Literal["redshift", "snowflake", "azure_synapse", "postgres", "databricks"]` — there is no
`sql_server` at all. So an unnormalized `sql_server` string does not collapse cleanly to Synapse; it
**matches no literal and falls through to the default**, which two call sites document in place:
`retrieval_agent/tools.py:471` — *"'sql_server', which is not a valid literal → the LLM gets
Redshift"* — and `metadata_retrieval.py:41` notes the same drop. A SQL Server workspace silently
getting **Redshift** dialect is a wrong-answer bug, not a cosmetic one.

Adding the identity member is safe where it matters most: lineage provider selection keys on the
**raw** secret type, so it survives a new member untouched. The one label that breaks is the
hardcode at `lineage_refresh_task.py:95` (`engine = "azure_synapse"`), which today files *every*
Loop Capital lineage graph under Synapse regardless of what was connected. Fixing that is part of
this decision, not a separate one.

**Resolving via the adapter kills the name-branches instead of adding another.** `grep -rn
azure_synapse brightbot --include='*.py'` returns **37 sites** (dialect branches at
`table_name_utils.py:74`, the internal-engine list at `warehouse_catalog.py:48`, and the rest). The
doctrine-aligned fix lets the `Warehouse` adapter own its dialect and has those sites ask it — so
SQL Server is a registered adapter, not a 38th literal. A shared `TDS_FAMILY` frozenset (mirroring
platform-core's shipped `MSSQL_FAMILY_PROVIDERS`) is the pragmatic first hop *if* the full
adapter-capability refactor is too large for one PR — but it is a waypoint, not the destination:
copying a hardcoded family list into Python is the very per-name determinism we opt off. Either way,
Synapse behavior is unchanged and the SQL Server fall-through-to-Redshift closes.

## The Cost

- **A cross-repo naming commitment.** `SQL_SERVER`/`sql_server` is now a real, permanent member on
  both sides. Dropping it later means another 37-site sweep — this is the kind of choice ADR-0001
  got wrong by conflating layers, so we name the layers explicitly here.
- **A migration touch, not a redesign.** The 37 Python sites move to adapter-resolved dialect (or,
  as a waypoint, one family set) in a single pass; a half-done sweep leaves the exact "only checks
  one name" bug the platform-core comment warns about.
- **The dialect contract stays deterministic *inside* the adapter.** "Resolve, don't branch" is
  about routing, not correctness — T-SQL bracket quoting is a fixed fact the adapter owns, never an
  LLM guess. The agent/DAG picks *which* adapter; the adapter guarantees the SQL is right.
- **Lineage backfill.** Graphs already written under `azure_synapse` for a SQL Server workspace stay
  mislabeled until re-run; the fix stops new mislabels but does not rewrite history.
- **One more member for every future dialect switch to remember.** Mitigated by the family set:
  new code branches on the set, so forgetting `SQL_SERVER` specifically becomes hard by construction.

## Alternatives We Considered

- **Alias `sql_server` → `azure_synapse` at the edge, no new Python member.** Rejected: it keeps the
  UI honest only if the collapse happens *after* identity is captured, and it leaves the two
  codebases disagreeing (platform-core has the member, Python doesn't). Every engineer who reads one
  side and not the other reintroduces the fall-through.
- **Give `SQL_SERVER` its own dispatch branches everywhere.** Rejected: doubles 37 sites' worth of
  dialect logic that is byte-for-byte identical to Synapse, and guarantees the two drift.
- **Leave Python as-is (default fall-through).** Rejected: a SQL Server workspace silently getting
  Redshift dialect is a live correctness bug for Loop Capital, documented in the code comments
  themselves.
