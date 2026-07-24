# Slack-Server Notification Pipeline — Env Parity & Operational Learnings

> Last updated: 2026-07-24
> Scope: `brightbot-slack-server` notification pipeline env vars across staging ↔ prod, plus
> the operational traps found while bringing prod to parity (BH-1131).
> Companion to [`ENVIRONMENTS.md`](./ENVIRONMENTS.md) (the account/URL matrix) and
> [`../langsmith-vault/README.md`](../langsmith-vault/README.md) (deployment secret shape + PATCH rules).

---

## TL;DR

The slack-server notification pipeline needs **three** env settings to actually push notifications
to Slack. Two are plain GitHub Actions **variables**; one is a **shared secret** that must match on
both the sender (slack-server) and the receiver (the brightbot LangGraph deployment). Prod was
missing all three at various points; a var flip alone does nothing until the service is **redeployed**
(the value is baked into the ECS task-def at deploy time).

---

## The pipeline (why each var exists)

```
EventBridge / on-demand signal
        │
        ▼
 brightbot (LangGraph Cloud)  ──POST /graphql──▶  platform-core notifications API
        │                                              (NOTIFICATIONS_API_URL)
        ▼
 slack-server poller  ──polls every 5s──▶  posts to Slack
   (NOTIFICATIONS_POLLER_ENABLED)
        │
        ▼
 user clicks "mute" in Slack
        │
        ▼
 slack-server ──POST /manage/chat-sessions/{threadId}/mute──▶ brightbot
   (header x-chat-notify-mute-secret == CHAT_NOTIFY_MUTE_SECRET, must match both ends)
```

---

## The three settings

| Setting | Type | GH scope | Prod value | Purpose | Silent-fail mode if missing |
|---|---|---|---|---|---|
| `NOTIFICATIONS_POLLER_ENABLED` | **variable** | `production` env | `true` | Starts the 5s poll loop that drains queued notifications to Slack | `!== "false"` → any non-`true`/unset still starts, but was explicitly `false` → poller disabled, logs `[notifications] poller disabled` |
| `NOTIFICATIONS_API_URL` | **variable** | `production` env | `https://api.app.brighthive.net` | Base URL the poller GETs notifications from (poller appends `/graphql` itself) | `poller.ts:520`: `if (!NOTIFICATIONS_API_URL \|\| !NOTIFICATIONS_API_KEY) return true;` — marks event **handled** (no retry) but never pushes. Poller looks alive; nothing reaches Slack. |
| `CHAT_NOTIFY_MUTE_SECRET` | **secret** | `production` env + brightbot `brightagent-prod` LangGraph deployment | *(shared secret — see below)* | Authenticates the slack-server → brightbot mute callback | Sender-only or receiver-only → mute action returns `not_configured` or 401; **both ends or neither** |

### Why "both ends or neither" for the mute secret

`CHAT_NOTIFY_MUTE_SECRET` is a **static shared header secret**, set once platform-wide:

- **Sender** (slack-server): `src/notifications/chat-notify-mute-action.ts` reads it, sends header
  `x-chat-notify-mute-secret`. Empty → returns `{ok:false, reason:"not_configured"}` (no-op).
- **Receiver** (brightbot): `routes/chat_session_notify_routes.py:478`
  `expected_secret = os.getenv("CHAT_NOTIFY_MUTE_SECRET", "")` on `POST /{thread_id}/mute`.

Setting **one side only** is the exact shape of the 2026-07-13 incident (a secret set on one system
without its counterpart). Set both, same value, in the same change — or set neither.

---

## Operational learnings (the traps)

### 1. Env vars are baked into the task-def at deploy time — a var flip does NOT restart anything

Flipping a GitHub Actions variable/secret changes what the **next** deploy bakes into the ECS
task-def `environment` block. The **running** container keeps its old value until a redeploy.
To pick up a var change without a code commit:

```bash
gh workflow run deploy.yml --ref main -f reason="pick up NOTIFICATIONS_* var change"
```

`workflow_dispatch` deploys `main` HEAD — no dummy commit needed. Verify the live boot log shows
`[poller] Starting — polling every 5s` (not `[notifications] poller disabled`).

### 2. `OPTIONAL_SECRET_ENV_VARS` — empty optionals are omitted, not set empty

