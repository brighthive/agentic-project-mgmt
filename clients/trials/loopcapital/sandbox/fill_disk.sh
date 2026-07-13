#!/usr/bin/env bash
# Fills the fixed-size tmpfs data volume toward the 18-20% free-space
# threshold Frank named — sys.dm_os_volume_stats reports the REAL mount's
# free space, so this is a genuine disk-pressure condition, not a fabricated
# metric.
#
# Idempotent by construction, not just by re-computing a delta: the filler
# is sized as an ABSOLUTE target (total_bytes - target_free_bytes -
# non_filler_used_bytes), computed by first EXCLUDING the filler's own
# current size from "used." A prior version computed a delta against
# whatever "used" already included the filler — re-running it after the
# filler existed could shrink the filler to a smaller size, silently
# REDUCING disk pressure below the demo threshold (caught in review).
set -euo pipefail

readonly TARGET_FREE_PCT="${LOOPCAPITAL_TARGET_FREE_PCT:-18}"
readonly DATA_PATH="/var/opt/mssql/loopcapital_data"
readonly FILLER_PATH="${DATA_PATH}/.disk_filler"

echo "Reading current volume size/free space inside the container..."
volume_stats=$(docker exec loopcapital-sql-sandbox df -B1 "${DATA_PATH}" | tail -1)
total_bytes=$(echo "${volume_stats}" | awk '{print $2}')
used_bytes=$(echo "${volume_stats}" | awk '{print $3}')

filler_current_bytes=$(docker exec loopcapital-sql-sandbox sh -c \
  "test -f '${FILLER_PATH}' && stat -c%s '${FILLER_PATH}' || echo 0")

non_filler_used_bytes=$(( used_bytes - filler_current_bytes ))
target_free_bytes=$(( total_bytes * TARGET_FREE_PCT / 100 ))
target_filler_bytes=$(( total_bytes - target_free_bytes - non_filler_used_bytes ))

if [[ "${target_filler_bytes}" -le 0 ]]; then
  echo "Non-filler usage alone is already at or below ${TARGET_FREE_PCT}% free — no filler needed."
  docker exec loopcapital-sql-sandbox rm -f "${FILLER_PATH}"
  exit 0
fi

echo "Total: $((total_bytes / 1024 / 1024))MiB, non-filler used: $((non_filler_used_bytes / 1024 / 1024))MiB"
echo "Writing filler to an ABSOLUTE $((target_filler_bytes / 1024 / 1024))MiB (not a delta) to reach ~${TARGET_FREE_PCT}% free..."
docker exec loopcapital-sql-sandbox dd if=/dev/zero "of=${FILLER_PATH}" bs=1M count=$(( target_filler_bytes / 1024 / 1024 )) status=progress

echo "Done. Verify with: ./validate.sh"
