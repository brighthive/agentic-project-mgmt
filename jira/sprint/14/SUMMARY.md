# Sprint 14 🍯 — Per-Person Summary (July 21 – Aug 1, 2026)

> **Unofficial, date-range cut.** No Jira sprint object exists for this window — the
> last release was Sprint 13 (🧵, July 20). This is the **fourth unofficial sprint in
> a row** (11–14). Opening a formal Jira sprint object is overdue.
>
> This summary is organized **per person** — Kuri first, then one section per engineer.

```
┌──────────────────────────────────────────────────────────────┐
│  SPRINT 14 🍯  —  Warehouse Health, MCP Hardening, Lineage     │
│  July 21 – Aug 1, 2026  (12 days)                              │
├──────────────────────────────────────────────────────────────┤
│  PRs merged .............................. 82                  │
│    · code PRs ............................ 62                  │
│    · release / promotion PRs ............. 20                  │
│  Tickets resolved ........................ 28 (27 Done, 1 ✗)   │
│  Tickets in flight ....................... 10                  │
│  Repos touched ........................... 5                   │
│  Code lines (excl. release re-merges) .... +41,813 / −4,316    │
│  Team .................................... Kuri, Harbour, Marwan│
└──────────────────────────────────────────────────────────────┘
```

**Reading the line counts:** raw merged-line totals are dominated by 20
release-promotion PRs (`chore(release)` / `Develop => Staging`) that re-merge an
entire branch — one of them alone shows +262k. Every number below is
**code-only** (release/promotion PRs excluded) so it reflects work authored, not
branches re-shipped.

---

## 🌟 Kuri (drchinca) — *the through-line of the whole sprint*

**57 PRs** · 41 code + 16 release · **+38,402 / −3,556** code lines · **5 repos**
(platform-core 31, webapp 17, apm 6, platform-saas-ai-context 2, e2e 1) ·
**69.5% of all PRs merged this sprint** · **15 tickets Done, 10 carried in flight**

Kuri owned the sprint's three backbone initiatives end-to-end — backend, frontend,
tests, docs, and the release train that shipped them to staging and prod.

**1. MCP prod-test hardening — a 13-fix sweep (BH-1181 family).**
Every warehouse/pipeline MCP tool was driven against a real prod-test Redshift
workspace and the failures fixed one by one:
- Hyphenated Redshift DB names rejected by the identifier regex (BH-1192)
- Redshift Spectrum external tables reported empty (BH-1202)
- `get_database_size` failing on missing `svv_table_info` SELECT grant (BH-1191)
- `run_longitudinal_analysis` hardcoded to Longaeva's columns (BH-1209)
- Event-loop blocking → CloudFront 120s severs turned into honest `status=pending`
  (BH-1233, BH-1234)
- Missing-arg errors returned generic "internal error" instead of `bad_request` (BH-1220)
- Stale dispatcher locks silently dropping runs (BH-1238), and 6 more.
- New: `list_workspace_signals` MCP read tool for BrightSignals alert history (BH-1215).

**2. Engine-agnostic lineage + staged quality (BH-1036).**
Pipeline lineage that derives medallion tiers from *declared structure*, not table-name
guesses (BH-1265); a service-key write path for pipeline lineage (BH-1124); a
lineage-scoped, re-runnable, immutable `runPipelineSegment` / `reRunFromNode` model
(BH-1258); and the webapp surface for all of it — a 6-tier medallion lineage view on
project observability (BH-1368/1370), plus a boot-time schema guardrail so an invalid
directive enum can never crash staging again (BH-1130).

**3. Warehouse-health snapshot → landing band (BH-1280).**
The cross-repo feature closed this sprint: platform-core folds a watchdog health
snapshot worst-of into connection status (never optimistic), the webapp home band +
Health Checks page render disk-free % and failed-job counts engine-neutrally, and a
3-engine ground-truth fixture set lands in e2e. Shipped to staging by sprint end.

