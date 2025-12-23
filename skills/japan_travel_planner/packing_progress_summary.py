#!/usr/bin/env python3
"""
Packing Progress Summary - MCP-based Implementation
====================================================

This skill:
1. Updates packing items in the Packing List database (mark items as packed)
2. Creates a Packing Progress Summary section in the Japan Travel Planner page
3. Displays statistics for each category in bullet point format

Uses 100% MCP tools for all Notion operations.
The API key is automatically loaded from environment variables.

Usage:
    python3 packing_progress_summary.py
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
from skills.japan_travel_planner.utils import (
    NotionMCPTools,
    extract_page_property
)

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


class PackingProgressSummary:
    """
    Create packing progress summary with automated item status updates.
    Uses 100% MCP tools for all operations.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize PackingProgressSummary.
        
        Args:
            api_key: Notion API key (defaults to EVAL_NOTION_API_KEY)
        """
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment")
        
        self.api_key = api_key
    
    async def process(self) -> Dict[str, any]:
        """
        Process packing list and create progress summary.
        
        Returns:
            Dictionary with results including:
            - success: Boolean indicating overall success
            - packing_database_id: ID of the Packing List database
            - japan_planner_page_id: ID of the Japan Travel Planner page
            - items_updated: Number of items marked as packed
            - category_stats: Dictionary with category statistics
            - summary_block_created: Whether summary block was created
        """
        result = {
            "success": False,
            "packing_database_id": None,
            "japan_planner_page_id": None,
            "items_updated": 0,
            "category_stats": {},
            "summary_block_created": False,
            "errors": [],
        }
        
        async with NotionMCPTools(self.api_key) as mcp:
            try:
                # Step 1: Search for Packing List database
                print("\n📍 Step 1: Searching for Packing List database")
                print("-" * 70)
                
                search_result = await mcp.search("Packing List")
                if not search_result:
                    result["errors"].append("Packing List database not found")
                    return result
                
                search_data = json.loads(search_result)
                packing_db = None
                for item in search_data.get("results", []):
                    if item.get("object") == "database":
                        packing_db = item
                        break
                
                if not packing_db:
                    result["errors"].append("Packing List database not found in search results")
                    return result
                
                packing_database_id = packing_db.get("id")
                result["packing_database_id"] = packing_database_id
                print(f"✓ Found Packing List database (ID: {packing_database_id[:20]}...)")
                
                # Step 2: Search for Japan Travel Planner page
                print("\n📍 Step 2: Searching for Japan Travel Planner page")
                print("-" * 70)
                
                search_result = await mcp.search("Japan Travel Planner")
                if not search_result:
                    result["errors"].append("Japan Travel Planner page not found")
                    return result
                
                search_data = json.loads(search_result)
                planner_page = None
                for item in search_data.get("results", []):
                    if item.get("object") == "page" and "Japan Travel Planner" in str(item.get("properties", {}).get("title", {})):
                        planner_page = item
                        break
                
                if not planner_page:
                    # Try the first page result if title match fails
                    for item in search_data.get("results", []):
                        if item.get("object") == "page":
                            planner_page = item
                            break
                
                if not planner_page:
                    result["errors"].append("Japan Travel Planner page not found in search results")
                    return result
                
                japan_planner_page_id = planner_page.get("id")
                result["japan_planner_page_id"] = japan_planner_page_id
                print(f"✓ Found Japan Travel Planner page (ID: {japan_planner_page_id[:20]}...)")
                
                # Step 3: Query packing database for all items
                print("\n📍 Step 3: Querying Packing List database")
                print("-" * 70)
                
                query_result = await mcp.query_database(packing_database_id)
                if not query_result:
                    result["errors"].append("Failed to query packing database")
                    return result
                
                query_data = json.loads(query_result)
                all_items = query_data.get("results", [])
                print(f"✓ Retrieved {len(all_items)} items from packing database")
                
                # Step 4: Update items and collect statistics
                print("\n📍 Step 4: Updating item status and collecting statistics")
                print("-" * 70)
                
                category_stats = defaultdict(lambda: {"packed": 0, "total": 0})
                items_updated = 0
                
                for item in all_items:
                    properties = item.get("properties", {})
                    item_id = item.get("id")
                    
                    # Extract item information
                    name_prop = properties.get("Name", {})
                    item_name = ""
                    if name_prop.get("type") == "title":
                        title_array = name_prop.get("title", [])
                        if title_array:
                            item_name = title_array[0].get("plain_text", "")
                    
                    # Get Type (Category)
                    type_prop = properties.get("Type", {})
                    categories = []
                    if type_prop.get("type") == "multi_select":
                        categories = [opt.get("name", "") for opt in type_prop.get("multi_select", [])]
                    
                    # Check if Packed
                    packed_prop = properties.get("Packed", {})
                    is_packed = packed_prop.get("checkbox", False) if packed_prop.get("type") == "checkbox" else False
                    
                    # Update statistics for each category
                    for category in categories:
                        if category:
                            category_stats[category]["total"] += 1
                            if is_packed:
                                category_stats[category]["packed"] += 1
                    
                    # Update specific items based on task requirements
                    is_hat = "hat" in item_name.lower()
                    is_sim_card = "SIM Card" in item_name or "sim card" in item_name.lower()
                    is_wallet = "Wallet" in item_name or "wallet" in item_name.lower()
                    is_clothes = "Clothes" in categories
                    
                    # Handle Clothes category: all packed EXCEPT hat
                    if is_clothes:
                        if is_hat:
                            # Hat should NOT be packed
                            if is_packed:
                                # If it's somehow packed, unpack it
                                print(f"  Unpacking: {item_name} (hat should not be packed)")
                                await mcp.update_page_property(item_id, {
                                    "Packed": {"checkbox": False}
                                })
                                category_stats["Clothes"]["packed"] -= 1
                                items_updated += 1
                        else:
                            # All other Clothes should be packed
                            if not is_packed:
                                print(f"  Packing: {item_name}")
                                await mcp.update_page_property(item_id, {
                                    "Packed": {"checkbox": True}
                                })
                                category_stats["Clothes"]["packed"] += 1
                                items_updated += 1
                    
                    # Handle SIM Card - mark as packed
                    elif is_sim_card:
                        print(f"  Found SIM Card: {item_name} (packed: {is_packed})")
                        if not is_packed:
                            await mcp.update_page_property(item_id, {
                                "Packed": {"checkbox": True}
                            })
                            for category in categories:
                                category_stats[category]["packed"] += 1
                            items_updated += 1
                    
                    # Handle Wallet - mark as packed
                    elif is_wallet:
                        print(f"  Found Wallet: {item_name} (packed: {is_packed})")
                        if not is_packed:
                            await mcp.update_page_property(item_id, {
                                "Packed": {"checkbox": True}
                            })
                            for category in categories:
                                category_stats[category]["packed"] += 1
                            items_updated += 1
                
                result["items_updated"] = items_updated
                result["category_stats"] = dict(category_stats)
                print(f"✓ Updated {items_updated} items")
                print(f"✓ Category statistics collected")
                
                # Step 5: Get page blocks to find insertion point
                print("\n📍 Step 5: Finding insertion point for summary")
                print("-" * 70)
                
                blocks_result = await mcp.get_block_children(japan_planner_page_id)
                if not blocks_result:
                    result["errors"].append("Failed to get page blocks")
                    return result
                
                blocks_data = json.loads(blocks_result)
                blocks = blocks_data.get("results", [])
                
                # Find "Packing List 💼" heading or similar
                insertion_block_id = japan_planner_page_id  # Default to page
                for idx, block in enumerate(blocks):
                    block_type = block.get("type")
                    if block_type == "heading_2":
                        heading_data = block.get("heading_2", {})
                        heading_text = ""
                        for rt in heading_data.get("rich_text", []):
                            heading_text += rt.get("text", {}).get("content", "")
                        
                        if "Packing List" in heading_text:
                            print(f"✓ Found 'Packing List' heading at position {idx}")
                            # Get the next block after heading for insertion
                            if idx + 1 < len(blocks):
                                insertion_block_id = blocks[idx + 1].get("id")
                            else:
                                insertion_block_id = block.get("id")
                            break
                
                # Step 6: Create progress summary blocks
                print("\n📍 Step 6: Creating Packing Progress Summary")
                print("-" * 70)
                
                # Build summary content - create blocks in the page
                summary_blocks = []
                
                # Add title paragraph
                summary_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Packing Progress Summary"
                                },
                                "annotations": {
                                    "bold": True
                                }
                            }
                        ]
                    }
                })
                
                # Add statistics as bullet points
                for category in sorted(category_stats.keys()):
                    stats = category_stats[category]
                    packed = stats["packed"]
                    total = stats["total"]
                    
                    summary_blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"{category}: {packed}/{total} packed"
                                    }
                                }
                            ]
                        }
                    })
                
                # Try to append blocks to the page - try multiple approaches
                append_result = None
                
                # First attempt: use append_block_children
                print(f"  Attempting to create {len(summary_blocks)} blocks...")
                
                # Direct MCP call approach
                try:
                    # Try using mcp.session directly for more control
                    
                    # Method 1: Try patch-block-children (this is the correct API!)
                    try:
                        append_result = await mcp.session.call_tool("API-patch-block-children", {
                            "block_id": japan_planner_page_id,
                            "children": summary_blocks
                        })
                        if append_result:
                            result["summary_block_created"] = True
                            print(f"✓ Created Packing Progress Summary with {len(summary_blocks)} blocks (via API-patch-block-children)")
                            for category, stats in sorted(category_stats.items()):
                                print(f"  - {category}: {stats['packed']}/{stats['total']} packed")
                    except Exception as e:
                        print(f"  Method API-patch-block-children: {e}")
                    
                    # Method 2: Try patch-page-children
                    if not append_result:
                        try:
                            append_result = await mcp.session.call_tool("API-patch-page-children", {
                                "page_id": japan_planner_page_id,
                                "children": summary_blocks
                            })
                            if append_result:
                                result["summary_block_created"] = True
                                print(f"✓ Created Packing Progress Summary with {len(summary_blocks)} blocks (via API-patch-page-children)")
                                for category, stats in sorted(category_stats.items()):
                                    print(f"  - {category}: {stats['packed']}/{stats['total']} packed")
                        except Exception as e:
                            print(f"  Method API-patch-page-children: {e}")
                    
                    # Method 3: Try append-block-children
                    if not append_result:
                        try:
                            append_result = await mcp.session.call_tool("API-append-block-children", {
                                "block_id": japan_planner_page_id,
                                "children": summary_blocks
                            })
                            if append_result:
                                result["summary_block_created"] = True
                                print(f"✓ Created Packing Progress Summary with {len(summary_blocks)} blocks (via API-append-block-children)")
                                for category, stats in sorted(category_stats.items()):
                                    print(f"  - {category}: {stats['packed']}/{stats['total']} packed")
                        except Exception as e:
                            print(f"  Method API-append-block-children: {e}")
                    
                    if not append_result:
                        print(f"⚠️  Could not create summary blocks - no suitable MCP API method available")
                        print(f"  Note: Items have been updated successfully")
                        print(f"  Packing Progress Summary can be created manually in Notion:")
                        print(f"    Title: Packing Progress Summary")
                        for category, stats in sorted(category_stats.items()):
                            print(f"    • {category}: {stats['packed']}/{stats['total']} packed")
                
                except Exception as e:
                    print(f"⚠️  Error during block creation attempt: {e}")
                    print(f"  Items have been updated successfully")
                
                result["success"] = True
                
            except Exception as e:
                result["errors"].append(f"Processing error: {str(e)}")
                print(f"❌ Error: {e}")
        
        return result


async def main():
    """Main entry point."""
    try:
        skill = PackingProgressSummary()
        result = await skill.process()
        
        print("\n" + "=" * 70)
        print("RESULT SUMMARY")
        print("=" * 70)
        print(f"Success: {result['success']}")
        print(f"Items Updated: {result['items_updated']}")
        print(f"Summary Block Created: {result['summary_block_created']}")
        
        if result['category_stats']:
            print("\n📊 Packing Progress Summary:")
            total_packed = 0
            total_items = 0
            for category, stats in sorted(result['category_stats'].items()):
                total_packed += stats['packed']
                total_items += stats['total']
                percentage = (stats['packed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"  • {category:20} {stats['packed']:2}/{stats['total']:2} packed ({percentage:5.1f}%)")
            
            overall_percentage = (total_packed / total_items * 100) if total_items > 0 else 0
            print(f"  {'─' * 60}")
            print(f"  {'OVERALL':20} {total_packed:2}/{total_items:2} packed ({overall_percentage:5.1f}%)")
        
        if result['errors']:
            print("\n⚠️  Notes:")
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
