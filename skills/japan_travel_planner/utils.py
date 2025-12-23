"""
MCP Tools for Notion Operations (Japan Travel Planner)
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
    
    async def get_page(self, page_id: str) -> Optional[str]:
        """
        Retrieve a page by ID
        
        Args:
            page_id: Page ID
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-retrieve-a-page", {
                "page_id": page_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Get page error: {e}")
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
    
    async def query_database(self, database_id: str, filter_obj: Dict[str, Any] = None, 
                            sorts: List[Dict] = None) -> Optional[str]:
        """
        Query a Notion database with optional filters and sorts
        
        Args:
            database_id: Database ID
            filter_obj: Optional filter object for the query
            sorts: Optional list of sort configurations
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            args = {
                "database_id": database_id
            }
            
            if filter_obj:
                args["filter"] = filter_obj
            
            if sorts:
                args["sorts"] = sorts
            
            result = await self.session.call_tool("API-post-database-query", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Query database error: {e}")
            return None
    
    async def patch_page(self, page_id: str, archived: bool = True) -> Optional[str]:
        """
        Archive or update a page
        
        Args:
            page_id: Page ID to archive
            archived: Whether to archive the page (default: True)
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            result = await self.session.call_tool("API-patch-page", {
                "page_id": page_id,
                "archived": archived
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Patch page error: {e}")
            return None
    
    async def create_page(self, parent_database_id: str, properties: Dict[str, Any]) -> Optional[str]:
        """
        Create a new page in a database
        
        Args:
            parent_database_id: Database ID where the page will be created
            properties: Page properties to set
            
        Returns:
            Raw MCP result as JSON string or None on error
        """
        try:
            args = {
                "parent": {
                    "database_id": parent_database_id
                },
                "properties": properties
            }
            
            result = await self.session.call_tool("API-post-page", args)
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


def parse_time_to_minutes(time_str: str) -> Optional[int]:
    """
    Convert time string to minutes since midnight for comparison.
    Supports formats like "6 PM", "6:30 PM", "18:00", etc.
    
    Args:
        time_str: Time string to parse
    
    Returns:
        Minutes since midnight (0-1439), or None if unparseable
    """
    if not time_str:
        return None
    
    try:
        time_str = time_str.strip().upper()
        # Remove trailing newlines/whitespace
        time_str = time_str.split('\n')[0].strip()
        
        if "PM" in time_str:
            time_part = time_str.replace("PM", "").strip()
            if ":" in time_part:
                hours, minutes = map(int, time_part.split(":"))
            else:
                hours = int(time_part)
                minutes = 0
            
            # Convert to 24-hour format
            if hours != 12:
                hours += 12
            return hours * 60 + minutes
        
        elif "AM" in time_str:
            time_part = time_str.replace("AM", "").strip()
            if ":" in time_part:
                hours, minutes = map(int, time_part.split(":"))
            else:
                hours = int(time_part)
                minutes = 0
            
            # Handle 12 AM (midnight)
            if hours == 12:
                hours = 0
            return hours * 60 + minutes
        
        else:
            # Try parsing as 24-hour format
            if ":" in time_str:
                hours, minutes = map(int, time_str.split(":"))
                return hours * 60 + minutes
            else:
                hours = int(time_str)
                return hours * 60
    
    except Exception:
        return None


def extract_page_property(page_result: Dict, property_name: str) -> Optional[str]:
    """
    Extract a property value from a Notion page result.
    
    Args:
        page_result: Page result from Notion API
        property_name: Name of the property to extract
    
    Returns:
        Property value as string, or None if not found
    """
    try:
        properties = page_result.get("properties", {})
        prop = properties.get(property_name, {})
        prop_type = prop.get("type")
        
        if prop_type == "title":
            title_array = prop.get("title", [])
            if title_array:
                return title_array[0].get("plain_text", "")
        
        elif prop_type == "rich_text":
            rich_text_array = prop.get("rich_text", [])
            if rich_text_array:
                return rich_text_array[0].get("plain_text", "")
        
        elif prop_type == "select":
            select = prop.get("select", {})
            if select:
                return select.get("name", "")
        
        elif prop_type == "date":
            date = prop.get("date", {})
            if date:
                return date.get("start", "")
        
        return None
    except Exception:
        return None

