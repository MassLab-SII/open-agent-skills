---
name: goals-restructure
description: Restructures the Current Goals section on the Company In A Box page by converting goal headings to toggleable headings, moving descriptions inside toggles, and adding a new goal. Uses 100% MCP tools for all Notion operations.
---

# Goals Restructure Skill - 100% MCP Implementation

This skill demonstrates **100% MCP-based implementation** for managing complex Notion page structures. It restructures the Current Goals section on the Company In A Box page with toggleable headings and nested content.

## Overview

The skill orchestrates multiple MCP operations to:
- Find the "Company In A Box" page
- Locate the "Current Goals" section
- Convert all goal headings to toggleable headings
- Move description blocks inside the toggles as child blocks
- Add a new goal: "🔄 Digital Transformation Initiative"
- Preserve all content and formatting

## Basic Usage

```bash
# This skill should be integrated with an MCP server instance
python3 add_go_snippets.py

# Or using environment variable
export EVAL_NOTION_API_KEY="ntn_..."
python3 goals_restructure.py
```

**This will automatically:**
1. Search for "Company In A Box" page
2. Find "Current Goals" section via BFS
3. Identify all goal headings and descriptions
4. Convert each heading to toggleable
5. Move descriptions inside toggles
6. Add new Digital Transformation goal
7. Return success confirmation

## Task Details

### 1. Page Discovery
- **Target**: "Company In A Box"
- **Method**: MCP `API-post-search` tool
- **Returns**: Page ID

### 2. Current Goals Locator
- **Find**: "Current Goals" heading
- **Method**: BFS through page hierarchy
- **Search**: All nested blocks with `has_children`
- **Returns**: Parent block ID containing section

### 3. Goal Processing

#### Existing Goals (3 total)
- ⚙️ Expand Operations to LATAM
- 🛠️ Push for Enterprise
- 🩶 Boost Employee Engagement

#### New Goal to Add
- 🔄 Digital Transformation Initiative

### 4. Restructuring Operations

For each goal heading:

**Step 1: Make Toggleable**
- Use MCP `API-patch-block` to update heading
- Add `is_toggleable: true` flag

**Step 2: Move Descriptions**
- Retrieve description blocks after heading
- Use MCP `API-patch-block-children` to add as child blocks
- Delete original blocks with MCP `API-delete-block`

**Step 3: Add New Goal**
- Create new heading_3 with emoji and text
- Make it toggleable
- Add description paragraph as child

### 5. Verification
- ✅ 4 toggleable goal headings exist
- ✅ Each has description content inside
- ✅ New Digital Transformation goal present
- ✅ No non-toggleable goal headings remain

## Technical Architecture

### MCP Tools Used

This skill uses the following MCP tools exclusively:

| Tool | Purpose | Calls |
|------|---------|-------|
| **API-post-search** | Find pages by title | 1 |
| **API-get-block-children** | Retrieve block structure | 5+ |
| **API-patch-block** | Update block properties | 3+ |
| **API-patch-block-children** | Add child blocks | 3+ |
| **API-delete-block** | Delete blocks | 3+ |

### Tool Invocation Pattern

#### 1. Page Discovery
```
API-post-search
├─ Input: {"query":"Company In A Box"}
└─ Output: Page ID
```

#### 2. BFS Traversal
```
API-get-block-children
├─ Input: {"block_id":"<current_block>"}
├─ Returns: Child blocks
├─ Check: has_children flag
└─ Enqueue: Children with has_children
```

#### 3. Convert to Toggleable
```
API-patch-block
├─ Input: {
│   "block_id":"<heading_id>",
│   "heading_3":{"is_toggleable":true,...}
│ }
└─ Output: Updated heading block
```

#### 4. Move Descriptions
```
API-patch-block-children
├─ Input: {
│   "block_id":"<heading_id>",
│   "children":[<desc_block>]
│ }
└─ Output: Child block added

API-delete-block
├─ Input: {"block_id":"<old_desc_id>"}
└─ Output: Block deleted
```

#### 5. Add New Goal
```
API-patch-block-children
├─ Input: {
│   "block_id":"<parent_id>",
│   "children":[{
│     "type":"heading_3",
│     "heading_3":{
│       "rich_text":[{"type":"text","text":{"content":"🔄..."}}],
│       "is_toggleable":true
│     }
│   }]
│ }
└─ Output: New heading created

API-patch-block-children (again)
├─ Input: {
│   "block_id":"<new_goal_id>",
│   "children":[{
│     "type":"paragraph",
│     "paragraph":{"rich_text":[...]}
│   }]
│ }
└─ Output: Description added
```

