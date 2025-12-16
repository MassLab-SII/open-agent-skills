#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Manager Script
====================

Manage labels on GitHub Issues and Pull Requests.
Supports adding, removing, and batch operations on labels.

Usage:
    python label_manager.py <command> <owner> <repo> [options]

Commands:
    add         Add labels to issues or PRs
    remove      Remove labels from issues or PRs
    batch       Batch add labels to multiple issues/PRs

Examples:
    # Add labels to an issue
    python label_manager.py add owner repo --issue 42 --labels "bug,priority-high"
    
    # Add labels to a PR
    python label_manager.py add owner repo --pr 42 --labels "enhancement"
    
    # Remove labels from an issue
    python label_manager.py remove owner repo --issue 42 --labels "needs-triage"
    
    # Batch add labels to multiple issues
    python label_manager.py batch owner repo --issues "1,2,3" --labels "reviewed"
"""

import asyncio
import argparse
import json
import sys
from typing import List, Optional

from utils import GitHubTools


class LabelManager:
    """Manage labels on Issues and Pull Requests"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Label Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def add_labels_to_issue(
        self,
        issue_number: int,
        labels: List[str]
    ) -> bool:
        """
        Add labels to an issue.

        Args:
            issue_number: Issue number
            labels: List of labels to add

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Adding labels {labels} to issue #{issue_number}")
            
            # Get current issue details
            issue_detail = await gh.issue_read(
                owner=self.owner,
                repo=self.repo,
                issue_number=issue_number
            )
            
            issue_data = self._parse_result(issue_detail)
            if not isinstance(issue_data, dict):
                print(f"Failed to get issue #{issue_number}")
                return False
            
            # Get existing labels
            existing_labels = issue_data.get("labels", [])
            existing_label_names = [
                l.get("name") if isinstance(l, dict) else str(l)
                for l in existing_labels
            ]
            
            # Merge with new labels (avoid duplicates)
            all_labels = list(set(existing_label_names + labels))
            
            # Update issue with merged labels
            result = await gh.issue_write(
                owner=self.owner,
                repo=self.repo,
                title=issue_data.get("title", ""),
                issue_number=issue_number,
                labels=all_labels,
                method="update"
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Labels added to issue #{issue_number}")
            else:
                print(f"✗ Failed to add labels")
            
            return success

    async def add_labels_to_pr(
        self,
        pr_number: int,
        labels: List[str]
    ) -> bool:
        """
        Add labels to a pull request.

        Args:
            pr_number: Pull request number
            labels: List of labels to add

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Adding labels {labels} to PR #{pr_number}")
            
            # Get current PR details
            pr_detail = await gh.pull_request_read(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                method="get"
            )
            
            pr_data = self._parse_result(pr_detail)
            if not isinstance(pr_data, dict):
                print(f"Failed to get PR #{pr_number}")
                return False
            
            # Get existing labels
            existing_labels = pr_data.get("labels", [])
            existing_label_names = [
                l.get("name") if isinstance(l, dict) else str(l)
                for l in existing_labels
            ]
            
            # Merge with new labels
            all_labels = list(set(existing_label_names + labels))
            
            # Update PR with merged labels
            result = await gh.update_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                labels=all_labels
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Labels added to PR #{pr_number}")
            else:
                print(f"✗ Failed to add labels")
            
            return success

    async def batch_add_labels(
        self,
        issue_numbers: List[int],
        labels: List[str],
        is_pr: bool = False
    ) -> int:
        """
        Batch add labels to multiple issues or PRs.

        Args:
            issue_numbers: List of issue/PR numbers
            labels: List of labels to add
            is_pr: True if targets are PRs, False for issues

        Returns:
            Number of successful operations
        """
        success_count = 0
        
        for number in issue_numbers:
            try:
                if is_pr:
                    success = await self.add_labels_to_pr(number, labels)
                else:
                    success = await self.add_labels_to_issue(number, labels)
                
                if success:
                    success_count += 1
            except Exception as e:
                print(f"Error processing #{number}: {e}")
        
        return success_count

    def _parse_result(self, result):
        """Parse API result, handling MCP response format"""
        # Handle MCP format: {'content': [{'type': 'text', 'text': '...'}]}
        if isinstance(result, dict):
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            pass
            # Direct dict (not MCP format)
            if "content" not in result or not isinstance(result.get("content"), list):
                return result
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {}
        return {}

    def _check_success(self, result) -> bool:
        """Check if operation was successful, handling MCP response format"""
        if not result:
            return False
        
        def check_data(data: dict) -> bool:
            if "error" in data or data.get("isError"):
                return False
            return True
        
        if isinstance(result, dict):
            # Check for MCP format first
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            import json
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return check_data(parsed)
                        except json.JSONDecodeError:
                            text_lower = text.lower()
                            if "error" in text_lower or "failed" in text_lower:
                                return False
                            return True
            return check_data(result)
        if isinstance(result, str):
            try:
                import json
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    return check_data(parsed)
            except json.JSONDecodeError:
                pass
            result_lower = result.lower()
            if "error" in result_lower or "failed" in result_lower:
                return False
            return True
        return True


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage labels on Issues and Pull Requests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add labels to an issue
  python label_manager.py add owner repo --issue 42 --labels "bug,priority-high"
  
  # Add labels to a PR
  python label_manager.py add owner repo --pr 42 --labels "enhancement"
  
  # Batch add labels to multiple issues
  python label_manager.py batch owner repo --issues "1,2,3" --labels "reviewed"
  
  # Batch add labels to multiple PRs
  python label_manager.py batch owner repo --prs "10,11,12" --labels "needs-review"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: add
    add_parser = subparsers.add_parser("add", help="Add labels")
    add_parser.add_argument("owner", help="Repository owner")
    add_parser.add_argument("repo", help="Repository name")
    add_parser.add_argument("--issue", type=int, help="Issue number")
    add_parser.add_argument("--pr", type=int, help="Pull request number")
    add_parser.add_argument("--labels", required=True, help="Comma-separated labels")
    
    # Command: batch
    batch_parser = subparsers.add_parser("batch", help="Batch add labels")
    batch_parser.add_argument("owner", help="Repository owner")
    batch_parser.add_argument("repo", help="Repository name")
    batch_parser.add_argument("--issues", help="Comma-separated issue numbers")
    batch_parser.add_argument("--prs", help="Comma-separated PR numbers")
    batch_parser.add_argument("--labels", required=True, help="Comma-separated labels")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = LabelManager(args.owner, args.repo)
    labels = [l.strip() for l in args.labels.split(",")]
    
    try:
        if args.command == "add":
            if args.issue:
                success = await manager.add_labels_to_issue(args.issue, labels)
                sys.exit(0 if success else 1)
            elif args.pr:
                success = await manager.add_labels_to_pr(args.pr, labels)
                sys.exit(0 if success else 1)
            else:
                print("Error: Must specify either --issue or --pr")
                sys.exit(1)
                
        elif args.command == "batch":
            if args.issues:
                numbers = [int(n.strip()) for n in args.issues.split(",")]
                count = await manager.batch_add_labels(numbers, labels, is_pr=False)
                print(f"\n✓ Successfully added labels to {count}/{len(numbers)} issues")
            elif args.prs:
                numbers = [int(n.strip()) for n in args.prs.split(",")]
                count = await manager.batch_add_labels(numbers, labels, is_pr=True)
                print(f"\n✓ Successfully added labels to {count}/{len(numbers)} PRs")
            else:
                print("Error: Must specify either --issues or --prs")
                sys.exit(1)
                
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
