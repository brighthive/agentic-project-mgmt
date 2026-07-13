-- SQL Server Agent jobs — a real mix of pass/fail, for GC-15's job-status
-- query (msdb.dbo.sysjobs/sysjobhistory, confirmed by BH-1045's real query
-- text in docs/specs/golden-cases-loopcapital.md). Deliberately simple T-SQL
-- steps — the point is real job-history rows exist, not that the jobs do
-- anything resembling a real SSIS extract.

USE msdb;
GO

IF EXISTS (SELECT job_id FROM msdb.dbo.sysjobs WHERE name = 'LoopCapital_NightlyExtract_OK')
  EXEC sp_delete_job @job_name = 'LoopCapital_NightlyExtract_OK';
GO

EXEC sp_add_job
  @job_name = 'LoopCapital_NightlyExtract_OK',
  @description = 'Sandbox: simulates a healthy nightly SSIS-equivalent extract.';
GO

EXEC sp_add_jobstep
  @job_name = 'LoopCapital_NightlyExtract_OK',
  @step_name = 'run_extract',
  @subsystem = 'TSQL',
  @command = 'SELECT COUNT(*) FROM LoopCapitalAM.dbo.holdings_raw;',
  @database_name = 'LoopCapitalAM';
GO

EXEC sp_add_jobserver
  @job_name = 'LoopCapital_NightlyExtract_OK',
  @server_name = '(LOCAL)';
GO

EXEC sp_start_job @job_name = 'LoopCapital_NightlyExtract_OK';
GO

IF EXISTS (SELECT job_id FROM msdb.dbo.sysjobs WHERE name = 'LoopCapital_NightlyExtract_FAILED')
  EXEC sp_delete_job @job_name = 'LoopCapital_NightlyExtract_FAILED';
GO

EXEC sp_add_job
  @job_name = 'LoopCapital_NightlyExtract_FAILED',
  @description = 'Sandbox: simulates a failed nightly extract — a deliberate T-SQL error, for GC-15''s job-status query to find a real failed run.';
GO

EXEC sp_add_jobstep
  @job_name = 'LoopCapital_NightlyExtract_FAILED',
  @step_name = 'run_extract_broken',
  @subsystem = 'TSQL',
  @command = 'RAISERROR(''Deliberate sandbox failure — simulated SSIS extract error'', 16, 1);',
  @database_name = 'LoopCapitalAM';
GO

EXEC sp_add_jobserver
  @job_name = 'LoopCapital_NightlyExtract_FAILED',
  @server_name = '(LOCAL)';
GO

EXEC sp_start_job @job_name = 'LoopCapital_NightlyExtract_FAILED';
GO

-- BH-1045's ticket flags VIEW SERVER STATE as required for the disk-check
-- query (sys.dm_os_volume_stats) on a NON-sysadmin login. This sandbox
-- connects as `sa`, which already has sysadmin (and SQL Server refuses to
-- GRANT anything to sa explicitly — confirmed directly: "Cannot grant, deny,
-- or revoke permissions to sa... or yourself" — caught by this script's own
-- strict -b error checking). No grant statement needed here; this comment
-- exists so a reader porting this fixture to a non-sa login knows to add
-- `GRANT VIEW SERVER STATE TO [that_login];` themselves.
