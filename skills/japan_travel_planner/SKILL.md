# Japan Travel Planner Skills Documentation

This directory contains MCP-based skills for managing Japan travel planning tasks in Notion.

## Skills Overview

### 1. Remove Osaka Itinerary (`remove_osaka_itinerary.py`)

Remove itinerary items from the Travel Itinerary database based on:
- **Location filter**: Remove items from specific locations (e.g., Osaka)
- **Day filter**: Target specific days (e.g., Day 1, Day 2)
- **Time threshold**: Remove entries after a specified time (default: 6 PM)

**Usage:**
```bash
python3 remove_osaka_itinerary.py
```

**Key Features:**
- Searches and identifies the Travel Itinerary database
- Filters items by location and day
- Removes items based on time threshold
- Uses 100% MCP tools for all operations

---

### 2. Restaurant Expenses Sync (`restaurant_expenses_sync.py`)

Synchronize restaurant expenses from the Itinerary database to the Expenses database.

**Usage:**
```bash
python3 restaurant_expenses_sync.py
```

**Key Features:**
- Extracts restaurant entries from the Travel Itinerary database
- Creates corresponding expense records
- Handles amount, date, and category mapping
- Uses 100% MCP tools for all operations

---

### 3. Packing Progress Summary (`packing_progress_summary.py`)

Manage packing list status and create a progress summary in the Japan Travel Planner page.

**Step 1: Update Packing Items**
- Marks specific items as packed in the Packing List database:
  - Hat (in Clothes category)
  - SIM Card (in Essentials)
  - Wallet (in Essentials)

**Step 2: Create Progress Summary**
- Searches for the Packing List database and Japan Travel Planner page
- Queries all items in the database to collect statistics
- Creates a new section in the main planning page after "Packing List 💼" heading
- Displays packing progress in the format: "Category: X/Y packed"

**Usage:**
```bash
python3 packing_progress_summary.py
```

**Input Requirements:**
- Notion API key must be set in `EVAL_NOTION_API_KEY` environment variable
- Packing List database must exist with the following structure:
  - Name (title property)
  - Type (multi_select: Clothes, Electronics, Essentials, Miscellaneous, Shoes, Toiletries)
  - Packed (checkbox)
  - Quantity (number)
  - Notes (rich_text)

**Output:**
The skill creates the following structure in Japan Travel Planner page:
```
**Packing Progress Summary**
• Clothes: X/Y packed
• Electronics: X/Y packed
• Essentials: X/Y packed
• Miscellaneous: X/Y packed
• Shoes: X/Y packed
• Toiletries: X/Y packed
```

**Key Features:**
- Queries Packing List database for all items
- Groups items by category (Type property)
- Counts packed vs total items per category
- Creates both summary block and updates item statuses
- Uses 100% MCP tools for all operations

---

## MCP Tools Used

All skills use the `NotionMCPTools` wrapper class which provides:

### Database & Page Operations
- `search()`: Search for pages and databases
- `query_database()`: Query database with filters
- `get_page()`: Retrieve page details
- `create_page()`: Create new page in database
- `patch_page()`: Archive or update page

### Block Operations
- `get_block_children()`: Get all child blocks
- `append_block_children()`: Add new blocks
- `update_block()`: Modify block content
- `update_page_property()`: Update page properties

### Helper Functions
- `parse_time_to_minutes()`: Convert time strings to minutes
- `extract_page_property()`: Extract specific properties from pages

---

## Environment Setup

Ensure the following environment variable is set:
```bash
export EVAL_NOTION_API_KEY="your-notion-api-key"
```

Or create a `.mcp_env` file in the project root:
```
EVAL_NOTION_API_KEY=your-notion-api-key
```

---

## Common Patterns

### Searching for Resources
```python
async with NotionMCPTools(api_key) as mcp:
    result = await mcp.search("Packing List")
    data = json.loads(result)
    database = next((item for item in data["results"] if item["object"] == "database"), None)
```

### Querying Databases
```python
query_result = await mcp.query_database(database_id)
items = json.loads(query_result).get("results", [])
```

### Creating Summary Blocks
```python
blocks = [
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
        }
    }
]
await mcp.append_block_children(page_id, blocks)
```

---

## Notes

- All skills use asynchronous operations (`async`/`await`)
- Error handling includes logging and result dictionaries
- Environment variables are loaded from multiple locations (`.mcp_env`, `.env`, etc.)
- Results follow a consistent format with `success`, `errors`, and relevant statistics
