---
name: github_branch_strategist
description: This skill provides comprehensive branch management for GitHub repositories. It supports creating branches with any name, GitFlow-style branches, release management with version bumping and changelog generation, and cross-branch commit analysis.
---

# GitHub Branch Strategist Skill

This skill is based on Github MCP tools, providing branch management and GitFlow workflow capabilities for GitHub repositories.

## Core Concepts

In GitHub branch management, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations

---

## I. Skills

### 1. Branch Management

**File**: `branch_manager.py`

**Use Cases**:
- Create branches with any name (test/, doc/, etc.)
- Create GitFlow-style branches (feature/, release/, hotfix/)
- List all branches in a repository

**Typical Task Examples**:
- Create a feature branch from develop
- Create a release branch for version 2.0.0
- List all branches to see current state

**Usage**:
```bash
# Usage:
#   python branch_manager.py <command> <owner> <repo> [options]
# Commands:
#   create      Create a branch with any name
#   feature     Create a feature branch (feature/<name>)
#   release     Create a release branch (release/v<version>)
#   hotfix      Create a hotfix branch (hotfix/<name>)
#   list        List all branches
#
# create options:
#   --name <branch_name>  Full branch name (required)
#   --from <branch>       Source branch (default: main)
#
# feature options:
#   --name <name>         Feature name without prefix (required)
#   --from <branch>       Source branch (default: develop)
#
# release options:
#   --version <version>   Version number (required)
#   --from <branch>       Source branch (default: develop)
#
# hotfix options:
#   --name <name>         Hotfix name without prefix (required)
#   --from <branch>       Source branch (default: main)
#
# Example:
python branch_manager.py create owner repo --name "test/integration-tests" --from main
python branch_manager.py feature owner repo --name "user-authentication" --from develop
python branch_manager.py release owner repo --version "2.0.0" --from develop
```

---

### 2. GitFlow Workflow

**File**: `gitflow_manager.py`

**Use Cases**:
- Initialize GitFlow structure (create develop branch)
- Finish feature/release/hotfix branches (create PR and merge)

**Note**: For creating branches, use `branch_manager.py`.

**Typical Task Examples**:
- Initialize GitFlow for a new repository
- Finish a feature by merging to develop
- Finish a release by merging to main

**Usage**:
```bash
# Usage:
#   python gitflow_manager.py <command> <owner> <repo> [options]
# Commands:
#   init        Initialize GitFlow (create develop from main)
#   finish      Finish a branch (create PR and merge)
#
# init options:
#   (no additional options)
#
# finish options:
#   --type <type>           Branch type: feature/release/hotfix (required)
#   --name <name>           Branch name without prefix (required)
#   --target <branch>       Target branch to merge into (required)
#   --merge-method <m>      Merge method: squash/merge/rebase (default: squash)
#
# Example:
python gitflow_manager.py init owner repo
python gitflow_manager.py finish owner repo --type feature --name "user-auth" --target develop
python gitflow_manager.py finish owner repo --type release --name "2.0.0" --target main --merge-method merge
```

---

### 3. Release Management

**File**: `release_manager.py`

**Use Cases**:
- Prepare releases (create release branch + changelog)
- Bump version numbers in config files
- Generate changelogs from commit history
- Finish releases (merge to main)

**Typical Task Examples**:
- Prepare version 2.1.0 release from develop
- Update version in package.json
- Generate changelog for the past month

**Usage**:
```bash
# Usage:
#   python release_manager.py <command> <owner> <repo> [options]
# Commands:
#   prepare       Prepare a release (create branch + changelog)
#   bump-version  Update version in config file
#   changelog     Generate changelog from commits
#   finish        Finish release (merge to main)
#
# prepare options:
#   --version <version>   Version number (required)
#   --from <branch>       Source branch (default: develop)
#
# bump-version options:
#   --file <filepath>     Config file path: package.json/Cargo.toml/pyproject.toml (required)
#   --version <version>   New version number (required)
#   --branch <branch>     Target branch (required)
#
# changelog options:
#   --since <date>        Start date in ISO 8601 format (required)
#   --until <date>        End date in ISO 8601 format (optional)
#   --output <path>       Output file path (default: CHANGELOG.md)
#
# finish options:
#   --version <version>   Version number (required)
#
# Example:
python release_manager.py prepare owner repo --version "2.1.0" --from develop
python release_manager.py bump-version owner repo --file "package.json" --version "2.1.0" --branch release/v2.1.0
python release_manager.py changelog owner repo --since "2024-01-01" --output "CHANGELOG.md"
python release_manager.py finish owner repo --version "2.1.0"
```

