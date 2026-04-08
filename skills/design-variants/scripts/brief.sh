#!/usr/bin/env bash
# Generate BRIEF.md for each variant worktree.
# Usage: brief.sh <skill_dir> <scope_json> <worktrees_json>
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required for brief.sh" >&2
    exit 1
fi

SKILL_DIR="$1"
SCOPE_FILE="$2"   # path to JSON file, not raw JSON
WT_FILE_ARG="$3"  # path to JSON file, not raw JSON

TEMPLATE="$SKILL_DIR/scripts/brief-template.md"
TOOLS_FILE="$SKILL_DIR/scripts/tools.json"

# Extract scope fields from file (not variable)
FILES_LIST=$(jq -r '.files_to_redesign[]' "$SCOPE_FILE" 2>/dev/null | sed 's/^/- `/' | sed 's/$/`/')
OFF_LIMITS=$(jq -r '.files_off_limits[]' "$SCOPE_FILE" 2>/dev/null | sed 's/^/- `/' | sed 's/$/`/')
[[ -z "$OFF_LIMITS" ]] && OFF_LIMITS="- (none detected — use your judgment)"
FRAMEWORK=$(jq -r '.framework' "$SCOPE_FILE")
REPO_ROOT=$(jq -r '.repo_root' "$SCOPE_FILE")
APP_ROOT=$(jq -r '.app_root // ""' "$SCOPE_FILE")

# Detect serve command for preview instructions
if [[ -n "$APP_ROOT" && "$APP_ROOT" != "." && "$APP_ROOT" != "" ]]; then
    SERVE_INSTRUCTIONS="cd $APP_ROOT && npm install && npm run dev"
elif [[ "$FRAMEWORK" == *"react"* || "$FRAMEWORK" == *"vue"* || "$FRAMEWORK" == *"svelte"* || "$FRAMEWORK" == *"node"* || "$FRAMEWORK" == *"vite"* ]]; then
    SERVE_INSTRUCTIONS="npm install && npm run dev"
else
    SERVE_INSTRUCTIONS="Check for package.json or app.py in the project root and run the appropriate dev server."
fi

while IFS= read -r entry; do
    tool=$(echo "$entry" | jq -r '.tool')
    display=$(echo "$entry" | jq -r '.display')
    branch=$(echo "$entry" | jq -r '.branch')
    wt_path=$(echo "$entry" | jq -r '.path')

    instruction=$(jq -r --arg t "$tool" '.[$t].instruction' "$TOOLS_FILE")
    setup=$(jq -r --arg t "$tool" '.[$t].setup // empty' "$TOOLS_FILE")

    SETUP_NOTE=""
    [[ -n "$setup" ]] && SETUP_NOTE="**Setup required:** $setup"

    BASE=$(git -C "$wt_path" log --oneline -1 --format=%D HEAD 2>/dev/null | grep -o 'origin/[^ ,]*' | head -1 || echo "main")

    # Generate brief from template using temp vars to avoid sed issues with multiline
    BRIEF_FILE="$wt_path/BRIEF.md"
    cp "$TEMPLATE" "$BRIEF_FILE"

    # Use perl for multiline-safe replacements
    perl -pi -e "s|__TOOL_DISPLAY__|$display|g" "$BRIEF_FILE"
    perl -pi -e "s|__TOOL_INSTRUCTION__|$instruction|g" "$BRIEF_FILE"
    perl -pi -e "s|__SETUP_NOTE__|$SETUP_NOTE|g" "$BRIEF_FILE"
    perl -pi -e "s|__SERVE_INSTRUCTIONS__|$SERVE_INSTRUCTIONS|g" "$BRIEF_FILE"
    perl -pi -e "s|__BRANCH__|$branch|g" "$BRIEF_FILE"
    perl -pi -e "s|__BASE__|$BASE|g" "$BRIEF_FILE"

    # Replace file lists using a different approach (append after markers)
    python3 -c "
import sys
with open('$BRIEF_FILE', 'r') as f:
    content = f.read()
files = '''$FILES_LIST'''
offlimits = '''$OFF_LIMITS'''
content = content.replace('__FILES_LIST__', files)
content = content.replace('__OFF_LIMITS__', offlimits)
with open('$BRIEF_FILE', 'w') as f:
    f.write(content)
"

    echo "  Wrote $BRIEF_FILE" >&2
done < <(jq -c '.[]' "$WT_FILE")

rm -f "$SCOPE_FILE" "$WT_FILE"
