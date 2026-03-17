#!/bin/bash
set -e

# Directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
PYTHON_SCRIPT="$SCRIPT_DIR/scripts/scaffold_stac.py"

# Make sure requirements exists (or create minimal if missing)
if [ ! -f "$REQUIREMENTS" ]; then
    echo "requests" > "$REQUIREMENTS"
    echo "pystac" >> "$REQUIREMENTS"
    echo "xarray" >> "$REQUIREMENTS"
    echo "netCDF4" >> "$REQUIREMENTS"
    echo "h5netcdf" >> "$REQUIREMENTS"
fi

# Function to check if python3 is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is required but not installed."
        exit 1
    fi
}

# Ensure Virtual Environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        echo "Installing dependencies..."
        "$VENV_DIR/bin/pip" install -q -r "$REQUIREMENTS"
    fi
}

# Main Execution
check_python
setup_venv

echo "Running STAC Project Scaffolder..."
"$VENV_DIR/bin/python" "$PYTHON_SCRIPT" "$@"
