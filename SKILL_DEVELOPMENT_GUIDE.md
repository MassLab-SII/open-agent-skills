# Skill 开发完整指南

## 📌 概述

这份指南总结了在 open-agent-skills 项目中开发 Notion MCP Skill 的完整流程、最佳实践和常见问题解决方案。

---

## 🎯 核心原则

### 1. **MCP 优先**
- ✅ **所有写入操作必须使用 MCP**（Model Context Protocol）
- ✅ 不能使用 `notion_client` 的 write 方法（如 `.pages.create()`, `.pages.update()`, `.blocks.children.append()`）
- ✅ 可以使用 `notion_client` 的读取操作（`.search()`, `.databases.query()`, `.pages.retrieve()`）

### 2. **混合架构最优**
```
读取操作 → Notion Client (快速且高效)
写入操作 → MCP (符合要求)
```

### 3. **自动发现数据库**
- ❌ 不要硬编码数据库 ID
- ✅ 应该从 "Python Roadmap" 主页面的 child_database 块中动态发现数据库
- ✅ 这样即使在新的 Notion workspace 中也能自动适配

---

## 🏗️ 项目结构

```
open-agent-skills/
├── skills/
│   └── python_roadmap/
│       └── expert_level_lessons/          # Skill 实现
│           └── expert_skill_mcp_official.py
├── tasks/
│   └── notion/
│       └── standard/
│           └── python_roadmap/
│               └── expert_level_lessons/
│                   ├── skill.py            # 任务定义
│                   └── verify.py           # 验证脚本
├── tasks/
│   └── utils/
│       └── notion_utils.py               # 工具函数库
└── requirements.txt
```

---

## 🔧 关键技术栈

### 必需的包
```python
notion-client==2.4.0          # Notion API 客户端
mcp==0.8.0+                   # MCP 协议库
@notionhq/notion-mcp-server   # Notion MCP 服务器（通过 npx 运行）
```

### 环境变量
```bash
export EVAL_NOTION_API_KEY="ntn_..."   # Notion API 密钥
export OPENAPI_MCP_HEADERS='...'       # MCP 连接头
```

---

## 📝 完整开发流程

### Step 1: 发现数据库和查询现有内容

**使用 `notion_utils` 中的帮助函数：**

```python
from tasks.utils import notion_utils
from notion_client import Client
import os

# 获取 Notion 客户端（自动添加 .databases.query() 兼容层）
api_key = os.getenv("EVAL_NOTION_API_KEY")
notion = notion_utils.get_notion_client(api_key)

# 找到主页面
main_page_id = notion_utils.find_page(notion, "Python Roadmap")

# 从主页面的 child_database 块中发现数据库
all_blocks = notion_utils.get_all_blocks_recursively(notion, main_page_id)

chapters_db_id = None
steps_db_id = None

for block in all_blocks:
    if block and block.get("type") == "child_database":
        db_title = block.get("child_database", {}).get("title", "")
        if "Chapters" in db_title:
            chapters_db_id = block["id"]
        elif "Steps" in db_title:
            steps_db_id = block["id"]

# 查询现有数据
steps_response = notion.databases.query(database_id=steps_db_id, page_size=100)
```

**关键要点：**
- ✅ 使用 `notion_utils.get_notion_client()` 而不是直接创建 Client
- ✅ 使用 `notion_utils.find_page()` 查找主页面
- ✅ 从 child_database 块中提取数据库 ID（自动适配）
- ✅ 这样即使数据库 ID 变化也能正常工作

---

### Step 2: 连接 MCP 服务器

**使用 StdioServerParameters + ClientSession：**

```python
import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2025-09-03"
    }
    
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={**os.environ, "OPENAPI_MCP_HEADERS": json.dumps(headers)}
    )
    
    stack = AsyncExitStack()
    try:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(session.initialize(), timeout=120)
        
        # MCP 现在已连接，可以使用
        # 示例：创建页面
        result = await session.call_tool("API-post-page", {...})
        
    finally:
        await stack.aclose()

asyncio.run(main())
```

**关键要点：**
- ✅ 使用 `stdio_client()` 和 `ClientSession` 管理 MCP 生命周期
- ✅ 在 env 中正确传递 MCP 头部
- ✅ 使用 `AsyncExitStack` 确保正确清理资源
- ✅ 设置足够长的超时时间（120 秒）

