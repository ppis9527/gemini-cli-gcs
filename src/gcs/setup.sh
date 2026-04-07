#!/bin/bash
# ~/.gemini/extensions/gcs-guardian/scripts/setup.sh
# GCS Environment Bootstrap (v1.20)

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
VENV_PATH="$PROJECT_ROOT/.gemini/gcs-venv"

echo "GCS: Setting up GCS Guardian Environment..."

# 1. Check dependencies
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 required."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq required."; exit 1; }

# 2. Create venv
if [ ! -d "$VENV_PATH" ]; then
    python3 -m venv "$VENV_PATH"
    echo "GCS: Virtual environment created at $VENV_PATH"
fi

# 3. Install core packages
source "$VENV_PATH/bin/activate"
pip install --quiet tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript
echo "GCS: tree-sitter and language bindings installed."

# 4. Success message
echo "GCS: Setup complete. GCS Distiller ready."
