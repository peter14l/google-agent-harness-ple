# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Production Autonomous Agent Harness for Physical-Engineering's Last Exam (PLE).

Architecture:
1. Planner: Read-only inspection to map deliverable paths, schemas, and hard constraints.
2. Worker: Execution phase running code-driven calculations and generating deliverables.
3. Verifier: Independent QA stage validating deliverables against hard physical & code constraints.
"""

import asyncio
import json
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import openai
import taskbridge
from agent.context_manager import (
    apply_cache_control_if_claude,
    prune_old_tool_outputs,
    truncate_middle,
    CONTEXT_LENGTH_PATTERNS,
)
from agent.mcp_manager import MCPManager
from agent.prompts import PLANNER_PROMPT, WORKER_PROMPT, VERIFIER_PROMPT

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper(), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ple_harness")

# Model configuration from injected environment variables
MODEL = os.environ.get("MODEL_NAME", "gemini-3.8-flash")
MAX_EFFORT_MODELS = ("claude", "glm", "gpt-6", "deepseek-v4")
EFFORT = os.environ.get("REASONING_EFFORT") or (
    "max" if any(m in MODEL.lower() for m in MAX_EFFORT_MODELS) else "high"
)

MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "32000"))
COMPACT_AT_TOKENS = int(os.environ.get("COMPACT_AT_TOKENS", "150000"))

# Time budgeting shares
PLAN_SHARE = 0.10     # 10% of total time for planning
CHECK_SHARE = 0.25    # 25% of total time reserved for verification and fixes
WRAP_UP_SEC = 240     # 4 minutes reserved for safe wrap-up before deadline
RETRY_WAITS = (5, 15, 30, 60, 120)

client = openai.AsyncOpenAI(max_retries=5, timeout=1800)


def build_tool_schemas(include_write: bool = True) -> List[Dict[str, Any]]:
    """Generates standard function calling schemas for the agent."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Execute a bash shell command in the task container. Use for running scripts, solvers, compilers, and inspections.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "The exact bash command line to run."},
                        "timeout_sec": {"type": "integer", "description": "Command timeout in seconds (default 120, max 600)."},
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read content from a file in the task container.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Absolute or relative file path to read."},
                    },
                    "required": ["path"],
                },
            },
        },
    ]

    if include_write:
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Create or overwrite a file in the task container. Parent directories are created automatically.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to write."},
                            "content": {"type": "string", "description": "Text content to write."},
                            "append": {"type": "boolean", "description": "If true, appends to the file instead of overwriting."},
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Perform an exact string replacement inside an existing file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to modify."},
                            "target": {"type": "string", "description": "Exact text to find and replace."},
                            "replacement": {"type": "string", "description": "Drop-in replacement text."},
                        },
                        "required": ["path", "target", "replacement"],
                    },
                },
            },
        ])

    return tools


async def execute_tool(
    name: str,
    args: Dict[str, Any],
    session: taskbridge.Session,
    mcp_mgr: MCPManager,
) -> str:
    """Dispatches tool execution to the task container via session or MCP."""
    try:
        if name == "bash":
            cmd = args.get("command", "")
            timeout = args.get("timeout_sec", 120)
            res = await session.exec(cmd, timeout_sec=timeout)
            out = res.output
            if res.timed_out:
                out += f"\n[Process timed out after {timeout} seconds]"
            return truncate_middle(out, max_chars=20_000)

        elif name == "read_file":
            path = args.get("path", "")
            data = await session.read_file(path)
            # Try decoding as UTF-8 text, otherwise report size
            try:
                text = data.decode("utf-8")
                return truncate_middle(text, max_chars=30_000)
            except UnicodeDecodeError:
                return f"[Binary file read successfully: {len(data):,} bytes]"

        elif name == "write_file":
            path = args.get("path", "")
            content = args.get("content", "")
            append = bool(args.get("append", False))
            await session.write_file(path, content, append=append)
            return f"Successfully wrote {len(content):,} characters to {path}"

        elif name == "edit_file":
            path = args.get("path", "")
            target = args.get("target", "")
            replacement = args.get("replacement", "")
            data = await session.read_file(path)
            text = data.decode("utf-8")
            if target not in text:
                return f"Error: Target text not found in {path}"
            updated = text.replace(target, replacement)
            await session.write_file(path, updated, append=False)
            return f"Successfully replaced occurrences in {path}"

        elif name.startswith("mcp_"):
            parts = name.split("_", 2)
            if len(parts) >= 3:
                server = parts[1]
                tool = parts[2]
                return await mcp_mgr.call_tool(server, tool, args)
            return f"Error: Unrecognized MCP tool format: {name}"

        return f"Unknown tool: {name}"

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return f"Execution error in {name}: {str(e)}"


