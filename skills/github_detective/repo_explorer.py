#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository Explorer Script
==========================

Explore repository structure: branches, tags, releases, and directory contents.
Uses multiple APIs to give a comprehensive view of the repository.

Usage:
    python repo_explorer.py <owner> <repo> [--show branches,tags,releases,files]

Examples:
    # Show all repository info
    python repo_explorer.py enigma mcpmark
    
    # Show only branches and tags
    python repo_explorer.py enigma mcpmark --show branches,tags
    
    # Show directory structure
    python repo_explorer.py enigma mcpmark --show files --path "src"
"""

import asyncio
import argparse
import json
from typing import List, Dict, Any, Optional

from utils import GitHubTools


class RepoExplorer:
    """Explore repository structure and metadata"""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def explore(
        self, 
        show: List[str] = None,
        path: str = ""
    ) -> Dict[str, Any]:
        """
        Explore repository structure.

        Args:
            show: List of items to show: branches, tags, releases, files
            path: Directory path for file listing

        Returns:
            Dict with requested information
        """
        show = show or ['branches', 'tags', 'releases']
        result = {}
        
        async with GitHubTools() as gh:
            print(f"Exploring {self.owner}/{self.repo}...\n")
            
            # Get branches
            if 'branches' in show:
                print("Fetching branches...")
                branches = await gh.list_branches(
                    owner=self.owner,
                    repo=self.repo,
                    page=1,
                    per_page=30
                )
                result['branches'] = self._parse_result(branches)
                print(f"  Found {len(result['branches'])} branches")
            
            # Get tags
            if 'tags' in show:
                print("Fetching tags...")
                tags = await gh.list_tags(
                    owner=self.owner,
                    repo=self.repo
                )
                result['tags'] = self._parse_result(tags)
                print(f"  Found {len(result['tags'])} tags")
            
            # Get releases
            if 'releases' in show:
                print("Fetching releases...")
                releases = await gh.list_releases(
                    owner=self.owner,
                    repo=self.repo
                )
                result['releases'] = self._parse_result(releases)
                print(f"  Found {len(result['releases'])} releases")
            
            # Get directory contents
            if 'files' in show:
                print(f"Fetching directory contents: {path or '/'}")
                contents = await gh.get_file_contents(
                    owner=self.owner,
                    repo=self.repo,
                    path=path
                )
                result['files'] = self._parse_result(contents)
                if isinstance(result['files'], list):
                    print(f"  Found {len(result['files'])} items")
            
            return result

    def _parse_result(self, result: Any) -> Any:
        """Parse API result"""
        if isinstance(result, (list, dict)):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except:
                return []
        return []

    def print_results(self, data: Dict[str, Any]):
        """Pretty print exploration results"""
        # Branches
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
        
        # Tags
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
        
        # Releases
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
                else:
                    print(f"  • {r}")
            if len(releases) > 10:
                print(f"  ... and {len(releases) - 10} more")
        
        # Files
        if 'files' in data:
            files = data['files']
            if isinstance(files, list):
                print("\n" + "=" * 50)
                print(f"DIRECTORY CONTENTS ({len(files)} items)")
                print("=" * 50)
                # Sort: directories first, then files
                dirs = [f for f in files if isinstance(f, dict) and f.get('type') == 'dir']
                items = [f for f in files if isinstance(f, dict) and f.get('type') != 'dir']
                
                for d in dirs:
                    print(f"  📁 {d.get('name', '')}/")
                for f in items:
                    size = f.get('size', 0)
                    size_str = f"{size:,}" if size else ""
                    print(f"  📄 {f.get('name', '')} ({size_str} bytes)")


async def main():
    parser = argparse.ArgumentParser(
        description='Explore repository structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all repo info
  python repo_explorer.py owner repo
  
  # Show only branches and tags
  python repo_explorer.py owner repo --show branches,tags
  
  # List directory contents
  python repo_explorer.py owner repo --show files --path "src"
        """
    )
    
    parser.add_argument('owner', help='Repository owner')
    parser.add_argument('repo', help='Repository name')
    parser.add_argument('--show', default='branches,tags,releases',
                        help='Comma-separated: branches,tags,releases,files')
    parser.add_argument('--path', default='',
                        help='Directory path for file listing')

    args = parser.parse_args()
    
    show_items = [s.strip() for s in args.show.split(',')]
    
    explorer = RepoExplorer(args.owner, args.repo)
    
    try:
        results = await explorer.explore(show=show_items, path=args.path)
        explorer.print_results(results)
    except Exception as e:
        print(f"\nError exploring repo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
