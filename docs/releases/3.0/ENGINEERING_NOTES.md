# Brighthive 3.0 — Engineering Release Notes

> **Status: DRAFT — release is gated, not shipped.** See §3 before treating anything here as final.

**Window covered**: Sprint 13 (2026-06-23 → 2026-07-20).
**Scope**: 5 app repos — `brightbot`, `brighthive-platform-core`, `brighthive-webapp`, `brightbot-slack-server`, `brighthive-admin`.

---

## 1. Versioning

All 5 app repos bump to major version **3** as a synced platform release label. Each repo keeps its own independent semver (`3.0.0`) and its own `vX.Y.Z.W-pre-release` tag deploy mechanism — unchanged. Source of truth: [`docs/RELEASE_MANIFEST.json`](../../RELEASE_MANIFEST.json).

| Repo | Version | PR | Status |
|---|---|---|---|
| brightbot | 0.1.0 → 3.0.0 | [#910](https://github.com/brighthive/brightbot/pull/910) | Draft |
| brighthive-platform-core | 0.1.0 → 3.0.0 | [#1120](https://github.com/brighthive/brighthive-platform-core/pull/1120) | Draft |
| brighthive-webapp | 0.1.0 → 3.0.0 | [#1353](https://github.com/brighthive/brighthive-webapp/pull/1353) | Draft |
| brightbot-slack-server | 1.0.0 → 3.0.0 | [#157](https://github.com/brighthive/brightbot-slack-server/pull/157) | Draft |
| brighthive-admin | none (no git tags) | — | Needs a `v3.0.0` tag — BH-1144 |

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

235 tickets sit in "Needs Refinement" despite merged PRs — ticket status lags real code, 3rd sprint running. Treat Jira status as a lead, not a fact, until BH-1140–1145 close the CI gap.

## 3. Blocking `main`

Three fixes are live on `develop`/`staging` and missing from `main`:

| Fix | Ticket | Fix location | Action |
|---|---|---|---|
| PII masking on dbt sample-row endpoints, the preview tool, and the description agent | BH-1078 (P0) | [brightbot#912](https://github.com/brighthive/brightbot/pull/912) | Ready for review, CI green — needs approval + merge |
| Analyst checks data exists before disambiguating | BH-776 | `develop` (PR #737) | Needs a PR to `main` |
| Fast-path for "no data" answers + KB relevance floor | BH-777 | `develop` (PR #737) | Needs a PR to `main` |

None of these three can be called shipped until they're merged to `main`.

## 4. CI/CD gates — open work, tracked under BH-170

No app repo has a staging→main promote gate (unit + integration + e2e + env-var health) today.

| Repo | Gap | Ticket |
|---|---|---|
| brightbot | Unit-test CI step disabled | BH-1140 |
| brighthive-platform-core | No integration/e2e gate; env vars unvalidated in CI | BH-1141 |
| brighthive-webapp | `deploy.yml`'s "test" job runs no tests | BH-1142 |
| brightbot-slack-server | No test step before deploy (its env-health check is the best of the five — worth copying elsewhere) | BH-1143 |
| brighthive-admin | No CI at all | BH-1144 |
| brighthive-e2e | `--gate` mode exists, wired to nothing | BH-1145 |

BH-1145 is the highest-leverage fix — it would catch drift like §3 automatically.

## 5. Secrets — prod checklist complete

4 secrets required for BrightSignals + BrightRoutines are now live in prod, copied from staging and verified:

✅ `NOTIFICATIONS_API_KEY` · ✅ `SLACK_CONNECT_INTERNAL_SECRET` · ✅ `SCHEDULER_SERVICE_API_KEY` · ✅ `SCHEDULER_WEBHOOK_SECRET`

Audit trail: `aws-secrets-vault/snapshots/2026-07-21_prod-*` + `langsmith-vault/data/prod/brightagent-prod.json`.

Open gap: `platform-core`'s env schema declares only 1 of these 4 as required; `brightbot` has no required-secrets manifest. A missing prod secret fails at runtime, not at deploy time.

## 6. Schema risk — Virginia & Indiana

~50 schema-touching commits this sprint. Risk to these two live clients: **low** — changes are additive, no data-migration scripts ran against their data. CI still can't catch a semantic breaking change on its own (only checks SDL staleness); added a manual review step to the deployment guide as a stopgap.

## 7. Brand casing

`Brighthive` (lowercase h) is now the canonical spelling. Updated the naming rule, workspace root `CLAUDE.md`, and the Sprint 13 Slack post.

## 8. Shipped this cycle, not release-relevant

- Upload modal click-to-browse
- Update/Edit and Add/Create label consistency
- Green-background button contrast
- Delete confirmations for projects and schemas
- Password show/hide toggle on login
- Projects Grid/Table view parity
- Stale beta/preview tags removed

## 9. Built, hidden from nav

- **Analytics Dashboard** — wired to real data, hidden pending further work
- **Access Control & Usage/Audit pages** (Govern) — hidden pending further work
- **Monitoring Agents / pipeline watchdog** — in Staging QC, not rolled out

## 10. Separately tracked, not blockers

PII-masking hardening beyond BH-1078, Longaeva grounding/disambiguation, and Semantic View lifecycle bugs — in progress, unrelated to this release.

## 11. Before calling this a release

1. Merge [PR #912](https://github.com/brighthive/brightbot/pull/912) (BH-1078).
2. Open and merge BH-776/BH-777 to `main`.
3. Re-verify all three against `main`'s HEAD.
4. Prioritize BH-1145.
5. Run the 235-ticket Needs-Refinement sweep.
6. Cut `v3.0.0` on `brighthive-admin` (BH-1144).
