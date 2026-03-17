#!/bin/bash
set -e

# Directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR/maptoposter"
VENV_DIR="$SCRIPT_DIR/.venv"
REPO_URL="https://github.com/originalankur/maptoposter"

# 1. Ensure Repo Directory Exists
if [ ! -d "$REPO_DIR" ]; then
    echo "Error: maptoposter directory missing. This skill requires the vendored code to be present."
    exit 1
fi

# 2. Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed."
    exit 1
fi

# 3. Setup Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up virtual environment..."
    if command -v uv &> /dev/null; then
        echo "Using uv for high-speed installation..."
        uv venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        uv pip install -r "$REPO_DIR/requirements.txt"
    else
        echo "Note: This may take a few minutes for OSMnx and Geopandas."
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip
        "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"
    fi
fi

# 4. Execute
export OUTPUT_DIR="$SCRIPT_DIR/output"
mkdir -p "$OUTPUT_DIR"

# We need to run it from the repo directory because it expects themes/ and fonts/ folders relative to CWD
cd "$REPO_DIR"
../.venv/bin/python create_map_poster.py "$@"
