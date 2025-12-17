"""
Notion utilities for Toronto Guide weekend adventure planner skills.
Handles database queries, page creation, and block operations.
"""

import os
import sys
from typing import Dict, List, Optional, Any
from notion_client import Client
from dotenv import load_dotenv

# Add the parent directory to the path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.logger import get_logger

logger = get_logger(__name__)


class TorontoGuideNotionTools:
    """Specialized Notion tools for Toronto Guide database operations."""

    def __init__(self, api_key: str = None):
        """Initialize TorontoGuideNotionTools with Notion API client."""
        if api_key is None:
            # Try to load from environment first
            api_key = os.getenv("EVAL_NOTION_API_KEY")
            
            # If not found, try to load from .mcp_env file
            if not api_key:
                load_dotenv(dotenv_path=".mcp_env")
                api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment or .mcp_env")
        
        self.client = Client(auth=api_key)
        self.logger = logger

    def search_page(self, query: str, object_type: str = "page") -> Optional[str]:
        """
        Search for a page by query string.
        
        Args:
            query: Search query string
            object_type: Type of object to search ('page' or 'database')
        
        Returns:
            Page ID if found, None otherwise
        """
        try:
            response = self.client.search(query=query, filter={"value": object_type, "property": "object"})
            results = response.get("results", [])
            if results:
                page_id = results[0].get("id")
                self.logger.info(f"Found {object_type}: {page_id}")
                return page_id
            self.logger.warning(f"No {object_type} found for query: {query}")
            return None
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {e}")
            return None

    def find_databases_in_page(self, parent_id: str) -> Dict[str, str]:
        """
        Find all child databases within a page by name.
        
        Args:
            parent_id: Parent page ID
        
        Returns:
            Dictionary mapping database names to their IDs
        """
        try:
            databases = {}
            blocks = self._get_all_blocks_recursively(parent_id)
            
            for block in blocks:
                if block.get("type") == "child_database":
                    child_db = block.get("child_database", {})
                    title = child_db.get("title", "")
                    
                    # Try to find the actual database ID
                    actual_db_id = self._find_database_by_search(title)
                    if actual_db_id:
                        databases[title] = actual_db_id
                    else:
                        databases[title] = block.get("id")
            
            self.logger.info(f"Found {len(databases)} databases in page {parent_id}")
            return databases
        except Exception as e:
            self.logger.error(f"Error finding databases in page '{parent_id}': {e}")
            return {}

    def _find_database_by_search(self, db_name: str) -> Optional[str]:
        """
        Search for a database by name using the Notion search API.
        
        Args:
            db_name: Database name to search for
        
        Returns:
            Database ID if found, None otherwise
        """
        try:
            response = self.client.search(query=db_name)
            
            results = response.get("results", [])
            
            # Prefer database objects first
            for result in results:
                if result.get("object") == "database":
                    return result.get("id")
            
            # If no database found, try data_source
            for result in results:
                if result.get("object") == "data_source":
                    return result.get("id")
            
            return None
        except Exception as e:
            self.logger.debug(f"Error searching for database '{db_name}': {e}")
            return None

    def query_database(self, db_id: str, filter_criteria: Dict = None) -> List[Dict]:
        """
        Query a database with optional filter criteria.
        Handles API compatibility for notion-client 2.7.0.
        
        Args:
            db_id: Database ID (can be block ID or data_source ID)
            filter_criteria: Optional filter dictionary
        
        Returns:
            List of page results
        """
        try:
            # Try using data_sources.query() first (notion-client 2.7.0+)
            try:
                if filter_criteria:
                    response = self.client.data_sources.query(data_source_id=db_id, filter=filter_criteria)
                else:
                    response = self.client.data_sources.query(data_source_id=db_id)
                
                pages = response.get("results", [])
                self.logger.info(f"Queried database {db_id}: found {len(pages)} pages")
                return pages
            except (AttributeError, TypeError):
                # Fallback: if db_id is a block ID, try to find the data_source
                self.logger.debug(f"data_sources.query() failed, trying databases.query() as fallback")
                if filter_criteria:
                    response = self.client.databases.query(database_id=db_id, filter=filter_criteria)
                else:
                    response = self.client.databases.query(database_id=db_id)
                
                pages = response.get("results", [])
                self.logger.info(f"Queried database {db_id}: found {len(pages)} pages")
                return pages
        except Exception as e:
            self.logger.error(f"Error querying database {db_id}: {e}")
            # If it's a block ID, try to find the actual data_source
            try:
                self.logger.debug(f"Attempting to convert block ID {db_id} to data_source ID")
                block = self.client.blocks.retrieve(block_id=db_id)
                if block.get("type") == "child_database":
                    title = block.get("child_database", {}).get("title", "")
                    data_source_id = self._find_database_by_search(title)
                    if data_source_id:
                        self.logger.info(f"Found data_source {data_source_id} for block {db_id}")
                        return self.query_database(data_source_id, filter_criteria)
            except Exception as e2:
                self.logger.error(f"Error converting block ID to data_source: {e2}")
            
            return []

    def get_page_property(self, page: Dict, property_name: str, default: str = None) -> Optional[str]:
        """
        Extract a property value from a page result.
        
        Args:
            page: Page result from Notion API
            property_name: Name of the property to extract
            default: Default value if property not found
        
        Returns:
            Property value as string, or default value if not found
        """
        try:
            properties = page.get("properties", {})
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
            
            elif prop_type == "multi_select":
                multi_select_array = prop.get("multi_select", [])
                if multi_select_array:
                    return [item.get("name") for item in multi_select_array]
            
            elif prop_type == "url":
                return prop.get("url", "")
            
            elif prop_type == "date":
                date = prop.get("date", {})
                if date:
                    return date.get("start", "")
            
            return default
        except Exception as e:
            self.logger.error(f"Error extracting property '{property_name}': {e}")
            return default

    def create_page(self, parent_id: str, title: str) -> Optional[str]:
        """
        Create a new page as a child of another page.
        
        Args:
            parent_id: Parent page ID
            title: Page title
        
        Returns:
            New page ID if successful, None otherwise
        """
        try:
            response = self.client.pages.create(
                parent={"page_id": parent_id},
                properties={
                    "title": {
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title}
                            }
                        ]
                    }
                }
            )
            page_id = response.get("id")
            self.logger.info(f"Created page '{title}': {page_id}")
            return page_id
        except Exception as e:
            self.logger.error(f"Error creating page '{title}': {e}")
            return None

    def add_blocks_to_page(self, page_id: str, blocks: List[Dict]) -> bool:
        """
        Add multiple blocks to a page.
        Handles blocks with children correctly by adding them separately.
        Preserves the original order of blocks.
        
        Args:
            page_id: Page ID to add blocks to
            blocks: List of block dictionaries
        
        Returns:
            True if successful, False otherwise
        """
        import copy
        try:
            # Process blocks while maintaining order
            # First pass: add all blocks, separating those with children for special handling
            blocks_with_children_info = []  # Store info about blocks with children
            
            for idx, block in enumerate(blocks):
                # Check if block has children in its type-specific object
                block_type = block.get("type")
                type_obj = block.get(block_type, {})
                
                if isinstance(type_obj, dict) and "children" in type_obj:
                    # Make a copy to avoid modifying the original
                    block_copy = copy.deepcopy(block)
                    type_obj_copy = block_copy.get(block_type, {})
                    children = type_obj_copy.pop("children", [])
                    
                    # Add the parent block (without children) 
                    response = self.client.blocks.children.append(
                        block_id=page_id,
                        children=[block_copy]
                    )
                    
                    if response.get("results"):
                        parent_block_id = response["results"][0].get("id")
                        self.logger.info(f"Created parent block {block_type}: {parent_block_id}")
                        
                        # Now add the children to the parent block
                        if parent_block_id and children:
                            try:
                                self.client.blocks.children.append(
                                    block_id=parent_block_id,
                                    children=children
                                )
                                self.logger.info(f"Added {len(children)} children to {block_type} block {parent_block_id}")
                            except Exception as child_error:
                                self.logger.error(f"Failed to add children to {block_type} block {parent_block_id}: {child_error}")
                                return False
                else:
                    # Add regular blocks
                    response = self.client.blocks.children.append(
                        block_id=page_id,
                        children=[block]
                    )
                    
                    if response.get("results"):
                        self.logger.debug(f"Added {block_type} block")
            
            self.logger.info(f"Successfully added all {len(blocks)} blocks to page {page_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding blocks to page {page_id}: {e}")
            return False

    def _get_all_blocks_recursively(self, parent_id: str, max_depth: int = 10) -> List[Dict]:
        """
        Get all blocks recursively from a page.
        
        Args:
            parent_id: Parent page/block ID
            max_depth: Maximum recursion depth
        
        Returns:
            List of all blocks
        """
        if max_depth <= 0:
            return []
        
        try:
            blocks = []
            response = self.client.blocks.children.list(block_id=parent_id)
            
            for block in response.get("results", []):
                blocks.append(block)
                
                # Recursively get child blocks
                if block.get("has_children"):
                    child_blocks = self._get_all_blocks_recursively(block.get("id"), max_depth - 1)
                    blocks.extend(child_blocks)
            
            return blocks
        except Exception as e:
            self.logger.error(f"Error getting blocks from {parent_id}: {e}")
            return []
