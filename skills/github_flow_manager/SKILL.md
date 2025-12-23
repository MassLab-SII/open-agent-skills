---
name: github_flow_manager
description: This skill manages GitHub Issues, Pull Requests, labels, and comments. It enables lifecycle management, batch operations, and automated workflows for repository collaboration.
---

# GitHub Flow Manager Skill

This skill is based on Github MCP tools, providing management capabilities for GitHub Issues, Pull Requests, labels, and comments.

## Core Concepts

In GitHub flow management, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiplse tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations

---

## I. Skills

### 1. Issue Management

**File**: `issue_manager.py`

**Use Cases**:
- Create new issues with labels and checklists
- Update issue title, body, or state
- Close/reopen issues with state reasons
- List issues with filters
- Batch close/reopen issues

**Note**: For adding labels, use `label_manager.py`. For adding comments, use `comment_manager.py`.

**Typical Task Examples**:
- Create a bug report issue
- Close an issue as completed
- Batch close all issues with comments

**Usage**:
```bash
# Usage:
#   python issue_manager.py <command> <owner> <repo> [options]
# Commands:
#   create      Create a new issue
#   update      Update an existing issue
#   list        List issues with filters
#   close       Batch close issues based on filters
#   reopen      Batch reopen closed issues matching query
#
# create options:
#   --title <text>        Issue title (required)
#   --body <text>         Issue body/description
#   --labels <csv>        Comma-separated labels
#   --checklist <csv>     Comma-separated checklist items
#   --assignees <csv>     Comma-separated assignees
#
# update options:
#   --number <n>          Issue number (required)
#   --title <text>        New title
#   --body <text>         New body
#   --state <state>       New state: open/closed
#   --state-reason <r>    Reason: completed/not_planned/reopened
#
# list options:
#   --state <state>       Filter by state: open/closed/all (default: open)
#   --labels <csv>        Filter by labels
#   --limit <n>           Maximum results (default: 30)
#
# close options:
#   --filter <filter>     Filter criteria: has_comments
#
# reopen options:
#   --query <text>        Search query (required)
#
# Example:
python issue_manager.py create owner repo --title "Bug Report" --body "Steps to reproduce..." --labels "bug,priority-high"
```

---

### 2. Pull Request Management

**File**: `pr_manager.py`

**Use Cases**:
- Create PRs from branches
- Create and immediately merge PRs
- Merge existing PRs with different strategies
- Close PRs without merging
- Update PR details

**Note**: For adding comments to PRs, use `comment_manager.py`. For adding labels, use `label_manager.py`.

**Typical Task Examples**:
- Create a PR from feature branch to main
- Merge a PR with squash strategy
- Close a PR without merging

**Usage**:
```bash
# Usage:
#   python pr_manager.py <command> <owner> <repo> [options]
# Commands:
#   create      Create a new pull request
#   merge       Merge an existing pull request
#   close       Close a pull request without merging
#   update      Update pull request details
#
# create options:
#   --head <branch>       Head branch (required)
#   --base <branch>       Base branch (required)
#   --title <text>        PR title (required)
#   --body <text>         PR description
#   --draft               Create as draft PR
#   --merge <method>      Merge immediately: squash/merge/rebase
#
# merge options:
#   --number <n>          PR number (required)
#   --method <method>     Merge method: squash/merge/rebase (default: squash)
#   --commit-title <t>    Custom commit title
#   --commit-message <m>  Custom commit message
#
# close options:
#   --number <n>          PR number (required)
#
# update options:
#   --number <n>          PR number (required)
#   --title <text>        New title
#   --body <text>         New description
#   --state <state>       New state: open/closed
#
# Example:
python pr_manager.py create owner repo --head feature-branch --base main --title "Add new feature" --merge squash
```

---

### 3. Label Management

**File**: `label_manager.py`

**Use Cases**:
- Add labels to a single issue or PR
- Batch add labels to multiple issues or PRs

**Typical Task Examples**:
- Add "bug" and "priority-high" labels to an issue
- Batch add "reviewed" label to multiple issues

