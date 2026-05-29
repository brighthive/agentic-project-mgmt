-- RBAC stub mirroring Longaeva's MCP permission model.
-- Per Grant 2026-05-29: agents get a SCOPED SUBSET of the user's perms,
-- not full inheritance. MCP enforces this at query time.
--
-- LONGAEVA_POC_ROLE   = "user role" (full read/write within sandbox)
-- LONGAEVA_AGENT_ROLE = "agent role" (read-only on SEMANTIC + GOLD; nothing on BRONZE/SILVER/REF)
--
-- The agent role can serve queries through the semantic view but cannot:
--   - read upstream tables directly (BRONZE/SILVER/REF/SHARE_SIM)
--   - write anything anywhere
--   - use a heavier warehouse than POC_WH

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS LONGAEVA_AGENT_ROLE
  COMMENT = 'Scoped subset of LONGAEVA_POC_ROLE; consumed by MCP for agent queries';

-- Warehouse: same one, no upgrade rights
GRANT USAGE ON WAREHOUSE POC_WH TO ROLE LONGAEVA_AGENT_ROLE;

-- Database/schema usage
GRANT USAGE ON DATABASE LONGAEVA_POC TO ROLE LONGAEVA_AGENT_ROLE;
GRANT USAGE ON SCHEMA LONGAEVA_POC.SEMANTIC TO ROLE LONGAEVA_AGENT_ROLE;
GRANT USAGE ON SCHEMA LONGAEVA_POC.GOLD     TO ROLE LONGAEVA_AGENT_ROLE;

-- Read access scoped to GOLD + SEMANTIC only.
-- Note: querying a SEMANTIC VIEW transitively reads its underlying tables.
-- Without these GOLD + REF grants, SELECT on the view fails.
GRANT SELECT ON ALL TABLES IN SCHEMA LONGAEVA_POC.GOLD
  TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA LONGAEVA_POC.GOLD
  TO ROLE LONGAEVA_AGENT_ROLE;

-- Reference data needed for the semantic view's joins
GRANT USAGE  ON SCHEMA LONGAEVA_POC.REF TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA LONGAEVA_POC.REF
  TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON FUTURE TABLES IN SCHEMA LONGAEVA_POC.REF
  TO ROLE LONGAEVA_AGENT_ROLE;

-- Semantic views (current and future)
GRANT SELECT ON ALL SEMANTIC VIEWS IN SCHEMA LONGAEVA_POC.SEMANTIC
  TO ROLE LONGAEVA_AGENT_ROLE;
GRANT SELECT ON FUTURE SEMANTIC VIEWS IN SCHEMA LONGAEVA_POC.SEMANTIC
  TO ROLE LONGAEVA_AGENT_ROLE;

-- DELIBERATELY ABSENT (this is the "subset" part):
--   - BRONZE schema: agents must not see raw vendor data
--   - SILVER schema: agents go through GOLD/SEMANTIC, not staging tables
--   - LONGAEVA_VENDOR_SHARE_SIM: vendor data not exposed to agents
--   - WRITE on anything: agents are read-only
--   - Larger warehouses: agents can't escalate compute

-- Grant the agent role to KURICHINCA so we can test it
GRANT ROLE LONGAEVA_AGENT_ROLE TO USER KURICHINCA;
