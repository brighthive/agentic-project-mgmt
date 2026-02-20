#!/usr/bin/env bash
set -euo pipefail

# apply-env-overlay.sh <repo-dir> <overlay-file>
#
# Merges an overlay file into the repo's .env.
# Overlay format:
#   KEY=value        → set or replace KEY in .env
#   ~KEY             → comment out KEY in .env (prefix with #)
#
# Backs up to .env.bak before modifying.

REPO_DIR="${1:?Usage: apply-env-overlay.sh <repo-dir> <overlay-file>}"
OVERLAY="${2:?Usage: apply-env-overlay.sh <repo-dir> <overlay-file>}"

ENV_FILE="${REPO_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} does not exist" >&2
  exit 1
fi

if [[ ! -f "${OVERLAY}" ]]; then
  echo "ERROR: overlay ${OVERLAY} does not exist" >&2
  exit 1
fi

cp "${ENV_FILE}" "${ENV_FILE}.bak"

while IFS= read -r line || [[ -n "${line}" ]]; do
  # Skip empty lines and comments
  [[ -z "${line}" ]] && continue
  [[ "${line}" =~ ^# ]] && continue

  # ~KEY → comment out that key
  if [[ "${line}" =~ ^~(.+)$ ]]; then
    key="${BASH_REMATCH[1]}"
    # Comment out any active line with this key
    if grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null; then
      sed -i '' "s|^${key}=|# ${key}=|" "${ENV_FILE}"
    fi
    continue
  fi

  # KEY=value → set or replace
  key="${line%%=*}"
  if grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null; then
    # Replace existing active line
    sed -i '' "s|^${key}=.*|${line}|" "${ENV_FILE}"
  elif grep -q "^# *${key}=" "${ENV_FILE}" 2>/dev/null; then
    # Uncomment and replace
    sed -i '' "s|^# *${key}=.*|${line}|" "${ENV_FILE}"
  else
    # Append
    echo "${line}" >> "${ENV_FILE}"
  fi

done < "${OVERLAY}"

echo "  Applied $(basename "${OVERLAY}") → ${ENV_FILE}"
