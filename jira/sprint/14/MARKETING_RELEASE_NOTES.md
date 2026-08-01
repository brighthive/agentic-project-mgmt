# Sprint 14 🍯 — What Shipped (July 21 – Aug 1, 2026)

The sprint that made the platform **honest about the state of your warehouses** —
and gave every pipeline a lineage you can see, re-run, and trust.

---

## 🩺 Your warehouse's real health, on the home screen

The landing page no longer just says "connected." A background watchdog now folds
each warehouse's **operational health** — disk pressure, failed nightly jobs, the
name of the step that broke — into the health band you see first. The rule is
**worst-of, never optimistic**: a warehouse that's connected but out of disk shows
as impaired, not green. Works the same across SQL Server, Snowflake, and Redshift —
no engine gets special treatment. *(Kuri)*

## 🧬 Pipeline lineage you can see and re-run

Every pipeline now carries a **6-tier medallion lineage** you can open on the project
observability page — where the data came from, what transformed it, where it landed.
Tiers are derived from the pipeline's declared structure, not guessed from table names.
And when one node fails, you can **re-run from that node** without replaying the whole
chain — each run is versioned and immutable. *(Kuri)*

## 🔌 The MCP tool layer, hardened against real customer warehouses

Thirteen fixes drove the warehouse and pipeline tools against a real production-test
Redshift workspace until they stopped lying: hyphenated database names now parse,
Redshift Spectrum external tables are no longer invisible, slow analyses degrade to an
honest "pending" instead of a 120-second timeout, and a missing argument returns a clear
"bad request" instead of a generic "internal error." A new tool surfaces **BrightSignals
alert history** so agents can see what's been flagged. *(Kuri)*

## 🧹 The product surface, cleaned up end to end

The long tail of "small things that make a product feel unfinished" — cleared in one
sweep. Real toggle switches replacing fake ones, correct write-mode labels, the missing
"JSON Schema" tab on Projects, a Tags field on file uploads, aligned field-label casing,
and a real file-type detection bug fixed behind a cosmetic-looking ticket. Project
creation is now **atomic** — it either completes cleanly or rolls back, no orphaned
projects left behind. *(Harbour)*

## 📄 Bring your own schema files

Projects now accept **XSD/XML schema files** — upload them, store them, read them back,
and edit them in place with a dedicated editor. A clean vertical slice from the GraphQL
layer through to the Project Files UI. *(Marwan)*

## 🧠 Sharper knowledge-base answers

The knowledge base now **reranks** its retrieval for precision, agents are grounded to
cut hallucination, and file-scoping works correctly across every graph alias. *(Harbour)*

---

## 📊 By the numbers

- **82 PRs merged** across 5 repositories
- **28 tickets resolved** (27 delivered, 1 investigated and retired)
- **+41,813 / −4,316** lines of authored code (release re-merges excluded)
- **3 engineers**: Kuri, Harbour, Marwan

## 🌟 Team

- **Kuri** carried the sprint's three backbone initiatives end-to-end — warehouse health,
  engine-agnostic lineage, and the MCP hardening sweep — plus the release train that
  shipped them to staging and prod. 57 PRs, 69.5% of the sprint.
- **Harbour** owned the product-surface quality: 11 catalog/projects UX fixes, atomic
  project creation, and knowledge-base retrieval precision.
- **Marwan** delivered the schema-file intake slice — upload, store, read, edit — across
  backend and frontend.

## ⚠️ Sprint health

- **Fourth unofficial (date-range) sprint in a row.** A formal Jira sprint object is
  overdue — it would make completion %, carry-over, and velocity real instead of
  reconstructed.
- **Authorship concentration** sits at ~70% on one engineer, consistent with last sprint.
- **10 tickets in flight**, all on the default-warehouse ingestion path and the
  unstructured-data stack — the priorities carrying into Sprint 15.
