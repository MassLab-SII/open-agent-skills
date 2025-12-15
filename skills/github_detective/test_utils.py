#!/usr/bin/env python3
"""
Comprehensive Unit Tests for GitHubTools
========================================
This script verifies that ALL tools in utils.py correctly marshal arguments
and invoke the underlying MCP tool. It uses mocking to avoid actual network
calls or side effects, allowing safe verification of the wrapper logic.
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure module can be imported even if run from root
try:
    import skills.github_detective.utils as utils_module
    from skills.github_detective.utils import GitHubTools
except ImportError:
    import utils as utils_module
    from utils import GitHubTools

class TestGitHubTools(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # We need to patch the server classes so proper mocks are created on init
        # Use patch.object on the imported module for robustness
        self.http_patcher = patch.object(utils_module, 'MCPHttpServer')
        self.stdio_patcher = patch.object(utils_module, 'MCPStdioServer')
        self.exists_patcher = patch('os.path.exists', return_value=False)
        
        self.MockHttp = self.http_patcher.start()
        self.MockStdio = self.stdio_patcher.start()
        self.MockExists = self.exists_patcher.start()
        
        # Setup mock instances
        self.mock_http_instance = self.MockHttp.return_value
        self.mock_http_instance.call_tool = AsyncMock(return_value={"content": [{"text": "mock_success"}]})
        
        self.mock_stdio_instance = self.MockStdio.return_value
        self.mock_stdio_instance.call_tool = AsyncMock(return_value={"content": [{"text": "mock_success"}]})

    async def asyncTearDown(self):
        self.http_patcher.stop()
        self.stdio_patcher.stop()
        self.exists_patcher.stop()

    async def verify_tool_call(self, server_mock, func_to_test, expected_tool_name, expected_args, **kwargs):
        """Helper to call a method and verify the underlying tool call"""
        await func_to_test(**kwargs)
        server_mock.call_tool.assert_called_with(expected_tool_name, expected_args)

    async def test_init_remote_with_token(self):
        with patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"}):
            gh = GitHubTools()
            self.MockHttp.assert_called()
            # Verify we are using the HTTP server
            await self.verify_tool_call(
                self.mock_http_instance,
                gh.get_me,
                "get_me",
                {}
            )

    async def test_init_local_without_token(self):
        # Ensure no token
        with patch.dict(os.environ, {}, clear=True):
            gh = GitHubTools()
            self.MockStdio.assert_called()
            # Verify we are using the Stdio server
            await self.verify_tool_call(
                self.mock_stdio_instance,
                gh.get_me,
                "get_me",
                {}
            )

    # All subsequent tests assume a valid instance (we'll use Stdio for simplicity of argument checking)
    async def setup_gh(self):
        # Note: os.path.exists is already patched to False in asyncSetUp, 
        # so .mcp_env won't interfere.
        # We also simulate strict connection via Stdio by clearing env.
        with patch.dict(os.environ, {}, clear=True):
             self.gh = GitHubTools()
             return self.mock_stdio_instance

    # ==================== Repository Management ====================

    async def test_create_repository(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.create_repository,
            "create_repository",
            {"name": "test-repo", "private": True, "description": "desc"},
            name="test-repo", private=True, description="desc"
        )

    async def test_fork_repository(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.fork_repository,
            "fork_repository",
            {"owner": "original", "repo": "repo", "organization": "my-org"},
            owner="original", repo="repo", organization="my-org"
        )

    # ==================== Branch & Commit Management ====================

    async def test_create_branch(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.create_branch,
            "create_branch",
            {"owner": "o", "repo": "r", "branch": "feature", "from_branch": "main"},
            owner="o", repo="r", branch="feature", from_branch="main"
        )

    async def test_get_commit(self):
        server = await self.setup_gh()
        # Note: Updated to match utils.py (sha, include_diff=True)
        await self.verify_tool_call(
            server,
            self.gh.get_commit,
            "get_commit",
            {"owner": "o", "repo": "r", "sha": "sha123", "include_diff": True},
            owner="o", repo="r", sha="sha123"
        )

    async def test_list_branches(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.list_branches,
            "list_branches",
            {"owner": "o", "repo": "r", "page": 1, "perPage": 30},
            owner="o", repo="r"
        )

    async def test_list_commits(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.list_commits,
            "list_commits",
            {"owner": "o", "repo": "r", "page": 1, "perPage": 30, "author": "me", "sha": "main"},
            owner="o", repo="r", author="me", sha="main"
        )

    # ==================== File Operations ====================

    async def test_create_or_update_file(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.create_or_update_file,
            "create_or_update_file",
            {"owner": "o", "repo": "r", "path": "p", "content": "c", "message": "m", "branch": "b", "sha": "s"},
            owner="o", repo="r", path="p", content="c", message="m", branch="b", sha="s"
        )

    async def test_delete_file(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.delete_file,
            "delete_file",
            {"owner": "o", "repo": "r", "path": "p", "message": "m", "branch": "b", "sha": "s"},
            owner="o", repo="r", path="p", message="m", branch="b", sha="s"
        )

    async def test_get_file_contents(self):
        server = await self.setup_gh()
        # Matches updated utils.py with sha support
        await self.verify_tool_call(
            server,
            self.gh.get_file_contents,
            "get_file_contents",
            {"owner": "o", "repo": "r", "path": "p", "ref": "main", "sha": "s"},
            owner="o", repo="r", path="p", ref="main", sha="s"
        )

    async def test_push_files(self):
        server = await self.setup_gh()
        files = [{"path": "a", "content": "b"}]
        await self.verify_tool_call(
            server,
            self.gh.push_files,
            "push_files",
            {"owner": "o", "repo": "r", "branch": "b", "files": files, "message": "m"},
            owner="o", repo="r", branch="b", files=files, message="m"
        )

    # ==================== Issues ====================

    async def test_add_issue_comment(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.add_issue_comment,
            "add_issue_comment",
            {"owner": "o", "repo": "r", "issue_number": 1, "body": "b"},
            owner="o", repo="r", issue_number=1, body="b"
        )

    async def test_assign_copilot_to_issue(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.assign_copilot_to_issue,
            "assign_copilot_to_issue",
            {"owner": "o", "repo": "r", "issue_number": 1},
            owner="o", repo="r", issue_number=1
        )

    async def test_issue_read(self):
        server = await self.setup_gh()
        # Matches updated utils.py with method
        await self.verify_tool_call(
            server,
            self.gh.issue_read,
            "issue_read",
            {"owner": "o", "repo": "r", "issue_number": 1, "method": "get_labels"},
            owner="o", repo="r", issue_number=1, method="get_labels"
        )

    async def test_issue_write(self):
        server = await self.setup_gh()
        # create
        await self.verify_tool_call(
            server,
            self.gh.issue_write,
            "issue_write",
            {"owner": "o", "repo": "r", "title": "t", "body": "b", "labels": ["l"], "method": "create"},
            owner="o", repo="r", title="t", body="b", labels=["l"], method="create"
        )
        # update
        await self.verify_tool_call(
            server,
            self.gh.issue_write,
            "issue_write",
            {"owner": "o", "repo": "r", "title": "t", "issue_number": 1, "method": "update"},
            owner="o", repo="r", title="t", issue_number=1, method="update"
        )

    async def test_list_issue_types(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.list_issue_types,
            "list_issue_types",
            {"owner": "o", "repo": "r"},
            owner="o", repo="r"
        )

    async def test_list_issues(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.list_issues,
            "list_issues",
            {"owner": "o", "repo": "r", "state": "closed", "page": 1, "perPage": 30},
            owner="o", repo="r", state="closed"
        )

    async def test_search_issues(self):
        server = await self.setup_gh()
        # Matches updated utils.py with owner/repo and query
        await self.verify_tool_call(
            server,
            self.gh.search_issues,
            "search_issues",
            {"query": "query", "page": 1, "perPage": 30, "owner": "o", "repo": "r"},
            query="query", owner="o", repo="r"
        )

    async def test_sub_issue_write(self):
        server = await self.setup_gh()
        # Matches updated utils.py with method/sub_issue_id
        await self.verify_tool_call(
            server,
            self.gh.sub_issue_write,
            "sub_issue_write",
            {"owner": "o", "repo": "r", "issue_number": 1, "method": "add", "sub_issue_id": 123},
            owner="o", repo="r", issue_number=1, method="add", sub_issue_id=123
        )

    # ==================== Pull Requests ====================

    async def test_add_comment_to_pending_review(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.add_comment_to_pending_review,
            "add_comment_to_pending_review",
            {"pull_number": 1, "body": "b"},
            pull_number=1, body="b"
        )

    async def test_create_pull_request(self):
        server = await self.setup_gh()
        # Matches updated utils.py with maintainer_can_modify
        await self.verify_tool_call(
            server,
            self.gh.create_pull_request,
            "create_pull_request",
            {"owner": "o", "repo": "r", "title": "t", "head": "h", "base": "b", "body": "desc", "draft": False, "maintainer_can_modify": True},
            owner="o", repo="r", title="t", head="h", base="b", body="desc"
        )

    async def test_list_pull_requests(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.list_pull_requests,
            "list_pull_requests",
            {"owner": "o", "repo": "r", "state": "open", "page": 1, "perPage": 30},
            owner="o", repo="r"
        )

    async def test_merge_pull_request(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.merge_pull_request,
            "merge_pull_request",
            {"owner": "o", "repo": "r", "pullNumber": 1, "merge_method": "squash"},
            owner="o", repo="r", pull_number=1, merge_method="squash"
        )

    async def test_pull_request_read(self):
        server = await self.setup_gh()
        # Matches updated utils.py with method/per_page
        await self.verify_tool_call(
            server,
            self.gh.pull_request_read,
            "pull_request_read",
            {"owner": "o", "repo": "r", "pullNumber": 1, "method": "get", "perPage": 10},
            owner="o", repo="r", pull_number=1, method="get", per_page=10
        )

    async def test_pull_request_review_write(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.pull_request_review_write,
            "pull_request_review_write",
            {"pull_number": 1, "event": "APPROVE"},
            pull_number=1, event="APPROVE"
        )

    async def test_request_copilot_review(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.request_copilot_review,
            "request_copilot_review",
            {"owner": "o", "repo": "r", "pullNumber": 1},
            owner="o", repo="r", pull_number=1
        )

    async def test_search_pull_requests(self):
        server = await self.setup_gh()
        # utils.py uses "query"
        await self.verify_tool_call(
            server,
            self.gh.search_pull_requests,
            "search_pull_requests",
            {"query": "query", "page": 1, "perPage": 30},
            query="query"
        )

    async def test_update_pull_request(self):
        server = await self.setup_gh()
        # Matches updated utils.py with labels/reviewers
        await self.verify_tool_call(
            server,
            self.gh.update_pull_request,
            "update_pull_request",
            {"owner": "o", "repo": "r", "pullNumber": 1, "title": "new", "labels": ["bug"], "reviewers": ["me"]},
            owner="o", repo="r", pull_number=1, title="new", labels=["bug"], reviewers=["me"]
        )

    async def test_update_pull_request_branch(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.update_pull_request_branch,
            "update_pull_request_branch",
            {"owner": "o", "repo": "r", "pullNumber": 1},
            owner="o", repo="r", pull_number=1
        )
            
    # ==================== Search (General) ====================

    async def test_search_code(self):
        server = await self.setup_gh()
        # utils.py uses "query"
        await self.verify_tool_call(
            server,
            self.gh.search_code,
            "search_code",
            {"query": "query", "page": 1, "perPage": 30},
            query="query"
        )

    async def test_search_users(self):
        server = await self.setup_gh()
        # utils.py uses "query"
        await self.verify_tool_call(
            server,
            self.gh.search_users,
            "search_users",
            {"query": "query", "page": 1, "perPage": 30},
            query="query"
        )
        
    async def test_search_repositories(self):
        server = await self.setup_gh()
        # utils.py uses "query"
        await self.verify_tool_call(
            server,
            self.gh.search_repositories,
            "search_repositories",
            {"query": "query", "page": 1, "perPage": 30},
            query="query"
        )

    # ==================== Teams & Users ====================

    # get_me is covered in setup tests but valid here too
    async def test_get_me(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.get_me,
            "get_me",
            {}
        )
        
    async def test_get_team_members(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.get_team_members,
            "get_team_members",
            {"org": "o", "team_slug": "s"},
            org="o", team_slug="s"
        )

    async def test_get_teams(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.get_teams,
            "get_teams",
            {"org": "o"},
            org="o"
        )

    # ==================== Other ====================

    async def test_get_label(self):
        server = await self.setup_gh()
        await self.verify_tool_call(
            server,
            self.gh.get_label,
            "get_label",
            {"owner": "o", "repo": "r", "name": "l"},
            owner="o", repo="r", name="l"
        )

if __name__ == "__main__":
    unittest.main()
