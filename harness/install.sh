#!/usr/bin/env bash
# Harness build script executed inside builder container
set -euo pipefail

echo "==> Setting up Python virtual environment at /opt/harness/venv..."
uv venv --python 3.12 /opt/harness/venv

echo "==> Installing Python dependencies..."
uv pip install --python /opt/harness/venv/bin/python -r requirements.txt

echo "==> Verifying installation..."
/opt/harness/venv/bin/python -c "import openai, websockets, pydantic, aiohttp; print('All core modules imported successfully.')"
echo "==> Harness setup complete."
