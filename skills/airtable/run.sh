#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv &> /dev/null; then
    if [ ! -d ".venv" ]; then
        uv venv .venv
    fi
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    fi
    PYTHON=".venv/bin/python"
else
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    PYTHON=".venv/bin/python"
fi

$PYTHON scripts/airtable_cli.py "$@"
