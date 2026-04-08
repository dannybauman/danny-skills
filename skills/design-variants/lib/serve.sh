#!/usr/bin/env bash
# Create worktrees and start servers for each branch.
# Usage: serve.sh <skill_dir> <branches_json> [base_port]
set -euo pipefail

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required for serve.sh" >&2
    exit 1
fi

SKILL_DIR="$1"
BRANCHES_JSON="$2"
BASE_PORT="${3:-5001}"
STATE_DIR="$SKILL_DIR/.state"
PIDS_DIR="$STATE_DIR/pids"
mkdir -p "$PIDS_DIR"

REPO_ROOT=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_ROOT")
PARENT_DIR=$(dirname "$REPO_ROOT")

# ── Detect app subdirectory from CLAUDE.md ──
APP_SUBDIR=""
for candidate in "$REPO_ROOT/CLAUDE.md" "$REPO_ROOT/.claude/CLAUDE.md"; do
    if [[ -f "$candidate" ]]; then
        detected=$(grep -oiE '(primary|active|main|production)\s+(app\s+)?(code|directory|dir|work)[^`]*`([^`]+)`' "$candidate" 2>/dev/null | grep -oE '`[^`]+`' | tr -d '`' | head -1)
        if [[ -z "$detected" ]]; then
            detected=$(grep -oiE '(all\s+new\s+work|development)\s+.*\bin\s+`([^`]+)`' "$candidate" 2>/dev/null | grep -oE '`[^`]+`' | tr -d '`' | head -1)
        fi
        if [[ -n "$detected" ]] && [[ -d "$REPO_ROOT/$detected" ]]; then
            APP_SUBDIR="$detected"
            echo "  App directory: $APP_SUBDIR (from CLAUDE.md)" >&2
        fi
        break
    fi
done

# Load environment overrides
ENV_FILE="${BRANCH_COMPARE_ENV:-$REPO_ROOT/.branch-compare.env}"
if [[ -f "$ENV_FILE" ]]; then
    echo "  Loading env overrides from $ENV_FILE" >&2
    set -a
    source "$ENV_FILE"
    set +a
fi

# Load or init worktrees tracking
WT_FILE="$STATE_DIR/worktrees.json"
[[ -f "$WT_FILE" ]] || echo '{}' > "$WT_FILE"

# Load or init ports
PORTS_FILE="$STATE_DIR/ports.json"
[[ -f "$PORTS_FILE" ]] || echo '{}' > "$PORTS_FILE"

# ── Copy gitignored env files to a worktree ──
copy_env_files() {
    local target_dir="$1"
    local source_dir="$REPO_ROOT"

    # If app is in a subdirectory, scope to that
    if [[ -n "$APP_SUBDIR" ]]; then
        source_dir="$REPO_ROOT/$APP_SUBDIR"
        target_dir="$target_dir/$APP_SUBDIR"
    fi

    # Copy .env* files that exist in source but not in target
    for env_file in "$source_dir"/.env "$source_dir"/.env.local "$source_dir"/.env.development "$source_dir"/.env.development.local; do
        if [[ -f "$env_file" ]]; then
            local basename_env=$(basename "$env_file")
            if [[ ! -f "$target_dir/$basename_env" ]]; then
                cp "$env_file" "$target_dir/$basename_env"
                echo "  Copied $basename_env to worktree" >&2
            fi
        fi
    done
}

detect_serve_cmd() {
    local dir="$1"
    local port="$2"

    # If app is in a subdirectory, look there first
    local app_dir="$dir"
    if [[ -n "$APP_SUBDIR" ]] && [[ -d "$dir/$APP_SUBDIR" ]]; then
        app_dir="$dir/$APP_SUBDIR"
    fi

    # 1. package.json with dev script in app dir
    if [[ -f "$app_dir/package.json" ]]; then
        if jq -e '.scripts.dev' "$app_dir/package.json" &>/dev/null; then
            echo "cd '$app_dir' && npm run dev -- --port $port"
            return
        fi
        if jq -e '.scripts.build and .scripts.preview' "$app_dir/package.json" &>/dev/null; then
            echo "cd '$app_dir' && npm run build --silent && npm run preview -- --port $port"
            return
        fi
    fi

    # 2. package.json at worktree root
    if [[ "$app_dir" != "$dir" ]] && [[ -f "$dir/package.json" ]]; then
        if jq -e '.scripts.dev' "$dir/package.json" &>/dev/null; then
            echo "cd '$dir' && npm run dev -- --port $port"
            return
        fi
    fi

    # 3. Python apps
    if [[ -f "$app_dir/app.py" ]] || [[ -f "$app_dir/wsgi.py" ]]; then
        local entry="app.py"
        [[ -f "$app_dir/wsgi.py" ]] && entry="wsgi.py"
        echo "cd '$app_dir' && FLASK_RUN_PORT=$port python3 -c \"import sys;sys.path.insert(0,'.');from app import app;app.run(host='127.0.0.1',port=$port,debug=False)\""
        return
    fi

    # 4. manage.py (Django)
    if [[ -f "$app_dir/manage.py" ]]; then
        echo "cd '$app_dir' && python3 manage.py runserver 0.0.0.0:$port"
        return
    fi

    # 5. Static HTML
    for subdir in "" "public" "dist" "build" "src"; do
        local check="$app_dir"
        [[ -n "$subdir" ]] && check="$app_dir/$subdir"
        if [[ -f "$check/index.html" ]]; then
            echo "cd '$check' && python3 -m http.server $port"
            return
        fi
    done

    echo ""
}

