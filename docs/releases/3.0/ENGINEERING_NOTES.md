# Brighthive 3.0 — Engineering Release Notes

> **Status: DRAFT — release is gated, not shipped.** See "Go/No-Go" below before treating anything here as final.

**Window covered**: Sprint 13 (2026-06-23 → 2026-07-20) plus verification work done 2026-07-21.
**Scope**: 5 app repos — `brightbot`, `brighthive-platform-core`, `brighthive-webapp`, `brightbot-slack-server`, `brighthive-admin`.

---

## 1. Versioning

All 5 app repos are bumped to major version **3** as a synchronized platform release label. Each repo keeps its own independent semver (`3.0.0`) and its own `vX.Y.Z.W-pre-release` tag deploy mechanism — unchanged. Source of truth: [`docs/RELEASE_MANIFEST.json`](../../RELEASE_MANIFEST.json).

| Repo | Version | PR | Status |
|---|---|---|---|
| brightbot | 0.1.0 → 3.0.0 | [#910](https://github.com/brighthive/brightbot/pull/910) | Draft, not merged |
| brighthive-platform-core | 0.1.0 → 3.0.0 | [#1120](https://github.com/brighthive/brighthive-platform-core/pull/1120) | Draft, not merged |
| brighthive-webapp | 0.1.0 → 3.0.0 | [#1353](https://github.com/brighthive/brighthive-webapp/pull/1353) | Draft, not merged |
| brightbot-slack-server | 1.0.0 → 3.0.0 | [#157](https://github.com/brighthive/brightbot-slack-server/pull/157) | Draft, not merged |
| brighthive-admin | none (setuptools_scm, no git tags exist) | — | Gap — needs a `v3.0.0` tag cut, tracked in BH-1144 |

## 2. Sprint 13 delivery stats

```
┌─────────────────────────────────────────────────────────────┐
│  446 tickets touched (BH-737 → BH-1137)                     │
│  141 Done (31.6%) — understates delivery, see note below    │
│  499 feature/fix PRs + 80 staging-release-carrier PRs       │
│  +355,423 / −91,481 lines, 6 repos touched                   │
│  Only 13/446 tickets carry story points                     │
└─────────────────────────────────────────────────────────────┘
```

**Ticket-status caveat (systemic, 3rd sprint running)**: 235 tickets sit in "Needs Refinement" despite merged PRs — ticket transitions lag real code. This was proven concretely three separate times during this release's readiness check (below) — treat Jira status as a lead, not a fact, until BH-1140–1145 close the CI gap that would catch this automatically.

## 3. Go/No-Go — what's actually blocking `main`

Three security/quality fixes were verified **present on `develop`/`staging` but absent from `main`** during this release's readiness audit. Each was independently confirmed by reading the real diff against `origin/main`, not by trusting ticket status:

| Fix | Ticket | Evidence | PR to `main` |
|---|---|---|---|
| PII masking on dbt sample-row endpoints (`load-table-schema`, `load-table-schema-full`), the `preview_transformation_sample` chat tool, and the description-generation agent — all three had **zero** masking calls on `main` | BH-1078 (P0) | `git show origin/main:routes/dbt_routes.py \| grep enforce_pii_masking` → no hits, confirmed 2026-07-21 | [brightbot#912](https://github.com/brighthive/brightbot/pull/912) — hand-ported (couldn't cherry-pick, `main`/`develop` have diverged file structure), 22/22 tests pass, CI green, **ready for review, awaiting human approval** |
| Analyst checks data exists before disambiguating (was disambiguating first, then discovering there's no data) | BH-776 | `brightbot/agents/retrieval_agent/data_presence.py` exists on `develop`, absent on `main` (PR #737, merged 2026-06-25) | Not yet opened — needs the same hand-port treatment as BH-1078 |
| Fast-path short-circuit + KB relevance floor fixing >90s "no data" grind | BH-777 | Same PR #737 — `_KB_MIN_RELEVANCE_SCORE` filter in `brightbot/tools/aws/knowledge_base.py`, absent on `main` | Not yet opened |

**No release should be called "shipped" until all three are merged to `main` and re-verified against `main`'s actual HEAD** — not against `develop`, not against ticket status.

## 4. CI/CD gate audit — tracked, not yet fixed

None of the 5 app repos has a real staging→main promote gate (unit + integration + e2e + env-var health) today. Filed under epic BH-170:

| Repo | Gap | Ticket |
|---|---|---|
| brightbot | Unit-test CI step disabled (`if: false`) | BH-1140 |
| brighthive-platform-core | No integration/e2e gate; env-var Zod schema never validated in CI | BH-1141 |
| brighthive-webapp | `deploy.yml` job named "test" runs zero tests | BH-1142 |
| brightbot-slack-server | No test step before deploy (has the best env-health check of all 5 — `validate-deploy-config.mjs` — worth copying elsewhere) | BH-1143 |
| brighthive-admin | Zero CI, no `.github/workflows` at all | BH-1144 |
| brighthive-e2e | Has a real `--gate` mode, wired to zero repos | BH-1145 |

**This is why the three fixes above sat on `develop` for up to 4 weeks without anyone noticing they hadn't reached `main`** — there's no automated check that would have flagged the drift.

## 5. Secrets — prod promote checklist, complete

4 secrets required for BrightSignals notifications + BrightRoutines scheduler were missing from `prod/platform/platform-core` and/or their GitHub/LangGraph targets. All copied verbatim from staging (no new values generated), verified via sha256-prefix match, snapshotted per the existing vault protocol:

| Secret | Targets | Status |
|---|---|---|
| `NOTIFICATIONS_API_KEY` | AWS prod + GitHub (slack-server) | ✅ Done, verified |
| `SLACK_CONNECT_INTERNAL_SECRET` | AWS prod + GitHub (slack-server) | ✅ Done, verified |
| `SCHEDULER_SERVICE_API_KEY` | AWS prod + GitHub + LangGraph Cloud (`brightagent-prod`) | ✅ Done, verified |
| `SCHEDULER_WEBHOOK_SECRET` | AWS prod + LangGraph Cloud | ✅ Done, verified |

Full audit trail: `aws-secrets-vault/snapshots/2026-07-21_prod-*` (4 folders) + `langsmith-vault/data/prod/brightagent-prod.json` (pre/post-change snapshots committed).

**Known gap (not yet fixed)**: `platform-core`'s `env-vars.ts` zod schema declares only 1 of these 4 as required; `brightbot` has no required-secrets manifest at all. Both read via bare `process.env`/`os.environ.get`. A missing prod secret fails silently at runtime, not at deploy time.

## 6. Schema/DB change risk — Virginia & Indiana clients

Investigated whether the volume of Sprint 13 GraphQL/schema changes (~50 commits) risked breaking existing client data for Indiana Tech (Jenzabar) or the Virginia Workforce Data Trust (14-agency consortium). **Verdict: LOW risk** — changes were almost entirely additive; two changes that looked like breaking removals were checked and found safe (consumers already migrated in lockstep). No Neo4j OGM/data migration scripts ran against existing client data this window.

**Process gap flagged**: CI only checks that the committed GraphQL SDL artifact isn't stale — there's no semantic breaking-change gate. Added a manual review step to the cross-app deployment guide (`platform-saas-ai-context/docs/infrastructure/DEPLOYMENT_GUIDE.md`) as a stopgap.

## 7. Brand casing correction

`Brighthive` (lowercase h) is now the canonical spelling globally, replacing `BrightHive`. Updated `~/.claude/rules/naming.md`, the workspace root `CLAUDE.md`, and the live Sprint 13 Slack post. Historical ticket text and already-shipped-feature descriptions referencing the old casing were left as-is (they're records of real ticket text, not new prose).

## 8. Recommendations before calling this a release

1. **Get PR #912 (BH-1078) reviewed and merged** — this is the release's actual blocker.
2. **Open and merge equivalent hand-ports for BH-776/BH-777** — same divergence problem as #912, same fix pattern.
3. **Re-verify all three against `main`'s HEAD after merge**, not against `develop`.
4. **Prioritize BH-1145** (e2e gate wiring) — the single highest-leverage CI fix; would have caught the develop→main drift automatically.
5. **Run the 235-ticket Needs-Refinement transition sweep** before trusting any future "% complete" number.
6. **Cut a `v3.0.0` tag on `brighthive-admin`** to close the versioning gap (BH-1144).
