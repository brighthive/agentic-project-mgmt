# Spec consolidation — 92 specs → 14 themes

Audit date 2026-08-18. Every spec in `docs/specs/` was read and classified. This file is the
**classification map**: what to build, what to archive, what conflicts. For the **dated frontier,
verified sizing, and the order of work**, see [ROADMAP.md](ROADMAP.md).

> **Sizes and the decision list below were re-verified against code on 2026-08-19.** Where the
> repos contradicted this audit, the row is corrected here and the evidence is in
> [ROADMAP.md](ROADMAP.md). The short version: four of the seven "decisions" were already settled
> by shipped code, and the claimed live P0 had been fixed five weeks before this file was written.

**Headline:** 41 specs describe work that already shipped, died, or was superseded. Seven pairs
of specs invented **competing mechanisms for the same problem** — and in three cases the spec's
design was never built while the real capability shipped under a different name.

**Verified 2026-08-19:** only **one** of those seven is a live decision (#3, `SQL_SERVER`). Four
were already answered by shipped code, one (#6) is stated backwards, and one (#1) names two
mechanisms that both return zero grep hits. The cleanup is still worth doing; it is a
~30-minute documentation pass, not a blocker on thirteen of the fourteen themes.

---

## ⚠️ Seven conflicts — all now resolved

Originally filed as "seven decisions that block delegation." Verified against code, **#3 was the
only open call — and it is now settled by [ADR-0003](../adr/0003-sql-server-is-identity-only-tds-dispatch-is-shared.md)
(Accepted 2026-08-19)**; the rest are corrections to make in this file and in the specs.

| # | Conflict | Verified state (2026-08-19) | Recommendation |
|---|---|---|---|
| 1 | **Warehouse fan-out**: fleet spec's `ConnectionDirectory` (keyed by `source_type`) vs connectivity watchdog's `poll_configured_warehouses` (keyed by warehouse, honors `is_default`) | ⚪ **Not a decision** — both names return **zero** grep hits. The shipped code is a third thing: `pipeline_watchdog_task.py:165-180` sweeps the registry with `config={}` and never enumerates warehouses | Skip the naming call — the build is identical either way. One ticket: fan out via `list_workspace_warehouses` (`warehouse_catalog.py:135`, already honors `is_default`, zero callers in `agents/`) |
| 2 | **Engine port ×3**: `PipelineRunner` (real, in `pipelines/core/port.py`) vs `PipelineEnginePort` vs `ProjectPipelineEngine` — the latter two **do not exist in code**, zero grep matches | ✅ **Settled by shipped code.** `PipelineRunner` at `port.py:182`, registry `:430`, consumed cross-repo (`project-run-sync.ts:83`). BH-1323's own branch shipped the "new port" as *verbs on the existing one* | Keep `PipelineRunner`. Rewrite the other two specs as as-built docs or delete |
| 3 | **`SQL_SERVER` type**: is it its own `WarehouseType` or an alias for `azure_synapse`? Three specs answer differently within two weeks | ✅ **Settled — [ADR-0003](../adr/0003-sql-server-is-identity-only-tds-dispatch-is-shared.md), Accepted 2026-08-19.** Both layers shipped and both are right: identity says own member (`warehouse-provider-typedefs.ts:23`), wire protocol says alias (`warehouse.py:184-185`). **32 dispatch sites** key on the collapsed literal; `lineage_refresh_task.py:95` files every SQL Server lineage graph under Synapse | **ADR written & Accepted.** Identity member only, never dispatch. ADR-0003 splits it: **PR #1** adds the identity member + fixes `lineage_refresh_task.py:95` (closes the live bug); the 32→`capabilities()` sweep is tracked separately under BH-1168. Note: the I-1 break is narrower than filed — provider selection keys on the *raw* secret type (`lineage_provider_selection.py:52`) and survives |
| 4 | **On-prem dbt execution**: [`on-prem-engineering-runner.md`](./on-prem-engineering-runner.md) ADR-0002 says running dbt cloud-side against on-prem SQL Server was "the error" — which is exactly what [`autonomous-dbt-project-lifecycle.md`](./autonomous-dbt-project-lifecycle.md) built one day earlier | ✅ **Settled by shipped code in two repos.** `brightagent-engineering-runner` is real and on `main`; platform-core shipped `recordOnPremRunReport` (`resolvers.ts:435`). The cloud-side alternative returns zero hits (`DbtCoreRunner`) | ADR-0002 wins — **flip it `Proposed` → `Accepted`**; mark the older spec superseded |
| 5 | **Routine approval path**: shipped Slack → platform-core mutation → brightbot (writes ownership edges) vs a parallel LangGraph `interruptible()` POSTing straight to brightbot (**bypasses platform-core and the edges**) | ✅ **Settled by shipped code.** All three hops live (`app.ts:151` → `resolvers.ts:310` → `scheduled_agents_routes.py`). `interruptible()` has **zero** routine callers, and the rival spec concedes at its own line 30 that the wire "does not exist" | Keep the shipped platform-core path; delete the rival spec |
| 6 | **Project ACTIVE trigger**: direct `on_project_activated` hook vs `project.activated` pub/sub event | 🔴 **This row was wrong.** Not "neither is built" — a **third** mechanism is built, tested and live in prod: `project.ts:1970` → `project-activation-check-client.ts` → `project_activation_check_routes.py`, 7 unit tests. Both specced names return zero hits | **Correct the row.** Hang new work off the existing route. Building the pub/sub as specced would give **duplicate activation runs in prod** — this is the most dangerous stale claim in the file |
| 7 | **`@` sigil collision**: [`inline-context-anchors.md`](./inline-context-anchors.md) defines `@` as a UI picker; the **already-merged** [`chat-addressing-context-injection.md`](./chat-addressing-context-injection.md) defines it as a parsed dotted path | ⚪ **No collision exists.** Same grammar — the webapp picker *emits the dotted path the parser reads* (`ChatField/index.tsx:137`); the anchors spec's own examples are `@snowflake.ORDERS`. They are one feature | **Do not kill it.** Strip its shipped `@` half as as-built; keep BH-1354–1358 (`#` knowledge-base and `[` project sigils) — real unbuilt work, no rival design |

~~Also: **one live P0** was found buried at line 1,077 of a spec marked `implemented-verified-staging` —
the BrightRoutines intent detector's gate 2 (manager → direct-reports) fails closed with no
hierarchy source, so the live detector has no hierarchy check at all. Never lifted into a ticket.~~

**Retracted 2026-08-19 — the P0 does not exist.** It was fixed, ticketed (**BH-991**), merged
(`c3598a48`, PR #789) and regression-tested on **2026-07-12**, five weeks before this audit.
`detector.py:305-326` hard-disables the multi-user gate with a literal `False` plus the
plain-language comment; `:325` stamps `multi_user_path=disabled_no_hierarchy_signal` into the
audit trail on every evaluation. It **fails closed by blocking** — strictly more conservative than
before, not waving anything through. Test at `test_detector.py:112-131`, present on develop,
staging and main.

**A real customer-facing defect was found instead, in a different theme.**
`webapp/src/Governance/GovernancePolicyItem.tsx:55` — the **"Enforced" toggle is local React
state** (`useState(false)`), never persisted, never read. Its tooltip at `:83` promises *"Hard
enforcement — BrightAgent will block violating operations."* ~0.5 pd to remove; ship it
independently.

---

## Themes to delegate

Tier 1 is client-driven and should start now. Each theme gets its own `THEME-*.md` (lean,
150-line cap) before it's handed over. ✅ = theme spec written and linked.

**All 14 are `status: Draft`, meaning none is `Ready to delegate` yet.** A theme flips to Ready
when **five** gates hold, not one: its blocking decision is settled (**D**), real tickets exist
(**T**), they are refined rather than `Needs Refinement` (**R**), they are assigned (**A**), and
they do not collide with work already in flight (**C**). Verified 2026-08-19, **T/R/A/C fail on
almost every theme** — `cost-and-volume` and `routine-delivery` have no real tickets at all,
`legacy-file-intake`'s seven are unassigned, and `fleet-self-healing` and `governance-enforced`
overlap tickets already in `Staging QC`. See [ROADMAP.md](ROADMAP.md) for the per-theme gate state
and the order of work.

### Tier 1 — now

| Theme | Goal in one line | Merges | Verified size | Blocked by |
|---|---|---|---|---|
| [**Warehouse health you can trust**](THEME-warehouse-health-truth.md) ✅ | Every connected warehouse is really watched; the status on screen is true; alerts say something useful | 5 specs | **11 pd** | ⚪ nothing — needs the shared `warehouseServices` query first |
| [**Work where the customer's data lives**](THEME-onprem-engineering.md) ✅ | Run dbt inside the customer's own network, where their files and database actually live | 2 specs | **9.5 pd** | ⚪ nothing — already In Progress (BH-1403/1421) |
| [**Always know which warehouse you're talking to**](THEME-catalog-and-identity.md) ✅ | Browse warehouses → databases → tables, always know which is default, never a silent coin-flip | 5 specs | **10 pd** | 🔴 Decision 3 (items 3–4 only) |

### Tier 2 — next

| Theme | Goal in one line | Merges | Verified size | Blocked by |
|---|---|---|---|---|
| [**Same answers on every warehouse engine**](THEME-cross-engine-correctness.md) ✅ | Read, write, lineage, and quality behave the same on every engine — starting with a silent Synapse sampling bug | 5 specs | **9 pd** | 🔵 a prod release, not a decision |
| [**Pipelines that fix themselves**](THEME-fleet-self-healing.md) ✅ | Detect a broken pipeline, diagnose it, open a human-approved PR — never self-merge | 2 specs | **18 pd** | 🟡 rebase-or-rewrite the orphaned branch |
| [**Governance you declare is governance we enforce**](THEME-governance-enforced.md) ✅ | One enforcement point, three artifact types — closes the "declared but never applied" gap | 5 specs | **23–28 pd** | — |
| [**Drop in your legacy pipeline files**](THEME-legacy-file-intake.md) ✅ | Upload a `.dtsx`/`.rdl`/`.sql`, get diagnostics and a reviewable PR | 4 specs | **9–10 pd** | — (BH-1274 needs a named secrets approval) |
| [**Finish BrightRoutines**](THEME-brightroutines-closeout.md) ✅ | Close the short real tail behind a shipped feature — including the live P0 | 3 specs | **0.75 pd** | ⚪ nothing — BH-914 is `Done`, Decision 5 is settled |

### Tier 3 — later

| Theme | Goal in one line | Merges | Verified size |
|---|---|---|---|
| [**Routine results land where the team already works**](THEME-routine-delivery.md) ✅ | A routine reports to a team channel with its provenance, not just to its creator | 2 specs | **7–9 pd** |
| [**Describe a routine and get one**](THEME-routine-authoring.md) ✅ | Say what you want in your own words, get a working multi-step routine | 1 spec | **~20 pd** |
| [**Catch a bad number before your customers do**](THEME-blast-radius-quality.md) ✅ | An anomaly alert names what's downstream of it, worst tier first | 1 spec (rewrite as 4) | **6–9 pd** |
| [**Turn on a project and it knows its own history**](THEME-project-activation.md) ✅ | Activate a project and existing runs/models appear, instead of a blank page | 3 specs | **11 pd** |
| [**The screen never lies**](THEME-honest-surfaces.md) ✅ | Never-checked shows as unknown, a degraded badge names the culprit, logs are readable | 6 specs | **16 pd** |
| [**Answer what it costs**](THEME-cost-and-volume.md) ✅ | Give sales a real volume-and-cost picture per workspace | 3 specs | **14 pd** |

Standalone, unmerged, keep as-is — each is already one coherent spec and needs no theme wrapper:
[`platform-core-develop-main-reconciliation.md`](./platform-core-develop-main-reconciliation.md) (L), [`reset-workspace-resources.md`](./reset-workspace-resources.md) (M),
[`byow-end-to-end-omd-native.md`](./byow-end-to-end-omd-native.md) (M — make the BYOW catalog scan actually populate, and retire the
dead scanner lambdas), and **decommission LangGraph Cloud** (M — rewrite [`langgraph-cloud-detach.md`](./langgraph-cloud-detach.md)
+ [`agentcore-deployment-migration.md`](./agentcore-deployment-migration.md) as one current-state doc; CEMAF won, the old plan didn't
execute).

---

## Archive — shipped or dead (41 specs, no more engineering time)

**Shipped, wrong status.** Move to `docs/features/`; these are history, not queue:
[`okta-cognito-federation`](./okta-cognito-federation.md) (both PRs merged 06-22) · [`github-enterprise-host-config`](./github-enterprise-host-config.md) (shipped via
consolidation PR #793) · [`skills-extension-deep-agent`](./skills-extension-deep-agent.md) (BH-860 `Done`) ·
[`quality-rules-configurable`](./quality-rules-configurable.md) (BH-503 `Done`) · [`longitudinal-monitoring`](./longitudinal-monitoring.md) + `-capability` +
`-deployment` (staging-verified 06-18) · [`brightroutines-intent-loop`](./brightroutines-intent-loop.md) +
`-execute-workflow-schedule` + `-your-routines-persistence` (BH-876 `Done`) ·
[`dbt-react-migration`](./dbt-react-migration.md) (only Phase-3 deletion left → one ticket) · [`pipeline-run-lifecycle`](./pipeline-run-lifecycle.md) ·
[`project-engine-run-sync`](./project-engine-run-sync.md) · [`remediation-pr-engine-run-logs`](./remediation-pr-engine-run-logs.md) · [`chat-addressing-context-injection`](./chat-addressing-context-injection.md) ·
[`warehouse-selection-on-mcp-tools`](./warehouse-selection-on-mcp-tools.md) (BH-1430 `Done`) · [`snowflake-full-integration`](./snowflake-full-integration.md) (Phase 1) ·
[`chat-session-notifications`](./chat-session-notifications.md) · [`warehouse-connection-health`](./warehouse-connection-health.md) (BH-1341 shipped — it is the
on-demand probe the warehouse-health theme reuses; keep as reference, don't rebuild) ·
[`longitudinal-monitoring-capability`](./longitudinal-monitoring-capability.md) + [`longitudinal-monitoring-deployment`](./longitudinal-monitoring-deployment.md) (staging-verified with
their parent)

**Dead or superseded.** Delete or rewrite:
[`langgraph-cloud-detach`](./langgraph-cloud-detach.md) (Track A closed unmerged; Track B won) · [`agentcore-deployment-migration`](./agentcore-deployment-migration.md)
(CEMAF is the supervisor now) · [`azure-synapse-full-integration`](./azure-synapse-full-integration.md) (April; still frames the
deprecated Datapiary as a dependency) · [`warehouse-extensibility-pattern`](./warehouse-extensibility-pattern.md) (same 7-layer registry
as its sibling, 3 days apart, different variable name) · [`inline-context-anchors`](./inline-context-anchors.md) (collides with
shipped `@`) · [`pipeline-engine-full-lifecycle-control`](./pipeline-engine-full-lifecycle-control.md) (specs a port that was never built)

[`self-healing-pipelines`](./self-healing-pipelines.md) is **not** in this pile — archive it only *after*
[Pipelines that fix themselves](THEME-fleet-self-healing.md) folds in its four data-shape failure
modes as healer registrations. Its verification-loop design is superseded; its failure taxonomy is
not.

**Park — no confirmed demand.** Revisit on a real signal, not speculatively:
[`saas-mcp-bridge-integration`](./saas-mcp-bridge-integration.md) (no customer ask; no real file:line grounding) ·
[`brightagent-local-plugin`](./brightagent-local-plugin.md) (half its scenarios are `@blocked-pending-confirmation`) ·
[`user-activity-event-store`](./user-activity-event-store.md) · [`brightroutines-detector-fanout-fairness`](./brightroutines-detector-fanout-fairness.md) (designs for hundreds of
workspaces; staging runs 3–5) · [`brightroutines-online-judge-eval-circuit-breaker`](./brightroutines-online-judge-eval-circuit-breaker.md) ·
[`platform-analytics-dashboard`](./platform-analytics-dashboard.md) (April, still on mock data) · [`ssis-ssrs-to-dbt-regeneration`](./ssis-ssrs-to-dbt-regeneration.md)
(643 lines for explicitly out-of-scope work → cut to a 1-page concept note) ·
[`brightroutines-naming-proposal`](./brightroutines-naming-proposal.md) (self-described as "not a spec — a decision doc"; move to an ADR
or delete once BH-953 resolves)

**Superseded by a decision, not by a theme.** [`brightroutine-approve-schedule`](./brightroutine-approve-schedule.md) and
[`slack-routine-suggestion-scheduling`](./slack-routine-suggestion-scheduling.md) are the two competing approval write paths in decision 5 —
whichever loses gets deleted, the winner becomes reference. Neither is a theme on its own.

**Relocate — not implementation specs:**
[`golden-cases-loopcapital`](./golden-cases-loopcapital.md) + [`loopcapital-trial-readiness`](./loopcapital-trial-readiness.md) → `clients/trials/loopcapital/`
(the pattern Longaeva already uses) · [`open-semantic-view`](./open-semantic-view.md) + [`aws-azure-network-connectivity`](./aws-azure-network-connectivity.md) →
ADRs · [`onboarding-bootstrap`](./onboarding-bootstrap.md) → internal-tooling backlog (it's a Makefile runbook in spec clothing)

**Rewrite — real content buried in bloat:**
[`lineage-aware-data-quality`](./lineage-aware-data-quality.md) 2,282 lines → split into 4 specs ≤500 each; delete every "pass N"
annotation (they run to pass 78) and move its unrelated "Track D" webapp UI audit to its own
ticket · [`proactive-pipeline-ingestion-monitoring`](./proactive-pipeline-ingestion-monitoring.md) 2,000 lines → keep the "Start Here" section,
archive the rest as a decision log · [`warehouse-database-table-identity`](./warehouse-database-table-identity.md) 880 lines / 16 invariants
→ ship the DatabaseNode + `isDefault` slice (~300 lines), split out the rest

---

## Why this happened, and the guard against a repeat

The root cause is [`SPEC_TEMPLATE.md`](./SPEC_TEMPLATE.md): 13 mandatory sections, three of them narrating current
state before you reach what to build, and a literal instruction to **"Be exhaustive"** (now
removed). Applied 92 times it produced a corpus where **68 of 92 specs have exactly one commit** —
written once, never revised, never read. Mega-detail didn't produce delegatable work; it hid a
P0, three phantom ports, and four already-shipped epics.

New default: **[`THEME_SPEC_TEMPLATE.md`](./THEME_SPEC_TEMPLATE.md)** — 150-line cap, plain-language goal, numbered build
list, verifiable checklist. Reach for the full template only for a genuine state machine,
security/tenancy boundary, or timing guarantee — and treat its budgets as ceilings, not quotas.
