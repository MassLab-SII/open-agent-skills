#!/usr/bin/env python3
"""
Expert Level Lessons Skill - 100% MCP Implementation
Uses pure MCP tools from utils.py
"""
import asyncio
import json
import os
import re
from utils import NotionMCPTools

def extract_page_id(result_text):
    """Extract page ID from MCP result text"""
    if not result_text:
        return None
    try:
        data = json.loads(result_text)
        if "id" in data:
            return data["id"]
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r'"id":"([^"]+)"', result_text)
    return match.group(1) if match else None

def parse_courses(response_text):
    """Parse courses from database query response"""
    if not response_text:
        return {}
    
    try:
        data = json.loads(response_text)
        courses = {}
        
        for item in data.get("results", []):
            lessons_field = item["properties"].get("Lessons", {})
            if lessons_field.get("type") == "title" and lessons_field.get("title"):
                title = lessons_field["title"][0]["text"]["content"]
                status = item["properties"].get("Status", {}).get("status", {}).get("name", "")
                courses[title] = {"id": item["id"], "status": status}
        
        return courses
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}

def parse_chapters(response_text):
    """Parse chapters from database query response"""
    if not response_text:
        return {}
    
    try:
        data = json.loads(response_text)
        chapters = {}
        
        for item in data.get("results", []):
            name_field = item["properties"].get("Name", {})
            if name_field.get("type") == "title" and name_field.get("title"):
                name = name_field["title"][0]["text"]["content"]
                chapters[name] = item["id"]
        
        return chapters
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}

def discover_databases(search_result):
    """Discover and identify database IDs from search results"""
    if not search_result:
        return None, None
    
    try:
        data = json.loads(search_result)
        databases = []
        
        for result in data.get("results", []):
            if result.get("object") == "database":
                databases.append(result["id"])
        
        return databases if len(databases) >= 2 else (None, None)
    except (json.JSONDecodeError, KeyError):
        return None, None

async def identify_database_types(mcp_tools, database_ids):
    """Identify which database is chapters vs steps by querying content"""
    chapters_db_id = None
    steps_db_id = None
    
    for db_id in database_ids:
        query_result = await mcp_tools.query_database(db_id)
        if query_result:
            try:
                data = json.loads(query_result)
                if data.get("results"):
                    first_item = data["results"][0]
                    properties = list(first_item.get("properties", {}).keys())
                    
                    # Simple heuristic: chapters DB has fewer properties
                    if "Name" in properties and len(properties) < 5:
                        chapters_db_id = db_id
                    elif "Lessons" in properties or len(properties) >= 5:
                        steps_db_id = db_id
            except (json.JSONDecodeError, KeyError):
                continue
    
    return chapters_db_id, steps_db_id

