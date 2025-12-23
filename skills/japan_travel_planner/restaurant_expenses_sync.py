#!/usr/bin/env python3
"""
Restaurant Expenses Sync - MCP-based Implementation
====================================================

This skill finds restaurants from Day 1 of the Travel Itinerary database
and creates corresponding entries in the Expenses database.

Each restaurant entry is created with:
- Date: Jan 1, 2025
- Cost: $120
- Category: Dining
- Comment: Description from the restaurant page
- Expense field: Restaurant name

Uses 100% MCP tools for all Notion operations.
The API key is automatically loaded from environment variables.

Usage:
    python3 restaurant_expenses_sync.py
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv
from skills.japan_travel_planner.utils import NotionMCPTools, extract_page_property

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


class RestaurantExpensesSync:
    """
    Sync restaurants from Day 1 Travel Itinerary to Expenses database.
    Uses 100% MCP tools for all operations.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize RestaurantExpensesSync.
        
        Args:
            api_key: Notion API key (defaults to EVAL_NOTION_API_KEY)
        """
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment")
        
        self.api_key = api_key

    async def sync_expenses(self) -> Dict[str, any]:
        """
        Find restaurants from Day 1 and create expense entries.
        
        Returns:
            Dictionary with results including:
            - success: Boolean indicating overall success
            - restaurants_found: List of restaurant names
            - entries_created: Number of expense entries created
            - errors: List of any errors encountered
        """
        result = {
            "success": False,
            "restaurants_found": [],
            "entries_created": 0,
            "errors": [],
        }

        async with NotionMCPTools(self.api_key) as mcp:
            try:
                # Step 1: Search for Travel Itinerary database
                print("\n📍 Step 1: Searching for 'Travel Itinerary' database")
                print("-" * 70)
                
                search_result = await mcp.search("Travel Itinerary")
                if not search_result:
                    result["errors"].append("Failed to search for Travel Itinerary")
                    return result
                
                try:
                    search_data = json.loads(search_result)
                    if not search_data.get("results"):
                        result["errors"].append("Travel Itinerary database not found")
                        return result
                    
                    # Find the actual database (not a page)
                    itinerary_db_id = None
                    for item in search_data["results"]:
                        if item.get("object") == "database":
                            itinerary_db_id = item.get("id")
                            break
                    
                    if not itinerary_db_id:
                        result["errors"].append("Travel Itinerary database not found (not a database object)")
                        return result
                    
                    print(f"✓ Found Travel Itinerary database (ID: {itinerary_db_id})")
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    result["errors"].append(f"Failed to parse search results: {e}")
                    return result
                
                # Step 2: Search for Expenses database
                print("\n📍 Step 2: Searching for 'Expenses' database")
                print("-" * 70)
                
                search_result = await mcp.search("Expenses")
                if not search_result:
                    result["errors"].append("Failed to search for Expenses")
                    return result
                
                try:
                    search_data = json.loads(search_result)
                    if not search_data.get("results"):
                        result["errors"].append("Expenses database not found")
                        return result
                    
                    # Find the active Expenses database (not in trash, and is a database)
                    expenses_db_id = None
                    for item in search_data["results"]:
                        if item.get("object") == "database" and not item.get("in_trash"):
                            expenses_db_id = item.get("id")
                            break
                    
                    if not expenses_db_id:
                        result["errors"].append("No active Expenses database found")
                        return result
                    
                    print(f"✓ Found Expenses database (ID: {expenses_db_id})")
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse Expenses search: {e}")
                    return result
                
                # Step 3: Query Travel Itinerary for Day 1 entries
                print("\n📍 Step 3: Querying Travel Itinerary for Day 1 restaurants")
                print("-" * 70)
                
                filter_obj = {
                    "and": [
                        {
                            "property": "Day",
                            "select": {
                                "equals": "Day 1"
                            }
                        },
                        {
                            "property": "Type",
                            "multi_select": {
                                "contains": "Food"
                            }
                        }
                    ]
                }
                
                query_result = await mcp.query_database(itinerary_db_id, filter_obj)
                if not query_result:
                    result["errors"].append("Failed to query Travel Itinerary")
                    return result
                
                try:
                    query_data = json.loads(query_result)
                    restaurants = query_data.get("results", [])
                    print(f"✓ Found {len(restaurants)} restaurants on Day 1")
                    
                    if not restaurants:
                        result["success"] = True
                        print("✓ No restaurants found on Day 1")
                        return result
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse query results: {e}")
                    return result
                
                # Step 4: Process each restaurant
                print("\n📍 Step 4: Creating expense entries")
                print("-" * 70)
                
                for restaurant in restaurants:
                    try:
                        restaurant_id = restaurant.get("id")
                        restaurant_name = None
                        description = None
                        
                        # Extract restaurant name from properties
                        if "properties" in restaurant:
                            props = restaurant["properties"]
                            
                            # Get restaurant name from "Name" title property
                            if "Name" in props:
                                name_prop = props["Name"].get("title", [])
                                if name_prop:
                                    restaurant_name = name_prop[0].get("plain_text", "")
                            
                            # Get description from "Description" property
                            if "Description" in props:
                                desc_prop = props["Description"].get("rich_text", [])
                                if desc_prop:
                                    description = desc_prop[0].get("plain_text", "")
                        
                        if not restaurant_name:
                            print(f"⚠ Skipped restaurant without name")
                            continue
                        
                        print(f"  Processing: {restaurant_name}")
                        
                        # Step 5: Retrieve full page to get all details
                        page_result = await mcp.get_page(restaurant_id)
                        if page_result:
                            try:
                                page_data = json.loads(page_result)
                                if "properties" in page_data:
                                    props = page_data["properties"]
                                    
                                    # Update name from full page if needed
                                    if not restaurant_name and "Name" in props:
                                        name_prop = props["Name"].get("title", [])
                                        if name_prop:
                                            restaurant_name = name_prop[0].get("plain_text", "")
                                    
                                    # Update description from full page if needed
                                    if not description and "Description" in props:
                                        desc_prop = props["Description"].get("rich_text", [])
                                        if desc_prop:
                                            description = desc_prop[0].get("plain_text", "")
                            except json.JSONDecodeError:
                                pass
                        
                        # Step 6: Create expense entry
                        properties = {
                            "Expense": {
                                "title": [
                                    {
                                        "text": {
                                            "content": restaurant_name
                                        }
                                    }
                                ]
                            },
                            "Date": {
                                "date": {
                                    "start": "2025-01-01"
                                }
                            },
                            "Transaction Amount": {
                                "number": 120
                            },
                            "Category": {
                                "multi_select": [
                                    {
                                        "name": "Dining"
                                    }
                                ]
                            }
                        }
                        
                        # Add comment if description exists
                        if description:
                            properties["Comment"] = {
                                "rich_text": [
                                    {
                                        "text": {
                                            "content": description
                                        }
                                    }
                                ]
                            }
                        
                        # Create the page
                        create_result = await mcp.create_page(expenses_db_id, properties)
                        if create_result:
                            result["entries_created"] += 1
                            result["restaurants_found"].append(restaurant_name)
                            print(f"  ✓ Created expense entry for {restaurant_name}")
                        else:
                            result["errors"].append(f"Failed to create expense for {restaurant_name}")
                            print(f"  ❌ Failed to create expense for {restaurant_name}")
                    
                    except Exception as e:
                        result["errors"].append(f"Error processing restaurant: {str(e)}")
                        print(f"  ❌ Error: {str(e)}")
                
                result["success"] = True
                return result
            
            except Exception as e:
                result["errors"].append(f"Unexpected error: {str(e)}")
                print(f"❌ Unexpected error: {str(e)}")
                return result


async def main():
    """Main execution function"""
    try:
        sync = RestaurantExpensesSync()
        result = await sync.sync_expenses()
        
        print("\n" + "=" * 70)
        print("📊 Execution Summary")
        print("=" * 70)
        print(f"Success: {result['success']}")
        print(f"Restaurants Found: {len(result['restaurants_found'])}")
        print(f"Entries Created: {result['entries_created']}")
        
        if result['restaurants_found']:
            print(f"\nRestaurants processed:")
            for restaurant in result['restaurants_found']:
                print(f"  • {restaurant}")
        
        if result['errors']:
            print(f"\nErrors encountered:")
            for error in result['errors']:
                print(f"  • {error}")
        
        if result['success']:
            print("\n✅ SUCCESS: Restaurant expenses synchronized")
        else:
            print("\n❌ FAILED: Restaurant expenses sync failed")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
