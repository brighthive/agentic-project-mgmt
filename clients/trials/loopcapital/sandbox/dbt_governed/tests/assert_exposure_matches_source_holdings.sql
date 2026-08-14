-- Reconciles the governed roll-up against the raw extract it claims to summarise.
--
-- Extract_Holdings_Nightly.dtsx reads quantity as DT_R8 — a binary double — into a
-- decimal(18,4) column, and sets no error disposition on the destination. Both halves
-- of that are silent. A binary double cannot represent every exact decimal, so a
-- quantity can arrive perturbed and still insert cleanly; and a row that does fail
-- conversion takes the package down rather than being redirected to an error output.
-- In either case the first visible symptom is a total that no longer matches its source.
--
-- schema.yml tests portfolio_id, as_of_date and position_count for null. It does not
-- test total_quantity at all — the one number the exposure report is actually built on.
-- This closes that gap by comparing the model to the source it was derived from, so a
-- partial load, a dropped row, or drifted precision fails the run instead of publishing.

with source_rollup as (

    select
        portfolio_id,
        as_of_date,
        count(*)      as source_position_count,
        sum(quantity) as source_total_quantity

    from {{ source('loopcapital', 'holdings_raw') }}
    group by portfolio_id, as_of_date

)

select
    coalesce(rolled_up.portfolio_id, from_source.portfolio_id) as portfolio_id,
    coalesce(rolled_up.as_of_date, from_source.as_of_date)     as as_of_date,
    rolled_up.position_count,
    from_source.source_position_count,
    rolled_up.total_quantity,
    from_source.source_total_quantity

from {{ ref('portfolio_exposure_daily') }} as rolled_up
full outer join source_rollup as from_source
    on  rolled_up.portfolio_id = from_source.portfolio_id
    and rolled_up.as_of_date   = from_source.as_of_date

where rolled_up.portfolio_id is null
   or from_source.portfolio_id is null
   or rolled_up.position_count <> from_source.source_position_count
   or rolled_up.total_quantity <> from_source.source_total_quantity
