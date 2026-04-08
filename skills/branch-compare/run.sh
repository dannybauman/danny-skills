#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB="$SKILL_DIR/lib"

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required. Install with: brew install jq" >&2
    exit 1
fi

# Parse args
BRANCH_ARGS=()
WAIT=false
WAIT_TIMEOUT=1800  # 30 min default
while [[ $# -gt 0 ]]; do
    case "$1" in
        --stop)
            shift
            bash "$LIB/stop.sh" "$SKILL_DIR" "$@"
            exit 0
            ;;
        --env-file)
            export BRANCH_COMPARE_ENV="$2"
            shift 2
            ;;
        --wait)
            WAIT=true
            shift
            # Optional timeout in seconds
            if [[ "${1:-}" =~ ^[0-9]+$ ]]; then
                WAIT_TIMEOUT="$1"
                shift
            fi
            ;;
        --help|-h)
            echo "Usage: branch-compare [branches...] [--env-file path] [--wait [seconds]] [--stop [--cleanup]]"
            echo ""
            echo "  No args           Auto-detect recent non-main branches"
            echo "  branch names      Compare specific branches"
            echo "  glob pattern      Match branches (e.g. design-variant-*)"
            echo "  --env-file PATH   Load env vars for backend URLs"
            echo "  --wait [SEC]      Wait for branches to have new commits (default: 1800s)"
            echo "  --stop            Stop all running servers"
            echo "  --stop --cleanup  Stop + remove skill-created worktrees"
            exit 0
            ;;
        *)
            BRANCH_ARGS+=("$1")
            shift
            ;;
    esac
done

# ── Guided mode when no branches specified and none auto-detected ──
if [[ ${#BRANCH_ARGS[@]} -eq 0 ]]; then
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║      Branch Compare — Visual Diff        ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""

    # Try auto-detect
    BRANCHES_JSON=$(bash "$LIB/detect.sh" 2>/dev/null || echo "[]")
    COUNT=$(echo "$BRANCHES_JSON" | jq 'length')

    if [[ "$COUNT" -eq 0 ]]; then
        echo "No recent non-main branches found."
        echo ""
        echo "This tool compares git branches side by side in your browser."
        echo ""
        echo "To use it, you need at least 2 branches. You can:"
        echo "  1. Create branches manually:  git checkout -b my-redesign"
        echo "  2. Use /design-variants to create multiple UI variants"
        echo "  3. Specify branches explicitly: /branch-compare main my-branch"
        echo ""
        echo "Available branches:"
        git branch --format='  %(refname:short)' | head -20
        exit 0
    fi

    echo "Found $COUNT recent branches:"
    echo "$BRANCHES_JSON" | jq -r '.[] | "  \(.branch)"'
    echo ""
    echo "Starting comparison..."
    echo ""
else
    BRANCHES_JSON=$(bash "$LIB/detect.sh" "${BRANCH_ARGS[@]}")
fi

# ── Wait mode: poll branches for new commits ──
if [[ "$WAIT" == "true" ]]; then
    echo "Waiting for variants to be built (timeout: ${WAIT_TIMEOUT}s)..."
    echo ""

    # Snapshot current HEAD of each branch
    declare -A BASE_COMMITS
    while IFS= read -r entry; do
        branch=$(echo "$entry" | jq -r '.branch')
        BASE_COMMITS["$branch"]=$(git rev-parse "$branch" 2>/dev/null || echo "none")
    done < <(echo "$BRANCHES_JSON" | jq -c '.[]')

    TOTAL=$(echo "$BRANCHES_JSON" | jq 'length')
    ELAPSED=0
    INTERVAL=30

    while [[ $ELAPSED -lt $WAIT_TIMEOUT ]]; do
        READY=0
        STATUS=""
        while IFS= read -r entry; do
            branch=$(echo "$entry" | jq -r '.branch')
            name=$(echo "$entry" | jq -r '.name')
            current=$(git rev-parse "$branch" 2>/dev/null || echo "none")
            base="${BASE_COMMITS[$branch]}"
            if [[ "$current" != "$base" ]]; then
                READY=$((READY + 1))
                STATUS="$STATUS  ✓ $name\n"
            else
                STATUS="$STATUS  ⏳ $name (waiting...)\n"
            fi
        done < <(echo "$BRANCHES_JSON" | jq -c '.[]')

        echo -e "  Progress: $READY/$TOTAL variants ready (${ELAPSED}s elapsed)"
        echo -e "$STATUS"

        if [[ $READY -ge $TOTAL ]]; then
            echo "All variants ready!"
            echo ""
            break
        fi

        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done

    if [[ $ELAPSED -ge $WAIT_TIMEOUT ]]; then
        echo "Timeout reached. Comparing what's available..."
        echo ""
    fi
fi

# ── Serve → Switcher ──
VARIANTS_JSON=$(bash "$LIB/serve.sh" "$SKILL_DIR" "$BRANCHES_JSON")

RUNNING=$(echo "$VARIANTS_JSON" | jq 'length')
if [[ "$RUNNING" -eq 0 ]]; then
    echo "Error: no variants could be served." >&2
    echo "Check that the branches contain a web app (package.json, app.py, or index.html)." >&2
    exit 1
fi

bash "$LIB/switcher.sh" "$SKILL_DIR" "$VARIANTS_JSON"

echo ""
echo "════════════════════════════════════════"
echo "  $RUNNING variants running"
echo ""
echo "  Stop servers:   /branch-compare --stop"
echo "  Stop + cleanup: /branch-compare --stop --cleanup"
echo "════════════════════════════════════════"
