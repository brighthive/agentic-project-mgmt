# BrightRoutines — Team Reference (BH-876)

> One-page map of the whole epic: what it does, the flow, and every env / feature
> flag / cloud resource it touches. Share this with the team.
> Deep spec: [`docs/specs/brightroutines-intent-loop.md`](docs/specs/brightroutines-intent-loop.md)
> · persistence slice: [`docs/specs/brightroutines-your-routines-persistence.md`](docs/specs/brightroutines-your-routines-persistence.md)

## What it is

BrightRoutines notices when a workspace keeps asking BrightAgent for the same
thing (the weekly earnings report, the daily pipeline status…), and offers to
run it automatically on a schedule. The user turns it on in one click; it runs
headless and delivers where they work (webapp / Slack). They can turn it off
anytime, and "Your routines" survives a reload.

## The flow

```text
  ┌───────────────────────────── brightbot ─────────────────────────────┐
  │  user chats → deep_agent turn                                       │
  │       → IntentCaptureMiddleware  (after_agent, SYNC hook)           │
  │            gate: FEATURE_FLAG_BRIGHTROUTINES_CAPTURE                │
  │            (threaded, off the graph loop)                           │
  │            classify → scrub PII → fingerprint → embed               │
  └─────────────────────────────────┬───────────────────────────────────┘
                                     ▼
      ProactiveSignal row  ──▶  brightroutines-{env}  (DynamoDB, GSI1)
                                     │
   nightly / on-demand:  detect_recurring_patterns graph
                                     │  cluster (embedding cohesion ≥ 0.86, 28d window)
                                     ▼  8 trust gates
      RoutineJudge (N=3 Bedrock quorum, median)
                                     │  offer iff median ≥ MIN_JUDGE_CONFIDENCE (0.70)
                                     ▼
      RoutineSuggestion (OFFERED)  ──▶  brightroutines-{env} (GSI4)
                                     │
   webapp /context/workflows         │  reads/writes via
   "Suggested" + "Your routines"  ──▶  platform-core GraphQL (Apollo Lambda)
   Schedule / Dismiss / Off          │  ├─ routineSuggestionsForWorkspace  (OFFERED read)
                                     │  ├─ scheduledRoutinesForWorkspace   (SCHEDULED read · BH-975)
                                     │  ├─ scheduleRoutineSuggestion       (OFFERED→SCHEDULED · BH-967)
                                     │  ├─ dismissRoutineSuggestion        (→DISMISSED/SUPPRESSED)
                                     │  └─ unscheduleRoutine               (SCHEDULED→OFFERED · BH-976)
                                     ▼
      schedule creates/deletes an execute_workflow cron
                                     │
   brightbot POST/DELETE /manage/scheduled-agents  ──▶  EventBridge Scheduler
                                     │  cron fires → dispatcher Lambda → LangGraph run
                                     ▼
      result delivered  (webapp / Slack)
```

## Suggestion state machine

```text
                     schedule                       (cron deleted)
   OFFERED ──lock──▶ SCHEDULING ──success──▶ SCHEDULED ──lock──▶ UNSCHEDULING ──▶ OFFERED
      │                  │                      ▲                     │
      │ dismiss          └── failure ───────────┘  (rollback)         └── delete fails / 409 ──▶ SCHEDULED
      ▼                                                                   (never OFFERED w/ live cron)
   DISMISSED ──(2nd dismiss, same pattern)──▶ SUPPRESSED
```

- **Delete-before-flip** on turn-off: cron deleted *before* re-offer; a delete
  failure rolls back to SCHEDULED so a turned-off routine never keeps firing.
- **Conditional writes** guard every transition — concurrent turn-offs: exactly
  one wins. Stale `*_started_at` lock (> 10 min) self-heals via reclaim.
- **Owner-only** turn-off; all reads/writes **workspace-membership gated**
  (`@authenticated(workspaceIdLoc)`).

