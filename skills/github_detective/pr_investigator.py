#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PR Investigator Script
======================

Search and analyze Pull Requests in a GitHub repository.
When viewing a specific PR, shows all commits with their full SHAs.

Usage:
    python pr_investigator.py <owner> <repo> [--query <text>] [--state open|closed|all] [--number N]

Examples:
    # List recent PRs
    python pr_investigator.py enigma mcpmark
    
    # Search PRs containing "RAG"
    python pr_investigator.py enigma mcpmark --query "RAG"
    
    # Get specific PR details (shows all commits in the PR)
    python pr_investigator.py enigma mcpmark --number 42
    
    # Filter by state
    python pr_investigator.py owner repo --state closed
"""

import asyncio
import argparse
import json
from typing import List, Dict, Any, Optional

from utils import GitHubTools


class PRInvestigator:
    """Investigate Pull Requests in a repository"""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def search_prs(
        self, 
        query: Optional[str] = None,
        state: str = "all",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for Pull Requests.

        Args:
            query: Optional search query
            state: PR state (open/closed/all)
            limit: Maximum results

        Returns:
            List of PR info dicts
        """
        async with GitHubTools() as gh:
            results = []
            
            if query:
                # Use search API for query-based search
                full_query = f"{query} repo:{self.owner}/{self.repo}"
                if state != "all":
                    full_query += f" is:{state}"
                
                print(f"Searching PRs for: {query}")
                
                search_result = await gh.search_pull_requests(
                    query=full_query,
                    page=1,
                    per_page=min(limit, 100)
                )
                
                items = self._parse_search_result(search_result)
                results = items[:limit]
            else:
                # Use list API for recent PRs
                print(f"Listing {state} PRs...")
                
                prs = await gh.list_pull_requests(
                    owner=self.owner,
                    repo=self.repo,
                    state=state if state != "all" else "open",
                    page=1,
                    per_page=min(limit, 100)
                )
                
                results = self._parse_result(prs)[:limit]
            
            return results

    async def get_pr_details(self, pr_number: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific PR, including all commits.

        Args:
            pr_number: Pull request number

        Returns:
            PR details including commits list
        """
        async with GitHubTools() as gh:
            # Get PR details
            pr = await gh.pull_request_read(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                method="get"
            )
            
            # Parse PR response
            if isinstance(pr, str):
                try:
                    pr = json.loads(pr)
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse PR response: {pr[:200]}...")
                    return {}
            
            if not isinstance(pr, dict) or pr.get('isError'):
                if isinstance(pr, dict):
                    print(f"API Error: {pr.get('content', [{}])[0].get('text', 'Unknown error')}")
                return {}
            
            # Fetch commits list using head branch ref
            # This is the key: use list_commits with the head branch name
            head_ref = pr.get('head', {}).get('ref', '')
            if head_ref:
                commits_result = await gh.list_commits(
                    owner=self.owner,
                    repo=self.repo,
                    sha=head_ref,
                    page=1,
                    per_page=100
                )
                
                # Parse commits
                if isinstance(commits_result, str):
                    try:
                        commits_result = json.loads(commits_result)
                    except:
                        commits_result = []
                
                if isinstance(commits_result, list):
                    pr['_commits_list'] = commits_result
                else:
                    pr['_commits_list'] = []
            else:
                pr['_commits_list'] = []
            
            return pr

    async def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get list of files changed in a specific PR.

        Args:
            pr_number: Pull request number

        Returns:
            List of file change info dicts
        """
        async with GitHubTools() as gh:
            result = await gh.pull_request_read(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                method="get_files",
                per_page=100
            )
            
            # Parse result
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    return []
            
            if isinstance(result, list):
                return result
            return []

    def _parse_search_result(self, result: Any) -> List[Dict[str, Any]]:
        """Parse search API result, handling MCP response format"""
        # Handle MCP format: {'content': [{'type': 'text', 'text': '...'}]}
        if isinstance(result, dict):
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return parsed.get('items', [])
                        except json.JSONDecodeError:
                            pass
            # Direct dict with items
            return result.get('items', [])
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return parsed.get('items', []) if isinstance(parsed, dict) else []
            except json.JSONDecodeError:
                return []
        return []

    def _parse_result(self, result: Any) -> Any:
        """Parse general API result, handling MCP response format"""
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
                return []
        return []

    def print_results(self, prs: List[Dict[str, Any]]):
        """Pretty print PR list"""
        if not prs:
            print("\nNo Pull Requests found.")
            return

        print(f"\n{'#':<6} | {'State':<8} | {'Title':<45} | {'Author'}")
        print("-" * 90)
        
        for pr in prs:
            number = pr.get('number', '')
            state = pr.get('state', '')
            title = pr.get('title', '')[:45]
            author = pr.get('user', {}).get('login', '') if isinstance(pr.get('user'), dict) else ''
            
            state_icon = "🟢" if state == "open" else "🟣"
            print(f"{state_icon} {number:<4} | {state:<8} | {title:<45} | {author}")

    def print_pr_detail(self, pr: Dict[str, Any]):
        """Pretty print PR details including all commits"""
        if not pr:
            print("\nPR not found.")
            return

        print("\n" + "=" * 70)
        print(f"PR #{pr.get('number', '')}: {pr.get('title', '')}")
        print("=" * 70)
        print(f"State:    {pr.get('state', '')}")
        print(f"Author:   {pr.get('user', {}).get('login', '')}")
        
        # Show branch info
        base_ref = pr.get('base', {}).get('ref', '')
        head_ref = pr.get('head', {}).get('ref', '')
        head_sha = pr.get('head', {}).get('sha', '')
        print(f"Base:     {base_ref}")
        print(f"Head:     {head_ref}")
        if head_sha:
            print(f"Head SHA: {head_sha}")
        
        print(f"Created:  {pr.get('created_at', '')[:19].replace('T', ' ')}")
        print(f"Modified: {pr.get('updated_at', '')[:19].replace('T', ' ')}")
        
        # Show all commits in this PR (critical for finding the right SHA)
        commits_list = pr.get('_commits_list', [])
        if commits_list:
            print(f"\n--- Commits in this PR ({len(commits_list)}) ---")
            for c in commits_list:
                sha = c.get('sha', '')[:7]
                full_sha = c.get('sha', '')
                commit_info = c.get('commit', {})
                msg = commit_info.get('message', '').split('\n')[0][:50]
                author = commit_info.get('author', {}).get('name', '')[:15]
                print(f"  {sha} | {author:<15} | {msg}")
                print(f"         Full SHA: {full_sha}")
        
        if pr.get('body'):
            print(f"\nDescription:\n{pr.get('body', '')[:300]}")


async def main():
    parser = argparse.ArgumentParser(
        description='Investigate Pull Requests in a repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List recent PRs
  python pr_investigator.py owner repo
  
  # Search PRs
  python pr_investigator.py owner repo --query "fix bug"
  
  # Get specific PR details (shows all commits)
  python pr_investigator.py owner repo --number 42
  
  # Also show files changed in the PR
  python pr_investigator.py owner repo --number 42 --show-files
        """
    )
    
    parser.add_argument('owner', help='Repository owner')
    parser.add_argument('repo', help='Repository name')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--state', choices=['open', 'closed', 'all'], 
                        default='all', help='PR state filter')
    parser.add_argument('--number', type=int, help='Specific PR number to inspect')
    parser.add_argument('--show-files', action='store_true', help='Show files changed in the PR')
    parser.add_argument('--limit', type=int, default=20, help='Max results')

    args = parser.parse_args()
    
    investigator = PRInvestigator(args.owner, args.repo)
    
    try:
        if args.number:
            # Get specific PR details
            pr = await investigator.get_pr_details(args.number)
            investigator.print_pr_detail(pr)
            
            # Optionally show files changed
            if args.show_files:
                files = await investigator.get_pr_files(args.number)
                if files:
                    print(f"\n--- Files changed in PR #{args.number} ({len(files)}) ---")
                    for f in files:
                        status = f.get('status', '')[:8]
                        filename = f.get('filename', '')
                        additions = f.get('additions', 0)
                        deletions = f.get('deletions', 0)
                        print(f"  [{status:<8}] {filename} (+{additions}/-{deletions})")
                else:
                    print("\nNo files found or error fetching files.")
        else:
            # Search/list PRs
            prs = await investigator.search_prs(
                query=args.query,
                state=args.state,
                limit=args.limit
            )
            investigator.print_results(prs)
    except Exception as e:
        print(f"\nError investigating PRs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
