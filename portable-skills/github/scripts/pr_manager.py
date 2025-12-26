#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PR Manager Script
=================

Manage Pull Request lifecycle: create, merge, close, and update.
Supports creating PRs from branches and immediate merging with different strategies.
Now includes label management (add/remove labels) to enable atomic PR + Label operations.

Usage:
    python pr_manager.py <command> <owner> <repo> [options]

Commands:
    create      Create a new pull request
    merge       Merge an existing pull request
    close       Close a pull request without merging
    update      Update pull request details (title, body, state, labels)

Examples:
    # Create a PR
    python pr_manager.py create owner repo --head feature-branch --base main --title "Add feature" --body "Description"
    
    # Create and immediately merge
    python pr_manager.py create owner repo --head feature --base main --title "Fix" --merge squash
    
    # Merge existing PR
    python pr_manager.py merge owner repo --number 42 --method squash
    
    # Close PR without merging
    python pr_manager.py close owner repo --number 42
    
    # Update PR title/body
    python pr_manager.py update owner repo --number 42 --title "New Title" --body "Updated description"
    
    # Add labels to a PR
    python pr_manager.py update owner repo --number 42 --add-labels "reviewed,approved"
    
    # Remove labels from a PR
    python pr_manager.py update owner repo --number 42 --remove-labels "needs-review"
"""

import asyncio
import argparse
import json
import sys
from typing import Optional, Dict, Any, List

from utils import (
    GitHubTools,
    parse_mcp_result,
    extract_pr_number,
    check_api_success,
    check_merge_success,
)


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
        state: Optional[str] = None,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> bool:
        """
        Update pull request details.

        Note: GitHub API requires separate calls for PR fields vs labels.
        Labels are managed via the Issues API (PRs are a type of Issue).
        This method handles both atomically where possible.

        Args:
            pr_number: Pull request number
            title: New title
            body: New description
            state: New state (open/closed)
            add_labels: List of labels to add (optional)
            remove_labels: List of labels to remove (optional)

        Returns:
            True if all operations successful
        """
        async with GitHubTools() as gh:
            print(f"Updating PR #{pr_number}")
            
            # Determine what operations are needed
            needs_pr_update = title is not None or body is not None or state is not None
            needs_label_update = add_labels or remove_labels
            
            # Fetch PR details if we need labels or need to preserve title for label update
            pr_data = None
            if needs_label_update:
                pr_detail = await gh.pull_request_read(
                    owner=self.owner,
                    repo=self.repo,
                    pull_number=pr_number,
                    method="get"
                )
                pr_data = self._parse_result(pr_detail)
                
                if not isinstance(pr_data, dict):
                    print(f"✗ Failed to fetch PR #{pr_number} details")
                    return False
            
            # Calculate final labels if label update is needed
            final_labels = None
            if needs_label_update:
                existing_labels = [
                    l.get("name") if isinstance(l, dict) else str(l)
                    for l in pr_data.get("labels", [])
                ]
                
                # Add new labels
                if add_labels:
                    existing_labels = list(set(existing_labels + add_labels))
                    print(f"  Adding labels: {add_labels}")
                
                # Remove specified labels
                if remove_labels:
                    existing_labels = [l for l in existing_labels if l not in remove_labels]
                    print(f"  Removing labels: {remove_labels}")
                
                final_labels = existing_labels
            
            # Strategy: If only updating labels (no title/body/state), use issue_write alone
            # If updating PR fields + labels, we need two API calls (GitHub limitation)
            
            operations_performed = []
            
            # Update title/body/state if provided (use update_pull_request)
            if needs_pr_update:
                result = await gh.update_pull_request(
                    owner=self.owner,
                    repo=self.repo,
                    pull_number=pr_number,
                    title=title,
                    body=body,
                    state=state
                )
                if not self._check_success(result):
                    print(f"✗ Failed to update PR #{pr_number} title/body/state")
                    return False
                operations_performed.append("title/body/state")
            
            # Update labels if requested (use issue_write - GitHub treats PRs as Issues for labels)
            if final_labels is not None:
                # Get PR title: use new title if provided, otherwise use existing
                pr_title = title if title is not None else pr_data.get("title", "")
                if not pr_title:
                    print(f"✗ Cannot update labels: PR #{pr_number} has no title")
                    return False
                
                # Use issue_write for label operations (GitHub API requirement)
                result = await gh.issue_write(
                    owner=self.owner,
                    repo=self.repo,
                    title=pr_title,
                    issue_number=pr_number,
                    labels=final_labels,
                    method="update"
                )
                if not self._check_success(result):
                    print(f"✗ Failed to update PR #{pr_number} labels")
                    # Note: If PR update succeeded but label update failed, we have partial success
                    if operations_performed:
                        print(f"  Warning: PR fields were updated but labels failed")
                    return False
                operations_performed.append("labels")
            
            if operations_performed:
                print(f"✓ Successfully updated PR #{pr_number} ({', '.join(operations_performed)})")
            else:
                print(f"  No changes requested for PR #{pr_number}")
            return True

    def _parse_result(self, result: Any) -> Any:
        """Parse API result, handling MCP response format"""
        return parse_mcp_result(result)

    def _extract_pr_number(self, result: Any) -> int:
        """Extract PR number from API result"""
        return extract_pr_number(result)

    def _check_merge_success(self, result: Any) -> bool:
        """Check if merge was successful"""
        return check_merge_success(result)

    def _check_success(self, result: Any) -> bool:
        """Check if operation was successful, handling MCP response format"""
        return check_api_success(result)


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
    update_parser.add_argument("--add-labels", help="Comma-separated labels to add")
    update_parser.add_argument("--remove-labels", help="Comma-separated labels to remove")
    
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
            add_labels = [l.strip() for l in args.add_labels.split(",")] if args.add_labels else None
            remove_labels = [l.strip() for l in args.remove_labels.split(",")] if args.remove_labels else None
            success = await manager.update_pr(
                pr_number=args.number,
                title=args.title,
                body=args.body,
                state=args.state,
                add_labels=add_labels,
                remove_labels=remove_labels
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
