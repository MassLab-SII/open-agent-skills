#!/usr/bin/env python3
"""
Goals Restructure Skill - 100% MCP Implementation
=================================================

Restructures the Current Goals section on the Company In A Box page by:
1. Adding a new goal heading: "🔄 Digital Transformation Initiative"
2. Converting all four goal headings to toggleable headings
3. Moving descriptions inside the toggles as child blocks
4. Preserving content and order

Uses pure MCP tools for all Notion operations.
"""

import asyncio
import json
import re
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from utils import NotionMCPTools

# Load environment
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break

api_key = os.getenv("EVAL_NOTION_API_KEY")

if not api_key:
    print("Error: EVAL_NOTION_API_KEY not set", file=sys.stderr)
    sys.exit(1)


#!/usr/bin/env python3
"""
Goals Restructure Skill - 100% MCP Implementation
=================================================

Restructures the Current Goals section on the Company In A Box page by:
1. Adding a new goal heading: "🔄 Digital Transformation Initiative"
2. Converting all four goal headings to toggleable headings
3. Moving descriptions inside the toggles as child blocks
4. Preserving content and order

Uses pure MCP tools for all Notion operations.
"""

import asyncio
import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from utils import NotionMCPTools

# Load environment
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break

api_key = os.getenv("EVAL_NOTION_API_KEY")

if not api_key:
    print("Error: EVAL_NOTION_API_KEY not set", file=sys.stderr)
    sys.exit(1)


def extract_page_id_from_json(result_text: str) -> str:
    """Extract page/block ID from JSON response"""
    if not result_text:
        return None
    try:
        data = json.loads(result_text)
        if "id" in data:
            return data["id"]
    except (json.JSONDecodeError, TypeError):
        pass
    
    match = re.search(r'"id":"([^"]+)"', result_text)
    return match.group(1) if match else None


def get_block_text(block: Dict) -> str:
    """Extract plain text from a block"""
    if not isinstance(block, dict):
        return ""
    
    block_type = block.get("type", "")
    type_obj = block.get(block_type, {})
    
    if isinstance(type_obj, dict):
        rich_text = type_obj.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in rich_text)
    return ""


def parse_blocks_response(response_text: str):
    """Parse blocks from API response"""
    if not response_text:
        return []
    
    try:
        data = json.loads(response_text)
        results = data.get("results", [])
        return results if isinstance(results, list) else []
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


async def find_page_by_title(mcp: NotionMCPTools, title: str) -> str:
    """Find a page by title using search"""
    search_result = await mcp.search(title)
    if not search_result:
        return None
    
    try:
        data = json.loads(search_result)
        for result in data.get("results", []):
            if result.get("object") == "page":
                return result.get("id")
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return None


async def find_current_goals_parent(mcp: NotionMCPTools, page_id: str) -> str:
    """
    Find the parent block containing the Current Goals section.
    Handles column structures in Company In A Box page.
    """
    queue = [page_id]
    visited = set()
    
    while queue:
        parent_id = queue.pop(0)
        if parent_id in visited:
            continue
        visited.add(parent_id)
        
        children_result = await mcp.get_block_children(parent_id)
        blocks = parse_blocks_response(children_result)
        
        # First check if Current Goals is in direct children
        for block in blocks:
            if block.get("type") in ["heading_1", "heading_2", "heading_3"]:
                text = get_block_text(block)
                if "current goals" in text.lower():
                    print(f"✓ Found Current Goals in parent: {parent_id}")
                    return parent_id
        
        # Check all blocks for column_list and explore them
        for block in blocks:
            if block.get("type") == "column_list":
                # Get columns
                columns_result = await mcp.get_block_children(block["id"])
                columns = parse_blocks_response(columns_result)
                
                # Check each column
                for col in columns:
                    if col.get("type") == "column":
                        # Check if Current Goals is in this column
                        col_result = await mcp.get_block_children(col["id"])
                        col_blocks = parse_blocks_response(col_result)
                        
                        for cb in col_blocks:
                            if cb.get("type") in ["heading_1", "heading_2", "heading_3"]:
                                text = get_block_text(cb)
                                if "current goals" in text.lower():
                                    print(f"✓ Found Current Goals in column: {col['id']}")
                                    return col["id"]
        
        # Add children with has_children to queue for further search
        for block in blocks:
            if block.get("has_children") and block.get("type") != "column_list":
                queue.append(block["id"])
    
    return None


