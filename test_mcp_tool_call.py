#!/usr/bin/env python3
"""
Standalone MCP Tool Call Test Script
============================

Used to test the get_file_info tool call of the filesystem MCP server
"""

import asyncio
import json
import os
from pathlib import Path
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPStdioServer:
    """Lightweight MCP Stdio Server wrapper"""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 120):
        self.params = StdioServerParameters(
            command=command, 
            args=args, 
            env={**os.environ, **(env or {})}
        )
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None

    async def __aenter__(self):
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(self.params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def list_tools(self) -> list[dict]:
        """List all available tools"""
        resp = await asyncio.wait_for(self.session.list_tools(), timeout=self.timeout)
        return [t.model_dump() for t in resp.tools]

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call the specified tool"""
        result = await asyncio.wait_for(
            self.session.call_tool(name, arguments), 
            timeout=self.timeout
        )
        return result.model_dump()


async def test_get_file_info():
    """Test get_file_info tool call"""
    
    # Configuration parameters
    test_directory = "/Users/zhaoji/project/mcpmark/.mcpmark_backups/backup_filesystem_file_property_size_classification_78093"
    file_path = f"{test_directory}/bear.jpg"
    
    # Create MCP server
    mcp_server = MCPStdioServer(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", test_directory]
    )
    
    async with mcp_server:
        
        # Call get_file_info tool
        func_name = "get_file_info"
        func_args = {"path": file_path}
        
        try:
            result = await asyncio.wait_for(
                mcp_server.call_tool(func_name, func_args),
                timeout=60
            )

            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        except asyncio.TimeoutError:
            print("❌ Call timed out (60 seconds)")
        except Exception as e:
            print(f"❌ Call failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main function"""
    print("\n" + "="*60)
    print("MCP Tool Call Test")
    print("="*60 + "\n")
    
    # Test get_file_info
    asyncio.run(test_get_file_info())
    
    print("\n" + "="*60)
    print("Test completed")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

