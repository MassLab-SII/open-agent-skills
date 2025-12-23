#!/usr/bin/env python3
"""
IT Asset Retirement Migration Skill
Migrates expired/returned assets from IT Inventory to a new retirement queue database
Pure MCP implementation - NO hardcoded IDs, all discovered via API-post-search
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from utils import NotionMCPTools


class AssetRetirementMigration:
    """
    Orchestrates the complete IT asset retirement migration using pure MCP calls.
    All IDs are dynamically discovered via API-post-search, never hardcoded.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.mcp = None
        self.hub_page_id = None
        self.inventory_db_id = None
        self.retirement_queue_db_id = None
        self.migrated_count = 0
        self.migration_date = "2025-03-24"
    
    async def execute(self) -> Dict[str, Any]:
        """Execute the complete asset retirement migration"""
        try:
            async with NotionMCPTools(self.api_key) as mcp:
                self.mcp = mcp
                
                print("Step 1: Finding IT Trouble Shooting Hub page (via API-post-search)...")
                await self._find_hub_page()
                if not self.hub_page_id:
                    raise Exception("Could not find IT Trouble Shooting Hub")
                print(f"  ✅ Found hub page: {self.hub_page_id}")
                
                print("\nStep 2: Locating IT Inventory database (via API-post-search)...")
                await self._find_inventory_database()
                if not self.inventory_db_id:
                    raise Exception("Could not find IT Inventory database")
                print(f"  ✅ Found inventory database: {self.inventory_db_id}")
                
                print("\nStep 3: Querying for expired/returned assets (via API-post-database-query)...")
                items = await self._query_expired_items()
                if not items:
                    print("  ℹ️ No expired or to-be-returned items found")
                    return {"success": True, "migrated_count": 0}
                print(f"  ✅ Found {len(items)} items to migrate")
                
                print("\nStep 4: Creating IT Asset Retirement Queue database (via API-create-a-database)...")
                await self._create_retirement_database()
                if not self.retirement_queue_db_id:
                    raise Exception("Failed to create retirement queue database")
                print(f"  ✅ Created database: {self.retirement_queue_db_id}")
                
                print("\nStep 5: Migrating items to retirement queue...")
                for item in items:
                    await self._migrate_item(item)
                print(f"  ✅ Migrated {self.migrated_count} items")
                
                print("\nStep 6: Updating database description (via API-update-a-database)...")
                await self._update_database_description()
                print("  ✅ Updated description")
                
                print("\nStep 7: Creating Retirement Migration Log page (via API-post-page + API-patch-block-children)...")
                await self._create_migration_log()
                print("  ✅ Created migration log")
                
                return {
                    "success": True,
                    "migrated_count": self.migrated_count,
                    "database_id": self.retirement_queue_db_id
                }
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _find_hub_page(self):
        """Find IT Trouble Shooting Hub via API-post-search"""
        result_text = await self.mcp.search("IT Trouble Shooting Hub", 
                                             filter_obj={"property": "object", "value": "page"})
        if not result_text:
            return
        
        result = json.loads(result_text)
        results = result.get("results", [])
        for item in results:
            if item.get("object") == "page":
                self.hub_page_id = item.get("id")
                break
    
    async def _find_inventory_database(self):
        """Find IT Inventory database via API-post-search"""
        result_text = await self.mcp.search("IT Inventory",
                                             filter_obj={"property": "object", "value": "database"})
        if not result_text:
            return
        
        result = json.loads(result_text)
        results = result.get("results", [])
        # Find IT Inventory, not IT Asset Retirement Queue
        for item in results:
            if item.get("object") == "database":
                title_data = item.get("title", [])
                title_text = "".join([t.get("plain_text", "") for t in title_data]).strip()
                if title_text == "IT Inventory":
                    self.inventory_db_id = item.get("id")
                    break
    
    async def _query_expired_items(self) -> List[Dict[str, Any]]:
        """Query IT Inventory for Expired or To be returned items via API-post-database-query"""
        filter_obj = {
            "or": [
                {"property": "Status", "select": {"equals": "Expired"}},
                {"property": "Status", "select": {"equals": "To be returned"}}
            ]
        }
        
        result_text = await self.mcp.query_database(self.inventory_db_id, filter_obj)
        if not result_text:
            return []
        
        result = json.loads(result_text)
        pages = result.get("results", [])
        
        items = []
        for page in pages:
            props = page.get("properties", {})
            item = {
                "page_id": page.get("id"),
                "serial": self._get_property_value(props, "Serial"),
                "status": self._get_property_value(props, "Status"),
                "vendor": self._get_property_value(props, "Vendor"),
                "tags": self._get_property_values(props, "Tags"),
                "expiration_date": self._get_date_property(props, "Expiration date")
            }
            items.append(item)
        
        return items
    
    async def _create_retirement_database(self):
        """Create IT Asset Retirement Queue database via API-create-a-database"""
        properties = {
            "Serial": {"title": {}},
            "Tags": {"multi_select": {"options": []}},
            "Status": {"select": {"options": []}},
            "Vendor": {"select": {"options": []}},
            "Expiration date": {"date": {}},
            "Retirement Reason": {
                "select": {
                    "options": [
                        {"name": "Expired License", "color": "red"},
                        {"name": "Hardware Obsolete", "color": "orange"},
                        {"name": "Security Risk", "color": "yellow"},
                        {"name": "User Offboarding", "color": "blue"}
                    ]
                }
            }
        }
        
        result_text = await self.mcp.create_database(
            self.hub_page_id,
            "IT Asset Retirement Queue",
            properties
        )
        
        if result_text:
            result = json.loads(result_text)
            self.retirement_queue_db_id = result.get("id")
    
    async def _migrate_item(self, item: Dict[str, Any]):
        """Migrate a single item via API-post-page + API-patch-page"""
        try:
            retirement_reason = self._determine_retirement_reason(item["status"])
            
            # Step 1: Create page with just the title via API-post-page
            title_properties = {
                "title": [{"text": {"content": item["serial"]}}]
            }
            
            result_text = await self.mcp.create_page_with_properties(
                self.retirement_queue_db_id,
                "database_id",
                title_properties
            )
            
            if not result_text:
                print(f"  ⚠️ Failed to create page for {item['serial']}")
                return
            
            result = json.loads(result_text)
            new_page_id = result.get("id")
            
            if not new_page_id:
                print(f"  ⚠️ Could not get ID for new page {item['serial']}")
                return
            
            # Step 2: Update page with other properties via API-patch-page
            properties = {
                "Tags": {"multi_select": [{"name": tag} for tag in item["tags"]]},
                "Status": {"select": {"name": item["status"]}},
                "Vendor": {"select": {"name": item["vendor"]}},
                "Retirement Reason": {"select": {"name": retirement_reason}}
            }
            
            if item["expiration_date"]:
                properties["Expiration date"] = {"date": {"start": item["expiration_date"]}}
            
            await self.mcp.update_page(new_page_id, properties)
            
            # Step 3: Archive the original page via API-patch-page
            await self.mcp.archive_page(item["page_id"])
            self.migrated_count += 1
        except Exception as e:
            print(f"  ⚠️ Error migrating {item.get('serial', 'unknown')}: {e}")
    
    async def _update_database_description(self):
        """Update retirement queue database description via API-update-a-database"""
        await self.mcp.update_database_description(
            self.retirement_queue_db_id,
            "AUTO-GENERATED MIGRATION COMPLETED"
        )
    
    async def _create_migration_log(self):
        """Create migration log page via API-post-page + API-patch-block-children"""
        # Step 1: Create the log page via API-post-page
        result_text = await self.mcp.create_page(
            self.hub_page_id,
            "Retirement Migration Log",
            "page_id"  # Important: use page_id not database_id
        )
        
        if result_text:
            result = json.loads(result_text)
            log_page_id = result.get("id")
            
            # Step 2: Add callout block via API-patch-block-children
            log_message = f"Successfully migrated {self.migrated_count} assets to the retirement queue on {self.migration_date}."
            children = [self.mcp.create_callout(log_message, "📝")]
            
            await self.mcp.patch_block_children(log_page_id, children)
    
    @staticmethod
    def _get_property_value(properties: Dict, prop_name: str) -> str:
        """Extract single value from property"""
        if prop_name not in properties:
            return ""
        
        prop = properties[prop_name]
        prop_type = prop.get("type", "")
        
        if prop_type == "title":
            texts = prop.get("title", [])
        elif prop_type == "rich_text":
            texts = prop.get("rich_text", [])
        elif prop_type == "select":
            select = prop.get("select", {})
            return select.get("name", "") if select else ""
        else:
            return ""
        
        if texts and len(texts) > 0:
            return texts[0].get("text", {}).get("content", "")
        return ""
    
    @staticmethod
    def _get_property_values(properties: Dict, prop_name: str) -> List[str]:
        """Extract multiple values from property"""
        if prop_name not in properties:
            return []
        
        prop = properties[prop_name]
        prop_type = prop.get("type", "")
        
        if prop_type == "multi_select":
            items = prop.get("multi_select", [])
            return [item.get("name", "") for item in items]
        
        return []
    
    @staticmethod
    def _get_date_property(properties: Dict, prop_name: str) -> str:
        """Extract date value from property"""
        if prop_name not in properties:
            return ""
        
        prop = properties[prop_name]
        if prop.get("type") == "date":
            date_obj = prop.get("date", {})
            return date_obj.get("start", "") if date_obj else ""
        
        return ""
    
    @staticmethod
    def _determine_retirement_reason(status: str) -> str:
        """Determine retirement reason based on status"""
        if status == "Expired":
            return "Expired License"
        elif status == "To be returned":
            return "User Offboarding"
        return "Expired License"


async def main():
    """Main entry point"""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY environment variable not set")
        return
    
    skill = AssetRetirementMigration(api_key)
    result = await skill.execute()
    
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    if result["success"]:
        print(f"✅ SUCCESS: Migrated {result['migrated_count']} assets")
        print(f"📊 Database ID: {result.get('database_id', 'N/A')}")
    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
