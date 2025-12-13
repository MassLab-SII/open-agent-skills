#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Commit Finder Script
====================

Search for commits by message content, author, date range, or file path.
Uses only list_commits API for fast message-based searching (no diff search).

For searching code CONTENT (not commit messages), use content_tracker.py instead.

Usage:
    python commit_finder.py <owner> <repo> [--query <regex>] [--author <name>] 
                            [--path <file>] [--since <date>] [--until <date>] [--limit N]

Examples:
    # Find commits with "fix" in the message
    python commit_finder.py enigma mcpmark --query "fix"
    
    # Find commits by author affecting a specific file
    python commit_finder.py enigma mcpmark --author "Daniel" --path "src/main.py"
    
    # Limit results
    python commit_finder.py owner repo --query "bug" --limit 10
"""

import asyncio
import argparse
import re
import json
from typing import List, Dict, Any, Optional

from utils import GitHubTools


class CommitFinder:
    """Fast commit search using list_commits API"""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def find_commits(
        self, 
        query: Optional[str] = None,
        author: Optional[str] = None,
        path: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find commits matching criteria.

        Args:
            query: Regex to match in commit messages
            author: Filter by author name
            path: Filter by file path
            since: ISO date to start from
            until: ISO date to end at
            limit: Maximum results

        Returns:
            List of matching commits
        """
        async with GitHubTools() as gh:
            all_commits = []
            page = 1
            per_page = 100
            max_pages = 5  # Safety limit
            
            print(f"Searching commits in {self.owner}/{self.repo}...")
            
            while len(all_commits) < limit and page <= max_pages:
                result = await gh.list_commits(
                    owner=self.owner,
                    repo=self.repo,
                    author=author,
                    path=path,
                    since=since,
                    until=until,
                    page=page,
                    per_page=per_page
                )
                
                batch = self._parse_result(result)
                if not batch:
                    break
                
                # Filter by message query if specified
                for commit in batch:
                    if len(all_commits) >= limit:
                        break
                    if self._matches_query(commit, query):
                        all_commits.append(commit)
                
                if len(batch) < per_page:
                    break
                page += 1
            
            return all_commits

    def _parse_result(self, result: Any) -> List[Dict[str, Any]]:
        """Parse API result"""
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return []
        return []

    def _matches_query(self, commit: Dict[str, Any], query: Optional[str]) -> bool:
        """Check if commit message matches query"""
        if not query:
            return True
        
        message = commit.get('commit', {}).get('message', '')
        try:
            return bool(re.search(query, message, re.IGNORECASE))
        except re.error:
            return query.lower() in message.lower()

    def print_results(self, commits: List[Dict[str, Any]]):
        """Pretty print commits"""
        if not commits:
            print("\nNo commits found matching criteria.")
            return

        print(f"\nFound {len(commits)} commits:\n")
        print(f"{'SHA':<9} | {'Date':<20} | {'Author':<15} | {'Message'}")
        print("-" * 80)
        
        for c in commits:
            sha = c.get('sha', '')[:7]
            commit_info = c.get('commit', {})
            author_info = commit_info.get('author', {})
            
            author = author_info.get('name', 'Unknown')[:15]
            date = author_info.get('date', '')[:19].replace('T', ' ')
            msg = commit_info.get('message', '').split('\n')[0][:45]
            
            print(f"{sha:<9} | {date:<20} | {author:<15} | {msg}")


async def main():
    parser = argparse.ArgumentParser(
        description='Fast commit search by message, author, path, or date',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search by message
  python commit_finder.py owner repo --query "fix"
  
  # Search by author and path
  python commit_finder.py owner repo --author "Daniel" --path "src/main.py"
  
  # Search by date range
  python commit_finder.py owner repo --since "2024-01-01" --until "2024-06-01"
  
  # Limit results
  python commit_finder.py owner repo --query "bug" --limit 10
  
NOTE: To search for code CONTENT (not commit messages), use content_tracker.py
        """
    )
    
    parser.add_argument('owner', help='Repository owner')
    parser.add_argument('repo', help='Repository name')
    parser.add_argument('--query', help='Regex to search in commit messages')
    parser.add_argument('--author', help='Filter by author')
    parser.add_argument('--path', help='Filter by file path')
    parser.add_argument('--since', help='Start date (ISO format)')
    parser.add_argument('--until', help='End date (ISO format)')
    parser.add_argument('--limit', type=int, default=20, help='Max results')

    args = parser.parse_args()
    
    finder = CommitFinder(args.owner, args.repo)
    
    try:
        commits = await finder.find_commits(
            query=args.query,
            author=args.author,
            path=args.path,
            since=args.since,
            until=args.until,
            limit=args.limit
        )
        finder.print_results(commits)
    except Exception as e:
        print(f"\nError searching commits: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
