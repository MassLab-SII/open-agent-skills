"""
File Editor Script (Using utils.py)
===================================

General purpose file editor for GitHub repositories.
This script allows for modifying existing files, applying specific fixes, or performing
bulk find-and-replace operations across multiple files.

Usage:
    python file_editor.py <command> <owner> <repo> [options]

Commands:
    edit            Edit/Overwrite a file
    apply_fix       Apply a search and replace fix
    file_edit       Search and replace across multiple files
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

    # Edit by reading from local file
    python file_editor.py edit owner repo --path "src/app.js" --content-file "./local_app.js" --message "Add app.js"

    # Edit by piping content
    echo "const x = 1;" | python file_editor.py edit owner repo --path "src/x.js" --stdin --message "Add x.js"

    # Apply a specific fix (search and replace)
    python file_editor.py apply_fix mcpmark-source build-your-own-x --path "src/buggy.py" --pattern "if x = y:" --replacement "if x == y:" --message "Fix syntax error"

    # Mass edit (search and replace across multiple files)
    python file_editor.py file_edit mcpmark-source build-your-own-x --query "http://old-api.com" --replacement "https://new-api.com" --message "Migrate to HTTPS"

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

# Add skills directory to path to allow importing from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from github_content_editor.utils import GitHubTools


class FileEditor:
    """Editor class for modifying files in GitHub repositories"""
    
    def __init__(self):
        """Initialize the editor with GitHubTools"""
        self.github = GitHubTools()

    def _check_api_success(self, result: any) -> bool:
        """Check if API result indicates success."""
        if not result:
            return False
        if isinstance(result, dict) and ("commit" in result or "content" in result):
            return True
        elif isinstance(result, str):
            result_lower = result.lower()
            if "error" in result_lower or "not found" in result_lower or "failed" in result_lower:
                return False
            elif "commit" in result_lower or '"sha"' in result_lower:
                return True
        return False

    def _extract_sha(self, result) -> str:
        """Extract SHA from get_file_contents result."""
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
        """Apply a fix by replacing a specific pattern in a file."""
        async with self.github:
            print(f"Fetching current state of {path} in {owner}/{repo} on {branch}...")
            existing_file = await self.github.get_file_contents(
                owner, repo, path, ref=branch
            )
            
            if not existing_file or not isinstance(existing_file, dict) or "content" not in existing_file:
                # Note: get_file_contents usually returns metadata, but for text content we might need to decode?
                # The MCP tool get_file_contents returns the content in the 'content' field if successful.
                # However, the wrapper returns result.get('content', [])[0].get('text', '') which is the string content.
                # Wait, let's check utils.py again. create_or_update_file returns that. 
                # get_file_contents in utils.py lines 339-363 returns the same.
                # If it returns a string, it's the file content. If it returns dict, it might be the raw result.
                # Let's assume utils.py returns the text content directly if it unwraps it, OR the dict if not.
                # Re-checking utils.py logic:
                # result = await self.mcp_server.call_tool("get_file_contents", args)
                # content = result.get('content', [])
                # if content ... return content[0].get('text', '')
                # So if successful, it returns the file content string (or info string). 
                # Wait, get_file_contents (MCP) usually returns file content.
                pass

            # Getting file content via MCP might return a string description or the actual content.
            # The standard MCP get_file_contents usually returns the content.
            # However, for text replacement, we need to be sure.
            # Let's rely on what we get.
            
            # Correction: The utils.py wrapper for get_file_contents returns content[0].get('text', '')
            # which is actually the text content of the file provided by the MCP server.
            
            content = existing_file
            # Handle potential Dict result from get_file_contents (Raw MCP outcome)
            file_content = ""
            sha = None
            
            if isinstance(existing_file, str):
                file_content = existing_file
            elif isinstance(existing_file, dict):
                # Try to extract content from MCP result structure
                # Result format: {'content': [{'type': 'text', 'text': '...'}], ...}
                if 'content' in existing_file and isinstance(existing_file['content'], list):
                    for item in existing_file['content']:
                        if item.get('type') == 'text':
                            file_content = item.get('text', '')
                            break
                
                # Try to extract SHA if present (though unlikely in standard MCP result)
                if 'sha' in existing_file:
                    sha = existing_file['sha']
            
            if not file_content and not sha:
                 # If we have neither content nor sha, and we received a dict, it might be an empty file or error
                 # But if existing_file matches error pattern?
                 pass
            # Extract SHA from the result if available
            sha = self._extract_sha(existing_file)
            
            if pattern not in file_content:
                if replacement in file_content:
                    print(f"Pattern not found, but replacement found. Assuming fixed.")
                    return True
                else:
                    print(f"Pattern '{pattern}' not found in file.")
                    return False

            new_content = file_content.replace(pattern, replacement)
            
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

    async def mass_edit(
        self,
        owner: str,
        repo: str,
        query: str,
        replacement: str,
        message: str,
        branch: str = "main",
    ) -> bool:
        """Apply a mass edit across multiple files based on a search query."""
        async with self.github:
            # Construct a code search query to find files containing the string in this repo
            # search_code format: "query repo:owner/repo"
            search_query = f"{query} repo:{owner}/{repo}"
            print(f"Searching for files matching '{query}' in {owner}/{repo}...")
            
            search_results = await self.github.search_code(query=search_query, per_page=20)
            
            # Parse result if string (utils.py returns JSON string)
            if isinstance(search_results, str):
                try:
                    import json
                    search_results = json.loads(search_results)
                except json.JSONDecodeError:
                    print(f"Failed to parse search results: {search_results}")
                    return False
            
            if not search_results or not isinstance(search_results, dict):
                 print(f"Search failed or returned invalid format: {search_results}")
                 return False

            items = search_results.get("items", [])
            if not items:
                print("No files found matching the query.")
                return True

            print(f"Found {len(items)} files to potentially edit.")
            
            success_count = 0
            fail_count = 0

            for item in items:
                path = item.get("path")
                if not path:
                    continue

                print(f"Processing {path}...")
                
                # Reuse apply_fix logic internally? Or re-implement to allow simple string replace logic?
                # Let's use get_file_contents + replace to be explicit.
                
                existing_file = await self.github.get_file_contents(
                    owner, repo, path, ref=branch
                )
                
                # Handle potential Dict result
                file_content = ""
                if isinstance(existing_file, str):
                    file_content = existing_file
                elif isinstance(existing_file, dict):
                    # Try to extract content from MCP result structure
                    if 'content' in existing_file and isinstance(existing_file['content'], list):
                        for item in existing_file['content']:
                            if item.get('type') == 'text':
                                file_content = item.get('text', '')
                                break
                
                if query not in file_content:
                    print(f"  Query '{query}' not explicitly found in content (might be partial match in search). Skipping.")
                    continue

                new_content = file_content.replace(query, replacement)
                
                # Extract SHA from the result
                sha = self._extract_sha(existing_file)
                
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
                if self._check_api_success(result):
                    print(f"  Updated {path}")
                    success_count += 1
                else:
                    print(f"  Failed to update {path}: {result}")
                    fail_count += 1
            
            print(f"Mass edit completed. Updated: {success_count}, Failed: {fail_count}")
            return fail_count == 0

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
  
  # Mass edit
  python file_editor.py file_edit owner repo --query "old" --replacement "new" --message "update"
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
    
    # Command: file_edit
    mass_parser = subparsers.add_parser("file_edit", help="Search and replace across multiple files")
    mass_parser.add_argument("owner", help="Repository owner")
    mass_parser.add_argument("repo", help="Repository name")
    mass_parser.add_argument("--query", required=True, help="Search query (text to replace)")
    mass_parser.add_argument("--replacement", required=True, help="Replacement text")
    mass_parser.add_argument("--message", required=True, help="Commit message")
    mass_parser.add_argument("--branch", default="main", help="Target branch")

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
            
        elif args.command == "file_edit":
            success = await editor.mass_edit(
                args.owner, args.repo, args.query, args.replacement, args.message, args.branch
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
