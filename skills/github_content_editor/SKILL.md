---
name: github_content_editor
description: This skill enables direct file manipulation within GitHub repositories. It allows you to generate documentation (like ANSWER.md) and edit code files, handling the creating, updating, and pushing of files to the remote repository. Use this when you need to submit answers or apply fixes.
---

# GitHub Content Editor Skill

This skill allows for direct file manipulation within GitHub repositories:

1. **Document generation**: Create or update documentation files (ANSWER.md, CHANGELOG.md, etc.)
2. **File editing**: General-purpose file modification with search and replace

## 1. Document Generation

Create or update documentation files in the repository, including answer submission, changelog, and contributors list.

**Use when**: You need to submit answers, create documentation, or generate changelog/contributors from commit history.

### Example

```bash
# Submit an answer (creates/updates ANSWER.md)
python doc_gen.py answer owner repo --content "answer text" --message "Submit answer"

# Specify a branch (if not default)
python doc_gen.py answer owner repo --content "answer text" --message "Submit" --branch "master"

# Create a generic document
python doc_gen.py create owner repo --path "docs/API.md" --content "# API Reference" --message "Add API docs"

# Generate a changelog from commit history
python doc_gen.py changelog owner repo --since "2024-01-01"

# Generate a contributors list
python doc_gen.py contributors owner repo --output "CONTRIBUTORS.md"
```

## 2. File Editing (Single File)

Edit a single file. **Note: Each `edit` call creates a separate commit.**

**Use when**: You need to update a single file and a separate commit is acceptable.

### Example

```bash
# Edit/Overwrite a single file (creates 1 commit)
python file_editor.py edit owner repo --path "src/config.py" --content "DEBUG = False" --message "Disable debug"

# Apply a specific fix (search and replace in a single file)
python file_editor.py apply_fix owner repo --path "src/bug.py" --pattern "old_text" --replacement "new_text" --message "Fix bug"

# Mass edit (search and replace across multiple files - creates 1 commit per file)
python file_editor.py file_edit owner repo --query "http://old.com" --replacement "https://new.com" --message "Update URLs"
```

## 3. Batch File Operations (Multiple Files, Single Commit)

**IMPORTANT**: Use `batch` when you need to create/update multiple files in a **single commit**. This is essential when:
- Task requires "all files in one commit"
- Files are related and should be committed together (e.g., workflow + config)
- Atomic changes are needed

**Use when**: You need to create/update multiple files and want all changes in ONE commit.

### Example

```bash
# Push multiple files in a single commit (JSON array format)
python file_editor.py batch owner repo --files '[{"path": ".eslintrc.json", "content": "{...}"}, {"path": ".github/workflows/lint.yml", "content": "..."}, {"path": "src/example.js", "content": "..."}]' --message "Add linting setup" --branch "feature-branch"

# Add CI workflow with config files (all in one commit)
python file_editor.py batch owner repo --files '[{"path": ".github/workflows/ci.yml", "content": "..."}, {"path": ".prettierrc", "content": "..."}]' --message "Setup CI pipeline"
```
