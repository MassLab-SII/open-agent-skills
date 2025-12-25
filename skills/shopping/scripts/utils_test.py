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
        args = {"ref": ref, "text": text, "submit": true}
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
    
    # async def create_tab(self, url: Optional[str] = None) -> Optional[str]:
    #     """
    #     Create a new browser tab.
        
    #     Args:
    #         url: Optional URL to open in the new tab
            
    #     Returns:
    #         Result text, or None if error
    #     """
    #     args = {"action": "create"}
    #     if url:
    #         args["url"] = url
    #     return await self._call_tool("browser_tabs", args)
    
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
    
   



# ==================== Test Main Function ====================

def print_result(name: str, result: Optional[str], max_len: int = 200):
    """Helper to print test result"""
    status = '✓' if result is not None else '✗'
    print(f"  {name}: {status}")
    if result:
        preview = result[:max_len] + "..." if len(result) > max_len else result
        print(f"    -> {preview}")


async def test_browser_tools():
    """
    Test ALL BrowserTools functions based on actual execution.log format.
    """
    print("=" * 60)
    print("BrowserTools Complete Test Suite")
    print("=" * 60)
    
    async with BrowserTools(timeout=120) as browser:
        
        # ==================== Navigation Tools ====================
        print("\n" + "=" * 40)
        print("[Navigation Tools]")
        print("=" * 40)
        
        # 1. navigate
        print("\n[1] navigate(url)")
        result = await browser.navigate("http://localhost:7770")
        print_result("navigate", result)
        
        # 2. navigate_back
        print("\n[2] navigate_back()")
        await browser.navigate("http://localhost:7770/customer/account/login/")
        result = await browser.navigate_back()
        print_result("navigate_back", result)
        
        # ==================== Page State Tools ====================
        print("\n" + "=" * 40)
        print("[Page State Tools]")
        print("=" * 40)
        
        # 3. snapshot
        print("\n[3] snapshot()")
        result = await browser.snapshot()
        print_result("snapshot", result, max_len=300)
        
        # 4. get_console_messages
        print("\n[4] get_console_messages()")
        result = await browser.get_console_messages()
        print_result("get_console_messages", result)
        
        # 5. get_network_requests
        print("\n[5] get_network_requests()")
        result = await browser.get_network_requests()
        print_result("get_network_requests", result)
        
        # ==================== Wait Tools ====================
        print("\n" + "=" * 40)
        print("[Wait Tools]")
        print("=" * 40)
        
        # 6. wait_for_time
        print("\n[6] wait_for_time(milliseconds)")
        result = await browser.wait_for_time(2)
        print_result("wait_for_time", result)
        
        # ==================== Interaction Tools ====================
        print("\n" + "=" * 40)
        print("[Interaction Tools]")
        print("=" * 40)
        
        # 导航到 Video Games 页面进行交互测试
        await browser.navigate("http://localhost:7770")
        await browser.wait_for_time(2)
        snapshot = await browser.snapshot()
        print(f"  (Got homepage snapshot, length: {len(snapshot) if snapshot else 0})")
        
        # 8. click - 点击 Video Games 菜单
        print("\n[8] click(ref, element)")
        result = await browser.click("e68", "Video Games menu item")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # 9. hover - 悬停在元素上
        print("\n[9] hover(ref, element)")
        snapshot = await browser.snapshot()
        result = await browser.hover("e94", "Sort By dropdown")
        print_result("hover", result)
        
        # 10. select_option - 选择排序方式
        print("\n[10] select_option(ref, element_desc, value)")
        result = await browser.select_option("e94", "Sort By dropdown", "Price")
        print_result("select_option", result)
        await browser.wait_for_time(2)
        
        # 11. type_text - 在搜索框输入
        print("\n[11] type_text(ref, text)")
        result = await browser.type_text("e30", "controller", "Search box")
        print_result("type_text", result)
        
        # 12. press_key - 按回车搜索
        print("\n[12] press_key(key)")
        result = await browser.press_key("Enter")
        print_result("press_key", result)
        await browser.wait_for_time(2)
        
        # 13. fill_form - 填写表单 (导航到结账页面测试)
        print("\n[13] fill_form(fields)")
        # 先添加商品到购物车
        await browser.navigate("http://localhost:7770")
        await browser.wait_for_time(2)
        snapshot = await browser.snapshot()
        # fill_form 需要特定页面，这里只测试格式
        result = await browser.fill_form([
            {"name": "Email Address", "type": "textbox", "ref": "e30", "value": "test@example.com"},
            {"name": "First Name", "type": "textbox", "ref": "e40", "value": "Test"}
        ])
        print_result("fill_form", result)
        
        # 14. drag - 拖拽 (需要特定页面支持)
        print("\n[14] drag(source_ref, target_ref)")
        result = await browser.drag("e30", "e40")
        print_result("drag", result)
        
        # ==================== Tab Management Tools ====================
        print("\n" + "=" * 40)
        print("[Tab Management Tools]")
        print("=" * 40)
        
        # 15. list_tabs
        print("\n[15] list_tabs()")
        result = await browser.list_tabs()
        print_result("list_tabs", result)
        
        # 16. create_tab
        print("\n[16] create_tab(url)")
        result = await browser.create_tab("http://localhost:7770/customer/account/login/")
        print_result("create_tab", result)
        
        # 17. select_tab
        print("\n[17] select_tab(tab_id)")
        result = await browser.select_tab("0")
        print_result("select_tab", result)
        
        # 18. close_tab
        print("\n[18] close_tab()")
        result = await browser.close_tab()
        print_result("close_tab", result)
        
        # ==================== Advanced Tools ====================
        print("\n" + "=" * 40)
        print("[Advanced Tools]")
        print("=" * 40)
        
        await browser.navigate("http://localhost:7770")
        await browser.wait_for_time(2)
        
        # 19. run_code - 运行 Playwright 代码
        print("\n[19] run_code(code)")
        code = """async (page) => {
  await page.getByRole('combobox', { name: 'Search' }).clear();
  await page.getByRole('combobox', { name: 'Search' }).fill('test');
}"""
        result = await browser.run_code(code)
        print_result("run_code", result)
        
        # 20. handle_dialog - 处理弹窗 (需要页面有弹窗)
        print("\n[20] handle_dialog(action)")
        result = await browser.handle_dialog("accept")
        print_result("handle_dialog", result)
        
        # 21. file_upload - 文件上传 (需要文件上传元素)
        print("\n[21] file_upload(ref, files)")
        result = await browser.file_upload("e100", ["/tmp/test.txt"])
        print_result("file_upload", result)
        
        # ==================== Browser Management Tools ====================
        print("\n" + "=" * 40)
        print("[Browser Management Tools]")
        print("=" * 40)
        
        # 22. close
        print("\n[22] close()")
        result = await browser.close()
        print_result("close", result)
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)



