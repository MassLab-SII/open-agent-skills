#!/usr/bin/env python3
"""
MCP Tools for Notion Operations (Company In A Box - Goals Restructure)
======================================================================

Pure MCP tool wrapper for Notion operations without using notion_client library.
All operations are performed via MCP protocol tools.
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
    
    async def update_block(self, block_id: str, block_data: Dict) -> Optional[str]:
        """
        Update a block's properties using API-update-a-block
        
        Args:
            block_id: Block ID
            block_data: Block data to update (e.g., {"heading_3": {...}})
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            args = {
                "block_id": block_id,
            }
            args.update(block_data)
            
            result = await self.session.call_tool("API-update-a-block", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Update block error: {e}")
            return None
    
    async def delete_block(self, block_id: str) -> Optional[str]:
        """
        Delete a block using API-delete-a-block
        
        Args:
            block_id: Block ID to delete
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-delete-a-block", {
                "block_id": block_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Delete block error: {e}")
            return None
        """
        Delete a block
        
        Args:
            block_id: Block ID to delete
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-delete-block", {
                "block_id": block_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Delete block error: {e}")
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
    
    def create_heading_3_block(self, text: str, is_toggleable: bool = False) -> Dict:
        """
        Create heading_3 block structure
        
        Args:
            text: Heading text
            is_toggleable: Whether heading should be toggleable
            
        Returns:
            Heading block dictionary
        """
        block = {
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            }
        }
        
        if is_toggleable:
            block["heading_3"]["is_toggleable"] = True
        
        return block
    
    def create_paragraph_block(self, text: str) -> Dict:
        """
        Create paragraph block structure
        
        Args:
            text: Text content
            
        Returns:
            Paragraph block dictionary
        """
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
    
    # ==================== High-level Operations ====================
    
    async def add_heading_3(self, parent_id: str, text: str, 
                           is_toggleable: bool = False,
                           after: Optional[str] = None) -> Optional[str]:
        """
        Add heading_3 block
        
        Args:
            parent_id: Parent block ID
            text: Heading text
            is_toggleable: Whether heading should be toggleable
            after: Optional block ID after which to insert
            
        Returns:
            Raw MCP result
        """
        block = self.create_heading_3_block(text, is_toggleable)
        return await self.patch_block_children(parent_id, [block], after)
    
    async def add_paragraph(self, block_id: str, text: str) -> Optional[str]:
        """
        Add paragraph block
        
        Args:
            block_id: Parent block ID
            text: Text content
            
        Returns:
            Raw MCP result
        """
        block = self.create_paragraph_block(text)
        return await self.patch_block_children(block_id, [block])
    
    async def create_database(self, parent_page_id: str, title: str, 
                             properties: Dict[str, Any]) -> Optional[str]:
        """
        Create a new database
        
        Args:
            parent_page_id: Parent page ID
            title: Database title
            properties: Database properties
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            args = {
                "parent": {
                    "page_id": parent_page_id,
                    "type": "page_id"
                },
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title}
                    }
                ],
                "properties": properties
            }
            
            result = await self.session.call_tool("API-create-a-database", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Create database error: {e}")
            return None
    
    async def create_page(self, parent_id: str, 
                         properties: Dict[str, Any],
                         children: Optional[List[Dict]] = None,
                         parent_type: Optional[str] = None) -> Optional[str]:
        """
        Create a new page
        
        Args:
            parent_id: Database ID or Page ID (depends on parent_type)
            properties: Page properties to set
            children: Optional list of child blocks
            parent_type: Type of parent - 'database_id' or 'page_id'. 
                        If None, auto-detect (32-char UUID typically database, otherwise assume page)
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            # Auto-detect parent type if not specified
            if parent_type is None:
                # Simple heuristic: if it looks like it could be either, try to infer
                # For safety, assume database_id if not specified explicitly
                parent_type = "database_id"
            
            args = {
                "parent": {
                    parent_type: parent_id,
                    "type": parent_type
                },
                "properties": properties
            }
            
            if children:
                args["children"] = children
            
            result = await self.session.call_tool("API-post-page", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Create page error: {e}")
            return None

