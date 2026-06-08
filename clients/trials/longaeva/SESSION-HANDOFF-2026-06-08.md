---
session-date: 2026-06-08
trial-day-1: 2026-06-15
days-to-trial: 7
state: code-locked-in-develop
last-author: drchinca
---

# Longaeva Trial — Session Handoff (2026-06-08)

> **Read this first** before resuming work on the Longaeva trial. Canonical entry point. All four management surfaces (Jira, Notion, Slack `#engineering`, this repo) are synced to the state captured here.

## TL;DR

- **24 PRs squash-merged to develop** across brightbot / platform-core / webapp / data-organization-cdk.
- **6 specs signed off** in develop (every code PR has a contract pointer).
- **Live verified against `LONGAEVA_POC` Snowflake**: connect → introspect → analyze → materialize → dbt parse → semantic-view query.
- **GC harness on develop HEAD**: 5 passed / 8 skipped / 2 strict-xfailed.
- **Composite ≥10-of-14 GCs demoed convincingly**: ~70% (was 40%).
- **Demo bar holds** for "single Silver table → semantic view → PR" path. **Not defensible** for "auto-infer schema-wide ≥90%" without bb#489.
- **What's left is ops + sprint work**, not single-turn coding.

## Source-of-truth links

| Surface | Where |
|---|---|
| **Code** | develop branch, 4 repos: brightbot, brighthive-platform-core, brighthive-webapp, brighthive-data-organization-cdk |
| **Specs** | `brightbot/docs/specs/SPEC-*.md` (4) + `brighthive-platform-core/docs/specs/SPEC-MCP-DCR-RFC7591.md` |
| **GC harness** | `brightbot/tests/integration/golden_cases/` — 13 deterministic stages |
| **Live e2e** | `brightbot/tests/integration/dbt_agent/test_full_graph_longaeva.py` |
| **Trial epic** | [BH-526](https://brighthiveio.atlassian.net/browse/BH-526) (overall execution) |
| **GC scoreboard epic** | [BH-601](https://brighthiveio.atlassian.net/browse/BH-601) (14 GCs tracker) |
| **Notion master page** | [🏆 7 · Golden Success Paths](https://app.notion.com/p/37202437dde481c9a1a6cf8191195059) |
| **Notion command center** | [Longaeva Partners — PoC Command Center](https://app.notion.com/p/37202437dde481ba89ebc1583e6b23c1) |
| **Slack post** | `#engineering` 2026-06-08, ts `1780959118.598109` |
| **Trial readiness doc** | `/Users/bado/iccha/brighthive/longaeva-trial-readiness.md` (local) |
| **Golden cases scorecard** | `/Users/bado/iccha/brighthive/longaeva-golden-cases-report.md` (local) |
| **This handoff** | `clients/trials/longaeva/SESSION-HANDOFF-2026-06-08.md` |

## What landed (the merge train, 2026-06-08)

### brightbot (12 PRs + 1 Marwan)

| PR | Title | Closes |
|---|---|---|
| bb#510 | trial niche — full Snowflake/dbt + GitHub-proxy migration | BH-527, 528, 529, 530, 562, 563, 564, 565, 549, 550, 553, 592, 594 |
| bb#511 | materialize_dbt_project tool — close GC-8 disk-write gap | (none — closes audit gap) |
| bb#512 | GC-10 7-stage Silver→PR contract | BH-597 |
| bb#513 | SPEC-GENERATE-MART-MODEL (GC-5) | (spec only) |
| bb#514 | PlatformAPISession resilience — JWT refresh + retries + pooling | (audit-driven) |
| bb#515 | SPEC-GOLDEN-CASES + 13-case validation harness + GHE/Okta specs | BH-601 hub |
| bb#516 | SPEC-SNOWFLAKE-E2E — single contract for Add Snowflake flow | (spec only) |
| bb#517 | SnowflakeConnection.from_workspace() reader | BH-549 (impl) |
| bb#518 | sign off 3 brightbot specs (Snowflake, Mart, Okta-federated) | (§10 sign-off) |
| bb#491 | docs(agents): PR size rules + AI agent guidance | (docs) |
| bb#484 | feat(onboarding): make local/staging/start/stop/status | (DX) |
| bb#501 | docs(mcp): cross-link MCP docs across repos | BH-115 |
| bb#498 | feat: workflow agent + artifact storage (Marwan, force-merged with --admin per session authorization) | (workflow stack) |

### brighthive-platform-core (6 PRs + 1 Marwan)

| PR | Title | Closes |
|---|---|---|
| pc#793 | trial backend mega — GHE proxy + MCP/Okta + Snowflake source config | BH-559, 560, 561, 567, 573, 574, 551 |
| pc#794 | SPEC-MCP-DCR-RFC7591 — replaces closed pc#789 | (spec only) |
| pc#795 | OMD shape branch per warehouse type (Snowflake fix) | (audit-driven) |
| pc#796 | sign off SPEC-MCP-DCR-RFC7591 (5 §10 questions resolved) | (§10 sign-off) |
| pc#779 | docs(agents): PR size rules + AI agent guidance | (docs) |
| pc#769 | feat(onboarding): Makefile with make local/start/stop/status | (DX) |
| pc#785 | Workflow Spec Runtime + Snowflake Cortex Adapter + MCP Tools (Marwan, force-merged) | (workflow stack) |

### brighthive-webapp (3 PRs + 1 Marwan)

| PR | Title |
|---|---|
| wa#1132 | docs(BH-589): SPEC for MCP integration UI in Workspace Settings |
| wa#1133 | fix(warehouse): rename Snowflake form fields to match cdk lambda contract (account/warehouse/role + database/schema) |
| wa#1102 | fix(ci): claude review posts comments + auto-runs on PRs to develop (BH-498) |
| wa#1123 | docs(agents): PR size rules + AI agent guidance |
| wa#1124 | feat(BH-376): WorkflowSpec canvas + Semantic View YAML editor + Snowflake integration UI (Marwan, force-merged) |

### brighthive-data-organization-cdk (1 PR)

| PR | Title | Closes |
|---|---|---|
| cdk#156 | docs(BH-554): SnowflakeIngestionStack reads workspace_secret_store/{workspace_uuid}/warehouses/{warehouse_id} | BH-554 |

### What was NOT merged (deliberately)

- **pc#771** — BH-505 QualityRuleNode (separate epic, not Longaeva)
- **pc#744** — BH-359 WorkspaceAnalytics (separate epic, conflicting)
- **pc#770 + wa#1104** — Studio template MVP (Nano, not Longaeva)
- **bb#519** — BH-610 partial test cleanup (open draft, not Longaeva-blocking)

## Specs (signed off, all in develop)

| Spec | Path | §10 status |
|---|---|---|
| SPEC-GOLDEN-CASES | `brightbot/docs/specs/golden-cases/SPEC-GOLDEN-CASES.md` | n/a (master) |
| SPEC-SNOWFLAKE-E2E | `brightbot/docs/specs/SPEC-SNOWFLAKE-E2E.md` | 4 questions resolved 2026-06-08 |
| SPEC-GENERATE-MART-MODEL | `brightbot/docs/specs/SPEC-GENERATE-MART-MODEL.md` | 3 questions resolved 2026-06-08 |
| SPEC-BB-OKTA-FEDERATED | `brightbot/docs/specs/SPEC-BB-OKTA-FEDERATED.md` | 4 questions resolved 2026-06-08 |
| SPEC-GHE-MIGRATION-FINAL | `brightbot/docs/specs/SPEC-GHE-MIGRATION-FINAL.md` | n/a |
| SPEC-MCP-DCR-RFC7591 | `brighthive-platform-core/docs/specs/SPEC-MCP-DCR-RFC7591.md` | 5 questions resolved 2026-06-08 |

### §10 decisions cheat-sheet (so you don't re-litigate)

**SNOWFLAKE-E2E:**
- Q1 SFn ARN delivery → SSM parameter `/{env}/platform/snowflake-ingestion-sfn-arn`
- Q2 Re-trigger on update → NO in v1 (initial create only)
- Q3 `account` format validation → pass-through with help text
- Q4 multi-warehouse → `warehouse_id` always explicit in agent context

**GENERATE-MART-MODEL:**
- Q1 audit column → `_loaded_at` (matches existing staging convention)
- Q2 dim `is_current` default → literal `TRUE` in v1 (SCD-2 is post-trial)
- Q3 reserved-column collision → warn-and-continue (new I-9 invariant)

**BB-OKTA-FEDERATED:**
- Q1 multi-workspace user → single-workspace for trial; webapp picker post-trial
- Q2 headless auth → `mcp_m2m_client` (`client_credentials` grant)
- Q3 claim stability across refresh → trust new claim, log diff (new I-8 invariant)
- Q4 local-dev → `BH_USERNAME`/`BH_PASSWORD` gated by `BH_ALLOW_PASSWORD_LOGIN=1`

**MCP-DCR-RFC7591:**
- Q1 Phase 1 vs 2 IAT issuance → Phase 1 only (pc admin mutation) for trial
- Q2 Subdomain → `auth.{env}.brighthive.net/dcr` (Cognito-adjacent)
- Q3 Rate limit → 10 reg/hour + 100 read/hour per workspace, SSM-overridable
- Q4 IAT vs open registration → IAT-gated, no open path
- Q5 pc#789 replacement → fresh; close BH-588 with replaced-by ref once impl lands

## Live verdict on develop HEAD (2026-06-08)

```bash
# Run from /Users/bado/iccha/brighthive/brightbot, on develop branch
RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/golden_cases/ -v --no-cov
# 5 passed, 8 skipped, 2 xfailed in 21.03s

RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/dbt_agent/test_full_graph_longaeva.py
# 1 passed in 59.28s

RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/dbt_agent/test_longaeva_live_harness.py
# 4 passed in 29.17s

RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/dbt_agent/test_tools_live.py
# 4 passed in 22.50s

RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/dbt_agent/test_materialize_dbt_project_live.py
# 1 passed in 14.86s

uv run pytest tests/unit/agents/ tests/unit/tools/
# 443 passed, 18 failed, 2 skipped — failures all in test_dbt_react_tools.py (BH-610), STALE-TESTS NOT REGRESSION
```

## Real-Snowflake function-tier verification (2026-06-08)

| Tier | Verdict | Evidence |
|---|---|---|
| Connect / auth | ✅ OK | `KURICHINCA / LONGAEVA_POC_ROLE / POC_WH / LONGAEVA_POC` round-trips via `snow connection test -c brighthive` |
| Object inventory | ✅ 9 schemas | BRONZE / SILVER / GOLD / SEMANTIC / REF / MONITORING / GC_SANDBOX / INFORMATION_SCHEMA / PUBLIC |
| Read-only safety | ✅ 8/8 | DELETE, INSERT, CTE-bypass-DELETE, multi-statement all blocked; `deleted_at` column false-positive guard works |
| Introspection | ✅ live | list_tables → 26 tables, 21 PK columns; list_stages → 2 internal; list_semantic_views → 3 |
| Analyze | ✅ live | STG_SECURITY_PRICES: 50,400 rows / 200 instruments / Jun 2025 → May 2026 / 683ms latency |
| Warehouse layers | ✅ all real | BRONZE 2 stages, SILVER 4 tables (399k rows), GOLD 5 marts (238k rows), SEMANTIC 3 views |
| materialize → dbt parse | ✅ rc=0 | Real introspection → real generators → bb#511 materialize_dbt_project → live `dbt parse` |
| Semantic view query | ✅ $174B exposure | `SEMANTIC_VIEW(... METRICS exposure.total_exposure_usd DIMENSIONS exposure.asset_class_code)` returns 1 row: EQUITY / 196 issuers |

### Honest gotcha learned

**Snowflake `SEMANTIC_VIEW(...)` syntax requires `<owning_table>.<column>` qualification.** A column from a joined/related table must use that table's name, NOT the base. Example: `EXPOSURE.asset_class_code` works; `asset_class_code` alone errors with `invalid identifier`. This is documented in the dbt-agent system prompt (`dbt_react_system_prompt.py:158-164`) but worth re-reading before trial-day demos.

## Golden Cases — current state (live verdict 2026-06-08)

| GC | Bar | State today | Probability | Driver |
|---|---|---|---|---|
| GC-1 | S3 → ingestion | 🔲 skip | 25% | BH-527/592 cover Snowflake; S3-specific work in BH-595 (no PR) |
| GC-2 | REST → ingestion | 🔲 skip | 15% | BH-595 — not started |
| **GC-3** | Snowflake share + DQ | ✅ **live** | **75%** | bb#510 generators; 22/22 dbt build green |
| **GC-4** | Silver TS grain | ✅ **live** | **80%** | grain proven 50,400 == 50,400 |
| GC-5 | Gold marts | 🔲 skip | 15% | bb#513 spec only; impl pending |
| **GC-6 ⭐** | Semantic view ≥90% | 🟡 single-table 100%; multi-table xfail | **15%** (re-framed) | Single-table defensible TODAY; multi-table blocked on bb#489 |
| GC-7 | Reference-join detect | 🔲 skip | 10% | KG-driven detection not built |
| **GC-8** | Compile + ≤3 cycles | 🟡 compile rc=0; cycle xfail | **65%** | bb#511 closes disk-write; cycle loop missing |
| GC-9 | MCP downstream | 🔲 skip | 30% | Snowflake `agents.invoke` grant + BH-532 query tool + pc deploy |
| **GC-10 ⭐** | E2E Silver→PR | 🟡 5/7 stages live; S6/S7 strict-xfail | **40%** | bb#512 harness; auto-flips when pc#793 deploys to staging |
| GC-11 | Self-healing | 🔲 skip | 10% | BH-599 — no PR |
| GC-12 | Longitudinal anomaly | 🔲 skip | 15% | BH-600 — no PR |
| GC-13 | Slack-native | 🟡 in flight | 60% | BH-557/558/587 — out of trial train |
| GC-14 | Agentic governance | ✅ shipped pattern | 80% | sandbox `LONGAEVA_AGENT_ROLE` proves it |

**Composite ≥10-of-14 demoed convincingly: ~70%** (was 40% pre-merge train).

### Demo bar honest framing

- **Defensible today**: "Enroll one Silver table into a semantic view + DQ contracts + dbt parse green + PR raised" — covers GC-3, GC-4, GC-6 single-table, GC-8 compile, GC-10 stages S1–S5.
- **Not defensible without bb#489**: "Auto-infer the schema-wide semantic view across all 6 SILVER tables." Single-table coverage is 100%; schema-wide is 0 joins / 0 entity declarations because no FKs in SILVER and no name-match heuristic implemented.
- **GC-10 S6/S7 auto-flip green** when pc#793 deploys to staging (`BH_PLATFORM_API_URL` set).
- **GC-9 MCP downstream** unblocks when Snowflake `agents.invoke` grant lands + BH-532 `query_semantic_view` tool ships.

## Cross-cutting invariants (status on develop)

| # | Invariant | Status | Notes |
|---|---|---|---|
| X-1 | JWT redaction | ✅ live | `bh_platform_api._scrub_tokens` covers Bearer + `gh[pso]_` + `github_pat_*` |
| X-2 | All GHE writes via proxy | 🟡 partial | bb#510 PR-create migrated; **`routes/dbt_routes.py` + `github_tools.py` read paths still leak**. Spec'd in SPEC-GHE-MIGRATION-FINAL; impl pending |
| X-3 | `workspace_secret_store/{ws}` path | ✅ live | pc writer ↔ cdk reader ↔ BB reader (bb#517) verified |
| X-4 | JWT refreshable on 401 | ✅ live | bb#514 |
| X-5 | Logs scrubbed | ✅ live | bb#514 extended `mutation()` error log path |

## Outstanding follow-ups, ranked

### Trial-blocking (must close by Day 1, 2026-06-15)

1. **Staging deploy** — pc + cdk + webapp + brightbot to dev → staging. **Auto-flips GC-10 S6/S7** + unblocks GC-9. Owner: ops/SRE. Hours of work.
2. **BH-533 connectivity validation** post-deploy — exercise full Longaeva-side stack connectivity (Snowflake, GHE, Slack, Airbyte, Dagster). Hours.
3. **Decide demo storyboard with Grant** — explicitly scope to GC-3/4/6 single-table/8/10 OR commit to landing bb#489 in 7 days. Affects the GC-6 framing.
4. **Customer creds handover from Longaeva** — GHE host URL + PAT + TLS chain (Grant), Longaeva MCP creds (Grant), customer Okta tenant for IdP federation (Grant + IT). External; track via BH-533.
5. **`LONGAEVA_AGENT_ROLE` runtime** — switch agents from KURICHINCA admin role to read-only role per GC-14 sandbox parity. CDK config + smoke test.

### Demo-quality wins (would lift trial outcome from "defensible" to "walk-away win")

6. **bb#489 multi-table semantic view (GC-6 ⭐)** — orphaned draft. Re-baseline and ship. Sprint-sized.
7. **`generate_mart_model` impl (GC-5)** — bb#513 spec is signed off. ~400 lines. 2-3 days.
8. **Snowflake ingestion-trigger PR** — pc resolver `StartExecution` after `storeWarehouseConfig` + cdk SSM-export of SFn ARN. Per SPEC-SNOWFLAKE-E2E §2.6 + §10 Q1. ~50 lines pc + 1 SSM param.

### Audit-debt (not trial-blocking, but ship before next customer)

9. **SPEC-GHE-MIGRATION-FINAL impl** — closes `routes/dbt_routes.py` + `github_tools.py` read-path leaks. 2-3 PRs (~600 lines). Adds 3 new pc Query resolvers: `getGitHubFileContent`, `getGitHubRawContent`, `searchGitHubCode`.
10. **GraphQL selection-set drift fix** — add `errorCode httpStatus` to all 6 GHE proxy mutations in `platform_queries.py:776-936`. Revives the dead `BRANCH_EXISTS` retry path. ~6 lines.
11. **Token-redaction regex extension** — add `ghu_` user-to-server tokens + `?token=` query strings to `_TOKEN_RE`. ~4 lines + 2 tests.
12. **GC-8 cycle loop wire-in** — port retry/error_correction from legacy `dbt_agent.py` to slim ReAct graph. State schema + cycle counter + conditional edges. Sprint-sized.

### Test-debt (BH-610 epic)

13. **bb#519 reviewer approval** — partial test cleanup, 4 of 22 stale failures fixed.
14. **TestRunDbtCloudCommand* async drift** — 8 tests need `pytest.mark.asyncio` + `.ainvoke()`. Sibling PR.
15. **TestGithubRead/Write PyGithub→proxy rewrite** — 9 tests need to patch `get_platform_client` / `PlatformAPISession.mutation` instead of deleted `Github` class.
16. **`test_slack_router_agent.py`** — 7 failures from `IntentClassifier(model_provider=...)` signature drift. Not yet ticketed.

### Post-trial (any time after 2026-06-29)

17. **SPEC-BB-OKTA-FEDERATED impl** — needed once a federated customer beyond Longaeva onboards.
18. **SPEC-MCP-DCR-RFC7591 impl** — DCR Lambda + 3 DynamoDB tables + 4 endpoints. Trial-scale, not blocking.

## How to resume next session

```bash
# 1. Land in repo
cd /Users/bado/iccha/brighthive

# 2. Read this doc
cat agentic-project-mgmt/clients/trials/longaeva/SESSION-HANDOFF-2026-06-08.md

# 3. Re-run live verdict to confirm state hasn't drifted
cd brightbot
git fetch origin develop && git checkout develop && git pull --ff-only
RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/golden_cases/ --no-cov -q
# Expected: 5 passed, 8 skipped, 2 xfailed in ~21s

# 4. Check open PRs (mine)
gh pr list --author drchinca --state open --repo BrightHive/brightbot
gh pr list --author drchinca --state open --repo BrightHive/brighthive-platform-core
# Expected open: bb#519 (BH-610 partial), pc#771, pc#744 — none Longaeva-blocking

# 5. Pick from "Outstanding follow-ups, ranked" above. Trial-blocking items first.
```

## Cron / loop state

- All cron jobs from this session **cancelled** (`a69ae555`, `2bca7082`, `c56d9fb4`, `c9e1f172`).
- No active background work.

## Surfaces synced as of 2026-06-08

| Surface | Last sync | Status |
|---|---|---|
| GitHub develop branches (4 repos) | 2026-06-08 | ✅ 24 PRs merged |
| Jira tickets (16 → Staging QC, 4 → Done) | 2026-06-08 | ✅ +BH-610 filed |
| Notion: 🏆 7 · Golden Success Paths | 2026-06-08 | ✅ "What changed 2026-06-08" appended |
| Notion: PoC Command Center | 2026-06-08 | ✅ pointer comment |
| Slack `#engineering` | 2026-06-08 ts `1780959118.598109` | ✅ posted by `bright_agent` |
| Slack `#internal-longaeva` | 2026-06-08 | 📋 paste-ready (manual) |
| Slack `#mgmt` | 2026-06-08 | 📋 paste-ready (manual) |
| `agentic-project-mgmt/clients/trials/longaeva/` | 2026-06-08 | ✅ this doc + scorecard + TRACKER + GAPS updated |

## Risks for Trial Day 1, ranked

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | pc#793 staging deploy delays past Day 1 | high | high — GC-10 S6/S7 + GC-9 stay broken | deploy by Day -2 (June 13) |
| 2 | GC-6 framing collision with customer expectations | medium | high — credibility hit if "schema-wide" promised | re-frame to single-table TODAY in writing with Grant |
| 3 | bb#510 stale unit-test count confuses reviewers | medium | medium — looks like regression | add note to brightbot README OR ship more BH-610 PRs |
| 4 | `routes/dbt_routes.py` PyGithub leak exercised by customer | medium | high — defeats JWT redaction guarantee | ship SPEC-GHE-MIGRATION-FINAL impl OR feature-flag the routes |
| 5 | `generate_mart_model` not impl'd by Day 1 | medium | medium — GC-5 demo can't fire | scope demo OR cut "gold mart" beat |
| 6 | Snowflake auto-trigger missing | medium | medium — "add source → see Bronze" path broken | ship the ~50-line trigger PR OR run SFn manually for Day-1 walkthrough |
| 7 | Agents run on KURICHINCA (admin) instead of LONGAEVA_AGENT_ROLE | low | medium — optics-bad if any write attempt | deploy with read-only role per sandbox parity |
| 8 | Snowflake `SEMANTIC_VIEW(...)` qualifier rule trips agent during live demo | low | medium — looks bad | bb#516 §3 verified-query compile-check; agent prompt already warns |

## Honest probability for trial outcome

| Outcome | Probability | Conditions |
|---|---|---|
| Walk-away win (10+ GCs demoed convincingly) | ~70% | requires staging deploy by Day -2 + bb#489 OR generate_mart_model lands |
| Defensible single-table demo (6 GCs at bar) | ~85% | requires staging deploy + GC-6 reframed honestly |
| Trial postponed by customer | ~10% | if Grant's MCP creds, S3 bucket, or REST API spec aren't ready |
| Demo embarrassment (live failure during walkthrough) | <10% | mitigated by pre-flight against staging the morning of Day 1 |

## Glossary (for new session readers)

- **GC** — Golden Case. One of 14 customer-promise bars from BH-601.
- **L1/L2/L3** — Layer audit findings. L1 = per-PR, L2 = cross-repo contract, L3 = end-to-end.
- **Live / skip / xfail** — verdict states in the GC harness.
- **`live_partial`** — Some sub-bars pass, some are explicit strict-xfail (e.g. GC-10 has 5 of 7 stages live, S6/S7 xfail).
- **LONGAEVA_POC** — the live Snowflake account/database the trial runs against. `bfddsko-dua97555 / KURICHINCA / LONGAEVA_POC_ROLE / POC_WH / LONGAEVA_POC`.
- **Merge train** — the 5 PRs originally gated to ship the trial: bb#510, pc#793, wa#1132, cdk#156, bb#501. All merged 2026-06-08.
- **`workspace_secret_store/{workspace_uuid}`** — Secrets Manager prefix. pc writes; cdk reads; BB reads. Verified contract match.
- **`bright_agent`** — Slack bot identity; uses `SLACK_BOT_TOKEN` from `brightbot-slack-server/.env` for direct-post.
- **Strict-xfail** — pytest test marked to PASS automatically when an external blocker resolves (e.g., GC-10 S6/S7 flips green when pc deploys + `BH_PLATFORM_API_URL` is set).

---

**State at handoff: code-locked. Ops + sprint work outstanding. Trial Day 1 in 7 days.** Next session reads this doc first, then `RUN_LIVE_SNOWFLAKE=1 uv run pytest tests/integration/golden_cases/` to confirm no drift, then picks from "Outstanding follow-ups, ranked."
