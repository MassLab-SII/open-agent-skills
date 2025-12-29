#!/usr/bin/env python3
"""
Create Packing Progress Summary - Specialized Skill
==================================================

This skill creates a "Packing Progress Summary" section in the Japan Travel Planner page.
It calculates packed/unpacked counts for each category and creates a nice summary.

Usage:
  python3 create_packing_summary.py "Japan Travel Planner" "Packing List"
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any
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


class CreatePackingSummary:
    """
    Specialized skill to create a packing progress summary.
    Queries the packing list and creates a formatted summary.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EVAL_NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in EVAL_NOTION_API_KEY environment variable")
    
    async def process(self, page_name: str, database_name: str) -> Dict[str, Any]:
        """
        Create and insert packing progress summary.
        
        Args:
            page_name: Name of the page to insert summary into
            database_name: Name of the database to query for statistics
            
        Returns:
            Result dictionary
        """
        result = {
            "success": False,
            "page_id": None,
            "blocks_created": 0,
            "categories_stats": {},
            "errors": []
        }
        
        try:
            async with NotionMCPTools(self.api_key, notion_version="2025-09-03") as mcp:
                # Step 1: Search for the page
                print(f"\n📍 Searching for page: {page_name}")
                print("-" * 70)
                
                search_result = await mcp.search(page_name)
                if not search_result:
                    result["errors"].append(f"Page '{page_name}' not found")
                    return result
                
                search_data = json.loads(search_result)
                page = None
                for item in search_data.get("results", []):
                    if item.get("object") == "page":
                        page = item
                        break
                
                if not page:
                    result["errors"].append(f"No page found for '{page_name}'")
                    return result
                
                page_id = page.get("id")
                result["page_id"] = page_id
                print(f"✓ Found page (ID: {page_id[:20]}...)")
                
                # Step 2: Search for the database to query
                print(f"\n📍 Searching for database: {database_name}")
                print("-" * 70)
                
                search_result = await mcp.search(database_name)
                if not search_result:
                    result["errors"].append(f"Database '{database_name}' not found")
                    return result
                
                search_data = json.loads(search_result)
                database = None
                for item in search_data.get("results", []):
                    obj_type = item.get("object")
                    if obj_type in ["database", "data_source"]:
                        database = item
                        break
                
                if not database:
                    result["errors"].append(f"No database found for '{database_name}'")
                    return result
                
                database_id = database.get("id")
                print(f"✓ Found database (ID: {database_id[:20]}...)")
                
                # Step 3: Query the database to get statistics
                print(f"\n📍 Querying database for statistics")
                print("-" * 70)
                
                query_result = await mcp.query_database(database_id)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                query_data = json.loads(query_result)
                all_items = query_data.get("results", [])
                print(f"✓ Retrieved {len(all_items)} items")
                
                # Step 4: Calculate statistics by category
                print(f"\n📍 Calculating packing statistics")
                print("-" * 70)
                
                category_stats = {}
                for item in all_items:
                    properties = item.get("properties", {})
                    type_prop = properties.get("Type", {})
                    packed = properties.get("Packed", {}).get("checkbox", False)
                    
                    # Extract category
                    if type_prop.get("type") == "multi_select":
                        categories = [s.get("name") for s in type_prop.get("multi_select", [])]
                    else:
                        categories = []
                    
                    # Update stats for each category
                    for category in categories:
                        if category not in category_stats:
                            category_stats[category] = {"total": 0, "packed": 0}
                        category_stats[category]["total"] += 1
                        if packed:
                            category_stats[category]["packed"] += 1
                
                result["categories_stats"] = category_stats
                
                # Print stats
                total_items = len(all_items)
                total_packed = sum(s["packed"] for s in category_stats.values())
                
                print(f"  Total items: {total_items}")
                print(f"  Total packed: {total_packed}")
                print(f"\n  By category:")
                for category in sorted(category_stats.keys()):
                    stats = category_stats[category]
                    pct = (stats["packed"] / stats["total"] * 100) if stats["total"] > 0 else 0
                    print(f"    • {category:20} {stats['packed']:2}/{stats['total']:2} ({pct:5.1f}%)")
                
                # Step 5: Find the "Packing List" heading to insert after
                print(f"\n📍 Finding insertion point")
                print("-" * 70)
                
                blocks_result = await mcp.get_block_children(page_id)
                if not blocks_result:
                    result["errors"].append("Failed to get page blocks")
                    return result
                
                blocks_data = json.loads(blocks_result)
                blocks = blocks_data.get("results", [])
                
                insertion_block_id = None
                for idx, block in enumerate(blocks):
                    if block.get("type") == "heading_2":
                        heading_text = self._extract_block_text(block)
                        if "packing list" in heading_text.lower():
                            print(f"✓ Found 'Packing List' heading at position {idx}")
                            # Get the next block after heading for insertion (same as packing_progress_summary.py)
                            if idx + 1 < len(blocks):
                                insertion_block_id = blocks[idx + 1].get("id")
                            else:
                                insertion_block_id = block.get("id")
                            break
                
                if not insertion_block_id:
                    # If not found, use the page ID
                    print("⚠️  'Packing List' heading not found, will append to page")
                    insertion_block_id = page_id
                
                # Step 6: Create and insert summary blocks
                print(f"\n📍 Creating and inserting summary blocks")
                print("-" * 70)
                
                summary_blocks = self._build_summary_blocks(category_stats, total_packed, total_items)
                
                append_result = None
                
                # Method 1: Try to use insertion_block_id (Packing List heading) to append children
                try:
                    append_result = await mcp.session.call_tool("API-patch-block-children", {
                        "block_id": insertion_block_id,
                        "children": summary_blocks
                    })
                    if append_result:
                        result["blocks_created"] = len(summary_blocks)
                        print(f"✓ Created and inserted {len(summary_blocks)} blocks (via API-patch-block-children)")
                except Exception as e:
                    print(f"  Method API-patch-block-children failed: {type(e).__name__}")
                
                # Method 2: Fallback - try to append to the main page
                if not append_result:
                    try:
                        append_result = await mcp.session.call_tool("API-patch-page-children", {
                            "page_id": page_id,
                            "children": summary_blocks
                        })
                        if append_result:
                            result["blocks_created"] = len(summary_blocks)
                            print(f"✓ Created and inserted {len(summary_blocks)} blocks (via API-patch-page-children)")
                    except Exception as e:
                        result["errors"].append(f"Failed to append blocks: {str(e)}")
                        print(f"❌ Error appending blocks: {e}")
                
                if append_result:
                    print(f"✓ Created and inserted {len(summary_blocks)} blocks")
                    for block in summary_blocks:
                        block_type = block.get("type")
                        if block_type == "paragraph":
                            text = block.get("paragraph", {}).get("rich_text", [])
                            text_str = "".join([t.get("text", {}).get("content", "") for t in text])
                            print(f"  • {block_type}: {text_str[:50]}")
                        elif block_type == "bulleted_list_item":
                            text = block.get("bulleted_list_item", {}).get("rich_text", [])
                            text_str = "".join([t.get("text", {}).get("content", "") for t in text])
                            print(f"  • {block_type}: {text_str[:50]}")
                        else:
                            print(f"  • {block_type}")
                else:
                    result["errors"].append("Failed to append blocks with both methods")
                
                result["success"] = True
                print(f"\n✓ Packing summary created successfully")
        
        except Exception as e:
            result["errors"].append(f"Processing error: {str(e)}")
            print(f"❌ Error: {e}")
        
        return result
    
    def _extract_block_text(self, block: Dict) -> str:
        """Extract text content from a block"""
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        if block_type == "heading_2":
            text_array = block_data.get("rich_text", [])
        elif block_type == "paragraph":
            text_array = block_data.get("rich_text", [])
        else:
            return ""
        
        if text_array:
            return "".join([t.get("plain_text", "") for t in text_array])
        return ""
    
    def _extract_block_text_from_definition(self, block: Dict) -> str:
        """Extract text from a block definition"""
        block_type = block.get("type")
        block_data = block.get(block_type, {})
        
        if isinstance(block_data, dict):
            if "rich_text" in block_data:
                text_array = block_data.get("rich_text", [])
                return "".join([t.get("plain_text", "") for t in text_array])
            elif "text" in block_data:
                return block_data.get("text", "")
        
        return ""
    
    def _build_summary_blocks(self, category_stats: Dict, total_packed: int, total_items: int) -> List[Dict]:
        """Build block definitions for the summary"""
        blocks = []
        
        # Title block - simple paragraph with bold text (NOT heading)
        blocks.append({
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
        
        # Category breakdown as bulleted list
        for category in sorted(category_stats.keys()):
            stats = category_stats[category]
            pct = (stats["packed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"{category}: {stats['packed']}/{stats['total']} packed"
                            }
                        }
                    ]
                }
            })
        
        return blocks


