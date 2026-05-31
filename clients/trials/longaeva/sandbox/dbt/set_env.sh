#!/usr/bin/env bash
# Source me to export Snowflake env vars from ~/.snowflake/config.toml.
# Usage: source ./set_env.sh

set -e
CONFIG="$HOME/.snowflake/config.toml"
[ -f "$CONFIG" ] || { echo "missing $CONFIG"; return 1 2>/dev/null || exit 1; }

# Parse the [connections.brighthive] block via Python (tomllib).
eval "$(python3 - "$CONFIG" <<'PY'
import sys, tomllib
with open(sys.argv[1], "rb") as f:
    cfg = tomllib.load(f)
c = cfg["connections"]["brighthive"]
print(f'export SNOWFLAKE_ACCOUNT={c["account"]!r}')
print(f'export SNOWFLAKE_USER={c["user"]!r}')
print(f'export SNOWFLAKE_PASSWORD={c["password"]!r}')
PY
)"

echo "Snowflake env exported for account=$SNOWFLAKE_ACCOUNT user=$SNOWFLAKE_USER"
