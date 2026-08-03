# BrightAgent Demo Runbook — Rebuild a Legacy Pipeline on dbt, Then Govern It

**Audience:** GTM / SE running the live Loop Capital demo (epic BH-1036, champion Frank Sung).
**Time:** ~20 minutes.
**Difficulty:** No SQL required — you drive BrightAgent in plain English and read the results.

> **Legend:** 🟢 live/real · ⚠️ honest caveat · ⚪ not in this demo (tracked) · 🛡️ safety boundary

---

## What this demo actually shows

Frank already runs his pipelines on SQL Server. He hands BrightAgent the **schemas and
instructions** for a table his internal pipeline produced. BrightAgent:

1. **Reads** the legacy contract (`.xsd`) and his live SQL Server table — read-only.
2. **Rebuilds** that pipeline as version-controlled **dbt models**, committed to a connected
   GitHub repo as **BrightAgent[bot]**.
3. **Materializes** the rebuilt table via **dbt Cloud** into the dbt-supported warehouse
   (**Azure Synapse**) — a real, standing, queryable object.
4. **Compares 1:1** the rebuilt table against his original live SQL Server table — schema,
   row counts, values — **and explains why the rebuilt one is better**.
5. **Governs it** — the rebuilt pipeline is now fully observable and controllable across chat,
   the observability page, and MCP: control, monitoring, lineage, governance, provenance.

**The story for Frank:**
*"Hand the agent your schema and your instructions. It rebuilds your pipeline on the tooling your
team already trusts — dbt, version-controlled, bot-authored — and from that moment every run,
lineage edge, quality rule, and provenance record is something you can see and act on."*

---

## 🛡️ The two things that make this honest (read before you demo)

1. **BrightAgent never writes to the warehouse with its own connection.** Its own driver is
   SELECT-only by design (a safety boundary). The **writes happen through dbt Cloud** — the agent
   commits model SQL, then triggers a dbt run, and *dbt* (authenticated to Synapse) issues the
   CREATE TABLE / INSERT. This is why we can promise "it writes to the warehouse" without breaking
   the read-only guard.
2. **There is no fabricated "before run."** We do **not** execute Frank's SQL Server pipeline —
   his table already exists because *he* ran it. BrightAgent reads it as the reference. The
   comparison is his **real live table** vs the **real dbt-materialized table**. Nothing is invented.

---

## Before you start (SE checklist)

* [ ] 🟢 Frank's SQL Server is reachable — his hosted, open-port, whitelisted test DB, connected to
  BrightAgent (connection verified via `connection_health`).
* [ ] 🟢 A dbt Cloud project + **Azure Synapse** environment is configured and connected to the
  demo GitHub repo. *(Synapse, not SQL Server — SQL Server is not a dbt Cloud target. ⚠️)*
* [ ] 🟢 The GitHub repo is connected through Platform Core (the agent commits via the proxy).
* [ ] ⚠️ **BrightAgent[bot] committer identity** requires platform-core PR #1158 deployed to the
  demo env. If not yet deployed, commits show the PAT owner — say so, don't hide it.
* [ ] 🟢 The real contract asset is on hand: `sandbox/contracts/TradeDW.ReconStaging.xsd`
  (the `TradeDW.dbo.ReconStaging` FIX-reconciliation table).
* [ ] 🟢 Frank's live `TradeDW.dbo.ReconStaging` (or the agreed reference table) exists on his
  SQL Server for the 1:1 comparison.

*If any box is unchecked, ping the SE before the demo. Do not fix connections live.*

---

## The asset we build against (real, in-repo)

`TradeDW.dbo.ReconStaging` — FIX drop-copy reconciliation landing table. Three columns, and it
carries a **real, documented defect** that makes the "why it's better" story concrete:

| Column | Legacy SQL type | Nullable | Note |
|---|---|---|---|
| `Symbol` | `nvarchar(12)` | NO | mapped destination column |
| `LastQty` | `int` | YES | |
| `LastPx` | `money` (scale 4) | YES | **the pipeline feeds it a `DT_STR` value — TC-DTM-03** |

The defect (`LastPx` is `money` but fed a string) is the anchor of the comparison: the rebuilt dbt
model types it correctly and enforces it with a test.

---

## Run the demo

Each step: what to **do**, what to **say** to BrightAgent, and what **success** looks like.

### 1. Confirm the source connection 🟢
* **Say:** `"Which warehouses are you connected to, and is Frank's SQL Server connection healthy?"`
* **Success:** Agent names the SQL Server + Synapse connections and reports health (backed by the
  `connection_health` verb).

### 2. Read the legacy contract 🟢
* **Do:** Point the agent at `TradeDW.ReconStaging.xsd`.
* **Say:** `"Read the ReconStaging.xsd contract. What table and columns does it describe, and do you
  see any risk in the column types?"`
* **Success:** Agent reports `TradeDW.dbo.ReconStaging` with `Symbol`/`LastQty`/`LastPx`, and flags
  the `LastPx money` ← `DT_STR` mismatch (TC-DTM-03). *This is the diagnostic capability — real.*

