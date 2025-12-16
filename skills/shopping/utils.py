#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Playwright Browser Tools Wrapper
=====================================

This module provides a high-level wrapper around MCP Playwright browser tools.
It simplifies common browser operations for web automation tasks like shopping.

"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Optional, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def print_result(name: str, result: Optional[str], max_len: int = 200):
    """Helper to print test result"""
    status = '✓' if result is not None else '✗'
    print(f"  {name}: {status}")
    if result:
        preview = result[:max_len] + "..." if len(result) > max_len else result
        print(f"    -> {preview}")
        
class MCPStdioServer:
    """Lightweight MCP Stdio Server wrapper"""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 120):
        self.params = StdioServerParameters(
            command=command, 
            args=args, 
            env={**os.environ, **(env or {})}
        )
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None

    async def __aenter__(self):
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(self.params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call the specified MCP tool"""
        result = await asyncio.wait_for(
            self.session.call_tool(name, arguments), 
            timeout=self.timeout
        )
        return result.model_dump()


class BrowserTools:
    """
    High-level wrapper for MCP Playwright browser tools.
    
    This class provides convenient methods for common browser operations using the
    MCP Playwright server.
    """
    
    def __init__(self, timeout: int = 120):
        """
        Initialize the browser tools.
        
        Args:
            timeout: Timeout for MCP operations in seconds
        """
        self.timeout = timeout
        self.mcp_server = MCPStdioServer(
            command="npx",
            args=["-y", "@playwright/mcp@latest"],
            timeout=timeout
        )
    
    async def __aenter__(self):
        """Enter async context manager"""
        await self.mcp_server.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context manager"""
        await self.mcp_server.__aexit__(exc_type, exc, tb)
    
    # ==================== Helper Methods ====================
    
    def _extract_text(self, result: dict) -> Optional[str]:
        """
        Extract text content from MCP result.
        
        Args:
            result: MCP call result dict
            
        Returns:
            Text content from result["content"][0]["text"], or None if not found
        """
        try:
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError):
            pass
        return None
    
    async def _call_tool(self, name: str, arguments: dict) -> Optional[str]:
        """
        Call MCP tool and extract text result.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Text content from result, or None if error
        """
        try:
            result = await self.mcp_server.call_tool(name, arguments)
            return self._extract_text(result)
        except Exception as e:
            print(f"Error calling {name}: {e}")
            return None
    
    # ==================== Navigation Tools ====================
    
    async def navigate(self, url: str) -> Optional[str]: #verified
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_navigate", {"url": url})
    
    async def navigate_back(self) -> Optional[str]: #verified
        """
        Go back to the previous page.
        
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_navigate_back", {})
    
    # ==================== Interaction Tools ====================
    
    async def click(self, ref: str, element: Optional[str] = None) -> Optional[str]: #verified
        """
        Perform click on a web page element.
        
        Args:
            ref: Element reference (e.g., "e31")
            element: Optional element description
            
        Returns:
            Result text, or None if error
        """
        args = {"ref": ref}
        if element:
            args["element"] = element
        return await self._call_tool("browser_click", args)
    
    async def type_text(self, ref: str, text: str, element: Optional[str] = None) -> Optional[str]: #verified
        """
        Type text into an editable element.
        
        Args:
            ref: Element reference
            text: Text to type
            element: Optional element description
            
        Returns:
            Result text, or None if error
        """
        args = {"ref": ref, "text": text}
        if element:
            args["element"] = element
        return await self._call_tool("browser_type", args)
    
    async def fill_form(self, fields: List[Dict[str, str]]) -> Optional[str]: #verified
        """
        Fill multiple form fields at once.
        
        Args:
            fields: List of dicts with 'ref' and 'value' keys
            
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_fill_form", {"fields": fields})
    
    # async def hover(self, ref: str, element: Optional[str] = None) -> Optional[str]:
    #     """
    #     Hover over an element on the page.
        
    #     Args:
    #         ref: Element reference
    #         element: Optional element description
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     args = {"ref": ref}
    #     if element:
    #         args["element"] = element
    #     return await self._call_tool("browser_hover", args)
    
    async def select_option(self, ref: str, element_desc: str, value: str) -> Optional[str]: #verified
        """
        Select an option in a dropdown.
        
        Args:
            ref: Element reference
            element_desc: Element description
            value: Option value to select
            
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_select_option", {"ref": ref, "element": element_desc, "values": [value]})
    
    async def press_key(self, key: str) -> Optional[str]: #verified
        """
        Press a key on the keyboard.
        
        Args:
            key: Key to press (e.g., "Enter", "Tab", "Escape")
            
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_press_key", {"key": key})
    
    # async def drag(self, source_ref: str, target_ref: str) -> Optional[str]:
    #     """
    #     Perform drag and drop between two elements.
        
    #     Args:
    #         source_ref: Source element reference
    #         target_ref: Target element reference
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     return await self._call_tool("browser_drag", {
    #         "sourceRef": source_ref, 
    #         "targetRef": target_ref
    #     })

    
    # ==================== Page State Tools ====================
    
    async def snapshot(self) -> Optional[str]: #verified
        """
        Capture accessibility snapshot of the current page.
        Better than screenshot for actions.
        
        Returns:
            Snapshot text, or None if error
        """
        return await self._call_tool("browser_snapshot", {})

    
    async def get_console_messages(self) -> Optional[str]: #verified
        """
        Returns all console messages from the page.
        
        Returns:
            Console messages text, or None if error
        """
        return await self._call_tool("browser_console_messages", {})
    
    async def get_network_requests(self) -> Optional[str]: #verified
        """
        Returns all network requests since loading the page.
        
        Returns:
            Network requests text, or None if error
        """
        return await self._call_tool("browser_network_requests", {})
    
    # ==================== Wait Tools ====================
    
    async def wait_for_time(self, seconds: int) -> Optional[str]: #verified
        """
        Wait for a specified time to pass.
        
        Args:
            seconds: Time to wait in seconds
            
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_wait_for", {"time": seconds})
    
    # ==================== Browser Management Tools ====================
    
    async def close(self) -> Optional[str]: #verified
        """
        Close the browser page.
        
        Returns:
            Result text, or None if error
        """
        return await self._call_tool("browser_close", {})
    
    # ==================== Tab Management Tools ====================
    
    async def list_tabs(self) -> Optional[str]: #verified
        """
        List all browser tabs.
        
        Returns:
            Tabs info text, or None if error
        """
        return await self._call_tool("browser_tabs", {"action": "list"})
    
    async def tab_new(self, url: Optional[str] = None) -> Optional[str]:
        """
        Create a new browser tab.
        
        Args:
            url: Optional URL to open in the new tab
            
        Returns:
            Result text, or None if error
        """
        args = {}
        if url:
            args["url"] = url
        return await self._call_tool("browser_tab_new", args)
    
    # async def close_tab(self, tab_id: Optional[str] = None) -> Optional[str]:
    #     """
    #     Close a browser tab.
        
    #     Args:
    #         tab_id: Optional tab ID to close (closes current if not specified)
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     args = {"action": "close"}
    #     if tab_id:
    #         args["tabId"] = tab_id
    #     return await self._call_tool("browser_tabs", args)
    
    # async def select_tab(self, tab_id: str) -> Optional[str]:
    #     """
    #     Select/switch to a browser tab.
        
    #     Args:
    #         tab_id: Tab ID to select
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     return await self._call_tool("browser_tabs", {"action": "select", "tabId": tab_id})

    
    # ==================== Advanced Tools ====================
    
    # async def file_upload(self, ref: str, files: List[str]) -> Optional[str]:
    #     """
    #     Upload one or multiple files.
        
    #     Args:
    #         ref: File input element reference
    #         files: List of file paths to upload
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     return await self._call_tool("browser_file_upload", {"ref": ref, "files": files})
    
    # async def handle_dialog(self, action: str, text: Optional[str] = None) -> Optional[str]:
    #     """
    #     Handle a dialog (alert, confirm, prompt).
        
    #     Args:
    #         action: Action to take ("accept" or "dismiss")
    #         text: Optional text to enter for prompt dialogs
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     args = {"action": action}
    #     if text:
    #         args["text"] = text
    #     return await self._call_tool("browser_handle_dialog", args)
    
    async def run_code(self, code: str) -> Optional[str]: #verified
        """
        Run Playwright code snippet directly.
        
        Args:
            code: Playwright code to execute
            
        Returns:
            Code execution result text, or None if error
        """
        return await self._call_tool("browser_run_code", {"code": code})
    
   