#!/usr/bin/env bash
# Starts local LiteLLM model proxy for google-cloud models backed by Vertex AI
set -euo pipefail

ENV_FILE="${1:-local.env}"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

if [ -z "${VERTEXAI_PROJECT:-}" ]; then
    echo "Error: VERTEXAI_PROJECT must be set in $ENV_FILE or environment."
    exit 1
fi

MODEL_PROXY_KEY="${MODEL_PROXY_KEY:-$(openssl rand -hex 24)}"
export MODEL_PROXY_KEY

echo "==> Starting local model proxy on port 4000..."
echo "==> Model Proxy Key: $MODEL_PROXY_KEY"
cd ple
bash kit/model_proxy/start.sh
