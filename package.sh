#!/bin/bash
set -e
if [ -z "$1" ]; then
    echo "Usage: ./package.sh <skill-name>"
    exit 1
fi
SKILL="$1"
if [ ! -d "skills/$SKILL" ]; then
    echo "Error: Directory 'skills/$SKILL' not found"
    exit 1
fi
ZIP_FILE="${SKILL}.zip"
rm -f "$ZIP_FILE"
zip -r "$ZIP_FILE" "skills/$SKILL/" \
    -x "*/.venv/*" "*/output/*" "*/input/*" "*/.env" \
    "*/__pycache__/*" "*/.DS_Store" "*/node_modules/*" \
    "*/.git/*" "*/deps/*" "*.pyc"
COUNT=$(zipinfo -1 "$ZIP_FILE" | wc -l | tr -d ' ')
echo ""
echo "Packaged: $ZIP_FILE ($COUNT files)"
if [ "$COUNT" -gt 200 ]; then
    echo "WARNING: $COUNT files exceeds Claude.ai's 200 file limit!"
    exit 1
else
    echo "Ready to upload to Claude.ai"
fi
