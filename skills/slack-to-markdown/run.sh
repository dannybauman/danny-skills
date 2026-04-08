#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

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

# Load local .env if it exists
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Ensure output dir exists
mkdir -p output

.venv/bin/python scripts/export_slack.py "$@"
