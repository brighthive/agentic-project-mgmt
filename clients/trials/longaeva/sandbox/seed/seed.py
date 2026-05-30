"""Synthetic seed data for the Longaeva POC sandbox.

Generates a ~1y, multi-portfolio, multi-issuer dataset large enough to exercise
the semantic view, baseline_expectations, and longitudinal monitoring paths
without spending real money on warehouse compute.

Volumes (deterministic, seeded):
  REF.geo_codes                   ~25 rows
  REF.classification_codes        ~30 rows
  REF.fiscal_calendar             24 rows  (2 cohorts x 3 FY x 4 Q)
  REF.identifier_map              200 issuers
  SILVER.stg_security_prices      ~50k rows  (200 instruments x ~252 trading days)
  SILVER.stg_holdings_snapshot    ~190k rows (30 portfolios x 252 days x ~25 holdings)
  SILVER.stg_corporate_actions    100 rows
  GOLD.mart_daily_portfolio_exposure  ~190k rows  (mirrors stg_holdings_snapshot)
  GOLD.mart_issuer_risk_summary       ~50k rows  (200 issuers x 252 days)

Run:
  uv run --with 'snowflake-connector-python[pandas]' --with pandas --with numpy \\
    python seed.py [--connection brighthive] [--reset]

`--reset` truncates target tables before loading. Idempotent without `--reset`
because we use REPLACE-on-key inserts (pk-aware).
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

RNG_SEED = 42
ASOF_END = dt.date(2026, 5, 30)
DAYS = 252  # 1 trading year
N_ISSUERS = 200
N_PORTFOLIOS = 30
HOLDINGS_PER_PORT_PER_DAY = (15, 35)  # uniform range
N_CORP_ACTIONS = 100

REGIONS = {
    "AMERICAS": ["USA", "CAN", "MEX", "BRA", "ARG"],
    "EMEA":     ["GBR", "DEU", "FRA", "CHE", "ESP", "ITA", "NLD", "SWE", "POL"],
    "APAC":     ["JPN", "AUS", "SGP", "HKG", "CHN", "IND", "KOR"],
    "AFRICA":   ["ZAF", "NGA", "EGY", "KEN"],
}
COUNTRY_NAMES = {
    "USA": "United States", "CAN": "Canada", "MEX": "Mexico", "BRA": "Brazil",
    "ARG": "Argentina", "GBR": "United Kingdom", "DEU": "Germany",
    "FRA": "France", "CHE": "Switzerland", "ESP": "Spain", "ITA": "Italy",
    "NLD": "Netherlands", "SWE": "Sweden", "POL": "Poland", "JPN": "Japan",
    "AUS": "Australia", "SGP": "Singapore", "HKG": "Hong Kong",
    "CHN": "China", "IND": "India", "KOR": "South Korea",
    "ZAF": "South Africa", "NGA": "Nigeria", "EGY": "Egypt", "KEN": "Kenya",
}
LONGAEVA_GROUPING = {
    **{c: "DM_AMERICAS" for c in ["USA", "CAN"]},
    **{c: "EM_AMERICAS" for c in ["MEX", "BRA", "ARG"]},
    **{c: "DM_EMEA" for c in ["GBR", "DEU", "FRA", "CHE", "ESP", "ITA", "NLD", "SWE"]},
    **{c: "EM_EMEA" for c in ["POL"]},
    **{c: "DM_APAC" for c in ["JPN", "AUS", "SGP", "HKG"]},
    **{c: "EM_APAC" for c in ["CHN", "IND", "KOR"]},
    **{c: "EM_AFRICA" for c in ["ZAF", "NGA", "EGY", "KEN"]},
}

SECTORS = ["TECH", "FINS", "ENRG", "HLTH", "CONS", "INDU", "UTIL", "MATR", "REAL", "COMM"]
ASSET_CLASSES = ["EQUITY", "BOND", "FX", "DERIV"]


# -----------------------------------------------------------------------------
# Generators
# -----------------------------------------------------------------------------

def gen_geo_codes() -> pd.DataFrame:
    rows = []
    for region, countries in REGIONS.items():
        sub = "DEVELOPED" if not any(c in LONGAEVA_GROUPING and LONGAEVA_GROUPING[c].startswith("EM_") for c in countries) else "MIXED"
        for c in countries:
            rows.append({
                "COUNTRY_CODE": c,
                "COUNTRY_NAME": COUNTRY_NAMES[c],
                "REGION": region,
                "SUB_REGION": sub,
                "LONGAEVA_GROUPING": LONGAEVA_GROUPING[c],
            })
    return pd.DataFrame(rows)


def gen_classification_codes() -> pd.DataFrame:
    rows = []
    for s in SECTORS:
        rows.append({
            "CLASSIFICATION_ID": f"SEC_{s}",
            "CLASSIFICATION_TYPE": "SECTOR",
            "CODE": s,
            "LABEL": s.title(),
            "PARENT_ID": None,
        })
    for a in ASSET_CLASSES:
        rows.append({
            "CLASSIFICATION_ID": f"AC_{a}",
            "CLASSIFICATION_TYPE": "ASSET_CLASS",
            "CODE": a,
            "LABEL": a.title(),
            "PARENT_ID": None,
        })
    return pd.DataFrame(rows)


def gen_fiscal_calendar() -> pd.DataFrame:
    """Two cohorts: CALENDAR (Jan-Dec) and NONCAL (Apr-Mar). Three FY each."""
    rows = []
    for fy in (2024, 2025, 2026):
        for q in (1, 2, 3, 4):
            # Calendar cohort: FY = calendar year
            cal_start = dt.date(fy, 3 * (q - 1) + 1, 1)
            cal_end = (
                dt.date(fy, 3 * q + 1, 1) if q < 4 else dt.date(fy + 1, 1, 1)
            ) - dt.timedelta(days=1)
            rows.append({
                "FISCAL_PERIOD_ID": f"CALENDAR-FY{fy}-Q{q}",
                "ISSUER_COHORT": "CALENDAR",
                "FISCAL_YEAR": fy,
                "FISCAL_QUARTER": q,
                "PERIOD_START_DATE": cal_start,
                "PERIOD_END_DATE": cal_end,
                "IS_CURRENT": cal_start <= ASOF_END <= cal_end,
            })
            # NONCAL cohort: FY runs Apr-Mar; NONCAL FY2026 = Apr 2025 - Mar 2026
            nc_start_month = 4 + 3 * (q - 1)
            nc_start_year = fy - 1 if nc_start_month <= 12 else fy
            nc_start_month = nc_start_month if nc_start_month <= 12 else nc_start_month - 12
            nc_start = dt.date(nc_start_year, nc_start_month, 1)

            nc_end_month_exclusive = 4 + 3 * q
            nc_end_year_exclusive = fy - 1 if nc_end_month_exclusive <= 12 else fy
            nc_end_month_exclusive = nc_end_month_exclusive if nc_end_month_exclusive <= 12 else nc_end_month_exclusive - 12
            nc_end = dt.date(nc_end_year_exclusive, nc_end_month_exclusive, 1) - dt.timedelta(days=1)
            rows.append({
                "FISCAL_PERIOD_ID": f"NONCAL-FY{fy}-Q{q}",
                "ISSUER_COHORT": "NONCAL",
                "FISCAL_YEAR": fy,
                "FISCAL_QUARTER": q,
                "PERIOD_START_DATE": nc_start,
                "PERIOD_END_DATE": nc_end,
                "IS_CURRENT": nc_start <= ASOF_END <= nc_end,
            })
    return pd.DataFrame(rows)


def gen_identifier_map(rng: np.random.Generator) -> pd.DataFrame:
    countries = list(LONGAEVA_GROUPING.keys())
    rows = []
    for i in range(N_ISSUERS):
        cohort = "CALENDAR" if i % 3 != 0 else "NONCAL"  # ~1/3 non-calendar
        country = countries[i % len(countries)]
        sector = SECTORS[i % len(SECTORS)]
        rows.append({
            "INTERNAL_ISSUER_ID": f"ISS-{i:04d}",
            "LEI": f"LEI{i:017d}".upper()[:20],
            "FIGI": f"BBG{i:09d}".upper()[:12],
            "CUSIP": f"C{i:08d}"[:9],
            "ISIN": f"{country[:2]}{i:010d}"[:12],
            "ISSUER_NAME": f"Synthetic Issuer {i:04d}",
            "ISSUER_COHORT": cohort,
            "PRIMARY_COUNTRY": country,
            "PRIMARY_SECTOR": sector,
            "IS_ACTIVE": True,
            "EFFECTIVE_FROM": dt.date(2020, 1, 1),
            "EFFECTIVE_TO": None,
        })
    return pd.DataFrame(rows)


def trading_days(end: dt.date, n: int) -> list[dt.date]:
    """Return n business days ending at `end`."""
    out = []
    d = end
    while len(out) < n:
        if d.weekday() < 5:  # Mon-Fri
            out.append(d)
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def gen_security_prices(rng: np.random.Generator, identifier_map: pd.DataFrame, days: list[dt.date]) -> pd.DataFrame:
    """Random walk per issuer: close prices around 100, ~1% daily vol."""
    n_issuers = len(identifier_map)
    n_days = len(days)
    log_returns = rng.normal(loc=0.0003, scale=0.012, size=(n_issuers, n_days))
    prices = 100.0 * np.exp(np.cumsum(log_returns, axis=1))
    rows = []
    for issuer_idx, issuer in enumerate(identifier_map.itertuples()):
        for day_idx, d in enumerate(days):
            rows.append({
                "INTERNAL_ISSUER_ID": issuer.INTERNAL_ISSUER_ID,
                "INSTRUMENT_ID": f"INSTR-{issuer_idx:04d}",
                "METRIC_NAME": "close_price",
                "TS": d,
                "VALUE": round(float(prices[issuer_idx, day_idx]), 6),
                "CURRENCY": "USD",
                "SOURCE_SYSTEM": "synthetic_v1",
                "AS_OF_TIME": dt.datetime.combine(d, dt.time(20, 0)),
                "QUALITY_FLAG": "OK",
            })
    return pd.DataFrame(rows)


def gen_holdings_and_exposure(
    rng: np.random.Generator,
    identifier_map: pd.DataFrame,
    fiscal_calendar: pd.DataFrame,
    days: list[dt.date],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Holdings + parallel exposure mart. Each portfolio holds 15-35 instruments."""
    issuers = identifier_map.set_index("INTERNAL_ISSUER_ID")

    def fiscal_period_for(cohort: str, d: dt.date) -> str:
        cal = fiscal_calendar[
            (fiscal_calendar["ISSUER_COHORT"] == cohort)
            & (fiscal_calendar["PERIOD_START_DATE"] <= d)
            & (fiscal_calendar["PERIOD_END_DATE"] >= d)
        ]
        return cal["FISCAL_PERIOD_ID"].iloc[0] if len(cal) else None

    holdings_rows = []
    exposure_rows = []

    portfolios = [f"P-{p:03d}" for p in range(N_PORTFOLIOS)]

    # Per portfolio, fix a stable instrument set to make the data look real
    portfolio_holdings_template: dict[str, list[str]] = {}
    for p in portfolios:
        n = rng.integers(*HOLDINGS_PER_PORT_PER_DAY)
        chosen = rng.choice(identifier_map["INTERNAL_ISSUER_ID"].values, size=n, replace=False)
        portfolio_holdings_template[p] = list(chosen)

    for d in days:
        for p, instruments in portfolio_holdings_template.items():
            # Drift exposure ~ N(1M, 200k) per holding, weights normalize to ~1
            raw_amounts = rng.normal(loc=1_000_000, scale=200_000, size=len(instruments))
            raw_amounts = np.clip(raw_amounts, 50_000, None)
            total = raw_amounts.sum()
            for instr_idx, internal_issuer_id in enumerate(instruments):
                amount = float(raw_amounts[instr_idx])
                weight = amount / total
                row = issuers.loc[internal_issuer_id]
                country = row["PRIMARY_COUNTRY"]
                sector = row["PRIMARY_SECTOR"]
                cohort = row["ISSUER_COHORT"]
                instr_id = f"INSTR-{int(internal_issuer_id.split('-')[1]):04d}"
                fp_id = fiscal_period_for(cohort, d)

                holdings_rows.append({
                    "PORTFOLIO_ID": p,
                    "INTERNAL_ISSUER_ID": internal_issuer_id,
                    "INSTRUMENT_ID": instr_id,
                    "AS_OF_DATE": d,
                    "QUANTITY": round(amount / 100.0, 6),  # synthetic quantity
                    "MARKET_VALUE_LOCAL": round(amount, 2),
                    "MARKET_VALUE_USD": round(amount, 2),
                    "CURRENCY": "USD",
                    "SOURCE_SYSTEM": "synthetic_v1",
                    "AS_OF_TIME": dt.datetime.combine(d, dt.time(20, 0)),
                    "QUALITY_FLAG": "OK",
                })
                exposure_rows.append({
                    "AS_OF_DATE": d,
                    "PORTFOLIO_ID": p,
                    "INTERNAL_ISSUER_ID": internal_issuer_id,
                    "INSTRUMENT_ID": instr_id,
                    "COUNTRY_CODE": country,
                    "SECTOR_CODE": sector,
                    "ASSET_CLASS_CODE": "EQUITY",
                    "FISCAL_PERIOD_ID": fp_id,
                    "EXPOSURE_AMOUNT_USD": round(amount, 2),
                    "POSITION_COUNT": 1,
                    "WEIGHT_PCT": round(float(weight), 6),
                })
    return pd.DataFrame(holdings_rows), pd.DataFrame(exposure_rows)


