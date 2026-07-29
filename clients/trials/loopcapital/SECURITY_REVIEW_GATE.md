# Security Review Gate — Loop Capital real SQL Server connection

> **Blocking.** No code in `brightbot`, `brighthive-platform-core`, or any sibling repo may
> initiate a connection to Loop Capital's real SQL Server 2019 Azure VM until every item below is
> checked and this document is signed off **by name**, per `~/.claude/CLAUDE.md`'s hard rule on
> credentials/secrets (named, explicit, per-action confirmation) and `pluggable-scalable.md`'s
> PS-11/12/13. This gate is referenced as a blocking dependency in
> [`docs/specs/loopcapital-trial-readiness.md`](../../../docs/specs/loopcapital-trial-readiness.md)
> §6, and as a precondition on tickets BH-1246 and BH-1249–BH-1253.

## Checklist

- [ ] **Least-privilege login confirmed.** The dedicated SQL Server login Loop Capital provides
      (blocker #2, per Doc 1) is read-only, scoped to the in-scope databases plus SSISDB/
      ReportServer catalogs and SQL Agent job/disk views only. If it's broader than that, reject
      and re-request — do not proceed with an over-scoped credential.
- [ ] **Multi-tenant isolation (PS-13).** The connection credential is stored and namespaced by
      `workspace_id`, using the existing `SecretsPort`/secret-name-template convention
      (`~/.claude/rules/brighthive-ops.md`) — not a one-off hardcoded secret path.
- [ ] **Resilience envelope (PS-11).** `timeout_s`, `retries`, `circuit_breaker`, and `bulkhead`
      (concurrency cap) are configured for this specific new `SqlServerPipelineSource` /
      warehouse-connection instance before the first real call — this is a brand-new external
      customer connection, higher blast-radius than the sandbox/EC2 stand-ins used so far.
- [ ] **Cost & blast-radius budgets (PS-12).** `max_rows` and `max_cost_per_call` are set for this
      connection specifically, once blocker #3 (in-scope database list) resolves and real data
      volumes are known.
- [ ] **PII readiness.** `BH-1060` has reached at least "Ready for Dev" — `scrub_text()` alone
      (secret-shape detection only) is not sufficient before real Loop Capital customer data flows
      through any agent. This gate cannot be signed off with `BH-1060` still in "Needs Refinement"
      if the connection will process customer PII (criterion 8 assumes it will).
- [ ] **Named confirmation.** State the exact action — "connecting brightbot's runtime to Loop
      Capital's real Azure VM over their allowlisted egress IP, using [credential name/path]" —
      and obtain explicit written confirmation from the approver below before ticket BH-1246 moves
      out of To Do. A prior approval of a *different* action does not carry over to this one.

## Sign-off

| Item | Approver | Date | Notes |
|---|---|---|---|
| All checklist items above | _(pending)_ | _(pending)_ | Not yet signed — Loop Capital has not yet provided the 5 blocking items (server DNS/IP, login, DB list, SSISDB/ReportServer confirmation or files, known-bad artifacts). |

## Related

- Spec: [`docs/specs/loopcapital-trial-readiness.md`](../../../docs/specs/loopcapital-trial-readiness.md)
- Blockers: [`TRACKER.md`](TRACKER.md) — "Trial cannot start" section
- PII gap: `BH-1060`
