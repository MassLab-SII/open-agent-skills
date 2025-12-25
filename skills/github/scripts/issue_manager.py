#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Issue Manager Script
====================

Manage GitHub Issues lifecycle: create, update, close, reopen, list, and batch operations.
Now includes label management (add/remove labels) to enable atomic Issue + Label operations.

Usage:
    python issue_manager.py <command> <owner> <repo> [options]

Commands:
    create      Create a new issue
    update      Update an existing issue (title, body, state, labels)
    list        List issues with filters
    close       Batch close issues based on filters
    reopen      Batch reopen closed issues matching query

Examples:
    # Create a new issue
    python issue_manager.py create owner repo --title "Bug Report" --body "Description" --labels "bug"
    
    # Create issue with checklist
    python issue_manager.py create owner repo --title "Task" --body "Description" --checklist "item1,item2"
    
    # Update an issue
    python issue_manager.py update owner repo --number 42 --title "New Title"
    
    # Close an issue with reason AND add a label
    python issue_manager.py update owner repo --number 42 --state closed --state-reason completed --add-labels "wontfix"
    
    # Add labels to an existing issue
    python issue_manager.py update owner repo --number 42 --add-labels "bug,priority-high"
    
    # Remove labels from an issue
    python issue_manager.py update owner repo --number 42 --remove-labels "needs-triage"
    
    # Reopen a closed issue
    python issue_manager.py update owner repo --number 42 --state open --state-reason reopened
    
    # List open issues
    python issue_manager.py list owner repo --state open --labels "bug"
    
    # Batch close all issues with comments
    python issue_manager.py close owner repo --filter has_comments
    
    # Batch reopen issues matching query
    python issue_manager.py reopen owner repo --query "memory leak"
