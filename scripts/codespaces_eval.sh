#!/usr/bin/env bash
# One-click evaluation script for GitHub Codespaces or any Linux VM
set -euo pipefail

echo "=========================================================="
echo "  PLE Autonomous Engineering Agent: Codespaces Evaluator  "
echo "=========================================================="

# 1. Environment & Tokens
export HF_TOKEN="${HF_TOKEN:-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}"
export GEMINI_API_KEY="${GEMINI_API_KEY:-AQ.Ab8RN6JlKBesyWQN1w5hk8Sdawucyrbtvb2NPj8UGTUBYj8ryw}"
export MODEL_PROXY_KEY="codespaces-proxy-key"
export MODEL_PROXY_URL="http://localhost:4000"

# 2. Check / Install uv
if ! command -v uv >/dev/null 2>&1; then
    echo "==> Installing Astral uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 3. Check / Install Harbor
if ! command -v harbor >/dev/null 2>&1; then
    echo "==> Installing Harbor 0.20.0 with WebSockets..."
    uv tool install harbor==0.20.0 --with websockets
    export PATH="$HOME/.local/bin:$PATH"
fi

# 4. Verify Docker
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running or accessible. In Codespaces, Docker starts automatically."
    exit 1
fi
echo "==> Docker is active and running."

# 5. Clone tasks repository using Git Smart HTTP to avoid HF REST 429 rate limits
TASKS_CACHE_DIR="/tmp/ple-tasks"
if [ ! -d "$TASKS_CACHE_DIR/tasks" ]; then
    echo "==> Fetching PLE tasks dataset via Git (bypassing Hugging Face REST rate limits)..."
    GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "https://oauth2:${HF_TOKEN}@huggingface.co/datasets/google/physical-engineerings-last-exam" "$TASKS_CACHE_DIR"
else
    echo "==> PLE tasks cache already present at $TASKS_CACHE_DIR"
fi

# 6. Ensure LiteLLM is installed upfront
if ! command -v litellm >/dev/null 2>&1; then
    echo "==> Installing litellm with proxy support..."
    uv tool install 'litellm[proxy]'
    export PATH="$HOME/.local/bin:$PATH"
fi

# Stop any previous proxy instance on port 4000
pkill -f "litellm" 2>/dev/null || true
sleep 1

# Start LiteLLM Gemini Proxy on port 4000 (bind to 0.0.0.0 so Docker bridge 172.17.0.1 reaches it)
echo "==> Starting LiteLLM Gemini Proxy on 0.0.0.0:4000..."
litellm \
    --config .github/litellm_gemini_proxy.yaml \
    --host 0.0.0.0 --port 4000 > proxy.log 2>&1 &
PROXY_PID=$!

echo "==> Waiting for LiteLLM proxy to initialize..."
READY=0
for i in {1..60}; do
    if curl -s http://127.0.0.1:4000/health >/dev/null 2>&1; then
        echo "==> Proxy is healthy and ready on port 4000."
        READY=1
        break
    fi
    sleep 1
done

if [ "$READY" -ne 1 ]; then
    echo "Error: LiteLLM proxy failed to start within 60s. Log output:"
    cat proxy.log
    exit 1
fi

BRIDGE_IP="172.17.0.1"
if curl -s "http://${BRIDGE_IP}:4000/health" >/dev/null 2>&1; then
    echo "==> Docker bridge can reach LiteLLM at ${BRIDGE_IP}:4000."
fi

# 7. Prepare local.env
cat <<EOF > local.env
HF_TOKEN=${HF_TOKEN}
MODEL_PROXY_URL=${MODEL_PROXY_URL}
MODEL_PROXY_KEY=${MODEL_PROXY_KEY}
EOF

# 8. Execute Harbor Dev Set Evaluation
echo "==> Executing Harbor Dev Set Evaluation..."
cd ple
uv run python eval/run.py .. \
    --env-file ../local.env \
    --tasks-dir "$TASKS_CACHE_DIR/tasks" \
    "$@"

cd ..
echo "=========================================================="
echo "  Evaluation completed! Deliverables written to artifacts/ "
echo "=========================================================="
echo "To commit and save your artifacts back to GitHub:"
echo "  git add artifacts/ && git commit -m 'chore: add dev artifacts' && git push"
