#!/usr/bin/env bash
# (Experimental) Spawn Claude Code agents in background, one per worktree.
# Usage: launch.sh <worktrees_json>
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required but not installed" >&2
    exit 1
fi

WORKTREES_JSON="$1"

echo ""
echo "Launching Claude Code agents..."
echo ""

while IFS= read -r entry; do
    tool=$(echo "$entry" | jq -r '.tool')
    display=$(echo "$entry" | jq -r '.display')
    wt_path=$(echo "$entry" | jq -r '.path')

    echo "  Launching agent for $display in $wt_path..."
    (cd "$wt_path" && claude --message "Read BRIEF.md and execute the redesign. Commit your work when done." &) 2>/dev/null

done < <(echo "$WORKTREES_JSON" | jq -c '.[]')

echo ""
echo "Agents launched. Monitor progress with: git worktree list"
