---
title: "Same answers on every warehouse engine"
epic: "BH-1168"
owner: "drchinca"
status: "Draft"
created: "2026-08-18"
supersedes:
  - engineering-agent-warehouse-agnostic.md
  - on-prem-sql-server-warehouse.md
  - lineage-adapter-sql-server.md
  - quality-rules-synapse-table-quoting.md
  - warehouse-extensibility-pattern.md
  - table-parity-verb.md
  - table-parity-cross-warehouse-database.md
  - analyst-query-dialect-hint.md
reference:
  - warehouse-agnostic-architecture.md   # the engine-onboarding rule — keep, don't archive
---

# Same answers on every warehouse engine

> Delegation unit. Cap 150 lines.

## The goal

Reading data, writing models, tracing lineage, and running quality checks behave identically
whether the customer is on SQL Server, Synapse, Snowflake, Redshift, or Databricks. Adding the
next engine is a config entry, not a code change. Today several of these silently work on one
engine and silently misbehave on another.

## Why now

Quality checks on Synapse **check a sample instead of the whole table**, because we don't wrap
table names the way Synapse requires. The customer gets a quality result that looks fine and is
wrong — the worst kind of bug, because nothing fails or warns. Separately, the agent can only
write models to Redshift, so a SQL Server customer silently gets read-only behaviour and no
explanation of why.

## What to build

1. `brightbot` — fix the Synapse table-name wrapping so quality checks scan the real table instead
   of a sample. This is a correctness bug, not a feature; do it first. The same wrapping bug also
   makes analyst queries pick the wrong dialect — one fix, both symptoms
   (`analyst-query-dialect-hint.md` is the second half of this).
2. `brightbot` — let the engineering agent write on engines other than Redshift. **This theme owns
   the write path**; [Always know which warehouse you're talking to](THEME-catalog-and-identity.md)
   defers it here. Scope it to the writes the agent already performs on Redshift today — creating
   and replacing models — and no more. **Decide and record:** whether this reuses the existing
   connection classes per engine or needs one shared write interface. Recommendation: start with
   the existing per-engine connections and only extract a shared one when the second engine
   actually forces it.
3. `brightbot` — lineage extraction for SQL Server / Synapse, behind the same lineage provider
   the other engines use.
4. `brightbot` — resolve what `SQL_SERVER` *is* (see the decision below) and make
   `warehouse_type_from_secret()` match that answer everywhere.
5. `brightbot` — table parity across engines: compare a table in one warehouse to a table in
   another and report schema, row-count, and value differences honestly, including when the two
   engines' types aren't directly comparable.
6. Confirm the onboarding rule still holds — adding an engine touches only its registry entry and
   config, never engine-neutral code. The rule is written in `warehouse-agnostic-architecture.md`
   (BH-172, Approved), which stays as the reference. If any of items 1–5 forced an edit to
   engine-neutral code, that's a defect in the rule — fix it there too.

## Done when

- [ ] A quality check on a Synapse table scans the full table; a test proves it no longer samples
- [ ] The engineering agent writes a model successfully on a non-Redshift engine
- [ ] Lineage appears for a SQL Server source in the same graph as a dbt/Snowflake source
- [ ] `SQL_SERVER` resolves to one answer, and every caller agrees — no path disagrees
- [ ] Table parity reports a real difference between two engines, and says clearly when types
      can't be compared rather than guessing
- [ ] Real-behavior tests on **two real engines** — SQL Server (the local Docker sandbox from
      [Work where the customer's data lives](THEME-onprem-engineering.md)) and Snowflake (the
      existing staging connection). If CI can't reach both, that's a CI gap to fix, not a reason
      to drop to mocks

## Don't do

- **A second engine port.** `PipelineRunner` in `pipelines/core/port.py` is the real one; two
  other specs describe ports that don't exist in code. Don't add a third.
- **Warehouse health, staleness, and connectivity** — owned by
  [Warehouse health you can trust](THEME-warehouse-health-truth.md).
- **Catalog browsing, database nodes, and default resolution** — owned by
  [Always know which warehouse you're talking to](THEME-catalog-and-identity.md).
- **New engines nobody has asked for** (Oracle, BigQuery). The playbook makes them cheap later;
  building them now is speculative.
- **The full 7-layer integration audit per engine.** Snowflake's shipped and Synapse's is a stale
  April draft that still names the deprecated Datapiary as a dependency. Read them as history.

## Where it lives

| Repo | What changes |
|---|---|
| `brightbot` | dialect quoting, cross-engine write path, lineage provider, parity verb |
| `brighthive-platform-core` | warehouse-type resolution consistency |
| `brighthive-e2e` | two-engine correctness tests |

**Tickets:** BH-1168 (epic), BH-1320, BH-1121, BH-1036

---

## ⚠️ Decision 3 in [THEMES.md](THEMES.md) — settle before code starts

**Is `SQL_SERVER` its own `WarehouseType`, or an alias for `azure_synapse`?** Three specs written
within two weeks answer differently:

- `lineage-adapter-sql-server.md` writes its invariant assuming SQL-Server-shaped secrets route to
  a provider whose `engine == "azure_synapse"`.
- `engineering-agent-warehouse-agnostic.md` has a scenario where the type *is* `SQL_SERVER` but it
  connects via `SynapseConnection` — implying the type already resolves.
- `on-prem-sql-server-warehouse.md` states flatly that no `sql_server` member exists today and
  proposes adding one, changing `warehouse_type_from_secret()` so SQL Server no longer maps to
  `azure_synapse`.

If the third ships, the first one's invariant **breaks silently** — no error, just wrong routing.
This needs a written ADR before item 4, and items 1–3 should assume its outcome rather than
guessing. Recommendation: give SQL Server its own type. Loop Capital is on real SQL Server, not
Synapse, and the platform already tells customers "you're connected to Azure Synapse" when they
aren't — which one customer has already pushed back on.
