---
name: notion-itinerary-filter
description: General-purpose itinerary filtering skill for Notion. Removes itinerary items based on location, day, and time filters. Parameters are fully configurable to handle any location, day combination, and time threshold without code changes.
---

# Itinerary Filter Skill

This is a general-purpose skill for filtering and removing itinerary items from a Notion database. By adjusting parameters, it can be used to remove items for any location, any days, and any time threshold.

## ⚠️ IMPORTANT - Read Before Using

**DO NOT generate or use different script names like:**
- ❌ `filter_itinerary.py`
- ❌ `itinerary_filter.py`
- ❌ `filter_itinerary.sh`

**ALWAYS use:**
- ✅ `python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove [OPTIONS]`

This is the ONLY correct script name and path for this skill.

## Configurable Filtering

Remove itinerary items based on three configurable dimensions:

1. **Location Filter** - Filter by location/group (e.g., Osaka, Tokyo, Kyoto, etc.)
2. **Day Filter** - Filter by specific days (e.g., Day 1, Day 2, or any day values)
3. **Time Filter** - Remove items after a specified time (e.g., after 6 PM, after 8 PM, etc.)

**Use when**: You need to filter or remove schedule items based on location, day, and time criteria. Fully parameterized - no code changes needed.

## Command Format

**Script Name**: `remove_osaka_itinerary.py` (located in `skills/japan_travel_planner/`)

**Command Structure**: 
```
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove [OPTIONS]
```

**Default Behavior** (removes Osaka items after 6 PM from Day 1 & 2):
```
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove
```

### Execution Examples

```bash
# Default: Remove Osaka items after 6 PM from Day 1 & 2
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove

# Remove Tokyo items after 7 PM from Day 3 & 4
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove \
  --location "Tokyo" \
  --days "Day 3" "Day 4" \
  --cutoff-time 19

# Remove Kyoto items after 8 PM from Day 1 & 2
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove \
  --location "Kyoto" \
  --cutoff-time 20

# Remove items before 10 AM from Day 1
python3 skills/japan_travel_planner/remove_osaka_itinerary.py remove \
  --location "Tokyo" \
  --days "Day 1" \
  --cutoff-time 10
```

## How It Works

1. **Search Hub Page** - Finds the travel planner page by name
2. **Locate Database** - Finds the itinerary database within the hub
3. **Query Items** - Filters database for specified location and days
4. **Parse Times** - Converts time strings to comparable format
5. **Filter by Time** - Identifies items after the cutoff time
6. **Remove Items** - Archives matched items
7. **Report Results** - Shows removed items and count

## Fully Parameterized Design

All filtering criteria are configurable through command-line parameters:

### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--hub-page` | string | "Japan Travel Planner" | Name of the hub page |
| `--database-name` | string | "Travel Itinerary" | Name of the itinerary database |
| `--location` | string | "Osaka" | Location/Group to filter |
| `--days` | list | ["Day 1", "Day 2"] | Days to process |
| `--cutoff-time` | int | 18 | Cutoff hour in 24-hour format (0-23) |

### Important Notes

- **Location values**: Must match the exact values in the "Group" property (e.g., "Osaka", "Tokyo", "Kyoto")
- **Days format**: Use "Day 1", "Day 2", etc. or exact day values in database
- **Cutoff time**: Use 24-hour format (0-23), where 18 = 6 PM, 19 = 7 PM, 20 = 8 PM, etc.
- **Time filtering**: Removes items AFTER the cutoff time (not including the cutoff time itself). For example, `--cutoff-time 18` removes items after 6 PM, but keeps items AT 6 PM.

### Parameter Quick Reference

**For removing items after a specific time:**
- After 6 PM: `--cutoff-time 18`
- After 7 PM: `--cutoff-time 19`
- After 8 PM: `--cutoff-time 20`
- After 9 PM: `--cutoff-time 21`
- After 10 AM: `--cutoff-time 10`

**For specifying multiple days:**
```bash
--days "Day 1" "Day 2" "Day 3"
```

**For specifying location (must match database exactly):**
```bash
--location "Osaka"
--location "Tokyo"
--location "Kyoto"
```

## Core Components

### TravelNotionTools - Notion API Wrapper
- Page searching
- Database discovery and querying
- Property extraction (title, rich_text, select, date)
- Time parsing for multiple formats
- Page archiving (soft delete)

### TravelItineraryFilter - Filtering Logic
- Orchestrates the filtering workflow
- Applies location, day, and time filters
- Handles errors and reports results

## Use Cases

- **Remove late items** - Remove items after 6 PM on specific days
- **Remove early items** - Remove items before 9 AM
- **Location-based filtering** - Remove all Day 2 events for a specific location
- **Multi-location processing** - Run once per location with different parameters
- **Time threshold adjustments** - Adjust cutoff times based on requirements

## MCP Tools Used

1. **search** - Find pages by query
2. **data_sources.query** - Query databases with filters
3. **blocks.children.list** - Get child blocks  
4. **pages.update** - Archive pages (soft delete)