async def call_model_with_retry(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    deadline_sec: Optional[float] = None,
) -> Any:
    """Robust OpenAI completion call with backoff and error recovery."""
    params: Dict[str, Any] = {
        "model": MODEL,
        "messages": apply_cache_control_if_claude(messages, MODEL),
        "max_completion_tokens": MAX_OUTPUT_TOKENS,
    }
    if tools:
        params["tools"] = tools

    # Inject reasoning effort if supported
    if EFFORT and "gpt-4o" not in MODEL:
        params["reasoning_effort"] = EFFORT

    for attempt, wait in enumerate(RETRY_WAITS):
        try:
            return await client.chat.completions.create(**params)
        except openai.BadRequestError as e:
            err_msg = str(e)
            if CONTEXT_LENGTH_PATTERNS.search(err_msg):
                raise e  # Let caller compact context
            if "reasoning_effort" in err_msg:
                params.pop("reasoning_effort", None)
                continue
            if "max_completion_tokens" in err_msg:
                params.pop("max_completion_tokens", None)
                params["max_tokens"] = min(MAX_OUTPUT_TOKENS, 4096)
                continue
            raise e
        except (openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError) as e:
            if attempt == len(RETRY_WAITS) - 1:
                raise e
            logger.warning(f"Transient error ({type(e).__name__}). Retrying in {wait}s...")
            await asyncio.sleep(wait)


async def run_agent_turn_loop(
    role_name: str,
    system_prompt: str,
    initial_user_prompt: str,
    tools: List[Dict[str, Any]],
    session: taskbridge.Session,
    mcp_mgr: MCPManager,
    max_turns: int = 50,
    time_limit_sec: Optional[float] = None,
) -> str:
    """Runs a conversational agent loop until termination or deadline."""
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_user_prompt},
    ]

    start_time = asyncio.get_event_loop().time()
    session.log(f"Starting {role_name} stage (Limit: {time_limit_sec or 'unbounded'}s)...")

    for turn in range(max_turns):
        now = asyncio.get_event_loop().time()
        elapsed = now - start_time
        remaining = session.time_left()

        # Check stage deadline or global wrap-up
        if (time_limit_sec and elapsed >= time_limit_sec) or (remaining and remaining <= WRAP_UP_SEC):
            session.log(f"{role_name} reached time budget. Wrapping up...")
            messages.append({"role": "user", "content": "Time is up for this phase. Please provide your summary now."})
            try:
                resp = await call_model_with_retry(messages, tools=None)
                return resp.choices[0].message.content or "Completed on deadline."
            except Exception:
                return "Completed on deadline."

        try:
            response = await call_model_with_retry(messages, tools=tools)
        except openai.BadRequestError as e:
            if CONTEXT_LENGTH_PATTERNS.search(str(e)):
                session.log("Context full. Pruning older tool outputs...")
                messages = prune_old_tool_outputs(messages, keep_chars=500)
                response = await call_model_with_retry(messages, tools=tools)
            else:
                raise e

        choice = response.choices[0]
        msg = choice.message
        tool_calls = msg.tool_calls

        # Log token usage if reported
        if response.usage:
            u = response.usage
            cache_read = getattr(u.prompt_tokens_details, "cached_tokens", 0) if hasattr(u, "prompt_tokens_details") else 0
            session.usage(MODEL, u.prompt_tokens, u.completion_tokens, cache_read)

        # Record assistant reply
        assistant_dict: Dict[str, Any] = {"role": "assistant"}
        if msg.content:
            assistant_dict["content"] = msg.content
        if tool_calls:
            assistant_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in tool_calls
            ]
        messages.append(assistant_dict)

        # If no tool calls, stage is finished
        if not tool_calls:
            return msg.content or "Finished without text."

        # Execute all tool calls
        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}

            res_str = await execute_tool(name, args, session, mcp_mgr)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": res_str,
            })

    return "Max turns reached."


