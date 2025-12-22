"""
FAQ Column Layout Skill - Reorganize FAQ section into two-column layout.

This skill reorganizes the FAQ toggle in the Self Assessment page by:
1. Creating a column list with two columns
2. Moving Q&A pairs to left and right columns
3. Adding new Q&A content as needed
4. Maintaining consistent formatting
"""

import asyncio
import os
from typing import Any, Dict, List
from skills.self_assessment.utils import NotionMCPTools, extract_block_property


class FAQColumnLayout:
    """Reorganize FAQ section into two-column layout."""
    
    def __init__(self, api_key: str):
        """Initialize with Notion API key."""
        self.api_key = api_key
    
    async def reorganize_faq(self) -> Dict[str, Any]:
        """
        Main execution method:
        1. Find Self Assessment page
        2. Find FAQ toggle block
        3. Create column list structure
        4. Move Q&A pairs to columns
        5. Delete old blocks and return result
        """
        result = {
            "success": False,
            "message": "",
            "faq_toggle_id": None,
            "columns_created": False,
            "qa_pairs_moved": 0,
            "errors": []
        }
        
        async with NotionMCPTools(self.api_key) as tools:
            try:
                # Step 1: Find Self Assessment page
                print("Step 1: Searching for Self Assessment page...")
                pages_result = await tools.search("Self Assessment", filter_type="page")
                
                if not pages_result or not pages_result.get("results"):
                    result["errors"].append("Self Assessment page not found")
                    return result
                
                page_id = pages_result["results"][0]["id"]
                print(f"  ✓ Found Self Assessment page (ID: {page_id})")
                
                # Step 2: Get page children to find FAQ toggle
                print("Step 2: Finding FAQ toggle block...")
                page_children = await tools.get_block_children(page_id)
                
                faq_toggle = None
                faq_toggle_id = None
                
                if page_children.get("results"):
                    for block in page_children["results"]:
                        if block.get("type") == "toggle":
                            toggle_text = extract_block_property(block, "toggle", "text")
                            if toggle_text and "FAQ" in toggle_text:
                                faq_toggle = block
                                faq_toggle_id = block.get("id")
                                break
                
                if not faq_toggle_id:
                    result["errors"].append("FAQ toggle not found in Self Assessment page")
                    return result
                
                print(f"  ✓ Found FAQ toggle (ID: {faq_toggle_id})")
                result["faq_toggle_id"] = faq_toggle_id
                
                # Step 3: Get existing FAQ content
                print("Step 3: Retrieving existing FAQ content...")
                faq_children = await tools.get_block_children(faq_toggle_id)
                
                qa_blocks = []
                if faq_children.get("results"):
                    qa_blocks = [b for b in faq_children["results"] 
                                if b.get("type") in ["heading_3", "paragraph"]]
                
                print(f"  ✓ Found {len(qa_blocks)} Q&A blocks")
                
                # Step 4: Create column list structure
                print("Step 4: Creating column list structure...")
                column_list_data = {
                    "type": "column_list",
                    "column_list": {
                        "children": [
                            {"type": "column", "column": {"children": []}},
                            {"type": "column", "column": {"children": []}}
                        ]
                    }
                }
                
                column_list_response = await tools.patch_block_children(
                    faq_toggle_id, [column_list_data]
                )
                
                result["columns_created"] = True
                print("  ✓ Column list created")
                
                # Step 5: Get column IDs from response
                print("Step 5: Retrieving column IDs...")
                faq_children_updated = await tools.get_block_children(faq_toggle_id)
                
                column_list_block = None
                if faq_children_updated.get("results"):
                    for block in faq_children_updated["results"]:
                        if block.get("type") == "column_list":
                            column_list_block = block
                            break
                
                if not column_list_block:
                    result["errors"].append("Column list not created properly")
                    return result
                
                column_list_id = column_list_block.get("id")
                
                # Get columns
                columns_response = await tools.get_block_children(column_list_id)
                columns = []
                if columns_response.get("results"):
                    columns = [b for b in columns_response["results"] 
                              if b.get("type") == "column"]
                
                if len(columns) != 2:
                    result["errors"].append(f"Expected 2 columns, got {len(columns)}")
                    return result
                
                left_column_id = columns[0].get("id")
                right_column_id = columns[1].get("id")
                print(f"  ✓ Left column: {left_column_id}")
                print(f"  ✓ Right column: {right_column_id}")
                
                # Step 6: Distribute Q&A pairs to columns
                print("Step 6: Distributing Q&A pairs to columns...")
                
                # Prepare Q&A pairs for left column (first 2 pairs from original)
                left_qa = []
                for i in range(0, min(4, len(qa_blocks)), 2):
                    if i < len(qa_blocks) and i+1 < len(qa_blocks):
                        left_qa.append(qa_blocks[i])
                        left_qa.append(qa_blocks[i+1])
                
                # Prepare Q&A pairs for right column (remaining pairs + new Q4)
                right_qa = []
                if len(qa_blocks) > 4:
                    for i in range(4, len(qa_blocks), 2):
                        if i < len(qa_blocks) and i+1 < len(qa_blocks):
                            right_qa.append(qa_blocks[i])
                            right_qa.append(qa_blocks[i+1])
                else:
                    # Add Q3 to right column
                    if len(qa_blocks) > 4:
                        right_qa.extend(qa_blocks[4:6])
                
                # Add Q4 to right column if needed
                if len(right_qa) < 4:
                    q4_heading = {
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": "How long should a typical hyperfocus session last?"}}]
                        }
                    }
                    q4_answer = {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": "Optimal hyperfocus sessions typically last 90-120 minutes, but this can vary by individual. Use the self-assessment worksheet to find your ideal duration."}}]
                        }
                    }
                    right_qa.extend([q4_heading, q4_answer])
                
                # Add to left column
                if left_qa:
                    await tools.patch_block_children(left_column_id, left_qa)
                    result["qa_pairs_moved"] += len([b for b in left_qa if b.get("type") == "heading_3"])
                    print(f"  ✓ Added {len([b for b in left_qa if b.get('type') == 'heading_3'])} Q&A pairs to left column")
                
                # Add to right column
                if right_qa:
                    await tools.patch_block_children(right_column_id, right_qa)
                    result["qa_pairs_moved"] += len([b for b in right_qa if b.get("type") == "heading_3"])
                    print(f"  ✓ Added {len([b for b in right_qa if b.get('type') == 'heading_3'])} Q&A pairs to right column")
                
                # Step 7: Delete old Q&A blocks from FAQ toggle
                print("Step 7: Cleaning up old Q&A blocks...")
                for block in qa_blocks:
                    block_id = block.get("id")
                    if block_id:
                        await tools.delete_block(block_id)
                
                print(f"  ✓ Deleted {len(qa_blocks)} old Q&A blocks")
                
                result["success"] = True
                result["message"] = f"FAQ reorganized into {len(columns)} columns with {result['qa_pairs_moved']} Q&A pairs"
                
            except Exception as e:
                result["errors"].append(str(e))
                print(f"Error: {str(e)}")
        
        return result


async def main():
    """CLI entry point."""
    api_key = os.getenv("EVAL_NOTION_API_KEY")
    if not api_key:
        print("Error: EVAL_NOTION_API_KEY environment variable not set")
        return
    
    skill = FAQColumnLayout(api_key)
    result = await skill.reorganize_faq()
    
    print("\n" + "=" * 70)
    print("📊 Execution Summary")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"FAQ Toggle ID: {result['faq_toggle_id']}")
    print(f"Columns Created: {result['columns_created']}")
    print(f"Q&A Pairs Moved: {result['qa_pairs_moved']}")
    
    if result["errors"]:
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
