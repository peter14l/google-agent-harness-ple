# Agent Harness Architecture & System Design
## PLE Autonomous Engineering Agent Specification

---

### 1. Architectural Topology

The Physical-Engineering's Last Exam (PLE) evaluation platform decouples the agent harness from the execution environment. This provides strict security, reproducible sandboxing, and standardized grading.

```
+-----------------------------------------------------------------------------------------+
|                                    EVALUATOR HARNESS                                    |
|                                                                                         |
|  +--------------------------------+                  +-------------------------------+  |
|  |     SERVE CONTAINER            |                  |       TASK CONTAINER          |  |
|  |   (debian:bookworm unpriv)     |                  |       (Harbor isolated)       |  |
|  |                                |                  |                               |  |
|  |  +--------------------------+  |   WebSocket v1   |  - Project Files & CAD        |  |
|  |  |    serve.py (FastAPI /   |  |<================>|  - IFC models, PDF drawings   |  |
|  |  |    Taskbridge Server)    |  |  exec/read/write |  - Python/Bash Solvers        |  |
|  |  +--------------------------+  |   MCP proxying   |  - Task MCP Servers           |  |
|  |               |                |                  |    (Documents, CAD, etc.)     |  |
|  |               v                |                  |  - Deliverables (/app/...)    |  |
|  |  +--------------------------+  |                  +-------------------------------+  |
|  |  | Autonomous Agent Core:   |  |                                                     |
|  |  | 1. Planner Agent         |  |                                                     |
|  |  | 2. Worker Engine         |  |                                                     |
|  |  | 3. Verifier Gatekeeper   |  |                                                     |
|  |  +--------------------------+  |                                                     |
|  +---------------+----------------+                                                     |
|                  | (HTTPS / TLS only)                                                   |
|                  v                                                                      |
|  +--------------------------------+                                                     |
|  |     EGRESS PROXY LAYER         |                                                     |
|  |   - Filters all foreign traffic|                                                     |
|  |   - Grants access ONLY to      |                                                     |
|  |     Google Model Gateway       |                                                     |
|  +---------------+----------------+                                                     |
+------------------|----------------------------------------------------------------------+
                   v
   +--------------------------------+
   |   FOUNDATION MODEL PROVIDER    |
   |   - Gemini 3.8 Flash           |
   |   - Claude Opus 5.5            |
   |   - Gemini 4 Argon             |
   +--------------------------------+
```

---

### 2. The Serve Protocol (Version 1)

Communication between the evaluator and the harness occurs across a bidirectionally streamed WebSocket connection on `0.0.0.0:$PORT`. Every frame is a UTF-8 JSON object (maximum 16 MiB).

#### Phase 1: Evaluator Handshake (`task` message)
Upon connection, the evaluator initiates the task:
```json
{
  "type": "task",
  "protocol": 1,
  "session": "3f2c9a1e0b7d4c55",
  "instruction": "Perform geotechnical bearing capacity calculations according to AASHTO...",
  "workdir": "/app",
  "limits": {
    "agent_timeout_sec": 21600,
    "exec_timeout_sec": 600,
    "max_output_bytes": 100000,
    "max_write_bytes": 10000000
  },
  "mcp_servers": [
    {"name": "cad_tools", "url": "http://127.0.0.1:8000/mcp/", "transport": "streamable-http"}
  ]
}
```

#### Phase 2: Harness Commands to Task Container
The agent interacts with the workspace using 4 core operations (up to 8 concurrent requests):

1. **`exec`**: Runs `bash -c "<command>"` inside the task container at `workdir`.
   * Returns `exit_code`, `output` (interleaved stdout/stderr, head/tail truncated past 100 KB), `truncated`, and `timed_out`.
2. **`read_file`**: Fetches raw file bytes encoded as Base64 (up to 10 MB per chunk). Supports reading text files, scripts, logs, and binary CAD/image assets.
3. **`write_file`**: Writes binary or text files (Base64 payload). Missing directories are created automatically. Supports `append: true` for large file streaming.
4. **`http`**: Forwards requests from inside the task container to task-provided MCP servers (CAD servers, document processors, email simulation) using Streamable HTTP.

