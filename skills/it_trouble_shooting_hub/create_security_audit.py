#!/usr/bin/env python3
"""Create Security Audit Ticket - MCP Implementation"""

import asyncio
import json
import os
import re
from utils import NotionMCPTools


def extract_page_id(json_text: str) -> str:
    """Extract page ID from JSON response"""
    if not json_text:
        return None
    try:
        data = json.loads(json_text)
        return data.get("id")
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r'"id":"([^"]+)"', json_text)
    return match.group(1) if match else None


def parse_results(response_text: str) -> list:
    """Parse results from API response"""
    if not response_text:
        return []
    try:
        data = json.loads(response_text)
        return data.get("results", [])
    except (json.JSONDecodeError, TypeError):
        return []


def get_page_title(page: dict) -> str:
    """Extract page title from page object"""
    try:
        properties = page.get("properties", {})
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0].get("text", {}).get("content", "")
    except:
        pass
    return ""


def get_property_value(page: dict, property_name: str) -> str:
    """Extract property value from page object"""
    try:
        properties = page.get("properties", {})
        prop_data = properties.get(property_name, {})
        
        if prop_data.get("type") == "title":
            title_array = prop_data.get("title", [])
            if title_array:
                return title_array[0].get("text", {}).get("content", "")
        
        elif prop_data.get("type") == "multi_select":
            multi_select = prop_data.get("multi_select", [])
            return [item.get("name") for item in multi_select]
        
        elif prop_data.get("type") == "rich_text":
            rich_text = prop_data.get("rich_text", [])
            if rich_text:
                return rich_text[0].get("text", {}).get("content", "")
    except:
        pass
    return None


async def find_page_by_title(mcp: NotionMCPTools, title: str) -> str:
    """Find a page by its title"""
    search_result = await mcp.search(title)
    if not search_result:
        return None
    
    try:
        data = json.loads(search_result)
        for item in data.get("results", []):
            if item.get("object") == "page":
                page_title = get_page_title(item)
                if title.lower() in page_title.lower():
                    return item["id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return None


async def find_database_by_name(mcp: NotionMCPTools, db_name: str) -> str:
    """Find a database by name"""
    search_result = await mcp.search(db_name)
    if not search_result:
        return None
    
    try:
        data = json.loads(search_result)
        for item in data.get("results", []):
            if item.get("object") == "database":
                if "title" in item:
                    titles = item.get("title", [])
                    if titles and db_name.lower() in titles[0].get("text", {}).get("content", "").lower():
                        return item["id"]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return None


async def create_security_audit(mcp: NotionMCPTools, main_page_id: str = None) -> bool:
    """Create the security audit ticket"""
    
    print("\n" + "="*70)
    print("Creating Security Audit Ticket...")
    print("="*70)
    
    # Step 1: Find databases
    print("\nStep 1: Finding databases...")
    
    inventory_db_id = await find_database_by_name(mcp, "IT Inventory")
    if not inventory_db_id:
        print("❌ Failed to find IT Inventory database")
        return False
    print(f"✓ Found IT Inventory: {inventory_db_id}")
    
    faqs_db_id = await find_database_by_name(mcp, "IT FAQs")
    if faqs_db_id:
        print(f"✓ Found IT FAQs: {faqs_db_id}")
    else:
        print("⚠ IT FAQs database not found (optional)")
    
    requests_db_id = await find_database_by_name(mcp, "IT Requests")
    if not requests_db_id:
        print("❌ Failed to find IT Requests database")
        return False
    print(f"✓ Found IT Requests: {requests_db_id}")
    
    # Step 2: Query for expired items
    print("\nStep 2: Finding expired items (before 2023-07-15)...")
    
    filter_config = {
        "property": "Expiration date",
        "date": {"before": "2023-07-15"}
    }
    
    expired_result = await mcp.query_database(inventory_db_id, filter_config)
    expired_pages = parse_results(expired_result)
    
    if not expired_pages:
        print("❌ No expired items found")
        return False
    
    expired_items = []
    for page in expired_pages:
        serial = get_page_title(page)
        tag_data = page.get("properties", {}).get("Tags", {})
        tags = tag_data.get("multi_select", [])
        tag = tags[0].get("name") if tags else ""
        
        if serial:
            expired_items.append({"serial": serial, "tag": tag})
            print(f"  ✓ {serial} ({tag})")
    
    print(f"✓ Found {len(expired_items)} expired item(s)")
    
    # Step 3: Query for security FAQs
    print("\nStep 3: Finding security FAQs...")
    
    security_faqs = []
    if faqs_db_id:
        faqs_filter = {
            "property": "Category",
            "select": {"equals": "Security & Malware"}
        }
        
        faqs_result = await mcp.query_database(faqs_db_id, faqs_filter)
        faq_pages = parse_results(faqs_result)
        
        for page in faq_pages:
            faq_title = get_page_title(page)
            if faq_title:
                security_faqs.append(faq_title)
        
        print(f"✓ Found {len(security_faqs)} security FAQ(s)")
    
    # Step 4: Create ticket page
    print("\nStep 4: Creating security audit ticket in IT Requests...")
    
    ticket_title = "Quarterly Security Audit - Expired Assets Review"
    
    # Use API-post-page directly for database creation with properties
    ticket_result = await mcp.session.call_tool("API-post-page", {
        "parent": {"database_id": requests_db_id},
        "properties": {
            "Task name": {
                "title": [{"type": "text", "text": {"content": ticket_title}}]
            },
            "Priority": {
                "select": {"name": "High"}
            },
            "Due": {
                "date": {"start": "2023-06-22"}
            }
        }
    })
    
    ticket_page_id = extract_page_id(mcp._extract_text(ticket_result))
    
    if not ticket_page_id:
        print("❌ Failed to create ticket page")
        return False
    
    print(f"✓ Created ticket page: {ticket_page_id}")
    print(f"  - Title: {ticket_title}")
    print(f"  - Priority: High")
    print(f"  - Due Date: 2023-06-22")
    
    # Step 5: Add bullet list with recommendations
    print("\nStep 5: Adding bullet list with recommendations...")
    
    # Build recommendations map based on item tags
    recommendations = {
        "Computer Accessory": "Contact IT support immediately for proper disposal and security assessment",
        "License": "Review license expiration and disconnect from network to prevent security incidents",
        "Laptop": "Immediately disconnect from network and perform full security audit"
    }
    
    bullet_blocks = []
    for item in expired_items:
        serial = item.get("serial", "Unknown")
        tag = item.get("tag", "Unknown")
        recommendation = recommendations.get(tag, "Report to IT support for security incident review")
        
        bullet_text = f"{serial} - {tag} - {recommendation}"
        
        bullet_block = {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": bullet_text}}]
            }
        }
        bullet_blocks.append(bullet_block)
        print(f"  • {bullet_text}")
    
    # Add all bullet blocks
    await mcp.patch_block_children(ticket_page_id, bullet_blocks)
    print(f"✓ Added {len(bullet_blocks)} bullet item(s)")
    
    print("\n" + "="*70)
    print("✅ Security audit ticket created successfully!")
    print("="*70)
    
    return True


async def main():
    """Main entry point"""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY not set")
        return
    
    async with NotionMCPTools(api_key) as mcp:
        success = await create_security_audit(mcp)
        return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
