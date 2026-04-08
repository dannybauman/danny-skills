#!/usr/bin/env bash
# Detect git branches matching a pattern. Output JSON array.
# Usage: detect.sh [pattern...] or detect.sh (auto-detect)
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Warning: jq not found. JSON output may be malformed for branch names with special characters." >&2
fi

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: not inside a git repository" >&2
    exit 1
fi

BRANCHES=()

if [[ $# -gt 0 ]]; then
    # Explicit branches or glob patterns
    for pattern in "$@"; do
        while IFS= read -r branch; do
            [[ -n "$branch" ]] && BRANCHES+=("$branch")
        done < <(git branch --list "$pattern" --format='%(refname:short)' 2>/dev/null)
        # Also try as exact branch name
        if git rev-parse --verify "$pattern" &>/dev/null && [[ ! " ${BRANCHES[*]} " =~ " $pattern " ]]; then
            BRANCHES+=("$pattern")
        fi
    done
else
    # Auto-detect: non-main branches with commits in last 30 days
    CUTOFF=$(date -v-30d +%Y-%m-%d 2>/dev/null || date -d '30 days ago' +%Y-%m-%d 2>/dev/null || echo "1970-01-01")
    while IFS= read -r branch; do
        [[ -z "$branch" ]] && continue
        [[ "$branch" == "main" || "$branch" == "master" ]] && continue
        last_commit=$(git log -1 --format=%ci "$branch" 2>/dev/null | cut -d' ' -f1)
        if [[ "$last_commit" > "$CUTOFF" || "$last_commit" == "$CUTOFF" ]]; then
            BRANCHES+=("$branch")
        fi
    done < <(git branch --format='%(refname:short)')
fi

if [[ ${#BRANCHES[@]} -eq 0 ]]; then
    echo "Error: no matching branches found" >&2
    exit 1
fi

# Output JSON array
echo -n "["
for i in "${!BRANCHES[@]}"; do
    branch="${BRANCHES[$i]}"
    name=$(echo "$branch" | sed 's/[^a-zA-Z0-9]/-/g')
    [[ $i -gt 0 ]] && echo -n ","
    echo -n "{\"name\":\"$name\",\"branch\":\"$branch\"}"
done
echo "]"
