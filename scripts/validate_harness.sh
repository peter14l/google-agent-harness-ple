#!/usr/bin/env bash
# Runs the official kit check smoke tests on the harness
set -euo pipefail

ENV_FILE="${1:-local.env}"
echo "==> Running kit check on harness using $ENV_FILE..."
cd ple
uv run python -m kit check ../harness --env-file "../$ENV_FILE"