---

### Step 3: 使用 MCP 创建页面

**MCP Tool: `API-post-page`**

```python
# 创建一个新章节
chapter_result = await session.call_tool("API-post-page", {
    "parent": {"database_id": chapters_db_id},
    "properties": {
        "Name": [{"text": {"content": "Expert Level"}}]
    },
    "icon": {"emoji": "🟣"}
})

chapter_id = extract_page_id(chapter_result.model_dump())
```

**参数说明：**
- `parent`: 指定数据库 ID
- `properties`: 页面属性（根据数据库的数据库结构设置）
- `icon`: 可选，设置页面图标

**关键要点：**
- ✅ 返回的是 MCP 工具结果对象，需要提取页面 ID
- ✅ 属性必须符合数据库的字段定义

---

### Step 4: 使用 MCP 更新页面

**MCP Tool: `API-patch-page`**

```python
# 更新页面属性
await session.call_tool("API-patch-page", {
    "page_id": page_id,
    "properties": {
        "Status": {"status": {"name": "Done"}},
        "Sub-item": [{"id": sub_item_id_1}, {"id": sub_item_id_2}]
    }
})
```

**常见属性类型：**
- Status: `{"status": {"name": "Done"}}` 或 `{"status": {"name": "To Do"}}`
- Relation: `{"relations_or_people": [{"id": related_page_id}]}`
- 多行关系：`[{"id": id1}, {"id": id2}]`

---

### Step 5: 使用 MCP 添加内容块

**MCP Tool: `API-patch-block-children`**

```python
# 添加标题和列表项
await session.call_tool("API-patch-block-children", {
    "block_id": page_id,
    "children": [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Prerequisites Checklist"}
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Item 1"}
                    }
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Paragraph text"}
                    }
                ]
            }
        }
    ]
})
```

**支持的块类型：**
- `heading_1`, `heading_2`, `heading_3` - 标题
- `paragraph` - 段落
- `bulleted_list_item` - 无序列表
- `numbered_list_item` - 有序列表

---

## 🧰 关键工具函数

### notion_utils 中的重要函数

```python
# 获取 Notion 客户端（自动添加 .databases.query() 兼容层）
notion = notion_utils.get_notion_client(api_key)

# 查找页面
page_id = notion_utils.find_page(notion, "Python Roadmap")

# 查找页面或数据库
page_id, object_type = notion_utils.find_page_or_database_by_id(notion, page_id)

# 递归获取所有块
blocks = notion_utils.get_all_blocks_recursively(notion, page_id)

# 查询数据库（自动处理兼容性）
results = notion.databases.query(database_id=db_id, filter={...})
```

---

## 🔍 MCP 响应处理

### 提取页面 ID

```python
def extract_page_id(data):
    """从 MCP 响应中提取页面 ID"""
    if isinstance(data, dict):
        if "id" in data:
            return data["id"]
        elif "content" in data and data["content"]:
            content_text = data["content"][0].get("text", "")
            if content_text:
                import re
                match = re.search(r'"id":"([^"]+)"', content_text)
                if match:
                    return match.group(1)
    return None
```

---

## ✅ 验证脚本编写

创建 `verify.py` 来验证所有创建的内容：

```python
def verify(notion: Client, main_id: str = None) -> bool:
    """验证 skill 的执行结果"""
    
    # Step 1: 找到数据库
    main_page_id = notion_utils.find_page(notion, "Python Roadmap")
    all_blocks = notion_utils.get_all_blocks_recursively(notion, main_page_id)
    
    # Step 2: 查询特定内容
    results = notion.databases.query(
        database_id=db_id,
        filter={
            "property": "Name",
            "title": {"equals": "Expert Level"}
        }
    )
    
    if not results.get("results"):
        print("❌ Expert Level 章节未找到")
        return False
    
    print("✅ Expert Level 章节已创建")
    return True
```

---

## 📋 常见问题与解决方案

### Q1: `notion.databases.query()` 方法不存在

**原因：** notion-client 2.4.0+ 中将 `databases.query()` 改为 `data_sources.query()`

**解决方案：** 使用 `notion_utils.get_notion_client()` 自动添加兼容层

