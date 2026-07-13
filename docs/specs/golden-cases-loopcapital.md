<!--
  Frontmatter intentionally uses brightbot's SPEC-GOLDEN-CASES.md template
  (spec-id/status/owner/trial), NOT docs/specs/SPEC_TEMPLATE.md's shape
  (title/epic/author/created/generates/tags) — this doc extends that
  sibling template's Golden Case format, the same way brightbot's own
  file does. Flagged by review (docs/AGENTS.md says specs use
  SPEC_TEMPLATE.md); noting the deviation explicitly here rather than
  force-fitting an unrelated template shape onto a Golden Case catalog.
-->
---
spec-id: SPEC-GOLDEN-CASES-LOOPCAPITAL
status: draft
last-reviewed: 2026-07-13
owner: drchinca
trial: loopcapital
related:
  specs:
    - proactive-pipeline-ingestion-monitoring.md
    - lineage-aware-data-quality.md
    - self-healing-pipelines.md
  tickets: [BH-1042, BH-1043, BH-1045, BH-1046, BH-1047, BH-1054, BH-1057, BH-1058, BH-1067, BH-1087]
---

# SPEC-GOLDEN-CASES-LOOPCAPITAL — Loop Capital Trial Bars

> Loop Capital had **zero** Golden Cases before this spec — every "GC-11"/"GC-12" mention in
> `clients/trials/loopcapital/` cites Longaeva's cases as mechanism precedent, never as a Loop
> Capital-scoped bar. This spec mints the first ones, continuing the numbering from brightbot's
> `docs/specs/golden-cases/SPEC-GOLDEN-CASES.md` (GC-1 through GC-13, all Longaeva) so `GC-N`
> stays a single global namespace across clients rather than forking per-trial numbering.
>
> Each case below maps 1:1 to a real commitment: the first 3 are Suzanne's literal reply to
> Frank (the 2026-07-17 demo gate); GC-17 is the safety precondition that gates GC-16's
> mechanism regardless of demo timing. **None of these are ⭐ trial demo-bars in the
> Longaeva sense** — they're demo-gated on a hard date, which is a stricter bar than Longaeva's
> open-ended trial window.

## Index

| GC | Title | Bar | Status today | Demo-gating? |
|---|---|---|---|---|
| GC-14 | Proactive monitor/detect/alert loop | Frank's ops team learns their nightly Asset Management dbt job broke BEFORE a portfolio manager asks why the SSRS holdings report looks wrong — via Slack + webapp, without anyone asking BrightAgent first | spec landed (BH-1042/1043/1046/1054/1087), zero code — webapp detail-parity (BH-1087) is a real, scoped 3-5hr build, not an open question | **Yes — 7/17** |
| GC-15 | SQL Server disk-space monitoring with no MCP | BrightAgent catches Loop's legacy SQL Server running low on disk — the exact box Frank said has no MCP and no BrightHive software installed — before SSIS jobs start failing from lack of space | spec landed (BH-1045), fixture BUILT + verified working (`clients/trials/loopcapital/sandbox/`, Docker SQL Server — replaces the original AWS RDS plan), BH-1045's own disk/job-status logic still zero code | **Yes — 7/17** |
| GC-16 | Fix-recurrence surfacing via surgical PR | when the same class of pipeline break recurs, Frank's team gets a reviewable PR with a plain-language diagnosis instead of re-diagnosing from scratch — they merge it, BrightAgent never does | spec landed (BH-1047 reuses GC-11's mechanism), zero code, **BLOCKED on GC-17** | **Yes — 7/17** |
| GC-17 | Auto-merge exclusion (safety precondition) | there is no code path by which BrightAgent can merge its own fix into Loop's pipeline — the one failure mode that would turn "careful digital coworker" into "software that changes our data without asking," and lose the deal | **CRITICAL, no code** — confirmed `github_merge_pull_request` still bound into `dbt_agent_react.py`'s `DBT_REACT_TOOLS` (brightbot, `dbt_agent_react.py`) | Gates GC-16, not independently demoed |

## How to read each GC

