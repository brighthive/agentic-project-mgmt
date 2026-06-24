---
title: "Longaeva UAT — BrightAgent MCP exercise findings"
date: "2026-06-24"
runner: "Kuri"
mcp_endpoint: "https://brightagent-mcp.staging.brighthive.net/mcp"
workspace: "4d7ffd13-73d0-4f14-8f0e-63bfddceca7c (OneTen / Longaeva PoC)"
mcp_server_version: "brightbot-mcp 3.4.2"
purpose: "Drive each UAT prompt through the live staging MCP. Capture what works, what's stubbed, what's broken. Inputs to UAT_GUIDE corrections + Jira."
---

# MCP UAT exercise — staging — 2026-06-24

## TL;DR

- **MCP handshake green** on staging — `initialize` + bearer JWT + workspace gate all work.
- **`introspect_warehouse_schema`** returns the real warehouse: 28 tables, 3 semantic views, exact match with Snowflake. ✅
- **`qc_semantic_view_pipeline`** runs end-to-end and surfaces the real `IDENTIFIER_MAP.EFFECTIVE_TO` 100%-null finding the UAT promised. ✅
- **`get_semantic_view`** returns full Snowflake DDL for `SV_DAILY_PORTFOLIO_EXPOSURE`. ✅
- **`analyst_ask` is a stub** on staging — returns `{"status":"stub", "note":"Analyst agent invocation TODO"}`. **P0 for the MCP-from-IDE scenario** (Scenario 8). 🔴
- **`get_semantic_view_yaml`** returns `not_found` for both the SV name (`SV_DAILY_PORTFOLIO_EXPOSURE`) and the gold mart name (`MART_DAILY_PORTFOLIO_EXPOSURE`) and reports `available_tables` as ten copies of `"Not Available"`. 🔴 P1
- **`discover_data_assets`** works but returns asset rows with `"table_name":"Not Available"` and weak descriptions ("Data asset containing X information"). Discovery surface is shallow. 🟡 P2
- **`get_anomalies`** for `LONGAEVA_POC.GOLD.MART_DAILY_PORTFOLIO_EXPOSURE` returns `[]` — i.e., no stored anomalies, despite Scenario 6 promising "longitudinal monitoring live in cycle-21". 🟡 P1 (truth-in-advertising vs UAT)

## Tools exercised (and what argument names they actually want)

The MCP tool list says one thing; the validators want another. Worth fixing in tool schemas before Longaeva analysts wire Claude Desktop.

| Tool | Doc/intuitive arg | Actual required arg | Notes |
|---|---|---|---|
| `discover_data_assets` | `query` | `question` | rename in tool schema or accept both |
| `get_semantic_view_yaml` | `table` | `table_name` | also: returns `not_found` for both SV and mart names, see below |
| `qc_semantic_view_pipeline` | `table_name` | `semantic_view_name` | resolves correctly with the right name |
| `get_anomalies` | `table_name` | `dataset_fqn` (full `DB.SCHEMA.TABLE`) | docs should say FQN required |
| `analyze_dataset_structure` | `data_asset_id` | `dataset_name` + `dataset_table_name` | inconsistent with `discover_data_assets` output |
| `introspect_warehouse_schema` | `include_columns` | (no such arg accepted) | strip from any docs/examples |

→ **Filing recommendation**: one Jira (BH-?) under BH-624 (semantic view epic) titled *"BrightAgent MCP tool argument names diverge from MCP-tool description text"* with the table above as evidence.

## Per-scenario findings (against `UAT_GUIDE.md`)

### Scenario 1 — "Show me my semantic views" 🟡 (downgrade from ✅)
- **MCP behavior**: `introspect_warehouse_schema` returns 3 SVs correctly. `discover_data_assets` returns the gold mart, not the SV.
- **Gap**: there is no top-level `list_semantic_views` tool; an analyst plugged into Claude Desktop has to know to call `introspect_warehouse_schema`. The Slack `@BrightBot` path may wire this differently — **untested in this run**.
- **Fix**: add `list_semantic_views(workspace_id)` tool, or document that `introspect_warehouse_schema` is the answer.

### Scenario 2 — "Show me the YAML" 🔴 (downgrade from ✅)
- **MCP behavior**: `get_semantic_view_yaml(table_name="SV_DAILY_PORTFOLIO_EXPOSURE")` → `not_found`. Tried `MART_DAILY_PORTFOLIO_EXPOSURE` too — also `not_found`.
- **`available_tables` field** is literally `["Not Available", ...×10]` — a render bug.
- **Workaround**: `get_semantic_view(table_name="MART_DAILY_PORTFOLIO_EXPOSURE")` returns the **Snowflake DDL** (not Atlas YAML). DDL is fine for a smoke test, but it's not what Scenario 2 promises.
- **Fix**: either (a) Atlas YAML round-tripping isn't actually live on staging — update UAT to ✅ for DDL, 🔴 for Atlas YAML; or (b) fix the asset→YAML resolver so `get_semantic_view_yaml` finds the asset.

