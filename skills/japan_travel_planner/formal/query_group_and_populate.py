#!/usr/bin/env python3
"""
Query, Group and Populate Page - Reusable Skill
================================================

This skill:
1. Searches for a database by name
2. Queries all items from the database
3. Organizes items by a specified property (grouping)
4. Formats grouped data into Notion blocks
5. Adds blocks to the specified page

Uses Notion MCP for all operations.

Example:
  python3 query_group_and_populate.py \\
    "page-id" \\
    "Travel Itinerary" \\
    "Day" \\
    "Daily Itinerary Overview"
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


class QueryGroupAndPopulate:
    """
    Query database items, group them, and populate a Notion page.
    
    MCP Calls:
    - API-post-search: Find database by name
    - API-post-database-query: Query all items
    - API-patch-block-children: Add blocks to page
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EVAL_NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in EVAL_NOTION_API_KEY environment variable")
    
    def _extract_property_value(self, properties: Dict, property_name: str, 
                               property_type: str, default: Any = None) -> Any:
        """Extract a property value from Notion properties object."""
        prop = properties.get(property_name, {})
        
        if not prop:
            return default
        
        prop_type = prop.get("type")
        
        if property_type == "title" and prop_type == "title":
            title_array = prop.get("title", [])
            if title_array:
                return title_array[0].get("plain_text", default)
        
        elif property_type == "text" and prop_type == "rich_text":
            rich_text = prop.get("rich_text", [])
            if rich_text:
                return rich_text[0].get("text", {}).get("content", default)
        
        elif property_type == "select" and prop_type == "select":
            selected = prop.get("select")
            if selected:
                return selected.get("name", default)
        
        elif property_type == "checkbox" and prop_type == "checkbox":
            return prop.get("checkbox", default)
        
        elif property_type == "multi_select" and prop_type == "multi_select":
            multi = prop.get("multi_select", [])
            if multi:
                return [item.get("name") for item in multi]
        
        return default
    
    def _build_blocks(self, page_title: str, items_by_group: Dict[str, List[Dict]],
                     groups_order: Optional[List[str]] = None,
                     group_prefixes: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Format grouped items into Notion blocks."""
        blocks = []
        
        # Group prefixes/labels (provided by LLM or caller)
        if group_prefixes is None:
            group_prefixes = {}
        
        # Add title heading
        blocks.append({
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": page_title}}]
            }
        })
        
        # Count total and completed items
        total_items = sum(len(items) for items in items_by_group.values())
        
        # Count completed items (only in specified groups if groups_order provided)
        if groups_order:
            completed_count = sum(
                len([item for item in items_by_group.get(group, []) 
                     if item.get("completed", False)])
                for group in groups_order
            )
        else:
            completed_count = sum(
                len([item for item in items if item.get("completed", False)])
                for items in items_by_group.values()
            )
        
        # Summary heading
        blocks.append({
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📊 Trip Summary"}}]
            }
        })
        
        # Summary paragraph
        groups = groups_order or list(items_by_group.keys())
        if groups:
            group_range = f"from {groups[0]} to {groups[-1]}"
        else:
            group_range = ""
        
        summary_text = f"Total activities visited ({group_range}): {completed_count}"
        blocks.append({
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": summary_text}
                    }
                ]
            }
        })
        
        # Add group sections with items
        groups = groups_order or sorted(list(items_by_group.keys()))
        
        for group_name in groups:
            if group_name not in items_by_group:
                continue
            
            items = items_by_group[group_name]
            
            # Get prefix for group from LLM parameters
            prefix = group_prefixes.get(group_name, "")
            
            # Group heading with prefix
            group_heading = f"{prefix} {group_name}".strip()
            blocks.append({
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": group_heading}}]
                }
            })
            
            # Items as to-do blocks
            for item in items:
                blocks.append({
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": item["name"]}
                            }
                        ],
                        "checked": item.get("completed", False)
                    }
                })
        
        return blocks
    
    async def process(self, page_id: str, database_name: str, grouping_property: str,
                     page_title: str,
                     item_property: str = "Name",
                     location_property: Optional[str] = None,
                     status_property: Optional[str] = None,
                     groups_order: Optional[List[str]] = None,
                     group_prefixes: Optional[Dict[str, str]] = None) -> Dict:
        """
        Query database, group items, and populate page.
        
        Args:
            page_id: ID of the page to populate
            database_name: Name of the database to query
            grouping_property: Property to group items by (e.g., "Day", "Category")
            page_title: Title for the page
            item_property: Property name for item names (default: "Name")
            location_property: Optional property for additional info (default: None)
            status_property: Optional checkbox property for completion status (default: None)
            groups_order: Order to display groups (default: alphabetical)
            group_prefixes: Dict mapping group names to prefix text (e.g., {"Day 1": "Morning", "Day 2": "Afternoon"})
            
        Returns:
            Dictionary with:
            - success: bool
            - database_id: str
            - total_items: int
            - completed_items: int
            - blocks_added: int
            - groups_processed: Dict[str, int]
            - errors: List[str]
        """
        result = {
            "success": False,
            "database_id": None,
            "total_items": 0,
            "completed_items": 0,
            "blocks_added": 0,
            "groups_processed": {},
            "errors": []
        }
        
        try:
            async with NotionMCPTools(self.api_key, notion_version="2025-09-03") as mcp:
                # Step 1: Find database
                print(f"\n📍 Step 1: Searching for database: {database_name}")
                print("-" * 70)
                
                search_result = await mcp.search(database_name)
                if not search_result:
                    result["errors"].append(f"Database '{database_name}' not found")
                    return result
                
                search_data = json.loads(search_result)
                item_db = None
                
                # Handle both "data_source" and "database" types
                for item in search_data.get("results", []):
                    obj_type = item.get("object")
                    if obj_type == "data_source" or obj_type == "database":
                        title_prop = item.get("title", [])
                        if title_prop:
                            if isinstance(title_prop, list) and len(title_prop) > 0:
                                item_title = title_prop[0].get("plain_text", "")
                            else:
                                item_title = str(title_prop)
                            
                            if database_name.lower() in item_title.lower():
                                item_db = item
                                break
                
                # If no exact title match, just take the first data_source/database
                if not item_db:
                    for item in search_data.get("results", []):
                        obj_type = item.get("object")
                        if obj_type == "data_source" or obj_type == "database":
                            item_db = item
                            break
                
                if not item_db:
                    result["errors"].append(f"Database '{database_name}' not found")
                    return result
                
                db_id = item_db.get("id")
                result["database_id"] = db_id
                print(f"✓ Found database")
                print(f"  ID: {db_id[:30]}...")
                print(f"  Name: {database_name}")
                
                # Step 2: Query database
                print(f"\n📍 Step 2: Querying database for items")
                print("-" * 70)
                
                query_result = await mcp.query_database(db_id)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                query_data = json.loads(query_result)
                all_items = query_data.get("results", [])
                print(f"✓ Retrieved {len(all_items)} items")
                result["total_items"] = len(all_items)
                
                # Step 3: Organize by grouping property
                print(f"\n📍 Step 3: Organizing items by '{grouping_property}'")
                print("-" * 70)
                
                items_by_group = defaultdict(list)
                all_groups = set()
                completed_count = 0
                
                for item in all_items:
                    props = item.get("properties", {})
                    
                    # Extract item information
                    item_name = self._extract_property_value(
                        props, item_property, "title", "Untitled"
                    )
                    
                    group_name = self._extract_property_value(
                        props, grouping_property, "select"
                    )
                    
                    location = None
                    if location_property:
                        location = self._extract_property_value(
                            props, location_property, "select"
                        )
                    
                    is_completed = False
                    if status_property:
                        is_completed = self._extract_property_value(
                            props, status_property, "checkbox", False
                        )
                        if is_completed:
                            completed_count += 1
                    
                    # Format item display name
                    item_display = item_name
                    if location:
                        item_display = f"{item_name} - {location}"
                    
                    # Group by grouping property
                    if group_name:
                        items_by_group[group_name].append({
                            "name": item_display,
                            "completed": is_completed
                        })
                        all_groups.add(group_name)
                
                result["completed_items"] = completed_count
                
                print(f"✓ Organized into {len(all_groups)} groups")
                print(f"  Completed items: {completed_count}/{len(all_items)}")
                for group in sorted(list(all_groups)):
                    count = len(items_by_group[group])
                    print(f"  - {group}: {count} items")
                
                # Step 4: Build blocks
                print(f"\n📍 Step 4: Building page blocks")
                print("-" * 70)
                
                blocks = self._build_blocks(
                    page_title=page_title,
                    items_by_group=items_by_group,
                    groups_order=groups_order,
                    group_prefixes=group_prefixes
                )
                
                print(f"✓ Built {len(blocks)} blocks")
                for group_name in sorted(list(all_groups)):
                    result["groups_processed"][group_name] = len(items_by_group[group_name])
                
                # Step 5: Add blocks to page
                print(f"\n📍 Step 5: Adding blocks to page")
                print("-" * 70)
                
                try:
                    blocks_result = await mcp.session.call_tool("API-patch-block-children", {
                        "block_id": page_id,
                        "children": blocks
                    })
                    
                    if blocks_result:
                        result["blocks_added"] = len(blocks)
                        print(f"✓ Added {len(blocks)} blocks to page")
                        result["success"] = True
                    else:
                        result["errors"].append("Failed to add blocks - empty response")
                        
                except Exception as e:
                    result["errors"].append(f"Failed to add blocks: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                return result
                
        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return result


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Query database, group items, and populate page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Populate daily itinerary overview
  python3 query_group_and_populate.py \\
    "page-id" \\
    "Travel Itinerary" \\
    "Day" \\
    "Daily Itinerary Overview" \\
    --item-property "Name" \\
    --location-property "Group" \\
    --status-property "Visited" \\
    --groups-order "Day 1" "Day 2" "Day 3" \\
    --group-prefixes "Day 1" "Morning -" "Day 2" "Afternoon -"
        """
    )
    
    parser.add_argument("page_id", help="ID of the page to populate")
    parser.add_argument("database_name", help="Name of database to query")
    parser.add_argument("grouping_property", help="Property to group items by")
    parser.add_argument("page_title", help="Title for the page")
    parser.add_argument("--item-property", default="Name", help="Property for item name (default: Name)")
    parser.add_argument("--location-property", help="Property for additional info (optional)")
    parser.add_argument("--status-property", help="Checkbox property for completion status (optional)")
    parser.add_argument("--groups-order", nargs="*", help="Order to display groups (optional)")
    parser.add_argument("--group-prefixes", nargs="*", help="Prefix text for groups, format: group_name prefix group_name prefix ... (optional)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Query, Group and Populate Page Skill")
    print("=" * 70)
    
    skill = QueryGroupAndPopulate()
    
    # Parse group prefixes from command line
    group_prefixes = None
    if args.group_prefixes:
        group_prefixes = {}
        for i in range(0, len(args.group_prefixes), 2):
            if i + 1 < len(args.group_prefixes):
                group_name = args.group_prefixes[i]
                prefix = args.group_prefixes[i + 1]
                group_prefixes[group_name] = prefix
    
    result = await skill.process(
        page_id=args.page_id,
        database_name=args.database_name,
        grouping_property=args.grouping_property,
        page_title=args.page_title,
        item_property=args.item_property,
        location_property=args.location_property,
        status_property=args.status_property,
        groups_order=args.groups_order if args.groups_order else None,
        group_prefixes=group_prefixes
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print("RESULT SUMMARY")
        print("=" * 70)
        
        if result["success"]:
            print(f"✅ Success")
            print(f"   Database ID: {result['database_id']}")
            print(f"   Total Items: {result['total_items']}")
            print(f"   Completed: {result['completed_items']}")
            print(f"   Blocks Added: {result['blocks_added']}")
            if result["groups_processed"]:
                print(f"   Groups Processed:")
                for group, count in result["groups_processed"].items():
                    print(f"     - {group}: {count} items")
        else:
            print(f"❌ Failed")
            for error in result["errors"]:
                print(f"   - {error}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
