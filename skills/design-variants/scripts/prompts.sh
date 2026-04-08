#!/usr/bin/env bash
# Output copy-paste prompts for each variant's Claude Code tab.
# Usage: prompts.sh <worktrees_json>
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_FILE="$SKILL_DIR/scripts/tools.json"

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required but not installed" >&2
    exit 1
fi

WT_FILE="$1"  # path to JSON file, not raw JSON
COUNT=0

echo ""
echo "=== Claude Code Prompts ==="
echo "Open a new terminal tab for each variant and paste the prompt."
echo ""

while IFS= read -r entry; do
    tool=$(echo "$entry" | jq -r '.tool')
    display=$(echo "$entry" | jq -r '.display')
    wt_path=$(echo "$entry" | jq -r '.path')
    COUNT=$((COUNT + 1))

    # Get tool-specific skill reference
    skill=$(jq -r --arg t "$tool" '.[$t].skill // empty' "$TOOLS_FILE")
    instruction=$(jq -r --arg t "$tool" '.[$t].instruction' "$TOOLS_FILE")

    # Build a tool-specific prompt
    if [[ -n "$skill" ]]; then
        skill_hint="Start by invoking $skill to guide your process. "
    else
        skill_hint=""
    fi

    cat <<PROMPT_EOF
### Terminal Tab $COUNT — $display
\`\`\`bash
cd $wt_path
claude
\`\`\`
Then paste:
\`\`\`
Read BRIEF.md for your redesign task. You're one of 5 parallel variants competing to produce the best UI redesign. ${skill_hint}${instruction} Make bold aesthetic choices — don't play it safe. Commit your work when done.
\`\`\`

PROMPT_EOF
done < <(jq -c '.[]' "$WT_FILE")