**Usage**:
```bash
# Usage:
#   python label_manager.py <command> <owner> <repo> [options]
# Commands:
#   add         Add labels to a single issue or PR
#   batch       Batch add labels to multiple issues or PRs
#
# add options:
#   --issue <n>           Issue number (use this OR --pr)
#   --pr <n>              PR number (use this OR --issue)
#   --labels <csv>        Comma-separated labels (required)
#
# batch options:
#   --issues <csv>        Comma-separated issue numbers (use this OR --prs)
#   --prs <csv>           Comma-separated PR numbers (use this OR --issues)
#   --labels <csv>        Comma-separated labels (required)
#
# Example:
python label_manager.py add owner repo --issue 42 --labels "bug,priority-high"
```

---

### 4. Comment Management

**File**: `comment_manager.py`

**Use Cases**:
- Add comments to issues
- Add comments to PRs
- Submit PR reviews (comment, approve, request changes)

**Typical Task Examples**:
- Thank someone for reporting an issue
- Approve a PR with a comment
- Request changes on a PR

**Usage**:
```bash
# Usage:
#   python comment_manager.py <command> <owner> <repo> [options]
# Commands:
#   add         Add a comment to an issue or PR
#   review      Submit a PR review
#
# add options:
#   --issue <n>           Issue number (use this OR --pr)
#   --pr <n>              PR number (use this OR --issue)
#   --body <text>         Comment body (required)
#
# review options:
#   --pr <n>              PR number (required)
#   --body <text>         Review body (required)
#   --event <event>       Review event: COMMENT/APPROVE/REQUEST_CHANGES (default: COMMENT)
#
# Example:
python comment_manager.py review owner repo --pr 42 --body "LGTM!" --event APPROVE
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases for atomic flow management operations. These are atomic operations for flexible combination.

**Note**: Code should be written without line breaks. Do not use multi-line logic or complex scripts.

### How to Run

```bash
# Usage:
#   python run_github_ops.py -c "<async_code>"
# Example:
python run_github_ops.py -c "await github.add_issue_comment('owner', 'repo', 42, 'Thanks!')"
```

---

### Issue Tools

#### `issue_write(owner, repo, title, body=None, labels=None, assignees=None, issue_number=None, state=None, state_reason=None, method=None)`
**Use Cases**:
- Create a new issue
- Update an existing issue
- Close or reopen an issue

**Usage**:
```bash
# Usage:
#   await github.issue_write('<owner>', '<repo>', '<title>', body='<body>', labels=['<label>'], issue_number=<n>, state='<state>', state_reason='<reason>', method='<method>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   title: Issue title (string, required)
#   body: Issue description (string, optional)
#   labels: List of labels (list, optional)
#   assignees: List of assignees (list, optional)
#   issue_number: Issue number for updates (int, optional)
#   state: Issue state: open/closed (string, optional)
#   state_reason: Reason: completed/not_planned/reopened (string, optional)
#   method: Operation: create/update (string, auto-detected if not provided)
# Example (create):
python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'Bug Report', body='Description', labels=['bug'], method='create')"
# Example (close):
python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'title', issue_number=42, state='closed', state_reason='completed', method='update')"
```

---

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
#   await github.list_issues('<owner>', '<repo>', state='<state>', labels=['<label>'], per_page=<n>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   state: Issue state filter: open/closed/all (string, default: 'open')
#   labels: Filter by labels (list, optional)
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

### Pull Request Tools

#### `create_pull_request(owner, repo, title, head, base, body=None, draft=False)`
**Use Cases**:
- Create a new pull request

**Usage**:
```bash
# Usage:
#   await github.create_pull_request('<owner>', '<repo>', '<title>', '<head>', '<base>', body='<body>', draft=<bool>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   title: PR title (string, required)
#   head: Head branch (string, required)
#   base: Base branch (string, required)
#   body: PR description (string, optional)
#   draft: Create as draft (bool, default: False)
# Example:
python run_github_ops.py -c "await github.create_pull_request('owner', 'repo', 'Add feature', 'feature-branch', 'main', body='Description')"
```

---

#### `merge_pull_request(owner, repo, pull_number, merge_method='merge', commit_title=None, commit_message=None)`
**Use Cases**:
- Merge a pull request
- Choose merge strategy (squash, merge, rebase)

**Usage**:
```bash
# Usage:
#   await github.merge_pull_request('<owner>', '<repo>', <pull_number>, merge_method='<method>', commit_title='<title>', commit_message='<msg>')
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

