"""Longitudinal anomaly monitor (POC use case 4.3).

Beyond pass/fail gates: snapshot data-health metrics every refresh and detect
statistical anomalies vs a trailing window. Four signal families Grant named:

  - row_count_drift        : row count vs trailing-window mean
  - cardinality_breakdown  : distinct count of a key dim drops sharply
  - distributional_skew    : numeric metric mean/stddev deviates from baseline
  - null_spike             : null rate in a well-populated column jumps

Flow:
  snapshot()  -> compute current metrics, write to MONITORING.metric_history
  detect()    -> compare latest snapshot vs trailing window, write anomaly_events
  simulate()  -> inject N historical snapshots + one anomalous snapshot, then
                 detect, to prove the monitor fires (self-contained demo)

Run:
  uv run --with snowflake-connector-python python monitor.py snapshot --run-id r1
  uv run --with snowflake-connector-python python monitor.py detect
  uv run --with snowflake-connector-python python monitor.py simulate
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import tomllib
from pathlib import Path

import snowflake.connector

DATASET = "GOLD.mart_daily_portfolio_exposure"
FQ = "LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure"
HIST = "LONGAEVA_POC.MONITORING.metric_history"
EVENTS = "LONGAEVA_POC.MONITORING.anomaly_events"
TRAILING_WINDOW = 7
# per-metric tolerances (fractional deviation that triggers an anomaly)
TOLERANCE = {
    "row_count": 0.20,
    "cardinality:country_code": 0.20,
    "cardinality:sector_code": 0.20,
    "null_rate:fiscal_period_id": 0.15,   # absolute jump in null rate
    "mean:exposure_amount_usd": 0.30,
    "stddev:exposure_amount_usd": 0.40,
}
ANOMALY_TYPE = {
    "row_count": "row_count_drift",
    "cardinality:country_code": "cardinality_breakdown",
    "cardinality:sector_code": "cardinality_breakdown",
    "null_rate:fiscal_period_id": "null_spike",
    "mean:exposure_amount_usd": "distributional_skew",
    "stddev:exposure_amount_usd": "distributional_skew",
}


def connect(connection: str = "brighthive"):
    cfg_path = Path.home() / ".snowflake" / "config.toml"
    with cfg_path.open("rb") as f:
        c = tomllib.load(f)["connections"][connection]
    return snowflake.connector.connect(
        account=c["account"], user=c["user"], password=c["password"],
        role=c.get("role"), warehouse=c.get("warehouse"),
        database=c.get("database"), schema="MONITORING",
    )


def compute_metrics(conn) -> dict[str, float]:
    cur = conn.cursor()
    cur.execute(f"""
        SELECT
            COUNT(*)                                                    AS row_count,
            COUNT(DISTINCT country_code)                                AS card_country,
            COUNT(DISTINCT sector_code)                                 AS card_sector,
            SUM(CASE WHEN fiscal_period_id IS NULL THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0)                                     AS null_fiscal,
            AVG(exposure_amount_usd)                                    AS mean_exp,
            STDDEV(exposure_amount_usd)                                 AS stddev_exp
        FROM {FQ}
    """)
    r = cur.fetchone()
    return {
        "row_count": float(r[0]),
        "cardinality:country_code": float(r[1]),
        "cardinality:sector_code": float(r[2]),
        "null_rate:fiscal_period_id": float(r[3] or 0),
        "mean:exposure_amount_usd": float(r[4] or 0),
        "stddev:exposure_amount_usd": float(r[5] or 0),
    }


def write_snapshot(conn, ts: dt.datetime, metrics: dict[str, float], run_id: str):
    cur = conn.cursor()
    rows = [(ts, DATASET, name, val, run_id) for name, val in metrics.items()]
    cur.executemany(
        f"INSERT INTO {HIST} (snapshot_ts, dataset, metric_name, metric_value, run_id) "
        f"VALUES (%s, %s, %s, %s, %s)",
        rows,
    )


def snapshot(conn, run_id: str, ts: dt.datetime | None = None):
    ts = ts or _now(conn)
    metrics = compute_metrics(conn)
    write_snapshot(conn, ts, metrics, run_id)
    print(f"snapshot {run_id} @ {ts}: {metrics}", file=sys.stderr)
    return metrics


def _now(conn) -> dt.datetime:
    cur = conn.cursor()
    cur.execute("SELECT CURRENT_TIMESTAMP()::TIMESTAMP_NTZ")
    return cur.fetchone()[0]


def detect(conn) -> list[dict]:
    """Compare the latest snapshot per metric vs the trailing-window baseline."""
    cur = conn.cursor()
    anomalies = []
    for metric, tol in TOLERANCE.items():
        cur.execute(f"""
            SELECT snapshot_ts, metric_value FROM {HIST}
            WHERE dataset = '{DATASET}' AND metric_name = '{metric}'
            ORDER BY snapshot_ts DESC
            LIMIT {TRAILING_WINDOW + 1}
        """)
        rows = cur.fetchall()
        if len(rows) < 2:
            continue
        current_ts, current = rows[0]
        baseline_vals = [r[1] for r in rows[1:]]
        baseline = sum(baseline_vals) / len(baseline_vals)

        if metric.startswith("null_rate"):
            deviation = abs(current - baseline)         # absolute for rates
            triggered = deviation > tol
            dev_pct = deviation * 100
        else:
            if baseline == 0:
                continue
            deviation = abs(current - baseline) / baseline
            triggered = deviation > tol
            dev_pct = deviation * 100

        if triggered:
            sev = "error" if dev_pct > tol * 200 else "warning"
            desc = (f"{metric} = {current:.4g} vs trailing baseline {baseline:.4g} "
                    f"({dev_pct:.1f}% deviation, tol {tol*100:.0f}%)")
            cur.execute(
                f"INSERT INTO {EVENTS} (detected_ts, dataset, metric_name, "
                f"current_value, baseline_value, deviation_pct, anomaly_type, "
                f"severity, description) VALUES "
                f"(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (current_ts, DATASET, metric, current, baseline, dev_pct,
                 ANOMALY_TYPE[metric], sev, desc),
            )
            anomalies.append({"metric": metric, "type": ANOMALY_TYPE[metric],
                              "severity": sev, "description": desc})
    return anomalies


def simulate(conn):
    """Self-contained demo: 7 stable historical snapshots + 1 anomalous, then detect."""
    print("Simulating 7 stable snapshots + 1 anomalous...", file=sys.stderr)
    # clear prior sim rows for idempotency
    conn.cursor().execute(f"DELETE FROM {HIST} WHERE run_id LIKE 'sim-%'")
    conn.cursor().execute(f"DELETE FROM {EVENTS} WHERE dataset = '{DATASET}'")

    base = compute_metrics(conn)
    now = _now(conn)
    # 7 stable historical snapshots (tiny jitter)
    for i in range(TRAILING_WINDOW, 0, -1):
        ts = now - dt.timedelta(days=i)
        jittered = {k: v * (1 + 0.01 * ((i % 3) - 1)) for k, v in base.items()}
        write_snapshot(conn, ts, jittered, f"sim-hist-{i}")
    # 1 anomalous snapshot: row count halves, sector cardinality collapses,
    # null rate spikes, exposure mean jumps
    anomalous = dict(base)
    anomalous["row_count"] = base["row_count"] * 0.4          # -60% rows
    anomalous["cardinality:sector_code"] = 3                  # collapse from 10
    anomalous["null_rate:fiscal_period_id"] = base["null_rate:fiscal_period_id"] + 0.30
    anomalous["mean:exposure_amount_usd"] = base["mean:exposure_amount_usd"] * 1.6
    write_snapshot(conn, now, anomalous, "sim-anomaly")

    anomalies = detect(conn)
    print(f"\nDetected {len(anomalies)} anomalies:")
    for a in anomalies:
        print(f"  [{a['severity']}] {a['type']}: {a['description']}")
    expected = {"row_count_drift", "cardinality_breakdown", "null_spike", "distributional_skew"}
    found = {a["type"] for a in anomalies}
    missing = expected - found
    ok = not missing
    print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — anomaly families detected: "
          f"{sorted(found)}" + (f" (missing {sorted(missing)})" if missing else ""))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["snapshot", "detect", "simulate"])
    ap.add_argument("--run-id", default="manual")
    ap.add_argument("--connection", default="brighthive")
    args = ap.parse_args()

    conn = connect(args.connection)
    rc = 0
    if args.command == "snapshot":
        snapshot(conn, args.run_id)
    elif args.command == "detect":
        anomalies = detect(conn)
        for a in anomalies:
            print(f"  [{a['severity']}] {a['type']}: {a['description']}")
        print(f"{len(anomalies)} anomalies detected")
    elif args.command == "simulate":
        rc = 0 if simulate(conn) else 1
    conn.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