**Also:** BrightRoutines cadence override + feedback capture (BH-993), dispatcher lock
reclaim (BH-1235), GSI5 for the routines leaderboard (BH-1207), an OpenMetadata N+1
perf gate (BH-1242), MFA2 V1 opt-in SMS on the staging pool (approval-gated), and the
full 3.0.0 release train.

**In flight (10):** the default-warehouse ingestion path (BH-1023 subtasks), unstructured-data
stack into workspace accounts (BH-293/285), and the staging ingestion-source mismatch (BH-815).

---

## 👤 Harbour (Nano-233) — *the product-surface craftsman*

**17 PRs** (all code, zero release) · **+2,020 / −575** · webapp 14, platform-core 2, apm 1 ·
**12 tickets Done**

Harbour owned the user-facing quality of the catalog and projects surfaces, and the
retrieval quality of the knowledge base.

- **Catalog + Projects UX sweep — 11 fixes in one sprint (BH-1154 → BH-1162).**
  Real Switch components replacing fake toggles, correct write-mode labels, aligned
  field-label casing, the missing Projects "JSON Schema" tab, the missing project-file
  Tags field, backwards governance switch labels, page-title mismatches — the long tail
  of "small things that make the product feel unfinished," cleared.
- **`resourceType()` extension bug (BH-1162/#1367):** it only ever matched the first
  extension per type — a real correctness fix behind a cosmetic-looking ticket.
- **Atomic project creation (#1382):** create-with-rollback, toast on failure, no more
  orphaned projects; plus one-mutation project creation with a name (#1147).
- **KB retrieval precision:** reranking on `query_knowledge_base` (BH-1164), grounding
  instructions to cut hallucination (BH-1165), and file-id scoping for the
  omni/superduper graph aliases (BH-1163).
- **Catalog healthcheck + bulk tagging (#1176)** and `previewAvailable`/`profilerAvailable`
  fields with an N+1 batch fix (#889, BH-1036).

*(BH-1188, the Neo4j onboard-hang lock-contention bug, was investigated and Canceled —
superseded, not shipped.)*

---

## 👤 Marwan (Marwan-Samih-Brighthive) — *schema-file intake, end to end*

**8 PRs** · 4 code + 4 promotion · **+1,391 / −185** · platform-core 4, webapp 4

Marwan delivered one clean vertical slice: raw schema-file support across the stack, so
XSD/XML schema files can be uploaded, stored, read back, and edited in Project Files.

- **platform-core:** `resourceContent` query for raw schema-file reads (#1144), and
  `resourceContentUploadUrl` for schema-file upload URLs (#1148).
- **webapp:** XSD/XML schema file uploads in Project Files (#1377), and an XSD/XML
  schema file editor (#1383).
- Each shipped develop→staging under its own promotion PR.

---

## 📊 Sprint health & honest notes

- **Completion by ticket transition understates delivery** — as every prior sprint,
  most work ships via PR before its ticket flips to Done. 82 PRs against 28 resolved
  tickets is the same PR-ahead-of-Jira pattern flagged in Sprints 11–13.
- **Concentration risk unchanged.** Kuri authored 69.5% of PRs (57/82), in line with
  the 72% flagged last sprint. The bus-factor conversation from Sprint 13 still stands.
- **Points aren't tracked** — the team measures by PRs + resolved tickets, not
  estimation. All in-window tickets except BH-233 (2 pts) are unpointed.
- **Fourth unofficial sprint running.** Sprints 11–14 were all date-range cuts. A formal
  Jira sprint object would make completion %, carry-over, and velocity trend real
  instead of reconstructed.

## Recommendations for Sprint 15

1. **Open a formal Jira sprint object** before the next cut — end the 4-sprint drift.
2. **Distribute review + authorship** — the 70% concentration is a standing risk.
3. **Close the BH-1023 default-warehouse chain** — it's been in flight the whole window.
4. **Sweep the 10 in-flight tickets** to Done/next-sprint so carry-over is explicit.
