"""
Documentation Generator Script (Using utils.py)
================================================

This script specializes in creating or updating standard documentation files
such as ANSWER.md, CHANGELOG.md, or generic markdown files. It handles the
creation of the file and pushing it to the remote repository.
It uses the GitHubTools wrapper for cleaner code and consistent API usage.

Usage:
    python doc_gen.py <command> <owner> <repo> [options]

Commands:
    answer          Create/Update ANSWER.md
    create          Create/Update generic file
    changelog       Generate CHANGELOG.md from commit history
    contributors    Generate CONTRIBUTORS.md from commit history

Examples:
    # Submit an answer file
    python doc_gen.py answer mcpmark-source build-your-own-x --content "048cd3b..." --message "Submit answer"

    # Create a generic document
    python doc_gen.py create mcpmark-source build-your-own-x --path "docs/API.md" --content "## API Documentation..." --branch "feature/docs" --message "Add API docs"

    # Generate a changelog
    python doc_gen.py changelog mcpmark-source build-your-own-x --since "2024-01-01" --branch "main"

    # Generate a contributors list
    python doc_gen.py contributors mcpmark-source build-your-own-x --output "docs/CONTRIBUTORS.md"
"""

import argparse
import asyncio
import sys
import os
from typing import Optional

# Add skills directory to path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_content_editor.utils import GitHubTools


class DocGenerator:
    """Generator that creates documentation files in GitHub repositories"""

    def __init__(self):
        """Initialize the generator with GitHubTools"""
        self.github = GitHubTools()

    # ... (rest of the class methods remain the same) ...


