#!/usr/bin/env python3
import asyncio
import json
import os
from typing import Optional, Dict, List, Any
from utils import NotionMCPTools


class DeploymentProcessSOP:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.mcp = None
        self.sop_page_id = None
        self.block_map = {}
    
    async def complete_sop(self) -> Dict:
        result = {
            "success": False,
            "message": "",
            "sections_updated": 0,
            "errors": []
        }
        
        try:
            async with NotionMCPTools(self.api_key) as tools:
                self.mcp = tools
                
                print("Step 1: Searching for SOP page...")
                self.sop_page_id = await self._search_and_find_sop_page()
                if not self.sop_page_id:
                    result["errors"].append("SOP page not found")
                    return result
                print(f"  Found SOP page")
                
                print(f"Step 2: Exploring page structure...")
                await self._explore_page_structure()
                print(f"  Discovered {len(self.block_map)} blocks in block_map")
                print(f"  Block keys: {list(self.block_map.keys())}")
                
                updates = 0
                updates += await self._update_section("header")
                updates += await self._update_section("purpose")
                updates += await self._update_section("context")
                updates += await self._update_section("terminologies")
                updates += await self._update_section("tools")
                updates += await self._update_section("roles")
                updates += await self._update_section("procedure")
                
                result["sections_updated"] = updates
                result["success"] = True
                result["message"] = f"Successfully completed SOP"
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"Error: {str(e)}")
        
        return result
    
    async def _search_and_find_sop_page(self) -> Optional[str]:
        try:
            response = await self.mcp.search("Standard Operating Procedure")
            if not response:
                return None
            
            data = json.loads(response)
            for item in data.get("results", []):
                if item.get("object") == "page":
                    title = self._extract_title(item.get("properties", {}))
                    if "Standard" in title or "procedure" in title.lower():
                        return item.get("id")
        except Exception as e:
            print(f"Error searching: {e}")
        
        return None
    
    async def _explore_page_structure(self):
        try:
            root_response = await self.mcp.get_block_children(self.sop_page_id)
            if not root_response:
                return
            
            root_data = json.loads(root_response)
            root_blocks = root_data.get("results", [])
            
            print(f"  Root blocks found: {len(root_blocks)}")
            
            # Two-phase approach:
            # 1. Explore column_list for header blocks
            # 2. Explore root blocks for sections
            
            for block in root_blocks:
                if block.get("type") == "column_list":
                    print(f"  Found column_list with header")
                    await self._explore_column_list(block.get("id"))
                    break
            
            # Now explore root blocks to find section headings
            print(f"  Exploring root blocks for sections...")
            await self._explore_root_blocks(root_blocks)
            
        except Exception as e:
            print(f"Error: {e}")
    
    async def _explore_root_blocks(self, blocks: List):
        """Explore heading_2 sections in root blocks"""
        try:
            for i, block in enumerate(blocks):
                if block.get("type") == "heading_2":
                    text = self._extract_text(block)
                    section = self._normalize_section(text)
                    self.block_map[f"heading_{section}"] = block.get("id")
                    print(f"    Found section: {section}")
                    
                    # Find content after this heading
                    await self._find_section_content_in_root(blocks, i, section)
        except Exception:
            pass
    
    async def _find_section_content_in_root(self, all_blocks: List, heading_index: int, section: str):
        """Find content blocks after a heading_2 in root"""
        try:
            for j in range(heading_index + 1, len(all_blocks)):
                block = all_blocks[j]
                block_type = block.get("type")
                block_id = block.get("id")
                
                # Stop at next heading
                if block_type in ["heading_1", "heading_2"]:
                    break
                
                # Store paragraphs
                if block_type == "paragraph":
                    if f"para_{section}" not in self.block_map:
                        self.block_map[f"para_{section}"] = block_id
                
                # Store toggle
                elif block_type == "toggle":
                    self.block_map[f"toggle_{section}"] = block_id
                    await self._explore_toggle(block_id)
                
                # Store first list item
                elif block_type in ["bulleted_list_item", "numbered_list_item"]:
                    key = f"first_{block_type}_{section}"
                    if key not in self.block_map:
                        self.block_map[key] = block_id
                
                # Store child_page and explore it
                elif block_type == "child_page":
                    title = await self._get_child_page_title(block_id)
                    if title:
                        self.block_map[f"child_{title}"] = block_id
                        # Explore child page to find callouts
                        await self._explore_child_page(block_id, title)
        except Exception:
            pass
    
    async def _explore_column_list(self, column_list_id: str):
        try:
            response = await self.mcp.get_block_children(column_list_id)
            if not response:
                return
            
            data = json.loads(response)
            for column in data.get("results", []):
                if column.get("type") == "column":
                    await self._explore_column(column.get("id"))
        except Exception:
            pass
    
    async def _explore_column(self, column_id: str):
        try:
            response = await self.mcp.get_block_children(column_id)
            if not response:
                return
            
            data = json.loads(response)
            blocks = data.get("results", [])
            
            print(f"  Column {column_id[:12]}: {len(blocks)} blocks")
            
            # Store heading_1 and paragraphs in order for header section
            heading_1_found = False
            for i, block in enumerate(blocks):
                block_type = block.get("type")
                block_id = block.get("id")
                
                if block_type == "heading_1":
                    self.block_map["heading_1"] = block_id
                    heading_1_found = True
                elif heading_1_found and block_type == "paragraph" and "created_date" not in self.block_map:
                    text = self._extract_text(block)
                    if text:
                        self.block_map["created_date"] = block_id
                elif heading_1_found and block_type == "paragraph" and "created_date" in self.block_map and "responsible_dept" not in self.block_map:
                    self.block_map["responsible_dept"] = block_id
                    heading_1_found = False
                elif block_type == "child_page":
                    # Explore child pages in column (like "People team" for header)
                    title = await self._get_child_page_title(block_id)
                    if title:
                        self.block_map[f"child_{title}"] = block_id
                        await self._explore_child_page(block_id, title)
                elif block_type == "heading_2":
                    text = self._extract_text(block)
                    section = self._normalize_section(text)
                    self.block_map[f"heading_{section}"] = block_id
                    print(f"    Found heading: {section}")
                    # Find content blocks after this heading
                    await self._find_section_content(column_id, blocks, i, section)
        except Exception as e:
            print(f"  Error in column: {e}")
    
    async def _find_section_content(self, column_id: str, all_blocks: List, heading_index: int, section: str):
        """Find content blocks after a heading"""
        try:
            for j in range(heading_index + 1, len(all_blocks)):
                block = all_blocks[j]
                block_type = block.get("type")
                block_id = block.get("id")
                
                # Stop at next heading
                if block_type in ["heading_1", "heading_2"]:
                    break
                
                # Store paragraphs
                if block_type == "paragraph":
                    if f"para_{section}" not in self.block_map:
                        self.block_map[f"para_{section}"] = block_id
                
                # Store toggle (for Context callouts)
                elif block_type == "toggle":
                    self.block_map[f"toggle_{section}"] = block_id
                    await self._explore_toggle(block_id)
                
                # Store first list item
                elif block_type in ["bulleted_list_item", "numbered_list_item"]:
                    key = f"first_{block_type}_{section}"
                    if key not in self.block_map:
                        self.block_map[key] = block_id
                
                # Store child_page references
                elif block_type == "child_page":
                    title = await self._get_child_page_title(block_id)
                    if title:
                        self.block_map[f"child_{title}"] = block_id
        except Exception:
            pass
    
    async def _explore_toggle(self, toggle_id: str):
        try:
            response = await self.mcp.get_block_children(toggle_id)
            if not response:
                return
            
            data = json.loads(response)
            for block in data.get("results", []):
                if block.get("type") == "child_page":
                    child_id = block.get("id")
                    title = await self._get_child_page_title(child_id)
                    if title:
                        self.block_map[f"child_{title}"] = child_id
                        await self._explore_child_page(child_id, title)
        except Exception:
            pass
    
    async def _explore_child_page(self, page_id: str, title: str):
        try:
            response = await self.mcp.get_block_children(page_id)
            if not response:
                return
            
            data = json.loads(response)
            for block in data.get("results", []):
                if block.get("type") == "callout":
                    self.block_map[f"callout_{title}"] = block.get("id")
                    break
        except Exception:
            pass
    
    async def _update_section(self, section: str) -> int:
        if section == "header":
            return await self._update_header()
        elif section == "purpose":
            return await self._update_purpose()
        elif section == "context":
            return await self._update_context()
        elif section == "terminologies":
            return await self._update_terminologies()
        elif section == "tools":
            return await self._update_tools()
        elif section == "roles":
            return await self._update_roles()
        elif section == "procedure":
            return await self._update_procedure()
        
        return 0
    
    async def _update_header(self) -> int:
        updates = 0
        
        if "heading_1" in self.block_map:
            updates += await self._update_block(
                self.block_map["heading_1"], "heading_1",
                {"rich_text": [{"type": "text", "text": {"content": "Software Deployment Process"}}]}
            )
            print("  Updated title")
        
        if "created_date" in self.block_map:
            updates += await self._update_block(
                self.block_map["created_date"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": "Created 2025-01-19"}}]}
            )
            print("  Updated date")
        
        if "responsible_dept" in self.block_map:
            updates += await self._update_block(
                self.block_map["responsible_dept"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": "Responsible department: DevOps Engineering Team"}}]}
            )
            print("  Updated department")
        
        if "callout_People team" in self.block_map:
            updates += await self._update_block(
                self.block_map["callout_People team"], "callout", {
                    "rich_text": [{"type": "text", "text": {"content": "DevOps Engineering Team Wiki - Contains team contact information, escalation procedures, and deployment schedules. Access required for all deployment activities."}}],
                    "color": "gray_background"
                }
            )
            print("  Updated People team callout")
        
        return updates
    
    async def _update_purpose(self) -> int:
        updates = 0
        if "para_Purpose" in self.block_map:
            text = "This SOP defines the standardized process for deploying software applications to production environments, ensuring zero-downtime deployments, proper rollback procedures, and compliance with security protocols. This procedure applies to all production deployments and must be followed by all engineering teams."
            updates += await self._update_block(
                self.block_map["para_Purpose"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": text}}]}
            )
            print("  Updated purpose")
        return updates
    
    async def _update_context(self) -> int:
        updates = 0
        if "para_Context" in self.block_map:
            text = "Software deployments are critical operations that can impact system availability and user experience. This process has been developed based on industry best practices and our incident response learnings from Q3 2023. All deployments must go through automated testing pipelines and require approval from designated reviewers."
            updates += await self._update_block(
                self.block_map["para_Context"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": text}}]}
            )
            print("  Updated context")
        
        callouts = {
            "Contacting IT": "Change Management Policy (SOP-001) - Defines approval workflows and change review processes for all production modifications.",
            "Team lunches": "Incident Response Procedures (SOP-003) - Emergency procedures for handling deployment failures and system outages.",
            "Sending swag": "Security Compliance Guidelines (SOP-007) - Security requirements and validation steps for production deployments."
        }
        
        for title, text in callouts.items():
            key = f"callout_{title}"
            if key in self.block_map:
                updates += await self._update_block(self.block_map[key], "callout", {
                    "rich_text": [{"type": "text", "text": {"content": text}}],
                    "color": "gray_background"
                })
                print(f"  Updated {title} callout")
        
        return updates
    
    async def _update_terminologies(self) -> int:
        updates = 0
        if "para_Terminologies" in self.block_map:
            updates += await self._update_block(
                self.block_map["para_Terminologies"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": "Essential deployment terminology for team understanding:"}}]}
            )
            print("  Updated terminologies intro")
        
        items = [
            "Blue-Green Deployment: A deployment strategy that maintains two identical production environments",
            "Rollback Window: The maximum time allowed to revert a deployment (30 minutes)",
            "Smoke Test: Initial verification tests run immediately after deployment",
            "Production Gateway: The approval checkpoint before production release"
        ]
        
        key = "first_bulleted_list_item_Terminologies"
        if key in self.block_map:
            # Update first item
            updates += await self._update_block(
                self.block_map[key], "bulleted_list_item",
                {"rich_text": [{"type": "text", "text": {"content": items[0]}}]}
            )
            print("  Updated first terminology")
            
            # Check for and add missing items
            existing_items = await self._get_list_items_after_block(self.block_map[key])
            existing_names = {item.split(':')[0].strip() for item in existing_items}
            
            missing_items = []
            for item in items[1:]:
                item_name = item.split(':')[0].strip()
                if item_name not in existing_names:
                    missing_items.append(item)
            
            if missing_items:
                updates += await self._add_list_items(
                    self.sop_page_id, 
                    self.block_map[key], 
                    missing_items, 
                    "bulleted_list_item"
                )
        
        return updates
    
    async def _update_tools(self) -> int:
        updates = 0
        if "para_Tools" in self.block_map:
            updates += await self._update_block(
                self.block_map["para_Tools"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": "Critical tools required for deployment operations:"}}]}
            )
            print("  Updated tools intro")
        
        tools = [
            "Jenkins CI/CD Pipeline - Primary deployment automation tool with integrated testing and approval workflows. Required for all automated deployments.",
            "Kubernetes Dashboard - Container orchestration monitoring and management interface for deployment verification and rollback operations."
        ]
        
        tool_idx = 1
        for title in ["Notion", "Figma"]:
            key = f"callout_{title}"
            if key in self.block_map and tool_idx <= len(tools):
                updates += await self._update_block(self.block_map[key], "callout", {
                    "rich_text": [{"type": "text", "text": {"content": tools[tool_idx - 1]}}],
                    "color": "gray_background"
                })
                print(f"  Updated tool {tool_idx}")
                tool_idx += 1
        
        return updates
    
    async def _update_roles(self) -> int:
        updates = 0
        
        if "para_Roles & responsibilities" in self.block_map:
            updates += await self._update_block(
                self.block_map["para_Roles & responsibilities"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": "The following roles are essential for successful deployment execution:"}}]}
            )
            print("  Updated roles intro")
        
        items = [
            "DevOps Engineer: Executes deployment, monitors system health, initiates rollbacks if needed",
            "Lead Developer: Reviews code changes, approves deployment package, validates functionality",
            "QA Engineer: Verifies smoke tests, confirms user acceptance criteria",
            "Security Officer: Validates security compliance, approves security-sensitive deployments"
        ]
        
        key = "first_bulleted_list_item_Roles & responsibilities"
        if key in self.block_map:
            # Update first item
            updates += await self._update_block(self.block_map[key], "bulleted_list_item",
                {"rich_text": [{"type": "text", "text": {"content": items[0]}}]})
            print("  Updated first role")
            
            # Check for and add missing items
            existing_items = await self._get_list_items_after_block(self.block_map[key])
            existing_names = {item.split(':')[0].strip() for item in existing_items}
            
            missing_items = []
            for item in items[1:]:
                item_name = item.split(':')[0].strip()
                if item_name not in existing_names:
                    missing_items.append(item)
            
            if missing_items:
                updates += await self._add_list_items(
                    self.sop_page_id, 
                    self.block_map[key], 
                    missing_items, 
                    "bulleted_list_item"
                )
        
        return updates
    
    async def _update_procedure(self) -> int:
        updates = 0
        
        if "para_Procedure" in self.block_map:
            updates += await self._update_block(
                self.block_map["para_Procedure"], "paragraph",
                {"rich_text": [{"type": "text", "text": {"content": "Follow these steps in sequence. Do not skip steps or perform them out of order."}}]}
            )
            print("  Updated procedure intro")
        
        items = [
            "Pre-deployment: Verify all automated tests pass, obtain required approvals from Lead Developer and Security Officer, confirm rollback plan is documented and tested",
            "Deployment execution: Deploy to staging environment first, run comprehensive smoke tests, obtain final Production Gateway approval, deploy to production using blue-green strategy",
            "Post-deployment: Monitor system metrics for minimum 30 minutes, validate all functionality using automated tests, document deployment results in change log, notify all stakeholders via deployment notification system"
        ]
        
        key = "first_numbered_list_item_Procedure"
        if key in self.block_map:
            updates += await self._update_block(self.block_map[key], "numbered_list_item",
                {"rich_text": [{"type": "text", "text": {"content": items[0]}}]})
            print("  Updated first procedure")
            
            # Check for and add missing items
            existing_items = await self._get_list_items_after_block(self.block_map[key])
            existing_names = {item.split(':')[0].strip() for item in existing_items}
            
            missing_items = []
            for item in items[1:]:
                item_name = item.split(':')[0].strip()
                if item_name not in existing_names:
                    missing_items.append(item)
            
            if missing_items:
                updates += await self._add_list_items(
                    self.sop_page_id, 
                    self.block_map[key], 
                    missing_items, 
                    "numbered_list_item"
                )
        
        return updates
    
    async def _update_block(self, block_id: str, block_type: str, props: Dict) -> int:
        try:
            await self.mcp.update_block(block_id, block_type, props)
            return 1
        except Exception as e:
            print(f"  Error: {e}")
            return 0
    
    async def _get_list_items_after_block(self, block_id: str) -> List[str]:
        """Get all list item contents after a given block ID in the SOP page"""
        try:
            root_response = await self.mcp.get_block_children(self.sop_page_id)
            if not root_response:
                return []
            
            root_data = json.loads(root_response)
            root_blocks = root_data.get("results", [])
            
            # Find the index of the given block_id
            target_index = None
            for i, block in enumerate(root_blocks):
                if block.get("id") == block_id:
                    target_index = i
                    break
            
            if target_index is None:
                return []
            
            # Collect list items after this block until next heading
            items = []
            for j in range(target_index, len(root_blocks)):
                block = root_blocks[j]
                
                # Stop at next heading
                if block.get("type") in ["heading_2"] and j > target_index:
                    break
                
                # Collect bulleted and numbered list items
                if block.get("type") in ["bulleted_list_item", "numbered_list_item"]:
                    content = self._extract_text(block)
                    if content:
                        items.append(content)
            
            return items
        except Exception as e:
            print(f"  Error getting list items: {e}")
            return []
    
    async def _add_list_items(self, parent_id: str, after_id: str, items: List[str], item_type: str) -> int:
        try:
            children = [{
                "type": item_type,
                item_type: {"rich_text": [{"type": "text", "text": {"content": item}}]}
            } for item in items]
            
            await self.mcp.patch_block_children(parent_id, children, after=after_id)
            print(f"  Added {len(items)} items")
            return len(items)
        except Exception as e:
            print(f"  Error adding items: {e}")
            return 0
    
    @staticmethod
    def _extract_title(props: Dict) -> str:
        for prop in props.values():
            if prop.get("type") == "title":
                arr = prop.get("title", [])
                if arr:
                    return arr[0].get("plain_text", "")
        return ""
    
    @staticmethod
    def _extract_text(block: Dict) -> str:
        block_type = block.get("type")
        data = block.get(block_type, {})
        
        if "rich_text" in data:
            text = ""
            for item in data.get("rich_text", []):
                if item.get("type") == "text":
                    text += item.get("text", {}).get("content", "")
            return text
        
        return ""
    
    async def _get_child_page_title(self, page_id: str) -> Optional[str]:
        try:
            response = await self.mcp.retrieve_page(page_id)
            if response:
                data = json.loads(response)
                return self._extract_title(data.get("properties", {}))
        except Exception:
            pass
        return None
    
    @staticmethod
    def _normalize_section(text: str) -> str:
        lower = text.lower()
        if "purpose" in lower:
            return "Purpose"
        elif "context" in lower:
            return "Context"
        elif "terminologies" in lower or "terminology" in lower:
            return "Terminologies"
        elif "tools" in lower:
            return "Tools"
        elif "roles" in lower or "responsibilities" in lower:
            return "Roles & responsibilities"
        elif "procedure" in lower:
            return "Procedure"
        return text


async def main():
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: API key not set")
        return
    
    skill = DeploymentProcessSOP(api_key)
    result = await skill.complete_sop()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Sections: {result['sections_updated']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
