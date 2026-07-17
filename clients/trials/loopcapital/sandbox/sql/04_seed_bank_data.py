#!/usr/bin/env python3
"""Seed the synthetic bank data model for the Loop Capital sandbox (BH-1036).

Seeds:
- 10 securities (equities, fixed income, cash)
- 90 days of daily market prices (~900 rows)
- 30 days of raw positions across 3 portfolios (~480 rows)
- Staging holdings + daily P&L
- Gold-tier daily portfolio exposure mart
- 1 real compliance breach (PORT-001-GROWTH over 20% single-security concentration)

Usage:
    MSSQL_HOST=54.197.188.168 MSSQL_SA_PASSWORD=LoopCapitalDemoSA2026Aa1 python3 04_seed_bank_data.py
    # or run reset.py --scenario baseline (which calls this)
"""

from __future__ import annotations

import datetime
import os
import random
import sys

try:
    import pymssql
except ImportError:
    print("pymssql required: pip install pymssql")
    sys.exit(1)

HOST = os.environ.get("MSSQL_HOST", "localhost")
SA_PASS = os.environ.get("MSSQL_SA_PASSWORD", "")
if not SA_PASS:
    raise SystemExit("MSSQL_SA_PASSWORD must be set")

conn = pymssql.connect(HOST, "sa", SA_PASS, "LoopCapitalAM", port=1433, timeout=60)
conn.autocommit(True)
cur = conn.cursor()

SECURITIES = [
    ("AAPL", "037833100", "US0378331005", "AAPL", "Apple Inc", "EQUITY", "Technology", "US", "USD"),
    ("MSFT", "594918104", "US5949181045", "MSFT", "Microsoft Corp", "EQUITY", "Technology", "US", "USD"),
    ("JPM",  "46625H100", "US46625H1005", "JPM",  "JPMorgan Chase", "EQUITY", "Financials", "US", "USD"),
    ("GS",   "38141G104", "US38141G1040", "GS",   "Goldman Sachs", "EQUITY", "Financials", "US", "USD"),
    ("TLT",  "464287440", "US4642874402", "TLT",  "iShares 20+ Year Treasury", "FIXED_INCOME", "Government", "US", "USD"),
    ("LQD",  "464287622", "US4642876225", "LQD",  "iShares IG Corporate Bond", "FIXED_INCOME", "Corporate", "US", "USD"),
    ("AMZN", "023135106", "US0231351067", "AMZN", "Amazon.com Inc", "EQUITY", "Consumer Discretionary", "US", "USD"),
    ("NVDA", "67066G104", "US67066G1040", "NVDA", "NVIDIA Corp", "EQUITY", "Technology", "US", "USD"),
    ("CASH_USD", None, None, "CASH", "USD Cash", "CASH", "Cash", "US", "USD"),
    ("USB_T3M", None, None, "TBILL", "US Treasury 3-Month", "FIXED_INCOME", "Government", "US", "USD"),
]

BASE_PRICES = {
    "AAPL": 185, "MSFT": 415, "JPM": 210, "GS": 520,
    "TLT": 88, "LQD": 107, "AMZN": 205, "NVDA": 875,
    "CASH_USD": 1, "USB_T3M": 98,
}

PORTFOLIOS = {
    "PORT-001-GROWTH": [("AAPL", 1500), ("NVDA", 800), ("MSFT", 1200), ("AMZN", 600), ("CASH_USD", 500000)],
    "PORT-002-INCOME": [("TLT", 5000), ("LQD", 8000), ("JPM", 2000), ("GS", 500), ("USB_T3M", 3000)],
    "PORT-003-BALANCED": [("AAPL", 700), ("MSFT", 600), ("TLT", 2500), ("LQD", 3000), ("JPM", 900), ("CASH_USD", 200000)],
}

SEC_META = {s[0]: s for s in SECURITIES}
today = datetime.date.today()

# Security master
for s in SECURITIES:
    cur.execute(
        "IF NOT EXISTS (SELECT 1 FROM raw_security_master WHERE security_id=%s) "
        "INSERT INTO raw_security_master (security_id,cusip,isin,ticker,security_name,asset_class,sector,country,currency) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (s[0],) + s,
    )
print("Securities OK")

# 90 days of prices
for d in range(90, 0, -1):
    dt = today - datetime.timedelta(days=d)
    for sec_id, base in BASE_PRICES.items():
        px = round(base * (1 + random.uniform(-0.012, 0.012)), 4)
        cur.execute("INSERT INTO raw_market_prices (security_id,price_date,close_price) VALUES (%s,%s,%s)", (sec_id, dt, px))
print("Prices OK")

# 30 days of raw positions
for d in range(30, 0, -1):
    dt = today - datetime.timedelta(days=d)
    for port, positions in PORTFOLIOS.items():
        for sec_id, qty in positions:
            mv = round(qty * BASE_PRICES[sec_id] * random.uniform(0.99, 1.01), 2)
            cur.execute(
                "INSERT INTO raw_positions (portfolio_id,security_id,quantity,market_value,currency,as_of_date) VALUES (%s,%s,%s,%s,'USD',%s)",
                (port, sec_id, qty, mv, dt),
            )
print("Raw positions OK")

# Clear and re-seed staging/gold
cur.execute("DELETE FROM holdings_raw")
cur.execute("DELETE FROM stg_holdings")
cur.execute("DELETE FROM stg_positions")
cur.execute("DELETE FROM mart_daily_portfolio_exposure")
cur.execute("DELETE FROM mart_compliance_breaches")

for port, positions in PORTFOLIOS.items():
    total_mv = sum(qty * BASE_PRICES[sec_id] for sec_id, qty in positions)
    for sec_id, qty in positions:
        mv = round(qty * BASE_PRICES[sec_id], 2)
        weight = round(mv / total_mv * 100, 4) if total_mv else 0
        sec = SEC_META[sec_id]
        cur.execute(
            "INSERT INTO holdings_raw (portfolio_id,instrument_id,quantity,as_of_date) VALUES (%s,%s,%s,%s)",
            (port, sec_id, qty, today),
        )
        cur.execute(
            "INSERT INTO stg_holdings (portfolio_id,instrument_id,security_name,quantity,market_value_usd,weight_pct,as_of_date,settlement_ccy) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,'USD')",
            (port, sec_id, sec[4], qty, mv, weight, today),
        )
    equity = sum(qty * BASE_PRICES[s] for s, qty in positions if SEC_META[s][5] == "EQUITY")
    fi = sum(qty * BASE_PRICES[s] for s, qty in positions if SEC_META[s][5] == "FIXED_INCOME")
    cash = sum(qty * BASE_PRICES[s] for s, qty in positions if SEC_META[s][5] == "CASH")
    cur.execute(
        "INSERT INTO mart_daily_portfolio_exposure (portfolio_id,as_of_date,total_market_value,equity_exposure,fixed_income_exposure,cash_exposure,num_positions) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (port, today, round(equity+fi+cash,2), round(equity,2), round(fi,2), round(cash,2), len(positions)),
    )

# Plant a real compliance breach for GC-14/15 monitoring demo
cur.execute(
    "INSERT INTO mart_compliance_breaches (portfolio_id,rule_name,breach_type,limit_value,actual_value,breach_pct,as_of_date,severity) "
    "VALUES ('PORT-001-GROWTH','Single Security Concentration 20%','CONCENTRATION',20.00,28.47,8.47,%s,'CRITICAL')",
    (today,),
)
print("Staging + gold + compliance breach OK")
conn.close()
print("ALL DONE")
