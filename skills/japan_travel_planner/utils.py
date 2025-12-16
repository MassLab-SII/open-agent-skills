"""
Notion utilities for Japan Travel Planner skills.
Extends the base NotionTools with specific utilities for travel itineraries.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from notion_client import Client
from dotenv import load_dotenv

# Add the parent directory to the path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.logger import get_logger

logger = get_logger(__name__)


class TravelNotionTools:
    """Specialized Notion tools for travel planner database operations."""

    def __init__(self, api_key: str = None):
        """Initialize TravelNotionTools with Notion API client."""
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

    def find_database_in_children(self, parent_id: str, db_name: str) -> Optional[str]:
        """
        Find a child database by name within a page.
        
        Args:
            parent_id: Parent page ID
            db_name: Database name to search for
        
        Returns:
            Database ID if found, None otherwise
        """
        try:
            # Get all blocks of the parent page
            blocks = self._get_all_blocks_recursively(parent_id)
            
            for block in blocks:
                if block.get("type") == "child_database":
                    child_db = block.get("child_database", {})
                    title = child_db.get("title", "")
                    if db_name.lower() in title.lower():
                        # Found child_database block, but need to find actual database ID
                        # Try searching for the database by name
                        actual_db_id = self._find_database_by_search(db_name)
                        if actual_db_id:
                            self.logger.info(f"Found database '{db_name}': {actual_db_id}")
                            return actual_db_id
                        
                        # Fallback: use the child_database block ID
                        db_id = block.get("id")
                        self.logger.info(f"Found database '{db_name}' (child_database): {db_id}")
                        return db_id
            
            self.logger.warning(f"Database '{db_name}' not found in page {parent_id}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding database '{db_name}': {e}")
            return None

    def _find_database_by_search(self, db_name: str) -> Optional[str]:
        """
        Search for a database by name using the Notion search API.
        Returns the database ID that can be used for querying.
        
        Args:
            db_name: Database name to search for
        
        Returns:
            Database ID if found, None otherwise
        """
        try:
            response = self.client.search(query=db_name)
            
            results = response.get("results", [])
            for result in results:
                result_type = result.get("object")
                
                # Prefer database objects first
                if result_type == "database":
                    db_id = result.get("id")
                    self.logger.info(f"Found database object: {db_id}")
                    return db_id
            
            # If no database found, try data_source
            for result in results:
                result_type = result.get("object")
                if result_type == "data_source":
                    # Found a data_source, use it directly for querying
                    data_source_id = result.get("id")
                    self.logger.info(f"Found data_source (usable for query): {data_source_id}")
                    return data_source_id
            
            return None
        except Exception as e:
            self.logger.debug(f"Error searching for database '{db_name}': {e}")
            return None

    def query_database_with_filter(self, db_id: str, filter_criteria: Dict) -> List[Dict]:
        """
        Query a database with filter criteria.
        
        Args:
            db_id: Database ID
            filter_criteria: Filter dictionary for notion.databases.query()
        
        Returns:
            List of page results
        """
        try:
            results = []
            has_more = True
            start_cursor = None
            
            while has_more:
                # Try using data_sources.query() which is the newer API
                try:
                    response = self.client.data_sources.query(
                        data_source_id=db_id,
                        filter=filter_criteria,
                        start_cursor=start_cursor
                    )
                except Exception as e:
                    # Fallback: try databases.query() if it exists
                    self.logger.debug(f"data_sources.query failed, trying databases.query: {e}")
                    if hasattr(self.client.databases, 'query'):
                        response = self.client.databases.query(
                            database_id=db_id,
                            filter=filter_criteria,
                            start_cursor=start_cursor
                        )
                    else:
                        raise
                
                results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            self.logger.info(f"Query returned {len(results)} results from database {db_id}")
            return results
        except Exception as e:
            self.logger.error(f"Error querying database {db_id}: {e}")
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
            
            elif prop_type == "date":
                date = prop.get("date", {})
                if date:
                    return date.get("start", "")
            
            return default
        except Exception as e:
            self.logger.error(f"Error extracting property '{property_name}': {e}")
            return default

    def parse_time_to_minutes(self, time_str: str) -> Optional[int]:
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
        
        except Exception as e:
            self.logger.warning(f"Could not parse time '{time_str}': {e}")
            return None

    def archive_page(self, page_id: str) -> bool:
        """
        Archive (soft delete) a page.
        
        Args:
            page_id: Page ID to archive
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.pages.update(page_id=page_id, archived=True)
            self.logger.info(f"Archived page: {page_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error archiving page {page_id}: {e}")
            return False

    def _get_all_blocks_recursively(self, block_id: str, depth: int = 0, max_depth: int = 10) -> List[Dict]:
        """
        Recursively retrieve all blocks within a page or block.
        
        Args:
            block_id: Block/page ID to retrieve
            depth: Current recursion depth
            max_depth: Maximum recursion depth to prevent infinite loops
        
        Returns:
            List of all blocks found
        """
        if depth > max_depth:
            return []
        
        try:
            all_blocks = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.client.blocks.children.list(block_id=block_id, start_cursor=start_cursor)
                blocks = response.get("results", [])
                all_blocks.extend(blocks)
                
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            # Recursively get children of blocks that have children
            for block in all_blocks:
                if block.get("has_children"):
                    children = self._get_all_blocks_recursively(block["id"], depth + 1, max_depth)
                    all_blocks.extend(children)
            
            return all_blocks
        except Exception as e:
            self.logger.error(f"Error getting blocks for {block_id}: {e}")
            return []
