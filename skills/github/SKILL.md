---
name: github
description: Comprehensive GitHub repository management toolkit. Provides file editing, issue/PR management, GitFlow workflow, release management, commit investigation, CI/CD workflow creation, and configuration file generation via MCP GitHub tools.
---

# GitHub Skill

This skill provides complete GitHub repository management capabilities using MCP GitHub tools.

## Core Concepts

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls for atomic operations via `run_github_ops.py`

---

## I. Strategy: Skills vs Tools (Read First)

### 1. Skill-First Strategy

Always prioritize **Skill Scripts** over atomic tools. Skills encapsulate best practices and error handling.

| Goal                      | Recommended Skill         | Why?                                             |
| :------------------------ | :------------------------ | :----------------------------------------------- |
| **Multi-file Edits**      | `file_editor.py batch`    | Atomic commit; prevents partial updates          |
| **Content Investigation** | `github_detective.py`     | Unified interface for all investigation tasks    |
| **GitFlow Operations**    | `gitflow_manager.py`      | Enforces naming conventions and correct workflow |
| **PR + Label Management** | `pr_manager.py update`    | Handles labels atomically with PR updates        |
| **Issue + Label**         | `issue_manager.py update` | Handles labels atomically with issue updates     |
| **CI/CD Setup**           | `workflow_builder.py`     | Full automated pipeline (branch → PR → merge)    |
| **Release Preparation**   | `release_manager.py`      | Automates version bump, changelog, and merge     |
| **Project Config**        | `config_generator.py`     | Standardized templates and configurations        |

### 2. When to Use Basic Tools

Only use `run_github_ops.py` when:
1. **Unique Filtering**: Need specific API filters not exposed by skills
2. **One-off Read**: Quick check of file SHA or content
3. **Custom Operations**: Operations not covered by any skill

### 3. GitHub Domain Coverage

This skill covers the following GitHub task categories:

| Category               | Covered By                                       |
| :--------------------- | :----------------------------------------------- |
| File CRUD              | `file_editor.py`, basic file tools               |
| Issue Management       | `issue_manager.py`                               |
| PR Management          | `pr_manager.py`                                  |
| Label Management       | `issue_manager.py`, `pr_manager.py` (integrated) |
| Branch Management      | `gitflow_manager.py`, basic branch tools         |
| Commit Investigation   | `github_detective.py`                            |
| PR Investigation       | `github_detective.py`                            |
| Repository Exploration | `github_detective.py`                            |
| CI/CD Workflows        | `workflow_builder.py`                            |
| Release Management     | `release_manager.py`                             |
| Config Generation      | `config_generator.py`                            |

### 4. Command Line Safety

> [!WARNING]
> **Shell Escaping**: When passing complex strings (JSON, Python code, multi-line text) in command line arguments, be extremely careful with shell escaping.
> Ensure quotes are matched and special characters (like `$`) are handled correctly to prevent execution errors.


---

## II. Skills (High-Level Scripts)

### 1. File Editing

**File**: `file_editor.py`

**Use Cases**:
- Create new files in a repository
- Edit/overwrite existing files
- Apply search-and-replace fixes to a single file
- Push multiple files in a single commit (atomic batch operations)

**Typical Task Examples**:
- Create a README.md file
- Update configuration files
- Fix a typo or bug in a specific file

> [!Note]
> **Check Default Branch**: Before editing or creating files, ALWAYS check the default branch name (e.g., using `github_detective.py explore` or `list_branches`) unless you are explicitly targeting a specific feature branch.

**Usage**:
```bash
# Usage:
#   python file_editor.py <command> <owner> <repo> [options]
# Commands:
#   batch       Push multiple files in a single commit
#
# edit options:
#   --path <filepath>         File path (required)
#   --content <text>          Content string
#   --content-file <path>     Content from local file
#   --content-base64 <b64>    Content (base64 encoded)
#   --message <text>          Commit message (required)
#   --branch <name>           Target branch
# apply_fix options:
#   --path <filepath>         File path (required)
#   --pattern <text>          Text pattern to find (required)
#   --replacement <text>      Replacement text (required)
#   --message <text>          Commit message (required)
#   --branch <name>           Target branch
#
# batch options:
#   --files <json>            JSON array string
#   --files-file <path>       Path to JSON file containing files array
#   --files-base64 <b64>      Base64 encoded JSON array
#   --message <text>          Commit message (required)
#   --branch <name>           Target branch
#
# Examples:
#
python file_editor.py edit owner repo --path "docs/README.md" --content "# Documentation\n\nUpdated content." --message "Update README"
python file_editor.py batch owner repo --files '[{"path": "test.txt", "content": "test"}]' --message "Add files"
python file_editor.py edit owner repo --path "version.txt" --content "1.0.0" --message "Update version"
```

