#!/usr/bin/env bash
# Generate and open the switcher HTML page.
# Usage: switcher.sh <skill_dir> <variants_json>
set -euo pipefail

SKILL_DIR="$1"
VARIANTS_JSON="$2"
PAGE_CONFIG="${3:-{}}"
STATE_DIR="$SKILL_DIR/.state"
mkdir -p "$STATE_DIR"

TEMPLATE="$SKILL_DIR/lib/switcher-template.html"
OUTPUT="$STATE_DIR/switcher.html"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "Error: switcher template not found at $TEMPLATE" >&2
    exit 1
fi

# Inject variants JSON and page config into template
sed -e "s|__VARIANTS__|$VARIANTS_JSON|g" -e "s|__PAGE_CONFIG__|$PAGE_CONFIG|g" "$TEMPLATE" > "$OUTPUT"

echo "Switcher ready: $OUTPUT"

# Open in browser
if command -v open &>/dev/null; then
    open "$OUTPUT"
elif command -v xdg-open &>/dev/null; then
    xdg-open "$OUTPUT"
else
    echo "Open in your browser: file://$OUTPUT"
fi
