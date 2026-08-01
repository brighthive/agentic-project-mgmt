-- Student matter-scores — SQL Server / Azure Synapse DDL.
-- Materializes the canonical 3-table model (../../MODEL.md) in T-SQL dialect.
-- The SSIS packages in ../ssis/*.dtsx load these tables from ../../sources/*.csv.
-- Types follow MODEL.md's "SQL Server / Synapse" column: NVARCHAR / INT / DECIMAL(5,2).

IF OBJECT_ID('dbo.weekly_matter_scores', 'U') IS NOT NULL DROP TABLE dbo.weekly_matter_scores;
IF OBJECT_ID('dbo.monthly_matter_scores', 'U') IS NOT NULL DROP TABLE dbo.monthly_matter_scores;
IF OBJECT_ID('dbo.schools', 'U') IS NOT NULL DROP TABLE dbo.schools;

CREATE TABLE dbo.schools (
    school_id    INT            NOT NULL,
    school_name  NVARCHAR(120)  NOT NULL,
    state        NVARCHAR(2)    NOT NULL,   -- the "by state" rollup key
    city         NVARCHAR(80)   NULL,
    enrollment   INT            NULL,
    CONSTRAINT PK_schools PRIMARY KEY (school_id)
);

CREATE TABLE dbo.weekly_matter_scores (
    school_id      INT           NOT NULL,
    iso_year       INT           NOT NULL,
    iso_week       INT           NOT NULL,
    matter_score   DECIMAL(5,2)  NOT NULL,  -- national weekly index 0.00-100.00
    national_rank  INT           NULL,
    CONSTRAINT PK_weekly_matter_scores PRIMARY KEY (school_id, iso_year, iso_week),
    CONSTRAINT FK_weekly_school FOREIGN KEY (school_id) REFERENCES dbo.schools (school_id)
);

CREATE TABLE dbo.monthly_matter_scores (
    school_id      INT           NOT NULL,
    [year]         INT           NOT NULL,
    [month]        INT           NOT NULL,
    matter_score   DECIMAL(5,2)  NOT NULL,  -- national monthly index 0.00-100.00
    national_rank  INT           NULL,
    CONSTRAINT PK_monthly_matter_scores PRIMARY KEY (school_id, [year], [month]),
    CONSTRAINT FK_monthly_school FOREIGN KEY (school_id) REFERENCES dbo.schools (school_id)
);
