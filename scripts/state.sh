#!/usr/bin/env bash
# state.sh — sentinel-file helpers for the onboarding bootstrap Makefile.
#
# Each function is idempotent and quiet on success. Designed to be sourced
# from Makefile recipes:
#
#   . scripts/state.sh
#   state_skip_if_fresh aws/main 28800 "AWS main session" && return 0
#
# All sentinel files live under .state/ (gitignored).

set -euo pipefail

STATE_DIR="${STATE_DIR:-.state}"

# state_touch <subpath>
# Mark a sentinel as "done now". Creates parent dirs as needed.
state_touch() {
    local subpath="$1"
    local full="${STATE_DIR}/${subpath}"
    mkdir -p "$(dirname "$full")"
    touch "$full"
}

# state_age_seconds <subpath>
# Print the age of a sentinel in seconds, or "missing" if absent.
# Handles both macOS (stat -f %m) and GNU/Linux (stat -c %Y).
# If mtime cannot be determined, prints "missing" to avoid arithmetic explosion.
state_age_seconds() {
    local subpath="$1"
    local full="${STATE_DIR}/${subpath}"
    if [[ ! -f "$full" ]]; then
        echo "missing"
        return 0
    fi
    local now mtime
    now=$(date +%s)
    mtime=$(stat -f %m "$full" 2>/dev/null || stat -c %Y "$full" 2>/dev/null || echo "")
    if [[ -z "$mtime" ]]; then
        echo "missing"
        return 0
    fi
    echo "$((now - mtime))"
}

# state_is_fresh <subpath> <ttl_seconds>
# Exit 0 if sentinel exists AND its age <= ttl. Exit 1 otherwise.
state_is_fresh() {
    local subpath="$1"
    local ttl="$2"
    local age
    age=$(state_age_seconds "$subpath")
    [[ "$age" != "missing" ]] && [[ "$age" -le "$ttl" ]]
}

# state_skip_if_fresh <subpath> <ttl_seconds> <description>
# If the sentinel is fresh, print a "skipped" message and return 0.
# Otherwise return 1 so the caller proceeds to do the work.
#
# Honors FORCE=1 environment variable to always force re-run.
state_skip_if_fresh() {
    local subpath="$1"
    local ttl="$2"
    local desc="$3"

    if [[ "${FORCE:-0}" == "1" ]]; then
        return 1
    fi

    if state_is_fresh "$subpath" "$ttl"; then
        local age human
        age=$(state_age_seconds "$subpath")
        human=$(state_format_age "$age")
        echo "  ✓ ${desc} (skipped — fresh, ${human} old)"
        return 0
    fi
    return 1
}

# state_format_age <seconds>
# Print a human-readable age like "23m" or "4h" or "2d".
state_format_age() {
    local s="$1"
    if   [[ "$s" -lt 60    ]]; then echo "${s}s"
    elif [[ "$s" -lt 3600  ]]; then echo "$((s / 60))m"
    elif [[ "$s" -lt 86400 ]]; then echo "$((s / 3600))h"
    else                            echo "$((s / 86400))d"
    fi
}

# state_sha256 <file>
# Print sha256 of a file, or "MISSING" if the file doesn't exist.
state_sha256() {
    local f="$1"
    if [[ ! -f "$f" ]]; then
        echo "MISSING"
        return 0
    fi
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$f" | awk '{print $1}'
    else
        sha256sum "$f" | awk '{print $1}'
    fi
}

# state_write_meta <repo>-<env> template_sha secrets_sha rendered_sha
# Write a .meta file with three SHA records for env materialization tracking.
state_write_meta() {
    local key="$1"
    local template_sha="$2"
    local secrets_sha="$3"
    local rendered_sha="$4"
    local meta="${STATE_DIR}/env/${key}.meta"
    mkdir -p "$(dirname "$meta")"
    cat > "$meta" <<EOF
template_sha=${template_sha}
secrets_sha=${secrets_sha}
rendered_sha=${rendered_sha}
written_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
}

# state_read_meta <repo>-<env> <field>
# Read one field from a .meta file. Print empty string if missing.
state_read_meta() {
    local key="$1"
    local field="$2"
    local meta="${STATE_DIR}/env/${key}.meta"
    if [[ ! -f "$meta" ]]; then
        echo ""
        return 0
    fi
    grep "^${field}=" "$meta" | head -1 | cut -d= -f2-
}

# When sourced, expose functions. When run directly, run the requested subcommand.
if [[ "${BASH_SOURCE[0]:-$0}" == "${0}" ]]; then
    cmd="${1:-help}"
    shift || true
    case "$cmd" in
        touch)          state_touch "$@" ;;
        age)            state_age_seconds "$@" ;;
        fresh)          state_is_fresh "$@" ;;
        skip-if-fresh)  state_skip_if_fresh "$@" ;;
        sha256)         state_sha256 "$@" ;;
        write-meta)     state_write_meta "$@" ;;
        read-meta)      state_read_meta "$@" ;;
        help|*)
            cat <<EOF
state.sh — sentinel-file helpers

Usage:
  scripts/state.sh touch <subpath>
  scripts/state.sh age <subpath>
  scripts/state.sh fresh <subpath> <ttl_seconds>
  scripts/state.sh skip-if-fresh <subpath> <ttl_seconds> <description>
  scripts/state.sh sha256 <file>
  scripts/state.sh write-meta <key> <template_sha> <secrets_sha> <rendered_sha>
  scripts/state.sh read-meta <key> <field>
EOF
            ;;
    esac
fi
