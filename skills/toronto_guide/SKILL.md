---
name: notion-weekend-adventure-planner
description: Creates a comprehensive weekend adventure planner page from city guide databases. Analyzes Activities, Food, and Cafes databases to generate a structured itinerary with beach activities, cultural dining, and coffee spots.
---

# Weekend Adventure Planner Skill

This skill creates a comprehensive weekend adventure planner by analyzing city guide databases and generating a beautifully formatted Notion page with curated recommendations.

## Basic Usage

```bash
python3 skills/toronto_guide/create_weekend_planner.py
```

**This will automatically:**
1. Find the Toronto Guide page
2. Discover all child databases (Activities, Food, Cafes)
3. Query each database with appropriate filters
4. Create a "Perfect Weekend Adventure" page with all content
5. Format everything with proper Notion blocks


## Configurable Analysis

Create a weekend adventure planner by analyzing three configurable dimensions:

1. **Activities Filter** - Filter by tag (e.g., "Beaches", "Museums", "Outdoor")
2. **Dining Filter** - Filter by multiple tags (e.g., "Turkish", "Hakka", "Italian")
3. **Cafes Collection** - Retrieve all cafe entries

**Use when**: You need to create a structured weekend guide from city database information. Fully parameterized - no code changes needed.

## Quick Start (Copy & Paste)

**For Toronto Guide (default):**
```bash
python3 skills/toronto_guide/create_weekend_planner.py
```

This will:
- Find the Toronto Guide page
- Query Activities DB for "Beaches" tag
- Query Food DB for "Turkish" or "Hakka" tags
- Query all Cafes
- Create "Perfect Weekend Adventure" page with all content
- Format everything with proper headings, lists, toggle, and callout

**That's it! No other setup needed.**

## Command Format

**Script Name**: `create_weekend_planner.py` (located in `skills/toronto_guide/`)

**Command Structure**: 
```
python3 skills/toronto_guide/create_weekend_planner.py [OPTIONS]
```

**Default Behavior** (creates planner for Toronto Guide with Beaches, Turkish, and Hakka dining):
```
python3 skills/toronto_guide/create_weekend_planner.py
```

### Execution Examples

```bash
# Default: Toronto Guide with Beaches, Turkish, Hakka
python3 skills/toronto_guide/create_weekend_planner.py

# Montreal Guide with Parks and French Dining
python3 skills/toronto_guide/create_weekend_planner.py \
  --main-page "Montreal Guide" \
  --activities-tag "Parks" \
  --food-tags "French" "Quebec"

# Vancouver Guide with specific tags
python3 skills/toronto_guide/create_weekend_planner.py \
  --main-page "Vancouver Guide" \
  --activities-tag "Mountains" \
  --food-tags "Asian" "Pacific"
```

## How It Works

1. **Search Main Page** - Finds the city guide page by name
2. **Locate Databases** - Discovers Activities, Food, and Cafes databases
3. **Query Activities** - Filters for items with specified tag
4. **Query Restaurants** - Filters for items with any of specified tags
5. **Query Cafes** - Retrieves all cafe entries
6. **Create Page** - Generates "Perfect Weekend Adventure" child page
7. **Format Content** - Structures all data with proper Notion blocks
8. **Report Results** - Shows collected data and counts

## Fully Parameterized Design

All filtering criteria are configurable through command-line parameters:

### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--main-page` | string | "Toronto Guide" | Name of the main guide page |
| `--activities-db` | string | "Activities" | Name of the activities database |
| `--food-db` | string | "Food" | Name of the food database |
| `--cafes-db` | string | "Cafes" | Name of the cafes database |
| `--activities-tag` | string | "Beaches" | Tag to filter activities |
| `--food-tags` | list | ["Turkish", "Hakka"] | Tags to filter restaurants |

### Important Notes

- **Main page**: Must match exact page name in Notion (case-sensitive)
- **Database names**: Must match child database names under main page
- **Activity tag**: Single tag value, e.g., "Beaches", "Museums", "Parks"
- **Food tags**: Space-separated list of tags, e.g., `"Turkish" "Hakka" "Italian"`
- **Output**: Creates "Perfect Weekend Adventure" page as child of main page

### Page Structure Created

The skill creates a page with this exact structure:

```
🎒 Perfect Weekend Adventure (Heading 1)

🏖️ Beach Activities (Heading 2)
• Activity 1 - Google Maps Link
• Activity 2 - Google Maps Link
...

🍽️ Cultural Dining Experience (Heading 2)
1. Restaurant 1 (Tag: Turkish)
2. Restaurant 2 (Tag: Hakka)
...

☕ Coffee Break Spots (Heading 2)
📋 Top Cafes to Visit (Toggle)
  ☐ Cafe 1
  ☐ Cafe 2
  ...

📊 Weekend Summary (Heading 2)
This weekend includes [X] beach activities, [Y] cultural dining options, and [Z] coffee spots to explore!

────────────────── (Divider)

💡 Pro tip: Check the Seasons database for the best time to enjoy outdoor activities!
```

## Core Components

### TorontoGuideNotionTools - Notion API Wrapper
- Page and database searching
- Database querying with filters
- Property extraction (name, tags, URLs)
- Page creation
- Block addition to pages
- Recursive block traversal

### WeekendAdventurePlanner - Planning Logic
- Orchestrates the planning workflow
- Applies activity, dining, and cafe filters
- Collects and organizes data
- Builds formatted page content
- Handles errors and reports results

## Use Cases

- **Weekend getaways** - Create itineraries for specific interests
- **Tourist guides** - Generate curated activity lists
- **City exploration** - Organize activities by category and cuisine
- **Travel planning** - Build structured guides with dining and cafe recommendations
- **Event planning** - Gather venue and activity options in one place

## MCP Tools Used

1. **search** - Find pages and databases by query
2. **databases.query** - Query databases with filters
3. **blocks.children.list** - Get child blocks recursively
4. **pages.create** - Create new pages
5. **blocks.children.append** - Add blocks to pages
