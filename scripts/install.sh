#!/usr/bin/env bash
# install.sh — install ai-workspace as a global command
# Usage: bash scripts/install.sh
# For development setup: bash scripts/install.sh --dev

set -euo pipefail

DEV=false
[[ "${1:-}" == "--dev" ]] && DEV=true

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

if $DEV; then
    echo "Setting up development environment..."
    python3 -m venv "$REPO_DIR/.venv"
    "$REPO_DIR/.venv/bin/pip" install -q -e "$REPO_DIR/.[dev]"
    echo "Done. Activate with: source $REPO_DIR/.venv/bin/activate"
    exit 0
fi

if command -v pipx &>/dev/null; then
    echo "Installing via pipx..."
    pipx install "$REPO_DIR"
    echo "Done. Run: ai-workspace --help"
    exit 0
fi

echo "pipx not found — installing into managed venv at ~/.ai-workspace-env"
python3 -m venv "$HOME/.ai-workspace-env"
"$HOME/.ai-workspace-env/bin/pip" install -q "$REPO_DIR"
ln -sf "$HOME/.ai-workspace-env/bin/ai-workspace" "$INSTALL_DIR/ai-workspace"

# Ensure ~/.local/bin is on PATH
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo ""
    echo "Add this to your shell profile (~/.bashrc or ~/.zshrc):"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "Then reload: source ~/.bashrc"
fi

echo "Done. Run: ai-workspace --help"
