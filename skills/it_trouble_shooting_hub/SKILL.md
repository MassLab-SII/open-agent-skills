---
name: it-security-audit
description: Create comprehensive security audit tickets based on expired IT inventory items and security FAQ entries. Parameterized skill that can work with any hub/database structure. Automatically queries databases, analyzes expiration data, and generates actionable security recommendations.
---

# IT Security Audit Skill

This skill creates comprehensive security audit tickets combining data from multiple Notion databases to generate a consolidated security review. Fully parameterized for flexibility and reusability.

## Capabilities

1. **Database Querying**: Search and filter inventory and FAQ databases
2. **Data Aggregation**: Combine information from multiple sources
3. **Intelligent Filtering**: Find expired items based on cutoff dates
4. **Report Generation**: Create organized audit tickets with recommendations
5. **Parameterized Execution**: All critical parameters can be passed dynamically without code changes

## 1. Create Security Audit Ticket

Create a comprehensive security audit ticket combining expired inventory items with security best practices.

**Use when**: You need to generate a security audit report based on expired assets in any Notion workspace.

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

## Implementation Details

### Workflow Steps

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

## Reusability & Extensibility

### Adapting to Different Tasks

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

## Architecture

### Class Hierarchy

```
NotionTools (utils.py)
  └─ Provides base Notion API operations
     ├── search_page()
     ├── find_database_by_name()
     ├── query_database()
     ├── create_page_in_database()
     └── add_bullet_list()

SecurityAuditTicketCreator (create_security_audit.py)
  └─ Implements specific business logic
     ├── create_ticket()
     ├── _find_expired_items()
     ├── _find_security_faqs()
     ├── _create_ticket_page()
     └── _generate_bullet_items()
```

### API Adaptation Layer

The skill includes automatic handling of Notion API version differences:

- Converts `data_source` IDs to actual `database_id` for querying
- Supports both `child_database` blocks and `data_source` type databases
- Provides `databases.query()` compatibility for newer notion-client versions

## Error Handling

The skill gracefully handles common errors:

- **Database not found**: Searches by name, provides clear error message
- **Page creation failure**: Checks for parent database accessibility
- **Property validation**: Ensures all required properties are correctly formatted
- **API rate limits**: Returns error with suggestion to retry

## Future Enhancements

Potential improvements:

1. **Batch operations**: Create multiple tickets in one run
2. **Custom recommendations**: Load recommendations from a config file
3. **Email notifications**: Send summary emails after ticket creation
4. **Historical tracking**: Archive old tickets before creating new ones
5. **Multi-database support**: Query from multiple inventory sources

Create new ticket page with specified properties.

### `add_recommendations(page_id: str, items: List[Dict], recommendations: Dict) -> bool`
Add bullet list with recommendations to ticket.

## Notion Databases Used

The skill interacts with three core databases:

1. **IT Inventory** - Stores IT assets with expiration dates and tags
2. **IT FAQs** - Contains security-related FAQ entries
3. **IT Requests** - Stores task tickets and audit reports

## Error Handling

The skill gracefully handles:
- Missing databases - Reports specific database not found
- No expired items - Returns error indicating no items to audit
- Database query failures - Logs error and continues
- Missing FAQs database - Treats as optional, continues with defaults

## Notes

- All parameters (dates, titles, priorities) are configured dynamically by the evaluation system
- The skill respects the MCPMark Eval Hub isolation model
- Recommendations are always generated based on item characteristics
- All API key management is handled automatically by the evaluation system
