---
name: it-trouble-shooting-hub-skills
description: Comprehensive skills for IT Trouble Shooting Hub workspace management. Includes asset retirement migration for managing expired inventory and security audit ticket creation. Automatically discovers databases, queries assets, and generates audit trails with actionable recommendations.
---

# IT Trouble Shooting Hub Skills

## 1. Asset Retirement Migration Skill

**Name**: asset-retirement-migration

**Description**: Automatically migrate expired or returned IT assets from inventory to a dedicated retirement queue. Creates new database, migrates items with properties, archives originals, and generates audit logs.

### Purpose

Streamline IT asset lifecycle management by automatically identifying assets that need to be retired and moving them to a specialized tracking database.

### Usage

```bash
# Set API key
export EVAL_NOTION_API_KEY="ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Run migration
python3 asset_retirement_migration.py
```

### What It Does

1. Finds IT Trouble Shooting Hub page (via API-post-search)
2. Locates IT Inventory database (via API-post-search)
3. Queries for Status="Expired" OR Status="To be returned" (via API-post-database-query)
4. Creates IT Asset Retirement Queue database (via API-create-a-database)
5. Migrates items to retirement queue (via API-post-page + API-patch-page)
6. Archives original items (via API-patch-page)
7. Updates database description (via API-update-a-database)
8. Creates Retirement Migration Log with callout (via API-post-page + API-patch-block-children)

### Expected Output

```
Step 1: Finding IT Trouble Shooting Hub page...
  ✅ Found hub page: 2d25d1cf-e7c4-80cd-8fa6-c711a47ece78

Step 2: Locating IT Inventory database...
  ✅ Found inventory database: 2d25d1cf-e7c4-815b-ab8d-cfe057a347f3

Step 3: Querying for expired/returned assets...
  ✅ Found 2 items to migrate

Step 4: Creating IT Asset Retirement Queue database...
  ✅ Created database: 2d25d1cf-e7c4-812c-b8a3-f098d6d7295c

Step 5: Migrating items to retirement queue...
  ✅ Migrated 2 items

Step 6: Updating database description...
  ✅ Updated description

Step 7: Creating Retirement Migration Log page...
  ✅ Created migration log

============================================================
MIGRATION SUMMARY
============================================================
✅ SUCCESS: Migrated 2 assets
📊 Database ID: 2d25d1cf-e7c4-812c-b8a3-f098d6d7295c
```

### Prerequisites

- IT Trouble Shooting Hub page exists
- IT Inventory database with Serial, Status, Vendor, Tags, Expiration date fields
- Items with Status="Expired" or Status="To be returned"

### Database Created

**IT Asset Retirement Queue** with properties:
- Serial (Title)
- Status (Select)
- Vendor (Select)
- Tags (Multi-select)
- Expiration date (Date)
- Retirement Reason (Select): Expired License, Hardware Obsolete, Security Risk, User Offboarding

---

## 2. IT Security Audit Skill

**Name**: it-security-audit

**Description**: Create comprehensive security audit tickets based on expired IT inventory items and security FAQ entries. Parameterized skill that can work with any hub/database structure. Automatically queries databases, analyzes expiration data, and generates actionable security recommendations.

### Purpose

Create comprehensive security audit tickets combining data from multiple Notion databases to generate a consolidated security review. Fully parameterized for flexibility and reusability.

### Capabilities

- **Database Querying**: Search and filter inventory and FAQ databases
- **Data Aggregation**: Combine information from multiple sources
- **Intelligent Filtering**: Find expired items based on cutoff dates
- **Report Generation**: Create organized audit tickets with recommendations
- **Parameterized Execution**: All critical parameters can be passed dynamically without code changes

### Basic Usage

```bash
# Use default parameters (for IT Trouble Shooting Hub)
python create_security_audit.py audit
```

### Customized Usage

```bash
# Create with custom parameters
python create_security_audit.py audit \
  --hub-page "IT Trouble Shooting Hub" \
  --inventory-db "IT Inventory" \
  --faqs-db "IT FAQs" \
  --requests-db "IT Requests" \
  --title "Quarterly Security Audit - Expired Assets Review" \
  --priority "High" \
  --due-date "2023-06-22" \
  --expiration-cutoff "2023-07-15"
```

### Use Different Hub or Database Names

```bash
# For a different hub with different database names
python create_security_audit.py audit \
  --hub-page "Asset Management Hub" \
  --inventory-db "Asset Inventory" \
  --requests-db "Maintenance Requests" \
  --title "Asset Maintenance Review" \
  --priority "Medium" \
  --due-date "2023-08-15" \
  --expiration-cutoff "2023-09-01"
```

