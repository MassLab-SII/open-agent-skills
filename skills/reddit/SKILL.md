---
name: reddit-browser-automation
description: This skill provides tools and techniques for Postmill/Reddit-like forum automation. Includes account creation, posting, forum creation and wiki management. Suitable for tasks requiring complex operations on forum platforms.
---

# Reddit/Postmill Browser Automation Skill

This skill is based on Playwright MCP tools, providing automation capabilities for Reddit-like forum platforms (Postmill).

## Core Concepts

In forum automation, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations.

---

## I. Skills

### 1. Sign Up

**Use Cases**:
- Create a new account on the forum after cilcing "Sign up" button
- Register with specific username and password


**Usage**:
```bash
# Usage:
#   python sign_up.py <username> <password> <username_ref> <password_ref> <password_repeat_ref> <submit_ref>
# Example:
python sign_up.py "AIDataAnalyst2025" "SecurePass123!" e35 e43 e44 e54
```

---

### 2. Create Post

**Use Cases**:
- Submit a new post/submission to a forum aftering clicking "Submit" button
- Create text posts with title and body

**Usage**:
```bash
# Usage:
#   python create_post.py <title> <body> <title_ref> <body_ref> <create_btn_ref>
# Example:
python create_post.py "My Post Title" "Post body content here" e58 e63 e82
```
**Note**: The body text can contain multiple lines. Each line should start with a dash (-) for proper formatting.

---

### 3. Create Forum

**Use Cases**:
- Create a new forum/community after clicking "Create forum" button
- Set up forum name, title, description, and sidebar

**Usage**:
```bash
# Usage:
#   python create_forum.py <name> <title> <description> <sidebar> <name_ref> <title_ref> <desc_ref> <sidebar_ref> <create_btn_ref>
# Example:
python create_forum.py "BudgetEuropeTravel" "Budget Travel Europe" "Community for sharing money-saving tips" "Share your best deals!" e51 e56 e61 e69 e83
```

---

### 4. Create Wiki

**Use Cases**:
- Create a wiki page for a forum after clicking "Create new page" button
- Set up wiki URL path, title, and content

**Usage**:
```bash
# Usage:
#   python create_wiki.py <url_path> <title> <body> <url_ref> <title_ref> <body_ref> <save_btn_ref>
# Example:
python create_wiki.py "europe-travel-guide" "Complete Budget Travel Guide" "Wiki content here" e51 e56 e62 e69
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases. These are atomic operations for flexible combination.

**Note**: Code should be written without line breaks.

### How to Run

```bash
# Standard format (browser persists across calls)
python run_browser_ops.py -c "await browser.navigate('http://localhost:9999')"
```

### Navigation Tools

#### `navigate(url: str)`
**Use Cases**:
- Open forum homepage
- Navigate to specific forum or post

**Example**:
```bash
python run_browser_ops.py -c "await browser.navigate('http://localhost:9999')"
python run_browser_ops.py -c "await browser.navigate('http://localhost:9999/f/MachineLearning')"
```

---

#### `navigate_back()`
**Use Cases**:
- Go back to previous page
- Return to forum listing after viewing post

**Example**:
```bash
python run_browser_ops.py -c "await browser.navigate_back()"
```

---

### Interaction Tools

#### `click(ref: str, element: Optional[str] = None)`
**Use Cases**:
- Click navigation links (Forums, Submit, Wiki, etc.)
- Click forum links and post titles
- Click buttons (Sign up, Create, Save, Upvote, etc.)
- Click pagination links (More, Page 2, etc.)

**Example**:
```bash
# Click Forums link
python run_browser_ops.py -c "await browser.click(ref='e22', element='Forums link')"

# Click a post title
python run_browser_ops.py -c "await browser.click(ref='e77', element='Post title link')"

# Click Upvote button
python run_browser_ops.py -c "await browser.click(ref='e94', element='Upvote button')"
```

---

#### `type_text(ref: str, text: str, element: Optional[str] = None)`
**Use Cases**:
- Fill form fields (username, password, title, body)
- Enter search queries
- Fill wiki content

**Example**:
```bash
# Enter username
python run_browser_ops.py -c "await browser.type_text(ref='e35', text='MyUsername', element='Username field')"

# Enter post body
python run_browser_ops.py -c "await browser.type_text(ref='e63', text='Post content here', element='Body textbox')"
```

---

#### `select_option(ref: str, element_desc: str, value: str)`
**Use Cases**:
- Select timezone in user settings
- Select sorting options
- Select dropdown values

**Example**:
```bash
# Select timezone
python run_browser_ops.py -c "await browser.select_option(ref='e56', element_desc='Time zone combobox', value='Europe / Amsterdam')"
```

---

#### `press_key(key: str)`
**Use Cases**:
- Submit search queries (press Enter)
- Submit forms

**Example**:
```bash
python run_browser_ops.py -c "await browser.press_key('Enter')"
```

---

### Page State Tools

#### `snapshot()`
**Use Cases**:
- When unsure about current page state
- Need to find ref references for elements
- Verify if operation was successful
- Count posts or comments on a page

**Example**:
```bash
python run_browser_ops.py -c "await browser.snapshot()"
```

**Best Practices**:
- Use snapshot after navigation to find element refs
- Use snapshot to count items on a page
- Use snapshot to verify data before submitting

---

## III. Common Navigation Patterns

### Forum Navigation
```bash
# Navigate to homepage
python run_browser_ops.py -c "await browser.navigate('http://localhost:9999')"
```

### Sorting and Pagination
```bash
# Click Sort by dropdown
python run_browser_ops.py -c "await browser.click(ref='e54', element='Sort by: Hot dropdown')"
```

---

## IV. Best Practices

### Use snapshot() Liberally

Use `snapshot()` in the following situations:
- After navigating to a new page
- Before performing actions that require element refs
- When counting posts or analyzing content
- To verify successful completion of actions

## Usage Principles

1. **Navigate first**: Start by navigating to `http://localhost:9999`
2. **Use snapshot() liberally**: Forum pages have dynamic refs, verify state often
3. **Find refs**: Always find current refs before using skills