### Scenario 3 — "Open a PR with this semantic view" 🟡 (untested)
- Did not exercise `ship_semantic_view_to_github` against the real GitHub org in this run (would actually open a PR).
- Tool exists with confirm-gated semantics. Worth driving through with `confirm=false` to see the preview shape, then a real run.

### Scenario 4 — "QC this semantic view" ✅ (verified)
- `qc_semantic_view_pipeline(semantic_view_name="SV_DAILY_PORTFOLIO_EXPOSURE")` returns a clean structured report:
  - 174,384-row gold mart, freshness `2026-05-29`, null-rate per column.
  - 3 REF upstream tables introspected (FISCAL_CALENDAR, GEO_CODES, IDENTIFIER_MAP).
  - **Real flag surfaced**: `HIGH_NULL_RATE: LONGAEVA_POC.REF.IDENTIFIER_MAP.EFFECTIVE_TO null-rate 100% > 20%` — the same flag UAT promises.
- **This scenario is actually live and demoable as written.**

### Scenario 5 — "Build a dbt model from raw data" 🟡 (UAT prompt fixed)
- **Fixed**: prompt referenced `RAW.PORTFOLIO_DAILY` which doesn't exist. Replaced with `BRONZE.RAW_REST_HOLDINGS` (4,536 rows, the holdings landing table).
- MCP tool `generate_dbt_source_and_staging` exists; not driven end-to-end in this run.

### Scenario 6 — "Tell me when something breaks" 🟡 (downgrade)
- `get_anomalies(dataset_fqn="LONGAEVA_POC.GOLD.MART_DAILY_PORTFOLIO_EXPOSURE")` returns `[]`.
- UAT says cycle-21 has 4 anomaly families live in production. Either:
  - the asset hasn't been monitored yet (need a `run_longitudinal_analysis` kickoff first), or
  - monitoring is live but no anomalies have fired, or
  - it's not actually wired for this asset.
- **Action**: trigger `run_longitudinal_analysis` against the mart, wait for the EventBridge nightly, re-check `get_anomalies` next morning. If still empty, downgrade Scenario 6 to 🟡 in UAT.

### Scenario 7 — "Just chat with it like an analyst" 🔴 (downgrade from ✅)
- **`analyst_ask` is a stub**. Verbatim response: `{"status":"stub", "note":"Analyst agent invocation TODO — wire via langgraph_sdk client in follow-up."}`.
- This means the conversational path is **not** behind the MCP. It's behind the Slack server / webapp chat surface only.
- **The UAT gives the impression that an MCP tester running Claude Desktop can do scenario 7. They cannot, today.**
- **Fix**:
  1. Wire `analyst_ask` (BH-? under BH-561 or wherever the analyst-via-MCP epic lives), OR
  2. Update Scenario 7 + the Notion intro page to say "this scenario requires Slack `@BrightBot` or the BrightHive webapp — not the MCP endpoint."

### Scenario 8 — "Call BrightHive tools from my own MCP client" 🟡 (status as written holds)
- MCP endpoint live, OAuth handshake green, tool list returned (54+ tools).
- **But**: `analyst_ask` is the natural entrypoint for a Cursor/Claude Desktop user, and it's the stub. So the *practical* MCP UX is reduced to direct tool calls.
- Recommend updating the scenario to: *"Call individual BrightHive tools (e.g. `qc_semantic_view_pipeline`) from your MCP client. Conversational `analyst_ask` is wired separately and not yet live on staging."*

### Scenarios 9–13
- Not exercised against MCP in this run — they live in Slack alerts, RBAC, governance, monitoring surfaces beyond the MCP. Worth a follow-up pass.

### Scenario 14 — Non-technical UAT
- Depends on `analyst_ask` (stub on MCP, see BH-741) but should work via Slack `@BrightBot`. The S14 jargon-firewall regression test runs against the deep_agent path on MCP — caught a real leak (BH-744).
- The five prompts in `NON_TECH_UAT.md` reference real warehouse objects (`SV_DAILY_PORTFOLIO_EXPOSURE`, `SV_WEEKLY_EXPOSURE_DELTA`, `REF.WATCHLIST`) — all confirmed live in Snowflake. Issuer names in the SARAH demo are synthetic by design.

## Recommended Jira tickets (under BH-624 or BH-559 epic)

1. **`analyst_ask` is a stub on staging MCP** — wire via langgraph_sdk client. P0 for MCP-from-IDE story.
2. **`get_semantic_view_yaml` returns `not_found` for valid asset names** — and `available_tables` is `["Not Available"]×10`. P1.
3. **Tool argument names inconsistent with documentation/intuition** — see table above. P2 polish before customer hands-on.
4. **`get_anomalies` returns empty for the gold mart** — confirm whether monitoring is wired for this asset on staging; if so, why no events; if not, downgrade Scenario 6 honesty in UAT. P1.
5. **`discover_data_assets` returns thin descriptions + `table_name: "Not Available"`** — fix the asset-catalog ingest so descriptions and table_names round-trip. P2.