def gen_corporate_actions(rng: np.random.Generator, identifier_map: pd.DataFrame, days: list[dt.date]) -> pd.DataFrame:
    rows = []
    types = ["DIVIDEND", "SPLIT", "MERGER", "SPINOFF"]
    chosen_issuers = rng.choice(identifier_map["INTERNAL_ISSUER_ID"].values, size=N_CORP_ACTIONS, replace=True)
    for i, internal_issuer_id in enumerate(chosen_issuers):
        d = days[rng.integers(0, len(days))]
        action = types[i % len(types)]
        rows.append({
            "INTERNAL_ISSUER_ID": internal_issuer_id,
            "INSTRUMENT_ID": f"INSTR-{int(internal_issuer_id.split('-')[1]):04d}",
            "ACTION_TYPE": action,
            "EX_DATE": d,
            "RECORD_DATE": d + dt.timedelta(days=1),
            "PAY_DATE": d + dt.timedelta(days=14),
            "RATIO": 2.0 if action == "SPLIT" else None,
            "CASH_AMOUNT": round(float(rng.uniform(0.1, 5.0)), 4) if action == "DIVIDEND" else None,
            "CURRENCY": "USD",
            "SOURCE_SYSTEM": "synthetic_v1",
            "AS_OF_TIME": dt.datetime.combine(d, dt.time(20, 0)),
            "QUALITY_FLAG": "OK",
        })
    return pd.DataFrame(rows)


