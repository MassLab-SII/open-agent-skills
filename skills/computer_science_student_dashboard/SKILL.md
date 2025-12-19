---
name: code-snippets-go
description: Adds a new Go column with code examples to the "Code Snippets" section of the Computer Science Student Dashboard using 100% MCP tools. This skill demonstrates how to use MCP for Notion page structure navigation and content manipulation.
---

# Computer Science Student Dashboard - Add Go Code Snippets Skill

This skill demonstrates **100% MCP-based implementation** for managing Notion page content. It adds a new Go programming language column to the "Code Snippets" section of the Computer Science Student Dashboard.

## Overview

The skill orchestrates multiple MCP operations to:
- Find the Computer Science Student Dashboard page
- Locate the "Code Snippets" section and its column_list block
- Add a new Go column positioned after the existing Python column
- Populate the Go column with a bold "Go" header and three code examples
- Verify the final result by retrieving updated column information

## Basic Usage

```bash
# This skill should be integrated with an MCP server instance
python3 add_go_snippets.py

# Or with explicit API key
python3 add_go_snippets.py <YOUR_NOTION_API_KEY>

# Or using environment variable
export EVAL_NOTION_API_KEY="ntn_..."
python3 add_go_snippets.py
```

**This will automatically:**
1. Search for "Computer Science Student Dashboard" page
2. Retrieve page structure to find Code Snippets section
3. Locate the column_list block
4. Identify existing columns (CSS, Python, JavaScript)
5. Find the Python column position
6. Create a new column after Python
7. Add "Go" heading (bold)
8. Add three Go code examples with captions
9. Verify final column order and return success

## Task Details

### 1. Page Discovery
- **Target**: "Computer Science Student Dashboard"
- **Method**: MCP `API-post-search` tool
- **Returns**: Page ID and metadata

### 2. Section Navigation
- **Find**: "Code Snippets" heading
- **Method**: Retrieve page children, scan for heading blocks
- **Check**: Both direct children and sibling blocks

### 3. Column Analysis
- **Examine**: Existing columns (CSS, Python, JavaScript)
- **Extract**: Column header text by parsing paragraph blocks
- **Position**: Identify Python column for insertion point

### 4. Column Addition
- **Create**: New column block after Python
- **Method**: MCP `API-patch-block-children` with `after` parameter
- **Returns**: New column ID

### 5. Content Population

#### Go Column Header
- **Type**: Paragraph block with bold annotation
- **Content**: "Go"

#### Code Examples (3 total)

**Example 1: Basic Go program**
```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
```
- Caption: "Basic Go program"
- Language: go

**Example 2: For loop in Go**
```go
for i := 0; i < 5; i++ {
    fmt.Println(i)
}
```
- Caption: "For loop in Go"
- Language: go

**Example 3: Function definition in Go**
```go
func add(a, b int) int {
    return a + b
}
```
- Caption: "Function definition in Go"
- Language: go

### 6. Verification
- **Retrieve**: Updated column_list children
- **Extract**: Final column order and names
- **Confirm**: Go column is positioned correctly

## Technical Architecture

### MCP Tools Used

This skill uses the following MCP tools exclusively:

| Tool | Purpose |
|------|---------|
| **API-post-search** | Find pages and databases by query |
| **API-get-block-children** | Retrieve child blocks of any parent block |
| **API-patch-block-children** | Create or append blocks to a parent block |

### Tool Invocation Pattern

#### 1. Page Discovery
```
API-post-search
├─ Input: {"query":"Computer Science Student Dashboard"}
└─ Output: Page ID, metadata
```

#### 2. Page Structure Retrieval
```
API-get-block-children
├─ Input: {"block_id":"<page_id>"}
├─ Returns: All page children blocks
└─ Parse: Find Code Snippets heading
```

#### 3. Heading Children Retrieval
```
API-get-block-children
├─ Input: {"block_id":"<heading_id>"}
├─ Returns: Blocks under heading
└─ Parse: Find column_list block
```

#### 4. Column List Analysis
```
API-get-block-children
├─ Input: {"block_id":"<column_list_id>"}
├─ Returns: All columns
├─ For each column:
│  └─ API-get-block-children to get column contents
└─ Parse: Extract header text and identify Python column
```

#### 5. Add New Column
```
API-patch-block-children
├─ Input: {
│   "block_id":"<column_list_id>",
│   "children":[{"type":"column","column":{"children":[]}}],
│   "after":"<python_column_id>"
│ }
└─ Output: New column ID
```

