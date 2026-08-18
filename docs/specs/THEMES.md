# Spec consolidation — 92 specs → 12 themes

Audit date 2026-08-18. Every spec in `docs/specs/` was read and classified. This file is the
delegation map: what to build, what to archive, and what needs a decision from Kuri first.

**Headline:** 41 specs describe work that already shipped, died, or was superseded. Seven pairs
of specs invented **competing mechanisms for the same problem** — and in three cases the spec's
design was never built while the real capability shipped under a different name. Fixing those
seven conflicts is worth more than writing any new spec.

---

## ⚠️ Seven decisions that block delegation

No engineer can start cleanly on the affected themes until these are settled. Each is a
one-line call, not a design exercise.

| # | Conflict | Recommendation |
|---|---|---|
| 1 | **Warehouse fan-out**: fleet spec's `ConnectionDirectory` (keyed by `source_type`) vs connectivity watchdog's `poll_configured_warehouses` (keyed by warehouse, honors `is_default`) | Keep the **warehouse-keyed** one — `is_default` *is* the BH-1457 bug and `source_type` keying can't express it |
| 2 | **Engine port ×3**: `PipelineRunner` (real, in `pipelines/core/port.py`) vs `PipelineEnginePort` vs `ProjectPipelineEngine` — the latter two **do not exist in code**, zero grep matches | Keep `PipelineRunner`. Rewrite the other two specs as as-built docs or delete |
| 3 | **`SQL_SERVER` type**: is it its own `WarehouseType` or an alias for `azure_synapse`? Three specs answer differently within two weeks | **Needs an ADR.** If `on-prem-sql-server-warehouse.md` ships its new member, `lineage-adapter-sql-server.md`'s invariant I-1 breaks silently |
| 4 | **On-prem dbt execution**: `on-prem-engineering-runner.md` ADR-0002 says running dbt cloud-side against on-prem SQL Server was "the error" — which is exactly what `autonomous-dbt-project-lifecycle.md` built one day earlier | ADR-0002 wins; mark the older spec superseded |
| 5 | **Routine approval path**: shipped Slack → platform-core mutation → brightbot (writes ownership edges) vs a parallel LangGraph `interruptible()` POSTing straight to brightbot (**bypasses platform-core and the edges**) | Keep the shipped platform-core path |
| 6 | **Project ACTIVE trigger**: direct `on_project_activated` hook vs `project.activated` pub/sub event | Pick one; both are specced, neither is built |
| 7 | **`@` sigil collision**: `inline-context-anchors.md` defines `@` as a UI picker; the **already-merged** `chat-addressing-context-injection.md` defines it as a parsed dotted path | Shipped code wins — kill or rewrite `inline-context-anchors.md` |

Also: **one live P0** was found buried at line 1,077 of a spec marked `implemented-verified-staging` —
the BrightRoutines intent detector's gate 2 (manager → direct-reports) fails closed with no
hierarchy source, so the live detector has no hierarchy check at all. Never lifted into a ticket.

---

## Themes to delegate

Tier 1 is client-driven and should start now. Each theme gets its own `THEME-*.md` (lean,
150-line cap) before it's handed over. ✅ = theme spec written and linked.

### Tier 1 — now

