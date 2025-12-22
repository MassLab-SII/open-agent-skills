---
name: standard-operating-procedure-deployment-sop
description: Completes and updates a comprehensive Standard Operating Procedure (SOP) template for deployment processes using 100% MCP tools. Discovers and populates all sections with deployment process information, including header details, purpose, context, terminology, tools, roles, and procedures.
---

# Standard Operating Procedure - Deployment Process SOP Skill

This skill demonstrates **100% MCP-based implementation** for managing complex Notion page structures. It systematically discovers and completes a comprehensive Standard Operating Procedure (SOP) template for deployment processes.

## Overview

The skill orchestrates multiple MCP operations to:
- Find the "standard_operating_procedure__deployment_process_sop" page
- Dynamically discover all page sections through systematic block exploration
- Update header information (title, creation date, responsible department)
- Populate all 7 SOP sections with structured content:
  - Purpose of the SOP
  - Context and related processes
  - Essential terminology and definitions
  - Critical tools required for execution
  - Roles and responsibilities
  - Step-by-step procedure
- Maintain consistent formatting and block structure
- Update callouts within child pages

## Basic Usage

```bash
# This skill should be integrated with an MCP server instance
python3 deployment_process_sop.py

# Or using environment variable
export EVAL_NOTION_API_KEY="ntn_..."
python3 deployment_process_sop.py
```

**This will automatically:**
1. Search for "standard_operating_procedure__deployment_process_sop" page
2. Explore page structure (header column_list + 7 root-level sections)
3. Discover all blocks through recursive exploration
4. Update header information (title, date, department)
5. Update purpose section with deployment context
6. Update context section with child pages and callouts
7. Update terminology with 4 key deployment terms
8. Update tools section with Jenkins and Kubernetes information
9. Update roles section with 4 critical deployment roles
10. Update procedure section with numbered deployment steps
11. Return success confirmation with update count

## Task Details

### 1. Page Discovery
- **Target**: "standard_operating_procedure__deployment_process_sop"
- **Method**: MCP `API-post-search` tool
- **Returns**: Page ID

### 2. Page Structure Exploration

The SOP page has a unique two-part structure:

**Part A: Header Section (column_list)**
- Column 1: Heading 1 (title), 2 paragraphs, 1 child_page (People team)
- Column 2: Empty
- Contains: SOP title, creation date, responsible department
- Also contains: People team page callout with team information

**Part B: Root-Level Sections (7 heading_2 blocks)**
1. **Purpose** - Heading_2 + Paragraph + Toggle (with child_pages)
2. **Context** - Heading_2 + Paragraph + Toggle (with 3 child_pages: Contacting IT, Team lunches, Sending swag)
3. **Terminologies** - Heading_2 + Paragraph + 4 bulleted_list_items
4. **Tools** - Heading_2 + Paragraph + 2 child_pages (Notion, Figma) with callouts
5. **Roles & responsibilities** - Heading_2 + Paragraph + 4 bulleted_list_items
6. **Procedure** - Heading_2 + Paragraph + 3 numbered_list_items

### 3. Content Updates

#### Header Section
- **SOP Title**: "Deployment Process SOP"
- **Creation Date**: "December 2024"
- **Responsible Department**: "DevOps Engineering"
- **People Team Callout**: "DevOps Engineering Team Wiki"

#### Purpose Section
- Description: Clear explanation of SOP purpose
- Toggle: Contains related context and policy references

#### Context Section
- Introduction paragraph
- 3 child pages with deployment-related information:
  - Contacting IT: IT support procedures
  - Team lunches: Team coordination details
  - Sending swag: Recognition programs
- Each with descriptive callout

#### Terminologies (4 items)
1. Blue-Green Deployment: A deployment strategy that maintains two identical production environments
2. Rollback Window: The maximum time allowed to revert a deployment (30 minutes)
3. Smoke Test: Initial verification tests run immediately after deployment
4. Production Gateway: The approval checkpoint before production release

#### Tools (2 items)
1. Jenkins CI/CD Pipeline: Primary deployment automation tool with integrated testing and approval workflows
2. Kubernetes Dashboard: Container orchestration monitoring and management interface

