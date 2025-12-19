#!/usr/bin/env python3
"""
Toronto Weekend Adventure Planner - 100% MCP Implementation
Creates a comprehensive weekend adventure itinerary using pure MCP tools
"""
import asyncio
import json
import os
import re
from utils import NotionMCPTools


def extract_page_id(json_text: str) -> str:
    """Extract page ID from JSON response"""
    if not json_text:
        return None
    try:
        data = json.loads(json_text)
        return data.get("id")
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r'"id":"([^"]+)"', json_text)
    return match.group(1) if match else None


def parse_results(response_text: str) -> list:
    """Parse results from API response"""
    if not response_text:
        return []
    try:
        data = json.loads(response_text)
        return data.get("results", [])
    except (json.JSONDecodeError, TypeError):
        return []


def get_page_title(page: dict) -> str:
    """Extract page title from page object"""
    try:
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0].get("text", {}).get("content", "")
    except:
        pass
    return ""


def get_property_value(page: dict, property_name: str, prop_type: str = "title") -> str:
    """Extract property value from page object"""
    try:
        properties = page.get("properties", {})
        prop_data = properties.get(property_name, {})
        
        if prop_data.get("type") == "title":
            title_array = prop_data.get("title", [])
            if title_array:
                return title_array[0].get("text", {}).get("content", "")
        
        elif prop_data.get("type") == "multi_select":
            multi_select = prop_data.get("multi_select", [])
            return [item.get("name") for item in multi_select]
        
        elif prop_data.get("type") == "url":
            return prop_data.get("url", "")
        
        elif prop_data.get("type") == "rich_text":
            rich_text = prop_data.get("rich_text", [])
            if rich_text:
                return rich_text[0].get("text", {}).get("content", "")
    except:
        pass
    return None


