---
name: github_content_editor
description: This skill enables direct file manipulation within GitHub repositories. It allows you to generate documentation (like ANSWER.md) and edit code files, handling the creating, updating, and pushing of files to the remote repository. Use this when you need to submit answers or apply fixes.
---

# GitHub Content Editor Skill

This skill is based on Github MCP tools, providing file creation and editing capabilities for GitHub repositories.

## Core Concepts

In GitHub file editing, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations

---

## I. Skills

### 1. Document Generation

**File**: `doc_gen.py`

**Use Cases**:
- Submit answers (create/update ANSWER.md)
- Create or update documentation files
- Generate changelog from commit history
- Generate contributors list

**Typical Task Examples**:
- Submit an answer to a task
- Create API documentation
- Auto-generate CHANGELOG.md from commits

**Usage**:
```bash
# Usage:
#   python doc_gen.py <command> <owner> <repo> [options]
# Commands:
#   answer        Create/Update ANSWER.md
#   create        Create/Update generic file
#   changelog     Generate CHANGELOG.md from commit history
#   contributors  Generate CONTRIBUTORS.md from commit history
# 
# answer options:
#   --content <text>    Content of ANSWER.md (required)
#   --message <msg>     Commit message (default: "Add ANSWER.md")
#   --branch <branch>   Target branch (default: main)
#
# create options:
#   --path <filepath>   Path to the file (required)
#   --content <text>    Content of the file (required)
#   --message <msg>     Commit message (required)
#   --branch <branch>   Target branch (default: main)
#
# changelog options:
#   --output <path>     Output file path (default: CHANGELOG.md)
#   --since <date>      Start date in ISO 8601 format
#   --until <date>      End date in ISO 8601 format
#   --branch <branch>   Target branch (default: main)
#
# contributors options:
#   --output <path>     Output file path (default: CONTRIBUTORS.md)
#   --branch <branch>   Target branch (default: main)
#
# Example:
python doc_gen.py answer owner repo --content "The answer is 42" --message "Submit answer"
```

---

### 2. File Editing (Single File)

**File**: `file_editor.py`

**Use Cases**:
- Edit/overwrite a single file
- Apply search-and-replace fix to a file
- Mass edit across multiple files

**Note**: Each `edit` or `apply_fix` call creates a separate commit.

**Typical Task Examples**:
- Update a configuration file
- Fix a typo or bug in code
- Replace old URLs with new ones across files

**Usage**:
```bash
# Usage:
#   python file_editor.py <command> <owner> <repo> [options]
# Commands:
#   edit        Edit/Overwrite a file (creates 1 commit)
#   apply_fix   Apply search and replace fix (creates 1 commit)
#   file_edit   Search and replace across multiple files (creates 1 commit per file)
#   batch       Push multiple files in a single commit
#
# edit options:
#   --path <filepath>       Path to the file (required)
#   --content <text>        New content (direct string, may have shell escaping issues)
#   --content-base64 <b64>  Base64 encoded content (recommended for code with quotes)
#   --content-file <path>   Read content from local file
#   --stdin                 Read content from stdin
#   --message <msg>         Commit message (required)
#   --branch <branch>       Target branch (default: main)
#
# apply_fix options:
#   --path <filepath>       Path to the file (required)
#   --pattern <text>        Text pattern to find (required)
#   --replacement <text>    Replacement text (required)
#   --message <msg>         Commit message (required)
#   --branch <branch>       Target branch (default: main)
#
# file_edit options:
#   --query <text>          Search query / text to replace (required)
#   --replacement <text>    Replacement text (required)
#   --message <msg>         Commit message (required)
#   --branch <branch>       Target branch (default: main)
#
# Example (simple content):
python file_editor.py edit owner repo --path "src/config.py" --content "DEBUG = False" --message "Disable debug"
# Example (base64 for code with quotes - recommended):
python file_editor.py edit owner repo --path "src/app.js" --content-base64 "Y29uc3QgbXNnID0gJ2hlbGxvJzs=" --message "Add app.js"
```

---

### 3. Batch File Operations (Multiple Files, Single Commit)

**File**: `file_editor.py` (batch command)

**Use Cases**:
- Create/update multiple files in a single commit
- Atomic changes (all files committed together)
- Add workflow + config files together

**IMPORTANT**: Use `batch` when you need all changes in ONE commit. This is essential when:
- Task requires "all files in one commit"
- Files are related and should be committed together
- Atomic changes are needed

**Typical Task Examples**:
- Add CI workflow with ESLint config (2 files, 1 commit)
- Create multiple documentation files at once
- Setup project structure with multiple files

