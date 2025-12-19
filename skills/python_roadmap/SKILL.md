---
name: expert-level-learning-path
description: Creates an Expert Level chapter in Python Roadmap with sophisticated prerequisite chains and cross-referenced lessons through MCP tools.
---

# Expert Level Learning Path Skill

This skill creates a comprehensive **Expert Level chapter** in the Python Roadmap with sophisticated prerequisite chains, demonstrating how to build complex Notion structures using MCP tools.

## Overview

The skill orchestrates multiple MCP operations to create:
- A new Expert Level chapter (🟣 icon)
- A bridge lesson that connects Advanced → Expert content
- 4 expert-level lessons with deep prerequisite chains
- Rich content blocks with learning path guidance
- Cross-referenced relationships across lessons

## Basic Usage

```bash
# This skill should be integrated with an MCP server instance
python3 expert_level_lessons.py
```

**This will automatically:**
1. Locate the Python Roadmap's Chapters and Steps databases
2. Create the Expert Level chapter with purple circle icon
3. Find all prerequisite lessons by searching and filtering
4. Create bridge lesson linking Advanced → Expert progression
5. Create 4 expert-level lessons with proper parent/child relationships
6. Update existing lessons' status and relationships
7. Add learning path content blocks with prerequisites checklist
8. Return all created IDs for verification

## Task Details

### 1. Expert Level Chapter
- **Icon**: 🟣 (purple circle)
- **Location**: Chapters database, after Advanced Level
- **Properties**: Name: "Expert Level"

### 2. Bridge Lesson: Advanced Foundations Review
Serves as transition checkpoint from Advanced to Expert content:
- **Status**: Done
- **Chapter**: Expert Level
- **Parent**: Control Flow lesson (the "In Progress" lesson with "Control")
- **Sub-items**: 
  - Decorators
  - Calling API
  - Regular Expressions
- **Content**: Prerequisites checklist with 3 items and guidance paragraph

### 3. Expert Level Lessons (4 total)

#### Lesson 1: Metaprogramming and AST Manipulation
- Status: To Do
- Parent: Advanced Foundations Review
- Date: 2025-09-15

#### Lesson 2: Async Concurrency Patterns
- Status: To Do
- Parent: Calling API lesson
- Date: 2025-09-20

#### Lesson 3: Memory Management and GC Tuning
- Status: In Progress
- Parent: Advanced Foundations Review
- Sub-items: 
  - Any "To Do" lesson from Data Structures (e.g., Lists)
  - OOP/Classes lesson
- Date: 2025-09-25

#### Lesson 4: Building Python C Extensions
- Status: To Do
- Parent: Metaprogramming and AST Manipulation
- Date: 2025-10-01

### 4. Existing Lessons Updates
- ✓ Decorators: Status changed To Do → Done
- ✓ Error Handling: Add Async Concurrency Patterns as sub-item
- ✓ Control Flow: Status changed In Progress → Done

### 5. Learning Path Content
Added to "Advanced Foundations Review" lesson:
- **Heading 2**: "Prerequisites Checklist"
- **Bulleted List** (3 items):
  - ✅ Advanced Python Features (Decorators, Context Managers)
  - ✅ API Integration and Async Basics
  - ✅ Pattern Matching and Text Processing
- **Paragraph**: Checkpoint message before expert content

## Technical Architecture

### MCP Tools Used

This skill uses the following MCP tools:
- **API-post-search**: Find Python Roadmap page
- **API-post-database-query**: Query Chapters and Steps databases
- **API-post-page**: Create new lessons and chapters
- **API-patch-page**: Update existing lessons
- **API-patch-block-children**: Add content blocks
- **API-retrieve-a-page**: Get page details and sub-items

### Key Components

#### NotionMCPClient (utils_comprehensive.py)
High-level wrapper around MCP tools providing:
- `query_database()`: Query with flexible filtering
- `create_page()`: Create pages with all properties
- `update_page()`: Update properties and relationships
- `add_blocks()`: Add rich content blocks
- Helper methods for building properties and filters

#### ExpertLevelLessonsSkill (expert_level_lessons.py)
Main skill orchestration with 7 execution steps:
1. Find databases
2. Create Expert chapter
3. Find prerequisite lessons
4. Create bridge lesson
5. Create expert lessons
6. Update existing lessons
7. Add learning content

