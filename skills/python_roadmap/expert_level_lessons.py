#!/usr/bin/env python3
"""
Expert Level Lessons Skill - 正式完整版本
完全使用 MCP (Model Context Protocol) 实现所有操作

功能：
1. 发现数据库 IDs
2. 查询现有课程
3. 使用 MCP 创建 Expert Level 章节
4. 使用 MCP 创建 Advanced Foundations Review Bridge 课程
5. 使用 MCP 创建 4 个专家级课程
6. 使用 MCP 更新现有课程状态
7. 使用 MCP 设置所有课程关系
8. 使用 MCP 添加学习路径内容块
9. 使用 MCP 添加 Memory Management 的 Sub-items

所有 Notion 写入操作都使用 MCP 而不是 Notion Client。
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from notion_client import Client
from tasks.utils import notion_utils


async def expert_skill_full_mcp():
    """
    完整的 Expert Level Lessons Skill 实现 - 全部使用 MCP
    """
    
    print("\n" + "="*80)
    print("🔍 STEP 1: 发现数据库和查询现有内容")
    print("="*80 + "\n")
    
    # 使用兼容性包装获取 notion client
    notion = notion_utils.get_notion_client()
    
    # 搜索 Python Roadmap 主页面
    print("搜索 Python Roadmap 主页面...")
    main_page_id = notion_utils.find_page(notion, "Python Roadmap")
    
    if not main_page_id:
        print("❌ Python Roadmap 页面未找到")
        return
    
    print(f"✓ 找到主页面: {main_page_id}\n")
    
    # 从主页面中获取所有块，找出数据库 IDs
    print("搜索 Chapters 和 Steps 数据库...")
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
    
    if not chapters_db_id or not steps_db_id:
        print(f"❌ 数据库未找到")
        print(f"   Chapters: {chapters_db_id}")
        print(f"   Steps: {steps_db_id}")
        return
    
    print(f"✓ Chapters 数据库: {chapters_db_id}")
    print(f"✓ Steps 数据库: {steps_db_id}\n")
    
    # 查询所有课程
    print("查询现有课程...")
    steps_response = notion.databases.query(
        database_id=steps_db_id,
        page_size=100
    )
    
    existing_lessons = {}
    for item in steps_response.get("results", []):
        lessons_field = item["properties"].get("Lessons", {})
        if lessons_field.get("type") == "title":
            title_blocks = lessons_field.get("title", [])
            if title_blocks:
                lesson_title = title_blocks[0]["text"]["content"]
                existing_lessons[lesson_title] = {
                    "id": item["id"],
                    "status": item["properties"].get("Status", {}).get("status", {}).get("name", "")
                }
    
    print(f"✓ 找到 {len(existing_lessons)} 个现有课程")
    
    # 查询所有章节
    print("查询现有章节...")
    chapters_response = notion.databases.query(
        database_id=chapters_db_id,
        page_size=100
    )
    
    existing_chapters = {}
    for item in chapters_response.get("results", []):
        name_field = item["properties"].get("Name", {})
        if name_field.get("type") == "title":
            title_blocks = name_field.get("title", [])
            if title_blocks:
                chapter_name = title_blocks[0]["text"]["content"]
                existing_chapters[chapter_name] = item["id"]
    
    print(f"✓ 找到 {len(existing_chapters)} 个现有章节")
    
    # 找到必需的课程 IDs
    control_flow_id = existing_lessons.get("Control Flow", {}).get("id", "")
    decorators_id = existing_lessons.get("Decorators", {}).get("id", "")
    calling_api_id = existing_lessons.get("Calling API", {}).get("id", "")
    regex_id = existing_lessons.get("Regular Expressions", {}).get("id", "")
    error_handling_id = existing_lessons.get("Error Handling", {}).get("id", "")
    data_structures_id = existing_lessons.get("Data Structures", {}).get("id", "")
    
    # 找 OOP 课程
    oops_id = None
    for lesson_title, lesson_info in existing_lessons.items():
        if "OOP" in lesson_title or "Object" in lesson_title:
            oops_id = lesson_info["id"]
            break
    
    print()
    
    # ==========================================
    # STEP 2: 使用 MCP 执行所有操作
    # ==========================================
    
    print("="*80)
    print("🚀 STEP 2: 使用 MCP 创建和更新所有内容")
    print("="*80 + "\n")
    
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
        
        print("✅ MCP 已连接\n")
        
        # ==========================================
        # Task 1: 创建 Expert Level 章节
        # ==========================================
        
        print("Task 1️⃣: 创建 Expert Level 章节 (使用 MCP)...")
        
        expert_chapter_result = await session.call_tool("API-post-page", {
            "parent": {"database_id": chapters_db_id},
            "properties": {
                "Name": [{"text": {"content": "Expert Level"}}]
            },
            "icon": {"emoji": "🟣"}
        })
        
        expert_chapter_id = extract_page_id(expert_chapter_result.model_dump())
        
        if expert_chapter_id:
            print(f"✓ 创建成功: {expert_chapter_id}\n")
        else:
            print(f"✗ 创建失败\n")
            return
        
        # ==========================================
        # Task 2: 创建 Advanced Foundations Review Bridge 课程
        # ==========================================
        
        print("Task 2️⃣: 创建 Bridge 课程 (使用 MCP)...")
        
        bridge_properties = {
            "Lessons": [{"text": {"content": "Advanced Foundations Review"}}],
            "Status": {"name": "Done"},
            "Chapters": [{"id": expert_chapter_id}]
        }
        
        if control_flow_id:
            bridge_properties["Parent item"] = [{"id": control_flow_id}]
        
        sub_items = []
        if decorators_id:
            sub_items.append({"id": decorators_id})
        if calling_api_id:
            sub_items.append({"id": calling_api_id})
        if regex_id:
            sub_items.append({"id": regex_id})
        
        if sub_items:
            bridge_properties["Sub-item"] = sub_items
        
        bridge_result = await session.call_tool("API-post-page", {
            "parent": {"database_id": steps_db_id},
            "properties": bridge_properties
        })
        
        bridge_id = extract_page_id(bridge_result.model_dump())
        
        if bridge_id:
            print(f"✓ 创建成功: {bridge_id}\n")
        else:
            print(f"✗ 创建失败\n")
            bridge_id = None
        
        # ==========================================
        # Task 3: 创建 4 个专家级课程
        # ==========================================
        
        print("Task 3️⃣: 创建 4 个专家级课程 (使用 MCP)...")
        
        expert_lessons_config = [
            {
                "title": "Metaprogramming and AST Manipulation",
                "date": "2025-09-15",
                "status": "To Do",
                "parent": bridge_id
            },
            {
                "title": "Async Concurrency Patterns",
                "date": "2025-09-20",
                "status": "To Do",
                "parent": calling_api_id
            },
            {
                "title": "Memory Management and GC Tuning",
                "date": "2025-09-25",
                "status": "In Progress",
                "parent": bridge_id
            },
            {
                "title": "Building Python C Extensions",
                "date": "2025-10-01",
                "status": "To Do",
                "parent": None
            }
        ]
        
        expert_lesson_ids = {}
        created_count = 0
        
        for config in expert_lessons_config:
            properties = {
                "Lessons": [{"text": {"content": config["title"]}}],
                "Status": {"name": config["status"]},
                "Date": {"start": config["date"]},
                "Chapters": [{"id": expert_chapter_id}]
            }
            
            if config["parent"]:
                properties["Parent item"] = [{"id": config["parent"]}]
            
            lesson_result = await session.call_tool("API-post-page", {
                "parent": {"database_id": steps_db_id},
                "properties": properties
            })
            
            lesson_id = extract_page_id(lesson_result.model_dump())
            
            if lesson_id:
                expert_lesson_ids[config["title"]] = lesson_id
                print(f"✓ {config['title']}")
                created_count += 1
        
        print(f"✓ 创建了 {created_count} 个专家级课程\n")
        
        # ==========================================
        # Task 4: 更新现有课程状态 (使用 MCP)
        # ==========================================
        
        print("Task 4️⃣: 更新现有课程状态 (使用 MCP)...")
        
        # 更新 Decorators 为 Done
        if decorators_id:
            await session.call_tool("API-patch-page", {
                "page_id": decorators_id,
                "properties": {"Status": {"status": {"name": "Done"}}}
            })
            print(f"✓ Decorators: Updated to Done")
        
        # 更新 Control Flow 为 Done
        if control_flow_id:
            await session.call_tool("API-patch-page", {
                "page_id": control_flow_id,
                "properties": {"Status": {"status": {"name": "Done"}}}
            })
            print(f"✓ Control Flow: Updated to Done")
        
        print()
        
        # ==========================================
        # Task 5: 更新 Error Handling 的 Sub-items (使用 MCP)
        # ==========================================
        
        print("Task 5️⃣: 更新 Error Handling (使用 MCP)...")
        
        if error_handling_id and "Async Concurrency Patterns" in expert_lesson_ids:
            await session.call_tool("API-patch-page", {
                "page_id": error_handling_id,
                "properties": {
                    "Sub-item": [{"id": expert_lesson_ids["Async Concurrency Patterns"]}]
                }
            })
            print(f"✓ Added Async Concurrency Patterns as sub-item\n")
        else:
            print(f"⚠ Error Handling not found\n")
        
        # ==========================================
        # Task 6: 设置 Building Python C Extensions 的 Parent (使用 MCP)
        # ==========================================
        
        print("Task 6️⃣: 设置 Building Python C Extensions Parent (使用 MCP)...")
        
        if "Building Python C Extensions" in expert_lesson_ids and "Metaprogramming and AST Manipulation" in expert_lesson_ids:
            await session.call_tool("API-patch-page", {
                "page_id": expert_lesson_ids["Building Python C Extensions"],
                "properties": {
                    "Parent item": [{"id": expert_lesson_ids["Metaprogramming and AST Manipulation"]}]
                }
            })
            print(f"✓ Parent set to Metaprogramming and AST Manipulation\n")
        
        # ==========================================
        # Task 7: 添加学习路径内容块到 Bridge 课程 (使用 MCP)
        # ==========================================
        
        print("Task 7️⃣: 添加学习路径内容块 (使用 MCP)...")
        
        if bridge_id:
            await session.call_tool("API-patch-block-children", {
                "block_id": bridge_id,
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
                                    "text": {"content": "✅ Advanced Python Features (Decorators, Context Managers)"}
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
                                    "text": {"content": "✅ API Integration and Async Basics"}
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
                                    "text": {"content": "✅ Pattern Matching and Text Processing"}
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
                                    "text": {"content": "This lesson serves as a checkpoint before entering expert-level content. Ensure you have mastered all prerequisites listed above."}
                                }
                            ]
                        }
                    }
                ]
            })
            print(f"✓ 内容块已添加\n")
        
        # ==========================================
        # Task 8: 添加 Memory Management 的 Sub-items (使用 MCP)
        # ==========================================
        
        print("Task 8️⃣: 添加 Memory Management Sub-items (使用 MCP)...")
        
        if "Memory Management and GC Tuning" in expert_lesson_ids and data_structures_id and oops_id:
            await session.call_tool("API-patch-page", {
                "page_id": expert_lesson_ids["Memory Management and GC Tuning"],
                "properties": {
                    "Sub-item": [
                        {"id": data_structures_id},
                        {"id": oops_id}
                    ]
                }
            })
            print(f"✓ 2 个 Sub-items 已添加\n")
        else:
            print(f"⚠ 缺少必需的课程\n")
        
        # ==========================================
        # 完成
        # ==========================================
        
        print("="*80)
        print("✅ EXPERT LEVEL LESSONS SKILL COMPLETED")
        print("="*80)
        print(f"\n📊 Summary (所有操作都使用了 MCP):")
        print(f"  ✓ Expert Level 章节已创建: {expert_chapter_id}")
        print(f"  ✓ Advanced Foundations Review Bridge 课程已创建: {bridge_id}")
        print(f"  ✓ 4 个专家级课程已创建")
        print(f"  ✓ 现有课程状态已更新 (MCP)")
        print(f"  ✓ 所有关系已设置 (MCP)")
        print(f"  ✓ 学习路径内容已添加 (MCP)")
        print(f"  ✓ Memory Management Sub-items 已添加 (MCP)")
        print()
        
    except Exception as e:
        print(f"❌ MCP 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await stack.aclose()


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


if __name__ == "__main__":
    asyncio.run(expert_skill_full_mcp())