## Implementation Details

### Pure MCP Architecture

This skill demonstrates the **100% MCP approach**:

✅ **No `notion_client` library** - All operations through MCP protocol
✅ **Async/await pattern** - Uses `NotionMCPTools` context manager
✅ **Error handling** - Comprehensive error checks and fallbacks
✅ **JSON parsing** - Direct parsing of MCP API responses
✅ **BFS traversal** - Efficient searching through nested structure

### Key Components

**utils.py - NotionMCPTools Class**
- Manages MCP client initialization and lifecycle
- Core async methods:
  - `search(query)` - Search pages
  - `get_block_children(block_id)` - Retrieve blocks
  - `patch_block_children(block_id, children, after)` - Add blocks
  - `update_block(block_id, block_data)` - Update block properties
  - `delete_block(block_id)` - Delete block
- Helpers for creating blocks:
  - `create_heading_3_block(text, is_toggleable)`
  - `create_paragraph_block(text)`

**goals_restructure.py - Skill Execution**
- Orchestrates complete workflow
- Utility functions:
  - `extract_page_id_from_json()` - Parse IDs from responses
  - `get_block_text()` - Extract text from blocks
  - `parse_blocks_response()` - Parse block arrays
  - `find_page_by_title()` - Search and find page
  - `find_current_goals_parent()` - BFS to find section
  - `restructure_goals()` - Main restructuring logic

### Error Handling

The skill handles:
- Page not found → Clear error message
- Current Goals section not found → BFS ensures thorough search
- Duplicate goals → Automatic removal
- Missing descriptions → Graceful handling
- Block operations failures → Detailed logging

## Workflow Diagram

```
START
  │
  ├─ Search for "Company In A Box" page
  │   └─ Get page ID
  │
  ├─ BFS to find "Current Goals" heading
  │   ├─ Check current block's children
  │   └─ Enqueue children with has_children
  │
  ├─ Parse goals section
  │   ├─ Find all heading_3 blocks
  │   └─ Collect descriptions for each
  │
  ├─ For each goal:
  │   ├─ Convert to toggleable (API-patch-block)
  │   ├─ For each description:
  │   │  ├─ Add as child (API-patch-block-children)
  │   │  └─ Delete original (API-delete-block)
  │
  ├─ Check for new goal existence
  │
  ├─ If missing, add new goal:
  │   ├─ Create heading_3 (toggleable)
  │   └─ Add description paragraph
  │
  └─ SUCCESS
```

## Testing & Validation

### Success Criteria
- ✅ 4 toggleable goal headings created
- ✅ Each goal has description inside toggle
- ✅ "Digital Transformation Initiative" present
- ✅ No non-toggleable goal headings remain
- ✅ All content preserved
- ✅ Formatting maintained

### Verification
```bash
python3 tasks/notion/standard/company_in_a_box/goals_restructure/verify.py
```

Expected output:
```
Success: Verified goal restructuring with new toggle blocks and descriptions.
```

## References

### MCP Notion Server
- Repository: @notionhq/notion-mcp-server
- Tools: API-post-search, API-get-block-children, API-patch-block, API-patch-block-children, API-delete-block

### Notion Concepts
- Toggleable headings with `is_toggleable` flag
- Block hierarchy and children
- Rich text annotations
- Block deletion and moving


---

## Employee Onboarding

| Aspect | Details |
|--------|---------|
| **Skill Name** | Employee Onboarding System |
| **Domain** | Company In A Box |
| **Description** | Creates a comprehensive employee onboarding system with checklist database and onboarding hub |
| **File** | `employee_onboarding.py` |

### Core Concepts

1. **Database Creation**: Create a structured Employee Onboarding Checklist database with properties for employee name, start date, and department
2. **Sample Data Population**: Populate checklist with 3 sample employees (Alice, Bob, Carol) across different departments
3. **Hub Page Construction**: Create an Onboarding Hub page with embedded database reference and organized sections for benefits, timeline, and feedback
4. **Benefit Linking**: Search for and link to existing benefit policy pages via @-mentions in the Onboarding Hub
5. **Multi-Block Structure**: Construct complex page with multiple child block types (headings, lists, to-dos, database references)

### Execution Flow

The skill performs a 5-step orchestrated MCP workflow:

1. **Search for Company In A Box Page** (API-post-search)
   - Locates the parent page for all onboarding content
   - Validates object type is "page"

2. **Search for Benefit Policy Pages** (API-post-search x3+)
   - Retrieves IDs for: Benefits policy, Vacation Policy, Corporate travel
   - Implements fallback searches if primary names don't match
   - Stores page IDs for later @-mention linking

