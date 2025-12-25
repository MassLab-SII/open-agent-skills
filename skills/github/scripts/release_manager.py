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
    
    # Bump version in package.json
    python release_manager.py bump-version owner repo --file "package.json" --version "1.1.0" --branch release/v1.1.0
    
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
from datetime import datetime
from typing import Optional, List, Dict, Any

from utils import (
    GitHubTools,
    parse_mcp_result,
    extract_sha_from_result,
    extract_file_content,
    extract_pr_number,
    check_api_success,
    check_merge_success,
)


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
            result = await gh.create_branch(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                from_branch=from_branch
            )
            
            if not self._check_success(result):
                print(f"✗ Failed to create branch: {result}")
                return False
            
            print(f"Step 2: Generating changelog")
            changelog_content = await self._generate_changelog_content(gh, version)
            
            print(f"Step 3: Pushing changelog to release branch")
            files = [{"path": "CHANGELOG.md", "content": changelog_content}]
            result = await gh.push_files(
                owner=self.owner,
                repo=self.repo,
                branch=branch_name,
                files=files,
                message=f"Add changelog for v{version}"
            )
            
            if not self._check_success(result):
                print(f"✗ Failed to push changelog: {result}")
                return False
            
            print(f"✓ Release v{version} prepared on branch '{branch_name}'")
            print(f"  Next steps:")
            print(f"  1. Update version: python release_manager.py bump-version {self.owner} {self.repo} --file package.json --version {version} --branch {branch_name}")
            print(f"  2. Finish release: python release_manager.py finish {self.owner} {self.repo} --version {version}")
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
            file_path: Path to version file (e.g., Cargo.toml, package.json, pyproject.toml)
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
            elif file_path.endswith("pyproject.toml"):
                new_content = self._update_pyproject_version(current_content, version)
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
                print(f"✓ Version updated to {version} in {file_path}")
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
        Appends new entries to existing changelog if present.

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
                sha=branch,
                since=since,
                until=until,
                per_page=100
            )
            
            commits = self._parse_commits(commits_result)
            if not commits:
                print("No commits found")
                return False
            
            print(f"Found {len(commits)} commits")
            
            # Generate new changelog content
            new_changelog_section = self._format_changelog(commits, since, until)
            
            # Check if file exists and get existing content
            existing = await gh.get_file_contents(
                owner=self.owner,
                repo=self.repo,
                path=output_path,
                ref=branch
            )
            sha = self._extract_sha(existing)
            existing_content = self._extract_content(existing)
            
            # Merge with existing changelog if present
            if existing_content and existing_content.strip():
                # Insert new section after the header
                if existing_content.startswith("# Changelog"):
                    # Find the end of the header line
                    header_end = existing_content.find("\n")
                    if header_end != -1:
                        # Remove the "# Changelog" header from new section since it exists
                        new_section_without_header = new_changelog_section.replace("# Changelog\n\n", "")
                        changelog_content = (
                            existing_content[:header_end + 1] + 
                            "\n" + new_section_without_header + 
                            existing_content[header_end + 1:]
                        )
                    else:
                        changelog_content = new_changelog_section + "\n\n---\n\n" + existing_content
                else:
                    changelog_content = new_changelog_section + "\n\n---\n\n" + existing_content
            else:
                changelog_content = new_changelog_section
            
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
        target: str = "main",
        merge_method: str = "squash"
    ) -> bool:
        """
        Finish release by merging to target branch.

        Args:
            version: Release version
            target: Target branch (default: main)
            merge_method: Merge method (squash/merge/rebase)

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
                body=f"## Release v{version}\n\nMerging release branch into {target}.\n\n### Changes\nSee CHANGELOG.md for details."
            )
            
            pr_number = self._extract_pr_number(pr_result)
            
            if not pr_number:
                print(f"✗ Failed to create PR: {pr_result}")
                return False
            
            print(f"  Created PR #{pr_number}")
            
            # Merge PR
            print(f"  Merging PR #{pr_number} with method: {merge_method}")
            
            merge_result = await gh.merge_pull_request(
                owner=self.owner,
                repo=self.repo,
                pull_number=pr_number,
                merge_method=merge_method
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
        
        commits = self._parse_commits(commits_result)
        return self._format_changelog(commits, version=version)

    def _format_changelog(
        self,
        commits: List[Dict[str, Any]],
        since: Optional[str] = None,
        until: Optional[str] = None,
        version: Optional[str] = None
    ) -> str:
        """Format commits into changelog markdown"""
        content = "# Changelog\n\n"
        
        if version:
            date = datetime.now().strftime("%Y-%m-%d")
            content += f"## [{version}] - {date}\n\n"
        else:
            content += f"## Changes"
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
            sha = commit.get("sha", "")[:7]  # Short SHA
            author = commit_info.get("author", {}).get("name", "Unknown")
            
            entry = f"- {message} ({sha}) by {author}"
            
            msg_lower = message.lower()
            if msg_lower.startswith(("feat", "add", "new", "feature")):
                features.append(entry)
            elif msg_lower.startswith(("fix", "bug", "patch", "hotfix")):
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
            content += "\n".join(others[:15]) + "\n\n"  # Limit to 15
        
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
        """Update version in package.json safely.
        
        Uses JSON parsing to ensure only the top-level version field is updated,
        not version fields in dependencies or other nested objects.
        """
        try:
            data = json.loads(content)
            if "version" not in data:
                print("Warning: No top-level 'version' field found in package.json")
            data["version"] = version
            # Preserve formatting: detect indent from original content
            indent = 2  # default
            lines = content.split('\n')
            for line in lines[1:5]:  # Check first few lines for indent
                stripped = line.lstrip()
                if stripped and not stripped.startswith('}'):
                    indent = len(line) - len(stripped)
                    break
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except json.JSONDecodeError as e:
            # JSON parsing failed - this is unusual for package.json
            # Use a more careful regex that only matches top-level version
            print(f"Warning: Could not parse package.json as JSON: {e}")
            print("Attempting regex-based update (less safe)...")
            
            # Strategy: Find "version" that appears before any nested { }
            # This regex looks for "version": "x.y.z" that is NOT inside nested braces
            # by checking it appears early in the file (within first 500 chars typically)
            
            # Find the position of first "version" field
            version_match = re.search(r'"version"\s*:\s*"[^"]*"', content)
            if version_match:
                # Check if this appears before any nested object (indicated by second '{')
                first_brace = content.find('{')
                second_brace = content.find('{', first_brace + 1)
                
                if second_brace == -1 or version_match.start() < second_brace:
                    # Safe to replace - version appears before nested objects
                    return re.sub(
                        r'("version"\s*:\s*")[^"]+(")',
                        f'\\g<1>{version}\\g<2>',
                        content,
                        count=1
                    )
                else:
                    print("Error: Cannot safely update version - it may be in a nested object")
                    print("Please fix the package.json format manually")
                    return content  # Return unchanged to avoid corruption
            
            print("Error: No version field found in package.json")
            return content

    def _update_pyproject_version(self, content: str, version: str) -> str:
        """Update version in pyproject.toml"""
        return re.sub(
            r'(version\s*=\s*")[^"]+(")',
            f'\\g<1>{version}\\g<2>',
            content,
            count=1
        )

    def _parse_commits(self, result) -> List[Dict[str, Any]]:
        """Parse API result, handling MCP response format"""
        parsed = parse_mcp_result(result)
        return parsed if isinstance(parsed, list) else []

    def _extract_content(self, result) -> Optional[str]:
        """Extract actual file content from MCP get_file_contents result."""
        return extract_file_content(result)

    def _extract_sha(self, result) -> Optional[str]:
        """Extract SHA from result"""
        return extract_sha_from_result(result)

    def _extract_pr_number(self, result) -> int:
        """Extract PR number from result"""
        return extract_pr_number(result)

    def _check_success(self, result) -> bool:
        """Check if operation was successful"""
        return check_api_success(result)

    def _check_merge_success(self, result) -> bool:
        """Check if merge was successful"""
        return check_merge_success(result)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage releases for GitHub repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare a release
  python release_manager.py prepare owner repo --version "1.1.0" --from develop
  
  # Bump version in package.json
  python release_manager.py bump-version owner repo --file "package.json" --version "1.1.0" --branch release/v1.1.0
  
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
    bump_parser.add_argument("--file", required=True, help="Version file path (package.json/Cargo.toml/pyproject.toml)")
    bump_parser.add_argument("--version", required=True, help="New version")
    bump_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: changelog
    changelog_parser = subparsers.add_parser("changelog", help="Generate changelog")
    changelog_parser.add_argument("owner", help="Repository owner")
    changelog_parser.add_argument("repo", help="Repository name")
    changelog_parser.add_argument("--since", help="Start date (ISO format: YYYY-MM-DD)")
    changelog_parser.add_argument("--until", help="End date (ISO format: YYYY-MM-DD)")
    changelog_parser.add_argument("--output", default="CHANGELOG.md", help="Output file")
    changelog_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: finish
    finish_parser = subparsers.add_parser("finish", help="Finish release")
    finish_parser.add_argument("owner", help="Repository owner")
    finish_parser.add_argument("repo", help="Repository name")
    finish_parser.add_argument("--version", required=True, help="Release version")
    finish_parser.add_argument("--target", default="main", help="Target branch")
    finish_parser.add_argument("--merge-method", dest="merge_method", default="squash",
                              choices=["squash", "merge", "rebase"], help="Merge method")
    
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
                target=args.target,
                merge_method=args.merge_method
            )
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
