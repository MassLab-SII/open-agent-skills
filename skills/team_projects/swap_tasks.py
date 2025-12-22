#!/usr/bin/env python3
"""
Team Projects Task Swap - 100% MCP Implementation
Finds the person with most tasks and least tasks, then swaps all their assignments
"""

import asyncio
import json
import os
from typing import Optional, Dict, List, Tuple
from utils import NotionMCPTools


class SwapTasks:
    """Swap tasks between person with most and person with fewest tasks"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.mcp = None
    
    async def swap(self) -> Dict:
        """Main method to swap tasks between people with most and least tasks"""
        result = {
            "success": False,
            "message": "",
            "person_with_most": "",
            "person_with_least": "",
            "tasks_swapped": 0,
            "errors": []
        }
        
        try:
            async with NotionMCPTools(self.api_key) as tools:
                self.mcp = tools
                
                # Step 1: Find Team Projects page
                print("Step 1: Finding Team Projects page...")
                page_id = await self._find_team_projects_page()
                if not page_id:
                    result["errors"].append("Team Projects page not found")
                    return result
                print(f"  ✓ Found Team Projects page (ID: {page_id})")
                
                # Step 2: Find Tasks database
                print("Step 2: Finding Tasks database...")
                tasks_db_id = await self._find_tasks_database(page_id)
                if not tasks_db_id:
                    result["errors"].append("Tasks database not found")
                    return result
                print(f"  ✓ Found Tasks database (ID: {tasks_db_id})")
                
                # Step 3: Query all tasks and count per person
                print("Step 3: Querying all tasks and analyzing assignments...")
                all_tasks = await self._get_all_tasks(tasks_db_id)
                if not all_tasks:
                    result["errors"].append("No tasks found")
                    return result
                print(f"  ✓ Found {len(all_tasks)} total tasks")
                
                # Step 4: Count tasks per person
                print("Step 4: Analyzing task distribution...")
                task_counts = await self._count_tasks_per_person(all_tasks)
                if len(task_counts) < 2:
                    result["errors"].append("Need at least 2 people with tasks")
                    return result
                
                # Sort to find person with most and least
                sorted_counts = sorted(task_counts.items(), key=lambda x: len(x[1]))
                person_with_least_id, least_tasks = sorted_counts[0]
                person_with_most_id, most_tasks = sorted_counts[-1]
                
                result["person_with_most"] = person_with_most_id
                result["person_with_least"] = person_with_least_id
                
                print(f"  ✓ Person with MOST tasks: {person_with_most_id[:8]}... ({len(most_tasks)} tasks)")
                print(f"  ✓ Person with LEAST tasks: {person_with_least_id[:8]}... ({len(least_tasks)} tasks)")
                
                # Step 5: Swap tasks
                print("Step 5: Swapping task assignments...")
                tasks_swapped = await self._swap_task_assignments(
                    most_tasks, least_tasks,
                    person_with_most_id, person_with_least_id,
                    all_tasks
                )
                
                result["tasks_swapped"] = tasks_swapped
                result["success"] = True
                result["message"] = f"Successfully swapped {tasks_swapped} tasks between {person_with_most_id[:8]}... and {person_with_least_id[:8]}..."
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"Error: {str(e)}")
        
        return result
    
    async def _find_team_projects_page(self) -> Optional[str]:
        """Search for Team Projects page"""
        try:
            response = await self.mcp.search("Team Projects")
            if not response:
                return None
            
            data = json.loads(response)
            for item in data.get("results", []):
                if item.get("object") == "page":
                    title = self._get_page_title(item)
                    if "Team Projects" in title:
                        return item.get("id")
        except Exception as e:
            print(f"Error finding Team Projects: {e}")
        
        return None
    
    async def _find_tasks_database(self, page_id: str) -> Optional[str]:
        """Find Tasks database in Team Projects page"""
        try:
            response = await self.mcp.get_block_children(page_id)
            if not response:
                return None
            
            data = json.loads(response)
            for block in data.get("results", []):
                if block.get("type") == "child_database":
                    db_title = block.get("child_database", {}).get("title", "")
                    if "Tasks" in db_title:
                        return block.get("id")
        except Exception as e:
            print(f"Error finding Tasks database: {e}")
        
        return None
    
    async def _get_all_tasks(self, tasks_db_id: str) -> List[Dict]:
        """Get all tasks from the Tasks database"""
        try:
            response = await self.mcp.query_database(tasks_db_id)
            if not response:
                return []
            
            data = json.loads(response)
            return data.get("results", [])
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    async def _count_tasks_per_person(self, all_tasks: List[Dict]) -> Dict[str, List[Dict]]:
        """Count tasks per person"""
        task_counts = {}
        
        for task in all_tasks:
            try:
                assignees = task.get("properties", {}).get("Assigned", {}).get("people", [])
                if assignees:
                    assignee_id = assignees[0].get("id")
                    if assignee_id not in task_counts:
                        task_counts[assignee_id] = []
                    task_counts[assignee_id].append(task)
            except Exception:
                continue
        
        return task_counts
    
    async def _swap_task_assignments(self, most_tasks: List[Dict], least_tasks: List[Dict],
                                     person_with_most_id: str, person_with_least_id: str,
                                     all_tasks: List[Dict]) -> int:
        """Swap task assignments between two people"""
        tasks_swapped = 0
        
        try:
            # Assign most_tasks to person_with_least_id
            for task in most_tasks:
                task_id = task.get("id")
                try:
                    await self.mcp.patch_page(task_id, {
                        "properties": {
                            "Assigned": {
                                "people": [{"id": person_with_least_id}]
                            }
                        }
                    })
                    tasks_swapped += 1
                except Exception as e:
                    print(f"  ⚠ Error updating task {task_id}: {e}")
            
            # Assign least_tasks to person_with_most_id
            for task in least_tasks:
                task_id = task.get("id")
                try:
                    await self.mcp.patch_page(task_id, {
                        "properties": {
                            "Assigned": {
                                "people": [{"id": person_with_most_id}]
                            }
                        }
                    })
                    tasks_swapped += 1
                except Exception as e:
                    print(f"  ⚠ Error updating task {task_id}: {e}")
            
            print(f"  ✓ Swapped {tasks_swapped} task assignments")
        
        except Exception as e:
            print(f"Error during task swap: {e}")
        
        return tasks_swapped
    
    @staticmethod
    def _get_page_title(page: Dict) -> str:
        """Extract page title from page object"""
        try:
            properties = page.get("properties", {})
            for prop_name, prop_data in properties.items():
                if prop_data.get("type") == "title":
                    title_array = prop_data.get("title", [])
                    if title_array:
                        return title_array[0].get("text", {}).get("content", "")
        except Exception:
            pass
        return ""


async def main():
    """CLI entry point"""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY environment variable not set")
        return
    
    skill = SwapTasks(api_key)
    result = await skill.swap()
    
    print("\n" + "=" * 70)
    print("📊 Execution Summary")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Person with Most Tasks: {result['person_with_most']}")
    print(f"Person with Least Tasks: {result['person_with_least']}")
    print(f"Tasks Swapped: {result['tasks_swapped']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
