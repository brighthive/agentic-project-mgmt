# Loop Capital — E2E Flow, Happy Path + Worst-Case Branches (BH-1036)

> One-page map of the 7/17 demo's actual mechanism: what fires, in what order, and every
> failure mode found by this session's architecture trace, folded into the same diagram.
> Deep specs: [`docs/specs/golden-cases-loopcapital.md`](docs/specs/golden-cases-loopcapital.md)
> (GC-14–17, the demo bars) · [`docs/specs/proactive-pipeline-ingestion-monitoring.md`](docs/specs/proactive-pipeline-ingestion-monitoring.md)
> (the platform contract) · [`docs/specs/self-healing-pipelines.md`](docs/specs/self-healing-pipelines.md)
> (the surgical-PR mechanism GC-16 reuses) · sandbox: [`clients/trials/loopcapital/sandbox/`](clients/trials/loopcapital/sandbox/)

## What it is

A dbt Cloud job fails. BrightAgent detects it without being asked, alerts Frank's team on
Slack + webapp within 15 minutes, and — if the root cause is a known data-shape drift —
opens a human-reviewed surgical PR. Nothing merges itself. Once merged, BrightAgent checks
whether the fix actually worked and says so honestly either way.

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
