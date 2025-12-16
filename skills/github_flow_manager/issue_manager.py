#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Issue Manager Script
====================

Manage GitHub Issues lifecycle: create, update, close, reopen, list, and batch operations.

Note: For adding labels to issues, use label_manager.py instead.
Note: For adding comments to issues, use comment_manager.py instead.

Usage:
    python issue_manager.py <command> <owner> <repo> [options]

Commands:
    create      Create a new issue
    update      Update an existing issue (title, body, state)
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
    
    # Close an issue with reason
    python issue_manager.py update owner repo --number 42 --state closed --state-reason completed
    
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

from utils import GitHubTools


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

    async def close_issues_with_comments(self) -> List[int]:
        """
        Close all open issues that have at least one comment.

        Returns:
            List of closed issue numbers
        """
        async with GitHubTools() as gh:
            closed_issues = []
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
                if not issues:
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
                        
                        # Step 3: Close the issue
                        await gh.issue_write(
                            owner=self.owner,
                            repo=self.repo,
                            title=issue.get("title", ""),
                            issue_number=issue_number,
                            state="closed",
                            method="update"
                        )
                        closed_issues.append(issue_number)
                
                if len(issues) < 100:
                    break
                page += 1
            
            return closed_issues

    async def reopen_issues(self, query: str) -> List[int]:
        """
        Reopen closed issues matching query.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of reopened issue numbers
        """
        async with GitHubTools() as gh:
            reopened = []
            
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
                return reopened
            
            print(f"Found {len(items)} closed issues to reopen")
            
            for item in items:
                issue_number = item.get("number")
                if not issue_number:
                    continue
                
                print(f"  Reopening issue #{issue_number}: {item.get('title', '')[:50]}")
                
                # Step 2: Reopen the issue
                await gh.issue_write(
                    owner=self.owner,
                    repo=self.repo,
                    title=item.get("title", ""),
                    issue_number=issue_number,
                    state="open",
                    method="update"
                )
                reopened.append(issue_number)
            
            return reopened

    async def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        checklist: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> int:
        """
        Create a new issue.

        Args:
            title: Issue title
            body: Issue body/description
            labels: List of labels
            checklist: List of checklist items
            assignees: List of assignees

        Returns:
            Created issue number
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
            print(f"Created issue #{issue_number}")
            
            return issue_number

    async def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
        state_reason: Optional[str] = None
    ) -> bool:
        """
        Update an existing issue.

        Args:
            issue_number: Issue number to update
            title: New title (optional)
            body: New body (optional)
            state: New state - open/closed (optional)
            state_reason: Reason for state change - completed/not_planned/reopened (optional)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Updating issue #{issue_number}")
            
            # Get current issue details if we need the title
            current_title = title
            if not current_title:
                issue_detail = await gh.issue_read(
                    owner=self.owner,
                    repo=self.repo,
                    issue_number=issue_number
                )
                issue_data = self._parse_result(issue_detail)
                if isinstance(issue_data, dict):
                    current_title = issue_data.get("title", "")
            
            result = await gh.issue_write(
                owner=self.owner,
                repo=self.repo,
                title=current_title or "",
                body=body,
                issue_number=issue_number,
                state=state,
                state_reason=state_reason,
                method="update"
            )
            
            success = self._check_success(result)
            
            if success:
                action = f"closed ({state_reason})" if state == "closed" else f"updated"
                print(f"✓ Issue #{issue_number} {action}")
            else:
                print(f"✗ Failed to update issue #{issue_number}")
            
            return success

    def _check_success(self, result: Any) -> bool:
        """Check if operation was successful"""
        if not result:
            return False
        if isinstance(result, dict):
            # Check for MCP format
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        if "error" in text.lower():
                            return False
                        return True
            if "error" in result or result.get("isError"):
                return False
            return True
        if isinstance(result, str):
            return "error" not in result.lower()
        return True

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
        # MCP format: {'content': [{'type': 'text', 'text': 'JSON_STRING'}]}
        if isinstance(result, dict):
            # Check for MCP format first
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            continue
            # Direct dict (not MCP format)
            return result
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return []
        return []

    def _parse_search_result(self, result: Any) -> List[Dict[str, Any]]:
        """Parse search API result, handling MCP response format"""
        def extract_items(data: dict) -> List[Dict[str, Any]]:
            """Extract items from parsed data"""
            return data.get("items", [])
        
        # MCP format: {'content': [{'type': 'text', 'text': 'JSON_STRING'}]}
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
                                return extract_items(parsed)
                        except json.JSONDecodeError:
                            continue
            # Direct dict (not MCP format)
            return extract_items(result)
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return extract_items(parsed) if isinstance(parsed, dict) else []
            except json.JSONDecodeError:
                return []
        return []

    def _extract_issue_number(self, result: Any) -> int:
        """Extract issue number from API result"""
        import re
        
        def extract_from_data(data: dict) -> int:
            """Extract issue number from parsed data dict"""
            # Direct number field
            if "number" in data:
                return data.get("number", 0)
            # Extract from URL: https://github.com/owner/repo/issues/52
            url = data.get("url", "") or data.get("html_url", "")
            if url:
                match = re.search(r'/issues/(\d+)', url)
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
                            match = re.search(r'/issues/(\d+)', text)
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
            match = re.search(r'/issues/(\d+)', result)
            if match:
                return int(match.group(1))
        return 0

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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = IssueManager(args.owner, args.repo)
    
    try:
        if args.command == "close":
            closed = await manager.close_issues_with_comments()
            print(f"\n✓ Closed {len(closed)} issues: {closed}")
            
        elif args.command == "reopen":
            reopened = await manager.reopen_issues(args.query)
            print(f"\n✓ Reopened {len(reopened)} issues: {reopened}")
            
        elif args.command == "create":
            labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
            checklist = [c.strip() for c in args.checklist.split(",")] if args.checklist else None
            assignees = [a.strip() for a in args.assignees.split(",")] if args.assignees else None
            
            issue_number = await manager.create_issue(
                title=args.title,
                body=args.body,
                labels=labels,
                checklist=checklist,
                assignees=assignees
            )
            print(f"\n✓ Created issue #{issue_number}")
            
        elif args.command == "list":
            labels = [l.strip() for l in args.labels.split(",")] if args.labels else None
            issues = await manager.list_issues(
                state=args.state,
                labels=labels,
                limit=args.limit
            )
            manager.print_results(issues)
            
        elif args.command == "update":
            success = await manager.update_issue(
                issue_number=args.number,
                title=args.title,
                body=args.body,
                state=args.state,
                state_reason=args.state_reason
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
