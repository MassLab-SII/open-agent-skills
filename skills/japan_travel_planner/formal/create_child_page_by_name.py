#!/usr/bin/env python3
"""
Create Child Page By Name - Reusable Skill
===========================================

This skill:
1. Searches for a parent page by name
2. Creates a new child page under it

Uses Notion MCP for all operations.

Example:
  python3 create_child_page_by_name.py \\
    "Japan Travel Planner" \\
    "Daily Itinerary Overview"
"""

import asyncio
import json
import os
import sys
from typing import Dict, Optional
from pathlib import Path

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


class CreateChildPageByName:
    """
    Create a child page under a parent page identified by name.
    
    MCP Calls:
    - API-post-search: Find parent page
    - API-post-pages: Create child page
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EVAL_NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in EVAL_NOTION_API_KEY environment variable")
    
    async def process(self, parent_page_name: str, child_page_title: str) -> Dict:
        """
        Create a child page under a parent page.
        
        Args:
            parent_page_name: Name of the parent page to search for
            child_page_title: Title for the new child page
            
        Returns:
            Dictionary with:
            - success: bool
            - page_id: str (if successful)
            - parent_id: str (if successful)
            - errors: List[str]
        """
        result = {
            "success": False,
            "page_id": None,
            "parent_id": None,
            "errors": []
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
                
                # Handle both "page" and other object types
                for item in search_data.get("results", []):
                    obj_type = item.get("object")
                    if obj_type == "page":
                        # Check if the title matches
                        title_prop = item.get("properties", {}).get("title", {})
                        if title_prop.get("type") == "title":
                            title_array = title_prop.get("title", [])
                            if title_array:
                                item_title = title_array[0].get("plain_text", "")
                                if parent_page_name.lower() in item_title.lower():
                                    parent_page = item
                                    break
                
                # If no exact title match, just take the first page
                if not parent_page:
                    for item in search_data.get("results", []):
                        if item.get("object") == "page":
                            parent_page = item
                            break
                
                if not parent_page:
                    result["errors"].append(f"Parent page '{parent_page_name}' not found")
                    return result
                
                parent_id = parent_page.get("id")
                print(f"✓ Found parent page")
                print(f"  ID: {parent_id}")
                print(f"  Title: {parent_page_name}")
                result["parent_id"] = parent_id
                
                # Step 2: Create child page
                print(f"\n📍 Step 2: Creating child page: {child_page_title}")
                print("-" * 70)
                
                create_result = await mcp.create_child_page(
                    parent_page_id=parent_id,
                    title=child_page_title
                )
                
                if not create_result:
                    result["errors"].append("Failed to create child page")
                    return result
                
                page_data = json.loads(create_result)
                new_page_id = page_data.get("id")
                
                print(f"✓ Created child page")
                print(f"  ID: {new_page_id}")
                print(f"  Title: {child_page_title}")
                
                result["success"] = True
                result["page_id"] = new_page_id
                return result
                
        except Exception as e:
            result["errors"].append(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return result


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create a child page under a parent page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create Daily Itinerary Overview page
  python3 create_child_page_by_name.py \\
    "Japan Travel Planner" \\
    "Daily Itinerary Overview"
  
  # Create meeting notes page
  python3 create_child_page_by_name.py \\
    "Team Hub" \\
    "Meeting Notes - 2025-12-25"
        """
    )
    
    parser.add_argument("parent_page_name", help="Name of parent page")
    parser.add_argument("child_page_title", help="Title for child page")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Create Child Page By Name Skill")
    print("=" * 70)
    
    skill = CreateChildPageByName()
    result = await skill.process(
        parent_page_name=args.parent_page_name,
        child_page_title=args.child_page_title
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print("RESULT")
        print("=" * 70)
        
        if result["success"]:
            print(f"✅ Success")
            print(f"   Page ID: {result['page_id']}")
            print(f"   Parent ID: {result['parent_id']}")
        else:
            print(f"❌ Failed")
            for error in result["errors"]:
                print(f"   - {error}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
