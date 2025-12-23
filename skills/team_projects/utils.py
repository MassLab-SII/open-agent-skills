"""MCP Tools for Team Projects task management operations."""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Optional, List, Dict, Any
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
    
    async def search(self, query: str) -> Optional[str]:
        """Search for pages and databases in Notion."""
        try:
            result = await self.client.call_tool("API-post-search", {
                "query": query,
                "filter": {"property": "object", "value": "page"}
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None
    
    async def retrieve_page(self, page_id: str) -> Optional[str]:
        """Retrieve a page by ID."""
        try:
            result = await self.client.call_tool("API-retrieve-a-page", {
                "page_id": page_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Retrieve page error: {e}")
            return None
    
    async def get_block_children(self, block_id: str) -> Optional[str]:
        """Get children blocks of a specified block."""
        try:
            result = await self.client.call_tool("API-get-block-children", {
                "block_id": block_id
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Get block children error: {e}")
            return None
    
    async def query_database(self, database_id: str, filter_obj: Optional[Dict] = None,
                           sorts: Optional[List] = None) -> Optional[str]:
        """Query a database."""
        try:
            args = {"database_id": database_id}
            if filter_obj:
                args["filter"] = filter_obj
            if sorts:
                args["sorts"] = sorts
            
            result = await self.client.call_tool("API-post-database-query", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Query database error: {e}")
            return None
    
    async def patch_page(self, page_id: str, properties: Dict[str, Any]) -> Optional[str]:
        """Update page properties."""
        try:
            args = {"page_id": page_id}
            args.update(properties)
            result = await self.client.call_tool("API-patch-page", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Patch page error: {e}")
            return None
    
    async def patch_block_children(self, block_id: str, children: List[Dict[str, Any]]) -> Optional[str]:
        """Add children blocks to a block using patch."""
        try:
            args = {
                "block_id": block_id,
                "children": children
            }
            result = await self.client.call_tool("API-patch-block-children", args)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Patch block children error: {e}")
            return None
    
    async def search_database(self, query: str) -> Optional[str]:
        """Search for databases in Notion."""
        try:
            result = await self.client.call_tool("API-post-search", {
                "query": query,
                "filter": {"property": "object", "value": "database"}
            })
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ Search database error: {e}")
            return None
    
    @staticmethod
    def _extract_text(result) -> Optional[str]:
        """Extract text content from MCP result."""
        try:
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
            content = result_dict.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        return None


def extract_property_value(properties: Dict[str, Any], property_name: str) -> Optional[str]:
    """Extract a property value from Notion properties."""
    try:
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
        elif prop_type == "people":
            people_array = prop.get("people", [])
            if people_array:
                return people_array[0].get("id", "")
        
        return None
    except Exception:
        return None


def extract_number_value(properties: Dict[str, Any], property_name: str) -> Optional[float]:
    """Extract a number value from Notion properties."""
    try:
        prop = properties.get(property_name, {})
        if prop.get("type") == "number":
            return prop.get("number")
        elif prop.get("type") == "rollup":
            rollup_data = prop.get("rollup", {})
            if isinstance(rollup_data, dict):
                return rollup_data.get("number")
        return None
    except Exception:
        return None


def extract_date_value(properties: Dict[str, Any], property_name: str) -> Optional[str]:
    """Extract a date value from Notion properties."""
    try:
        prop = properties.get(property_name, {})
        if prop.get("type") == "date":
            date_data = prop.get("date", {})
            if isinstance(date_data, dict):
                return date_data.get("start")
        return None
    except Exception:
        return None


def get_page_title(page: Dict[str, Any]) -> str:
    """Extract title from a Notion page object."""
    try:
        properties = page.get("properties", {})
        title_prop = properties.get("title", {})
        title_array = title_prop.get("title", [])
        if title_array:
            return title_array[0].get("plain_text", "")
    except Exception:
        pass
    return ""