---

### 4. Branch Analysis

**File**: `branch_analyzer.py`

**Use Cases**:
- Aggregate commits from multiple branches
- Analyze top contributors
- Generate comprehensive branch reports

**Typical Task Examples**:
- Get recent commits from main, develop, and feature branches
- Find top 10 contributors on main branch
- Generate a branch report for documentation

**Usage**:
```bash
# Usage:
#   python branch_analyzer.py <command> <owner> <repo> [options]
# Commands:
#   aggregate     Aggregate commits from multiple branches
#   contributors  Analyze top contributors
#   report        Generate comprehensive branch report
#
# aggregate options:
#   --branches <csv>      Comma-separated branch names (required)
#   --per-branch <n>      Commits per branch (default: 10)
#   --output <path>       Output JSON file (optional)
#
# contributors options:
#   --branch <branch>     Specific branch to analyze (optional, default: all)
#   --top <n>             Number of top contributors (default: 10)
#
# report options:
#   --output <path>       Output file path (default: BRANCH_REPORT.md)
#
# Example:
python branch_analyzer.py aggregate owner repo --branches "main,develop,feature/auth" --per-branch 5
python branch_analyzer.py contributors owner repo --branch main --top 10
python branch_analyzer.py report owner repo --output "BRANCH_REPORT.md"
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases for atomic branch operations. These are atomic operations for flexible combination. 

**Note**: Code should be written without line breaks. Do not use multi-line logic or complex scripts.

### How to Run

```bash
# Usage:
#   python run_github_ops.py -c "<async_code>"
# Example:
python run_github_ops.py -c "await github.create_branch('owner', 'repo', 'feature/new', from_branch='main')"
```

---

### Branch Tools

#### `create_branch(owner, repo, branch, from_branch=None)`
**Use Cases**:
- Create a new branch
- Create branch from specific source branch

**Usage**:
```bash
# Usage:
#   await github.create_branch('<owner>', '<repo>', '<branch_name>', from_branch='<source_branch>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   branch: New branch name (string, required)
#   from_branch: Source branch to create from (string, optional)
# Example:
python run_github_ops.py -c "await github.create_branch('owner', 'repo', 'feature/user-auth', from_branch='develop')"
```

---

#### `list_branches(owner, repo, page=1, per_page=30)`
**Use Cases**:
- List all branches in a repository
- Check if a branch exists

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

### Commit Tools

#### `list_commits(owner, repo, sha=None, path=None, author=None, since=None, until=None, page=1, per_page=30)`
**Use Cases**:
- List commits on a branch
- Get commits for changelog generation
- Filter commits by author or date

**Usage**:
```bash
# Usage:
#   await github.list_commits('<owner>', '<repo>', sha='<branch>', since='<date>', until='<date>', per_page=<n>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   sha: Branch name or commit SHA (string, optional)
#   path: Filter by file path (string, optional)
#   author: Filter by author (string, optional)
#   since: Start date in ISO 8601 format (string, optional)
#   until: End date in ISO 8601 format (string, optional)
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30, max: 100)
# Example:
python run_github_ops.py -c "await github.list_commits('owner', 'repo', sha='develop', since='2024-01-01', per_page=50)"
```

---

#### `get_commit(owner, repo, sha)`
**Use Cases**:
- Get detailed commit information
- View commit diff

**Usage**:
```bash
# Usage:
#   await github.get_commit('<owner>', '<repo>', '<commit_sha>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   sha: Commit SHA (string, required)
# Example:
python run_github_ops.py -c "await github.get_commit('owner', 'repo', 'abc123def456')"
```

---

### PR Tools (for branch merging)

#### `create_pull_request(owner, repo, title, head, base, body=None, draft=False)`
**Use Cases**:
- Create PR to merge branches
- Finish GitFlow branches via PR

**Usage**:
```bash
# Usage:
#   await github.create_pull_request('<owner>', '<repo>', '<title>', '<head>', '<base>', body='<body>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   title: PR title (string, required)
#   head: Head branch to merge from (string, required)
#   base: Base branch to merge into (string, required)
#   body: PR description (string, optional)
#   draft: Create as draft (bool, default: False)
# Example:
python run_github_ops.py -c "await github.create_pull_request('owner', 'repo', 'Merge feature/auth to develop', 'feature/auth', 'develop')"
```

---

#### `merge_pull_request(owner, repo, pull_number, merge_method='merge', commit_title=None, commit_message=None)`
**Use Cases**:
- Merge a PR to complete branch workflow
- Choose merge strategy

**Usage**:
```bash
# Usage:
#   await github.merge_pull_request('<owner>', '<repo>', <pull_number>, merge_method='<method>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   pull_number: PR number (int, required)
#   merge_method: Merge method: merge/squash/rebase (string, default: 'merge')
#   commit_title: Custom commit title (string, optional)
#   commit_message: Custom commit message (string, optional)
# Example:
python run_github_ops.py -c "await github.merge_pull_request('owner', 'repo', 42, merge_method='squash')"
```

---

### File Tools (for version bumping)

#### `get_file_contents(owner, repo, path, ref=None)`
**Use Cases**:
- Read config file before version bump
- Get file SHA for updates

**Usage**:
```bash
# Usage:
#   await github.get_file_contents('<owner>', '<repo>', '<path>', ref='<branch>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   path: File path (string, required)
#   ref: Branch name or commit SHA (string, optional)
# Example:
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'package.json', ref='release/v2.1.0')"
```

---

#### `create_or_update_file(owner, repo, path, content, message, branch, sha=None)`
**Use Cases**:
- Update version in config file
- Create/update changelog file

**Usage**:
```bash
# Usage:
#   await github.create_or_update_file('<owner>', '<repo>', '<path>', '<content>', '<message>', '<branch>', sha='<sha>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   path: File path (string, required)
#   content: New file content (string, required)
#   message: Commit message (string, required)
#   branch: Target branch (string, required)
#   sha: File SHA for updates (string, optional - required when updating)
# Example:
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'package.json', '{\"version\": \"2.1.0\"}', 'Bump version to 2.1.0', 'release/v2.1.0', sha='abc123')"
```

---

## III. Best Practice Recommendations

### 1. Choose the Right Approach

| Scenario                          | Recommended Approach                     |
| --------------------------------- | ---------------------------------------- |
| Create single branch              | Use `create_branch()` basic tool         |
| Create GitFlow branch with prefix | Use `branch_manager.py` skill            |
| Initialize GitFlow                | Use `gitflow_manager.py init` skill      |
| Finish branch (PR + merge)        | Use `gitflow_manager.py finish` skill    |
| Prepare full release              | Use `release_manager.py prepare` skill   |
| Simple version bump               | Use `create_or_update_file()` basic tool |
| Analyze multiple branches         | Use `branch_analyzer.py` skill           |

### 2. GitFlow Branch Naming

Standard GitFlow prefixes:
- `feature/` - New features (merge to develop)
- `release/v` - Release preparation (merge to main)
- `hotfix/` - Production fixes (merge to main)
- `develop` - Integration branch

### 3. Release Workflow

Typical release workflow:
1. Create release branch: `branch_manager.py release --version "2.1.0"`
2. Bump version: `release_manager.py bump-version --file "package.json" --version "2.1.0"`
3. Generate changelog: `release_manager.py changelog --since "2024-01-01"`
4. Finish release: `release_manager.py finish --version "2.1.0"`

Or use the combined command:
```bash
python release_manager.py prepare owner repo --version "2.1.0" --from develop
```

---

## Usage Principles

1. **Prefer skills for multi-step workflows**: e.g., release preparation, GitFlow finish
2. **Use basic tools for simple atomic operations**: e.g., create branch, list branches
3. **Follow GitFlow conventions**: Use standard prefixes for branch types
