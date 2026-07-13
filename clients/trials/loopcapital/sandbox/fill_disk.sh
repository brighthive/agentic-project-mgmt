#!/usr/bin/env bash
# Fills the fixed-size tmpfs data volume toward the 18-20% free-space
# threshold Frank named — sys.dm_os_volume_stats reports the REAL mount's
# free space, so this is a genuine disk-pressure condition, not a fabricated
# metric. Idempotent: safe to re-run, always recomputes the filler size from
# the volume's CURRENT free space rather than assuming a fresh volume.
set -euo pipefail

TARGET_FREE_PCT="${LOOPCAPITAL_TARGET_FREE_PCT:-18}"
FILLER_PATH="/var/opt/mssql/data/.disk_filler"

echo "Reading current volume size/free space inside the container..."
VOLUME_STATS=$(docker exec loopcapital-sql-sandbox df -B1 /var/opt/mssql/data | tail -1)
TOTAL_BYTES=$(echo "${VOLUME_STATS}" | awk '{print $2}')
USED_BYTES=$(echo "${VOLUME_STATS}" | awk '{print $3}')

TARGET_FREE_BYTES=$(( TOTAL_BYTES * TARGET_FREE_PCT / 100 ))
TARGET_USED_BYTES=$(( TOTAL_BYTES - TARGET_FREE_BYTES ))
FILLER_BYTES=$(( TARGET_USED_BYTES - USED_BYTES ))

if [[ "${FILLER_BYTES}" -le 0 ]]; then
  echo "Volume is already at or below ${TARGET_FREE_PCT}% free — no filler needed."
  exit 0
fi

echo "Total: $((TOTAL_BYTES / 1024 / 1024))MiB, currently used: $((USED_BYTES / 1024 / 1024))MiB"
echo "Writing $((FILLER_BYTES / 1024 / 1024))MiB filler to reach ~${TARGET_FREE_PCT}% free..."
docker exec loopcapital-sql-sandbox dd if=/dev/zero "of=${FILLER_PATH}" bs=1M count=$(( FILLER_BYTES / 1024 / 1024 )) status=progress

echo "Done. Verify with: ./validate.sh"
