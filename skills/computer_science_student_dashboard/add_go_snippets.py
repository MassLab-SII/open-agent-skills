#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Go Code Snippets to Computer Science Student Dashboard
===========================================================

This script finds the "Computer Science Student Dashboard" page in the MCPMark Eval Hub
and adds a Go column with code examples to the "Code Snippets" section.

The API key is automatically loaded from the .mcp_env file by the evaluation system.
This script is invoked automatically during pipeline evaluation.
"""

import json
import sys
import os
from typing import Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv
from utils import NotionTools

# Load environment variables from .mcp_env file
# Try multiple paths to find .mcp_env
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",  # skills/computer_science_student_dashboard/add_go_snippets.py -> .mcp_env
    Path.cwd() / ".mcp_env",  # Current working directory
    Path(".") / ".mcp_env",  # Relative path
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break


class GoCodeSnippetAdder:
    """Add Go code snippets to Notion page"""

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

    def __init__(self, api_key: str):
        """
        Initialize the Go snippet adder
        
        Args:
            api_key: Notion API key
        """
        self.api_key = api_key
        self.notion = NotionTools(api_key)

    def add_go_snippets(self) -> Dict:
        """
        Main workflow to add Go snippets to the dashboard
        
        Returns:
            Dictionary with success status and details
        """
        try:
            # Step 1: Search for the Computer Science Student Dashboard page
            print("\n" + "="*70)
            print("Step 1: Searching for 'Computer Science Student Dashboard' page")
            print("="*70)
            page = self.notion.search_page("Computer Science Student Dashboard")
            
            if not page:
                return {
                    "success": False,
                    "error": "Page 'Computer Science Student Dashboard' not found",
                    "output": ""
                }
            
            page_id = page.get("id")
            print(f"✓ Found page: {page.get('title', 'Unknown')} (ID: {page_id})")
            
            # Step 2: Get page children to find Code Snippets section
            print("\n" + "="*70)
            print("Step 2: Finding 'Code Snippets' section in the page")
            print("="*70)
            children = self.notion.get_block_children(page_id)
            
            code_snippets_heading = None
            code_snippets_id = None
            
            for child in children:
                block_type = child.get("type", "")
                if "heading" in block_type:
                    content = child.get(block_type, {}).get("rich_text", [])
                    text = "".join([item.get("text", {}).get("content", "") for item in content])
                    if "Code snippets" in text or "Code Snippets" in text:
                        code_snippets_heading = child
                        code_snippets_id = child.get("id")
                        print(f"✓ Found heading: '{text}' (ID: {code_snippets_id})")
                        break
            
            if not code_snippets_heading:
                return {
                    "success": False,
                    "error": "Code Snippets section not found",
                    "output": ""
                }
            
            # Step 3: Get the column_list - it could be either a child of heading or a sibling
            print("\n" + "="*70)
            print("Step 3: Finding column_list in Code Snippets section")
            print("="*70)
            
            # First, try to find column_list as a child of the heading
            snippet_children = self.notion.get_block_children(code_snippets_id)
            
            column_list = None
            column_list_id = None
            
            for child in snippet_children:
                if child.get("type") == "column_list":
                    column_list = child
                    column_list_id = child.get("id")
                    print(f"✓ Found column_list as child of heading (ID: {column_list_id})")
                    break
            
            # If not found as child, look for it as a sibling (next block after heading)
            if not column_list:
                print("  Column list not found as child of heading, checking page children...")
                page_children = self.notion.get_block_children(page_id)
                heading_found = False
                
                for i, child in enumerate(page_children):
                    if child.get("id") == code_snippets_id:
                        heading_found = True
                        # Check next blocks for column_list
                        for j in range(i + 1, len(page_children)):
                            next_child = page_children[j]
                            if next_child.get("type") == "column_list":
                                column_list = next_child
                                column_list_id = next_child.get("id")
                                print(f"✓ Found column_list as sibling of heading (ID: {column_list_id})")
                                break
                        break
                
                if not column_list:
                    return {
                        "success": False,
                        "error": "Column list not found near Code Snippets section. Page structure may differ from expected.",
                        "output": ""
                    }
            
            # Step 4: Get existing columns and their content
            print("\n" + "="*70)
            print("Step 4: Examining existing columns")
            print("="*70)
            columns = self.notion.get_block_children(column_list_id)
            print(f"✓ Found {len(columns)} columns")
            
            # Identify columns by their content
            column_info = {}
            python_column_id = None
            javascript_column_id = None
            
            for i, col in enumerate(columns):
                col_id = col.get("id")
                col_children = self.notion.get_block_children(col_id)
                
                # Get first paragraph text to identify column
                for child in col_children:
                    if child.get("type") == "paragraph":
                        content = child.get("paragraph", {}).get("rich_text", [])
                        text = "".join([item.get("text", {}).get("content", "") for item in content])
                        print(f"  Column {i+1}: {text} (ID: {col_id})")
                        
                        if text == "Python":
                            python_column_id = col_id
                        elif text == "JavaScript":
                            javascript_column_id = col_id
                        break
            
            # Step 5: Create new Go column after Python column
            print("\n" + "="*70)
            print("Step 5: Adding new Go column")
            print("="*70)
            
            new_column_response = self.notion.add_column_to_list(
                column_list_id,
                after_column_id=python_column_id
            )
            go_column_id = new_column_response.get("id")
            print(f"✓ Created new Go column (ID: {go_column_id})")
            
            # Step 6: Add Go heading to the new column
            print("\n" + "="*70)
            print("Step 6: Adding 'Go' heading to the column")
            print("="*70)
            
            self.notion.add_text_to_block(
                go_column_id,
                "Go",
                bold=True
            )
            print("✓ Added 'Go' heading (bold)")
            
            # Step 7: Add Go code examples
            print("\n" + "="*70)
            print("Step 7: Adding Go code examples")
            print("="*70)
            
            for example in self.GO_EXAMPLES:
                self.notion.add_code_block(
                    go_column_id,
                    example["code"],
                    language="go",
                    caption=example["caption"]
                )
                print(f"✓ Added code block: {example['caption']}")
            
            # Step 8: Verify the result
            print("\n" + "="*70)
            print("Step 8: Verifying the result")
            print("="*70)
            
            final_columns = self.notion.get_block_children(column_list_id)
            print(f"✓ Final column count: {len(final_columns)}")
            
            column_names = []
            for col in final_columns:
                col_children = self.notion.get_block_children(col.get("id"))
                for child in col_children:
                    if child.get("type") == "paragraph":
                        content = child.get("paragraph", {}).get("rich_text", [])
                        text = "".join([item.get("text", {}).get("content", "") for item in content])
                        column_names.append(text)
                        break
            
            print(f"✓ Column order: {', '.join(column_names)}")
            
            
            return {
                "success": True,
                "output": f"Successfully added Go code snippets to {page.get('title')}. Column order: {', '.join(column_names)}",
                "error": ""
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error during execution: {str(e)}",
                "output": ""
            }


def main():
    """Main entry point"""
    # Get API key from command line or environment
    api_key = None
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("NOTION_API_KEY")
        if not api_key:
            api_key = os.getenv("EVAL_NOTION_API_KEY")
        if not api_key:
            api_key = os.getenv("SOURCE_NOTION_API_KEY")
    
    if not api_key:
        print("Error: Notion API key not provided")
        print("Usage: python add_go_snippets.py <api_key>")
        print("Or set NOTION_API_KEY, EVAL_NOTION_API_KEY, or SOURCE_NOTION_API_KEY environment variable")
        sys.exit(1)
    
    adder = GoCodeSnippetAdder(api_key)
    result = adder.add_go_snippets()
    
    print("\n" + "="*70)
    if result["success"]:
        print("✅ Task completed successfully!")
        print(result["output"])
    else:
        print("❌ Task failed!")
        print(result["error"])
    print("="*70)
    
    return result


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result.get("success") else 1)