# ... (rest of the methods) ...


    async def create_answer_file(
        self,
        owner: str,
        repo: str,
        content: str,
        message: str = "Add ANSWER.md",
        branch: str = "main",
    ) -> bool:
        """Create or update ANSWER.md in the repository."""
        async with self.github:
            # First check if file exists to get SHA for update (if needed)
            # For ANSWER.md we usually just overwrite or create new
            print(f"Checking for existing ANSWER.md in {owner}/{repo} on {branch}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, "ANSWER.md", ref=branch
            )
            
            sha = None
            if isinstance(existing_file, dict) and "sha" in existing_file:
                sha = existing_file["sha"]
                print(f"Found existing ANSWER.md (SHA: {sha}), updating...")
            else:
                print("Creating new ANSWER.md...")

            result = await self.github.create_or_update_file(
                owner=owner,
                repo=repo,
                path="ANSWER.md",
                content=content,
                message=message,
                branch=branch,
                sha=sha,
            )
            # Check for actual success: result should contain GitHub API success indicators
            # A successful create_or_update_file returns JSON with "commit" info
            success = False
            if result:
                if isinstance(result, dict) and ("commit" in result or "content" in result):
                    success = True
                elif isinstance(result, str):
                    # Parse string result for success indicators
                    result_lower = result.lower()
                    if "error" in result_lower or "not found" in result_lower or "failed" in result_lower:
                        success = False
                    elif "commit" in result_lower or '"sha"' in result_lower:
                        success = True
                    else:
                        # Unknown format, treat as failure to be safe
                        success = False
            
            if success:
                print(f"Successfully created/updated ANSWER.md")
                return True
            else:
                print(f"Failed to create/update ANSWER.md: {result}")
                return False

    async def create_generic_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> bool:
        """Create or update any file in the repository."""
        async with self.github:
            print(f"Checking for existing {path} in {owner}/{repo} on {branch}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, path, ref=branch
            )
            
            sha = None
            if isinstance(existing_file, dict) and "sha" in existing_file:
                sha = existing_file["sha"]
                print(f"Found existing {path} (SHA: {sha}), updating...")
            else:
                print(f"Creating new {path}...")

            result = await self.github.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                branch=branch,
                sha=sha,
            )

            if result and (isinstance(result, str) or isinstance(result, dict)):
                print(f"Successfully processed {path}")
                return True
            else:
                print(f"Failed to process {path}: {result}")
                return False


    async def create_changelog(
        self,
        owner: str,
        repo: str,
        output_path: str = "CHANGELOG.md",
        since: Optional[str] = None,
        until: Optional[str] = None,
        branch: str = "main",
        message: str = "Update CHANGELOG.md"
    ) -> bool:
        """Generate and submit a changelog based on commit history."""
        async with self.github:
            print(f"Fetching commits for {owner}/{repo}...")
            commits_data = await self.github.list_commits(
                owner=owner, repo=repo, since=since, until=until, per_page=100
            )
            
            # Parse result if string (utils.py returns JSON string)
            if isinstance(commits_data, str):
                try:
                    import json
                    commits_data = json.loads(commits_data)
                except json.JSONDecodeError:
                    print(f"Failed to parse commit data: {commits_data}")
                    return False

            if not commits_data or not isinstance(commits_data, list):
                # Try parsing if it's a string response (some tools return text)
                # But typically list_commits returns a list of dicts or a JSON string
                print(f"Failed to fetch commits or no commits found: {commits_data}")
                return False

            # Generate Markdown content
            content = "# Changelog\n\n"
            content += f"Generated based on commits from {since or 'beginning'} to {until or 'now'}.\n\n"
            
            # Simple grouping by date
            commits_by_date = {}
            for commit in commits_data:
                if not isinstance(commit, dict): continue
                commit_info = commit.get("commit", {})
                author_info = commit_info.get("author", {})
                date = author_info.get("date", "Unknown Date")[:10] # YYYY-MM-DD
                message_text = commit_info.get("message", "").split("\n")[0]
                sha = commit.get("sha", "")  # Full SHA for accuracy
                author_name = author_info.get("name", "Unknown")
                
                if date not in commits_by_date:
                    commits_by_date[date] = []
                commits_by_date[date].append(f"- {message_text} ({sha}) by @{author_name}")

            for date in sorted(commits_by_date.keys(), reverse=True):
                content += f"## {date}\n\n"
                for line in commits_by_date[date]:
                    content += line + "\n"
                content += "\n"

            # Reuse create_generic_file logic manually to avoid re-entering context
            # (Since we are already in async with self.github)
            print(f"Checking for existing {output_path}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, output_path, ref=branch
            )
            
            sha = None
            if isinstance(existing_file, dict) and "sha" in existing_file:
                sha = existing_file["sha"]
                print(f"Found existing {output_path} (SHA: {sha}), updating...")
            else:
                print(f"Creating new {output_path}...")

            result = await self.github.create_or_update_file(
                owner=owner,
                repo=repo,
                path=output_path,
                content=content,
                message=message,
                branch=branch,
                sha=sha,
            )

            if result and (isinstance(result, str) or isinstance(result, dict)):
                print(f"Successfully generated {output_path}")
                return True
            else:
                print(f"Failed to generate {output_path}: {result}")
                return False

    async def create_contributors(
        self,
        owner: str,
        repo: str,
        output_path: str = "CONTRIBUTORS.md",
        branch: str = "main",
        message: str = "Update CONTRIBUTORS.md"
    ) -> bool:
        """Generate and submit a contributors list."""
        async with self.github:
            print(f"Fetching commits for {owner}/{repo} to analyze contributors...")
            # Fetch a large number of commits to get a good sample
            commits_data = await self.github.list_commits(
                owner=owner, repo=repo, per_page=100
            )

            # Parse result if string (utils.py returns JSON string)
            if isinstance(commits_data, str):
                try:
                    import json
                    commits_data = json.loads(commits_data)
                except json.JSONDecodeError:
                    print(f"Failed to parse commit data: {commits_data}")
                    return False

            if not commits_data or not isinstance(commits_data, list):
                print(f"Failed to fetch commits or no commits found: {commits_data}")
                return False

            contributors = {}
            for commit in commits_data:
                if not isinstance(commit, dict): continue
                commit_info = commit.get("commit", {})
                author = commit_info.get("author", {})
                name = author.get("name", "Unknown")
                email = author.get("email", "")
                
                key = name  # Aggregate by name
                if key not in contributors:
                    contributors[key] = {"count": 0, "email": email}
                contributors[key]["count"] += 1

            # Generate Markdown Table
            content = "# Contributors\n\n"
            content += "| Name | Commits | Email |\n"
            content += "|------|---------|-------|\n"
            
            # Sort by count descending
            sorted_contributors = sorted(contributors.items(), key=lambda x: x[1]["count"], reverse=True)
            
            for name, info in sorted_contributors:
                content += f"| {name} | {info['count']} | {info['email']} |\n"

            print(f"Checking for existing {output_path}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, output_path, ref=branch
            )
            
            sha = None
            if isinstance(existing_file, dict) and "sha" in existing_file:
                sha = existing_file["sha"]
            
            result = await self.github.create_or_update_file(
                owner=owner,
                repo=repo,
                path=output_path,
                content=content,
                message=message,
                branch=branch,
                sha=sha,
            )

            if result:
                print(f"Successfully generated {output_path}")
                return True
            return False


