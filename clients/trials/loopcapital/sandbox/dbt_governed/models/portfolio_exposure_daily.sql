-- A real transformation an engineer would actually write: daily exposure per
-- portfolio, rolled up from the raw holdings extract.
--
-- Reads the client's dbo data, writes into the brightagent schema. That split IS
-- the governed-write contract, and it is enforced by the connection principal
-- rather than by anything in this file.
select
    portfolio_id,
    as_of_date,
    count(*)              as position_count,
    sum(quantity)         as total_quantity,
    max(loaded_at)        as last_loaded_at
from {{ source('loopcapital', 'holdings_raw') }}
group by portfolio_id, as_of_date
