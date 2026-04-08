#!/usr/bin/env bash
# Create one worktree per variant tool, branching from base.
# Usage: worktree.sh <skill_dir> <base_branch> [tool1 tool2 ...]
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required for worktree.sh" >&2
    exit 1
fi

SKILL_DIR="$1"
BASE="$2"
shift 2

TOOLS_FILE="$SKILL_DIR/scripts/tools.json"
STATE_DIR="$SKILL_DIR/.state"
mkdir -p "$STATE_DIR"

REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
PARENT_DIR=$(dirname "$REPO_ROOT")

# Get tool list: from args or all from tools.json
TOOLS=("$@")
if [[ ${#TOOLS[@]} -eq 0 ]]; then
    while IFS= read -r tool; do
        TOOLS+=("$tool")
    done < <(jq -r 'keys[]' "$TOOLS_FILE")
fi

RESULTS="["
COUNT=0

for tool in "${TOOLS[@]}"; do
    branch="design-variant-$tool"
    wt_path="$PARENT_DIR/${REPO_NAME}-${tool}"

    # Skip if worktree already exists
    if [[ -d "$wt_path" ]]; then
        echo "  $tool: worktree exists at $wt_path" >&2
    else
        echo "  $tool: creating worktree from $BASE..." >&2
        git worktree add -b "$branch" "$wt_path" "$BASE" 2>&1 >&2 || {
            # Branch may already exist
            git worktree add "$wt_path" "$branch" 2>&1 >&2 || {
                echo "  WARN: failed to create worktree for $tool" >&2
                continue
            }
        }
    fi

    display=$(jq -r --arg t "$tool" '.[$t].display // $t' "$TOOLS_FILE")

    [[ $COUNT -gt 0 ]] && RESULTS="$RESULTS,"
    RESULTS="$RESULTS{\"tool\":\"$tool\",\"display\":\"$display\",\"branch\":\"$branch\",\"path\":\"$wt_path\"}"
    COUNT=$((COUNT + 1))
done

RESULTS="$RESULTS]"
echo "$RESULTS"
