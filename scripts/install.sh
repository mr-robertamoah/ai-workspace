#!/usr/bin/env bash

set -euo pipefail

python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

echo "ai-workspace development environment is ready."
