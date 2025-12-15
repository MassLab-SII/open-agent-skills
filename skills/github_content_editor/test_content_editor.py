import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import asyncio

# Add skills directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock mcp module BEFORE importing utils
mcp_mock = MagicMock()
sys.modules["mcp"] = mcp_mock
sys.modules["mcp.client.stdio"] = MagicMock()

from github_content_editor.doc_gen import DocGenerator
from github_content_editor.file_editor import FileEditor


class TestGitHubContentEditor(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch GitHubTools in doc_gen and file_editor where it is used
        self.doc_patcher = patch("github_content_editor.doc_gen.GitHubTools")
        self.file_patcher = patch("github_content_editor.file_editor.GitHubTools")
        
        self.mock_github_cls_doc = self.doc_patcher.start()
        self.mock_github_cls_file = self.file_patcher.start()
        
        # They should return the same mock instance for simplicity, or we check separate
        self.mock_github = MagicMock()
        self.mock_github_cls_doc.return_value = self.mock_github
        self.mock_github_cls_file.return_value = self.mock_github
        
        # Setup context manager mocks
        self.mock_github.__aenter__.return_value = self.mock_github
        self.mock_github.__aexit__.return_value = None
        
        # Default mock responses
        self.mock_github.get_file_contents = AsyncMock(return_value=None) # Default: file not found
        self.mock_github.create_or_update_file = AsyncMock(return_value={"content": [{"text": "Success"}]})

    async def asyncTearDown(self):
        self.doc_patcher.stop()
        self.file_patcher.stop()

    async def test_doc_gen_answer_new_file(self):
        """Test creating a new ANSWER.md"""
        generator = DocGenerator()
        # Mock that file does not exist
        self.mock_github.get_file_contents.return_value = None
        
        success = await generator.create_answer_file(
            "owner", "repo", "content", "message"
        )
        
        self.assertTrue(success)
        # Verify get_file_contents was called
        self.mock_github.get_file_contents.assert_called_with(
            "owner", "repo", "ANSWER.md", ref="main"
        )
        # Verify create_or_update_file was called with correct args for NEW file (sha=None)
        self.mock_github.create_or_update_file.assert_called_with(
            owner="owner",
            repo="repo",
            path="ANSWER.md",
            content="content",
            message="message",
            branch="main",
            sha=None
        )

    async def test_doc_gen_answer_update_file(self):
        """Test updating an existing ANSWER.md"""
        generator = DocGenerator()
        # Mock that file exists
        self.mock_github.get_file_contents.return_value = {"sha": "existing_sha"}
        
        success = await generator.create_answer_file(
            "owner", "repo", "content", "message"
        )
        
        self.assertTrue(success)
        # Verify call used the existing SHA
        self.mock_github.create_or_update_file.assert_called_with(
            owner="owner",
            repo="repo",
            path="ANSWER.md",
            content="content",
            message="message",
            branch="main",
            sha="existing_sha"
        )

    async def test_doc_gen_changelog(self):
        """Test changelog generation"""
        generator = DocGenerator()
        
        # Mock list_commits response
        self.mock_github.list_commits = AsyncMock(return_value=[
            {
                "sha": "sha123",
                "commit": {
                    "author": {"name": "Bot", "date": "2024-01-01T12:00:00Z"},
                    "message": "feat: new feature\n\nDetails"
                }
            },
            {
                "sha": "sha456",
                "commit": {
                    "author": {"name": "Dev", "date": "2024-01-02T12:00:00Z"},
                    "message": "fix: bug fix"
                }
            }
        ])
        self.mock_github.get_file_contents.return_value = None
        
        # Ensure list_commits is attached to the mock instance used by generator
        # The generator uses self.github which is a new instance of GitHubTools.
        # But we mocked the CLASS GitHubTools to return self.mock_github.
        # So generator.github IS self.mock_github.
        
        success = await generator.create_changelog(
            "owner", "repo", "CHANGELOG.md"
        )
        
        self.assertTrue(success)
        # Verify content generation (simple check)
        call_args = self.mock_github.create_or_update_file.call_args
        self.assertIsNotNone(call_args)
        content = call_args.kwargs['content']
        self.assertIn("# Changelog", content)
        self.assertIn("feat: new feature", content)
        self.assertIn("fix: bug fix", content)
        self.assertIn("2024-01-01", content)

    async def test_doc_gen_contributors(self):
        """Test contributors generation"""
        generator = DocGenerator()
        
        # Mock list_commits response
        self.mock_github.list_commits = AsyncMock(return_value=[
            {"commit": {"author": {"name": "Alice", "email": "a@example.com"}}},
            {"commit": {"author": {"name": "Alice", "email": "a@example.com"}}},
            {"commit": {"author": {"name": "Bob", "email": "b@example.com"}}}
        ])
        self.mock_github.get_file_contents.return_value = None
        
        success = await generator.create_contributors(
            "owner", "repo", "CONTRIBUTORS.md"
        )
        
        self.assertTrue(success)
        call_args = self.mock_github.create_or_update_file.call_args
        content = call_args.kwargs['content']
        self.assertIn("| Alice | 2 | a@example.com |", content)
        self.assertIn("| Bob | 1 | b@example.com |", content)

    async def test_file_editor_edit(self):
        """Test file editor logic"""
        editor = FileEditor()
        self.mock_github.get_file_contents.return_value = {"sha": "old_sha"}
        
        success = await editor.edit_file(
            "owner", "repo", "src/file.py", "new_content", "fix_bug", "dev"
        )
        
        self.assertTrue(success)
        self.mock_github.create_or_update_file.assert_called_with(
            owner="owner",
            repo="repo",
            path="src/file.py",
            content="new_content",
            message="fix_bug",
            branch="dev",
            sha="old_sha"
        )

    async def test_file_editor_apply_fix_success(self):
        """Test apply_fix success case"""
        editor = FileEditor()
        # Mock file content
        self.mock_github.get_file_contents.return_value = "var x = 1;"
        
        success = await editor.apply_fix(
            "owner", "repo", "file.js", "var x = 1;", "var x = 2;", "fix"
        )
        
        self.assertTrue(success)
        self.mock_github.create_or_update_file.assert_called()
        call_args = self.mock_github.create_or_update_file.call_args
        self.assertEqual(call_args.kwargs['content'], "var x = 2;")

    async def test_file_editor_apply_fix_idempotent(self):
        """Test apply_fix idempotent case (already fixed)"""
        editor = FileEditor()
        self.mock_github.get_file_contents.return_value = "var x = 2;"
        
        success = await editor.apply_fix(
            "owner", "repo", "file.js", "var x = 1;", "var x = 2;", "fix"
        )
        
        self.assertTrue(success)
        # Should NOT call create_or_update_file if no changes needed
        self.mock_github.create_or_update_file.assert_not_called()

    async def test_file_editor_apply_fix_fail(self):
        """Test apply_fix failure (pattern not found)"""
        editor = FileEditor()
        self.mock_github.get_file_contents.return_value = "var x = 3;"
        
        success = await editor.apply_fix(
            "owner", "repo", "file.js", "var x = 1;", "var x = 2;", "fix"
        )
        
        self.assertFalse(success)
        self.mock_github.create_or_update_file.assert_not_called()

    async def test_file_editor_mass_edit(self):
        """Test mass edit across multiple files"""
        editor = FileEditor()
        
        # Mock search_code
        self.mock_github.search_code = AsyncMock(return_value={
            "items": [
                {"path": "src/config.js"},
                {"path": "README.md"}
            ]
        })
        
        # Mock get_file_contents for different files
        # We need side_effect to return different content based on call args?
        # Or simpler: just return a string containing the query
        self.mock_github.get_file_contents.return_value = "Content with OLD_URL inside."
        
        success = await editor.mass_edit(
            "owner", "repo", "OLD_URL", "NEW_URL", "Update URLs"
        )
        
        self.assertTrue(success)
        
        # Verify search called with repo scope
        self.mock_github.search_code.assert_called_with(
            query="OLD_URL repo:owner/repo", per_page=20
        )
        
        # Verify updates called twice
        self.assertEqual(self.mock_github.create_or_update_file.call_count, 2)
        
        # Check content of first call
        call_args = self.mock_github.create_or_update_file.call_args_list[0]
        self.assertEqual(call_args.kwargs['path'], "src/config.js")
        self.assertEqual(call_args.kwargs['content'], "Content with NEW_URL inside.")

if __name__ == "__main__":
    unittest.main()
