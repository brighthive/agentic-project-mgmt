# BH-1255 Trial Spec Family — Ticket List

39 tickets under epic **BH-1255**, all `Needs Refinement`. ⚠️ = gated on named confirmation before work starts.

## 🏗️ Pipeline run lifecycle — foundation (BH-1256→1264)

| Key | Repo | Summary |
|---|---|---|
| BH-1256 | brightbot | PipelineRunner port + DbtCloudRunner adapter + registry |
| BH-1257 | brightbot | `path_between(A,B)` lineage segment resolution |
| BH-1258 | platform-core | `runPipelineSegment` mutation + `lineageNodesTouched` on WorkflowRun |
| BH-1259 | platform-core | terminal-run immutability guard on WorkflowRun |
| BH-1260 | platform-core | `reRunFromNode` mutation + capability-gated resume |
| BH-1261 | brightbot | `schedule_pipeline_run` chat tool — schedule + alert rules |
| BH-1262 | webapp | re-run-from-node affordance on RunTimeline |
| BH-1263 | platform-core | finish `DbtAdapter.checkStatus` poll (unblock async segment runs) |
| BH-1264 | e2e | chat → routine → scheduled segment run → Slack/inbox alert |

## 📄 SSIS/SSRS proactive source — crit 5 & 6 (BH-1274→1277)

| Key | Repo | Summary |
|---|---|---|
| BH-1274 ⚠️ | brightbot | populate `services.ssis_packages` for Loop Capital + verify on staging (secret-write — needs named confirmation) |
| BH-1275 | brightbot | `SsrsCatalogPipelineSource` — .rdl proactive source |
| BH-1276 | brightbot | real-behavior L2 vs LC sandbox .dtsx/.rdl fixtures |
| BH-1277 | e2e | new SSIS/SSRS finding reaches notification surface |

## 🩺 SQL Server health-watch — crit 4 (BH-1278→1282)

| Key | Repo | Summary |
|---|---|---|
| BH-1278 | brightbot | extend GC-15 coverage to failed Agent job + healthy-no-signal |
| BH-1279 | brightbot | emit `sql_server_health` OTel span + log events (§9) |
| BH-1280 | brightbot | per-workspace watchdog schedule + surface critical signals |
| BH-1281 | brightbot | provision read-only BYOW login w/ VIEW SERVER STATE (GAP #1) |
| BH-1282 | brightbot | unit L2 for threshold/never-drop/no-secret invariants |

## ✅ Data quality rules — crit 7 axis-3 (BH-1283→1287)

| Key | Repo | Summary |
|---|---|---|
| BH-1283 | platform-core | `rulesInScope(tag\|groupId)` resolver |
| BH-1284 | brightbot | `AssetRuleSelector` port + registry + OGM adapter |
| BH-1285 | brightbot | `QualityRulePipelineSource` + bridge + routing |
| BH-1286 | brightbot | real-behavior L2 quality-rule eval |
| BH-1287 | e2e | scheduled tag-scoped rule failure reaches quality surface |

## 🤝 BrightRoutine approve→schedule — crit 9 & 8 (BH-1288→1293)

| Key | Repo | Summary |
|---|---|---|
| BH-1288 | brightbot | `RoutineApprovalGate` port + registry + Slack adapter |
| BH-1289 | brightbot | register `routine_approval` graph; OFFERED→SCHEDULING→SCHEDULED |
| BH-1290 | brightbot | build `ScheduleRoutineRequest`, call `create_schedule`, record approver |
| BH-1291 | platform-core | expose approver + SCHEDULED transition (audit, crit 8) |
| BH-1292 | brightbot | L0/L1/L2 approval-gate suites incl. real `create_schedule` |
| BH-1293 | e2e | chat → OFFERED → Slack approve → schedule fires |

## 🏅 Data-product tier surfacing (BH-1294→1300)

| Key | Repo | Summary |
|---|---|---|
| BH-1294 | platform-core | additive `CreatedFinalProduct.pipelineTier` |
| BH-1295 | webapp | tier badge column on Created Data Products grid |
| BH-1296 | webapp | Gold/Platinum client-side tier filter |
| BH-1297 | webapp | top-level "Data Products" sidebar entry |
| BH-1298 | brightbot | attach `data_product` + `pipeline_tier` to watchdog payload |
| BH-1299 | slack | tier badge + data-product grouping in card renderer |
| BH-1300 | e2e | Gold product shows tier badge; no-lineage → UNKNOWN |

## 🔌 Pipeline artifact parser registry (BH-1301→1303)

| Key | Repo | Summary |
|---|---|---|
| BH-1301 | brightbot | `PipelineArtifactParser` port + registry; dtsx/rdl behind adapters |
| BH-1302 | brightbot | golden L2 — registry == direct calls on real fixtures |
| BH-1303 | e2e | .dtsx diagnostics via registry; unsupported ext fails loudly |

## Repo load

| Repo | Ticket count |
|---|---|
| brightbot | 18 |
| platform-core | 7 |
| e2e | 7 |
| webapp | 4 |
| slack | 1 |

**One gate:** BH-1274 (workspace-secret write) needs explicit named confirmation before work starts. All others are pick-up-and-go.
