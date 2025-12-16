#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Release Manager Script
======================

Manage releases for GitHub repositories.
Supports version bumping, changelog generation, and release preparation.

Usage:
    python release_manager.py <command> <owner> <repo> [options]

Commands:
    prepare         Prepare a release (create branch, update version, generate changelog)
    bump-version    Update version number in a file
    changelog       Generate changelog from commit history
    finish          Finish release (merge to main)

Examples:
    # Prepare a release
    python release_manager.py prepare owner repo --version "1.1.0" --from develop
    
    # Bump version in Cargo.toml
    python release_manager.py bump-version owner repo --file "Cargo.toml" --version "1.1.0" --branch release/v1.1.0
    
    # Generate changelog
    python release_manager.py changelog owner repo --since "2024-01-01" --output "CHANGELOG.md"
    
    # Finish release (merge to main)
    python release_manager.py finish owner repo --version "1.1.0"
"""

import asyncio
import argparse
import json
import re
import sys
from typing import Optional, List, Dict, Any

from utils import GitHubTools


class ReleaseManager:
    """Manage releases for GitHub repositories"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the Release Manager.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def prepare_release(
        self,
        version: str,
        from_branch: str = "develop"
    ) -> bool:
        """
        Prepare a release by creating branch, updating version, and generating changelog.

        Args:
            version: Release version (e.g., "1.1.0")
            from_branch: Source branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            branch_name = f"release/v{version}"
            
            print(f"Step 1: Creating release branch '{branch_name}' from '{from_branch}'")
            await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                from_branch=from_branch
            )
            
            print(f"Step 2: Generating changelog")
            changelog_content = await self._generate_changelog_content(gh, version)
            
            print(f"Step 3: Pushing changelog to release branch")
            files = [{"path": "CHANGELOG.md", "content": changelog_content}]
            await gh.push_files(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                files=files,
                message=f"Add changelog for v{version}"
            )
            
            print(f"✓ Release v{version} prepared on branch '{branch_name}'")
            return True

    async def bump_version(
        self,
        file_path: str,
        version: str,
        branch: str = "main"
    ) -> bool:
        """
        Update version number in a file.

        Args:
            file_path: Path to version file (e.g., Cargo.toml, package.json)
            version: New version number
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Updating version to {version} in {file_path}")
            
            # Get current file content
            file_result = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=file_path,
                ref=branch
            )
            
            current_content = self._extract_content(file_result)
            if not current_content:
                print(f"✗ Failed to get {file_path}")
                return False
            
            # Update version based on file type
            if file_path.endswith("Cargo.toml"):
                new_content = self._update_cargo_version(current_content, version)
            elif file_path.endswith("package.json"):
                new_content = self._update_package_json_version(current_content, version)
            else:
                # Generic version replacement
                new_content = re.sub(
                    r'version\s*=\s*["\'][\d.]+["\']',
                    f'version = "{version}"',
                    current_content
                )
            
            # Get SHA for update
            sha = self._extract_sha(file_result)
            
            # Update file
            result = await gh.create_or_update_file(
                owner=self.owner,
                repo=self.repo,
                path=file_path,
                content=new_content,
                message=f"Bump version to {version}",
                branch=branch,
                sha=sha
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Version updated to {version}")
            else:
                print(f"✗ Failed to update version: {result}")
            
            return success

    async def generate_changelog(
        self,
        output_path: str = "CHANGELOG.md",
        since: Optional[str] = None,
        until: Optional[str] = None,
        branch: str = "main"
    ) -> bool:
        """
        Generate changelog from commit history.

        Args:
            output_path: Output file path
            since: Start date (ISO format)
            until: End date (ISO format)
            branch: Target branch

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            print(f"Generating changelog from commits...")
            
            # Get commits
            commits_result = await gh.list_commits(
                owner=self.owner,
                repo=self.repo,
                since=since,
                until=until,
                per_page=100
            )
            
            commits = self._parse_result(commits_result)
            if not commits:
                print("No commits found")
                return False
            
            print(f"Found {len(commits)} commits")
            
            # Generate changelog content
            changelog_content = self._format_changelog(commits, since, until)
            
            # Check if file exists
            existing = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                ref=branch
            )
            sha = self._extract_sha(existing)
            
            # Create/update changelog
            result = await gh.create_or_update_file(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                content=changelog_content,
                message="Update CHANGELOG.md",
                branch=branch,
                sha=sha
            )
            
            success = self._check_success(result)
            
            if success:
                print(f"✓ Changelog generated at {output_path}")
            else:
                print(f"✗ Failed to generate changelog: {result}")
            
            return success

    async def finish_release(
        self,
        version: str,
        target: str = "main"
    ) -> bool:
        """
        Finish release by merging to target branch.

        Args:
            version: Release version
            target: Target branch (default: main)

        Returns:
            True if successful
        """
        async with GitHubTools() as gh:
            branch_name = f"release/v{version}"
            
            print(f"Finishing release v{version}")
            print(f"  Creating PR: {branch_name} → {target}")
            
            # Create PR
            pr_result = await gh.create_pull_request(
                owner=self.owner,
                repo=self.repo,
                title=f"Release v{version}",
                head=branch_name,
                base=target,
                body=f"## Release v{version}\n\nMerging release branch into {target}."
            )
            
            pr_number = self._extract_pr_number(pr_result)
            
            if not pr_number:
                print(f"✗ Failed to create PR: {pr_result}")
                return False
            
            print(f"  Created PR #{pr_number}")
            
            # Merge PR
            print(f"  Merging PR #{pr_number}")
            
            merge_result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method="squash"
            )
            
            success = self._check_merge_success(merge_result)
            
            if success:
                print(f"✓ Release v{version} merged to {target}")
            else:
                print(f"✗ Failed to merge release: {merge_result}")
            
            return success

    async def _generate_changelog_content(self, gh, version: str) -> str:
        """Generate changelog content from commits"""
        commits_result = await gh.list_commits(
            owner=self.owner,
            repo=self.repo,
            per_page=50
        )
        
        commits = self._parse_result(commits_result)
        return self._format_changelog(commits, version=version)

    def _format_changelog(
        self,
        commits: List[Dict[str, Any]],
        since: Optional[str] = None,
        until: Optional[str] = None,
        version: Optional[str] = None
    ) -> str:
        """Format commits into changelog markdown"""
        from datetime import datetime
        
        content = "# Changelog\n\n"
        
        if version:
            date = datetime.now().strftime("%Y-%m-%d")
            content += f"## [{version}] - {date}\n\n"
        else:
            content += f"Generated from commits"
            if since:
                content += f" since {since}"
            if until:
                content += f" until {until}"
            content += "\n\n"
        
        # Group commits by type
        features = []
        fixes = []
        others = []
        
        for commit in commits:
            commit_info = commit.get("commit", {})
            message = commit_info.get("message", "").split("\n")[0]
            sha = commit.get("sha", "")[:7]
            author = commit_info.get("author", {}).get("name", "Unknown")
            
            entry = f"- {message} ({sha}) by {author}"
            
            if message.lower().startswith(("feat", "add", "new")):
                features.append(entry)
            elif message.lower().startswith(("fix", "bug", "patch")):
                fixes.append(entry)
            else:
                others.append(entry)
        
        if features:
            content += "### Added\n\n"
            content += "\n".join(features) + "\n\n"
        
        if fixes:
            content += "### Fixed\n\n"
            content += "\n".join(fixes) + "\n\n"
        
        if others:
            content += "### Changed\n\n"
            content += "\n".join(others[:10]) + "\n\n"  # Limit to 10
        
        return content

    def _update_cargo_version(self, content: str, version: str) -> str:
        """Update version in Cargo.toml"""
        return re.sub(
            r'(version\s*=\s*")[^"]+(")',
            f'\\g<1>{version}\\g<2>',
            content,
            count=1
        )

    def _update_package_json_version(self, content: str, version: str) -> str:
        """Update version in package.json"""
        try:
            data = json.loads(content)
            data["version"] = version
            return json.dumps(data, indent=2)
        except:
            return re.sub(
                r'("version"\s*:\s*")[^"]+(")',
                f'\\g<1>{version}\\g<2>',
                content
            )

    def _parse_result(self, result) -> List[Dict[str, Any]]:
        """Parse API result, handling MCP response format"""
        # Handle MCP format: {'content': [{'type': 'text', 'text': '...'}]}
        if isinstance(result, dict):
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, list):
                                return parsed
                        except json.JSONDecodeError:
                            pass
            return []
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        return []

    def _extract_content(self, result) -> Optional[str]:
        """Extract file content from result"""
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            # Handle MCP result format: {'content': [{'type': 'text', 'text': '...'}]}
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text", "")
            # Fallback: try direct content field (GitHub API format)
            content = result.get("content", "")
            if content and isinstance(content, str):
                # Check if it's base64 encoded (GitHub raw API)
                import base64
                try:
                    return base64.b64decode(content).decode("utf-8")
                except:
                    return content
        return None

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

    def _extract_pr_number(self, result) -> int:
        """Extract PR number from result, handling MCP response format"""
        import re
        
        def extract_from_data(data: dict) -> int:
            if "number" in data:
                return data.get("number", 0)
            url = data.get("url", "") or data.get("html_url", "")
            if url:
                match = re.search(r'/pull/(\d+)', url)
                if match:
                    return int(match.group(1))
            return 0
        
        if isinstance(result, dict):
            num = extract_from_data(result)
            if num:
                return num
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
                            match = re.search(r'"number"\s*:\s*(\d+)', text)
                            if match:
                                return int(match.group(1))
                            match = re.search(r'/pull/(\d+)', text)
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
            match = re.search(r'"number"\s*:\s*(\d+)', result)
            if match:
                return int(match.group(1))
            match = re.search(r'/pull/(\d+)', result)
            if match:
                return int(match.group(1))
        return 0

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
                            parsed = json.loads(text)
                            if isinstance(parsed, dict):
                                return check_data(parsed)
                        except json.JSONDecodeError:
                            return "error" not in text.lower()
            return check_data(result)
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    return check_data(parsed)
            except json.JSONDecodeError:
                pass
            return "error" not in result.lower()
        return True

    def _check_merge_success(self, result) -> bool:
        """Check if merge was successful, handling MCP response format"""
        def check_data(data: dict) -> bool:
            return data.get("merged", False) or "sha" in data
        
        if isinstance(result, dict):
            if check_data(result):
                return True
            content_list = result.get("content", [])
            if isinstance(content_list, list) and content_list:
                for item in content_list:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "")
                        try:
                            parsed = json.loads(text)
                            if isinstance(parsed, dict) and check_data(parsed):
                                return True
                        except json.JSONDecodeError:
                            if '"merged":true' in text.lower() or '"sha"' in text:
                                return True
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                if isinstance(parsed, dict) and check_data(parsed):
                    return True
            except json.JSONDecodeError:
                pass
            result_lower = result.lower()
            return '"merged":true' in result_lower or '"sha"' in result_lower
        return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage releases for GitHub repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare a release
  python release_manager.py prepare owner repo --version "1.1.0" --from develop
  
  # Bump version in Cargo.toml
  python release_manager.py bump-version owner repo --file "Cargo.toml" --version "1.1.0"
  
  # Generate changelog
  python release_manager.py changelog owner repo --since "2024-01-01" --output "CHANGELOG.md"
  
  # Finish release
  python release_manager.py finish owner repo --version "1.1.0"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: prepare
    prepare_parser = subparsers.add_parser("prepare", help="Prepare a release")
    prepare_parser.add_argument("owner", help="Repository owner")
    prepare_parser.add_argument("repo", help="Repository name")
    prepare_parser.add_argument("--version", required=True, help="Release version")
    prepare_parser.add_argument("--from", dest="from_branch", default="develop", help="Source branch")
    
    # Command: bump-version
    bump_parser = subparsers.add_parser("bump-version", help="Update version number")
    bump_parser.add_argument("owner", help="Repository owner")
    bump_parser.add_argument("repo", help="Repository name")
    bump_parser.add_argument("--file", required=True, help="Version file path")
    bump_parser.add_argument("--version", required=True, help="New version")
    bump_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: changelog
    changelog_parser = subparsers.add_parser("changelog", help="Generate changelog")
    changelog_parser.add_argument("owner", help="Repository owner")
    changelog_parser.add_argument("repo", help="Repository name")
    changelog_parser.add_argument("--since", help="Start date (ISO format)")
    changelog_parser.add_argument("--until", help="End date (ISO format)")
    changelog_parser.add_argument("--output", default="CHANGELOG.md", help="Output file")
    changelog_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: finish
    finish_parser = subparsers.add_parser("finish", help="Finish release")
    finish_parser.add_argument("owner", help="Repository owner")
    finish_parser.add_argument("repo", help="Repository name")
    finish_parser.add_argument("--version", required=True, help="Release version")
    finish_parser.add_argument("--target", default="main", help="Target branch")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = ReleaseManager(args.owner, args.repo)
    
    try:
        if args.command == "prepare":
            success = await manager.prepare_release(
                version=args.version,
                from_branch=args.from_branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "bump-version":
            success = await manager.bump_version(
                file_path=args.file,
                version=args.version,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "changelog":
            success = await manager.generate_changelog(
                output_path=args.output,
                since=args.since,
                until=args.until,
                branch=args.branch
            )
            sys.exit(0 if success else 1)
            
        elif args.command == "finish":
            success = await manager.finish_release(
                version=args.version,
                target=args.target
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