---

### 2. Issue Management

**File**: `issue_manager.py`

**Use Cases**:
- Create new issues with labels and checklists
- Create sub-issues linked to a parent issue
- Update issue title, body, state, and labels
- Close/reopen issues with state reasons
- List issues with filters
- Batch close/reopen issues

**Typical Task Examples**:
- Create a bug report issue
- Create sub-issues linked to a tracking issue
- Close an issue as completed and add "wontfix" label
- Add or remove labels from an existing issue

**Usage**:
```bash
# Usage:
#   python issue_manager.py <command> <owner> <repo> [options]
# Commands:
#   create      Create a new issue (optionally as sub-issue)
#   update      Update an existing issue (title, body, state, labels)
#   list        List issues with filters
#   close       Batch close issues (requires filter)
#   reopen      Batch reopen issues (requires query)
# create options:
#   --title <text>        Issue title (required)
#   --body <text>         Issue body/description
#   --labels <csv>        Comma-separated labels
#   --checklist <csv>     Comma-separated checklist items
#   --assignees <csv>     Comma-separated assignees
#   --parent <n>          Parent issue number to link as sub-issue
#
# update options:
#   --number <n>          Issue number (required)
#   --title <text>        New title
#   --body <text>         New body
#   --state <state>       New state: open/closed
#   --state-reason <r>    Reason: completed/not_planned/reopened
#   --add-labels <csv>    Labels to add
#   --remove-labels <csv> Labels to remove
#   --assignees <csv>     Comma-separated assignees to set
#   --milestone <n>       Milestone number
#
# list options:
#   --state <state>       Filter: open/closed/all (default: open)
#   --labels <csv>        Filter by labels
#   --limit <n>           Maximum results (default: 30)
#
# Output: Issue number and database ID are printed (e.g., "Created issue #52 (ID: 3753519439)")
#
# Examples:
python issue_manager.py create owner repo --title "Bug Report" --body "Description" --labels "bug,priority-high"
python issue_manager.py create owner repo --title "Sub-task 1" --body "Details" --parent 51
python issue_manager.py update owner repo --number 42 --state closed --state-reason completed --add-labels "wontfix"
python issue_manager.py list owner repo --state open --labels "bug"
```

---

### 3. Pull Request Management

**File**: `pr_manager.py`

**Use Cases**:
- Create PRs from branches
- Create and immediately merge PRs
- Merge PRs with different strategies (merge/squash/rebase)
- Close PRs without merging
- Update PR details including labels

**Typical Task Examples**:
- Create a PR from feature branch to main
- Merge a PR with squash strategy
- Add "approved" label to a PR
  
> [!Tips]
> **Respecting Original Context**: When fixing issues or conflicts in an existing PR, prefer updating and merging the original PR rather than creating a duplicate, unless explicitly instructed otherwise. This preserves the conversation history and context attached to the original PR number.

**Usage**:
```bash
# Usage:
#   python pr_manager.py <command> <owner> <repo> [options]
# Commands:
#   create      Create a new PR
#   merge       Merge an existing PR
#   close       Close a PR without merging
#   update      Update PR details (title, body, state, labels)
#
# create options:
#   --title <text>        PR title (required)
#   --head <branch>       Source branch (required)
#   --base <branch>       Target branch (required)
#   --body <text>         PR description
#   --draft               Create as draft PR
#   --merge <method>      Merge immediately: squash/merge/rebase
#
# merge options:
#   --number <n>          PR number (required)
#   --method <method>     Merge method: merge/squash/rebase (default: squash)
#   --commit-title <text> Custom commit title
#   --commit-message <text> Custom commit message
#
# update options:
#   --number <n>          PR number (required)
#   --title <text>        New title
#   --body <text>         New description
#   --add-labels <csv>    Labels to add
#   --remove-labels <csv> Labels to remove
#
# Examples:
python pr_manager.py create owner repo --title "Add feature" --head "feature/login" --base "main"
python pr_manager.py create owner repo --title "Fix bug" --head "fix" --base "main" --merge squash
python pr_manager.py update owner repo --number 42 --add-labels "approved,reviewed"
```


