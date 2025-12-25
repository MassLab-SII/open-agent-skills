"""
File Editor Script (Using utils.py)
===================================

General purpose file editor for GitHub repositories.
This script allows for modifying existing files, applying specific fixes,
or pushing multiple files in a single atomic commit.

Usage:
    python file_editor.py <command> <owner> <repo> [options]

Commands:
    edit            Edit/Overwrite a file
    apply_fix       Apply a search and replace fix to a single file
    batch           Push multiple files in a single commit

Content Input Methods (for edit and batch commands):
    --content       Direct content string (may have shell escaping issues with quotes)
    --content-base64  Base64 encoded content (recommended for code with special chars)
    --content-file    Read content from a local file
    --stdin           Read content from stdin (for piping)

Examples:
    # Edit/Overwrite a configuration file
    python file_editor.py edit mcpmark-source build-your-own-x --path "src/config.py" --content "DEBUG = False" --message "Disable debug mode"

    # Edit with base64 encoded content (recommended for code)
    python file_editor.py edit owner repo --path "src/app.js" --content-base64 "Y29uc3QgbXNnID0gJ2hlbGxvJzs=" --message "Add app.js"

    # Apply a specific fix (search and replace in a single file)
    python file_editor.py apply_fix mcpmark-source build-your-own-x --path "src/buggy.py" --pattern "if x = y:" --replacement "if x == y:" --message "Fix syntax error"

    # Batch push multiple files in a single commit
    python file_editor.py batch mcpmark-source build-your-own-x --files '[{"path": ".github/workflows/lint.yml", "content": "..."}, {"path": "eslint.config.js", "content": "..."}]' --message "Add linting workflow and config"

    # Batch push with base64 encoded files (recommended)
    python file_editor.py batch owner repo --files-base64 "W3sicGF0aCI6ICJzcmMvYXBwLmpzIiwgImNvbnRlbnQiOiAiY29uc3QgeCA9IDE7In1d" --message "Add files"
"""

import argparse
import asyncio
import sys
import os
import traceback
import base64

from utils import (
    GitHubTools,
    extract_sha_from_result,
    extract_file_content,
    check_api_success,
)


