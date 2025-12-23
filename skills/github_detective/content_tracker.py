#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Tracker Script
======================

Find which commit introduced specific content to a file.

Uses a smart approach:
1. search_code - Find files containing the content (if --file not specified)
2. list_commits - Get history of those files  
3. get_commit - Check diffs to find the introducing commit

Usage:
    python content_tracker.py <owner> <repo> --content <text> [--file <path>] [--max-commits N]

Examples:
    # Search within a specific file (recommended for faster results)
    python content_tracker.py enigma repo --content "def main" --file "src/app.py"
    
    # Search on a specific branch
    python content_tracker.py owner repo --content "text" --file "README.md" --branch feature/new
    
    # Find which branches contain specific content
    python content_tracker.py owner repo --content "TODO" --file "README.md" --find-branches
    
    # Increase search depth for older commits
    python content_tracker.py owner repo --content "old text" --file "README.md" --max-commits 10
"""

import asyncio
import argparse
import json
import re
from typing import List, Dict, Any, Optional

from utils import GitHubTools


class ContentTracker:
    """Track which commit introduced specific content"""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def find_introducing_commit(
        self, 
        content: str, 
        file_path: Optional[str] = None,
        branch: Optional[str] = None,
        max_commits: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Find the commit that introduced specific content.

        Args:
            content: Text content to search for
            file_path: Optional specific file to search in
            branch: Branch name to search (default: repository default branch)
            max_commits: Maximum commits to scan

        Returns:
            Commit info dict or None if not found
        """
        async with GitHubTools() as gh:
            # Determine branch to search
            if branch:
                branches_to_search = [branch]
            else:
                branches_to_search = [None]  # Use default branch
            
            target_files = []
            
            # Step 1: Determine which file(s) to search
            if not file_path:
                print(f"⚠️ Warning: --file not specified. Attempting search_code but it may not work on new/private repos.")
                print(f"Step 1: Searching for files containing '{content[:50]}...'")
                full_query = f"{content} repo:{self.owner}/{self.repo}"
                
                search_result = await gh.search_code(
                    query=full_query,
                    page=1,
                    per_page=10
                )
                
                items = self._parse_search_result(search_result)
                if not items:
                    print("  ❌ No files found. This is expected for new/private repos.")
                    print("  💡 Tip: Use --file parameter to specify the file path directly.")
                    print("  Example: python content_tracker.py owner repo --content \"text\" --file \"README.md\"")
                    return None
                
                target_files = [item.get('path') for item in items if item.get('path')]
                print(f"  Found in {len(target_files)} files: {', '.join(target_files[:3])}...")
            else:
                target_files = [file_path]
                print(f"Step 1: Using specified file: {file_path}")
            
            # Step 2 & 3: Search across branches (only branches that contain the content)
            for branch_name in branches_to_search:
                branch_display = branch_name or "default branch"
                
                for fp in target_files:
                    print(f"\nStep 2: Getting commit history for {fp} on '{branch_display}'")
                    
                    commits_result = await gh.list_commits(
                        owner=self.owner,
                        repo=self.repo,
                        sha=branch_name,
                        path=fp,
                        page=1,
                        per_page=min(max_commits, 100)
                    )
                    
                    commits = self._parse_result(commits_result)
                    if not commits:
                        print(f"  No commits found for {fp}")
                        continue
                    
                    print(f"  Found {len(commits)} commits, checking diffs...")
                    
                    # Step 3: Check each commit's diff for the content
                    for i, commit in enumerate(commits):
                        sha = commit.get('sha')
                        if not sha:
                            continue
                        
                        if (i + 1) % 10 == 0:
                            print(f"  Checked {i + 1}/{len(commits)} commits...")
                        
                        try:
                            commit_detail = await gh.get_commit(
                                owner=self.owner,
                                repo=self.repo,
                                sha=sha
                            )
                            
                            detail = self._parse_result(commit_detail)
                            if isinstance(detail, dict):
                                files = detail.get('files', [])
                                for f in files:
                                    if f.get('filename') == fp:
                                        patch = f.get('patch', '')
                                        if self._content_added_in_patch(content, patch):
                                            print(f"\n✓ Found! Content was added in commit {sha[:7]} on branch '{branch_display}'")
                                            return {
                                                'sha': sha,
                                                'message': commit.get('commit', {}).get('message', ''),
                                                'author': commit.get('commit', {}).get('author', {}).get('name', ''),
                                                'date': commit.get('commit', {}).get('author', {}).get('date', ''),
                                                'file': fp,
                                                'branch': branch_name or 'default'
                                            }
                        except Exception as e:
                            print(f"  Warning: Error checking commit {sha[:7]}: {e}")
                            continue
                
            print("\nContent not found in searched commits.")
            return None

    async def find_content_in_branches(
        self,
        content: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Find which branches contain specific content in a file.
        Useful for locating content that might be in PR/feature branches.

        Args:
            content: Text content to search for
            file_path: File path to check

        Returns:
            List of branches containing the content
        """
        async with GitHubTools() as gh:
            print(f"Searching for content in '{file_path}' across all branches...")
            
            # Get all branches
            branches_result = await gh.list_branches(
                owner=self.owner,
                repo=self.repo,
                page=1,
                per_page=100
            )
            branches_data = self._parse_result(branches_result)
            
            if not isinstance(branches_data, list):
                print("  Could not fetch branches")
                return []
            
            branches = [b.get('name') for b in branches_data if b.get('name')]
            print(f"  Found {len(branches)} branches to check")
            
            matching_branches = []
            
            for i, branch in enumerate(branches):
                if (i + 1) % 10 == 0:
                    print(f"  Checked {i + 1}/{len(branches)} branches...")
                
                try:
                    file_result = await gh.get_file_contents(
                        owner=self.owner,
                        repo=self.repo,
                        path=file_path,
                        ref=branch
                    )
                    
                    file_content = self._extract_file_content(file_result)
                    if file_content and content in file_content:
                        matching_branches.append({
                            'branch': branch,
                            'file': file_path
                        })
                        print(f"  ✓ Found content in branch: {branch}")
                except Exception:
                    continue
            
            return matching_branches

    def _extract_file_content(self, result: Any) -> Optional[str]:
        """Extract file content from API result"""
        if isinstance(result, dict):
            content_list = result.get('content', [])
            if isinstance(content_list, list):
                for item in content_list:
                    if isinstance(item, dict):
                        # Check for resource type (file content)
                        if item.get('type') == 'resource':
                            resource = item.get('resource', {})
                            return resource.get('text', '')
        return None

    def _content_added_in_patch(self, content: str, patch: str) -> bool:
        """Check if content was added (appears in + lines) in the patch"""
        if not patch:
            return False
        
        # Look for the content in added lines (starting with +)
        for line in patch.split('\n'):
            if line.startswith('+') and content in line:
                return True
        
        # Also try partial match for multi-word content
        words = content.split()
        if len(words) >= 2:
            added_lines = [l for l in patch.split('\n') if l.startswith('+')]
            added_text = ' '.join(added_lines)
            matches = sum(1 for w in words if w in added_text)
            if matches >= len(words) * 0.7:
                return True
        
        return False

    def _parse_search_result(self, result: Any) -> List[Dict[str, Any]]:
        """Parse search API result"""
        if isinstance(result, dict):
            return result.get('items', [])
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return parsed.get('items', []) if isinstance(parsed, dict) else []
            except:
                return []
        return []

    def _parse_result(self, result: Any) -> Any:
        """Parse general API result"""
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            content_list = result.get('content', [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text = item.get('text', '')
                        try:
                            parsed = json.loads(text)
                            return parsed
                        except json.JSONDecodeError:
                            pass
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return []
        return []

    def print_result(self, result: Optional[Dict[str, Any]]):
        """Pretty print the result"""
        if not result:
            print("\n❌ Could not find the commit that introduced this content.")
            return

        print("\n" + "=" * 60)
        print("CONTENT INTRODUCTION FOUND")
        print("=" * 60)
        print(f"Commit SHA:  {result.get('sha', '')}")
        print(f"Author:      {result.get('author', '')}")
        print(f"Date:        {result.get('date', '')[:19].replace('T', ' ')}")
        print(f"File:        {result.get('file', '')}")
        print(f"Branch:      {result.get('branch', 'default')}")
        print(f"Message:     {result.get('message', '').split(chr(10))[0]}")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(
        description='Find which commit introduced specific content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search in a specific file on default branch
  python content_tracker.py owner repo --content "def main" --file "src/app.py"
  
  # Search on a specific branch
  python content_tracker.py owner repo --content "new feature" --file "README.md" --branch develop
  
  # Find which branches contain specific content
  python content_tracker.py owner repo --content "RAG" --file "README.md" --find-branches
  
  # Increase search depth for older commits
  python content_tracker.py owner repo --content "old text" --file "README.md" --max-commits 10
        """
    )
    
    parser.add_argument('owner', help='Repository owner')
    parser.add_argument('repo', help='Repository name')
    parser.add_argument('--content', required=True, help='Content text to find')
    parser.add_argument('--file', help='Specific file to search in (recommended)')
    parser.add_argument('--branch', help='Specific branch to search (default: repository default branch)')
    parser.add_argument('--max-commits', type=int, default=10, 
                        help='Max commits to scan (default: 10, max: 30)')
    parser.add_argument('--find-branches', action='store_true',
                        help='Find which branches contain the content (requires --file)')

    args = parser.parse_args()
    
    tracker = ContentTracker(args.owner, args.repo)
    
    try:
        if args.find_branches:
            if not args.file:
                print("Error: --find-branches requires --file parameter")
                return
            branches = await tracker.find_content_in_branches(
                content=args.content,
                file_path=args.file
            )
            if branches:
                print(f"\n✓ Found content in {len(branches)} branch(es):")
                for b in branches:
                    print(f"  - {b['branch']}")
            else:
                print("\n❌ Content not found in any branch")
        else:
            result = await tracker.find_introducing_commit(
                content=args.content,
                file_path=args.file,
                branch=args.branch,
                max_commits=min(args.max_commits, 50)
            )
            tracker.print_result(result)
    except Exception as e:
        print(f"\nError tracking content: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
