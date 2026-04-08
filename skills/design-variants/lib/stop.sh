#!/usr/bin/env bash
# Stop all running variant servers. Optionally clean up worktrees.
# Usage: stop.sh <skill_dir> [--cleanup]
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Warning: jq not found. Worktree cleanup may not work." >&2
fi

SKILL_DIR="$1"
CLEANUP=false
[[ "${2:-}" == "--cleanup" ]] && CLEANUP=true

STATE_DIR="$SKILL_DIR/.state"
PIDS_DIR="$STATE_DIR/pids"

# Kill servers
if [[ -d "$PIDS_DIR" ]]; then
    echo "Stopping servers..."
    for pidfile in "$PIDS_DIR"/*.pid; do
        [[ -f "$pidfile" ]] || continue
        name=$(basename "$pidfile" .pid)
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "  Stopped $name (PID $pid)"
        else
            echo "  $name already stopped"
        fi
        rm -f "$pidfile"
    done
fi

# Clean up worktrees
if [[ "$CLEANUP" == "true" ]]; then
    WT_FILE="$STATE_DIR/worktrees.json"
    if [[ -f "$WT_FILE" ]]; then
        echo "Removing skill-created worktrees..."
        for name in $(jq -r 'keys[]' "$WT_FILE"); do
            wt_path=$(jq -r --arg k "$name" '.[$k]' "$WT_FILE")
            if [[ -d "$wt_path" ]]; then
                git worktree remove "$wt_path" --force 2>/dev/null || {
                    echo "  WARN: could not remove $wt_path"
                    continue
                }
                echo "  Removed $wt_path"
            fi
        done
        echo '{}' > "$WT_FILE"
    fi
fi

# Clear ports
[[ -f "$STATE_DIR/ports.json" ]] && echo '{}' > "$STATE_DIR/ports.json"

echo "Done."
