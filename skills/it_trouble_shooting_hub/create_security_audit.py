#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Security Audit Ticket
=============================

This script creates a comprehensive security audit ticket based on:
1. Expired items in a source database
2. Security FAQs from a FAQ database
3. Creates a new page in a requests database with detailed recommendations

The API key is automatically loaded from the .mcp_env file by the evaluation system.

Usage:
    python create_security_audit.py audit \\
        --hub-page "IT Trouble Shooting Hub" \\
        --inventory-db "IT Inventory" \\
        --faqs-db "IT FAQs" \\
        --requests-db "IT Requests" \\
        --title "Quarterly Security Audit - Expired Assets Review" \\
        --priority "High" \\
        --due-date "2023-06-22" \\
        --expiration-cutoff "2023-07-15"
"""

import json
import sys
import os
import argparse
from typing import Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv
from utils import NotionTools

# Load environment variables from .mcp_env file
env_paths = [
    Path(__file__).parent.parent.parent / ".mcp_env",
    Path.cwd() / ".mcp_env",
    Path(".") / ".mcp_env",
]

for env_file in env_paths:
    if env_file.exists():
        load_dotenv(dotenv_path=str(env_file), override=False)
        break


class SecurityAuditTicketCreator:
    """Create a comprehensive security audit ticket with configurable parameters"""

    def __init__(
        self,
        api_key: str,
        hub_page_name: str = "IT Trouble Shooting Hub",
        inventory_db_name: str = "IT Inventory",
        faqs_db_name: str = "IT FAQs",
        requests_db_name: str = "IT Requests",
        ticket_title: str = "Quarterly Security Audit - Expired Assets Review",
        ticket_priority: str = "High",
        ticket_due_date: str = "2023-06-22",
        expiration_cutoff: str = "2023-07-15",
    ):
        """
        Initialize the ticket creator
        
        Args:
            api_key: Notion API key
            hub_page_name: Name of the hub page containing databases
            inventory_db_name: Name of the inventory/source database
            faqs_db_name: Name of the FAQ database
            requests_db_name: Name of the requests database
            ticket_title: Title for the created ticket
            ticket_priority: Priority level (e.g., "High", "Medium", "Low")
            ticket_due_date: Due date in YYYY-MM-DD format
            expiration_cutoff: Date cutoff in YYYY-MM-DD format for finding expired items
        """
        self.api_key = api_key
        self.notion = NotionTools(api_key)
        
        # Configuration
        self.hub_page_name = hub_page_name
        self.inventory_db_name = inventory_db_name
        self.faqs_db_name = faqs_db_name
        self.requests_db_name = requests_db_name
        
        self.ticket_title = ticket_title
        self.ticket_priority = ticket_priority
        self.ticket_due_date = ticket_due_date
        self.expiration_cutoff = expiration_cutoff

    def create_ticket(self) -> Dict:
        """
        Main workflow to create security audit ticket
        
        Returns:
            Dictionary with success status and details
        """
        try:
            # Step 1: Find IT Trouble Shooting Hub page
            print("\n" + "="*70)
            print("Step 1: Finding IT Trouble Shooting Hub page")
            print("="*70)
            hub_page = self.notion.search_page(self.hub_page_name)
            
            if not hub_page:
                return {
                    "success": False,
                    "error": f"Page '{self.hub_page_name}' not found",
                    "output": ""
                }
            
            hub_page_id = hub_page.get("id")
            print(f"✓ Found hub page (ID: {hub_page_id})")
            
            # Step 2: Find databases in the hub page
            print("\n" + "="*70)
            print("Step 2: Finding databases in IT Trouble Shooting Hub")
            print("="*70)
            
            # Find databases by name (they appear as data_source type in newer Notion API)
            inventory_db_id = self.notion.find_database_by_name(self.inventory_db_name)
            if not inventory_db_id:
                return {
                    "success": False,
                    "error": f"Database '{self.inventory_db_name}' not found",
                    "output": ""
                }
            print(f"✓ Found {self.inventory_db_name} (ID: {inventory_db_id})")
            
            faqs_db_id = self.notion.find_database_by_name(self.faqs_db_name)
            if not faqs_db_id:
                print(f"  Note: {self.faqs_db_name} not found (optional)")
                faqs_db_id = None
            else:
                print(f"✓ Found {self.faqs_db_name} (ID: {faqs_db_id})")
            
            requests_db_id = self.notion.find_database_by_name(self.requests_db_name)
            if not requests_db_id:
                return {
                    "success": False,
                    "error": f"Database '{self.requests_db_name}' not found",
                    "output": ""
                }
            print(f"✓ Found {self.requests_db_name} (ID: {requests_db_id})")
            
            # Step 3: Query IT Inventory for expired items
            print("\n" + "="*70)
            print(f"Step 3: Finding expired items (before {self.expiration_cutoff})")
            print("="*70)
            
            expired_items = self._find_expired_items(inventory_db_id)
            print(f"✓ Found {len(expired_items)} expired item(s)")
            
            for item in expired_items:
                serial = item.get("serial", "N/A")
                tag = item.get("tag", "N/A")
                print(f"  - {serial} ({tag})")
            
            if not expired_items:
                return {
                    "success": False,
                    "error": "No expired items found in inventory",
                    "output": ""
                }
            
            # Step 4: Get security FAQs (for context)
            print("\n" + "="*70)
            print("Step 4: Gathering security FAQ references")
            print("="*70)
            
            security_faqs = []
            if faqs_db_id:
                security_faqs = self._find_security_faqs(faqs_db_id)
                print(f"✓ Found {len(security_faqs)} security FAQ(s)")
            
            # Step 5: Create ticket page
            print("\n" + "="*70)
            print("Step 5: Creating security audit ticket")
            print("="*70)
            
            ticket_page = self._create_ticket_page(requests_db_id)
            
            if not ticket_page:
                return {
                    "success": False,
                    "error": "Failed to create ticket page",
                    "output": ""
                }
            
            ticket_page_id = ticket_page.get("id")
            print(f"✓ Created ticket page (ID: {ticket_page_id})")
            print(f"  - Title: {self.ticket_title}")
            print(f"  - Priority: {self.ticket_priority}")
            print(f"  - Due Date: {self.ticket_due_date}")
            
            # Step 6: Add bullet list with expired items and recommendations
            print("\n" + "="*70)
            print("Step 6: Adding expired items and recommendations")
            print("="*70)
            
            bullet_items = self._generate_bullet_items(expired_items)
            
            self.notion.add_bullet_list(ticket_page_id, bullet_items)
            print(f"✓ Added {len(bullet_items)} bullet item(s)")
            
            for item_text in bullet_items:
                print(f"  • {item_text}")
            
            # Step 7: Verify completion
            print("\n" + "="*70)
            print("Step 7: Verifying ticket creation")
            print("="*70)
            
            ticket_props = self.notion.get_page_properties(ticket_page_id)
            priority = ticket_props.get("Priority", {}).get("select", {}).get("name")
            due = ticket_props.get("Due", {}).get("date", {}).get("start")
            
            print(f"✓ Ticket verified:")
            print(f"  - Priority: {priority}")
            print(f"  - Due Date: {due}")
            
            return {
                "success": True,
                "output": f"Successfully created security audit ticket '{self.ticket_title}' with {len(expired_items)} expired item(s)",
                "error": ""
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Error during execution: {str(e)}",
                "output": ""
            }

    def _find_expired_items(self, inventory_db_id: str) -> List[Dict]:
        """
        Find all expired items in IT Inventory database
        
        Args:
            inventory_db_id: Inventory database ID
            
        Returns:
            List of expired item dictionaries
        """
        try:
            # Query for items with expiration date before the cutoff
            filter_config = {
                "property": "Expiration date",
                "date": {"before": self.expiration_cutoff}
            }
            
            results = self.notion.query_database(inventory_db_id, filter_config)
            
            expired_items = []
            for page in results:
                props = page.get("properties", {})
                
                # Extract serial number (from "Serial" property, which is typically title)
                serial = ""
                for prop_name, prop_data in props.items():
                    if prop_data.get("type") == "title":
                        title_content = prop_data.get("title", [])
                        if title_content:
                            serial = self.notion.get_plain_text_from_rich_text(title_content)
                        break
                
                # Extract tag (from first tag in a multi_select property)
                tag = ""
                for prop_name, prop_data in props.items():
                    if prop_data.get("type") == "multi_select":
                        tags = prop_data.get("multi_select", [])
                        if tags:
                            tag = tags[0].get("name", "")
                        break
                
                # Extract expiration date for reference
                expiration_date = props.get("Expiration date", {}).get("date", {}).get("start", "")
                
                if serial:  # Only add if we have a serial
                    expired_items.append({
                        "serial": serial,
                        "tag": tag,
                        "expiration_date": expiration_date,
                        "page_id": page.get("id")
                    })
            
            return expired_items
        except Exception as e:
            print(f"Error finding expired items: {e}")
            return []

    def _find_security_faqs(self, faqs_db_id: str) -> List[Dict]:
        """
        Find security-related FAQ entries
        
        Args:
            faqs_db_id: FAQs database ID
            
        Returns:
            List of security FAQ dictionaries
        """
        try:
            # Query for FAQs with "Security" category
            filter_config = {
                "property": "Category",
                "select": {"equals": "Security & Malware"}
            }
            
            results = self.notion.query_database(faqs_db_id, filter_config)
            
            security_faqs = []
            for page in results:
                props = page.get("properties", {})
                
                # Extract title
                title = ""
                for prop_name, prop_data in props.items():
                    if prop_data.get("type") == "title":
                        title_content = prop_data.get("title", [])
                        if title_content:
                            title = self.notion.get_plain_text_from_rich_text(title_content)
                        break
                
                if title:
                    security_faqs.append({
                        "title": title,
                        "page_id": page.get("id")
                    })
            
            return security_faqs
        except Exception as e:
            print(f"Error finding security FAQs: {e}")
            return []

    def _create_ticket_page(self, requests_db_id: str) -> Optional[Dict]:
        """
        Create a new ticket page in IT Requests database
        
        Args:
            requests_db_id: Requests database ID
            
        Returns:
            Created page object or None
        """
        try:
            # Note: The title property in IT Requests database is called "Task name"
            properties = {
                "Task name": {
                    "title": [{"text": {"content": self.ticket_title}}]
                },
                "Priority": {"select": {"name": self.ticket_priority}},
                "Due": {"date": {"start": self.ticket_due_date}}
            }
            
            page = self.notion.create_page_in_database(
                requests_db_id,
                self.ticket_title,
                properties
            )
            
            return page
        except Exception as e:
            print(f"Error creating ticket page: {e}")
            return None

    def _generate_bullet_items(self, expired_items: List[Dict]) -> List[str]:
        """
        Generate bullet list items with recommendations
        
        Args:
            expired_items: List of expired items
            
        Returns:
            List of formatted bullet item texts
        """
        bullet_items = []
        
        recommendations = {
            "Computer Accessory": "Contact IT support immediately for proper disposal and security assessment",
            "License": "Review license expiration and disconnect from network to prevent security incidents",
            "Laptop": "Immediately disconnect from network and perform full security audit"
        }
        
        for item in expired_items:
            serial = item.get("serial", "Unknown")
            tag = item.get("tag", "Unknown")
            
            # Get recommendation based on tag type
            recommendation = recommendations.get(
                tag,
                "Report to IT support for security incident review"
            )
            
            # Format: <Serial> - <Tag> - <Recommendation>
            bullet_text = f"{serial} - {tag} - {recommendation}"
            bullet_items.append(bullet_text)
        
        return bullet_items


def main():
    """Main entry point with command line argument support"""
    parser = argparse.ArgumentParser(
        description="Create a security audit ticket in Notion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default parameters
  python create_security_audit.py audit
  
  # Customize all parameters
  python create_security_audit.py audit \\
    --hub-page "IT Trouble Shooting Hub" \\
    --inventory-db "IT Inventory" \\
    --faqs-db "IT FAQs" \\
    --requests-db "IT Requests" \\
    --title "Security Audit Report" \\
    --priority "Medium" \\
    --due-date "2023-07-30" \\
    --expiration-cutoff "2023-08-01"
  
  # Use for different hub with different databases
  python create_security_audit.py audit \\
    --hub-page "Asset Management Hub" \\
    --inventory-db "Asset Inventory" \\
    --requests-db "Maintenance Requests"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create 'audit' subcommand
    audit_parser = subparsers.add_parser(
        "audit",
        help="Create a security audit ticket"
    )
    
    audit_parser.add_argument(
        "--hub-page",
        type=str,
        default="IT Trouble Shooting Hub",
        help="Name of the hub page containing databases (default: IT Trouble Shooting Hub)"
    )
    
    audit_parser.add_argument(
        "--inventory-db",
        type=str,
        default="IT Inventory",
        help="Name of the inventory/source database (default: IT Inventory)"
    )
    
    audit_parser.add_argument(
        "--faqs-db",
        type=str,
        default="IT FAQs",
        help="Name of the FAQ database (default: IT FAQs)"
    )
    
    audit_parser.add_argument(
        "--requests-db",
        type=str,
        default="IT Requests",
        help="Name of the requests database (default: IT Requests)"
    )
    
    audit_parser.add_argument(
        "--title",
        type=str,
        default="Quarterly Security Audit - Expired Assets Review",
        help="Title for the created ticket (default: Quarterly Security Audit - Expired Assets Review)"
    )
    
    audit_parser.add_argument(
        "--priority",
        type=str,
        default="High",
        help="Priority level (default: High)"
    )
    
    audit_parser.add_argument(
        "--due-date",
        type=str,
        default="2023-06-22",
        help="Due date in YYYY-MM-DD format (default: 2023-06-22)"
    )
    
    audit_parser.add_argument(
        "--expiration-cutoff",
        type=str,
        default="2023-07-15",
        help="Date cutoff in YYYY-MM-DD format for expired items (default: 2023-07-15)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Get API key from environment
    api_key = os.getenv("NOTION_API_KEY")
    if not api_key:
        api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        api_key = os.getenv("SOURCE_NOTION_API_KEY")
    
    if not api_key:
        print("Error: Notion API key not provided")
        print("Please set NOTION_API_KEY, EVAL_NOTION_API_KEY, or SOURCE_NOTION_API_KEY environment variable")
        sys.exit(1)
    
    # Execute audit command
    if args.command == "audit":
        creator = SecurityAuditTicketCreator(
            api_key=api_key,
            hub_page_name=args.hub_page,
            inventory_db_name=args.inventory_db,
            faqs_db_name=args.faqs_db,
            requests_db_name=args.requests_db,
            ticket_title=args.title,
            ticket_priority=args.priority,
            ticket_due_date=args.due_date,
            expiration_cutoff=args.expiration_cutoff,
        )
        
        result = creator.create_ticket()
        
        print("\n" + "="*70)
        if result["success"]:
            print("✅ Task completed successfully!")
            print(result["output"])
        else:
            print("❌ Task failed!")
            print(result["error"])
        print("="*70)
        
        sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
