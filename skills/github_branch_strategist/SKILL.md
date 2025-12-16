---
name: github_branch_strategist
description: This skill provides comprehensive branch management for GitHub repositories. It supports creating branches with any name, GitFlow-style branches, release management with version bumping and changelog generation, and cross-branch commit analysis.
---

# GitHub Branch Strategist Skill

This skill provides comprehensive branch management and GitFlow workflow support:

1. **Branch Management**: Create branches with any name, list branches, delete branches
2. **GitFlow Workflow**: Initialize GitFlow, finish (merge) feature/release/hotfix branches
3. **Release Management**: Prepare releases, bump versions, generate changelogs
4. **Branch Analysis**: Aggregate commits across branches, analyze contributors

## 1. Branch Management

Create and list branches. Supports both generic branch names and GitFlow-style prefixes.

**Use when**: You need to create a branch with any name (like `test/xxx`, `doc/xxx`), create GitFlow-style branches (`feature/`, `release/`, `hotfix/`), or list all branches in a repository.

### Example

```bash
# Create a branch with any name (most flexible)
python branch_manager.py create owner repo --name "test/integration-tests" --from main
python branch_manager.py create owner repo --name "doc/api-reference" --from develop

# Create GitFlow-style branches (with automatic prefix)
python branch_manager.py feature owner repo --name "user-authentication" --from develop
python branch_manager.py release owner repo --version "2.0.0" --from develop
python branch_manager.py hotfix owner repo --name "security-patch" --from main

# List all branches
python branch_manager.py list owner repo
```

## 2. GitFlow Workflow

Initialize GitFlow structure and finish (merge) branches.

**Use when**: You need to initialize GitFlow (create develop branch) or finish a feature/release/hotfix by creating a PR and merging it.

**Note**: For creating branches, use `branch_manager.py` (Section 1).

### Example

```bash
# Initialize GitFlow (creates develop branch from main)
python gitflow_manager.py init owner repo

# Finish feature (creates PR and merges to develop)
python gitflow_manager.py finish owner repo --type feature --name "user-authentication" --target develop

# Finish release (creates PR and merges to main)
python gitflow_manager.py finish owner repo --type release --name "2.0.0" --target main

# Finish hotfix (creates PR and merges to main)
python gitflow_manager.py finish owner repo --type hotfix --name "security-patch" --target main

# Finish with custom merge method
python gitflow_manager.py finish owner repo --type feature --name "api-refactor" --target develop --merge-method merge
```

## 3. Release Management

Prepare releases with version bumping and changelog generation.

**Use when**: You need to prepare a release (creates release branch + changelog), update version numbers in config files, or generate changelogs from commit history.

**Note**: The `prepare` command creates a release branch automatically. For other branch types, use `branch_manager.py`.

### Example

```bash
# Prepare a release (creates release/vX.X.X branch and generates changelog)
python release_manager.py prepare owner repo --version "2.1.0" --from develop

# Bump version in package.json
python release_manager.py bump-version owner repo --file "package.json" --version "2.1.0" --branch release/v2.1.0

# Bump version in Cargo.toml
python release_manager.py bump-version owner repo --file "Cargo.toml" --version "2.1.0" --branch release/v2.1.0

# Bump version in pyproject.toml
python release_manager.py bump-version owner repo --file "pyproject.toml" --version "2.1.0" --branch release/v2.1.0

# Generate changelog from commit history
python release_manager.py changelog owner repo --since "2024-01-01" --output "CHANGELOG.md"

# Generate changelog for specific date range
python release_manager.py changelog owner repo --since "2024-06-01" --until "2024-12-01" --output "CHANGELOG.md"

# Finish release (merge to main)
python release_manager.py finish owner repo --version "2.1.0"
```

## 4. Branch Analysis

Analyze commits across branches and generate contributor statistics.

**Use when**: You need to aggregate commits from multiple branches, analyze top contributors, or generate branch reports.

### Example

```bash
# Aggregate commits from multiple branches
python branch_analyzer.py aggregate owner repo --branches "main,develop,feature/auth" --per-branch 5

# Aggregate and save to JSON file
python branch_analyzer.py aggregate owner repo --branches "main,develop,release/v2.0" --output "commits.json"

# Analyze top contributors on main branch
python branch_analyzer.py contributors owner repo --branch main --top 10

# Analyze contributors across all branches
python branch_analyzer.py contributors owner repo --top 20

# Generate comprehensive branch report
python branch_analyzer.py report owner repo --output "BRANCH_REPORT.md"
```
