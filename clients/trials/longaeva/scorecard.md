---
name: "Longaeva Partners LP"
slug: "longaeva"
stage: "trial"
updated: "2026-06-16-cycle-19"
---

# Longaeva — Trial Scorecard

14-day POC. Start date: **2026-06-15** (Trial Day 2). Days are relative to the agreed start. Updated daily once trial begins.

> **2026-06-16 cycle-19 — Golden-case completeness audit + remaining-gap map.** Infra foundation is solid (OM-native AutoPilot ingestion clean to 2 keepers, Demo Redshift 196 + OneTen Snowflake 57 embeddings, dbt agent verified live e2e vs LONGAEVA_POC, MCP handshake healthy). **But against the 13 golden cases the PoC is NOT done:**
>
> | Bucket | GCs | Count |
> |---|---|---|
> | ✅ Live | GC-3 (Snowflake DQ), GC-4 (Silver time-series) | 2 |
> | 🟡 Partial | GC-6 (semantic view — built, gated on `deep_agent` MCP routing), GC-8 (validation compile), GC-10 (E2E silver→PR) | 3 |
> | 🔴 Skip / no code | GC-1, GC-2 (ingestion connectors), GC-5 (gold marts — spec only), GC-7 (reference-join), GC-9 (MCP downstream), GC-11 (self-healing GAP-7), GC-12 (longitudinal anomaly GAP-8), GC-13 (Slack-native) | 8 |
>
> **PoC completeness for a 100%-success run: ~27%** (weighted live=1.0/partial=0.5/skip=0; strict fully-live = 15%). Honest, not green-washed — the harness `skip`s exactly the unbuilt cases.
>
> **The 4 gaps flagged + their approach .MDs:**
> - **Quality rules** → `docs/specs/quality-rules-configurable.md` (BH-503, status **Ready**) — workspace rule library + `QualityRuleExecutionNode` + history. Specced, not built.
> - **Longitudinal monitoring** (GC-12 / **GAP-8**, the headline gap) → `BRIGHTHIVE_GAPS.md` §GAP-8 + proven sandbox `sandbox/monitoring/` (`monitor.py` + `00_monitoring_ddl.sql`; 4/4 anomaly families fire in sim: row-count drift, cardinality, distributional skew, null spike). Approach: persist per-run metrics → trend vs trailing window; mirror sandbox `metric_history` + `anomaly_events` tables. Sequence after BH-503. ~1 sprint, Marwan.
> - **Notifications** (BrightSignals) → scaffold shipped (bb#486); GC-12/Q5 alerting **not wired** — needs GAP-8 as the source to push from.
> - **Nightshift** (scheduled nightly monitoring) → **no dedicated .MD yet** — the cron/scheduled-run wrapper around GAP-8 + BH-503. Needs a spec.
>
> **Self-healing** (GC-11 / **GAP-7**) → `BRIGHTHIVE_GAPS.md` §GAP-7 + sandbox `self_healing/failure_modes.py` (4/4 detect→fix verified). ~1 sprint.
>
> Full gap inventory + effort/owner table: `BRIGHTHIVE_GAPS.md`. BYOW ingestion plan: `../../../docs/specs/byow-end-to-end-omd-native.md`. Posted to `#engineering` (ts `1781588321`).

> **EOD 2026-06-12 (T-3 to Day 1) — status broadcast pushed.** Tracker auto-refresh: **20/83 tickets done · 19 in flight · 44 merged PRs across 4 repos**. No new red lights since cycle-18: `deep_agent` routing is still the gating bug (Marwan), Sat 2026-06-13 staging deploy of pc#797..806 + bb#520 still the path, customer-side prep (Grant: GHE creds + MCP creds + Okta tenant) still the unknown. **Day-1 readiness: code/platform ~85%, customer-side ~0% visibility.** Status posted to `#engineering` + commented on BH-526. Notion update pending OAuth.

> **2026-06-11 cycle-18 — SV lifecycle + QC live on staging; MCP reaches the agent, not yet Snowflake.** Shipped the semantic-view *lifecycle* (lineage, ship-to-PR, QC) to staging and stood up a live MCP integration harness. Honest headline: **MCP → BrightAgent is live and verified; BrightAgent → Snowflake *via MCP* is NOT yet working** — a `deep_agent` routing gap, handed to Marwan. No green-washing; the harness proves it by failing on it.
>
> **Shipped to staging (all 4 repos at develop=staging parity):**
> - **BH-619** SV lineage — `base_tables` + join graph on `list_semantic_views` ([bb#532](https://github.com/brighthive/brightbot/pull/532)→[#533](https://github.com/brighthive/brightbot/pull/533)). Live-verified: 4 base tables + 3 joins.
> - **BH-620** ship SV YAML as a governed PR — scaffold→upsert→`commitSemanticViewToGitHub` ([bb#536](https://github.com/brighthive/brightbot/pull/536)→[#537](https://github.com/brighthive/brightbot/pull/537)). 11 contract tests, write-safety reviewed (idempotent branch, partial-write honesty).
> - **BH-622** SV QC — read-only upstream-vs-product (row counts, null rates, freshness, flags) ([bb#538](https://github.com/brighthive/brightbot/pull/538)→[#539](https://github.com/brighthive/brightbot/pull/539)). Live vs `LONGAEVA_POC`: 174,384-row mart vs 3 REF upstreams; surfaced a real `IDENTIFIER_MAP.EFFECTIVE_TO` 100%-null flag.
> - **BH-601** live MCP-driven Golden Cases + Longaeva PoC E2E harness ([bb#540](https://github.com/brighthive/brightbot/pull/540)→[#541](https://github.com/brighthive/brightbot/pull/541)) — the repeatable acceptance gate.
>
> **MCP end-to-end — proven vs blocked:**
> - ✅ MCP server live (`mcp.staging.brighthive.net/mcp`); OAuth gate fixed (`BH_MCP_*` env → staging Cognito issuer); auth→agent→Bedrock inference verified live.
> - ✅ OneTen staging workspace now → Snowflake `LONGAEVA_POC` (replaced its Synapse+2×Redshift; backup retained).
> - 🔴 `deep_agent` answers warehouse questions from `search_memory_tool`/`read_file` instead of delegating to the dbt subagent's `introspect_warehouse_schema`/`qc_semantic_view_pipeline`; when forced, errors `Missing user_id or token in session_info` (MCP→subagent handoff drops session_info). **Handed to Marwan.** Harness Q1/Q2/Q4 correctly FAIL on this by design.
>
> **6 analyst questions:** Q1 SV-list, Q2 lineage, Q3 ship-PR, Q4 QC — **all built**, *gated on the deep_agent routing fix for MCP reachability*. Q5 alerting ❌ not built. Q6 RBAC ⚠️ read-half only.
>
> **Jira:** BH-619/620/622 → Staging QC. **Notion** "2 · Current Status" + **TRACKER.md** synced. **#engineering:** Matt (Claude connect-guide) + Marwan (routing finding) posted 2026-06-10.

> **EOD 2026-06-09 cycle-17 — final tally, 20 PRs across 4 repos**. Cycles 8-17 added a CI workflow gating 70 unit tests (`pc#805`), a `make verify-pristine` one-command pre-flight (`pc#804`), folder + scripts READMEs and CONTRIBUTING guides, a Unit-Tests CI badge, and an expanded runbook glossary keying every `errorCode` to a recovery path. **Net change since cycle-7**: GC-6 platform layer was already end-to-end then; cycles 8-17 made it discoverable, gated, and testable cold by anyone with a laptop. Cycles 13-17 were explicitly marked **FILLER** in PR descriptions per user election. Eng channel updated 2026-06-09 (`#engineering` ts `1781011761.012769`). Final PR list captured under `BRIGHTHIVE_GAPS.md` `amended[]`.

> **EOD 2026-06-08 cycle-7 — GC-6 demo loop fulfills its purpose end-to-end**. After the merge train captured below, an autonomous loop shipped 8 more PRs across 4 repos closing the platform-side of GC-6 from "specced" to "live PR opens against `github.com/brighthive/longaeva-semantic-views` in 30 seconds." Composite ≥10-of-14 GCs demoed convincingly: ~70% (held — no GC moved, but GC-6 went from `[~] needs work` to `✅ end-to-end on local`). Detail:
>
> - **pc#797** — auth role hierarchy (BH-612), full OGM seed (7 unseeded types, 42 nodes), 109-mutation inventory, 14-of-23 Longaeva delta verified live
> - **pc#798** — SPEC-SEMANTIC-VIEW-AUTHORING-E2E (open, draft) — 10 invariants + 11 Gherkin scenarios + 4 properties; defines the trial-uses-our-GitHub-not-customer-GHE model
> - **pc#799** — `WorkspaceGitHubBindingNode` + `setWorkspaceGitHubBinding` + `getWorkspaceGitHubBinding` (BH-613). PAT in Secrets Manager only, never echoed
> - **pc#800** — `commitSemanticViewToGitHub` orchestrator (BH-614). 9-step pipeline, idempotent retry, every step surfaces verbatim `errorCode` + `httpStatus`. Verified against real `github.com/brighthive/longaeva-semantic-views`
> - **pc#801** — 20 deterministic eval tests for the orchestrator (BH-618) — Properties 1–4 + 5 eval rows
> - **pc#802** — LocalStack in `docker-compose.local.yml` + endpoint-aware AWS clients (BH-611). Local stack now round-trips Secrets Manager calls without LocalStack-Pro / SSO
> - **pc#803** — token-redaction regex extension (audit-debt #11). `ghu_*`, `ghr_*`, `?access_token=`, `&pat=` — closed leak surfaces on X-1 invariant. 20 regression tests
> - **bb#520** — GHE proxy selection-set drift (audit-debt #10). All 7 mutations now select `errorCode` + `httpStatus`; revives the dormant BRANCH_EXISTS retry path. 7 regression tests
> - **brighthive-scripts#3** — `provision_semantic_views_repo.sh` (BH-617) — one-command per-customer onboarding
> - **brighthive-scripts#4** — `trial_day_1_dry_run.sh` — re-runnable 5-step demo smoke against any environment + JWT, with cleanup. Verified happy + auto-merge + bad-JWT paths
> - **agentic-project-mgmt#30** — [`OPERATOR-RUNBOOK-DAY-1.md`](./OPERATOR-RUNBOOK-DAY-1.md) — pre-flight checklist + 4-mutation live demo script + 7 named recovery paths keyed on errorCode values
>
> **Trial-Day-1 platform readiness**: ✅ green. Anyone with `PC_GRAPHQL_URL` + admin JWT + workspace/asset UUIDs can run `scripts/trial_day_1_dry_run.sh` and a real GitHub PR opens. Property 1 (PAT redaction) and Property 2 (yamlHash continuity) hold under test.
>
> **Outstanding for Day 1 (humans only, not session-reachable)**: staging deploy of pc#797–803 + bb#520 (auto-flips GC-10 S6/S7 + the GC-6 demo path); BH-533 connectivity validation post-deploy; demo storyboard scope decision with Grant; LONGAEVA_AGENT_ROLE runtime in CDK.
>
> **Sprint-sized deferrals** (untouched this cycle, intentionally): #6 bb#489 multi-table semantic view, #7 generate_mart_model (GC-5), #8 Snowflake auto-trigger (~50 lines pc + SSM), BH-615 + BH-616 (webapp UI — paused per "no UI mess" instruction).
>
> Full pre-cron handoff: [`SESSION-HANDOFF-2026-06-08.md`](./SESSION-HANDOFF-2026-06-08.md).

> **EOD 2026-06-08 — Pre-trial code locked in develop** (pre-cron baseline). 24 PRs squash-merged across brightbot / pc / webapp / cdk over the weekend (bb#510, 511, 512, 513, 514, 515, 516, 517, 518, 491, 484, 501, 498; pc#793, 794, 795, 796, 779, 769, 785; wa#1132, 1133, 1102, 1123, 1124; cdk#156). 6 specs signed off in develop (SPEC-GOLDEN-CASES, SPEC-SNOWFLAKE-E2E, SPEC-GENERATE-MART-MODEL, SPEC-BB-OKTA-FEDERATED, SPEC-GHE-MIGRATION-FINAL, SPEC-MCP-DCR-RFC7591) — every code PR has a contract pointer; §10 questions resolved on all 4 spec docs that had them. Live verdict on develop HEAD: GC harness 5 passed / 8 skipped / 2 strict-xfailed in 21s; L3 full-graph e2e 1 passed in 59s; semantic-view query alive ($174B exposure across 196 issuers via `SEMANTIC_VIEW(... METRICS exposure.total_exposure_usd DIMENSIONS exposure.asset_class_code)`); 14 distinct live-Snowflake function-tier verifications green. Composite ≥10-of-14 GCs demoed convincingly: **40% → ~70%**. **Outstanding for Day 1**: staging deploy (auto-flips GC-10 S6/S7), BH-533 connectivity validation, demo storyboard scope decision with Grant (single-table vs schema-wide GC-6 framing). Full handoff: [`SESSION-HANDOFF-2026-06-08.md`](./SESSION-HANDOFF-2026-06-08.md).

> **EOD 2026-06-01**: Snowflake integration shipped end-to-end across 4 PRs (brightbot [#488](https://github.com/brighthive/brightbot/pull/488) + [#489](https://github.com/brighthive/brightbot/pull/489), platform-core [#777](https://github.com/brighthive/brighthive-platform-core/pull/777), data-organization-cdk [#156](https://github.com/brighthive/brighthive-data-organization-cdk/pull/156)). 168 unit tests green. All 7 layers of the warehouse-agnostic pattern Snowflake-compliant. Trial unblocked for §1 ingestion + §2 semantic-view enrollment.
>
> **EOD 2026-06-03**: Self-hosting deployment simplified. Per Matt's 11:29 ET email to Grant/Sumukh, BrightHive committed to ship a **Terraform module as the primary deployment path** for Longaeva (CDK remains as alternative). Trial-guide artifact extended with Path A (Terraform, recommended) + Path B (CDK), plus a uv-based local install section (`uv tool install brighthive` recommended; pip fallback documented). Simplified setup doc + Terraform module due to Longaeva by EOW 2026-06-05. New tickets **BH-584** (TF module — Ahmed), **BH-585** (setup doc — Kuri), **BH-586** (CLI/uv publish — Marwan) created under BH-526. MCP auth-workflow conversation to be held with Grant + Sumukh before Grant's vacation.
>
> **Honest engineering reality (2026-06-03)**: the FS-critical foundation is **open PRs in review, NOT merged** — Snowflake (`brightbot#488`), GHE proxy (`platform-core#778` + `brightbot#490`), P0 security chain (BH-559→565, drafts), Atlas scaffolder (`brightbot#489`, draft). Merged to `develop` so far: MCP server *scaffold* (`brightbot#497` — `invoke_analyst` still a stub), data profiler (`#485/#487`), BrightSignals notif (`#486`). Nothing is deployed to staging/prod. The PoC sandbox (11/11 use cases vs live Snowflake) de-risks the design; it is not the product running.

---

## Milestone Progress

| # | Milestone | Owner | Target | Status | Notes |
|---|---|---|---|---|---|
| 0 | Confirm exact June start date with Grant | Kuri | Pre-Day 1 | 🔲 | Was May 18 in original proposal, slipped to June |
| 1 | Use cases & success criteria confirmed | Joint | Day 1 | 🔲 | Use this scorecard as the contract |
| 2 | System access provisioned | Longaeva | Day 2 | 🔲 | Snowflake, S3, dbt repo, Dagster, GHE, their MCP server |
| 3 | Brighthive environment setup | Brighthive | Day 3 | 🔲 | Workspace + Snowflake connectivity validated |
| 4 | Context layer creation | Brighthive | Day 5 | 🔲 | Pipeline lineage, dbt sources, Snowflake schema, their YAML spec, existing semantic views |
| 5 | Environment mapping validation | Joint | Day 5 | 🔲 | Joint working session, NOT async |
| 6 | Ingestion execution (S3, REST API, Data Share) | Joint | Day 8 | 🔲 | Time-to-PR per source type |
| 7 | Semantic view enrollment + MCP validation | Joint | Day 10 | 🔲 | 1-2 datasets, end-to-end |
| 8 | Automated maintenance demo (deliberate drift event) | Joint | Day 12 | 🔲 | All 4 failure modes demonstrated |
| 9 | Final evaluation | Joint | Day 13 | 🔲 | Fill Success Criteria below |
| 10 | Next steps discussion | Brighthive | Day 14 | 🔲 | Commercial path |

Status: 🔲 Pending / 🔄 In Progress / ✅ Done / ⚠️ Blocked

---

## Success Criteria Scorecard

Filled at Day 13 evaluation (Milestone 9). 17 criteria across 4 core workstreams + 4 bonus.

### 1. Ingestion (3 source types)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 1.1 S3 — Snowflake external stage + dbt `sources.yml` | Merge-ready, ≤1 revision | — | — |
| 1.2 REST API — 20-30k instrument universe, pagination, batched IDs, parallel, retry | dbt source wired correctly | — | — |
| 1.3 Snowflake Data Share — dbt source + staging + DQ contracts | Passes validation on first run | — | — |

### 2. Semantic View Enrollment (grounded in Atlas YAML contract — `artifacts/atlas-semantic-view-spec.md`)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 2.1 YAML dimension/time-dim/fact inference from Silver schema | ≥80% correct first scaffold | — | — |
| 2.2 Atlas custom blocks populated (`dataset_key`, `entities.primary`, `defaults`, `dagster_dep`, `owners`, `custom_instructions`) | All required blocks present + non-empty `custom_instructions` | — | — |
| 2.3 `atlas.target` binding auto-inference | ≥2 of: `lngv_issuer_id`, `bloomberg_ticker`, `period_*`, `metric_attributes.geography.*` | — | — |
| 2.4 `atlas.metric.aggregations` defaulted from fact-name heuristics | counts→sum, prices→avg, percentages→raw | — | — |
| 2.5 `verified_queries[]` in Snowflake `SEMANTIC_VIEW(...)` syntax | ≥1 query per major use case | — | — |
| 2.6 YAML accepted by Atlas SDK (round-trips PyYAML; no DDL emission) | Accepted on first pass | — | — |
| 2.7 Validation via running a `verified_query` end-to-end through MCP | ≤3 revision cycles | — | — |
| 2.8 Errors surface with actionable remediation | All errors human-readable | — | — |

### 3. MCP Validation (Longaeva's internal MCP server)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 3.1 Measures, dimensions, time-dims queryable via their MCP | 100% surface | — | — |
| 3.2 Representative query suite correctness | ≤5% error rate; filtered + aggregated + multi-dim | — | — |
| 3.3 Gap detection in enrollment PR | Sample values / examples / instructions called out | — | — |

### 4a. Self-Healing — must demonstrate all 4 failure modes
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 4a.1 Schema drift from vendor | Surgical fix PR + plain-language diagnosis | — | — |
| 4a.2 Missing partition | Detected + fix PR | — | — |
| 4a.3 Broken external stage | Root cause + corrected DDL PR | — | — |
| 4a.4 dbt contract failure | Contract analyzed + targeted PR | — | — |

### 4b. Longitudinal Anomaly Monitoring
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 4b.1 Row count drift detection | Flagged vs historical baseline | — | — |
| 4b.2 Dimension cardinality breakdown | Flagged with affected dimension named | — | — |
| 4b.3 Distributional skew in numeric metric | Flagged with deviation magnitude | — | — |
| 4b.4 Unexpected nulls in well-populated column | Flagged before downstream impact | — | — |

### 4c. Slack
| Criterion | Target | Result | Pass |
|---|---|---|---|
| 4c.1 Alert triage-ready | Dataset + issue + severity + PR/run link in message | — | — |
| 4c.2 Bidirectional `@brightagent` | Pipeline state Q&A, re-run, scaffold-trigger | — | — |

### Bonus (only if core finishes early)
| Criterion | Target | Result | Pass |
|---|---|---|---|
| B.1 Vendor + dataset registry | Demo on ≥3 active datasets | — | — |
| B.2 Agentic governance walkthrough | Permission model + runaway prevention | — | — |
| B.3 KG subgraph grafting | Instruments / counterparties / vendors on base ontology, MCP-exposed | — | — |
| B.4 Rapid DQ at scale | Auto-generate + maintain test suites as datasets evolve | — | — |

---

## Daily Notes

_Days are filled in once the exact June start date is confirmed with Grant. Template below._

### Day 1 — [DATE]
_Set agenda, confirm success criteria, kick off access provisioning._

### Day 2 — [DATE]
_Access provisioned. First Snowflake connectivity smoke test._

### Day 3 — [DATE]
_Critical context handoff: their YAML spec, reference schemas, fiscal calendar, identifier maps. Joint session._

### Day 4 — [DATE]
### Day 5 — [DATE]
_Environment mapping validated. Context layer build complete._
### Day 6 — [DATE]
### Day 7 — [DATE]
### Day 8 — [DATE]
_Ingestion execution target — 3 source types done._
### Day 9 — [DATE]
### Day 10 — [DATE]
_Semantic view + MCP validation target._
### Day 11 — [DATE]
### Day 12 — [DATE]
_Automated maintenance demo — schedule deliberate drift event upstream._
### Day 13 — [DATE]
_Final evaluation — fill scorecard above._
### Day 14 — [DATE]
_Next steps discussion._

---

## Final Score

_Filled at Day 13._

| Workstream | Criteria Met | Total | Pass Rate |
|---|---|---|---|
| 1. Ingestion | — | 3 | — |
| 2. Semantic Enrollment | — | 8 | — |
| 3. MCP Validation | — | 3 | — |
| 4a. Self-Healing | — | 4 | — |
| 4b. Anomaly Monitoring | — | 4 | — |
| 4c. Slack | — | 2 | — |
| **Core total** | — | **24** | — |
| Bonus | — | 4 | — |

**Recommendation**: Won / Lost / Extended — _rationale here_
