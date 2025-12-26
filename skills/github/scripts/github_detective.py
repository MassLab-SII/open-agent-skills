#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Detective Script
=======================

Unified investigation tool for GitHub repositories.
Combines repository exploration, commit search, content tracking, and PR investigation.

Usage:
    python github_detective.py <command> <owner> <repo> [options]

Commands:
    explore         Explore repository structure (branches, tags, releases, files)
    search-commits  Search commits by message, author, path, or date
    trace-content   Find the commit that introduced specific content
    search-prs      Search and investigate Pull Requests
    search-issues   Search and investigate Issues

Examples:
    # Explore repository structure
    python github_detective.py explore owner repo --show branches,tags
    python github_detective.py explore owner repo --show files --path "src"
    
    # Search commits
    python github_detective.py search-commits owner repo --query "fix" --limit 10
    python github_detective.py search-commits owner repo --author "Daniel" --path "src/main.py"
    
    # Trace content origin
    python github_detective.py trace-content owner repo --content "def main" --file "src/app.py"
    python github_detective.py trace-content owner repo --content "RAG" --file "README.md" --find-branches
    
    # Search PRs
    python github_detective.py search-prs owner repo --query "authentication"
    python github_detective.py search-prs owner repo --number 42 --show-files
"""

import asyncio
import argparse
import re
import json
from typing import List, Dict, Any, Optional

from utils import (
    GitHubTools,
    parse_mcp_result,
    parse_mcp_search_result,
    extract_file_content,
)


# ==================== Repository Explorer ====================
class RepoExplorer:
    """Explore repository structure and metadata"""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def explore(
        self, 
        show: List[str] = None,
        path: str = "",
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Explore repository structure."""
        show = show or ['branches', 'tags', 'releases']
        result = {}
        
        async with GitHubTools() as gh:
            print(f"Exploring {self.owner}/{self.repo}...\n")
            
            if 'branches' in show:
                print("Fetching branches...")
                branches = await gh.list_branches(self.owner, self.repo, page=1, per_page=30)
                result['branches'] = self._parse_result(branches)
                print(f"  Found {len(result['branches'])} branches")
            
            if 'tags' in show:
                print("Fetching tags...")
                tags = await gh.list_tags(self.owner, self.repo)
                result['tags'] = self._parse_result(tags)
                print(f"  Found {len(result['tags'])} tags")
            
            if 'releases' in show:
                print("Fetching releases...")
                releases = await gh.list_releases(self.owner, self.repo)
                result['releases'] = self._parse_result(releases)
                print(f"  Found {len(result['releases'])} releases")
            
            if 'files' in show:
                branch_info = f" on branch '{branch}'" if branch else ""
                print(f"Fetching directory contents: {path or '/'}{branch_info}")
                contents = await gh.get_file_contents(self.owner, self.repo, path, ref=branch)
                result['files'] = self._parse_result(contents)
                if isinstance(result['files'], list):
                    print(f"  Found {len(result['files'])} items")
            
            return result

    def _parse_result(self, result: Any) -> Any:
        return parse_mcp_result(result)

    def print_results(self, data: Dict[str, Any]):
        if 'branches' in data:
            branches = data['branches']
            print("\n" + "=" * 50)
            print(f"BRANCHES ({len(branches)})")
            print("=" * 50)
            for b in branches[:20]:
                name = b.get('name', '') if isinstance(b, dict) else str(b)
                protected = " [protected]" if isinstance(b, dict) and b.get('protected') else ""
                print(f"  • {name}{protected}")
            if len(branches) > 20:
                print(f"  ... and {len(branches) - 20} more")
        
        if 'tags' in data:
            tags = data['tags']
            print("\n" + "=" * 50)
            print(f"TAGS ({len(tags)})")
            print("=" * 50)
            for t in tags[:15]:
                name = t.get('name', '') if isinstance(t, dict) else str(t)
                print(f"  • {name}")
            if len(tags) > 15:
                print(f"  ... and {len(tags) - 15} more")
        
        if 'releases' in data:
            releases = data['releases']
            print("\n" + "=" * 50)
            print(f"RELEASES ({len(releases)})")
            print("=" * 50)
            for r in releases[:10]:
                if isinstance(r, dict):
                    name = r.get('name') or r.get('tag_name', '')
                    prerelease = " [pre-release]" if r.get('prerelease') else ""
                    print(f"  • {name}{prerelease}")
        
        if 'files' in data:
            files = data['files']
            if isinstance(files, list):
                print("\n" + "=" * 50)
                print(f"DIRECTORY CONTENTS ({len(files)} items)")
                print("=" * 50)
                dirs = [f for f in files if isinstance(f, dict) and f.get('type') == 'dir']
                items = [f for f in files if isinstance(f, dict) and f.get('type') != 'dir']
                for d in dirs:
                    print(f"  📁 {d.get('name', '')}/")
                for f in items:
                    size = f.get('size', 0)
                    print(f"  📄 {f.get('name', '')} ({size:,} bytes)" if size else f"  📄 {f.get('name', '')}")


