"""Context window management, prompt caching, and token budgeting for long-horizon tasks."""

import re
from typing import Any, Dict, List

# Context length error patterns across providers
CONTEXT_LENGTH_PATTERNS = re.compile(
    r"context.?(length|window)|prompt is too long|maximum prompt length|exceed[^.]{0,40}(token|context)",
    re.IGNORECASE,
)

CACHE_CONTROL_EPHEMERAL = {"type": "ephemeral"}


def apply_cache_control_if_claude(messages: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """Mark system prompt and newest message for Claude prompt caching.
    Other providers (Gemini, OpenAI, vLLM) cache prefixes automatically.
    """
    if "claude" not in model_name.lower():
        return messages

    out = list(messages)
    n = len(out)
    if n == 0:
        return out

    # Target system prompt (index 0) and the newest user/tool message
    target_indices = {0, n - 1}
    for idx in target_indices:
        msg = out[idx]
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            out[idx] = {
                **msg,
                "content": [{"type": "text", "text": content, "cache_control": CACHE_CONTROL_EPHEMERAL}],
            }
        elif isinstance(content, list) and content:
            # Add cache_control to the last block if not already marked
            new_blocks = list(content)
            last_block = dict(new_blocks[-1])
            last_block["cache_control"] = CACHE_CONTROL_EPHEMERAL
            new_blocks[-1] = last_block
            out[idx] = {**msg, "content": new_blocks}

    return out


def truncate_middle(text: str, max_chars: int = 20_000) -> str:
    """Retain the head and tail of an overly long output string."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    omitted = len(text) - max_chars
    return (
        f"{text[:half]}\n\n"
        f"[... Omitted {omitted:,} characters of tool output ...]\n\n"
        f"{text[-half:]}"
    )


def prune_old_tool_outputs(messages: List[Dict[str, Any]], keep_chars: int = 1_000) -> List[Dict[str, Any]]:
    """Prune historical tool responses that the model has already processed,
    retaining only recent tool outputs in full.
    """
    if len(messages) <= 6:
        return messages

    pruned = list(messages)
    # Prune all but the last 4 tool outputs
    tool_indices = [i for i, m in enumerate(pruned) if m.get("role") == "tool"]
    if len(tool_indices) > 4:
        to_prune = tool_indices[:-4]
        for idx in to_prune:
            msg = pruned[idx]
            content = msg.get("content")
            if isinstance(content, str) and len(content) > keep_chars:
                pruned[idx] = {
                    **msg,
                    "content": f"{content[:keep_chars]}\n[... older output truncated for context compaction ...]",
                }
    return pruned
