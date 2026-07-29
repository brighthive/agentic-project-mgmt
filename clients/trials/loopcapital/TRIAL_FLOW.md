# Loop Capital — Trial (Doc 1) Flow, Happy Path + Worst-Case Branches (BH-1245)

> This is the **Trial** flow — the live SQL Server 2019 connection into Loop Capital's real
> Azure VM, per "Trial Scope & Success Criteria." It is deliberately a separate doc from
> [`LOOPCAPITAL.md`](../../LOOPCAPITAL.md), which maps the internal **GC-14..17 dbt-Cloud** flow.
> Do not conflate the two — see the table below and `LOOPCAPITAL.md`'s own "three things this
> doc's ecosystem covers" section.
>
> Spec: [`docs/specs/loopcapital-trial-readiness.md`](../../docs/specs/loopcapital-trial-readiness.md)
> · Security gate: [`SECURITY_REVIEW_GATE.md`](SECURITY_REVIEW_GATE.md) · Tickets: BH-1246–BH-1254
> under epic BH-1245.

## What this doc covers, and what it doesn't

| # | Doc | Covers |
|---|---|---|
| (a) | [`LOOPCAPITAL.md`](../../LOOPCAPITAL.md) | Internal GC-14..17 — dbt Cloud job fails → detect → alert → surgical PR → merge → verify. **Not this doc.** |
| (b) | Doc 2 ("Your Brighthive Demo") | Hosted demo workspace, representative data. **Not this doc.** |
| (c) | **This doc** | The Trial (Doc 1) — live SQL Server 2019 connection, Loop Capital's real Azure VM, 9 numbered success criteria. |

## The flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  HAPPY PATH: blockers cleared → connected → catalog → quality → NL → health →       │
│              real issue detected → autonomy loop → Slack-approved → audited         │
└─────────────────────────────────────────────────────────────────────────────────────┘

  [0] Loop Capital provides the 5 blocking items (per Doc 1's "What we'll need from you"):
      server DNS/IP, dedicated least-privilege SQL login, in-scope DB list,
      SSISDB/ReportServer confirmation (or .dtsx/.rdl files), known-bad artifacts
           │
           ▼
  [0.5] SECURITY_REVIEW_GATE.md signed off BY NAME — least-privilege login confirmed,
        multi-tenant isolation (PS-13), resilience envelope (PS-11), budgets (PS-12),
        BH-1060 (PII) at least "Ready for Dev"
           │
           ▼
  [1] BrightAgent connects over the allowlisted egress IP, TLS
      → CRITERION 1: browsable catalog produced (BH-1246)
           │
           ▼
  [2] quality_check_agent authors + runs checks on chosen tables
      → CRITERION 2: score + report + generated SQL + root cause (BH-1247)
           │
           ▼
  [3] NL business question asked against real data
      → CRITERION 3: answered correctly, SQL shown (BH-1248)
           │
           ▼
  [4] SqlServerPipelineSource polls the real server on a cadence
      → CRITERION 4: names the actual failed job / disk-pressure condition,
        unprompted (BH-1249) — mechanism already live-proven on demo EC2,
        this step proves it on LC's own server
           │
           ▼
  [5] (supporting) analyze_dtsx_package / analyze_rdl_report run against real
      SSISDB/ReportServer content or supplied files
      → CRITERIA 5/6: true structural issue / anti-pattern found (BH-1250/1251)
           │
           ▼
  [6] A real issue is detected on the real server → autonomy loop starts
      (scheduled_agent_dispatcher → remediation graph)
           │
           ▼
  [7] Agent opens a governed surgical PR
      → PAUSES for approval **in Slack** (not just GitHub PR review)
      → structurally unable to self-merge (GC-17 mechanism, reused unchanged)
      → CRITERION 7 (BH-1252)
           │
           ▼
  [8] Frank's team approves/denies in Slack → human merges in GitHub
           │
           ▼
  [9] Every step above logged to the tamper-evident audit trail; PII in any
      surfaced data is tagged (not just secret-shaped strings — requires
      BH-1060 resolved)
      → CRITERION 8 (BH-1253)


┌─────────────────────────────────────────────────────────────────────────────────────┐
│  WORST-CASE BRANCHES                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────┘

  AT [0] — Loop Capital provides an over-broad SQL login (write access beyond scope)
      │
      ▼
  ⚠ WITHOUT SECURITY_REVIEW_GATE.md: over-scoped credential gets used as-is →
      violates Doc 1's own "least-privilege" commitment to Frank
  ✅ WITH the gate: reject and re-request before any connection is attempted

  AT [1] — LC's dedicated login lacks SSISDB/ReportServer read
      │
      ▼
  ⚠ Criteria 5/6 cannot run against the live catalog
  ✅ Falls back to blocker item 4's alternative: Frank supplies the .dtsx/.rdl
      files directly — same diagnostic tools, different input path

  AT [7] — Slack approval times out or is denied
      │
      ▼
  ⚠ UNTESTED PATH (only GitHub-PR-review has been live-proven so far, via
      GC-17/BH-1114) — if the agent or dispatcher treats "no Slack response"
      as implicit approval, that's a governance failure
  ✅ MUST NOT auto-merge or silently retry on timeout/denial — this is the
      specific thing BH-1252's verification exists to confirm, not assume

  AT [9] — real customer PII flows through scrub_text() before BH-1060 lands
      │
      ▼
  ⚠ scrub_text() only catches secret-shaped strings (JWT/API-key patterns) —
      a real customer name/account number would NOT be tagged
  ✅ SECURITY_REVIEW_GATE.md blocks this: criterion 8 verification (BH-1253)
      is explicitly gated on BH-1060 reaching "Ready for Dev" first
```

## Status as of 2026-07-28

Trial not started. All 5 blocking items in [0] are outstanding — see
[`TRACKER.md`](TRACKER.md)'s blockers section. Nothing in this flow has run against Loop
Capital's real server; every mechanism referenced (steps 1-9) is proven against a sandbox or
demo-EC2 stand-in only, per `docs/specs/loopcapital-trial-readiness.md` §1's status table.