### Prerequisite Lessons Discovery

The skill implements robust lesson discovery:
- Searches by title containing keywords (e.g., "Control", "Decorator")
- Filters by status (e.g., "In Progress", "To Do")
- Extracts relationships from existing lessons
- Handles missing lessons gracefully with warnings

### Relationship Building

Complex relationship handling:
- Parent-child hierarchies between lessons
- Cross-chapter linking (Advanced → Expert)
- Multi-level sub-item management
- Bidirectional updates (e.g., adding to Error Handling's sub-items)

## Quick Start

### Integration with MCP Server

```python
from mcp import MCPStdioServer
from expert_level_lessons import execute_skill

# Initialize MCP server
mcp = MCPStdioServer()

# Execute the skill
results = await execute_skill(mcp)

print(f"Expert Chapter ID: {results['expert_chapter_id']}")
print(f"Bridge Lesson ID: {results['bridge_lesson_id']}")
```

### Using NotionMCPClient

```python
from utils_comprehensive import NotionMCPClient, StatusValue

client = NotionMCPClient(mcp_server)

# Search for pages
results = await client.search_page("Python Roadmap")

# Query database
lessons = await client.query_database(
    database_id=STEPS_DB_ID,
    filter_title_contains="Control",
    filter_status_equals=StatusValue.IN_PROGRESS
)

# Create a page with properties
page = await client.create_page(
    database_id=STEPS_DB_ID,
    properties={
        "Lessons": [{"text": {"content": "New Lesson"}}],
        "Status": {"name": StatusValue.TODO},
        "Date": {"start": "2025-09-15"}
    }
)

# Add content blocks
blocks = [
    client.create_heading_block("Title", level=2),
    client.create_paragraph_block("Description")
]
await client.add_blocks(page_id, blocks)
```

## Expected Result

After successful execution, you will have:

✓ **Expert Level chapter** with 🟣 icon in Chapters database
✓ **Advanced Foundations Review** lesson as bridge with learning checklist
✓ **4 expert lessons** with proper hierarchies:
  - Metaprogramming → AST Manipulation
  - Async Concurrency Patterns → Error Handling integration
  - Memory Management → Data Structures & OOP relationships
  - C Extensions → Metaprogramming parent
✓ **Updated existing lessons** with correct status transitions
✓ **Rich learning content** with prerequisites and guidance

## Architecture Highlights

### MCP-First Design
- All Notion operations use MCP tools (never direct API)
- Encapsulated in `NotionMCPClient` for reusability
- Clear separation of concerns: utils vs. skill logic

### Type Safety
- Full type hints throughout
- Enum for status values (StatusValue)
- Return type documentation for all methods

### Error Handling
- Graceful handling of missing lessons
- Comprehensive error messages
- Detailed execution logging

### Extensibility
- `NotionMCPClient` is domain-agnostic
- Can be used for other Notion workflows
- Reusable helper methods for common operations
- Configurable constants in `ExpertLevelLessonsConfig`

## File Structure

```
skills/notion_mcp_tutorial/
├── utils_comprehensive.py          # MCP tools wrapper (reusable)
├── expert_level_lessons.py         # Skill implementation
├── SKILL.md                        # This file
└── README.md                       # Tutorials & guides
```

## Troubleshooting

**Missing lessons**: The skill logs warnings but continues. Check search terms in `_find_prerequisite_lessons()`.

**Database not found**: Ensure Python Roadmap has Chapters and Steps databases with correct names.

**Relationship errors**: Sub-items are created as lists; ensure all IDs are valid.

**Block content issues**: Use `client.create_*_block()` helpers instead of raw dictionaries.

## Learning Resources

This skill demonstrates:
- How to structure complex workflows with MCP
- Building reusable client libraries
- Handling Notion relationships and hierarchies
- Filtering and searching strategies
- Error handling and logging best practices
- Async/await patterns with MCP

Study the code to understand how to:
1. Encapsulate MCP calls in helper methods
2. Build complex properties for Notion API
3. Handle multi-step relationships
4. Extract data from Notion responses
5. Implement skill orchestration patterns