### 3. Read the live reference table 🟢
> **⚠️ Precondition — verify the reference table exists before you demo.** The verified-live
> Loop Capital workspace (`e3fc0917-…`) is database **`LoopCapitalAM`** with 11 medallion assets
> (`holdings_raw`, `raw_counterparties`, `stg_holdings`, `mart_compliance_breaches`, …) — see
> `artifacts/AGENT_CAPABILITIES_NOTES.md`. `TradeDW.dbo.ReconStaging` from the `.xsd` is the
> **contract we build to**, not a confirmed-present live table. If Frank has loaded it, use it as
> the reference. **If not, pick the closest real `LoopCapitalAM` asset** (e.g. `raw_market_prices`
> for a price-typed comparison) and align the `.xsd` build target to it. Confirm this with the SE
> in the pre-flight; do not assume `TradeDW` is live.
* **Say:** `"Read the current <reference table> on the SQL Server. How many rows, and what
  do the values look like?"`
* **Success:** Agent SELECTs (read-only) from Frank's live table and reports a row count + sample.
  This is the **reference** side of the 1:1. *(Backed live by `dataAssetPreview` — first-10 +
  random-100 straight from the BYOW warehouse, not a cached snapshot.)*

### 4. Rebuild the pipeline as dbt, commit as BrightAgent[bot] 🟢
* **Say:** `"Rebuild this as a dbt model that matches the contract but fixes the LastPx type and
  adds a not-null test on Symbol. Commit it to the connected repo."`
