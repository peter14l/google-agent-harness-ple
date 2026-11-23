# PLE Autonomous Engineering Agent Harness
## Production-Grade Multi-Stage Agent for Physical-Engineering's Last Exam

---

### 1. Architectural Highlights

* **Plan-Work-Verify Staging:**
  * **Planner:** Read-only analysis identifying deliverable schemas, file paths, and hard constraints ($G$ gates).
  * **Worker:** Programmatic execution utilizing Python numerical libraries (`numpy`, `scipy`, `shapely`, `ifcopenshell`) to guarantee deterministic math.
  * **Verifier:** Independent QA auditor re-inspecting files from disk, executing validation scripts, and ensuring $DCR \le 1.0$ and zero hard constraint breaches.
* **Context & Token Resilience:**
  * Automated head/tail truncation of long tool outputs ($20,000$ characters max).
  * Dynamic context compaction pruning historical tool outputs.
  * Native Claude prompt caching markers (`cache_control`) and automatic Gemini prefix caching.
  * Exponential backoff retries on rate limits ($429$), server errors ($5xx$), and connection resets.
* **Deadline Aware:**
  * Dedicated wrap-up window ($240$ seconds) ensuring final deliverables and memos are saved before hard 6-hour timeouts.

---

### 2. File Organization

```
harness/
├── submission.yaml          # Evaluator container configuration & model declaration
├── serve.py                 # Master WebSocket v1 server with Plan-Work-Verify lifecycle
├── taskbridge.py            # Serve protocol client/server implementation
├── requirements.txt         # Pinned production dependencies
├── pyproject.toml           # Project metadata
├── install.sh               # Container build script
├── .gitattributes           # Normalized LF line endings for Linux containers
├── .gitignore
└── agent/
    ├── __init__.py
    ├── prompts.py           # Domain system prompts for Planner, Worker, and Verifier
    ├── context_manager.py   # Token truncation and prompt cache management
    └── mcp_manager.py       # Task MCP server discovery and execution bridge
```

---

### 3. Local Verification

To run static checks and container smoke tests from the kit:
```bash
cd ../ple
uv run python -m kit check ../harness --env-file ../local.env
```

To evaluate against the public dev set:
```bash
uv run python eval/run.py ../harness --env-file ../local.env
```
