# Loop Capital — E2E Flow, Happy Path + Worst-Case Branches (BH-1036)

> One-page map of the 7/17 demo's actual mechanism: what fires, in what order, and every
> failure mode found by this session's architecture trace, folded into the same diagram.
> Deep specs: [`docs/specs/golden-cases-loopcapital.md`](docs/specs/golden-cases-loopcapital.md)
> (GC-14–17, the demo bars) · [`docs/specs/proactive-pipeline-ingestion-monitoring.md`](docs/specs/proactive-pipeline-ingestion-monitoring.md)
> (the platform contract) · [`docs/specs/self-healing-pipelines.md`](docs/specs/self-healing-pipelines.md)
> (the surgical-PR mechanism GC-16 reuses) · sandbox: [`clients/trials/loopcapital/sandbox/`](clients/trials/loopcapital/sandbox/)
>
> **For the Trial (Doc 1) specifically** — the live SQL Server 2019 connection into Loop
> Capital's real Azure VM — start at
> [`clients/trials/loopcapital/TRIAL_STATEMENT.md`](clients/trials/loopcapital/TRIAL_STATEMENT.md),
> the consolidated readiness snapshot. This doc covers the internal GC-14..17 dbt-Cloud
> mechanism only (see the "three things" table below).

## What it is

A dbt Cloud job fails. BrightAgent detects it without being asked, alerts Frank's team on
Slack + webapp within 15 minutes, and — if the root cause is a known data-shape drift —
opens a human-reviewed surgical PR. Nothing merges itself. Once merged, BrightAgent checks
whether the fix actually worked and says so honestly either way.

## Three things this doc's ecosystem now covers — do not conflate

Two new client-facing documents were sent to Frank Sung (VP, Data Management, Loop Capital)
in July 2026 — captured verbatim in
[`clients/trials/loopcapital/artifacts/2026-07-client-docs-trial-scope-and-demo.md`](clients/trials/loopcapital/artifacts/2026-07-client-docs-trial-scope-and-demo.md).
This doc's scope now spans three distinct things:

| # | What | Data / environment | Source |
|---|---|---|---|
| (a) | **Internal GC-14..17 flow** (this doc, below) — dbt Cloud job fails → detect → alert → surgical PR → merge → verify | Internal sandbox (`clients/trials/loopcapital/sandbox/`), dbt Cloud pipeline | `docs/specs/golden-cases-loopcapital.md`, 7/17 internal demo rehearsal |
| (b) | **The Demo** ("Your Brighthive Demo — What to Expect") — pre-POC guided walkthrough, governed multi-agent workflow, MCP + OSI preview | Hosted Brighthive demo workspace, representative/synthetic data (incl. sample legacy SSIS/SSRS artifacts) | Doc 2, artifacts file above |
| (c) | **The Trial** ("Trial Scope & Success Criteria") — live SQL Server 2019 connection, 9 numbered success criteria | Loop Capital's actual Azure VM (Windows Server 2019, SQL Server 2019), allowlisted egress IP over TLS | Doc 1, artifacts file above — flow diagram: [`clients/trials/loopcapital/TRIAL_FLOW.md`](clients/trials/loopcapital/TRIAL_FLOW.md), spec: [`docs/specs/loopcapital-trial-readiness.md`](docs/specs/loopcapital-trial-readiness.md), epic: `BH-1245` |

**⚠ Unresolved discrepancy — flagged, not guessed at.** (a)'s internal flow uses **dbt Cloud**
as the pipeline under test. (c)'s Trial doc describes **SSIS / SSRS / SQL Server 2019**
(with POC-deferred ADF / Synapse / Databricks / Snowflake Cortex) — no dbt Cloud mention
anywhere in Doc 1 or Doc 2. These may be **two different workloads for the same client** (a
dbt Cloud demo vs. a SQL Server/SSIS trial), or the internal framing may need to be
re-pointed at the SQL Server stack. **This needs confirmation with Kuri — do not assume
either way.** Until resolved, treat (a) as internal-demo-only and (c) as the client's actual
trial scope; the flow diagram below is left as-is (see "Status" section for why).