async def expert_level_lessons_skill():
    """Main skill execution - simplified"""
    
    print("🚀 Expert Level Lessons Skill - 100% MCP")
    print("=" * 50)
    
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("❌ API key not found")
        return
    
    async with NotionMCPTools(api_key) as mcp:
        # Step 1: Discover databases
        print("🔍 Discovering databases...")
        search_result = await mcp.search("")
        database_ids = discover_databases(search_result)
        
        if not database_ids or len(database_ids) < 2:
            print("❌ Could not find databases")
            return
        
        chapters_db_id, steps_db_id = await identify_database_types(mcp, database_ids)
        
        if not chapters_db_id or not steps_db_id:
            print("❌ Could not identify database types")
            return
        
        print(f"✓ Chapters DB: {chapters_db_id}")
        print(f"✓ Steps DB: {steps_db_id}")
        
        # Step 2: Query existing content
        print("\n📊 Querying existing content...")
        courses_data = await mcp.query_database(steps_db_id)
        chapters_data = await mcp.query_database(chapters_db_id)
        
        existing_courses = parse_courses(courses_data)
        existing_chapters = parse_chapters(chapters_data)
        
        print(f"✓ Found {len(existing_courses)} courses, {len(existing_chapters)} chapters")
        
        # Get course IDs for relationships
        control_flow_id = existing_courses.get("Control Flow", {}).get("id", "")
        decorators_id = existing_courses.get("Decorators", {}).get("id", "")
        calling_api_id = existing_courses.get("Calling API", {}).get("id", "")
        regex_id = existing_courses.get("Regular Expressions", {}).get("id", "")
        error_handling_id = existing_courses.get("Error Handling", {}).get("id", "")
        data_structures_id = existing_courses.get("Data Structures", {}).get("id", "")
        
        # Find OOP course
        oops_id = None
        for title, info in existing_courses.items():
            if "OOP" in title or "Object" in title:
                oops_id = info["id"]
                break
        
        # Step 3: Create Expert Level chapter
        print("\n📝 Creating Expert Level chapter...")
        chapter_result = await mcp.create_page(
            chapters_db_id,
            {"Name": [{"text": {"content": "Expert Level"}}]},
            "🟣"
        )
        expert_chapter_id = extract_page_id(chapter_result)
        
        if not expert_chapter_id:
            print("❌ Failed to create chapter")
            return
        
        print(f"✓ Created chapter: {expert_chapter_id}")
        
        # Step 4: Create Bridge course
        print("\n🌉 Creating Bridge course...")
        bridge_properties = {
            "Lessons": [{"text": {"content": "Advanced Foundations Review"}}],
            "Status": {"name": "Done"},
            "Chapters": [{"id": expert_chapter_id}]
        }
        
        if control_flow_id:
            bridge_properties["Parent item"] = [{"id": control_flow_id}]
        
        # Add sub-items
        sub_items = []
        for course_id in [decorators_id, calling_api_id, regex_id]:
            if course_id:
                sub_items.append({"id": course_id})
        
        if sub_items:
            bridge_properties["Sub-item"] = sub_items
        
        bridge_result = await mcp.create_page(steps_db_id, bridge_properties)
        bridge_id = extract_page_id(bridge_result)
        
        if bridge_id:
            print(f"✓ Created bridge course: {bridge_id}")
        
        # Step 5: Create expert courses
        print("\n🎓 Creating expert courses...")
        expert_courses = [
            {"title": "Metaprogramming and AST Manipulation", "date": "2025-09-15", "status": "To Do", "parent": bridge_id},
            {"title": "Async Concurrency Patterns", "date": "2025-09-20", "status": "To Do", "parent": calling_api_id},
            {"title": "Memory Management and GC Tuning", "date": "2025-09-25", "status": "In Progress", "parent": bridge_id},
            {"title": "Building Python C Extensions", "date": "2025-10-01", "status": "To Do", "parent": None}
        ]
        
        expert_course_ids = {}
        
        for course in expert_courses:
            properties = {
                "Lessons": [{"text": {"content": course["title"]}}],
                "Status": {"name": course["status"]},
                "Date": {"start": course["date"]},
                "Chapters": [{"id": expert_chapter_id}]
            }
            
            if course["parent"]:
                properties["Parent item"] = [{"id": course["parent"]}]
            
            result = await mcp.create_page(steps_db_id, properties)
            course_id = extract_page_id(result)
            
            if course_id:
                expert_course_ids[course["title"]] = course_id
                print(f"✓ {course['title']}")
        
        # Step 6: Update existing course status
        print("\n🔄 Updating course status...")
        status_updates = [
            (decorators_id, "Decorators"),
            (control_flow_id, "Control Flow")
        ]
        
        for course_id, name in status_updates:
            if course_id:
                await mcp.update_page(course_id, {"Status": {"status": {"name": "Done"}}})
                print(f"✓ Updated {name} to Done")
        
        # Step 7: Set course relationships
        print("\n🔗 Setting course relationships...")
        
        # Error Handling -> Async Concurrency Patterns
        if error_handling_id and "Async Concurrency Patterns" in expert_course_ids:
            await mcp.update_page(error_handling_id, {
                "Sub-item": [{"id": expert_course_ids["Async Concurrency Patterns"]}]
            })
            print("✓ Added Async Concurrency as Error Handling sub-item")
        
        # Building C Extensions -> Metaprogramming
        if "Building Python C Extensions" in expert_course_ids and "Metaprogramming and AST Manipulation" in expert_course_ids:
            await mcp.update_page(expert_course_ids["Building Python C Extensions"], {
                "Parent item": [{"id": expert_course_ids["Metaprogramming and AST Manipulation"]}]
            })
            print("✓ Set Metaprogramming as C Extensions parent")
        
        # Memory Management -> Data Structures + OOP
        if "Memory Management and GC Tuning" in expert_course_ids and data_structures_id and oops_id:
            await mcp.update_page(expert_course_ids["Memory Management and GC Tuning"], {
                "Sub-item": [{"id": data_structures_id}, {"id": oops_id}]
            })
            print("✓ Added Data Structures and OOP as Memory Management sub-items")
        
        # Step 8: Add content to Bridge course
        if bridge_id:
            print("\n📄 Adding content to Bridge course...")
            await mcp.add_heading(bridge_id, 2, "Prerequisites Checklist")
            await mcp.add_bullet_list(bridge_id, [
                "✅ Advanced Python Features (Decorators, Context Managers)",
                "✅ API Integration and Async Basics",  
                "✅ Pattern Matching and Text Processing"
            ])
            await mcp.add_paragraph(bridge_id,
                "This lesson serves as a checkpoint before entering expert-level content. "
                "Ensure you have mastered all prerequisites listed above."
            )
            print("✓ Added prerequisites content")
        
        print("\n" + "=" * 50)
        print("✅ Expert Level Lessons Skill completed!")
        print(f"📊 Created: 1 chapter, {len(expert_course_ids) + 1} courses")
        print("🎯 All operations completed using 100% MCP")

if __name__ == "__main__":
    asyncio.run(expert_level_lessons_skill())