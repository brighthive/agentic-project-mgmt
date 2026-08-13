# ADR-0001: Run dbt Core cloud-side against Frank's on-prem SQL Server

**Date:** 2026-08-13
**Status:** Superseded — see the correction below, and ADR-0002
**Who:** @drchinca (Kuri)

> ## ⚠️ Correction (same day): this decision is wrong for engineering
>
> The reasoning below — *"dbt is ELT, so the warehouse computes wherever dbt runs"* — is true of
> the **data** and irrelevant to the **files**. dbt Core is a filesystem tool before it is a SQL
> tool: the project tree, the models, `target/`, and the git working tree all live on disk.
> Running dbt cloud-side puts the customer's project on **our** filesystem, where their engineers
> cannot see or edit their own models and any local change is invisible to us.
>
> The same over-extension applies to the legacy artifacts. SSISDB holds *deployed* packages, so
> reading those over 1433 works — but the **source** `.dtsx` files engineers open in SSDT live on
> the filesystem, not in the catalog.
>
> **The correct split:**
>
> | Activity | Where it runs | State |
> |---|---|---|
> | Monitoring — disk, Agent jobs, catalog, health | Cloud, over 1433 | Already ships (`SqlServerPipelineSource`) |
> | Engineering — dbt project, SSIS/SSRS sources, git tree | **Must be local** | Nothing exists (BH-1421) |
>
> Everything below remains accurate **for monitoring**, which is what it was really arguing about.
> It is wrong as a decision about the engineering path.

## The Problem

Loop Capital is off-cloud. dbt Cloud cannot serve them — it has no SQL Server destination
(plain SQL Server is the community `dbt-sqlserver` adapter, which dbt Cloud does not host), and
it is SaaS so it could not reach a box behind their firewall anyway. dbt Core is therefore the
write engine ([BH-1403](https://brighthiveio.atlassian.net/browse/BH-1403), proven locally).

That raised an assumption worth testing: that we must deploy an MCP server *inside* their
network to drive dbt Core, and build a filesystem sync between their box and our cloud. Both
are expensive, and both would need firewall changes they have not agreed to.

## Our Decision

**dbt Core runs on our side**, in the existing cloud control plane, connecting to their SQL
Server over the already-allowlisted TCP 1433 link. No on-prem MCP server. No filesystem sync.

Everything else — self-healing loops, lineage, git/PR governance, sandboxing, evals, Slack —
stays exactly as it is today.

## Why This Choice

**dbt is ELT, not ETL.** dbt does not process data; it compiles SQL and sends it to the
warehouse, which does all the computation. So dbt Core running in our cloud against their
server means every row is processed *inside their database*. SQL text goes in; `manifest.json`
/ `run_results.json` / `catalog.json` metadata comes back. That is zero-copy by construction —
the property they care about — with **zero new firewall asks**.

The two things that looked like they needed filesystem access do not:

| Artifact | Where it actually lives | Reachable over 1433? |
|---|---|---|
| SSIS packages | `SSISDB` catalog (deployed packages are DB rows, not loose files) | ✅ already granted in Doc 1 |
| SSRS reports | `ReportServer.dbo.Catalog.Content` (RDL stored as varbinary) | ✅ already granted in Doc 1 |
| dbt project | our git repo — we own it | ✅ never theirs |

Doc 1 already grants read on SSISDB and ReportServer. Their "filesystem" is already exposed to
us *as database content*.

"sync()" is therefore just the dbt artifacts feeding platform-core's Neo4j lineage graph — the
same metadata path every other warehouse already uses. Nothing new to build.

## The Cost

- **Latency.** dbt's many small metadata round-trips run over a public-internet TLS hop instead
  of a LAN. Fine for nightly models; noticeable on wide `dbt ls`/`docs generate` calls.
- **We hold the credential**, so our egress IP and secret handling are in their audit scope.
- **Their outage is our outage** — no local runner keeps working if the link drops.
- **It does not satisfy a strict "no external process may issue DDL" policy.** That is a policy
  stance, not a technical limit; if Frank takes it, we fall back to Alternative B and it becomes
  the POC-phase VPN conversation Doc 2 already defers.

## Alternatives We Considered

- **B — On-prem MCP runner inside their perimeter.** True on-prem execution, and
  [`brightbot-dbt-MCP-server`](https://github.com/brighthive/brightbot-dbt-MCP-server) already
  wraps the dbt CLI as MCP tools (`dbt_run`, `dbt_test`, `dbt_ls`, `dbt_compile`, `dbt_build`),
  so the artifact exists. Rejected *for the trial* because 1433 is the only ingress — reaching
  it needs a new NSG rule, and Doc 1 promises "no software installed on server." Keep in the
  drawer for the POC.
- **C — Outbound-only pull runner** (agent inside their network polls a cloud queue, no inbound
  holes). The most enterprise-friendly shape and the likely POC answer, but it still means
  installing software on their infrastructure, which the trial explicitly avoids.
- **D — Wait for dbt Cloud SQL Server support.** Not on dbt Labs' roadmap; would not solve
  reachability regardless.
