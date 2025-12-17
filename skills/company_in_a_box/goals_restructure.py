#!/usr/bin/env python3
"""
Goals Restructure Skill

Restructures the Current Goals section on the Company In A Box page by:
1. Adding a new goal heading: "🔄 Digital Transformation Initiative"
2. Converting all four goal headings to toggleable headings
3. Moving descriptions inside the toggles as child blocks
4. Preserving content and order
"""

import os
import sys
from dotenv import load_dotenv
from notion_client import Client
import logging

# Setup logging
logging.basicConfig(level=logging.ERROR, format='%(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv(dotenv_path=".mcp_env")
api_key = os.getenv("EVAL_NOTION_API_KEY")

if not api_key:
    print("Error: EVAL_NOTION_API_KEY not set", file=sys.stderr)
    sys.exit(1)

client = Client(auth=api_key)


def find_page(title: str) -> str:
    """Find a page by title"""
    try:
        response = client.search(query=title, filter={"property": "object", "value": "page"})
        for result in response.get("results", []):
            if result.get("object") == "page":
                page_title = get_page_title(result)
                if page_title and title.lower() in page_title.lower():
                    return result["id"]
    except Exception as e:
        print(f"Error searching for page: {e}", file=sys.stderr)
    return None


def get_page_title(page: dict) -> str:
    """Extract page title from page object"""
    if "properties" in page:
        for prop_name, prop_value in page["properties"].items():
            if prop_value.get("type") == "title":
                title_parts = prop_value.get("title", [])
                return "".join(t.get("plain_text", "") for t in title_parts)
    return ""


def get_block_children(block_id: str) -> list:
    """Get direct children of a block"""
    try:
        response = client.blocks.children.list(block_id=block_id)
        return response.get("results", [])
    except Exception as e:
        print(f"Error fetching children for block {block_id}: {e}", file=sys.stderr)
        return []


def get_block_text(block: dict) -> str:
    """Extract plain text from a block"""
    block_type = block.get("type")
    type_obj = block.get(block_type, {})
    
    if isinstance(type_obj, dict):
        rich_text = type_obj.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in rich_text)
    return ""


def find_current_goals_parent(page_id: str) -> str:
    """
    Find the parent block containing the Current Goals section.
    In Company In A Box, this is usually inside column lists.
    Returns the block ID of the parent containing the "Current Goals" heading.
    """
    # BFS to find Current Goals
    queue = [page_id]
    visited = set()
    
    while queue:
        parent_id = queue.pop(0)
        if parent_id in visited:
            continue
        visited.add(parent_id)
        
        children = get_block_children(parent_id)
        for child in children:
            if child.get("type") in ["heading_1", "heading_2", "heading_3"]:
                text = get_block_text(child)
                if "current goals" in text.lower():
                    print(f"Found Current Goals in parent: {parent_id}")
                    return parent_id
        
        # Add children with has_children to queue
        for child in children:
            if child.get("has_children"):
                queue.append(child["id"])
    
    return None


def restructure_goals(parent_id: str) -> bool:
    """Main function to restructure the Current Goals section"""
    
    print("Starting Goals Restructure...")
    
    # Get children of parent
    children = get_block_children(parent_id)
    
    # Find Current Goals heading index
    goals_heading_idx = None
    for idx, child in enumerate(children):
        if child.get("type") in ["heading_1", "heading_2", "heading_3"]:
            text = get_block_text(child)
            if "current goals" in text.lower():
                goals_heading_idx = idx
                break
    
    if goals_heading_idx is None:
        print("Could not find Current Goals heading")
        return False
    
    # Get goal blocks (after Current Goals heading)
    goal_blocks = children[goals_heading_idx + 1:]
    
    # Find all goal heading_3 blocks and their descriptions
    # Also remove duplicates
    goals = []
    seen_goals = set()
    i = 0
    while i < len(goal_blocks):
        block = goal_blocks[i]
        if block.get("type") == "heading_3":
            heading_id = block["id"]
            heading_text = get_block_text(block)
            
            # Check for duplicates
            if heading_text in seen_goals:
                # Delete duplicate
                print(f"Removing duplicate goal: {heading_text}")
                try:
                    client.blocks.delete(block_id=heading_id)
                except Exception as e:
                    print(f"Error deleting duplicate: {e}")
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
                "heading_block": block,
                "heading_text": heading_text,
                "description_blocks": descriptions
            })
        else:
            i += 1
    
    print(f"Found {len(goals)} unique goals to convert")
    
    # Process each goal
    for goal in goals:
        heading_id = goal["heading_id"]
        heading_block = goal["heading_block"]
        descriptions = goal["description_blocks"]
        
        print(f"Converting: {goal['heading_text']}")
        
        # Convert heading to toggleable (if not already)
        heading_type = heading_block.get("type")
        heading_data = heading_block.get(heading_type, {})
        is_toggleable = heading_data.get("is_toggleable", False)
        
        if not is_toggleable:
            try:
                client.blocks.update(
                    block_id=heading_id,
                    **{heading_type: {**heading_data, "is_toggleable": True}}
                )
            except Exception as e:
                print(f"Error updating heading: {e}")
                return False
        else:
            print(f"  Already toggleable")
        
        # Move descriptions as children
        for desc_block in descriptions:
            desc_id = desc_block["id"]
            desc_type = desc_block.get("type")
            desc_data = desc_block.get(desc_type, {})
            
            # Add as child
            try:
                client.blocks.children.append(
                    block_id=heading_id,
                    children=[{
                        "type": desc_type,
                        desc_type: desc_data
                    }]
                )
            except Exception as e:
                print(f"Error adding child block: {e}")
                return False
            
            # Delete from current location
            try:
                client.blocks.delete(block_id=desc_id)
            except Exception as e:
                print(f"Error deleting block: {e}")
                return False
    
    # Check if new goal needs to be added
    new_goal_exists = False
    for goal in goals:
        if "digital transformation" in goal["heading_text"].lower():
            new_goal_exists = True
            break
    
    if not new_goal_exists:
        # Add new goal
        print("Adding new goal: 🔄 Digital Transformation Initiative")
        
        # Create new goal heading
        try:
            response = client.blocks.children.append(
                block_id=parent_id,
                children=[{
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": "🔄 Digital Transformation Initiative"}}],
                        "is_toggleable": True
                    }
                }]
            )
            
            if response.get("results"):
                new_goal_id = response["results"][0]["id"]
                print(f"Created new goal heading: {new_goal_id}")
                
                # Add description as child
                client.blocks.children.append(
                    block_id=new_goal_id,
                    children=[{
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": "Modernize our technology infrastructure and digitize key business processes to improve efficiency and customer experience."}}]
                        }
                    }]
                )
        except Exception as e:
            print(f"Error adding new goal: {e}")
            return False
    else:
        print("All 4 goals already exist and are toggleable")
    
    print("Goals restructure completed successfully!")
    return True


def main():
    """Main entry point"""
    # Find the Company In A Box page
    page_id = find_page("Company In A Box")
    
    if not page_id:
        print("Error: Could not find 'Company In A Box' page", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found Company In A Box page: {page_id}")
    
    # Find parent containing Current Goals
    parent_id = find_current_goals_parent(page_id)
    
    if not parent_id:
        print("Error: Could not find Current Goals section", file=sys.stderr)
        sys.exit(1)
    
    # Restructure the goals
    if restructure_goals(parent_id):
        print("Success!")
        sys.exit(0)
    else:
        print("Error: Failed to restructure goals", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