**Client-delivery tracking for (c) now lives under its own epic**, `BH-1245` ("Loop Capital
Trial Execution") — separate from this doc's `BH-1036` (the monitoring-engine epic), since
proving the 9 criteria against Loop Capital's real server is client-delivery verification
work, not platform-monitoring-engine work. `BH-1036`'s mechanisms are what gets verified;
`BH-1245`'s 9 tickets (BH-1246–BH-1254) do the verifying. See
[`docs/specs/loopcapital-trial-readiness.md`](docs/specs/loopcapital-trial-readiness.md).

## The flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  HAPPY PATH: dbt job fails → detected → alerted → fixed → merged → confirmed        │
└─────────────────────────────────────────────────────────────────────────────────────┘

  [1] dbt Cloud job fails
      real transform error, status=20 (Error)
           │
           ▼
  [2] BH-1054 watchdog polls (scheduled dispatcher, deterministic StateGraph
      — NOT an LLM agent run, confirmed safe this session)
           │
           ▼
  [3] BH-1043 detects failure, emits PipelineHealthSignal
      root_cause_class = DATA_SHAPE
           │
           ▼
  [4] BH-1046 dual-writes: Slack (#brighthive-ops) + webapp Notifications
      BH-1067/1087 render real model_name/job_id/error/log_id
           │
           ▼
  [5] Frank's team sees it within 15 min — BEFORE the morning SSRS run
           │
           ▼
  [6] BH-1047 remediation loop: agent run starts (scheduled_agent_dispatcher
      → dbt_agent_react_graph, LLM-driven — the ONE non-deterministic hop)
           │
           ▼
  [7] Agent decides to call the PR tool, opens surgical PR
      GC-17 gate: github_merge_pull_request NOT bound → cannot self-merge
           │
           ▼
  [8] Human reviews in GitHub, merges
           │
           ▼
  [9] BH-1091: cooldown → VERIFYING state, next poll in ~15 min (not full 1hr)
           │
           ▼
  [10] Signal GONE → success confirmation posted on SAME alert thread
      "the fix you merged worked" — Frank's team gets closure, not silence


┌─────────────────────────────────────────────────────────────────────────────────────┐
│  WORST-CASE BRANCHES — where this pass's audits found the happy path was assumed    │
│  to hold and DIDN'T, until closed                                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘

  AT [1] — job was CANCELLED by a human (status=30), not a real failure
      │
      ▼
  ⚠ WITHOUT Invariant 19 (BH-1043): treated same as a real failure → false alert
      → Frank's team learns to ignore BrightAgent ("cried wolf")
  ✅ WITH Invariant 19: status=30 checked explicitly → NO signal emitted, silence
      is correct here (this is the one place silence is the RIGHT answer)

  AT [6]→[7] — agent run starts but model NEVER CALLS the PR tool
      (prompt fails to elicit the tool call — a real, distinct failure mode)
      │
      ▼
  ⚠ WITHOUT BH-1092: dispatcher sees "run completed" = success. NO PR opens.
      NOTHING notices. Silent no-op — worse than a visible error.
  ✅ WITH BH-1092: PRExistenceCheck (deterministic, no LLM judge) confirms a PR
      matching the signature actually exists within the window → if not,
      alert "the agent was asked to fix this and did not"

  AT [7] — model DOES call the merge tool (adversarial prompt / model error)
      │
      ▼
  ⚠ WITHOUT GC-17 code-level exclusion: prompt-only "never merge" instruction
      is a PERMISSION, not a prohibition (confirmed: dbt_react_system_prompt.py
      actually says "merge when the user asks") → could self-merge
  ✅ WITH GC-17 (BH-1047): github_merge_pull_request absent from
      REMEDIATION_TOOLS by construction → merge attempt fails at the
      BINDING layer, not because the model behaved

      ↳ Cross-ref: this code-level exclusion is what satisfies the client's
        success criterion 7 ("cannot approve its own change") and feeds
        criterion 8's audit trail — see the success-criteria table below.

  AT [8] — human merges, but the fix is WRONG (doesn't actually resolve it)
      │
      ▼
  ⚠ WITHOUT BH-1091: Invariant 3's cooldown key is keyed on the FAILURE
      SIGNATURE, not "was it resolved" → same signature recurs → SILENTLY
      SUPPRESSED for up to 1hr. Frank's team thinks it's fixed. It isn't.
  ✅ WITH BH-1091: VERIFYING state polls sooner; if signature RECURS →
      immediate escalation, bypassing normal cooldown, explicitly stating
      "the fix merged on {date} did not resolve this" — NEVER a second
      auto-fix attempt without going through the SAME human gate again

  AT [2] — SQL Server disk-space variant (GC-15), same watchdog, different source
      │
      ▼
  ⚠ workspace has 2+ SQL Server connections → Invariant 16 gap: could
      silently poll only the first, second instance never monitored
  ✅ Invariant 16 + 18: explicit multi-connection disambiguation + stable
      per-connection job_id so instances don't share/collide a cooldown key
```

## What's demo-gating for 7/17 vs. not

| Branch | Demo-gating? | Why |
|---|---|---|
| Cancelled-run suppression (Invariant 19) | **Yes** | Can surface live if anyone on Frank's team touches a job during the demo window |
| GC-17 code-level auto-merge exclusion | **Yes** | GC-16 cannot be demoed safely without it |
| BH-1091 (post-merge verification) | No | Needs hours/days to surface — the demo window is far shorter than the cooldown periods this reasons about |
| BH-1092 (PR-existence verification) | No | Same reasoning — a probabilistic gap that needs a full remediation cycle to manifest |
| GC-15 multi-connection disambiguation | No | Loop Capital's real demo workspace connection count still needs confirming — see Open Blockers in [`clients/trials/loopcapital/overview.md`](clients/trials/loopcapital/overview.md) |

## Client-facing success criteria (Trial, Doc 1)

9 numbered criteria from `2026-07-client-docs-trial-scope-and-demo.md`. **Core = 1–4, 7–8**
(5, 6, 9 are supporting evidence, not pass/fail).

| # | Core? | Criterion (condensed) | Maps to internal mechanism |
|---|---|---|---|
| 1 | Core | Connect & catalog SQL Server over allowlisted link, browsable catalog fast | Not covered by GC-14..17 (dbt-scoped) — needs SQL Server connector work — verified by BH-1246 |
| 2 | Core | Data quality checks on their tables, score + report + SQL shown | Not covered by GC-14..17 — quality-agent capability exists per Doc 2 demo bullets — verified by BH-1247 |
| 3 | Core | Plain-language question answered correctly, SQL shown | Not covered by GC-14..17 — verified by BH-1248 |
| 4 | Core | Proactive SQL Server health — names the actual job/disk failure | Analogous in spirit to GC-15 (SQL Server disk-space variant, watchdog-driven) but GC-15 is **not demo-gating** per table above — verified by BH-1249 |
| 5 | Supporting | SSIS diagnostics — ≥1 true structural issue on a package | Not covered by GC-14..17 — verified by BH-1250 |
| 6 | Supporting | SSRS diagnostics — ≥1 true anti-pattern on a report | Not covered by GC-14..17 — verified by BH-1251 |
| 7 | Core | **Autonomy loop (headline)** — detect → diagnose → governed PR → pause for approval → cannot self-approve | **GC-16/GC-17** (surgical PR + code-level auto-merge exclusion) satisfies this directly — verified by BH-1252 |
| 8 | Core | Governed & auditable — tamper-evident trail, PII tagged, nothing written without review | **GC-17**'s binding-layer exclusion is one input; PII tagging is a real gap (`BH-1060`, escalated) — verified by BH-1253 |
| 9 | Supporting | Platform capability — external agent via MCP + BrightAgent proposes a recurring routine | Not covered by GC-14..17 — this is Doc 2 demo territory (MCP/OSI preview) — verified by BH-1254 |

**Read this table honestly**: only criteria 7 and part of 8 have a direct internal-mechanism
match in this doc's GC-14..17 flow. Criteria 1–6 and 9 are either SQL Server/SSIS-stack work
not yet represented here, or Demo-doc (b) territory. This is the practical shape of the
dbt-Cloud-vs-SQL-Server discrepancy flagged above — resolve with Kuri before assuming GC-14..17
covers more of the Trial than criteria 7–8. Every mechanism above is proven only against a
sandbox/EC2 stand-in — none of it has run against Loop Capital's real server yet. The 9
verification tickets (BH-1246–BH-1254, epic `BH-1245`) close that gap; see
[`TRIAL_FLOW.md`](clients/trials/loopcapital/TRIAL_FLOW.md) for the dedicated Trial-path
diagram and [`SECURITY_REVIEW_GATE.md`](clients/trials/loopcapital/SECURITY_REVIEW_GATE.md)
for the sign-off required before any real connection.

## Tickets, in build order

`BH-1042` (contract) → `GC-17`/`BH-1047`'s exclusion (zero deps, cheapest) → `BH-1043`+`BH-1045`
(parallel adapters) → `BH-1054` (watchdog wiring) → `BH-1046`+`BH-1067`+`BH-1087` (make the
alert visible) → dress rehearsal against the real sandbox. `BH-1091`/`BH-1092` after the demo,
not before.

## Status as of 2026-07-13

Zero code. Every ticket above is `Needs Refinement` in Jira. The sandbox
(`clients/trials/loopcapital/sandbox/`) is built and verified — real Docker SQL Server, real
SSIS/SSRS fixtures, a real profiler script, a `reset.py` for reseeding named scenarios
(`baseline`/`disk-pressure`/`type-drift`/`cancelled-run`). BH-1057/1058's remaining work is
executing that sandbox in the real demo environment and creating one dbt Cloud fixture job —
neither is code.

## Status as of 2026-07-28

Two client-facing documents received — "Trial Scope & Success Criteria" (Doc 1, live SQL
Server 2019 connection, 9 numbered success criteria) and "Your Brighthive Demo — What to
Expect" (Doc 2, pre-POC hosted-workspace walkthrough). Full verbatim capture:
[`clients/trials/loopcapital/artifacts/2026-07-client-docs-trial-scope-and-demo.md`](clients/trials/loopcapital/artifacts/2026-07-client-docs-trial-scope-and-demo.md).

This doc was reconciled against both: added the three-things-covered section near the top,
cross-referenced GC-16/17's auto-merge exclusion to success criterion 7/8, and added the
success-criteria mapping table above. The flow diagram and GC-14..17 mechanism content below
were **not edited** — no line in them is factually contradicted by the new docs, only
potentially scoped to a different pipeline (dbt Cloud vs. SQL Server/SSIS). That stack
question is still open — see the discrepancy flag near the top of this doc — and is not
resolved by this pass. Sandbox and ticket status otherwise unchanged since 2026-07-13.

## Status as of 2026-07-28 (planning pass)

Full docs/specs/tickets/epic/diagram pass completed for the Trial (Doc 1):

- New epic `BH-1245` "Loop Capital Trial Execution" — separate from `BH-1036`, cross-linked.
- New spec [`docs/specs/loopcapital-trial-readiness.md`](docs/specs/loopcapital-trial-readiness.md)
  — defines a `TrialCriterionVerification` record shape; no new Port/adapter code.
- 9 verification tickets `BH-1246`–`BH-1254` under `BH-1245`, one per success criterion.
- `BH-1060` (PII tagging) escalated — real code gap for criterion 8, not just unproven-on-real-data.
- New [`clients/trials/loopcapital/SECURITY_REVIEW_GATE.md`](clients/trials/loopcapital/SECURITY_REVIEW_GATE.md)
  — named sign-off required before any code connects to Loop Capital's real server.
- New [`clients/trials/loopcapital/TRIAL_FLOW.md`](clients/trials/loopcapital/TRIAL_FLOW.md) —
  dedicated Trial-path ASCII flow, separate from this doc's dbt-Cloud GC-14..17 diagram.

No code written, no repo spun up, no credentials touched — planning artifacts only, per this
pass's explicit scope. Trial itself remains blocked on Loop Capital providing 5 items (server
DNS/IP, login, DB list, SSISDB/ReportServer confirmation or files, known-bad artifacts).
