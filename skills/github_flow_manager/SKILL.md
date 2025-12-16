---
name: github_flow_manager
description: This skill manages GitHub Issues, Pull Requests, labels, and comments. It enables lifecycle management, batch operations, and automated workflows for repository collaboration.
---

# GitHub Flow Manager Skill

This skill provides comprehensive management capabilities for GitHub's collaboration features:

1. **Issue Management**: Create, update, close, reopen, list, and batch manage issues
2. **Pull Request Management**: Create, merge, close, and update PRs
3. **Label Management**: Add labels to issues and PRs (single or batch)
4. **Comment Management**: Add comments to issues and PRs, submit reviews

## 1. Issue Management

Manage GitHub Issues lifecycle with create, update, close, reopen, list, and batch operations.

**Use when**: You need to create issues, update issue details, close/reopen issues, list issues, or perform batch operations.

**Note**: For adding labels to issues, use `label_manager.py`. For adding comments, use `comment_manager.py`.

### Example

```bash
# Create a new issue
python issue_manager.py create owner repo --title "Bug Report" --body "## Description\n\nSteps to reproduce..."

# Create issue with labels and checklist
python issue_manager.py create owner repo --title "Feature Request" --body "Add dark mode" --labels "enhancement,ui" --checklist "Design,Implement,Test"

# List open issues
python issue_manager.py list owner repo --state open --limit 50

# List issues with specific labels
python issue_manager.py list owner repo --state all --labels "bug,critical"

# Update issue title and body
python issue_manager.py update owner repo --number 42 --title "Updated Title" --body "New description"

# Close an issue (mark as completed)
python issue_manager.py update owner repo --number 42 --state closed --state-reason completed

# Close an issue (mark as not planned)
python issue_manager.py update owner repo --number 42 --state closed --state-reason not_planned

# Reopen a closed issue
python issue_manager.py update owner repo --number 42 --state open --state-reason reopened

# Batch: Close all issues that have comments
python issue_manager.py close owner repo --filter has_comments

# Batch: Reopen issues matching query
python issue_manager.py reopen owner repo --query "memory leak"
```

## 2. Pull Request Management

Manage the complete PR lifecycle from creation to merging.

**Use when**: You need to create PRs, merge them with specific strategies, close PRs without merging, or update PR details.

**Note**: For adding comments to PRs, use `comment_manager.py`. For adding labels, use `label_manager.py`.

### Example

```bash
# Create a PR
python pr_manager.py create owner repo --head feature-branch --base main --title "Add new feature" --body "## Summary\n\nThis PR implements..."

# Create a draft PR
python pr_manager.py create owner repo --head wip-feature --base develop --title "WIP: New feature" --draft

# Create and immediately merge with squash
python pr_manager.py create owner repo --head hotfix/memory-leak --base main --title "Fix memory leak" --merge squash

# Merge existing PR with different methods
python pr_manager.py merge owner repo --number 42 --method squash
python pr_manager.py merge owner repo --number 42 --method merge
python pr_manager.py merge owner repo --number 42 --method rebase

# Merge with custom commit message
python pr_manager.py merge owner repo --number 42 --method squash --commit-title "feat: add feature" --commit-message "Detailed description"

# Close PR without merging
python pr_manager.py close owner repo --number 42

# Update PR details
python pr_manager.py update owner repo --number 42 --title "New Title" --body "Updated description"
python pr_manager.py update owner repo --number 42 --state closed
```

## 3. Label Management

Add labels to issues and pull requests, single or batch operations.

**Use when**: You need to add labels to issues or PRs.

### Example

```bash
# Add labels to an issue
python label_manager.py add owner repo --issue 42 --labels "bug,priority-high"

# Add labels to a PR
python label_manager.py add owner repo --pr 42 --labels "enhancement,needs-review"

# Batch add labels to multiple issues
python label_manager.py batch owner repo --issues "1,2,3,4,5" --labels "reviewed"

# Batch add labels to multiple PRs
python label_manager.py batch owner repo --prs "10,11,12" --labels "approved,ready-to-merge"
```

## 4. Comment Management

Add comments to issues and pull requests, including review comments with approval/rejection.

**Use when**: You need to add comments to issues or PRs, or submit code reviews.

### Example

```bash
# Add comment to an issue
python comment_manager.py add owner repo --issue 42 --body "Thanks for reporting this issue!"

# Add comment to a PR
python comment_manager.py add owner repo --pr 42 --body "LGTM! Great work on this feature."

# Submit review: just comment
python comment_manager.py review owner repo --pr 42 --body "Some suggestions for improvement..."

# Submit review: approve
python comment_manager.py review owner repo --pr 42 --body "Code looks good, approving." --event APPROVE

# Submit review: request changes
python comment_manager.py review owner repo --pr 42 --body "Please fix:\n\n1. Add null check\n2. Add unit tests" --event REQUEST_CHANGES
```
