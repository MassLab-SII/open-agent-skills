---
name: shopping-browser-automation
description: This skill provides tools and techniques for e-commerce website automation. Includes advanced search, product comparison, cart management, checkout process and other common shopping scenarios. Suitable for tasks requiring complex operations on e-commerce websites.
---

# Shopping Browser Automation Skill

This skill is based on Playwright MCP tools, providing automation capabilities for e-commerce websites.

## Core Concepts

In shopping website automation, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls in `utils.py`, used for atomic operations.

---

## I. Skills

### 1. Simple Search - Type and Submit

**File**: `simple_search.py`

**Use Cases**:
- Need to search for a product using the main search bar
- Want to type a search term and automatically press Enter to submit

**Prerequisites**:
- First use `navigate()` to navigate to the website homepage
- Get the ref value of the search input field


**Usage**:
```bash
# Usage:
#   python simple_search.py <search_term> <search_input_ref>
# Example:
python simple_search.py "gingerbread" e35
```

---

### 2. Advanced Search - By Product Name and Price Range

**File**: `advanced_search_by_name.py`

**Use Cases**:
- Already on the Advanced Search page
- Need to fill in product name and price range for search

**Prerequisites**:
- First use `navigate()` to navigate to the website homepage
- Then use `click()` to click the "Advanced Search" link
- Get the ref values of form fields

**Typical Task Examples**:
- Search for products with name containing "Ginger", price between $50.00 and $100.00
- Search for products with name containing "cookie", price between $20.00 and $40.00

**Usage**:
```bash
# Usage:
#   python advanced_search_by_name.py <product_name> <price_from> <price_to> <name_ref> <price_from_ref> <price_to_ref> <search_btn_ref>
# Example:
python advanced_search_by_name.py "Ginger" 50.00 100.00 e91 e110 e114 e118
```

---

### 3. Advanced Search - By Description and Price Range

**File**: `advanced_search_by_description.py`

**Use Cases**:
- Already on the Advanced Search page
- Need to search keywords in product description (not product name)
- Need to filter by price range

**Prerequisites**:
- First use `navigate()` to navigate to the website homepage
- Then use `click()` to click the "Advanced Search" link
- Get the ref values of form fields

**Typical Task Examples**:
- Search for products with description containing "vitamin", price $0.00-$99.99

**Usage**:
```bash
# Usage:
#   python advanced_search_by_description.py <description> <price_from> <price_to> <desc_ref> <price_from_ref> <price_to_ref> <search_btn_ref>
# Example:
python advanced_search_by_description.py "vitamin" 0.00 99.99 e99 e110 e114 e118
```

---

### 4. Checkout - Fill Shipping Information

**File**: `fill_shipping_info.py`

**Use Cases**:
- Already on the checkout page (after clicking "Proceed to Checkout")
- Need to fill in complete shipping address information

**Typical Task Examples**:
- Fill in customer's name, address, city, state, zip code, phone, etc.

**Prerequisites**:
- First use `click()` to click the "Proceed to Checkout" button
- Use `snapshot()` to get all form field ref values

