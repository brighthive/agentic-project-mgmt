# ADR-0002: Engineering runs on the customer's filesystem; monitoring runs from our cloud

**Date:** 2026-08-13
**Status:** Proposed
**Who:** @drchinca (Kuri)
**Supersedes:** [ADR-0001](0001-dbt-core-runs-cloud-side-against-on-prem-sql-server.md)

## The Problem

Loop Capital is off-cloud: SQL Server 2019 on Windows Server 2019, one allowlisted egress IP,
TCP 1433 inbound only. We need to decide where BrightAgent's work physically executes.

ADR-0001 answered "all of it, cloud-side", on the grounds that dbt is ELT so the warehouse does
the computation wherever dbt runs. That reasoning conflates two different things and gets the
engineering half wrong.

## Our Decision

**Split by what the work touches, not by what computes it.**

- **Monitoring runs from our cloud**, over the existing 1433 link. Nothing installed on their host.
- **Engineering runs on their network**, on a host with filesystem access to their project files.

## Why This Choice

dbt Core is a **filesystem tool** before it is a SQL tool. Its project tree, models, `target/`
artifacts and the git working tree all live on disk. Run it cloud-side and the customer's project
lives on *our* filesystem — their engineers cannot open or edit their own models, and anything they
change locally is invisible to us. "The warehouse computes anyway" is true of the data and says
nothing about where the code lives.

The legacy stack splits the same way. SSISDB holds *deployed* packages, readable over 1433. The
*source* `.dtsx` files engineers open in SSDT live on the filesystem. Diagnosing what is running
and proposing an edit to its source are different jobs; only the second unblocks the engineering
loop, and only the second needs local files.

Monitoring genuinely does not need any of this. `SqlServerPipelineSource` already reads
volume-level free space and SQL Agent job history over the BYOW warehouse connection, and its own
docstring notes it needs "no new on-host collector, no agent installed on the SQL Server itself."
That capability ships; duplicating it locally would add a second, weaker door onto the same data.

**The customer's own harness closes the loop.** Frank's team runs Claude Code / Cortex on their
network. Those speak MCP and sit beside the runner, so they drive it locally with **no inbound
firewall rule**. Metadata flows outbound to our control plane over HTTPS. Nothing reaches in.

## The Cost

- **We now ship software onto customer infrastructure.** That means a security review, a support
  boundary, an upgrade path, and a Windows-or-adjacent-Linux-host decision we did not previously own.
- **Two execution locations to reason about.** Every new capability needs an explicit answer to
  "does this touch files?" — and the failure mode is re-conflating them, exactly as ADR-0001 did.
- **They can read and modify the runner.** Our governance claim therefore cannot live in our code.
  It lives in *their* database: the scoped principal's `GRANT`/`DENY` means a forked, modified
  runner still cannot write outside the schema it owns. Anything we promise about auditability must
  be enforced server-side too, not in code they control.
- **Local runs go blind by default.** Artifacts land on their disk, so lineage, run history and
  self-healing stop working unless metadata is explicitly synced back (BH-1425).

## Alternatives We Considered

- **All cloud-side (ADR-0001).** Rejected: puts the customer's project on our filesystem and cannot
  read the SSIS sources their engineers actually work on.
- **All on-prem, including monitoring.** Rejected: monitoring already ships and works from the cloud
  with nothing installed. Moving it on-prem would duplicate a working capability and bypass the
  hosted MCP's workspace scoping, default-deny scopes, and two-call write confirmation.
- **Copy their project into our cloud, run there, copy back.** Rejected: code egress out of their
  tenant, a sync conflict every time an engineer edits locally, and it fails the zero-copy posture
  the POC is explicitly built around.