## Repos & branches

| Repo | Role | dev branch | staging | prod |
|---|---|---|---|---|
| `brightbot` | capture middleware, detector, judge, `detect_recurring_patterns` graph | `develop` | `staging` (`build_on_push`) | `main` |
| `brighthive-platform-core` | GraphQL query/mutations, DynamoDB store (CDK), Apollo Lambda | `develop` | `staging` (prerelease → `deploy-staging.yml`) | `main` (release → `release.yml`) |
| `brighthive-webapp` | `/context/workflows` — Suggested + Your routines | `develop` | `staging` (Amplify) | `main` (Amplify) |
| `brighthive-e2e` | surface + lifecycle + concurrency tests | `master` | runs *against* env | — |
| `agentic-project-mgmt` | specs, this doc | `master` | — | — |

## Cloud resources

| Resource | Detail |
|---|---|
| **DynamoDB table** | `brightroutines-{dev,stg,prod}` — single-table, PK=`WORKSPACE#<ws>` SK=`SIGNAL#…`/`PATTERN#…`/`SUGGESTION#…`, TTL attr `ttl` (~35d on signals). CDK: `brighthive_core/brightroutines_data_stack.py` |
| **GSI1** | `SCHEDULABLE#<ws>` / `<iso>#<fingerprint>` — schedulable signals by fingerprint (detector read) |
| **GSI2** | `USER#<ws>#<user>` / `<iso>` — signals by user |
| **GSI3** | `PATTERN_STATUS#<ws>#<status>` / `<last_detected_at>` — patterns by status |
| **GSI4** | `SUGGESTION_STATUS#<ws>#<status>` / `<offered_at>` — **suggestions by status** (OFFERED / SCHEDULED reads) |
| **GSI5** | `SCORE_SCOPE#…` — W/P/U scoring rollups (BH-950) |
| **EventBridge Scheduler** | group `scheduled-agents`; one schedule per turned-on routine (dispatcher Lambda ARN + role via env) |
| **Bedrock** | judge model (Sonnet default) + intent classifier (Haiku default) |
| **Embeddings** | OpenAI `text-embedding-3-small` (env `GRAPHQL_EMBEDDING_MODEL`) — signal + cohesion vectors |
| **Apollo Lambda** | platform-core GraphQL — needs `BRIGHTROUTINES_TABLE_NAME` env + `grant_read_write_data` on the table (both wired in `core_subgraph_api_stack.py`) |

## Feature flags & env vars

Resolution (`brightbot/utils/feature_flags.py`): **global env flag** →
if off, off everywhere; if on, check **per-workspace** override in AWS Secrets
(`workspace_secret_store/<ws>`); capture middleware passes `default=False`.

| Flag / var | Where | Default | Purpose |
|---|---|---|---|
| `FEATURE_FLAG_BRIGHTROUTINES_CAPTURE` | brightbot deployment env (global) + per-ws Secrets override | **off** | master switch for capturing chat turns as signals |
| `BRIGHTROUTINES_TABLE_NAME` | brightbot **and** platform-core Apollo Lambda | — (**required**) | the DynamoDB table; store no-ops if unset |
| `BRIGHTROUTINES_MIN_JUDGE_CONFIDENCE` | brightbot | `0.70` | offer threshold (recalibrated from 0.85 · BH-956) |
| `BRIGHTROUTINES_JUDGE_MODEL` | brightbot | `sonnet` | judge model tier (Bedrock) |
| `BRIGHTROUTINES_CLASSIFIER_MODEL` | brightbot | `haiku` | intent classifier tier |
| `BRIGHTROUTINES_CAPTURE_MAX_WORKERS` | brightbot | `4` | capture thread-pool size |
| `BRIGHTROUTINES_CAPTURE_DEADLINE_S` | brightbot | `30` | per-capture deadline |
| `BRIGHTROUTINES_ENDPOINT_URL` | platform-core (local dev only) | unset | points the routines DynamoDB client at LocalStack |
| `SCHEDULER_WEBHOOK_URL` | platform-core (from Secrets) | — | brightbot base URL for schedule create/delete |

