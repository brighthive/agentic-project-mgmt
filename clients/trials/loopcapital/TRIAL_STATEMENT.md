# Loop Capital — Trial Statement (internal, as of 2026-07-28)

> Single consolidated readiness snapshot for the Trial (Doc 1: "Trial Scope & Success
> Criteria" — live SQL Server 2019 connection into Frank Sung's Azure VM). Aggregates the
> full docs/specs/tickets/epic/diagram/gate pass completed this session. Internal only —
> not client-facing. For the underlying artifacts, follow the links; this doc is the index
> and the honest one-page answer to "where do we actually stand."

## TL;DR

- **Trial has not started.** Blocked on 5 items only Loop Capital can provide (§3).
- **Every mechanism the Trial needs already exists in code**, and is proven — but only against
  a Docker sandbox or a stand-in EC2 SQL Server, never Loop Capital's real environment (§2).
- **One real code gap, not just an unproven-on-real-data gap**: PII tagging (`BH-1060`) —
  `scrub_text()` catches secret shapes only, not customer PII values. Escalated this session
  (§4).
- **A separate, unresolved open question**: whether this Trial (SQL Server/SSIS/SSRS) and the
  internal GC-14..17 mechanism (dbt Cloud) are the same Loop Capital engagement described two
  ways, or two parallel workstreams. Not resolved by this pass — needs Kuri's confirmation (§6).
- **New tracking structure**: epic `BH-1245`, spec
  [`docs/specs/loopcapital-trial-readiness.md`](../../docs/specs/loopcapital-trial-readiness.md),
  9 verification tickets `BH-1246`–`BH-1254`, security gate
  [`SECURITY_REVIEW_GATE.md`](SECURITY_REVIEW_GATE.md), flow diagram
  [`TRIAL_FLOW.md`](TRIAL_FLOW.md).
- **No code written, no repo spun up, no credentials touched.** This entire pass is planning
  artifacts only, per explicit scope.

## 1. What the Trial is

Loop Capital's "Trial Scope & Success Criteria" doc (Doc 1, sent to Frank Sung, VP Data
Management, July 2026) defines a live, allowlisted, TLS-encrypted connection from Brighthive's
hosted demo workspace into Frank's real SQL Server 2019 Azure VM. Read access to in-scope
databases plus SSISDB/ReportServer catalogs and SQL Agent job/disk views; optional governed
write via reviewable PR if a writable target is agreed. Full verbatim capture:
[`artifacts/2026-07-client-docs-trial-scope-and-demo.md`](artifacts/2026-07-client-docs-trial-scope-and-demo.md).

This is explicitly **not** the same thing as the "Your Brighthive Demo — What to Expect" doc
(Doc 2) — that's a separate pre-POC walkthrough on representative/synthetic data in the hosted
demo workspace, tracked in `TRACKER.md`'s "Demo (Doc 2)" phase, out of scope for this statement.

## 2. The 9 success criteria — honest status

Core = 1-4, 7, 8 (the passing bar). Supporting = 5, 6, 9 (strong additional evidence).

| # | Core? | Criterion | Mechanism exists? | Proven against | Verification ticket |
|---|---|---|---|---|---|
| 1 | Core | Connect & catalog | Yes — `sql_server` WarehouseType + discovery (BH-1075/1107/1076) | Sandbox / demo EC2 — **not** Loop Capital's server | `BH-1246` |
| 2 | Core | Data quality + SQL shown | Yes — `quality_check_agent` | Sandbox / demo workspace | `BH-1247` |
| 3 | Core | NL question + SQL shown | Yes — warehouse SQL tooling (BH-1120) | Sandbox / demo workspace | `BH-1248` |
| 4 | Core | Proactive SQL Server health | Yes — `SqlServerPipelineSource` (BH-1045) | **Live-proven** on demo EC2 (`54.197.188.168`) | `BH-1249` |
| 5 | Supporting | SSIS diagnostics | Yes — `analyze_dtsx_package` (BH-823/863/865/866/869, Done) | Synthetic `.dtsx` fixture | `BH-1250` |
| 6 | Supporting | SSRS diagnostics | Yes — `analyze_rdl_report` | Sandbox `.rdl` fixture | `BH-1251` |
| 7 | Core | Autonomy loop, no self-merge | Yes — GC-14..17 (dbt) + `ssis_remediation_agent.py`/BH-1114 (SSIS), both live-proven | dbt Cloud demo stack + sandbox SSIS — **Slack-approval-gate specifically unconfirmed** (only GitHub-PR-review proven) | `BH-1252` |
| 8 | Core | Governed & auditable | Partial — audit trail (BH-695) + human-review proven; **PII tagging is a real code gap** | Partial | `BH-1253` (gated on `BH-1060`) |
| 9 | Supporting | Platform capability (MCP + routine) | Partial — routine-proposal proven live; MCP-external-agent half unproven | Demo-workspace territory | `BH-1254` (gated on `BH-1172`/BH-1038-1041) |

**Reading this honestly**: nearly everything is built and code-level proven. Nothing is proven
against Loop Capital's actual server, because the Trial hasn't connected to it yet — that's the
entire gap this pass's tickets exist to close.

