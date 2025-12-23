---
name: github_detective
description: This skill investigates GitHub repositories to find specific content, track code changes, explore repository structure, and analyze Pull Requests. Use this when you need to find who added specific content, search commits, or analyze PRs.
---

# GitHub Detective Skill

This skill provides investigation and exploration capabilities for GitHub repositories using MCP GitHub tools.

## Core Concepts

In GitHub repository investigation, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations

---

## I. Skills

### 1. Pull Request Analysis

**File**: `pr_investigator.py`

**Use Cases**:
- Search for PRs by keyword
- View complete PR information including all commits
- See what files were changed in a PR

**Typical Task Examples**:
- Find the PR that introduced a specific feature
- List all commits in a specific PR
- See which files were modified in a specific PR

**Usage**:
```bash
# Usage:
#   python pr_investigator.py <owner> <repo> [options]
# Options:
#   --query <keyword>     Search PRs by keyword
#   --number <pr_number>  Get specific PR details
#   --show-files          Show files changed in PR (use with --number)
#   --state <state>       Filter by state: open/closed/all (default: all)
# Example:
python pr_investigator.py owner repo --number 42 --show-files
```

---

### 2. Content Tracking

**File**: `content_tracker.py`

**Use Cases**:
- Find which commit first introduced specific content to a file
- Track when/who added a specific piece of code or text
- Find which branches contain specific content

**Prerequisites**:
- Always specify `--file` for reliable results

**Typical Task Examples**:
- Find the commit that added a specific entry to a file
- Track when a specific function was introduced
- Find which branches contain specific content

**Usage**:
```bash
# Usage:
#   python content_tracker.py <owner> <repo> --content <text> --file <filepath> [options]
# Options:
#   --content <text>           Text content to search for (required)
#   --file <filepath>          File to search in (recommended for reliable results)
#   --branch <branch>          Specific branch to search (default: repository default branch)
#   --max-commits <n>          Maximum commits to search (max: 20)
#   --find-branches            Find which branches contain the content
# Example:
python content_tracker.py owner repo --content "def calculate" --file "src/utils.py" --branch develop
```

---

### 3. Commit Search

**File**: `commit_finder.py`

**Use Cases**:
- Find commits based on message keywords
- Filter commits by specific authors or time periods
- Search commits that modified a specific file

**Note**: This searches commit messages, not file content. Use `content_tracker.py` to find commits that added specific file content.

**Typical Task Examples**:
- Find all commits with "fix" in the message
- List commits by author "Daniel" on main branch
- Find commits between two dates

**Usage**:
```bash
# Usage:
#   python commit_finder.py <owner> <repo> [options]
# Options:
#   --query <keyword>     Search commits by message keyword
#   --author <username>   Filter by author
#   --path <filepath>     Filter by file path
#   --branch <branch>     Branch to search on (default: main)
#   --since <date>        Start date (ISO 8601 format: YYYY-MM-DD)
#   --until <date>        End date (ISO 8601 format: YYYY-MM-DD)
#   --limit <n>           Maximum results (max: 20)
# Example:
python commit_finder.py owner repo --query "fix" --author "Daniel"
```

---

### 4. Repository Exploration

**File**: `repo_explorer.py`

**Use Cases**:
- Understand repository structure
- Find branches, tags, and releases
- Browse file contents and directory structure

**Typical Task Examples**:
- List all branches in a repository
- View available releases and tags
- Browse files in a specific directory