Extends the template from `brightbot/docs/specs/golden-cases/SPEC-GOLDEN-CASES.md` with one
change: **Acceptance** here is written as a real scene at Loop Capital first — Frank, a named
pipeline, a real business consequence — with the underlying DTOs/invariants demoted to a "what
proves this, underneath" note. A platform-feature Gherkin scenario ("a PipelineHealthSignal is
emitted") is necessary for the harness but insufficient for the demo — it proves the code path
exists, not that it resolves something Frank actually asked for. Each GC still carries: **Bar**
(customer promise, plain English), **Code path** (file:line or "no code"), **Interface contract**,
**Invariants**, **Acceptance** (the scene + Gherkin + underlying proof), **Validation** (pointer
to `tests/integration/golden_cases/test_gc_NN_<slug>.py` in brightbot, once filed — none exist yet
for these four).

---

## GC-14 — Proactive monitor/detect/alert loop

### Bar
Suzanne's demo commitment #1, verbatim: "the engineering agent and how it proactively monitors,
detects and resolves issues with the ability to alert the user on what it finds." Concretely: a
real dbt Cloud job failure is detected without a human prompting the agent, and the failure is
visible on both Slack and the webapp within one poll cycle.

### Status today
**Spec landed, zero code.** `proactive-pipeline-ingestion-monitoring.md` fully specifies the
contract (§2 `PipelineSource` Protocol, `PIPELINE_SOURCE_ADAPTERS` registry, `PipelineHealthSignal`
DTO — BH-1042) and 18 invariants, but BH-1043 (dbt poller), BH-1046 (dual-write alert path), and
BH-1054 (watchdog node registration on the existing scheduled dispatcher) are all unimplemented.
BH-1067 (renderer for 5 of 6 stage values) is also unimplemented for those 5 — without it, a
detected failure on those stages would dual-write successfully but render as blank text on both
surfaces, per that spec's Invariant 15.

**The 6th stage, `dbt_run_failure` (this GC's own bar), is a narrower and cheaper gap — resolved
here, corroborated against real platform-core/webapp code, not left open:** brightbot-slack-server
already has a real renderer (`renderDbtFailureDetails`); the webapp side does not — no detail
builder exists in platform-core's `sources` registry for `dbt_run_failure` (it's `{category:
'dbt'}` only), so today's webapp Notifications card falls through to a generic label. **This is
real, buildable capacity, not a hypothetical** — `quality_asset_result`'s existing registry entry
(`formatQualityDisplay`/`buildQualityDetail`, `notifications.ts:243-244`) is a directly-copyable
template: same signal-metadata-to-detail-object shape, no new GraphQL types, no schema migration.
On webapp, `QualityNotificationCard.tsx` is the card-with-detail template to adapt (vs.
`GenericNotificationCard.tsx`, what `dbt_run_failure` renders through today). Estimated 3-5 hours
end to end (formatter + detail builder in platform-core, a new card + registry entry in webapp,
one smoke test against a staging signal) — a single-afternoon build, not a multi-day one.

