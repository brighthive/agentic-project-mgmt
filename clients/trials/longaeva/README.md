---
client: longaeva
trial-day-1: 2026-06-15
last-reviewed: 2026-06-08
---

# Longaeva — Trial Folder Index

> **Read me first if you're new to the Longaeva trial.** This is a directory map. Every artifact lives somewhere; this doc tells you which one to open for which question.

## Status at a glance

- **Trial Day 1**: 2026-06-15 (7 days out as of 2026-06-08)
- **Stage**: pre-trial-locked-cycle-7 (per `BRIGHTHIVE_GAPS.md`)
- **Composite ≥10-of-14 GCs demoed convincingly**: ~70%
- **GC-6 platform layer**: ✅ end-to-end verified — `make verify-pristine` opens a real GitHub PR in ~30s
- **Outstanding for Day 1**: humans-only items (staging deploy, BH-533 connectivity, demo storyboard with Grant, LONGAEVA_AGENT_ROLE runtime)

## Read in this order

If you've never seen this trial before:

1. **[`overview.md`](./overview.md)** — what we're selling, who Longaeva is, the 14-day POC structure
2. **[`scorecard.md`](./scorecard.md)** — 17 success criteria + daily-notes template + status entries
3. **[`SESSION-HANDOFF-2026-06-08.md`](./SESSION-HANDOFF-2026-06-08.md)** — pre-cron baseline (24-PR merge train, GC harness verdict, §10 sign-off cheat sheet)
4. **[`BRIGHTHIVE_GAPS.md`](./BRIGHTHIVE_GAPS.md)** — gap-by-gap analysis with `amended:` audit log of every shipped change
5. **[`OPERATOR-RUNBOOK-DAY-1.md`](./OPERATOR-RUNBOOK-DAY-1.md)** — pre-flight checklist + 4-mutation live demo script + 7 named recovery paths

## Demoing GC-6 cold

If you have a laptop and a customer in 30 minutes:

```bash
cd ~/iccha/brighthive/brighthive-platform-core
NAME=<your-name> make verify-pristine
```

That single command:
1. Brings up `neo4j + redis + localstack` via docker-compose
2. Pre-creates the Secrets Manager / S3 fixtures LocalStack needs
3. Seeds Neo4j with two workspaces, three users, and the canonical DataAssets
4. Materializes `.env` from your vault
5. Starts platform-core on `:4040`
6. Runs the 5-step dry-run script: auth → binding → upsertSemanticView → (optional) Snowflake validation → commitSemanticViewToGitHub
7. Opens a real GitHub PR against `brighthive/longaeva-semantic-views` and cleans up after itself

Then walk through `OPERATOR-RUNBOOK-DAY-1.md` §"Live demo script" with the customer watching.

## Folder map

| File | Purpose | Update cadence |
|---|---|---|
| `README.md` | This index | When new docs land in the folder |
| `overview.md` | One-page client briefing (sales-tilted) | Pre-trial only |
| `scorecard.md` | 17 success criteria + daily-notes + per-day status | Daily during trial |
| `BRIGHTHIVE_GAPS.md` | Gap-by-gap analysis with `amended:` audit log | After every meaningful shipping cycle |
| `SESSION-HANDOFF-2026-06-08.md` | Pre-cron baseline frozen for posterity | Never (frozen) |
| `OPERATOR-RUNBOOK-DAY-1.md` | Day-1 demo runbook (pre-flight + live script) | When the demo flow materially changes |
| `TRACKER.md` | Auto-generated live tracker (`make longaeva-tracker`) | Auto, daily |
| `TEAM_GUIDE.md` | How the BH team coordinates during the trial | Pre-trial only |
| `poc.yaml` | Machine-readable trial spec | Pre-trial only |
| `artifacts/` | Customer-supplied + BH-supplied PoC inputs | As received |
| `notion/` | Local copies of canonical Notion pages | Per session-handoff |
| `sandbox/` | The 11/11 PoC validator + fidelity tracker (locally vendored) | Updated when sandbox changes |
| `integration/` | Live integration logs (Snowflake / dbt / Dagster verifications) | When new integration runs |

