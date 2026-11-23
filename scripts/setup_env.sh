#!/usr/bin/env bash
# Sets up the local environment: uv, harbor, and dependencies
set -euo pipefail

echo "==> Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but not installed. Aborting."; exit 1; }
command -v uv >/dev/null 2>&1 || {
    echo "==> Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
}

echo "==> Installing Harbor 0.20.0 with websockets..."
uv tool install harbor==0.20.0 --with websockets

echo "==> Initializing local configuration..."
if [ ! -f "local.env" ]; then
    cp local.env.example local.env
    echo "Created local.env from template. Please update with your credentials."
fi

echo "==> Setup finished successfully."