def gen_issuer_risk_summary(exposure: pd.DataFrame, identifier_map: pd.DataFrame) -> pd.DataFrame:
    """Roll up GOLD.mart_daily_portfolio_exposure to per-issuer-per-day."""
    issuers = identifier_map.set_index("INTERNAL_ISSUER_ID")
    grouped = (
        exposure.groupby(["AS_OF_DATE", "INTERNAL_ISSUER_ID"])
        .agg(TOTAL_EXPOSURE_USD=("EXPOSURE_AMOUNT_USD", "sum"))
        .reset_index()
    )
    grouped["COUNTRY_CODE"] = grouped["INTERNAL_ISSUER_ID"].map(issuers["PRIMARY_COUNTRY"])
    grouped["SECTOR_CODE"] = grouped["INTERNAL_ISSUER_ID"].map(issuers["PRIMARY_SECTOR"])
    grouped["ASSET_CLASS_CODE"] = "EQUITY"
    grouped["VAR_95_1D"] = (grouped["TOTAL_EXPOSURE_USD"] * 0.025).round(2)
    grouped["AVG_CREDIT_RATING_NUM"] = 12.0
    return grouped


# -----------------------------------------------------------------------------
# Loader
# -----------------------------------------------------------------------------

LOAD_TARGETS = [
    ("REF",    "GEO_CODES",                  "gen_geo_codes"),
    ("REF",    "CLASSIFICATION_CODES",       "gen_classification_codes"),
    ("REF",    "FISCAL_CALENDAR",            "gen_fiscal_calendar"),
    ("REF",    "IDENTIFIER_MAP",             "gen_identifier_map"),
    ("SILVER", "STG_SECURITY_PRICES",        "gen_security_prices"),
    ("SILVER", "STG_HOLDINGS_SNAPSHOT",      "gen_holdings_snapshot"),
    ("SILVER", "STG_CORPORATE_ACTIONS",      "gen_corporate_actions"),
    ("GOLD",   "MART_DAILY_PORTFOLIO_EXPOSURE", "gen_exposure"),
    ("GOLD",   "MART_ISSUER_RISK_SUMMARY",   "gen_issuer_risk_summary"),
]


