#!/usr/bin/env bash
# new-project.sh — Create a new Apps Script Drive Viewer project from the starter.
#
# Usage:
#   ./new-project.sh <project-name> [<target-parent-dir>]
#
# Examples:
#   ./new-project.sh staffing-matrix-viewer ~/Source/
#   ./new-project.sh my-dashboard ~/projects/
#
# Creates <target-parent-dir>/<project-name>/ with all starter files, pre-fills
# the project name in Code.gs, and prints next-steps pointing at the README.

set -euo pipefail

if [ $# -lt 1 ]; then
  cat <<EOF
Usage: $0 <project-name> [<target-parent-dir>]

Creates a new Apps Script Drive Viewer project from the starter template.

Examples:
  $0 staffing-matrix-viewer ~/Source/
  $0 my-dashboard ~/projects/

If <target-parent-dir> is omitted, uses the current directory.
EOF
  exit 1
fi

PROJECT_NAME="$1"
TARGET_PARENT="${2:-$PWD}"

# Expand ~ in the target path
TARGET_PARENT="${TARGET_PARENT/#\~/$HOME}"

PROJECT_DIR="$TARGET_PARENT/$PROJECT_NAME"

# Resolve the skill directory (one level up from this script's location)
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STARTER_DIR="$SKILL_DIR/assets/starter-project"

if [ ! -d "$STARTER_DIR" ]; then
  echo "Error: starter project not found at $STARTER_DIR"
  echo "Is the skill installed correctly?"
  exit 1
fi

if [ -e "$PROJECT_DIR" ]; then
  echo "Error: $PROJECT_DIR already exists. Pick a different name or location."
  exit 1
fi

mkdir -p "$TARGET_PARENT"
cp -r "$STARTER_DIR" "$PROJECT_DIR"

# Make scripts executable
chmod +x "$PROJECT_DIR/deploy-helper.sh"

# Pre-fill the project title in Code.gs
sed -i.bak "s|Tool Name|$PROJECT_NAME|g" "$PROJECT_DIR/Code.gs" "$PROJECT_DIR/Index.html" "$PROJECT_DIR/README.md"
find "$PROJECT_DIR" -name "*.bak" -delete

cat <<EOF

✓ Created project at: $PROJECT_DIR

Next steps:
  cd "$PROJECT_DIR"
  cat README.md

The README walks through:
  1. Install clasp (~2 min)
  2. Place your data file in Drive (~3 min)
  3. Create the Apps Script project (~2 min)
  4. Wire the data file ID (~1 min)
  5. Drop your HTML/JS into Index.html (varies)
  6. Push and deploy (~3 min)
  7. Set domain restriction (~2 min)
  8. Test as a non-owner Workspace user (~3 min)

Roughly 30 min from here to a working URL.
EOF
