# Draft for Ahmed — OMD native ingestion / AutoPilot contract + the empty-catalog bug

> Ready to send (Slack DM or #engineering). Context: confirming the new OM 1.8.9 path and a likely root cause for OneTen's empty Snowflake catalog. It's your layer, so confirming before anyone touches `v2.ts`.

---

Ahmed — confirmed your point: the new OMD path (OM 1.8.9 native Airflow ingestion + AutoPilot, the enhanced webhook, MCP) is warehouse-agnostic and the old `*_ingestion_lambda` scanner is the deprecated pattern. I shelved a plan I had to generalize that lambda — wrong layer, thanks for the steer. I also wrote a LIVE-vs-DEPRECATED OMD inventory into the saas architecture doc (PR #12) so we stop confusing the two webhooks — flag if I got any of it wrong:

- **Live control plane**: `v2.ts::upsertDatabaseService` registers the DatabaseService + triggers native **AutoPilotApplication**.
- **Live table-sync webhook**: `openmetadata_webhook_lambda` (gateway `POST /openmetadata/webhook`, `warehouse_adapter` → DataAssetNodes).
- **Live enrichment webhook**: `new_openmetadata_webhook_lambda` / EnhancedOmWebhookLambda (Function URL → description/embedding/quality/profiler).
- **Deprecated scanners**: `openmetadata_ingestion_lambda` (0.12.2, can't talk to 1.8.9) + `snowflake_ingestion_lambda` (superseded, never wired live).

**Likely why OneTen's catalog is still empty** — a real bug in `v2.ts`, not a warehouse issue:

`platform-core src/data-source/openmetadata/v2.ts`, in `upsertDatabaseService`:
1. **AutoPilot trigger never fires** (line ~212): `"${apiUrl}/apps/trigger/AutoPilotApplication"` — double-quoted, so `${apiUrl}` is sent as a **literal** string, and the var is `apiURL` (capital URL) anyway. The two `databaseServices` POSTs just above (lines 177/194) correctly use backticks + `apiURL`. → the native scan is never triggered.
2. **Snowflake connection fields dropped** (interface lines 13-25 + body 180-205): both PUT/POST hardcode `config: { hostPort, username, password, database, sslMode }` — discarding `account/warehouse/role` that the caller (`warehouse-service.ts`) correctly built for Snowflake. → a Snowflake DatabaseService registers with `hostPort: undefined` and can't connect.

Either alone → empty catalog. Both are on production/staging/develop since the file was created (Aug 2025).

**Three things I want to confirm before touching it:**
1. Is `v2.upsertDatabaseService` → AutoPilot the intended way the native scan kicks off, or does something else (Airflow DAG / scheduled pipeline / MCP) trigger it in your setup?
2. **The exact OM 1.8.9 AutoPilot trigger contract** — is it `POST {apiURL}/apps/trigger/AutoPilotApplication` with body `{ entityLink: "<#E::databaseService::{name}>" }`, or no-body, or a `triggerConfig` payload? (The only in-repo reference is the broken line, so I have no ground truth.)
3. The two webhooks — did I get the sync-vs-enrich split right, and which one owns the OM event subscription?

If you confirm 1+2, I'll put up the one-file fix (both bugs + a unit test) under BH-526 and verify it against staging — or it's yours if you'd rather own it. Either way I won't change `v2.ts` until you weigh in.

---

## UPDATE 2026-06-15 — root-caused the empty-embeddings gap (live staging dig)

The catalog isn't actually empty (OneTen has 23 OM tables w/ descriptions). The real gap is **embeddings**: only 46/277 Neo4j `DataAssetNode`s are embedded, and the embedded ones all belong to **one workspace** (`1c7cb12e-6d1a-4922-98a8-cff4de70f24d`).

**Root cause (verified in CloudWatch + OM subscriptions):** the OM event-subscription `OpenMetadata_alert_5sqp51K8O` sends a **hardcoded static header `workspace_uuid: 1c7cb12e…`** on EVERY webhook call, for every workspace's tables. The enhanced webhook (`new_openmetadata_webhook_lambda`) routes on that header → calls `syncDataAssets(workspaceId=1c7cb12e…, filterByOmdTableIds=[<other-workspace-table>])` → `getAllDataAssets` queries the WRONG tenant's OM creds → no match → `syncedAssetIds` empty → embedding/description/quality all skipped (`if neo4j_asset_ids:`). So only `1c7cb12e`'s tables ever embed; OneTen + DemoEnv (182 assets) + everyone else stay unembedded → invisible to retrieval.

**Why I didn't just fix it:** the obvious fix (derive workspace from the event entity's `service.name`) works for Snowflake (`<uuid>_snowflake_ingestion`) but **breaks Redshift** — that service is named `"Staging Demo Workspace"` (human name, no uuid). Naming is inconsistent across warehouses, so there's no single reliable parse. **Design question for you:** how should the webhook derive the correct workspace per-event across all warehouse naming schemes? Options: (a) make each workspace's OM subscription carry ITS OWN `workspace_uuid` header (one subscription per workspace, not one global), (b) tag OM DatabaseServices with the workspace uuid and read it off the entity, (c) a service-name→workspace lookup table. Your call — it's the OM-subscription/webhook-routing layer.

---

## UPDATE 2026-06-15 (#843 deployed) — the static-header subscription fix, fully scoped

#843 (v2.ts AutoPilot interpolation + Snowflake connection forwarding) is **merged + deployed to staging** (v2.9.0.17, CFN UPDATE_COMPLETE, post-deploy integrity clean). The duplicate-DataAssetNode "bug" turned out NOT to be a warehouse-sync defect (55/89 dupes are S3-upload/legacy with NULL omd_id; sync dedup works; 1 excess was my own replay).

**The ONE real remaining bug = the static-header subscription.** OM event-subscription `OpenMetadata_alert_5sqp51K8O` sends a hardcoded `workspace_uuid: 1c7cb12e` on EVERY webhook call → the enhanced webhook (`new_openmetadata_webhook_lambda` `get_workspace_id_from_headers`) routes every workspace's scanned tables to `1c7cb12e` → sync finds nothing for other workspaces → no embedding. Only auto-works for `1c7cb12e`; every other BYOW needs manual intervention (what I did for OneTen: fix its secret + replay).

**Recommended fix (Option B — verified feasible, warehouse-agnostic, no OM renames):** derive workspace in the webhook from the event's `entity.service.name` via a reverse lookup, NOT the header. Confirmed in Neo4j that `(WorkspaceNode)-[:USES]->(WarehouseServiceNode {name: <service.name>})` resolves the workspace for BOTH Redshift ("Demo workspace Redshift" → 1c7cb12e) and Snowflake (`<uuid>_snowflake_ingestion`). Implementation:
1. New platform GraphQL query `getWorkspaceByWarehouseServiceName(serviceName)` → returns workspace id via the USES edge (handles non-uuid Redshift names that FQN-parsing can't).
2. In `new_openmetadata_webhook_lambda` `lambda_handler`: parse `body.entity` → `service.name`, call the lookup, use that as `workspace_id`; fall back to the header only if lookup fails.
3. Keep the subscription as-is (or drop the misleading static header).

Why NOT the alternatives: FQN-parse (`<uuid>_..._ingestion`) breaks on Redshift's human-named services; per-workspace subscriptions (one alert per ws) is more OM config churn. Option B is one query + one webhook change + tests.

**Question for you:** OK to implement Option B, or do you prefer canonicalizing OM service names to `<workspace_uuid>_<provider>_ingestion` for all warehouses (Option A — cleaner long-term but renames existing Redshift services in OM)? I did NOT hot-patch the live webhook — it's your layer + a multi-tenant routing change. Ready to put up a draft PR on your nod.

---

## UPDATE 2026-06-15 (#847 verified) — Snowflake BYOW auto-routes; Redshift needs a naming decision

#847 (parse workspace uuid from OM service-name prefix) is **merged + deployed (v2.9.0.19) + UAT-verified live**: replayed a OneTen event with the wrong static header → resolver logged "resolved workspace 4d7ffd13 ... (header said 1c7cb12e)" → synced + embedded. **Snowflake BYOW now auto-routes correctly.**

**But Redshift (and any future v2.ts-registered warehouse) still won't auto-route — root cause is a known two-path naming divergence:**
- OLD `openmetadata_ingestion_lambda/config_loader.py` names services canonically: `<uuid>_redshift_ingestion`, `<uuid>_snowflake_ingestion`, etc. (This is why existing Snowflake services are uuid-named and my resolver routes them.)
- LIVE `v2.ts upsertDatabaseService` (warehouse-service.ts:182) registers with `name: warehouseService.name` — the **human name** ("Staging Demo Workspace"). The delete path (admin-resource-deletion.ts:183) has an explicit comment that this is intentional ("NOT the {workspaceId}_{suffix}_ingestion convention").
- So services registered via the live v2.ts path get human names → no uuid prefix → my resolver falls back to the header → no auto-route. The only Redshift OM service ("Staging Demo Workspace") is exactly this case (+ has no workspace USES edge).

**Completing decision (yours — it changes OM service identity + the delete path together):**
- **Option 1 (recommended):** make `v2.ts upsertDatabaseService` register with the canonical `<workspaceId>_<provider>_ingestion` name (matching the old lambda + my resolver), and update `admin-resource-deletion.ts` delete to use the same. Then ALL warehouses auto-route via the uuid prefix — no resolver change needed. One-time: existing human-named services either get re-registered or grandfathered (resolver header-fallback keeps them working).
- **Option 2:** keep human names; have the resolver ALSO do a workspace lookup keyed on something reliable (but the OGM node.name ≠ OM service name, and datapiaryServiceId is junk — so there's no clean key; this is why #845's lookup failed).

Option 1 is the clean fix. I did NOT change service naming — it's OM identity + delete-path coupling on your layer. Ready to implement Option 1 as a draft PR (warehouse-service.ts + admin-resource-deletion.ts + tests) on your nod.