async def test_shopping_workflow():
    """
    Test a complete shopping workflow based on execution.log example.
    """
    print("=" * 60)
    print("Shopping Workflow Test (Based on execution.log)")
    print("=" * 60)
    
    async with BrowserTools(timeout=120) as browser:
        
        # Step 1: Navigate to homepage
        print("\n[Step 1] Navigate to homepage...")
        result = await browser.navigate("http://localhost:7770")
        print_result("navigate", result, max_len=100)
        
        # Step 2: Take snapshot
        print("\n[Step 2] Take snapshot...")
        snapshot = await browser.snapshot()
        print_result("snapshot", snapshot, max_len=300)
        
        # Step 3: Click Video Games menu
        print("\n[Step 3] Click Video Games menu...")
        result = await browser.click("e68", "Video Games menu item")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 4: Take snapshot of Video Games page
        print("\n[Step 4] Snapshot Video Games page...")
        snapshot = await browser.snapshot()
        print_result("snapshot", snapshot, max_len=300)
        
        # Step 5: Click Page 2
        print("\n[Step 5] Click Page 2...")
        result = await browser.click("e419", "Page 2 link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 6: Go back to Page 1
        print("\n[Step 6] Click Page 1...")
        result = await browser.click("e388", "Page 1 link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 7: Sort by Price
        print("\n[Step 7] Sort by Price...")
        result = await browser.select_option("e94", "Sort By dropdown", "Price")
        print_result("select_option", result)
        await browser.wait_for_time(2)
        
        # Step 8: Click on first product
        print("\n[Step 8] Click first product...")
        snapshot = await browser.snapshot()
        result = await browser.click("e150", "First product link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 9: Search for product by SKU
        print("\n[Step 9] Search for SKU...")
        result = await browser.type_text("e30", "B07D6LSCXZ", "Search box")
        print_result("type_text", result)
        result = await browser.press_key("Enter")
        print_result("press_key (Enter)", result)
        await browser.wait_for_time(2)
        
        # Step 10: Click on search result
        print("\n[Step 10] Click search result...")
        snapshot = await browser.snapshot()
        result = await browser.click("e108", "N64 Controller product link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 11: Update quantity
        print("\n[Step 11] Update quantity to 3...")
        result = await browser.type_text("e113", "3", "Quantity spinbutton")
        print_result("type_text", result)
        
        # Step 12: Add to cart
        print("\n[Step 12] Add to cart...")
        result = await browser.click("e115", "Add to Cart button")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 13: Add to compare
        print("\n[Step 13] Search and add to compare...")
        result = await browser.type_text("e30", "B071DR5V1K", "Search box")
        print_result("type_text", result)
        result = await browser.press_key("Enter")
        await browser.wait_for_time(2)
        result = await browser.click("e131", "Add to Compare button")
        print_result("click (Add to Compare)", result)
        
        # Step 14: Run Playwright code to clear and search
        print("\n[Step 14] Run Playwright code...")
        code = """async (page) => {
  await page.getByRole('combobox', { name: '\\ue615 Search' }).clear();
  await page.getByRole('combobox', { name: '\\ue615 Search' }).fill('B082LZ4451');
  await page.getByRole('combobox', { name: '\\ue615 Search' }).press('Enter');
}"""
        result = await browser.run_code(code)
        print_result("run_code", result)
        await browser.wait_for_time(2)
        
        # Step 15: Add second product to compare
        print("\n[Step 15] Add second product to compare...")
        result = await browser.click("e125", "Add to Compare button")
        print_result("click", result)
        
        # Step 16: Go to compare page
        print("\n[Step 16] Go to compare page...")
        result = await browser.click("e156", "Compare link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 17: Go to cart
        print("\n[Step 17] Go to cart...")
        result = await browser.click("e23", "My Cart link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 18: View and Edit Cart
        print("\n[Step 18] View and Edit Cart...")
        result = await browser.click("e321", "View and Edit Cart link")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 19: Update quantity to 5
        print("\n[Step 19] Update quantity to 5...")
        result = await browser.type_text("e141", "5", "Quantity spinbutton")
        print_result("type_text", result)
        result = await browser.click("e152", "Update Shopping Cart button")
        print_result("click (Update)", result)
        await browser.wait_for_time(2)
        
        # Step 20: Proceed to checkout
        print("\n[Step 20] Proceed to checkout...")
        result = await browser.click("e110", "Proceed to Checkout button")
        print_result("click", result)
        await browser.wait_for_time(2)
        
        # Step 21: Fill checkout form
        print("\n[Step 21] Fill checkout form...")
        result = await browser.fill_form([
            {"name": "Email Address", "type": "textbox", "ref": "e30", "value": "test.buyer@example.com"},
            {"name": "First Name", "type": "textbox", "ref": "e40", "value": "Alice"},
            {"name": "Last Name", "type": "textbox", "ref": "e44", "value": "Johnson"},
            {"name": "Street Address Line 1", "type": "textbox", "ref": "e55", "value": "456 Oak Avenue"},
            {"name": "State/Province", "type": "combobox", "ref": "e67", "value": "California"},
            {"name": "City", "type": "textbox", "ref": "e71", "value": "San Francisco"},
            {"name": "Zip/Postal Code", "type": "textbox", "ref": "e75", "value": "94102"},
            {"name": "Phone Number", "type": "textbox", "ref": "e79", "value": "415-555-0123"}
        ])
        print_result("fill_form", result)
        
        # Step 22: Final snapshot
        print("\n[Step 22] Final snapshot...")
        snapshot = await browser.snapshot()
        print_result("snapshot", snapshot, max_len=500)
        
        # Close browser
        print("\n[Done] Close browser...")
        await browser.close()
    
    print("\n" + "=" * 60)
    print("Workflow test completed!")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    import os
    import debugpy
    debugpy.listen(("localhost", 5678))
    print("⏳ 等待调试器附加...")
    debugpy.wait_for_client()
    print("🚀 调试器已附加！继续执行...")
    
    print("BrowserTools Test Runner")
    print("-" * 30)
    print("Usage:")
    print("  python utils.py          - Run complete tool tests")
    print("  python utils.py workflow - Run shopping workflow test")
    print("-" * 30)
    
    if len(sys.argv) > 1 and sys.argv[1] == "workflow":
        asyncio.run(test_shopping_workflow())
    else:
        asyncio.run(test_browser_tools())
        # asyncio.run(test_create_tab_close_tab_select_tab())