---

### 4. Comment Manager

**File**: `comment_manager.py`

**Use Cases**:
- Add comments to Issues
- Add comments to Pull Requests
- Submit PR reviews (comment, approve, request changes)

**Typical Task Examples**:
- Thank someone for reporting an issue
- Add a "LGTM" comment to a PR
- Approve a PR with a review comment
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
#   --body <text>         Comment text (required)
#
# review options:
#   --pr <n>              PR number (required)
#   --body <text>         Review comment (required)
#   --event <event>       Event: COMMENT/APPROVE/REQUEST_CHANGES (default: COMMENT)
#
# Examples:
python comment_manager.py add owner repo --issue 42 --body "Thanks for reporting!"
python comment_manager.py add owner repo --pr 42 --body "LGTM!"
python comment_manager.py review owner repo --pr 42 --body "Great work!" --event APPROVE
python comment_manager.py review owner repo --pr 42 --body "Please fix..." --event REQUEST_CHANGES
```

---

### 5. GitHub Detective (Investigation Tools)

**File**: `github_detective.py`

**Use Cases**:
- Explore repository structure (branches, tags, releases, files)
- Search commits by message, author, path, or date
- Track which commit introduced specific content (searches **Diffs/Patches**, not current Blame)
- Search and investigate Pull Requests
- Search and investigate Issues

**Typical Task Examples**:
- List all branches in a repository
- Find commits with "fix" in the message
- Trace which commit introduced a specific function
- Find the PR that introduced authentication
- Find issues related to "memory leak"

**Usage**:
```bash
# Usage:
#   python github_detective.py <command> <owner> <repo> [options]
# Commands:
#   explore         Explore repository structure
#   search-commits  Search commits by message/author/path
#   trace-content   Find the commit that introduced content
#   search-prs      Search and investigate Pull Requests
#   search-issues   Search and investigate Issues
#
# explore options:
#   --show <items>        Comma-separated: branches,tags,releases,files
#   --path <dir>          Directory path for file listing
#   --branch <name>       Branch for file listing
#
# search-commits options:
#   --query <regex>       Pattern to match in commit messages
#   --author <name>       Filter by author
#   --path <file>         Filter by file path
#   --branch <name>       Branch to search
#   --since <date>        Start date (ISO format: YYYY-MM-DD)
#   --until <date>        End date (ISO format: YYYY-MM-DD)
#   --limit <n>           Maximum results (default: 10)
#
# trace-content options:
#   --content <text>      Text to search for (required)
#   --file <filepath>     File to search in (recommended)
#   --branch <name>       Branch to search
#   --max-commits <n>     Maximum commits to scan (default: 10)
#   --find-branches       Find which branches contain the content
#
# search-prs options:
#   --query <keyword>     Search PRs by keyword
#   --number <n>          Get specific PR details
#   --show-files          Show files changed (use with --number)
#   --state <state>       Filter: open/closed/all
#
# search-issues options:
#   --query <keyword>     Search Issues by keyword
#   --state <state>       Filter: open/closed/all
#   --limit <n>           Maximum results (default: 20)
#
# Examples:
  python github_detective.py explore owner repo --show branches,tags
  python github_detective.py search-commits owner repo --query "fix" --limit 20
  python github_detective.py trace-content owner repo --content "def calculate" --file "src/utils.py"
  python github_detective.py search-prs owner repo --number 42 --show-files
  python github_detective.py search-issues owner repo --query "bug" --state open