**Usage**:
```bash
# Usage:
#   python repo_explorer.py <owner> <repo> [options]
# Options:
#   --show <items>        What to show: branches,tags,releases,files (comma-separated)
#   --path <dirpath>      Directory path for file listing (use with --show files)
#   --branch <branch>     Branch for file listing (default: main)
# Example:
python repo_explorer.py owner repo --show files --path "src" --branch develop
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases for atomic investigation operations. These are atomic operations for flexible combination.

**Note**: Code should be written without line breaks. Do not use multi-line logic or complex scripts.

### How to Run

```bash
# Usage:
#   python run_github_ops.py -c "<async_code>"
# Example:
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'README.md', ref='main')"
```

---

### Commit Investigation Tools

#### `get_commit(owner, repo, sha)`
**Use Cases**:
- Get detailed information about a specific commit
- View commit diff and changed files
- Verify commit content

**Usage**:
```bash
# Usage:
#   await github.get_commit('<owner>', '<repo>', '<commit_sha>')
# Parameters:
#   owner: Repository owner (string)
#   repo: Repository name (string)
#   sha: Commit SHA (string)
# Example:
python run_github_ops.py -c "await github.get_commit('owner', 'repo', 'abc123def456')"
```

---

#### `list_commits(owner, repo, sha=None, path=None, author=None, since=None, until=None, page=1, per_page=30)`
**Use Cases**:
- List commits on a branch
- Filter commits by file path
- Filter commits by author
- Filter commits by date range

**Usage**:
```bash
# Usage:
#   await github.list_commits('<owner>', '<repo>', sha='<branch>', path='<file>', author='<user>', since='<date>', until='<date>', per_page=<n>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   sha: Branch name or commit SHA to start from (string, optional)
#   path: Filter by file path (string, optional)
#   author: Filter by author username (string, optional)
#   since: Start date in ISO 8601 format (string, optional)
#   until: End date in ISO 8601 format (string, optional)
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30, max: 100)
# Example:
python run_github_ops.py -c "await github.list_commits('owner', 'repo', sha='main', author='username', per_page=10)"
```

---

### Pull Request Investigation Tools

#### `pull_request_read(owner, repo, pull_number, method=None, per_page=None)`
**Use Cases**:
- Get PR details (title, body, state, author)
- Get list of files changed in a PR (method='get_files')
- Get commits in a PR (method='get_commits')

**Usage**:
```bash
# Usage:
#   await github.pull_request_read('<owner>', '<repo>', <pull_number>, method='<method>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   pull_number: PR number (int, required)
#   method: Operation type (string, optional): 'get', 'get_files', 'get_commits'
#   per_page: Results per page for list operations (int, optional)
# Example:
python run_github_ops.py -c "await github.pull_request_read('owner', 'repo', 42, method='get_files')"
```

---

#### `list_pull_requests(owner, repo, state='open', page=1, per_page=30)`
**Use Cases**:
- List open/closed/all PRs in a repository
- Browse recent PRs

**Usage**:
```bash
# Usage:
#   await github.list_pull_requests('<owner>', '<repo>', state='<state>', per_page=<n>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   state: PR state filter (string, default: 'open'): 'open', 'closed', 'all'
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30)
# Example:
python run_github_ops.py -c "await github.list_pull_requests('owner', 'repo', state='closed', per_page=10)"
```

---

#### `search_pull_requests(query, page=1, per_page=30)`
**Use Cases**:
- Search PRs by keyword, author, label, etc.
- Find merged PRs
- Advanced PR filtering

**Usage**:
```bash
# Usage:
#   await github.search_pull_requests('<query>', per_page=<n>)
# Parameters:
#   query: GitHub search query (string, required)
#          Common qualifiers: repo:owner/repo, author:username, is:merged, is:open
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30)
# Example:
python run_github_ops.py -c "await github.search_pull_requests('repo:owner/repo author:username is:merged')"
```

---

### Repository Exploration Tools

#### `list_branches(owner, repo, page=1, per_page=30)`
**Use Cases**:
- List all branches in a repository
- Find feature/release branches

**Usage**:
```bash
# Usage:
#   await github.list_branches('<owner>', '<repo>', per_page=<n>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30)
# Example:
python run_github_ops.py -c "await github.list_branches('owner', 'repo')"
```

---

#### `list_tags(owner, repo)`
**Use Cases**:
- List all tags in a repository
- Find version tags

**Usage**:
```bash
# Usage:
#   await github.list_tags('<owner>', '<repo>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
# Example:
python run_github_ops.py -c "await github.list_tags('owner', 'repo')"
```

---

#### `list_releases(owner, repo)`
**Use Cases**:
- List all releases in a repository
- Find latest release information

**Usage**:
```bash
# Usage:
#   await github.list_releases('<owner>', '<repo>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
# Example:
python run_github_ops.py -c "await github.list_releases('owner', 'repo')"
```

---

#### `get_file_contents(owner, repo, path, ref=None)`
**Use Cases**:
- Read file content from repository
- Browse directory contents
- Get file content at specific branch/commit

**Usage**:
```bash
# Usage:
#   await github.get_file_contents('<owner>', '<repo>', '<path>', ref='<branch_or_sha>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   path: File or directory path (string, required)
#   ref: Branch name or commit SHA (string, optional, default: default branch)
# Example:
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'src/main.py', ref='develop')"
```

---

### Issue Investigation Tools

#### `issue_read(owner, repo, issue_number, method=None)`
**Use Cases**:
- Get issue details
- Get issue labels

**Usage**:
```bash
# Usage:
#   await github.issue_read('<owner>', '<repo>', <issue_number>, method='<method>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   issue_number: Issue number (int, required)
#   method: Operation type (string, optional): 'get_labels'
# Example:
python run_github_ops.py -c "await github.issue_read('owner', 'repo', 42)"
```

---

#### `list_issues(owner, repo, state='open', labels=None, page=1, per_page=30)`
**Use Cases**:
- List issues in a repository
- Filter by state or labels

**Usage**:
```bash
# Usage:
#   await github.list_issues('<owner>', '<repo>', state='<state>', labels=['<label>'])
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   state: Issue state filter (string, default: 'open'): 'open', 'closed', 'all'
#   labels: Filter by labels (list of strings, optional)
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30)
# Example:
python run_github_ops.py -c "await github.list_issues('owner', 'repo', state='open', labels=['bug'])"
```

---

#### `search_issues(query, page=1, per_page=30, owner=None, repo=None)`
**Use Cases**:
- Search issues by keyword
- Advanced issue filtering

**Usage**:
```bash
# Usage:
#   await github.search_issues('<query>', owner='<owner>', repo='<repo>')
# Parameters:
#   query: Search query (string, required)
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30)
#   owner: Filter by repository owner (string, optional)
#   repo: Filter by repository name (string, optional)
# Example:
python run_github_ops.py -c "await github.search_issues('memory leak', owner='owner', repo='repo')"
```

---

## III. Best Practice Recommendations

### 1. Choose the Right Approach

| Scenario                                 | Recommended Approach                 |
| ---------------------------------------- | ------------------------------------ |
| Complex PR analysis with commits + files | Use `pr_investigator.py` skill       |
| Track who added specific content         | Use `content_tracker.py` skill       |
| Simple commit lookup by SHA              | Use `get_commit()` basic tool        |
| Quick branch listing                     | Use `list_branches()` basic tool     |
| Read a single file                       | Use `get_file_contents()` basic tool |

### 2. Investigation Strategy

1. **Start broad, then narrow down**:
   - First use `list_commits()` or `list_pull_requests()` to get an overview
   - Then use `get_commit()` or `pull_request_read()` for specific details

2. **Use search for unknown targets**:
   - When you don't know the exact PR/commit, use `search_pull_requests()` or `search_issues()`
   - When you know the target, use direct read methods

3. **File-based investigation**:
   - To find who changed a file: `list_commits(path='file.py')`
   - To see file content: `get_file_contents()`
   - To track specific content: use `content_tracker.py`

---

## Usage Principles

1. **Prefer skills for complex multi-step investigations**: e.g., PR analysis, content tracking
2. **Use basic tools for simple atomic queries**: e.g., get commit, list branches, read file
3. **Combine tools flexibly**: Start with listing, then drill down to specifics
