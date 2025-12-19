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