* **Success:** Agent generates the model SQL + schema tests and commits them. The commit author is
  **BrightAgent[bot]** (⚠️ if PR #1158 is deployed). Ask it for the branch + commit SHA — real
  provenance you can click.

### 5. Materialize into Synapse via dbt Cloud 🟢
* **Say:** `"Run the model into the dev stage and tell me when the table is live."`
* **Success:** Agent triggers a dbt Cloud run (`run_models_to_stage`) and reports the run status +
  that `recon_staging` is materialized in Synapse. **This table now persists** — Frank can query it
  himself, tomorrow, without us. *(That persistence is the answer to "your screen says this is not
  live.")*

### 6. Query the rebuilt table 🟢
* **Say (pick a few):**
  * `"How many rows landed, and how many distinct symbols?"`
  * `"Show me the LastPx values — are they typed as numbers now?"`
  * `"Any rows where Symbol is null?"` *(should be zero — the test enforces it)*
* **Success:** Answers are internally consistent and `LastPx` is numeric (not string).

### 7. Compare 1:1 — live SQL Server vs rebuilt Synapse table, with reasoning 🟢
* **Say:** `"Compare the rebuilt recon_staging in Synapse to Frank's original
  TradeDW.dbo.ReconStaging on SQL Server. Schema match? Row-count match? And tell me why the
  rebuilt one is better."`
* **Success:** Agent produces a side-by-side: schema diff, row-count match/diff, and a plain-English
  rationale — e.g. *"`LastPx` was `money` fed a `DT_STR` (TC-DTM-03); the rebuilt model types it
  `decimal(19,4)` and adds a not-null test on `Symbol`, so the pipeline can no longer silently land
  a malformed price or a null key."* **This is the "this table is better because X" moment.**

### 8. Show the governance layer 🟢 (the "full control" story)
The rebuilt pipeline isn't just a table — it's now fully governed. Show as many as time allows:

| Pillar | Say | Surface |
|---|---|---|
| **Monitoring** | `"Profile recon_staging and show its health."` | chat + observability page |
| **Lineage** | `"Show the lineage for recon_staging."` | observability page (`PipelineLineageSection`) |
| **Control** | `"Show me the recent dbt runs for this project."` | observability page (`RecentRunsList`) + MCP |
| **Governance** | `"Attach a quality rule: Symbol must never be null."` | chat declare-gate + node drawer |
| **Provenance** | `"Who authored the last commit and which PR shipped it?"` | observability page (`AgentPRs`, commit SHA) |

* **Success:** Each pillar returns a real result. The point Frank takes away: *once the pipeline is
  on dbt, everything about it is observable and actionable — from four places (chat, the page, MCP,
  and Slack notifications).*

---

## Generalization — the artifact is interchangeable

The class of request is the constant, the artifact type is swappable. The **same flow** runs from:

| Artifact | What the agent reads | Status |
|---|---|---|
| `.xsd` | table/column contract | 🟢 (this demo) |
| `.dtsx` (SSIS) | package → source→destination mappings, defects | 🟢 diagnose real; rebuild via dbt |
| `.rdl` (SSRS) | report dataset queries | 🟢 diagnose real |
| `.dbt` / dbt project | existing models | 🟢 |
| `.yml` (dbt/Atlas) | sources / semantic view | 🟢 |
| `.xsl` | transform | ⚪ not built — don't demo |

Hand it a different artifact, same request: *read → rebuild on dbt → materialize → compare →
govern.*

---

## Live-readiness — proven vs. to-verify (grounded in `AGENT_CAPABILITIES_NOTES.md`)

Every capacity below was **verified live** on the real LC staging workspace (`e3fc0917-…`) on
2026-07-17 unless marked ⚠️/⚪. Use this to know what will "just work" vs. what the SE must confirm
in pre-flight.

| Demo step | Capability | Status | Evidence |
|---|---|---|---|
| 1 | Warehouse connection health | 🟢 proven | BYOW SQL Server `LoopCapitalAM` @ `54.197.188.168:1433`, self-signed TLS opt-in shipped (`#1089`) |
| 2 | Read `.xsd` + flag type risk | 🟢 proven | deterministic `.dtsx`/`.rdl`/xsd parsers; SSIS/SSRS analyzer real |
| 3 | Read live reference table | 🟢 proven | `dataAssetPreview` live first-10/random-100; 11/11 assets profiled |
| 4 | Commit dbt models | 🟢 proven | GC-16 opened a real GitHub PR; ⚠️ BrightAgent[bot] author needs platform-core #1158 deployed |
| 5 | Materialize via dbt Cloud | 🟢 proven | `run_models_to_stage`; ⚠️ target is **Synapse**, not SQL Server |
| 6 | Query the rebuilt table | 🟢 proven | read-only warehouse query tool, dialect-aware |
| 7 | 1:1 compare + reasoning | 🟢 proven | profiler + preview both sides; ⚠️ verify the reference table is loaded (Step 3 note) |
| 8 — Monitoring | Profiler + quality | 🟢 proven | 11/11 assets carry real `profiling` + `quality_check` |
| 8 — Lineage | `SEMANTIC_REFERENCES` edges | 🟢 proven | 11/11 semantic views; `hasSemanticView` resolver shipped (`#1094`) |
| 8 — Control | Recent dbt runs | 🟢 proven | GC-14/15 watchdog live on the real EC2 box |
| 8 — Governance | Attach quality rule / gate | 🟢 proven | `declareGovernanceGate` shipped (BH-1333/1334/1335) |
| 8 — Provenance | Commit author + PR | 🟢 proven | GC-17 human-merge gate held live (`open`, `mergedAt: null`) |
| 8 — Drift alert (optional) | Longitudinal anomaly | 🟢 proven | null-spike CRITICAL detected end-to-end; ⚠️ needs snapshot history |
| — | Live schema-change → PR | ⚪ NOT demoable | only dbt build-failure error text routes to PR; value-drift does not |
| — | Slack lifecycle verbs | ⚪ not built | task #48 |
| — | Before+after run logs | ⚪ spec stage | BH-1329 |

**The one honest gate:** the 3+1 is proven live *per capability*. The only unverified assumption is
whether `TradeDW.dbo.ReconStaging` specifically is loaded on Frank's server — resolve that in
pre-flight (Step 3 note) and the lifecycle is complete end-to-end.

---

## Pass / fail checklist
* [ ] **Step 2** — Agent read the `.xsd` and flagged the `LastPx` type risk.
* [ ] **Step 3** — Agent read Frank's live SQL Server table (read-only).
* [ ] **Step 4** — Model committed to the connected repo (BrightAgent[bot] if PR #1158 deployed).
* [ ] **Step 5** — dbt Cloud run materialized `recon_staging` in Synapse.
* [ ] **Step 6** — Rebuilt table queried; `LastPx` numeric, no null `Symbol`.
* [ ] **Step 7** — 1:1 comparison with a clear "better because…" rationale.
* [ ] **Step 8** — At least three governance pillars shown live.

---

## Honest gaps (say these plainly if asked)
* ⚠️ **BrightAgent[bot] committer** — live only after platform-core PR #1158 deploys to the demo env.
* ⚠️ **SQL Server is not a dbt Cloud target** — the rebuilt table materializes into **Synapse**,
  not back into Frank's SQL Server. The comparison is cross-warehouse by design.
* ⚪ **Slack lifecycle verbs** (run/schedule from Slack) — tracked (BH task #48), not in this demo.
* ⚪ **Before+after dbt run logs** (BH-1329) — spec stage; the comparison spine here is table-vs-table,
  not run-log-vs-run-log.
* ⚪ **`.xsl` transforms** — not built; do not offer.

---

## If something goes wrong
* **"I can't reach the SQL Server."** Connection/NSG issue — hand to the SE; don't fix live.
* **dbt run fails.** Ask the agent to show the run log; it surfaces the dbt error verbatim.
* **Comparison shows unexpected differences.** Ask the agent to explain each — schema, row-count, or
  value. Differences with a clear cause are a *feature* of the demo, not a failure.
* **Commit shows a personal author, not the bot.** PR #1158 isn't deployed yet — say so honestly.

---
*Companion assets: `sandbox/contracts/TradeDW.ReconStaging.xsd` (the real contract), the SSIS/SSRS
diagnostic packages under `sandbox/`, and the capability inventory in
`artifacts/AGENT_CAPABILITIES_NOTES.md`.*