# ==================== Commit Finder ====================
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
        branch: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        async with GitHubTools() as gh:
            all_commits = []
            page = 1
            per_page = 100
            max_pages = 5
            
            branch_info = f" on branch '{branch}'" if branch else ""
            print(f"Searching commits in {self.owner}/{self.repo}{branch_info}...")
            
            while len(all_commits) < limit and page <= max_pages:
                result = await gh.list_commits(
                    owner=self.owner, repo=self.repo, sha=branch,
                    author=author, path=path, since=since, until=until,
                    page=page, per_page=per_page
                )
                
                batch = self._parse_result(result)
                if not batch:
                    break
                
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
        parsed = parse_mcp_result(result)
        return parsed if isinstance(parsed, list) else []

    def _matches_query(self, commit: Dict[str, Any], query: Optional[str]) -> bool:
        if not query:
            return True
        message = commit.get('commit', {}).get('message', '')
        try:
            return bool(re.search(query, message, re.IGNORECASE))
        except re.error:
            return query.lower() in message.lower()

    def print_results(self, commits: List[Dict[str, Any]]):
        if not commits:
            print("\nNo commits found matching criteria.")
            return
        print(f"\nFound {len(commits)} commits:\n")
        print(f"{'SHA':<42} | {'Date':<20} | {'Author':<15} | {'Message'}")
        print("-" * 130)
        for c in commits:
            sha = c.get('sha', '')
            commit_info = c.get('commit', {})
            author_info = commit_info.get('author', {})
            author = author_info.get('name', 'Unknown')[:15]
            date = author_info.get('date', '')[:19].replace('T', ' ')
            msg = commit_info.get('message', '').split('\n')[0][:45]
            print(f"{sha:<42} | {date:<20} | {author:<15} | {msg}")


