# Validated harnesses — proof, not paper

Runnable code + tests that were **executed against live `LONGAEVA_POC`** to prove
the impl-specs in the parent directory are correct. When a spec here says
"verified," this is the verification. Re-run before trusting a spec.

## How to run

Use the brightbot `.venv` (has `pytest`; the introspection module lazy-imports
the Snowflake driver, so unit tests run without it):

```bash
VENV=../../../../../../brightbot/.venv/bin/python   # adjust to your brightbot checkout
$VENV -m pytest bh590/test_introspection.py bh596/test_verified_query_validator.py -o markers=live -q
```

Live tests (`@pytest.mark.live`) shell out to `snow sql -c brighthive` against
`LONGAEVA_POC`. They need the `brighthive` connection in `~/.snowflake/config.toml`.
Drop `-m "not live"` to skip them.

## What's here

| Dir | Spec | Proves |
|---|---|---|
| `bh590/` | `BH-590-snowflake-introspection.md` | `list_tables`/`list_stages`/`list_semantic_views` against live Snowflake. Caught: `KEY_COLUMN_USAGE` doesn't exist (→ `SHOW PRIMARY KEYS`); INFORMATION_SCHEMA/PUBLIC must be excluded; `SHOW` output keys are lower-case. 10 tests. |
| `bh596/` | `BH-591-wire-atlas-tool.md` (verified_query gate) | The verified_query compile-and-run validator. Proves a correct `SEMANTIC_VIEW()` query passes AND the `EXPOSURE.region` table-qualification bug is caught. Seed for BH-596. 7 tests (5 unit + 2 live). |

## Why live matters

Both fatal findings — `KEY_COLUMN_USAGE` (crashes every introspection call) and
cross-table qualification (`EXPOSURE.region` → invalid identifier) — are invisible
to a paper review. Only running the SQL against the real warehouse surfaced them.
That's the discipline the `poc-drive` skill (Gate 5) enforces.
