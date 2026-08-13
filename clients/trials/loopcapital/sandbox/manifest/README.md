# Loop Capital sandbox — manifest mode

> Rebuild a local SQL Server whose **shape** mirrors what staging knows about Loop Capital,
> seeded with **deterministic synthetic rows**, from **git alone**. No staging access at recreate
> time, no real rows, no credentials. Never touches Loop Capital's real server.

Manifest mode is a distinct front door from **scenario mode** (`../setup.sh` → `../reset.py`, which
drives the golden-case fixtures in `../sql/*.sql`). They never run together — that keeps the
sandbox's "one seeding mechanism, not two" rule intact: scenario mode seeds from `sql/*.sql`;
manifest mode seeds only from `schema_manifest.json`.

| Mode | Front door | Schema source | Seed source | Use for |
|---|---|---|---|---|
| **Scenario** | `setup.sh` / `reset.py --scenario X` | `sql/*.sql` (hand-authored) | `reset.py` + `sql/04_seed_bank_data.py` | Golden cases GC-14/15/16 (injected problems) |
| **Manifest** | `make sandbox-recreate` | `schema_manifest.json` (captured) | `synthesize.py` (deterministic) | Reproducible-from-git shape mirroring staging |

## The four make targets (run from repo root)

```bash
make capture-loopcapital   # ① SSO'd, READ-ONLY: staging platform-core GraphQL + linked GitHub
                           #    → schema_manifest.json (committed) + _raw/ (gitignored). Never Frank's server.
make sandbox-nuke          # ② docker compose down -v: destroy the local SQL Server volume
make sandbox-recreate      # ③ compose up + apply manifest DDL + synthesize rows (idempotent, git-only)
make sandbox-synthesize    # ④ re-seed deterministic rows into a running container (no restart)
```

`MSSQL_SA_PASSWORD` must be exported for every target that touches the container (②③④) — a
throwaway local password, never committed.

## Files

| File | Ticket | Role |
|---|---|---|
| `manifest_model.py` | — | Typed contract (`SchemaManifest`/`TableSpec`/`ColumnSpec`). Both capture paths + the synthesizer share it. |
| `capture_from_staging.py` | BH-1404 | Production capture: staging GraphQL → manifest. Reads a bearer token from env, never persists it. |
| `introspect_local.py` | BH-1404 | Dev bootstrap + round-trip proof: reads our own sandbox container's `INFORMATION_SCHEMA` → manifest. Never external. |
| `synthesize.py` | BH-1406 | Manifest → faithful `CREATE TABLE` DDL + deterministic seeded rows (`--rows`/`--seed`). |
| `recreate.py` | BH-1405 | Orchestrator: compose up → wait healthy → apply DDL → synthesize. |
| `../schema_manifest.json` | — | The committed shape (no rows, no secrets). Regenerate with capture/introspect. |
| `../_raw/` | — | Raw capture dumps for debugging — **gitignored**. |

## Round-trip (how the committed manifest was built, and how to rebuild it)

```bash
export MSSQL_SA_PASSWORD='<throwaway-local-password>'
../setup.sh                                             # scenario mode boots the full sql/*.sql schema
uv run --with pymssql python introspect_local.py        # our own container → ../schema_manifest.json
make sandbox-nuke && make sandbox-recreate              # rebuild the SAME shape from the manifest alone
```

The committed `schema_manifest.json` is a faithful projection of the sandbox schema, captured from
a real backend — not hand-typed. When `sql/*.sql` changes, re-run `introspect_local.py` to keep the
manifest honest.