"""

import asyncio
import argparse
import json
import sys
from typing import List, Dict, Any, Optional

from utils import (
    GitHubTools,
    parse_mcp_result,
    parse_mcp_search_result,
    extract_issue_number,
    extract_issue_id,
    check_api_success,
)


class IssueManager:
    """Manage GitHub Issues with batch operations"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Issue Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def close_issues_with_comments(self) -> Dict[str, List[int]]:
        """
        Close all open issues that have at least one comment.

        Returns:
            Dict with 'closed' and 'failed' lists of issue numbers
        """
        async with GitHubTools() as gh:
            closed_issues = []
            failed_issues = []
            page = 1
            
            print(f"Fetching open issues from {self.owner}/{self.repo}...")
            
            while True:
                # Step 1: Get all open issues
                issues_result = await gh.list_issues(
                    owner=self.owner,
                    repo=self.repo,
                    state="open",
                    page=page,
                    per_page=100
                )
                
                issues = self._parse_result(issues_result)
                if not issues or not isinstance(issues, list):
                    break
                
                print(f"Processing page {page} ({len(issues)} issues)...")
                
                for issue in issues:
                    issue_number = issue.get("number")
                    if not issue_number:
                        continue
                    
                    # Step 2: Check if issue has comments
                    comments_count = issue.get("comments", 0)
                    
                    if comments_count > 0:
                        print(f"  Closing issue #{issue_number} ({comments_count} comments)")
                        
                        # Step 3: Close the issue and check result
                        result = await gh.issue_write(
                            owner=self.owner,
                            repo=self.repo,
                            title=issue.get("title", ""),
                            issue_number=issue_number,
                            state="closed",
                            method="update"
                        )
                        
                        if self._check_success(result):
                            closed_issues.append(issue_number)
                        else:
                            print(f"    ✗ Failed to close issue #{issue_number}")
                            failed_issues.append(issue_number)
                
                if len(issues) < 100:
                    break
                page += 1
            
            if failed_issues:
                print(f"Warning: Failed to close {len(failed_issues)} issues: {failed_issues}")
            
            return {"closed": closed_issues, "failed": failed_issues}

    async def reopen_issues(self, query: str) -> Dict[str, List[int]]:
        """
        Reopen closed issues matching query.

        Args:
            query: Search query (case-insensitive)

        Returns:
            Dict with 'reopened' and 'failed' lists of issue numbers
        """
        async with GitHubTools() as gh:
            reopened = []
            failed = []
            
            print(f"Searching for closed issues containing '{query}'...")
            
            # Step 1: Search closed issues
            search_query = f"{query} repo:{self.owner}/{self.repo} is:closed is:issue"
            
            search_result = await gh.search_issues(
                query=search_query,
                page=1,
                per_page=100
            )
            
            items = self._parse_search_result(search_result)
            
            if not items:
                print("No closed issues found matching the query.")
                return {"reopened": reopened, "failed": failed}
            
            print(f"Found {len(items)} closed issues to reopen")
            
            for item in items:
                issue_number = item.get("number")
                if not issue_number:
                    continue
                
                print(f"  Reopening issue #{issue_number}: {item.get('title', '')[:50]}")
                
                # Step 2: Reopen the issue
                result = await gh.issue_write(
                    owner=self.owner,
                    repo=self.repo,
                    title=item.get("title", ""),
                    issue_number=issue_number,
                    state="open",
                    method="update"
                )
                
                if self._check_success(result):
                    reopened.append(issue_number)
                else:
                    print(f"    ✗ Failed to reopen issue #{issue_number}")
                    failed.append(issue_number)
            
            if failed:
                print(f"Warning: Failed to reopen {len(failed)} issues: {failed}")
            
            return {"reopened": reopened, "failed": failed}

    async def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        checklist: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        parent_issue: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue, optionally as a sub-issue of a parent.

        Args:
            title: Issue title
            body: Issue body/description
            labels: List of labels
            checklist: List of checklist items
            assignees: List of assignees
            parent_issue: Parent issue number to link this as sub-issue (optional)

        Returns:
            Dict with 'number' (issue number) and 'id' (database ID)
        """
        async with GitHubTools() as gh:
            # Build body with checklist if provided
            full_body = body or ""
            
            if checklist:
                full_body += "\n\n## Checklist\n\n"
                full_body += "\n".join([f"- [ ] {item}" for item in checklist])
            
            print(f"Creating issue: {title}")
            
            result = await gh.issue_write(
                owner=self.owner,
                repo=self.repo,
                title=title,
                body=full_body,
                labels=labels,
                assignees=assignees,
                method="create"
            )
            
            issue_number = self._extract_issue_number(result)
            issue_id = self._extract_issue_id(result)
            
            # Debug: print raw result to understand the format
            print(f"  DEBUG: Raw result type: {type(result)}")
            print(f"  DEBUG: Raw result: {result[:200] if isinstance(result, str) else result}")
            
            print(f"Created issue #{issue_number} (ID: {issue_id})")
            
            # Link as sub-issue if parent specified
            if parent_issue and issue_id:
                await self.add_sub_issue(parent_issue, issue_id)
            
            return {"number": issue_number, "id": issue_id}

    async def add_sub_issue(self, parent_number: int, sub_issue_id: int) -> bool:
        """
        Link an issue as a sub-issue of a parent issue.

        Args:
            parent_number: Parent issue number
            sub_issue_id: Sub-issue database ID (not number)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"  Linking as sub-issue to #{parent_number}...")
            
            result = await gh.sub_issue_write(
                owner=self.owner,
                repo=self.repo,
                issue_number=parent_number,
                method="add",
                sub_issue_id=sub_issue_id
            )
            
            # Print raw response for debugging
            print(f"  API Response: {result}")
            
            # Use proper success check
            success = self._check_success(result)
            
            if success:
                print(f"  ✓ Successfully linked to parent issue #{parent_number}")
                return True
            else:
                print(f"  ✗ Failed to link sub-issue to #{parent_number}")
                return False

    async def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        state_reason: Optional[str] = None,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None
    ) -> bool:
        """
        Update an existing issue.

        Args:
            issue_number: Issue number to update
            title: New title (optional)
            body: New body (optional)
            state: New state - open/closed (optional)
            state_reason: Reason for state change - completed/not_planned/reopened (optional)
            add_labels: List of labels to add (optional)
            remove_labels: List of labels to remove (optional)
            assignees: List of assignees to set (optional)
            milestone: Milestone number (optional)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Updating issue #{issue_number}")
            
            # Get current issue details (needed for title preservation and existing labels)
            issue_detail = await gh.issue_read(
                owner=self.owner,
                repo=self.repo,
                issue_number=issue_number
            )
            issue_data = self._parse_result(issue_detail)
            
            if not isinstance(issue_data, dict):
                print(f"✗ Failed to fetch issue #{issue_number} details")
                return False
            
            # Get current title - use provided title or preserve existing
            current_title = title if title is not None else issue_data.get("title", "")
            if not current_title:
                print(f"✗ Cannot update issue #{issue_number}: no title available")
                return False
            
            # Handle label modifications
            final_labels = None
            if add_labels or remove_labels:
                existing_labels = [
                    l.get("name") if isinstance(l, dict) else str(l)
                    for l in issue_data.get("labels", [])
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
            
            result = await gh.issue_write(
                owner=self.owner,
                repo=self.repo,
                title=current_title,
                body=body,
                issue_number=issue_number,
                state=state,
                state_reason=state_reason,
                labels=final_labels,
                assignees=assignees,
                milestone=milestone,
                method="update"
            )
            
            success = self._check_success(result)
            
            if success:
                action = f"closed ({state_reason})" if state == "closed" else "updated"
                print(f"✓ Issue #{issue_number} {action}")
            else:
                print(f"✗ Failed to update issue #{issue_number}")
            
            return success


    def _check_success(self, result: Any) -> bool:
        """Check if operation was successful"""
        return check_api_success(result)

    async def list_issues(
        self,
        state: str = "open",
        labels: Optional[List[str]] = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List issues with filters.

        Args:
            state: Issue state (open/closed/all)
            labels: Filter by labels
            limit: Maximum results

        Returns:
            List of issue dicts
        """
        async with GitHubTools() as gh:
            print(f"Listing {state} issues...")
            
            result = await gh.list_issues(
                owner=self.owner,
                repo=self.repo,
                state=state,
                labels=labels,
                page=1,
                per_page=limit
            )
            
            issues = self._parse_result(result)
            return issues[:limit] if isinstance(issues, list) else []

    def _parse_result(self, result: Any) -> Any:
        """Parse API result, handling MCP response format"""
        return parse_mcp_result(result)

    def _parse_search_result(self, result: Any) -> List[Dict[str, Any]]:
        """Parse search API result, handling MCP response format"""
        return parse_mcp_search_result(result)

    def _extract_issue_number(self, result: Any) -> int:
        """Extract issue number from API result"""
        return extract_issue_number(result)

    def _extract_issue_id(self, result: Any) -> int:
        """Extract issue database ID from API result"""
        return extract_issue_id(result)

    def print_results(self, issues: List[Dict[str, Any]]):
        """Pretty print issue list"""
        if not issues:
            print("\nNo issues found.")
            return

        print(f"\n{'#':<6} | {'State':<8} | {'Title':<50} | {'Labels'}")
        print("-" * 100)
        
        for issue in issues:
            number = issue.get("number", "")
            state = issue.get("state", "")
            title = issue.get("title", "")[:50]
            labels = ", ".join([l.get("name", "") if isinstance(l, dict) else str(l) 
                               for l in issue.get("labels", [])])[:30]
            
            state_icon = "🟢" if state == "open" else "🟣"
            print(f"{state_icon} {number:<4} | {state:<8} | {title:<50} | {labels}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Batch manage GitHub Issues',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a new issue
  python issue_manager.py create owner repo --title "Bug Report" --body "Description"
  
  # Update an issue
  python issue_manager.py update owner repo --number 42 --title "New Title"
  
  # Close an issue
  python issue_manager.py update owner repo --number 42 --state closed --state-reason completed
  
  # List issues
  python issue_manager.py list owner repo --state open --labels "bug"
  
  # Batch close issues with comments
  python issue_manager.py close owner repo --filter has_comments
  
  # Batch reopen issues
  python issue_manager.py reopen owner repo --query "memory leak"

Note: For labels use label_manager.py, for comments use comment_manager.py
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: close
    close_parser = subparsers.add_parser("close", help="Close issues")
    close_parser.add_argument("owner", help="Repository owner")
    close_parser.add_argument("repo", help="Repository name")
    close_parser.add_argument("--filter", choices=["has_comments"], 
                             default="has_comments", help="Filter criteria")
    
    # Command: reopen
    reopen_parser = subparsers.add_parser("reopen", help="Batch reopen closed issues")
    reopen_parser.add_argument("owner", help="Repository owner")
    reopen_parser.add_argument("repo", help="Repository name")
    reopen_parser.add_argument("--query", required=True, help="Search query")
    
    # Command: create
    create_parser = subparsers.add_parser("create", help="Create a new issue")
    create_parser.add_argument("owner", help="Repository owner")
    create_parser.add_argument("repo", help="Repository name")
    create_parser.add_argument("--title", required=True, help="Issue title")
    create_parser.add_argument("--body", help="Issue body")
    create_parser.add_argument("--labels", help="Comma-separated labels")
    create_parser.add_argument("--checklist", help="Comma-separated checklist items")
    create_parser.add_argument("--assignees", help="Comma-separated assignees")
    create_parser.add_argument("--parent", type=int, help="Parent issue number to link as sub-issue")
    
    # Command: list
    list_parser = subparsers.add_parser("list", help="List issues")
    list_parser.add_argument("owner", help="Repository owner")
    list_parser.add_argument("repo", help="Repository name")
    list_parser.add_argument("--state", choices=["open", "closed", "all"], 
                            default="open", help="Issue state")
    list_parser.add_argument("--labels", help="Comma-separated labels")
    list_parser.add_argument("--limit", type=int, default=30, help="Max results")
    
    # Command: update
    update_parser = subparsers.add_parser("update", help="Update an existing issue")
    update_parser.add_argument("owner", help="Repository owner")
    update_parser.add_argument("repo", help="Repository name")
    update_parser.add_argument("--number", type=int, required=True, help="Issue number")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--body", help="New body")
    update_parser.add_argument("--state", choices=["open", "closed"], help="New state")
    update_parser.add_argument("--state-reason", dest="state_reason",
                              choices=["completed", "not_planned", "reopened"],
                              help="Reason for state change")
    update_parser.add_argument("--add-labels", help="Comma-separated labels to add")
    update_parser.add_argument("--remove-labels", help="Comma-separated labels to remove")
    update_parser.add_argument("--assignees", help="Comma-separated assignees to set")
    update_parser.add_argument("--milestone", type=int, help="Milestone number")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = IssueManager(args.owner, args.repo)
    
    try:
        if args.command == "close":
            result = await manager.close_issues_with_comments()
            closed = result["closed"]
            failed = result["failed"]
            print(f"\n✓ Closed {len(closed)} issues: {closed}")
            if failed:
                print(f"✗ Failed to close {len(failed)} issues: {failed}")
                sys.exit(1)
            
        elif args.command == "reopen":
            result = await manager.reopen_issues(args.query)
            reopened = result["reopened"]
            failed = result["failed"]
            print(f"\n✓ Reopened {len(reopened)} issues: {reopened}")
            if failed:
                print(f"✗ Failed to reopen {len(failed)} issues: {failed}")
                sys.exit(1)
            
        elif args.command == "create":
            labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
            checklist = [c.strip() for c in args.checklist.split(",")] if args.checklist else None
            assignees = [a.strip() for a in args.assignees.split(",")] if args.assignees else None
            
            result = await manager.create_issue(
                title=args.title,
                body=args.body,
                labels=labels,
                checklist=checklist,
                assignees=assignees,
                parent_issue=args.parent
            )
            issue_number = result["number"]
            issue_id = result["id"]
            print(f"\n✓ Created issue #{issue_number} (ID: {issue_id})")
            if args.parent:
                if issue_id and issue_id > 0:
                    print(f"  Linked as sub-issue to #{args.parent}")
                else:
                    print(f"  ⚠ Warning: Could not link as sub-issue (ID extraction failed)")
            
        elif args.command == "list":
            labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
            issues = await manager.list_issues(
                state=args.state,
                labels=labels,
                limit=args.limit
            )
            manager.print_results(issues)
            
        elif args.command == "update":
            add_labels = [l.strip() for l in args.add_labels.split(",")] if args.add_labels else None
            remove_labels = [l.strip() for l in args.remove_labels.split(",")] if args.remove_labels else None
            assignees = [a.strip() for a in args.assignees.split(",")] if args.assignees else None
            
            success = await manager.update_issue(
                issue_number=args.number,
                title=args.title,
                body=args.body,
                state=args.state,
                state_reason=args.state_reason,
                add_labels=add_labels,
                remove_labels=remove_labels,
                assignees=assignees,
                milestone=args.milestone
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
