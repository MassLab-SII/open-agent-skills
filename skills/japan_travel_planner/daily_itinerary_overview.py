#!/usr/bin/env python3
"""Daily Itinerary Overview - MCP-based Implementation"""

import asyncio
import json
import os
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from skills.japan_travel_planner.utils import NotionMCPTools

env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break


class DailyItineraryOverview:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found")
        self.api_key = api_key
    
    async def process(self):
        result = {
            "success": False,
            "page_created": False,
            "blocks_added": 0,
            "visited_count": 0,
            "total_activities": 0,
            "errors": [],
        }
        
        async with NotionMCPTools(self.api_key) as mcp:
            try:
                # Step 1: Find Japan Travel Planner page
                print("\n📍 Step 1: Searching for Japan Travel Planner page")
                print("-" * 70)
                
                search_result = await mcp.search("Japan Travel Planner")
                if not search_result:
                    result["errors"].append("Japan Travel Planner not found")
                    return result
                
                search_data = json.loads(search_result)
                japan_page = None
                for item in search_data.get("results", []):
                    if item.get("object") == "page":
                        japan_page = item
                        break
                
                if not japan_page:
                    result["errors"].append("Japan Travel Planner page not found")
                    return result
                
                japan_id = japan_page.get("id")
                print(f"✓ Found Japan Travel Planner (ID: {japan_id[:20]}...)")
                
                # Step 2: Find Travel Itinerary database
                print("\n📍 Step 2: Searching for Travel Itinerary database")
                print("-" * 70)
                
                db_result = await mcp.search("Travel Itinerary")
                if not db_result:
                    result["errors"].append("Travel Itinerary not found")
                    return result
                
                db_data = json.loads(db_result)
                travel_db = None
                for item in db_data.get("results", []):
                    if item.get("object") == "database":
                        travel_db = item
                        break
                
                if not travel_db:
                    result["errors"].append("Travel Itinerary database not found")
                    return result
                
                travel_id = travel_db.get("id")
                print(f"✓ Found Travel Itinerary (ID: {travel_id[:20]}...)")
                
                # Step 3: Query Travel Itinerary database
                print("\n📍 Step 3: Querying Travel Itinerary database")
                print("-" * 70)
                
                query_result = await mcp.query_database(travel_id)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                query_data = json.loads(query_result)
                all_activities = query_data.get("results", [])
                print(f"✓ Retrieved {len(all_activities)} activities")
                
                # Step 4: Parse activities by day
                print("\n📍 Step 4: Parsing activities by day")
                print("-" * 70)
                
                activities_by_day = defaultdict(list)
                visited_count = 0
                
                for activity in all_activities:
                    props = activity.get("properties", {})
                    
                    name_prop = props.get("Name", {})
                    activity_name = ""
                    if name_prop.get("type") == "title":
                        title_array = name_prop.get("title", [])
                        if title_array:
                            activity_name = title_array[0].get("plain_text", "")
                    
                    day_prop = props.get("Day", {})
                    day_name = ""
                    if day_prop.get("type") == "select":
                        selected = day_prop.get("select")
                        if selected:
                            day_name = selected.get("name", "")
                    
                    group_prop = props.get("Group", {})
                    city = ""
                    if group_prop.get("type") == "select":
                        selected = group_prop.get("select")
                        if selected:
                            city = selected.get("name", "")
                    
                    visited_prop = props.get("Visited", {})
                    is_visited = visited_prop.get("checkbox", False) if visited_prop.get("type") == "checkbox" else False
                    
                    # Only count visited items from Day 1-3 for the trip summary
                    if is_visited and day_name in ["Day 1", "Day 2", "Day 3"]:
                        visited_count += 1
                    
                    activity_display = activity_name
                    if city:
                        activity_display = f"{activity_name} - {city}"
                    
                    if day_name:
                        activities_by_day[day_name].append({
                            "name": activity_display,
                            "visited": is_visited
                        })
                
                result["visited_count"] = visited_count
                result["total_activities"] = len(all_activities)
                print(f"✓ Parsed {visited_count}/{len(all_activities)} visited")
                
                # Step 5: Create Daily Itinerary Overview page
                print("\n📍 Step 5: Creating Daily Itinerary Overview page")
                print("-" * 70)
                
                create_result = await mcp.create_child_page(
                    parent_page_id=japan_id,
                    title="Daily Itinerary Overview"
                )
                
                if not create_result:
                    result["errors"].append("Failed to create page")
                    return result
                
                page_data = json.loads(create_result)
                new_page_id = page_data.get("id")
                print(f"✓ Created page (ID: {new_page_id[:20]}...)")
                result["page_created"] = True
                
                # Step 6: Build blocks
                print("\n📍 Step 6: Building page blocks")
                print("-" * 70)
                
                blocks = []
                
                blocks.append({
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": "📅 Daily Itinerary Overview"}}]
                    }
                })
                
                blocks.append({
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "📊 Trip Summary"}}]
                    }
                })
                
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": f"Total activities visited (from Day 1 to Day 3): {visited_count}"}}]
                    }
                })
                
                day_emojis = {"Day 1": "🌅", "Day 2": "🌆", "Day 3": "🌃"}
                
                for day_key in ["Day 1", "Day 2", "Day 3"]:
                    emoji = day_emojis.get(day_key, "📅")
                    blocks.append({
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"type": "text", "text": {"content": f"{emoji} {day_key}"}}]
                        }
                    })
                    
                    if day_key in activities_by_day:
                        for activity in activities_by_day[day_key]:
                            blocks.append({
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [{"type": "text", "text": {"content": activity["name"]}}],
                                    "checked": activity["visited"]
                                }
                            })
                
                print(f"✓ Built {len(blocks)} blocks")
                
                # Step 7: Add blocks to page using API-patch-block-children
                print("\n📍 Step 7: Adding blocks to page")
                print("-" * 70)
                
                # Use the correct API method to add blocks
                try:
                    blocks_result = await mcp.session.call_tool("API-patch-block-children", {
                        "block_id": new_page_id,
                        "children": blocks
                    })
                    
                    if blocks_result:
                        result["blocks_added"] = len(blocks)
                        print(f"✓ Added {len(blocks)} blocks via API-patch-block-children")
                    else:
                        result["errors"].append("Failed to add blocks - no result")
                        return result
                except Exception as e:
                    print(f"API-patch-block-children failed: {e}")
                    result["errors"].append(f"Failed to add blocks: {e}")
                    return result
                
                result["success"] = True
                return result
                
            except Exception as e:
                result["errors"].append(f"Exception: {str(e)}")
                import traceback
                traceback.print_exc()
                return result


async def main():
    print("=" * 70)
    print("Daily Itinerary Overview Skill")
    print("=" * 70)
    
    skill = DailyItineraryOverview()
    result = await skill.process()
    
    print("\n" + "=" * 70)
    print("RESULT SUMMARY")
    print("=" * 70)
    
    if result["success"]:
        print(f"✅ Success")
        print(f"   Page Created: {result['page_created']}")
        print(f"   Blocks Added: {result['blocks_added']}")
        print(f"   Activities Visited: {result['visited_count']}/{result['total_activities']}")
    else:
        print(f"❌ Failed")
        for error in result["errors"]:
            print(f"   - {error}")
    
    return result["success"]


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