**CORRECTING A REAL BUG THIS AUDIT FOUND, not just a doc gap**: BH-1046's own ticket text asserts
"the formatter already exists per BH-1067's own verification" and frames its scope as "verify the
existing renderer fires correctly" — that premise is FALSE for the webapp half; only Slack has a
renderer. BH-1067 compounds this by explicitly excluding `dbt_run_failure` from its own scope,
"mirroring dbt_run_failure's existing pattern" — a pattern that, on webapp, does not exist.
**Resolved, not left open**: filed **BH-1087** for the corrected scope (add `formatDbtDisplay`/
`buildDbtDetail` to platform-core's registry + a detail card to webapp, ~3-5 hours), and added
correcting comments to BH-1046 and BH-1067 so this gap doesn't silently fall through either
ticket's scope a third time.

### Code path
No code. Contract only: `proactive-pipeline-ingestion-monitoring.md` §2 (`PipelineSource`,
`PipelineHealthSignal`, `PIPELINE_SOURCE_ADAPTERS`).

### Interface contract
Reused verbatim from the handover spec — no new types for this GC:
```python
class PipelineSource(Protocol):
    async def poll_health(self, *, ctx: RequestContext) -> list[PipelineHealthSignal]: ...

PIPELINE_SOURCE_ADAPTERS: dict[str, type[PipelineSource]] = {
    DBT: DbtPipelineSource,
    DATABRICKS: DatabricksPipelineSource,
    ETL_GENERIC: EtlGenericPipelineSource,
}
```

### Invariants
Inherits `proactive-pipeline-ingestion-monitoring.md` §3 Invariants 1 (dual-write), 3 (4-tuple
cooldown key), 15 (renderer-required), 17 (exact `model_name`/`job_id`/`error`/`log_id` metadata
keys), and 19 (cancelled runs never alert — added this pass) as the ones this GC's harness must
assert against.

### Acceptance — Frank's real Monday morning

**The scene**: Frank's ops team runs a nightly dbt job that rebuilds Loop's Asset Management
staging tables from the legacy SSIS-fed SQL Server extract, ahead of the morning SSRS holdings
report going out to portfolio managers. Tonight, that job fails partway through — a source table
changed shape and the transform errored. Nobody at Loop is watching a dashboard at 2am.

```gherkin
Scenario: Frank's team learns about a broken pipeline before the portfolio managers do
  Given the nightly Asset Management dbt job fails at 2:14am with a real transform error
  And no one at Loop Capital has opened BrightAgent or asked about this job
  When BrightAgent's watchdog runs its next scheduled check — target: within 15 minutes of the
    failure, the cadence BH-1054's dispatcher is expected to run at for job-status checks (the
    exact number is still an implementer decision as of this spec — see the sibling spec's
    Invariant 12 — but 15 minutes is the bar this GC is written against, not an open question)
  Then a message lands in Loop's #brighthive-ops Slack channel naming the job, the model that
    broke, and the error — in time for Frank's team to see it well before the morning SSRS run
  And Frank's team knows, from that one Slack message alone, WHICH holdings numbers are stale —
    before a portfolio manager asks why the SSRS report looks wrong

Scenario: BrightAgent doesn't spam Frank's team on every retry
  Given the same job fails again on its next scheduled retry, less than an hour after the first
    failure (Invariant 3's cooldown window)
  When the watchdog polls again
  Then Loop's ops channel gets ONE actionable alert for this incident, not one per retry —
    Frank's team should never learn to ignore BrightAgent because it cried wolf

Scenario: BrightAgent doesn't alert on a run Frank's own team intentionally cancelled
  Given someone on Frank's team manually cancels a dbt run mid-flight for a planned reason
    (e.g. a maintenance window) — not a genuine pipeline failure
  When the watchdog observes this run's terminal status
  Then no alert fires — a cancelled-by-a-human run is not treated the same as a failed run
  And this distinction is what keeps every alert BrightAgent sends trustworthy enough that
    Frank's team acts on it, rather than second-guessing whether it's real
```

**What proves this, underneath**: a `PipelineHealthSignal` is emitted for the failed run, the
dual-write reaches BOTH brightbot-slack-server and brighthive-webapp Notifications (Invariant 1).
Webapp parity for the 4 detail fields (`model_name`/`job_id`/`error`/`log_id`) is currently UNBUILT
(see Status today) — tracked as **BH-1087**, a real, scoped, 3-5-hour build, not an open design
question. Until BH-1087 lands, this scenario's webapp claim is aspirational, not yet demoable;
the Slack half is real once BH-1043/1046/1054 ship. **The third scenario (cancelled-run
suppression) is now tracked, not an open gap**: added Invariant 19 to the sibling spec and a
corresponding comment on BH-1043 — `_fetch_run_status` (`dbt_cloud_tools.py:125-197`) already
reads dbt Cloud's real status taxonomy (`10=Success, 20=Error, 30=Cancelled`); the fix is a
status-code branch on an already-read field, not new capability. Still unbuilt, like the rest
of GC-14, but no longer zero-ticket.

### Validation
**Filed** (2026-07-13, brightbot PR #811): `brightbot/tests/integration/golden_cases/test_gc_14_proactive_monitor_alert.py`
— one main verdict-recording test + 3 documented sub-case stubs (dual-write, retry-storm
suppression, cancelled-run suppression). All 4 currently `pytest.skip` until BH-1043/1046/1054/
1067/1087 land — verified they collect and skip cleanly, zero collection errors.

---

## GC-15 — SQL Server disk-space monitoring with no MCP

### Bar
Suzanne's demo commitment #2, Frank's literal named example: "how MCP will connect to the SQL
server when the server does not have an MCP... monitoring the disk space and alerting when it's
at 20% capacity left." Direct rebuttal to Frank's stated disbelief this is technically possible —
must run against a real SQL Server instance, not a mock (per `test-behavior-real.md`), since a
mocked page is exactly what triggered his "this is not live" reaction on 2026-07-09.

### Status today
**Fixture BUILT and verified working; BH-1045's actual query logic still zero code.**
**Superseded the original AWS RDS plan** — BH-1057 is now a local Docker SQL Server sandbox
(`clients/trials/loopcapital/sandbox/`), avoiding a billable cloud resource for a demo fixture.
Confirmed real, not a mock: `SynapseConnection` cannot tell the difference between this container
and production SQL Server. Two real Docker-specific gaps were researched and resolved (not
assumed) — SQL Server Agent is off by default in the `mssql-server` image (`MSSQL_AGENT_ENABLED=
true` fixes it) and `sys.dm_os_volume_stats` reports the container's REAL mounted volume, not a
fabricated number (a fixed-size `tmpfs` mount + a filler script gets it to the real 18% free
threshold). **Verified end-to-end, 2026-07-13, not claimed**: `./setup.sh` + `./validate.sh` both
of BH-1045's confirmed query texts against the running container, real results both times (disk
query returned `17.99` percent_free; job-status query returned one real Succeeded and one real
Failed run). BH-1045 (the disk/job query logic itself, wired through `WarehousePort`/
`SynapseConnection` — confirmed zero new connectivity code needed) is specified but still unbuilt
as a brightbot capability — the sandbox proves the TARGET is real and reachable; BH-1045 still
needs to write the code that queries it as part of the watchdog.

### Code path
No code. `SynapseConnection` (`brightbot/tools/warehouse_connections.py:248-424`) is the reused
connectivity layer — confirmed generic pymssql/T-SQL, zero Azure-exclusive requirement, connects
to bare SQL Server today with zero code changes. The disk-query logic itself (BH-1045) does not
exist yet.

### Invariants
Inherits `proactive-pipeline-ingestion-monitoring.md` §3 Invariant 16 (multi-connection
disambiguation — a workspace with 2+ SQL Server connections must not silently poll only the
first) and Invariant 18 (job_id must be a stable per-connection identifier, e.g. the
`warehouseServiceId`, since a disk-space signal has no natural job/execution ID to reuse).

### Acceptance — the exact thing Frank said wouldn't work

**The scene**: Frank's legacy SQL Server has been running Loop's SSIS jobs and SSRS reports for
years. It has no agent, no MCP server, nothing BrightHive-installed on it — because Frank's IT
policy won't let a vendor put software on a production database box, and Frank told Suzanne
directly he didn't believe BrightHive could monitor it without one: *"I don't believe what he
shared with me will work."* If that disk fills up, the nightly SSIS extract jobs start failing
and the morning SSRS holdings report doesn't go out — a business-visible failure, not an
abstract one.

```gherkin
Scenario: BrightAgent catches a disk problem on a box it was never installed on
  Given Loop Capital's SQL Server (this sandbox's real, running Docker container, standing in
    for their production box) has NO MCP server, agent, or BrightHive software of any kind
    installed on it
  And its free disk space has dropped to 18% — below the 20% threshold Frank named
  When BrightAgent's watchdog runs its next scheduled check — target: within 15 minutes of
    crossing the threshold
  Then Frank's team gets an alert naming the SQL Server instance and its current free-space
    percentage, before an SSIS job fails from lack of disk
  And Frank can verify, by asking his own IT team, that nothing was installed on that box to
    make this possible — because nothing was

Scenario: Loop's DR replica for the same SQL Server doesn't get its alert swallowed by the primary
  Given Loop Capital's SSIS/SSRS setup includes a disaster-recovery replica of the same SQL
    Server (a real posture for a production database backing daily reporting, not a
    hypothetical) — and that replica is also low on disk
  When BrightAgent polls both the primary and the replica
  Then Frank's team gets a distinct alert per instance, naming which one — an alert about the
    replica never gets silently swallowed because the primary alerted first, and vice versa,
    since losing disk on the replica is exactly as disruptive to Frank's DR posture as losing
    it on the primary
```

**What proves this, underneath**: `SynapseConnection` (`warehouse_connections.py:248-424`) reused
as-is — confirmed generic pymssql/T-SQL, zero Azure-exclusive requirement — reaching a bare SQL
Server the same way BrightHive already reaches any customer warehouse. Per `test-behavior-real.md`,
this MUST run against BH-1057's real sandbox, not a mock — a mocked page is exactly what triggered
Frank's "this is not live" reaction on 2026-07-09. **Confirmed real, not aspirational**: the
sandbox's own `validate.sh` already runs this exact scenario's underlying query and gets a real
non-mock result. Invariant 16 (multi-connection disambiguation) and Invariant 18 (stable
per-connection `job_id`) are what make the second scenario actually hold rather than silently
collapsing both instances into one alert bucket — the sandbox currently runs ONE SQL Server
instance; the second scenario (DR replica) is not yet exercised against a real second container,
flagging as the one part of GC-15 still resting on the invariant text alone, not a live test.

### Validation
**Filed** (2026-07-13, brightbot PR #811): `brightbot/tests/integration/golden_cases/test_gc_15_sql_server_disk_monitoring.py`
— points directly at `clients/trials/loopcapital/sandbox/` for its fixture (no longer
`pytest.skip`ping on missing infrastructure, since that's built and verified). 3 sub-case
stubs (disk-check, job-status, multi-connection disambiguation) still `pytest.skip` — blocked
on BH-1045's actual query code landing in brightbot.

---

## GC-16 — Fix-recurrence surfacing via surgical PR

### Bar
Suzanne's demo commitment #3, verbatim: "the ability to build skills that help surface the fixes
the agent applied when they are not abided by so we can avoid the recurrence of the same kind of
issue." **Descoped for 7/17, corroborated against real capacities, not left as an open
question**: this GC's DEMO-GATING bar is narrowed to *surfacing a fast, reviewable fix with a
plain-language diagnosis* — genuinely proving the pipeline break is no longer prevented from
recurring is OUT OF SCOPE for 7/17 (see "What's demo-gated vs. future scope" below). Mechanism:
reuse Longaeva's GC-11 surgical-PR loop (`self-healing-pipelines.md`), wired to this trial's own
watchdog signals (GC-14) — but this GC is **blocked from ever running** until GC-17's safety gate
ships, regardless of how complete the detection/PR-drafting code is.

### What's demo-gated vs. future scope (resolved on review, not an open design question)
Researched against real code before deciding, not assumed: making the drafted fix actually
PREVENT the same drift from recurring (not just diagnose it fast) requires `root_cause_class`
(BH-1047, today only DATA_SHAPE vs JOB_RUNTIME) to sub-classify further — type-drift vs
missing-column vs renamed-column, each needing a different generalized fix template (e.g.
explicit `CAST`/`TRY_CAST` staging models for type-drift, a well-established dbt pattern, but the
CLASSIFICATION step that recognizes "this needs that template" does not exist in any tool today —
confirmed: `analyze_dbt_error`/`convert_sql_to_dbt`/`generate_sql_model` all draft a fix scoped to
the exact observed error, never a generalized category). **This is genuinely new classification
capability, not a prompt tweak or a few-hour build** — unlike GC-14's webapp-parity gap (a real,
scoped, few-hour fix), this is multi-day, unscoped work with no ticket. Demoing it honestly by
7/17 is not realistic. The demo-gating bar below is scoped to what's real: a fast, reviewable,
plain-language fix — not recurrence prevention. Frank should be told this distinction directly,
not have it implied away — "faster, better-documented fixes" is still a genuine improvement over
today's undocumented tribal-knowledge fixes, and it's what's actually being demoed.

### Status today
**Spec landed, zero code, blocked on GC-17.** BH-1047 specifies wiring a `root_cause_class`
classifier (DATA_SHAPE vs JOB_RUNTIME) that routes DATA_SHAPE signals into GC-11's existing
surgical-PR loop. Reuses Longaeva's mechanism rather than inventing a new one — this GC is a new
*signal source* into an existing loop, not a new loop.

### Code path
No code. Mechanism reused from `self-healing-pipelines.md` (GC-11, Longaeva) — that loop itself
also has zero code today (`test_gc_11_self_healing.py` is `pytest.skip`, per the source spec).
BH-1047's classifier + wiring is net-new on top of a not-yet-built base.

### Invariants
- **This GC cannot pass its acceptance scenario below until GC-17 passes first** — auto-merge
  exclusion is a precondition, not a parallel workstream. A harness that runs GC-16 without first
  confirming GC-17 is testing an unsafe configuration.
- Root-cause classification never fabricates a fix: an unclassifiable failure surfaces as "cannot
  auto-diagnose," not a guessed PR.

### Acceptance — the same break happening twice is the actual complaint

**The scene**: last month, a source table feeding the Asset Management staging models changed a
column's type (a real recurrence pattern in Loop's environment — legacy SSIS sources drift
without warning). An engineer on Frank's team fixed it by hand. Two weeks later, the SAME kind of
drift breaks the SAME pipeline again — because nothing captured *why* it broke or *how* it was
fixed the first time, so the fix wasn't durable. This is Frank's literal ask #3: help him avoid
the recurrence, not just re-detect the same fire every time.

**Honesty check on the Bar, resolved on review — not left open**: the demo-gating scenarios below
prove BrightAgent proposes a reviewable fix fast, with a real paper trail. They do NOT prove the
recurrence itself is prevented — that claim is explicitly OUT of 7/17 scope (see "What's
demo-gated vs. future scope" above) because it needs classification capability that doesn't exist
in any tool today, confirmed by direct code inspection, not assumed. Frank should be told this
distinction plainly during the demo, not have it implied away.

```gherkin
Scenario: BrightAgent proposes the fix instead of making Frank's team re-diagnose it from scratch
  Given the code-level auto-merge exclusion (this spec's other gating case) has already shipped —
    unsafe to demo this scenario otherwise
  And BrightAgent's watchdog detects a column-type-drift failure on the Asset Management pipeline
    — the same failure CLASS that broke this pipeline once before
  When BrightAgent's remediation loop drafts a fix
  Then a pull request opens against Loop's dbt project with a plain-language explanation any of
    Frank's engineers can read without opening the stack trace — "source column X changed from
    NUMBER to FLOAT, here's the diff that adapts the model"
  And the PR sits waiting for a human on Frank's team to review and merge it themselves —
    BrightAgent never merges its own fix, no matter how confident the diagnosis
  And Frank's team now has a real, searchable PR history for this failure class — faster recovery
    next time, even though this demo does not yet claim the recurrence itself is prevented

Scenario: BrightAgent admits when it doesn't know, instead of guessing
  Given a pipeline failure that doesn't cleanly match a known root-cause pattern
  When the remediation loop evaluates it
  Then no PR is drafted, and Frank's team is told plainly this needs a human to look at it —
    a wrong guessed fix landing in a PR is worse than no PR, because it burns trust exactly like
    the "this is not live" reaction from 7/9
```

**Future scope, NOT demo-gating — kept here so it isn't lost, not deleted just because it's hard**:
```gherkin
Scenario: the SAME drift, after the fix is merged, no longer breaks the pipeline a third time
  Given Frank's team merged the PR from the scenario above
  When the source table drifts again in the exact same way (the same column, the same type
    change) — the real test of "avoided the recurrence," not just "diagnosed it faster"
  Then the pipeline run succeeds without a new failure, because the merged fix already
    generalized to this input — this is the difference between recurrence PREVENTED and
    recurrence RE-DETECTED, and it's the stronger claim Suzanne's original commitment implies
```
This needs `root_cause_class` sub-classified into type-drift/missing-column/renamed-column (each
with its own generalized fix template, e.g. explicit `CAST`/`TRY_CAST` for type-drift — a real
dbt best practice, not invented here) — new capability, no ticket filed yet. Flagging as
post-demo scope, not silently dropping Suzanne's stronger original wording.

**What proves this, underneath**: reuses Longaeva's GC-11 surgical-PR loop
(`self-healing-pipelines.md`) as the delivery mechanism, with BH-1047's `root_cause_class`
classifier (DATA_SHAPE vs JOB_RUNTIME) as the new signal source routing Loop's failures into it.
The "code-level auto-merge exclusion" referenced above is GC-17, in this spec's own numbering —
see the Invariants below for how the two cases gate each other; Frank-facing material should
never need to say "GC-17" out loud.

### Validation
**Filed** (2026-07-13, brightbot PR #811): `brightbot/tests/integration/golden_cases/test_gc_16_fix_recurrence_surfacing.py`
— `pytest.skip("BH-1047 not started; blocked on GC-17")` on the main test, plus a dedicated
sub-case stub (`test_gc_16_requires_gc_17_pass_as_precondition`) documenting the still-unbuilt
cross-GC precondition check, and an `xfail(strict=False)` stub for the future-scope
recurrence-prevented scenario. The harness MUST assert GC-17's verdict is PASS before executing
GC-16's own scenarios once that precondition check is implemented — not just skip independently.

---

## GC-17 — Auto-merge exclusion (safety precondition)

### Bar
Not a customer-facing demo point — a safety precondition Suzanne's demo commitment #3 (GC-16)
depends on. The remediation loop's tool-binding must exclude `github_merge_pull_request` at the
**code level**. "Never auto-merge" being prompt-only is not an acceptable safety posture for any
agent that can open PRs against pipeline code.

### Status today
**CRITICAL, no code.** Confirmed: `github_merge_pull_request` (`brightbot/agents/dbt_agent/tools/github_tools.py:503-560`) is
still fully bound into `dbt_agent_react.py`'s live `DBT_REACT_TOOLS` list with zero exclusion
logic anywhere in the repo. **Corrected on review** — the merge guard today is weaker than "never
auto-merge, prompt-only": `dbt_react_system_prompt.py:119-125` actually reads *"Only call
`github_merge_pull_request` when the user explicitly wants the PR merged (and CI is green)"* —
that is a conditional PERMISSION to merge on request, not a prohibition. There is no "never
merge" instruction anywhere in the prompt, only a general note that the agent shouldn't bypass
the PR by committing directly to the base branch on failure. So the real gap is worse than
originally stated: nothing today — not code, not prompt — instructs the remediation loop to
never merge; it is fully capable of merging today if a user (or a misrouted signal) asks it to.
Jira status: `Needs Refinement`. The concrete fix (a `REMEDIATION_TOOLS` list built via direct
import, omitting the merge tool by name) is already specified in BH-1047's ticket text, just not
implemented.

### Code path
`brightbot/agents/dbt_agent/dbt_agent_react.py` (`DBT_REACT_TOOLS`, includes
`github_merge_pull_request` today) + `brightbot/agents/dbt_agent/tools/github_tools.py:503-560`
(`github_merge_pull_request`'s definition).

### Invariants
- The remediation loop's tool list SHALL NOT include `github_merge_pull_request` by construction
  (a `REMEDIATION_TOOLS` list explicitly built without it), not by relying on the model to decline
  to call a tool it has access to.
- This exclusion is verifiable by static inspection of the bound tool list — not solely provable
  by observing that the model didn't call it in N test runs.

### Acceptance — the thing that would actually lose Loop Capital as a customer

**The scene**: Frank is already skeptical of unattended AI making changes to his production
pipelines — that's the entire subtext of "I don't think you're there yet" from 7/9. GC-16
promises Frank a PR his team reviews. If BrightAgent ever merged that PR itself — even once,
even correctly — the story Frank tells his own leadership stops being "a careful digital
coworker" and becomes "software that changes our asset-management pipelines without asking."
That's not a bug report, it's a lost deal.

```gherkin
Scenario: there is no code path by which BrightAgent can merge its own fix
  Given the remediation loop that opens a PR against Loop's pipeline when a fix is proposed
  When the tool list that loop is actually bound to is inspected directly — not by watching
    what the model chose to do in a test run, but by looking at what it's ALLOWED to do
  Then the merge capability is simply not present in that list
  And this is true independent of the model's judgment, the prompt, or how the failure was
    classified — Frank's team is the only party that can ever put this PR into production

Scenario: even an adversarial or confused attempt to merge fails safely
  Given the remediation loop as fixed above
  When the model attempts to call the merge tool anyway — whether from a bad prompt, a
    misclassification, or a genuine model error
  Then the attempt fails because the capability doesn't exist to call — not because the model
    was well-behaved this time
```

**What proves this, underneath**: `REMEDIATION_TOOLS` built via direct import, statically omitting
`github_merge_pull_request` (`brightbot/agents/dbt_agent/tools/github_tools.py:503-560`) by construction — verifiable by a plain
unit test asserting the tool's absence from the bound list, no live agent run required. Today
this is enforced ONLY by a system-prompt instruction (`dbt_react_system_prompt.py:119-125`) with
zero code-level backstop — the gap this GC exists to close before GC-16 is ever demoed.

### Validation
**Filed** (2026-07-13, brightbot PR #811): `brightbot/tests/integration/golden_cases/test_gc_17_auto_merge_exclusion.py`
— a **pure static/unit test**, no live Snowflake/AWS gate needed: will assert
`"github_merge_pull_request" not in {t.name for t in REMEDIATION_TOOLS}` once `REMEDIATION_TOOLS`
exists. This is the cheapest GC in this spec to make LIVE — no infrastructure blocker, only code
that hasn't been written yet, and the cheapest test file in this whole set to promote out of
skip. Should ship first among GC-14/15/16/17, both because it's cheapest and because it gates
GC-16.

---

## Per-GC harness layout (FILED — brightbot PR #811, mirrors brightbot's existing convention)

```
brightbot/tests/integration/golden_cases/
├── test_gc_14_proactive_monitor_alert.py         # SKIP — BH-1043/1046/1054/1067/1087 not started
├── test_gc_15_sql_server_disk_monitoring.py       # SKIP — BH-1045 not started (fixture is ready)
├── test_gc_16_fix_recurrence_surfacing.py         # SKIP — BH-1047 not started; blocked on GC-17
└── test_gc_17_auto_merge_exclusion.py             # SKIP — BH-1047 not started; cheapest to unblock
```

All 4 files now exist (brightbot PR #811, 2026-07-13) — 16 tests total (4 main verdict-recording
tests + 12 documented sub-case stubs), verified to collect and skip cleanly under pytest. The
`pytest.skip` reason strings are CI-visible tracking even with zero implementation; each stub's
docstring names the exact assertion it will make once its blocking ticket lands.

## Relationship to Longaeva's Golden Cases

This spec does not duplicate or fork Longaeva's numbering — GC-14/15/16/17 are net-new entries in
the same global `GC-N` sequence `brightbot/docs/specs/golden-cases/SPEC-GOLDEN-CASES.md` defines.
GC-16 explicitly reuses GC-11's mechanism (the surgical-PR loop) rather than building a second
one — Loop Capital's contribution is a new signal source (GC-14) feeding an existing loop, plus
closing a safety gap (GC-17) that Longaeva's own GC-11 spec left as a known, un-ticketed risk.

## Glossary

- **GC** — Golden Case. A measurable, customer-facing (or safety-gating) bar with a code path
  or an explicit gap, following the template `brightbot/docs/specs/golden-cases/SPEC-GOLDEN-CASES.md`
  established for Longaeva.
- **Demo-gating** — this GC must be live (or convincingly dry-run) for the 2026-07-17 decision
  gate. Distinct from Longaeva's ⭐ trial-demo-bar concept — Loop Capital's gate is a hard date,
  not an open trial window.
- **DATA_SHAPE / JOB_RUNTIME** — `root_cause_class` values from `self-healing-pipelines.md`/BH-1047;
  DATA_SHAPE routes into the surgical-PR loop, JOB_RUNTIME does not (out of this spec's scope).
- **"GC-14" name collision, disambiguated**: Longaeva's ticket **BH-601** independently labels
  its own agentic-governance/RBAC case "GC-14" (Notion-tracked, never implemented under that
  name). That is a DIFFERENT case in a DIFFERENT client's numbering scheme, not this spec's
  GC-14. This spec's GC-14 continues brightbot's `SPEC-GOLDEN-CASES.md` GC-1–13 numbering
  (Longaeva's own repo-tracked cases), which never reached 14. If searching Jira for "GC-14"
  surfaces BH-601, that ticket is unrelated to this spec.
