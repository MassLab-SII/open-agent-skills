#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitFlow Manager Script
======================

Implement GitFlow workflow operations for GitHub repositories.
Handles initialization and finishing (merging) of GitFlow branches.

Note: For creating branches, use branch_manager.py instead.

Usage:
    python gitflow_manager.py <command> <owner> <repo> [options]

Commands:
    init        Initialize GitFlow structure (create develop branch)
    finish      Finish a feature/release/hotfix branch (create PR and merge)

Examples:
    # Initialize GitFlow
    python gitflow_manager.py init owner repo
    
    # Finish feature (merge to develop)
    python gitflow_manager.py finish owner repo --type feature --name "user-auth" --target develop
    
    # Finish release (merge to main)
    python gitflow_manager.py finish owner repo --type release --name "1.0.0" --target main
    
    # Finish hotfix (merge to main)
    python gitflow_manager.py finish owner repo --type hotfix --name "security-patch" --target main
"""

import asyncio
import argparse
import json
import re
import sys
from typing import Optional, Any

from utils import GitHubTools


class GitFlowManager:
    """Manage GitFlow workflow operations"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the GitFlow Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def init_gitflow(self) -> bool:
        """
        Initialize GitFlow structure by creating develop branch from main.

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Initializing GitFlow for {self.owner}/{self.repo}")
            print("Creating 'develop' branch from 'main'")
            
            result = await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch="develop",
                from_branch="main"
            )
            
            success = self._check_success(result)
            
            if success:
                print("✓ GitFlow initialized successfully")
                print("  - develop branch created from main")
            else:
                print(f"✗ Failed to initialize GitFlow: {result}")
            
            return success

    async def finish_branch(
        self,
        branch_type: str,
        name: str,
        target: str = "develop",
        title: Optional[str] = None,
        merge_method: str = "squash"
    ) -> bool:
        """
        Finish a feature/release/hotfix branch by creating and merging a PR.

        Args:
            branch_type: Branch type (feature/release/hotfix)
            name: Branch name (without prefix)
            target: Target branch to merge into
            title: Optional PR title
            merge_method: Merge method (squash/merge/rebase)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            # Construct branch name based on type
            if branch_type == "release":
                branch_name = f"release/v{name}"
            else:
                branch_name = f"{branch_type}/{name}"
            
            pr_title = title or f"Merge {branch_name} into {target}"
            
            print(f"Finishing {branch_type} '{name}'")
            print(f"  Creating PR: {branch_name} → {target}")
            
            # Step 1: Create PR
            pr_result = await gh.create_pull_request(
                owner=self.owner,
                repo=self.repo,
                title=pr_title,
                head=branch_name,
                base=target,
                body=f"## Summary\n\nMerging {branch_type} branch '{name}' into {target}.\n\nThis PR was created by GitFlow finish operation."
            )
            
            pr_number = self._extract_pr_number(pr_result)
            
            if not pr_number:
                print(f"✗ Failed to create PR: {pr_result}")
                return False
            
            print(f"  Created PR #{pr_number}")
            
            # Step 2: Merge PR
            print(f"  Merging PR #{pr_number} with method: {merge_method}")
            
            merge_result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method=merge_method
            )
            
            success = self._check_merge_success(merge_result)
            
            if success:
                print(f"✓ Successfully finished {branch_type} '{name}'")
                print(f"  - PR #{pr_number} merged into {target}")
            else:
                print(f"✗ Failed to merge PR: {merge_result}")
            
            return success

    def _check_success(self, result: Any) -> bool:
        """Check if operation was successful, handling MCP response format"""
        if not result:
            return False
        
        def check_data(data: dict) -> bool:
            if "error" in data or data.get("isError"):
                return False
            return True
        
        if isinstance(result, dict):
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
                            text_lower = text.lower()
                            if "error" in text_lower or "failed" in text_lower:
                                return False
                            return True
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

    def _check_merge_success(self, result: Any) -> bool:
        """Check if merge was successful, handling MCP response format"""
        def check_data(data: dict) -> bool:
            return data.get("merged", False) or "sha" in data
        
        if isinstance(result, dict):
            if check_data(result):
                return True
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
                            if '"merged":true' in text.lower() or '"sha"' in text:
                                return True
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and check_data(parsed):
                    return True
            except json.JSONDecodeError:
                pass
            result_lower = result.lower()
            return '"merged":true' in result_lower or '"sha"' in result_lower
        return False

    def _extract_pr_number(self, result: Any) -> int:
        """Extract PR number from result, handling MCP response format"""
        def extract_from_data(data: dict) -> int:
            if "number" in data:
                return data.get("number", 0)
            url = data.get("url", "") or data.get("html_url", "")
            if url:
                match = re.search(r'/pull/(\d+)', url)
                if match:
                    return int(match.group(1))
            return 0
        
        if isinstance(result, dict):
            num = extract_from_data(result)
            if num:
                return num
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
            match = re.search(r'"number"\s*:\s*(\d+)', result)
            if match:
                return int(match.group(1))
            match = re.search(r'/pull/(\d+)', result)
            if match:
                return int(match.group(1))
        return 0


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage GitFlow workflow operations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize GitFlow
  python gitflow_manager.py init owner repo
  
  # Finish feature (merge to develop)
  python gitflow_manager.py finish owner repo --type feature --name "user-auth" --target develop
  
  # Finish release (merge to main)
  python gitflow_manager.py finish owner repo --type release --name "1.0.0" --target main
  
  # Finish hotfix (merge to main)
  python gitflow_manager.py finish owner repo --type hotfix --name "security-patch" --target main

Note: For creating branches, use branch_manager.py instead.
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize GitFlow (create develop branch)")
    init_parser.add_argument("owner", help="Repository owner")
    init_parser.add_argument("repo", help="Repository name")
    
    # Command: finish
    finish_parser = subparsers.add_parser("finish", help="Finish branch (create PR and merge)")
    finish_parser.add_argument("owner", help="Repository owner")
    finish_parser.add_argument("repo", help="Repository name")
    finish_parser.add_argument("--type", required=True, choices=["feature", "release", "hotfix"], help="Branch type")
    finish_parser.add_argument("--name", required=True, help="Branch name (without prefix)")
    finish_parser.add_argument("--target", default="develop", help="Target branch (default: develop)")
    finish_parser.add_argument("--title", help="PR title")
    finish_parser.add_argument("--merge-method", dest="merge_method", default="squash",
                              choices=["squash", "merge", "rebase"], help="Merge method (default: squash)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = GitFlowManager(args.owner, args.repo)
    
    try:
        if args.command == "init":
            success = await manager.init_gitflow()
            sys.exit(0 if success else 1)
            
        elif args.command == "finish":
            success = await manager.finish_branch(
                branch_type=args.type,
                name=args.name,
                target=args.target,
                title=args.title,
                merge_method=args.merge_method
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