async def main():
    """Main entry point for the documentation generator"""
    parser = argparse.ArgumentParser(
        description="Generate and submit documentation files to GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit an answer file
  python doc_gen.py answer mcpmark-source build-your-own-x --content "048cd3b..."
  
  # Create a custom file
  python doc_gen.py create mcpmark-source build-your-own-x --path "docs/GUIDE.md" --content "# Guide" --message "Add guide"
  
  # Generate changelog
  python doc_gen.py changelog mcpmark-source build-your-own-x --since "2023-01-01"
  
  # Generate contributors list
  python doc_gen.py contributors mcpmark-source build-your-own-x --output "CONTRIBUTORS.md"
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: answer
    answer_parser = subparsers.add_parser("answer", help="Create/Update ANSWER.md")
    answer_parser.add_argument("owner", help="Repository owner")
    answer_parser.add_argument("repo", help="Repository name")
    answer_parser.add_argument("--content", required=True, help="Content of ANSWER.md")
    answer_parser.add_argument("--message", default="Add ANSWER.md", help="Commit message")
    answer_parser.add_argument("--branch", default="main", help="Target branch")

    # Command: create
    create_parser = subparsers.add_parser("create", help="Create/Update generic file")
    create_parser.add_argument("owner", help="Repository owner")
    create_parser.add_argument("repo", help="Repository name")
    create_parser.add_argument("--path", required=True, help="Path to the file")
    create_parser.add_argument("--content", required=True, help="Content of the file")
    create_parser.add_argument("--message", required=True, help="Commit message")
    create_parser.add_argument("--branch", default="main", help="Target branch")
    
    # Command: changelog
    changelog_parser = subparsers.add_parser("changelog", help="Generate CHANGELOG.md")
    changelog_parser.add_argument("owner", help="Repository owner")
    changelog_parser.add_argument("repo", help="Repository name")
    changelog_parser.add_argument("--output", default="CHANGELOG.md", help="Output file path")
    changelog_parser.add_argument("--since", help="Since date (ISO 8601)")
    changelog_parser.add_argument("--until", help="Until date (ISO 8601)")
    changelog_parser.add_argument("--branch", default="main", help="Target branch")
    changelog_parser.add_argument("--message", default="Update CHANGELOG.md", help="Commit message")

    # Command: contributors
    contrib_parser = subparsers.add_parser("contributors", help="Generate CONTRIBUTORS.md")
    contrib_parser.add_argument("owner", help="Repository owner")
    contrib_parser.add_argument("repo", help="Repository name")
    contrib_parser.add_argument("--output", default="CONTRIBUTORS.md", help="Output file path")
    contrib_parser.add_argument("--branch", default="main", help="Target branch")

    args = parser.parse_args()
    generator = DocGenerator()

    try:
        if args.command == "answer":
            success = await generator.create_answer_file(
                args.owner, args.repo, args.content, args.message, args.branch
            )
            if not success: sys.exit(1)
            
        elif args.command == "create":
            success = await generator.create_generic_file(
                args.owner, args.repo, args.path, args.content, args.message, args.branch
            )
            if not success: sys.exit(1)
            
        elif args.command == "changelog":
            success = await generator.create_changelog(
                args.owner, args.repo, args.output, args.since, args.until, args.branch, args.message
            )
            if not success: sys.exit(1)

        elif args.command == "contributors":
            success = await generator.create_contributors(
                args.owner, args.repo, args.output, args.branch
            )
            if not success: sys.exit(1)
            
        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"\\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
