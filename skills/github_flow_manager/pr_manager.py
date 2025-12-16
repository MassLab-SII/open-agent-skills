#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PR Manager Script
=================

Manage Pull Request lifecycle: create, merge, close, and update.
Supports creating PRs from branches and immediate merging with different strategies.

Note: For adding comments to PRs, use comment_manager.py instead.

Usage:
    python pr_manager.py <command> <owner> <repo> [options]

Commands:
    create      Create a new pull request
    merge       Merge an existing pull request
    close       Close a pull request without merging
    update      Update pull request details

Examples:
    # Create a PR
    python pr_manager.py create owner repo --head feature-branch --base main --title "Add feature" --body "Description"
    
    # Create and immediately merge
    python pr_manager.py create owner repo --head feature --base main --title "Fix" --merge squash
    
    # Merge existing PR
    python pr_manager.py merge owner repo --number 42 --method squash
    
    # Close PR without merging
    python pr_manager.py close owner repo --number 42
    
    # Update PR
    python pr_manager.py update owner repo --number 42 --title "New Title" --body "Updated description"
"""

import asyncio
import argparse
import json
import sys
from typing import Optional, Dict, Any

from utils import GitHubTools


class PRManager:
    """Manage Pull Request lifecycle"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the PR Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def create_pr(
        self,
        head: str,
        base: str,
        title: str,
        body: Optional[str] = None,
        draft: bool = False,
        merge_method: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request and optionally merge it immediately.

        Args:
            head: Head branch name
            base: Base branch name
            title: PR title
            body: PR description
            draft: Create as draft PR
            merge_method: If specified, merge immediately (squash/merge/rebase)

        Returns:
            Dict with pr_number and merged status
        """
        async with GitHubTools() as gh:
            print(f"Creating PR: {head} → {base}")
            
            # Step 1: Create PR
            pr_result = await gh.create_pull_request(
                owner=self.owner,
                repo=self.repo,
                title=title,
                head=head,
                base=base,
                body=body,
                draft=draft
            )
            
            pr_number = self._extract_pr_number(pr_result)
            
            if not pr_number:
                print(f"Failed to create PR: {pr_result}")
                return {"pr_number": 0, "merged": False}
            
            print(f"Created PR #{pr_number}")
            
            # Step 2: Merge if requested
            if merge_method:
                print(f"Merging PR #{pr_number} with method: {merge_method}")
                
                merge_result = await gh.merge_pull_request(
                    owner=self.owner,
                    repo=self.repo,
                    pull_number=pr_number,
                    merge_method=merge_method
                )
                
                merged = self._check_merge_success(merge_result)
                print(f"Merge {'successful' if merged else 'failed'}")
                
                return {"pr_number": pr_number, "merged": merged}
            
            return {"pr_number": pr_number, "merged": False}

    async def merge_pr(
        self,
        pr_number: int,
        merge_method: str = "squash",
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> bool:
        """
        Merge an existing pull request.

        Args:
            pr_number: Pull request number
            merge_method: Merge method (squash/merge/rebase)
            commit_title: Optional commit title
            commit_message: Optional commit message

        Returns:
            True if merge successful
        """
        async with GitHubTools() as gh:
            print(f"Merging PR #{pr_number} with method: {merge_method}")
            
            result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method=merge_method,
                commit_title=commit_title,
                commit_message=commit_message
            )
            
            success = self._check_merge_success(result)
            
            if success:
                print(f"✓ Successfully merged PR #{pr_number}")
            else:
                print(f"✗ Failed to merge PR #{pr_number}: {result}")
            
            return success

    async def close_pr(self, pr_number: int) -> bool:
        """
        Close a pull request without merging.

        Args:
            pr_number: Pull request number

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Closing PR #{pr_number}")
            
            result = await gh.update_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                state="closed"
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Successfully closed PR #{pr_number}")
            else:
                print(f"✗ Failed to close PR #{pr_number}")
            
            return success

    async def update_pr(
        self,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None
    ) -> bool:
        """
        Update pull request details.

        Args:
            pr_number: Pull request number
            title: New title
            body: New description
            state: New state (open/closed)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Updating PR #{pr_number}")
            
            result = await gh.update_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                title=title,
                body=body,
                state=state
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Successfully updated PR #{pr_number}")
            else:
                print(f"✗ Failed to update PR #{pr_number}")
            
            return success

    def _extract_pr_number(self, result: Any) -> int:
        """Extract PR number from API result"""
        import re
        
        def extract_from_data(data: dict) -> int:
            """Extract PR number from parsed data dict"""
            # Direct number field
            if "number" in data:
                return data.get("number", 0)
            # Extract from URL: https://github.com/owner/repo/pull/51
            url = data.get("url", "") or data.get("html_url", "")
            if url:
                match = re.search(r'/pull/(\d+)', url)
                if match:
                    return int(match.group(1))
            return 0
        
        if isinstance(result, dict):
            # Direct dict with number or url
            num = extract_from_data(result)
            if num:
                return num
            # MCP format: {'content': [{'type': 'text', 'text': '...'}]}
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                num = extract_from_data(parsed)
                                if num:
                                    return num
                        except json.JSONDecodeError:
                            # Try regex on raw text
                            match = re.search(r'"number"\s*:\s*(\d+)', text)
                            if match:
                                return int(match.group(1))
                            match = re.search(r'/pull/(\d+)', text)
                            if match:
                                return int(match.group(1))
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    num = extract_from_data(parsed)
                    if num:
                        return num
            except json.JSONDecodeError:
                pass
            # Try regex on raw string
            match = re.search(r'"number"\s*:\s*(\d+)', result)
            if match:
                return int(match.group(1))
            match = re.search(r'/pull/(\d+)', result)
            if match:
                return int(match.group(1))
        return 0

    def _check_merge_success(self, result: Any) -> bool:
        """Check if merge was successful"""
        def check_data(data: dict) -> bool:
            """Check merge success from parsed data"""
            return data.get("merged", False) or "sha" in data
        
        if isinstance(result, dict):
            # Direct dict check
            if check_data(result):
                return True
            # MCP format: {'content': [{'type': 'text', 'text': '...'}]}
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict) and check_data(parsed):
                                return True
                        except json.JSONDecodeError:
                            # Check raw text
                            if '"merged":true' in text.lower() or '"sha"' in text:
                                return True
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and check_data(parsed):
                    return True
            except json.JSONDecodeError:
                pass
            # Check raw string
            result_lower = result.lower()
            return '"merged":true' in result_lower or '"sha"' in result_lower
        return False

    def _check_success(self, result: Any) -> bool:
        """Check if operation was successful, handling MCP response format"""
        if not result:
            return False
        
        def check_data(data: dict) -> bool:
            """Check success from parsed data"""
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
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return check_data(parsed)
                        except json.JSONDecodeError:
                            # Check raw text for errors
                            text_lower = text.lower()
                            if "error" in text_lower or "failed" in text_lower:
                                return False
                            return True
            # Direct dict (not MCP format)
            return check_data(result)
        if isinstance(result, str):
            try:
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
        description='Manage Pull Request lifecycle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a PR
  python pr_manager.py create owner repo --head feature --base main --title "Add feature"
  
  # Create and merge immediately
  python pr_manager.py create owner repo --head fix --base main --title "Fix bug" --merge squash
  
  # Merge existing PR
  python pr_manager.py merge owner repo --number 42 --method squash
  
  # Close PR without merging
  python pr_manager.py close owner repo --number 42
  
  # Update PR
  python pr_manager.py update owner repo --number 42 --title "New Title"

Note: For adding comments to PRs, use comment_manager.py instead.
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: create
    create_parser = subparsers.add_parser("create", help="Create a pull request")
    create_parser.add_argument("owner", help="Repository owner")
    create_parser.add_argument("repo", help="Repository name")
    create_parser.add_argument("--head", required=True, help="Head branch")
    create_parser.add_argument("--base", required=True, help="Base branch")
    create_parser.add_argument("--title", required=True, help="PR title")
    create_parser.add_argument("--body", help="PR description")
    create_parser.add_argument("--draft", action="store_true", help="Create as draft")
    create_parser.add_argument("--merge", choices=["squash", "merge", "rebase"],
                              help="Merge immediately with specified method")
    
    # Command: merge
    merge_parser = subparsers.add_parser("merge", help="Merge a pull request")
    merge_parser.add_argument("owner", help="Repository owner")
    merge_parser.add_argument("repo", help="Repository name")
    merge_parser.add_argument("--number", type=int, required=True, help="PR number")
    merge_parser.add_argument("--method", choices=["squash", "merge", "rebase"],
                             default="squash", help="Merge method")
    merge_parser.add_argument("--commit-title", help="Commit title")
    merge_parser.add_argument("--commit-message", help="Commit message")
    
    # Command: close
    close_parser = subparsers.add_parser("close", help="Close a pull request")
    close_parser.add_argument("owner", help="Repository owner")
    close_parser.add_argument("repo", help="Repository name")
    close_parser.add_argument("--number", type=int, required=True, help="PR number")
    
    # Command: update
    update_parser = subparsers.add_parser("update", help="Update pull request")
    update_parser.add_argument("owner", help="Repository owner")
    update_parser.add_argument("repo", help="Repository name")
    update_parser.add_argument("--number", type=int, required=True, help="PR number")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--body", help="New description")
    update_parser.add_argument("--state", choices=["open", "closed"], help="New state")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = PRManager(args.owner, args.repo)
    
    try:
        if args.command == "create":
            result = await manager.create_pr(
                head=args.head,
                base=args.base,
                title=args.title,
                body=args.body,
                draft=args.draft,
                merge_method=args.merge
            )
            print(f"\n✓ PR #{result['pr_number']} created" + 
                  (f" and merged" if result['merged'] else ""))
            
        elif args.command == "merge":
            success = await manager.merge_pr(
                pr_number=args.number,
                merge_method=args.method,
                commit_title=args.commit_title,
                commit_message=args.commit_message
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "close":
            success = await manager.close_pr(pr_number=args.number)
            sys.exit(0 if success else 1)
            
        elif args.command == "update":
            success = await manager.update_pr(
                pr_number=args.number,
                title=args.title,
                body=args.body,
                state=args.state
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