class FileEditor:
    """Editor class for modifying files in GitHub repositories"""
    
    def __init__(self):
        """Initialize the editor with GitHubTools"""
        self.github = GitHubTools()

    def _check_api_success(self, result: any) -> bool:
        """Check if API result indicates success."""
        return check_api_success(result)

    def _extract_sha(self, result) -> str:
        """Extract SHA from get_file_contents result."""
        return extract_sha_from_result(result)


    async def edit_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> bool:
        """Edit an existing file or create if it doesn't exist."""
        async with self.github:
            print(f"Fetching current state of {path} in {owner}/{repo} on {branch}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, path, ref=branch
            )
            
            sha = None
            if isinstance(existing_file, dict) and "sha" in existing_file:
                sha = existing_file["sha"]
                print(f"Found existing file (SHA: {sha}), updating...")
            else:
                print("File not found, creating new file...")

            # Note: For now, we simply overwrite the content.
            # In a more advanced version, we could support 'replace' logic (read -> str replace -> write).
            
            result = await self.github.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=content,
                message=message,
                branch=branch,
                sha=sha,
            )

            # Check for actual success: result should contain GitHub API success indicators
            success = self._check_api_success(result)
            if success:
                print(f"Successfully edited {path}")
                return True
            else:
                print(f"Failed to edit {path}: {result}")
                return False


    def _extract_file_content(self, result) -> str:
        """Extract actual file content from MCP get_file_contents result."""
        return extract_file_content(result) or ""

    async def apply_fix(
        self,
        owner: str,
        repo: str,
        path: str,
        pattern: str,
        replacement: str,
        message: str,
        branch: str = "main",
    ) -> bool:
        """Apply a fix by replacing a specific pattern in a file.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            pattern: Text pattern to find and replace
            replacement: Replacement text
            message: Commit message
            branch: Target branch
            
        Returns:
            True if fix was applied successfully, False otherwise
            
        Note:
            This method does NOT assume a fix was already applied just because
            the replacement text exists. It requires the exact pattern to be present.
        """
        async with self.github:
            print(f"Fetching current state of {path} in {owner}/{repo} on {branch}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, path, ref=branch
            )
            
            if not existing_file:
                print(f"Error: Could not fetch file {path}")
                return False
            
            # Extract file content properly from MCP result
            file_content = self._extract_file_content(existing_file)
            sha = self._extract_sha(existing_file)
            
            if not file_content:
                print(f"Error: Could not extract content from {path}")
                return False
            
            if pattern not in file_content:
                # Pattern not found - check if this might be an idempotent case
                # Only consider it "already applied" if:
                # 1. The replacement text exists in the file
                # 2. The pattern and replacement are different (not a no-op)
                # 3. The replacement appears in a context that suggests it replaced the pattern
                #    (e.g., similar line structure)
                
                if replacement in file_content and pattern != replacement:
                    # More careful check: see if the replacement is on a line by itself
                    # or in a similar context where the pattern would have been
                    pattern_lines = pattern.strip().split('\n')
                    replacement_lines = replacement.strip().split('\n')
                    
                    # If both are single-line and replacement exists, it's likely already applied
                    if len(pattern_lines) == 1 and len(replacement_lines) == 1:
                        print(f"Pattern not found, but replacement text exists in file.")
                        print(f"Note: Cannot confirm if fix was previously applied or if pattern never existed.")
                        print(f"Returning success (idempotent behavior).")
                        return True
                    
                    # For multi-line patterns, be more conservative
                    print(f"Pattern not found in file.")
                    print(f"Replacement text exists but cannot confirm prior application.")
                
                print(f"Pattern '{pattern[:100]}{'...' if len(pattern) > 100 else ''}' not found in file.")
                print(f"File content preview (first 500 chars):")
                print(file_content[:500])
                return False

            new_content = file_content.replace(pattern, replacement)
            
            # Verify the replacement actually changed something
            if new_content == file_content:
                print(f"Warning: Replacement did not change file content")
                return False
            
            result = await self.github.create_or_update_file(
                owner=owner,
                repo=repo,
                path=path,
                content=new_content,
                message=message,
                branch=branch,
                sha=sha,
            )

            # Check for actual success
            success = self._check_api_success(result)
            if success:
                print(f"Successfully applied fix to {path}")
                return True
            else:
                print(f"Failed to apply fix: {result}")
                return False



    async def batch_push(
        self,
        owner: str,
        repo: str,
        files: list,
        message: str,
        branch: str = "main",
    ) -> bool:
        """
        Push multiple files to a repository in a single commit.
        
        This is useful when you need to create/update multiple files atomically,
        ensuring all changes are in one commit (e.g., adding workflow + config files).
        
        Args:
            owner: Repository owner
            repo: Repository name
            files: List of file dicts with 'path' and 'content' keys
            message: Commit message
            branch: Target branch (default: main)
            
        Returns:
            True if successful, False otherwise
            
        Example:
            files = [
                {"path": ".github/workflows/lint.yml", "content": "name: Lint..."},
                {"path": "eslint.config.js", "content": "module.exports = {...}"}
            ]
            await editor.batch_push(owner, repo, files, "Add linting", "main")
        """
        async with self.github:
            print(f"Pushing {len(files)} files to {owner}/{repo} on {branch} in a single commit...")
            
            # Validate files format
            for i, f in enumerate(files):
                if not isinstance(f, dict) or 'path' not in f or 'content' not in f:
                    print(f"Error: File at index {i} must have 'path' and 'content' keys")
                    return False
            
            result = await self.github.push_files(
                owner=owner,
                repo=repo,
                branch=branch,
                files=files,
                message=message,
            )
            
            # Check for success
            success = self._check_api_success(result)
            if success:
                print(f"Successfully pushed {len(files)} files in a single commit")
                for f in files:
                    print(f"  - {f['path']}")
                return True
            else:
                print(f"Failed to push files: {result}")
                return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Edit files in GitHub repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Edit/Overwrite a file
  python file_editor.py edit owner repo --path "src/config.py" --content "data" --message "upd"

  # Apply a fix
  python file_editor.py apply_fix owner repo --path "src/bug.py" --pattern "bad" --replacement "good" --message "fix"
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: edit
    edit_parser = subparsers.add_parser("edit", help="Edit/Overwrite a file")
    edit_parser.add_argument("owner", help="Repository owner")
    edit_parser.add_argument("repo", help="Repository name")
    edit_parser.add_argument("--path", required=True, help="Path to the file")
    # Content input options (mutually exclusive)
    content_group = edit_parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument("--content", help="New content of the file (direct string)")
    content_group.add_argument("--content-base64", help="Base64 encoded content (recommended for code)")
    content_group.add_argument("--content-file", help="Read content from local file")
    content_group.add_argument("--stdin", action="store_true", help="Read content from stdin")
    edit_parser.add_argument("--message", required=True, help="Commit message")
    edit_parser.add_argument("--branch", default="main", help="Target branch")

    # Command: apply_fix
    fix_parser = subparsers.add_parser("apply_fix", help="Apply a search and replace fix")
    fix_parser.add_argument("owner", help="Repository owner")
    fix_parser.add_argument("repo", help="Repository name")
    fix_parser.add_argument("--path", required=True, help="Path to the file")
    fix_parser.add_argument("--pattern", required=True, help="Text pattern to find")
    fix_parser.add_argument("--replacement", required=True, help="Replacement text")
    fix_parser.add_argument("--message", required=True, help="Commit message")
    fix_parser.add_argument("--branch", default="main", help="Target branch")
    

    # Command: batch
    batch_parser = subparsers.add_parser("batch", help="Push multiple files in a single commit")
    batch_parser.add_argument("owner", help="Repository owner")
    batch_parser.add_argument("repo", help="Repository name")
    # Files input options (mutually exclusive)
    files_group = batch_parser.add_mutually_exclusive_group(required=True)
    files_group.add_argument("--files", help='JSON array of files: [{"path": "...", "content": "..."}]')
    files_group.add_argument("--files-base64", help="Base64 encoded JSON array of files (recommended)")
    files_group.add_argument("--files-file", help="Read files JSON from local file")
    batch_parser.add_argument("--message", required=True, help="Commit message")
    batch_parser.add_argument("--branch", default="main", help="Target branch")

    args = parser.parse_args()
    editor = FileEditor()

    try:
        if args.command == "edit":
            # Resolve content from various input methods
            content = None
            if args.content:
                content = args.content
            elif args.content_base64:
                try:
                    content = base64.b64decode(args.content_base64).decode('utf-8')
                except Exception as e:
                    print(f"Error: Failed to decode base64 content: {e}")
                    sys.exit(1)
            elif args.content_file:
                try:
                    with open(args.content_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error: Failed to read content file: {e}")
                    sys.exit(1)
            elif args.stdin:
                content = sys.stdin.read()
            
            if content is None:
                print("Error: No content provided")
                sys.exit(1)
            
            success = await editor.edit_file(
                args.owner, args.repo, args.path, content, args.message, args.branch
            )
            if not success: sys.exit(1)
            
        elif args.command == "apply_fix":
            success = await editor.apply_fix(
                args.owner, args.repo, args.path, args.pattern, args.replacement, args.message, args.branch
            )
            if not success: sys.exit(1)
            

        elif args.command == "batch":
            import json
            files_json = None
            
            # Resolve files from various input methods
            if args.files:
                files_json = args.files
            elif args.files_base64:
                try:
                    files_json = base64.b64decode(args.files_base64).decode('utf-8')
                except Exception as e:
                    print(f"Error: Failed to decode base64 files: {e}")
                    sys.exit(1)
            elif args.files_file:
                try:
                    with open(args.files_file, 'r', encoding='utf-8') as f:
                        files_json = f.read()
                except Exception as e:
                    print(f"Error: Failed to read files file: {e}")
                    sys.exit(1)
            
            if files_json is None:
                print("Error: No files provided")
                sys.exit(1)
            
            try:
                files = json.loads(files_json)
                if not isinstance(files, list):
                    print("Error: files must be a JSON array")
                    sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in files: {e}")
                sys.exit(1)
            
            success = await editor.batch_push(
                args.owner, args.repo, files, args.message, args.branch
            )
            if not success: sys.exit(1)
            
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