**Usage**:
```bash
# Usage:
#   python fill_shipping_info.py <email> <first_name> <last_name> <street> <country> <state> <city> <zipcode> <phone> <email_ref> <fname_ref> <lname_ref> <street_ref> <country_ref> <state_ref> <city_ref> <zip_ref> <phone_ref>
# Example:
python fill_shipping_info.py test.buyer@example.com Alice Johnson "456 Oak Avenue" "United States" California "San Francisco" 94102 415-555-0123 e33 e46 e51 e65 e75 e80 e85 e90 e95
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions provided in `utils.py` and their use cases. These are atomic operations for flexible combination.

**Note**: Basic tools need to be used in async context. Can be simplified using `run_browser_ops.py`. Code should be written without line breaks.

### How to Run

```bash
# Standard format (browser persists across calls)
python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')"
```
### Navigation Tools

#### `navigate(url: str)`
**Use Cases**:
- Open website homepage
- Directly access specific product page URL
- Jump to specific URL

**Example**:
```bash
python run_browser_ops.py -c "await browser.navigate('http://localhost:7770')"
```

---

#### `navigate_back()`
**Use Cases**:
- Go back to previous page
- Return to search results page after browsing products

**Example**:
```bash
python run_browser_ops.py -c "await browser.navigate_back()"
```
---

### Interaction Tools

#### `click(ref: str, element: Optional[str] = None)`
**Use Cases** (very broad):
- Click navigation menu (categories, subcategories)
- Click product links
- Click "Add to Compare" button
- Click "Add to Cart" button
- Click pagination links (Page 2, Page 3, etc.)
- Click price filters
- Click sort direction toggle

**Example**:
```bash
python run_browser_ops.py -c "await browser.click(ref='e56', element='Health & Household menu item')"
```
---

#### `type_text(ref: str, text: str, element: Optional[str] = None)`
**Use Cases**:
- Enter keywords in search box
- Fill single form field
- Modify quantity input box

**Example**:
```bash
# Enter in search box
python run_browser_ops.py -c "await browser.type_text(ref='e32', text='gingerbread', element='Search input')"
# Press Enter to submit
python run_browser_ops.py -c "await browser.press_key('Enter')"
```

---

#### `fill_form(fields: List[Dict[str, str]])`
**Use Cases**:
- Fill multiple form fields (e.g., advanced search form)
- Batch update form data
- Update quantity in shopping cart

**Example**:
```bash
# Fill advanced search form
python run_browser_ops.py -c "await browser.fill_form(fields=[{'name': 'Product Name', 'ref': 'e111', 'value': 'cookie'}, {'name': 'Price From', 'ref': 'e134', 'value': '20.00'}, {'name': 'Price To', 'ref': 'e138', 'value': '40.00'}])"

# Update cart quantity
python run_browser_ops.py -c "await browser.fill_form(fields=[{'name': 'Qty', 'ref': 'e141', 'value': '3'}])"
```

---

#### `select_option(ref: str, element_desc: str, value: str)`
**Use Cases**:
- Select sort method (Sort By: Price, Relevance, etc.)
- Select country/state/province dropdown
- Select product options (e.g., Flavor, Size, etc.)

**Example**:
```bash
# Sort by price
python run_browser_ops.py -c "await browser.select_option(ref='e114', element_desc='Sort By dropdown', value='Price')"

# Select product flavor
python run_browser_ops.py -c "await browser.select_option(ref='e128', element_desc='Flavor', value='Peanut Butter')"
```

---

#### `press_key(key: str)`
**Use Cases**:
- Submit search (press Enter key)
- Close dialog (press Escape key)

**Example**:
```bash
# Press Enter after typing in search box
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
- Use snapshot on search results page to view all products
- Use snapshot after page navigation to confirm page loaded completely

---

#### `get_console_messages()`
**Use Cases**:
- Debug JavaScript errors
- View log information during page loading

---

#### `get_network_requests()`
**Use Cases**:
- Debug network request issues
- View API call status

---

### Wait Tools

#### `wait_for_time(seconds: int)`
**Use Cases**:
- Wait for page to load completely
- Wait for animation effects to finish
- Wait for async data loading

**Example**:
```bash
python run_browser_ops.py -c "await browser.wait_for_time(3)"
```
---

### Tab Management

#### `list_tabs()`
**Use Cases**:
- View all currently open tabs
- Get tab ID

---

#### `tab_new(url: Optional[str] = None)`
**Use Cases**:
- Open product detail page in new tab (keep search results page)
- Compare multiple products simultaneously

**Example**:
```bash
python run_browser_ops.py -c "await browser.tab_new(url='http://localhost:7770/product-page.html')"
```

## III. Best Practice Recommendations

### 1. Make Good Use of snapshot()

Use `snapshot()` in the following situations:
- Just entered a new page, unsure about page structure
- After executing an operation, need to verify results
- Need to find ref references for elements
- Unsure about current sort order (descending or ascending) / filter state

---

## Usage Principles

1. **Prefer combined skills for fixed workflows**: e.g., advanced search, add quantity to cart, fill forms
2. **Use basic tools flexibly for changing scenarios**: e.g., click, input, select and other atomic operations
3. **Make good use of `snapshot()` to understand page state**: confirm state before and after critical steps