## 3. Blockers — waiting on Loop Capital

Five items, all outstanding, all required before ticket `BH-1246` can leave To Do:

1. Server DNS name or public IP, and confirmation TCP 1433 is reachable from Brighthive's
   provided egress IP.
2. A dedicated, least-privilege SQL Server login (read on in-scope databases; read on
   SSISDB/ReportServer + SQL Agent job/disk views).
3. Which databases are in scope for the trial.
4. Confirmation packages are deployed to SSISDB and reports to the ReportServer catalog, or the
   `.dtsx`/`.rdl` files themselves.
5. A couple of representative "known-bad" artifacts (a flawed SSIS package, a slow SSRS report,
   a quality-issue table) so diagnostics have something Frank recognizes.

Frank indicated the server would be ready "early next week" (per his message referenced at the
top of this session). Tracked live in [`TRACKER.md`](TRACKER.md)'s blockers section.

## 4. The one real code gap: PII tagging (BH-1060)

Not just unproven-on-real-data — an actual gap. `scrub_text()` catches secret-shaped strings
(JWT/API-key patterns) but not customer PII values (names, account numbers, etc.). Doc 1's
criterion 8 requires "PII is tagged" as a core pass/fail bar — running real Loop Capital customer
data through the current pipeline would not satisfy that.

**Escalated this session**: comment posted on `BH-1060` cross-linking `BH-1253`, priority flagged
for the next planning pass. `SECURITY_REVIEW_GATE.md` and the spec's invariants both block
criterion-8 verification and any real-data connection until `BH-1060` reaches at least "Ready for
Dev."

## 5. What's new from this pass

| Artifact | What it is | Link |
|---|---|---|
| Epic `BH-1245` | "Loop Capital Trial Execution" — client-delivery verification, separate from `BH-1036`'s platform-monitoring-engine scope, cross-linked to it | Jira |
| Spec | Defines the `TrialCriterionVerification` record; explicitly adds no new Port/adapter — reuses `PipelineSource`/`SqlServerPipelineSource` unchanged | [`docs/specs/loopcapital-trial-readiness.md`](../../docs/specs/loopcapital-trial-readiness.md) |
| 9 tickets | `BH-1246`–`BH-1254`, one per success criterion, each requiring an `evidence_link` to a real (`verified_against=real_lc_server`) run before Done | Jira, under `BH-1245` |
| Security gate | Named sign-off checklist — least-privilege login, multi-tenant isolation (PS-13), resilience envelope (PS-11), budgets (PS-12), PII readiness — required before any code connects to Loop Capital's real VM | [`SECURITY_REVIEW_GATE.md`](SECURITY_REVIEW_GATE.md) |
| Flow diagram | Trial-specific ASCII happy-path + worst-case branches, deliberately separate from `LOOPCAPITAL.md`'s dbt-Cloud GC-14..17 diagram | [`TRIAL_FLOW.md`](TRIAL_FLOW.md) |
| Client-docs capture | Verbatim condensed capture of Doc 1 + Doc 2, the source of truth this whole pass reconciles against | [`artifacts/2026-07-client-docs-trial-scope-and-demo.md`](artifacts/2026-07-client-docs-trial-scope-and-demo.md) |
| Tracker | `TRACKER.md`/`poc.yaml` regenerated via `scripts.poc_tracker` — Trial (Doc 1) phase now links all 9 criteria to real tickets, not `_manual_` placeholders | [`TRACKER.md`](TRACKER.md#trial-doc-1--9-numbered-success-criteria) |
| `LOOPCAPITAL.md` | Cross-linked to the new epic/spec/tickets; discrepancy flag (§6 below) preserved, not resolved | [`../../LOOPCAPITAL.md`](../../LOOPCAPITAL.md) |

## 6. Open question — not resolved by this pass

`LOOPCAPITAL.md`'s internal GC-14..17 flow is scoped to **dbt Cloud**. Doc 1 and Doc 2 both
describe **SQL Server 2019 / SSIS / SSRS** — no dbt Cloud mention in either. This may be two
different workloads for the same client, or the internal framing may need to be re-pointed at the
SQL Server stack. Flagged in `LOOPCAPITAL.md`, the new spec, and `TRIAL_FLOW.md`. **Needs Kuri's
confirmation before any doc treats these as the same engagement.**

## 7. What happens next

1. Kuri resolves the dbt-vs-SQL-Server engagement question (§6).
2. Loop Capital provides the 5 blockers (§3).
3. `SECURITY_REVIEW_GATE.md` signed off by name (§4/§3 of that doc).
4. Verification tickets `BH-1246`–`BH-1254` move out of To Do, each producing a
   `TrialCriterionVerification` record with `verified_against=real_lc_server` as evidence.
5. Separately, and not gated on the above: local-stack spin-up
   (`brightbot`/`brighthive-platform-core`/`brighthive-webapp` on `develop` against staging, per
   `platform-saas-ai-context/docs/infrastructure/RUN_LOCAL_AGAINST_STAGING.md`) — a future phase,
   not part of this pass, not started.

No code was written and no credentials were touched to produce this statement or the artifacts
it aggregates.
