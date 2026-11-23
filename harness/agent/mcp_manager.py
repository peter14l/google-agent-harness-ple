"""Task MCP Server Discovery and Dynamic Tool Registration."""

import json
from typing import Any, Dict, List, Optional
import taskbridge


class MCPManager:
    """Manages local Model Context Protocol (MCP) servers provided by the task."""

    def __init__(self, session: taskbridge.Session):
        self.session = session
        self.clients: Dict[str, taskbridge.MCPClient] = {}
        self.all_tools: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Connect to and initialize each task-provided MCP server."""
        for server in self.session.mcp_servers:
            name = server.get("name", "unknown")
            url = server.get("url")
            if not url:
                continue

            client = taskbridge.MCPClient(self.session, url)
            try:
                await client.initialize()
                tools = await client.list_tools()
                self.clients[name] = client
                for tool in tools:
                    tool_entry = dict(tool)
                    tool_entry["_server_name"] = name
                    self.all_tools.append(tool_entry)
            except Exception as e:
                self.session.log(f"Failed to initialize MCP server {name}: {e}")

    def should_use_dynamic_tools(self) -> bool:
        """Determines if the tool catalog is too large to expose statically."""
        if len(self.all_tools) > 128:
            return True
        total_schema_size = sum(len(json.dumps(t.get("inputSchema", {}))) for t in self.all_tools)
        return total_schema_size > 40_000

    def get_static_tool_definitions(self) -> List[Dict[str, Any]]:
        """Converts MCP tool definitions to standard OpenAI function tool format."""
        openai_tools = []
        for t in self.all_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{t['_server_name']}_{t['name']}",
                    "description": f"[{t['_server_name']}] {t.get('description', '')}",
                    "parameters": t.get("inputSchema", {"type": "object", "properties": {}}),
                },
            })
        return openai_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Executes a tool on the designated MCP client."""
        client = self.clients.get(server_name)
        if not client:
            return f"Error: MCP server '{server_name}' not found."
        try:
            result = await client.call_tool(tool_name, arguments)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error executing {server_name}/{tool_name}: {e}"