3. **Create Employee Onboarding Checklist Database** (API-create-a-database)
   - Parent: Company In A Box page
   - Title: "Employee Onboarding Checklist"
   - Properties:
     - **Employee Name** (type: title)
     - **Start Date** (type: date)
     - **Department** (type: select with options: Product, Marketing, Sales, HR, Engineering)

4. **Create 3 Employee Entries** (API-post-page x3)
   - Alice Johnson | Start: 2025-10-01 | Department: Engineering
   - Bob Smith | Start: 2025-10-05 | Department: Marketing
   - Carol Lee | Start: 2025-10-10 | Department: HR

5. **Create Onboarding Hub Page with Children** (API-post-page)
   - Parent: Company In A Box page
   - Title: "Onboarding Hub"
   - Child Blocks:
     - child_database: Reference to Employee Onboarding Checklist
     - heading_2: "Benefits Overview"
     - bulleted_list_item (x3): Benefit policy mentions
     - heading_2: "30-Day Timeline"
     - numbered_list_item (x7): Onboarding timeline steps
     - heading_2: "Feedback Form"
     - to_do (x3): Feedback completion tasks

### Basic Tools

| Tool | MCP API | Purpose |
|------|---------|---------|
| `search(query)` | API-post-search | Find pages/databases by name with object type filtering |
| `create_database(parent_id, title, properties)` | API-create-a-database | Create new database with schema in parent page |
| `create_page(parent_id, properties, children)` | API-post-page | Create page with properties and optional children blocks |

### Created Structure

**Database: Employee Onboarding Checklist**
```
Employee Onboarding Checklist
├── Properties:
│   ├── Employee Name (title)
│   ├── Start Date (date)
│   └── Department (select)
└── Entries:
    ├── Alice Johnson | 2025-10-01 | Engineering
    ├── Bob Smith | 2025-10-05 | Marketing
    └── Carol Lee | 2025-10-10 | HR
```

**Page: Onboarding Hub**
```
Onboarding Hub
├── Embedded Database: Employee Onboarding Checklist
├── Section: Benefits Overview
│   ├── @mention: Benefits policy
│   ├── @mention: Vacation Policy
│   └── @mention: Corporate travel
├── Section: 30-Day Timeline
│   ├── Day 1: Account setup & access provisioning
│   ├── Day 2-3: Team introductions & workspace tour
│   ├── Day 4-5: System & process training
│   ├── Week 2: Project assignment & team kickoff
│   ├── Week 3-4: Mentorship check-ins
│   ├── Day 30: Performance review discussion
│   └── Post-30 days: Ongoing development plan
└── Section: Feedback Form
    ├── ☐ Complete day 1 onboarding survey
    ├── ☐ Manager check-in scheduled
    └── ☐ 30-day review completed
```

### Expected Output

Successful execution returns:
```python
{
    "success": True,
    "checklist_db_id": "c7d1e8f2-a9b3-4e2f-9c1a-2d5e8f7b4a3c",
    "onboarding_hub_id": "b2c4e6f8-d9e1-4a3c-8b5d-7f2e4c6a9d1b",
    "employees_created": 3,
    "errors": []
}
```

### Implementation Details

**Database Property Format**
- Title: `{"title": {}}`
- Date: `{"date": {}}`
- Select: `{"select": {"options": [{"name": "Engineering"}, ...]}}`

**Page Property Format**
- Title: `{"title": [{"text": {"content": "Employee Name"}}]}`
- Date: `{"date": {"start": "2025-10-01"}}`
- Select: `{"select": {"name": "Engineering"}}`

**Children Block Types**
```python
{
    "type": "child_database",
    "child_database": {"database_id": "..."}
}

{
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "..."}}]}
}

{
    "type": "bulleted_list_item",
    "bulleted_list_item": {"rich_text": [{"text": {"content": "..."}}]}
}

{
    "type": "numbered_list_item",
    "numbered_list_item": {"rich_text": [{"text": {"content": "..."}}]}
}

{
    "type": "to_do",
    "to_do": {"rich_text": [...], "checked": False}
}
```

### Error Handling

1. **Company Page Not Found**: Logs error and stops execution
2. **Benefit Page Search Failures**: Implements fallback searches (e.g., "benefits" if "Benefits policy" fails)
3. **Database Creation Errors**: Catches API errors and reports in results
4. **Property Format Validation**: Ensures title, select, and date properties match API requirements
5. **Block Structure Validation**: Validates children blocks before submission to API

