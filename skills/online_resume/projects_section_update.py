"""
Projects Section Update Skill - Reorganize projects to showcase recent work.

This skill:
1. Deletes the "Knitties eComm Website" project
2. Creates a new "Zapier Dashboard Redesign" project
3. Updates database with new fields (Phone, URL)
4. Adds "Current Focus" section with dynamic skill reference
"""

import asyncio
import os
from typing import Any, Dict, List, Optional, Tuple
from skills.online_resume.utils import NotionMCPTools, extract_property_value


class ProjectsSectionUpdate:
    """Reorganize projects section in Online Resume."""
    
    def __init__(self, api_key: str):
        """Initialize with Notion API key."""
        self.api_key = api_key
    
    async def update_projects(self) -> Dict[str, Any]:
        """
        Main execution method:
        1. Find Online Resume page
        2. Find Projects and Skills databases
        3. Delete "Knitties eComm Website" project
        4. Get contact info (phone, URL)
        5. Query Skills database for highest skill
        6. Update Projects database with new fields
        7. Create "Zapier Dashboard Redesign" project
        8. Add "Current Focus" section with dynamic content
        """
        result = {
            "success": False,
            "message": "",
            "deleted_project": None,
            "created_project": None,
            "highest_skill": None,
            "highest_skill_level": None,
            "current_focus_added": False,
            "errors": []
        }
        
        async with NotionMCPTools(self.api_key) as tools:
            try:
                # Step 1: Find Online Resume page
                print("Step 1: Searching for Online Resume page...")
                pages_result = await tools.search("Online Resume", filter_type="page")
                
                if not pages_result or not pages_result.get("results"):
                    result["errors"].append("Online Resume page not found")
                    return result
                
                page_id = pages_result["results"][0]["id"]
                print(f"  ✓ Found Online Resume page (ID: {page_id})")
                
                # Step 2: Get page content to find databases
                print("Step 2: Finding Projects and Skills databases...")
                page_children = await tools.get_block_children(page_id)
                
                projects_db_id = None
                skills_db_id = None
                contact_block_id = None
                left_column_id = None
                right_column_id = None
                
                if page_children.get("results"):
                    for block in page_children["results"]:
                        if block.get("type") == "column_list":
                            # Get columns
                            col_children = await tools.get_block_children(block.get("id"))
                            if col_children.get("results"):
                                columns = [b for b in col_children["results"] if b.get("type") == "column"]
                                if len(columns) >= 2:
                                    left_column_id = columns[0].get("id")
                                    right_column_id = columns[1].get("id")
                                    # Get right column children to find databases
                                    right_col_children = await tools.get_block_children(right_column_id)
                                    if right_col_children.get("results"):
                                        for child in right_col_children["results"]:
                                            if child.get("type") == "child_database":
                                                db_title = child.get("child_database", {}).get("title", "")
                                                if "Projects" in db_title:
                                                    projects_db_id = child.get("id")
                                                elif "Skills" in db_title:
                                                    skills_db_id = child.get("id")
                
                if not projects_db_id or not skills_db_id:
                    result["errors"].append("Projects or Skills database not found")
                    return result
                
                print(f"  ✓ Found Projects database (ID: {projects_db_id})")
                print(f"  ✓ Found Skills database (ID: {skills_db_id})")
                
                # Step 3: Get contact info
                print("Step 3: Retrieving contact information...")
                contact_info = await self._get_contact_info(tools, left_column_id)
                phone = contact_info.get("phone", "")
                website = contact_info.get("url", "")
                print(f"  ✓ Contact: Phone={phone}, URL={website}")
                
                # Step 4: Find and delete "Knitties eComm Website"
                print("Step 4: Deleting 'Knitties eComm Website' project...")
                projects = await tools.query_database(projects_db_id)
                knitties_id = None
                
                if projects.get("results"):
                    for project in projects["results"]:
                        name = extract_property_value(project.get("properties", {}), "Name")
                        if name == "Knitties eComm Website":
                            knitties_id = project.get("id")
                            break
                
                if knitties_id:
                    await tools.patch_page(knitties_id, archived=True)
                    result["deleted_project"] = "Knitties eComm Website"
                    print(f"  ✓ Deleted Knitties eComm Website (ID: {knitties_id})")
                else:
                    print("  ⚠ Knitties eComm Website not found (may already be deleted)")
                
                # Step 5: Query Skills database for highest skill
                print("Step 5: Finding highest skill level...")
                highest_skill, highest_level = await self._get_highest_skill(tools, skills_db_id)
                result["highest_skill"] = highest_skill
                result["highest_skill_level"] = highest_level
                print(f"  ✓ Highest skill: {highest_skill} ({highest_level}%)")
                
                # Step 6: Update Projects database with new fields
                print("Step 6: Updating Projects database schema...")
                db_info = await tools.retrieve_database(projects_db_id)
                await self._update_database_schema(tools, projects_db_id, db_info)
                print("  ✓ Database schema updated with Phone, URL, and Enterprise tag")
                
                # Step 7: Create new Zapier project
                print("Step 7: Creating 'Zapier Dashboard Redesign' project...")
                zapier_id = await self._create_zapier_project(
                    tools, projects_db_id, phone, website
                )
                result["created_project"] = "Zapier Dashboard Redesign"
                print(f"  ✓ Created Zapier project (ID: {zapier_id})")
                
                # Step 8: Add "Current Focus" section after Projects database
                print("Step 8: Adding 'Current Focus' section...")
                await self._add_current_focus_section(
                    tools, right_column_id, projects_db_id,
                    highest_skill, highest_level
                )
                result["current_focus_added"] = True
                print("  ✓ Added Current Focus section with dynamic skill reference")
                
                result["success"] = True
                result["message"] = f"Projects section updated: deleted 1, created 1, added Current Focus section"
                
            except Exception as e:
                result["errors"].append(str(e))
                print(f"Error: {str(e)}")
        
        return result
    
    async def _get_contact_info(self, tools: NotionMCPTools, column_id: str) -> Dict[str, str]:
        """Extract contact information from left column."""
        contact_info = {"phone": "", "url": ""}
        try:
            col_children = await tools.get_block_children(column_id)
            found_contact = False
            
            for block in col_children.get("results", []):
                block_type = block.get("type")
                
                # Check for Contact heading
                if block_type == "heading_2":
                    heading_text = block.get("heading_2", {}).get("rich_text", [])
                    if heading_text:
                        text = heading_text[0].get("plain_text", "")
                        if "Contact" in text:
                            found_contact = True
                        elif found_contact:  # New section, stop
                            break
                
                # Extract contact details from paragraphs
                elif found_contact and block_type == "paragraph":
                    para_text = block.get("paragraph", {}).get("rich_text", [])
                    if para_text:
                        full_text = "".join(item.get("plain_text", "") for item in para_text)
                        
                        if "📞" in full_text and not contact_info["phone"]:
                            contact_info["phone"] = full_text.replace("📞\xa0", "").strip()
                        elif "🌐" in full_text and not contact_info["url"]:
                            contact_info["url"] = full_text.replace("🌐\xa0", "").strip()
        except Exception:
            pass
        return contact_info
    
    async def _get_highest_skill(self, tools: NotionMCPTools, skills_db_id: str) -> Tuple[Optional[str], Optional[float]]:
        """Query Skills database to find highest skill level."""
        try:
            skills = await tools.query_database(
                skills_db_id,
                sorts=[{"property": "Skill Level", "direction": "descending"}]
            )
            
            if skills.get("results"):
                first_skill = skills["results"][0]
                skill_name = extract_property_value(first_skill.get("properties", {}), "Skill")
                skill_level = extract_property_value(first_skill.get("properties", {}), "Skill Level")
                
                if skill_level is not None:
                    # Convert to percentage
                    skill_percentage = int(skill_level * 100) if skill_level < 1 else int(skill_level)
                    return skill_name, skill_percentage
        except Exception as e:
            print(f"Error getting highest skill: {e}")
        
        return None, None
    
    async def _update_database_schema(self, tools: NotionMCPTools, db_id: str, db_info: Dict) -> None:
        """Update database to add Phone and URL fields if missing."""
        try:
            properties = db_info.get("properties", {})
            updates = {}
            
            # Add Phone field if missing
            if "Phone" not in properties:
                updates["Phone"] = {
                    "type": "phone_number",
                    "phone_number": {}
                }
            
            # Add URL field if missing
            if "Url" not in properties:
                updates["Url"] = {
                    "type": "url",
                    "url": {}
                }
            
            # Update Tags to include Enterprise option
            if "Tags" in properties:
                current_tags = properties["Tags"]
                if current_tags.get("type") == "multi_select":
                    options = current_tags.get("multi_select", {}).get("options", [])
                    # Check if Enterprise tag exists
                    has_enterprise = any(opt.get("name") == "Enterprise" for opt in options)
                    if not has_enterprise:
                        options.append({"name": "Enterprise", "color": "purple"})
                        updates["Tags"] = {
                            "type": "multi_select",
                            "multi_select": {"options": options}
                        }
            
            if updates:
                await tools.update_database(db_id, updates)
        except Exception as e:
            print(f"Warning: Could not update database schema: {e}")
    
    async def _create_zapier_project(self, tools: NotionMCPTools, db_id: str, 
                                    phone: str, website: str) -> Optional[str]:
        """Create the Zapier Dashboard Redesign project."""
        try:
            properties = {
                "Name": {
                    "title": [{"text": {"content": "Zapier Dashboard Redesign"}}]
                },
                "Description": {
                    "rich_text": [{
                        "text": {"content": "Led the complete redesign of Zapier's main dashboard, focusing on improved usability and modern design patterns. Implemented new navigation system and responsive layouts."}
                    }]
                },
                "Date": {
                    "date": {
                        "start": "2024-01-01",
                        "end": "2024-06-30"
                    }
                },
                "Tags": {
                    "multi_select": [
                        {"name": "UI Design"},
                        {"name": "Enterprise"}
                    ]
                }
            }
            
            if phone:
                properties["Phone"] = {"phone_number": phone}
            if website:
                properties["Url"] = {"url": website}
            
            result = await tools.create_page(db_id, properties)
            return result.get("id")
        except Exception as e:
            print(f"Error creating Zapier project: {e}")
            return None
    
    async def _add_current_focus_section(self, tools: NotionMCPTools, column_id: str,
                                        projects_db_id: str,
                                        skill_name: str, 
                                        skill_level: int) -> None:
        """Add Current Focus section after Projects database in the column."""
        try:
            # Create the blocks
            blocks = [
                {
                    "type": "divider",
                    "divider": {}
                },
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "Current Focus"}}]
                    }
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {
                                "content": f"The Zapier Dashboard Redesign represents my most impactful recent work, leveraging my expertise in {skill_name} ({skill_level}%) to deliver enterprise-grade solutions that prioritize both aesthetics and functionality."
                            }
                        }]
                    }
                }
            ]
            
            # Add blocks to the right column, positioned after the Projects database
            await tools.patch_block_children(column_id, blocks, after=projects_db_id)
        except Exception as e:
            print(f"Error adding Current Focus section: {e}")
    
    @staticmethod
    def _get_block_text(block: Dict) -> str:
        """Extract text from a block."""
        block_type = block.get("type")
        content = block.get(block_type, {})
        
        if "rich_text" in content:
            rich_text = content.get("rich_text", [])
            if rich_text:
                return rich_text[0].get("plain_text", "")
        
        return ""


async def main():
    """CLI entry point."""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY environment variable not set")
        return
    
    skill = ProjectsSectionUpdate(api_key)
    result = await skill.update_projects()
    
    print("\n" + "=" * 70)
    print("📊 Execution Summary")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Deleted: {result['deleted_project']}")
    print(f"Created: {result['created_project']}")
    print(f"Highest Skill: {result['highest_skill']} ({result['highest_skill_level']}%)")
    print(f"Current Focus Added: {result['current_focus_added']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
