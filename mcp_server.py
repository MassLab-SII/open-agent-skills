#!/usr/bin/env python3
"""
真实的 MCP 服务器实现

这个服务器通过 HTTP 接收 MCP 工具调用请求，
将其翻译成 Notion API 调用，并返回结果。

运行方式：
    python mcp_server.py --host localhost --port 5000
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    from notion_client import Client
except ImportError:
    print("❌ Missing dependencies. Installing...")
    os.system("pip install fastapi uvicorn pydantic notion-client")
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    from notion_client import Client


# ========================================================================================
# 数据模型
# ========================================================================================

class ToolCallRequest(BaseModel):
    """MCP 工具调用请求"""
    api_key: str
    tool_name: str
    params: Dict[str, Any]


# ========================================================================================
# MCP 服务器实现
# ========================================================================================

class NotionMCPServer:
    """
    真实的 MCP 服务器
    
    这个服务器：
    1. 接收 HTTP POST 请求
    2. 验证请求中的 MCP 工具名称
    3. 调用对应的 Notion API
    4. 返回结果
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Notion MCP Server",
            description="真实的 MCP 服务器，提供 Notion API 工具"
        )
        self._setup_routes()
    
    def _setup_routes(self):
        """设置 API 路由"""
        
        @self.app.post("/api/tools/call")
        async def call_tool(request: ToolCallRequest):
            """
            调用 MCP 工具
            
            这是真实的 MCP 调用点：
            - 接收工具名称和参数
            - 创建 Notion 客户端
            - 调用相应的 Notion API
            - 返回结果
            """
            
            print(f"\n📍 MCP Tool Call Received: {request.tool_name}")
            print(f"   API Key: {request.api_key[:20]}...")
            
            try:
                # 创建 Notion 客户端
                notion = Client(auth=request.api_key)
                
                # 根据工具名称调用相应的 API
                result = await self._handle_tool(notion, request.tool_name, request.params)
                
                print(f"   ✅ Success")
                return {"success": True, "result": result}
            
            except Exception as e:
                print(f"   ❌ Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/health")
        async def health():
            """健康检查"""
            return {"status": "ok", "service": "Notion MCP Server"}
        
        @self.app.get("/tools")
        async def list_tools():
            """列出所有可用的 MCP 工具"""
            return {
                "tools": [
                    "API-post-search",
                    "API-post-database-query",
                    "API-post-page",
                    "API-patch-page",
                    "API-patch-block-children",
                    "API-retrieve-a-page",
                    "API-get-block-children"
                ]
            }
    
    async def _handle_tool(self, notion: Client, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        处理 MCP 工具调用
        
        这里是真实的 Notion API 调用发生的地方
        """
        
        if tool_name == "API-post-search":
            # Notion Search API
            return notion.search(**params)
        
        elif tool_name == "API-post-database-query":
            # Notion Database Query API
            return notion.databases.query(**params)
        
        elif tool_name == "API-post-page":
            # Notion Create Page API
            return notion.pages.create(**params)
        
        elif tool_name == "API-patch-page":
            # Notion Update Page API
            page_id = params.pop("page_id")
            return notion.pages.update(page_id=page_id, **params)
        
        elif tool_name == "API-patch-block-children":
            # Notion Add Blocks API
            block_id = params.pop("block_id")
            return notion.blocks.children.append(block_id=block_id, **params)
        
        elif tool_name == "API-retrieve-a-page":
            # Notion Retrieve Page API
            return notion.pages.retrieve(**params)
        
        elif tool_name == "API-get-block-children":
            # Notion Get Block Children API
            return notion.blocks.children.list(**params)
        
        else:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
    
    def run(self, host: str = "localhost", port: int = 5000):
        """启动服务器"""
        print(f"🚀 Starting Notion MCP Server")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   URL: http://{host}:{port}")
        print(f"\n📖 API Documentation: http://{host}:{port}/docs")
        print(f"🏥 Health Check: http://{host}:{port}/health")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )


def main():
    """主函数"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Notion MCP Server")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    
    args = parser.parse_args()
    
    # 验证 API key
    if not os.getenv("EVAL_NOTION_API_KEY"):
        print("⚠️  Warning: EVAL_NOTION_API_KEY not set")
        print("   API key will need to be provided in MCP tool calls")
    
    # 启动服务器
    server = NotionMCPServer()
    server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
