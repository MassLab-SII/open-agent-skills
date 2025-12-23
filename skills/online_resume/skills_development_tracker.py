"""
Skills Development Tracker Skill - Create comprehensive skills audit system.

This skill performs the following operations:
1. Searches for Skills database
2. Searches for Online Resume page
3. Gets block structure (columns) from page
4. Finds Skills database block in right column
5. Queries Skills database for skills with proficiency < 70%
6. Creates a new "Skills Development Tracker" database as child of Online Resume page
7. Updates database with rollup and formula properties
8. Creates development plan entries for each skill below 70%
9. Adds a callout block after the Skills section highlighting focus areas

This implementation follows the exact MCP API call sequence from the successful trajectory.
"""

import asyncio
import os
import json
from typing import Any, Dict, List, Optional
from utils import NotionMCPTools, extract_property_value


class SkillsDevelopmentTracker:
    """Create comprehensive skills audit system with development tracking."""
    
    def __init__(self, api_key: str):
        """Initialize with Notion API key."""
        self.api_key = api_key
    
    async def execute(self) -> Dict[str, Any]:
        """
        Main execution method - 10 step process from successful trajectory:
        1. Search for Skills database
        2. Search for Online Resume page
        3. Get block children (column_list) from page
        4. Get columns from column_list
        5. Get right column children to find Skills database block
        6. Query Skills database for skills < 70% proficiency
        7. Create Skills Development Tracker database
        8. Update database with additional properties (rollup, formula)
        9. Create entries for each skill below 70%
        10. Add callout block after Skills database
        """
        result = {
            "success": False,
            "message": "",
            "tracker_db_id": None,
            "entries_created": 0,
            "skills_tracked": [],
            "callout_added": False,
            "errors": []
        }
        
        async with NotionMCPTools(self.api_key) as tools:
            try:
                # Step 1: Search for Skills database
                print("Step 1: Searching for Skills database...")
                skills_search = await tools.search("Skills", filter_type="database")
                if not skills_search or not skills_search.get("results"):
                    result["errors"].append("Skills database not found")
                    return result
                
                skills_db_id = skills_search["results"][0]["id"]
                print(f"  ✓ Found Skills database (ID: {skills_db_id})")
                
                # Step 2: Search for Online Resume page
                print("Step 2: Searching for Online Resume page...")
                resume_search = await tools.search("Resume", filter_type="page")
                if not resume_search or not resume_search.get("results"):
                    result["errors"].append("Online Resume page not found")
                    return result
                
                page_id = resume_search["results"][0]["id"]
                print(f"  ✓ Found Online Resume page (ID: {page_id})")
                
                # Step 3: Get block children (column_list) from page
                print("Step 3: Getting page structure...")
                page_blocks = await tools.get_block_children(page_id)
                
                column_list_id = None
                if page_blocks.get("results"):
                    for block in page_blocks["results"]:
                        if block.get("type") == "column_list":
                            column_list_id = block.get("id")
                            break
                
                if not column_list_id:
                    result["errors"].append("Column list not found in page")
                    return result
                
                print(f"  ✓ Found column_list (ID: {column_list_id})")
                
                # Step 4: Get columns from column_list
                print("Step 4: Getting columns...")
                col_list_blocks = await tools.get_block_children(column_list_id)
                
                right_column_id = None
                if col_list_blocks.get("results"):
                    columns = [b for b in col_list_blocks["results"] if b.get("type") == "column"]
                    if len(columns) >= 2:
                        right_column_id = columns[1].get("id")
                
                if not right_column_id:
                    result["errors"].append("Right column not found")
                    return result
                
                print(f"  ✓ Found right column (ID: {right_column_id})")
                
                # Step 5: Get right column children to find Skills database block
                print("Step 5: Finding Skills database block in right column...")
                right_col_blocks = await tools.get_block_children(right_column_id)
                
                skills_db_block_id = None
                if right_col_blocks.get("results"):
                    for block in right_col_blocks["results"]:
                        if block.get("type") == "child_database":
                            db_title = block.get("child_database", {}).get("title", "")
                            if "Skills" in db_title:
                                skills_db_block_id = block.get("id")
                                break
                
                if not skills_db_block_id:
                    result["errors"].append("Skills database block not found")
                    return result
                
                print(f"  ✓ Found Skills database block (ID: {skills_db_block_id})")
                
                # Step 6: Query Skills database for skills < 70% proficiency
                print("Step 6: Querying skills below 70% proficiency...")
                skills_below_70 = await self._query_skills_below_70(tools, skills_db_id)
                print(f"  ✓ Found {len(skills_below_70)} skills below 70%")
                for skill in skills_below_70:
                    print(f"    - {skill['name']}: {skill['level']*100:.0f}%")
                
                # Step 7: Create Skills Development Tracker database
                print("Step 7: Creating Skills Development Tracker database...")
                tracker_db_id = await self._create_tracker_database(
                    tools, page_id, skills_db_id
                )
                
                if not tracker_db_id:
                    result["errors"].append("Failed to create tracker database")
                    return result
                
                result["tracker_db_id"] = tracker_db_id
                print(f"  ✓ Created tracker database (ID: {tracker_db_id})")
                
                # Step 8: Update database with additional properties
                print("Step 8: Updating database properties...")
                await self._update_tracker_database(tools, tracker_db_id)
                print(f"  ✓ Added rollup and formula properties")
                
                # Step 9: Create entries for each skill below 70%
                print("Step 9: Creating development plan entries...")
                for skill in skills_below_70:
                    try:
                        entry_id = await self._create_tracker_entry(
                            tools, tracker_db_id, skill
                        )
                        result["entries_created"] += 1
                        result["skills_tracked"].append(skill["name"])
                        print(f"  ✓ Created entry for {skill['name']} (ID: {entry_id})")
                    except Exception as e:
                        result["errors"].append(f"Failed to create entry for {skill['name']}: {e}")
                
                # Step 10: Add callout block after Skills database
                print("Step 10: Adding focus areas callout block...")
                if len(skills_below_70) > 0:
                    # Get 3 skills with lowest proficiency
                    focus_skills = sorted(skills_below_70, key=lambda x: x["level"])[:3]
                    focus_skill_names = [s["name"] for s in focus_skills]
                    
                    callout_added = await self._add_callout_block(
                        tools, right_column_id, skills_db_block_id, focus_skill_names
                    )
                    result["callout_added"] = callout_added
                    if callout_added:
                        print(f"  ✓ Added callout block with focus areas: {', '.join(focus_skill_names)}")
                
                result["success"] = True
                result["message"] = f"Successfully created Skills Development Tracker with {result['entries_created']} entries"
                
            except Exception as e:
                result["errors"].append(f"Execution error: {e}")
                print(f"  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def _create_tracker_database(
        self, 
        tools: NotionMCPTools, 
        page_id: str, 
        skills_db_id: str
    ) -> str:
        """Step 7: Create Skills Development Tracker database with basic properties."""
        
        # Define database properties (without rollup/formula which are added in step 8)
        basic_properties = {
            "Name": {
                "title": {}
            },
            "Current Skill": {
                "relation": {
                    "database_id": skills_db_id,
                    "type": "single_property",
                    "single_property": {}
                }
            },
            "Target Proficiency": {
                "number": {
                    "format": "percent"
                }
            },
            "Learning Resources": {
                "rich_text": {}
            },
            "Progress Notes": {
                "rich_text": {}
            }
        }
        
        try:
            result = await tools.create_database(
                parent_id=page_id,
                title="Skills Development Tracker",
                properties=basic_properties
            )
            
            db_id = result.get("id", "") if isinstance(result, dict) else ""
            return db_id
        except Exception as e:
            print(f"  ❌ Failed to create tracker database: {e}")
            return ""
    
    async def _update_tracker_database(
        self, 
        tools: NotionMCPTools, 
        tracker_db_id: str
    ) -> None:
        """Step 8: Update database with rollup and formula properties."""
        
        try:
            # Add Current Proficiency rollup property (show_original to get the actual number)
            rollup_properties = {
                "Current Proficiency": {
                    "rollup": {
                        "relation_property_name": "Current Skill",
                        "rollup_property_name": "Skill Level",
                        "function": "show_original"
                    }
                }
            }
            await tools.update_database(tracker_db_id, rollup_properties)
            
            # Add Gap formula property
            # Use toNumber() to convert the rollup result to number for subtraction
            formula_properties = {
                "Gap": {
                    "formula": {
                        "expression": "prop(\"Target Proficiency\") - toNumber(prop(\"Current Proficiency\"))"
                    }
                }
            }
            await tools.update_database(tracker_db_id, formula_properties)
        except Exception as e:
            print(f"  ⚠ Warning: Could not add all properties: {e}")
    
    async def _query_skills_below_70(self, tools: NotionMCPTools, skills_db_id: str) -> List[Dict[str, Any]]:
        """Step 6: Query Skills database for skills with proficiency below 70%."""
        skills = []
        
        filter_obj = {
            "property": "Skill Level",
            "number": {
                "less_than": 0.7
            }
        }
        
        query_result = await tools.query_database(skills_db_id, filter_obj)
        
        if query_result.get("results"):
            for skill in query_result["results"]:
                props = skill.get("properties", {})
                
                # Extract skill name from title property
                name_prop = props.get("Skill", {}).get("title", [])
                if not name_prop:
                    continue
                skill_name = name_prop[0].get("text", {}).get("content", "")
                
                # Extract proficiency level
                level = props.get("Skill Level", {}).get("number", 1.0)
                
                if level < 0.7:
                    skills.append({
                        "id": skill.get("id"),
                        "name": skill_name,
                        "level": level,
                        "type": extract_property_value(props, "Type")
                    })
        
        return skills
    
    async def _create_tracker_entry(
        self, 
        tools: NotionMCPTools, 
        tracker_db_id: str,
        skill: Dict[str, Any]
    ) -> str:
        """Step 9: Create a single entry in Skills Development Tracker."""
        
        # Calculate target proficiency (current + 25%, capped at 95%)
        current_level = skill["level"]
        target_level = min(current_level + 0.25, 0.95)
        
        # Create page properties following the successful trajectory format
        properties = {
            "Name": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"{skill['name']} Development Plan"
                        }
                    }
                ]
            },
            "Current Skill": {
                "relation": [
                    {
                        "id": skill["id"]
                    }
                ]
            },
            "Target Proficiency": {
                "number": target_level
            },
            "Learning Resources": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Online courses and practice projects"
                        }
                    }
                ]
            },
            "Progress Notes": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": "Initial assessment completed"
                        }
                    }
                ]
            }
        }
        
        result = await tools.create_page(
            parent_database_id=tracker_db_id,
            properties=properties
        )
        
        return result.get("id", "")
    
    async def _add_callout_block(
        self,
        tools: NotionMCPTools,
        column_id: str,
        skills_db_block_id: str,
        focus_skill_names: List[str]
    ) -> bool:
        """Step 10: Add callout block after Skills database section."""
        try:
            # Create callout content
            callout_content = f"Focus Areas: {', '.join(focus_skill_names)}"
            
            # Prepare callout block children for patch_block_children
            children = [
                {
                    "callout": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": callout_content
                                },
                                "type": "text"
                            }
                        ],
                        "icon": {
                            "emoji": "🎯",
                            "type": "emoji"
                        },
                        "color": "blue_background"
                    },
                    "type": "callout"
                }
            ]
            
            # Add the callout block after Skills database
            result = await tools.patch_block_children(column_id, children, skills_db_block_id)
            
            return result.get("object") == "list" or result.get("results") is not None
        
        except Exception as e:
            print(f"  ⚠ Failed to add callout block: {e}")
            return False


async def main():
    """Main entry point."""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY environment variable not set")
        return
    
    tracker = SkillsDevelopmentTracker(api_key)
    result = await tracker.execute()
    
    # Print results
    print("\n" + "="*60)
    if result["success"]:
        print("✅ SUCCESS: Skills Development Tracker created")
        print(f"   Tracker Database ID: {result['tracker_db_id']}")
        print(f"   Entries Created: {result['entries_created']}")
        print(f"   Skills Tracked: {', '.join(result['skills_tracked'])}")
        print(f"   Callout Block Added: {result['callout_added']}")
    else:
        print("❌ FAILED: Skills Development Tracker creation failed")
        if result["errors"]:
            print("   Errors:")
            for error in result["errors"]:
                print(f"   - {error}")
    print("="*60)
    
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
