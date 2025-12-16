#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Branch Manager Script
=====================

Comprehensive branch management for GitHub repositories.
Supports creating branches with any name, GitFlow-style branches, and listing.

Usage:
    python branch_manager.py <command> <owner> <repo> [options]

Commands:
    create      Create a branch with any name
    feature     Create a feature/* branch (GitFlow)
    release     Create a release/* branch (GitFlow)
    hotfix      Create a hotfix/* branch (GitFlow)
    list        List all branches

Examples:
    # Create a branch with any name
    python branch_manager.py create owner repo --name "fix/race-condition" --from main
    
    # Create GitFlow-style branches
    python branch_manager.py feature owner repo --name "user-auth" --from develop
    python branch_manager.py release owner repo --version "1.0.0" --from develop
    python branch_manager.py hotfix owner repo --name "security-patch" --from main
    
    # List all branches
    python branch_manager.py list owner repo
"""

import asyncio
import argparse
import json
import sys
from typing import List, Dict, Any, Optional

from utils import GitHubTools


class BranchManager:
    """Comprehensive branch management for GitHub repositories"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Branch Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def create_branch(self, name: str, from_branch: str = "main") -> bool:
        """
        Create a branch with any name.

        Args:
            name: Branch name (can be any valid git branch name)
            from_branch: Source branch to create from

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Creating branch '{name}' from '{from_branch}'")
            
            result = await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch=name,
                from_branch=from_branch
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Branch '{name}' created successfully")
            else:
                print(f"✗ Failed to create branch: {result}")
            
            return success

    async def create_feature_branch(self, name: str, from_branch: str = "develop") -> bool:
        """
        Create a feature branch (GitFlow style).

        Args:
            name: Feature name (will be prefixed with 'feature/')
            from_branch: Source branch (default: develop)

        Returns:
            True if successful
        """
        branch_name = f"feature/{name}"
        return await self.create_branch(branch_name, from_branch)

    async def create_release_branch(self, version: str, from_branch: str = "develop") -> bool:
        """
        Create a release branch (GitFlow style).

        Args:
            version: Release version (will be prefixed with 'release/v')
            from_branch: Source branch (default: develop)

        Returns:
            True if successful
        """
        branch_name = f"release/v{version}"
        return await self.create_branch(branch_name, from_branch)

    async def create_hotfix_branch(self, name: str, from_branch: str = "main") -> bool:
        """
        Create a hotfix branch (GitFlow style).

        Args:
            name: Hotfix name (will be prefixed with 'hotfix/')
            from_branch: Source branch (default: main)

        Returns:
            True if successful
        """
        branch_name = f"hotfix/{name}"
        return await self.create_branch(branch_name, from_branch)

    async def list_branches(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        List all branches in the repository.

        Args:
            per_page: Number of branches per page

        Returns:
            List of branch information dicts
        """
        async with GitHubTools() as gh:
            print(f"Listing branches for {self.owner}/{self.repo}")
            
            all_branches = []
            page = 1
            
            while True:
                result = await gh.list_branches(
                    owner=self.owner,
                    repo=self.repo,
                    page=page,
                    per_page=per_page
                )
                
                branches = self._parse_result(result)
                
                if not branches:
                    break
                
                all_branches.extend(branches)
                
                if len(branches) < per_page:
                    break
                
                page += 1
            
            return all_branches

    async def branch_exists(self, name: str) -> bool:
        """
        Check if a branch exists.

        Args:
            name: Branch name to check

        Returns:
            True if branch exists
        """
        branches = await self.list_branches()
        branch_names = [b.get("name", "") for b in branches]
        return name in branch_names

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

    def _parse_result(self, result: Any) -> List[Dict[str, Any]]:
        """Parse API result, handling MCP response format"""
        if isinstance(result, dict):
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, list):
                                return parsed
                        except json.JSONDecodeError:
                            continue
            if isinstance(result, list):
                return result
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return []

    def print_branches(self, branches: List[Dict[str, Any]]):
        """Pretty print branch list"""
        if not branches:
            print("\nNo branches found.")
            return

        print(f"\n{'Branch Name':<50} | {'Protected'}")
        print("-" * 65)
        
        for branch in branches:
            name = branch.get("name", "")
            protected = "🔒" if branch.get("protected", False) else ""
            print(f"{name:<50} | {protected}")
        
        print(f"\nTotal: {len(branches)} branches")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Comprehensive branch management for GitHub repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a branch with any name
  python branch_manager.py create owner repo --name "fix/race-condition" --from main
  python branch_manager.py create owner repo --name "bugfix/memory-leak" --from develop
  
  # Create GitFlow-style branches
  python branch_manager.py feature owner repo --name "user-auth" --from develop
  python branch_manager.py release owner repo --version "1.0.0" --from develop
  python branch_manager.py hotfix owner repo --name "security-patch" --from main
  
  # List all branches
  python branch_manager.py list owner repo
  
  # Delete a branch
  python branch_manager.py delete owner repo --name "feature/old-feature"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: create (generic branch creation)
    create_parser = subparsers.add_parser("create", help="Create a branch with any name")
    create_parser.add_argument("owner", help="Repository owner")
    create_parser.add_argument("repo", help="Repository name")
    create_parser.add_argument("--name", required=True, help="Branch name (any valid git branch name)")
    create_parser.add_argument("--from", dest="from_branch", default="main", help="Source branch (default: main)")
    
    # Command: feature (GitFlow)
    feature_parser = subparsers.add_parser("feature", help="Create a feature/* branch")
    feature_parser.add_argument("owner", help="Repository owner")
    feature_parser.add_argument("repo", help="Repository name")
    feature_parser.add_argument("--name", required=True, help="Feature name")
    feature_parser.add_argument("--from", dest="from_branch", default="develop", help="Source branch (default: develop)")
    
    # Command: release (GitFlow)
    release_parser = subparsers.add_parser("release", help="Create a release/* branch")
    release_parser.add_argument("owner", help="Repository owner")
    release_parser.add_argument("repo", help="Repository name")
    release_parser.add_argument("--version", required=True, help="Release version")
    release_parser.add_argument("--from", dest="from_branch", default="develop", help="Source branch (default: develop)")
    
    # Command: hotfix (GitFlow)
    hotfix_parser = subparsers.add_parser("hotfix", help="Create a hotfix/* branch")
    hotfix_parser.add_argument("owner", help="Repository owner")
    hotfix_parser.add_argument("repo", help="Repository name")
    hotfix_parser.add_argument("--name", required=True, help="Hotfix name")
    hotfix_parser.add_argument("--from", dest="from_branch", default="main", help="Source branch (default: main)")
    
    # Command: list
    list_parser = subparsers.add_parser("list", help="List all branches")
    list_parser.add_argument("owner", help="Repository owner")
    list_parser.add_argument("repo", help="Repository name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = BranchManager(args.owner, args.repo)
    
    try:
        if args.command == "create":
            success = await manager.create_branch(
                name=args.name,
                from_branch=args.from_branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "feature":
            success = await manager.create_feature_branch(
                name=args.name,
                from_branch=args.from_branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "release":
            success = await manager.create_release_branch(
                version=args.version,
                from_branch=args.from_branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "hotfix":
            success = await manager.create_hotfix_branch(
                name=args.name,
                from_branch=args.from_branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "list":
            branches = await manager.list_branches()
            manager.print_branches(branches)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
