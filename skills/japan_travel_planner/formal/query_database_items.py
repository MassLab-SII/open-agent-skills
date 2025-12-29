#!/usr/bin/env python3
"""
Query Database Items - Generic Skill
====================================

This skill:
1. Searches for a database by name
2. Queries all items in the database
3. Groups items by a specified property (optional)
4. Returns structured data about all items

Generic parameters allow LLM to customize:
- database_name: Name of the database to query
- group_by_property: Property name to group results (optional)
- filter_criteria: Filter conditions (optional)

Uses Notion Client library for all Notion operations.
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
from skills.japan_travel_planner.utils import NotionMCPTools

# Load environment variables
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break


class QueryDatabaseItems:
    """
    Generic skill to query items from a Notion database.
    Can group results by any property.
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with Notion API key"""
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment")
        
        self.api_key = api_key
    
    async def process(
        self,
        database_name: str,
        group_by_property: Optional[str] = None,
        return_full_objects: bool = False
    ) -> Dict[str, Any]:
        """
        Query database items.
        
        Args:
            database_name: Name of the database to search for
            group_by_property: Optional property name to group results by
            return_full_objects: Whether to return full page objects or just key properties
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - database_id: ID of the found database
            - items: List of items or grouped items
            - groups: Dictionary of grouped items (if group_by_property specified)
            - total_count: Total number of items
            - errors: List of error messages
        """
        result = {
            "success": False,
            "database_id": None,
            "items": [],
            "groups": {},
            "total_count": 0,
            "errors": [],
        }
        
        async with NotionMCPTools(self.api_key, notion_version="2025-09-03") as mcp:
            try:
                # Step 1: Search for database
                print(f"\n📍 Searching for database: {database_name}")
                print("-" * 70)
                
                search_result = await mcp.search(database_name)
                if not search_result:
                    result["errors"].append(f"Database '{database_name}' not found")
                    return result
                
                search_data = json.loads(search_result)
                database = None
                
                # In MCP v2.0.0+, databases are called "data_source"
                # In older versions, they were called "database"
                for item in search_data.get("results", []):
                    obj_type = item.get("object")
                    if obj_type == "data_source" or obj_type == "database":
                        # Check if the title matches
                        title_prop = item.get("title", [])
                        if title_prop:
                            if isinstance(title_prop, list) and len(title_prop) > 0:
                                item_title = title_prop[0].get("plain_text", "")
                            else:
                                item_title = str(title_prop)
                            
                            if database_name.lower() in item_title.lower():
                                database = item
                                break
                
                # If no exact title match, just take the first data_source/database
                if not database:
                    for item in search_data.get("results", []):
                        obj_type = item.get("object")
                        if obj_type == "data_source" or obj_type == "database":
                            database = item
                            break
                
                if not database:
                    result["errors"].append(f"No data_source/database found for '{database_name}'")
                    return result
                
                database_id = database.get("id")
                result["database_id"] = database_id
                print(f"✓ Found database (ID: {database_id[:20]}...)")
                
                # Step 2: Query all items
                print(f"\n📍 Querying items from database")
                print("-" * 70)
                
                query_result = await mcp.query_database(database_id)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                query_data = json.loads(query_result)
                all_items = query_data.get("results", [])
                result["total_count"] = len(all_items)
                print(f"✓ Retrieved {len(all_items)} items")
                
                # Step 3: Parse items and optionally group them
                if group_by_property:
                    print(f"\n📍 Grouping items by: {group_by_property}")
                    print("-" * 70)
                    
                    grouped_items = defaultdict(list)
                    
                    for item in all_items:
                        properties = item.get("properties", {})
                        
                        # Extract the grouping property
                        group_prop = properties.get(group_by_property, {})
                        group_values = []
                        
                        if group_prop.get("type") == "multi_select":
                            group_values = [opt.get("name", "") for opt in group_prop.get("multi_select", [])]
                        elif group_prop.get("type") == "select":
                            select_val = group_prop.get("select")
                            if select_val:
                                group_values = [select_val.get("name", "")]
                        elif group_prop.get("type") == "title":
                            title_array = group_prop.get("title", [])
                            if title_array:
                                group_values = ["".join([t.get("plain_text", "") for t in title_array])]
                        else:
                            # Try to extract as text
                            if isinstance(group_prop, dict) and "plain_text" in str(group_prop):
                                group_values = [str(group_prop)]
                        
                        # If no group values, put in "Unspecified"
                        if not group_values:
                            group_values = ["Unspecified"]
                        
                        # Create simplified item representation
                        item_data = self._extract_item_data(item, return_full_objects)
                        
                        # Add to each group this item belongs to
                        for group_val in group_values:
                            if group_val:
                                grouped_items[group_val].append(item_data)
                    
                    result["groups"] = dict(grouped_items)
                    
                    # Print group summary
                    for group_name, items in sorted(grouped_items.items()):
                        print(f"  • {group_name}: {len(items)} items")
                
                else:
                    # Return flat list
                    result["items"] = [self._extract_item_data(item, return_full_objects) for item in all_items]
                
                result["success"] = True
                
            except Exception as e:
                result["errors"].append(f"Processing error: {str(e)}")
                print(f"❌ Error: {e}")
        
        return result
    
    def _extract_item_data(self, item: Dict, return_full: bool = False) -> Dict[str, Any]:
        """Extract key information from a page object"""
        if return_full:
            return item
        
        properties = item.get("properties", {})
        item_data = {
            "id": item.get("id"),
            "name": self._extract_property_value(properties, "Name"),
            "properties": {}
        }
        
        # Extract all properties
        for prop_name, prop_value in properties.items():
            item_data["properties"][prop_name] = self._extract_property_value(
                {prop_name: prop_value}, prop_name
            )
        
        return item_data
    
    def _extract_property_value(self, properties: Dict, prop_name: str) -> Any:
        """Extract value from any property type"""
        prop = properties.get(prop_name, {})
        prop_type = prop.get("type")
        
        if prop_type == "title":
            title_array = prop.get("title", [])
            return "".join([t.get("plain_text", "") for t in title_array])
        elif prop_type == "rich_text":
            text_array = prop.get("rich_text", [])
            return "".join([t.get("plain_text", "") for t in text_array])
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        elif prop_type == "select":
            select_val = prop.get("select")
            return select_val.get("name", "") if select_val else None
        elif prop_type == "multi_select":
            return [opt.get("name", "") for opt in prop.get("multi_select", [])]
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "date":
            date_val = prop.get("date")
            return date_val.get("start", "") if date_val else None
        else:
            return None


async def main():
    """Main entry point - supports CLI usage"""
    try:
        # Parse command line arguments
        if len(sys.argv) < 2:
            print("Usage: python3 query_database_items.py <database_name> [group_by_property] [--json] [--api-key KEY]")
            print("\nExamples:")
            print("  python3 query_database_items.py 'Packing List'")
            print("  python3 query_database_items.py 'Packing List' Type")
            print("  python3 query_database_items.py 'Packing List' Type --json")
            return 1
        
        database_name = sys.argv[1]
        group_by_property = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
        output_json = "--json" in sys.argv
        
        # Extract API key from args or environment
        api_key = os.getenv("EVAL_NOTION_API_KEY")
        for i, arg in enumerate(sys.argv):
            if arg == "--api-key" and i + 1 < len(sys.argv):
                api_key = sys.argv[i + 1]
        
        skill = QueryDatabaseItems(api_key)
        
        result = await skill.process(
            database_name=database_name,
            group_by_property=group_by_property
        )
        
        # Output results
        if output_json:
            # Output as JSON for programmatic use
            print(json.dumps(result, indent=2))
        else:
            # Pretty print
            print("\n" + "=" * 70)
            print("RESULT SUMMARY")
            print("=" * 70)
            print(f"Success: {result['success']}")
            print(f"Database ID: {result['database_id']}")
            print(f"Total Items: {result['total_count']}")
            
            if result['groups']:
                print("\n📊 Items by Group:")
                for group_name, items in sorted(result['groups'].items()):
                    print(f"  {group_name}: {len(items)} items")
                    # Show first item as example
                    if items:
                        first = items[0]
                        print(f"    └─ Example: {first.get('name')}")
            
            if result['errors']:
                print("\n⚠️  Errors:")
                for error in result['errors']:
                    print(f"  - {error}")
        
        return 0 if result['success'] else 1
    
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
