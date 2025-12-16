#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Tools for IT Trouble Shooting Hub
=========================================

This module provides a high-level wrapper around Notion API for IT management tasks.
It includes database querying, page creation, and block manipulation capabilities.
"""

from typing import Dict, List, Optional, Any

from notion_client import Client


class NotionTools:
    """
    High-level wrapper for Notion API operations specific to IT management.
    
    This class provides convenient methods for common Notion operations used in
    IT Trouble Shooting Hub tasks.
    """

    def __init__(self, api_key: str):
        """
        Initialize Notion tools.
        
        Args:
            api_key: Notion API key
        """
        self.api_key = api_key
        self.client = Client(auth=api_key)

    def search_page(self, query: str, object_type: Optional[str] = None) -> Optional[Dict]:
        """
        Search for a page by name/query
        
        Args:
            query: Search query (page name or content)
            object_type: Optional type filter ("page", "data_source", etc)
            
        Returns:
            Dictionary with page information or None if not found
        """
        try:
            # Try searching for the specific type if specified
            if object_type:
                response = self.client.search(query=query, filter={"value": object_type, "property": "object"})
            else:
                # Search without type filter
                response = self.client.search(query=query)
            
            if response.get("results"):
                return response["results"][0]
            return None
        except Exception as e:
            print(f"Error searching for page: {e}")
            return None

    def find_database_by_name(self, database_name: str) -> Optional[str]:
        """
        Find a database ID by searching for it by name
        Searches for data_source type which includes databases in newer Notion API
        
        Args:
            database_name: Name of the database to find
            
        Returns:
            Database ID or None if not found
        """
        try:
            # Search for databases by name (they appear as data_source type)
            search_result = self.client.search(query=database_name)
            
            # Look for data_source or database type results
            for result in search_result.get("results", []):
                result_type = result.get("object")
                title = result.get("title")
                
                # Handle title as list of rich text
                if isinstance(title, list):
                    title = "".join(rt.get("plain_text", "") for rt in title)
                
                # Match by exact name and type
                if result_type in ("database", "data_source"):
                    if title == database_name:
                        return result.get("id")
            
            return None
        except Exception as e:
            print(f"Error finding database: {e}")
            return None

    def find_database_in_page(self, page_id: str, database_name: str) -> Optional[str]:
        """
        Find a database ID by searching through child blocks of a page
        or by searching for it by name
        
        Args:
            page_id: Parent page ID
            database_name: Name of the database to find
            
        Returns:
            Database ID or None if not found
        """
        try:
            # First, try to find it as a child database block
            blocks = self.client.blocks.children.list(page_id)
            for block in blocks.get("results", []):
                if block.get("type") == "child_database":
                    child_db = block.get("child_database", {})
                    if child_db.get("title") == database_name:
                        return block.get("id")
            
            # If not found as child block, search for database by name
            return self.find_database_by_name(database_name)
            
            return None
        except Exception as e:
            print(f"Error finding database in page: {e}")
            return None

    def search_database(self, query: str) -> Optional[Dict]:
        """
        Search for a database by name/query
        
        Args:
            query: Search query (database name)
            
        Returns:
            Dictionary with database information or None if not found
        """
        try:
            # Search without filter - will return both pages and databases
            response = self.client.search(query=query)
            
            # Filter for databases in the response
            for result in response.get("results", []):
                if result.get("object") == "database":
                    return result
            
            return None
        except Exception as e:
            print(f"Error searching for database: {e}")
            return None

    def query_database(
        self,
        database_id: str,
        filter_config: Optional[Dict] = None,
        page_size: int = 100
    ) -> List[Dict]:
        """
        Query a database with optional filters
        
        Args:
            database_id: Database ID to query
            filter_config: Optional filter configuration
            page_size: Number of results per page
            
        Returns:
            List of page objects matching the query
        """
        try:
            query_params = {
                "data_source_id": database_id,
                "page_size": page_size
            }
            if filter_config:
                query_params["filter"] = filter_config
            
            # Use data_sources.query() for newer notion-client versions
            response = self.client.data_sources.query(**query_params)
            return response.get("results", [])
        except Exception as e:
            print(f"Error querying database: {e}")
            return []

    def get_page_properties(self, page_id: str) -> Dict:
        """
        Get all properties of a page
        
        Args:
            page_id: Page ID
            
        Returns:
            Dictionary with page properties
        """
        try:
            page = self.client.pages.retrieve(page_id)
            return page.get("properties", {})
        except Exception as e:
            print(f"Error getting page properties: {e}")
            return {}

    def create_page_in_database(
        self,
        database_id: str,
        title: str,
        properties: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a new page in a database
        
        Note: This method handles both regular databases and data_source databases.
        For data_source databases, we first retrieve the parent database_id.
        
        Args:
            database_id: Database or data_source ID
            title: Page title (used as fallback if not in properties)
            properties: Additional properties to set (should include title property)
            
        Returns:
            Created page object or None
        """
        try:
            # First, check if this is a data_source and get the actual database_id
            actual_db_id = database_id
            try:
                ds = self.client.data_sources.retrieve(data_source_id=database_id)
                parent = ds.get("parent", {})
                if parent.get("type") == "database_id":
                    actual_db_id = parent.get("database_id")
            except:
                # Not a data_source, use as-is
                pass
            
            # Prepare properties
            page_properties = {}
            if properties:
                page_properties.update(properties)
            
            # If no title property was provided, create a default one
            # (This handles cases where properties doesn't explicitly include title)
            if not any(v.get("title") for v in page_properties.values() if isinstance(v, dict)):
                page_properties["title"] = [{"text": {"content": title}}]
            
            # Use proper parent format for database creation
            page = self.client.pages.create(
                parent={"database_id": actual_db_id},
                properties=page_properties
            )
            return page
        except Exception as e:
            print(f"Error creating page in database: {e}")
            return None

    def add_bullet_list(
        self,
        page_id: str,
        items: List[str]
    ) -> Dict:
        """
        Add a bullet list to a page
        
        Args:
            page_id: Page ID
            items: List of text items for bullets
            
        Returns:
            Response from the API
        """
        try:
            children = []
            for item in items:
                children.append({
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": item}
                            }
                        ]
                    }
                })
            
            result = self.client.blocks.children.append(
                block_id=page_id,
                children=children
            )
            return result
        except Exception as e:
            print(f"Error adding bullet list: {e}")
            return {}

    def get_block_children(self, block_id: str) -> List[Dict]:
        """
        Get children blocks of a specified block
        
        Args:
            block_id: Block ID
            
        Returns:
            List of child blocks
        """
        try:
            response = self.client.blocks.children.list(block_id)
            return response.get("results", [])
        except Exception as e:
            print(f"Error getting block children: {e}")
            return []

    def get_plain_text_from_rich_text(self, rich_text_array: List[Dict]) -> str:
        """
        Extract plain text from a rich_text array
        
        Args:
            rich_text_array: Array of rich text objects
            
        Returns:
            Concatenated plain text
        """
        return "".join([item.get("plain_text", "") for item in rich_text_array])

    def _get_page_title(self, page: Dict) -> str:
        """
        Extract title from a page object
        
        Args:
            page: Page object from Notion API
            
        Returns:
            Page title as string
        """
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_content = prop_data.get("title", [])
                if title_content:
                    return self.get_plain_text_from_rich_text(title_content)
        return ""