```

---

### 6. GitFlow Workflow

**File**: `gitflow_manager.py`

**Use Cases**:
- Initialize GitFlow structure (create develop branch from main)
- Finish feature/release/hotfix branches (create PR and merge)

**Note**: This script handles GitFlow workflow operations. For creating branches, use basic tools.
> [!TIP]
> **How to Start a Feature/Release**:
> GitFlow "start" is simply creating a branch from `develop`.
> ```bash
> # Start a feature
> python run_github_ops.py -c "await github.create_branch('owner', 'repo', 'feature/login', from_branch='develop')"
> ```

**Typical Task Examples**:
- Initialize GitFlow for a new repository
- Finish a feature by merging to develop
- Finish a release by merging to main

**Usage**:
```bash
# Usage:
#   python gitflow_manager.py <command> <owner> <repo> [options]
# Commands:
#   init        Initialize GitFlow (create develop branch from main)
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
# Examples:
python gitflow_manager.py init owner repo
python gitflow_manager.py finish owner repo --type feature --name "user-auth" --target develop
python gitflow_manager.py finish owner repo --type release --name "1.0.0" --target main --merge-method merge
```

---

### 7. CI/CD Workflow Builder

**File**: `workflow_builder.py`

**Use Cases**:
- Create GitHub Actions workflow files
- Generate common CI/CD pipelines (lint, test, scheduled tasks)

**IMPORTANT**: These commands are **fully automated pipelines** that create branch, push files, create PR, and merge. Do NOT use when you need manual control over commits.

**Typical Task Examples**:
- Create a linting workflow for PRs
- Add a CI pipeline that runs tests
- Create a scheduled health check job

**Usage**:
```bash
# Usage:
#   python workflow_builder.py <command> <owner> <repo> [options]
# Commands:
#   ci-basic    Create basic CI workflow (test + build)
#   lint        Create linting workflow with ESLint
#   scheduled   Create scheduled/cron workflow
#
# ci-basic options:
#   --trigger <events>      Trigger events: push,pull_request (default: push,pull_request)
#   --branch <branch>       Branch to run on (default: main)
#   --node-version <v>      Node.js version (default: 18)
#
# lint options:
#   --trigger <events>      Trigger events (default: push,pull_request)
#   --branch <branch>       Branch to run on (default: main)
#
# scheduled options:
#   --cron <expression>     Cron expression (required, e.g., "0 2 * * *")
#   --script <command>      Script to run (required)
#   --name <name>           Workflow name (default: "Nightly Health Check")
#
# Examples:
python workflow_builder.py ci-basic owner repo --trigger "push,pull_request" --branch main
python workflow_builder.py lint owner repo --trigger "push,pull_request" --branch main
python workflow_builder.py scheduled owner repo --cron "0 2 * * *" --script "npm run health-check"
```

---

### 8. Release Manager

**File**: `release_manager.py`

**Use Cases**:
- Prepare releases (create release branch + changelog)
- Bump version numbers in config files (package.json, Cargo.toml, pyproject.toml)
- Generate changelogs from commit history
- Finish releases (merge to main)

**Typical Task Examples**:
- Prepare version 2.1.0 release from develop
- Update version in package.json
- Generate changelog for the past month
- Finish and merge a release

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
#   --version <version>   Version number (required, e.g., "2.1.0")
#   --from <branch>       Source branch (default: develop)
#
# bump-version options:
#   --file <filepath>     Config file: package.json/Cargo.toml/pyproject.toml (required)
#   --version <version>   New version number (required)
#   --branch <branch>     Target branch (required)
#
# changelog options:
#   --since <date>        Start date in ISO format: YYYY-MM-DD (optional)
#   --until <date>        End date in ISO format: YYYY-MM-DD (optional)
#   --output <path>       Output file path (default: CHANGELOG.md)
#   --branch <branch>     Target branch (default: main)
#
# finish options:
#   --version <version>   Version number (required)
#   --target <branch>     Target branch (default: main)
#   --merge-method <m>    Merge method: squash/merge/rebase (default: squash)
#
# Examples:
python release_manager.py prepare owner repo --version "2.1.0" --from develop
python release_manager.py bump-version owner repo --file "package.json" --version "2.1.0" --branch release/v2.1.0
python release_manager.py changelog owner repo --since "2024-01-01" --output "CHANGELOG.md"
python release_manager.py finish owner repo --version "2.1.0"
```