#### Phase 3: One-Way Signals & Task Completion
* **`log`**: Real-time progress logs visible in evaluation telemetry.
* **`usage`**: Token consumption reporting (`input_tokens`, `output_tokens`, `cache_read_tokens`).
* **`done`**: Signal indicating the agent has completed all deliverables.
* **`error`**: Fatal error termination signal.

---

### 3. Tri-Stage Agent Architecture: Plan-Work-Verify

To excel on the $s = 0.4p + 0.6GO'$ scoring formula, a monolithic agent loop is insufficient. A single hallucinated sign error or missed code requirement triggers $G=0$, destroying 60% of the possible score.

We implement a **Tri-Stage Architecture**:

```
[Start Task]
     |
     v
+-------------------------------------------------------------------+
| 1. PLANNER STAGE (Time budget: ~10% of remaining time)            |
| - Explores workspace (read_file, find, ls, grep) - Read Only      |
| - Extracts all deliverable specifications, file formats, schemas   |
| - Flags all HARD CONSTRAINTS (Safety, Physical, Building Codes)   |
| - Generates structured Execution Plan & Verification Criteria     |
+-------------------------------------------------------------------+
     |
     v
+-------------------------------------------------------------------+
| 2. WORKER STAGE (Time budget: ~65% of remaining time)             |
| - Executes code, computations, modeling scripts                   |
| - Generates primary engineering deliverables (IFC, PDF, CSV, TXT) |
| - Uses Python libraries (NumPy, SciPy, Shapely, IfcOpenShell)      |
| - Compiles interim deliverable summary                            |
+-------------------------------------------------------------------+
     |
     v
+-------------------------------------------------------------------+
| 3. VERIFIER STAGE (Time budget: ~25% of remaining time)           |
| - Independent verification agent with fresh context               |
| - Re-inspects produced deliverable files directly from disk        |
| - Executes automated assertion checks against all Hard Constraints|
| - IF Defect Found AND Time Remaining:                             |
|     Sends Targeted Defect Report to Worker (Fix Round)            |
|   ELSE:                                                           |
|     Emits PASS & Final Engineering Memo                           |
+-------------------------------------------------------------------+
     |
     v
[Deliverables Verified & Task Done]
```

---

### 4. Context Window & Memory Compaction

Engineering tasks run for up to 6 hours and generate hundreds of thousands of output characters. Without aggressive memory management, agents hit context limits or incur high latency.

1. **Head/Tail Truncation:** Command outputs over 20,000 characters keep the top 10,000 and bottom 10,000 characters, summarizing the truncation point.
2. **Turn Pruning:** Older tool execution outputs that have already been digested are trimmed down to 500-1,000 characters while preserving tool call signatures.
3. **Prompt Cache Optimization:**
   * For **Claude models**, explicit cache breakpoints (`"cache_control": {"type": "ephemeral"}`) are marked on the system prompt and the newest user message.
   * For **Gemini models**, implicit prefix caching is leveraged by keeping system instructions and immutable tool definitions strictly ordered at the start of the message array.
4. **Emergency Context Condensation:** When prompt tokens exceed `COMPACT_AT_TOKENS` (default 150,000), an automated condensation sub-call summarizes the investigation history into a persistent scratchpad memo.

---

### 5. Task MCP Server Integration

When a task provides application servers (such as LibreOffice document converters, FreeCAD geometric engines, or municipal code databases):
* Small catalogs ($\le 128$ tools) are preloaded directly into the model's tool schema.
* Large catalogs ($> 128$ tools) are dynamically exposed via two meta-tools:
  * `mcp_find(query: str)`: Searches available tools using fuzzy regex and semantic categorization.
  * `mcp_call(server: str, tool: str, arguments: dict)`: Invokes the target tool over the internal HTTP relay.
