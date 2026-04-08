#!/usr/bin/env bash
# Analyze project to detect frontend files, backend entry points, and framework.
# Reads CLAUDE.md for hints about which subdirectory is the active app.
# Output: JSON scope object to stdout.
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required for scope.sh" >&2
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

# ── Detect active subdirectory from CLAUDE.md ──
APP_ROOT="$REPO_ROOT"
CLAUDE_MD=""
for candidate in "$REPO_ROOT/CLAUDE.md" "$REPO_ROOT/.claude/CLAUDE.md"; do
    [[ -f "$candidate" ]] && CLAUDE_MD="$candidate" && break
done

if [[ -n "$CLAUDE_MD" ]]; then
    # Look for hints like "Primary app code: bmad/app/" or "All new work should happen in X"
    active_dir=$(grep -oiE '(primary|active|main|production)\s+(app\s+)?(code|directory|dir|work)[^`]*`([^`]+)`' "$CLAUDE_MD" 2>/dev/null | grep -oE '`[^`]+`' | tr -d '`' | head -1)
    if [[ -z "$active_dir" ]]; then
        # Try "All new work should happen in X"
        active_dir=$(grep -oiE '(all\s+new\s+work|development)\s+.*\bin\s+`([^`]+)`' "$CLAUDE_MD" 2>/dev/null | grep -oE '`[^`]+`' | tr -d '`' | head -1)
    fi
    if [[ -n "$active_dir" ]] && [[ -d "$REPO_ROOT/$active_dir" ]]; then
        APP_ROOT="$REPO_ROOT/$active_dir"
        echo "  Scoped to: $active_dir (from CLAUDE.md)" >&2
    fi
fi

# ── Detect if monorepo (multiple package.json at top level) ──
if [[ "$APP_ROOT" == "$REPO_ROOT" ]]; then
    pkg_count=$(find "$REPO_ROOT" -maxdepth 2 -name "package.json" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
    if [[ "$pkg_count" -gt 2 ]]; then
        # Monorepo detected — look for the one with a dev script and most source files
        best_dir=""
        best_count=0
        while IFS= read -r pkg; do
            dir=$(dirname "$pkg")
            if jq -e '.scripts.dev' "$pkg" &>/dev/null; then
                count=$(find "$dir/src" -type f 2>/dev/null | wc -l | tr -d ' ')
                if [[ "$count" -gt "$best_count" ]]; then
                    best_count=$count
                    best_dir="$dir"
                fi
            fi
        done < <(find "$REPO_ROOT" -maxdepth 2 -name "package.json" -not -path "*/node_modules/*")
        if [[ -n "$best_dir" && "$best_count" -gt 5 ]]; then
            APP_ROOT="$best_dir"
            rel=$(echo "$APP_ROOT" | sed "s|$REPO_ROOT/||")
            echo "  Monorepo detected — scoped to: $rel (largest app with dev script)" >&2
        fi
    fi
fi

# ── Find files relative to APP_ROOT ──

# Find HTML files
HTML_FILES=$(find "$APP_ROOT" -maxdepth 4 -name "*.html" \
    -not -path "*/node_modules/*" -not -path "*/.venv/*" \
    -not -path "*/dist/*" -not -path "*/build/*" \
    | sed "s|$REPO_ROOT/||" | sort)

# Find CSS files
CSS_FILES=$(find "$APP_ROOT" -maxdepth 4 \( -name "*.css" -o -name "*.scss" -o -name "*.less" \) \
    -not -path "*/node_modules/*" -not -path "*/.venv/*" \
    -not -path "*/dist/*" -not -path "*/build/*" \
    | sed "s|$REPO_ROOT/||" | sort)

# Find JS/TS frontend files (components, pages, layouts — not hooks/lib/stores)
JS_FILES=$(find "$APP_ROOT" -maxdepth 6 \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.vue" -o -name "*.svelte" \) \
    -not -path "*/node_modules/*" -not -path "*/.venv/*" \
    -not -path "*/dist/*" -not -path "*/build/*" \
    -not -path "*/hooks/*" -not -path "*/lib/*" -not -path "*/stores/*" \
    -not -path "*/test/*" -not -path "*/tests/*" -not -path "*/__tests__/*" \
    -not -name "*.config.*" -not -name "*.test.*" -not -name "*.spec.*" \
    | sed "s|$REPO_ROOT/||" | sort)

# Off-limits: hooks, lib, stores, tests — things that shouldn't change in a visual redesign
OFF_LIMITS_FILES=""
for subdir in hooks lib stores utils services api test tests __tests__; do
    found=$(find "$APP_ROOT" -maxdepth 4 -type d -name "$subdir" \
        -not -path "*/node_modules/*" 2>/dev/null | sed "s|$REPO_ROOT/||")
    [[ -n "$found" ]] && OFF_LIMITS_FILES="$OFF_LIMITS_FILES"$'\n'"$found/"
done

# Detect framework from the app root's package.json
FRAMEWORK="unknown"
PKG="$APP_ROOT/package.json"
[[ ! -f "$PKG" ]] && PKG="$REPO_ROOT/package.json"
if [[ -f "$PKG" ]]; then
    if jq -e '.dependencies.react or .devDependencies.react' "$PKG" &>/dev/null; then
        if jq -e '.dependencies.vite or .devDependencies.vite' "$PKG" &>/dev/null; then
            FRAMEWORK="react-vite"
        elif jq -e '.dependencies.next or .devDependencies.next' "$PKG" &>/dev/null; then
            FRAMEWORK="nextjs"
        else
            FRAMEWORK="react"
        fi
    elif jq -e '.dependencies.vue or .devDependencies.vue' "$PKG" &>/dev/null; then
        FRAMEWORK="vue"
    elif jq -e '.dependencies.svelte or .devDependencies.svelte' "$PKG" &>/dev/null; then
        FRAMEWORK="svelte"
    else
        FRAMEWORK="node"
    fi
elif [[ -n "$HTML_FILES" ]]; then
    FRAMEWORK="static"
fi

# Detect backend entry
BACKEND=""
for candidate in app.py wsgi.py server.js server.ts manage.py; do
    found=$(find "$APP_ROOT" -maxdepth 3 -name "$candidate" -not -path "*/node_modules/*" | head -1)
    if [[ -n "$found" ]]; then
        BACKEND=$(echo "$found" | sed "s|$REPO_ROOT/||")
        break
    fi
done

# Build JSON — write to temp file to avoid bash variable expansion issues
TMPFILE=$(mktemp)
files_redesign=$(echo "$HTML_FILES"$'\n'"$CSS_FILES"$'\n'"$JS_FILES" | jq -R -s 'split("\n") | map(select(length > 0))')
off_limits=$(echo "$OFF_LIMITS_FILES" | jq -R -s 'split("\n") | map(select(length > 0))')
[[ -n "$BACKEND" ]] && off_limits=$(echo "$off_limits" | jq --arg b "$BACKEND" '. + [$b]')

cat > "$TMPFILE" <<SCOPE_EOF
{
  "files_to_redesign": $files_redesign,
  "files_off_limits": $off_limits,
  "backend": $(echo "$BACKEND" | jq -R '.'),
  "framework": "$FRAMEWORK",
  "repo_root": "$REPO_ROOT",
  "app_root": $(echo "$APP_ROOT" | sed "s|$REPO_ROOT/||" | jq -R '.')
}
SCOPE_EOF

cat "$TMPFILE"
rm -f "$TMPFILE"
