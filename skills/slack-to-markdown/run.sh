#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

# Only setup runs inside the skill dir. The exporter keeps the caller's cwd,
# or a relative --output-dir lands inside this repo instead of where you ran it
(
cd "$DIR"

# Dependency setup
if command -v uv &> /dev/null; then
    if [ ! -d ".venv" ]; then
        uv venv .venv --quiet
    fi
    uv pip install -r requirements.txt --quiet
else
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    .venv/bin/pip install -r requirements.txt --quiet
fi

# Ensure output dir exists
mkdir -p output
)

# Load local .env if it exists
if [ -f "$DIR/.env" ]; then
    set -a
    source "$DIR/.env"
    set +a
fi

"$DIR/.venv/bin/python" "$DIR/scripts/export_slack.py" "$@"
