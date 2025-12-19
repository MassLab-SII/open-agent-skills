#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Notion API Tools Wrapper
============================

这个模块提供对 MCP Notion 工具的高级包装。
完全参考 shopping/utils.py 的模式，但用于 Notion API 操作。

MCP 服务器: @notionhq/notion-mcp-server
协议: stdio (标准输入输出)
"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Optional, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def print_result(name: str, result: Optional[str], max_len: int = 200):
    """辅助函数：打印测试结果"""
    status = '✓' if result is not None else '✗'
    print(f"  {name}: {status}")
    if result:
        preview = result[:max_len] + "..." if len(result) > max_len else result
        print(f"    -> {preview}")


class MCPStdioServer:
    """轻量级 MCP Stdio 服务器包装"""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 120):
        """
        初始化 MCP 服务器
        
        Args:
            command: 要执行的命令 (如 "npx")
            args: 命令参数列表
            env: 环境变量字典
            timeout: 操作超时时间 (秒)
        """
        self.params = StdioServerParameters(
            command=command, 
            args=args, 
            env={**os.environ, **(env or {})}
        )
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(self.params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """异步上下文管理器出口"""
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """
        调用指定的 MCP 工具
        
        Args:
            name: 工具名称
            arguments: 工具参数字典
            
        Returns:
            工具执行结果
        """
        result = await asyncio.wait_for(
            self.session.call_tool(name, arguments), 
            timeout=self.timeout
        )
        return result.model_dump()


class NotionMCPClient:
    """
    Notion MCP 工具的高级包装
    
    提供了对 Notion API 的便捷方法，通过 MCP 服务器执行。
    
    支持的 MCP 工具:
    - API-post-search: 搜索页面和数据库
    - API-post-database-query: 查询数据库
    - API-post-page: 创建新页面
    - API-patch-page: 更新页面属性
    - API-patch-block-children: 更新块内容
    - API-retrieve-a-page: 获取页面详情
    - API-get-block-children: 获取页面的块内容
    """
    
    def __init__(self, notion_api_key: str, timeout: int = 120):
        """
        初始化 Notion MCP 客户端
        
        Args:
            notion_api_key: Notion API 密钥
            timeout: MCP 操作超时时间 (秒)
        """
        self.api_key = notion_api_key
        self.timeout = timeout
        self.mcp_server = MCPStdioServer(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={"OPENAPI_MCP_HEADERS": f'{{"Authorization": "Bearer {notion_api_key}", "Notion-Version": "2022-06-28"}}'},
            timeout=timeout
        )
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.mcp_server.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """异步上下文管理器出口"""
        await self.mcp_server.__aexit__(exc_type, exc, tb)
    
    # ==================== 辅助方法 ====================
    
    def _extract_text(self, result: dict) -> Optional[str]:
        """
        从 MCP 结果中提取文本内容
        
        Args:
            result: MCP 调用结果字典
            
        Returns:
            结果中的文本内容，如果找不到返回 None
        """
        try:
            content = result.get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", "")
        except (KeyError, IndexError, TypeError):
            pass
        return None
    
    def _extract_full_result(self, result: dict) -> dict:
        """
        提取完整的 MCP 结果（用于需要完整数据的操作）
        
        Args:
            result: MCP 调用结果字典
            
        Returns:
            完整的结果字典
        """
        return result
    
    async def _call_tool(self, name: str, arguments: dict) -> Optional[str]:
        """
        调用 MCP 工具并提取文本结果
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            结果文本，如果出错返回 None
        """
        try:
            result = await self.mcp_server.call_tool(name, arguments)
            return self._extract_text(result)
        except Exception as e:
            print(f"❌ 调用 {name} 出错: {e}")
            return None
    
    async def _call_tool_raw(self, name: str, arguments: dict) -> dict:
        """
        调用 MCP 工具并返回原始结果
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            原始的 MCP 结果
        """
        try:
            result = await self.mcp_server.call_tool(name, arguments)
            return result
        except Exception as e:
            print(f"❌ 调用 {name} 出错: {e}")
            return {"error": str(e)}
    
    # ==================== 搜索和查询 ====================
    
    async def search_page(self, query: str, object_type: Optional[str] = None) -> Optional[str]:
        """
        搜索页面或数据库
        
        Args:
            query: 搜索查询字符串
            object_type: 可选的对象类型 ("page" 或 "database")
            
        Returns:
            搜索结果文本，如果出错返回 None
        """
        args = {"query": query}
        if object_type:
            args["filter"] = {"object": object_type}
        
        return await self._call_tool("API-post-search", args)
    
    async def query_database(self, database_id: str, filter_obj: Optional[dict] = None, 
                            sorts: Optional[list] = None) -> Optional[str]:
        """
        查询数据库
        
        Args:
            database_id: 数据库 ID
            filter_obj: 可选的过滤条件
            sorts: 可选的排序条件
            
        Returns:
            查询结果文本，如果出错返回 None
        """
        args = {
            "database_id": database_id,
            "sort": sorts if sorts else [],
            "filter": filter_obj if filter_obj else {}
        }
        
        return await self._call_tool("API-post-database-query", args)
    
    # ==================== 页面操作 ====================
    
    async def create_page(self, parent_id: str, title: str, 
                         properties: Optional[dict] = None, 
                         icon: Optional[str] = None,
                         children: Optional[list] = None) -> Optional[str]:
        """
        创建新页面
        
        Args:
            parent_id: 父页面或数据库 ID
            title: 页面标题
            properties: 可选的页面属性
            icon: 可选的 emoji 图标
            children: 可选的初始块内容
            
        Returns:
            创建的页面信息文本，如果出错返回 None
        """
        args = {
            "parent": {"type": "database_id", "database_id": parent_id},
            "properties": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        }
        
        if icon:
            args["icon"] = {"type": "emoji", "emoji": icon}
        
        if properties:
            args["properties"].update(properties)
        
        if children:
            args["children"] = children
        
        return await self._call_tool("API-post-page", args)
    
    async def update_page(self, page_id: str, properties: dict) -> Optional[str]:
        """
        更新页面属性
        
        Args:
            page_id: 页面 ID
            properties: 要更新的属性字典
            
        Returns:
            更新结果文本，如果出错返回 None
        """
        args = {
            "page_id": page_id,
            "properties": properties
        }
        
        return await self._call_tool("API-patch-page", args)
    
    async def retrieve_page(self, page_id: str) -> Optional[str]:
        """
        获取页面详情
        
        Args:
            page_id: 页面 ID
            
        Returns:
            页面详情文本，如果出错返回 None
        """
        args = {"page_id": page_id}
        return await self._call_tool("API-retrieve-a-page", args)
    
    # ==================== 块操作 ====================
    
    async def get_block_children(self, page_id: str) -> Optional[str]:
        """
        获取页面的块内容
        
        Args:
            page_id: 页面 ID
            
        Returns:
            块内容文本，如果出错返回 None
        """
        args = {"block_id": page_id}
        return await self._call_tool("API-get-block-children", args)
    
    async def add_blocks(self, page_id: str, blocks: list) -> Optional[str]:
        """
        为页面添加块
        
        Args:
            page_id: 页面 ID
            blocks: 块定义列表
            
        Returns:
            添加结果文本，如果出错返回 None
        """
        args = {
            "block_id": page_id,
            "children": blocks
        }
        
        return await self._call_tool("API-patch-block-children", args)
    
    async def add_heading(self, page_id: str, level: int, text: str) -> Optional[str]:
        """
        添加标题块
        
        Args:
            page_id: 页面 ID
            level: 标题级别 (1-3)
            text: 标题文本
            
        Returns:
            添加结果文本，如果出错返回 None
        """
        block = {
            "object": "block",
            "type": f"heading_{level}",
            f"heading_{level}": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
        
        return await self.add_blocks(page_id, [block])
    
    async def add_paragraph(self, page_id: str, text: str) -> Optional[str]:
        """
        添加段落块
        
        Args:
            page_id: 页面 ID
            text: 段落文本
            
        Returns:
            添加结果文本，如果出错返回 None
        """
        block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }
        
        return await self.add_blocks(page_id, [block])
    
    async def add_bulleted_list(self, page_id: str, items: list) -> Optional[str]:
        """
        添加项目符号列表
        
        Args:
            page_id: 页面 ID
            items: 列表项目文本列表
            
        Returns:
            添加结果文本，如果出错返回 None
        """
        blocks = []
        for item in items:
            block = {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": item}}]
                }
            }
            blocks.append(block)
        
        return await self.add_blocks(page_id, blocks)
