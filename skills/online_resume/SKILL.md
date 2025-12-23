| name | description |
|------|-------------|
| projects-section-update | Updates the projects section in Online Resume by removing outdated projects, creating new ones, and adding dynamic skill-based content using MCP tools. |
| skills-development-tracker | Creates a skills audit system that identifies gaps and generates development plans automatically. |

# Online Resume Skills

## Core Concepts

**Skill**: Meaningful combinations of multiple MCP tool calls, encapsulated as independent Python scripts
**Basic Tools**: Single MCP function calls in utils.py for atomic operations

## I. Skills

### 1. Projects Section Update
**File**: `projects_section_update.py`

**Use Cases**:
- Remove outdated projects from portfolio
- Create new project entries with rich information
- Update database schemas with new fields
- Add dynamic content that references other databases

**Prerequisites**:
- Online Resume page exists in Notion workspace
- Projects and Skills databases are configured

**Usage**:
```bash
python3 projects_section_update.py
```

**Examples**:
- Remove "Knitties eComm Website" and create "Zapier Dashboard Redesign"
- Update Projects database to add Phone, URL fields
- Add "Current Focus" section with highest proficiency skill

### 2. Skills Development Tracker
**File**: `skills_development_tracker.py`

**Use Cases**:
- Identify skills below 70% proficiency threshold
- Create automated development plans for skill improvement
- Track progress across multiple skill areas
- Organize learning priorities visually

**Prerequisites**:
- Online Resume page with column layout exists
- Skills database with proficiency levels is configured
- EVAL_NOTION_API_KEY environment variable set

**Usage**:
```bash
export EVAL_NOTION_API_KEY="your-api-key"
python3 skills_development_tracker.py
```

**Examples**:
- Create tracker with 5 skills below 70% proficiency
- Generate plans with target proficiency (current + 25%, max 95%)
- Add 🎯 callout block highlighting top 3 focus areas
- Link tracker entries to original skills database

## II. Basic Tools (utils.py)

| Tool | MCP API | Purpose |
|------|---------|---------|
| `search()` | API-post-search | Find databases and pages |
| `get_block_children()` | API-get-block-children | Retrieve child blocks |
| `query_database()` | API-post-database-query | Query with filters/sorts |
| `create_database()` | API-create-a-database | Create new database |
| `create_page()` | API-post-page | Create pages in database |
| `update_database()` | API-update-a-database | Add/modify properties |
| `patch_block_children()` | API-patch-block-children | Insert blocks at positions |
