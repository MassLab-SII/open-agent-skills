#!/usr/bin/env python3
"""
Create Daily Itinerary Overview - Generic Skill
================================================

This skill creates a daily itinerary overview page under a parent page.
It queries a database to retrieve activities, groups them by day, 
and creates a formatted page with proper structure.

Generic parameters allow LLM to customize:
- parent_page_name: Name of parent page (e.g., "Japan Travel Planner")
- new_page_title: Title for the new overview page (e.g., "Daily Itinerary Overview")
- database_name: Name of the database with activities (e.g., "Travel Itinerary")
- day_property: Property name for days (e.g., "Day")
- activity_property: Property name for activity names (e.g., "Name")
- city_property: Property name for city/location (e.g., "Group")
- visited_property: Property name for visited status (e.g., "Visited")
- days_list: List of day names to include (e.g., ["Day 1", "Day 2", "Day 3"])

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


class CreateItineraryOverview:
    """
    Generic skill to create a daily itinerary overview page.
    Queries activities database and organizes by days.
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
    
    async def process(self, parent_page_name: str, new_page_title: str, 
                     database_name: str, day_property: str = "Day",
                     activity_property: str = "Name", 
                     city_property: str = "Group",
                     visited_property: str = "Visited",
                     days_list: Optional[List[str]] = None,
                     day_emojis: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Create and populate a daily itinerary overview page.
        
        Args:
            parent_page_name: Name of the parent page to create child under
            new_page_title: Title for the new overview page
            database_name: Name of the database with activities
            day_property: Property name for days (default: "Day")
            activity_property: Property name for activity names (default: "Name")
            city_property: Property name for city/location (default: "Group")
            visited_property: Property name for visited checkbox (default: "Visited")
            days_list: List of day names to include (default: ["Day 1", "Day 2", "Day 3"])
            day_emojis: Dict mapping day names to emojis (optional)
            
        Returns:
            Result dictionary with status and details
        """
        result = {
            "success": False,
            "page_created": False,
            "blocks_added": 0,
            "visited_count": 0,
            "total_activities": 0,
            "page_id": None,
            "errors": []
        }
        
        # Use defaults if not provided
        if days_list is None:
            days_list = ["Day 1", "Day 2", "Day 3"]
        
        if day_emojis is None:
            day_emojis = {
                "Day 1": "🌅",
                "Day 2": "🌆",
                "Day 3": "🌃"
            }
        
        try:
            async with NotionMCPTools(self.api_key, notion_version="2025-09-03") as mcp:
                # Step 1: Find parent page
                print(f"\n📍 Step 1: Searching for parent page: {parent_page_name}")
                print("-" * 70)
                
                search_result = await mcp.search(parent_page_name)
                if not search_result:
                    result["errors"].append(f"Parent page '{parent_page_name}' not found")
                    return result
                
                search_data = json.loads(search_result)
                parent_page = None
                for item in search_data.get("results", []):
                    if item.get("object") == "page":
                        parent_page = item
                        break
                
                if not parent_page:
                    result["errors"].append(f"Parent page '{parent_page_name}' not found")
                    return result
                
                parent_id = parent_page.get("id")
                print(f"✓ Found parent page (ID: {parent_id[:20]}...)")
                
                # Step 2: Find activities database
                print(f"\n📍 Step 2: Searching for database: {database_name}")
                print("-" * 70)
                
                db_result = await mcp.search(database_name)
                if not db_result:
                    result["errors"].append(f"Database '{database_name}' not found")
                    return result
                
                db_data = json.loads(db_result)
                activity_db = None
                for item in db_data.get("results", []):
                    if item.get("object") == "database":
                        activity_db = item
                        break
                
                if not activity_db:
                    result["errors"].append(f"Database '{database_name}' not found")
                    return result
                
                activity_id = activity_db.get("id")
                print(f"✓ Found database (ID: {activity_id[:20]}...)")
                
                # Step 3: Query activities database
                print(f"\n📍 Step 3: Querying activities from database")
                print("-" * 70)
                
                query_result = await mcp.query_database(activity_id)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                query_data = json.loads(query_result)
                all_activities = query_data.get("results", [])
                print(f"✓ Retrieved {len(all_activities)} activities")
                result["total_activities"] = len(all_activities)
                
                # Step 4: Parse activities by day
                print(f"\n📍 Step 4: Parsing activities by day")
                print("-" * 70)
                
                activities_by_day = defaultdict(list)
                visited_count = 0
                
                for activity in all_activities:
                    props = activity.get("properties", {})
                    
                    # Extract activity information
                    activity_name = self._extract_property_value(
                        props, activity_property, "title", "Untitled"
                    )
                    
                    day_name = self._extract_property_value(
                        props, day_property, "select"
                    )
                    
                    city = self._extract_property_value(
                        props, city_property, "select"
                    )
                    
                    is_visited = self._extract_property_value(
                        props, visited_property, "checkbox", False
                    )
                    
                    # Count visited activities from included days
                    if is_visited and day_name in days_list:
                        visited_count += 1
                    
                    # Format activity display name
                    activity_display = activity_name
                    if city:
                        activity_display = f"{activity_name} - {city}"
                    
                    # Group by day
                    if day_name:
                        activities_by_day[day_name].append({
                            "name": activity_display,
                            "visited": is_visited
                        })
                
                result["visited_count"] = visited_count
                print(f"✓ Parsed {visited_count} visited activities from {len(activities_by_day)} days")
                
                # Step 5: Create new overview page
                print(f"\n📍 Step 5: Creating new page: {new_page_title}")
                print("-" * 70)
                
                create_result = await mcp.create_child_page(
                    parent_page_id=parent_id,
                    title=new_page_title
                )
                
                if not create_result:
                    result["errors"].append("Failed to create page")
                    return result
                
                page_data = json.loads(create_result)
                new_page_id = page_data.get("id")
                print(f"✓ Created page (ID: {new_page_id[:20]}...)")
                result["page_created"] = True
                result["page_id"] = new_page_id
                
                # Step 6: Build page blocks
                print(f"\n📍 Step 6: Building page blocks")
                print("-" * 70)
                
                blocks = []
                
                # Title heading
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": f"📅 {new_page_title}"}}]
                    }
                })
                
                # Trip summary section
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Trip Summary"}}]
                    }
                })
                
                # Total visited count
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Total activities visited (from {' to '.join([days_list[0], days_list[-1]])}): {visited_count}"
                                }
                            }
                        ]
                    }
                })
                
                # Daily sections
                for day_key in days_list:
                    emoji = day_emojis.get(day_key, "📅")
                    
                    # Day heading
                    blocks.append({
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": f"{emoji} {day_key}"}}]
                        }
                    })
                    
                    # Activities for this day
                    if day_key in activities_by_day:
                        for activity in activities_by_day[day_key]:
                            blocks.append({
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {"content": activity["name"]}
                                        }
                                    ],
                                    "checked": activity["visited"]
                                }
                            })
                
                print(f"✓ Built {len(blocks)} blocks")
                
                # Step 7: Add blocks to page
                print(f"\n📍 Step 7: Adding blocks to page")
                print("-" * 70)
                
                try:
                    blocks_result = await mcp.session.call_tool("API-patch-block-children", {
                        "block_id": new_page_id,
                        "children": blocks
                    })
                    
                    if blocks_result:
                        result["blocks_added"] = len(blocks)
                        print(f"✓ Added {len(blocks)} blocks to page")
                        result["success"] = True
                    else:
                        result["errors"].append("Failed to add blocks - empty response")
                        
                except Exception as e:
                    print(f"Failed to add blocks: {e}")
                    result["errors"].append(f"Failed to add blocks: {str(e)}")
                
                return result
                
        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return result


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create a daily itinerary overview page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 create_itinerary_overview.py "Japan Travel Planner" "Daily Itinerary Overview" "Travel Itinerary"
  
  python3 create_itinerary_overview.py \\
    "Japan Travel Planner" \\
    "Weekly Plan" \\
    "Activities DB" \\
    --day-property "Week" \\
    --days-list "Week 1" "Week 2" "Week 3"
        """
    )
    
    parser.add_argument("parent_page", help="Name of parent page")
    parser.add_argument("new_page_title", help="Title for new overview page")
    parser.add_argument("database_name", help="Name of activities database")
    parser.add_argument("--day-property", default="Day", help="Property for day grouping (default: Day)")
    parser.add_argument("--activity-property", default="Name", help="Property for activity name (default: Name)")
    parser.add_argument("--city-property", default="Group", help="Property for city/location (default: Group)")
    parser.add_argument("--visited-property", default="Visited", help="Property for visited status (default: Visited)")
    parser.add_argument("--days-list", nargs="*", help="List of days to include (default: Day 1, Day 2, Day 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Use provided days or defaults
    days_list = args.days_list if args.days_list else ["Day 1", "Day 2", "Day 3"]
    
    print("=" * 70)
    print("Create Daily Itinerary Overview Skill")
    print("=" * 70)
    
    skill = CreateItineraryOverview()
    result = await skill.process(
        parent_page_name=args.parent_page,
        new_page_title=args.new_page_title,
        database_name=args.database_name,
        day_property=args.day_property,
        activity_property=args.activity_property,
        city_property=args.city_property,
        visited_property=args.visited_property,
        days_list=days_list
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print("RESULT SUMMARY")
        print("=" * 70)
        
        if result["success"]:
            print(f"✅ Success")
            print(f"   Page Created: {result['page_created']}")
            print(f"   Page ID: {result['page_id']}")
            print(f"   Blocks Added: {result['blocks_added']}")
            print(f"   Activities Visited: {result['visited_count']}/{result['total_activities']}")
        else:
            print(f"❌ Failed")
            for error in result["errors"]:
                print(f"   - {error}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
