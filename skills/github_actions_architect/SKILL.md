---
name: github_actions_architect
description: This skill builds and deploys GitHub Actions workflows and configuration files for CI/CD automation. It creates workflows for testing, linting, scheduled tasks, and generates supporting configuration files like ESLint configs and Issue templates. Use this when you need to set up CI/CD pipelines or standardize repository configurations.
---

# GitHub Actions Architect Skill

This skill automates the creation and deployment of GitHub Actions workflows and configurations:

1. **Workflow Building**: Create CI/CD workflows (basic CI, linting, scheduled tasks)
2. **Configuration Generation**: Generate ESLint configs, Issue templates, PR templates

## 1. Workflow Building (Automated Full Pipeline)

**IMPORTANT**: These commands are **fully automated pipelines** that:
1. Create a branch
2. Push all required files (workflow + configs)
3. Create a PR
4. Merge the PR

**Use when**: You want a quick, fully automated setup and don't need control over individual commits.

**DO NOT USE when**: The task requires a specific number of commits or manual control over the process. In that case, use `github_content_editor` skill's `batch` command to push files manually.

### Example

```bash
# Create basic CI workflow (automated: creates branch → pushes files → creates PR → merges)
python workflow_builder.py ci-basic owner repo --trigger "push,pull_request" --branch main --node-version 18

# Create linting workflow with ESLint (automated full pipeline)
python workflow_builder.py lint owner repo --trigger "push,pull_request" --branch main

# Create scheduled workflow (e.g., nightly health check)
python workflow_builder.py scheduled owner repo --cron "0 2 * * *" --script "npm run health-check" --name "Nightly Health Check"
```

## 2. Configuration Generation

Generate CI/CD related configuration files including ESLint config, Issue templates, and PR templates.

**Use when**: You need to add ESLint configuration, standardize Issue reporting, or create PR templates.

### Example

```bash
# Create ESLint configuration
python config_generator.py eslint owner repo --extends "eslint:recommended" --rules "semi,quotes"

# Create Issue templates (bug, feature, maintenance)
python config_generator.py issue-templates owner repo --types "bug,feature,maintenance"

# Create PR template
python config_generator.py pr-template owner repo
```