#### Roles & Responsibilities (4 items)
1. DevOps Engineer: Executes deployment, monitors system health, initiates rollbacks
2. Lead Developer: Reviews code changes, approves deployment package, validates functionality
3. QA Engineer: Verifies smoke tests, confirms user acceptance criteria
4. Security Officer: Validates security compliance, approves security-sensitive deployments

#### Procedure (3 numbered items)
1. Pre-deployment validation
2. Deployment execution
3. Post-deployment verification

### 4. Discovery Strategy

The skill uses a **systematic exploration pattern**:

1. **Column List Discovery**
   - Identify `column_list` blocks in page root
   - Explore each column's children
   - Find and explore child_pages within columns

2. **Root Block Exploration**
   - Iterate through root blocks looking for heading_2
   - For each section heading, find following blocks until next heading_2
   - Build block_map with semantic keys:
     - `heading_Purpose`, `para_Purpose`, etc.
     - `child_PageName`, `callout_PageName` for child_pages
     - `first_bulleted_list_item_Section` for lists

3. **Dynamic Block Mapping**
   - Never hardcodes block IDs
   - Discovers all block IDs through systematic exploration
   - Maintains flexibility for page structure variations

### 5. Verification

All 14 verification checks:
- ✅ SOP Title updated correctly
- ✅ Created date updated correctly
- ✅ Responsible department updated correctly
- ✅ Header People team page callout updated correctly
- ✅ Purpose section content updated correctly
- ✅ Context child_page 'Contacting IT' updated correctly
- ✅ Context child_page 'Team lunches' updated correctly
- ✅ Context child_page 'Sending swag' updated correctly
- ✅ Context section content updated correctly
- ✅ All 3 Context child_page callouts updated correctly
- ✅ Terminologies section with exactly 4 correct items
- ✅ Tools section with 2 correctly updated child_page callouts
- ✅ Roles & responsibilities section with exactly 4 correct items
- ✅ Procedure section with exactly 3 correct items

## Technical Architecture

### MCP Tools Used

| Tool | Purpose | Use Cases |
|------|---------|-----------|
| **API-post-search** | Find pages by query | Locate SOP page |
| **API-get-block-children** | Retrieve block hierarchy | Explore structure, find sections |
| **API-update-a-block** | Update block properties | Modify content and formatting |
| **API-patch-block-children** | Add child blocks | Add list items to sections |
| **API-delete-a-block** | Delete blocks | Clean up duplicates |

### Block Type Management

The skill handles various Notion block types:
- `heading_1`, `heading_2`: Section markers
- `paragraph`: Text content
- `bulleted_list_item`: List items for terminology and roles
- `numbered_list_item`: Numbered steps for procedure
- `column_list`, `column`: Page layout structure
- `child_page`: Nested pages with content
- `callout`: Highlighted information blocks
- `toggle`: Expandable/collapsible sections

### Async Implementation

Full async/await pattern:
```python
async with NotionMCPTools(api_key) as mcp:
    # All MCP operations are async
    result = await mcp.search(query)
    blocks = await mcp.get_block_children(block_id)
    await mcp.update_block(block_id, block_type, properties)
```

## File Structure

```
skills/standard_operating_procedure/
├── deployment_process_sop.py     # Main skill implementation (573 lines)
├── utils.py                      # MCP tools wrapper (151 lines)
├── SKILL.md                      # This documentation
└── __init__.py                   # Package initialization
```

## Key Classes and Methods

### **DeploymentProcessSOP** class
Main skill orchestrator for SOP completion.

**Initialization**:
```python
skill = DeploymentProcessSOP(api_key)
```

**Core Methods**:
- `async complete_sop()`: Execute the skill
  - Returns: `{success: bool, updates: int, errors: List[str]}`
  
- `async _search_and_find_sop_page()`: Locate SOP page
- `async _explore_page_structure()`: Build comprehensive block map
- `async _explore_root_blocks()`: Find section headings
- `async _explore_column_list()`: Process header structure
- `async _find_section_content()`: Locate blocks within sections
- `async _explore_child_page()`: Discover content in nested pages

