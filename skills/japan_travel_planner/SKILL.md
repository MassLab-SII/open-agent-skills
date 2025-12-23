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

### 4. Daily Itinerary Overview (`daily_itinerary_overview.py`)

Create a comprehensive daily itinerary overview page organizing all activities by day with visited status.

**Usage:**
```bash
EVAL_NOTION_API_KEY="your-key" python3 daily_itinerary_overview.py
```

**Input Requirements:**
- Notion API key must be set in `EVAL_NOTION_API_KEY` environment variable
- Travel Itinerary database must exist with the following structure:
  - Name (title property)
  - Day (select: Day 1, Day 2, Day 3, etc.)
  - Group (select: Tokyo, Osaka, Kyoto, etc.)
  - Visited (checkbox)
  - Type (multi_select: Attractions, Shopping, Food)

**Step-by-Step Process:**

1. **Search for Main Page**: Locates the "Japan Travel Planner" page
2. **Search for Database**: Finds the "Travel Itinerary" database
3. **Query All Activities**: Retrieves all 73+ activities from the database
4. **Parse by Day**: Organizes activities by day (Day 1, Day 2, Day 3) and counts visited items
5. **Create Child Page**: Creates "Daily Itinerary Overview" as a child of Japan Travel Planner
6. **Build Blocks**: Constructs 35+ blocks with proper structure:
   - `heading_1`: "📅 Daily Itinerary Overview"
   - `heading_2`: "📊 Trip Summary"
   - `paragraph`: "Total activities visited (from Day 1 to Day 3): [COUNT]"
   - `heading_2`: "🌅 Day 1", "🌆 Day 2", "🌃 Day 3"
   - `to_do` items for each activity with checked status matching visited status
7. **Add Blocks**: Uses `API-patch-block-children` to add all blocks to the page

**Output Structure:**
```
Daily Itinerary Overview (child page)
├── 📅 Daily Itinerary Overview (heading_1)
├── 📊 Trip Summary (heading_2)
├── Total activities visited (from Day 1 to Day 3): 8 (paragraph)
├── 🌅 Day 1 (heading_2)
│   ├── [✓] Osaka Castle - Osaka (to_do)
│   ├── [✓] Unagi Kushiyaki Idumo - Osaka (to_do)
│   └── [ ] Other activities... (to_do)
├── 🌆 Day 2 (heading_2)
│   ├── [✓] Studio Ghibli Store - Osaka (to_do)
│   └── [ ] Other activities... (to_do)
└── 🌃 Day 3 (heading_2)
    ├── [✓] Tokyo Tower - Tokyo (to_do)
    └── [ ] Other activities... (to_do)
```

**Key Features:**
- Organizes 29 activities across Day 1-3
- Automatically counts visited items (8 in this case)
- Matches to-do checked status with database visited status
- Displays city/group name for each activity
- Uses emoji-based day indicators for visual clarity
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
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": "Summary"}}]
        }
    }
]
await mcp.session.call_tool("API-patch-block-children", {
    "block_id": page_id,
    "children": blocks
})
```

---

## Notes

- All skills use asynchronous operations (`async`/`await`)
- Error handling includes logging and result dictionaries
- Environment variables are loaded from multiple locations (`.mcp_env`, `.env`, etc.)
- Results follow a consistent format with `success`, `errors`, and relevant statistics
