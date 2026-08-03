# 🚀 Project Phoenix: Loop Capital Workspace Nuke & Rebuild

**Target Workspace ID:** `e3fc0917-03a6-4ac6-aad4-ac265329bfb9`
**Database Environment:** SQL Server 2019 (Docker Sandbox / EC2) + Azure Synapse
**Epic / Focus:** BH-1036, BH-1245

This is the master orchestration plan for the complete teardown and deterministic reconstruction of the Loop Capital pilot environment. The goal is an absolute zero-state followed by a rigorous, layered rebuild that guarantees the 29-item SSIS Monitoring Test Plan and the GC-14..17 autonomous loops can be executed flawlessly.

---

## Phase 1: The Annihilation Protocol (Nuke to Zero-State)
We must ensure no ghost data, stale configurations, or orphaned alert states survive.

1. **Destroy the Data Plane (Local/Docker):**
   - Execute the ultimate hard reset on the SQL Server container.
   - Use `docker compose down -v` in `clients/trials/loopcapital/sandbox/` to obliterate the `tmpfs` mounts and the persistent `LoopCapitalAM` database files.
   - Run `docker system prune` selectively to clear dangling images/volumes related to the sandbox.
2. **Purge the Brighthive Platform State (Staging Workspace `e3fc0917...`):**
   - Execute API calls or administrative scripts to flush all `PipelineHealthSignal` records linked to this workspace.
   - Clear the `NotificationInbox` and Slack dual-write queues.
   - Delete all mocked data assets (the 11 medallion assets currently in the staging catalog) via the GraphQL/REST API.
   - Reset the workspace's secret store (specifically ensuring the `loopcapital.demo@brighthive.io` Cognito password is reset from `TempPass123!` back to `LoopCapital6474cb7c43de!Aa1` as flagged in Tracker blocker #7).

---

## Phase 2: The Foundation (Infrastructure Re-Scaffolding)
Bring the physical and logical infrastructure back online from a clean slate.

1. **Boot the SQL Server Sandbox:**
   - Run `docker compose up -d` to spin up a pristine SQL Server 2019 instance.
   - Verify health checks and ensure `tmpfs` mounts are correctly sized.
2. **Authenticate & Validate Platform Core:**
   - Authenticate BrightAgent against the Staging API using the corrected Cognito credentials.
   - Verify `workspace_id` `e3fc0917-03a6-4ac6-aad4-ac265329bfb9` returns an empty catalog (`workspace.dataAssets` length == 0).

---

## Phase 3: The Medallion Data Hydration
Recreate the `LoopCapitalAM` database with deterministic seed data.

1. **Schema Initialization:**
   - Execute `01_create_database.sql` to lay the physical files on the `tmpfs` mount.
   - Execute `03_bank_schema.sql` to create the Bronze, Silver, and Gold tier tables.
2. **Agent Watchdog Configuration:**
   - Execute `02_create_agent_jobs.sql` to establish the `LoopCapital_NightlyExtract_OK` and `FAILED` jobs in `msdb` for the GC-15 health monitor to observe.
3. **Deterministic Seeding:**
   - Run `04_seed_bank_data.py` (via `reset.py --scenario baseline`).
   - Validate row counts: `holdings_raw` (2000), `raw_market_prices` (~900), `raw_positions` (~480).
   - Verify the planted compliance breach: `mart_compliance_breaches` contains `PORT-001-GROWTH` over 20%.

---

## Phase 4: The Legacy Trading Fabric (Contracts & Defects)
Deploy the specific assets required to run the 29-item test plan.

1. **Contract Registration:**
   - Ingest the 6 XSD files (`TradeDW.ReconStaging.xsd`, `OMS.Trades.xsd`, etc.) into the BrightHive metadata catalog for the workspace.
2. **SSIS & SSRS Artifact Staging:**
   - Verify the presence of `01_LoadVendorPrices.dtsx`, `02_LoadTradesFromOLTP.dtsx`, and `03_LoadFixExecutionsAndReconcile.dtsx`.
   - Verify the presence of `DailyTradeBlotter.rdl` and `Holdings_Daily_Report.rdl`.
3. **Agent Capability Mapping:**
   - Ensure BrightAgent's static analysis tools (e.g., `analyze_dtsx_package`, `analyze_rdl_report`) are pointed at these fresh files.

---

## Phase 5: The Autonomous Operations (dbt Cloud & Autonomy Loop)
Set up the environment for the GC-14..17 demo scenarios.

1. **Compile the Reclaim Model:**
   - Run the dbt-sqlserver adapter targeting `loopcapital_disk_reclaim/models/holdings_current.sql`.
   - Verify the Clustered Columnstore Index (CCI) is successfully built on `holdings_current`.
2. **Arm the Watchdogs & Traps:**
   - Scenario A (Type Drift): Use `reset.py --scenario type-drift` to inject the string into the `quantity` column.
   - Scenario B (Disk Pressure): Use `fill_disk.sh` to trigger the 18% free-space threshold.
   - Scenario C (Cancelled Run): Use `reset.py --scenario cancelled-run` to alter the SQL Agent job status.
3. **Verify the Autonomy Loop:**
   - Ensure the dual-write engine successfully fires the Slack alert and Webapp notification for each scenario.
   - Ensure the surgical PR generation tool is invoked, but the `github_merge_pull_request` tool is *strictly blocked* (GC-17 safety gate).

---

## Phase 6: Exhaustive Validation (The 29-Item Gauntlet)
Execute a systemic sweep against the SSIS test plan to guarantee 100% compliance.

1. **Static Analysis Sweeps:** Verify TC-DTM-01 through TC-SCHEMA-01. (Agent finds `DT_STR` mismatches, `SELECT *` loops, `MaximumErrorCount=1000`, plaintext passwords, etc.)
2. **Precision Guards:** Verify TC-PREC-01 and 02. (Agent does *not* flag SSPI or Fast Load incorrectly).
3. **Runtime & Troubleshooting:** Validate TC-RUN-* and TC-TSHOOT-* capabilities using the configured Agent tooling.

---

## Execution Constraints
- **Zero-Trust Commits:** Do not modify any codebase files without explicit instruction.
- **Traceability:** Output shell command results for every major phase transition.
- **Fail-Fast:** If a teardown command fails (e.g., cannot drop a DB due to locks), halt immediately and resolve rather than proceeding to build on a dirty state.