#!/usr/bin/env python3
"""
Notion MCP Tools wrapper for Standard Operating Procedure skills
Pure MCP implementation without notion_client library
"""

import json
import os
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class NotionMCPTools:
    """Wrapper for Notion MCP tools with async context manager support"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._stack = None
    
    async def __aenter__(self):
        """Async context manager entry"""
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
        """Async context manager exit"""
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, exc_tb)
    
    async def search(self, query: str) -> Optional[str]:
        """Search for pages/databases by query"""
        try:
            result = await self.client.call_tool("API-post-search", {
                "query": query,
                "filter": {"property": "object", "value": "page"}
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"Error searching: {e}")
            return None
    
    async def retrieve_page(self, page_id: str) -> Optional[str]:
        """Retrieve page details"""
        try:
            result = await self.client.call_tool("API-retrieve-a-page", {
                "page_id": page_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"Error retrieving page: {e}")
            return None
    
    async def get_block_children(self, block_id: str) -> Optional[str]:
        """Get child blocks"""
        try:
            result = await self.client.call_tool("API-get-block-children", {
                "block_id": block_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"Error getting block children: {e}")
            return None
    
    async def update_block(self, block_id: str, block_type: str, properties: Dict[str, Any]) -> Optional[str]:
        """Update a block with new properties"""
        try:
            args = {"block_id": block_id, block_type: properties}
            result = await self.client.call_tool("API-update-a-block", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"Error updating block: {e}")
            return None
    
    async def patch_block_children(self, block_id: str, children: List[Dict[str, Any]], 
                                   after: Optional[str] = None) -> Optional[str]:
        """Add or modify child blocks"""
        try:
            args = {
                "block_id": block_id,
                "children": children
            }
            if after:
                args["after"] = after
            result = await self.client.call_tool("API-patch-block-children", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"Error patching block children: {e}")
            return None
    
    async def delete_block(self, block_id: str) -> Optional[str]:
        """Delete a block"""
        try:
            result = await self.client.call_tool("API-delete-a-block", {
                "block_id": block_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"Error deleting block: {e}")
            return None
    
    @staticmethod
    def _extract_text(result: Any) -> Optional[str]:
        """Extract text content from MCP result"""
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
            content = result_dict.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        return None
