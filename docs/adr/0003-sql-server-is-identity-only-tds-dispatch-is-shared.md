# ADR-0003: SQL_SERVER is an identity-only warehouse type; TDS dispatch is shared

**Date:** 2026-08-19
**Status:** Accepted
**Who:** @drchinca (Kuri)
**Reviewed:** 2026-08-19 — independent non-author review, two passes: architecture (ACCEPT-WITH-FIXES) and product-voice/mission-coherence (COHERENT-WITH-FIXES). Both found real defects (actionability gap, cross-repo ambiguity, brand-casing, waypoint-calcification risk); all blocking items applied before this flip.

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
   `== "sql_server"`. Each `Warehouse` adapter *declares its own dialect/connection capability* via
   `capabilities()` (per Ports & Adapters PS-15) — T-SQL bracket quoting, the TDS connection — and
   call sites ask the adapter. Adding SQL Server is then registering an adapter, not editing 37
   branches — the end state has **zero name-branches**.

3. **Sequence — the urgent fix is not the refactor.** These are two efforts, not one, and bundling
   them is what stalls the fix:
   - **PR #1 (urgent, non-deferrable):** add the `sql_server` identity member to
     `warehouse_types.py:20` and fix the `lineage_refresh_task.py:95` hardcode. This alone closes the
     live Loop Capital wrong-answer bug (SQL Server → Redshift dialect). Small, isolated, ships now.
   - **The refactor (tracked separately):** move the 37 `azure_synapse` dispatch sites onto
     adapter-declared `capabilities()`. This is the doctrine's destination and gets its own tickets;
     it does not gate the bug fix.

This honors the Brighthive doctrine: wrap every vendor in the main concept (`Warehouse`), opt off
hardcoded/deterministic dispatch, and let the adapter/capability — agent- and DAG-resolvable —
decide. **Cross-repo, both codebases share one destination: capability-on-the-adapter.** Platform-core
already shipped the identity half under BH-1107; its `MSSQL_FAMILY_PROVIDERS` set is a valid *interim
mechanism*, not a divergent end state — TS simply started closer to the line. The two repos must not
permanently disagree on *mechanism* for the same concept: the family list is a waypoint on both sides,
never a second hardcoded list copied into Python and left there.

**Home:** identity member → BH-1370 (catalog-and-identity); the dispatch fall-through bug → BH-1168
(BUGS-V3). PR #1 and the capability refactor are separate children under those epics — creating the
child tickets is a Jira mutation held for sign-off, so this ADR names the epics rather than inventing
ticket IDs.

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
  mislabeled until re-run; the fix stops new mislabels but does not rewrite history. Until re-run,
  those graphs should be **surfaced as suspect** (flagged "engine label predates the fix"), not shown
  as confidently correct — silent-but-wrong provenance is the one honesty seam this decision leaves
  open, and it closes on re-run, not on deploy.
- **The waypoint tends to stick — name it, don't wish it away.** The most likely real-world failure
  is: ship the interim family list, never fund the capability refactor, and you have institutionalized
  the per-name determinism the doctrine opts off. This is temporary debt, not a fix. Its only offramp
  is the tracked refactor ticket under BH-1168; without that ticket funded, the "waypoint" silently
  becomes the destination. The family list buys correctness today at the cost of a debt someone must
  retire — say so, so the retirement is a plan, not a hope.

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
- **Stop at the family set as the *permanent* endpoint (rule-of-two).** Fairly considered, not
  dismissed: with exactly two TDS providers whose T-SQL is byte-for-byte identical, `pluggable-scalable`'s
  own rule-of-two says a frozenset can be enough until a third appears — an abstraction lands on the
  *second* real implementation, and here both already exist. So this is defensible *for this narrow
  case*. We still set the direction to capability-on-the-adapter because the 37 sites are already the
  cost the doctrine warns about, and because capability negotiation is what lets a *future* TDS-family
  member (or a dialect quirk between Synapse and on-prem SQL Server) be a config change, not a 38th
  branch. The honest resolution: capability is the direction; consciously stopping at the frozenset is
  a permitted rule-of-two call the refactor ticket can make with evidence — never a silent drift into it.
