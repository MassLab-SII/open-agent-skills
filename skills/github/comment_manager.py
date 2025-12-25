#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comment Manager Script
======================

Manage comments on GitHub Issues and Pull Requests.
Supports adding regular comments and PR review comments.

Usage:
    python comment_manager.py <command> <owner> <repo> [options]

Commands:
    add         Add a comment to an issue or PR
    review      Submit a PR review (COMMENT/APPROVE/REQUEST_CHANGES)

Examples:
    # Add comment to an issue
    python comment_manager.py add owner repo --issue 42 --body "Thanks for reporting!"
    
    # Add comment to a PR
    python comment_manager.py add owner repo --pr 42 --body "LGTM!"
    
    # Approve a PR with comment
    python comment_manager.py review owner repo --pr 42 --body "Great work!" --event APPROVE
    
    # Request changes on a PR
    python comment_manager.py review owner repo --pr 42 --body "Please fix..." --event REQUEST_CHANGES
"""

import asyncio
import argparse
import sys
from typing import Any

from utils import (
    GitHubTools,
    check_api_success,
)


class CommentManager:
    """Manage comments on Issues and Pull Requests"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Comment Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def add_comment(
        self,
        number: int,
        body: str,
        is_pr: bool = False
    ) -> bool:
        """
        Add a comment to an issue or pull request.

        Args:
            number: Issue or PR number
            body: Comment text
            is_pr: True if target is a PR (uses same API)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            target_type = "PR" if is_pr else "issue"
            print(f"Adding comment to {target_type} #{number}")
            
            result = await gh.add_issue_comment(
                owner=self.owner,
                repo=self.repo,
                issue_number=number,
                body=body
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Comment added to {target_type} #{number}")
            else:
                print(f"✗ Failed to add comment: {result}")
            
            return success

    async def add_review(
        self,
        pr_number: int,
        body: str,
        event: str = "COMMENT"
    ) -> bool:
        """
        Submit a review on a pull request.

        Args:
            pr_number: Pull request number
            body: Review comment text
            event: Review event (COMMENT/APPROVE/REQUEST_CHANGES)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Submitting review on PR #{pr_number} (event: {event})")
            
            result = await gh.pull_request_review_write(
                owner=self.owner,
                repo=self.repo,
                pullNumber=pr_number,
                method="create",
                event=event,
                body=body
            )
            
            success = self._check_success(result)
            
            if success:
                event_msg = {
                    "COMMENT": "commented on",
                    "APPROVE": "approved",
                    "REQUEST_CHANGES": "requested changes on"
                }.get(event, "reviewed")
                print(f"✓ Successfully {event_msg} PR #{pr_number}")
            else:
                print(f"✗ Failed to submit review: {result}")
            
            return success

    def _check_success(self, result: Any) -> bool:
        """Check if operation was successful"""
        return check_api_success(result)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage comments on Issues and Pull Requests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add comment to an issue
  python comment_manager.py add owner repo --issue 42 --body "Thanks for reporting!"
  
  # Add comment to a PR
  python comment_manager.py add owner repo --pr 42 --body "LGTM!"
  
  # Approve a PR
  python comment_manager.py review owner repo --pr 42 --body "Great work!" --event APPROVE
  
  # Request changes
  python comment_manager.py review owner repo --pr 42 --body "Please fix..." --event REQUEST_CHANGES
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: add
    add_parser = subparsers.add_parser("add", help="Add a comment to issue or PR")
    add_parser.add_argument("owner", help="Repository owner")
    add_parser.add_argument("repo", help="Repository name")
    add_parser.add_argument("--issue", type=int, help="Issue number")
    add_parser.add_argument("--pr", type=int, help="Pull request number")
    add_parser.add_argument("--body", required=True, help="Comment text")
    
    # Command: review
    review_parser = subparsers.add_parser("review", help="Submit a PR review")
    review_parser.add_argument("owner", help="Repository owner")
    review_parser.add_argument("repo", help="Repository name")
    review_parser.add_argument("--pr", type=int, required=True, help="Pull request number")
    review_parser.add_argument("--body", required=True, help="Review comment text")
    review_parser.add_argument("--event", 
                               choices=["COMMENT", "APPROVE", "REQUEST_CHANGES"],
                               default="COMMENT",
                               help="Review event type (default: COMMENT)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = CommentManager(args.owner, args.repo)
    
    try:
        if args.command == "add":
            if args.issue:
                success = await manager.add_comment(args.issue, args.body, is_pr=False)
            elif args.pr:
                success = await manager.add_comment(args.pr, args.body, is_pr=True)
            else:
                print("Error: Must specify either --issue or --pr")
                sys.exit(1)
            
            sys.exit(0 if success else 1)
            
        elif args.command == "review":
            success = await manager.add_review(
                pr_number=args.pr,
                body=args.body,
                event=args.event
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
