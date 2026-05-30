"""Source Type 2 — paginated REST API stub.

Mimics a vendor holdings API: date-partitioned, paginated, batched ID lookups
against Longaeva's instrument universe. Deterministic responses (seeded by
as_of_date + id) so the ingestion loader's output is reproducible.

Run:
  uv run --with 'fastapi[standard]' --with uvicorn fastapi dev main.py
  # or: uv run --with fastapi --with uvicorn python -m uvicorn main:app --port 8000

Endpoints:
  GET /v1/instruments?page=N&page_size=M
      -> the security universe (paginated)
  GET /v1/holdings?as_of_date=YYYY-MM-DD&ids=ID1,ID2&page=N&page_size=M
      -> holdings for the requested ids on the date (paginated)
  GET /healthz
"""

from __future__ import annotations

import datetime as dt
import hashlib

from fastapi import FastAPI, Query, HTTPException

app = FastAPI(title="Longaeva Vendor API Stub", version="1.0.0")

UNIVERSE_SIZE = 25_000          # within Grant's 20-30k instrument universe
MAX_IDS_PER_CALL = 500
PORTFOLIOS = [f"P-{p:03d}" for p in range(30)]


def instrument_id(i: int) -> str:
    return f"VEND-{i:05d}"


def _seeded_float(*parts: str) -> float:
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


@app.get("/healthz")
def healthz():
    return {"status": "ok", "universe_size": UNIVERSE_SIZE}


@app.get("/v1/instruments")
def instruments(
    page: int = Query(1, ge=1),
    page_size: int = Query(1000, ge=1, le=5000),
):
    start = (page - 1) * page_size
    end = min(start + page_size, UNIVERSE_SIZE)
    if start >= UNIVERSE_SIZE:
        data = []
    else:
        data = [
            {"instrument_id": instrument_id(i), "is_active": True}
            for i in range(start, end)
        ]
    total_pages = (UNIVERSE_SIZE + page_size - 1) // page_size
    return {
        "data": data,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": UNIVERSE_SIZE,
        "next_cursor": page + 1 if page < total_pages else None,
    }


@app.get("/v1/holdings")
def holdings(
    as_of_date: str = Query(..., description="YYYY-MM-DD"),
    ids: str = Query(..., description="Comma-separated instrument ids (max 500)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=500),
):
    try:
        d = dt.date.fromisoformat(as_of_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of_date must be YYYY-MM-DD")

    id_list = [x for x in ids.split(",") if x]
    if len(id_list) > MAX_IDS_PER_CALL:
        raise HTTPException(
            status_code=422,
            detail=f"max {MAX_IDS_PER_CALL} ids per call, got {len(id_list)}",
        )

    # Build holdings: each instrument held by a deterministic subset of portfolios
    rows = []
    for iid in id_list:
        for p in PORTFOLIOS:
            if _seeded_float(as_of_date, iid, p) < 0.15:  # ~15% holding probability
                qty = round(_seeded_float(iid, p, "qty") * 10_000, 2)
                mv = round(qty * (50 + _seeded_float(iid, "px") * 450), 2)
                rows.append({
                    "portfolio_id": p,
                    "instrument_id": iid,
                    "as_of_date": as_of_date,
                    "quantity": qty,
                    "market_value": mv,
                    "currency": "USD",
                })

    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]
    total_pages = max(1, (len(rows) + page_size - 1) // page_size)
    return {
        "data": page_rows,
        "as_of_date": as_of_date,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_count": len(rows),
        "next_cursor": page + 1 if page < total_pages else None,
    }
