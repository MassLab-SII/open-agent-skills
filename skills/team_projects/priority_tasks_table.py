#!/usr/bin/env python3
"""
Priority Tasks Table Creator - 100% MCP Implementation
========================================================

Creates a five-column table in the Team Projects page that lists all tasks
meeting either condition:
1. Progress is 50% or less
2. Task has priority P0 but is not yet completed (progress not at 100%)

The table includes columns:
- Project (task name)
- Eng Hours (engineering hours)
- Progress (percentage)
- Start Date
- End Date

The table is sorted by End Date in ascending order.

Uses 100% MCP tools for all Notion operations.
The API key is automatically loaded from environment variables.

Usage:
    python3 priority_tasks_table.py
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from utils import (
    NotionMCPTools,
    extract_property_value,
    extract_number_value,
    extract_date_value,
    get_page_title,
)

# Load environment variables
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break


class PriorityTasksTable:
    """
    Create a priority tasks table in Team Projects page.
    Uses 100% MCP tools for all operations.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize PriorityTasksTable.

        Args:
            api_key: Notion API key (defaults to EVAL_NOTION_API_KEY)
        """
        if api_key is None:
            api_key = os.getenv("EVAL_NOTION_API_KEY")

        if not api_key:
            raise ValueError("EVAL_NOTION_API_KEY not found in environment")

        self.api_key = api_key

    async def create_table(self) -> Dict[str, Any]:
        """
        Create priority tasks table in Team Projects page.

        Returns:
            Dictionary with results including:
            - success: Boolean indicating overall success
            - team_projects_id: ID of Team Projects page
            - projects_db_id: ID of Projects database
            - tasks_found: Number of qualifying tasks
            - table_created: Boolean if table was created
            - errors: List of any errors encountered
        """
        result = {
            "success": False,
            "team_projects_id": None,
            "projects_db_id": None,
            "tasks_found": 0,
            "table_created": False,
            "errors": [],
        }

        async with NotionMCPTools(self.api_key) as mcp:
            try:
                # Step 1: Search for Team Projects page
                print("\n📍 Step 1: Searching for 'Team Projects' page")
                print("-" * 70)

                search_result = await mcp.search("Team Projects")
                if not search_result:
                    result["errors"].append("Failed to search for Team Projects")
                    return result

                try:
                    search_data = json.loads(search_result)
                    if not search_data.get("results"):
                        result["errors"].append("Team Projects page not found")
                        return result

                    team_projects_id = None
                    for item in search_data["results"]:
                        if item.get("object") == "page":
                            title = get_page_title(item)
                            if "Team Projects" in title:
                                team_projects_id = item.get("id")
                                break

                    if not team_projects_id:
                        result["errors"].append("Team Projects page not found")
                        return result

                    result["team_projects_id"] = team_projects_id
                    print(f"✓ Found Team Projects page (ID: {team_projects_id})")
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse Team Projects search: {e}")
                    return result

                # Step 2: Search for Projects database
                print("\n📍 Step 2: Searching for 'Projects' database")
                print("-" * 70)

                search_result = await mcp.search_database("Projects")
                if not search_result:
                    result["errors"].append("Failed to search for Projects database")
                    return result

                try:
                    search_data = json.loads(search_result)
                    if not search_data.get("results"):
                        result["errors"].append("Projects database not found")
                        return result

                    projects_db_id = search_data["results"][0].get("id")
                    if not projects_db_id:
                        result["errors"].append("Projects database ID not found")
                        return result

                    result["projects_db_id"] = projects_db_id
                    print(f"✓ Found Projects database (ID: {projects_db_id})")
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse Projects search: {e}")
                    return result

                # Step 3: Query all projects from Projects database
                print("\n📍 Step 3: Querying Projects database for all items")
                print("-" * 70)

                query_result = await mcp.query_database(projects_db_id)
                if not query_result:
                    result["errors"].append("Failed to query Projects database")
                    return result

                try:
                    projects_data = json.loads(query_result)
                    all_projects = projects_data.get("results", [])
                    print(f"✓ Retrieved {len(all_projects)} projects")
                except (json.JSONDecodeError, KeyError) as e:
                    result["errors"].append(f"Failed to parse Projects query: {e}")
                    return result

                # Step 4: Filter qualifying projects
                print("\n📍 Step 4: Filtering projects by criteria")
                print("-" * 70)

                qualifying_projects = self._filter_qualifying_projects(all_projects)
                result["tasks_found"] = len(qualifying_projects)
                print(f"✓ Found {len(qualifying_projects)} qualifying projects")

                if not qualifying_projects:
                    print("  (No projects meet the criteria)")
                    result["success"] = True
                    return result

                # Step 5: Sort by End Date
                print("\n📍 Step 5: Sorting projects by End Date")
                print("-" * 70)

                sorted_projects = self._sort_by_end_date(qualifying_projects)
                print(f"✓ Sorted {len(sorted_projects)} projects by End Date")

                # Step 6: Build table rows
                print("\n📍 Step 6: Building table structure")
                print("-" * 70)

                table_rows = self._build_table_rows(sorted_projects)
                print(f"✓ Built table with {len(table_rows)} rows")

                # Step 7: Add table to Team Projects page
                print("\n📍 Step 7: Adding table to Team Projects page")
                print("-" * 70)

                table_block = {
                    "type": "table",
                    "table": {
                        "table_width": 5,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": table_rows,
                    },
                }

                patch_result = await mcp.patch_block_children(
                    team_projects_id, [table_block]
                )
                if not patch_result:
                    result["errors"].append("Failed to add table to page")
                    return result

                result["table_created"] = True
                result["success"] = True
                print(f"✓ Table successfully added to Team Projects page")

            except Exception as e:
                result["errors"].append(str(e))
                print(f"❌ Error: {str(e)}")

        return result

    def _filter_qualifying_projects(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter projects that meet the criteria:
        1. Progress is 50% or less, OR
        2. Priority is P0 AND progress is not 100%
        """
        qualifying = []

        for project in projects:
            try:
                properties = project.get("properties", {})

                # Extract Progress (rollup property)
                progress = extract_number_value(properties, "Progress")
                if progress is None:
                    progress = 0.0

                # Extract Priority
                priority_prop = properties.get("Priority", {})
                priority_select = priority_prop.get("select", {})
                priority = priority_select.get("name", "")

                # Check criteria
                # Condition 1: Progress <= 0.5
                if progress <= 0.5:
                    qualifying.append(project)
                    continue

                # Condition 2: Priority is P0 AND Progress < 1.0
                if priority == "P0" and progress < 1.0:
                    qualifying.append(project)

            except Exception as e:
                print(f"  Error processing project: {e}")
                continue

        return qualifying

    def _sort_by_end_date(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort projects by End Date (Timeline) in ascending order."""
        def get_end_date(project):
            try:
                properties = project.get("properties", {})
                timeline = extract_date_value(properties, "Timeline")
                
                if timeline:
                    # Timeline is a date range, extract start date
                    # For a date range property, we need to check the structure
                    timeline_prop = properties.get("Timeline", {})
                    if timeline_prop.get("type") == "date":
                        date_obj = timeline_prop.get("date", {})
                        if isinstance(date_obj, dict):
                            # If it has a range, use the end date; otherwise use start
                            end = date_obj.get("end") or date_obj.get("start")
                            if end:
                                return datetime.strptime(end, "%Y-%m-%d")
                
                return datetime.max  # Push items without dates to the end
            except Exception:
                return datetime.max

        return sorted(projects, key=get_end_date)

    def _build_table_rows(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build table header and row blocks."""
        rows = []

        # Header row
        header_row = {
            "type": "table_row",
            "table_row": {
                "cells": [
                    [{"type": "text", "text": {"content": "Project"}}],
                    [{"type": "text", "text": {"content": "Eng Hours"}}],
                    [{"type": "text", "text": {"content": "Progress"}}],
                    [{"type": "text", "text": {"content": "Start Date"}}],
                    [{"type": "text", "text": {"content": "End Date"}}],
                ]
            },
        }
        rows.append(header_row)

        # Data rows
        for project in projects:
            try:
                properties = project.get("properties", {})

                # Extract values
                project_name = extract_property_value(properties, "Project") or ""
                eng_hours = extract_number_value(properties, "Eng hours")
                progress = extract_number_value(properties, "Progress") or 0.0
                timeline_prop = properties.get("Timeline", {})
                
                # Extract start and end dates from Timeline
                start_date = ""
                end_date = ""
                if timeline_prop.get("type") == "date":
                    date_obj = timeline_prop.get("date", {})
                    if isinstance(date_obj, dict):
                        start_date = date_obj.get("start", "")
                        end_date = date_obj.get("end", "")

                # Format progress as percentage
                progress_str = f"{int(progress * 100)}%"

                # Format eng hours (N/A if None or 0)
                eng_hours_str = str(int(eng_hours)) if eng_hours else ""

                # Build row
                row = {
                    "type": "table_row",
                    "table_row": {
                        "cells": [
                            [{"type": "text", "text": {"content": project_name}}],
                            [{"type": "text", "text": {"content": eng_hours_str}}],
                            [{"type": "text", "text": {"content": progress_str}}],
                            [{"type": "text", "text": {"content": start_date}}],
                            [{"type": "text", "text": {"content": end_date}}],
                        ]
                    },
                }
                rows.append(row)

            except Exception as e:
                print(f"  Error building row for project: {e}")
                continue

        return rows


async def main():
    """Main entry point."""
    try:
        creator = PriorityTasksTable()
        result = await creator.create_table()

        print("\n" + "=" * 70)
        print("RESULT SUMMARY")
        print("=" * 70)
        print(f"Success: {result['success']}")
        print(f"Team Projects ID: {result['team_projects_id']}")
        print(f"Projects DB ID: {result['projects_db_id']}")
        print(f"Qualifying Tasks Found: {result['tasks_found']}")
        print(f"Table Created: {result['table_created']}")

        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")

        return result

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "errors": [str(e)]}


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result["success"] else 1)