**Usage**:
```bash
# Usage:
#   python file_editor.py batch <owner> <repo> [options] --message <msg> [--branch <branch>]
# Parameters:
#   owner                   Repository owner (required)
#   repo                    Repository name (required)
#   --files <json>          JSON array of files (direct string, may have shell escaping issues)
#   --files-base64 <b64>    Base64 encoded JSON array (recommended for code with quotes)
#   --files-file <path>     Read files JSON from local file
#   --message <msg>         Commit message (required)
#   --branch <branch>       Target branch (default: main)
# Example (simple content):
python file_editor.py batch owner repo --files '[{"path": "README.md", "content": "# Hello"}]' --message "Add readme"
# Example (base64 for code with quotes - recommended):
python file_editor.py batch owner repo --files-base64 "W3sicGF0aCI6ICJzcmMvYXBwLmpzIiwgImNvbnRlbnQiOiAiY29uc3QgeCA9IDE7In1d" --message "Add app.js"
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases for atomic file operations. These are atomic operations for flexible combination.

**Note**: Code should be written without line breaks. Do not use multi-line logic or complex scripts.

### How to Run

```bash
# Usage:
#   python run_github_ops.py -c "<async_code>"
# Example:
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'file.txt', 'content', 'message', 'main')"
```

---

### File Creation/Update Tools

#### `create_or_update_file(owner, repo, path, content, message, branch, sha=None)`
**Use Cases**:
- Create a new file in repository
- Update an existing file (requires SHA)
- Simple single-file commits

**Usage**:
```bash
# Usage:
#   await github.create_or_update_file('<owner>', '<repo>', '<path>', '<content>', '<message>', '<branch>', sha='<sha>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   path: File path in repository (string, required)
#   content: File content (string, required)
#   message: Commit message (string, required)
#   branch: Target branch (string, required)
#   sha: File SHA for updates (string, optional - required when updating existing file)
# Example (create new file):
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'README.md', '# Hello World', 'Add readme', 'main')"
# Example (update existing file - need SHA first):
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', 'README.md', '# Updated', 'Update readme', 'main', sha='abc123')"
```

---

#### `push_files(owner, repo, branch, files, message)`
**Use Cases**:
- Push multiple files in a single commit
- Atomic multi-file changes
- Batch file creation/update

**Usage**:
```bash
# Usage:
#   await github.push_files('<owner>', '<repo>', '<branch>', [{'path': '<path>', 'content': '<content>'}, ...], '<message>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   branch: Target branch (string, required)
#   files: List of file dicts with 'path' and 'content' keys (list, required)
#   message: Commit message (string, required)
# Example:
python run_github_ops.py -c "await github.push_files('owner', 'repo', 'main', [{'path': 'a.txt', 'content': 'File A'}, {'path': 'b.txt', 'content': 'File B'}], 'Add two files')"
```

---

### File Reading Tools

#### `get_file_contents(owner, repo, path, ref=None)`
**Use Cases**:
- Read file content before editing
- Get file SHA for updates
- Check if file exists

**Usage**:
```bash
# Usage:
#   await github.get_file_contents('<owner>', '<repo>', '<path>', ref='<branch_or_sha>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   path: File path in repository (string, required)
#   ref: Branch name or commit SHA (string, optional)
# Example:
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', 'src/config.py', ref='main')"
```

---

### Commit History Tools (for changelog/contributors generation)

#### `list_commits(owner, repo, sha=None, path=None, author=None, since=None, until=None, page=1, per_page=30)`
**Use Cases**:
- Get commit history for changelog generation
- Find commits by author for contributors list
- Track file change history

**Usage**:
```bash
# Usage:
#   await github.list_commits('<owner>', '<repo>', sha='<branch>', since='<date>', until='<date>', per_page=<n>)
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
python run_github_ops.py -c "await github.list_commits('owner', 'repo', since='2024-01-01', per_page=50)"
```

---

## III. Best Practice Recommendations

### 1. Choose the Right Approach

| Scenario                      | Recommended Approach                                          |
| ----------------------------- | ------------------------------------------------------------- |
| Submit answer (ANSWER.md)     | Use `doc_gen.py answer` skill                                 |
| Create single file            | Use `create_or_update_file()` basic tool                      |
| Update single file with SHA   | Use `create_or_update_file()` basic tool                      |
| Multiple files, single commit | Use `file_editor.py batch` skill or `push_files()` basic tool |
| Search and replace in file    | Use `file_editor.py apply_fix` skill                          |
| Generate changelog            | Use `doc_gen.py changelog` skill                              |

### 2. Single vs Batch Commits

**Use single-file operations when**:
- Only one file needs to change
- Separate commits are acceptable or desired
- Simple file creation/update

**Use batch operations when**:
- Multiple related files need to change together
- Task explicitly requires "single commit"
- Atomic changes are important (e.g., workflow + config)

### 3. Update Workflow

When updating an existing file:
1. First get the file to obtain its SHA: `get_file_contents()`
2. Then update with the SHA: `create_or_update_file(..., sha='...')`

Or use the skill scripts which handle this automatically.

---

## Usage Principles

1. **Prefer skills for standard workflows**: e.g., answer submission, changelog generation
2. **Use basic tools for simple atomic operations**: e.g., create one file, push multiple files
3. **Always use batch for multi-file single-commit requirements**: ensures atomicity
