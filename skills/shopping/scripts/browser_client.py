#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Client - Connect to Browser Server
============================================

This module provides a BrowserClient class that connects to the browser_server.py
daemon and executes browser operations on the persistent browser session.

Usage:
    from browser_client import BrowserClient
    
    async with BrowserClient() as browser:
        await browser.navigate("http://localhost:7770")
        snapshot = await browser.snapshot()
"""

import asyncio
import json
import os
from typing import Optional

# Server configuration (must match browser_server.py)
SOCKET_PATH = "/tmp/browser_server.sock"


def is_server_running() -> bool:
    """Check if browser server is running."""
    return os.path.exists(SOCKET_PATH)


class BrowserClient:
    """
    Client that connects to browser_server.py for browser operations.
    
    This provides the same API as BrowserTools but executes operations
    on the persistent browser session maintained by browser_server.py.
    """
    
    def __init__(self, fallback_to_standalone: bool = True):
        """
        Initialize browser client.
        
        Args:
            fallback_to_standalone: If True, fall back to standalone mode when server not running
        """
        self.fallback_to_standalone = fallback_to_standalone
        self._standalone_browser = None
        self._using_standalone = False
    
    async def __aenter__(self):
        """Enter async context - check server availability."""
        if not is_server_running():
            if self.fallback_to_standalone:
                print("⚠️  Browser server not running, using standalone mode")
                print("   For persistent browser, run: python browser_server.py")
                from utils import BrowserTools
                self._standalone_browser = BrowserTools(timeout=300)
                await self._standalone_browser.__aenter__()
                self._using_standalone = True
            else:
                raise ConnectionError("Browser server not running. Start with: python browser_server.py")
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context."""
        if self._standalone_browser:
            await self._standalone_browser.__aexit__(exc_type, exc, tb)
    
    async def _send_command(self, code: str) -> str:
        """Send command to browser server."""
        try:
            reader, writer = await asyncio.open_unix_connection(SOCKET_PATH)
            
            request = json.dumps({"command": code})
            writer.write(request.encode())
            await writer.drain()
            writer.write_eof()
            
            data = await reader.read()
            response = json.loads(data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response.get("success"):
                return response.get("result", "")
            else:
                raise Exception(response.get("error", "Unknown error"))
                
        except (ConnectionRefusedError, FileNotFoundError):
            raise ConnectionError("Browser server connection failed")
    
    async def _execute(self, method: str, **kwargs) -> Optional[str]:
        """Execute a browser method."""
        if self._using_standalone:
            # Use standalone browser
            func = getattr(self._standalone_browser, method)
            return await func(**kwargs)
        else:
            # Build and send command to server
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
            code = f"await browser.{method}({args_str})"
            return await self._send_command(code)
    
    # ==================== Navigation Tools ====================
    
    async def navigate(self, url: str) -> Optional[str]:
        """Navigate to a URL."""
        return await self._execute("navigate", url=url)
    
    async def navigate_back(self) -> Optional[str]:
        """Go back to the previous page."""
        return await self._execute("navigate_back")
    
    # ==================== Interaction Tools ====================
    
    async def click(self, ref: str, element: Optional[str] = None) -> Optional[str]:
        """Click on an element."""
        kwargs = {"ref": ref}
        if element:
            kwargs["element"] = element
        return await self._execute("click", **kwargs)
    
    async def type_text(self, ref: str, text: str, element: Optional[str] = None) -> Optional[str]:
        """Type text into an element."""
        kwargs = {"ref": ref, "text": text}
        if element:
            kwargs["element"] = element
        return await self._execute("type_text", **kwargs)
    
    async def fill_form(self, fields: list) -> Optional[str]:
        """Fill multiple form fields."""
        return await self._execute("fill_form", fields=fields)
    
    async def select_option(self, ref: str, element_desc: str, value: str) -> Optional[str]:
        """Select option in dropdown."""
        return await self._execute("select_option", ref=ref, element_desc=element_desc, value=value)
    
    async def press_key(self, key: str) -> Optional[str]:
        """Press a keyboard key."""
        return await self._execute("press_key", key=key)
    
    # ==================== Page State Tools ====================
    
    async def snapshot(self) -> Optional[str]:
        """Get page accessibility snapshot."""
        return await self._execute("snapshot")
    
    async def get_console_messages(self) -> Optional[str]:
        """Get console messages."""
        return await self._execute("get_console_messages")
    
    async def get_network_requests(self) -> Optional[str]:
        """Get network requests."""
        return await self._execute("get_network_requests")
    
    # ==================== Wait Tools ====================
    
    async def wait_for_time(self, seconds: int) -> Optional[str]:
        """Wait for specified time."""
        return await self._execute("wait_for_time", seconds=seconds)
    
    # ==================== Tab Management ====================
    
    async def list_tabs(self) -> Optional[str]:
        """List browser tabs."""
        return await self._execute("list_tabs")
    
    async def tab_new(self, url: Optional[str] = None) -> Optional[str]:
        """Open new tab."""
        kwargs = {}
        if url:
            kwargs["url"] = url
        return await self._execute("tab_new", **kwargs)