async def solve(session: taskbridge.Session) -> str:
    """Master workflow: Plan -> Work -> Verify."""
    session.log(f"Initializing PLE Autonomous Engineer on model: {MODEL}")
    mcp_mgr = MCPManager(session)
    await mcp_mgr.initialize()

    # Time budget allocation
    total_time = session.time_left() or 21600
    plan_budget = min(total_time * PLAN_SHARE, 1800)  # max 30m for planning
    check_budget = min(total_time * CHECK_SHARE, 3600) # max 60m for verifier

    # Stage 1: Planner (Read-Only)
    planner_tools = build_tool_schemas(include_write=False)
    plan_prompt = f"Task Instruction:\n{session.instruction}\n\nWorkdir: {session.workdir}\n\nInspect project files and output the plan."
    plan_result = await run_agent_turn_loop(
        role_name="Planner",
        system_prompt=PLANNER_PROMPT.format(workdir=session.workdir),
        initial_user_prompt=plan_prompt,
        tools=planner_tools,
        session=session,
        mcp_mgr=mcp_mgr,
        max_turns=20,
        time_limit_sec=plan_budget,
    )

    # Stage 2: Worker (Execution)
    worker_tools = build_tool_schemas(include_write=True)
    if not mcp_mgr.should_use_dynamic_tools():
        worker_tools.extend(mcp_mgr.get_static_tool_definitions())

    worker_prompt = (
        f"Original Task:\n{session.instruction}\n\n"
        f"Approved Execution Plan:\n{plan_result}\n\n"
        "Execute all computations, generate deliverables, and verify outputs."
    )
    worker_result = await run_agent_turn_loop(
        role_name="Worker",
        system_prompt=WORKER_PROMPT.format(workdir=session.workdir),
        initial_user_prompt=worker_prompt,
        tools=worker_tools,
        session=session,
        mcp_mgr=mcp_mgr,
        max_turns=60,
        time_limit_sec=total_time - plan_budget - check_budget,
    )

    # Stage 3: Verifier (Independent Audit & Fixes)
    verifier_tools = build_tool_schemas(include_write=False)
    verifier_prompt = (
        f"Task:\n{session.instruction}\n\n"
        f"Execution Plan:\n{plan_result}\n\n"
        f"Worker Deliverable Summary:\n{worker_result}\n\n"
        "Audit every deliverable against hard constraints. Check files directly on disk."
    )
    verification_result = await run_agent_turn_loop(
        role_name="Verifier",
        system_prompt=VERIFIER_PROMPT,
        initial_user_prompt=verifier_prompt,
        tools=verifier_tools,
        session=session,
        mcp_mgr=mcp_mgr,
        max_turns=25,
        time_limit_sec=check_budget,
    )

    final_report = (
        f"# Physical Engineering Deliverable Sign-Off\n\n"
        f"## 1. Executive Summary\n{worker_result}\n\n"
        f"## 2. Quality Assurance & Hard-Constraint Audit\n{verification_result}\n"
    )
    return final_report


if __name__ == "__main__":
    taskbridge.run(solve)
