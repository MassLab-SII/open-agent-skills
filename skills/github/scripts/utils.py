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

    async def get_commit(self, owner: str, repo: str, sha: str, include_diff: bool = True, **kwargs) -> Any:
        """
        Get details for a commit from a GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA
            include_diff: Whether to include diff (default True)
            **kwargs: Extra arguments (e.g. hallucinated parameters)
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            # Check if include_diff was passed in kwargs (hallucination support)
            if 'include_diff' in kwargs:
                include_diff = kwargs['include_diff']
                
            args = {"owner": owner, "repo": repo, "sha": sha, "include_diff": include_diff}
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

    async def list_commits(self, owner: str, repo: str, sha: Optional[str] = None, path: Optional[str] = None, author: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None, page: int = 1, per_page: int = 30, **kwargs) -> Any:
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
            **kwargs: Extra arguments (e.g. perPage)
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            # Handle perPage alias
            if 'perPage' in kwargs:
                per_page = kwargs['perPage']
                
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

    async def pull_request_read(self, owner: str, repo: str, pull_number: int, method: Optional[str] = None, per_page: Optional[int] = None, **kwargs) -> Any:
        """
        Get information on a specific pull request in GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            method: Optional method (e.g. "get", "get_files")
            per_page: Results per page
            **kwargs: Extra arguments (e.g. perPage)
            
        Returns:
            Tool execution result or None if failed
        """
        try:
            # Handle perPage alias
            if 'perPage' in kwargs:
                per_page = kwargs['perPage']
                
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

 # ==================== Labels ====================

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


# ==============================================================================
# Common Helper Functions (NOT MCP Tools)
# ==============================================================================
# These are utility functions for parsing MCP responses and extracting data.
# They are NOT MCP tools, just common helpers used across multiple skill scripts.
# ==============================================================================

import json
import re
import base64


def parse_mcp_result(result: Any) -> Any:
    """
    Parse MCP API result, handling the standard MCP response format.
    
    MCP format: {'content': [{'type': 'text', 'text': 'JSON_STRING'}]}
    
    Args:
        result: Raw MCP API result
        
    Returns:
        Parsed data (dict, list, or original result)
    """
    if isinstance(result, dict):
        # Check for MCP format first
        content_list = result.get("content", [])
        if isinstance(content_list, list) and content_list:
            for item in content_list:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        continue
        # Direct dict (not MCP format)
        return result
    if isinstance(result, list):
        return result
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    return result


def parse_mcp_search_result(result: Any) -> List[Dict[str, Any]]:
    """
    Parse MCP search API result, extracting 'items' from the response.
    
    Args:
        result: Raw MCP search API result
        
    Returns:
        List of items from search result
    """
    def extract_items(data: dict) -> List[Dict[str, Any]]:
        return data.get("items", [])
    
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
                            return extract_items(parsed)
                    except json.JSONDecodeError:
                        continue
        # Direct dict (not MCP format)
        return extract_items(result)
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            return extract_items(parsed) if isinstance(parsed, dict) else []
        except json.JSONDecodeError:
            return []
    return []


def extract_sha_from_result(result: Any) -> Optional[str]:
    """
    Extract SHA from MCP get_file_contents result.
    
    Args:
        result: Raw MCP API result
        
    Returns:
        SHA string or None if not found
    """
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
                        parsed = json.loads(text)
                        if isinstance(parsed, dict):
                            return parsed.get("sha")
                    except json.JSONDecodeError:
                        pass
    return None


def extract_file_content(result: Any) -> Optional[str]:
    """
    Extract actual file content from MCP get_file_contents result.
    
    The MCP result format is: {'content': [{'type': 'text', 'text': '...'}], ...}
    The 'text' field contains a JSON string with the file info including 'content' (base64) and 'sha'.
    
    Args:
        result: Raw MCP API result
        
    Returns:
        Decoded file content string or None
    """
    if not result:
        return None
    
    def decode_base64_content(b64_content: str) -> Optional[str]:
        """Safely decode base64 content, handling potential binary files."""
        try:
            b64_clean = b64_content.replace('\n', '')
            decoded_bytes = base64.b64decode(b64_clean)
            # Try UTF-8 first
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # Try latin-1 as fallback (handles most binary-ish text)
            try:
                return decoded_bytes.decode('latin-1')
            except Exception:
                return None
        except (ValueError, Exception):
            return None
    
    if isinstance(result, str):
        # Try to parse as JSON first
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and 'content' in parsed:
                return decode_base64_content(parsed['content'])
        except json.JSONDecodeError:
            return result
    
    if isinstance(result, dict):
        # MCP result format: {'content': [{'type': 'text', 'text': '...'}], ...}
        content_list = result.get('content', [])
        if isinstance(content_list, list) and content_list:
            for item in content_list:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    # The text is a JSON string containing file info
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, dict):
                            # GitHub MCP returns base64 encoded content
                            if 'content' in parsed:
                                return decode_base64_content(parsed['content'])
                    except json.JSONDecodeError:
                        # Not JSON, return as-is
                        return text
        # Direct dict with base64 content field
        content = result.get("content", "")
        if content and isinstance(content, str):
            decoded = decode_base64_content(content)
            if decoded is not None:
                return decoded
            return content
    return None


def extract_pr_number(result: Any) -> int:
    """
    Extract PR number from MCP API result.
    
    Args:
        result: Raw MCP API result
        
    Returns:
        PR number or 0 if not found
    """
    def extract_from_data(data: dict) -> int:
        # Direct number field - handle both int and string types
        if "number" in data:
            num = data.get("number", 0)
            # Handle string number (e.g., "51")
            if isinstance(num, str):
                try:
                    num = int(num)
                except (ValueError, TypeError):
                    num = 0
            if isinstance(num, int) and num > 0:
                return num
        # Extract from URL: https://github.com/owner/repo/pull/51
        url = data.get("url", "") or data.get("html_url", "")
        if url and isinstance(url, str):
            match = re.search(r'/pull/(\d+)', url)
            if match:
                return int(match.group(1))
        return 0
    
    if isinstance(result, dict):
        # Direct dict with number or url
        num = extract_from_data(result)
        if num:
            return num
        # MCP format: {'content': [{'type': 'text', 'text': '...'}]}
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
                        # Try regex on raw text - handle both "number": 51 and "number": "51"
                        match = re.search(r'"number"\s*:\s*"?(\d+)"?', text)
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
        # Try regex on raw string - handle both "number": 51 and "number": "51"
        match = re.search(r'"number"\s*:\s*"?(\d+)"?', result)
        if match:
            return int(match.group(1))
        match = re.search(r'/pull/(\d+)', result)
        if match:
            return int(match.group(1))
    return 0


def extract_issue_number(result: Any) -> int:
    """
    Extract Issue number from MCP API result.
    
    Handles multiple response formats:
    1. Direct dict with 'number' field: {"number": 51, ...}
    2. JSON string: '{"number": 51, ...}'
    3. MCP format: {'content': [{'type': 'text', 'text': '{"number": 51, ...}'}]}
    4. URL extraction: https://github.com/owner/repo/issues/51
    5. Nested JSON string: '{"type":"text","text":"{\"number\":51,...}"}'
    6. Dict with 'type':'text' and 'text' field: {'type': 'text', 'text': '{"number":...}'}
    
    Args:
        result: Raw MCP API result
        
    Returns:
        Issue number or 0 if not found
    """
    def extract_from_data(data: dict) -> int:
        # Direct number field - handle both int and string types
        if "number" in data:
            num = data.get("number", 0)
            # Handle string number (e.g., "52")
            if isinstance(num, str):
                try:
                    num = int(num)
                except (ValueError, TypeError):
                    num = 0
            if isinstance(num, int) and num > 0:
                return num
        # Extract from URL: https://github.com/owner/repo/issues/52
        url = data.get("url", "") or data.get("html_url", "")
        if url and isinstance(url, str):
            match = re.search(r'/issues/(\d+)', url)
            if match:
                return int(match.group(1))
        return 0
    
    def extract_from_string(text: str, depth: int = 0) -> int:
        """Extract issue number from a string (JSON or raw text)
        
        Args:
            text: String to extract from
            depth: Recursion depth to prevent infinite loops
        """
        if not text or not isinstance(text, str) or depth > 3:
            return 0
        
        # First try to parse as JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                # Check for direct number field
                num = extract_from_data(parsed)
                if num > 0:
                    return num
                
                # Handle nested format: {'type': 'text', 'text': '{"number":...}'}
                # This is the format returned by issue_write when it extracts content[0].text
                if parsed.get("type") == "text" and "text" in parsed:
                    nested_text = parsed.get("text", "")
                    if nested_text:
                        num = extract_from_string(nested_text, depth + 1)
                        if num > 0:
                            return num
                
                # Also check any 'text' field even without type
                if "text" in parsed:
                    nested_text = parsed.get("text", "")
                    if nested_text and isinstance(nested_text, str):
                        num = extract_from_string(nested_text, depth + 1)
                        if num > 0:
                            return num
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Try regex patterns on raw text
        # Pattern 1: "number": 51 or "number":51 or "number": "51" or "number":"51"
        match = re.search(r'"number"\s*:\s*"?(\d+)"?', text)
        if match:
            num = int(match.group(1))
            if num > 0:
                return num
        
        # Pattern 2: /issues/51
        match = re.search(r'/issues/(\d+)', text)
        if match:
            num = int(match.group(1))
            if num > 0:
                return num
        
        return 0
    
    # Handle None
    if result is None:
        return 0
    
    # Handle dict
    if isinstance(result, dict):
        # Direct dict with number or url
        num = extract_from_data(result)
        if num > 0:
            return num
        
        # Handle format: {'type': 'text', 'text': '{"number":...}'}
        # This can happen when the result is already partially parsed
        if result.get("type") == "text" and "text" in result:
            text = result.get("text", "")
            if text:
                num = extract_from_string(text)
                if num > 0:
                    return num
        
        # MCP format: {'content': [{'type': 'text', 'text': '...'}]}
        content_list = result.get("content", [])
        if isinstance(content_list, list):
            for item in content_list:
                if isinstance(item, dict):
                    # Check for 'text' type content
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        num = extract_from_string(text)
                        if num > 0:
                            return num
                    # Also check direct 'text' field without type
                    elif "text" in item:
                        text = item.get("text", "")
                        num = extract_from_string(text)
                        if num > 0:
                            return num
        
        # Try to extract from any string value in the dict
        for key, value in result.items():
            if isinstance(value, str):
                num = extract_from_string(value)
                if num > 0:
                    return num
    
    # Handle string
    if isinstance(result, str):
        num = extract_from_string(result)
        if num > 0:
            return num
    
    return 0


def extract_issue_id(result: Any) -> int:
    """
    Extract Issue database ID from MCP API result.
    
    The 'id' field is the GitHub database ID (e.g., 3753519439), which is different
    from the 'number' field (e.g., 52). The ID is required for sub_issue_write operations.
    
    Handles multiple response formats:
    1. Direct dict with 'id' field: {"id": 3753519439, ...}
    2. JSON string: '{"id": 3753519439, ...}'
    3. MCP format: {'content': [{'type': 'text', 'text': '{"id": 3753519439, ...}'}]}
    4. Nested JSON string: '{"type":"text","text":"{\"id\":3753519439,...}"}'
    5. Dict with 'type':'text' and 'text' field: {'type': 'text', 'text': '{"id":...}'}
    
    Args:
        result: Raw MCP API result
        
    Returns:
        Issue database ID or 0 if not found
    """
    def extract_from_data(data: dict) -> int:
        # Direct id field - handle both int and string types
        if "id" in data:
            issue_id = data.get("id", 0)
            # Handle string ID (e.g., "3759796333")
            if isinstance(issue_id, str):
                try:
                    issue_id = int(issue_id)
                except (ValueError, TypeError):
                    return 0
            if isinstance(issue_id, int) and issue_id > 0:
                return issue_id
        return 0
    
    def extract_from_string(text: str, depth: int = 0) -> int:
        """Extract issue ID from a string (JSON or raw text)
        
        Args:
            text: String to extract from
            depth: Recursion depth to prevent infinite loops
        """
        if not text or not isinstance(text, str) or depth > 3:
            return 0
        
        # First try to parse as JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                # Check for direct id field
                issue_id = extract_from_data(parsed)
                if issue_id > 0:
                    return issue_id
                
                # Handle nested format: {'type': 'text', 'text': '{"id":...}'}
                # This is the format returned by issue_write when it extracts content[0].text
                if parsed.get("type") == "text" and "text" in parsed:
                    nested_text = parsed.get("text", "")
                    if nested_text:
                        issue_id = extract_from_string(nested_text, depth + 1)
                        if issue_id > 0:
                            return issue_id
                
                # Also check any 'text' field even without type
                if "text" in parsed:
                    nested_text = parsed.get("text", "")
                    if nested_text and isinstance(nested_text, str):
                        issue_id = extract_from_string(nested_text, depth + 1)
                        if issue_id > 0:
                            return issue_id
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Try regex pattern on raw text - id is usually a large number
        # Pattern: "id": 3753519439 or "id":3753519439 or "id": "3753519439" or "id":"3753519439"
        # First try without quotes around the value
        match = re.search(r'"id"\s*:\s*(\d+)', text)
        if match:
            issue_id = int(match.group(1))
            if issue_id > 0:
                return issue_id
        # Then try with quotes around the value (string ID)
        match = re.search(r'"id"\s*:\s*"(\d+)"', text)
        if match:
            issue_id = int(match.group(1))
            if issue_id > 0:
                return issue_id
        
        return 0
    
    # Handle None
    if result is None:
        return 0
    
    # Handle dict
    if isinstance(result, dict):
        # Direct dict with id
        issue_id = extract_from_data(result)
        if issue_id > 0:
            return issue_id
        
        # Handle format: {'type': 'text', 'text': '{"id":...}'}
        # This can happen when the result is already partially parsed
        if result.get("type") == "text" and "text" in result:
            text = result.get("text", "")
            if text:
                issue_id = extract_from_string(text)
                if issue_id > 0:
                    return issue_id
        
        # MCP format: {'content': [{'type': 'text', 'text': '...'}]}
        content_list = result.get("content", [])
        if isinstance(content_list, list):
            for item in content_list:
                if isinstance(item, dict):
                    # Check for 'text' type content
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        issue_id = extract_from_string(text)
                        if issue_id > 0:
                            return issue_id
                    # Also check direct 'text' field without type
                    elif "text" in item:
                        text = item.get("text", "")
                        issue_id = extract_from_string(text)
                        if issue_id > 0:
                            return issue_id
        
        # Try to extract from any string value in the dict
        for key, value in result.items():
            if isinstance(value, str):
                issue_id = extract_from_string(value)
                if issue_id > 0:
                    return issue_id
    
    # Handle string
    if isinstance(result, str):
        issue_id = extract_from_string(result)
        if issue_id > 0:
            return issue_id
    
    return 0


def check_api_success(result: Any) -> bool:
    """
    Check if MCP API operation was successful.
    
    This function checks for explicit error indicators in the API response.
    It avoids false positives by only checking for specific error patterns,
    not just the presence of the word "error" in content.
    
    Args:
        result: Raw MCP API result
        
    Returns:
        True if successful, False otherwise
    """
    if not result:
        return False
    
    def check_data(data: dict) -> bool:
        # Check for explicit MCP error indicator
        if data.get("isError") is True:
            return False
        
        # Check for GitHub API error response format
        # GitHub returns {"message": "Not Found", "documentation_url": "..."} for errors
        message = data.get("message", "")
        if message:
            message_lower = str(message).lower()
            # Only treat as error if it's a known GitHub API error message
            error_messages = [
                "not found",
                "bad credentials", 
                "requires authentication",
                "forbidden",
                "validation failed",
                "unprocessable entity",
                "rate limit exceeded",
                "server error",
                "service unavailable"
            ]
            if any(err in message_lower for err in error_messages):
                # Double-check: if there's also a "documentation_url", it's definitely an error
                if data.get("documentation_url"):
                    return False
                # Or if there's no other meaningful data, it's likely an error
                if len(data) <= 2:  # Only message and maybe one other field
                    return False
        
        # Check for explicit error object (not just a field named "error" with data)
        error_field = data.get("error")
        if isinstance(error_field, dict):
            # This is an error object, not just a field
            if error_field.get("message") or error_field.get("code"):
                return False
        elif isinstance(error_field, str) and error_field:
            # Non-empty error string
            return False
        
        return True
    
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
                        # For non-JSON text, check for explicit error patterns
                        text_lower = text.lower()
                        # Check for MCP error response patterns
                        if '"iserror":true' in text_lower or '"iserror": true' in text_lower:
                            return False
                        # Check for GitHub API error format
                        if '"message":"not found"' in text_lower and '"documentation_url"' in text_lower:
                            return False
                        return True
        # Direct dict (not MCP format)
        return check_data(result)
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                return check_data(parsed)
        except json.JSONDecodeError:
            pass
        # For raw strings, check for explicit error patterns
        result_lower = result.lower()
        if '"iserror":true' in result_lower or '"iserror": true' in result_lower:
            return False
        if '"message":"not found"' in result_lower and '"documentation_url"' in result_lower:
            return False
        return True
    return True


def check_merge_success(result: Any) -> bool:
    """
    Check if PR merge operation was successful.
    
    Args:
        result: Raw MCP API result from merge_pull_request
        
    Returns:
        True if merge was successful, False otherwise
    """
    def check_data(data: dict) -> bool:
        return data.get("merged", False) or "sha" in data
    
    if isinstance(result, dict):
        # Direct dict check
        if check_data(result):
            return True
        # MCP format: {'content': [{'type': 'text', 'text': '...'}]}
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
                        # Check raw text
                        if '"merged":true' in text.lower() or '"sha"' in text:
                            return True
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and check_data(parsed):
                return True
        except json.JSONDecodeError:
            pass
        # Check raw string
        result_lower = result.lower()
        return '"merged":true' in result_lower or '"sha"' in result_lower
    return False






