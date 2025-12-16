# Git 上传指南

## 步骤 1: 配置 Git 用户信息

首先需要配置你的 Git 用户名和邮箱（这些信息会显示在提交记录中）：

```bash
# 配置用户名（替换为你的 GitHub 用户名）
git config user.name "你的GitHub用户名"

# 配置邮箱（替换为你的 GitHub 邮箱）
git config user.email "你的邮箱@example.com"

# 验证配置
git config user.name
git config user.email
```

## 步骤 2: 添加要上传的文件

```bash
# 添加新开发的技能目录
git add skills/github_detective/
git add skills/github_content_editor/

# 添加技能开发文档
git add skills/GITHUB_SKILLS_DEVELOPMENT.md

# 添加任务设计文档
git add tasks/github/github_skills_design.md

# 添加技能分析报告
git add skill_analysis_and_design_report_zh.md

# 查看将要提交的文件
git status
```

## 步骤 3: 提交更改

```bash
# 提交更改（使用有意义的提交信息）
git commit -m "feat: add github_detective and github_content_editor skills

- Add github_detective skill for repository investigation
  - commit_finder.py: search commits by message/author/date
  - content_tracker.py: track content introduction
  - pr_investigator.py: analyze pull requests
  - repo_explorer.py: explore repository structure
  
- Add github_content_editor skill for file editing
  - doc_gen.py: generate documentation files
  - file_editor.py: edit files and apply fixes
  
- Add comprehensive GitHub skills development guide
- Add task design documentation"
```

## 步骤 4: 推送到 GitHub

```bash
# 推送到远程仓库
git push origin main
```

如果遇到认证问题，你可能需要：

### 选项 A: 使用 Personal Access Token (推荐)

1. 在 GitHub 上生成 Personal Access Token:
   - 访问 https://github.com/settings/tokens
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 勾选 `repo` 权限
   - 生成并复制 token

2. 推送时使用 token:
```bash
git push https://YOUR_TOKEN@github.com/zjtco-yr/open-agent-skills.git main
```

### 选项 B: 使用 SSH (如果已配置)

```bash
# 修改远程地址为 SSH
git remote set-url origin git@github.com:zjtco-yr/open-agent-skills.git

# 推送
git push origin main
```

## 步骤 5: 验证上传

访问 https://github.com/zjtco-yr/open-agent-skills 查看你的提交是否成功。

---

## 可选：清理不需要的文件

如果有些文件不想上传（如临时文件），可以添加到 `.gitignore`：

```bash
# 编辑 .gitignore
echo "ANSWER.md" >> .gitignore
echo "github_state.zip" >> .gitignore
echo "build-your-own-x/" >> .gitignore
echo "check_tools.py" >> .gitignore
echo "reproduce_split.py" >> .gitignore

# 提交 .gitignore 更改
git add .gitignore
git commit -m "chore: update .gitignore"
git push origin main
```

---

## 快速命令汇总

```bash
# 1. 配置用户信息
git config user.name "你的用户名"
git config user.email "你的邮箱"

# 2. 添加文件
git add skills/github_detective/ skills/github_content_editor/ skills/GITHUB_SKILLS_DEVELOPMENT.md

# 3. 提交
git commit -m "feat: add github skills"

# 4. 推送
git push origin main
```
