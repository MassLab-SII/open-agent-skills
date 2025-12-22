---
name: shopping-admin-browser-automation
description: This skill provides tools and techniques for Magento Admin panel automation. Includes admin login, customer management, search term analysis, and other common admin scenarios. Suitable for tasks requiring complex operations on e-commerce admin backends.
---

# Shopping Admin Browser Automation Skill

This skill is based on Playwright MCP tools, providing automation capabilities for Magento Admin panel.

## Core Concepts

In admin panel automation, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations.

---

## I. Skills

### 1. Admin Login

**Use Cases**:
- Login to Magento Admin panel at the start of admin tasks
- Authenticate with admin credentials

**Prerequisites**:
- Get ref values for form fields

**Usage**:
```bash
# Usage:
#   python admin_login.py <admin_url> <username> <password> <username_ref> <password_ref> <signin_ref>
# Example:
python admin_login.py http://localhost:7780/admin admin admin1234 e15 e20 e23
```

---

### 2. Create Customer

**Use Cases**:
- Create a new customer after clicking "Add New Customer" button
- Add customers to specific customer groups


**Usage**:
```bash
# Usage:
#   python create_customer.py <first_name> <last_name> <email> <group> <group_ref> <fname_ref> <lname_ref> <email_ref> <save_btn_ref>
# Example:
python create_customer.py "Isabella" "Romano" "isabella.romano@premium.eu" "Premium Europe" e92 e112 e124 e136 e61
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases. These are atomic operations for flexible combination.

**Note**: Code should be written without line breaks.

### How to Run

```bash
# Standard format (browser persists across calls)
python run_browser_ops.py -c "await browser.navigate('http://localhost:7780/admin')"
```

### Navigation Tools

#### `navigate(url: str)`
**Use Cases**:
- Open admin panel URL
- Navigate to specific admin pages

**Example**:
```bash
python run_browser_ops.py -c "await browser.navigate('http://localhost:7780/admin')"
```

---

#### `navigate_back()`
**Use Cases**:
- Go back to previous page
- Return to list page after viewing details

**Example**:
```bash
python run_browser_ops.py -c "await browser.navigate_back()"
```

---

### Interaction Tools

#### `click(ref: str, element: Optional[str] = None)`
**Use Cases** (very broad):
- Click navigation menu items (Customers, Marketing, Reports, etc.)
- Click submenu links (All Customers, Customer Groups, Search Terms, etc.)
- Click action buttons (Add New, Save, Search, Reset Filter)
- Click table rows for details

**Example**:
```bash
# Click Customers menu
python run_browser_ops.py -c "await browser.click(ref='e17', element='Customers menu')"

# Click All Customers link
python run_browser_ops.py -c "await browser.click(ref='e182', element='All Customers link')"
```

---

#### `type_text(ref: str, text: str, element: Optional[str] = None)`
**Use Cases**:
- Enter text in form fields
- Fill filter inputs
- Enter search terms

**Example**:
```bash
# Enter username
python run_browser_ops.py -c "await browser.type_text(ref='e15', text='admin', element='Username textbox')"

# Enter filter value
python run_browser_ops.py -c "await browser.type_text(ref='e109', text='tank', element='Search Query filter input')"
```

---

#### `select_option(ref: str, element_desc: str, value: str)`
**Use Cases**:
- Select dropdown values (Customer Group, Status filter, Store View)
- Select options in forms

**Example**:
```bash
# Select customer group
python run_browser_ops.py -c "await browser.select_option(ref='e92', element_desc='Group select', value='Premium Europe')"

# Select status filter
python run_browser_ops.py -c "await browser.select_option(ref='e124', element_desc='Status filter combobox', value='Subscribed')"
```

---

#### `press_key(key: str)`
**Use Cases**:
- Submit forms (press Enter)
- Close dialogs (press Escape)

**Example**:
```bash
python run_browser_ops.py -c "await browser.press_key('Enter')"
```

---

### Page State Tools

#### `snapshot()`
**Use Cases** (very important):
- When unsure about current page state
- Need to view complete page content to decide next action
- Verify if operation was successful
- Find ref references for specific elements

**Example**:
```bash
python run_browser_ops.py -c "await browser.snapshot()"
```

**Best Practices**:
- Use snapshot before and after critical operations to confirm state
- Use snapshot after navigation to find element refs
- Use snapshot to verify data in tables and grids

---

### Tab Management

#### `list_tabs()`
**Use Cases**:
- View all currently open tabs
- Get tab ID

---

#### `tab_new(url: Optional[str] = None)`
**Use Cases**:
- Open admin section in new tab
- Compare data across multiple pages

**Example**:
```bash
python run_browser_ops.py -c "await browser.tab_new(url='http://localhost:7780/admin/customer/index/')"
```

---

## III. Best Practice Recommendations

### Make Good Use of snapshot()

Use `snapshot()` in the following situations:
- Just entered a new page, unsure about page structure
- After executing an operation, need to verify results
- Need to find ref references for elements
- Unsure about current state of filters or grids

## Usage Principles

1. **Start with admin_login.py**: Most admin tasks require authentication first
2. **Use snapshot() liberally**: Admin pages have complex structures, verify state
3. **Use basic tools for dynamic refs**: Element refs may change, use snapshot to find current refs
