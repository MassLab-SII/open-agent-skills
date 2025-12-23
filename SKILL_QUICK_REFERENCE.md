# Skill 开发快速参考卡

## 🔑 黄金法则

```
📌 MCP 优先：所有写入操作必须使用 MCP
❌ 禁止：notion_client 的 .pages.create(), .pages.update(), .blocks.children.append()
✅ 允许：notion_client 的读取操作
```

---

## ⚡ 5 分钟快速开始

### 1️⃣ 环境设置
```bash
export EVAL_NOTION_API_KEY="ntn_..."
export OPENAPI_MCP_HEADERS='{"Authorization": "Bearer ntn_...", "Notion-Version": "2025-09-03"}'
```

### 2️⃣ 导入必需的包
```python
from tasks.utils import notion_utils
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
```

### 3️⃣ 发现数据库
```python
api_key = os.getenv("EVAL_NOTION_API_KEY")
notion = notion_utils.get_notion_client(api_key)

main_page_id = notion_utils.find_page(notion, "Python Roadmap")
blocks = notion_utils.get_all_blocks_recursively(notion, main_page_id)

for block in blocks:
    if block.get("type") == "child_database":
        title = block.get("child_database", {}).get("title", "")
        if "Chapters" in title:
            chapters_db_id = block["id"]
```

### 4️⃣ 连接 MCP
```python
async def main():
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={**os.environ, "OPENAPI_MCP_HEADERS": json.dumps(headers)}
    )
    
    stack = AsyncExitStack()
    read, write = await stack.enter_async_context(stdio_client(params))
    session = await stack.enter_async_context(ClientSession(read, write))
    await asyncio.wait_for(session.initialize(), timeout=120)
    
    # 使用 MCP...
```

### 5️⃣ 使用 MCP 创建页面
```python
result = await session.call_tool("API-post-page", {
    "parent": {"database_id": db_id},
    "properties": {
        "Name": [{"text": {"content": "Title"}}]
    }
})

page_id = extract_page_id(result.model_dump())
```

---

## 📖 MCP 工具速查表

### 创建页面
```python
await session.call_tool("API-post-page", {
    "parent": {"database_id": "..."},
    "properties": {...},
    "icon": {"emoji": "🟣"}  # 可选
})
```

### 更新页面属性
```python
await session.call_tool("API-patch-page", {
    "page_id": "...",
    "properties": {
        "Status": {"status": {"name": "Done"}},
        "Sub-item": [{"id": "..."}, {"id": "..."}]
    }
})
```

### 添加内容块
```python
await session.call_tool("API-patch-block-children", {
    "block_id": "...",
    "children": [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Title"}}]
            }
        }
    ]
})
```

---

## 🛠️ 常用代码片段

### 查询数据库
```python
results = notion.databases.query(
    database_id=db_id,
    page_size=100,
    filter={
        "property": "Title",
        "title": {"equals": "..."}
    }
)
```

### 提取页面 ID
```python
def extract_page_id(data):
    if isinstance(data, dict):
        if "id" in data:
            return data["id"]
        elif "content" in data and data["content"]:
            import re
            match = re.search(r'"id":"([^"]+)"', data["content"][0].get("text", ""))
            if match:
                return match.group(1)
    return None
```

### 处理多个关系
```python
"Parent item": [{"id": parent_id}],
"Sub-item": [
    {"id": id1},
    {"id": id2},
    {"id": id3}
]
```

### 查询多个条件
```python
results = notion.databases.query(
    database_id=db_id,
    filter={
        "and": [
            {"property": "Status", "status": {"equals": "Done"}},
            {"property": "Type", "select": {"equals": "Lesson"}}
        ]
    }
)
```

---

## ⚠️ 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `AttributeError: query` | notion-client 版本问题 | 使用 `notion_utils.get_notion_client()` |
| `MCP 连接超时` | 网络慢 | 增加超时到 120 秒 |
| `页面ID为None` | MCP 响应解析失败 | 检查 `extract_page_id()` 实现 |
| `关系无法设置` | 格式错误 | 使用 `[{"id": "..."}]` 数组格式 |
| `数据库ID变化` | 硬编码ID | 使用动态发现机制 |

---

## 📋 验证脚本模板

```python
def verify(notion: Client, main_id: str = None) -> bool:
    """验证 skill 执行结果"""
    
    # 找到数据库
    main_page_id = notion_utils.find_page(notion, "Python Roadmap")
    blocks = notion_utils.get_all_blocks_recursively(notion, main_page_id)
    
    db_id = None
    for block in blocks:
        if block.get("type") == "child_database":
            if "Steps" in block.get("child_database", {}).get("title", ""):
                db_id = block["id"]
    
    # 验证内容
    results = notion.databases.query(
        database_id=db_id,
        filter={"property": "Title", "title": {"equals": "Expected Title"}}
    )
    
    if not results.get("results"):
        print("❌ 内容未找到")
        return False
    
    print("✅ 验证通过")
    return True
```

---

## 🎯 开发检查清单

- [ ] 使用 MCP 进行所有写入操作
- [ ] 数据库 ID 动态发现（非硬编码）
- [ ] 使用 `notion_utils.get_notion_client()`
- [ ] MCP 超时设置 ≥ 120 秒
- [ ] 添加了错误处理
- [ ] 创建了 `verify.py`
- [ ] 在新 workspace 中测试通过
- [ ] 代码有清晰注释

---

## 🔗 重要函数快速导航

```python
# 获取客户端
notion_utils.get_notion_client(api_key)

# 查找页面
notion_utils.find_page(notion, "Title")

# 查找页面或数据库
notion_utils.find_page_or_database_by_id(notion, id)

# 获取所有块
notion_utils.get_all_blocks_recursively(notion, page_id)

# 查询数据库
notion.databases.query(database_id=..., filter=...)
```

---

## 📞 需要帮助？

1. 查看完整文档：`SKILL_DEVELOPMENT_GUIDE.md`
2. 参考示例实现：`expert_skill_mcp_official.py`
3. 查看验证脚本：`tasks/notion/standard/python_roadmap/expert_level_lessons/verify.py`
4. 工具函数库：`tasks/utils/notion_utils.py`

---

**🚀 祝你开发顺利！**