def truncate_targets(conn) -> None:
    for schema, table, _ in LOAD_TARGETS:
        conn.cursor().execute(f"TRUNCATE TABLE LONGAEVA_POC.{schema}.{table}")
        print(f"  truncated LONGAEVA_POC.{schema}.{table}")


def load_df(conn, df: pd.DataFrame, schema: str, table: str) -> int:
    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name=table,
        database="LONGAEVA_POC",
        schema=schema,
        auto_create_table=False,
        overwrite=False,
        quote_identifiers=False,
    )
    if not success:
        raise RuntimeError(f"write_pandas failed for {schema}.{table}")
    return nrows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", default="brighthive")
    parser.add_argument("--reset", action="store_true", help="TRUNCATE targets before load")
    args = parser.parse_args()

    rng = np.random.default_rng(RNG_SEED)
    days = trading_days(ASOF_END, DAYS)
    print(f"Generating data for {len(days)} trading days "
          f"({days[0]} -> {days[-1]})...", file=sys.stderr)

    geo = gen_geo_codes()
    classification = gen_classification_codes()
    fiscal = gen_fiscal_calendar()
    identifier_map = gen_identifier_map(rng)
    print(f"  ref: geo={len(geo)} classification={len(classification)} "
          f"fiscal={len(fiscal)} identifier={len(identifier_map)}",
          file=sys.stderr)

    prices = gen_security_prices(rng, identifier_map, days)
    print(f"  prices: {len(prices):,} rows", file=sys.stderr)

    holdings, exposure = gen_holdings_and_exposure(rng, identifier_map, fiscal, days)
    print(f"  holdings: {len(holdings):,} rows, exposure: {len(exposure):,} rows",
          file=sys.stderr)

    corp_actions = gen_corporate_actions(rng, identifier_map, days)
    print(f"  corp_actions: {len(corp_actions)}", file=sys.stderr)

    risk = gen_issuer_risk_summary(exposure, identifier_map)
    print(f"  risk_summary: {len(risk):,} rows", file=sys.stderr)

    # Load via snowflake-connector + write_pandas. Read connection from CLI config.
    config_path = Path.home() / ".snowflake" / "config.toml"
    if not config_path.exists():
        print(f"error: {config_path} missing", file=sys.stderr)
        return 1

    import tomllib
    with config_path.open("rb") as f:
        cfg = tomllib.load(f)
    conn_cfg = cfg["connections"][args.connection]

    print(f"Connecting to {conn_cfg['account']} as {conn_cfg['user']}...",
          file=sys.stderr)
    conn = snowflake.connector.connect(
        account=conn_cfg["account"],
        user=conn_cfg["user"],
        password=conn_cfg["password"],
        role=conn_cfg.get("role"),
        warehouse=conn_cfg.get("warehouse"),
        database=conn_cfg.get("database"),
        schema=conn_cfg.get("schema"),
    )

    if args.reset:
        print("Truncating targets...", file=sys.stderr)
        truncate_targets(conn)

    plan = [
        ("REF",    "GEO_CODES",                       geo),
        ("REF",    "CLASSIFICATION_CODES",            classification),
        ("REF",    "FISCAL_CALENDAR",                 fiscal),
        ("REF",    "IDENTIFIER_MAP",                  identifier_map),
        ("SILVER", "STG_SECURITY_PRICES",             prices),
        ("SILVER", "STG_HOLDINGS_SNAPSHOT",           holdings),
        ("SILVER", "STG_CORPORATE_ACTIONS",           corp_actions),
        ("GOLD",   "MART_DAILY_PORTFOLIO_EXPOSURE",   exposure),
        ("GOLD",   "MART_ISSUER_RISK_SUMMARY",        risk),
    ]
    total = 0
    for schema, table, df in plan:
        nrows = load_df(conn, df, schema, table)
        print(f"  loaded {schema}.{table}: {nrows:,}", file=sys.stderr)
        total += nrows

    conn.close()
    print(f"Total rows loaded: {total:,}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
