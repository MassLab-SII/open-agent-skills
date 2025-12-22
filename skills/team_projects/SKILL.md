---
name: notion-team-projects
description: This skill provides Notion automation tools for Team Projects management. Includes task assignment swapping between team members.
---

# Team Projects Skills

This skill set provides automation capabilities for managing the Team Projects Notion page, including intelligent task assignment management.

## Core Concepts

In Team Projects automation, we distinguish two types of operations:

**Skills**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
**Basic Tools**: Single function calls in utils.py, used for atomic operations

## Skills

### 1. Swap Tasks
**File**: `swap_tasks.py`

**Use Cases**:
- Balance workload by swapping task assignments between team members
- Redistribute tasks from person with most assignments to person with fewest
- Ensure fair task distribution across the team

**Prerequisites**:
- Team Projects page must exist in Notion
- Tasks database must be present as a child database
- At least 2 team members must have assigned tasks
- Environment variable `EVAL_NOTION_API_KEY` must be set

**Usage**:
```bash
# Swaps all tasks between person with most and person with fewest assignments
python3 skills/team_projects/swap_tasks.py
```

**What It Does**:
1. Finds the Team Projects page
2. Locates the Tasks database
3. Queries all tasks from the database
4. Counts task assignments per team member
5. Identifies person with most tasks and person with fewest tasks
6. Reassigns all tasks from person with most → person with fewest
7. Reassigns all tasks from person with fewest → person with most
8. Reports swap completion

**Output**: Complete task assignment swap between the two people with most/fewest workload

---

## Basic Tools (in utils.py)

| Function | Purpose |
|----------|---------|
| `search()` | Search for pages/databases by name |
| `retrieve_page()` | Get page details and properties |
| `get_block_children()` | Get child blocks (including databases) |
| `query_database()` | Query database to retrieve all tasks |
| `patch_page()` | Update page properties (task assignments) |
| `extract_property_value()` | Extract various property types from Notion objects |

---

## MCP Tools Used

### swap_tasks.py
- `API-post-search` - Find Team Projects page
- `API-get-block-children` - Locate Tasks database
- `API-post-database-query` - Query all tasks and their assignments
- `API-patch-page` - Update task assignments for each task

---