async def main():
    """Main CLI entry point"""
    try:
        if len(sys.argv) < 3:
            print("Usage: python3 create_packing_summary.py <page_name> <database_name>")
            print("\nExamples:")
            print('  python3 create_packing_summary.py "Japan Travel Planner" "Packing List"')
            return 1
        
        page_name = sys.argv[1]
        database_name = sys.argv[2]
        
        # Check for --json flag
        output_json = "--json" in sys.argv
        
        # Extract API key from args or environment
        api_key = os.getenv("EVAL_NOTION_API_KEY")
        for i, arg in enumerate(sys.argv):
            if arg == "--api-key" and i + 1 < len(sys.argv):
                api_key = sys.argv[i + 1]
        
        skill = CreatePackingSummary(api_key)
        
        result = await skill.process(
            page_name=page_name,
            database_name=database_name
        )
        
        # Output results
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print("\n" + "=" * 70)
            print("RESULT SUMMARY")
            print("=" * 70)
            print(f"Success: {result['success']}")
            print(f"Page ID: {result['page_id']}")
            print(f"Blocks Created: {result['blocks_created']}")
            
            if result['categories_stats']:
                print("\n📊 Category Statistics:")
                for category, stats in sorted(result['categories_stats'].items()):
                    pct = (stats['packed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    print(f"  • {category:20} {stats['packed']:2}/{stats['total']:2} ({pct:5.1f}%)")
            
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
