# 📚 Skill 开发文档导航

> 快速找到你需要的文档

---

## 🎯 快速导航

### 🆕 我是新手
```
1. SKILL_QUICK_REFERENCE.md (5 分钟)
2. SKILL_DEVELOPMENT_GUIDE.md (30 分钟)
3. expert_skill_mcp_official.py (参考代码)
```

### 🚀 我要快速开发
```
1. SKILL_QUICK_REFERENCE.md (代码片段)
2. 复制 expert_skill_mcp_official.py
3. MCP_TOOLS_REFERENCE.md (查询细节)
```

### 🆘 我遇到了问题
```
1. TROUBLESHOOTING_GUIDE.md (找问题)
2. 运行诊断脚本
3. SKILL_DEVELOPMENT_GUIDE.md (查最佳实践)
```

### 📖 我想学习 MCP API
```
1. MCP_TOOLS_REFERENCE.md (完整参考)
2. SKILL_QUICK_REFERENCE.md (快速查询)
3. expert_skill_mcp_official.py (实际使用)
```

---

## 📁 文档文件列表

| 文件 | 类型 | 内容 | 长度 |
|------|------|------|------|
| **SKILL_DEVELOPMENT_GUIDE.md** | 📖 教程 | 完整的开发指南和最佳实践 | 650+ 行 |
| **SKILL_QUICK_REFERENCE.md** | ⚡ 参考 | 快速查询卡，代码片段 | 280+ 行 |
| **MCP_TOOLS_REFERENCE.md** | 📚 API | MCP 工具详细参考 | 850+ 行 |
| **TROUBLESHOOTING_GUIDE.md** | 🆘 排查 | 常见问题和解决方案 | 700+ 行 |
| **DOCUMENTATION_INDEX.md** | 🗂️ 索引 | 文档总索引和导航 | 170+ 行 |
| **AGENT_HANDOFF_SUMMARY.md** | 📝 总结 | 项目总结和交接要点 | 400+ 行 |
| **README_DOCUMENTATION.md** | 👈 本文 | 快速导航（你在这里） | 这个文件 |

**总计：** 3,050+ 行文档 + 100+ 代码示例

---

## 🔑 核心概念（30 秒版本）

```python
# 1️⃣ 发现数据库（Notion Client）
notion = notion_utils.get_notion_client(api_key)
main_page = notion_utils.find_page(notion, "Python Roadmap")
blocks = notion_utils.get_all_blocks_recursively(notion, main_page)

# 2️⃣ 查询现有数据（Notion Client）
results = notion.databases.query(database_id=db_id, filter={...})

# 3️⃣ 连接 MCP
session = await initialize_mcp_session(api_key)

# 4️⃣ 创建页面（MCP）
result = await session.call_tool("API-post-page", {...})

# 5️⃣ 更新属性（MCP）
await session.call_tool("API-patch-page", {...})

# 6️⃣ 添加内容（MCP）
await session.call_tool("API-patch-block-children", {...})

# 7️⃣ 验证（Notion Client + 检查）
verify(notion)
```

---

## ⚡ 30 秒快速开始

### 最小化示例
```python
#!/usr/bin/env python3
import asyncio
import os
from tasks.utils import notion_utils
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def quick_example():
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    
    # 1. 获取 Notion 客户端
    notion = notion_utils.get_notion_client(api_key)
    main_page = notion_utils.find_page(notion, "Python Roadmap")
    
    # 2. 发现数据库
    blocks = notion_utils.get_all_blocks_recursively(notion, main_page)
    db_id = None
    for block in blocks:
        if block.get("type") == "child_database":
            if "Steps" in block.get("child_database", {}).get("title", ""):
                db_id = block["id"]
    
    # 3. 连接 MCP
    params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"]
    )
    
    async with stdio_client(params) as stdio:
        async with ClientSession(stdio[0], stdio[1]) as session:
            await session.initialize()
            
            # 4. 创建页面
            result = await session.call_tool("API-post-page", {
                "parent": {"database_id": db_id},
                "properties": {
                    "Lessons": [{"text": {"content": "My Lesson"}}]
                }
            })
            print(f"✓ 创建成功: {result}")

asyncio.run(quick_example())
```

---

## 🔍 按问题类型快速查找

### API 和连接问题
- `AttributeError: query()` → TROUBLESHOOTING_GUIDE.md 问题 2
- `401 Unauthorized` → TROUBLESHOOTING_GUIDE.md 问题 3
- `404 Not Found` → TROUBLESHOOTING_GUIDE.md 问题 4
- `Connection timeout` → TROUBLESHOOTING_GUIDE.md 问题 5

### 开发问题
- 如何创建页面？ → MCP_TOOLS_REFERENCE.md - API-post-page
- 如何更新属性？ → MCP_TOOLS_REFERENCE.md - API-patch-page
- 如何添加内容？ → MCP_TOOLS_REFERENCE.md - API-patch-block-children
- 关系设置失败？ → TROUBLESHOOTING_GUIDE.md 问题 9

### 查询问题
- 如何查询数据库？ → SKILL_DEVELOPMENT_GUIDE.md Step 1
- 查询返回空？ → TROUBLESHOOTING_GUIDE.md 问题 10
- 如何过滤数据？ → MCP_TOOLS_REFERENCE.md 查询示例

### 验证问题
- 如何编写验证脚本？ → SKILL_DEVELOPMENT_GUIDE.md 验证脚本编写
- verify.py 失败？ → TROUBLESHOOTING_GUIDE.md 问题 11

