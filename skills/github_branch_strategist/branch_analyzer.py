#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Branch Analyzer Script
======================

Analyze branches and commits across a GitHub repository.
Supports cross-branch commit aggregation and contributor statistics.

Usage:
    python branch_analyzer.py <command> <owner> <repo> [options]

Commands:
    aggregate       Aggregate commits from multiple branches
    contributors    Analyze top contributors
    report          Generate comprehensive branch report

Examples:
    # Aggregate commits from multiple branches
    python branch_analyzer.py aggregate owner repo --branches "main,develop,release/v1.0"
    
    # Analyze top contributors
    python branch_analyzer.py contributors owner repo --top 10
    
    # Generate branch report
    python branch_analyzer.py report owner repo --output "BRANCH_REPORT.md"
"""

import asyncio
import argparse
import json
import sys
from typing import List, Dict, Any, Optional
from collections import defaultdict

from utils import GitHubTools


class BranchAnalyzer:
    """Analyze branches and commits"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Branch Analyzer.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def aggregate_branch_commits(
        self,
        branches: List[str],
        commits_per_branch: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate commits from multiple branches.

        Args:
            branches: List of branch names
            commits_per_branch: Number of commits per branch

        Returns:
            Dict mapping branch names to commit lists
        """
        async with GitHubTools() as gh:
            result = {}
            
            print(f"Aggregating commits from {len(branches)} branches...")
            
            for branch in branches:
                print(f"  Fetching commits from '{branch}'...")
                
                commits_result = await gh.list_commits(
                    owner=self.owner,
                    repo=self.repo,
                    sha=branch,
                    per_page=commits_per_branch
                )
                
                commits = self._parse_result(commits_result)
                
                branch_commits = []
                for commit in commits[:commits_per_branch]:
                    commit_info = commit.get("commit", {})
                    author_info = commit_info.get("author", {})
                    
                    # Get files changed count
                    sha = commit.get("sha", "")
                    files_changed = 0
                    
                    if sha:
                        detail = await gh.get_commit(
                            owner=self.owner,
                            repo=self.repo,
                            sha=sha
                        )
                        detail_data = self._parse_result(detail)
                        if isinstance(detail_data, dict):
                            files_changed = len(detail_data.get("files", []))
                    
                    branch_commits.append({
                        "sha": sha,
                        "author": commit.get("author", {}).get("login", author_info.get("name", "Unknown")),
                        "message": commit_info.get("message", "").split("\n")[0],
                        "files_changed": files_changed
                    })
                
                result[branch] = branch_commits
                print(f"    Found {len(branch_commits)} commits")
            
            return result

    async def analyze_contributors(
        self,
        top_n: int = 10,
        branch: str = "main"
    ) -> List[Dict[str, Any]]:
        """
        Analyze top contributors by commit count.

        Args:
            top_n: Number of top contributors to return
            branch: Branch to analyze

        Returns:
            List of contributor dicts with name and commit count
        """
        async with GitHubTools() as gh:
            print(f"Analyzing contributors on '{branch}'...")
            
            # Get commits (up to 100)
            commits_result = await gh.list_commits(
                owner=self.owner,
                repo=self.repo,
                sha=branch,
                per_page=100
            )
            
            commits = self._parse_result(commits_result)
            
            # Count commits per author
            author_counts = defaultdict(int)
            
            for commit in commits:
                # Try to get GitHub username first, fall back to commit author name
                author = commit.get("author", {})
                if isinstance(author, dict) and author.get("login"):
                    author_name = author.get("login")
                else:
                    commit_info = commit.get("commit", {})
                    author_info = commit_info.get("author", {})
                    author_name = author_info.get("name", "Unknown")
                
                author_counts[author_name] += 1
            
            # Sort by count
            sorted_contributors = sorted(
                author_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_n]
            
            result = [
                {"name": name, "commits": count}
                for name, count in sorted_contributors
            ]
            
            print(f"Found {len(author_counts)} unique contributors")
            
            return result

    async def generate_report(
        self,
        output_path: str = "BRANCH_REPORT.md",
        branch: str = "main"
    ) -> bool:
        """
        Generate comprehensive branch report.

        Args:
            output_path: Output file path
            branch: Branch to create report on

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print("Generating branch report...")
            
            # Get branches
            print("  Fetching branches...")
            branches_result = await gh.list_branches(
                owner=self.owner,
                repo=self.repo,
                per_page=100
            )
            branches = self._parse_result(branches_result)
            
            # Get top contributors
            print("  Analyzing contributors...")
            contributors = await self.analyze_contributors(top_n=5, branch=branch)
            
            # Get recent merge commits
            print("  Fetching merge commits...")
            commits_result = await gh.list_commits(
                owner=self.owner,
                repo=self.repo,
                sha=branch,
                per_page=50
            )
            commits = self._parse_result(commits_result)
            
            # Filter merge commits (those with "Merge" in message)
            merge_commits = [
                c for c in commits
                if "merge" in c.get("commit", {}).get("message", "").lower()
            ][:10]
            
            # Generate report content
            report_content = self._format_report(branches, contributors, merge_commits)
            
            # Check if file exists
            existing = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                ref=branch
            )
            sha = self._extract_sha(existing)
            
            # Create/update report
            result = await gh.create_or_update_file(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                content=report_content,
                message="Update branch report",
                branch=branch,
                sha=sha
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Report generated at {output_path}")
            else:
                print(f"✗ Failed to generate report: {result}")
            
            return success

    async def create_branch_commits_json(
        self,
        branches: List[str],
        output_path: str = "BRANCH_COMMITS.json",
        target_branch: str = "main"
    ) -> bool:
        """
        Create JSON file with branch commits data.

        Args:
            branches: List of branches to analyze
            output_path: Output file path
            target_branch: Branch to commit the file to

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            # Aggregate commits
            commits_data = await self.aggregate_branch_commits(branches, commits_per_branch=3)
            
            # Convert to JSON
            json_content = json.dumps(commits_data, indent=2)
            
            # Check if file exists
            existing = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                ref=target_branch
            )
            sha = self._extract_sha(existing)
            
            # Create/update file
            result = await gh.create_or_update_file(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                content=json_content,
                message="Update branch commits data",
                branch=target_branch,
                sha=sha
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Branch commits JSON created at {output_path}")
            
            return success

    def _format_report(
        self,
        branches: List[Dict[str, Any]],
        contributors: List[Dict[str, Any]],
        merge_commits: List[Dict[str, Any]]
    ) -> str:
        """Format report as markdown"""
        content = "# Branch Report\n\n"
        
        # Branches section
        content += "## Branches\n\n"
        content += f"Total branches: {len(branches)}\n\n"
        
        for branch in branches[:20]:  # Limit to 20
            name = branch.get("name", "")
            content += f"- `{name}`\n"
        
        if len(branches) > 20:
            content += f"- ... and {len(branches) - 20} more\n"
        
        content += "\n"
        
        # Contributors section
        content += "## Top Contributors\n\n"
        content += "| Rank | Contributor | Commits |\n"
        content += "|------|-------------|--------|\n"
        
        for i, contrib in enumerate(contributors, 1):
            content += f"| {i} | {contrib['name']} | {contrib['commits']} |\n"
        
        content += "\n"
        
        # Merge commits section
        content += "## Recent Merge Commits\n\n"
        
        for commit in merge_commits:
            commit_info = commit.get("commit", {})
            sha = commit.get("sha", "")  # Full SHA for accuracy
            message = commit_info.get("message", "").split("\n")[0][:60]
            date = commit_info.get("author", {}).get("date", "")[:10]
            
            content += f"- `{sha}` ({date}): {message}\n"
        
        return content

    def _parse_result(self, result) -> Any:
        """Parse API result, handling MCP response format"""
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

    def _extract_sha(self, result) -> Optional[str]:
        """Extract SHA from result"""
        if isinstance(result, dict):
            # Direct sha field
            if "sha" in result:
                return result.get("sha")
            # Try to extract from MCP text content (JSON string)
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            import json
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return parsed.get("sha")
                        except:
                            pass
        return None

    def _check_success(self, result) -> bool:
        """Check if operation was successful, handling MCP response format"""
        if not result:
            return False
        
        def check_data(data: dict) -> bool:
            return "error" not in data and not data.get("isError")
        
        if isinstance(result, dict):
            # Check for MCP format first
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            import json
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return check_data(parsed)
                        except json.JSONDecodeError:
                            return "error" not in text.lower()
            return check_data(result)
        if isinstance(result, str):
            try:
                import json
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    return check_data(parsed)
            except json.JSONDecodeError:
                pass
            return "error" not in result.lower()
        return True

    def print_aggregate_results(self, data: Dict[str, List[Dict[str, Any]]]):
        """Pretty print aggregated commits"""
        for branch, commits in data.items():
            print(f"\n=== {branch} ===")
            for c in commits:
                print(f"  {c['sha']} | {c['author']:<15} | {c['message'][:40]}")

    def print_contributors(self, contributors: List[Dict[str, Any]]):
        """Pretty print contributors"""
        print(f"\n{'Rank':<6} | {'Contributor':<20} | {'Commits'}")
        print("-" * 45)
        for i, c in enumerate(contributors, 1):
            print(f"{i:<6} | {c['name']:<20} | {c['commits']}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Analyze branches and commits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aggregate commits from multiple branches
  python branch_analyzer.py aggregate owner repo --branches "main,develop,release/v1.0"
  
  # Analyze top contributors
  python branch_analyzer.py contributors owner repo --top 10
  
  # Generate branch report
  python branch_analyzer.py report owner repo --output "BRANCH_REPORT.md"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: aggregate
    agg_parser = subparsers.add_parser("aggregate", help="Aggregate branch commits")
    agg_parser.add_argument("owner", help="Repository owner")
    agg_parser.add_argument("repo", help="Repository name")
    agg_parser.add_argument("--branches", required=True, help="Comma-separated branch names")
    agg_parser.add_argument("--per-branch", type=int, default=3, help="Commits per branch")
    agg_parser.add_argument("--output", help="Output JSON file (optional)")
    agg_parser.add_argument("--target-branch", default="main", help="Branch to commit output to")
    
    # Command: contributors
    contrib_parser = subparsers.add_parser("contributors", help="Analyze contributors")
    contrib_parser.add_argument("owner", help="Repository owner")
    contrib_parser.add_argument("repo", help="Repository name")
    contrib_parser.add_argument("--top", type=int, default=10, help="Number of top contributors")
    contrib_parser.add_argument("--branch", default="main", help="Branch to analyze")
    
    # Command: report
    report_parser = subparsers.add_parser("report", help="Generate branch report")
    report_parser.add_argument("owner", help="Repository owner")
    report_parser.add_argument("repo", help="Repository name")
    report_parser.add_argument("--output", default="BRANCH_REPORT.md", help="Output file")
    report_parser.add_argument("--branch", default="main", help="Target branch")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    analyzer = BranchAnalyzer(args.owner, args.repo)
    
    try:
        if args.command == "aggregate":
            branches = [b.strip() for b in args.branches.split(",")]
            data = await analyzer.aggregate_branch_commits(
                branches=branches,
                commits_per_branch=args.per_branch
            )
            analyzer.print_aggregate_results(data)
            
            if args.output:
                success = await analyzer.create_branch_commits_json(
                    branches=branches,
                    output_path=args.output,
                    target_branch=args.target_branch
                )
                sys.exit(0 if success else 1)
            
        elif args.command == "contributors":
            contributors = await analyzer.analyze_contributors(
                top_n=args.top,
                branch=args.branch
            )
            analyzer.print_contributors(contributors)
            
        elif args.command == "report":
            success = await analyzer.generate_report(
                output_path=args.output,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
