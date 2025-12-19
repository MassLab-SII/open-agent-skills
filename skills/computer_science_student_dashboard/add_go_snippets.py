#!/usr/bin/env python3
"""
Add Go Code Snippets to Computer Science Student Dashboard
===========================================================

This script finds the "Computer Science Student Dashboard" page in Notion
and adds a Go column with code examples to the "Code Snippets" section.

Uses 100% MCP tools for all Notion operations.
The API key is automatically loaded from environment variables.
"""

import asyncio
import json
import re
import sys
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from dotenv import load_dotenv
from utils import NotionMCPTools

# Load environment variables from .mcp_env file
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break


# Go code examples to add
GO_EXAMPLES = [
    {
        "caption": "Basic Go program",
        "code": """package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}"""
    },
    {
        "caption": "For loop in Go",
        "code": """for i := 0; i < 5; i++ {
    fmt.Println(i)
}"""
    },
    {
        "caption": "Function definition in Go",
        "code": """func add(a, b int) int {
    return a + b
}"""
    }
]


def extract_page_id_from_json(result_text: str) -> Optional[str]:
    """Extract page/block ID from MCP result JSON"""
    if not result_text:
        return None
    try:
        data = json.loads(result_text)
        if "id" in data:
            return data["id"]
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Try regex fallback
    match = re.search(r'"id":"([^"]+)"', result_text)
    return match.group(1) if match else None


def parse_block_response(response_text: str) -> List[Dict]:
    """Parse block response from MCP API"""
    if not response_text:
        return []
    
    try:
        data = json.loads(response_text)
        if isinstance(data, dict):
            results = data.get("results", [])
            if results:
                return results
        return [data] if isinstance(data, dict) and "type" in data else []
    except (json.JSONDecodeError, TypeError):
        return []


def find_heading_with_text(blocks: List[Dict], search_text: str) -> Optional[Dict]:
    """Find a heading block containing specific text"""
    for block in blocks:
        block_type = block.get("type", "")
        if "heading" in block_type:
            content = block.get(block_type, {}).get("rich_text", [])
            text = "".join([item.get("text", {}).get("content", "") for item in content])
            if search_text in text or text == search_text:
                return block
    return None


def find_column_list(blocks: List[Dict]) -> Optional[Dict]:
    """Find column_list block in blocks"""
    for block in blocks:
        if block.get("type") == "column_list":
            return block
    return None


def find_column_by_header_text(columns: List[Dict], search_text: str) -> Optional[Dict]:
    """Find a column by its header text"""
    for col in columns:
        if col.get("type") == "column":
            col_id = col.get("id")
            col_children = col.get("children", [])
            for child in col_children:
                if child.get("type") == "paragraph":
                    content = child.get("paragraph", {}).get("rich_text", [])
                    text = "".join([item.get("text", {}).get("content", "") for item in content])
                    if text == search_text:
                        return col
    return None


