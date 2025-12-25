"""database_query_archive_skill.py

Generic skill to search for a database, query it with a filter, 
and archive items that match additional Python-side logic.

Composes: search -> query_database -> patch_page (archive)
"""

import os
import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable

# Support both direct execution and module import
try:
    from ..utils import NotionMCPTools, parse_time_to_minutes, extract_page_property
except (ImportError, ValueError):
    sys.path.append(str(Path(__file__).parent.parent))
    from utils import NotionMCPTools, parse_time_to_minutes, extract_page_property


async def run(
    api_key: str, 
    database_name: str, 
    query_filter: Dict[str, Any] = None,
    python_filter: Callable[[Dict[str, Any]], bool] = None
) -> dict:
    async with NotionMCPTools(api_key) as mcp:
        # 1. Search for database
        search_result = await mcp.search(database_name)
        if not search_result:
            return {"success": False, "error": f"Database '{database_name}' not found"}
        
        search_data = json.loads(search_result)
        db_id = None
        for item in search_data.get("results", []):
            if item.get("object") == "database":
                db_id = item.get("id")
                break
        
        if not db_id:
            return {"success": False, "error": f"Database '{database_name}' not found in search results"}

        # 2. Query database
        query_result = await mcp.query_database(db_id, filter_obj=query_filter)
        if not query_result:
            return {"success": False, "error": "Failed to query database"}
        
        query_data = json.loads(query_result)
        items = query_data.get("results", [])
        
        # 3. Filter and Archive
        archived_count = 0
        archived_items = []
        errors = []

        for item in items:
            # Apply python-side filter if provided
            if python_filter and not python_filter(item):
                continue
            
            item_id = item.get("id")
            try:
                await mcp.patch_page(item_id, archived=True)
                archived_count += 1
                # Extract name for reporting
                name = extract_page_property(item, "Name") or extract_page_property(item, "Title") or item_id
                archived_items.append(name)
            except Exception as e:
                errors.append(f"Failed to archive {item_id}: {str(e)}")

        return {
            "success": True,
            "database_id": db_id,
            "archived_count": archived_count,
            "archived_items": archived_items,
            "errors": errors
        }

# Example usage for CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch archive database items")
    parser.add_argument("--api-key", default=os.getenv("EVAL_NOTION_API_KEY"))
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--filter-prop", help="Property name to filter by")
    parser.add_argument("--filter-val", help="Value to filter by")
    parser.add_argument("--python-filter", help="Python expression for filtering (variable 'item' is available)")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: API key required")
        exit(1)

    q_filter = None
    if args.filter_prop and args.filter_val:
        q_filter = {"property": args.filter_prop, "select": {"equals": args.filter_val}}

    # Create a filter function from the string expression if provided
    py_filter = None
    if args.python_filter:
        def py_filter(item):
            # Provide helper functions in the eval context
            context = {
                "item": item,
                "extract_page_property": extract_page_property,
                "parse_time_to_minutes": parse_time_to_minutes
            }
            try:
                return eval(args.python_filter, {"__builtins__": None}, context)
            except Exception as e:
                print(f"Filter error: {e}")
                return False

    asyncio.run(run(args.api_key, args.db, query_filter=q_filter, python_filter=py_filter))
