---
name: remove-osaka-itinerary
description: Removes itinerary items from Osaka after 6 PM for Day 1 and Day 2 in the Japan Travel Planner using 100% MCP tools.
---

# Japan Travel Planner - Remove Osaka Itinerary Skill

This skill removes itinerary items from Osaka after 6 PM on Day 1 and Day 2 using MCP-based database operations.

## Core Concepts

In Notion automation, we distinguish two types of operations:

**Skill**: Meaningful combinations of multiple MCP tool calls, encapsulated as independent Python scripts
**Basic Tools**: Single MCP function calls (API-post-search, API-post-database-query, etc.)

## Skills

### Remove Osaka Itinerary

**Use Cases**:
- Filter and remove travel itinerary items based on location, day, and time
- Archive items in Osaka after 6 PM for Day 1 and Day 2
- Customize for different locations, days, and time thresholds

**Usage**:
```bash
# Basic usage with environment variable
export EVAL_NOTION_API_KEY="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"
python3 remove_osaka_itinerary.py

# Or with custom parameters in code
python3 -c "
import asyncio
from skills.japan_travel_planner.remove_osaka_itinerary import RemoveOsakaItinerary

async def main():
    skill = RemoveOsakaItinerary(
        api_key='ntn_...',
        location='Osaka',
        days=['Day 1', 'Day 2'],
        cutoff_time_minutes=18*60  # 6 PM
    )
    result = await skill.remove_itinerary()
    print(f'Removed: {result[\"removed_count\"]} items')

asyncio.run(main())
"
```

**Expected Output**:
```
======================================================================
📊 Execution Summary
======================================================================
Success: True
Items removed: 4

Removed items:
  - Rikuro's Namba Main Branch (7 PM on Day 1)
  - Ebisubashi Bridge (9 PM on Day 1)
  - Shin Sekai "New World" (8 PM on Day 2)
  - Katsudon Chiyomatsu (7:30 PM on Day 2)
```

## Execution Flow

1. **Search Page**: Find "Japan Travel Planner" page via `API-post-search`
2. **Locate Database**: Find "Travel Itinerary" database via `API-get-block-children`
3. **Query Database**: Query with filter (Location="Osaka" AND Day="Day 1"|"Day 2") via `API-post-database-query`
4. **Time Filter**: Parse time from "Notes" property, keep items where time > 6 PM
5. **Archive Items**: Archive matched items via `API-patch-page` with `archived=true`

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `API-post-search` | Search for pages |
| `API-get-block-children` | Retrieve page structure |
| `API-post-database-query` | Query database with filters |
| `API-patch-page` | Archive items |

## Customization

Adapt the skill for different scenarios:

```python
# Different location
RemoveOsakaItinerary(location="Tokyo")

# Different days
RemoveOsakaItinerary(days=["Day 3", "Day 4"])

# Different time threshold
RemoveOsakaItinerary(cutoff_time_minutes=15*60)  # 3 PM

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