#### 6. Add Go Header
```
API-patch-block-children
├─ Input: {
│   "block_id":"<go_column_id>",
│   "children":[{
│     "type":"paragraph",
│     "paragraph":{
│       "rich_text":[{
│         "type":"text",
│         "text":{"content":"Go"},
│         "annotations":{"bold":true}
│       }]
│     }
│   }]
│ }
└─ Output: Confirmation
```

#### 7. Add Code Blocks (repeated 3 times)
```
API-patch-block-children
├─ Input: {
│   "block_id":"<go_column_id>",
│   "children":[{
│     "type":"code",
│     "code":{
│       "rich_text":[{"type":"text","text":{"content":"<go_code>"}}],
│       "language":"go",
│       "caption":[{"type":"text","text":{"content":"<caption>"}}]
│     }
│   }]
│ }
└─ Output: Confirmation
```

#### 8. Verification
```
API-get-block-children (recursive on all columns)
├─ Input: {"block_id":"<column_list_id>"}
├─ For each column:
│  └─ Get column contents to extract header
└─ Output: Final column order [CSS, Python, Go, JavaScript]
```

## Implementation Details

### Pure MCP Architecture

This skill demonstrates the **100% MCP approach**:

✅ **No `notion_client` library** - All operations through MCP protocol
✅ **Async/await pattern** - Uses `NotionMCPTools` context manager
✅ **Error handling** - Graceful fallbacks for block structure variations
✅ **JSON parsing** - Direct parsing of MCP API responses
✅ **Block manipulation** - Creates and appends blocks via standardized MCP format

### Key Components

**utils.py - NotionMCPTools Class**
- Manages MCP client initialization and lifecycle
- Provides async methods for core operations:
  - `search(query)` - Search pages
  - `get_block_children(block_id)` - Retrieve blocks
  - `patch_block_children(block_id, children, after)` - Create/append blocks
- Includes helpers for creating block structures:
  - `create_paragraph_block(text, bold)`
  - `create_code_block(code, language, caption)`
  - `create_column_block()`

**add_go_snippets.py - Skill Execution**
- Orchestrates the complete workflow
- Step-by-step operations with logging
- Robust error handling and fallback strategies
- JSON response parsing utilities:
  - `extract_page_id_from_json()` - Extract IDs from responses
  - `parse_block_response()` - Parse block arrays
  - `find_heading_with_text()` - Search for blocks by content

### Error Handling Strategy

The skill handles various scenarios:

| Scenario | Handling |
|----------|----------|
| Page not found | Return error, suggest searching manually |
| Column list not found | Check both child and sibling positions |
| Python column missing | Append to end instead of after-positioning |
| API failures | Retry with timeout and detailed error logging |
| Parse errors | Graceful degradation with partial results |

## Workflow Diagram

```
START
  │
  ├─ Search for Dashboard page
  │   └─ Get page ID
  │
  ├─ Get page children
  │   └─ Find "Code Snippets" heading
  │
  ├─ Check heading children for column_list
  │   └─ Not found? Check page siblings
  │
  ├─ Get column_list children
  │   └─ Iterate each column for headers
  │
  ├─ Identify Python column position
  │
  ├─ Create new column after Python
  │   └─ Get new column ID
  │
  ├─ Add Go header (bold paragraph)
  │
  ├─ Add 3 code blocks sequentially
  │   ├─ Basic Go program
  │   ├─ For loop example
  │   └─ Function example
  │
  ├─ Retrieve all columns again
  │   └─ Extract final column order
  │
  └─ SUCCESS: Return results
```

## Testing & Validation

### Success Criteria
- ✅ New Go column created
- ✅ Positioned after Python column
- ✅ Bold "Go" header present
- ✅ Three code blocks with correct content
- ✅ All code blocks have language="go"
- ✅ Captions match specifications
- ✅ Final column order: CSS, Python, Go, JavaScript

### Verification Query
```sql
SELECT column_name, column_position 
FROM code_snippets_section
WHERE dashboard = "Computer Science Student Dashboard"
```

Expected result:
- Column 1: CSS
- Column 2: Python
- Column 3: Go (NEW)
- Column 4: JavaScript

## References

### MCP Notion Server
- Repository: @notionhq/notion-mcp-server
- Tools: API-post-search, API-get-block-children, API-patch-block-children

### Notion API Concepts
- Block structure and hierarchy
- Column layouts and column_list blocks
- Rich text annotations (bold, italic, code)
- Block children and append operations
