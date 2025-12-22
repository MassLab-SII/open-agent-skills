"""MCP tools wrapper for Notion API - Self Assessment page operations."""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class NotionMCPTools:
    """Wrapper for Notion MCP tools."""
    
    def __init__(self, api_key: str):
        """Initialize MCP tools with Notion API key."""
        self.api_key = api_key
        self.client = None
        self._stack = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": "2022-06-28"
        }
        
        params = StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={**os.environ, "OPENAPI_MCP_HEADERS": json.dumps(headers)},
        )
        
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()
        
        read_stream, write_stream = await self._stack.enter_async_context(
            stdio_client(params)
        )
        
        self.client = await self._stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self.client.initialize()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, exc_tb)
    
    async def search(self, query: str, filter_type: str = "page") -> Dict[str, Any]:
        """Search for pages using API-post-search."""
        try:
            result = await self.client.call_tool("API-post-search", {
                "query": query,
                "filter": {"property": "object", "value": filter_type}
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {}
    
    async def get_block_children(self, block_id: str) -> Dict[str, Any]:
        """Get children blocks using API-get-block-children."""
        try:
            result = await self.client.call_tool("API-get-block-children", {
                "block_id": block_id
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Get block children error: {e}")
            return {}
    
    async def patch_block_children(self, block_id: str, children: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Patch block children using API-patch-block-children."""
        try:
            result = await self.client.call_tool("API-patch-block-children", {
                "block_id": block_id,
                "children": children
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Patch block children error: {e}")
            return {}
    
    async def delete_block(self, block_id: str) -> Dict[str, Any]:
        """Delete a block using API-delete-a-block."""
        try:
            result = await self.client.call_tool("API-delete-a-block", {
                "block_id": block_id
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Delete block error: {e}")
            return {}
    
    @staticmethod
    def _extract_text(result: Any) -> Optional[str]:
        """Extract text content from MCP result."""
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
            content = result_dict.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        return None


def extract_block_property(block: Dict[str, Any], block_type: str, property_name: str) -> Optional[str]:
    """Extract property from a block by type and property name."""
    if not block or block.get("type") != block_type:
        return None
    
    block_content = block.get(block_type, {})
    
    if property_name == "text" and "rich_text" in block_content:
        rich_text = block_content.get("rich_text", [])
        if rich_text:
            return rich_text[0].get("plain_text", "")
    
    return block_content.get(property_name)

