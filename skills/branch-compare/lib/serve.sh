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

# Load environment overrides for local preview
# Web apps often hardcode Docker-internal or production URLs for backends.
# A .branch-compare.env file lets users set correct local URLs.
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

detect_serve_cmd() {
    local dir="$1"
    local port="$2"

    # 1. package.json with build + preview
    if [[ -f "$dir/package.json" ]]; then
        if jq -e '.scripts.build and .scripts.preview' "$dir/package.json" &>/dev/null; then
            echo "cd '$dir' && npm install --silent && npm run build --silent && npm run preview -- --port $port"
            return
        fi
        # 2. package.json with dev
        if jq -e '.scripts.dev' "$dir/package.json" &>/dev/null; then
            echo "cd '$dir' && npm install --silent && npm run dev -- --port $port"
            return
        fi
    fi

    # 3. app.py or wsgi.py (Flask/Python)
    if [[ -f "$dir/app.py" ]] || [[ -f "$dir/wsgi.py" ]]; then
        local entry="app.py"
        [[ -f "$dir/wsgi.py" ]] && entry="wsgi.py"
        echo "cd '$dir' && FLASK_RUN_PORT=$port python3 -c \"import sys;sys.path.insert(0,'.');from app import app;app.run(host='127.0.0.1',port=$port,debug=False)\""
        return
    fi

    # 4. manage.py (Django)
    if [[ -f "$dir/manage.py" ]]; then
        echo "cd '$dir' && python3 manage.py runserver 0.0.0.0:$port"
        return
    fi

    # 5. index.html anywhere common
    for subdir in "" "public" "dist" "build" "src"; do
        local check="$dir"
        [[ -n "$subdir" ]] && check="$dir/$subdir"
        if [[ -f "$check/index.html" ]]; then
            echo "cd '$check' && python3 -m http.server $port"
            return
        fi
    done

    # 6. Look for app entry in common subdirs (apps/hub/app.py pattern)
    local found_app
    found_app=$(find "$dir" -maxdepth 3 -name "app.py" -not -path "*/node_modules/*" -not -path "*/.venv/*" | head -1)
    if [[ -n "$found_app" ]]; then
        local app_dir=$(dirname "$found_app")
        echo "cd '$app_dir' && python3 -c \"import sys;sys.path.insert(0,'.');from app import app;app.run(host='127.0.0.1',port=$port,debug=False)\""
        return
    fi

    echo ""
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
        # Track as skill-created
        jq --arg k "$name" --arg v "$WT_PATH" '. + {($k): $v}' "$WT_FILE" > "$WT_FILE.tmp" && mv "$WT_FILE.tmp" "$WT_FILE"
    else
        echo "  Using existing worktree: $WT_PATH" >&2
    fi

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

    # Build step for npm projects
    if [[ -f "$WT_PATH/package.json" ]] && jq -e '.scripts.build' "$WT_PATH/package.json" &>/dev/null; then
        echo "  Building $name..." >&2
        (cd "$WT_PATH" && npm install --silent 2>&1 && npm run build --silent 2>&1) >&2 || {
            echo "  WARN: build failed for $name" >&2
        }
    fi

    # Start server
    LOG="$PIDS_DIR/$name.log"
    eval "$SERVE_CMD" > "$LOG" 2>&1 &
    PID=$!
    echo "$PID" > "$PIDS_DIR/$name.pid"
    jq --arg k "$name" --argjson v "$PORT" '. + {($k): $v}' "$PORTS_FILE" > "$PORTS_FILE.tmp" && mv "$PORTS_FILE.tmp" "$PORTS_FILE"
    echo "  Started $name on port $PORT (PID $PID)" >&2

    # Wait for server to respond
    for i in $(seq 1 10); do
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
