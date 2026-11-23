#!/usr/bin/env bash
# Runs dev tasks evaluation and exports artifacts
set -euo pipefail

ENV_FILE="${1:-local.env}"
shift || true
EXTRA_ARGS="$@"

echo "==> Running dev set evaluation..."
cd ple
uv run python eval/run.py ../harness --env-file "../$ENV_FILE" $EXTRA_ARGS
