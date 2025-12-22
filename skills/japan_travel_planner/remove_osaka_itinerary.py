#!/usr/bin/env python3
"""
Remove Osaka Itinerary Items - MCP-based Implementation
=========================================================

This skill removes itinerary items from a travel database based on:
- Location/Group filter (e.g., Osaka, Tokyo, Kyoto)
- Day filter (e.g., Day 1, Day 2, specific dates)
- Time threshold filter (after a specified time)

Uses 100% MCP tools for all Notion operations.
The API key is automatically loaded from environment variables.

Usage:
    python3 remove_osaka_itinerary.py
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv
from skills.japan_travel_planner.utils import NotionMCPTools, parse_time_to_minutes, extract_page_property

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


class RemoveOsakaItinerary:
    """
    Remove Osaka itinerary items after 6 PM from Day 1 and Day 2.
    Uses 100% MCP tools for all operations.
    """
    
    def __init__(
        self,
        api_key: str = None,
        location: str = "Osaka",
        days: List[str] = None,
        cutoff_time_minutes: int = 18 * 60,  # 6 PM = 1080 minutes
    ):
        """
        Initialize RemoveOsakaItinerary.
        
        Args:
            api_key: Notion API key (defaults to EVAL_NOTION_API_KEY)
            location: Location/Group to filter (e.g., "Osaka")
            days: List of days to process (e.g., ["Day 1", "Day 2"])
            cutoff_time_minutes: Time threshold in minutes (e.g., 1080 for 6 PM)
        """
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment")
        
        self.api_key = api_key
        self.location = location
        self.days = days or ["Day 1", "Day 2"]
        self.cutoff_time_minutes = cutoff_time_minutes

    async def remove_itinerary(self) -> Dict[str, any]:
        """
        Remove itinerary items from the specified location after the cutoff time.
        
        Returns:
            Dictionary with results including:
            - success: Boolean indicating overall success
            - removed_count: Number of items removed
            - removed_items: List of removed item details
            - errors: List of any errors encountered
        """
        result = {
            "success": False,
            "removed_count": 0,
            "removed_items": [],
            "errors": [],
        }

        async with NotionMCPTools(self.api_key) as mcp:
            try:
                # Step 1: Search for Japan Travel Planner page
                print("\n📍 Step 1: Searching for 'Japan Travel Planner' page")
                print("-" * 70)
                
                search_result = await mcp.search("Japan Travel Planner")
                if not search_result:
                    result["errors"].append("Failed to search for page")
                    return result
                
                try:
                    search_data = json.loads(search_result)
                    if not search_data.get("results"):
                        result["errors"].append("Page 'Japan Travel Planner' not found")
                        return result
                    
                    planner_page_id = search_data["results"][0].get("id")
                    print(f"✓ Found page (ID: {planner_page_id})")
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    result["errors"].append(f"Failed to parse search results: {e}")
                    return result
                
                # Step 2: Get page children to find Travel Itinerary database
                print("\n📍 Step 2: Finding 'Travel Itinerary' database")
                print("-" * 70)
                
                page_children_result = await mcp.get_block_children(planner_page_id)
                if not page_children_result:
                    result["errors"].append("Failed to fetch page children")
                    return result
                
                try:
                    page_children_data = json.loads(page_children_result)
                    page_blocks = page_children_data.get("results", [])
                    
                    # Find the Travel Itinerary database
                    itinerary_db_id = None
                    for block in page_blocks:
                        if block.get("type") == "child_database":
                            db_info = block.get("child_database", {})
                            if "Travel Itinerary" in db_info.get("title", ""):
                                itinerary_db_id = block.get("id")
                                print(f"✓ Found Travel Itinerary database (ID: {itinerary_db_id})")
                                break
                    
                    if not itinerary_db_id:
                        result["errors"].append("Travel Itinerary database not found")
                        return result
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse page children: {e}")
                    return result
                
                # Step 3: Query the database for Osaka items on Day 1 and Day 2
                print("\n📍 Step 3: Querying database for Osaka items")
                print("-" * 70)
                
                filter_obj = {
                    "and": [
                        {"property": "Group", "select": {"equals": self.location}},
                        {
                            "or": [
                                {"property": "Day", "select": {"equals": day}}
                                for day in self.days
                            ]
                        }
                    ]
                }
                
                query_result = await mcp.query_database(itinerary_db_id, filter_obj)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                try:
                    query_data = json.loads(query_result)
                    items = query_data.get("results", [])
                    print(f"✓ Found {len(items)} items in Osaka for Day 1 and Day 2")
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse query results: {e}")
                    return result
                
                # Step 4: Filter items by time and collect those to remove
                print("\n📍 Step 4: Filtering items by time (after 6 PM)")
                print("-" * 70)
                
                items_to_remove = []
                for item in items:
                    item_id = item.get("id")
                    item_name = extract_page_property(item, "Name")
                    item_time_str = extract_page_property(item, "Notes")
                    item_day = extract_page_property(item, "Day")
                    
                    # Parse time and compare with cutoff
                    if item_time_str:
                        item_time_minutes = parse_time_to_minutes(item_time_str)
                        
                        if item_time_minutes is not None and item_time_minutes > self.cutoff_time_minutes:
                            items_to_remove.append({
                                "id": item_id,
                                "name": item_name,
                                "time": item_time_str,
                                "day": item_day
                            })
                            print(f"  ✓ {item_name} ({item_time_str} on {item_day})")
                
                print(f"\n✓ Identified {len(items_to_remove)} items to remove")
                
                # Step 5: Archive/delete the items
                print("\n📍 Step 5: Removing items")
                print("-" * 70)
                
                for item in items_to_remove:
                    try:
                        await mcp.patch_page(item["id"], archived=True)
                        print(f"  ✓ Removed: {item['name']} ({item['time']})")
                        result["removed_items"].append(item)
                    except Exception as e:
                        error_msg = f"Failed to remove {item['name']}: {e}"
                        result["errors"].append(error_msg)
                        print(f"  ❌ {error_msg}")
                
                result["removed_count"] = len(result["removed_items"])
                result["success"] = result["removed_count"] > 0 or len(result["errors"]) == 0
                
                return result
                
            except Exception as e:
                result["errors"].append(f"Unexpected error: {e}")
                return result


async def main():
    """Main entry point for the skill."""
    print("\n" + "=" * 70)
    print("🚀 Remove Osaka Itinerary Skill - 100% MCP Implementation")
    print("=" * 70)
    
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("❌ Error: EVAL_NOTION_API_KEY environment variable not set")
        sys.exit(1)
    
    filter_tool = RemoveOsakaItinerary(api_key)
    result = await filter_tool.remove_itinerary()
    
    print("\n" + "=" * 70)
    print("📊 Execution Summary")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Items removed: {result['removed_count']}")
    
    if result['removed_items']:
        print("\nRemoved items:")
        for item in result['removed_items']:
            print(f"  - {item['name']} ({item['time']} on {item['day']})")
    
    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
