#!/usr/bin/env bash
# Scaffold a new short-film project from the starter kit.
#   new-project.sh <target-dir> [name]
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
target="${1:?usage: new-project.sh <target-dir> [name]}"
name="${2:-$(basename "$target")}"
[[ "$name" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "name must be lowercase letters, digits and hyphens: $name" >&2; exit 2; }
mkdir -p "$target"
[ -e "$target/video.json" ] && { echo "refusing to overwrite: $target/video.json already exists" >&2; exit 1; }
cp -R "$here/starter/." "$target/"
python3 - "$target/video.json" "$name" <<'PY'
import json, sys
p, name = sys.argv[1], sys.argv[2]
v = json.load(open(p)); v["name"] = name
json.dump(v, open(p, "w"), indent=2); open(p, "a").write("\n")
PY
mkdir -p "$target/audio/stems" "$target/output"
cd "$target"
if command -v npm >/dev/null 2>&1; then
  npm install --silent --no-audit --no-fund
  # one headless browser build (about 190 MB, not a model). Skipped when a matching build is already cached
  npx --yes playwright-core install chromium-headless-shell >/dev/null 2>&1 || echo "note: run 'npx playwright-core install chromium-headless-shell' before rendering"
else
  echo "note: npm not found; install Node 22+ and run 'npm install' in $target"
fi
cat <<MSG
scaffolded $target
  bash tools/preflight.sh                      # is the machine fit to render?
  node tools/build.mjs                         # -> output/$name.html
  node tools/shot.mjs /tmp/sheet.png 0.25 1 3 5 7    # look at frames
  node tools/render.mjs --workers 2            # -> output/$name.mp4
Next: write BRIEF.md, then audio/CUES.md, then replace src/50-scene.js.
MSG