---

### 9. Config Generator

**File**: `config_generator.py`

**Use Cases**:
- Generate ESLint configuration files
- Create Issue templates (bug, feature, maintenance)
- Create PR templates

**Typical Task Examples**:
- Add ESLint config with recommended rules
- Standardize issue reporting with templates
- Create PR template for code reviews

**Usage**:
```bash
# Usage:
#   python config_generator.py <command> <owner> <repo> [options]
# Commands:
#   eslint          Create ESLint configuration
#   issue-templates Create Issue templates
#   pr-template     Create PR template
#
# eslint options:
#   --extends <config>      Base config to extend (default: eslint:recommended)
#   --rules <csv>           Comma-separated rules: semi,quotes,indent,no-var,prefer-const
#   --branch <branch>       Target branch (default: main)
#
# issue-templates options:
#   --types <csv>           Template types: bug,feature,maintenance (default: bug,feature)
#   --branch <branch>       Target branch (default: main)
#
# pr-template options:
#   --branch <branch>       Target branch (default: main)
#
# Examples:
python config_generator.py eslint owner repo --extends "eslint:recommended" --rules "semi,quotes"
python config_generator.py issue-templates owner repo --types "bug,feature,maintenance"
python config_generator.py pr-template owner repo
```

---

## III. Basic Tools (When to Use Single Functions)

Below are the basic tool functions for atomic operations. Use these when skills don't cover your specific need.

> [!CAUTION]
> 1. **Strictly adhere to the tool list**: Do NOT use any tools or methods not explicitly documented in this section.
> 2. **Fragile Arguments**: Do NOT pass multi-line strings or code blocks to `run_github_ops.py`. It uses `eval()`, which is extremely fragile with complex quoting.
> 3. **Content Operations**: **ALWAYS** use Skill Scripts (`file_editor.py`, etc.) for content operations.

**Note**: Code should be written without line breaks. Do not use multi-line logic or complex scripts.

### How to Run

```bash
# Usage:
#   python run_github_ops.py -c "<await github.<tool_name>(args)"
# Example:
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'README.md', ref='main')"
```

---

### Branch Tools

#### `create_branch(owner, repo, branch, from_branch=None)`
Create a new branch in a GitHub repository

```bash
python run_github_ops.py -c "await github.create_branch('owner', 'repo', 'feature/new-login', from_branch='main')"
```

#### `list_branches(owner, repo, page=1, per_page=30)`
List all branches in a repository. Useful for checking if a branch exists before creating.

```bash
python run_github_ops.py -c "await github.list_branches('owner', 'repo')"
```

---

### File Tools

#### `get_file_contents(owner, repo, path, ref=None, sha=None)`
Read file content or directory listing. Also returns file SHA needed for updates.

```bash
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'src/main.py', ref='develop')"
```

#### `create_or_update_file(owner, repo, path, content, message, branch, sha=None)`
Create or update a single file in a GitHub repository. If updating, you must provide the SHA of the file you want to update. Use this tool to create or update a file in a GitHub repository remotely; do not use it for local file operations.

```bash
# Create new file:
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'README.md', '# Project', 'Add README', 'main')"
# Update existing file (need SHA):
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'README.md', '# Updated', 'Update README', 'main', sha='abc123')"
```

#### `push_files(owner, repo, branch, files, message)`
Push multiple files to a GitHub repository in a single commit

```bash
python run_github_ops.py -c "await github.push_files('owner', 'repo', 'main', [{'path': 'a.txt', 'content': 'A'}], 'Add files')"
```

---

### Issue Tools

#### `issue_write(owner, repo, title, body=None, labels=None, assignees=None, milestone=None, issue_number=None, state=None, state_reason=None, method=None)`
Create a new or update an existing issue in a GitHub repository.

```bash
# Create:
python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'Bug Report', body='Description', labels=['bug'], method='create')"
# Close
# fetch issue first to get title
python run_github_ops.py -c "await github.issue_write('owner', 'repo', 'Original Title', issue_number=42, state='closed', state_reason='completed', method='update')"
```