---

## 💻 代码位置

### 核心文件
- `expert_skill_mcp_official.py` - 完整实现（467 行）
- `tasks/utils/notion_utils.py` - 工具函数
- `tasks/notion/.../verify.py` - 验证脚本模板

### 如何使用
```bash
# 1. 查看完整实现
cat expert_skill_mcp_official.py

# 2. 查看工具函数
cat tasks/utils/notion_utils.py

# 3. 查看验证脚本
cat tasks/notion/standard/python_roadmap/expert_level_lessons/verify.py

# 4. 复制并修改
cp expert_skill_mcp_official.py my_skill.py
# 编辑 my_skill.py
# 运行并测试
python my_skill.py
```

---

## ✨ 黄金法则

### ✅ 必须做
- [ ] 所有写入操作使用 MCP
- [ ] 数据库 ID 动态发现
- [ ] 使用 notion_utils 工具函数
- [ ] 参数格式必须精确
- [ ] 写验证脚本

### ❌ 禁止做
- [ ] 硬编码数据库 ID
- [ ] 使用 notion_client.pages.create/update
- [ ] 忽视错误处理
- [ ] 缺少关系属性的数组括号
- [ ] MCP 超时设置不足

---

## 🚀 立即开始

### 方式 1：快速学习（推荐新手）
```bash
# 15 分钟
cat SKILL_QUICK_REFERENCE.md

# 30 分钟
cat SKILL_DEVELOPMENT_GUIDE.md | head -300

# 理解核心代码
cat expert_skill_mcp_official.py | grep -A 20 "API-post-page"
```

### 方式 2：快速开发（推荐有经验者）
```bash
# 5 分钟
cat SKILL_QUICK_REFERENCE.md | head -50

# 复制模板
cp expert_skill_mcp_official.py my_skill.py

# 根据需要修改
# 创建 verify.py
# 测试
python my_skill.py
```

### 方式 3：快速排查（推荐遇到问题者）
```bash
# 找问题
grep -n "你的错误关键词" TROUBLESHOOTING_GUIDE.md

# 运行诊断
python check_api_connection.py
python check_mcp_connection.py

# 查看解决方案
```

---

## 📞 常见问题秒答

**Q: 为什么必须用 MCP？**  
A: 这是项目要求，确保写入操作的安全性和可追踪性。

**Q: 数据库 ID 经常变吗？**  
A: 会的，每个新的 Notion workspace 都有不同的 ID。所以必须自动发现。

**Q: notion_utils 是什么？**  
A: 项目提供的工具库，包含发现、查询、兼容性处理等功能。

**Q: 参数格式不对会怎样？**  
A: 通常会无声失败或返回错误，很难调试。所以需要精确。

**Q: 超时时间设多少？**  
A: MCP 初始化至少 120 秒，API 调用 30-60 秒。

**Q: 如何快速诊断问题？**  
A: 运行 check_api_connection.py 和 check_mcp_connection.py。

---

## 📊 文档速查表

```
需要什么？              查看这个文档
────────────────────  ─────────────────────────────
系统学习                SKILL_DEVELOPMENT_GUIDE.md
快速参考                SKILL_QUICK_REFERENCE.md
API 细节                MCP_TOOLS_REFERENCE.md
问题排查                TROUBLESHOOTING_GUIDE.md
导航索引                DOCUMENTATION_INDEX.md
项目总结                AGENT_HANDOFF_SUMMARY.md
本快速导航              README_DOCUMENTATION.md ← 你在这里
```

---

## 🎓 学习时间估计

| 活动 | 时间 | 成果 |
|------|------|------|
| 阅读快速参考 | 15 分钟 | 理解基础概念 |
| 研究完整指南 | 1 小时 | 掌握完整流程 |
| 分析示例代码 | 30 分钟 | 理解实现细节 |
| 第一个 skill | 2-4 小时 | 可工作的实现 |
| 遇到问题调试 | 30 分钟 | 问题解决 |
| **总计** | **4-6 小时** | **完全掌握** |

---

## 🔗 快速链接

**文档：**
- 📖 [完整开发指南](./SKILL_DEVELOPMENT_GUIDE.md)
- ⚡ [快速参考卡](./SKILL_QUICK_REFERENCE.md)
- 📚 [MCP 工具参考](./MCP_TOOLS_REFERENCE.md)
- 🆘 [故障排查指南](./TROUBLESHOOTING_GUIDE.md)
- 🗂️ [文档索引](./DOCUMENTATION_INDEX.md)
- 📝 [项目总结](./AGENT_HANDOFF_SUMMARY.md)

**代码：**
- 💻 [完整实现](./expert_skill_mcp_official.py)
- 🧰 [工具函数](./tasks/utils/notion_utils.py)
- ✅ [验证脚本](./tasks/notion/standard/python_roadmap/expert_level_lessons/verify.py)

---

## 💡 Tips

1. **书签这个文件** - 它是所有文档的入口
2. **使用 Ctrl+F** - 快速搜索文档中的关键词
3. **copy-paste 代码** - 快速参考中的代码片段是可直接使用的
4. **运行诊断** - 遇到问题时总是先运行诊断脚本
5. **查阅原始代码** - 看不懂文档时，查看 expert_skill_mcp_official.py

---

**祝你开发顺利！** 🚀

*需要什么？一切都在文档中。*
