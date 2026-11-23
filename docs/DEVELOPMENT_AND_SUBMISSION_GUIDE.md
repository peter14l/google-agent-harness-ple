# Development & Submission Guide
## Complete Workflow from Local Testing to Kaggle Submission

---

### 1. Prerequisites & Environment Setup

The evaluation environment mirrors Debian Bookworm in containerized Docker instances. To develop and test locally:

* **Operating System:** Linux, macOS, or Windows with **WSL 2** (Ubuntu 22.04 or 24.04 recommended).
* **Docker:** Docker Desktop or Docker Engine (ensure daemon is running).
  * Minimum recommended VM resources: 6 CPUs, 16 GB RAM, 30 GB free disk space.
* **Python Tooling:**
  * Python 3.12+
  * `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
  * Harbor task runner:
    ```bash
    uv tool install harbor==0.20.0 --with websockets
    ```
* **Hugging Face Account:**
  * Request read access to [google/physical-engineerings-last-exam](https://huggingface.co/datasets/google/physical-engineerings-last-exam).
  * Generate a Read Access Token and set `export HF_TOKEN=hf_...`

---

### 2. Local Model Proxy Setup

For Stage 2 submissions, the evaluation platform injects access to Google-sponsored models. For local development, `kit/model_proxy` runs a local LiteLLM proxy:

#### Option A: Backed by Google Cloud Vertex AI
```bash
gcloud auth application-default login
export VERTEXAI_PROJECT="your-gcp-project-id"
export MODEL_PROXY_KEY=$(openssl rand -hex 24)

# Start proxy in background
bash ple/kit/model_proxy/start.sh &
export MODEL_PROXY_URL=http://localhost:4000
```

#### Option B: Backed by Direct API Keys (OpenAI / Anthropic / Gemini Studio)
Create a `local.env` file in the workspace root:
```ini
MODEL_PROXY_URL=http://localhost:4000
MODEL_PROXY_KEY=test-proxy-key-12345
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIzaSy...
ANTHROPIC_API_KEY=sk-ant-...
HF_TOKEN=hf_...
```

---

### 3. Validating the Harness with `kit check`

Before running full dev tasks, smoke-test your harness bundle:

```bash
cd E:\google-agent-harness-hackathon\ple
uv run python -m kit check ../harness --env-file ../local.env
```

`kit check` performs:
1. **Static Validation:** Validates `submission.yaml`, checks file naming, ensures no exposed secrets or API keys exist in git tracking.
2. **Container Build:** Builds `/opt/harness` in the Debian Bookworm builder image.
3. **Egress & Proxy Smoke Test:** Confirms the WebSocket server starts on `$PORT` within 120s and routes traffic properly through the model proxy.
4. **Smoke & MCP Tool Tests:** Simulates a minimal task and validates stdio and HTTP MCP interactions.

---

### 4. Evaluating on the Public Development Set

Once `kit check` passes, evaluate your agent across the 29 public dev tasks:

```bash
# Run all 29 dev tasks in parallel (e.g. 2 concurrent trials)
uv run python eval/run.py ../harness --trials 2 --env-file ../local.env

# Or test specific target tasks first:
uv run python eval/run.py ../harness --tasks data-center-site-model,engineers-estimate-check --env-file ../local.env
```

#### What happens during evaluation:
* Harbor pulls each task container from Hugging Face.
* Starts your harness container in isolation.
* Evaluates task prompts, runs agent commands, and writes deliverables into `../harness/artifacts/<task-id>/`.
* Runs automated graders and LLM judge rubrics to calculate scores ($0.0$ to $1.0$).
* Generates `manifest.json` recording task digests and run metadata.

---

### 5. Final Submission Checklist

Follow these exact steps to prepare your submission for the Kaggle competition:

1. **Verify Artifacts:**
   Ensure all 29 task folders exist inside `harness/artifacts/` with `manifest.json`.
   ```bash
   uv run python -m kit artifacts ../harness
   ```
2. **Review Offline Grading:**
   ```bash
   uv run python eval/run.py --artifacts ../harness
   ```
3. **Commit the Entire Harness Repository:**
   ```bash
   cd ../harness
   git init
   git add -A
   git commit -m "PLE Submission: Autonomous Engineering Agent Harness with Dev Artifacts"
   ```
4. **Final Readiness Check:**
   ```bash
   cd ../ple
   uv run python -m kit check ../harness
   ```
   *Must conclude with:* `ready to submit`.
5. **Push to GitHub & Submit to Kaggle:**
   * Push your repository commit to a private/public GitHub repository as instructed on the competition portal.
   * Submit the commit hash and repository URL on the Kaggle competition submission page.
