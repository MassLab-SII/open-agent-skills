"""
MCP Tools for Toronto Guide weekend adventure planner skills.
Pure MCP implementation without using notion_client library.
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
    Pure MCP tools for Notion operations via MCP protocol
    All methods call MCP tools and return raw results
    """
    
    def __init__(self, api_key: str, timeout: int = 120):
        """
        Initialize MCP tools.
        
        Args:
            api_key: Notion API key
            timeout: MCP operation timeout in seconds
        """
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
        """
        Search pages and databases in Notion
        
        Args:
            query: Search query string
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-post-search", {
                "query": query
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None
    
    async def query_database(self, database_id: str, filter_data: Optional[Dict] = None) -> Optional[str]:
        """
        Query a database
        
        Args:
            database_id: Database ID
            filter_data: Optional filter configuration
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            args = {"database_id": database_id}
            if filter_data:
                args["filter"] = filter_data
            
            result = await self.session.call_tool("API-post-database-query", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Query database error: {e}")
            return None
    
    async def get_block_children(self, block_id: str) -> Optional[str]:
        """
        Retrieve children blocks of a specified block
        
        Args:
            block_id: Block/Page ID
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-get-block-children", {
                "block_id": block_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Get block children error: {e}")
            return None
    
    async def patch_block_children(self, block_id: str, children: List[Dict], 
                                   after: Optional[str] = None) -> Optional[str]:
        """
        Add or update children blocks
        
        Args:
            block_id: Parent block ID
            children: List of children blocks to add
            after: Optional ID of block after which to insert
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            args = {
                "block_id": block_id,
                "children": children
            }
            
            if after:
                args["after"] = after
            
            result = await self.session.call_tool("API-patch-block-children", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Patch block children error: {e}")
            return None
    
    async def create_page(self, parent_id: str, title: str) -> Optional[str]:
        """
        Create a new page
        
        Args:
            parent_id: Parent page/database ID
            title: Page title
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-post-page", {
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"type": "text", "text": {"content": title}}]
                    }
                }
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Create page error: {e}")
            return None
    
    # ==================== Helper Methods ====================
    
    def _extract_text(self, result) -> Optional[str]:
        """
        Extract text content from MCP result
        
        Args:
            result: MCP result object
            
        Returns:
            Extracted text content or None
        """
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
            content = result_dict.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        return None
    
    # ==================== Block Creation Helpers ====================
    
    def create_heading_1(self, text: str) -> Dict:
        """Create heading_1 block"""
        return {
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_heading_2(self, text: str) -> Dict:
        """Create heading_2 block"""
        return {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_paragraph(self, text: str) -> Dict:
        """Create paragraph block"""
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_bulleted_list_item(self, text: str) -> Dict:
        """Create bulleted list item block"""
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_numbered_list_item(self, text: str) -> Dict:
        """Create numbered list item block"""
        return {
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    def create_toggle(self, title: str, children: List[Dict] = None) -> Dict:
        """Create toggle block with optional children"""
        block = {
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": title}}]
            }
        }
        if children:
            block["children"] = children
        return block
    
    def create_to_do(self, text: str, checked: bool = False) -> Dict:
        """Create to-do item block"""
        return {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "checked": checked
            }
        }
    
    def create_divider(self) -> Dict:
        """Create divider block"""
        return {
            "type": "divider",
            "divider": {}
        }
    
    def create_callout(self, text: str, emoji: str = "💡") -> Dict:
        """Create callout block with emoji icon"""
        return {
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "icon": {"type": "emoji", "emoji": emoji}
            }
        }
