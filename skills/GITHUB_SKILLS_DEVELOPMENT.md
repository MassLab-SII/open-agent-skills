# GitHub Skills Development Guide

> 本文档是 GitHub 领域技能开发的完整指南，包含已开发技能的介绍、待开发技能的设计规划，以及开发规范。

## 目录

1. [项目概述](#1-项目概述)
2. [MCP 工具函数清单](#2-mcp-工具函数清单)
3. [已开发技能](#3-已开发技能)
4. [待开发技能](#4-待开发技能)
5. [开发规范](#5-开发规范)
6. [任务覆盖矩阵](#6-任务覆盖矩阵)

---

## 1. 项目概述

### 1.1 背景

GitHub Skills 是 `open-agent-skills` 项目中针对 GitHub 任务领域的技能集合。每个 Skill 是一个 Python 脚本，通过组合 `utils.py` 中封装的 MCP 工具函数来完成特定的复杂任务。

### 1.2 设计原则

- **工具组合唯一性**：每个功能脚本使用的 MCP 工具组合必须不同，避免功能重复
- **CLI 接口**：所有技能通过命令行参数暴露功能
- **异步架构**：使用 `asyncio` 处理 MCP 调用
- **类封装**：核心逻辑封装在类中，便于复用和测试

### 1.3 目录结构

```
skills/
├── github_detective/          # 仓库调查分析（只读）
│   ├── SKILL.md
│   ├── utils.py               # 共享的 MCP 工具封装 ⭐
│   ├── commit_finder.py
│   ├── content_tracker.py
│   ├── pr_investigator.py
│   └── repo_explorer.py
├── github_content_editor/     # 文件编辑/文档生成（写入）
│   ├── SKILL.md
│   ├── utils.py               # 引用 github_detective/utils.py
│   ├── doc_gen.py
│   └── file_editor.py
├── github_flow_manager/       # [待开发] Issue/PR/Label 管理
├── github_actions_architect/  # [待开发] CI/CD 工作流构建
└── github_branch_strategist/  # [待开发] 分支策略与发布管理
```

---

## 2. MCP 工具函数清单


以下是 `github_detective/utils.py` 中封装的所有 MCP 工具函数，按功能分类：

### 2.1 仓库管理 (Repository Management)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `create_repository` | 创建新仓库 | name, description, private |
| `fork_repository` | Fork 仓库 | owner, repo, organization |

### 2.2 分支与提交 (Branch & Commit)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `create_branch` | 创建新分支 | owner, repo, branch, from_branch |
| `get_commit` | 获取提交详情（含 diff） | owner, repo, sha |
| `list_branches` | 列出分支 | owner, repo, page, per_page |
| `list_commits` | 列出提交历史 | owner, repo, sha, path, author, since, until |

### 2.3 文件操作 (File Operations)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `create_or_update_file` | 创建/更新文件 | owner, repo, path, content, message, branch, sha |
| `delete_file` | 删除文件 | owner, repo, path, message, branch, sha |
| `get_file_contents` | 获取文件内容 | owner, repo, path, ref |
| `push_files` | 批量推送文件 | owner, repo, branch, files, message |

### 2.4 Issue 管理 (Issues)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `add_issue_comment` | 添加 Issue 评论 | owner, repo, issue_number, body |
| `issue_read` | 读取 Issue 详情 | owner, repo, issue_number, method |
| `issue_write` | 创建/更新 Issue | owner, repo, title, body, labels, state, issue_number |
| `list_issues` | 列出 Issues | owner, repo, state, labels, page, per_page |
| `search_issues` | 搜索 Issues | query, owner, repo, page, per_page |
| `sub_issue_write` | 添加子 Issue | owner, repo, issue_number, title, sub_issue_id |

### 2.5 Pull Request 管理 (Pull Requests)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `create_pull_request` | 创建 PR | owner, repo, title, head, base, body, draft |
| `list_pull_requests` | 列出 PRs | owner, repo, state, page, per_page |
| `merge_pull_request` | 合并 PR | owner, repo, pull_number, merge_method |
| `pull_request_read` | 读取 PR 详情 | owner, repo, pull_number, method |
| `pull_request_review_write` | 创建/提交 Review | (kwargs) |
| `search_pull_requests` | 搜索 PRs | query, page, per_page |
| `update_pull_request` | 更新 PR | owner, repo, pull_number, title, body, state, labels |
| `update_pull_request_branch` | 更新 PR 分支 | owner, repo, pull_number |
| `add_comment_to_pending_review` | 添加待定 Review 评论 | (kwargs) |
| `request_copilot_review` | 请求 Copilot Review | owner, repo, pull_number |

### 2.6 Release & Tags

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `get_latest_release` | 获取最新 Release | owner, repo |
| `get_release_by_tag` | 按 Tag 获取 Release | owner, repo, tag |
| `get_tag` | 获取 Tag 详情 | owner, repo, tag |
| `list_releases` | 列出 Releases | owner, repo |
| `list_tags` | 列出 Tags | owner, repo |

### 2.7 搜索 (Search)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `search_code` | 搜索代码 ⚠️ | query, page, per_page |
| `search_repositories` | 搜索仓库 | query, page, per_page |
| `search_users` | 搜索用户 | query, page, per_page |

> ⚠️ `search_code` 在新建/私有仓库上不可用（GitHub 索引限制）

### 2.8 其他 (Other)

| 函数名 | 功能描述 | 主要参数 |
|--------|----------|----------|
| `get_me` | 获取当前用户信息 | - |
| `get_label` | 获取标签详情 | owner, repo, name |
| `get_team_members` | 获取团队成员 | org, team_slug |
| `get_teams` | 获取团队列表 | org |
| `assign_copilot_to_issue` | 分配 Copilot 到 Issue | owner, repo, issue_number |
| `list_issue_types` | 列出 Issue 类型 | owner, repo |

---

## 3. 已开发技能


### 3.1 github_detective（仓库调查分析）

**定位**：专注于 GitHub 仓库的只读调查和分析操作。

#### 功能模块

| 脚本 | 功能 | 使用的 MCP 工具组合 |
|------|------|---------------------|
| `commit_finder.py` | 按消息/作者/路径/日期搜索提交 | `list_commits` |
| `content_tracker.py` | 追踪特定内容首次出现的提交 | `search_code` → `list_commits` → `get_commit` |
| `pr_investigator.py` | 搜索和分析 PR | `search_pull_requests` / `list_pull_requests` → `pull_request_read` → `list_commits` |
| `repo_explorer.py` | 探索仓库结构（分支/标签/文件） | `list_branches` + `list_tags` + `list_releases` + `get_file_contents` |

#### 代码结构示例 (commit_finder.py)

```python
#!/usr/bin/env python3
"""Commit Finder Script - 按条件搜索提交"""

import asyncio
import argparse
from utils import GitHubTools

class CommitFinder:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def find_commits(self, query=None, author=None, path=None, 
                           since=None, until=None, limit=20):
        async with GitHubTools() as gh:
            # Step 1: 获取提交列表
            result = await gh.list_commits(
                owner=self.owner, repo=self.repo,
                author=author, path=path, since=since, until=until
            )
            # Step 2: 按消息过滤
            commits = self._parse_result(result)
            return [c for c in commits if self._matches_query(c, query)][:limit]

async def main():
    parser = argparse.ArgumentParser(description='Search commits')
    parser.add_argument('owner', help='Repository owner')
    parser.add_argument('repo', help='Repository name')
    parser.add_argument('--query', help='Regex for commit message')
    # ... 其他参数
    args = parser.parse_args()
    
    finder = CommitFinder(args.owner, args.repo)
    commits = await finder.find_commits(query=args.query)
    finder.print_results(commits)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 覆盖的任务

- `find_commit_date`, `find_rag_commit`, `find_legacy_name`
- `find_salient_file`, `feature_commit_tracking`
- `claude_collaboration_analysis`, `config_parameter_audit`
- `count_translations`, `find_ga_tracking_id`

---

### 3.2 github_content_editor（文件编辑/文档生成）

**定位**：专注于 GitHub 仓库的文件创建、编辑和文档生成。

#### 功能模块

| 脚本 | 功能 | 使用的 MCP 工具组合 |
|------|------|---------------------|
| `doc_gen.py` | 生成文档（ANSWER.md/CHANGELOG/CONTRIBUTORS） | `get_file_contents` → `create_or_update_file` / `list_commits` → `create_or_update_file` |
| `file_editor.py` | 编辑文件/应用修复/批量替换 | `get_file_contents` → `create_or_update_file` / `search_code` → `get_file_contents` → `create_or_update_file` |

#### 代码结构示例 (doc_gen.py)

```python
#!/usr/bin/env python3
"""Documentation Generator - 生成文档文件"""

import asyncio
import argparse
from utils import GitHubTools

class DocGenerator:
    def __init__(self):
        self.github = GitHubTools()

    async def create_answer_file(self, owner, repo, content, message, branch="main"):
        async with self.github:
            # Step 1: 检查文件是否存在（获取 SHA）
            existing = await self.github.get_file_contents(owner, repo, "ANSWER.md", ref=branch)
            sha = existing.get("sha") if isinstance(existing, dict) else None
            
            # Step 2: 创建/更新文件
            result = await self.github.create_or_update_file(
                owner=owner, repo=repo, path="ANSWER.md",
                content=content, message=message, branch=branch, sha=sha
            )
            return self._check_success(result)

async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    
    answer_parser = subparsers.add_parser("answer")
    answer_parser.add_argument("owner")
    answer_parser.add_argument("repo")
    answer_parser.add_argument("--content", required=True)
    # ...
    
    args = parser.parse_args()
    generator = DocGenerator()
    
    if args.command == "answer":
        await generator.create_answer_file(args.owner, args.repo, args.content, ...)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 覆盖的任务

- 所有需要提交 `ANSWER.md` 的任务
- `add_terminal_shortcuts_doc`
- `automated_changelog_generation`（部分）

---

## 4. 待开发技能


### 4.1 github_flow_manager（Issue/PR/Label 管理）⭐ 优先级最高

**定位**：管理 GitHub 的"人机交互"层面：Issue、PR、评论、标签的批量操作和生命周期管理。

#### 目录结构

```
skills/github_flow_manager/
├── SKILL.md
├── utils.py                    # 软链接或导入 github_detective/utils.py
├── issue_manager.py            # Issue 批量管理
├── pr_manager.py               # PR 生命周期管理
├── label_manager.py            # 标签管理
└── comment_manager.py          # 评论管理
```

#### 功能模块设计

##### 4.1.1 issue_manager.py - Issue 批量管理

**功能**：批量关闭/重开/打标签 Issue，创建 Issue，搜索 Issue

**使用的 MCP 工具组合**：
- 批量关闭有评论的 Issue：`list_issues` → `issue_read` → `issue_write(state="closed")`
- 重开并打标签：`search_issues` → `issue_write(state="open", labels=[...])`
- 创建 Issue：`issue_write(method="create")`

**CLI 设计**：
```bash
# 关闭所有有评论的 Issue
python issue_manager.py close owner repo --filter has_comments

# 重开包含关键词的 Issue 并打标签
python issue_manager.py reopen owner repo --query "qwen3" --add-label "qwen3-related"

# 批量打标签
python issue_manager.py label owner repo --issues "1,2,3" --add-labels "bug,priority-high"

# 创建 Issue
python issue_manager.py create owner repo --title "Bug Report" --body "..." --labels "bug"

# 创建带 checklist 的 Issue
python issue_manager.py create owner repo --title "Task" --checklist "item1,item2,item3"
```

**代码框架**：
```python
#!/usr/bin/env python3
"""Issue Manager - Issue 批量管理"""

import asyncio
import argparse
import json
from typing import List, Optional
from utils import GitHubTools

class IssueManager:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def close_issues_with_comments(self) -> List[int]:
        """关闭所有有评论的 Issue"""
        async with GitHubTools() as gh:
            closed_issues = []
            # Step 1: 获取所有 open issues
            issues = await gh.list_issues(self.owner, self.repo, state="open", per_page=100)
            issues = self._parse_result(issues)
            
            for issue in issues:
                issue_number = issue.get("number")
                # Step 2: 检查是否有评论
                detail = await gh.issue_read(self.owner, self.repo, issue_number)
                if self._has_comments(detail):
                    # Step 3: 关闭 Issue
                    await gh.issue_write(
                        owner=self.owner, repo=self.repo,
                        title=issue.get("title"), issue_number=issue_number,
                        state="closed"
                    )
                    closed_issues.append(issue_number)
            return closed_issues

    async def reopen_and_label(self, query: str, labels: List[str]) -> List[int]:
        """重开匹配的 Issue 并打标签"""
        async with GitHubTools() as gh:
            reopened = []
            # Step 1: 搜索已关闭的 Issue
            search_query = f"{query} repo:{self.owner}/{self.repo} is:closed"
            results = await gh.search_issues(search_query)
            items = self._parse_search_result(results)
            
            for item in items:
                issue_number = item.get("number")
                # Step 2: 重开并打标签
                await gh.issue_write(
                    owner=self.owner, repo=self.repo,
                    title=item.get("title"), issue_number=issue_number,
                    state="open", labels=labels
                )
                reopened.append(issue_number)
            return reopened

    async def create_issue(self, title: str, body: str = None, 
                           labels: List[str] = None, checklist: List[str] = None) -> int:
        """创建新 Issue"""
        async with GitHubTools() as gh:
            # 构建 body（支持 checklist）
            if checklist:
                body = (body or "") + "\n\n" + "\n".join([f"- [ ] {item}" for item in checklist])
            
            result = await gh.issue_write(
                owner=self.owner, repo=self.repo,
                title=title, body=body, labels=labels, method="create"
            )
            return self._extract_issue_number(result)
```

**覆盖的任务**：
- `close_commented_issues` (easy)
- `qwen3_issue_management` (standard)
- `triage_missing_tool_result_issue` (easy)
- `critical_issue_hotfix_workflow` (部分)
- `label_color_standardization` (部分)

---

##### 4.1.2 pr_manager.py - PR 生命周期管理

**功能**：创建 PR、合并 PR、关闭 PR、更新 PR、添加评论

**使用的 MCP 工具组合**：
- 创建并合并 PR：`create_branch` → `push_files` → `create_pull_request` → `merge_pull_request`
- 更新 PR 描述：`update_pull_request`
- 关闭 PR：`update_pull_request(state="closed")`
- 添加 PR 评论：`add_issue_comment`

**CLI 设计**：
```bash
# 创建 PR
python pr_manager.py create owner repo --head feature-branch --base main --title "Add feature" --body "..."

# 创建并立即合并
python pr_manager.py create owner repo --head feature --base main --title "Fix" --merge squash

# 合并已有 PR
python pr_manager.py merge owner repo --number 42 --method squash

# 关闭 PR（不合并）
python pr_manager.py close owner repo --number 42 --comment "Closing due to..."

# 更新 PR
python pr_manager.py update owner repo --number 42 --title "New Title" --body "Updated body"

# 添加评论
python pr_manager.py comment owner repo --number 42 --body "Thanks for the contribution!"
```

**代码框架**：
```python
#!/usr/bin/env python3
"""PR Manager - Pull Request 生命周期管理"""

import asyncio
import argparse
from typing import Optional, List
from utils import GitHubTools

class PRManager:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def create_and_merge(self, head: str, base: str, title: str, 
                                body: str = None, merge_method: str = "squash") -> dict:
        """创建 PR 并合并"""
        async with GitHubTools() as gh:
            # Step 1: 创建 PR
            pr_result = await gh.create_pull_request(
                owner=self.owner, repo=self.repo,
                title=title, head=head, base=base, body=body
            )
            pr_number = self._extract_pr_number(pr_result)
            
            # Step 2: 合并 PR
            merge_result = await gh.merge_pull_request(
                owner=self.owner, repo=self.repo,
                pull_number=pr_number, merge_method=merge_method
            )
            return {"pr_number": pr_number, "merged": True}

    async def close_pr(self, pr_number: int, comment: str = None) -> bool:
        """关闭 PR（不合并）"""
        async with GitHubTools() as gh:
            # Step 1: 添加评论（可选）
            if comment:
                await gh.add_issue_comment(self.owner, self.repo, pr_number, comment)
            
            # Step 2: 关闭 PR
            result = await gh.update_pull_request(
                owner=self.owner, repo=self.repo,
                pull_number=pr_number, state="closed"
            )
            return self._check_success(result)

    async def add_review_comment(self, pr_number: int, body: str, event: str = "COMMENT") -> bool:
        """添加 Review 评论"""
        async with GitHubTools() as gh:
            # Step 1: 创建 pending review
            await gh.pull_request_review_write(
                owner=self.owner, repo=self.repo,
                pullNumber=pr_number, method="create", event=event, body=body
            )
            return True
```

**覆盖的任务**：
- `thank_docker_pr_author` (easy)
- `fix_conflict` (standard)
- `issue_tagging_pr_closure` (standard)
- `issue_pr_commit_workflow` (standard)
- 所有需要创建/合并 PR 的 CI/CD 任务

---

##### 4.1.3 label_manager.py - 标签管理

**功能**：批量应用标签、移除标签、列出所有标签

**使用的 MCP 工具组合**：
- 批量打标签：`issue_write(labels=[...])` / `update_pull_request(labels=[...])`
- 获取标签信息：`get_label`
- 列出 Issue 标签：`issue_read(method="get_labels")`

**CLI 设计**：
```bash
# 给 Issue 添加标签
python label_manager.py add owner repo --issue 42 --labels "bug,priority-high"

# 给 PR 添加标签
python label_manager.py add owner repo --pr 42 --labels "enhancement"

# 移除标签
python label_manager.py remove owner repo --issue 42 --labels "needs-triage"

# 批量给多个 Issue 打标签
python label_manager.py batch owner repo --issues "1,2,3" --labels "reviewed"
```

**覆盖的任务**：
- `assign_contributor_labels` (standard)
- `label_color_standardization` (standard)
- `triage_missing_tool_result_issue` (easy)

---

##### 4.1.4 comment_manager.py - 评论管理

**功能**：添加 Issue/PR 评论、创建 Review 评论

**使用的 MCP 工具组合**：
- 添加普通评论：`add_issue_comment`
- 添加 Review 评论：`pull_request_review_write` → `add_comment_to_pending_review`

**CLI 设计**：
```bash
# 添加 Issue 评论
python comment_manager.py add owner repo --issue 42 --body "Thanks for reporting!"

# 添加 PR 评论
python comment_manager.py add owner repo --pr 42 --body "LGTM!"

# 添加 Review 评论
python comment_manager.py review owner repo --pr 42 --body "Please fix..." --event REQUEST_CHANGES
```

**覆盖的任务**：
- `thank_docker_pr_author` (easy)
- `triage_missing_tool_result_issue` (easy)
- `issue_pr_commit_workflow` (standard)

---


### 4.2 github_actions_architect（CI/CD 工作流构建）⭐ 优先级高

**定位**：专注于 GitHub Actions 工作流的创建、配置和管理。

#### 目录结构

```
skills/github_actions_architect/
├── SKILL.md
├── utils.py                    # 软链接或导入 github_detective/utils.py
├── workflow_builder.py         # 工作流构建器
├── config_generator.py         # 配置文件生成器
└── templates/                  # 工作流模板
    ├── ci_basic.yml
    ├── ci_lint.yml
    ├── issue_automation.yml
    ├── pr_automation.yml
    └── deployment.yml
```

#### 功能模块设计

##### 4.2.1 workflow_builder.py - 工作流构建器

**功能**：创建各类 GitHub Actions 工作流文件

**使用的 MCP 工具组合**：
- 创建工作流：`create_branch` → `push_files` → `create_pull_request` → `merge_pull_request`
- 直接推送：`create_or_update_file`

**CLI 设计**：
```bash
# 创建基础 CI 工作流
python workflow_builder.py create owner repo --type ci-basic \
    --trigger "push,pull_request" --branch main --node-version 18

# 创建 Lint 工作流
python workflow_builder.py create owner repo --type lint \
    --trigger "push,pull_request" --eslint-config ".eslintrc.json"

# 创建 Issue 自动化工作流
python workflow_builder.py create owner repo --type issue-automation \
    --auto-label --auto-assign --welcome-message

# 创建 PR 自动化工作流
python workflow_builder.py create owner repo --type pr-automation \
    --code-quality --testing --security-scan

# 创建定时任务工作流
python workflow_builder.py create owner repo --type scheduled \
    --cron "0 2 * * *" --script "npm run health-check"

# 创建部署状态工作流
python workflow_builder.py create owner repo --type deployment \
    --pre-deployment --rollback --post-deployment
```

**代码框架**：
```python
#!/usr/bin/env python3
"""Workflow Builder - GitHub Actions 工作流构建器"""

import asyncio
import argparse
from typing import Optional, List, Dict
from utils import GitHubTools

class WorkflowBuilder:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        self.templates = self._load_templates()

    async def create_ci_workflow(self, trigger: List[str], branch: str, 
                                  node_version: str = "18") -> bool:
        """创建基础 CI 工作流"""
        async with GitHubTools() as gh:
            # Step 1: 创建分支
            branch_name = "ci/add-basic-workflow"
            await gh.create_branch(self.owner, self.repo, branch_name, from_branch="main")
            
            # Step 2: 生成工作流内容
            workflow_content = self._generate_ci_workflow(trigger, branch, node_version)
            
            # Step 3: 推送文件
            files = [{"path": ".github/workflows/ci.yml", "content": workflow_content}]
            await gh.push_files(self.owner, self.repo, branch_name, files, "Add CI workflow")
            
            # Step 4: 创建 PR
            pr_result = await gh.create_pull_request(
                owner=self.owner, repo=self.repo,
                title="Add basic CI workflow", head=branch_name, base="main",
                body="## Summary\nAdds CI workflow for automated testing."
            )
            pr_number = self._extract_pr_number(pr_result)
            
            # Step 5: 合并 PR
            await gh.merge_pull_request(self.owner, self.repo, pr_number, "squash")
            return True

    def _generate_ci_workflow(self, trigger: List[str], branch: str, node_version: str) -> str:
        """生成 CI 工作流 YAML"""
        triggers = "\n".join([f"  {t}:\n    branches: [{branch}]" for t in trigger])
        return f'''name: Basic CI Checks

on:
{triggers}

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '{node_version}'
      - run: npm ci
      - run: npm run lint
      - run: npm test
'''
```

**覆盖的任务**：
- `basic_ci_checks` (easy)
- `issue_lint_guard` (easy)
- `nightly_health_check` (easy)
- `deployment_status_workflow` (standard)
- `issue_management_workflow` (standard)
- `linting_ci_workflow` (standard)
- `pr_automation_workflow` (standard)

---

##### 4.2.2 config_generator.py - 配置文件生成器

**功能**：生成 CI/CD 相关的配置文件（ESLint、package.json 等）

**使用的 MCP 工具组合**：
- 创建配置文件：`create_or_update_file`
- 批量创建：`push_files`

**CLI 设计**：
```bash
# 创建 ESLint 配置
python config_generator.py eslint owner repo --extends "eslint:recommended" --rules "semi,quotes"

# 创建 Issue 模板
python config_generator.py issue-templates owner repo --types "bug,feature,maintenance"

# 创建 PR 模板
python config_generator.py pr-template owner repo
```

**覆盖的任务**：
- `linting_ci_workflow` (standard) - 需要创建 `.eslintrc.json`
- `issue_management_workflow` (standard) - 需要创建 Issue 模板

---

### 4.3 github_branch_strategist（分支策略与发布管理）⭐ 优先级中

**定位**：管理分支策略（GitFlow）、发布流程、版本管理。

#### 目录结构

```
skills/github_branch_strategist/
├── SKILL.md
├── utils.py                    # 软链接或导入 github_detective/utils.py
├── gitflow_manager.py          # GitFlow 分支管理
├── release_manager.py          # 发布管理
└── branch_analyzer.py          # 分支分析
```

#### 功能模块设计

##### 4.3.1 gitflow_manager.py - GitFlow 分支管理

**功能**：初始化 GitFlow 结构、创建 feature/release/hotfix 分支

**使用的 MCP 工具组合**：
- 初始化 GitFlow：`create_branch("develop")` → `create_branch("release/v1.0.0")`
- 创建 feature 分支：`create_branch` → `push_files` → `create_pull_request`
- 合并到 develop：`merge_pull_request`

**CLI 设计**：
```bash
# 初始化 GitFlow 结构
python gitflow_manager.py init owner repo

# 创建 feature 分支
python gitflow_manager.py feature owner repo --name "protocol-fix" --from develop

# 创建 release 分支
python gitflow_manager.py release owner repo --version "1.0.0" --from develop

# 创建 hotfix 分支
python gitflow_manager.py hotfix owner repo --name "memory-fix" --from main

# 完成 feature（合并到 develop）
python gitflow_manager.py finish-feature owner repo --name "protocol-fix"
```

**代码框架**：
```python
#!/usr/bin/env python3
"""GitFlow Manager - GitFlow 分支管理"""

import asyncio
import argparse
from utils import GitHubTools

class GitFlowManager:
    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo

    async def init_gitflow(self) -> bool:
        """初始化 GitFlow 结构"""
        async with GitHubTools() as gh:
            # Step 1: 创建 develop 分支
            await gh.create_branch(self.owner, self.repo, "develop", from_branch="main")
            print("Created 'develop' branch from 'main'")
            return True

    async def create_feature_branch(self, name: str, from_branch: str = "develop") -> bool:
        """创建 feature 分支"""
        async with GitHubTools() as gh:
            branch_name = f"feature/{name}"
            await gh.create_branch(self.owner, self.repo, branch_name, from_branch=from_branch)
            print(f"Created '{branch_name}' from '{from_branch}'")
            return True

    async def create_release_branch(self, version: str, from_branch: str = "develop") -> bool:
        """创建 release 分支"""
        async with GitHubTools() as gh:
            branch_name = f"release/v{version}"
            await gh.create_branch(self.owner, self.repo, branch_name, from_branch=from_branch)
            print(f"Created '{branch_name}' from '{from_branch}'")
            return True

    async def finish_feature(self, name: str, target: str = "develop") -> bool:
        """完成 feature（创建 PR 并合并）"""
        async with GitHubTools() as gh:
            branch_name = f"feature/{name}"
            # Step 1: 创建 PR
            pr_result = await gh.create_pull_request(
                owner=self.owner, repo=self.repo,
                title=f"Merge feature/{name} into {target}",
                head=branch_name, base=target
            )
            pr_number = self._extract_pr_number(pr_result)
            
            # Step 2: 合并 PR
            await gh.merge_pull_request(self.owner, self.repo, pr_number, "squash")
            return True
```

**覆盖的任务**：
- `advanced_branch_strategy` (standard)
- `release_management_workflow` (standard)
- `performance_regression_investigation` (standard)

---

##### 4.3.2 release_manager.py - 发布管理

**功能**：版本更新、Changelog 生成、Release 创建

**使用的 MCP 工具组合**：
- 版本更新：`get_file_contents` → `create_or_update_file`
- Changelog 生成：`list_commits` → `push_files`
- 创建 Release PR：`create_branch` → `push_files` → `create_pull_request` → `merge_pull_request`

**CLI 设计**：
```bash
# 准备发布
python release_manager.py prepare owner repo --version "1.1.0" --from develop

# 更新版本号
python release_manager.py bump-version owner repo --file "Cargo.toml" --version "1.1.0"

# 生成 Changelog
python release_manager.py changelog owner repo --since "2024-01-01" --output "CHANGELOG.md"

# 完成发布（合并到 main）
python release_manager.py finish owner repo --version "1.1.0"
```

**覆盖的任务**：
- `release_management_workflow` (standard)
- `automated_changelog_generation` (standard)

---

##### 4.3.3 branch_analyzer.py - 分支分析

**功能**：跨分支 commit 聚合、分支比较、贡献者统计

**使用的 MCP 工具组合**：
- 跨分支聚合：`list_branches` → `list_commits(sha=branch)` (多次)
- 贡献者统计：`list_commits` → 聚合分析

**CLI 设计**：
```bash
# 聚合多分支 commit
python branch_analyzer.py aggregate owner repo --branches "main,develop,release/v1.0"

# 分析贡献者
python branch_analyzer.py contributors owner repo --top 10

# 生成分支报告
python branch_analyzer.py report owner repo --output "BRANCH_REPORT.md"
```

**覆盖的任务**：
- `multi_branch_commit_aggregation` (standard)
- `claude_collaboration_analysis` (standard)

---

## 5. 开发规范


### 5.1 代码风格规范

所有 GitHub Skills 必须遵循以下代码风格：

#### 5.1.1 文件头部

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
<Script Name>
=============

<Brief description of what this script does>

Usage:
    python <script_name>.py <command> <owner> <repo> [options]

Examples:
    # Example 1
    python <script_name>.py <command> owner repo --option value
    
    # Example 2
    python <script_name>.py <command> owner repo --another-option
"""

import asyncio
import argparse
import json
from typing import List, Dict, Any, Optional

from utils import GitHubTools
```

#### 5.1.2 类结构

```python
class SkillClassName:
    """<Class description>"""

    def __init__(self, owner: str, repo: str):
        """
        Initialize the skill.
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        self.owner = owner
        self.repo = repo

    async def main_function(self, param1: str, param2: Optional[str] = None) -> Any:
        """
        <Function description>

        Args:
            param1: Description of param1
            param2: Description of param2 (optional)

        Returns:
            Description of return value
        """
        async with GitHubTools() as gh:
            # Step 1: <Description>
            result1 = await gh.some_tool(...)
            
            # Step 2: <Description>
            result2 = await gh.another_tool(...)
            
            return result2

    def _parse_result(self, result: Any) -> Any:
        """Parse API result (internal helper)"""
        if isinstance(result, list):
            return result
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return []
        return []

    def print_results(self, results: List[Dict[str, Any]]):
        """Pretty print results"""
        if not results:
            print("\nNo results found.")
            return
        # ... formatting logic
```

#### 5.1.3 Main 函数结构

```python
async def main():
    parser = argparse.ArgumentParser(
        description='<Script description>',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Example 1
  python script.py command owner repo --option value
  
  # Example 2
  python script.py command owner repo --another-option
        """
    )
    
    # 子命令（如果需要）
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command: <command_name>
    cmd_parser = subparsers.add_parser("<command>", help="<Command description>")
    cmd_parser.add_argument("owner", help="Repository owner")
    cmd_parser.add_argument("repo", help="Repository name")
    cmd_parser.add_argument("--option", help="Option description")
    
    args = parser.parse_args()
    
    skill = SkillClassName(args.owner, args.repo)
    
    try:
        if args.command == "<command>":
            result = await skill.main_function(args.option)
            skill.print_results(result)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
```

### 5.2 工具组合唯一性原则

**核心原则**：每个功能脚本使用的 MCP 工具组合必须唯一，避免功能重复。

#### 已使用的工具组合

| 脚本 | 工具组合 |
|------|----------|
| `commit_finder.py` | `list_commits` |
| `content_tracker.py` | `search_code` → `list_commits` → `get_commit` |
| `pr_investigator.py` | `search_pull_requests` / `list_pull_requests` → `pull_request_read` → `list_commits` |
| `repo_explorer.py` | `list_branches` + `list_tags` + `list_releases` + `get_file_contents` |
| `doc_gen.py` | `get_file_contents` → `create_or_update_file` / `list_commits` → `create_or_update_file` |
| `file_editor.py` | `get_file_contents` → `create_or_update_file` / `search_code` → `get_file_contents` → `create_or_update_file` |

#### 待开发脚本的工具组合（确保唯一）

| 脚本 | 工具组合 |
|------|----------|
| `issue_manager.py` | `list_issues` → `issue_read` → `issue_write` / `search_issues` → `issue_write` |
| `pr_manager.py` | `create_branch` → `push_files` → `create_pull_request` → `merge_pull_request` |
| `label_manager.py` | `issue_write(labels)` / `update_pull_request(labels)` / `get_label` |
| `comment_manager.py` | `add_issue_comment` / `pull_request_review_write` → `add_comment_to_pending_review` |
| `workflow_builder.py` | `create_branch` → `push_files` → `create_pull_request` → `merge_pull_request` (with YAML generation) |
| `config_generator.py` | `create_or_update_file` (with config generation) |
| `gitflow_manager.py` | `create_branch` (multiple) → `create_pull_request` → `merge_pull_request` |
| `release_manager.py` | `get_file_contents` → `create_or_update_file` + `list_commits` → `push_files` |
| `branch_analyzer.py` | `list_branches` → `list_commits(sha=branch)` (multiple) |

### 5.3 错误处理规范

```python
async def some_function(self):
    async with GitHubTools() as gh:
        try:
            result = await gh.some_tool(...)
            
            # 检查 API 成功
            if not self._check_success(result):
                print(f"API call failed: {result}")
                return None
            
            return self._parse_result(result)
            
        except Exception as e:
            print(f"Error in some_function: {e}")
            return None

def _check_success(self, result: Any) -> bool:
    """Check if API result indicates success"""
    if not result:
        return False
    if isinstance(result, dict):
        if "error" in result or result.get("isError"):
            return False
        if "commit" in result or "content" in result:
            return True
    if isinstance(result, str):
        result_lower = result.lower()
        if "error" in result_lower or "failed" in result_lower:
            return False
        if "commit" in result_lower or '"sha"' in result_lower:
            return True
    return True  # Default to success if no error indicators
```

### 5.4 SKILL.md 文档规范

每个技能目录必须包含 `SKILL.md` 文件，格式如下：

```markdown
---
name: <skill_name>
description: <One-line description of the skill>
---

# <Skill Display Name>

<Brief description of what this skill does>

## 1. <Feature 1 Name>

<Description of feature 1>

**Use when**: <When to use this feature>

### Example

```bash
# Example command 1
python script.py command owner repo --option value

# Example command 2
python script.py command owner repo --another-option
```

## 2. <Feature 2 Name>

...
```

---

## 6. 任务覆盖矩阵


### 6.1 Easy 级别任务

| 任务 | 仓库 | 覆盖技能 | 状态 |
|------|------|----------|------|
| `close_commented_issues` | build-your-own-x | `github_flow_manager/issue_manager.py` | 待开发 |
| `record_recent_commits` | build-your-own-x | `github_flow_manager/issue_manager.py` | 待开发 |
| `add_terminal_shortcuts_doc` | claude-code | `github_content_editor/doc_gen.py` | ✅ 已覆盖 |
| `thank_docker_pr_author` | claude-code | `github_flow_manager/comment_manager.py` | 待开发 |
| `triage_missing_tool_result_issue` | claude-code | `github_flow_manager/issue_manager.py` + `label_manager.py` | 待开发 |
| `basic_ci_checks` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` | 待开发 |
| `issue_lint_guard` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` | 待开发 |
| `nightly_health_check` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` | 待开发 |
| `count_translations` | missing-semester | `github_detective/repo_explorer.py` + `github_content_editor/doc_gen.py` | ✅ 已覆盖 |
| `find_ga_tracking_id` | missing-semester | `github_detective/repo_explorer.py` + `github_content_editor/doc_gen.py` | ✅ 已覆盖 |

### 6.2 Standard 级别任务

| 任务 | 仓库 | 覆盖技能 | 状态 |
|------|------|----------|------|
| `find_commit_date` | build_your_own_x | `github_detective/content_tracker.py` | ✅ 已覆盖 |
| `find_rag_commit` | build_your_own_x | `github_detective/content_tracker.py` | ✅ 已覆盖 |
| `automated_changelog_generation` | claude-code | `github_branch_strategist/release_manager.py` | 待开发 |
| `claude_collaboration_analysis` | claude-code | `github_detective/commit_finder.py` + `github_content_editor/doc_gen.py` | ✅ 已覆盖 |
| `critical_issue_hotfix_workflow` | claude-code | `github_flow_manager` + `github_branch_strategist` | 待开发 |
| `feature_commit_tracking` | claude-code | `github_detective/commit_finder.py` + `github_content_editor/doc_gen.py` | ✅ 已覆盖 |
| `label_color_standardization` | claude-code | `github_flow_manager/label_manager.py` | 待开发 |
| `advanced_branch_strategy` | easyr1 | `github_branch_strategist/gitflow_manager.py` | 待开发 |
| `config_parameter_audit` | easyr1 | `github_detective/commit_finder.py` + `github_content_editor/doc_gen.py` | ✅ 已覆盖 |
| `performance_regression_investigation` | easyr1 | `github_flow_manager/issue_manager.py` + `github_branch_strategist` | 待开发 |
| `qwen3_issue_management` | easyr1 | `github_flow_manager/issue_manager.py` | 待开发 |
| `fix_conflict` | harmony | `github_flow_manager/pr_manager.py` | 待开发 |
| `issue_pr_commit_workflow` | harmony | `github_flow_manager` (全部模块) | 待开发 |
| `issue_tagging_pr_closure` | harmony | `github_flow_manager/issue_manager.py` + `pr_manager.py` | 待开发 |
| `multi_branch_commit_aggregation` | harmony | `github_branch_strategist/branch_analyzer.py` | 待开发 |
| `release_management_workflow` | harmony | `github_branch_strategist/release_manager.py` | 待开发 |
| `deployment_status_workflow` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` | 待开发 |
| `issue_management_workflow` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` + `config_generator.py` | 待开发 |
| `linting_ci_workflow` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` + `config_generator.py` | 待开发 |
| `pr_automation_workflow` | mcpmark-cicd | `github_actions_architect/workflow_builder.py` | 待开发 |
| `assign_contributor_labels` | missing-semester | `github_flow_manager/label_manager.py` | 待开发 |
| `find_legacy_name` | missing-semester | `github_detective/content_tracker.py` | ✅ 已覆盖 |
| `find_salient_file` | missing-semester | `github_detective/commit_finder.py` | ✅ 已覆盖 |

### 6.3 覆盖率统计

| 技能 | 覆盖任务数 | 状态 |
|------|-----------|------|
| `github_detective` | 9 | ✅ 已开发 |
| `github_content_editor` | 6 | ✅ 已开发 |
| `github_flow_manager` | 12 | 🔴 待开发 |
| `github_actions_architect` | 7 | 🔴 待开发 |
| `github_branch_strategist` | 5 | 🔴 待开发 |

### 6.4 开发优先级

1. **`github_flow_manager`** - 覆盖 12 个任务，优先级最高
2. **`github_actions_architect`** - 覆盖 7 个任务，优先级高
3. **`github_branch_strategist`** - 覆盖 5 个任务，优先级中

---

## 附录 A：工具函数快速参考

### Issue 相关
```python
# 列出 Issues
await gh.list_issues(owner, repo, state="open", labels=["bug"], per_page=100)

# 搜索 Issues
await gh.search_issues("qwen3 repo:owner/repo is:closed")

# 读取 Issue 详情
await gh.issue_read(owner, repo, issue_number)

# 创建 Issue
await gh.issue_write(owner, repo, title="Bug", body="...", labels=["bug"], method="create")

# 更新 Issue（关闭/重开/打标签）
await gh.issue_write(owner, repo, title="Bug", issue_number=42, state="closed", labels=["fixed"])

# 添加评论
await gh.add_issue_comment(owner, repo, issue_number, "Thanks!")
```

### PR 相关
```python
# 创建 PR
await gh.create_pull_request(owner, repo, title="Fix", head="feature", base="main", body="...")

# 合并 PR
await gh.merge_pull_request(owner, repo, pull_number, merge_method="squash")

# 更新 PR
await gh.update_pull_request(owner, repo, pull_number, title="New Title", state="closed")

# 读取 PR 详情
await gh.pull_request_read(owner, repo, pull_number, method="get")
await gh.pull_request_read(owner, repo, pull_number, method="get_files")
```

### 分支相关
```python
# 创建分支
await gh.create_branch(owner, repo, "feature/new", from_branch="main")

# 列出分支
await gh.list_branches(owner, repo)
```

### 文件相关
```python
# 获取文件内容
await gh.get_file_contents(owner, repo, "README.md", ref="main")

# 创建/更新文件
await gh.create_or_update_file(owner, repo, "file.md", content, message, branch, sha=None)

# 批量推送文件
files = [{"path": "a.txt", "content": "..."}, {"path": "b.txt", "content": "..."}]
await gh.push_files(owner, repo, branch, files, message)
```

---

*文档版本: 1.0*
*最后更新: 2025-12-13*
*作者: GitHub Skills Development Team*