async def add_go_snippets_skill(api_key: str) -> Dict:
    """
    Main skill execution - Add Go code snippets using 100% MCP
    
    Args:
        api_key: Notion API key
        
    Returns:
        Dictionary with success status and results
    """
    
    print("\n" + "=" * 70)
    print("🚀 Add Go Code Snippets Skill - 100% MCP Implementation")
    print("=" * 70)
    
    async with NotionMCPTools(api_key) as mcp:
        
        # Step 1: Search for the Computer Science Student Dashboard page
        print("\n📍 Step 1: Searching for 'Computer Science Student Dashboard' page")
        print("-" * 70)
        
        search_result = await mcp.search("Computer Science Student Dashboard")
        if not search_result:
            print("❌ Search failed or page not found")
            return {
                "success": False,
                "error": "Failed to search for page",
                "output": ""
            }
        
        try:
            search_data = json.loads(search_result)
            if not search_data.get("results"):
                return {
                    "success": False,
                    "error": "Page 'Computer Science Student Dashboard' not found",
                    "output": ""
                }
            
            page_info = search_data["results"][0]
            page_id = page_info.get("id")
            print(f"✓ Found page (ID: {page_id})")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            return {
                "success": False,
                "error": f"Failed to parse search results: {e}",
                "output": ""
            }
        
        # Step 2: Get page children to find Code Snippets section
        print("\n📍 Step 2: Finding 'Code Snippets' section")
        print("-" * 70)
        
        page_children_result = await mcp.get_block_children(page_id)
        if not page_children_result:
            return {
                "success": False,
                "error": "Failed to fetch page children",
                "output": ""
            }
        
        try:
            page_children_data = json.loads(page_children_result)
            page_blocks = page_children_data.get("results", [])
        except (json.JSONDecodeError, KeyError):
            return {
                "success": False,
                "error": "Failed to parse page children",
                "output": ""
            }
        
        # Find Code Snippets heading
        code_snippets_heading = find_heading_with_text(page_blocks, "Code snippet")
        if not code_snippets_heading:
            return {
                "success": False,
                "error": "Code Snippets section not found",
                "output": ""
            }
        
        heading_id = code_snippets_heading.get("id")
        print(f"✓ Found 'Code Snippets' heading (ID: {heading_id})")
        
        # Step 3: Find column_list near the Code Snippets heading
        print("\n📍 Step 3: Finding column_list block")
        print("-" * 70)
        
        # First try to get children of the heading
        heading_children_result = await mcp.get_block_children(heading_id)
        column_list_id = None
        
        try:
            heading_children_data = json.loads(heading_children_result) if heading_children_result else {}
            heading_blocks = heading_children_data.get("results", [])
            
            for block in heading_blocks:
                if block.get("type") == "column_list":
                    column_list_id = block.get("id")
                    print(f"✓ Found column_list as child of heading (ID: {column_list_id})")
                    break
        except (json.JSONDecodeError, KeyError):
            pass
        
        # If not found as child, look for it as sibling in page
        if not column_list_id:
            print("  Looking for column_list as sibling...")
            heading_index = None
            for i, block in enumerate(page_blocks):
                if block.get("id") == heading_id:
                    heading_index = i
                    break
            
            if heading_index is not None:
                for i in range(heading_index + 1, len(page_blocks)):
                    if page_blocks[i].get("type") == "column_list":
                        column_list_id = page_blocks[i].get("id")
                        print(f"✓ Found column_list as sibling (ID: {column_list_id})")
                        break
        
        if not column_list_id:
            return {
                "success": False,
                "error": "Column list block not found",
                "output": ""
            }
        
        # Step 4: Examine existing columns
        print("\n📍 Step 4: Examining existing columns")
        print("-" * 70)
        
        columns_result = await mcp.get_block_children(column_list_id)
        if not columns_result:
            return {
                "success": False,
                "error": "Failed to fetch column list children",
                "output": ""
            }
        
        try:
            columns_data = json.loads(columns_result)
            columns = columns_data.get("results", [])
        except (json.JSONDecodeError, KeyError):
            return {
                "success": False,
                "error": "Failed to parse column list",
                "output": ""
            }
        
        print(f"✓ Found {len(columns)} existing columns")
        
        # Identify columns and find Python column
        python_column_id = None
        column_names = []
        
        for i, col in enumerate(columns):
            if col.get("type") == "column":
                col_id = col.get("id")
                col_children_result = await mcp.get_block_children(col_id)
                
                if col_children_result:
                    try:
                        col_children_data = json.loads(col_children_result)
                        col_children = col_children_data.get("results", [])
                        
                        # Find header text
                        for child in col_children:
                            if child.get("type") == "paragraph":
                                content = child.get("paragraph", {}).get("rich_text", [])
                                text = "".join([item.get("text", {}).get("content", "") for item in content])
                                print(f"  Column {i+1}: {text} (ID: {col_id})")
                                column_names.append(text)
                                
                                if text == "Python":
                                    python_column_id = col_id
                                break
                    except (json.JSONDecodeError, KeyError):
                        pass
        
        if not python_column_id:
            print("  ⚠️ Warning: Python column not found, will append to end")
        
        # Step 5: Add new Go column
        print("\n📍 Step 5: Adding new Go column")
        print("-" * 70)
        
        add_column_result = await mcp.add_column(column_list_id, after=python_column_id)
        if not add_column_result:
            return {
                "success": False,
                "error": "Failed to add new column",
                "output": ""
            }
        
        go_column_id = extract_page_id_from_json(add_column_result)
        if not go_column_id:
            return {
                "success": False,
                "error": "Could not extract Go column ID",
                "output": ""
            }
        
        print(f"✓ Created new Go column (ID: {go_column_id})")
        
        # Step 6: Add Go heading to the column
        print("\n📍 Step 6: Adding 'Go' heading")
        print("-" * 70)
        
        heading_result = await mcp.add_paragraph(go_column_id, "Go", bold=True)
        if heading_result:
            print("✓ Added 'Go' heading (bold)")
        
        # Step 7: Add Go code examples
        print("\n📍 Step 7: Adding Go code examples")
        print("-" * 70)
        
        for example in GO_EXAMPLES:
            code_result = await mcp.add_code_block(
                go_column_id,
                example["code"],
                language="go",
                caption=example["caption"]
            )
            if code_result:
                print(f"✓ Added: {example['caption']}")
        
        # Step 8: Verify the result
        print("\n📍 Step 8: Verifying final result")
        print("-" * 70)
        
        final_columns_result = await mcp.get_block_children(column_list_id)
        if final_columns_result:
            try:
                final_data = json.loads(final_columns_result)
                final_columns = final_data.get("results", [])
                
                final_column_names = []
                for col in final_columns:
                    if col.get("type") == "column":
                        col_children_result = await mcp.get_block_children(col.get("id"))
                        if col_children_result:
                            col_children_data = json.loads(col_children_result)
                            col_children = col_children_data.get("results", [])
                            
                            for child in col_children:
                                if child.get("type") == "paragraph":
                                    content = child.get("paragraph", {}).get("rich_text", [])
                                    text = "".join([item.get("text", {}).get("content", "") for item in content])
                                    final_column_names.append(text)
                                    break
                
                print(f"✓ Final column order: {', '.join(final_column_names)}")
                
                return {
                    "success": True,
                    "output": f"Successfully added Go code snippets. Column order: {', '.join(final_column_names)}",
                    "error": ""
                }
            except (json.JSONDecodeError, KeyError):
                return {
                    "success": True,
                    "output": "Successfully added Go code snippets",
                    "error": ""
                }
        
        return {
            "success": True,
            "output": "Successfully added Go code snippets",
            "error": ""
        }


async def main():
    """Main entry point"""
    api_key = None
    
    # Try to get API key from various sources
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("NOTION_API_KEY") or \
                  os.getenv("EVAL_NOTION_API_KEY") or \
                  os.getenv("SOURCE_NOTION_API_KEY")
    
    if not api_key:
        print("❌ Error: Notion API key not provided")
        print("Usage: python add_go_snippets.py <api_key>")
        print("Or set NOTION_API_KEY, EVAL_NOTION_API_KEY, or SOURCE_NOTION_API_KEY")
        return {
            "success": False,
            "error": "API key not found",
            "output": ""
        }
    
    result = await add_go_snippets_skill(api_key)
    
    print("\n" + "=" * 70)
    if result.get("success"):
        print("✅ Task completed successfully!")
        if result.get("output"):
            print(result["output"])
    else:
        print("❌ Task failed!")
        if result.get("error"):
            print(result["error"])
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result.get("success") else 1)
