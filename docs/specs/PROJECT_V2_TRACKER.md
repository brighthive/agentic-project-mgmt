# 🧭 PROJECT_V2 Tracker — gluing existing capacities together

> This is not a new-feature backlog. Every row below is a **wiring gap between capacities that
> already ship** — BrightRoutines, `governance_agent` monitoring, the Project Spec 2.0
> pipeline-authoring engine, spec-conformance badges, and Skills routing. State verified against
> code and live PR/Jira lookups on **2026-09-22**, not taken from a ticket's `Status` field alone
> — see [ROADMAP.md](ROADMAP.md)'s own finding that Jira status routinely disagrees with what
> shipped.

## Legend

Reused verbatim from [ROADMAP.md](ROADMAP.md) so the two trackers read as one system.

| | Means |
|---|---|
| 🟢 **SHIPPED** | merged and provable at `file:line` |
| 🟠 **PARTIAL** | some of it exists; the named remainder is real |
| 🟡 **OPEN** | genuinely absent — a named grep returns zero |
| 🔵 **RELEASE** | finished on `develop`/`staging`; only a prod cut remains |
| ⚠️ **RECOVER** | finished work at risk — orphaned, stale status, or unmerged |
| 🔴 **SUPERSEDED** | the ticket's own premise is wrong — corrected by newer, code-verified work |

## The one correction that changes everything below

`BH-1343` and `BH-1504` are both written around a `SYNC()` mechanism. `THEME-spec-driven-pipelines.md`
(2026-09-16, three red-team passes) verified live against staging that **`SYNC()` is
vaporware — zero code** — and named the two real mechanisms to reuse instead:
`project_activation_check_routes.py` (real, shipped "prompt → findings → notification" trigger)
and `execute_workflow` (BH-877–881, real, shipped recurring scheduler). Both tickets should be
rewritten against those primitives, not built as specced. Flagged 🔴 below.

---

## Ticket table — verified 2026-09-22

| Key | Summary | Epic | Jira status | Code reality | Verdict |
|---|---|---|---|---|---|
| BH-1255 | Scheduled, Versioned, Lineage-Aware Pipeline Runs | — (epic) | Needs Refinement, **unassigned** | Parent epic for most of this tracker | 🟡 needs an owner |
| BH-1343 | Project ACTIVE → SYNC(): activation fan-out | BH-1255 | Needs Refinement | `SYNC()` confirmed zero code; superseded | 🔴 rewrite against `execute_workflow` + activation-check pattern |
| BH-1503 | Wire Great Expectations quality-check as a golden-nugget source in SYNC() | BH-1255 | Needs Refinement | Depends on BH-1343's mechanism | 🔴 same — retarget before building |
| BH-1504 | Recurring project SYNC() trigger | BH-1255 | Needs Refinement | This is the literal SYNC() ticket | 🔴 rewrite as "call `execute_workflow` for recurring re-check," not a new scheduler |
| BH-1505 | `project` Skills-affinity bucket + routing | BH-1255 | Needs Refinement — **stale** | 🟢 **SHIPPED** — `brightbot#1061` merged 2026-09-08 | ⚠️ move ticket to Done; zero `SKILL.md` tagged `affinity:[project]` yet — that's a *new*, smaller follow-up, not this ticket |
| BH-1506 | `addResourceToProject`/`removeResourceFromProject` missing `workspaceId` | BH-1255 | Needs Refinement — **stale** | 🟢 **SHIPPED** — `platform-core#1276` merged 09-05, `webapp#1450` merged 09-06 | ⚠️ move ticket to Done |
| BH-1507 | resource↔project link/unlink never invalidates Redis cache | BH-1255 | Needs Refinement — **stale** | 🟢 **SHIPPED** — same PR as BH-1506 | ⚠️ move ticket to Done |
| BH-1508 | Move activation/sync fan-out off `BackgroundTasks` onto a fair queue | BH-1255 | Needs Refinement | 🟡 no queue exists — real gap | Keep open; blocked behind BH-1343/1504's retarget |
| BH-1527 | Parse `/spec/*.md` frontmatter + canonical sections | BH-1255 | Needs Refinement | 🟠 **PARTIAL** — `platform-core#1300` (merged 09-18) parses spec markdown; unclear if it's this exact ticket's shape or a parallel path — **needs a verification pass** (see Open Items) | 🟠 verify before building more on top |
| BH-1528 | Spec Agent skill — parse spec into **Intent Graph** + diff | BH-1255 | Needs Refinement — **title still says "Intent Graph"** | Theme doc's own history: this exact framing was red-team-corrected 09-16 to extend `WorkflowSpec`, not build a parallel Intent Graph. The Jira **title** never got updated to match (only the description, per commit `b541363`) | ⚠️ rename ticket title before anyone picks it up cold |
| BH-1529 | Spec-conformance check — deployed vs. declared drift | BH-1255 | Needs Refinement | 🟠 **PARTIAL** — `spec-conformance.ts` exists on an unmerged local branch, classifies BUILT/NOT_BUILT/UNKNOWN | Close to done; needs a PR |
| BH-1530 | Per-section conformance status + Spec tab badges | BH-1255 | Needs Refinement | 🟡 no `Spec` tab exists in webapp yet; product decision to build one made 2026-09-17, gated behind `Flow`'s feature flag | Unblocked, not started |
| BH-172 | Platform Features & Enhancements (epic) | — (epic) | To Do | Parent epic for the schema-contract chain below | — |
| BH-1511 | Schema-contract resolver + typed `SchemaContract` model | BH-172 | Needs Refinement | 🟡 open | First in the 1511→1512→{1513,1514,1515} chain |
| BH-1512 | Deterministic conformance validator for schema contracts | BH-172 | Needs Refinement | 🟡 open, depends on 1511 | — |
| BH-1513 | Bind OUTPUT schema contract to analysis/query | BH-172 | Needs Refinement | 🟡 open, depends on 1512 | — |
| BH-1514 | Bind INPUT/OUTPUT schema contracts to dbt transformation generation | BH-172 | Needs Refinement | 🟡 open, depends on 1512 | — |
| BH-1515 | Bind schema contract gates to visualization + join output | BH-172 | Needs Refinement | 🟡 open, depends on 1512 | — |
| BH-1464 | Authorization & Governance Enforcement — one decision point | — (epic) | In Progress | 🟠 `authorize()` engine shipping now, ABAC (attribute-based access control) conditions added (BH-1491) | Open architecture question: does this become BH-172's "one enforcement point," making part of the 1511–1515 chain redundant? Not yet resolved |
| BH-1479 | Audit: sweep for authz/masking bypass paths | BH-1464 | Testing (Dev) | Same bug class as BH-1506/1507 | Cross-linked, in review |
| BH-1491 | Attribute conditions on `authorize()` | BH-1464 | Testing (Dev) | 🟠 in review | — |
| BH-1495 | `createQualityRuleExecution` missing workspace scope (cross-tenant write bug) | BH-1464 | Testing (Dev) | **Blocks BH-1503** — quality-check write path this ticket would use is mid-fix for a live cross-tenant bug | Don't build BH-1503 until this lands |
| BH-1061 | Lineage-Aware Data Quality (epic) | — (epic) | Needs Refinement | Lineage subsystem itself is 🟢 shipped and fully Project-scoped — the one capacity here that *isn't* isolated | — |