## Code artifacts (cross-repo references)

| Artifact | Repo | Path / PR | Purpose |
|---|---|---|---|
| Spec — Semantic View → GitHub | brighthive-platform-core | [pc#798](https://github.com/brighthive/brighthive-platform-core/pull/798) (open draft) | Single source of truth for the GC-6 author→PR loop |
| `WorkspaceGitHubBinding` + CRUD | brighthive-platform-core | pc#799 (BH-613) ✅ | Per-workspace GitHub repo + PAT routing |
| `commitSemanticViewToGitHub` orchestrator | brighthive-platform-core | pc#800 (BH-614) ✅ | 9-step pipeline that opens the real PR |
| 20 deterministic eval tests | brighthive-platform-core | pc#801 (BH-618) ✅ | Properties 1-4 + 5 §2.7 evals |
| LocalStack in compose | brighthive-platform-core | pc#802 (BH-611) ✅ | Local stack actually round-trips Secrets Manager |
| Token-redaction regex extension | brighthive-platform-core | pc#803 (audit-debt #11) ✅ | `ghu_*` + `?access_token=` no longer leak |
| `make verify` / `make verify-pristine` | brighthive-platform-core | pc#804 ✅ | One-command pre-flight |
| CI workflow for the eval harness | brighthive-platform-core | pc#805 ✅ | Locks the 70-test contract on every PR |
| Auth role hierarchy fix (BH-612) | brighthive-platform-core | pc#797 ✅ | Workspace admin satisfies any required-role directive |
| GHE proxy selection-set drift | brighthive/brightbot | bb#520 (audit-debt #10) ✅ | dbt-agent gets typed `errorCode` + `httpStatus` |
| `provision_semantic_views_repo.sh` | brighthive/brighthive-scripts | brighthive-scripts#3 (BH-617) ✅ | One-command per-customer onboarding |
| `trial_day_1_dry_run.sh` | brighthive/brighthive-scripts | brighthive-scripts#4 ✅ | 5-step demo smoke |

## Day-1 critical path

What's left on the human side before the demo:

1. **Staging deploy** of pc#797..805 + bb#520 (auto-flips GC-10 S6/S7, unblocks GC-9 MCP downstream)
2. **BH-533 connectivity validation** post-deploy
3. **Demo storyboard scope decision with Grant** (single-table vs schema-wide GC-6 framing)
4. **Customer creds handover** (GHE host URL + PAT, MCP creds, customer Okta tenant)
5. **`LONGAEVA_AGENT_ROLE` runtime** — switch agents from KURICHINCA admin to read-only role per GC-14 sandbox parity

Sprint-sized deferrals (intentionally NOT touched by the cron loop):

- `bb#489` multi-table semantic view (GC-6 schema-wide)
- `generate_mart_model` impl (GC-5)
- Snowflake auto-trigger (~50 lines pc + SSM export)
- Webapp `WorkspaceSettings/GitHubBinding` panel (BH-615) and `Save & Open PR` button (BH-616)

## Glossary

- **GC** — Golden Case. One of 14 customer-promise bars from BH-601.
- **L1/L2/L3** — Layer audit findings. L1 = per-PR, L2 = cross-repo contract, L3 = end-to-end.
- **`LONGAEVA_POC`** — the live Snowflake account/database the trial runs against.
- **`workspace_secret_store/{workspace_uuid}`** — Secrets Manager prefix; pc writes, cdk reads, BB reads.
- **Property 1** — "PAT never leaves Secrets Manager." Test-locked at `tests/unit/scrub-bearer.test.ts`.
- **Property 2** — "yamlHash continuity from upsert→commit." Test-locked at `tests/unit/semantic-view/commit-orchestrator.test.ts`.

## Ownership

- **Demo driver**: Kuri (drchinca) primary, Marwan secondary
- **On-call during demo**: Ahmed (infra), Harbour (UI)
- **Customer-facing**: Grant
- **Trial epic**: [BH-526](https://brighthiveio.atlassian.net/browse/BH-526)
