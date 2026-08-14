# ADR-0003: Package the engineering runner for a small Linux host in the customer's network — never the SQL Server box itself

**Date:** 2026-08-14
**Status:** Accepted
**Who:** @drchinca (Kuri)
**Related:** [ADR-0002](0002-engineering-runs-on-the-customers-filesystem.md)

## The Problem

BH-1427: Frank's box is SQL Server 2019 on Windows Server 2019 — an Azure VM. Every deployment
artifact BrightAgent has assumes Linux (`brightbot-dbt-MCP-server` ships as a container on ECS
Fargate). Docker on Windows Server 2019 is possible but awkward, and rarely welcome on a
production database host. We need one documented install path an admin can follow on a clean
machine, that survives reboot, reports health, and upgrades without uninstall/reinstall.

## Our Decision

**The runner installs on a small dedicated Linux host inside the customer's network — never on
the SQL Server machine.** Packaged as a systemd-managed service (`brightagent-onprem.service`),
installed via a single idempotent shell script, talking to SQL Server over 1433 like any other
client on the network.

ADR-0002 already established the deciding fact: "the plugin does not have to live ON the SQL
Server, only inside the network." Filesystem access to the dbt project / SSIS sources is a
network-reachable-share concern (SMB mount, git clone, or a shared dev volume), not a
same-machine-as-SQL-Server concern. Once that's true, there is no reason to solve Windows Service
packaging at all for v1.

## Why This Choice

- **Zero new packaging technology.** systemd + a shell installer is what every other Brighthive
  Linux service already uses. Windows Service packaging (NSSM wrapper or `pywin32`) would be new
  surface area we cannot even test here — there is no Windows Server 2019 box in this environment,
  so any Windows-native path would ship unverified.
- **Preserves "nothing installed on the database server."** Doc 1's promise to the customer, and
  the one thing that survives a DBA's security review without a fight. A Linux host the customer
  stands up for this purpose (or an existing jump box) never touches the production SQL Server's
  own filesystem or process list.
- **A DBA's first question — "what account does it connect as, and what does it touch" — gets a
  clean answer** when the runner is a service account on its own box, not a service running
  alongside `sqlservr.exe`.

## The Cost

- **The customer must provision a small Linux host** (or point us at an existing one) — a step
  Frank's team does not need for a Windows-native install. This is the real trade we are making:
  slightly more setup coordination, in exchange for shipping something we can actually test and
  support.
- **SSIS `.dtsx` source files, if they only ever exist on the Windows box's local disk** (SSDT is
  Windows-only), need a network path off that box — an SMB share or a git remote the engineers
  already push to — for the Linux-hosted runner to read them. If Loop Capital's SSIS sources are
  git-tracked (the common case for a team using source control at all), this is already satisfied.
  If they are not, that becomes a prerequisite conversation with the customer, not a packaging
  problem.
- **Not proven on the customer's actual network topology.** This ADR fixes the target (a Linux
  host, systemd-managed); it does not prove the customer has one available or that their SSIS
  files are network-reachable from it. That confirmation is an install-time, customer-specific
  step — tracked honestly as open, not assumed.

## Alternatives We Considered

- **Windows Service (native, via NSSM or `pywin32`)**: rejected for v1. Would run directly on
  whatever Windows box hosts it — likely the SQL Server VM itself, since that is the only Windows
  machine in scope — reintroducing exactly the "software on the database server" outcome ADR-0002
  exists to avoid. Also the option we are least able to verify from here.
- **Docker container on Windows Server 2019**: rejected. The ticket itself names this as "possible
  but awkward and rarely welcome on a production database host" — same objection as the native
  Windows Service option, plus the operational overhead of Docker Desktop / Windows containers on
  a box nobody wants extra moving parts on.
- **No packaging — `uv pip install -e .` from a private repo checkout**: this is what exists today.
  Rejected as a shipped state because it fails the ticket's own DoD ("an admin can follow without
  our help, on a clean machine") — it requires a Python toolchain, `uv`, and repo access, none of
  which a customer's ops admin should need to reason about.
