#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Tools Wrapper
====================

This module provides a high-level wrapper around Notion API.
It simplifies common Notion operations and makes them reusable across different skills.

"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any

from notion_client import Client


class NotionTools:
    """
    High-level wrapper for Notion API operations.
    
    This class provides convenient methods for common Notion operations using the
    official notion_client Python library.
    """

    def __init__(self, api_key: str):
        """
        Initialize Notion tools.
        
        Args:
            api_key: Notion API key
        """
        self.api_key = api_key
        self.client = Client(auth=api_key)

    def search_page(self, query: str) -> Optional[Dict]:
        """
        Search for a page by name/query
        
        Args:
            query: Search query (page name or content)
            
        Returns:
            Dictionary with page information or None if not found
        """
        try:
            response = self.client.search(query=query, filter={"value": "page", "property": "object"})
            if response.get("results"):
                return response["results"][0]
            return None
        except Exception as e:
            print(f"Error searching for page: {e}")
            return None

    def get_block_children(self, block_id: str) -> List[Dict]:
        """
        Get children blocks of a specified block
        
        Args:
            block_id: Block ID
            
        Returns:
            List of child blocks
        """
        try:
            response = self.client.blocks.children.list(block_id)
            return response.get("results", [])
        except Exception as e:
            print(f"Error getting block children: {e}")
            return []

    def patch_block_children(
        self,
        block_id: str,
        children: List[Dict],
        after: Optional[str] = None
    ) -> Dict:
        """
        Add or update children blocks
        
        Args:
            block_id: Parent block ID
            children: List of children blocks to add
            after: Optional ID of block after which to insert
            
        Returns:
            Response from the API
        """
        try:
            # Notion API requires children to have proper structure
            # For column_list, children should be columns with proper structure
            formatted_children = []
            for child in children:
                if child.get("type") == "column_list":
                    # column_list needs children field with columns
                    formatted_children.append({
                        "type": "column_list",
                        "column_list": {
                            "children": []  # Start with empty list
                        }
                    })
                else:
                    formatted_children.append(child)
            
            args = {
                "block_id": block_id,
                "children": formatted_children
            }
            if after:
                args["after"] = after
            
            result = self.client.blocks.children.append(**args)
            
            # Return the first created child or the response
            if isinstance(result, dict):
                if "results" in result and result["results"]:
                    return result["results"][0]
                return result
            return {}
        except Exception as e:
            print(f"Error patching block children: {e}")
            return {}

    def find_page_by_title(self, title: str) -> Optional[Dict]:
        """
        Find a page by its exact title
        
        Args:
            title: Page title to search for
            
        Returns:
            Page dictionary or None if not found
        """
        page = self.search_page(title)
        if page:
            # Extract title from the page object
            page_title = self._get_page_title(page)
            if page_title == title:
                return page
        return None

    def find_block_by_heading_text(
        self,
        parent_block_id: str,
        heading_text: str
    ) -> Optional[Dict]:
        """
        Find a block by its heading text within a parent block
        
        Args:
            parent_block_id: Parent block ID
            heading_text: Heading text to search for
            
        Returns:
            Block dictionary or None if not found
        """
        children = self.get_block_children(parent_block_id)
        for child in children:
            block_type = child.get("type")
            if block_type and "heading" in block_type:
                # Extract text from heading
                content = child.get(block_type, {}).get("rich_text", [])
                text = "".join([item.get("text", {}).get("content", "") for item in content])
                if heading_text in text or text == heading_text:
                    return child
        return None

    def add_column_to_list(
        self,
        column_list_id: str,
        after_column_id: Optional[str] = None
    ) -> Dict:
        """
        Add a new column to a column_list block
        
        Args:
            column_list_id: Column list block ID
            after_column_id: Optional ID of column after which to insert
            
        Returns:
            New column block
        """
        new_column = {
            "type": "column",
            "column": {"children": []}
        }
        
        result = self.patch_block_children(
            column_list_id,
            [new_column],
            after=after_column_id
        )
        return result

    def add_text_to_block(
        self,
        block_id: str,
        text: str,
        bold: bool = False,
        italic: bool = False
    ) -> Dict:
        """
        Add text to a block
        
        Args:
            block_id: Block ID
            text: Text content
            bold: Whether text should be bold
            italic: Whether text should be italic
            
        Returns:
            Response from API
        """
        paragraph = {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text},
                        "annotations": {
                            "bold": bold,
                            "italic": italic
                        }
                    }
                ]
            }
        }
        
        result = self.patch_block_children(block_id, [paragraph])
        return result

    def add_code_block(
        self,
        block_id: str,
        code: str,
        language: str = "go",
        caption: Optional[str] = None
    ) -> Dict:
        """
        Add a code block to a block
        
        Args:
            block_id: Parent block ID
            code: Code content
            language: Programming language
            caption: Optional caption for the code block
            
        Returns:
            Response from API
        """
        code_block = {
            "type": "code",
            "code": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": code}
                    }
                ],
                "language": language
            }
        }
        
        if caption:
            code_block["code"]["caption"] = [
                {
                    "type": "text",
                    "text": {"content": caption}
                }
            ]
        
        result = self.patch_block_children(block_id, [code_block])
        return result

    def find_column_by_content(
        self,
        column_list_id: str,
        search_text: str
    ) -> Optional[Dict]:
        """
        Find a column by its content text
        
        Args:
            column_list_id: Column list block ID
            search_text: Text to search for in column
            
        Returns:
            Column block or None if not found
        """
        columns = self.get_block_children(column_list_id)
        for col in columns:
            if col.get("type") == "column":
                col_children = self.get_block_children(col.get("id"))
                for child in col_children:
                    if child.get("type") == "paragraph":
                        content = child.get("paragraph", {}).get("rich_text", [])
                        text = "".join([item.get("text", {}).get("content", "") for item in content])
                        if search_text in text:
                            return col
        return None

    def _get_page_title(self, page: Dict) -> str:
        """
        Extract title from a page object
        
        Args:
            page: Page object from Notion API
            
        Returns:
            Page title as string
        """
        properties = page.get("properties", {})
        title_prop = properties.get("title", {})
        title_content = title_prop.get("title", [])
        if title_content:
            return "".join([item.get("text", {}).get("content", "") for item in title_content])
        return ""
