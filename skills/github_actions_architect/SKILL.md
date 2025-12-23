---
name: github_actions_architect
description: This skill builds and deploys GitHub Actions workflows and configuration files for CI/CD automation. It creates workflows for testing, linting, scheduled tasks, and generates supporting configuration files like ESLint configs and Issue templates. Use this when you need to set up CI/CD pipelines or standardize repository configurations.
---

# GitHub Actions Architect Skill

This skill is based on Github MCP tools, providing CI/CD workflow and configuration file creation capabilities.

## Core Concepts

In GitHub Actions setup, we distinguish two types of operations:

1. **Skill**: Meaningful combinations of multiple tool calls, encapsulated as independent Python scripts
2. **Basic Tools**: Single function calls used for atomic operations

---

## I. Skills

### 1. Workflow Building (Automated Full Pipeline)

**File**: `workflow_builder.py`

**Use Cases**:
- Create basic CI workflows (test, build)
- Create linting workflows with ESLint
- Create scheduled workflows (cron jobs)

**IMPORTANT**: These commands are **fully automated pipelines** that:
1. Create a branch
2. Push all required files (workflow + configs)
3. Create a PR
4. Merge the PR

**DO NOT USE when**: The task requires a specific number of commits or manual control over the process. In that case, use basic tools or `github_content_editor` skill's `batch` command.

**Typical Task Examples**:
- Set up CI pipeline for a Node.js project
- Add linting workflow with ESLint
- Create nightly health check job

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
#   --script <command>      Script to run (required, e.g., "npm run health-check")
#   --name <name>           Workflow name (default: "Scheduled Task")
#
# Example:
python workflow_builder.py ci-basic owner repo --trigger "push,pull_request" --branch main --node-version 18
python workflow_builder.py lint owner repo --trigger "push,pull_request" --branch main
python workflow_builder.py scheduled owner repo --cron "0 2 * * *" --script "npm run health-check" --name "Nightly Health Check"
```

---

### 2. Configuration Generation

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
#   --rules <csv>           Comma-separated rules to enable (e.g., "semi,quotes")
#
# issue-templates options:
#   --types <csv>           Template types: bug,feature,maintenance (default: bug,feature)
#
# pr-template options:
#   (no additional options)
#
# Example:
python config_generator.py eslint owner repo --extends "eslint:recommended" --rules "semi,quotes"
python config_generator.py issue-templates owner repo --types "bug,feature,maintenance"
python config_generator.py pr-template owner repo
```

---

## II. Basic Tools (When to Use Single Functions)

Below are the basic tool functions and their use cases for atomic CI/CD operations. These are atomic operations for flexible combination. 

**Note**: Code should be written without line breaks. Do not use multi-line logic or complex scripts.

### How to Run

```bash
# Usage:
#   python run_github_ops.py -c "<async_code>"
# Example:
python run_github_ops.py -c "await github.push_files('owner', 'repo', 'main', [{'path': '.github/workflows/ci.yml', 'content': '...'}], 'Add CI')"
```

---

### File Push Tools