#### `update_pull_request(owner, repo, pull_number, title=None, body=None, state=None)`
**Use Cases**:
- Update PR title or description
- Close a PR without merging

**Usage**:
```bash
# Usage:
#   await github.update_pull_request('<owner>', '<repo>', <pull_number>, title='<title>', body='<body>', state='<state>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   pull_number: PR number (int, required)
#   title: New title (string, optional)
#   body: New description (string, optional)
#   state: New state: open/closed (string, optional)
# Example:
python run_github_ops.py -c "await github.update_pull_request('owner', 'repo', 42, state='closed')"
```

---

#### `list_pull_requests(owner, repo, state='open', page=1, per_page=30)`
**Use Cases**:
- List PRs in a repository
- Filter by state

**Usage**:
```bash
# Usage:
#   await github.list_pull_requests('<owner>', '<repo>', state='<state>', per_page=<n>)
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   state: PR state filter: open/closed/all (string, default: 'open')
#   page: Page number (int, default: 1)
#   per_page: Results per page (int, default: 30)
# Example:
python run_github_ops.py -c "await github.list_pull_requests('owner', 'repo', state='all')"
```

---

### Comment Tools

#### `add_issue_comment(owner, repo, issue_number, body)`
**Use Cases**:
- Add comment to an issue
- Add comment to a PR (use PR number as issue_number)

**Usage**:
```bash
# Usage:
#   await github.add_issue_comment('<owner>', '<repo>', <issue_number>, '<body>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   issue_number: Issue or PR number (int, required)
#   body: Comment body (string, required)
# Example:
python run_github_ops.py -c "await github.add_issue_comment('owner', 'repo', 42, 'Thanks for reporting!')"
```

---

#### `pull_request_review_write(owner, repo, pullNumber, body, event='COMMENT', method='create')`
**Use Cases**:
- Submit a PR review
- Approve a PR
- Request changes on a PR

**Usage**:
```bash
# Usage:
#   await github.pull_request_review_write(owner='<owner>', repo='<repo>', pullNumber=<n>, body='<body>', event='<event>', method='create')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   pullNumber: PR number (int, required)
#   body: Review body (string, required)
#   event: Review event: COMMENT/APPROVE/REQUEST_CHANGES (string, default: 'COMMENT')
#   method: Operation: create (string, required)
# Example:
python run_github_ops.py -c "await github.pull_request_review_write(owner='owner', repo='repo', pullNumber=42, body='LGTM!', event='APPROVE', method='create')"
```

---

## III. Best Practice Recommendations

### 1. Choose the Right Approach

| Scenario                    | Recommended Approach                                                              |
| --------------------------- | --------------------------------------------------------------------------------- |
| Create issue with checklist | Use `issue_manager.py create` skill                                               |
| Simple issue creation       | Use `issue_write()` basic tool                                                    |
| Batch close issues          | Use `issue_manager.py close` skill                                                |
| Close single issue          | Use `issue_write()` basic tool                                                    |
| Create and merge PR         | Use `pr_manager.py create --merge` skill                                          |
| Simple PR merge             | Use `merge_pull_request()` basic tool                                             |
| Add single comment          | Use `add_issue_comment()` basic tool                                              |
| Submit PR review            | Use `comment_manager.py review` skill or `pull_request_review_write()` basic tool |

### 2. Issue State Management

When closing issues, always specify `state_reason`:
- `completed` - Issue was resolved
- `not_planned` - Issue won't be fixed

When reopening issues:
- `reopened` - Issue needs more work

### 3. PR Merge Strategies

- `squash` - Combine all commits into one (recommended for feature branches)
- `merge` - Create a merge commit (preserves all commits)
- `rebase` - Rebase commits onto base branch (linear history)

---

## Usage Principles

1. **Prefer skills for complex workflows**: e.g., batch operations, create with checklist
2. **Use basic tools for simple atomic operations**: e.g., add comment, close issue, merge PR
3. **Use appropriate state reasons**: Always specify why an issue is being closed/reopened
