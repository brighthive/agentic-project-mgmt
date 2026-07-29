# LoopCapital — client-facing docs received 2026-07-28

> Source of truth for this reconciliation pass. Two documents sent to Frank Sung (VP, Data
> Management, Loop Capital) in July 2026. Captured verbatim (condensed) so downstream docs can
> be reconciled against them without re-deriving from the PDF/paste.

## Doc 1: "Trial Scope & Success Criteria" (PDF, 4 pages)

**Framing**: Hosted demo workspace + a live connection to Loop Capital's SQL Server 2019 (on a
Windows Server 2019 VM in their Azure environment). Response to Frank's request for the agent's
egress IP to add to his Network Security Group.

**Connectivity**:
- One static egress IP allowlisted, TCP 1433 inbound only — the only ingress.
- TLS, dedicated least-privilege SQL Server login (read on in-scope DBs + SSISDB/ReportServer
  catalogs + SQL Agent job/disk views for monitoring).
- Credentials via in-conversation secure credentialing → managed secrets vault, never shown in
  plaintext after entry.
- Governed action (optional): narrow writable target agreed up front; every change is a
  reviewable PR, nothing applied without approval.

**Scenario mapping** (Frank's requested scenarios → trial scope):

| Scenario | In this trial? | What the agent does |
|---|---|---|
| SQL Server & database work | Partial | Connects/catalogs/profiles; creates governed tables/views/transformations as reviewed PRs if given a writable target. Not a DBA — no provisioning/administration. |
| SSIS package development | Not this trial | Authoring stays in SSDT/Visual Studio. |
| SSIS deployment | Not this trial | Deployment stays in their process. |
| SSIS monitoring & troubleshooting | Yes | Reads SSISDB catalog (or a provided `.dtsx`), flags structural issues (missing error handling, missing staging steps), watches package/job health. |
| SSRS report creation & publishing | Not this trial | Authoring/publishing stay in their tools. |
| SSRS troubleshooting | Yes | Reads ReportServer catalog (or provided `.rdl`), flags performance anti-patterns. |
| Power BI report development | Not this trial | Agent doesn't build Power BI reports; POC can discuss governed delivery of validated datasets into Power BI. |
| SQL Server health monitoring | Yes | Proactively reports disk pressure + SQL Agent job status/failures over the same connection, no software installed on server. |
| Windows / OS health monitoring | Not this trial | Out of scope; SQL Server health only. |

**Success criteria (9, numbered)** — passing bar is **1–4 and 7–8 are core**; 5, 6, 9 are strong
supporting evidence:

1. **Connect & catalog** — connects over allowlisted link, produces browsable catalog (tables,
   columns, types) shortly after receiving credentials.
2. **Data quality on your data** — authors/runs quality checks on chosen tables, returns a
   quality score + readable report + the SQL it generated; real issues flagged with plain-
   language root cause.
3. **Ask in plain language** — business question about their SQL Server data answered correctly,
   underlying SQL shown alongside the answer.
4. **Proactive SQL Server health** — unprompted, surfaces a specific SQL Agent job failure or
   disk-pressure condition, naming the job and actual error (not generic).
5. **SSIS diagnostics** — pointed at a deployed package (or `.dtsx`), identifies ≥1 true
   structural issue.
6. **SSRS diagnostics** — pointed at a report definition, flags ≥1 true performance anti-pattern.
7. **The autonomy loop (headline)** — proactively detects an issue in a SQL Server/SSIS pipeline,
   diagnoses it, opens governed remediation as reviewable change, pauses for approval in Slack,
   drives task to completion with visible progress. Cannot approve its own change.
8. **Governed & auditable** — every agent action in tamper-evident audit trail; PII tagged;
   nothing written without human review.
9. **Platform capability** — in the demo workspace, an external agent calls Brighthive's
   governed MCP lookups, and BrightAgent proposes a recurring routine the user can approve.

**Trial-scope limits (resolved/expanded at POC)**:
- Only SQL Server connected — no ADF, Synapse, ADLS, Power BI service, Entra ID SSO. POC adds
  the broader Azure estate, starting with Azure Data Factory via MCP.
- Connectivity ≠ production posture — trial is allowlisted outbound over public internet (TLS);
  production is zero-copy inside their own tenant, data never leaves. Trial should use
  non-sensitive/representative data.
- Hosted demo workspace, not their isolated environment — workspace-level features shown there
  instead.

**Product-scope clarifications (true in trial AND production)**:
- Diagnose & operate, don't author (no SSIS/SSRS/Power BI authoring).
- SQL Server health, not Windows/OS.
- Governed change, not DBA (creates tables/views/transformations as reviewed PRs given a
  target; doesn't provision/administer servers).
- Power BI: POC can deliver governed validated datasets into Power BI; agent doesn't build the
  reports.

**What Brighthive needs from Loop Capital**:
1. Server DNS name/public IP + confirmation TCP 1433 reachable from provided egress IP.
2. Dedicated least-privilege SQL Server login (read on in-scope DBs; read on SSISDB/ReportServer
   + SQL Agent job/disk views).
3. Which databases are in scope.
4. Confirmation packages deployed to SSISDB / reports to ReportServer catalog, or the
   `.dtsx`/`.rdl` files themselves.
5. A couple of representative "known-bad" artifacts (flawed SSIS package, slow SSRS report,
   quality-issue table) for recognizable diagnosis demos.

**Timeline**: Static egress IP sent right away so Frank can pre-stage the NSG rule. Server ready
"early next week" (per Frank's Slack note) — live connection walkthrough held for then: connect
together, catalog a database, run first quality check + health check live.

## Doc 2: "Your Brighthive Demo — What to Expect"

**Framing**: this is the demo-workspace walkthrough that precedes the paid POC — run on
representative/synthetic data (including sample legacy SSIS/SSRS artifacts), NOT the live
SQL Server connection from Doc 1. Explicit distinction: demo = neutral data, governed workflows
proven; POC = their data, their environment, their controls.

**What runs live in the demo** (representative data):
- **Governed multi-agent workflow end-to-end**: Quality Agent detects issue + explains root
  cause in plain language → Engineering Agent opens a version-controlled PR fix → human
  reviews/merges. Agent structurally unable to merge its own change.
- **Ask a question, see the reasoning**: NL question answered from governed data, SQL shown
  alongside answer, visualization renders only after quality + governance checks clear.
- **Governance that runs, not just documents**: automatic PII tagging, lineage, policy
  enforcement levels, tamper-evident audit trail.
- **Orchestration & Slack**: BrightAgent supervisor routing work across the agent team,
  proactive alerts + approvals in Slack.
- **MCP interface + portable semantics (first look)**:
  - MCP live: external agent (e.g. Claude in an IDE) calling Brighthive's read-only MCP lookups
    (workspace context, structure details, change-impact analysis) against demo workspace, every
    call governed + audit-logged.
  - OSI (Open Semantic Interchange) previewed: governed metric definition exported to OSI format
    — early, one-way proof of portable semantics; framed honestly as emerging standard, not
    overclaimed.
- **Legacy-aware analysis**: SSIS package + SSRS report diagnostics, plus a storage-cost
  optimization scan returning named savings — on demo data.

**What waits for the POC** (needs Loop Capital's real environment/data):

| Area | What gets configured together in POC |
|---|---|
| Data sources | Ingestion Agent → Synapse, Databricks, ADLS Gen2, operational systems |
| Identity | SSO via Microsoft Entra ID tenant |
| Cross-cloud connectivity | AWS↔Azure Site-to-Site VPN + identity federation, zero-copy design |
| Transformation engines | Azure Data Factory + Snowflake Cortex via their MCP servers, Databricks jobs, MSSQL where relevant |
| BI & semantics | Governed visualizations into Power BI; semantic/metric alignment with BI layer |
| Governance & scale | Enforcing their data contracts/policies/compliance at production scale |

**Evaluation questions posed to Frank**:
- Does the agent team actually divide/coordinate work, or is it one model pretending to be many?
- Is every autonomous action governed + auditable, human-in-the-loop where it should be?
- Can an outside agent reason over Brighthive's governed context through MCP?
- Is the reasoning explainable end-to-end (SQL, lineage, policy always visible)?

**Sequencing rationale**: demo proves product + governed workflows on neutral data; POC proves
it on their data/environment/controls — "the only test that ultimately matters for a production
decision."

## Reconciliation note — two distinct engagements, don't conflate

These are **two different things** and downstream docs must not blur them:

1. **Doc 1 (Trial)** = a live SQL Server 2019 connection into Loop Capital's actual Azure VM,
   scoped narrowly to read + optional governed-PR write, with 9 numbered success criteria (1–4,
   7–8 core). This is the "SQL Server trial."
2. **Doc 2 (Demo)** = the pre-POC guided walkthrough in Brighthive's hosted demo workspace on
   representative/synthetic data — proves the governed multi-agent workflow, MCP, OSI preview,
   legacy diagnostics — with a POC-deferred integration table (Synapse/Databricks/ADLS/Entra
   ID/ADF/Cortex/Power BI/governance-at-scale).

Existing LoopCapital docs in this repo (`LOOPCAPITAL.md`, `overview.md`,
`docs/specs/golden-cases-loopcapital.md`, `demo.md`, `TRACKER.md`) were written against an
internal GC-14..17 golden-case framing (dbt Cloud job failure → detection → Slack/webapp alert →
surgical PR → merge → verification) for a 7/17 internal demo. This reconciliation pass must:

- Map the internal GC numbering to the client's numbered success criteria (1–9) and demo bullets
  where they overlap (e.g. GC-16/17 auto-merge exclusion ↔ success criterion 7's "cannot approve
  its own change").
- Flag anywhere the internal docs assume capability now explicitly marked **"Not this trial"**
  (SSIS/SSRS authoring, Power BI report dev, Windows/OS monitoring, ADF/Synapse/ADLS/Entra ID
  SSO) — those need an explicit demo-vs-POC/trial-vs-not callout, not silent scope creep.
- Note the stack mismatch if any: existing docs reference **dbt Cloud** as the pipeline under
  test; Doc 1/Doc 2 describe **SSIS/SSRS/SQL Server 2019 + eventual ADF/Synapse/Databricks/
  Snowflake Cortex**. These may be two different workloads for the same client (dbt Cloud demo
  vs. SQL Server/SSIS trial) — do not merge them into one flow without confirming with the user;
  flag the discrepancy explicitly in each updated doc instead of guessing.
