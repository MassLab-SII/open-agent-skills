#!/usr/bin/env python3
"""
Test Capabilities
=================
Mocked unit tests and Data-Driven Integration tests for GitHub Detective capability scripts.
"""

import unittest
import asyncio
import os
import subprocess
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from find_commit import CommitFinder
from blame_analysis import BlameAnalyzer
from contributor_stats import ContributorAnalyzer
from file_history import FileHistoryTracker

# Path to the real github_state for integration tests
GITHUB_STATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../github_state'))

class TestGitHubCapabilities(unittest.IsolatedAsyncioTestCase):
    """Unit tests with synthetic data"""

    def setUp(self):
        # Create a mock GitHubTools context manager
        self.gh_mock = MagicMock()
        self.gh_instance = AsyncMock()
        self.gh_mock.return_value.__aenter__.return_value = self.gh_instance
        
        # Patch the GitHubTools class in all modules
        self.patcher1 = patch('find_commit.GitHubTools', self.gh_mock)
        self.patcher2 = patch('blame_analysis.GitHubTools', self.gh_mock)
        self.patcher3 = patch('contributor_stats.GitHubTools', self.gh_mock)
        self.patcher4 = patch('file_history.GitHubTools', self.gh_mock)
        
        self.patcher1.start()
        self.patcher2.start()
        self.patcher3.start()
        self.patcher4.start()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()
        self.patcher4.stop()

    async def test_find_commit(self):
        # Mock responses
        dataset = [
            {"sha": "1", "commit": {"message": "Fix bug in auth", "author": {"name": "Alice", "date": "2023-01-01"}}},
            {"sha": "2", "commit": {"message": "Add feature X", "author": {"name": "Bob", "date": "2023-01-02"}}},
            {"sha": "3", "commit": {"message": "Update README", "author": {"name": "Alice", "date": "2023-01-03"}}}
        ]
        self.gh_instance.list_commits.return_value = dataset

        # Test query filtering
        finder = CommitFinder("o", "r")
        results = await finder.find_commits(query="feature")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['sha'], "2")

        # Test author filtering (logic is server-side in script usually, but script passes args)
        await finder.find_commits(author="Alice")
        self.gh_instance.list_commits.assert_called_with(
            owner="o", repo="r", author="Alice", path=None, since=None, until=None, page=1, per_page=100
        )

    async def test_blame_analysis_no_query(self):
        dataset = [
            {"sha": "1", "commit": {"message": "Update", "author": {"name": "Bob", "date": "2023-01-02"}}}
        ]
        self.gh_instance.list_commits.return_value = dataset
        
        analyzer = BlameAnalyzer("o", "r")
        results = await analyzer.analyze("path.py")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['type'], "modification")

    async def test_contributor_stats(self):
        dataset = [
            {"commit": {"author": {"name": "Alice"}}},
            {"commit": {"author": {"name": "Alice"}}},
            {"commit": {"author": {"name": "Bob"}}}
        ]
        self.gh_instance.list_commits.return_value = dataset
        
        analyzer = ContributorAnalyzer("o", "r")
        stats = await analyzer.get_stats()
        self.assertEqual(stats["Alice"], 2)
        self.assertEqual(stats["Bob"], 1)

    async def test_file_history(self):
        dataset = [
            {"sha": "1", "commit": {"message": "Init", "author": {"name": "Alice", "date": "2023-01-01"}}}
        ]
        self.gh_instance.list_commits.return_value = dataset
        
        tracker = FileHistoryTracker("o", "r")
        history = await tracker.get_history("path.py")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['message'], "Init")


