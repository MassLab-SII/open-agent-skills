#!/usr/bin/env python3
"""
MCP Tools for Notion Operations
Pure MCP tool definitions without business logic
"""
import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional, List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class NotionMCPTools:
    """
    Pure MCP tools for Notion operations
    All methods return raw MCP results
    """
    
    def __init__(self, api_key: str, timeout: int = 120):
        self.api_key = api_key
        self.timeout = timeout
        self._stack = None
        self.session = None
    
    async def __aenter__(self):
        """Initialize MCP connection"""
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
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close MCP connection"""
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None
    
    # ==================== Core MCP Tools ====================
    
    async def search(self, query: str) -> Optional[str]:
        """Search pages and databases"""
        try:
            result = await self.session.call_tool("API-post-search", {
                "query": query
            })
            return self._extract_text(result)
        except Exception:
            return None
    
    async def query_database(self, database_id: str) -> Optional[str]:
        """Query database contents"""
        try:
            result = await self.session.call_tool("API-post-database-query", {
                "database_id": database_id
            })
            return self._extract_text(result)
        except Exception:
            return None
    
    async def create_page(self, parent_database_id: str, properties: Dict, icon: Optional[str] = None) -> Optional[str]:
        """Create a new page in database"""
        try:
            args = {
                "parent": {"database_id": parent_database_id},
                "properties": properties
            }
            
            if icon:
                args["icon"] = {"emoji": icon}
            
            result = await self.session.call_tool("API-post-page", args)
            return self._extract_text(result)
        except Exception:
            return None
    
    async def update_page(self, page_id: str, properties: Dict) -> Optional[str]:
        """Update page properties"""
        try:
            result = await self.session.call_tool("API-patch-page", {
                "page_id": page_id,
                "properties": properties
            })
            return self._extract_text(result)
        except Exception:
            return None
    
    async def add_blocks(self, page_id: str, blocks: List[Dict]) -> Optional[str]:
        """Add content blocks to page"""
        try:
            result = await self.session.call_tool("API-patch-block-children", {
                "block_id": page_id,
                "children": blocks
            })
            return self._extract_text(result)
        except Exception:
            return None
    
    # ==================== Helper Methods ====================
    
    def _extract_text(self, result) -> Optional[str]:
        """Extract text content from MCP result"""
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
            content = result_dict.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        return None
    
    # ==================== High-level Block Helpers ====================
    
    def create_heading_block(self, level: int, text: str) -> Dict:
        """Create heading block structure"""
        return {
            "object": "block",
            "type": f"heading_{level}",
            f"heading_{level}": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_paragraph_block(self, text: str) -> Dict:
        """Create paragraph block structure"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_bullet_list_blocks(self, items: List[str]) -> List[Dict]:
        """Create bulleted list blocks structure"""
        blocks = []
        for item in items:
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": item}}]
                }
            })
        return blocks
    
    async def add_heading(self, page_id: str, level: int, text: str) -> Optional[str]:
        """Add heading to page"""
        block = self.create_heading_block(level, text)
        return await self.add_blocks(page_id, [block])
    
    async def add_paragraph(self, page_id: str, text: str) -> Optional[str]:
        """Add paragraph to page"""
        block = self.create_paragraph_block(text)
        return await self.add_blocks(page_id, [block])
    
    async def add_bullet_list(self, page_id: str, items: List[str]) -> Optional[str]:
        """Add bulleted list to page"""
        blocks = self.create_bullet_list_blocks(items)
        return await self.add_blocks(page_id, blocks)