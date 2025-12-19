#!/usr/bin/env python3
"""
MCP Tools for Notion Operations (Computer Science Student Dashboard)
=====================================================================

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
    
    def create_column_block(self) -> Dict:
        """
        Create a column block structure for column_list
        
        Returns:
            Column block dictionary
        """
        return {
            "type": "column",
            "column": {
                "children": []
            }
        }
    
    def create_paragraph_block(self, text: str, bold: bool = False) -> Dict:
        """
        Create paragraph block structure
        
        Args:
            text: Text content
            bold: Whether to make text bold
            
        Returns:
            Paragraph block dictionary
        """
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": text},
                    "annotations": {"bold": bold} if bold else {}
                }]
            }
        }
    
    def create_code_block(self, code: str, language: str = "python", 
                         caption: Optional[str] = None) -> Dict:
        """
        Create code block structure
        
        Args:
            code: Code content
            language: Programming language
            caption: Optional caption for the code block
            
        Returns:
            Code block dictionary
        """
        block = {
            "type": "code",
            "code": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": code}
                }],
                "language": language
            }
        }
        
        if caption:
            block["code"]["caption"] = [{
                "type": "text",
                "text": {"content": caption}
            }]
        
        return block
    
    # ==================== High-level Operations ====================
    
    async def add_blocks_to_page(self, page_id: str, blocks: List[Dict], 
                                  after: Optional[str] = None) -> Optional[str]:
        """
        Add blocks to a page
        
        Args:
            page_id: Page ID
            blocks: List of block dictionaries to add
            after: Optional block ID after which to insert
            
        Returns:
            Raw MCP result as JSON string
        """
        return await self.patch_block_children(page_id, blocks, after)
    
    async def add_paragraph(self, block_id: str, text: str, 
                           bold: bool = False, after: Optional[str] = None) -> Optional[str]:
        """
        Add paragraph block
        
        Args:
            block_id: Parent block ID
            text: Text content
            bold: Whether text should be bold
            after: Optional block ID after which to insert
            
        Returns:
            Raw MCP result
        """
        block = self.create_paragraph_block(text, bold)
        return await self.patch_block_children(block_id, [block], after)
    
    async def add_code_block(self, block_id: str, code: str, 
                            language: str = "python", 
                            caption: Optional[str] = None,
                            after: Optional[str] = None) -> Optional[str]:
        """
        Add code block
        
        Args:
            block_id: Parent block ID
            code: Code content
            language: Programming language
            caption: Optional caption
            after: Optional block ID after which to insert
            
        Returns:
            Raw MCP result
        """
        block = self.create_code_block(code, language, caption)
        return await self.patch_block_children(block_id, [block], after)
    
    async def add_column(self, column_list_id: str, 
                        after: Optional[str] = None) -> Optional[str]:
        """
        Add a new column to a column_list block
        
        Args:
            column_list_id: Column list block ID
            after: Optional column ID after which to insert
            
        Returns:
            Raw MCP result with new column info
        """
        column = self.create_column_block()
        return await self.patch_block_children(column_list_id, [column], after)