class TestIntegrationRealData(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests that use REAL git data from github_state repos 
    by reading local git logs and mocking the API with them.
    This simulates 'real' execution against the repo state.
    """

    def setUp(self):
        # Target Repo: openai-harmony
        self.repo_path = os.path.join(GITHUB_STATE_DIR, 'openai-harmony/repo')
        
        # Setup mocks same as above
        self.gh_mock = MagicMock()
        self.gh_instance = AsyncMock()
        self.gh_mock.return_value.__aenter__.return_value = self.gh_instance
        
        self.patchers = [
            patch('find_commit.GitHubTools', self.gh_mock),
            patch('blame_analysis.GitHubTools', self.gh_mock),
            patch('contributor_stats.GitHubTools', self.gh_mock),
            patch('file_history.GitHubTools', self.gh_mock)
        ]
        for p in self.patchers:
            p.start()
            
        # Pre-load real commits using git log
        self.real_commits = self._load_git_commits(self.repo_path)
        # Configure list_commits to return these real commits
        self.gh_instance.list_commits.return_value = self.real_commits

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def _load_git_commits(self, repo_path):
        """Helper to load real commits from a local git repo"""
        if not os.path.exists(repo_path):
            return []
            
        # Format: SHA|Author|Date|Message
        cmd = ['git', 'log', '--pretty=format:%H|%an|%ad|%s', '-n', '100']
        try:
            output = subprocess.check_output(cmd, cwd=repo_path).decode('utf-8')
        except subprocess.CalledProcessError:
            return []
            
        commits = []
        for line in output.split('\n'):
            if not line: continue
            parts = line.split('|')
            if len(parts) < 4: continue
            
            sha = parts[0]
            author = parts[1]
            date = parts[2]
            message = parts[3]
            
            # Construct GitHub-API-like object
            commits.append({
                "sha": sha,
                "commit": {
                    "message": message,
                    "author": {
                        "name": author,
                        "date": date  # Git date format differs slightly from ISO, but usually fine for simple string checks
                    }
                }
            })
        return commits

    async def test_find_commit_harmony_format(self):
        """Test finding 'formatting' related commits in openai-harmony"""
        if not self.real_commits:
            self.skipTest("No real commits found (repo missing?)")
            
        finder = CommitFinder("openai", "harmony")
        # task: find commits about "format"
        results = await finder.find_commits(query="format")
        
        # We expect at least one because we saw 'Update harmony format' in git log
        self.assertTrue(len(results) > 0, "Should have found 'format' commits from real history")
        
        # Verify specific known commit if possible (from previous investigation)
        # 0c9c61c3... | Update harmony format
        found = any(c['sha'].startswith('0c9c61c3') for c in results)
        self.assertTrue(found, "Should find specific commit 0c9c61c3")

    async def test_contributor_stats_harmony(self):
        """Test contributor stats on real harmony history"""
        if not self.real_commits:
            self.skipTest("No real commits found")

        analyzer = ContributorAnalyzer("openai", "harmony")
        stats = await analyzer.get_stats()
        
        # We saw "Scott Lessans" and "Yuan-Man" in git log
        self.assertIn("Scott Lessans", stats)
        self.assertIn("Yuan-Man", stats)
        self.assertGreater(stats["Scott Lessans"], 0)

    async def test_file_history_readme(self):
        """Test file history for README (simulated)"""
        # Note: Since list_commits(path=...) is a server-side filter, 
        # our mock returns ALL commits. 
        # But FileHistoryTracker doesn't client-side filter by path (it relies on API).
        # SO: We need to manually filter our real_commits to simulate 'README' history 
        # OR we just accept that we get all commits and verify the format.
        # Ideally, we mock list_commits side_effect to filter if path is provided.
        
        def list_commits_side_effect(**kwargs):
            path = kwargs.get('path')
            if not path:
                return self.real_commits
                
            # Simple client-side simulation of server-side path filtering
            # We assume checking commit message for 'README' is a proxy for 'gl-search' in this test context
            # OR we just return the full list if we are lazy.
            # Let's try to filter by commits that MENTION the file in message (heuristic)
            # because we don't have file-diff info in 'git log' easily without -- name.
            filtered = [
                c for c in self.real_commits 
                if path.lower() in c['commit']['message'].lower() 
                or 'merge' in c['commit']['message'].lower() # Merges often touch everything
            ]
            return filtered

        self.gh_instance.list_commits.side_effect = list_commits_side_effect

        tracker = FileHistoryTracker("openai", "harmony")
        # We saw "improve-readme" in a merge message
        history = await tracker.get_history("README.md")
        
        self.assertTrue(len(history) > 0)
        found_merge = any("improve-readme" in e['message'] for e in history)
        self.assertTrue(found_merge, "Should find commit about readme")

if __name__ == "__main__":
    unittest.main()