#### `issue_read(owner, repo, issue_number, method=None)`
Get information about a specific issue in a GitHub repository.

```bash
python run_github_ops.py -c "await github.issue_read('owner', 'repo', 42)"
```

#### `add_issue_comment(owner, repo, issue_number, body)`
Add a comment to a specific issue in a GitHub repository. Use this tool to add comments to pull requests as well (in this case pass pull request number as issue_number), but only if user is not asking specifically to add review comments.

```bash
python run_github_ops.py -c "await github.add_issue_comment('owner', 'repo', 42, 'Thanks for reporting!')"
```

#### `list_issue_types(owner, repo)`
List supported issue types for repository owner (organization).

```bash
python run_github_ops.py -c "await github.list_issue_types('owner', 'repo')"
```

#### `sub_issue_write(owner, repo, issue_number, title=None, method=None, sub_issue_id=None)`
Add a sub-issue to a parent issue in a GitHub repository.

```bash
# Create new sub-issue:
python run_github_ops.py -c "await github.sub_issue_write('owner', 'repo', 42, title='Sub task')"
# Add existing issue as sub-issue:
python run_github_ops.py -c "await github.sub_issue_write('owner', 'repo', 42, method='add', sub_issue_id=43)"
```

#### `get_label(owner, repo, name)`
Get a specific label from a repository.

```bash
python run_github_ops.py -c "await github.get_label('owner', 'repo', 'bug')"
```

---

### Pull Request Tools

#### `create_pull_request(owner, repo, title, head, base, body=None, draft=False, maintainer_can_modify=True)`
Create a new pull request in a GitHub repository.

```bash
python run_github_ops.py -c "await github.create_pull_request('owner', 'repo', 'Add feature', 'feature-branch', 'main', body='Description', maintainer_can_modify=True)"
```

#### `merge_pull_request(owner, repo, pull_number, merge_method='merge', commit_title=None, commit_message=None)`
Merge a pull request in a GitHub repository.

```bash
python run_github_ops.py -c "await github.merge_pull_request('owner', 'repo', 42, merge_method='squash')"
```

#### `pull_request_read(owner, repo, pull_number, method=None, per_page=None)`
Get information on a specific pull request in GitHub repository.

```bash
python run_github_ops.py -c "await github.pull_request_read('owner', 'repo', 42, method='get_files')"
```

#### `update_pull_request(owner, repo, pull_number, title=None, body=None, state=None, labels=None, reviewers=None)`
Update an existing pull request in a GitHub repository.

```bash
python run_github_ops.py -c "await github.update_pull_request('owner', 'repo', 42, state='closed', labels=['wontfix'])"
```

#### `pull_request_review_write(owner, repo, pullNumber, method=None, body=None, event=None)`
Create and/or submit, delete review of a pull request.

```bash
python run_github_ops.py -c "await github.pull_request_review_write(owner='owner', repo='repo', pullNumber=42, method='create', body='LGTM! Great implementation.', event='COMMENT')"
```

#### `add_comment_to_pending_review(**kwargs)`
Add review comment to the requester's latest pending pull request review. A pending review needs to already exist to call this (check with the user if not sure).

```bash
python run_github_ops.py -c "await github.add_comment_to_pending_review(owner='owner', repo='repo', pullNumber=42, body='Fix this', path='file.py', line=10)"
```

#### `update_pull_request_branch(owner, repo, pull_number)`
Update the branch of a pull request with the latest changes from the base branch.

```bash
python run_github_ops.py -c "await github.update_pull_request_branch('owner', 'repo', 42)"
```

---

### User & Team Tools

#### `get_me()`
Get details of the authenticated GitHub user. Use this when a request is about the user's own profile for GitHub. Or when information is missing to build other tool calls.

```bash
python run_github_ops.py -c "await github.get_me()"
```

#### `get_teams(org)`
Get details of the teams the user is a member of. Limited to organizations accessible with current credentials

```bash
python run_github_ops.py -c "await github.get_teams('org-name')"
```

#### `get_team_members(org, team_slug)`
Get member usernames of a specific team in an organization. Limited to organizations accessible with current credentials

```bash
python run_github_ops.py -c "await github.get_team_members('org-name', 'team-slug')"
```

---