### Available Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--hub-page` | IT Trouble Shooting Hub | Name of the hub page containing databases |
| `--inventory-db` | IT Inventory | Name of the inventory/source database to query |
| `--faqs-db` | IT FAQs | Name of the FAQ database for recommendations |
| `--requests-db` | IT Requests | Name of the database where tickets are created |
| `--title` | Quarterly Security Audit - Expired Assets Review | Title for the created ticket |
| `--priority` | High | Priority level (e.g., High, Medium, Low) |
| `--due-date` | 2023-06-22 | Due date in YYYY-MM-DD format |
| `--expiration-cutoff` | 2023-07-15 | Date cutoff in YYYY-MM-DD format for finding expired items |

### What It Does

1. Searches for hub page by name
2. Finds inventory and FAQ databases
3. Queries for expired items (Expiration date < cutoff)
4. Gathers security FAQ entries for recommendations
5. Creates audit ticket in requests database
6. Generates recommendations: `<Serial> - <Tag> - <Recommendation>`
7. Returns success or error status

### Implementation Details

**Workflow Steps**:
1. **Search Page** - Locates the specified hub page
2. **Find Databases** - Discovers databases by name
3. **Query Inventory** - Finds items with expiration dates before cutoff
4. **Query FAQs** - Gathers FAQ entries for recommendations
5. **Create Ticket** - Creates a new page in requests database with custom properties
6. **Add Recommendations** - Creates bullet list: `<Serial> - <Tag> - <Recommendation>`
7. **Verify** - Confirms all properties are correctly set

### Data Processing

**Expired Items Query**:
- Filters inventory database by Expiration date < cutoff
- Extracts: Serial (title), Tag (from multi_select), Expiration date
- Returns all items before cutoff date

**Security FAQs Query**:
- Filters FAQ database for security-related entries
- Uses FAQ titles as reference for generating recommendations
- Informs security audit recommendations

**Bullet List Format**:
```
<Serial> - <Tag> - <Recommendation>
```

Example:
- `ABC123 - Laptop - Immediately disconnect from network and perform full security audit`
- `XYZ789 - License - Review license expiration and disconnect from network to prevent security incidents`

### Recommendations Logic

Recommendations are generated based on item tag and security best practices:

- **Computer Accessory**: Contact IT support for disposal and security assessment
- **License**: Review expiration and disconnect from network
- **Laptop**: Disconnect and perform full security audit
- **Other**: General IT support referral

### Reusability & Extensibility

This skill is designed to be **fully reusable** for similar tasks with only parameter changes:

#### Example 1: Monthly Review
```bash
python create_security_audit.py audit \
  --title "Monthly Asset Review - June 2023" \
  --priority "Medium" \
  --due-date "2023-06-30" \
  --expiration-cutoff "2023-06-30"
```

#### Example 2: Different Hub
```bash
python create_security_audit.py audit \
  --hub-page "Asset Management Hub" \
  --inventory-db "Asset Inventory" \
  --requests-db "Asset Requests"
```

#### Example 3: Different Databases
```bash
python create_security_audit.py audit \
  --inventory-db "Software Licenses" \
  --faqs-db "Software FAQs" \
  --title "Software License Audit"
```

### When Parameter Changes Are Not Enough

If you need fundamentally different logic, you would need to:
1. Create a new skill class (e.g., `SoftwareLicenseAudit`)
2. Reuse the `NotionTools` base class for common operations
3. Override specific methods like `_generate_bullet_items()`

---

## Shared Utilities (utils.py)

Both skills use these shared utility methods:

**Search & Query**:
- `search(query, filter_obj=None)` - Find pages/databases
- `query_database(database_id, filter_data=None)` - Query with filters
- `get_block_children(block_id)` - Get child blocks

**Create & Update**:
- `create_database(parent_id, title, properties)` - Create database
- `create_page(parent_id, title, parent_type)` - Create page
- `create_page_with_properties(parent_id, parent_type, properties)` - Create with properties
- `update_page(page_id, properties)` - Update page
- `update_database_description(database_id, description)` - Update DB description
- `archive_page(page_id)` - Archive page

**Block Operations**:
- `patch_block_children(block_id, children)` - Add/update blocks
- `create_callout(text, emoji)` - Create callout block

---

## Key Features

✅ **Dynamic ID Discovery**: No hardcoded IDs - discovers all IDs via API calls  
✅ **Async/Await**: Efficient async MCP operations  
✅ **Error Handling**: Graceful error messages and recovery  
✅ **Parameterized**: Easy customization for different databases/hubs  
✅ **Audit Trails**: Original items preserved/archived, never deleted  
✅ **Scalable**: Handles 10-100+ items efficiently  

---

## Troubleshooting

**Issue: "Could not find IT Trouble Shooting Hub"**
- Verify page exists and API key has access
- Check exact page name matches

**Issue: "Could not find IT Inventory database"**
- Verify database exists in hub
- Check exact database name

**Issue: "No expired items found"**
- Verify items exist with matching Status or Expiration date
- Check property names are correct

**Issue: API rate limit**
- Retry after waiting (Notion allows 3 requests/second)