**Update Methods** (one per section):
- `async _update_header()`: Update title, date, department, callouts
- `async _update_purpose()`: Update purpose section
- `async _update_context()`: Update context and child_pages
- `async _update_terminologies()`: Update terminology list
- `async _update_tools()`: Update tools with callouts
- `async _update_roles()`: Update roles and responsibilities
- `async _update_procedure()`: Update procedure steps

### **NotionMCPTools** class (in utils.py)
Async context manager for MCP API access.

**Core Methods**:
- `async search(query)`: Search pages/databases
- `async retrieve_page(page_id)`: Get page details
- `async get_block_children(block_id)`: Retrieve child blocks
- `async update_block(block_id, block_type, properties)`: Update block
- `async patch_block_children(block_id, children, after)`: Add child blocks
- `async delete_block(block_id)`: Delete a block

## Usage Examples

### Basic Execution
```bash
export EVAL_NOTION_API_KEY="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"
cd skills/standard_operating_procedure
python3 deployment_process_sop.py
```

### With Custom Key
```python
import asyncio
from skills.standard_operating_procedure.deployment_process_sop import DeploymentProcessSOP

async def main():
    skill = DeploymentProcessSOP(api_key="your_api_key")
    result = await skill.complete_sop()
    print(f"Success: {result['success']}")
    print(f"Updates made: {result['updates']}")

asyncio.run(main())
```

### Verification
```bash
# After running the skill, verify all sections
export EVAL_NOTION_API_KEY="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"
python3 ../../../tasks/notion/standard/standard_operating_procedure/deployment_process_sop/verify.py
```

**Expected Output**:
```
=== SOP Template Verification Results ===
✅ SOP Title updated correctly
✅ Created date updated correctly
✅ Responsible department updated correctly
✅ Header People team page callout updated correctly
✅ Purpose section content updated correctly
✅ Context child_page 'Contacting IT' updated correctly
✅ Context child_page 'Team lunches' updated correctly
✅ Context child_page 'Sending swag' updated correctly
✅ Context section content updated correctly
✅ All 3 Context child_page callouts updated correctly
✅ Terminologies section with exactly 4 correct items
✅ Tools section with 2 correctly updated child_page callouts
✅ Roles & responsibilities section with exactly 4 correct items
✅ Procedure section with exactly 3 correct items

=== Summary: 14/14 checks passed ===
🎉 SUCCESS: All SOP template requirements completed correctly!
```

## Key Features

✨ **Dynamic Discovery**: Never hardcodes block IDs - discovers structure on every run
✨ **Section-Aware**: Intelligently finds content between section headings
✨ **Child Page Support**: Handles nested pages and their callouts
✨ **Duplicate Prevention**: Avoids adding duplicate items on re-runs
✨ **Error Handling**: Gracefully handles missing sections or unexpected structures
✨ **Comprehensive Updates**: Updates 30+ blocks across 7 sections
✨ **Type Safe**: Uses TypeScript-style type hints in Python

## Related Skills

- Company In A Box - Goals Restructure (similar exploration and update pattern)
- Self Assessment - FAQ Column Layout (similar MCP tool usage)
- Other Notion automation tasks using systematic block exploration

## Troubleshooting

### Skill finds page but doesn't update sections
- Check that page has heading_2 blocks for each section
- Verify block_map is built correctly (enable debug output)
- Ensure API key has write permissions

### Some sections not updating
- Check if section structure differs from expected
- Verify child_page blocks are present
- Look for nested column_list or other structural variations

### Duplicate items appear
- Previous runs may have created duplicates (fixed in latest version)
- Current version prevents duplicates by not re-adding existing items
- Clean up manually with delete_block API if needed

## Implementation Notes

- **Lines of Code**: 573 lines (main skill) + 151 lines (utils)
- **MCP Tool Calls**: ~30-40 per execution
- **Block Types Handled**: 10+ different Notion block types
- **Success Rate**: 14/14 verification checks on clean run
- **Execution Time**: ~5-10 seconds depending on Notion API latency

