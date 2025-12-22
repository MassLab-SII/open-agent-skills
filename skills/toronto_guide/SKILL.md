---
name: notion-toronto-guide
description: This skill provides Notion automation tools for the Toronto Guide. Includes weekend adventure planner creation and pink element color management for databases and callouts.
---

# Toronto Guide Skills

This skill set provides automation capabilities for managing the Toronto Guide Notion page, including creating weekend adventure planners and managing element colors.

## Core Concepts

In Toronto Guide automation, we distinguish two types of operations:

**Skills**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
**Basic Tools**: Single function calls in utils.py, used for atomic operations

## Skills

### 1. Weekend Adventure Planner
**File**: `create_weekend_planner.py`

**Use Cases**:
- Create a curated weekend itinerary from city guide databases
- Combine Activities, Food, and Cafes recommendations into one page
- Generate "Perfect Weekend Adventure" page with structured content

**Prerequisites**:
- Toronto Guide page must exist in Notion
- Child databases (Activities, Food, Cafes) must be present
- Environment variable `EVAL_NOTION_API_KEY` must be set

**Usage**:
```bash
# Default: Creates Perfect Weekend Adventure with Beaches activities, Turkish/Hakka dining
python3 skills/toronto_guide/create_weekend_planner.py

# Customize for other city guides and preferences
python3 skills/toronto_guide/create_weekend_planner.py \
  --main-page "Vancouver Guide" \
  --activities-tag "Mountains" \
  --food-tags "Asian" "Pacific"
```

**What It Does**:
1. Finds the Toronto Guide page
2. Queries Activities DB for specified tag (e.g., "Beaches")
3. Queries Food DB for specified tags (e.g., "Turkish", "Hakka")
4. Retrieves all Cafes entries
5. Creates "Perfect Weekend Adventure" child page
6. Formats content with headings, lists, toggle blocks, and summary

**Output**: Page with activities, restaurants, cafes, and weekend summary

---

### 2. Change Color
**File**: `change_color.py`

**Use Cases**:
- Change all pink-colored elements in the Toronto Guide to different colors
- Update callout block colors
- Update database tag option colors

**Prerequisites**:
- Toronto Guide page must exist in Notion
- Pink callout blocks and pink-colored tags must be present
- Environment variable `EVAL_NOTION_API_KEY` must be set

**Usage**:
```bash
# Changes all pink elements (callouts and database tags) to other colors
python3 skills/toronto_guide/change_color.py
```

**What It Does**:
1. Finds the Toronto Guide page
2. Scans all blocks for pink callouts
3. Checks Activities, Food, and Cafes databases for pink tags
4. Changes callout colors to blue_background
5. Changes database tag colors to blue, green, orange, red, purple, gray, brown, or yellow
6. Reports all color changes made

**Output**: All pink elements replaced with other colors

---

## Basic Tools (in utils.py)

| Function | Purpose |
|----------|---------|
| `search()` | Search for pages/databases by name |
| `query_database()` | Query database with filters and sorts |
| `retrieve_database()` | Get database structure and properties |
| `update_database()` | Modify database tag properties and colors |
| `get_block_children()` | Get child blocks recursively |
| `patch_block_children()` | Add or modify blocks within a parent block |
| `update_block()` | Update block properties (e.g., callout color) |
| `create_page()` | Create new pages |

---

## MCP Tools Used

1. **API-post-search** - Search for pages and databases
2. **API-post-database-query** - Query databases with filters
3. **API-retrieve-a-database** - Get database properties
4. **API-update-a-database** - Update database schema and options
5. **API-get-block-children** - Get child blocks
6. **API-patch-block-children** - Add/modify blocks
7. **API-update-a-block** - Update block properties
8. **API-post-page** - Create pages
