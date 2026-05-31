"""Dagster definitions: the Longaeva ELT pipeline + a daily schedule.

OpenLineage export is configured via env (OPENLINEAGE_URL) when present; absent
it no-ops, so the project runs locally without a Marquez/OpenLineage backend.
The asset graph itself IS the lineage the self-healing agent traverses.
"""

from __future__ import annotations

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from longaeva_dagster import assets

all_assets = load_assets_from_modules([assets])

# Full pipeline job: ingestion -> dbt -> validate + monitor
elt_pipeline_job = define_asset_job(
    name="longaeva_elt_pipeline",
    selection=AssetSelection.all(),
    description="Full ELT: 3-source ingestion -> dbt build -> semantic validate + anomaly snapshot",
)

# Daily refresh (off-minute to avoid fleet pile-up), mirrors a vendor daily cadence.
daily_refresh = ScheduleDefinition(
    name="daily_refresh",
    job=elt_pipeline_job,
    cron_schedule="17 6 * * *",
    execution_timezone="America/New_York",
)

defs = Definitions(
    assets=all_assets,
    jobs=[elt_pipeline_job],
    schedules=[daily_refresh],
)
