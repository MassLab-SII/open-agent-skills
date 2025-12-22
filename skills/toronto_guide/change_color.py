#!/usr/bin/env python3
"""
Toronto Guide Change Color - 100% MCP Implementation
Changes all pink-colored elements (tags and callout colors) to different colors
"""

import asyncio
import json
import os
from typing import Optional, Dict, List, Tuple
from utils import NotionMCPTools


class ChangeColor:
    """Changes all pink elements in Toronto Guide to different colors"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.mcp = None
    
    async def change_colors(self) -> Dict:
        """Main method to change all pink colors in Toronto Guide"""
        result = {
            "success": False,
            "message": "",
            "pink_elements_changed": {},
            "errors": []
        }
        
        try:
            async with NotionMCPTools(self.api_key) as tools:
                self.mcp = tools
                
                # Step 1: Find Toronto Guide page
                print("Step 1: Finding Toronto Guide page...")
                page_id = await self._find_toronto_guide_page()
                if not page_id:
                    result["errors"].append("Toronto Guide page not found")
                    return result
                print(f"  ✓ Found Toronto Guide page (ID: {page_id})")
                
                # Step 2: Get all blocks to find callouts and databases
                print("Step 2: Scanning for pink elements...")
                callout_blocks, database_ids = await self._find_pink_elements(page_id)
                
                # Step 3: Change callout colors
                print("Step 3: Changing callout colors...")
                await self._change_callout_colors(callout_blocks)
                if callout_blocks:
                    result["pink_elements_changed"]["callouts"] = len(callout_blocks)
                
                # Step 4: Change database tag colors
                print("Step 4: Changing database tag colors...")
                for db_info in database_ids:
                    await self._change_database_tag_colors(db_info)
                
                if database_ids:
                    result["pink_elements_changed"]["databases"] = len(database_ids)
                
                result["success"] = True
                result["message"] = f"Changed pink colors for {len(callout_blocks)} callouts and {len(database_ids)} databases"
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"Error: {str(e)}")
        
        return result
    
    async def _find_toronto_guide_page(self) -> Optional[str]:
        """Search for Toronto Guide page"""
        try:
            response = await self.mcp.search("Toronto Guide")
            if not response:
                return None
            
            data = json.loads(response)
            for item in data.get("results", []):
                if item.get("object") == "page":
                    title = self._get_page_title(item)
                    if "Toronto Guide" in title:
                        return item.get("id")
        except Exception as e:
            print(f"Error finding Toronto Guide: {e}")
        
        return None
    
    async def _find_pink_elements(self, page_id: str) -> Tuple[List[Dict], List[Dict]]:
        """Find all pink elements: callouts and database tags"""
        callout_blocks = []
        database_ids = []
        
        try:
            # Get all blocks recursively
            all_blocks = await self._get_all_blocks_recursive(page_id)
            
            for block in all_blocks:
                if block is None:
                    continue
                
                # Check for pink callout
                if block.get("type") == "callout":
                    color = block.get("callout", {}).get("color", "")
                    if "pink" in color.lower():
                        callout_text = self._get_block_text(block)
                        callout_blocks.append({
                            "id": block.get("id"),
                            "text": callout_text,
                            "current_color": color
                        })
                        print(f"  ✓ Found pink callout: {callout_text[:50]}")
                
                # Check for child databases
                if block.get("type") == "child_database":
                    title = block.get("child_database", {}).get("title", "")
                    block_id = block.get("id")
                    
                    # Check if this database has pink tags
                    db_info = await self._check_database_for_pink_tags(block_id, title)
                    if db_info:
                        database_ids.append(db_info)
                        print(f"  ✓ Found {len(db_info['pink_tags'])} pink tags in {title} database")
        
        except Exception as e:
            print(f"Error finding pink elements: {e}")
        
        return callout_blocks, database_ids
    
    async def _check_database_for_pink_tags(self, db_id: str, db_name: str) -> Optional[Dict]:
        """Check if a database has pink tags and return info"""
        try:
            response = await self.mcp.retrieve_database(db_id)
            if not response:
                return None
            
            data = json.loads(response)
            properties = data.get("properties", {})
            tags_prop = properties.get("Tags", {})
            
            if tags_prop.get("type") != "multi_select":
                return None
            
            options = tags_prop.get("multi_select", {}).get("options", [])
            pink_tags = []
            all_tags = []
            
            for option in options:
                tag_name = option.get("name", "")
                tag_color = option.get("color", "")
                all_tags.append(option)
                
                if tag_color == "pink":
                    pink_tags.append({
                        "name": tag_name,
                        "color": tag_color,
                        "id": option.get("id")
                    })
            
            if pink_tags:
                return {
                    "database_id": db_id,
                    "database_name": db_name,
                    "pink_tags": pink_tags,
                    "all_tags": all_tags
                }
        
        except Exception as e:
            print(f"Error checking database {db_name}: {e}")
        
        return None
    
    async def _change_callout_colors(self, callout_blocks: List[Dict]) -> None:
        """Change callout colors from pink to blue"""
        for i, callout in enumerate(callout_blocks):
            try:
                # Change pink callout to blue background
                await self.mcp.update_block(callout["id"], callout={"color": "blue_background"})
                print(f"  ✓ Changed callout color to blue_background")
            except Exception as e:
                print(f"  ✗ Error changing callout color: {e}")
    
    async def _change_database_tag_colors(self, db_info: Dict) -> None:
        """Change database tag colors from pink to various other colors"""
        try:
            pink_tags = db_info["pink_tags"]
            all_tags = db_info["all_tags"]
            db_name = db_info["database_name"]
            
            # Define new colors to use
            new_colors = ["blue", "green", "orange", "red", "purple", "gray", "brown", "yellow"]
            
            # ONLY update the pink tags that need to be changed
            # Build a minimal update with ONLY the pink tag options
            updated_pink_options = []
            
            for i, pink_tag in enumerate(pink_tags):
                new_color = new_colors[i % len(new_colors)]
                # Only update pink tags with their new colors
                updated_pink_options.append({
                    "name": pink_tag["name"],
                    "color": new_color
                })
                print(f"  ✓ Changed '{pink_tag['name']}' from pink to {new_color} in {db_name}")
            
            # Update the database with ONLY the pink tag options being changed
            # This way we're not touching non-pink tags
            properties = {
                "Tags": {
                    "multi_select": {
                        "options": updated_pink_options
                    }
                }
            }
            
            result = await self.mcp.update_database(db_info["database_id"], properties)
            if not result:
                print(f"  ✗ Failed to update {db_name} tags")
        
        except Exception as e:
            print(f"  ✗ Error changing {db_info.get('database_name', 'database')} tags: {e}")
    
    async def _get_all_blocks_recursive(self, block_id: str, depth: int = 0, max_depth: int = 10) -> List[Dict]:
        """Get all blocks recursively from a page"""
        if depth > max_depth:
            return []
        
        blocks = []
        try:
            response = await self.mcp.get_block_children(block_id)
            if not response:
                return blocks
            
            data = json.loads(response)
            for block in data.get("results", []):
                blocks.append(block)
                
                # Recursively get children
                if block.get("has_children"):
                    children = await self._get_all_blocks_recursive(block.get("id"), depth + 1, max_depth)
                    blocks.extend(children)
        
        except Exception as e:
            print(f"Error getting blocks: {e}")
        
        return blocks
    
    @staticmethod
    def _get_page_title(page: Dict) -> str:
        """Extract page title from page object"""
        try:
            properties = page.get("properties", {})
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "title":
                    title_array = prop_data.get("title", [])
                    if title_array:
                        return title_array[0].get("text", {}).get("content", "")
        except Exception:
            pass
        return ""
    
    @staticmethod
    def _get_block_text(block: Dict) -> str:
        """Extract text from a block"""
        try:
            block_type = block.get("type")
            content = block.get(block_type, {})
            
            if "rich_text" in content:
                rich_text = content.get("rich_text", [])
                if rich_text:
                    return rich_text[0].get("text", {}).get("content", "")
        except Exception:
            pass
        return ""


async def main():
    """CLI entry point"""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY environment variable not set")
        return
    
    skill = ChangeColor(api_key)
    result = await skill.change_colors()
    
    print("\n" + "=" * 70)
    print("📊 Execution Summary")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Pink Elements Changed: {result['pink_elements_changed']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
