| name | description |---

|------|-------------|name: remove-osaka-itinerary

| remove-osaka-itinerary | Removes itinerary items from Osaka after 6 PM for Day 1 and Day 2 using MCP tools. |description: Removes itinerary items from Osaka after 6 PM for Day 1 and Day 2 in the Japan Travel Planner using 100% MCP tools.

| restaurant-expenses-sync | Syncs restaurants from Day 1 Travel Itinerary to Expenses database with standardized entries (date: Jan 1 2025, cost: $120, category: Dining). |---



# Japan Travel Planner Skills# Japan Travel Planner - Remove Osaka Itinerary Skill



This skill collection leverages Notion MCP tools for travel planning operations.This skill removes itinerary items from Osaka after 6 PM on Day 1 and Day 2 using MCP-based database operations.



## Core Concepts## Core Concepts



In Notion automation, we distinguish two types of operations:In Notion automation, we distinguish two types of operations:



**Skill**: Meaningful combinations of multiple MCP tool calls, encapsulated as independent Python scripts**Skill**: Meaningful combinations of multiple MCP tool calls, encapsulated as independent Python scripts

**Basic Tools**: Single MCP function calls (API-post-search, API-post-database-query, etc.)**Basic Tools**: Single MCP function calls (API-post-search, API-post-database-query, etc.)



## I. Skills## Skills



### 1. Remove Osaka Itinerary### Remove Osaka Itinerary



**File**: `remove_osaka_itinerary.py`**Use Cases**:

- Filter and remove travel itinerary items based on location, day, and time

**Use Cases**:- Archive items in Osaka after 6 PM for Day 1 and Day 2

- Filter and remove travel itinerary items by location, day, and time- Customize for different locations, days, and time thresholds

- Archive Osaka items after 6 PM for Day 1 and Day 2

- Customize filters for different locations and time thresholds**Usage**:

```bash

**Prerequisites**:# Basic usage with environment variable

- Japan Travel Planner page with Travel Itinerary databaseexport EVAL_NOTION_API_KEY="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"

- Itinerary items have Day, Group (location), and Notes (time) propertiespython3 remove_osaka_itinerary.py



**Usage**:# Or with custom parameters in code

```bashpython3 -c "

export EVAL_NOTION_API_KEY="ntn_..."import asyncio

python3 remove_osaka_itinerary.pyfrom skills.japan_travel_planner.remove_osaka_itinerary import RemoveOsakaItinerary

```

async def main():

**Typical Task Examples**:    skill = RemoveOsakaItinerary(

- Remove Osaka itinerary items after 6 PM on Day 1 and Day 2        api_key='ntn_...',

- Filter by Group property = "Osaka" and parse time from Notes field        location='Osaka',

- Archive matching items for cleanup        days=['Day 1', 'Day 2'],

        cutoff_time_minutes=18*60  # 6 PM

### 2. Restaurant Expenses Sync    )

    result = await skill.remove_itinerary()

**File**: `restaurant_expenses_sync.py`    print(f'Removed: {result[\"removed_count\"]} items')



**Use Cases**:asyncio.run(main())

- Synchronize restaurants from travel itinerary to expense tracker"

- Automatically create standardized expense entries```

- Link restaurants to financial records

- Maintain consistent formatting across entries**Expected Output**:

```

**Prerequisites**:======================================================================

- Travel Itinerary database with Day 1 items tagged as "Food" type📊 Execution Summary

- Expenses database with properties: Expense, Date, Transaction Amount, Category, Comment======================================================================

Success: True

**Usage**:Items removed: 4

```bash

export EVAL_NOTION_API_KEY="ntn_..."Removed items:

python3 restaurant_expenses_sync.py  - Rikuro's Namba Main Branch (7 PM on Day 1)

```  - Ebisubashi Bridge (9 PM on Day 1)

  - Shin Sekai "New World" (8 PM on Day 2)

**Typical Task Examples**:  - Katsudon Chiyomatsu (7:30 PM on Day 2)

- Create expense entries for all Day 1 restaurants```

- Set uniform date (Jan 1, 2025) and cost ($120)

- Populate comments from restaurant descriptions## Execution Flow

- Categorize entries as "Dining"

1. **Search Page**: Find "Japan Travel Planner" page via `API-post-search`

## II. Basic Tools (utils.py)2. **Locate Database**: Find "Travel Itinerary" database via `API-get-block-children`

3. **Query Database**: Query with filter (Location="Osaka" AND Day="Day 1"|"Day 2") via `API-post-database-query`

Available MCP API methods:4. **Time Filter**: Parse time from "Notes" property, keep items where time > 6 PM

5. **Archive Items**: Archive matched items via `API-patch-page` with `archived=true`

| Tool | MCP API | Purpose |

|------|---------|---------|## MCP Tools Used

| `search()` | API-post-search | Find pages and databases |

| `get_page()` | API-retrieve-a-page | Retrieve page details || Tool | Purpose |

| `get_block_children()` | API-get-block-children | Get child blocks ||------|---------|

| `query_database()` | API-post-database-query | Query with filters || `API-post-search` | Search for pages |

| `patch_page()` | API-patch-page | Archive or update pages || `API-get-block-children` | Retrieve page structure |

| `create_page()` | API-post-page | Create new pages || `API-post-database-query` | Query database with filters |

| `API-patch-page` | Archive items |

## Execution Flows

## Customization

### Remove Osaka Itinerary Flow:

1. Search for Japan Travel Planner pageAdapt the skill for different scenarios:

2. Get page children to find Travel Itinerary database

3. Query database with filters (Group="Osaka", Day="Day 1"|"Day 2")```python

4. Parse time from Notes property, filter time > 6 PM# Different location

5. Archive matching items via API-patch-pageRemoveOsakaItinerary(location="Tokyo")



### Restaurant Expenses Sync Flow:# Different days

1. Search for Travel Itinerary databaseRemoveOsakaItinerary(days=["Day 3", "Day 4"])

2. Search for Expenses database

3. Query Travel Itinerary for Day 1 + Food type# Different time threshold

4. Retrieve full page details for each restaurantRemoveOsakaItinerary(cutoff_time_minutes=15*60)  # 3 PM

5. Create expense entries in Expenses database with standardized properties

# All combined
RemoveOsakaItinerary(
    location="Kyoto",
    days=["Day 2"],
    cutoff_time_minutes=20*60  # 8 PM
)
```

## File Structure

```
skills/japan_travel_planner/
├── remove_osaka_itinerary.py    # Main skill implementation
├── utils.py                     # MCP tools wrapper
├── SKILL.md                     # This documentation
└── __init__.py                  # Package initialization
```

