# Longaeva PoC Sandbox — Architecture

Visual map of the sandbox. Mirrors Longaeva's stack (Snowflake + dbt + Dagster +
custom MCP) so BrightHive's agents develop against a known-good target before the
trial. GitHub renders all Mermaid blocks natively.

## 1. End-to-end data flow (medallion → semantic → consumers)

```mermaid
flowchart TB
    subgraph SRC["Source systems (3 ingestion patterns)"]
        S3["S3 vendor bucket\nCSV/Parquet, daily-partitioned\ncompletion.flag"]
        REST["REST API\npaginated, 25k instrument universe"]
        SHARE["Snowflake Data Share\nread-only external DB"]
    end

    subgraph SF["Snowflake — LONGAEVA_POC"]
        direction TB
        BRONZE["BRONZE (raw landing)\nraw_market_prices · raw_rest_holdings\nraw_corporate_actions · @stages"]
        SILVER["SILVER (standardized time-series)\nstg_security_prices · stg_holdings_snapshot\nint_enriched_holdings (dbt)"]
        GOLD["GOLD (data products)\nmart_daily_portfolio_exposure\ndp_regional_exposure_daily · dp_top_issuers_daily\ndp_fiscal_quarter_exposure"]
        REF["REF (reference data)\nfiscal_calendar · identifier_map\ngeo_codes · classification_codes"]
        SEM["SEMANTIC\nsv_daily_portfolio_exposure"]
    end

    SHARESIM["LONGAEVA_VENDOR_SHARE_SIM\nvendor_security_master · vendor_ratings"]

    subgraph CONS["Downstream consumers"]
        MCP["MCP server\n(Longaeva's — stand-in: mcp_check.py)"]
        AGENT["AI agents / analysts\nstandardized time-series primitives"]
    end

    S3 --> BRONZE
    REST --> BRONZE
    SHARE --> SHARESIM
    SHARESIM -.dbt staging.-> SILVER
    BRONZE -->|dbt| SILVER
    REF -.joins.-> SILVER
    SILVER -->|dbt| GOLD
    GOLD --> SEM
    REF -.relationships.-> SEM
    SEM --> MCP --> AGENT

    classDef bronze fill:#cd7f32,color:#fff
    classDef silver fill:#9ca3af,color:#fff
    classDef gold fill:#d4af37,color:#000
    class BRONZE bronze
    class SILVER silver
    class GOLD,SEM gold
```

## 2. Semantic-view YAML deploy pipeline (Grant's flow)

The extended YAML is the canonical artifact; SDK keywords are stripped before the
Snowflake DDL call. `strip_and_emit.py` implements exactly this.

```mermaid
flowchart LR
    YAML["sv_daily_portfolio_exposure.yaml\nspec: + sdk_extensions:"]
    STRIP["strip_and_emit.py\nstrip sdk_extensions"]
    DDL["CREATE SEMANTIC VIEW\n(Snowflake-native)"]
    VIEW["LONGAEVA_POC.SEMANTIC.\nsv_daily_portfolio_exposure"]
    ROUTE["SDK routing\nMCP / REST / agent context"]

    YAML --> STRIP --> DDL --> VIEW
    YAML -. sdk_extensions .-> ROUTE
    VIEW --> ROUTE
```

## 3. Orchestration — Dagster asset graph

```mermaid
flowchart LR
    s3a["bronze_s3_market_prices"]
    resta["bronze_rest_holdings"]
    sharea["vendor_share_seeded"]
    dbtb["dbt_build\n(SILVER + GOLD + tests)"]
    semv["semantic_view_validated\n(3-layer harness)"]
    anom["anomaly_snapshot\n(monitoring)"]

    s3a --> dbtb
    resta --> dbtb
    sharea --> dbtb
    dbtb --> semv
    dbtb --> anom
```

## 4. Validation & maintenance harnesses (the PoC use cases)

```mermaid
flowchart TB
    subgraph ENROLL["Semantic enrollment (use case 2)"]
        V1["validate.py L1: syntax → compile"]
        V2["validate.py L2: correctness invariants"]
        V3["validate.py L3: baseline_expectations"]
        V1 --> V2 --> V3
    end
    subgraph DOWN["MCP feedback (use case 3)"]
        M1["surface all dims/metrics"]
        M2["representative queries"]
        M3["gap detection"]
        M1 --> M2 --> M3
    end
    subgraph MAINT["Automated maintenance (use case 4)"]
        H["self_healing/failure_modes.py\n4 modes: detect→diagnose→fix"]
        N["monitoring/monitor.py\n4 anomaly families vs trailing window"]
    end
```

## 5. BrightHive integration point (GAP-1)

```mermaid
flowchart LR
    subgraph BH["BrightHive (brightbot)"]
        FAC["WarehouseConnectionFactory"]
        CC["CONNECTION_CLASSES\nredshift · azure_synapse · postgres"]
        NEW["+ snowflake → SnowflakeConnection\n(GAP-1, reference in brighthive_adapter/)"]
        FAC --> CC
        CC -.add.-> NEW
    end
    NEW -->|connects, SELECT-only| SF["LONGAEVA_POC\n(live sandbox)"]
```

## Component → capability map

| Component | Dir | PoC use case | Status |
|---|---|---|---|
| Medallion DDL | `snowflake/` | environment | ✅ live |
| Synthetic seed | `seed/` | data substrate | ✅ ~450k rows |
| dbt project | `dbt/` | 1.x / 4.2 | ✅ 41 tests |
| Semantic view + YAML | `semantic/` | 2.x | ✅ |
| S3 / REST / Share ingestion | `sources/` | 1.1 / 1.2 / 1.3 | ✅ |
| Validation harness | `semantic/validate.py` | 2.3 | ✅ 3 layers |
| MCP queryability | `semantic/mcp_check.py` | 3.x | ✅ |
| Self-healing | `self_healing/` | 4.1 | ✅ 4 modes |
| Monitoring | `monitoring/` | 4.3 | ✅ 4 families |
| Orchestration | `orchestration/` | ELT infra | ✅ Dagster |
| BrightHive adapter | `brighthive_adapter/` | GAP-1 | ✅ connects |

See [`FIDELITY.md`](FIDELITY.md) for the build journal and [`../BRIGHTHIVE_GAPS.md`](../BRIGHTHIVE_GAPS.md) for the next-sprint plan.
