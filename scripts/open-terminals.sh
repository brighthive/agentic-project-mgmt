#!/usr/bin/env bash
set -euo pipefail

# open-terminals.sh <session-name> <cmd1> <cmd2> <cmd3>
#
# Opens 3 Terminal.app tabs, each running a command.
# Falls back to printing instructions if not on macOS.

SESSION="${1:?session name}"
shift

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Not macOS — run these manually in 3 terminals:"
  i=1
  for cmd in "$@"; do
    echo "  Terminal ${i}: ${cmd}"
    ((i++))
  done
  exit 0
fi

# First tab: just run in current terminal
echo "Starting ${SESSION}..."
echo ""

i=0
for cmd in "$@"; do
  if [[ ${i} -eq 0 ]]; then
    # Open a new Terminal window for the first command
    osascript -e "
      tell application \"Terminal\"
        activate
        do script \"${cmd}\"
      end tell
    " >/dev/null 2>&1
  else
    # Open new tabs for subsequent commands
    osascript -e "
      tell application \"Terminal\"
        activate
        tell application \"System Events\" to keystroke \"t\" using command down
        delay 0.3
        do script \"${cmd}\" in front window
      end tell
    " >/dev/null 2>&1
  fi
  ((i++))
done

echo "Opened ${i} Terminal tabs for ${SESSION}"
