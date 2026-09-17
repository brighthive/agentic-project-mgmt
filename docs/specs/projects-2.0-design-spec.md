---
title: "Brighthive Projects 2.0 — Design Spec"
status: "Source doc — reconciled; premise partially inaccurate, see note below"
created: "2026-09-16"
companion: "projects-2.0-technical-requirements.md"
---

> **Reconciliation note (2026-09-16):** this design doc opens by describing a Project's `Spec`,
> `Pipeline`, and `Observability` tabs as "already in production." Verified against
> `brighthive-webapp` (`src/common/ProjectSidenav/ProjectSidenav.tsx`, checked against
> `origin/develop` tip, 2026-09-16): the real tabs are **Overview, Schemas, Flow, Input Data
> Assets, Files, Data Products**. There is no `Spec` tab and no `Observability` tab. `Pipeline` in
> this doc ≈ `Flow` in the real code (backed by the real `WorkflowSpec` system), but `Flow` is
> explicitly gated behind a feature flag and marked "not GA" in the sidenav's own code comment —
> not universally live the way this doc assumes. See
> [THEME-spec-driven-pipelines.md](THEME-spec-driven-pipelines.md) for the corrected, real-primitive
> build target and the open product decision this creates (what does the Spec tab actually become:
> new tab, folded into Overview, or gated behind the same flag as Flow). Full trail: PR #191.

Audience: Claude Design (visual/UX design pass) Companion doc: projects-2.0-technical-requirements.md (engineering / Claude Code) Status: Draft for design exploration — not yet reviewed by Matt Gee


1. Why this exists
Today, a Brighthive "Project" (e.g., Impact Capital / Daily Portfolio Data Pipeline Monitoring) already has: a Spec tab (narrative + tabular pipeline definition), a Pipeline tab (compiled step graph, Compile/Run/Schedule, Active/Paused), and an Observability tab (model success rate, failed runs, agent PRs to review, recent runs). Projects 2.0 doesn't replace this — it makes the relationship between these three views the product:

Spec → Graph → Health should feel like one continuous surface, not three disconnected tabs.

Three capabilities drive this redesign:

Spec-Driven Development (SDD) — a data engineer narratively describes a pipeline in one or more .md files; BrightAgent builds it and continuously verifies the running system against that spec.
Pipeline-to-Data-Product Visualizer — a single graph view spanning source → transform → quality → product → consuming application, typed against a formal node ontology.
Proactive Agentic Monitoring — the Observability surface becomes an incident workspace: root cause, blast radius, proposed fix, and verification status, all in one place.


