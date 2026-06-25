#!/usr/bin/env python3
"""Seed the local Postgres dogfood warehouse with Longaeva-shaped synthetic data (BH-764).

Deterministic (seed=42), self-contained (stdlib + psycopg2 only — no pandas /
snowflake-connector). Sized for FAST local use: a small but realistic slice that
lets the agent answer the UAT questions (top positions, sector/country
concentration, weekly movers, watchlist crosscheck) against local Postgres
instead of staging Snowflake.

Volumes (small on purpose — local, not a load test):
  ref.geo_codes            ~12 countries
  ref.classification_codes 10 sectors
  ref.identifier_map       60 issuers   (named "Synthetic Issuer NNNN" — matches
                                          the Snowflake sandbox naming)
  ref.watchlist            ~18 issuers  (critical/elevated/monitor mix)
  gold.mart_daily_portfolio_exposure   5 dates x 10 portfolios x ~12 holdings
  gold.mart_issuer_risk_summary        5 dates x 60 issuers
  gold.mart_weekly_exposure_delta      ~120 movers

Run (after 01_schema.sql is applied):
  POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_USER=bh \
  POSTGRES_PASSWORD=bh_local_dev POSTGRES_DATABASE=bh_warehouse \
  python seed_local_warehouse.py [--reset]

Idempotent: TRUNCATE before insert (so re-running gives the same deterministic set).
"""

from __future__ import annotations

import os
import random
import sys
from datetime import date, timedelta

import psycopg2

SEED = 42
N_ISSUERS = 60
N_PORTFOLIOS = 10
N_DATES = 5  # trailing business days
LATEST_DATE = date(2026, 5, 29)  # matches the Snowflake sandbox latest date

COUNTRIES = [
    ("USA", "United States", "AMERICAS"),
    ("CAN", "Canada", "AMERICAS"),
    ("BRA", "Brazil", "AMERICAS"),
    ("GBR", "United Kingdom", "EMEA"),
    ("FRA", "France", "EMEA"),
    ("DEU", "Germany", "EMEA"),
    ("CHE", "Switzerland", "EMEA"),
    ("ESP", "Spain", "EMEA"),
    ("KEN", "Kenya", "EMEA"),
    ("EGY", "Egypt", "EMEA"),
    ("JPN", "Japan", "APAC"),
    ("HKG", "Hong Kong", "APAC"),
]
SECTORS = ["TECH", "FINS", "ENRG", "HLTH", "CONS", "INDU", "UTIL", "MATR", "REAL", "COMM"]
ASSET_CLASSES = ["EQUITY", "BOND", "FX", "DERIV"]
SEVERITIES = ["critical", "elevated", "monitor"]
WATCHLIST_REASONS = {
    "critical": [
        "Concentration limit breach — position above soft cap",
        "Material news — debt covenant breach disclosed",
        "Regulatory review — SEC inquiry into restatements",
    ],
    "elevated": [
        "Credit rating downgrade — Moody's cut one notch",
        "Earnings miss — Q1 EPS below consensus",
        "Regulatory review — FTC second request",
    ],
    "monitor": [
        "Material news — CEO transition announced",
        "Watching trajectory — approaching watchpoint",
        "Q1 EPS below model, guidance maintained",
    ],
}


def _connect():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        user=os.environ.get("POSTGRES_USER", "bh"),
        password=os.environ.get("POSTGRES_PASSWORD", "bh_local_dev"),  # pragma: allowlist secret
        dbname=os.environ.get("POSTGRES_DATABASE", "bh_warehouse"),
    )


def _issuer_id(i: int) -> str:
    return f"ISS-{i:04d}"


def _issuer_name(i: int) -> str:
    return f"Synthetic Issuer {i:04d}"