# ── Ensure dependencies are installed ──
ensure_deps() {
    local dir="$1"
    local app_dir="$dir"
    if [[ -n "$APP_SUBDIR" ]] && [[ -d "$dir/$APP_SUBDIR" ]]; then
        app_dir="$dir/$APP_SUBDIR"
    fi

    if [[ -f "$app_dir/package.json" ]] && [[ ! -d "$app_dir/node_modules" ]]; then
        echo "  Installing dependencies..." >&2
        (cd "$app_dir" && npm install --silent 2>&1) >&2 || {
            echo "  WARN: npm install failed" >&2
        }
    fi
}

RESULTS="["
PORT=$BASE_PORT
COUNT=0

while IFS= read -r entry; do
    name=$(echo "$entry" | jq -r '.name')
    branch=$(echo "$entry" | jq -r '.branch')

    # Check for existing worktree
    WT_PATH="$PARENT_DIR/${REPO_NAME}-${name}"
    EXISTING_WT=$(git worktree list --porcelain | grep -A1 "worktree" | grep "$WT_PATH" || true)

    if [[ -z "$EXISTING_WT" ]] && [[ ! -d "$WT_PATH" ]]; then
        echo "  Creating worktree: $WT_PATH (branch: $branch)" >&2
        git worktree add "$WT_PATH" "$branch" 2>&1 >&2 || {
            echo "  WARN: failed to create worktree for $branch" >&2
            PORT=$((PORT + 1))
            continue
        }
        jq --arg k "$name" --arg v "$WT_PATH" '. + {($k): $v}' "$WT_FILE" > "$WT_FILE.tmp" && mv "$WT_FILE.tmp" "$WT_FILE"
    else
        echo "  Using existing worktree: $WT_PATH" >&2
    fi

    # Copy env files to worktree
    copy_env_files "$WT_PATH"

    # Ensure deps installed
    ensure_deps "$WT_PATH"

    # Check if already running on a port
    if [[ -f "$PIDS_DIR/$name.pid" ]]; then
        OLD_PID=$(cat "$PIDS_DIR/$name.pid")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            OLD_PORT=$(jq -r --arg k "$name" '.[$k] // empty' "$PORTS_FILE")
            echo "  $name already running on port $OLD_PORT (PID $OLD_PID)" >&2
            [[ $COUNT -gt 0 ]] && RESULTS="$RESULTS,"
            RESULTS="$RESULTS{\"name\":\"$name\",\"branch\":\"$branch\",\"port\":$OLD_PORT,\"pid\":$OLD_PID,\"url\":\"http://localhost:$OLD_PORT\"}"
            COUNT=$((COUNT + 1))
            PORT=$((PORT + 1))
            continue
        fi
    fi

    # Detect serve command
    SERVE_CMD=$(detect_serve_cmd "$WT_PATH" "$PORT")
    if [[ -z "$SERVE_CMD" ]]; then
        echo "  WARN: cannot detect how to serve $name, skipping" >&2
        PORT=$((PORT + 1))
        continue
    fi

    # Start server
    LOG="$PIDS_DIR/$name.log"
    eval "$SERVE_CMD" > "$LOG" 2>&1 &
    PID=$!
    echo "$PID" > "$PIDS_DIR/$name.pid"
    jq --arg k "$name" --argjson v "$PORT" '. + {($k): $v}' "$PORTS_FILE" > "$PORTS_FILE.tmp" && mv "$PORTS_FILE.tmp" "$PORTS_FILE"
    echo "  Started $name on port $PORT (PID $PID)" >&2

    # Wait for server to respond
    for i in $(seq 1 15); do
        if curl -s -o /dev/null -w '' "http://localhost:$PORT/" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    [[ $COUNT -gt 0 ]] && RESULTS="$RESULTS,"
    RESULTS="$RESULTS{\"name\":\"$name\",\"branch\":\"$branch\",\"port\":$PORT,\"pid\":$PID,\"url\":\"http://localhost:$PORT\"}"
    COUNT=$((COUNT + 1))
    PORT=$((PORT + 1))
done < <(echo "$BRANCHES_JSON" | jq -c '.[]')

RESULTS="$RESULTS]"
echo "$RESULTS"
