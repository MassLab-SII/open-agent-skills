---
name: faq-column-layout
description: Reorganizes FAQ section in Self Assessment page into a two-column layout with balanced Q&A pairs using MCP tools.
---

# Self Assessment - FAQ Column Layout Skill

This skill reorganizes the FAQ toggle in the Self Assessment page into a two-column layout with balanced Q&A pairs.

## Core Concepts

In Notion automation, we distinguish two types of operations:

**Skill**: Meaningful combinations of multiple MCP tool calls, encapsulated as independent Python scripts
**Basic Tools**: Single MCP function calls (API-post-search, API-get-block-children, etc.)

## Skills

### 1. FAQ Column Layout

**Use Cases**:
- Reorganize FAQ content into visual two-column layout
- Balance Q&A pairs across columns
- Maintain consistent formatting (heading_3 for questions, paragraph for answers)
- Add new Q&A content for column balance

**Usage**:
```bash
# Basic usage with environment variable
export EVAL_NOTION_API_KEY="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"
python3 faq_column_layout.py

# Or with custom parameters in code
python3 -c "
import asyncio
from skills.self_assessment.faq_column_layout import FAQColumnLayout

async def main():
    skill = FAQColumnLayout(api_key='ntn_...')
    result = await skill.reorganize_faq()
    print(f'Success: {result[\"success\"]}')
    print(f'Q&A pairs moved: {result[\"qa_pairs_moved\"]}')

asyncio.run(main())
"
```

**Expected Output**:
```
======================================================================
📊 Execution Summary
======================================================================
Success: True
Message: FAQ reorganized into 2 columns with 4 Q&A pairs
FAQ Toggle ID: 2532b7e8-cebd-81f9-be9c-e63a5e4b2bc4
Columns Created: True
Q&A Pairs Moved: 4
```

## Execution Flow

1. **Search Page**: Find "Self Assessment" page via `API-post-search`
2. **Find FAQ Toggle**: Retrieve page children and locate FAQ toggle block
3. **Get FAQ Content**: Extract existing Q&A pairs from FAQ toggle
4. **Create Columns**: Create column_list with two columns via `API-patch-block-children`
5. **Distribute Content**: Move Q&A pairs to left and right columns
6. **Add New Content**: Add new Q4 if needed for balance
7. **Cleanup**: Delete old Q&A blocks from FAQ toggle

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `API-post-search` | Search for Self Assessment page |
| `API-get-block-children` | Retrieve page and block structure |
| `API-patch-block-children` | Create columns and add Q&A content |
| `API-delete-a-block` | Remove old Q&A blocks |

## Customization

Adapt the skill for different scenarios:

```python
# Use custom API key
skill = FAQColumnLayout(api_key="custom_key")

# Execute with different parameters
result = await skill.reorganize_faq()

# Access result details
if result["success"]:
    print(f"Moved {result['qa_pairs_moved']} Q&A pairs")
```

---

### 2. Numbered List Emojis

**Use Cases**:
- Replace plain numbered lists with emoji numbers for visual formatting
- Improve visual distinction of list items
- Convert multiple numbered list formats across the page
- Enhance readability of sequential items

**Prerequisites**:
- Self Assessment page must exist in Notion
- Numbered list items (1., 2., 3., etc.) must be present
- Environment variable `EVAL_NOTION_API_KEY` must be set

**Usage**:
```bash
# Basic usage with environment variable
export EVAL_NOTION_API_KEY="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"
python3 skills/self_assessment/numbered_list_emojis.py
```

**What It Does**:
1. Finds the Self Assessment page
2. Retrieves all blocks recursively from the page
3. Identifies all numbered_list_item blocks
4. For each numbered item (1., 2., 3., etc.):
   - Extracts the number
   - Replaces it with corresponding emoji (1️⃣, 2️⃣, 3️⃣, etc.)
   - Updates the block with API-patch-block
5. Reports total items found and updated

**Example Transformation**:
```
Before:  1. Record Each Hyperfocus Session:
After:   1️⃣ Record Each Hyperfocus Session:

Before:  2. Review and Reflect:
After:   2️⃣ Review and Reflect:

Before:  3. Adjust and Optimize:
After:   3️⃣ Adjust and Optimize:
```

**Emoji Mapping**:
- 1 → 1️⃣, 2 → 2️⃣, 3 → 3️⃣, 4 → 4️⃣, 5 → 5️⃣
- 6 → 6️⃣, 7 → 7️⃣, 8 → 8️⃣, 9 → 9️⃣, 10 → 🔟

**Output Example**:
```
======================================================================
RESULT SUMMARY
======================================================================
Success: True
Self Assessment Page ID: 2552b7e8-cebd-804e-b8ce-c61bddd75364
Numbered List Items Found: 13
Blocks Updated: 13
```

## MCP Tools Used

### FAQ Column Layout
| Tool | Purpose |
|------|---------|
| `API-post-search` | Search for Self Assessment page |
| `API-get-block-children` | Retrieve page and block structure |
| `API-patch-block-children` | Create columns and add Q&A content |
| `API-delete-a-block` | Remove old Q&A blocks |

### Numbered List Emojis
| Tool | Purpose |
|------|---------|
| `API-post-search` | Search for Self Assessment page |
| `API-get-block-children` | Recursively retrieve all blocks |
| `API-patch-block` | Update numbered list items with emoji numbers |

## Customization

Adapt the skills for different scenarios:

```python
# FAQ Column Layout - Use custom API key
skill = FAQColumnLayout(api_key="custom_key")
result = await skill.reorganize_faq()

# Numbered List Emojis - Use custom API key
skill = NumberedListEmojis(api_key="custom_key")
result = await skill.process_page()

# Access result details
if result["success"]:
    print(f"Blocks updated: {result['blocks_updated']}")
```

## File Structure

```
skills/self_assessment/
├── faq_column_layout.py     # Main skill implementation
├── numbered_list_emojis.py  # Emoji numbers skill implementation
├── utils.py                 # MCP tools wrapper
├── SKILL.md                 # This documentation
└── __init__.py              # Package initialization
```

## Key Methods

**`FAQColumnLayout`** class:
- `__init__(api_key)`: Initialize skill
- `async reorganize_faq()`: Execute the skill, returns `{success, message, faq_toggle_id, columns_created, qa_pairs_moved, errors}`

**Helper functions** in `utils.py`:
- `NotionMCPTools`: Context manager for MCP tool calls
- `extract_block_property()`: Extract property from Notion blocks

## Related Skills

- Japan Travel Planner - Remove Osaka Itinerary (similar MCP pattern)
- Other Self Assessment automation tasks
