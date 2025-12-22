"""MCP tools wrapper for Notion API - Online Resume page operations."""

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
    
    async def retrieve_page(self, page_id: str) -> Dict[str, Any]:
        """Retrieve a page by ID."""
        try:
            result = await self.client.call_tool("API-retrieve-a-page", {
                "page_id": page_id
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Retrieve page error: {e}")
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
    
    async def retrieve_database(self, database_id: str) -> Dict[str, Any]:
        """Retrieve a database by ID."""
        try:
            result = await self.client.call_tool("API-retrieve-a-database", {
                "database_id": database_id
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Retrieve database error: {e}")
            return {}
    
    async def query_database(self, database_id: str, filter_obj: Optional[Dict] = None, 
                           sorts: Optional[List] = None) -> Dict[str, Any]:
        """Query a database using API-post-database-query."""
        try:
            args = {"database_id": database_id}
            if filter_obj:
                args["filter"] = filter_obj
            if sorts:
                args["sorts"] = sorts
            
            result = await self.client.call_tool("API-post-database-query", args)
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Query database error: {e}")
            return {}
    
    async def patch_page(self, page_id: str, archived: bool = True) -> Dict[str, Any]:
        """Archive or update a page using API-patch-page."""
        try:
            result = await self.client.call_tool("API-patch-page", {
                "page_id": page_id,
                "archived": archived
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Patch page error: {e}")
            return {}
    
    async def create_page(self, parent_database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new page in a database using API-post-page."""
        try:
            result = await self.client.call_tool("API-post-page", {
                "parent": {"database_id": parent_database_id},
                "properties": properties
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Create page error: {e}")
            return {}
    
    async def update_database(self, database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update database properties using API-update-a-database."""
        try:
            result = await self.client.call_tool("API-update-a-database", {
                "database_id": database_id,
                "properties": properties
            })
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Update database error: {e}")
            return {}
    
    async def patch_block_children(self, block_id: str, children: List[Dict[str, Any]], 
                                  after: Optional[str] = None) -> Dict[str, Any]:
        """Patch block children using API-patch-block-children."""
        try:
            args = {
                "block_id": block_id,
                "children": children
            }
            if after:
                args["after"] = after
            
            result = await self.client.call_tool("API-patch-block-children", args)
            text_result = self._extract_text(result)
            if text_result:
                return json.loads(text_result)
            return {}
        except Exception as e:
            print(f"❌ Patch block children error: {e}")
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
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "select":
            select = prop.get("select", {})
            if select:
                return select.get("name", "")
        elif prop_type == "phone_number":
            return prop.get("phone_number", "")
        elif prop_type == "url":
            return prop.get("url", "")
        
        return None
    except Exception:
        return None