```python
# ❌ 错误
notion = Client(auth=api_key)
notion.databases.query(database_id=...)  # AttributeError

# ✅ 正确
from tasks.utils import notion_utils
notion = notion_utils.get_notion_client(api_key)
notion.databases.query(database_id=...)  # 自动转换为 data_sources.query()
```

---

### Q2: 如何处理动态数据库 ID 变化

**原因：** 每次用户创建新的 Notion workspace，数据库 ID 都会变化

**解决方案：** 从主页面的 child_database 块中动态发现数据库

```python
# ❌ 错误：硬编码 ID
chapters_db_id = "2ce5d1cf-e7c4-81a1-97e4-eb9b090a0c6c"

# ✅ 正确：动态发现
main_page_id = notion_utils.find_page(notion, "Python Roadmap")
blocks = notion_utils.get_all_blocks_recursively(notion, main_page_id)

for block in blocks:
    if block.get("type") == "child_database":
        if "Chapters" in block.get("child_database", {}).get("title", ""):
            chapters_db_id = block["id"]
```

---

### Q3: MCP 连接超时

**原因：** 网络缓慢或 Notion MCP 服务器启动慢

**解决方案：** 增加超时时间和添加重试机制

```python
# 增加超时时间
await asyncio.wait_for(session.initialize(), timeout=120)  # 从 60 改为 120

# 添加重试
for attempt in range(3):
    try:
        result = await session.call_tool("API-post-page", {...})
        break
    except Exception as e:
        if attempt < 2:
            await asyncio.sleep(1)
        else:
            raise
```

---

### Q4: 页面关系设置不正确

**原因：** 关系字段格式错误

**解决方案：** 使用正确的关系格式

```python
# ❌ 错误格式
"Parent item": parent_id  # 只是 ID 字符串

# ✅ 正确格式
"Parent item": [{"id": parent_id}]  # 对象数组

# 多个关系
"Sub-item": [
    {"id": id1},
    {"id": id2},
    {"id": id3}
]
```

---

### Q5: 查询没有返回预期结果

**原因：** 过滤条件格式错误

**解决方案：** 使用正确的过滤格式

```python
# ✅ 按标题查询
results = notion.databases.query(
    database_id=db_id,
    filter={
        "property": "Lessons",
        "title": {"contains": "Control"}
    }
)

# ✅ 按状态查询
results = notion.databases.query(
    database_id=db_id,
    filter={
        "property": "Status",
        "status": {"equals": "Done"}
    }
)

# ✅ 复合条件
results = notion.databases.query(
    database_id=db_id,
    filter={
        "and": [
            {"property": "Status", "status": {"equals": "Done"}},
            {"property": "Chapters", "relation": {"contains": chapter_id}}
        ]
    }
)
```

---

## 📊 完整工作流示例