| Theme | Goal in one line | Merges | Size | Blocked by |
|---|---|---|---|---|
| [**Warehouse health you can trust**](THEME-warehouse-health-truth.md) ✅ | Every connected warehouse is really watched; the status on screen is true; alerts say something useful | 5 specs | L | Decision 1 |
| [**Work where the customer's data lives**](THEME-onprem-engineering.md) ✅ | Run dbt inside the customer's own network, where their files and database actually live | 2 specs | L | Decision 4 |
| [**Always know which warehouse you're talking to**](THEME-catalog-and-identity.md) ✅ | Browse warehouses → databases → tables, always know which is default, never a silent coin-flip | 5 specs | L | Decision 3 |

### Tier 2 — next

| Theme | Goal in one line | Merges | Size | Blocked by |
|---|---|---|---|---|
| **Cross-engine correctness** | Read, write, lineage, and quality behave the same on every warehouse engine | 6 specs | L | Decision 3 |
| **Fleet self-healing** | Detect a broken pipeline, diagnose it, open a human-approved surgical PR | 2 specs | L | Decision 1 |
| **Governance that's actually enforced** | A rule or contract you declare is one the platform applies and alerts on — the "declared but never enforced" gap, ×3 artifact types | 5 specs | L | — |
| **Legacy file intake** | Drop in a `.dtsx`/`.rdl`/`.sql` and get diagnostics plus a GitHub PR | 4 specs | M | one extension registry, not three |
| [**Finish BrightRoutines**](THEME-brightroutines-closeout.md) ✅ | Close the short real tail behind a shipped feature — including the live P0 | 3 specs | S | Decision 5 + BH-914 approval |

### Tier 3 — later

| Theme | Goal in one line | Merges | Size |
|---|---|---|---|
| **Blast-radius quality** | Trace a bad number downstream before a customer sees it | 1 spec (split into 4) | L |
| **Project engine binding & activation** | Bind a project to its engine + repo; going ACTIVE pulls in real state | 3 specs | M |
| **Observe-surface honesty** | What the UI shows is true — no lying dots, no thrashing cache, no thin cards | 4 specs | M |
| **Cost & volume matrix** | Answer "what does this cost" for enterprise prospects | 3 specs | M |

Standalone, unmerged, keep as-is: **platform-core develop→main reconciliation** (L),
**workspace reset admin tool** (M), **decommission LangGraph Cloud** (M — rewrite as
current-state; CEMAF won, the old plan didn't execute).

---

## Archive — shipped or dead (41 specs, no more engineering time)

**Shipped, wrong status.** Move to `docs/features/`; these are history, not queue:
`okta-cognito-federation` (both PRs merged 06-22) · `github-enterprise-host-config` (shipped via
consolidation PR #793) · `skills-extension-deep-agent` (BH-860 `Done`) ·
`quality-rules-configurable` (BH-503 `Done`) · `longitudinal-monitoring` + `-capability` +
`-deployment` (staging-verified 06-18) · `brightroutines-intent-loop` +
`-execute-workflow-schedule` + `-your-routines-persistence` (BH-876 `Done`) ·
`dbt-react-migration` (only Phase-3 deletion left → one ticket) · `pipeline-run-lifecycle` ·
`project-engine-run-sync` · `remediation-pr-engine-run-logs` · `chat-addressing-context-injection` ·
`warehouse-selection-on-mcp-tools` (BH-1430 `Done`) · `snowflake-full-integration` (Phase 1) ·
`chat-session-notifications`

**Dead or superseded.** Delete or rewrite:
`langgraph-cloud-detach` (Track A closed unmerged; Track B won) · `agentcore-deployment-migration`
(CEMAF is the supervisor now) · `azure-synapse-full-integration` (April; still frames the
deprecated Datapiary as a dependency) · `warehouse-extensibility-pattern` (same 7-layer registry
as its sibling, 3 days apart, different variable name) · `inline-context-anchors` (collides with
shipped `@`) · `pipeline-engine-full-lifecycle-control` (specs a port that was never built) ·
`self-healing-pipelines` (superseded by the fleet spec)

**Park — no confirmed demand.** Revisit on a real signal, not speculatively:
`saas-mcp-bridge-integration` (no customer ask; no real file:line grounding) ·
`brightagent-local-plugin` (half its scenarios are `@blocked-pending-confirmation`) ·
`user-activity-event-store` · `detector-fanout-fairness` (designs for hundreds of workspaces;
staging runs 3–5) · `online-judge-eval-circuit-breaker` · `platform-analytics-dashboard` (April,
still on mock data) · `ssis-ssrs-to-dbt-regeneration` (643 lines for explicitly out-of-scope work
→ cut to a 1-page concept note)

**Relocate — not implementation specs:**
`golden-cases-loopcapital` + `loopcapital-trial-readiness` → `clients/trials/loopcapital/`
(the pattern Longaeva already uses) · `open-semantic-view` + `aws-azure-network-connectivity` →
ADRs · `onboarding-bootstrap` → internal-tooling backlog (it's a Makefile runbook in spec clothing)

**Rewrite — real content buried in bloat:**
`lineage-aware-data-quality` 2,282 lines → split into 4 specs ≤500 each; delete every "pass N"
annotation (they run to pass 78) and move its unrelated "Track D" webapp UI audit to its own
ticket · `proactive-pipeline-ingestion-monitoring` 2,000 lines → keep the "Start Here" section,
archive the rest as a decision log · `warehouse-database-table-identity` 880 lines / 16 invariants
→ ship the DatabaseNode + `isDefault` slice (~300 lines), split out the rest

---

## Why this happened, and the guard against a repeat

The root cause is `SPEC_TEMPLATE.md`: 13 mandatory sections, three of them narrating current
state before you reach what to build, and a literal instruction to **"Be exhaustive"** (now
removed). Applied 92 times it produced a corpus where **68 of 92 specs have exactly one commit** —
written once, never revised, never read. Mega-detail didn't produce delegatable work; it hid a
P0, three phantom ports, and four already-shipped epics.

New default: **`THEME_SPEC_TEMPLATE.md`** — 150-line cap, plain-language goal, numbered build
list, verifiable checklist. Reach for the full template only for a genuine state machine,
security/tenancy boundary, or timing guarantee — and treat its budgets as ceilings, not quotas.
