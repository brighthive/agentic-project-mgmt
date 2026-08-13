-- A model that deliberately attempts to touch the CLIENT'S data.
--
-- Its pre-hook issues a DELETE against dbo — scoped `WHERE 1=0` so it would
-- affect zero rows even if it were permitted. The point is not the rows; it is
-- that SQL Server refuses the statement outright, because brightagent_engineer
-- holds DENY on SCHEMA::dbo.
--
-- This exists so the governed boundary is provable THROUGH dbt, not merely at
-- the connection level. A boundary that holds for hand-written SQL but leaks
-- through the transformation engine would be no boundary at all.
--
-- Run it deliberately, by selector. It is expected to FAIL, and a run in which
-- it succeeds is the regression this fixture exists to catch.
{{ config(materialized='table', pre_hook="DELETE FROM dbo.holdings_raw WHERE 1=0") }}

select 1 as probe
