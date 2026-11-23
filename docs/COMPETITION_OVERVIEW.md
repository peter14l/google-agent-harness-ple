# Google - Agent Harness on Physical-Engineering's Last Exam (PLE)
## Comprehensive Competition & Benchmark Overview

---

### 1. Executive Summary

The **"Google - Agent Harness on Physical-Engineering's Last Exam"** is a flagship AI competition hosted on Kaggle in partnership with **Google Cloud AI Research**, **Mercor**, and academic researchers from Stanford, Harvard, NYU, Columbia, and others.

* **Prize Pool:** **$400,000 USD**
  * 1st Place: $250,000
  * 2nd Place: $100,000
  * 3rd Place: $50,000
* **Competition Dates:** November 9, 2026 – January 5, 2027
* **Official Benchmark Site:** [https://ple-bench.com](https://ple-bench.com)
* **Official Evaluation Kit Repo:** [https://github.com/google-research/ple](https://github.com/google-research/ple)
* **Gated Public Dev Dataset:** [https://huggingface.co/datasets/google/physical-engineerings-last-exam](https://huggingface.co/datasets/google/physical-engineerings-last-exam)
* **arXiv Research Paper:** *PLE: Physical-Engineering's Last Exam* ([arXiv:2610.30537](https://arxiv.org/abs/2610.30537))

Unlike conventional text-based AI benchmarks (which test textbook trivia, multiple-choice questions, or small code snippets), PLE tests **autonomous agents solving messy, multi-hour, billable physical engineering tasks** that licensed Professional Engineers (PEs) handle in real-world infrastructure and engineering firms.

---

### 2. The Benchmark Structure

The PLE benchmark comprises **85 expert-curated, multi-hour tasks** distributed across two sets:
* **Public Development Set:** 29 tasks (released openly on Hugging Face with full grader suites for local training, validation, and optimization).
* **Hidden Test Set:** 56 tasks (sealed and evaluated on Google Cloud competition infrastructure).

#### Four Core Physical Engineering Disciplines:

| Discipline | Tasks | Scope & Typical Deliverables | Key Tools & Standards |
| :--- | :---: | :--- | :--- |
| **Structural Engineering** | 10 | Gravity, wind, and seismic load checks; member and connection sizing; seismic design criteria; structural drawing revisions from redlines; concrete/steel design checks. | AISC 360, ACI 318, ASCE 7, SAP2000, OpenSees, Python solvers |
| **Civil Engineering** | 18 | Soil settlement, slope stability, bearing capacity analysis; campus layouts; site grading and earthwork balancing; stormwater drainage design; construction sequencing; engineering cost estimates. | AASHTO, IBC, GeoStudio, EPANET, IFC/BIM, Pandas/GeoPandas |
| **Electrical Engineering** | 27 | Medium/low-voltage power distribution; feeder and cable sizing; short-circuit calculations; arc flash analysis; panel schedule responses; PV/solar grid interconnections; voltage drop mitigation. | NEC (NFPA 70), IEEE standards, ETAP/OpenDSS, single-line diagrams (SLD) |
| **Mechanical Engineering** | 30 | HVAC heating/cooling load calculations; fluid flow, ductwork, and chilled-water piping; clash-free 3D MEP routing; equipment equivalency evaluations; storage-tank life predictions; fire simulation validation. | ASHRAE 90.1 / 62.1, EnergyPlus, OpenFOAM, FDS, IFC/FreeCAD |

---

### 3. Detailed Scoring & Evaluation Mechanics

Tasks are scored on a continuous scale from **`0.0` to `1.0`**. 

#### Hard-Constraint & Objective Grading Formula
For optimization and engineering design tasks (e.g. tasks using `tests/paper_score.py`), each deliverable item is graded using:

$$s = 0.4 \cdot p + 0.6 \cdot G \cdot O'$$

Where:
* **$p \in [0, 1]$**: The fraction of all soft constraints met.
* **$G \in \{0, 1\}$**: The **Hard Constraint Gate**. 
  * $G = 1$ if and only if **EVERY hard constraint** (physical feasibility, structural safety factors, maximum allowable stress, non-clashing geometry, electrical voltage drop limits, building code compliance) is satisfied.
  * $G = 0$ if even a **single** hard constraint is breached. **Breaking any hard safety constraint caps the item score at $0.40$!**
* **$O' \in [0, 1]$**: Normalized design efficiency objective:
  $$O' = \text{clip}\left(\frac{O - O_{\text{naive}}}{1 - O_{\text{naive}}}, 0, 1\right)$$
  * $O$ is the agent's objective value ($1.0$ at certified theoretical optimal; for cost minimization, certified lower bound divided by the design's cost).
  * $O_{\text{naive}}$ is the objective of an unoptimized baseline compliant design.

#### Evaluation Modes
1. **Programmatic / Code Graders:** Deterministic unit tests, finite element scripts, geometric collision checkers, and balance checks executed inside a fresh verifier container.
2. **LLM Rubric Judges:** For qualitative technical memos, engineering reports, and design reviews, evaluated by an LLM Judge (official competition judge uses **Claude Opus 5.5** at standard temperature).
3. **Hybrid Checks-Judge:** Combines deterministic checks on numerical results with rubric evaluation on technical reasoning.

A competitor's final benchmark score is the **arithmetic mean across all tasks**. Any task that times out, crashes, or fails to produce valid files in the declared deliverable paths receives a score of **0.0**.

---

### 4. Technical Submission Architecture

An official submission is a **single commit on a GitHub repository** containing:
1. `submission.yaml`: Defines harness name, model declaration, build instructions, and serve entry point.
2. `serve.py`: High-performance WebSocket v1 server listening on `$PORT`.
3. `artifacts/`: Exact output directory exported by `eval/run.py` from running all 29 public dev tasks.
4. Supporting source files (`taskbridge.py`, agent logic, prompts, tools, requirements).

#### Execution Limits & Sandbox Rules
* **Task Duration:** Up to **6 hours (21,600 seconds)** per task.
* **Serve Container:** Unprivileged user (`uid 1000`), read-only root filesystem, 2 CPUs, 4 GB RAM, 1 GB `/tmp`, 1 GB `$HOME`.
* **Network Isolation:** 
  * Build phase: Full outbound internet as root for package installation (`install` hook).
  * Serve phase: Outbound traffic is restricted **exclusively** to the declared model endpoint via an egress proxy (`HTTPS_PROXY`). Web search, external browsing, and auxiliary web APIs are blocked.
  * Task container: Complete network isolation (no internet). Project files, CAD geometries, and local task MCP servers run here.

---

### 5. Google-Sponsored Model API Specifications

In the final submission (Stage 2), competitors must declare one of eight Google-sponsored models in `submission.yaml`:

| Model API String | Model Name | Primary Endpoint Interface |
| :--- | :--- | :--- |
| `google-cloud/gemini-4-argon` | Gemini 4 Argon | OpenAI Chat Completions, Gemini Native API |
| `google-cloud/gemini-3.8-flash` | Gemini 3.8 Flash | OpenAI Chat Completions, Gemini Native API |
| `google-cloud/gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview | OpenAI Chat Completions, Gemini Native API |
| `google-cloud/claude-opus-5-5` | Claude Opus 5.5 | OpenAI Chat Completions, Anthropic Messages API |
| `google-cloud/gpt-oss-120b` | GPT-OSS 120B | OpenAI Chat Completions |
| `google-cloud/glm-5.2` | GLM 5.2 | OpenAI Chat Completions |
| `google-cloud/gemma-4-26b` | Gemma 4 26B A4B | OpenAI Chat Completions |
| `google-cloud/llama-4-maverick` | Llama 4 Maverick 17B 128E | OpenAI Chat Completions |

*Zero API keys are committed in the repository.* The evaluation platform automatically injects credentials (`MODEL_BASE_URL`, `MODEL_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.) inside the container at runtime.

---

### 6. Fair Play & Integrity Guidelines

To maintain absolute competitive fairness:
1. **No Hard-coding:** Harnesses must never contain hard-coded answers, memorized values, or conditional branches keyed to specific task IDs or prompt signatures.
2. **Artifact Integrity:** The `artifacts/` folder committed to the repo must be generated strictly by `eval/run.py` executing the submitted harness and declared model. Hand-editing or mixing outputs from unapproved models is strictly forbidden.
3. **No Grader Peeking:** Harnesses must never attempt to inspect grading scripts, test harnesses, or hidden unit tests.
4. **No Network Tampering:** No attempts to bypass the egress proxy or access unauthorized network destinations.
