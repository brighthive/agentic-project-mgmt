# Loop Capital — disk-free-space reclaim demo (SQL Server)

A lifelike SQL Server disk-pressure story on the real Loop Capital sandbox
volume: a legacy nightly job quietly fills the disk, a **70%-free monitor**
fires, and **great dbt code** rebuilds the data to hand the space back — the
monitor flips green. Every number is read live off `sys.dm_os_volume_stats`;
nothing is faked.

This customizes the documented **GC-15** disk-space Golden Case
(`../../docs/specs/golden-cases-loopcapital.md`) into a concrete before→after
demo with a real reclaim, not just detection.

## The story

```
  nightly SSIS append (no dedup) ──▶ holdings_snapshot_raw bloats the .mdf
                                            │
                              70%-free monitor: 🚨 BREACH
                                            │
              great dbt code (holdings_current.sql) rebuilds it:
              deduped ▸ narrow types ▸ clustered columnstore
                                            │
                    drop raw heap + DBCC SHRINKFILE
                                            │
                              70%-free monitor: ✅ OK
```

| Step | What happens | Reads |
|---|---|---|
| MEASURE | baseline free % on the real tmpfs data volume | `sys.dm_os_volume_stats` |
| BLOAT | `seed_bloat.py` simulates N nightly full-snapshot appends into a wide, uncompressed heap | grows the real `.mdf` |
| BREACH | `monitor.py` reports below the 70% floor | `sys.dm_os_volume_stats` |
| RECLAIM | `dbt run` builds `holdings_current` — latest snapshot per (portfolio, instrument), narrow types, columnstore | real `dbt-sqlserver` |
| RELEASE | drop the raw heap + `DBCC SHRINKFILE` returns bytes to the volume | real DDL |
| OK | the same 70% monitor flips back to OK | `sys.dm_os_volume_stats` |

## Run it

The sandbox container must be up first (see `../README.md`). Then:

```bash
cd clients/trials/loopcapital/sandbox/disk_reclaim

# one-time: a venv with dbt-core + dbt-sqlserver + pyodbc (needs unixODBC +
# ODBC Driver 18 — `brew install unixodbc && brew install msodbcsql18`)
uv venv .venv
LDFLAGS="-L/opt/homebrew/lib" CPPFLAGS="-I/opt/homebrew/include" \
  ./.venv/bin/python -m pip install dbt-sqlserver pyodbc

export MSSQL_SA_PASSWORD='ChooseA-Strong1-Password!'   # sandbox dev password
./.venv/bin/python run_demo.py --nights 40 --threshold 70
```

`run_demo.py` prefers `./.venv/bin/dbt` (dbt-core + dbt-sqlserver) for the
reclaim. If dbt isn't installed it falls back to the model's identical T-SQL
transform, so the demo always runs end to end — but the artifact of record is
`dbt/models/holdings_current.sql`.

Check the monitor on its own at any time:

```bash
./.venv/bin/python monitor.py            # 70% floor, human-readable
./.venv/bin/python monitor.py --json     # machine-readable, for a watchdog dry run
```

## Captured run (real sandbox volume, 1 GiB tmpfs)

```text
1. MEASURE baseline    ✅ 73.24% free (750 MiB of 1024 MiB) → OK
3. after bloat         🚨 48.24% free (494 MiB of 1024 MiB) → BREACH
4. RECLAIM             ✅ reclaim via `dbt run` (dbt-sqlserver)
6. after reclaim       ✅ 73.24% free (750 MiB of 1024 MiB) → OK
   space reclaimed:    +25.00 percentage points free
```

## Why the numbers are real

- The data volume is a **fixed-size tmpfs** mount (`docker-compose.yml`,
  `LOOPCAPITAL_DATA_VOLUME_BYTES`), so `sys.dm_os_volume_stats` reports a real,
  bounded free-space figure — filling the `.mdf` genuinely drops it.
- `monitor.py` runs the **same DMV query** BH-1045's watchdog uses
  (`SynapseConnection`, plain T-SQL over pymssql) — this is the production
  monitoring path, not a demo-only query.
- The reclaim is a real `dbt run` against the container over ODBC Driver 18;
  the freed space only appears after `DBCC SHRINKFILE` actually returns pages
  to the OS.

## Files

| File | Role |
|---|---|
| `monitor.py` | 70%-free disk monitor (real DMV read → OK/BREACH, exit 0/1) |
| `seed_bloat.py` | the nightly-SSIS anti-pattern that bloats the volume |
| `dbt/models/holdings_current.sql` | the reclaim — deduped, narrow-typed, columnstore |
| `dbt/models/sources.yml` | declares `holdings_snapshot_raw` as the dbt source |
| `dbt/{dbt_project,profiles}.yml` | dbt-sqlserver project + local sandbox profile |
| `run_demo.py` | the end-to-end driver: measure → bloat → BREACH → dbt → shrink → OK |
