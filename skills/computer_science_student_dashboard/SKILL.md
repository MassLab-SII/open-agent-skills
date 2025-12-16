---
name: notion-code-snippets
description: This skill manages code snippets in a Computer Science Student Dashboard Notion page. It provides tools for adding programming language columns and organizing code examples. Use this when you need to programmatically manage Notion pages.
---

# Notion Code Snippets Skill

This skill provides comprehensive management capabilities for the Computer Science Student Dashboard Notion page:

1. **Code Snippet Management**: Add new programming language columns with code examples
2. **Content Organization**: Automatically position new content and format code blocks
3. **Page Navigation**: Find and traverse Notion page structure dynamically

## 1. Add Go Code Snippets

Add a new Go column with code examples to the Code Snippets section of the Computer Science Student Dashboard page.

**Use when**: You need to add new programming language sections with code examples to your Notion dashboard.

### Example

```bash
# Using command-line argument
python add_go_snippets.py

# Using environment variable


## Implementation Details

The skill performs the following steps:

1. **Search Page** - Uses the Notion search tool to find the page
2. **Find Section** - Retrieves page children to locate the "Code Snippets" heading
3. **Locate Column List** - Finds the column_list block within the section
4. **Examine Columns** - Inspects existing columns to understand structure
5. **Create Column** - Adds a new column positioned after the Python column
6. **Add Heading** - Inserts a bold heading to the column
7. **Add Code Examples** - Appends code blocks with examples
8. **Verify** - Confirms the final result

The three Go code examples added are:
- Basic Go program (Hello World)
- For loop example
- Function definition example

## MCP Tools Used

The skill utilizes three core MCP Notion tools:

1. **search** - Find pages by query
2. **get_block_children** - Retrieve child blocks
3. **patch_block_children** - Add or modify blocks