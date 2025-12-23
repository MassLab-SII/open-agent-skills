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

### 2. Priority Tasks Table
**File**: `priority_tasks_table.py`

**Use Cases**:
- Create a visual table of high-priority and in-progress work
- Monitor projects with 50% or less progress completion
- Track P0 priority items regardless of current progress
- Quick reference for deadline management (sorted by end date)

**Prerequisites**:
- Team Projects page must exist in Notion
- Projects database must be present with properties: Progress, Priority, Timeline, Eng hours
- Environment variable `EVAL_NOTION_API_KEY` must be set

**Usage**:
```bash
# Creates a five-column table in Team Projects page with priority tasks
python3 skills/team_projects/priority_tasks_table.py
```

**What It Does**:
1. Finds the Team Projects page
2. Locates the Projects database
3. Queries all projects from the database
4. Filters projects by criteria:
   - Progress ≤ 50% (early-stage work), OR
   - Priority = P0 AND Progress < 100% (high-priority incomplete items)
5. Sorts qualifying projects by End Date (ascending)
6. Builds table structure with 5 columns:
   - Project (name)
   - Eng Hours (allocated hours)
   - Progress (percentage)
   - Start Date
   - End Date
7. Adds table block to Team Projects page using plain text storage

**Output**: Table block in Team Projects page with sorted priority tasks

**Filtering Logic**:
```
Include project IF:
  (Progress <= 0.5) OR (Priority == "P0" AND Progress < 1.0)
```

**Table Features**:
- Sorted by End Date ascending (earliest deadlines first)
- All data stored as plain text (no formulas, relations, or links)
- Engineering hours displayed as plain numbers
- Progress displayed as percentage (e.g., "33%")
- Dates in YYYY-MM-DD format

---

## Basic Tools (in utils.py)

| Function | Purpose |
|----------|---------|
| `search()` | Search for pages/databases by name |
| `search_database()` | Search for databases specifically |
| `retrieve_page()` | Get page details and properties |
| `get_block_children()` | Get child blocks (including databases) |
| `query_database()` | Query database to retrieve records |
| `patch_page()` | Update page properties |
| `patch_block_children()` | Add children blocks (for creating tables) |
| `extract_property_value()` | Extract title/text property values |
| `extract_number_value()` | Extract numeric property values (progress, hours) |
| `extract_date_value()` | Extract date property values for sorting |
| `get_page_title()` | Extract page title from page object |

---

## MCP Tools Used

### swap_tasks.py
- `API-post-search` - Find Team Projects page
- `API-get-block-children` - Locate Tasks database
- `API-post-database-query` - Query all tasks and their assignments
- `API-patch-page` - Update task assignments for each task

### priority_tasks_table.py
- `API-post-search` - Find Team Projects page (with page filter)
- `API-post-search` - Find Projects database (with database filter)
- `API-post-database-query` - Query all projects with properties
- `API-patch-block-children` - Add table block to Team Projects page

---