#### `push_files(owner, repo, branch, files, message)`
**Use Cases**:
- Push workflow + config files in a single commit
- Atomic multi-file changes for CI setup
- Manual control over commit content

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
python run_github_ops.py -c "await github.push_files('owner', 'repo', 'main', [{'path': '.github/workflows/ci.yml', 'content': 'name: CI\\non: [push]\\njobs:\\n  test:\\n    runs-on: ubuntu-latest'}, {'path': '.eslintrc.json', 'content': '{\"extends\": \"eslint:recommended\"}'}], 'Add CI workflow and ESLint config')"
```

---

#### `create_or_update_file(owner, repo, path, content, message, branch, sha=None)`
**Use Cases**:
- Create/update a single workflow file
- Create/update a single config file
- Simple single-file commits

**Usage**:
```bash
# Usage:
#   await github.create_or_update_file('<owner>', '<repo>', '<path>', '<content>', '<message>', '<branch>', sha='<sha>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   path: File path (string, required)
#   content: File content (string, required)
#   message: Commit message (string, required)
#   branch: Target branch (string, required)
#   sha: File SHA for updates (string, optional - required when updating existing file)
# Example:
python run_github_ops.py -c "await github.create_or_update_file('owner', 'repo', '.github/workflows/ci.yml', 'name: CI\\non: [push]', 'Add CI workflow', 'main')"
```

---

### Branch Tools

#### `create_branch(owner, repo, branch, from_branch=None)`
**Use Cases**:
- Create branch for CI/CD changes
- Isolate workflow changes before PR

**Usage**:
```bash
# Usage:
#   await github.create_branch('<owner>', '<repo>', '<branch_name>', from_branch='<source_branch>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   branch: New branch name (string, required)
#   from_branch: Source branch (string, optional)
# Example:
python run_github_ops.py -c "await github.create_branch('owner', 'repo', 'ci/add-linting', from_branch='main')"
```

---

### PR Tools

#### `create_pull_request(owner, repo, title, head, base, body=None, draft=False)`
**Use Cases**:
- Create PR for workflow changes
- Review CI/CD changes before merge

**Usage**:
```bash
# Usage:
#   await github.create_pull_request('<owner>', '<repo>', '<title>', '<head>', '<base>', body='<body>')
# Parameters:
#   owner: Repository owner (string, required)
#   repo: Repository name (string, required)
#   title: PR title (string, required)
#   head: Head branch (string, required)
#   base: Base branch (string, required)
#   body: PR description (string, optional)
#   draft: Create as draft (bool, default: False)
# Example:
python run_github_ops.py -c "await github.create_pull_request('owner', 'repo', 'Add CI/CD workflow', 'ci/add-linting', 'main', body='This PR adds linting workflow')"
```

---

#### `merge_pull_request(owner, repo, pull_number, merge_method='merge', commit_title=None, commit_message=None)`
**Use Cases**:
- Merge CI/CD PR after review
- Complete workflow setup

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

### File Reading Tools

#### `get_file_contents(owner, repo, path, ref=None)`
**Use Cases**:
- Check if workflow file exists
- Get existing config for modification
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
python run_github_ops.py -c "await github.get_file_contents('owner', 'repo', '.github/workflows/ci.yml')"
```

---

## III. Best Practice Recommendations

### 1. Choose the Right Approach

| Scenario                      | Recommended Approach                                        |
| ----------------------------- | ----------------------------------------------------------- |
| Quick CI setup (automated)    | Use `workflow_builder.py` skill                             |
| Manual control over commits   | Use `push_files()` or `create_or_update_file()` basic tools |
| Single workflow file          | Use `create_or_update_file()` basic tool                    |
| Multiple files, single commit | Use `push_files()` basic tool                               |
| Add ESLint config only        | Use `config_generator.py eslint` skill                      |
| Custom workflow content       | Use basic tools with your own YAML content                  |

### 2. Workflow File Paths

Standard GitHub Actions paths:
- Workflows: `.github/workflows/<name>.yml`
- Issue templates: `.github/ISSUE_TEMPLATE/<name>.md`
- PR template: `.github/PULL_REQUEST_TEMPLATE.md`
- ESLint config: `.eslintrc.json` or `eslint.config.js`

### 3. Manual CI Setup Workflow

When you need fine-grained control:
1. Create branch: `create_branch('owner', 'repo', 'ci/setup', from_branch='main')`
2. Push files: `push_files('owner', 'repo', 'ci/setup', [...], 'Add CI')`
3. Create PR: `create_pull_request('owner', 'repo', 'Add CI', 'ci/setup', 'main')`
4. Merge PR: `merge_pull_request('owner', 'repo', pr_number, merge_method='squash')`

---

## Usage Principles

1. **Prefer skills for standard CI setups**: e.g., basic CI, linting, scheduled tasks
2. **Use basic tools for custom workflows**: When you need specific YAML content or commit control
3. **Use `push_files()` for atomic multi-file commits**: Ensures workflow + config are committed together