> ⚠️ Changing any deployment env var / Secrets Manager / LangSmith deploy var
> requires **explicit per-edit approval** (Sherbiny's standing rule) + the
> LangSmith snapshot protocol. Enabling capture per-workspace = a Secrets write
> under that rule.

## Detector tuning (brightbot/routines/detector.py)

| Constant | Value | Meaning |
|---|---|---|
| `DETECTION_WINDOW_DAYS` | 28 | trailing signal window |
| `COHESION_SIMILARITY_THRESHOLD` | 0.86 | embedding-cohesion cluster cutoff |
| `MIN_DISTINCT_USERS` | 3 | gate 2 (breadth) — OR one user ≥5× across ≥3 weeks |
| `MIN_SAME_USER_OCCURRENCES` | 5 | single-user recurrence path |
| `MIN_OUTCOME_OK_RATE` | 0.8 | gate 3 |
| `MIN_CADENCE_CONSISTENCY` | 0.6 | gate 5 |
| `MIN_JUDGE_CONFIDENCE` | 0.70 | gate 6 (judge median) |
| `MIN_SUMMARY_TOKENS` | 30 | signals below this excluded from cohesion |
| Judge samples (`N`) | 3 | median-of-3 Bedrock quorum |

## Deploy runbook

- **brightbot** → merge to `staging` branch; `build_on_push` rebuilds
  `brightagent-staging` automatically. (Prod: merge to `main`.)
- **platform-core** → PR `develop`→`staging` (a **merge** PR, resolve
  typedefs/`schema.graphql` conflicts to develop + regenerate SDL), then
  `gh release create vX.Y.Z-pre-release --target staging --prerelease`
  (`deploy-staging.yml` fires on `prereleased`). **Regenerate the SDL**
  (`npm run generate:core-api-schema`) on any schema change or the BH-686 CI
  gate fails. Prod: PR `staging`→`main` + a full release.
- **webapp** → merge to `staging` → Amplify auto-deploys. Prod: `main`.

## Status (2026-07-05)

- **Capture + detect + judge**: live on staging. Judge recalibrated 0.85→0.70
  (BH-956), promotion gate hardened (precision + recall floors; ECE reported not
  gated — real judge classifies 0.93/0.93 but ECE ~0.46).
- **"Your routines" persistence** (BH-975/976/977/978): merged, deployed to
  staging (platform-core `v2.9.0.65`, webapp Amplify), **verified live** — 10/10
  surface + 3/3 write-path (lifecycle · concurrency · stale-lock) green against
  the staging API.
- **Not yet in prod** — `staging`→`main` promotion pending an explicit release.
- **Open tech-debt**: BH-979 (split platform-core `typedefs.ts`, >1300 lines).

## Ticket map

| Ticket | Scope |
|---|---|
| BH-876 | Epic |
| BH-882 | DynamoDB single-table store (CDK) |
| BH-883 | DTOs, stores, capture queue, redaction |
| BH-884 | Shadow detector + judge + trust gates |
| BH-885 | Suggestion API (list/schedule/dismiss) + "Your routines" persistence |
| BH-956 | Judge recalibration + promotion-gate hardening |
| BH-960 | Intent capture wired into the supervisor |
| BH-967 | Schedule/dismiss state machine + `execute_workflow` schedule |
| BH-969/970 | Resolved action-artifact + editable recipient at schedule |
| BH-975 | `scheduledRoutinesForWorkspace` query |
| BH-976 | `unscheduleRoutine` mutation |
| BH-977 | Webapp server-derived "Your routines" |
| BH-978 | e2e surface + lifecycle + concurrency |
| BH-979 | (tech-debt) split `typedefs.ts` |
