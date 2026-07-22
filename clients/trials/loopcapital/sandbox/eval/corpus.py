"""Labeled corpus for the Layer 0 classifier eval.

Each case: {"error": <realistic error text>, "expected": <mode|None>, "note": ...}
- expected = one of the 4 modes  -> classifier SHOULD return that mode
- expected = None                -> classifier MUST abstain (JOB_RUNTIME / generic)

Honesty rule: these are written to resemble ACTUAL dbt / Snowflake / SQL Server /
Databricks / BigQuery error output. They are NOT reverse-engineered from the
classifier's regexes. Where a realistic phrasing is unlikely to match the current
patterns, it is still labeled by its TRUE root cause — so the eval surfaces recall
gaps rather than hiding them. Cases marked note="RECALL-RISK" are ones I expect
the current keyword patterns may miss; keeping them honest is the point.
"""

from __future__ import annotations

CORPUS: list[dict] = [
    # ------------------------------------------------------------------ #
    # schema_drift — vendor added/renamed a column; table lacks it
    # ------------------------------------------------------------------ #
    {
        "error": "SQL compilation error: invalid identifier 'SETTLEMENT_CCY'",
        "expected": "schema_drift",
        "note": "canonical Snowflake drift error",
    },
    {
        "error": 'Database Error in model stg_vendor_ratings: column "settlement_ccy" '
                 'of relation "raw_market_prices" does not exist',
        "expected": "schema_drift",
        "note": "dbt+Postgres drift",
    },
    {
        "error": "Column 'credit_watch_flag' does not exist in table VENDOR_SECURITY_MASTER",
        "expected": "schema_drift",
    },
    {
        "error": "SQL compilation error: error line 3 at position 8\n"
                 "invalid identifier 'ISSUER_LEI'",
        "expected": "schema_drift",
        "note": "multiline Snowflake",
    },
    {
        "error": "Model does not have a column named 'as_of_ccy' which was expected by the downstream ref",
        "expected": "schema_drift",
    },
    {
        "error": "Compilation Error in model int_enriched_holdings: unknown column 'rating_agency' in source",
        "expected": "schema_drift",
        "note": "RECALL-RISK: 'unknown column' not in patterns ('unrecognized column' is); "
                "'compilation error' requires co-occurring column|identifier — 'column' is present",
    },
    {
        "error": "Unrecognized name: settlement_ccy at [3:14]",
        "expected": "schema_drift",
        "note": "RECALL-RISK: BigQuery says 'unrecognized name', pattern is 'unrecognized column'",
    },

    # ------------------------------------------------------------------ #
    # missing_partition — a daily slice never landed
    # ------------------------------------------------------------------ #
    {
        "error": "No data found for partition dt=2026-05-15 in stg_security_prices",
        "expected": "missing_partition",
    },
    {
        "error": "Partition not found: 2026-05-15 (expected daily business-day partition)",
        "expected": "missing_partition",
    },
    {
        "error": "Query returned no rows: table LONGAEVA_POC.SILVER.STG_SECURITY_PRICES is empty for the requested window",
        "expected": "missing_partition",
        "note": "matches 'table .* is empty'",
    },
    {
        "error": "No such partition: ds=2026-05-15",
        "expected": "missing_partition",
    },
    {
        "error": "dbt test failed: assert_exposure_present_every_business_day "
                 "got 1 result, expected 0 (business day 2026-05-15 has no rows)",
        "expected": "missing_partition",
        "note": "RECALL-RISK: real dbt custom-test failures phrase it as 'got N, expected 0', "
                "no partition keyword — likely a miss, and that is the finding",
    },
    {
        "error": "Source freshness check failed: max(loaded_at) is 2 days old for stg_security_prices",
        "expected": "missing_partition",
        "note": "RECALL-RISK: freshness-based detection of a missing day; no matching keyword",
    },

    # ------------------------------------------------------------------ #
    # broken_stage — external stage mis-pointed / wrong format
    # ------------------------------------------------------------------ #
    {
        "error": "Stage 'S3_VENDOR_MARKET_DATA' does not exist or not authorized",
        "expected": "broken_stage",
        "note": "canonical Snowflake stage error",
    },
    {
        "error": "Error accessing external stage @s3_vendor_market_data: file format mismatch",
        "expected": "broken_stage",
        "note": "matches 'external stage'",
    },
    {
        "error": "Failed to load from stage @vendor_drops: 0 files matched pattern",
        "expected": "broken_stage",
        "note": "matches 'failed to load (stage|file|from)'",
    },
    {
        "error": "File not found: s3://loop-vendor-drops/2026-05-15/holdings.csv",
        "expected": "broken_stage",
    },
    {
        "error": "Remote file operation failed: S3 bucket 'loop-vendor-drops' access denied",
        "expected": "broken_stage",
        "note": "matches 's3 bucket'; borderline vs permission — labeled stage per intent",
    },
    {
        "error": "COPY INTO failed: unable to parse file as CSV, file format on stage is JSON",
        "expected": "broken_stage",
        "note": "RECALL-RISK: the failure_modes.py broken_stage scenario (JSON vs CSV) — "
                "real COPY error names no stage keyword; likely a miss",
    },

    # ------------------------------------------------------------------ #
    # dbt_contract — enforced contract violated
    # ------------------------------------------------------------------ #
    {
        "error": "Compilation Error: This model has an enforced contract that failed.\n"
                 "Contract enforcement failed for: mart_daily_portfolio_exposure",
        "expected": "dbt_contract",
        "note": "canonical dbt contract error",
    },
    {
        "error": "Contract enforcement failed for model dp_regional_exposure_daily: "
                 "columns not matched",
        "expected": "dbt_contract",
    },
    {
        "error": "Data type mismatch: expected NUMBER(38,2), got VARCHAR for exposure_amount_usd",
        "expected": "dbt_contract",
    },
    {
        "error": "Column type mismatch on as_of_date: model defines DATE, contract expects TIMESTAMP_NTZ",
        "expected": "dbt_contract",
    },
    {
        "error": "The model contract was violated: missing enforced column 'currency'",
        "expected": "dbt_contract",
        "note": "matches 'contract.*(enforce|violat)'",
    },

    # ------------------------------------------------------------------ #
    # MUST ABSTAIN — JOB_RUNTIME failures (retry/escalate, never a fix PR)
    # ------------------------------------------------------------------ #
    {
        "error": "dbt run failed: connection timed out after 300s connecting to warehouse",
        "expected": None,
        "note": "JOB_RUNTIME timeout",
    },
    {
        "error": "Databricks cluster terminated: DRIVER_UNRESPONSIVE (out of memory)",
        "expected": None,
        "note": "JOB_RUNTIME OOM",
    },
    {
        "error": "Warehouse LONGAEVA_WH suspended; statement queued and then aborted",
        "expected": None,
    },
    {
        "error": "SQL Server Agent job 'Extract_Holdings_Nightly' failed: "
                 "the step did not generate any output (step timed out)",
        "expected": None,
        "note": "SQL Server Agent runtime failure",
    },
    {
        "error": "HTTP 429 Too Many Requests from dbt Cloud API; retry after 60s",
        "expected": None,
        "note": "rate limit",
    },
    {
        "error": "Login failed for user 'brighthive_ro'. (SQL error 18456)",
        "expected": None,
        "note": "auth/permission, not data-shape",
    },
    {
        "error": "Insufficient privileges to operate on schema 'GOLD' (VIEW SERVER STATE required)",
        "expected": None,
        "note": "permission error — must NOT be broken_stage",
    },
    {
        "error": "Disk space on volume C: is at 18% remaining (threshold 20%)",
        "expected": None,
        "note": "Frank's disk-space signal — a real alert, but NOT a data-shape fix",
    },
    {
        "error": "Deadlock detected; transaction was chosen as the deadlock victim (SQL error 1205)",
        "expected": None,
    },
    {
        "error": "Segmentation fault in dbt adapter; process exited with code 139",
        "expected": None,
    },

    # ------------------------------------------------------------------ #
    # ADVERSARIAL near-misses — target the 3 CodeRabbit guardrails.
    # These MUST abstain; a naive keyword match would wrongly classify them.
    # ------------------------------------------------------------------ #
    {
        "error": "Failed to honor the data processing contract with the vendor SLA; "
                 "escalate to account team",
        "expected": None,
        "note": "GUARDRAIL: bare 'contract' with no enforce/violat — must NOT be dbt_contract",
    },
    {
        "error": "Compilation Error: syntax error at or near 'SELCT' in model dp_top_issuers_daily",
        "expected": None,
        "note": "GUARDRAIL: generic compile/syntax error, no column|identifier — must NOT be schema_drift",
    },
    {
        "error": "Compilation Error: macro 'get_fiscal_quarter' not found",
        "expected": None,
        "note": "GUARDRAIL: missing macro, a compile error but not schema drift",
    },
    {
        "error": "Failed to load Python dbt package dependencies from requirements.txt",
        "expected": None,
        "note": "GUARDRAIL: 'failed to load' but target is packages, not stage|file|from",
    },
    {
        "error": "Service contract renewal is overdue; API access will be throttled",
        "expected": None,
        "note": "GUARDRAIL: 'contract' in a totally unrelated billing sense",
    },
    {
        "error": "",
        "expected": None,
        "note": "empty string — must abstain (guarded by `if not error_message`)",
    },
]
