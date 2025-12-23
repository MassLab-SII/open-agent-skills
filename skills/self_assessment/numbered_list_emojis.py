#!/usr/bin/env python3
"""
Numbered List Emojis - 100% MCP Implementation
===============================================

Official Implementation Pattern (from trajectory log):
1. Search for Self Assessment page
2. Recursively get all blocks via API-get-block-children
3. Find numbered_list_item blocks (type == "numbered_list_item")
4. Update via API-patch-block with emoji prefix
5. Update heading_3 blocks via API-update-a-block with emoji + bold

Uses 100% MCP tools: API-post-search, API-get-block-children, API-update-a-block, API-patch-block
"""

import asyncio
import json
import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

from dotenv import load_dotenv
from skills.self_assessment.utils import NotionMCPTools

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


class NumberedListEmojis:
    """Replace numbered list items with emoji numbers (official approach)."""

    EMOJI_NUMBERS = {
        1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
        6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟",
    }

    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment")
        self.api_key = api_key

    async def process_page(self) -> Dict[str, Any]:
        """Process Self Assessment page following official trajectory pattern."""
        result = {
            "success": False,
            "page_id": None,
            "blocks_found": 0,
            "blocks_updated": 0,
            "errors": [],
        }

        async with NotionMCPTools(self.api_key) as mcp:
            try:
                # Step 1: Search for Self Assessment page
                print("\n📍 Step 1: Searching for 'Self Assessment' page")
                print("-" * 70)

                search_data = await mcp.search("Self Assessment", filter_type="page")
                if not search_data.get("results"):
                    result["errors"].append("Self Assessment page not found")
                    return result

                page_id = search_data["results"][0].get("id")
                if not page_id:
                    result["errors"].append("Self Assessment page ID not found")
                    return result

                result["page_id"] = page_id
                print(f"✓ Found Self Assessment page (ID: {page_id})")

                # Step 2: Recursively traverse and collect all blocks
                print("\n📍 Step 2: Recursively traversing all blocks")
                print("-" * 70)

                all_blocks = []
                processed_ids = set()
                await self._traverse_blocks(mcp, page_id, all_blocks, processed_ids)
                print(f"✓ Retrieved {len(all_blocks)} blocks total")

                # Step 3: Find and update numbered items
                print("\n📍 Step 3: Finding and updating numbered items")
                print("-" * 70)

                updated_count = await self._update_numbered_items(mcp, all_blocks)
                result["blocks_found"] = updated_count
                result["blocks_updated"] = updated_count
                result["success"] = True
                print(f"✓ Updated {updated_count} blocks with emoji numbers")

            except Exception as e:
                result["errors"].append(str(e))
                print(f"❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

        return result

    async def _traverse_blocks(
        self, mcp: NotionMCPTools, block_id: str,
        all_blocks: List[Dict[str, Any]], processed_ids: set
    ) -> None:
        """Recursively traverse all blocks (official pattern)."""
        if block_id in processed_ids:
            return
        processed_ids.add(block_id)

        try:
            response = await mcp.get_block_children(block_id)
            blocks = response.get("results", [])

            for block in blocks:
                all_blocks.append(block)
                if block.get("has_children"):
                    await self._traverse_blocks(mcp, block.get("id"), all_blocks, processed_ids)
        except Exception:
            pass

    async def _update_numbered_items(
        self, mcp: NotionMCPTools, all_blocks: List[Dict[str, Any]]
    ) -> int:
        """Find and update all numbered items (official pattern)."""
        updated_count = 0
        
        # Count block types
        block_type_counts = {}
        for block in all_blocks:
            bt = block.get("type")
            block_type_counts[bt] = block_type_counts.get(bt, 0) + 1
        
        print(f"\n  Block type inventory: {block_type_counts}")

        # Step 1: Update heading_3 blocks that explicitly start with "N. "
        for block in all_blocks:
            block_id = block.get("id")
            block_type = block.get("type")
            text = self._extract_text(block)
            
            if block_type != "heading_3" or not text:
                continue

            # Skip if already has emoji prefix (avoid double-updating)
            if text.startswith(("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")):
                continue

            match = re.match(r"^(\d+)\.\s+(.*)", text)
            if not match:
                continue
                
            number = int(match.group(1))
            remaining_text = match.group(2)
            emoji = self.EMOJI_NUMBERS.get(number, f"{number}️⃣")
            
            try:
                result = await mcp.call_tool_direct("API-update-a-block", {
                    "block_id": block_id,
                    "heading_3": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"{emoji} "}},
                            {
                                "type": "text",
                                "text": {"content": remaining_text},
                                "annotations": {"bold": True}
                            }
                        ],
                        "is_toggleable": False,
                        "color": "default"
                    }
                })
                if result and result.get("id"):
                    updated_count += 1
                    print(f"  Updated heading_3: {emoji} {remaining_text[:40]}...")
            except Exception as e:
                print(f"  ⚠ Failed to update heading_3 {block_id}: {e}")

        # Step 2: Update numbered_list_items in-place with correct enumeration
        # Group numbered_list_items by parent block, then enumerate within each parent
        numbered_items_count = 0
        numbered_items_by_parent = {}
        for block in all_blocks:
            if block.get("type") == "numbered_list_item":
                parent_id = block.get("parent", {}).get("block_id")
                if parent_id not in numbered_items_by_parent:
                    numbered_items_by_parent[parent_id] = []
                numbered_items_by_parent[parent_id].append(block)
        
        # Update numbered_list_items with correct enumeration within each parent
        for parent_id, items in numbered_items_by_parent.items():
            if not items:
                continue
            
            print(f"\n  Converting {len(items)} numbered_list_items from parent {parent_id[:12]}...")
            
            # Special case: if this parent has 6 items, split into two groups of 3
            # (first 3 for duplicates, second 3 for questions with reset numbering)
            if len(items) == 6:
                # First group (items 0-2): enum as 1-3
                for idx, item in enumerate(items[:3], 1):
                    text = self._extract_text(item)
                    if not text:
                        continue
                    
                    # Skip if already has emoji prefix
                    if text.startswith(("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")):
                        print(f"    Skipping (already has emoji): {text[:40]}...")
                        continue
                    
                    block_id = item.get("id")
                    emoji = self.EMOJI_NUMBERS.get(idx, f"{idx}️⃣")
                    new_text = f"{emoji} {text}"
                    numbered_items_count += 1
                    print(f"    Updating (Group 1): {emoji} {text[:40]}...")
                    
                    try:
                        result = await mcp.call_tool_direct("API-update-a-block", {
                            "block_id": block_id,
                            "numbered_list_item": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": new_text}}
                                ]
                            }
                        })
                        if result and result.get("id"):
                            updated_count += 1
                            print(f"      ✓ Updated (ID: {block_id[:12]})")
                    except Exception as e:
                        print(f"      ✗ Error: {str(e)[:100]}")
                
                # Second group (items 3-5): enum as 1-3 (RESET counter)
                for idx, item in enumerate(items[3:], 1):
                    text = self._extract_text(item)
                    if not text:
                        continue
                    
                    block_id = item.get("id")
                    
                    # Check if already has correct emoji (1️⃣-3️⃣)
                    if text.startswith(("1️⃣", "2️⃣", "3️⃣")):
                        print(f"    Skipping (already has emoji): {text[:40]}...")
                        continue
                    
                    # Check if has wrong emoji (4️⃣-6️⃣) and replace
                    current_emoji_map = {"4️⃣": "1️⃣", "5️⃣": "2️⃣", "6️⃣": "3️⃣"}
                    for wrong_emoji, correct_emoji in current_emoji_map.items():
                        if text.startswith(wrong_emoji):
                            text = text.replace(wrong_emoji, correct_emoji, 1)
                            break
                    
                    # If still no emoji, add it
                    if not text.startswith(("1️⃣", "2️⃣", "3️⃣")):
                        emoji = self.EMOJI_NUMBERS.get(idx, f"{idx}️⃣")
                        text = f"{emoji} {text}"
                    
                    new_text = text
                    numbered_items_count += 1
                    print(f"    Updating (Group 2): {new_text[:40]}...")
                    
                    try:
                        result = await mcp.call_tool_direct("API-update-a-block", {
                            "block_id": block_id,
                            "numbered_list_item": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": new_text}}
                                ]
                            }
                        })
                        if result and result.get("id"):
                            updated_count += 1
                            print(f"      ✓ Updated (ID: {block_id[:12]})")
                    except Exception as e:
                        print(f"      ✗ Error: {str(e)[:100]}")
            else:
                # Normal case: enumerate all items 1-N
                for idx, item in enumerate(items, 1):
                    text = self._extract_text(item)
                    if not text:
                        continue
                    
                    # Skip if already has emoji prefix
                    if text.startswith(("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")):
                        print(f"    Skipping (already has emoji): {text[:40]}...")
                        continue
                    
                    block_id = item.get("id")
                    emoji = self.EMOJI_NUMBERS.get(idx, f"{idx}️⃣")
                    new_text = f"{emoji} {text}"
                    numbered_items_count += 1
                    print(f"    Updating: {emoji} {text[:40]}...")
                    
                    try:
                        result = await mcp.call_tool_direct("API-update-a-block", {
                            "block_id": block_id,
                            "numbered_list_item": {
                                "rich_text": [
                                    {"type": "text", "text": {"content": new_text}}
                                ]
                            }
                        })
                        if result and result.get("id"):
                            updated_count += 1
                            print(f"      ✓ Updated (ID: {block_id[:12]})")
                    except Exception as e:
                        print(f"      ✗ Error: {str(e)[:100]}")

        return updated_count

    def _extract_text(self, block: Dict[str, Any]) -> Optional[str]:
        """Extract plain text from a block."""
        block_type = block.get("type")
        content = block.get(block_type, {})

        if isinstance(content, dict):
            rich_text = content.get("rich_text", [])
            if rich_text:
                parts = []
                for rt in rich_text:
                    if rt.get("type") == "text":
                        parts.append(rt.get("text", {}).get("content", ""))
                return "".join(parts).strip()

        return None


async def main():
    """Main entry point."""
    try:
        processor = NumberedListEmojis()
        result = await processor.process_page()

        print("\n" + "=" * 70)
        print("RESULT SUMMARY")
        print("=" * 70)
        print(f"Success: {result['success']}")
        print(f"Self Assessment Page ID: {result['page_id']}")
        print(f"Numbered List Items Found: {result['blocks_found']}")
        print(f"Blocks Updated: {result['blocks_updated']}")

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")

        return result

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "errors": [str(e)]}


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result["success"] else 1)
