---
name: github_detective
description: This skill investigates GitHub repositories to find specific content, track code changes, explore repository structure, and analyze Pull Requests. Use this when you need to find who added specific content, search commits, or analyze PRs.
---

# GitHub Repository Investigation Skill

This skill provides comprehensive investigation capabilities for GitHub repositories:

1. **Pull Request Analysis**: Search PRs, view details, see commits and changed files
2. **Content Tracking**: Find which commit introduced specific content to a file
3. **Commit Search**: Search commits by message, author, date, or file path
4. **Repository Exploration**: Browse branches, tags, releases, and file contents

## 1. Pull Request Analysis

Search for PRs and view complete PR information including all commits and changed files.

**Use when**: You need to find a specific PR, see what commits are in a PR, or understand what files were changed.

### Example

```bash
# List recent PRs
python pr_investigator.py owner repo

# Search PRs by keyword
python pr_investigator.py owner repo --query "RAG"

# Get specific PR details (shows all commits with full SHAs)
python pr_investigator.py owner repo --number 42

# Also show files changed in the PR
python pr_investigator.py owner repo --number 42 --show-files

# Filter by state
python pr_investigator.py owner repo --state closed
```

## 2. Content Tracking

Find which commit first introduced specific content to a file.

**Use when**: You need to find when/who added a specific piece of code or text.

> Note: Always specify `--file` for reliable results. Without it, search may not work on fresh repositories. The upper limit for `max-commits` is 20.

### Example

```bash
# Find commit that added specific text to a file
python content_tracker.py owner repo --content "RAG for Document Search" --file "README.md"

# Search on a specific branch
python content_tracker.py owner repo --content "new feature" --file "README.md" --branch develop

# Increase search depth for older commits
python content_tracker.py owner repo --content "old text" --file "README.md" --max-commits 10
```

## 3. Commit Search

Search commits by message content, author, date range, or file path.

**Use when**: You need to find commits based on message keywords, specific authors, or time periods. The upper limit for `limit` is 20.

### Example

```bash
# Find commits with keyword in message
python commit_finder.py owner repo --query "fix"

# Filter by author and file path
python commit_finder.py owner repo --author "Daniel" --path "src/main.py"

# Search on a specific branch
python commit_finder.py owner repo --query "feature" --branch develop

# Date range search
python commit_finder.py owner repo --since "2024-01-01" --until "2024-06-01"

# Limit results
python commit_finder.py owner repo --query "bug" --limit 10
```

## 4. Repository Exploration

Explore repository structure: branches, tags, releases, and directory contents.

**Use when**: You need to understand repository structure, find branches/tags, or browse file contents.

### Example

```bash
# Show all repository info (branches, tags, releases)
python repo_explorer.py owner repo

# Show only branches and tags
python repo_explorer.py owner repo --show branches,tags

# List directory contents
python repo_explorer.py owner repo --show files --path "src"

# List files on a specific branch
python repo_explorer.py owner repo --show files --path "src" --branch develop
```