async def find_page_by_title(mcp: NotionMCPTools, title: str) -> str:
    """Find a page by its title"""
    search_result = await mcp.search(title)
    if not search_result:
        return None
    
    try:
        data = json.loads(search_result)
        for item in data.get("results", []):
            if item.get("object") == "page":
                page_title = get_page_title(item)
                if title.lower() in page_title.lower():
                    return item["id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return None


async def find_database_by_name(mcp: NotionMCPTools, db_name: str) -> str:
    """Find a database by name"""
    search_result = await mcp.search(db_name)
    if not search_result:
        return None
    
    try:
        data = json.loads(search_result)
        for item in data.get("results", []):
            if item.get("object") == "database":
                # Check title/name
                if "title" in item:
                    titles = item.get("title", [])
                    if titles and db_name.lower() in titles[0].get("text", {}).get("content", "").lower():
                        return item["id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return None


async def query_database_by_tags(mcp: NotionMCPTools, db_id: str, tags: list) -> list:
    """Query database for items with specific tags"""
    results = []
    
    for tag in tags:
        query_result = await mcp.query_database(db_id, {
            "property": "Tags",
            "multi_select": {"contains": tag}
        })
        
        if query_result:
            pages = parse_results(query_result)
            results.extend(pages)
    
    # Remove duplicates
    seen = set()
    unique_results = []
    for item in results:
        item_id = item.get("id")
        if item_id not in seen:
            seen.add(item_id)
            unique_results.append(item)
    
    return unique_results


async def create_weekend_planner(mcp: NotionMCPTools, main_page_id: str) -> bool:
    """Create the Perfect Weekend Adventure page"""
    
    print("\n" + "="*70)
    print("Creating Perfect Weekend Adventure Planner...")
    print("="*70)
    
    # Step 1: Create the page
    print("\n📍 Step 1: Creating 'Perfect Weekend Adventure' page")
    print("-"*70)
    
    page_result = await mcp.create_page(main_page_id, "Perfect Weekend Adventure")
    if not page_result:
        print("❌ Failed to create page")
        return False
    
    page_id = extract_page_id(page_result)
    if not page_id:
        print("❌ Could not extract page ID")
        return False
    
    print(f"✓ Created page: {page_id}")
    
    # Step 2: Find databases
    print("\n📍 Step 2: Finding Toronto Guide databases")
    print("-"*70)
    
    activities_db_id = await find_database_by_name(mcp, "Activities")
    food_db_id = await find_database_by_name(mcp, "Food")
    cafes_db_id = await find_database_by_name(mcp, "Cafes")
    
    print(f"✓ Activities DB: {activities_db_id}")
    print(f"✓ Food DB: {food_db_id}")
    print(f"✓ Cafes DB: {cafes_db_id}")
    
    # Step 3: Query databases
    print("\n📍 Step 3: Querying databases")
    print("-"*70)
    
    # Query beach activities
    beach_activities = []
    if activities_db_id:
        activities_result = await mcp.query_database(activities_db_id, {
            "property": "Tags",
            "multi_select": {"contains": "Beaches"}
        })
        if activities_result:
            beach_activities = parse_results(activities_result)
    print(f"✓ Found {len(beach_activities)} beach activities")
    
    # Query cultural restaurants (Turkish or Hakka)
    cultural_restaurants = []
    if food_db_id:
        cultural_restaurants = await query_database_by_tags(mcp, food_db_id, ["Turkish", "Hakka"])
    print(f"✓ Found {len(cultural_restaurants)} cultural restaurants")
    
    # Query all cafes
    cafes = []
    if cafes_db_id:
        cafes_result = await mcp.query_database(cafes_db_id)
        if cafes_result:
            cafes = parse_results(cafes_result)
    print(f"✓ Found {len(cafes)} cafes")
    
    # Step 4: Build and add blocks
    print("\n📍 Step 4: Building page content")
    print("-"*70)
    
    blocks = []
    
    # Heading 1
    blocks.append(mcp.create_heading_1("🎒 Perfect Weekend Adventure"))
    
    # Beach Activities section
    blocks.append(mcp.create_heading_2("🏖️ Beach Activities"))
    for activity in beach_activities:
        name = get_property_value(activity, "Name", "title") or ""
        maps_url = get_property_value(activity, "Google Maps Link", "url") or ""
        
        if maps_url:
            # Format with link
            block_text = f"{name} - {maps_url}"
        else:
            block_text = name
        
        blocks.append(mcp.create_bulleted_list_item(block_text))
    
    # Cultural Dining section
    blocks.append(mcp.create_heading_2("🍽️ Cultural Dining Experience"))
    for restaurant in cultural_restaurants:
        name = get_property_value(restaurant, "Name", "title") or ""
        tags = get_property_value(restaurant, "Tags", "multi_select")
        tag_text = tags[0] if isinstance(tags, list) and tags else ""
        
        if tag_text:
            block_text = f"{name} (Tag: {tag_text})"
        else:
            block_text = name
        
        blocks.append(mcp.create_numbered_list_item(block_text))
    
    # Coffee Break Spots section
    blocks.append(mcp.create_heading_2("☕ Coffee Break Spots"))
    
    # Create toggle (without children - we'll add them separately)
    toggle_block = mcp.create_toggle("Top Cafes to Visit")
    blocks.append(toggle_block)
    
    # Weekend Summary section
    blocks.append(mcp.create_heading_2("📊 Weekend Summary"))
    summary_text = f"This weekend includes {len(beach_activities)} beach activities, {len(cultural_restaurants)} cultural dining options, and {len(cafes)} coffee spots to explore!"
    blocks.append(mcp.create_paragraph(summary_text))
    
    # Divider
    blocks.append(mcp.create_divider())
    
    # Pro tip callout
    pro_tip = "Pro tip: Check the Seasons database for the best time to enjoy outdoor activities!"
    blocks.append(mcp.create_callout(pro_tip, "💡"))
    
    print(f"✓ Built {len(blocks)} blocks")
    
    # Step 5: Add blocks to page
    print("\n📍 Step 5: Adding content to page")
    print("-"*70)
    
    add_result = await mcp.patch_block_children(page_id, blocks)
    if not add_result:
        print("❌ Failed to add blocks to page")
        return False
    
    print(f"✓ Added main blocks to page")
    
    # Step 6: Add cafe items to the toggle block
    # Find the toggle block in the results
    print("\n📍 Step 6: Adding cafe items to toggle block")
    print("-"*70)
    
    # Get the blocks we just added to find the toggle ID
    children_result = await mcp.get_block_children(page_id)
    if children_result:
        try:
            children = parse_results(children_result)
            toggle_id = None
            
            # Find the toggle block
            for child in children:
                if child.get("type") == "toggle":
                    toggle_text = child.get("toggle", {}).get("rich_text", [])
                    if toggle_text and "Top Cafes" in toggle_text[0].get("text", {}).get("content", ""):
                        toggle_id = child.get("id")
                        break
            
            if toggle_id:
                # Add cafe to-do items to the toggle
                cafe_todos = []
                for cafe in cafes:
                    cafe_name = get_property_value(cafe, "Name", "title") or ""
                    cafe_todos.append(mcp.create_to_do(cafe_name, checked=False))
                
                if cafe_todos:
                    cafe_result = await mcp.patch_block_children(toggle_id, cafe_todos)
                    if cafe_result:
                        print(f"✓ Added {len(cafe_todos)} cafe items to toggle")
                    else:
                        print("⚠️ Warning: Could not add cafe items to toggle")
        except Exception as e:
            print(f"⚠️ Warning: Error adding cafe items: {e}")
    
    print("\n" + "="*70)
    print("✅ Perfect Weekend Adventure page created successfully!")
    print("="*70)
    
    return True


async def main():
    """Main entry point"""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("❌ EVAL_NOTION_API_KEY not set")
        return False
    
    print("\n🚀 Toronto Weekend Adventure Planner - 100% MCP Implementation\n")
    
    async with NotionMCPTools(api_key) as mcp:
        # Find Toronto Guide page
        print("📍 Step 0: Finding 'Toronto Guide' page")
        print("-"*70)
        
        page_id = await find_page_by_title(mcp, "Toronto Guide")
        if not page_id:
            print("❌ Could not find Toronto Guide page")
            return False
        
        print(f"✓ Found page: {page_id}\n")
        
        # Create planner
        success = await create_weekend_planner(mcp, page_id)
        return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