def seed(reset: bool) -> None:
    rng = random.Random(SEED)
    conn = _connect()
    conn.autocommit = False
    cur = conn.cursor()

    tables = [
        "gold.mart_weekly_exposure_delta",
        "gold.mart_issuer_risk_summary",
        "gold.mart_daily_portfolio_exposure",
        "ref.watchlist",
        "ref.identifier_map",
        "ref.classification_codes",
        "ref.geo_codes",
    ]
    for t in tables:
        cur.execute(f"TRUNCATE TABLE {t}")

    # ── REF.geo_codes ─────────────────────────────────────────────────────────
    cur.executemany(
        "INSERT INTO ref.geo_codes (country_code, country_name, region, sub_region, longaeva_grouping) "
        "VALUES (%s,%s,%s,%s,%s)",
        [(c, n, r, r, f"DM_{r}") for c, n, r in COUNTRIES],
    )

    # ── REF.classification_codes ──────────────────────────────────────────────
    cur.executemany(
        "INSERT INTO ref.classification_codes (classification_id, classification_type, code, label, parent_id) "
        "VALUES (%s,%s,%s,%s,%s)",
        [(f"SEC-{s}", "SECTOR", s, s.title(), None) for s in SECTORS],
    )

    # ── REF.identifier_map (60 issuers) ───────────────────────────────────────
    issuers = []
    for i in range(N_ISSUERS):
        country = rng.choice(COUNTRIES)[0]
        sector = rng.choice(SECTORS)
        issuers.append((_issuer_id(i), _issuer_name(i), country, sector))
    cur.executemany(
        "INSERT INTO ref.identifier_map "
        "(internal_issuer_id, lei, figi, cusip, isin, issuer_name, issuer_cohort, "
        " primary_country, primary_sector, is_active, effective_from, effective_to) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        [
            (
                iid,
                f"LEI{idx:017d}",
                f"BBG{idx:09d}",
                f"{idx:09d}",
                f"US{idx:010d}",
                name,
                "COHORT_A",
                country,
                sector,
                True,
                date(2024, 1, 1),
                None,  # effective_to 100% null — mirrors the real sandbox flag
            )
            for idx, (iid, name, country, sector) in enumerate(issuers)
        ],
    )

    # ── REF.watchlist (~18, severity mix matching the sandbox ratio) ──────────
    wl_rows = []
    wl_issuers = rng.sample(range(N_ISSUERS), 18)
    # ratio ~ 6 critical : 19 elevated : 35 monitor → scaled to 18: 3:6:9
    sev_plan = (["critical"] * 3) + (["elevated"] * 6) + (["monitor"] * 9)
    for sev, i in zip(sev_plan, wl_issuers):
        reason = rng.choice(WATCHLIST_REASONS[sev])
        wl_rows.append(
            (_issuer_id(i), _issuer_name(i), reason, sev, date(2026, 5, 1), "risk-team")
        )
    cur.executemany(
        "INSERT INTO ref.watchlist "
        "(internal_issuer_id, issuer_name, watchlist_reason, severity, added_date, added_by) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        wl_rows,
    )

    # ── GOLD.mart_daily_portfolio_exposure ────────────────────────────────────
    dates = [LATEST_DATE - timedelta(days=7 * k) for k in range(N_DATES)][::-1]
    issuer_meta = {iid: (country, sector) for iid, _, country, sector in issuers}
    dpe_rows = []
    for d in dates:
        for p in range(N_PORTFOLIOS):
            portfolio_id = f"P-{p:03d}"
            held = rng.sample(range(N_ISSUERS), rng.randint(10, 14))
            for i in held:
                iid = _issuer_id(i)
                country, sector = issuer_meta[iid]
                instrument_id = f"INSTR-{i:04d}"
                exposure = round(rng.uniform(200_000, 1_750_000), 2)
                dpe_rows.append(
                    (
                        d,
                        portfolio_id,
                        iid,
                        instrument_id,
                        country,
                        sector,
                        rng.choice(ASSET_CLASSES),
                        "COHORT_A-FY2026-Q2",
                        exposure,
                        1,
                        round(rng.uniform(0.5, 8.0), 6),
                    )
                )
    cur.executemany(
        "INSERT INTO gold.mart_daily_portfolio_exposure "
        "(as_of_date, portfolio_id, internal_issuer_id, instrument_id, country_code, "
        " sector_code, asset_class_code, fiscal_period_id, exposure_amount_usd, "
        " position_count, weight_pct) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        dpe_rows,
    )

    # ── GOLD.mart_issuer_risk_summary ─────────────────────────────────────────
    irs_rows = []
    for d in dates:
        for i in range(N_ISSUERS):
            iid = _issuer_id(i)
            country, sector = issuer_meta[iid]
            irs_rows.append(
                (
                    d,
                    iid,
                    country,
                    sector,
                    rng.choice(ASSET_CLASSES),
                    round(rng.uniform(1_000_000, 9_000_000), 2),
                    round(rng.uniform(50_000, 500_000), 2),
                    round(rng.uniform(1.0, 10.0), 2),
                )
            )
    cur.executemany(
        "INSERT INTO gold.mart_issuer_risk_summary "
        "(as_of_date, internal_issuer_id, country_code, sector_code, asset_class_code, "
        " total_exposure_usd, var_95_1d, avg_credit_rating_num) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        irs_rows,
    )

    # ── GOLD.mart_weekly_exposure_delta ───────────────────────────────────────
    geo_name = {c: n for c, n, _ in COUNTRIES}
    wd_rows = []
    for p in range(N_PORTFOLIOS):
        portfolio_id = f"P-{p:03d}"
        movers = rng.sample(range(N_ISSUERS), 12)
        for i in movers:
            iid = _issuer_id(i)
            country, sector = issuer_meta[iid]
            today = round(rng.uniform(200_000, 1_500_000), 2)
            prior = round(rng.uniform(200_000, 1_500_000), 2)
            delta = round(today - prior, 2)
            pct = round((delta / prior * 100) if prior else 0.0, 4)
            change = "increased" if delta > 0 else "decreased"
            wd_rows.append(
                (
                    portfolio_id,
                    iid,
                    _issuer_name(i),
                    sector,
                    country,
                    geo_name[country],
                    today,
                    prior,
                    delta,
                    pct,
                    change,
                    LATEST_DATE,
                )
            )
    cur.executemany(
        "INSERT INTO gold.mart_weekly_exposure_delta "
        "(portfolio_id, internal_issuer_id, issuer_name, sector_code, country_code, "
        " country_name, exposure_today_usd, exposure_7d_ago_usd, delta_usd, delta_pct, "
        " change_type, as_of_date) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        wd_rows,
    )

    conn.commit()

    # ── Report ────────────────────────────────────────────────────────────────
    for t in [
        "ref.geo_codes",
        "ref.classification_codes",
        "ref.identifier_map",
        "ref.watchlist",
        "gold.mart_daily_portfolio_exposure",
        "gold.mart_issuer_risk_summary",
        "gold.mart_weekly_exposure_delta",
    ]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t:42s} {cur.fetchone()[0]:>7d} rows")
    cur.close()
    conn.close()
    print(f"[seed] done (deterministic seed={SEED}, latest_date={LATEST_DATE})")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
