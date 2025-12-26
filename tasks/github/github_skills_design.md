# GitHub Skills Design for Open Agent Skills

## 1. Analysis of Standard GitHub Tasks
Based on the analysis of 23 tasks in `mcpmark/tasks/github/standard`, the tasks can be categorized into four main domains. Deep understanding of these tasks helps in designing generalized skills.

### Category 1: Repository Analytics & Discovery (Read-Heavy)
**Tasks**: `find_commit_date`, `find_rag_commit`, `find_legacy_name`, `find_salient_file`, `feature_commit_tracking`, `multi_branch_commit_aggregation`, `claude_collaboration_analysis`, `config_parameter_audit`.
**Core Requirements**:
- Searching commit history (by author, date, message, file).
- Aggregating statistics (commit counts, frequently modified files).
- Cross-referencing data (commits across branches).
- Parsing specific file versions from history.

### Category 2: Workflow & CI/CD Automation (Write-Heavy / Configuration)
**Tasks**: `deployment_status_workflow`, `issue_management_workflow`, `pr_automation_workflow`, `linting_ci_workflow`, `automated_changelog_generation`.
**Core Requirements**:
- Creating/Editing GitHub Actions workflow files (`.github/workflows/*.yml`).
- Creating configuration files (`.eslintrc.json`, `package.json`).
- Understanding GitHub event triggers (push, pull_request, issues).
- generating documentation based on repo state (Changelog).

### Category 3: Issue & PR Management (Interaction-Heavy)
**Tasks**: `qwen3_issue_management`, `assign_contributor_labels`, `label_color_standardization`, `issue_tagging_pr_closure`, `fix_conflict`, `critical_issue_hotfix_workflow`.
**Core Requirements**:
- Bulk editing issues (reopening, labeling).
- Managing PR lifecycles (creating, reviewing, closing, merging).
- Handling merge conflicts.
- Linking issues and PRs (cross-referencing).
- Managing labels and milestones.

### Category 4: Branching & Release Strategy (Process-Heavy)
**Tasks**: `advanced_branch_strategy`, `release_management_workflow`, `performance_regression_investigation`, `issue_pr_commit_workflow`.
**Core Requirements**:
- Gitflow implementation (feature -> develop -> release -> main).
- Specific branch naming conventions.
- Release versioning (Cargo.toml updates).
- Cherry-picking or specific commit application.

---

## 2. Proposed Skills Design
To address these categories effectively, we propose the following Skills. Each skill is designed to be a "Generalized Agent" for its domain.

### Skill 1: `github_detective` (Analytics & Discovery)
**Purpose**: specialized in digging through repository history and extracting specific insights.
**Capabilities**:
- `find_commit`: Search commits by complex queries (msg pattern + author + date range).
- `blame_analysis`: Identify who changed what and when (for "find_commit_date").
- `contributor_stats`: Aggregate contributor activity (for "assign_contributor_labels").
- `file_history`: Track changes to a specific file across forks/branches.
**Example Usage**:
```bash
# Find commit adding "RAG" by "Daniel"
python github_detective.py find --query "RAG" --author "Daniel" --type commit

# Find most frequent file changes excluding .github
python github_detective.py stats --metric most_changed_files --exclude ".github/*"
```

### Skill 2: `github_actions_architect` (CI/CD Automation)
**Purpose**: Expert in setting up and fixing GitHub Actions workflows and related configuration.
**Capabilities**:
- `scaffold_workflow`: Generate workflow files from templates (CI, CD, Issue Management).
- `validate_config`: Check syntax of `.yml` and config files (eslint, etc).
- `simulate_trigger`: Explain what events will trigger the workflow.
**Example Usage**:
```bash
# Setup a linting workflow
python github_actions_architect.py create --type lint --runner ubuntu-latest --trigger push,pr

# Scaffolding an issue management workflow
python github_actions_architect.py create --type issue-triage --labels "bug,enhancement"
```

### Skill 3: `github_flow_manager` (Issue/PR/Branching)
**Purpose**: Manages the "human" side of GitHub: issues, PRs, comments, labels, and branching strategies.
**Capabilities**:
- `bulk_manage`: Apply labels/close/reopen multiple issues based on search (for `qwen3_issue_management`).
- `smart_merge`: Handle PR merging with specific strategies (squash, rebase) and conflict resolution helpers.
- `branch_strategy`: Enforce gitflow (create release branches, hotfix branches).
- `release_prep`: Automate version bumps and changelog generation.
**Example Usage**:
```bash
# Reopen all closed Qwen3 issues
python github_flow_manager.py issues --state closed --query "qwen3" --action reopen --add-label "qwen3-related"

# Prepare a release
python github_flow_manager.py release --version 1.1.0 --target main --generate-changelog
```

### Skill 4: `github_content_editor` (Code & Documentation)
**Purpose**: Handles direct file manipulation within the repo context, specifically for documentation and simple code fixes.
**Capabilities**:
- `doc_gen`: Generate Changelogs, Contributors lists, or answers to questions (ANSWER.md).
- `apply_fix`: Apply specific code patterns (like the race condition fix).
- `file_edit`: Search and replace across multiple files (branding updates, etc).

---

## 3. Implementation Plan (Priorities)

1.  **Shared Utils (`skills/github/utils.py`)**:
    *   Initialize `GitHubTools` wrapper for MCP (wrapping `src/mcp_services/github/`).
    *   Ensure robust error handling for API limits.

2.  **Phase 1: `github_detective`**:
    *   Easiest to implement (Read-only mostly).
    *   Solves ~35% of the standard tasks immediately.

3.  **Phase 2: `github_flow_manager`**:
    *   High impact for complex tasks.
    *   Requires careful state management (checks before actions).

4.  **Phase 3: `github_actions_architect`**:
    *   Complex generation but highly valuable for the `mcpmark-cicd` cluster.

## 4. Generic Skill Structure
All GitHub skills should follow this structure to ensuring consistency:
```python
class GitHubSkill:
    def __init__(self, repo_path: str):
        self.tools = GitHubTools(repo_path)

    async def run(self, command: str, **kwargs):
        # 1. Plan: Analyze the request
        # 2. Execute: Call MCP tools
        # 3. Verify: Check if the action succeeded (e.g. did the label appear?)
```
