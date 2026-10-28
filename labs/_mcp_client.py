# -*- coding: utf-8 -*-
"""Talk to the estate the way a real wedge talks to a real ticketing system: as
an MCP client, over stdio, to a server you did not write.

Three helpers, nothing hidden:

    async with estate_session("agent.priya") as session:   # spawns estate_mcp.py
        tools = openai_tools((await session.list_tools()).tools)
        text  = await call(session, "get_ticket", {"ticket_id": "T-30207"})

`estate_session` starts `labs/estate_mcp.py --as <user_id>` as a subprocess
with this interpreter and yields an initialised `ClientSession`; the server
dies when the block exits. `openai_tools` turns the server's tool listing into
the `tools=[...]` list the OpenAI chat API wants, so the model sees the
customer's tools exactly as the customer describes them. `call` runs one tool
and returns its text — a denial is text too (see `estate_mcp.py` for why).

Verified against the installed SDK (mcp 2.x): `mcp.ClientSession`,
`mcp.StdioServerParameters`, `mcp.client.stdio.stdio_client`, and
`Tool.input_schema` (snake_case in 2.x).
"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parent / "estate_mcp.py"


@asynccontextmanager
async def estate_session(user_id: str) -> AsyncIterator[ClientSession]:
    """Spawn the estate server as `user_id` and yield a ready session."""
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER), "--as", user_id],
                                   cwd=str(SERVER.parent.parent))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def openai_tools(session_tools) -> list[dict]:
    """MCP tool listing → OpenAI function-calling `tools`. Accepts the
    `ListToolsResult` or its `.tools` list."""
    tools = getattr(session_tools, "tools", session_tools)
    return [{"type": "function",
             "function": {"name": t.name, "description": t.description or "",
                          "parameters": t.input_schema}}
            for t in tools]


async def call(session: ClientSession, name: str, args: dict) -> str:
    """Run one tool; return its text. A transport-level error (bad argument
    types, unknown tool) is prefixed so the caller can tell it from a result."""
    result = await session.call_tool(name, args or {})
    parts = [c.text for c in getattr(result, "content", []) if getattr(c, "type", "") == "text"]
    text = "\n".join(parts).strip()
    if getattr(result, "is_error", False):
        return f"ERROR: {text or 'tool call failed'}"
    return text
