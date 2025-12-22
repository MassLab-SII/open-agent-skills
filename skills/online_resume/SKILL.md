---
name: projects-section-update
description: Updates the projects section in Online Resume by removing outdated projects, creating new ones, and adding dynamic skill-based content using MCP tools.
---

# Online Resume - Projects Section Update Skill

This skill reorganizes the projects section in an Online Resume page to showcase only the most recent and relevant work with dynamic cross-database references.

## Core Concepts

In Notion automation, we distinguish two types of operations:

**Skill**: Meaningful combinations of multiple MCP tool calls, encapsulated as independent Python scripts
**Basic Tools**: Single MCP function calls (API-post-search, API-post-database-query, etc.)

## Skills

### Projects Section Update

**Use Cases**:
- Remove outdated projects from portfolio
- Create new project entries with rich information
- Update database schemas with new fields and options
- Add dynamic content that references other databases
- Maintain cross-section consistency (contact info, skill levels)

**Usage**:
```bash
# Basic usage with environment variable
export EVAL_NOTION_API_KEY="ntn_..."
python3 projects_section_update.py

# Or with custom parameters in code
python3 -c "
import asyncio
from skills.online_resume.projects_section_update import ProjectsSectionUpdate

async def main():
    skill = ProjectsSectionUpdate(api_key='ntn_...')
    result = await skill.update_projects()
    print(f'Success: {result[\"success\"]}')
    print(f'Created: {result[\"created_project\"]}')

asyncio.run(main())
"
```

**Expected Output**:
```
======================================================================
📊 Execution Summary
======================================================================
Success: True
Message: Projects section updated: deleted 1, created 1, added Current Focus section
Deleted: Knitties eComm Website
Created: Zapier Dashboard Redesign
Highest Skill: Photoshop (90%)
Current Focus Added: True
```

## Execution Flow

1. **Search Page**: Find "Online Resume" page via `API-post-search`
2. **Locate Databases**: Find Projects and Skills databases in page children
3. **Get Contact Info**: Extract phone and website from contact section
4. **Delete Old Project**: Find and archive "Knitties eComm Website" via `API-patch-page`
5. **Query Skills**: Query Skills database sorted by skill level to find highest (via `API-post-database-query`)
6. **Update Schema**: Add Phone, URL fields and Enterprise tag to Projects database (via `API-update-a-database`)
7. **Create Project**: Create "Zapier Dashboard Redesign" entry (via `API-post-page`)
8. **Add Section**: Append "Current Focus" section with dynamic skill reference (via `API-patch-block-children`)

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `API-post-search` | Search for Online Resume page |
| `API-get-block-children` | Retrieve page and database structure |
| `API-retrieve-database` | Get database schema details |
| `API-post-database-query` | Query databases with filters/sorts |
| `API-patch-page` | Archive old projects |
| `API-post-page` | Create new project entries |
| `API-update-a-database` | Add new fields and options |
| `API-patch-block-children` | Add new content blocks |

## Customization

Adapt the skill for different scenarios:

```python
# Use custom API key
skill = ProjectsSectionUpdate(api_key="custom_key")

# Execute and handle result
result = await skill.update_projects()

# Access detailed results
if result["success"]:
    print(f"Highest skill: {result['highest_skill']}")
    print(f"Project created: {result['created_project']}")
```

## File Structure

```
skills/online_resume/
├── projects_section_update.py   # Main skill implementation
├── utils.py                     # MCP tools wrapper
├── SKILL.md                     # This documentation
└── __init__.py                  # Package initialization
```

## Key Methods

**`ProjectsSectionUpdate`** class:
- `__init__(api_key)`: Initialize skill
- `async update_projects()`: Execute the skill, returns `{success, message, deleted_project, created_project, highest_skill, highest_skill_level, current_focus_added, errors}`

**Helper functions** in `utils.py`:
- `NotionMCPTools`: Context manager for 8 MCP tool calls (search, retrieve, query, patch, create, update)
- `extract_property_value()`: Extract property values from Notion pages

## Related Skills

- Self Assessment - FAQ Column Layout (similar database manipulation)
- Japan Travel Planner - Remove Osaka Itinerary (similar filtering pattern)