```python
#!/usr/bin/env python3
"""
完整的 Skill 开发示例
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from tasks.utils import notion_utils

async def create_expert_lessons_skill():
    """创建专家级课程 Skill"""
    
    # ===== Step 1: 发现数据库 =====
    print("🔍 Step 1: 发现数据库...")
    
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    notion = notion_utils.get_notion_client(api_key)
    
    main_page_id = notion_utils.find_page(notion, "Python Roadmap")
    all_blocks = notion_utils.get_all_blocks_recursively(notion, main_page_id)
    
    chapters_db_id = None
    steps_db_id = None
    
    for block in all_blocks:
        if block and block.get("type") == "child_database":
            db_title = block.get("child_database", {}).get("title", "")
            if "Chapters" in db_title:
                chapters_db_id = block["id"]
            elif "Steps" in db_title:
                steps_db_id = block["id"]
    
    print(f"✓ 数据库已发现: Chapters={chapters_db_id}, Steps={steps_db_id}")
    
    # ===== Step 2: 查询现有数据 =====
    print("\n📊 Step 2: 查询现有数据...")
    
    steps_response = notion.databases.query(database_id=steps_db_id, page_size=100)
    existing_lessons = {
        item["properties"]["Lessons"]["title"][0]["text"]["content"]: item["id"]
        for item in steps_response.get("results", [])
    }
    
    print(f"✓ 找到 {len(existing_lessons)} 个现有课程")
    
    # ===== Step 3: 连接 MCP =====
    print("\n🔌 Step 3: 连接 MCP...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2025-09-03"
    }
    
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={**os.environ, "OPENAPI_MCP_HEADERS": json.dumps(headers)}
    )
    
    stack = AsyncExitStack()
    try:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(session.initialize(), timeout=120)
        
        print("✓ MCP 已连接")
        
        # ===== Step 4: 使用 MCP 创建内容 =====
        print("\n📝 Step 4: 使用 MCP 创建内容...")
        
        # 创建章节
        chapter_result = await session.call_tool("API-post-page", {
            "parent": {"database_id": chapters_db_id},
            "properties": {
                "Name": [{"text": {"content": "Expert Level"}}]
            },
            "icon": {"emoji": "🟣"}
        })
        
        chapter_id = extract_page_id(chapter_result.model_dump())
        print(f"✓ 章节已创建: {chapter_id}")
        
        # 创建课程
        lesson_result = await session.call_tool("API-post-page", {
            "parent": {"database_id": steps_db_id},
            "properties": {
                "Lessons": [{"text": {"content": "Advanced Python Techniques"}}],
                "Status": {"status": {"name": "To Do"}},
                "Chapters": [{"id": chapter_id}]
            }
        })
        
        lesson_id = extract_page_id(lesson_result.model_dump())
        print(f"✓ 课程已创建: {lesson_id}")
        
        # ===== Step 5: 验证 =====
        print("\n✅ 所有操作完成！")
        
    finally:
        await stack.aclose()

def extract_page_id(data):
    """从 MCP 响应中提取页面 ID"""
    if isinstance(data, dict):
        if "id" in data:
            return data["id"]
        elif "content" in data and data["content"]:
            import re
            match = re.search(r'"id":"([^"]+)"', data["content"][0].get("text", ""))
            if match:
                return match.group(1)
    return None

if __name__ == "__main__":
    asyncio.run(create_expert_lessons_skill())
```

---

## 🎓 开发检查清单

在提交 Skill 前，确保检查以下项目：

- [ ] **MCP 优先**：所有写入操作都使用 MCP，没有使用 `notion_client` 的写入方法
- [ ] **自动发现**：数据库 ID 从主页面动态发现，不是硬编码
- [ ] **错误处理**：添加了适当的错误处理和日志记录
- [ ] **验证脚本**：创建了 `verify.py` 来验证所有创建的内容
- [ ] **兼容性**：使用 `notion_utils.get_notion_client()` 处理 API 版本差异
- [ ] **超时设置**：MCP 连接设置了足够的超时时间（120 秒）
- [ ] **文档齐全**：代码有清晰的注释和文档
- [ ] **测试通过**：在新的 Notion workspace 中成功运行并通过验证

---

## 📚 参考资源

### 相关文件
- `tasks/utils/notion_utils.py` - 工具函数库
- `tasks/notion/standard/python_roadmap/expert_level_lessons/verify.py` - 验证脚本示例
- `expert_skill_mcp_official.py` - 完整实现示例

### MCP 工具列表
- `API-post-page` - 创建新页面
- `API-patch-page` - 更新页面属性
- `API-patch-block-children` - 添加内容块

### Notion API 文档
- https://developers.notion.com/reference
- https://github.com/notion-sdk-py

---

## 💡 最佳实践总结

1. **始终使用 MCP 进行写入操作**
   - 这是项目的核心要求
   - 无一例外

2. **动态发现而非硬编码**
   - 使用 `notion_utils` 中的函数
   - 支持多个 workspace 自动适配

3. **清晰的日志输出**
   - 帮助调试和理解流程
   - 对用户友好的进度反馈

4. **完整的验证脚本**
   - 每个 Skill 都需要对应的 verify.py
   - 确保所有创建的内容符合预期

5. **正确的错误处理**
   - 捕获并记录 MCP 和 API 错误
   - 提供有用的错误信息

6. **合理的超时时间**
   - MCP 初始化设置 120+ 秒
   - API 调用适当重试

---

## 🚀 下一步

现在你可以：

1. 参考本指南创建新的 Skill
2. 复用本项目的工具函数和最佳实践
3. 运行 verify.py 验证实现
4. 在新的 Notion workspace 中测试自动发现

祝你开发顺利！🎉
