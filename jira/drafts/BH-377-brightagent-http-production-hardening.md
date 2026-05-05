# BH-377 — BrightAgent v2: HTTP `/threads` production hardening (draft)

> **Status:** Draft for Jira creation — confirm the issue key in Jira is unused before using it; if Jira assigns a different key, rename this file and the feature branch.
>
> **Proposed Jira key:** `BH-377`  
> **Parent epic:** `BH-172` (Features) — per `agentic-project-mgmt/CLAUDE.md`  
> **Feature branch (after key confirmed):** `drchinca/BH-377/brightagent_improvements`  
> **Repo:** `brighthive/brightagent-v2`

---

## Jira fields (for create screen)

| Field | Value |
|-------|--------|
| **Summary** | BrightAgent v2: production hardening for `/threads` (auth, DAG parity, SessionStore, types) |
| **Issue type** | Story (or Task if team prefers) |
| **Parent** | BH-172 |
| **Labels** | `brightagent`, `brightagent-v2`, `backend`, `security` |
| **Component** | (match team default for API / platform) |

---

## Ticket body (paste into Jira Description)

```
📝 Description

Harden the LangGraph-compatible `/threads` HTTP surface in BrightAgent v2 so it matches production expectations: the same authentication posture as `/v1/chat`, a single code path for chat DAG outcomes (including partial/failed runs), durable thread/run state via SessionStorePort instead of an in-process dict, and stricter types at stable API boundaries.

Rationale: the current threads shim is correct for single-process dev and webapp SSE shape, but "top tier" production needs multi-instance safety, security parity, and behavioral alignment with the existing `/v1/chat` pipeline.

📍 Scope

**Include:**
- **Auth:** Apply the same `X-Api-Key` (or explicitly documented) dependency model to `/threads/*` as `POST /v1/chat` and `POST /v1/chat/stream`, OR produce a short ADR stating gateway-only auth and ensure in-app behavior matches that contract.
- **Shared DAG outcomes:** Refactor `threads` execution to reuse the same outcome path as `/v1/chat` — e.g. `_DAGOutcome`, `_parse_chat_result`, `_extract_partial_response` from `app.py` (or a shared module) so non-`COMPLETED` runs and partial orchestrator output behave consistently.
- **Persistence:** Implement and wire `SessionStorePort` (DynamoDB/Redis per platform) for thread metadata, messages, and run index; restrict the in-memory `_threads` store to dev/test or behind a setting.
- **Types:** Introduce Pydantic (or frozen dataclass) models for stable request/response fields; keep `dict` only where LangGraph SDK allows variable shape, document exceptions.

**Exclude:**
- Full HITL `__interrupt__` resume payloads (separate ticket).
- Full `runs/{id}/stream` reconnect replay buffer (separate ticket; may remain stub with explicit product sign-off).
- Per-token LLM streaming (separate ticket).

🏗️ Areas

- brightagent-v2 — `src/brightagent/interfaces/http/threads.py`, `app.py`, `contracts/session_store.py`, `platform/`, tests
- brighthive-webapp — only if auth header or base URL contract changes
- Infra — session store table/Redis (as per existing SessionStore design)

✅ Acceptance Criteria

- [ ] `/threads` routes match the chosen auth policy; no unauthenticated production deploy without written exception.
- [ ] Failed or partial DAG runs from the threads path match `/v1/chat` behavior for the same inputs (same user-visible fallbacks where applicable).
- [ ] Thread and run state for configured environments survives process restart (SessionStorePort + config).
- [ ] Contract tests and unit tests cover auth wiring, store round-trips, and message extraction.
- [ ] `docs/MIGRATION_MAP.md` row updated; `make check` green in brightagent-v2.

👥 Contact

**Stakeholders:** (fill in) @PM @Eng

🔧 Technical Notes

- **Code:** In-memory global `_threads` in `threads.py`; `verify_api_key` only on `/v1/chat` today — intentional gap to close or document.
- **Parity:** `threads._run_chat_dag` vs `app._execute_chat_dag` — consolidate to avoid behavioral drift.
- **CEMAF:** Chat path must remain `DAGExecutor` + `create_chat_dag()`; no direct agent calls from HTTP.
- **Multi-tenant:** `workspace_id` resolution from thread metadata / `session_info` must remain explicit and tested.

💼 Business Notes

- Unblocks horizontal scaling of BrightAgent v2 behind the webapp and reduces cutover risk vs brightbot.

📎 Attachments

- brightagent-v2 code review notes (threads + app.py).
- Link to spec when written (`docs/specs/`).

🔗 Related Issues

- Parent: BH-172 (Features Epic)
- Relates to: BrightAgent v2 migration / MIGRATION_MAP rows for HTTP and session
```

---

## Cross-repo reference

- **Platform architecture context:** `platform-saas-ai-context/docs/architecture/PRODUCTION_AI_ARCHITECTURE.md` (and related Bedrock/CEMAF docs).
- **Ticketing format source:** `agentic-project-mgmt/jira/TICKET_TEMPLATE.md`