## Why some MCP "agents" go through a different flow

This is the architectural answer to *"why is `analyst_ask` a stub when `qc_semantic_view_pipeline` runs end-to-end?"* — it's not a bug, it's a documented exposure split. From `brightbot/mcp/capabilities.py`:

| Exposure | What it means | Examples |
|---|---|---|
| **`live`** | Direct MCP tool — synchronous JSON-RPC call, finite latency, returns a typed result. | `qc_semantic_view_pipeline`, `introspect_warehouse_schema`, `get_semantic_view`, `discover_data_assets`, `add_user_memory`, `ship_semantic_view_to_github` |
| **`routed`** | Reachable only by asking the deep_agent via `brightagent_ask` — heavy, multi-step, may run for minutes, may pause for HITL. Not a direct MCP tool because a synchronous `tools/call` can't survive the gateway timeout (BH-648 — 504 cap). | The dbt agent's full `materialize → register → PR` lifecycle; long retrieval+plan flows |
| **`preview`** | Stub registered today, real wiring tracked in BH-572. Returns `{"status":"stub"}` so MCP consumers don't crash; flips to `live` once wired. | `analyst_ask`, `brightagent_ask` |

So the "different flow" is by design: tools that fit in one synchronous call are `live`, and the conversational umbrella tools (`analyst_ask`, `brightagent_ask`) are intentionally routed/preview because they kick off multi-minute LangGraph runs that can't return inside one HTTP request. The plan in BH-572 is to wire them via the LangGraph **runs API** (submit-then-poll) so the MCP surface offers `start_run` + `poll_run` instead of one blocking `analyst_ask`.

**What this means for UAT today**:
- Direct-tool scenarios (S1, S2, S4, S8, S10, S12, S13) — exercise via MCP, gradeable today.
- Conversational scenarios (S7, S14 "Sarah") — must run via Slack `@BrightBot` or the BrightHive webapp, **not** Claude Desktop hitting the MCP. The UAT_GUIDE Slack instructions are correct; the MCP path for those scenarios will only land when BH-572 ships.

**What this means for the next UAT cycle**: when BH-572 wires `analyst_ask`, the regression test in `test_longaeva_uat_mcp.py::test_finding_analyst_ask_is_a_stub` flips green automatically and we upgrade S7 + S14 to ✅ via MCP.

## Regression suite

The whole exercise is now a pytest harness in brightbot:

```
brightbot/tests/integration/golden_cases/test_longaeva_uat_mcp.py
```

Run:
```bash
BH_MCP_URL=https://brightagent-mcp.staging.brighthive.net/mcp \
BH_MCP_AUTH_VIA_GRAPHQL=1 \
BH_MCP_WORKSPACE_ID_HEADER=4d7ffd13-73d0-4f14-8f0e-63bfddceca7c \
BH_MCP_TEST_USER=kuri@brighthive.io \
BH_MCP_TEST_PASSWORD=<from LastPass: BH Staging - Kuri> \
RUN_LIVE_MCP=1 \
uv run pytest tests/integration/golden_cases/test_longaeva_uat_mcp.py -v --no-cov
```

Last run (2026-06-24): **12 passed · 5 xfailed (documented findings) · 1 failed (S14 jargon firewall caught `deep_agent` leaking into a user-facing reply — P0 for the SARAH demo)**.

The xfails are *not* test infra bugs — they're the four findings on this page, codified so they cannot silently regress green. When BH-572 wires `analyst_ask` and BH-624 fixes `get_semantic_view_yaml`, the corresponding tests flip to live without code changes here.

## Reproducer

```bash
# 1. Fresh JWT
PWD=<from LastPass: BH Staging - Kuri>
TOKEN=$(curl -s -X POST https://api.staging.brighthive.net/ -H 'Content-Type: application/json' \
  -d "{\"operationName\":\"login\",\"variables\":{\"input\":{\"username\":\"kuri@brighthive.io\",\"password\":\"$PWD\"}},\"query\":\"mutation login(\$input: LoginInput!) { login(input: \$input) { idToken } }\"}" \
  | jq -r '.data.login.idToken')

# 2. MCP initialize → grab session id
SESSION=$(curl -sS -i 'https://brightagent-mcp.staging.brighthive.net/mcp' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'X-Workspace-Id: 4d7ffd13-73d0-4f14-8f0e-63bfddceca7c' \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}' \
  | grep -i 'mcp-session-id' | awk '{print $2}' | tr -d '\r')

# 3. tools/call (example: QC scenario)
curl -sS 'https://brightagent-mcp.staging.brighthive.net/mcp' \
  -H "Authorization: Bearer $TOKEN" -H "Mcp-Session-Id: $SESSION" \
  -H 'X-Workspace-Id: 4d7ffd13-73d0-4f14-8f0e-63bfddceca7c' \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"qc_semantic_view_pipeline","arguments":{"semantic_view_name":"SV_DAILY_PORTFOLIO_EXPOSURE"}}}'
```
