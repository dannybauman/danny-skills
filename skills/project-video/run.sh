#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

# --- Virtual environment setup ---
if [ ! -d "$VENV_DIR" ]; then
    echo "Setting up virtual environment..."
    if command -v uv &>/dev/null; then
        uv venv "$VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
    fi
fi

source "$VENV_DIR/bin/activate"

# Install deps if needed (check for Pillow as sentinel)
if ! python3 -c "import PIL" &>/dev/null; then
    echo "Installing dependencies..."
    if command -v uv &>/dev/null; then
        uv pip install -r "$REQUIREMENTS"
    else
        pip install -q -r "$REQUIREMENTS"
    fi
fi

# --- Run the generator, passing all args through ---
python3 "$SCRIPT_DIR/scripts/generate_video.py" "$@"
