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

**`SQL_SERVER` is its own identity member. It is never its own dispatch branch. Every place that
switches on dialect/connection routes both `SQL_SERVER` and `AZURE_SYNAPSE` through one TDS family
set — never a bare equality on either name.**

This ratifies the choice platform-core already shipped under BH-1107 and extends the same pattern
into brightbot's Python, where it is currently missing.

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

**A family set makes the sweep mechanical, not 37 judgment calls.** `grep -rn azure_synapse
brightbot --include='*.py'` returns **37 sites** (dialect branches at `table_name_utils.py:74`,
the internal-engine list at `warehouse_catalog.py:48`, and the rest). Routing them through a shared
`MSSQL_FAMILY`/`TDS_FAMILY` frozenset — mirroring the TypeScript name already in production — turns
a 37-site rename into one constant plus call sites that read `provider in TDS_FAMILY`. Zero behavior
change for Synapse; the SQL Server fall-through closes.

## The Cost

- **A cross-repo naming commitment.** `SQL_SERVER`/`sql_server` is now a real, permanent member on
  both sides. Dropping it later means another 37-site sweep — this is the kind of choice ADR-0001
  got wrong by conflating layers, so we name the layers explicitly here.
- **A migration touch, not a redesign.** The 37 Python sites must move to the family set in one pass;
  a half-done sweep leaves the exact "only checks one name" bug the platform-core comment warns
  about. It ships as a single change, not incrementally.
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
