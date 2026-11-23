# Google - Agent Harness on Physical-Engineering's Last Exam (PLE)
## Complete Autonomous Engineering Agent Harness & Hackathon Suite

[![Benchmark](https://img.shields.io/badge/Benchmark-PLE--Bench-009FDB?style=for-the-badge)](https://ple-bench.com)
[![Paper](https://img.shields.io/badge/Paper-arXiv:2610.30537-B31B1B?style=for-the-badge)](https://arxiv.org/abs/2610.30537)
[![Prize](https://img.shields.io/badge/Kaggle_Prize_Pool-$400,000-FFD21E?style=for-the-badge)](https://www.kaggle.com/competitions/physical-engineerings-last-exam)
[![License](https://img.shields.io/badge/License-Apache_2.0-2EA44F?style=for-the-badge)](LICENSE)

---

### 1. Executive Summary

This repository hosts a production-grade autonomous agent harness engineered for the **Google - Agent Harness on Physical-Engineering's Last Exam (PLE)** Kaggle competition (November 9, 2026 – January 5, 2027; $400,000 prize pool).

Unlike conversational or toy coding benchmarks, PLE comprises **85 real-world engineering challenges** across four core disciplines:
* **Structural Engineering** (10 tasks): Gravity, wind, seismic checks; member and connection design.
* **Civil Engineering** (18 tasks): Soil settlement, bearing capacity, site grading, cut/fill balancing, stormwater.
* **Electrical Engineering** (27 tasks): Power distribution, feeder sizing, voltage drop mitigation, SLD compliance.
* **Mechanical Engineering** (30 tasks): HVAC cooling/heating loads, pipe/duct sizing, clash-free 3D MEP routing.

Tasks enforce a uniform **6-hour execution limit** and evaluate deliverables via the hard-constraint objective formula:

$$s = 0.4 \cdot p + 0.6 \cdot G \cdot O'$$

Where $G=0$ if **any** hard physical constraint or municipal building code is violated, immediately capping the task score at $0.40$.

---

### 2. High-Level System Architecture

```
                          EVALUATION TOPOLOGY
                          
       +-------------------------------------------------------+
       |                  EVALUATOR HARNESS                    |
       |                                                       |
       |  +--------------------+       WebSocket v1            |
       |  |  SERVE CONTAINER   |<==========================+   |
       |  |  (harness/serve.py)|                           |   |
       |  +---------+----------+                           |   |
       |            |                                      |   |
       |    Plan-Work-Verify Loop                          |   |
       |    1. Planner  (10% time, Read-Only, Specs & G)   |   |
       |    2. Worker   (65% time, Python Solvers, Outputs)|   |
       |    3. Verifier (25% time, QA Audit, Fix Rounds)   |   |
       |            |                                      |   |
       |            v                                      |   |
       |  +--------------------+                           |   |
       |  |   TASK CONTAINER   |---------------------------+   |
       |  | - Project files    | (exec, read_file, write_file, |
       |  | - CAD / IFC / PDFs |  mcp_call)                    |
       |  | - MCP Servers      |                               |
       |  +--------------------+                               |
       +-------------------------------------------------------+
                                  |
                            (HTTPS Proxy)
                                  v
       +-------------------------------------------------------+
       |            GOOGLE MODEL API GATEWAY                   |
       | - google-cloud/gemini-3.8-flash (Default)             |
       | - google-cloud/gemini-4-argon                         |
       | - google-cloud/claude-opus-5-5                        |
       +-------------------------------------------------------+
```

---

### 3. Repository Structure & Artifacts

```
.
├── README.md                           # Master orientation & architectural documentation
├── local.env.example                   # Local credentials and model proxy configuration template
├── docs/                               # Comprehensive specification playbooks
│   ├── COMPETITION_OVERVIEW.md         # Official competition rules, timeline, $400k prizes, scoring
│   ├── AGENT_HARNESS_ARCHITECTURE.md   # WebSocket v1 protocol, container sandbox, context compaction
│   ├── ENGINEERING_DOMAIN_PLAYBOOK.md  # Deep technical guides: AISC, ACI, NEC, ASHRAE, IFC/BIM
│   └── DEVELOPMENT_AND_SUBMISSION_GUIDE.md # Dev workflow, local model proxy, Harbor, kit check, Kaggle
├── harness/                            # Standalone Autonomous Engineering Agent Harness
│   ├── submission.yaml                 # Leaderboard entry metadata & model configuration
│   ├── serve.py                        # Master WebSocket v1 server with Plan-Work-Verify lifecycle
│   ├── taskbridge.py                   # Protocol framing, Base64 chunking, exec runner, HTTP relay
│   ├── requirements.txt                # Pinned production Python dependencies
│   ├── pyproject.toml                  # Build metadata
│   ├── install.sh                      # Container installation script
│   ├── .gitattributes                  # Normalized LF line endings for Linux Docker builds
│   ├── .gitignore
│   ├── README.md                       # Harness-specific operational guide
│   └── agent/
│       ├── __init__.py
│       ├── prompts.py                  # Domain-engineered Planner, Worker, and Verifier prompts
│       ├── context_manager.py          # Head/tail truncation, prompt caching, token compaction
│       └── mcp_manager.py              # Dynamic MCP tool cataloging and execution bridge
├── scripts/                            # Operational automation scripts
│   ├── setup_env.sh / .ps1             # Automated installation of uv, harbor, and dependencies
│   ├── run_local_proxy.sh              # Starts LiteLLM Vertex AI model proxy on port 4000
│   ├── validate_harness.sh / .ps1      # Runs official `kit check` validation
│   └── run_dev_eval.sh                 # Executes Harbor evaluation across dev tasks
└── ple/                                # Cloned official competition kit & dev task runner
    ├── docs/                           # Official kit docs (protocol, models, artifacts)
    ├── eval/                           # Dev set evaluation runner (`eval/run.py`)
    ├── kit/                            # Kit check smoke tests and model proxy tools
    └── sample_submissions/             # Reference starter submissions
```

---

### 4. Quick Start Guide

#### Step 1: Environment Setup
Ensure Docker Desktop is running, then run the automated setup script:

```bash
# On Linux / WSL 2:
bash scripts/setup_env.sh

# On Windows PowerShell:
.\scripts\setup_env.ps1
```

#### Step 2: Configure Local Credentials
Copy `local.env.example` to `local.env` and insert your credentials:
```bash
cp local.env.example local.env
# Configure VERTEXAI_PROJECT, MODEL_PROXY_KEY, and HF_TOKEN
```

#### Step 3: Start the Local Model Proxy (for `google-cloud` models)
```bash
bash scripts/run_local_proxy.sh
```

#### Step 4: Validate the Harness with `kit check`
```bash
# On Linux / WSL 2:
bash scripts/validate_harness.sh

# On Windows PowerShell:
.\scripts\validate_harness.ps1
```
This builds `/opt/harness` in Debian Bookworm, tests the WebSocket connection, checks model egress, runs smoke tests, and confirms submission readiness.

#### Step 5: Evaluate on the Public Development Set
```bash
# Run all 29 dev tasks:
bash scripts/run_dev_eval.sh local.env --trials 2

# Or run specific tasks:
bash scripts/run_dev_eval.sh local.env --tasks data-center-site-model,engineers-estimate-check
```

---

### 5. Final Kaggle Submission Checklist

1. **Dev Set Artifacts:** Verify that `harness/artifacts/` contains the generated deliverable files and `manifest.json`.
2. **Review Artifacts:** Run `uv run python -m kit artifacts ../harness` inside `ple/`.
3. **Commit the Harness Repository:**
   ```bash
   cd harness
   git init
   git add -A
   git commit -m "Autonomous Engineering Agent Harness for PLE"
   ```
4. **Final Gate Check:** Run `uv run python -m kit check ../harness` and verify output concludes with `ready to submit`.
5. **Publish & Submit:** Push the commit to GitHub and link it on the Kaggle competition page.