---

## PRs in flight — verified live, 2026-09-22

| PR | Repo | State | What it actually contains |
|---|---|---|---|
| #1061 | brightbot | 🟢 **MERGED** 09-08 | `project` Skills-affinity routing (BH-1505) |
| #1276 | platform-core | 🟢 **MERGED** 09-05 | `workspaceId` fix + cache invalidation (BH-1506/1507) |
| #1450 | webapp | 🟢 **MERGED** 09-06 | Call-site updates for the above |
| #1300 | platform-core | 🟢 **MERGED** 09-18 | Project Spec 2.0: parse spec → resolve real `DataAsset`s → brightbot LLM-authors a pipeline preview → apply → smoke-validate. **On-demand only** — nothing schedules it |
| #188 | agentic-project-mgmt | 🟡 OPEN, draft | `THEME-project-proactive-lifecycle.md` — never merged, doesn't exist on `master` |
| #189 | agentic-project-mgmt | 🟡 OPEN, draft | BH-1511–1515 ticket bodies |
| #191 | agentic-project-mgmt | 🟡 OPEN, draft, mergeable, **zero reviews** | The reconciliation itself — `THEME-spec-driven-pipelines.md` + the correction log entries this tracker is built from |

---

## Open items — need a decision or a next action, not more research

1. **Land #191 first.** It's mergeable today. Everything in this tracker is downstream of it becoming canonical instead of sitting in draft limbo.
2. **Verify `platform-core#1300` doesn't repeat the Intent-Graph mistake.** The theme doc caught itself designing a parallel pipeline mechanism instead of extending the shipped `WorkflowSpec` compiler (`compiler.ts`) — before any code was written. #1300 shipped a `propose-pipeline-from-spec.ts` that produces a `status: "preview"` pipeline object; confirm it authors into `WorkflowSpec` rather than a second parallel shape. This is a code review, not new research.
3. **Jira hygiene**: move BH-1505/1506/1507 to Done (code shipped); rename BH-1528's title off "Intent Graph"; assign BH-1255 to someone.
4. **Two small wiring items have no ticket yet** — flagging rather than filing, since ticket creation needs an explicit go:
   - Thread `project_id` through `governance_agent`'s `pipeline_watchdog_task` / `quality_check_task` so proactive monitoring becomes Project-scoped (currently zero `project_id` in either file).
   - Author actual `SKILL.md` content tagged `affinity: [project]` — BH-1505's routing has been merged and empty since 09-08.
5. **BH-1495 (cross-tenant write bug) blocks BH-1503.** Don't schedule BH-1503 work until BH-1495 ships.
6. **Open architecture question, not yet resolved**: does BH-1464's `authorize()` engine (with ABAC conditions since BH-1491) become BH-172's "one enforcement point," making part of the BH-1511–1515 chain redundant? Flagged in the theme doc itself as unresolved.

---

## Sequencing (from `THEME-spec-driven-pipelines.md`, mapped to real ticket keys)

```
BH-1527 → BH-1528 → { BH-1529, BH-1530 }        (spec-driven pipeline authoring)
BH-1511 → BH-1512 → { BH-1513, BH-1514, BH-1515 } (schema-contract gates)
BH-1343/1504 (rewritten) → BH-1503 (blocked on BH-1495) → BH-1508 (queue)
```

Not sized against code yet — same caveat `ROADMAP.md` already applies to `THEME-spec-driven-pipelines.md`.

## Related

[ROADMAP.md](ROADMAP.md), [THEME-spec-driven-pipelines.md](THEME-spec-driven-pipelines.md),
[THEME-governance-enforced.md](THEME-governance-enforced.md),
[project-activate-sync-golden-nuggets.md](project-activate-sync-golden-nuggets.md) (BH-1343 source spec).