`infrastructure/index.ts` (~lines 596–625) maps optional secrets via
`pulumi.output(config.getSecret(key)).apply((v) => v ?? "")`. When empty, the var is **omitted from
the container env entirely** (the app treats absence as a no-op), rather than injected as `""`.
`NOTIFICATIONS_API_URL`, `NOTIFICATIONS_API_KEY`, `SCHEDULER_SERVICE_API_KEY`,
`CHAT_NOTIFY_MUTE_SECRET` are all in this list.

### 3. Poller "silent drop" — the functional gap when the URL is missing

With the poller **on** but `NOTIFICATIONS_API_URL` **unset**, `poller.ts:520` returns `true`
(event handled, no retry) without pushing. The poll loop looks healthy in logs; notifications
silently never arrive. This is why the URL must be set **and** a redeploy performed — enabling the
poller alone is not enough.

### 4. LangSmith deployment secrets — `PATCH` REPLACES the whole array

`PATCH /v2/deployments/{id}` replaces the **entire** `secrets` array. A partial payload wiped
staging from 74 secrets → 1 on 2026-06-18. Before adding `CHAT_NOTIFY_MUTE_SECRET` to
`brightagent-prod` (currently 56 secrets, deployment_id `8e0d70b3-cd72-446c-875b-ce27576ec29d`):

1. `GET` the full array first.
2. Confirm whether GET returns secret **values** or **names-only** — this decides whether the array
   can be safely reconstructed and re-PATCHed. (Most control planes treat secrets as write-only;
   reconstructing from a names-only GET would PATCH empty values and wipe everything.)
3. Append the new entry; assert `new_count == old_count + 1`.
4. Dry-run, validate on `brightagent-staging` first, then apply to prod, then re-snapshot.

Governed by langsmith-vault rules #1 ("Never PATCH `secrets` without first reading the full array")
and #2 ("Never modify LangSmith deployment env vars without explicit per-edit approval").

### 5. Socket Mode contention — one server per Slack app

staging + prod slack-servers both holding a Socket Mode connection to the **same** Slack app cause
Slack to route each event to a random socket — so `@BrightAgent` in prod sometimes gets answered by
`brightagent-staging`. Only one server may hold the socket per app. Durable fix: a **separate Slack
app for prod**. Interim: drain the staging socket (autoscaling floor → 0 **first**, then
`desiredCount` → 0 — a bare `desiredCount=0` bounces back up under `min=1` autoscaling).

### 6. GitHub Actions variable vs secret — which gate applies

`vars.*` (e.g. `NOTIFICATIONS_POLLER_ENABLED`, `NOTIFICATIONS_API_URL`) are **variables** —
`gh variable set --env production` is outside the secret-confirmation gate. `secrets.*` (e.g.
`CHAT_NOTIFY_MUTE_SECRET`) are **secrets** — `gh secret set` is gated: state exact name + value +
systems and get named confirmation first (workspace `CLAUDE.md` rule).

---

## Current prod state (2026-07-24)

| Setting | Prod slack-server | brightbot `brightagent-prod` |
|---|---|---|
| `NOTIFICATIONS_POLLER_ENABLED` | ✅ `true` (redeployed, boot log confirms) | n/a |
| `NOTIFICATIONS_API_URL` | ✅ `https://api.app.brighthive.net` (redeployed) | n/a |
| `CHAT_NOTIFY_MUTE_SECRET` | ✅ set + baked (task-def rev `:10`, 2026-07-24) | ✅ present (56→57, PATCHed + re-snapshot verified) |

**Full parity reached 2026-07-24.** Both ends of the mute secret set in one change with a fresh
`openssl rand -hex 32` value via the `langsmith-vault/cli/add-secret` tool (GET→append→assert
count+1→PATCH full array→re-GET verify). Prod deploy green through `verify-deploy.sh`; boot log:
`[poller] Starting`, `[notifications] SSE endpoint active`, Socket Mode owned, no `not_configured`.

> **Hardening follow-up**: `CHAT_NOTIFY_MUTE_SECRET` (and `NOTIFICATIONS_API_KEY`) land in the ECS
> task-def **plaintext `environment` block**, not the `secrets` block. Move both to `secrets`
> (Secrets Manager–backed) in a future infra PR — separate ticket, not a regression.

---

## Related

- [`ENVIRONMENTS.md`](./ENVIRONMENTS.md) — account IDs, URLs, workspace UUIDs, deploy model.
- [`../langsmith-vault/README.md`](../langsmith-vault/README.md) — deployment secret shape + PATCH-replace rules.
- `brightbot-slack-server` memory: `project_slack_server_deploy_safety_hardening`, `project_notification_severity_gaps`.
