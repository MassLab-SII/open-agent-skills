#!/usr/bin/env python3
"""
Employee Onboarding System Skill for Company In A Box
Following the official implementation pattern from o3 run-3

This skill creates a comprehensive employee onboarding system including:
1. Employee Onboarding Checklist database with 3 sample employees
2. Onboarding Hub page with benefits overview, 30-day timeline, and feedback form
3. All content added via children parameter in page creation (official approach)
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Import utils
import sys
sys.path.insert(0, os.path.dirname(__file__))
from utils import NotionMCPTools

load_dotenv()


class EmployeeOnboarding:
    """Employee Onboarding System Implementation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EVAL_NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("EVAL_NOTION_API_KEY environment variable not set")
    
    async def setup_onboarding(self) -> Dict[str, Any]:
        """
        Set up the complete employee onboarding system.
        Follows official implementation pattern from o3 run-3.
        
        Returns:
            Dict with success status, IDs, and any errors
        """
        result = {
            "success": False,
            "checklist_db_id": None,
            "onboarding_hub_id": None,
            "employees_created": 0,
            "errors": []
        }
        
        try:
            mcp = NotionMCPTools(self.api_key)
            
            async with mcp:
                # Step 1: Find Company In A Box page
                print("\n📍 Step 1: Searching for 'Company In A Box' page")
                print("-" * 70)
                
                search_result = await mcp.search("Company In A Box")
                if not search_result:
                    result["errors"].append("Company In A Box page not found")
                    return result
                
                try:
                    search_data = json.loads(search_result)
                    results = search_data.get("results", [])
                    
                    company_page_id = None
                    for item in results:
                        if item.get("object") == "page":
                            company_page_id = item.get("id")
                            break
                    
                    if not company_page_id:
                        result["errors"].append("Company In A Box page not found in search results")
                        return result
                    
                    print(f"✓ Found Company In A Box page (ID: {company_page_id})")
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Error parsing search result: {e}")
                    return result
                
                # Step 2: Find benefit policy pages
                print("\n📍 Step 2: Searching for benefit policy pages")
                print("-" * 70)
                
                benefit_names = ["Benefits policy", "Vacation Policy", "Corporate travel"]
                benefit_pages = {}
                
                for benefit_name in benefit_names:
                    search_result = await mcp.search(benefit_name)
                    if search_result:
                        try:
                            search_data = json.loads(search_result)
                            results = search_data.get("results", [])
                            
                            for item in results:
                                if item.get("object") == "page":
                                    page_title = ""
                                    try:
                                        props = item.get("properties", {})
                                        title_prop = props.get("title", {})
                                        if isinstance(title_prop, dict):
                                            title_list = title_prop.get("title", [])
                                            if title_list:
                                                page_title = title_list[0].get("plain_text", "")
                                    except:
                                        page_title = benefit_name
                                    
                                    if benefit_name.lower() in page_title.lower():
                                        benefit_pages[benefit_name] = item.get("id")
                                        print(f"  ✓ Found '{benefit_name}' page")
                                        break
                        except (json.JSONDecodeError, KeyError):
                            pass
                
                if len(benefit_pages) < 3:
                    result["errors"].append(f"Only found {len(benefit_pages)} benefit pages, need at least 3")
                    return result
                
                print(f"✓ Found {len(benefit_pages)} benefit pages")
                
                # Step 3: Create Employee Onboarding Checklist database
                print("\n📍 Step 3: Creating 'Employee Onboarding Checklist' database")
                print("-" * 70)
                
                db_properties = {
                    "Employee Name": {"title": {}},
                    "Start Date": {"date": {}},
                    "Department": {
                        "select": {
                            "options": [
                                {"name": "Product"},
                                {"name": "Marketing"},
                                {"name": "Sales"},
                                {"name": "HR"},
                                {"name": "Engineering"}
                            ]
                        }
                    }
                }
                
                create_db_result = await mcp.create_database(
                    company_page_id,
                    "Employee Onboarding Checklist",
                    db_properties
                )
                
                checklist_db_id = None
                if create_db_result:
                    try:
                        db_data = json.loads(create_db_result)
                        checklist_db_id = db_data.get("id")
                        if checklist_db_id:
                            result["checklist_db_id"] = checklist_db_id
                            print(f"✓ Created Employee Onboarding Checklist database (ID: {checklist_db_id})")
                        else:
                            result["errors"].append("Database creation response missing ID")
                            return result
                    except (json.JSONDecodeError, KeyError) as e:
                        result["errors"].append(f"Failed to parse database response: {e}")
                        return result
                else:
                    result["errors"].append("Failed to create database")
                    return result
                
                # Step 4: Create 3 sample employees
                print("\n📍 Step 4: Creating employee entries")
                print("-" * 70)
                
                employees = [
                    {"name": "Alice Johnson", "start_date": "2025-10-01", "department": "Engineering"},
                    {"name": "Bob Smith", "start_date": "2025-10-05", "department": "Marketing"},
                    {"name": "Carol Lee", "start_date": "2025-10-10", "department": "HR"}
                ]
                
                for employee in employees:
                    emp_properties = {
                        "Employee Name": {
                            "title": [
                                {
                                    "type": "text",
                                    "text": {"content": employee["name"]}
                                }
                            ]
                        },
                        "Start Date": {
                            "date": {
                                "start": employee["start_date"]
                            }
                        },
                        "Department": {
                            "select": {
                                "name": employee["department"]
                            }
                        }
                    }
                    
                    create_emp_result = await mcp.create_page(
                        checklist_db_id,
                        emp_properties,
                        parent_type="database_id"
                    )
                    
                    if create_emp_result:
                        result["employees_created"] += 1
                        print(f"  ✓ Created employee: {employee['name']}")
                    else:
                        result["errors"].append(f"Failed to create employee: {employee['name']}")
                
                # Step 5: Create Onboarding Hub page with all content blocks
                print("\n📍 Step 5: Creating 'Onboarding Hub' page with sections")
                print("-" * 70)
                
                # Build all content blocks following the official pattern
                children_blocks = []
                
                # Add empty paragraph for spacing
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": " "}
                            }
                        ]
                    }
                })
                
                # Add link_to_page block for database reference
                children_blocks.append({
                    "object": "block",
                    "type": "link_to_page",
                    "link_to_page": {
                        "database_id": checklist_db_id
                    }
                })
                
                # Benefits Overview section
                children_blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Benefits Overview"}
                            }
                        ]
                    }
                })
                
                # Add benefit pages as mentions in a paragraph
                mention_items = []
                for benefit_id in list(benefit_pages.values())[:3]:
                    mention_items.append({
                        "type": "mention",
                        "mention": {
                            "page": {"id": benefit_id}
                        }
                    })
                    mention_items.append({
                        "type": "text",
                        "text": {"content": "  "}
                    })
                
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": mention_items
                    }
                })
                
                # 30-Day Timeline section
                children_blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "30-Day Timeline"}
                            }
                        ]
                    }
                })
                
                # Timeline steps with @mentions
                timeline_steps = [
                    {"text": "Week 1: IT setup & orientation – see ", "mention_id": list(benefit_pages.values())[0]},
                    {"text": "Week 1: HR paperwork – refer to ", "mention_id": list(benefit_pages.values())[0]},
                    {"text": "Week 2: Product training through ", "mention_id": checklist_db_id, "is_db": True},
                    {"text": "Week 2: Shadow sales calls – see ", "mention_id": list(benefit_pages.values())[1] if len(benefit_pages) > 1 else None},
                    {"text": "Week 3: Join team stand-ups – reference ", "mention_id": company_page_id},
                    {"text": "Week 3: Complete security training in ", "mention_id": list(benefit_pages.values())[1] if len(benefit_pages) > 1 else None},
                    {"text": "Week 4: Submit 30-day self-review – log in ", "mention_id": list(benefit_pages.values())[2] if len(benefit_pages) > 2 else None}
                ]
                
                for step in timeline_steps:
                    rich_text = [
                        {
                            "type": "text",
                            "text": {"content": step["text"]}
                        }
                    ]
                    
                    if step.get("mention_id"):
                        if step.get("is_db"):
                            rich_text.append({
                                "type": "mention",
                                "mention": {
                                    "database": {"id": step["mention_id"]}
                                }
                            })
                        else:
                            rich_text.append({
                                "type": "mention",
                                "mention": {
                                    "page": {"id": step["mention_id"]}
                                }
                            })
                    
                    children_blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": rich_text
                        }
                    })
                
                # Feedback Form section
                children_blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Feedback Form"}
                            }
                        ]
                    }
                })
                
                # To-do items
                todo_items = [
                    "Share first-week impressions",
                    "Identify any onboarding gaps",
                    "Suggest improvements to documentation"
                ]
                
                for todo in todo_items:
                    children_blocks.append({
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": todo}
                                }
                            ],
                            "checked": False
                        }
                    })
                
                # Create Onboarding Hub page with all children blocks
                hub_properties = {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": "Onboarding Hub"}
                        }
                    ]
                }
                
                create_hub_result = await mcp.create_page(
                    company_page_id,
                    hub_properties,
                    children=children_blocks,
                    parent_type="page_id"
                )
                
                if create_hub_result:
                    try:
                        hub_data = json.loads(create_hub_result)
                        onboarding_hub_id = hub_data.get("id")
                        if onboarding_hub_id:
                            result["onboarding_hub_id"] = onboarding_hub_id
                            print(f"✓ Created Onboarding Hub page (ID: {onboarding_hub_id})")
                            print(f"  ✓ Added all sections and content ({len(children_blocks)} blocks)")
                        else:
                            result["errors"].append("Onboarding Hub creation response missing ID")
                    except (json.JSONDecodeError, KeyError) as e:
                        result["errors"].append(f"Failed to parse Onboarding Hub response: {e}")
                else:
                    result["errors"].append("Failed to create Onboarding Hub page")
                
                result["success"] = True
                return result
            
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            print(f"❌ Unexpected error: {str(e)}")
            return result


async def main():
    """Main execution function"""
    try:
        onboarding = EmployeeOnboarding()
        result = await onboarding.setup_onboarding()
        
        print("\n" + "=" * 70)
        print("📊 Execution Summary")
        print("=" * 70)
        
        print(f"Success: {result['success']}")
        print(f"Checklist Database ID: {result['checklist_db_id']}")
        print(f"Onboarding Hub ID: {result['onboarding_hub_id']}")
        print(f"Employees Created: {result['employees_created']}")
        
        if result['errors']:
            print(f"\nErrors encountered:")
            for error in result['errors']:
                print(f"  • {error}")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
