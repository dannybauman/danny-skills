#!/usr/bin/env bash
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$SKILL_DIR/scripts"
LIB="$SKILL_DIR/lib"
TOOLS_FILE="$SCRIPTS/tools.json"

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required. Install with: brew install jq" >&2
    exit 1
fi

# Parse args
TOOLS=()
LAUNCH=false
COMPARE=false
BASE=""
INTERACTIVE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pick)
            bash "$SCRIPTS/pick-variant.sh" "$2"
            exit 0
            ;;
        --launch) LAUNCH=true; shift ;;
        --compare) COMPARE=true; shift ;;
        --base)   BASE="$2"; shift 2 ;;
        --interactive|-i) INTERACTIVE=true; shift ;;
        --help|-h)
            echo "Usage: design-variants [tool1 tool2 ...] [--base branch] [--launch] [-i]"
            echo ""
            echo "Options:"
            echo "  tool names     Which AI tools to use (default: all in tools.json)"
            echo "  --base BRANCH  Branch to fork from (default: main)"
            echo "  --launch       Spawn Claude Code agents automatically"
            echo "  -i             Interactive guided mode"
            echo ""
            echo "Available tools:"
            jq -r 'to_entries[] | "  \(.key)\t\(.value.display)"' "$TOOLS_FILE"
            exit 0
            ;;
        *)        TOOLS+=("$1"); shift ;;
    esac
done

# If no args at all, run guided mode
if [[ ${#TOOLS[@]} -eq 0 && -z "$BASE" && "$LAUNCH" == "false" ]]; then
    INTERACTIVE=true
fi

# ── Guided Interactive Mode ──
if [[ "$INTERACTIVE" == "true" ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║       Design Variants — Guided Setup        ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""
    echo "This tool creates multiple versions of your UI, each using a different"
    echo "AI design tool. You'll end up with side-by-side comparisons to pick from."
    echo ""

    # Step 1: Detect project
    echo "── Step 1: Analyzing your project ──"
    SCOPE_JSON=$(bash "$SCRIPTS/scope.sh")
    FRAMEWORK=$(echo "$SCOPE_JSON" | jq -r '.framework')
    FILE_COUNT=$(echo "$SCOPE_JSON" | jq '.files_to_redesign | length')
    echo "  Detected: $FRAMEWORK project with $FILE_COUNT frontend files"
    echo ""

    # Step 2: Choose base branch
    if [[ -z "$BASE" ]]; then
        CURRENT=$(git branch --show-current)
        DEFAULT_BASE=$(git rev-parse --verify main &>/dev/null && echo "main" || echo "master")
        echo "── Step 2: Which branch to start from? ──"
        echo "  Current branch: $CURRENT"
        echo "  Default: $DEFAULT_BASE"
        read -rp "  Base branch [$DEFAULT_BASE]: " USER_BASE
        BASE="${USER_BASE:-$DEFAULT_BASE}"
    fi
    echo ""

    # Step 3: Choose tools
    echo "── Step 3: Which design tools? ──"
    echo "  Available tools:"
    AVAILABLE_TOOLS=()
    while IFS= read -r tool; do
        AVAILABLE_TOOLS+=("$tool")
        display=$(jq -r --arg t "$tool" '.[$t].display' "$TOOLS_FILE")
        setup=$(jq -r --arg t "$tool" '.[$t].setup // empty' "$TOOLS_FILE")
        marker=""
        [[ -n "$setup" ]] && marker=" (requires setup)"
        echo "    $tool — $display$marker"
    done < <(jq -r 'keys[]' "$TOOLS_FILE")
    echo ""
    echo "  Enter tool names separated by spaces, or press Enter for all:"
    read -rp "  Tools [all]: " USER_TOOLS
    if [[ -n "$USER_TOOLS" ]]; then
        read -ra TOOLS <<< "$USER_TOOLS"
    fi
    echo ""

    # Step 4: Confirm
    TOOL_DISPLAY="${TOOLS[*]:-all (${AVAILABLE_TOOLS[*]})}"
    echo "── Ready to go ──"
    echo "  Base branch: $BASE"
    echo "  Tools: $TOOL_DISPLAY"
    echo "  Files to redesign: $FILE_COUNT"
    echo ""
    read -rp "  Create variant worktrees? [Y/n]: " CONFIRM
    if [[ "$CONFIRM" =~ ^[Nn] ]]; then
        echo "Cancelled."
        exit 0
    fi
    echo ""
fi

# ── Smart defaults ──
if [[ -z "$BASE" ]]; then
    BASE=$(git rev-parse --verify main &>/dev/null && echo "main" || echo "master")
fi

# ── Execute pipeline ──
# Use temp files for JSON to avoid bash variable expansion breaking arrays
SCOPE_FILE=$(mktemp)
WT_FILE=$(mktemp)
trap "rm -f '$SCOPE_FILE' '$WT_FILE'" EXIT

echo "── Analyzing project scope ──"
if [[ -n "${SCOPE_JSON:-}" ]]; then
    echo "$SCOPE_JSON" > "$SCOPE_FILE"
else
    bash "$SCRIPTS/scope.sh" > "$SCOPE_FILE"
fi

echo "── Creating variant worktrees from $BASE ──"
bash "$SCRIPTS/worktree.sh" "$SKILL_DIR" "$BASE" "${TOOLS[@]}" > "$WT_FILE"

echo "── Writing briefs ──"
bash "$SCRIPTS/brief.sh" "$SKILL_DIR" "$SCOPE_FILE" "$WT_FILE"

echo ""
bash "$SCRIPTS/prompts.sh" "$WT_FILE"

if [[ "$LAUNCH" == "true" ]]; then
    bash "$SCRIPTS/launch.sh" "$WORKTREES_JSON"
fi

echo ""
echo "════════════════════════════════════════"
echo "  Variants ready!"
echo ""
echo "  Next steps:"
echo "  1. Open a new terminal tab for each variant"
echo "  2. Paste the prompts above into each tab"
echo "  3. Watch each tool redesign your UI"
echo "  4. When all are done, come back and say"
echo "     'compare the variants'"
echo "════════════════════════════════════════"

# Auto-chain into branch-compare if --compare or --launch
if [[ "$COMPARE" == "true" || "$LAUNCH" == "true" ]]; then
    COMPARE_SCRIPT="$SKILL_DIR/lib/../../branch-compare/run.sh"
    if [[ -f "$COMPARE_SCRIPT" ]]; then
        echo ""
        echo "Waiting for variants to be built, then comparing..."
        bash "$COMPARE_SCRIPT" --wait 'design-variant-*'
    else
        echo ""
        echo "Run: /branch-compare --wait design-variant-*"
    fi
fi