2. Design principles
Spec is the source of truth, graph is the mirror. Every node in the visualizer should be traceable back to the line(s) of spec that produced it. When the running pipeline drifts from spec, that's a visible, first-class state — not an error toast.
Never hide the human gate. Every agent-authored change (a compiled pipeline, a proposed fix) is a diff a person reviews. The UI should make "propose vs. applied" unambiguous everywhere — color, icon, and copy all agree.
One ontology, one visual language. The same node shape/color for "SQL model" appears identically in the Spec tab's referenced-objects list, the Pipeline graph, and the Observability incident view.
Status is layered, not flattened. A node can be simultaneously: spec-conformant ✅, quality-passing ✅, but stale (hasn't run in 3 days) ⚠️. Don't collapse these into one traffic light.
Reuse existing chrome. Left rail, top breadcrumb (Workspace > Projects > Project), tab bar, and the teal (#0E7A6E) / dark-canvas graph style already in production (see reference screenshots) stay as-is. This is an evolution of Spec/Pipeline/Observability, not a new IA.


3. Information architecture
Keep the existing tab bar; add one tab, deepen three:

Tab
Change
Agent
No change
Spec
Deepened: multi-file spec support, per-section verification badges, "generate pipeline" CTA with diff preview
Schemas
No change
Files
No change
Pipeline
Renamed conceptually to Graph (keep URL/tab label flexible — see below) — becomes the full lifecycle graph, not just the dbt step chain
Observability
Deepened: incident workspace (RCA, impact, fix, verification) replaces the flat "Agent PRs to review" list
Data Assets / Data Products
No change, but nodes here should deep-link into the new Graph tab at that node
Settings
No change


Tab naming decision needed: "Pipeline" currently implies the dbt step sequence only. Recommend renaming to "Graph" with "Pipeline" as a filter/view mode inside it (see §5), so we don't break muscle memory while extending scope. Flag for Matt/Suzanne — naming is cheap to change, worth 10 minutes of debate before build.


4. Screen 1 — Spec tab (Spec-Driven Development)
4.1 Current state (reference)
Existing Spec tab shows a single rendered markdown document (Context, Goal, Source systems, Key columns, Transform logic, Outputs) with Edit and Generate pipeline actions.
4.2 New structure
Multi-file spec. A project's spec becomes a small file tree, not one document:

/spec
  00-overview.md         ← goal, stakeholders, success metric (mirrors "Project Goals")
  01-sources.md          ← source systems, tables, join keys
  02-transform.md        ← transform logic, key columns
  03-quality.md          ← data quality expectations, thresholds, contracts
  04-outputs.md          ← data products, consuming applications, notify rules

Left sub-panel: file tree (collapsible), each file shows a small verification badge (✅ conforms / ⚠️ drift / ⏳ pending / — not yet built).
Main panel: rendered markdown for the selected file, same typographic treatment as today (headers, tables, inline code for identifiers).
A single file is still fully valid for simple projects — the tree just collapses to one leaf. Don't force decomposition on small pipelines.

Per-section verification. Each markdown section (H2) gets a right-margin status chip, e.g. next to "Transform logic": ✅ matches compiled pipeline. Clicking it opens a Verification Panel (right-side drawer):

What was checked (e.g., "join key event_id in spec vs. join_catastrophe_emergency_d… step")
Verifier agent name + timestamp
Pass/fail detail, and if failed, the specific mismatch in a two-column diff (Spec says / Pipeline does)

Generate / re-generate pipeline.

Primary CTA: Compile from spec (mirrors existing "Generate pipeline").
On re-compile after a spec edit, show a diff preview modal before anything is written: nodes added (green), removed (red), modified (amber), each with a one-line rationale ("column estimated_damage_millions filter added per 02-transform.md line 14"). Human confirms before the Graph updates.
Secondary CTA: Run spec verification — runs verifier agents without recompiling, useful after someone edits the warehouse directly outside Brighthive.
4.3 States
No spec yet: empty state with a template picker (Blank / ETL pipeline / Data product mart / Monitoring-only) that seeds the file tree with headers filled in, prompting the user to narrate.
Spec present, not yet compiled: grey "Draft" pill, Compile CTA prominent.
Compiled, verified: green "Verified" pill with last-checked timestamp.
Compiled, drifted: amber "Drift detected" pill — persistent, not dismissible until addressed or spec updated to match reality.


5. Screen 2 — Graph tab (Pipeline-to-Data-Product Visualizer)
5.1 Purpose
One canvas showing the full lifecycle: Data Source → Connector → Raw/Staged Table → SQL Transform → Semantic View/Metric → Data Quality Test → Data Product → Application/Consumer, with agent and PR activity overlaid.
5.2 Node ontology (v1) — visual encoding
Reuse the existing dark-canvas node-card style (rounded rect, colored type tag top-left, title, one-line description, In/Out counters) already shown in the Pipeline tab. Extend the type tag palette:

Node type
Type tag color
Icon
Notes
Data Source
Slate grey
plug
External system (Redshift table, SFTP feed, API)
Connector / Ingestion Job
Slate grey (outline)
arrow-in
Scheduled pull
Raw / Staged Table
Blue
table
Landed data, pre-transform
SQL Model / Transform
Teal (existing "SQL" tag)
code
dbt model or equivalent
View
Light teal
eye
Non-materialized read layer
Semantic View / Metric
Purple
ruler
OSI-defined metric/semantic model
Data Quality Test
Amber
shield-check
Great Expectations suite, gate
Data Contract
Amber (outline)
file-check
Schema/SLA agreement between steps
Data Product
Green
package
Registered, cataloged, governed
Application / Consumer
Indigo
monitor
BI tool, dashboard, downstream app/API
Agent Action (existing "AGENT" tag)
Pink
bot
e.g. test_joined_data_quality — keep as-is
Pull Request
Grey with red/green diff icon
git-pull-request
Overlay, not a structural node — see §5.4


Full ontology schema and behavior lives in the technical requirements doc (§3). Design only needs the visual encoding above to be consistent everywhere this ontology appears (Graph tab, Data Assets list icons, Observability incident cards).
5.3 Layout & interaction
Default layout: left-to-right swim-lane by node type category (Source → Transform → Quality → Product → Consumption), matching the existing horizontal step-chain feel — just wider in scope.
Filter/view toggle (top-right, replacing nothing — new control): Full Lifecycle / Pipeline Only (today's dbt-step view) / Data Products Only / Impacted by [incident] (only visible when an incident is active, see §6).
Node click → right-side drawer: type, spec source-of-truth link (jumps to the exact spec file/section), last run status, quality score, owner, and — if applicable — active incident badge.
Edge click → shows the contract/join key/lineage detail (e.g., "event_id — LEFT JOIN, keep events even without a response") pulled straight from spec transform logic.
Spec vs. Compiled diff mode: toggle to overlay what the spec declares vs. what's actually deployed — nodes only in spec render dashed/ghosted; nodes only in the live graph (drift, manual changes) render with a warning outline.
Keep existing canvas controls (zoom, fit, minimap, lock) and the Compile/Run/Schedule/Active-Paused header controls — these apply to the "Pipeline Only" filtered view.
5.4 Pull requests as overlay, not nodes
PRs (from Engineering Agent fixes, spec re-compiles, or manual changes) attach to the node they affect as a small badge (open PR count) rather than becoming permanent graph nodes — keeps the lifecycle graph legible. Clicking the badge opens the same PR panel used in Observability (§6.3) scoped to that node.


6. Screen 3 — Observability tab (Proactive Monitoring)
6.1 Current state (reference)
Existing tab: Transformation engine/repo info, Models/Success rate/Failed/In flight tiles, Agent PRs to review list, Recent Runs list with expandable error detail and "View PR."
6.2 New structure: Incident Workspace
Keep the top tiles as-is (they're a good at-a-glance summary). Replace the flat PR + Runs lists with a single Incidents feed, each incident card expanding into four tabs:

Incident card (collapsed): 🔴 stg_holdings_nightly · dbt command failed · recurring (3rd time) · 7/17/2026 2:00 AM

Incident card (expanded) — four sub-tabs:

Diagnosis
Plain-language root cause (agent-authored)
"Same failure class as [2 prior incidents]" — recurrence badge, links to prior occurrences
Evidence sources used, shown as chips: dbt logs, GitHub Actions run #482, Snowflake query history — each expandable to raw excerpt
Impact
Blast-radius mini-graph (auto-filters the Graph tab to Impacted by [incident]): which downstream tables, data products, and consuming applications are affected, with a severity read (e.g., "2 data products stale, 1 dashboard showing yesterday's data")
Who's notified (owning data engineer via Slack + notification center, per existing pattern)
Proposed Fix
Diff view of the fix PR (reuse existing "View diff" pattern)
Verification status band above the diff: ✅ Verified in sandbox — 11/11 tests pass, no new downstream breaks or ⚠️ Verification incomplete — human review required before merge
Actions: Review PR (opens GitHub), Post to Slack, Copy link — all present today, keep them
Timeline
Chronological: failure detected → diagnosis complete → impact assessed → fix proposed → fix verified → (human) merged/rejected → resolved. Each step timestamped with the responsible agent named (Quality Agent, Engineering Agent, Verification Agent).
6.3 Recurrence & fatigue design
New failures of a known class collapse into the existing incident's timeline rather than spawning a new card (this is the "same class of failure → scoped fix PR, not blind re-alert" behavior from the project brief). Show a count badge instead of duplicate cards.
A genuinely new failure type gets a distinct card and a louder visual treatment (top of feed, no dismiss-by-default).
Respect existing alert suppression (1-hour repeat suppression) — surface "suppressed N alerts" as a small footnote, not hidden entirely.
6.4 Empty/healthy state
When there are no open incidents: collapse the feed to a compact "All clear" strip above the tiles, don't leave a big empty panel — this is a monitoring surface, not a to-do list, and should read as calm when things are calm.


7. Shared components inventory (for Claude Design to spec as reusable pieces)
Node card (typed, per §5.2 palette) — 3 sizes: canvas (full), list (Data Assets), inline chip (mentioned in text/diffs)
Verification badge — 4 states (verified / drift / pending / not built), consistent glyph+color across Spec, Graph, Observability
Diff preview modal — added/removed/modified, used for spec re-compiles and fix PRs
Evidence chip — expandable source citation (log excerpt, query, PR link)
Incident card — collapsed/expanded, 4 sub-tabs
Recurrence badge — "Nth occurrence, same class"
Spec file-tree item — filename + verification badge
Blast-radius mini-graph — a constrained, non-editable render of the Graph canvas scoped to one incident


8. Open questions for Claude Design to explore visually (not yet decided)
Does the Graph tab need a distinct dark canvas vs. the lighter Spec/Observability chrome, or should all three unify to one theme? (Screenshots show dark canvas for Pipeline today.)
How much of the "Spec vs. Compiled diff" overlay can render inline vs. needing a dedicated modal — this could get visually busy on large graphs.
Mobile/narrow-viewport behavior for the Graph tab is unresolved — likely read-only summary card list rather than a full canvas; needs a pass.


9. Explicitly out of scope for this design pass
Any UI for agents auto-merging fixes — no such capability exists or is planned; every fix path ends at a human-reviewed PR. Do not design a "one-click auto-apply" affordance.
New Slack/notification-center configuration UI — reuse what exists.
