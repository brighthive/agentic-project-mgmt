"""Source Type 2 — REST API ingestion loader.

The production pattern Grant described: fetch the ID universe, chunk into
batches, download in parallel with retry, write to the data lake, load to
Snowflake. Here we fetch from the local FastAPI stub and load
BRONZE.raw_rest_holdings directly.

Run (stub must be up on :8000):
  uv run --with httpx --with snowflake-connector-python python ingest.py \\
    --as-of-date 2026-05-29 --max-ids 2000

`--max-ids` caps the universe slice for a fast demo; omit for the full 25k.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import sys
import tomllib
from pathlib import Path

import httpx
import snowflake.connector

BASE_URL = "http://localhost:8000"
CHUNK = 500
TABLE = "LONGAEVA_POC.BRONZE.raw_rest_holdings"


def connect(connection: str):
    cfg_path = Path.home() / ".snowflake" / "config.toml"
    with cfg_path.open("rb") as f:
        c = tomllib.load(f)["connections"][connection]
    return snowflake.connector.connect(
        account=c["account"], user=c["user"], password=c["password"],
        role=c.get("role"), warehouse=c.get("warehouse"),
        database=c.get("database"), schema="BRONZE",
    )


def fetch_universe(client: httpx.Client, max_ids: int | None) -> list[str]:
    ids, page = [], 1
    while True:
        r = _get_with_retry(client, "/v1/instruments", {"page": page, "page_size": 5000})
        batch = [row["instrument_id"] for row in r["data"]]
        ids.extend(batch)
        if max_ids and len(ids) >= max_ids:
            return ids[:max_ids]
        if r["next_cursor"] is None:
            return ids
        page = r["next_cursor"]


def _get_with_retry(client: httpx.Client, path: str, params: dict, retries: int = 3) -> dict:
    last_exc = None
    for attempt in range(retries):
        try:
            resp = client.get(path, params=params, timeout=30.0)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError,) as exc:  # noqa: PERF203
            last_exc = exc
    raise RuntimeError(f"GET {path} failed after {retries} retries: {last_exc}")


def fetch_chunk(as_of_date: str, id_chunk: list[str]) -> list[dict]:
    """Fetch all pages of holdings for one ID chunk."""
    out, page = [], 1
    with httpx.Client(base_url=BASE_URL) as client:
        while True:
            r = _get_with_retry(client, "/v1/holdings", {
                "as_of_date": as_of_date,
                "ids": ",".join(id_chunk),
                "page": page,
                "page_size": 500,
            })
            for row in r["data"]:
                out.append((row, page))
            if r["next_cursor"] is None:
                return out
            page = r["next_cursor"]


def load_rows(conn, rows: list[tuple[dict, int]]) -> int:
    if not rows:
        return 0
    cur = conn.cursor()
    payload = [
        (
            row["portfolio_id"], row["instrument_id"], row["as_of_date"],
            row["quantity"], row["market_value"], row["currency"],
            "/v1/holdings", page, f"api-{row['as_of_date']}-p{page}",
        )
        for row, page in rows
    ]
    cur.executemany(
        f"""INSERT INTO {TABLE}
            (portfolio_id, instrument_id, as_of_date, quantity, market_value,
             currency, api_endpoint, page_number, api_response_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        payload,
    )
    return len(payload)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--connection", default="brighthive")
    ap.add_argument("--as-of-date", default="2026-05-29")
    ap.add_argument("--max-ids", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--truncate", action="store_true")
    args = ap.parse_args()

    with httpx.Client(base_url=BASE_URL) as client:
        try:
            health = client.get("/healthz", timeout=5.0).json()
        except httpx.HTTPError:
            print("error: REST stub not reachable on :8000. Start it first:\n"
                  "  uv run --with 'fastapi[standard]' fastapi dev main.py",
                  file=sys.stderr)
            return 1
        print(f"stub healthy, universe={health['universe_size']}", file=sys.stderr)
        universe = fetch_universe(client, args.max_ids)

    chunks = [universe[i:i + CHUNK] for i in range(0, len(universe), CHUNK)]
    print(f"universe sliced into {len(chunks)} chunks of <= {CHUNK} ids",
          file=sys.stderr)

    conn = connect(args.connection)
    if args.truncate:
        conn.cursor().execute(f"TRUNCATE TABLE {TABLE}")
        print("truncated raw_rest_holdings", file=sys.stderr)

    total = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch_chunk, args.as_of_date, c) for c in chunks]
        for fut in concurrent.futures.as_completed(futures):
            rows = fut.result()
            total += load_rows(conn, rows)

    print(f"loaded {total} holdings rows for {args.as_of_date}", file=sys.stderr)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
