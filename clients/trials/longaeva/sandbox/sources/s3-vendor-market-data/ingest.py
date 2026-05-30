"""Source Type 1 — S3 vendor bucket ingestion (internal-stage stand-in).

Demonstrates the full ingestion lifecycle the Brighthive Ingestion Agent must
scaffold for Longaeva:

  1. generate daily-partitioned CSV drops + a completion.flag sentinel
  2. PUT them to the BRONZE internal stage (stands in for the S3 external stage)
  3. completion-file detection — only COPY INTO once completion.flag is present
  4. lookback window — re-scan the last N days for late files
  5. COPY INTO raw_market_prices with file + batch lineage

Run:
  uv run --with snowflake-connector-python python ingest.py --generate --days 3
  uv run --with snowflake-connector-python python ingest.py --load --lookback 7

Idempotent: COPY INTO skips files already loaded (Snowflake load metadata).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
import sys
import tempfile
import tomllib
from pathlib import Path

import snowflake.connector

STAGE = "LONGAEVA_POC.BRONZE.s3_vendor_market_data"
TABLE = "LONGAEVA_POC.BRONZE.raw_market_prices"
ASOF = dt.date(2026, 5, 29)
CSV_HEADER = [
    "vendor_security_id", "ticker", "price_date", "open_price", "high_price",
    "low_price", "close_price", "adj_close_price", "volume", "currency",
]


def connect(connection: str):
    cfg_path = Path.home() / ".snowflake" / "config.toml"
    with cfg_path.open("rb") as f:
        c = tomllib.load(f)["connections"][connection]
    return snowflake.connector.connect(
        account=c["account"], user=c["user"], password=c["password"],
        role=c.get("role"), warehouse=c.get("warehouse"),
        database=c.get("database"), schema="BRONZE",
    )


def partition_path(d: dt.date) -> str:
    return f"yyyy={d.year:04d}/mm={d.month:02d}/dd={d.day:02d}"


def generate_drops(out_dir: Path, days: int) -> list[Path]:
    """Write `days` daily CSV files + a completion.flag per day."""
    rng = random.Random(42)
    written = []
    for offset in range(days):
        d = ASOF - dt.timedelta(days=offset)
        day_dir = out_dir / partition_path(d)
        day_dir.mkdir(parents=True, exist_ok=True)
        csv_path = day_dir / f"market_prices_{d.isoformat()}_001.csv"
        with csv_path.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(CSV_HEADER)
            for i in range(50):  # 50 instruments per file
                base = rng.uniform(50, 500)
                w.writerow([
                    f"VEND-{i:04d}", f"TK{i:04d}", d.isoformat(),
                    round(base, 4), round(base * 1.02, 4), round(base * 0.98, 4),
                    round(base * 1.005, 4), round(base * 1.005, 4),
                    rng.randint(10_000, 5_000_000), "USD",
                ])
        (day_dir / "completion.flag").write_text(f"complete:{d.isoformat()}\n")
        written.append(csv_path)
    return written


def put_files(conn, local_dir: Path) -> int:
    """PUT every file under local_dir to the stage, preserving partition path."""
    cur = conn.cursor()
    n = 0
    for path in sorted(local_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(local_dir).parent.as_posix()
            stage_target = f"@{STAGE}/{rel}/" if rel != "." else f"@{STAGE}/"
            # AUTO_COMPRESS adds .gz; OVERWRITE keeps reruns clean
            cur.execute(
                f"PUT 'file://{path}' '{stage_target}' "
                f"AUTO_COMPRESS=TRUE OVERWRITE=TRUE"
            )
            n += 1
    return n


def list_partitions_with_completion(conn, lookback: int) -> list[str]:
    """Return partition paths from the last `lookback` days that have completion.flag."""
    cur = conn.cursor()
    ready = []
    for offset in range(lookback):
        d = ASOF - dt.timedelta(days=offset)
        part = partition_path(d)
        cur.execute(f"LIST '@{STAGE}/{part}/'")
        files = [row[0] for row in cur.fetchall()]
        has_flag = any("completion.flag" in f for f in files)
        has_csv = any("market_prices" in f for f in files)
        if has_flag and has_csv:
            ready.append(part)
        elif has_csv and not has_flag:
            print(f"  skip {part}: csv present but no completion.flag", file=sys.stderr)
    return ready


def copy_into(conn, partitions: list[str]) -> int:
    """COPY INTO raw_market_prices for each ready partition."""
    cur = conn.cursor()
    total = 0
    for part in partitions:
        cur.execute(f"""
            COPY INTO {TABLE}
              (vendor_security_id, ticker, price_date, open_price, high_price,
               low_price, close_price, adj_close_price, volume, currency,
               source_file, source_batch_id)
            FROM (
              SELECT
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                METADATA$FILENAME, '{part}'
              FROM '@{STAGE}/{part}/'
            )
            FILE_FORMAT = (FORMAT_NAME = 'LONGAEVA_POC.BRONZE.ff_csv_vendor')
            PATTERN = '.*market_prices.*\\.csv\\.gz'
            ON_ERROR = 'ABORT_STATEMENT'
        """)
        rows = cur.fetchall()
        loaded = sum(int(r[2]) for r in rows if len(r) > 2 and str(r[2]).isdigit())
        print(f"  loaded {part}: {loaded} rows", file=sys.stderr)
        total += loaded
    return total


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--connection", default="brighthive")
    ap.add_argument("--generate", action="store_true", help="Generate + PUT sample drops")
    ap.add_argument("--load", action="store_true", help="Detect completion + COPY INTO")
    ap.add_argument("--days", type=int, default=3, help="How many daily drops to generate")
    ap.add_argument("--lookback", type=int, default=7, help="Lookback window for late files")
    args = ap.parse_args()

    if not (args.generate or args.load):
        ap.error("pass --generate and/or --load")

    conn = connect(args.connection)

    if args.generate:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            files = generate_drops(tmp_dir, args.days)
            print(f"generated {len(files)} daily CSV drops + completion flags",
                  file=sys.stderr)
            n = put_files(conn, tmp_dir)
            print(f"PUT {n} files to @{STAGE}", file=sys.stderr)

    if args.load:
        ready = list_partitions_with_completion(conn, args.lookback)
        print(f"{len(ready)} partitions ready (completion.flag present)",
              file=sys.stderr)
        total = copy_into(conn, ready)
        print(f"total rows loaded: {total}", file=sys.stderr)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
