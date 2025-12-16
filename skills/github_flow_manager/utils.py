#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP GitHub Tools Wrapper
=========================

This module provides a high-level wrapper around MCP GitHub server tools.
It simplifies common GitHub operations and makes them reusable across different skills.
Generated based on available tools in mcpmark execution logs.
"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Optional, Any, Union

from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.stdio import stdio_client

class MCPStdioServer:
    """Lightweight MCP Stdio Server wrapper"""

    def __init__(self, command: str, args: list[str], env: dict[str, str] | None = None, timeout: int = 120):
        self.params = StdioServerParameters(
            command=command, 
            args=args, 
            env={**os.environ, **(env or {})}
        )
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None

    async def __aenter__(self):
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(self.params))
        self.session = await self._stack.enter_async_context(ClientSession(read, write))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call the specified MCP tool"""
        result = await asyncio.wait_for(
            self.session.call_tool(name, arguments), 
            timeout=self.timeout
        )
        return result.model_dump()

class MCPHttpServer:
    """
    HTTP-based MCP client using the official MCP Python SDK
    (Streamable HTTP transport), aligned with mcpmark implementation.
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.url = url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout

        self._stack: Optional[AsyncExitStack] = None
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        self._stack = AsyncExitStack()
        
        # Use streamablehttp_client for HTTP transport
        read_stream, write_stream, _ = await self._stack.enter_async_context(
            streamablehttp_client(self.url, headers=self.headers)
        )

        self.session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await asyncio.wait_for(self.session.initialize(), timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._stack:
            await self._stack.aclose()
        self._stack = None
        self.session = None

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Invoke a remote tool and return the structured result."""
        if not self.session:
            raise RuntimeError("MCP HTTP client not started")
        
        result = await asyncio.wait_for(self.session.call_tool(name, arguments), timeout=self.timeout)
        return result.model_dump()


class GitHubTools:
    """
    High-level wrapper for MCP GitHub tools.
    """
    
    def __init__(self, timeout: int = 300):
        """
        Initialize the GitHub tools.
        
        Args:
            timeout: Timeout for MCP operations in seconds (default 300s for network ops)
        """
        self.timeout = timeout
        
        # Configure env to isolate npx/npm entirely from ~/.npm by setting HOME to a temp dir
        # This resolves EACCES issues when running without proper permissions on default cache
        env = os.environ.copy()
        
        # Load .mcp_env from project root if it exists
        # We assume utils.py is in skills/github-detective/, so root is ../../
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dotenv_path = os.path.join(root_dir, ".mcp_env")
        
        if os.path.exists(dotenv_path):
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path)
                # Reload env from os.environ after loading .mcp_env
                env.update(os.environ)
            except ImportError:
                print("Warning: python-dotenv not installed, skipping .mcp_env loading")

        # Handle Token Pooling: Pick one token from GITHUB_TOKENS if available
        # This matches mcpmark's behavior of rotating tokens to avoid rate limits
        selected_token = env.get("GITHUB_PERSONAL_ACCESS_TOKEN")
        if "GITHUB_TOKENS" in env:
            tokens = [t.strip() for t in env["GITHUB_TOKENS"].split(",") if t.strip()]
            if tokens:
                import random
                selected_token = random.choice(tokens)
                env["GITHUB_PERSONAL_ACCESS_TOKEN"] = selected_token
        
        # Priority 1: Use Remote Copilot MCP Server if token is available (Matches mcpmark)
        # Verify if we should use the remote server - usually if we have a token
        if selected_token:
            # print("Using Remote GitHub Copilot MCP Server (https://api.githubcopilot.com/mcp/)")
            self.mcp_server = MCPHttpServer(
                url="https://api.githubcopilot.com/mcp/",
                headers={
                    "Authorization": f"Bearer {selected_token}",
                    "User-Agent": "MCPMark/1.0"
                },
                timeout=timeout
            )
        else:
            # Priority 2: Fallback to Local Stdio Server (Open Source)
            # print("Using Local GitHub MCP Server (npx @modelcontextprotocol/server-github)")
            temp_home = os.path.join(os.path.expanduser("~"), ".mcp_temp_home")
            if not os.path.exists(temp_home):
                os.makedirs(temp_home, exist_ok=True)
            env["HOME"] = temp_home
            env["npm_config_cache"] = os.path.join(temp_home, ".npm")
            
            self.mcp_server = MCPStdioServer(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env=env,
                timeout=timeout
            )
    
    async def __aenter__(self):
        """Enter async context manager"""
        await self.mcp_server.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context manager"""
        await self.mcp_server.__aexit__(exc_type, exc, tb)

    # ==================== Repository Management ====================

    async def create_repository(self, name: str, description: Optional[str] = None, private: bool = False) -> Any:
        """
        Create a new GitHub repository in your account or specified organization
        
        Args:
            name: Repository name
            description: Repository description
            private: Visibility
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"name": name, "private": private}
            if description:
                args["description"] = description
            result = await self.mcp_server.call_tool("create_repository", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in create_repository: {e}")
            return None

    async def fork_repository(self, owner: str, repo: str, organization: Optional[str] = None) -> Any:
        """
        Fork a GitHub repository to your account or specified organization
        
        Args:
            owner: Repository owner
            repo: Repository name
            organization: Optional organization to fork into
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo}
            if organization:
                args["organization"] = organization
            result = await self.mcp_server.call_tool("fork_repository", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in fork_repository: {e}")
            return None

    # ==================== Branch & Commit Management ====================

    async def create_branch(self, owner: str, repo: str, branch: str, from_branch: Optional[str] = None) -> Any:
        """
        Create a new branch in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: New branch name
            from_branch: Optional source branch
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "branch": branch}
            if from_branch:
                args["from_branch"] = from_branch
            result = await self.mcp_server.call_tool("create_branch", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in create_branch: {e}")
            return None

    async def get_commit(self, owner: str, repo: str, sha: str) -> Any:
        """
        Get details for a commit from a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "sha": sha, "include_diff": True}
            result = await self.mcp_server.call_tool("get_commit", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_commit: {e}")
            return None

    async def list_branches(self, owner: str, repo: str, page: int = 1, per_page: int = 30) -> Any:
        """
        List branches in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "page": page, "perPage": per_page}
            result = await self.mcp_server.call_tool("list_branches", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_branches: {e}")
            return None

    async def list_commits(self, owner: str, repo: str, sha: Optional[str] = None, path: Optional[str] = None, author: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None, page: int = 1, per_page: int = 30) -> Any:
        """
        Get list of commits of a branch in a GitHub repository. Returns at least 30 results per page by default, but can return more if specified using the perPage parameter (up to 100).
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: SHA or branch to start listing from
            path: Only commits containing this file path
            author: GitHub login or email of author
            since: ISO 8601 date
            until: ISO 8601 date
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "page": page, "perPage": per_page}
            if sha: args["sha"] = sha
            if path: args["path"] = path
            if author: args["author"] = author
            if since: args["since"] = since
            if until: args["until"] = until
            result = await self.mcp_server.call_tool("list_commits", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_commits: {e}")
            return None

    # ==================== File Operations ====================

    async def create_or_update_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str, sha: Optional[str] = None) -> Any:
        """
        Create or update a single file in a GitHub repository. If updating, you must provide the SHA of the file you want to update. Use this tool to create or update a file in a GitHub repository remotely; do not use it for local file operations.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            branch: Branch name
            sha: File SHA (required for updates)
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "path": path, "content": content, "message": message, "branch": branch}
            if sha:
                args["sha"] = sha
            result = await self.mcp_server.call_tool("create_or_update_file", args)
            content_resp = result.get('content', [])
            if content_resp and len(content_resp) > 0:
                return content_resp[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in create_or_update_file: {e}")
            return None

    async def delete_file(self, owner: str, repo: str, path: str, message: str, branch: str, sha: str) -> Any:
        """
        Delete a file from a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            message: Commit message
            branch: Branch name
            sha: File SHA
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "path": path, "message": message, "branch": branch, "sha": sha}
            result = await self.mcp_server.call_tool("delete_file", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in delete_file: {e}")
            return None

    async def get_file_contents(self, owner: str, repo: str, path: str, ref: Optional[str] = None, sha: Optional[str] = None) -> Any:
        """
        Get the contents of a file or directory from a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Commit SHA or branch (optional)
            sha: Commit SHA (optional, alias for ref or specific sha param)
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "path": path}
            if ref:
                args["ref"] = ref
            if sha:
                args["sha"] = sha
            result = await self.mcp_server.call_tool("get_file_contents", args)
            return result
        except Exception as e:
            print(f"Error in get_file_contents: {e}")
            return None

    async def push_files(self, owner: str, repo: str, branch: str, files: List[Dict[str, str]], message: str) -> Any:
        """
        Push multiple files to a GitHub repository in a single commit
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            files: List of file dicts with 'path' and 'content'
            message: Commit message
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "branch": branch, "files": files, "message": message}
            result = await self.mcp_server.call_tool("push_files", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in push_files: {e}")
            return None

    # ==================== Issues ====================

    async def add_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Any:
        """
        Add a comment to a specific issue in a GitHub repository. Use this tool to add comments to pull requests as well (in this case pass pull request number as issue_number), but only if user is not asking specifically to add review comments.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue or PR number
            body: Comment content
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "issue_number": issue_number, "body": body}
            result = await self.mcp_server.call_tool("add_issue_comment", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in add_issue_comment: {e}")
            return None

    async def assign_copilot_to_issue(self, owner: str, repo: str, issue_number: int) -> Any:
        """
        Assign Copilot to a specific issue in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "issue_number": issue_number}
            result = await self.mcp_server.call_tool("assign_copilot_to_issue", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in assign_copilot_to_issue: {e}")
            return None

    async def issue_read(self, owner: str, repo: str, issue_number: int, method: Optional[str] = None) -> Any:
        """
        Get information about a specific issue in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            method: Optional method (e.g. "get_labels")
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "issue_number": issue_number}
            if method:
                args["method"] = method
            result = await self.mcp_server.call_tool("issue_read", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in issue_read: {e}")
            return None

    async def issue_write(self, owner: str, repo: str, title: str, body: Optional[str] = None, labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None, milestone: Optional[int] = None, issue_number: Optional[int] = None, state: Optional[str] = None, state_reason: Optional[str] = None, method: Optional[str] = None) -> Any:
        """
        Create a new or update an existing issue in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description
            labels: List of labels
            assignees: List of assignees
            milestone: Milestone number
            issue_number: Existing issue number (for updates)
            state: State (e.g. open, closed)
            state_reason: Reason for state change
            method: Method (create or update), optional if issue_number provided
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            # Default method logic if not provided
            if not method:
                method = "update" if issue_number else "create"
            
            args = {"owner": owner, "repo": repo, "title": title, "method": method}
            if body: args["body"] = body
            if labels: args["labels"] = labels
            if assignees: args["assignees"] = assignees
            if milestone: args["milestone"] = milestone
            if issue_number: args["issue_number"] = issue_number
            if state: args["state"] = state
            if state_reason: args["state_reason"] = state_reason
            
            result = await self.mcp_server.call_tool("issue_write", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in issue_write: {e}")
            return None

    async def list_issue_types(self, owner: str, repo: str) -> Any:
        """
        List supported issue types for repository owner (organization).
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo}
            result = await self.mcp_server.call_tool("list_issue_types", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_issue_types: {e}")
            return None

    async def list_issues(self, owner: str, repo: str, state: str = "open", labels: Optional[List[str]] = None, page: int = 1, per_page: int = 30) -> Any:
        """
        List issues in a GitHub repository. For pagination, use the 'endCursor' from the previous response's 'pageInfo' in the 'after' parameter.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state (open/closed/all)
            labels: List of label names
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "state": state, "page": page, "perPage": per_page}
            if labels: args["labels"] = labels
            result = await self.mcp_server.call_tool("list_issues", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_issues: {e}")
            return None

    async def search_issues(self, query: str, page: int = 1, per_page: int = 30, owner: Optional[str] = None, repo: Optional[str] = None) -> Any:
        """
        Search for issues in GitHub repositories using issues search syntax already scoped to is:issue
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            owner: Optional owner to filter by
            repo: Optional repo to filter by
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            # The MCP tool expects 'q' for the query string specifically for issues search
            args = {"query": query, "page": page, "perPage": per_page}
            if owner: args["owner"] = owner
            if repo: args["repo"] = repo
            result = await self.mcp_server.call_tool("search_issues", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in search_issues: {e}")
            return None

    async def sub_issue_write(self, owner: str, repo: str, issue_number: int, title: Optional[str] = None, method: Optional[str] = None, sub_issue_id: Optional[int] = None) -> Any:
        """
        Add a sub-issue to a parent issue in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Parent issue number
            title: Sub-issue title (required for creating new)
            method: Method (e.g. "add" to add existing issue)
            sub_issue_id: ID of existing issue to add as sub-issue
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "issue_number": issue_number}
            if title: args["title"] = title
            if method: args["method"] = method
            if sub_issue_id: args["sub_issue_id"] = sub_issue_id
            result = await self.mcp_server.call_tool("sub_issue_write", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in sub_issue_write: {e}")
            return None

    # ==================== Pull Requests ====================

    async def add_comment_to_pending_review(self, **kwargs) -> Any:
        """
        Add review comment to the requester's latest pending pull request review. A pending review needs to already exist to call this (check with the user if not sure).
        
        Args:
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            result = await self.mcp_server.call_tool("add_comment_to_pending_review", kwargs)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in add_comment_to_pending_review: {e}")
            return None

    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: Optional[str] = None, draft: bool = False, maintainer_can_modify: bool = True) -> Any:
        """
        Create a new pull request in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Head branch
            base: Base branch
            body: PR description
            draft: Whether to create as draft
            maintainer_can_modify: Whether maintainers can modify the PR
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "title": title, "head": head, "base": base, "draft": draft, "maintainer_can_modify": maintainer_can_modify}
            if body:
                args["body"] = body
            result = await self.mcp_server.call_tool("create_pull_request", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in create_pull_request: {e}")
            return None

    async def list_pull_requests(self, owner: str, repo: str, state: str = "open", page: int = 1, per_page: int = 30) -> Any:
        """
        List pull requests in a GitHub repository. If the user specifies an author, then DO NOT use this tool and use the search_pull_requests tool instead.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open/closed/all)
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "state": state, "page": page, "perPage": per_page}
            result = await self.mcp_server.call_tool("list_pull_requests", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_pull_requests: {e}")
            return None

    async def merge_pull_request(self, owner: str, repo: str, pull_number: int, merge_method: str = "merge", commit_title: Optional[str] = None, commit_message: Optional[str] = None) -> Any:
        """
        Merge a pull request in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            merge_method: Merge method (merge/squash/rebase)
            commit_title: Optional commit title
            commit_message: Optional commit message
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "pullNumber": pull_number, "merge_method": merge_method}
            if commit_title: args["commit_title"] = commit_title
            if commit_message: args["commit_message"] = commit_message
            result = await self.mcp_server.call_tool("merge_pull_request", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in merge_pull_request: {e}")
            return None

    async def pull_request_read(self, owner: str, repo: str, pull_number: int, method: Optional[str] = None, per_page: Optional[int] = None) -> Any:
        """
        Get information on a specific pull request in GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            method: Optional method (e.g. "get", "get_files")
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "pullNumber": pull_number}
            if method: args["method"] = method
            if per_page: args["perPage"] = per_page
            result = await self.mcp_server.call_tool("pull_request_read", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in pull_request_read: {e}")
            return None

    async def pull_request_review_write(self, **kwargs) -> Any:
        """
        Create and/or submit, delete review of a pull request.
        Available methods:
        - create: Create a new review of a pull request.
        - submit_pending: Submit an existing pending review.
        - delete_pending: Delete an existing pending review.
        
        Args:
            **kwargs: Arguments for review operations
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            result = await self.mcp_server.call_tool("pull_request_review_write", kwargs)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in pull_request_review_write: {e}")
            return None

    async def request_copilot_review(self, owner: str, repo: str, pull_number: int) -> Any:
        """
        Request a GitHub Copilot code review for a pull request. Use this for automated feedback on pull requests, usually before requesting a human reviewer.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "pullNumber": pull_number}
            result = await self.mcp_server.call_tool("request_copilot_review", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in request_copilot_review: {e}")
            return None

    async def search_pull_requests(self, query: str, page: int = 1, per_page: int = 30) -> Any:
        """
        Search for pull requests in GitHub repositories using issues search syntax already scoped to is:pr
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"query": query, "page": page, "perPage": per_page}
            result = await self.mcp_server.call_tool("search_pull_requests", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in search_pull_requests: {e}")
            return None

    async def update_pull_request(self, owner: str, repo: str, pull_number: int, title: Optional[str] = None, body: Optional[str] = None, state: Optional[str] = None, labels: Optional[List[str]] = None, reviewers: Optional[List[str]] = None) -> Any:
        """
        Update an existing pull request in a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            title: New title
            body: New description
            state: New state
            labels: List of labels to set
            reviewers: List of reviewers to request
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "pullNumber": pull_number}
            if title: args["title"] = title
            if body: args["body"] = body
            if state: args["state"] = state
            if labels: args["labels"] = labels
            if reviewers: args["reviewers"] = reviewers
            result = await self.mcp_server.call_tool("update_pull_request", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in update_pull_request: {e}")
            return None

    async def update_pull_request_branch(self, owner: str, repo: str, pull_number: int) -> Any:
        """
        Update the branch of a pull request with the latest changes from the base branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "pullNumber": pull_number}
            result = await self.mcp_server.call_tool("update_pull_request_branch", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in update_pull_request_branch: {e}")
            return None

    # ==================== Releases & Tags ====================

    async def get_latest_release(self, owner: str, repo: str) -> Any:
        """
        Get the latest release in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo}
            result = await self.mcp_server.call_tool("get_latest_release", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_latest_release: {e}")
            return None

    async def get_release_by_tag(self, owner: str, repo: str, tag: str) -> Any:
        """
        Get a specific release by its tag name in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            tag: Tag name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "tag": tag}
            result = await self.mcp_server.call_tool("get_release_by_tag", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_release_by_tag: {e}")
            return None

    async def get_tag(self, owner: str, repo: str, tag: str) -> Any:
        """
        Get details about a specific git tag in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            tag: Tag name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "tag": tag}
            result = await self.mcp_server.call_tool("get_tag", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_tag: {e}")
            return None

    async def list_releases(self, owner: str, repo: str) -> Any:
        """
        List releases in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo}
            result = await self.mcp_server.call_tool("list_releases", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_releases: {e}")
            return None

    async def list_tags(self, owner: str, repo: str) -> Any:
        """
        List git tags in a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo}
            result = await self.mcp_server.call_tool("list_tags", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in list_tags: {e}")
            return None

    # ==================== Search (General) ====================
    
    # ⚠️ MCPMARK LIMITATION WARNING ⚠️
    # search_code relies on GitHub's code search index which does NOT work on:
    # - Newly created repositories (not indexed yet)
    # - Private repositories (slower/limited indexing)
    # - Forked repositories (may not be indexed)
    # 
    # In MCPMark testing, all repos are newly created and private, so search_code
    # will ALWAYS return empty results. Use alternative approaches:
    # - For finding commits: use list_commits + get_commit
    # - For finding files: use get_file_contents with known paths
    # - For PR analysis: use pr_investigator which uses list_commits(sha=head_ref)

    async def search_code(self, query: str, page: int = 1, per_page: int = 30) -> Any:
        """
        ⚠️ WARNING: This tool does NOT work on newly created/private repositories!
        
        In MCPMark testing, all repos are newly created and private, so this tool
        will return empty results. Use list_commits + get_commit instead.
        
        Fast and precise code search across indexed GitHub repositories using 
        GitHub's native search engine. Best for finding exact symbols, functions, 
        classes, or specific code patterns in PUBLIC, ESTABLISHED repositories.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed (often empty for new/private repos)
        """
        try:
            args = {"query": query, "page": page, "perPage": per_page}
            result = await self.mcp_server.call_tool("search_code", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in search_code: {e}")
            return None

    async def search_repositories(self, query: str, page: int = 1, per_page: int = 30) -> Any:
        """
        Find GitHub repositories by name, description, readme, topics, or other metadata. Perfect for discovering projects, finding examples, or locating specific repositories across GitHub.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"query": query, "page": page, "perPage": per_page}
            result = await self.mcp_server.call_tool("search_repositories", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in search_repositories: {e}")
            return None

    async def search_users(self, query: str, page: int = 1, per_page: int = 30) -> Any:
        """
        Find GitHub users by username, real name, or other profile information. Useful for locating developers, contributors, or team members.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"query": query, "page": page, "perPage": per_page}
            result = await self.mcp_server.call_tool("search_users", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in search_users: {e}")
            return None

    # ==================== Teams & Users ====================

    async def get_me(self) -> Any:
        """
        Get details of the authenticated GitHub user. Use this when a request is about the user's own profile for GitHub. Or when information is missing to build other tool calls.
        
        Returns:
            Tool execution result or None if failed
        """
        try:
            result = await self.mcp_server.call_tool("get_me", {})
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_me: {e}")
            return None

    async def get_team_members(self, org: str, team_slug: str) -> Any:
        """
        Get member usernames of a specific team in an organization. Limited to organizations accessible with current credentials
        
        Args:
            org: Organization name
            team_slug: Team slug
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"org": org, "team_slug": team_slug}
            result = await self.mcp_server.call_tool("get_team_members", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_team_members: {e}")
            return None

    async def get_teams(self, org: str) -> Any:
        """
        Get details of the teams the user is a member of. Limited to organizations accessible with current credentials
        
        Args:
            org: Organization name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"org": org}
            result = await self.mcp_server.call_tool("get_teams", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_teams: {e}")
            return None

    # ==================== Other ====================

    async def get_label(self, owner: str, repo: str, name: str) -> Any:
        """
        Get a specific label from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            name: Label name
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            args = {"owner": owner, "repo": repo, "name": name}
            result = await self.mcp_server.call_tool("get_label", args)
            content = result.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            return result
        except Exception as e:
            print(f"Error in get_label: {e}")
            return None
