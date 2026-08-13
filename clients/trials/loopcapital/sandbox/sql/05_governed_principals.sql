-- Loop Capital sandbox — governed connection principals (BH-1403).
--
-- Frank's trial grants BrightAgent "scoped read + optional governed-write
-- (reviewable PRs only, nothing applied without approval)" against HIS OWN
-- SQL Server 2019 box. His DBAs will never hand over `sa`, so a demo that
-- runs as `sa` proves nothing: `sa` can do anything, and a write that
-- succeeds under `sa` says nothing about whether a boundary holds.
--
-- This file creates the two principals the trial actually implies, so the
-- boundary is enforced by SQL Server itself — not by prompt wording, not by
-- an agent's good behaviour, and not by a tool-layer guard that a future
-- refactor could drop.
--
--   brightagent_reader    read-only everywhere. The monitoring principal.
--   brightagent_engineer  reads the client's data, writes ONLY into the
--                         `brightagent` schema it owns.
--
-- Verified by ../governed_write_check.py against a real running instance.
-- See docs/specs/loopcapital-onprem-read-write-sandbox.md §3 for the
-- invariants each GRANT/DENY below exists to satisfy.

USE LoopCapitalAM;
GO

-- ============================================================================
-- The agent-owned workspace. Everything brightagent_engineer may write lives
-- here, and nothing else does. Schema ownership is what bounds the write
-- authority — not a naming convention we hope people follow.
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'brightagent')
  EXEC('CREATE SCHEMA brightagent');
GO

-- ============================================================================
-- brightagent_reader — the monitoring principal (INV-1, INV-5)
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'brightagent_reader')
  CREATE LOGIN brightagent_reader
    WITH PASSWORD = '$(BRIGHTAGENT_READER_PASSWORD)',
         CHECK_POLICY = OFF;   -- local throwaway sandbox; never a real credential
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'brightagent_reader')
  CREATE USER brightagent_reader FOR LOGIN brightagent_reader;
GO

-- Reads the client's data. Nothing more.
GRANT SELECT ON SCHEMA::dbo TO brightagent_reader;
GO

-- Belt and braces: SELECT alone does not imply write, but an explicit DENY
-- survives someone later adding this principal to a role that does. DENY
-- always beats GRANT in SQL Server, so this cannot be silently widened.
DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::dbo TO brightagent_reader;
DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::brightagent TO brightagent_reader;
GO

-- ============================================================================
-- brightagent_engineer — the governed-write principal (INV-2, INV-3, INV-5)
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = 'brightagent_engineer')
  CREATE LOGIN brightagent_engineer
    WITH PASSWORD = '$(BRIGHTAGENT_ENGINEER_PASSWORD)',
         CHECK_POLICY = OFF;
GO

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'brightagent_engineer')
  CREATE USER brightagent_engineer FOR LOGIN brightagent_engineer;
GO

-- Reads the client's data, exactly like the reader does.
GRANT SELECT ON SCHEMA::dbo TO brightagent_engineer;
GO

-- ...but may NOT change it. This is the load-bearing line of the whole file:
-- it is what makes "the agent cannot touch your data" a database fact rather
-- than a promise in a slide deck.
DENY INSERT, UPDATE, DELETE, ALTER ON SCHEMA::dbo TO brightagent_engineer;
GO

-- Owning the schema grants full DDL/DML *inside it* and nowhere else.
-- CREATE TABLE/VIEW are server-scoped rights that still resolve against a
-- schema the principal owns, so this pair is what bounds the blast radius.
ALTER AUTHORIZATION ON SCHEMA::brightagent TO brightagent_engineer;
GRANT CREATE TABLE, CREATE VIEW TO brightagent_engineer;
GO

-- dbt Core is the write engine for this trial (dbt Cloud has no SQL Server
-- destination, and could not reach an on-prem box even if it did — so dbt Core
-- runs on the client's own network instead). Its table materialization reads
-- sys.sql_expression_dependencies to find dependent objects before replacing a
-- table, and that catalog view requires VIEW DEFINITION.
--
-- BOTH grants below are required, and VIEW DEFINITION alone is not enough:
-- SELECT on sys.sql_expression_dependencies is granted to the db_owner fixed
-- role by default, and these principals are deliberately not db_owner (INV-4).
-- Found by running the real adapter — `dbt run` fails with error 229 on
-- 'sql_expression_dependencies' with only the first grant, even though the
-- write itself is permitted.
--
-- Both are metadata-only: they confer no data read and no write. Re-verified
-- after granting — governed_write_check.py still holds 13/13, so the boundary
-- above is unchanged.
GRANT VIEW DEFINITION TO brightagent_engineer;
GRANT SELECT ON OBJECT::sys.sql_expression_dependencies TO brightagent_engineer;
GO

-- ============================================================================
-- Health monitoring rights — both principals (success criterion 4)
--
-- Disk pressure and SQL Agent job status are the two signals Frank named
-- ("alert when it's at 20% capacity left"). Both live outside the user
-- database, so they need their own grants; without these the watchdog
-- queries return empty and look like a silent pass.
-- ============================================================================

USE master;
GO

-- sys.dm_os_volume_stats — the real free-space reading on the mounted volume.
GRANT VIEW SERVER STATE TO brightagent_reader;
GRANT VIEW SERVER STATE TO brightagent_engineer;
GO

USE msdb;
GO

-- SQL Agent job history. SQLAgentReaderRole is the least-privilege built-in
-- that can see *all* jobs' history, not merely jobs the principal owns —
-- which is what monitoring someone else's server requires.
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'brightagent_reader')
  CREATE USER brightagent_reader FOR LOGIN brightagent_reader;
IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'brightagent_engineer')
  CREATE USER brightagent_engineer FOR LOGIN brightagent_engineer;
GO

ALTER ROLE SQLAgentReaderRole ADD MEMBER brightagent_reader;
ALTER ROLE SQLAgentReaderRole ADD MEMBER brightagent_engineer;
GO

-- ============================================================================
-- INV-4: neither principal may hold admin rights. Not asserted here — asserted
-- by governed_write_check.py against the live server, because a check that
-- lives in the same file that does the granting can only ever agree with
-- itself.
-- ============================================================================
