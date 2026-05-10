#!/usr/bin/env bash
# build.sh — build a self-contained ai-workspace binary using PyInstaller
# Usage: bash scripts/build.sh
# Output: dist/ai-workspace (single executable, ~15-20MB)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$REPO_DIR/src/ai_workspace/data"

echo "Installing build dependencies..."
pip install -q pyinstaller

echo "Building binary..."
pyinstaller \
    --onefile \
    --name ai-workspace \
    --add-data "$DATA_DIR/skills:ai_workspace/data/skills" \
    --add-data "$DATA_DIR/standards:ai_workspace/data/standards" \
    --hidden-import "ruamel.yaml" \
    --hidden-import "ruamel.yaml.comments" \
    --hidden-import "ruamel.yaml.representer" \
    --hidden-import "pydantic" \
    --hidden-import "typer" \
    --hidden-import "rich" \
    "$REPO_DIR/src/ai_workspace/cli/main.py"

echo ""
echo "Binary built: $REPO_DIR/dist/ai-workspace"
echo "Install system-wide: sudo cp dist/ai-workspace /usr/local/bin/"
echo "Or user-local:       cp dist/ai-workspace ~/.local/bin/"
