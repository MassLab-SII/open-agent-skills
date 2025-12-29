#!/usr/bin/env python3
"""
Simple Update Items - Easy CLI Skill
====================================

Simplified version for easy LLM calling:
  python3 simple_update_items.py "Packing List" "Type=Clothes" "Packed=true"
  python3 simple_update_items.py "Packing List" "Name=SIM Card" "Packed=true"
  python3 simple_update_items.py "Packing List" "Name=Wallet" "Packed=true"
  python3 simple_update_items.py "Packing List" "Name=hat" "Packed=false"

Format:
  python3 simple_update_items.py <database_name> <criteria_key=value> <update_key=value> [<update_key=value>...]

Examples:
  python3 simple_update_items.py "Packing List" "Type=Clothes" "Packed=true"
  python3 simple_update_items.py "Packing List" "Name=hat" "Packed=false"
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


class SimpleUpdateItems:
    """
    Simple skill to update items in a Notion database.
    Takes criteria and updates as simple key=value pairs.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EVAL_NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in EVAL_NOTION_API_KEY environment variable")
    
    async def process(self, database_name: str, criteria_str: str, updates_str: List[str]) -> Dict[str, Any]:
        """
        Update items in database based on criteria and updates.
        
        Args:
            database_name: Name of the database
            criteria_str: Criteria as "key=value" string
            updates_str: List of update strings as ["key=value", "key=value", ...]
            
        Returns:
            Result dictionary
        """
        result = {
            "success": False,
            "database_id": None,
            "total_items": 0,
            "updated_count": 0,
            "updates_applied": [],
            "errors": []
        }
        
        try:
            async with NotionMCPTools(self.api_key, notion_version="2025-09-03") as mcp:
                # Step 1: Search for database
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
                    # Support both "database" and "data_source" object types
                    if obj_type in ["database", "data_source"]:
                        database = item
                        break
                
                if not database:
                    result["errors"].append(f"No database found for '{database_name}'")
                    return result
                
                database_id = database.get("id")
                result["database_id"] = database_id
                print(f"✓ Found database (ID: {database_id[:20]}...)")
                
                # Step 2: Query all items
                print(f"\n📍 Querying items from database")
                print("-" * 70)
                
                query_result = await mcp.query_database(database_id)
                if not query_result:
                    result["errors"].append("Failed to query database")
                    return result
                
                query_data = json.loads(query_result)
                all_items = query_data.get("results", [])
                result["total_items"] = len(all_items)
                print(f"✓ Retrieved {len(all_items)} items")
                
                # Step 3: Parse criteria
                print(f"\n📍 Parsing criteria: {criteria_str}")
                print("-" * 70)
                
                criteria = self._parse_key_value(criteria_str)
                if not criteria:
                    result["errors"].append(f"Invalid criteria format: {criteria_str}")
                    return result
                print(f"  Criteria: {criteria}")
                
                # Step 4: Parse updates
                print(f"\n📍 Parsing updates")
                print("-" * 70)
                
                updates = {}
                for update_str in updates_str:
                    parsed = self._parse_key_value(update_str)
                    if parsed:
                        updates.update(parsed)
                
                if not updates:
                    result["errors"].append("No valid updates specified")
                    return result
                print(f"  Updates: {updates}")
                
                # Step 5: Find and update matching items
                print(f"\n📍 Finding and updating matching items")
                print("-" * 70)
                
                matching_items = []
                for item in all_items:
                    if self._matches_criteria(item, criteria):
                        matching_items.append(item)
                
                print(f"  Found {len(matching_items)} matching items")
                
                # Update each matching item
                for item in matching_items:
                    item_id = item.get("id")
                    item_name = self._get_item_name(item)
                    
                    try:
                        # Prepare update payload
                        update_payload = self._prepare_update_payload(updates)
                        
                        # Apply update via MCP
                        await mcp.update_page_property(item_id, update_payload)
                        
                        result["updated_count"] += 1
                        result["updates_applied"].append({
                            "item_id": item_id,
                            "item_name": item_name,
                            "updates": updates
                        })
                        
                        print(f"  ✓ Updated: {item_name}")
                    
                    except Exception as e:
                        result["errors"].append(
                            f"Failed to update '{item_name}': {str(e)}"
                        )
                        print(f"  ✗ Error updating: {item_name} - {e}")
                
                result["success"] = True
                print(f"\n✓ Updated {result['updated_count']} items total")
        
        except Exception as e:
            result["errors"].append(f"Processing error: {str(e)}")
            print(f"❌ Error: {e}")
        
        return result
    
    def _parse_key_value(self, kvstr: str) -> Dict[str, Any]:
        """Parse key=value string to dictionary"""
        try:
            parts = kvstr.split("=", 1)
            if len(parts) != 2:
                return None
            
            key, value = parts[0].strip(), parts[1].strip()
            
            # Try to convert value to appropriate type
            if value.lower() == "true":
                return {key: True}
            elif value.lower() == "false":
                return {key: False}
            elif value.isdigit():
                return {key: int(value)}
            else:
                return {key: value}
        except:
            return None
    
    def _matches_criteria(self, item: Dict, criteria: Dict[str, Any]) -> bool:
        """Check if an item matches all criteria"""
        properties = item.get("properties", {})
        
        for prop_name, criteria_value in criteria.items():
            prop = properties.get(prop_name, {})
            item_value = self._extract_property_value(prop)
            
            # Handle different matching scenarios
            if isinstance(criteria_value, str):
                # Substring match for strings
                if isinstance(item_value, str):
                    if criteria_value.lower() not in item_value.lower():
                        return False
                elif isinstance(item_value, list):
                    # Check if any list item contains the criteria
                    if not any(criteria_value.lower() in str(v).lower() for v in item_value):
                        return False
                else:
                    if str(criteria_value) != str(item_value):
                        return False
            else:
                # Exact match for other types
                if item_value != criteria_value:
                    return False
        
        return True
    
    def _get_item_name(self, item: Dict) -> str:
        """Extract item name (usually from Name property)"""
        properties = item.get("properties", {})
        name_prop = properties.get("Name", {})
        
        if name_prop.get("type") == "title":
            title_array = name_prop.get("title", [])
            if title_array:
                return "".join([t.get("plain_text", "") for t in title_array])
        
        # Fallback: use first text property
        for prop_name, prop in properties.items():
            value = self._extract_property_value(prop)
            if isinstance(value, str) and value:
                return value
        
        return "Unknown"
    
    def _extract_property_value(self, prop: Dict) -> Any:
        """Extract value from any property type"""
        prop_type = prop.get("type")
        
        if prop_type == "title":
            title_array = prop.get("title", [])
            if title_array:
                return "".join([t.get("plain_text", "") for t in title_array])
        
        elif prop_type == "rich_text":
            text_array = prop.get("rich_text", [])
            if text_array:
                return "".join([t.get("plain_text", "") for t in text_array])
        
        elif prop_type == "select":
            select = prop.get("select", {})
            if select:
                return select.get("name")
        
        elif prop_type == "multi_select":
            multi_select = prop.get("multi_select", [])
            return [s.get("name") for s in multi_select] if multi_select else []
        
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        
        elif prop_type == "number":
            return prop.get("number")
        
        elif prop_type == "date":
            date = prop.get("date", {})
            return date.get("start") if date else None
        
        return None
    
    def _prepare_update_payload(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare update payload for Notion API"""
        payload = {}
        
        for key, value in updates.items():
            if isinstance(value, bool):
                # Checkbox property
                payload[key] = {
                    "checkbox": value
                }
            elif isinstance(value, (int, float)):
                # Number property
                payload[key] = {
                    "number": value
                }
            elif isinstance(value, str):
                # Try to detect if it's a select property
                payload[key] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": value
                            }
                        }
                    ]
                }
            else:
                # Default: treat as text
                payload[key] = {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": str(value)
                            }
                        }
                    ]
                }
        
        return payload


async def main():
    """Main CLI entry point"""
    try:
        if len(sys.argv) < 4:
            print("Usage: python3 simple_update_items.py <database_name> <criteria_key=value> <update_key=value> [<update_key=value>...]")
            print("\nExamples:")
            print('  python3 simple_update_items.py "Packing List" "Type=Clothes" "Packed=true"')
            print('  python3 simple_update_items.py "Packing List" "Name=SIM Card" "Packed=true"')
            print('  python3 simple_update_items.py "Packing List" "Name=Wallet" "Packed=true"')
            print('  python3 simple_update_items.py "Packing List" "Name=hat" "Packed=false"')
            return 1
        
        database_name = sys.argv[1]
        criteria_str = sys.argv[2]
        updates_str = sys.argv[3:]
        
        # Check for --json flag
        output_json = "--json" in updates_str
        if output_json:
            updates_str.remove("--json")
        
        # Extract API key from args or environment
        api_key = os.getenv("EVAL_NOTION_API_KEY")
        for i, arg in enumerate(sys.argv):
            if arg == "--api-key" and i + 1 < len(sys.argv):
                api_key = sys.argv[i + 1]
        
        skill = SimpleUpdateItems(api_key)
        
        result = await skill.process(
            database_name=database_name,
            criteria_str=criteria_str,
            updates_str=updates_str
        )
        
        # Output results
        if output_json:
            print(json.dumps(result, indent=2))
        else:
            print("\n" + "=" * 70)
            print("RESULT SUMMARY")
            print("=" * 70)
            print(f"Success: {result['success']}")
            print(f"Total Items: {result['total_items']}")
            print(f"Updated Count: {result['updated_count']}")
            
            if result['updates_applied']:
                print("\n📋 Updates Applied:")
                for update in result['updates_applied']:
                    print(f"  • {update['item_name']}: {update['updates']}")
            
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
