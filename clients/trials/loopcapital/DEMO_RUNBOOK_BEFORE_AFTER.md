# Loop Capital demo runbook — "plain legacy SQL Server → agentic with BrightHive"

**Audience:** Frank (Loop Capital). **Story:** a legacy Microsoft SQL Server in the
cloud, with no agentic anything built in — then BrightHive attached next to it
(BYOW, nothing installed on the DB) gives it watchdog pipeline health, file
diagnostics, versioned-control fixes, and dbt/Databricks data products.

Everything below was **verified live against staging on 2026-07-17** unless a
caveat says otherwise.

## The three things we're demonstrating (Frank's framing)

1. The engineering agent proactively **monitors, detects, resolves**, and **alerts**.
2. The MCP connects to a **SQL Server that has no MCP** — e.g. disk-space
   monitoring, "alert at 20% capacity left."
3. Skills that **surface the fixes the agent applied** so recurrence of the same
   kind of issue is visible and avoidable.

## Fixed facts (fill blanks before demoing)

| Thing | Value |
|---|---|
| Cloud SQL Server EC2 | `54.197.188.168` (`:1433` open; `:22` filtered — see caveat) |
| SQL Server DB | `LoopCapitalAM` · user `sa` · SA password in the `SqlServerSaSecret` CDK secret |
| LC workspace id | `e3fc0917-03a6-4ac6-aad4-ac265329bfb9` |
| LC demo login | `staging/loopcapital-demo/login-user` (Secrets Manager) |
| GC-16 project | `90e40f73-8ec3-4e15-b356-b3b0b8b2d70a` (the seeded pipeline story) |
| Webapp | `https://staging.brighthive.io` · MCP `brightagent-mcp.staging.brighthive.net` |

---

## ACT 1 — The "before": just a legacy database

**Point to land:** *"This is Loop Capital's warehouse. It's only a database.
Nothing monitors it, nothing understands its pipelines, no agent is attached."*

Connect from a laptop and query it directly (proven live — real rows returned):

```bash
# a SQL client / sqlcmd against the cloud SQL Server (NOT ssh — see caveat)
sqlcmd -S 54.197.188.168 -U sa -P '<SA password from SqlServerSaSecret>' -d LoopCapitalAM -C \
  -Q "SELECT TOP 5 * FROM dbo.holdings_raw"
# → real asset-mgmt rows (AAPL/NVDA/MSFT holdings, PORT-001-GROWTH)

sqlcmd ... -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY 1"
# → 11 tables: raw_* → stg_* → mart_* (a real raw→staging→mart medallion, but 'dumb')
```

> ⚠️ **SSH caveat:** the EC2's `:22` is filtered (SG-locked / SSM-managed). Do the
> "before" via the **SQL client on :1433** (verified working), not a literal
> `ssh` terminal. If you must show an SSH shell, confirm your demo machine's
> access first (SSM Session Manager), or skip the shell and open with the SQL query.

---

## ACT 2 — Attach BrightHive (BYOW, nothing on the DB)

**Point to land:** *"We put BrightHive next to it — no agent, no MCP installed on
the server. It reaches the SQL Server through a Bring-Your-Own-Warehouse
connection and immediately understands it."*

- The **same** SQL Server is registered as a BYOW warehouse **source** (SQL Server
  family). No connector on the box.
- Prove it via the MCP (bound to LC's identity):
  - `introspect_warehouse_schema` → returns the **same 11 tables + columns/types/PKs**
    the agent now reasons over. ✅ verified.
  - `scan_warehouse_tables` (max_tables:N) → discovers + profiles the legacy tables. ✅

---

## ACT 3 — The "after": agentic capabilities light up

### 3.1 — Proactive monitor / detect / resolve / alert (Pillar 1)
- **MCP:** `get_pipeline_health` → polls dbt-job + SQL Server disk + drift sources. ✅
- **MCP:** `get_anomalies` (`LoopCapitalAM.dbo.holdings_raw`) → longitudinal drift detect. ✅
- **In-app:** Project → **Observability** (GC-16): 11 pipelines, **82% success**,
  failures with PRs, one remediated re-run. Health scorecard + Recent Runs + Agent PRs.
- **Safety:** the agent never auto-merges its own fix (GC-17 — a human merges).

### 3.2 — SQL Server disk monitoring, "alert at 20% left" (Pillar 2)
- The `SqlServerPipelineSource` disk watchdog queries `sys.dm_os_volume_stats`,
  fires `source_disk_low` at the 20%-free threshold → **Slack + webapp inbox**
  alert naming the low volume + largest file. GC-15, live-proven against **this EC2**.

### 3.3 — Surface applied fixes to avoid recurrence (Pillar 3)
- File diagnostics: SSIS `.dtsx` / SSRS `.rdl` → the agent finds the real gaps →
  **versioned artifact**: a real GitHub PR (dbt fix PR #1 merged; SSIS PR #2 open).
- **Observability → Agent PRs** panel surfaces every fix the agent applied, with a
  **remediation diagnosis** on each (e.g. GC-16 `stg_holdings_nightly`:
  "settlement_currency→settlement_ccy drift, fixed & merged"; `stg_positions`:
  "duplicate settlement_id, dedupe proposed in PR #2"). 4 surfaced fixes live.

### 3.4 — dbt + Databricks data products (BYOW breadth)
- GC-16's pipelines are real **dbt** models tied to the project, from the connected
  dbt Cloud service. **Databricks** uses the same PipelineSource adapter pattern
  (shipped) — so the BYOW story spans SQL Server source + dbt + Databricks.

> ⚠️ **Databricks caveat:** the adapter exists and is the same mechanism, but LC's
> live demo warehouse is the **SQL Server** (that path is verified end-to-end).
> Frame Databricks as "also supported, same mechanism," not "here's LC's live
> Databricks connection."

---

## Supporting surfaces to show (all seeded/verified this session)

- **BrightRoutines** (`/context/workflows`): "Weekly earnings report" (scheduled) +
  3 more routines. The nightshift/data-companion story.
- **Nav**: Voice Connectors hidden for LC; Glossary + Schemas shown.

## The one honesty line to hold (Pillar 3 wording)
The agent **detects, diagnoses, drafts a reviewable PR, and surfaces every applied
fix** — automatic *recurrence-prevention* (guaranteeing the same class can't recur)
is roadmap, not shipped. Say **"faster, documented, reviewable fixes with every
applied fix surfaced,"** not "recurrence is automatically prevented."

## Known non-blocking gaps (don't get surprised)
- `analyze_dataset_structure` MCP tool is globally broken (all warehouse types) —
  **use `scan_warehouse_tables` for profiling instead** (it works).
- Live `get_lineage` dbt-DAG chat is blocked on a Snowflake MFA issue — **narrate
  lineage, don't click it live.**