# ==================== Content Tracker ====================
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
        async with GitHubTools() as gh:
            if not file_path:
                print("⚠️ Warning: --file not specified. Use --file for faster results.")
                return None
            
            print(f"Step 1: Using specified file: {file_path}")
            branch_display = branch or "default branch"
            
            print(f"\nStep 2: Getting commit history for {file_path} on '{branch_display}'")
            
            commits_result = await gh.list_commits(
                owner=self.owner, repo=self.repo, sha=branch,
                path=file_path, page=1, per_page=min(max_commits, 100)
            )
            
            commits = self._parse_result(commits_result)
            if not commits:
                print(f"  No commits found for {file_path}")
                return None
            
            print(f"  Found {len(commits)} commits, checking diffs...")
            
            for i, commit in enumerate(commits):
                sha = commit.get('sha')
                if not sha:
                    continue
                
                try:
                    commit_detail = await gh.get_commit(self.owner, self.repo, sha)
                    detail = self._parse_result(commit_detail)
                    if isinstance(detail, dict):
                        files = detail.get('files', [])
                        for f in files:
                            if f.get('filename') == file_path:
                                patch = f.get('patch', '')
                                if self._content_added_in_patch(content, patch):
                                    print(f"\n✓ Found! Content was added in commit {sha[:7]}")
                                    return {
                                        'sha': sha,
                                        'message': commit.get('commit', {}).get('message', ''),
                                        'author': commit.get('commit', {}).get('author', {}).get('name', ''),
                                        'date': commit.get('commit', {}).get('author', {}).get('date', ''),
                                        'file': file_path,
                                        'branch': branch or 'default'
                                    }
                except (KeyError, TypeError, AttributeError) as e:
                    print(f"  Warning: Error parsing commit {sha[:7]}: {e}")
                    continue
                except Exception as e:
                    # Log unexpected errors but continue processing
                    print(f"  Warning: Unexpected error checking commit {sha[:7]}: {type(e).__name__}: {e}")
                    continue
            
            print("\nContent not found in searched commits.")
            return None

    async def find_content_in_branches(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        async with GitHubTools() as gh:
            print(f"Searching for content in '{file_path}' across all branches...")
            branches_result = await gh.list_branches(self.owner, self.repo, page=1, per_page=100)
            branches_data = self._parse_result(branches_result)
            
            if not isinstance(branches_data, list):
                return []
            
            branches = [b.get('name') for b in branches_data if b.get('name')]
            print(f"  Found {len(branches)} branches to check")
            
            matching_branches = []
            for i, branch in enumerate(branches):
                try:
                    file_result = await gh.get_file_contents(self.owner, self.repo, file_path, ref=branch)
                    file_content = self._extract_file_content(file_result)
                    if file_content and content in file_content:
                        matching_branches.append({'branch': branch, 'file': file_path})
                        print(f"  ✓ Found content in branch: {branch}")
                except Exception:
                    continue
            
            return matching_branches

    def _extract_file_content(self, result: Any) -> Optional[str]:
        return extract_file_content(result)

    def _content_added_in_patch(self, content: str, patch: str) -> bool:
        if not patch:
            return False
        for line in patch.split('\n'):
            if line.startswith('+') and content in line:
                return True
        return False

    def _parse_result(self, result: Any) -> Any:
        return parse_mcp_result(result)

    def print_result(self, result: Optional[Dict[str, Any]]):
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


# ==================== PR Investigator ====================
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
        async with GitHubTools() as gh:
            if query:
                full_query = f"{query} repo:{self.owner}/{self.repo}"
                if state != "all":
                    full_query += f" is:{state}"
                print(f"Searching PRs for: {query}")
                search_result = await gh.search_pull_requests(query=full_query, page=1, per_page=min(limit, 100))
                items = self._parse_search_result(search_result)
                return items[:limit]
            else:
                print(f"Listing {state} PRs...")
                prs = await gh.list_pull_requests(
                    owner=self.owner, repo=self.repo,
                    state=state if state != "all" else "open",
                    page=1, per_page=min(limit, 100)
                )
                return self._parse_result(prs)[:limit]

    async def get_pr_details(self, pr_number: int) -> Dict[str, Any]:
        async with GitHubTools() as gh:
            pr = await gh.pull_request_read(self.owner, self.repo, pr_number, method="get")
            
            if isinstance(pr, str):
                try:
                    pr = json.loads(pr)
                except json.JSONDecodeError:
                    return {}
            
            if not isinstance(pr, dict) or pr.get('isError'):
                return {}
            
            # Get commits from the head branch
            # Note: For forked PRs, head.ref might not exist in the base repo
            head_ref = pr.get('head', {}).get('ref', '')
            head_repo_owner = pr.get('head', {}).get('repo', {}).get('owner', {}).get('login', '')
            base_repo_owner = pr.get('base', {}).get('repo', {}).get('owner', {}).get('login', self.owner)
            
            pr['_commits_list'] = []
            
            if head_ref:
                # Check if this is a cross-repo PR (fork)
                is_fork_pr = head_repo_owner and head_repo_owner != base_repo_owner
                
                if is_fork_pr:
                    print(f"  Note: PR is from fork ({head_repo_owner}), commits may be limited")
                
                try:
                    commits_result = await gh.list_commits(self.owner, self.repo, sha=head_ref, page=1, per_page=100)
                    if isinstance(commits_result, str):
                        try:
                            commits_result = json.loads(commits_result)
                        except json.JSONDecodeError:
                            commits_result = []
                    pr['_commits_list'] = commits_result if isinstance(commits_result, list) else []
                except Exception as e:
                    print(f"  Warning: Could not fetch commits for head ref '{head_ref}': {e}")
            
            return pr

    async def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        async with GitHubTools() as gh:
            result = await gh.pull_request_read(self.owner, self.repo, pr_number, method="get_files", per_page=100)
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except:
                    return []
            return result if isinstance(result, list) else []

    def _parse_search_result(self, result: Any) -> List[Dict[str, Any]]:
        return parse_mcp_search_result(result)

    def _parse_result(self, result: Any) -> Any:
        return parse_mcp_result(result)

    def print_results(self, prs: List[Dict[str, Any]]):
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
        if not pr:
            print("\nPR not found.")
            return
        print("\n" + "=" * 70)
        print(f"PR #{pr.get('number', '')}: {pr.get('title', '')}")
        print("=" * 70)
        print(f"State:    {pr.get('state', '')}")
        print(f"Author:   {pr.get('user', {}).get('login', '')}")
        print(f"Base:     {pr.get('base', {}).get('ref', '')}")
        print(f"Head:     {pr.get('head', {}).get('ref', '')}")
        head_sha = pr.get('head', {}).get('sha', '')
        if head_sha:
            print(f"Head SHA: {head_sha}")
        print(f"Created:  {pr.get('created_at', '')[:19].replace('T', ' ')}")
        
        commits_list = pr.get('_commits_list', [])
        if commits_list:
            print(f"\n--- Commits in this PR ({len(commits_list)}) ---")
            for c in commits_list:
                sha = c.get('sha', '')[:7]
                full_sha = c.get('sha', '')
                msg = c.get('commit', {}).get('message', '').split('\n')[0][:50]
                print(f"  {sha} | {msg}")
                print(f"         Full SHA: {full_sha}")


# ==================== Issue Investigator ====================
class IssueInvestigator:
    """Investigate Issues in a repository"""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def search_issues(
        self, 
        query: Optional[str] = None,
        state: str = "all",
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        async with GitHubTools() as gh:
            if query:
                full_query = f"{query} repo:{self.owner}/{self.repo} is:issue"
                if state != "all":
                    full_query += f" is:{state}"
                print(f"Searching issues for: {query}")
                search_result = await gh.search_issues(query=full_query, page=1, per_page=min(limit, 100))
                items = self._parse_search_result(search_result)
                return items[:limit]
            else:
                print(f"Listing {state} issues...")
                issues = await gh.list_issues(
                    owner=self.owner, repo=self.repo,
                    state=state if state != "all" else "open",
                    page=1, per_page=min(limit, 100)
                )
                return self._parse_result(issues)[:limit]

    def _parse_search_result(self, result: Any) -> List[Dict[str, Any]]:
        return parse_mcp_search_result(result)

    def _parse_result(self, result: Any) -> Any:
        return parse_mcp_result(result)

    def print_results(self, issues: List[Dict[str, Any]]):
        if not issues:
            print("\nNo Issues found.")
            return
        print(f"\n{'#':<6} | {'State':<8} | {'Title':<45} | {'User'}")
        print("-" * 90)
        for issue in issues:
            # Skip PRs which might appear in list_issues if not carefully filtered, 
            # though usually list_issues separates them. search_issues with is:issue handles it.
            if 'pull_request' in issue:
                continue
                
            number = issue.get('number', '')
            state = issue.get('state', '')
            title = issue.get('title', '')[:45]
            user = issue.get('user', {}).get('login', '') if isinstance(issue.get('user'), dict) else ''
            state_icon = "🟢" if state == "open" else "🟣"
            print(f"{state_icon} {number:<4} | {state:<8} | {title:<45} | {user}")


# ==================== CLI ====================
async def main():
    parser = argparse.ArgumentParser(
        description='Unified GitHub investigation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Explore repo structure
  python github_detective.py explore owner repo --show branches,tags
  
  # Search commits
  python github_detective.py search-commits owner repo --query "fix" --limit 10
  
  # Trace content origin
  python github_detective.py trace-content owner repo --content "def main" --file "src/app.py"
  
  # Search PRs
  python github_detective.py search-prs owner repo --query "authentication"

  # Search Issues
  python github_detective.py search-issues owner repo --query "memory leak"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: explore
    explore_parser = subparsers.add_parser("explore", help="Explore repository structure")
    explore_parser.add_argument("owner", help="Repository owner")
    explore_parser.add_argument("repo", help="Repository name")
    explore_parser.add_argument("--show", default="branches,tags,releases", help="Comma-separated: branches,tags,releases,files")
    explore_parser.add_argument("--path", default="", help="Directory path for file listing")
    explore_parser.add_argument("--branch", help="Branch name for file listing")
    
    # Command: search-commits
    commits_parser = subparsers.add_parser("search-commits", help="Search commits")
    commits_parser.add_argument("owner", help="Repository owner")
    commits_parser.add_argument("repo", help="Repository name")
    commits_parser.add_argument("--query", help="Regex to search in commit messages")
    commits_parser.add_argument("--author", help="Filter by author")
    commits_parser.add_argument("--path", help="Filter by file path")
    commits_parser.add_argument("--since", help="Start date (ISO format)")
    commits_parser.add_argument("--until", help="End date (ISO format)")
    commits_parser.add_argument("--branch", help="Branch name to search")
    commits_parser.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    
    # Command: trace-content
    trace_parser = subparsers.add_parser("trace-content", help="Find commit that introduced content")
    trace_parser.add_argument("owner", help="Repository owner")
    trace_parser.add_argument("repo", help="Repository name")
    trace_parser.add_argument("--content", required=True, help="Content text to find")
    trace_parser.add_argument("--file", help="Specific file to search in (recommended)")
    trace_parser.add_argument("--branch", help="Branch to search")
    trace_parser.add_argument("--max-commits", type=int, default=10, help="Max commits to scan")
    trace_parser.add_argument("--find-branches", action="store_true", help="Find which branches contain the content")
    
    # Command: search-prs
    prs_parser = subparsers.add_parser("search-prs", help="Search Pull Requests")
    prs_parser.add_argument("owner", help="Repository owner")
    prs_parser.add_argument("repo", help="Repository name")
    prs_parser.add_argument("--query", help="Search query")
    prs_parser.add_argument("--state", choices=["open", "closed", "all"], default="all", help="PR state filter")
    prs_parser.add_argument("--number", type=int, help="Specific PR number to inspect")
    prs_parser.add_argument("--show-files", action="store_true", help="Show files changed in the PR")
    prs_parser.add_argument("--limit", type=int, default=20, help="Max results")

    # Command: search-issues
    issues_parser = subparsers.add_parser("search-issues", help="Search Issues")
    issues_parser.add_argument("owner", help="Repository owner")
    issues_parser.add_argument("repo", help="Repository name")
    issues_parser.add_argument("--query", help="Search query")
    issues_parser.add_argument("--state", choices=["open", "closed", "all"], default="all", help="Issue state filter")
    issues_parser.add_argument("--limit", type=int, default=20, help="Max results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "explore":
            explorer = RepoExplorer(args.owner, args.repo)
            show_items = [s.strip() for s in args.show.split(',')]
            results = await explorer.explore(show=show_items, path=args.path, branch=args.branch)
            explorer.print_results(results)
        
        elif args.command == "search-commits":
            finder = CommitFinder(args.owner, args.repo)
            commits = await finder.find_commits(
                query=args.query, author=args.author, path=args.path,
                since=args.since, until=args.until, branch=args.branch, limit=args.limit
            )
            finder.print_results(commits)
        
        elif args.command == "trace-content":
            tracker = ContentTracker(args.owner, args.repo)
            if args.find_branches:
                if not args.file:
                    print("Error: --find-branches requires --file parameter")
                    return
                branches = await tracker.find_content_in_branches(args.content, args.file)
                if branches:
                    print(f"\n✓ Found content in {len(branches)} branch(es):")
                    for b in branches:
                        print(f"  - {b['branch']}")
                else:
                    print("\n❌ Content not found in any branch")
            else:
                result = await tracker.find_introducing_commit(
                    content=args.content, file_path=args.file,
                    branch=args.branch, max_commits=min(args.max_commits, 50)
                )
                tracker.print_result(result)
        
        elif args.command == "search-prs":
            investigator = PRInvestigator(args.owner, args.repo)
            if args.number:
                pr = await investigator.get_pr_details(args.number)
                investigator.print_pr_detail(pr)
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
                prs = await investigator.search_prs(query=args.query, state=args.state, limit=args.limit)
                investigator.print_results(prs)
        
        elif args.command == "search-issues":
            investigator = IssueInvestigator(args.owner, args.repo)
            issues = await investigator.search_issues(query=args.query, state=args.state, limit=args.limit)
            investigator.print_results(issues)
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