async def restructure_goals(mcp: NotionMCPTools, parent_id: str) -> bool:
    """
    Main function to restructure the Current Goals section
    Strategy:
    1. Find all goal headings and their descriptions
    2. Update each heading to be toggleable (is_toggleable: true)
    3. Delete original description blocks
    4. Add descriptions as children of toggleable headings
    5. Add new goal if needed
    """
    
    print("\n" + "="*70)
    print("Starting Goals Restructure...")
    print("="*70)
    
    # Get all blocks in the parent (Current Goals column)
    children_result = await mcp.get_block_children(parent_id)
    goal_blocks = parse_blocks_response(children_result)
    
    # Find Current Goals heading
    current_goals_idx = None
    for i, block in enumerate(goal_blocks):
        if block.get("type") in ["heading_1", "heading_2", "heading_3"]:
            text = get_block_text(block)
            if "current goals" in text.lower():
                print(f"✓ Found Current Goals heading at index {i}")
                current_goals_idx = i
                break
    
    if current_goals_idx is None:
        print("❌ Could not find Current Goals heading")
        return False
    
    # Collect all goal blocks (starting after the main heading)
    goals = []
    seen_goals = set()
    i = current_goals_idx + 1
    
    while i < len(goal_blocks):
        block = goal_blocks[i]
        if block.get("type") == "heading_3":
            heading_id = block["id"]
            heading_text = get_block_text(block)
            
            # Skip duplicates
            if heading_text in seen_goals:
                i += 1
                continue
            
            seen_goals.add(heading_text)
            
            # Collect description blocks until next heading
            descriptions = []
            i += 1
            while i < len(goal_blocks) and goal_blocks[i].get("type") != "heading_3":
                descriptions.append(goal_blocks[i])
                i += 1
            
            goals.append({
                "heading_id": heading_id,
                "heading_text": heading_text,
                "description_blocks": descriptions
            })
        else:
            i += 1
    
    print(f"✓ Found {len(goals)} unique goals to process\n")
    
    # Process each goal: update to toggleable, delete descriptions, add as children
    for goal in goals:
        heading_id = goal["heading_id"]
        heading_text = goal["heading_text"]
        descriptions = goal["description_blocks"]
        
        print(f"📝 Processing: {heading_text}")
        
        # Step 1: Update heading to be toggleable
        print(f"  → Converting to toggleable heading...")
        update_result = await mcp.update_block(heading_id, {
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": heading_text}}],
                "is_toggleable": True
            }
        })
        if not update_result:
            print(f"  ❌ Error updating heading")
            return False
        print(f"  ✓ Converted to toggleable")
        
        # Step 2: Delete original description blocks and collect their data
        description_data = []
        for desc_block in descriptions:
            desc_id = desc_block["id"]
            desc_type = desc_block.get("type")
            desc_content = desc_block.get(desc_type, {})
            
            # Delete the block
            delete_result = await mcp.delete_block(desc_id)
            if not delete_result:
                print(f"  ⚠️ Warning: Could not delete description block")
            
            # Store the data for re-adding as child
            description_data.append({
                "type": desc_type,
                desc_type: desc_content
            })
        
        # Step 3: Add descriptions as children of the toggleable heading
        if description_data:
            print(f"  → Moving {len(description_data)} description block(s) inside toggle...")
            add_result = await mcp.patch_block_children(heading_id, description_data)
            if not add_result:
                print(f"  ❌ Error adding child blocks")
                return False
            print(f"  ✓ Moved {len(description_data)} blocks inside toggle")
        else:
            print(f"  ✓ No descriptions to move")
    
    # Check if new goal needs to be added
    new_goal_exists = False
    for goal in goals:
        if "digital transformation" in goal["heading_text"].lower():
            new_goal_exists = True
            break
    
    if not new_goal_exists:
        print(f"\n➕ Adding new goal: 🔄 Digital Transformation Initiative")
        
        new_goal_text = "🔄 Digital Transformation Initiative"
        new_goal_description = "Modernize our technology infrastructure and digitize key business processes to improve efficiency and customer experience."
        
        # Get the last block ID in parent to add after it
        if goal_blocks:
            last_block_id = goal_blocks[-1]["id"]
        else:
            last_block_id = None
        
        # Create new goal with description
        new_blocks = [
            {
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": new_goal_text}}],
                    "is_toggleable": True
                }
            },
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": new_goal_description}}]
                }
            }
        ]
        
        add_result = await mcp.patch_block_children(parent_id, new_blocks, after=last_block_id)
        if not add_result:
            print(f"❌ Error adding new goal heading")
            return False
        
        print(f"✓ Created new goal heading")
        print(f"✓ Added description to new goal")
    
    print("\n" + "="*70)
    print("✅ Goals restructure completed successfully!")
    print("="*70)
    
    return True


async def main():
    """Main entry point"""
    print("\n🚀 Goals Restructure Skill - 100% MCP Implementation")
    
    async with NotionMCPTools(api_key) as mcp:
        # Find the Company In A Box page
        print("\n📍 Step 1: Finding 'Company In A Box' page")
        print("-"*70)
        
        page_id = await find_page_by_title(mcp, "Company In A Box")
        
        if not page_id:
            print("❌ Error: Could not find 'Company In A Box' page", file=sys.stderr)
            return False
        
        print(f"✓ Found Company In A Box page: {page_id}")
        
        # Find parent containing Current Goals
        print("\n📍 Step 2: Finding 'Current Goals' section")
        print("-"*70)
        
        parent_id = await find_current_goals_parent(mcp, page_id)
        
        if not parent_id:
            print("❌ Error: Could not find Current Goals section", file=sys.stderr)
            return False
        
        # Restructure the goals
        print("\n📍 Step 3: Restructuring goals")
        print("-"*70)
        
        success = await restructure_goals(mcp, parent_id)
        return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
