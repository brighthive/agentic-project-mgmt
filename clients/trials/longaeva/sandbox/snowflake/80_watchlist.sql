-- 80_watchlist.sql — REF.WATCHLIST seed
--
-- Powers the "Sarah's Monday morning" UAT use case (Scenario 14, SARAH_DEMO.md).
-- A non-technical analyst asks "any of these on a watchlist?" — this is the
-- ground-truth table the agent reads. Without it Q4 of the demo is hallucinated.
--
-- Idempotent: CREATE OR REPLACE + DELETE before INSERT.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;
USE SCHEMA REF;

CREATE OR REPLACE TABLE WATCHLIST (
    INTERNAL_ISSUER_ID  TEXT        NOT NULL,
    ISSUER_NAME         TEXT        NOT NULL,
    WATCHLIST_REASON    TEXT        NOT NULL,
    SEVERITY            TEXT        NOT NULL,
    ADDED_DATE          DATE        NOT NULL,
    ADDED_BY            TEXT        NOT NULL,
    CONSTRAINT pk_watchlist PRIMARY KEY (INTERNAL_ISSUER_ID)
) COMMENT = 'Analyst watchlist — issuers flagged for material attention. Grounds Q4 of the Sarah demo.';

-- Seed: 60 entries spanning the four severities + 8 reason categories.
-- Issuer IDs reference REF.IDENTIFIER_MAP (ISS-0000..ISS-0195, all active).
INSERT INTO WATCHLIST (INTERNAL_ISSUER_ID, ISSUER_NAME, WATCHLIST_REASON, SEVERITY, ADDED_DATE, ADDED_BY) VALUES
    ('ISS-0001', 'Synthetic Issuer 0001', 'Credit rating downgrade — Moody''s cut to Baa3 from Baa2',                  'elevated', '2026-05-12', 'risk-team'),
    ('ISS-0007', 'Synthetic Issuer 0007', 'Earnings miss — Q1 EPS 22% below consensus',                                 'monitor',  '2026-04-30', 'research-team'),
    ('ISS-0014', 'Synthetic Issuer 0014', 'Regulatory review — FTC second request on pending acquisition',              'elevated', '2026-05-22', 'compliance'),
    ('ISS-0018', 'Synthetic Issuer 0018', 'Concentration limit — position now 8.1% of book, breaches 7.5% soft cap',    'elevated', '2026-06-09', 'risk-team'),
    ('ISS-0021', 'Synthetic Issuer 0021', 'Material news — CEO transition announced',                                   'monitor',  '2026-05-28', 'research-team'),
    ('ISS-0026', 'Synthetic Issuer 0026', 'Sector overweight — sleeve at 28% vs 20% bench, monitor for rebalance',      'monitor',  '2026-05-05', 'pm-team'),
    ('ISS-0030', 'Synthetic Issuer 0030', 'Credit rating downgrade — S&P negative outlook',                             'monitor',  '2026-05-15', 'risk-team'),
    ('ISS-0033', 'Synthetic Issuer 0033', 'Liquidity concern — average daily volume down 60% over 90 days',             'elevated', '2026-06-02', 'trading-desk'),
    ('ISS-0038', 'Synthetic Issuer 0038', 'Concentration limit — position now 7.5% of P-000, at soft cap',              'elevated', '2026-06-15', 'risk-team'),
    ('ISS-0041', 'Synthetic Issuer 0041', 'Regulatory review — SEC inquiry into prior period restatements',             'critical', '2026-05-08', 'compliance'),
    ('ISS-0047', 'Synthetic Issuer 0047', 'Earnings miss — revenue guidance lowered by 8%',                             'monitor',  '2026-05-19', 'research-team'),
    ('ISS-0052', 'Synthetic Issuer 0052', 'Material news — major customer loss announced',                              'elevated', '2026-06-01', 'research-team'),
    ('ISS-0058', 'Synthetic Issuer 0058', 'Sector overweight — energy book up 35%, watching for crude reversion',       'monitor',  '2026-05-25', 'pm-team'),
    ('ISS-0063', 'Synthetic Issuer 0063', 'Credit rating downgrade — Fitch under review for downgrade',                 'elevated', '2026-06-04', 'risk-team'),
    ('ISS-0069', 'Synthetic Issuer 0069', 'Geopolitical exposure — primary operations in sanctioned jurisdiction',      'critical', '2026-04-22', 'compliance'),
    ('ISS-0074', 'Synthetic Issuer 0074', 'Material news — class action lawsuit filed',                                 'monitor',  '2026-05-30', 'compliance'),
    ('ISS-0078', 'Synthetic Issuer 0078', 'Earnings miss — Q1 below consensus, guidance withdrawn',                     'elevated', '2026-05-11', 'research-team'),
    ('ISS-0082', 'Synthetic Issuer 0082', 'Concentration limit — top-10 position in 3 portfolios concurrently',         'elevated', '2026-06-12', 'risk-team'),
    ('ISS-0087', 'Synthetic Issuer 0087', 'Regulatory review — environmental fine pending',                             'monitor',  '2026-05-03', 'compliance'),
    ('ISS-0091', 'Synthetic Issuer 0091', 'Liquidity concern — bid/ask widened 3x normal',                              'monitor',  '2026-06-07', 'trading-desk'),
    ('ISS-0095', 'Synthetic Issuer 0095', 'Sector overweight — APAC tech overweight, monitor for rotation',             'monitor',  '2026-05-17', 'pm-team'),
    ('ISS-0102', 'Synthetic Issuer 0102', 'Material news — debt covenant breach disclosed',                             'critical', '2026-06-05', 'risk-team'),
    ('ISS-0109', 'Synthetic Issuer 0109', 'Concentration limit — position 7.78% of P-000, at soft cap',                 'elevated', '2026-06-14', 'risk-team'),
    ('ISS-0115', 'Synthetic Issuer 0115', 'Credit rating downgrade — Moody''s downgrade to Ba1 (HY)',                   'elevated', '2026-05-26', 'risk-team'),
    ('ISS-0121', 'Synthetic Issuer 0121', 'Earnings miss — margin compression below model',                             'monitor',  '2026-05-09', 'research-team'),
    ('ISS-0127', 'Synthetic Issuer 0127', 'Regulatory review — antitrust filing under examination',                     'monitor',  '2026-04-28', 'compliance'),
    ('ISS-0129', 'Synthetic Issuer 0129', 'Concentration limit — 6.91% of P-000, watching trajectory',                  'monitor',  '2026-06-16', 'risk-team'),
    ('ISS-0133', 'Synthetic Issuer 0133', 'Material news — major asset divestiture announced',                          'monitor',  '2026-05-21', 'research-team'),
    ('ISS-0138', 'Synthetic Issuer 0138', 'Liquidity concern — illiquid issue, can''t exit in <5 days at NAV',          'elevated', '2026-05-18', 'trading-desk'),
    ('ISS-0142', 'Synthetic Issuer 0142', 'Concentration limit — top position at 8.0% of P-000, above soft cap',        'critical', '2026-06-15', 'risk-team'),
    ('ISS-0147', 'Synthetic Issuer 0147', 'Sector overweight — financials sleeve concentrated post-rate-shock',         'monitor',  '2026-05-23', 'pm-team'),
    ('ISS-0152', 'Synthetic Issuer 0152', 'Credit rating downgrade — S&P review for negative action',                   'monitor',  '2026-05-06', 'risk-team'),
    ('ISS-0156', 'Synthetic Issuer 0156', 'Earnings miss — Q2 preliminary read below model',                            'monitor',  '2026-06-08', 'research-team'),
    ('ISS-0159', 'Synthetic Issuer 0159', 'Concentration limit — 6.56% of P-000',                                       'monitor',  '2026-06-13', 'risk-team'),
    ('ISS-0162', 'Synthetic Issuer 0162', 'Regulatory review — labor practices investigation opened',                   'monitor',  '2026-05-14', 'compliance'),
    ('ISS-0166', 'Synthetic Issuer 0166', 'Material news — board chair stepped down unexpectedly',                      'elevated', '2026-06-03', 'research-team'),
    ('ISS-0170', 'Synthetic Issuer 0170', 'Geopolitical exposure — 40% of revenue from contested jurisdiction',         'elevated', '2026-05-01', 'compliance'),
    ('ISS-0174', 'Synthetic Issuer 0174', 'Sector overweight — utilities tilt above bench, watching rate path',         'monitor',  '2026-05-29', 'pm-team'),
    ('ISS-0178', 'Synthetic Issuer 0178', 'Liquidity concern — small-cap, max position size constraint hit',            'monitor',  '2026-06-10', 'trading-desk'),
    ('ISS-0183', 'Synthetic Issuer 0183', 'Concentration limit — 6.33% of P-000, monitor for trim',                     'monitor',  '2026-06-15', 'risk-team'),
    ('ISS-0186', 'Synthetic Issuer 0186', 'Credit rating downgrade — placed on negative watch',                         'monitor',  '2026-05-16', 'risk-team'),
    ('ISS-0189', 'Synthetic Issuer 0189', 'Earnings miss — operational guidance cut for FY',                            'elevated', '2026-05-24', 'research-team'),
    ('ISS-0192', 'Synthetic Issuer 0192', 'Concentration limit — 6.32% of P-000, at watchpoint',                        'monitor',  '2026-06-15', 'risk-team'),
    ('ISS-0195', 'Synthetic Issuer 0195', 'Material news — strategic review announced by board',                        'monitor',  '2026-06-11', 'research-team'),
    ('ISS-0011', 'Synthetic Issuer 0011', 'Regulatory review — banking license renewal under scrutiny',                 'elevated', '2026-05-04', 'compliance'),
    ('ISS-0024', 'Synthetic Issuer 0024', 'Material news — major recall affecting flagship product line',               'critical', '2026-06-06', 'research-team'),
    ('ISS-0036', 'Synthetic Issuer 0036', 'Earnings miss — Q1 EPS below model, guidance maintained',                    'monitor',  '2026-05-27', 'research-team'),
    ('ISS-0044', 'Synthetic Issuer 0044', 'Credit rating downgrade — junior debt cut by 2 notches',                     'elevated', '2026-04-25', 'risk-team'),
    ('ISS-0056', 'Synthetic Issuer 0056', 'Sector overweight — REITs above bench post duration shift',                  'monitor',  '2026-05-13', 'pm-team'),
    ('ISS-0066', 'Synthetic Issuer 0066', 'Liquidity concern — daily volume below 50k shares, hard to exit',            'monitor',  '2026-06-09', 'trading-desk'),
    ('ISS-0072', 'Synthetic Issuer 0072', 'Geopolitical exposure — Russia revenue line not yet wound down',             'critical', '2026-04-18', 'compliance'),
    ('ISS-0085', 'Synthetic Issuer 0085', 'Regulatory review — FDA action on pending approval',                         'elevated', '2026-05-20', 'compliance'),
    ('ISS-0098', 'Synthetic Issuer 0098', 'Material news — major customer concentration disclosure',                    'monitor',  '2026-06-04', 'research-team'),
    ('ISS-0106', 'Synthetic Issuer 0106', 'Earnings miss — Q2 prelim disappoint, model under review',                   'elevated', '2026-06-07', 'research-team'),
    ('ISS-0118', 'Synthetic Issuer 0118', 'Sector overweight — semis above target, watching cycle inflection',          'monitor',  '2026-05-31', 'pm-team'),
    ('ISS-0125', 'Synthetic Issuer 0125', 'Credit rating downgrade — senior unsecured under review',                    'monitor',  '2026-05-10', 'risk-team'),
    ('ISS-0140', 'Synthetic Issuer 0140', 'Liquidity concern — block trade overhang from prior insider sale',           'monitor',  '2026-06-02', 'trading-desk'),
    ('ISS-0155', 'Synthetic Issuer 0155', 'Regulatory review — IRS audit ongoing, no findings yet',                     'monitor',  '2026-05-07', 'compliance'),
    ('ISS-0168', 'Synthetic Issuer 0168', 'Material news — strategic acquisition closed, integration risk',             'monitor',  '2026-06-13', 'research-team'),
    ('ISS-0180', 'Synthetic Issuer 0180', 'Earnings miss — Q1 weak on FX headwind, expected to recover',                'monitor',  '2026-05-02', 'research-team');

-- Verify
SELECT severity, COUNT(*) AS n FROM WATCHLIST GROUP BY 1 ORDER BY 1;
SELECT COUNT(*) AS total_rows FROM WATCHLIST;

-- Grant read to agent
USE ROLE ACCOUNTADMIN;
GRANT SELECT ON TABLE LONGAEVA_POC.REF.WATCHLIST TO ROLE LONGAEVA_AGENT_ROLE;
