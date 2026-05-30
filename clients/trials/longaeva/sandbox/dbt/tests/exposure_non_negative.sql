-- Mirrors baseline_expectations.universal.total_exposure_usd_non_negative
select 1
from {{ ref('dp_regional_exposure_daily') }}
where total_exposure_usd < 0
